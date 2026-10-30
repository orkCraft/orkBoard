"""Spec 107 parts F, H and I (docs/specs/107-what-the-owners-day-said.md §6, §8, §9), Chromium against the table's stub host (tests/test_table_desktop_browser.py `TableHost`).

F: the System drawn at its natural size and scaled to the pane's width (never under 0.5, then it scrolls sideways and the scroll cue marks the right), its arrows still on the columns' tops, *Fit* and *100 %* in
its corner (kept per project), a drag on empty ground panning. H: *+ Party*, the **▾** after the project's name opening the projects, a party's tab with an ork at work wearing `data-working` and its leader's head
stepping (none under reduced motion). I: Play's pane filled by the build (the sheet came back), the project's logo on the start screen, *Full screen*."""
from __future__ import annotations

import base64
import copy

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_table_desktop_browser import SHOP, TableHost, open_tab, shot, system_doc, tab, title, watch  # noqa: E402

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
    pg.locator(".table-tab").first.wait_for(timeout=WAIT_MS)
    return pg


def scale_of(pg) -> float:
    return float(pg.locator(".arch").get_attribute("data-scale"))


def open_system(pg):
    open_tab(pg, "tech")
    pg.locator(".table-sys .sys[data-state=shown] .arch").wait_for(timeout=WAIT_MS)
    pg.wait_for_function("() => document.querySelectorAll('.arch-col').length > 0 && document.querySelector('.arch').dataset.scale")


# -- F: the System fits ------------------------------------------------------------------------------------------------------------------------------

def test_the_system_is_scaled_to_the_panes_width_its_right_edge_in_view_and_its_arrows_on_the_columns(gui):
    errors: list[str] = []
    pg = start(gui, {"width": 1280, "height": 800}, errors, Host(n=3))
    open_system(pg)
    f = scale_of(pg)
    assert 0.5 <= f < 1, f                                                                                             # three columns of three cards are wider than the pane
    pg.wait_for_function("() => document.querySelector('.arch').getBoundingClientRect().width > 0")
    scroller = pg.locator(".sys-scroll").bounding_box()
    fit = pg.locator(".arch-fit").bounding_box()
    assert fit["x"] + fit["width"] <= scroller["x"] + scroller["width"] + 0.5, (fit, scroller)                          # no clipped right edge
    assert pg.evaluate("() => { const e = document.querySelector('.sys-scroll'); return e.scrollWidth <= e.clientWidth + 1; }")   # and nothing to scroll sideways
    assert pg.locator(".arch").evaluate("e => getComputedStyle(e).transform") != "none"
    right = pg.locator(".arch-col").last.bounding_box()
    assert right["x"] + right["width"] <= scroller["x"] + scroller["width"] + 0.5                                       # the last column lies inside the pane
    for edge, slot in (("c0>c1", -14), ("c1>c2", 0)):                                                                   # an arrow ends on its column's top, measured in the unscaled box: the middle, or a slot (28 px) beside it where two meet
        head = pg.locator(f'.arena-arrow[data-edge="{edge}"] polygon').bounding_box()
        col = pg.locator(f'.arch-col[data-container="{edge.split(">")[1]}"]').bounding_box()
        assert abs((head["x"] + head["width"] / 2) - (col["x"] + col["width"] / 2) - slot * f) <= 1.5, (edge, head, col, f)
        assert abs((head["y"] + head["height"]) - col["y"]) <= 4, (edge, head, col)
    shot(pg, "owners-day-system-fitted.png")
    pg.context.close()
    assert not errors, "\n".join(errors)


def test_a_system_that_would_pass_half_scrolls_sideways_marks_its_edge_and_a_drag_on_empty_ground_pans(gui):
    errors: list[str] = []
    pg = start(gui, {"width": 1280, "height": 800}, errors, Host(n=6))
    open_system(pg)
    assert scale_of(pg) == 0.5                                                                                         # never under 0.5
    scroller = pg.locator(".sys-scroll")
    assert scroller.evaluate("e => e.scrollWidth > e.clientWidth + 10")
    assert "right" in (scroller.get_attribute("data-more") or "").split() and "left" not in (scroller.get_attribute("data-more") or "").split()
    box = scroller.bounding_box()
    y = box["y"] + box["height"] - 6                                                                                   # the empty ground under the cards
    pg.mouse.move(box["x"] + 600, y)
    pg.mouse.down()
    for dx in range(0, 300, 20):
        pg.mouse.move(box["x"] + 600 - dx, y)
    pg.mouse.up()
    assert scroller.evaluate("e => e.scrollLeft") > 100, "a drag on the empty ground pans"
    assert "left" in (scroller.get_attribute("data-more") or "").split()
    assert pg.locator(".table-back").count() == 0                                                                      # and presses nothing
    pg.context.close()
    assert not errors, "\n".join(errors)


