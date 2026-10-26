"""Spec 91 part C on the desktop (docs/specs/91-the-owners-list.md §5, decisions §107): Chromium at 1 440 × 900 against the assets stub host with `ideas.play` answering as the host gives it. While Play starts the
project's name in the pixel face fades in and out in a loop (2.4 s, in steps, never ending), and under it one line says the stage (*Making its worktree*, *Starting <command>*, *Waiting for a page on :<port>*) with
the seconds counting up from the host's `since`; under reduced motion the name stands still and fully seen, the line is there all the same. A build that did not start says why and shows the command's last lines in
a quiet box (the code face, scrolling, about twelve lines showing), with the control to open the build again. Screenshots to the directory ORKCRAFT_SHOTS_DIR names when it is set (play-breathing.png, play-tail.png)."""
from __future__ import annotations

import copy
import time

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_assets_desktop_browser import HEAD, AssetsHost, _play, level, serve  # noqa: E402,F401  (fixture)
from tests.test_route_desktop_browser import shot  # noqa: E402
from tests.test_shell_browser import _calls, _open  # noqa: E402

pytestmark = pytest.mark.browser

START = {"state": "starting", "commit": HEAD, "short": HEAD[:7]}
WORKTREE = START | {"stage": "worktree", "command": "", "ports": [], "since": 0.4}
COMMAND = START | {"stage": "command", "command": "npm run dev", "ports": [], "since": 7.0}
PAGE = START | {"stage": "page", "command": "npm run dev", "ports": [3001, 5173], "since": 12.0}
PAGE_ONE = PAGE | {"ports": [5173]}
TAIL = [f"line {i}" for i in range(30)] + ["error: vite could not start"]


class TickingHost(AssetsHost):
    """Play's answers as the host gives them: `since` runs on with the clock from `t0` (`live`: the answer, else the script's)."""

    live: dict | None = None
    t0 = 0.0

    def handle(self, name, a):
        if name == "ideas.play" and self.live is not None and a.get("peek"):
            self.log.append((name, a))
            return copy.deepcopy(self.live) | {"since": round(self.live["since"] + time.monotonic() - self.t0, 1)}
        return super().handle(name, a)


@pytest.fixture
def ticking(gui, tmp_path):
    pg, host, errors = _open(gui, host=TickingHost(), ready=".arena[data-goal=passkey]")
    serve(pg, tmp_path)
    yield pg, host
    pg.close()
    assert not errors, "\n".join(errors)


def _words(pg) -> str:
    return pg.locator(".play-stage-words").text_content().strip()


def test_the_name_fades_in_and_out_in_a_slow_loop_in_steps(level):
    pg, host = level
    host.play = [{"state": "stopped"}, WORKTREE]
    _play(pg)
    pg.get_by_role("button", name="Open the build").click()
    pg.locator('.playpane[data-state="starting"]').wait_for(timeout=WAIT_MS)
    title = pg.locator(".play-title")
    got = title.evaluate("e => { const s = getComputedStyle(e); return {name: s.animationName, count: s.animationIterationCount, time: s.animationDuration, fn: s.animationTimingFunction, face: s.fontFamily}; }")
    assert got["name"] == "play-name-loop" and got["count"] == "infinite" and got["time"] == "2.4s"           # a slow loop that never ends
    assert got["fn"].startswith("steps(") and "Pixelify" in got["face"]                                       # in steps, never a spin; the pixel face
    seen = set()
    for _ in range(12):                                                                                      # it is fading: the opacity is not one value
        seen.add(title.evaluate("e => getComputedStyle(e).opacity"))
        pg.wait_for_timeout(250)
    assert len(seen) > 2 and all(0 < float(o) <= 1 for o in seen)
    shot(pg, "play-breathing.png")


def test_the_line_under_the_name_says_the_stage_in_words(level):
    pg, host = level
    host.play = [{"state": "stopped"}, WORKTREE, COMMAND, PAGE, PAGE_ONE]
    _play(pg)
    pg.get_by_role("button", name="Open the build").click()
    pg.locator(".play-starting").wait_for(timeout=WAIT_MS)
    assert _words(pg) == "Making its worktree"
    pg.wait_for_function("() => document.querySelector('.play-stage-words')?.textContent.startsWith('Starting')", timeout=WAIT_MS)
    assert _words(pg) == "Starting npm run dev" and pg.locator(".play-stage-words code").text_content() == "npm run dev"       # the command as words, in the code face
    assert "Pixelify" not in pg.locator(".play-stage-words code").evaluate("e => getComputedStyle(e).fontFamily")
    pg.wait_for_function("() => document.querySelector('.play-stage-words')?.textContent.startsWith('Waiting')", timeout=WAIT_MS)
    assert _words(pg) in ("Waiting for a page on :3001, :5173", "Waiting for a page on :5173")                  # the ports asked so far
    pg.wait_for_function("() => document.querySelector('.play-stage-words')?.textContent === 'Waiting for a page on :5173'", timeout=WAIT_MS)
    assert pg.locator(".play-starting").get_attribute("role") == "status"
    shot(pg, "play-stage.png")


