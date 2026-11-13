"""Spec 107 parts F, H and I (docs/specs/107-what-the-owners-day-said.md §6, §8, §9), Chromium against the table's stub host (tests/test_table_desktop_browser.py `TableHost`).

F: the System drawn at its natural size and scaled to the pane's width (never under 0.5, then it scrolls sideways and the scroll cue marks the right), its arrows still on the columns' tops, *Fit* and *100 %* in
its corner (kept per project), a drag on empty ground panning. H: *+ Party*, the **▾** after the project's name opening the projects, a party's tab with an ork at work wearing `data-working` and its leader's head
standing still (its face says it: spec 123 §7.3). I: Play's pane filled by the build (the sheet came back), the project's logo on the start screen, *Full screen*."""
from __future__ import annotations

import base64
import copy

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_table_desktop_browser import TableHost, system_doc, watch  # noqa: E402

pytestmark = pytest.mark.browser

PAGE = base64.b64encode(b"<!doctype html><title>Game</title><body style='background:#123'><h1>dev's build</h1>").decode()
LOGO = "data:image/svg+xml;base64," + base64.b64encode(b"<svg xmlns='http://www.w3.org/2000/svg' width='32' height='32'><rect width='32' height='32' fill='#fff'/></svg>").decode()
PLAYING = {"state": "playing", "url": f"data:text/html;base64,{PAGE}", "commit": "a" * 40, "short": "aaaaaaa", "dev": "a" * 40, "logo": ""}


def system_of(n: int):
    """A System of `n` containers in a row, each a layer of three parts (a row of three cards): wider than a pane at 1280 px from three on, past twice its width from six."""
    doc = system_doc()
    parts, containers = {}, []
    for i in range(n):
        paths = [f"c{i}/p{j}.ts" for j in range(3)]
        for p in paths:
            parts[p] = {"path": p, "name": p.rsplit("/", 1)[-1], "count": 2, "uses": [], "used_by": [], "gone": False}
        containers.append({"path": f"c{i}", "name": f"c{i}/", "stack": [{"name": "Express", "role": "server"}], "unknown": 0, "ways_in": [], "parts": paths,
                           "layers": [{"role": "data", "parts": paths}], "gone": []})
    links = [{"from": f"c{i}", "to": f"c{i + 1}", "http": [{"method": "GET", "path": f"/r{i}", "called_in": f"c{i}/p0.ts", "answered_in": f"c{i + 1}/p0.ts"}], "socket": []} for i in range(n - 1)]
    doc["overview"] = {"containers": containers, "shared": [], "links": links, "parts": parts}
    return doc


class Host(TableHost):
    """The table's host with a System of `n` containers and a Play that answers `play`."""

    def __init__(self, n: int = 3, play: dict | None = None, **kw):
        super().__init__(**kw)
        self.n, self.play = n, play or {"state": "stopped"}

    def handle(self, name, a):
        if name == "ideas.system":
            self.log.append((name, a))
            return copy.deepcopy(system_of(self.n))
        if name == "ideas.play":
            self.log.append((name, a))
            return dict(self.play)
        if name == "ideas.play_stop":
            self.log.append((name, a))
            return {"ok": True, "stopped": True}
        return super().handle(name, a)


def start(gui, width, errors, host, **ctx):
    server, browser = gui
    context = browser.new_context(viewport=width, **ctx) if isinstance(width, dict) else narrow.context(browser, width)
    pg = context.new_page()
    pg.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    watch(pg, errors)
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".table-tab, .col-head__tab").first.wait_for(timeout=WAIT_MS)
    return pg






# -- F: the System fits ------------------------------------------------------------------------------------------------------------------------------






# -- H: + Party, the project ▾, a working party's head ---------------------------------------------------------------------------------------------------

@pytest.fixture(params=narrow.WIDTHS)
def tabs(gui, request):
    errors: list[str] = []
    host = Host(n=3)
    pg = start(gui, request.param, errors, host)
    pg.locator(".cards-lane").first.wait_for(timeout=WAIT_MS)
    yield pg, host, request.param
    pg.context.close()
    assert not errors, "\n".join(errors)








# -- I: Play ---------------------------------------------------------------------------------------------------------------------------------------------

def open_play(pg):
    pg.locator(".hand-die__play").click()
    pg.locator('.table-over[data-kind="play"]').wait_for(timeout=WAIT_MS)