def test_fit_and_100_percent_in_the_corner_the_choice_kept_for_the_project(gui):
    errors: list[str] = []
    host = Host(n=3)
    pg = start(gui, {"width": 1280, "height": 800}, errors, host)
    open_system(pg)
    fitted = scale_of(pg)
    assert fitted < 1 and pg.locator('.arch-zoom [data-fit="fit"]').get_attribute("aria-pressed") == "true"
    assert [b.inner_text().strip() for b in pg.locator(".arch-zoom button").all()] == ["Fit", "100 %"]
    pg.get_by_role("button", name="100 %").click()
    pg.wait_for_function("() => document.querySelector('.arch').dataset.scale === '1.000'")
    assert pg.locator('.arch-zoom [data-fit="full"]').get_attribute("aria-pressed") == "true"
    scroller = pg.locator(".sys-scroll")
    assert scroller.evaluate("e => e.scrollWidth > e.clientWidth + 10")                                                # its own size passes the pane: it scrolls
    assert pg.evaluate(f"() => localStorage.getItem('orkboard.system.fit.{SHOP}')") == "full"
    for slug in ("art", "tech"):                                                                                       # away and back, and the page again: kept
        open_tab(pg, slug)
    pg.locator(".arch").wait_for(timeout=WAIT_MS)
    assert scale_of(pg) == 1
    pg.reload()
    pg.locator(".table-tab").first.wait_for(timeout=WAIT_MS)
    open_system(pg)
    assert scale_of(pg) == 1
    pg.get_by_role("button", name="Fit").click()
    pg.wait_for_function(f"() => Number(document.querySelector('.arch').dataset.scale) === {fitted}")
    assert pg.evaluate(f"() => localStorage.getItem('orkboard.system.fit.{SHOP}')") == "fit"
    pg.context.close()
    assert not errors, "\n".join(errors)


def test_a_system_refused_its_storage_still_fits(gui):
    errors: list[str] = []
    server, browser = gui
    host = Host(n=3)
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    context.add_init_script("Object.defineProperty(window, 'localStorage', { get() { throw new Error('blocked'); } });")
    pg = context.new_page()
    watch(pg, errors)
    pg.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".table-tab").first.wait_for(timeout=WAIT_MS)
    open_system(pg)
    assert scale_of(pg) < 1
    pg.get_by_role("button", name="100 %").click()
    pg.wait_for_function("() => document.querySelector('.arch').dataset.scale === '1.000'")
    pg.context.close()
    assert not [e for e in errors if "blocked" not in e], "\n".join(errors)


# -- H: + Party, the project ▾, a working party's head ---------------------------------------------------------------------------------------------------

@pytest.fixture(params=narrow.WIDTHS)
def tabs(gui, request):
    errors: list[str] = []
    host = Host(n=3)
    pg = start(gui, request.param, errors, host)
    pg.locator(".table-card, .table-token").first.wait_for(timeout=WAIT_MS)
    yield pg, host, request.param
    pg.context.close()
    assert not errors, "\n".join(errors)


def test_plus_party_and_the_arrow_after_the_project_name_open_the_parties_and_the_projects(tabs):
    pg, host, w = tabs
    plus = pg.locator(".table-tabs__end .table-plus")
    assert " ".join(plus.inner_text().split()) == ("Party" if w == "wide" else "") and plus.get_attribute("aria-label") == "New party"      # a row of heads says the + alone
    assert "primary" not in plus.get_attribute("class")
    arrow = pg.get_by_role("button", name="Switch project")
    assert arrow.count() == 1 and arrow.get_attribute("title") == "Switch project" and arrow.locator("use").get_attribute("href").endswith("#chevron-down")
    first = tab(pg, "orkmaster").bounding_box()
    box = arrow.bounding_box()
    assert first["x"] <= box["x"] and box["x"] + box["width"] <= first["x"] + first["width"] + 1                       # after the name, inside the first tab's place
    shot(pg, f"owners-day-tabs-{w}.png")
    arrow.click()
    pg.locator('.table-over[data-kind="projects"]').wait_for(timeout=WAIT_MS)
    assert title(pg) == "Board · Projects" and pg.locator(".table-projects__one").count() == 3
    pg.locator(".table-title__back").click()
    pg.locator(".table-board").wait_for(timeout=WAIT_MS)
    assert tab(pg, "orkmaster").get_attribute("aria-selected") == "true"                                               # the ▾ is no tab
    plus.click()
    pg.locator('.table-over[data-kind="parties"]').wait_for(timeout=WAIT_MS)