def test_the_seconds_count_up_from_the_hosts_since_and_on_the_page_between_its_answers(ticking):
    pg, host = ticking
    host.play = [{"state": "stopped"}]
    _play(pg)
    host.play = [PAGE_ONE]
    host.live, host.t0 = PAGE_ONE, time.monotonic()
    pg.get_by_role("button", name="Open the build").click()
    pg.locator(".play-secs").wait_for(timeout=WAIT_MS)

    def secs() -> int:
        return int(pg.locator(".play-secs").text_content().strip().removesuffix(" s"))

    first = secs()
    assert 12 <= first <= 20                                                                                  # from the host's `since`
    seen = {first}
    for _ in range(6):
        pg.wait_for_timeout(500)                                                                              # the page's own clock runs between the host's answers (every second)
        seen.add(secs())
    assert max(seen) >= first + 2 and sorted(seen) == [*range(min(seen), max(seen) + 1)]                      # one by one, upwards
    assert pg.locator(".play-secs").get_attribute("aria-hidden") == "true"                                    # not read out each second


def test_under_reduced_motion_the_name_stands_still_and_the_stage_line_is_there(gui, tmp_path):
    pg = gui[1].new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    host = AssetsHost()
    host.play = [{"state": "stopped"}, COMMAND]
    pg.route_web_socket("**/ws*", host.on_socket)
    serve(pg, tmp_path)
    pg.goto(gui[0].url)
    pg.locator(".arena[data-goal=passkey]").wait_for(timeout=WAIT_MS)
    _play(pg)
    pg.get_by_role("button", name="Open the build").click()
    pg.locator('.playpane[data-state="starting"]').wait_for(timeout=WAIT_MS)
    title = pg.locator(".play-title")
    assert title.evaluate("e => getComputedStyle(e).animationName") == "none" and title.evaluate("e => getComputedStyle(e).opacity") == "1"
    pg.wait_for_function("() => document.querySelector('.play-stage-words')?.textContent === 'Starting npm run dev'", timeout=WAIT_MS)
    pg.wait_for_timeout(700)
    assert title.evaluate("e => getComputedStyle(e).opacity") == "1" and title.is_visible()                  # fully seen, still
    pg.close()
    assert not errors, "\n".join(errors)


def test_a_failure_says_why_and_shows_the_last_lines_in_a_quiet_scrolling_box(level):
    pg, host = level
    host.play = [{"state": "stopped"}, {"state": "failed", "error": "did not open", "tail": TAIL}]
    _play(pg)
    pg.get_by_role("button", name="Open the build").click()
    pg.locator(".play-tail").wait_for(timeout=WAIT_MS)
    assert pg.locator(".play-error").text_content().strip() == "The build would not start: did not open"
    box = pg.locator(".play-tail__lines")
    assert box.text_content() == "\n".join(TAIL)
    face = box.evaluate("e => { const s = getComputedStyle(e); return {family: s.fontFamily, overflow: s.overflowY, line: parseFloat(s.lineHeight), size: parseFloat(s.fontSize), height: e.clientHeight, scroll: e.scrollHeight, top: e.scrollTop, pad: parseFloat(s.paddingTop) + parseFloat(s.paddingBottom)}; }")
    code = pg.evaluate("() => { const e = document.createElement('code'); document.body.append(e); const f = getComputedStyle(e).fontFamily; e.remove(); return f; }")
    assert face["family"] == code and face["overflow"] in ("auto", "scroll")                                  # the code face; it scrolls
    assert face["size"] >= 12 and (face["height"] - face["pad"]) / face["line"] <= 12.01                       # about twelve lines show
    assert face["scroll"] > face["height"] and face["top"] > 0                                                # more lines than show; it stands at the newest
    background = box.evaluate("e => getComputedStyle(e).backgroundColor")
    panel = pg.evaluate("() => { const e = document.createElement('i'); e.style.background = 'var(--ork-panel)'; document.body.append(e); const c = getComputedStyle(e).backgroundColor; e.remove(); return c; }")
    assert background == panel                                                                                # an orkUI token, not a colour of its own
    assert pg.get_by_role("button", name="Open the build").count() == 1 and pg.locator("iframe").count() == 0   # it may be pressed again
    shot(pg, "play-tail.png")
    host.play = [{"state": "starting", **{k: v for k, v in WORKTREE.items() if k != "state"}}, {"state": "failed", "error": "did not open", "tail": ["again"]}]
    host.at = 0
    pg.get_by_role("button", name="Open the build").click()
    pg.wait_for_function("() => document.querySelector('.play-tail__lines')?.textContent === 'again'", timeout=WAIT_MS)
    assert len(_calls(pg, host, "ideas.play")) >= 3


def test_a_failure_with_no_output_shows_no_box_and_a_build_with_no_page_shows_its_lines(level):
    pg, host = level
    host.play = [{"state": "stopped"}, {"state": "failed", "error": "did not open", "tail": []}]
    _play(pg)
    pg.get_by_role("button", name="Open the build").click()
    pg.locator(".play-error").wait_for(timeout=WAIT_MS)
    assert pg.locator(".play-tail").count() == 0
    host.play = [{"state": "failed", "why": "nopage", "error": "The build started, but no port gives a page. Name it in .orkcraft/checks.toml: preview_port or preview_path.",
                  "ports": [3001], "tail": ["Local: http://localhost:3001/"]}]
    host.at = 0
    pg.get_by_role("button", name="Open the build").click()
    pg.locator('.playpane[data-state="nopage"]').wait_for(timeout=WAIT_MS)
    assert pg.locator(".play-tail__lines").text_content() == "Local: http://localhost:3001/" and pg.get_by_role("button", name="Stop the build").count() == 1