def test_a_party_with_an_ork_at_work_has_data_working_and_its_leaders_head_steps(gui):
    errors: list[str] = []
    host = Host(n=3)
    pg = start(gui, {"width": 1280, "height": 800}, errors, host)
    pg.locator(".table-card, .table-token").first.wait_for(timeout=WAIT_MS)
    assert tab(pg, "tech").get_attribute("data-working") is not None and tab(pg, "game").get_attribute("data-working") is not None
    assert tab(pg, "release").get_attribute("data-working") is None and tab(pg, "orkmaster").get_attribute("data-working") is None
    style = tab(pg, "tech").locator(".ork-race__head").evaluate("e => { const s = getComputedStyle(e); return [s.animationName, s.animationDuration, s.animationTimingFunction]; }")
    assert style == ["table-tab-step", "1.2s", "steps(2)"], style
    assert tab(pg, "release").locator(".ork-race__head").evaluate("e => getComputedStyle(e).animationName") == "none"
    host.nodes = [n for n in host.nodes if not n.get("tasks")]                                                         # nothing at work any more: the heads stand still
    host.rev += 1
    host.ws.send(__import__("json").dumps(host.snapshot()))
    pg.wait_for_function("() => !document.querySelector('.table-tab[data-tab=\"tech\"][data-working]')", timeout=WAIT_MS)
    pg.context.close()
    assert not errors, "\n".join(errors)


def test_the_head_stands_still_under_reduced_motion(gui):
    errors: list[str] = []
    pg = start(gui, {"width": 1280, "height": 800}, errors, Host(n=3), reduced_motion="reduce")
    pg.locator(".table-card, .table-token").first.wait_for(timeout=WAIT_MS)
    assert tab(pg, "tech").get_attribute("data-working") is not None
    assert tab(pg, "tech").locator(".ork-race__head").evaluate("e => getComputedStyle(e).animationName") == "none"
    pg.context.close()
    assert not errors, "\n".join(errors)


# -- I: Play ---------------------------------------------------------------------------------------------------------------------------------------------

def open_play(pg):
    pg.locator(".hand-die").click()
    pg.locator('.table-over[data-kind="play"]').wait_for(timeout=WAIT_MS)


def test_plays_frame_fills_the_pane_and_full_screen_lays_its_stage_over_the_screen(gui):
    errors: list[str] = []
    pg = start(gui, {"width": 1280, "height": 800}, errors, Host(play=PLAYING))
    open_play(pg)
    frame = pg.locator(".play-frame")
    frame.wait_for(timeout=WAIT_MS)
    box, pane = frame.bounding_box(), pg.locator(".table-over").bounding_box()
    assert box["height"] > 300 and box["width"] > 300, box                                                              # not the browser's 300 x 150
    assert box["width"] >= pane["width"] - 2 and box["y"] + box["height"] <= pane["y"] + pane["height"] + 1
    assert box["height"] >= pane["height"] - 80                                                                         # the bar over it is all that is not the build
    assert pg.locator(".play-bar").bounding_box()["height"] < 80
    assert pg.get_by_role("button", name="Stop the build").count() == 1
    shot(pg, "owners-day-play.png")
    full = pg.get_by_role("button", name="Full screen")
    assert full.count() == 1 and full.get_attribute("title")
    full.click()
    pg.wait_for_function("() => document.fullscreenElement && document.fullscreenElement.classList.contains('play-stage')", timeout=WAIT_MS)
    pg.keyboard.press("Escape")
    pg.context.close()
    assert not errors, "\n".join(errors)


def test_the_start_screen_is_the_projects_logo_with_its_name_under_it_else_the_name_alone(gui):
    """Spec 112 §3.4: the logo no longer shows while the build starts (the die is thrown then: tests/test_play_die_browser.py); it comes up after the die's landing on the tick, as it did before. Under reduced motion it is today's screen."""
    errors: list[str] = []
    starting = {"state": "starting", "commit": "a" * 40, "short": "aaaaaaa", "stage": "page", "command": "npm run dev", "ports": [5173], "since": 3.0}
    host = Host(play={**starting, "logo": LOGO})
    pg = start(gui, {"width": 1280, "height": 800}, errors, host)
    open_play(pg)
    pg.locator(".play-throw[data-phase=roll]").wait_for(timeout=WAIT_MS)
    assert pg.locator(".play-logo").count() == 0                                                                        # the die rolls, the logo waits
    host.play = {**PLAYING, "logo": LOGO}
    logo = pg.locator(".play-intro .play-logo__img")
    logo.wait_for(timeout=WAIT_MS)
    pg.wait_for_function("() => { const i = document.querySelector('.play-logo__img'); return i && i.complete && i.naturalWidth > 0; }")
    assert logo.bounding_box()["height"] == 128 and logo.get_attribute("src") == LOGO
    assert logo.evaluate("e => getComputedStyle(e).imageRendering") == "pixelated"                                      # 32 px wide: whole pixels
    assert pg.locator(".play-logo").evaluate("e => getComputedStyle(e).animationName") == "play-logo-in"
    assert pg.locator(".play-logo__sweep").evaluate("e => [getComputedStyle(e).animationName, getComputedStyle(e).animationDuration, getComputedStyle(e).animationIterationCount]") == ["play-logo-sweep", "2.4s", "infinite"]
    assert pg.locator(".play-intro .play-title").is_visible() and pg.locator(".play-intro.has-logo").count() == 1
    assert logo.bounding_box()["y"] + 128 <= pg.locator(".play-title").bounding_box()["y"] + 1                          # the name under it
    shot(pg, "owners-day-play-start.png")
    pg.context.close()
    host = Host(play={**starting, "logo": ""})
    plain = start(gui, {"width": 1280, "height": 800}, errors, host)
    open_play(plain)
    plain.locator(".play-throw[data-phase=roll]").wait_for(timeout=WAIT_MS)
    host.play = PLAYING
    plain.locator(".play-intro:not(.play-throw) .play-title").wait_for(timeout=WAIT_MS)
    assert plain.locator(".play-logo").count() == 0 and plain.locator(".play-intro.has-logo").count() == 0
    plain.context.close()
    assert not errors, "\n".join(errors)


def test_under_reduced_motion_the_start_screen_is_the_logo_while_it_starts_as_before(gui):
    errors: list[str] = []
    starting = {"state": "starting", "commit": "a" * 40, "short": "aaaaaaa", "stage": "page", "command": "npm run dev", "ports": [5173], "since": 3.0, "logo": LOGO}
    pg = start(gui, {"width": 1280, "height": 800}, errors, Host(play=starting), reduced_motion="reduce")
    open_play(pg)
    logo = pg.locator(".play-intro .play-logo__img")
    logo.wait_for(timeout=WAIT_MS)
    assert logo.bounding_box()["height"] == 128 and pg.locator(".play-intro.has-logo .play-title").is_visible() and pg.locator(".playpane .ork-die").count() == 0
    pg.context.close()
    assert not errors, "\n".join(errors)


def test_the_logo_stands_still_under_reduced_motion(gui):
    errors: list[str] = []
    starting = {"state": "starting", "commit": "a" * 40, "short": "aaaaaaa", "stage": "worktree", "command": "", "ports": [], "since": 0, "logo": LOGO}
    pg = start(gui, {"width": 1280, "height": 800}, errors, Host(play=starting), reduced_motion="reduce")
    open_play(pg)
    pg.locator(".play-logo__img").wait_for(timeout=WAIT_MS)
    for sel in (".play-logo", ".play-logo__img", ".play-intro .play-title"):
        assert pg.locator(sel).evaluate("e => getComputedStyle(e).animationName") == "none", sel
    assert pg.locator(".play-logo__sweep").evaluate("e => getComputedStyle(e).display") == "none"
    pg.context.close()
    assert not errors, "\n".join(errors)
