"""Spec 112 part B (docs/specs/112-the-bars-marks-and-the-play-die.md §3, decisions §190), Chromium against the table's stub host (tests/test_owners_day_desktop_browser.py `Host`, whose Play answers what a test sets).

The bar: + Party wears orkUI's banner (unfurling once on hover, not under reduced motion), Stop all the boards across a pole before its word. Play is no button of the pane's head but a die in the hand, left of the potions, its word under it, turned by the lean token;
it wobbles once on hover, opens the play view and closes it. A start is thrown: the die flies onto the black pane and rolls (no logo meanwhile), lands on the green tick (*It started*), then today's logo, the frame and the die in the hand glowing; a failed start lands on the
red cross, tips over and today's failure takes its place; a build already playing opens at once and the die in the hand wobbles twice; under reduced motion it is today's start screen. Screenshots to the directory ORKCRAFT_SHOTS_DIR names when it is set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_owners_day_desktop_browser import LOGO, PLAYING, Host, start  # noqa: E402

pytestmark = pytest.mark.browser

WIDE = {"width": 1280, "height": 800}
STARTING = {"state": "starting", "commit": "a" * 40, "short": "aaaaaaa", "stage": "command", "command": "npm run dev", "ports": [5173], "since": 2.0, "logo": ""}
FAILED = {"state": "failed", "error": "npm run dev stopped (exit 1)", "tail": ["> tower-brawl@0.3.0 dev", "> vite", "", "Error: Cannot find module 'vite'"]}
NO_ANIMATION = "none"


def shot(pg, name):
    d = os.environ.get("ORKCRAFT_SHOTS_DIR")
    if d:
        Path(d).mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(Path(d) / name))


def die(pg):
    return pg.locator(".hand-die")


def press(pg):
    die(pg).click()
    pg.locator('.table-over[data-kind="play"]').wait_for(timeout=WAIT_MS)


def window(gui, host, width=WIDE, errors=None, cards=True, **ctx):
    errors = [] if errors is None else errors
    pg = start(gui, width, errors, host, **ctx)
    if cards:
        pg.locator(".table-card, .table-token").first.wait_for(timeout=WAIT_MS)
    die(pg).wait_for(timeout=WAIT_MS)
    return pg, errors


def record_phases(pg):
    """Records every phase the throw goes through, with the die's animation at it (a phase of 300 ms is too short to wait for with a poll)."""
    pg.evaluate("""() => { window.__phases = []; const note = () => { const t = document.querySelector('.play-throw'); if (!t) return;
      const p = t.dataset.phase, d = t.querySelector('.play-die'), last = window.__phases[window.__phases.length - 1];
      if (!last || last[0] !== p) window.__phases.push([p, d ? getComputedStyle(d).animationName : '']); };
      new MutationObserver(note).observe(document.body, { subtree: true, childList: true, attributes: true, attributeFilter: ['data-phase'] }); note(); }""")


def phases_seen(pg):
    return pg.evaluate("() => window.__phases")


def finish(pg, errors):
    pg.context.close()
    assert not errors, "\n".join(errors)


# -- the bar ------------------------------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_plus_party_wears_the_banner_and_stop_all_the_boards_before_its_word_and_the_pane_has_no_play(gui, width):
    pg, errors = window(gui, Host(), {"wide": WIDE, "narrow": {"width": 390, "height": 844}}[width])
    plus, stop = pg.locator(".table-tabs__end .table-plus"), pg.locator(".table-tabs__end .table-stop")
    assert plus.locator("use").get_attribute("href").endswith("/icons/icons.svg#banner") and plus.get_attribute("aria-label") == "New party"
    assert stop.locator("use").get_attribute("href").endswith("/icons/icons.svg#boarded") and " ".join(stop.inner_text().split()) == "Stop all"
    icon, word = stop.locator(".ork-icon").bounding_box(), stop.bounding_box()
    assert word["x"] <= icon["x"] < word["x"] + word["width"] / 2                                                         # the boards stand before the word
    assert stop.locator(".ork-icon").evaluate("e => getComputedStyle(e).color") == stop.evaluate("e => getComputedStyle(e).color")      # in the danger colour of the button
    assert stop.evaluate("e => getComputedStyle(e).color") != pg.locator(".table-tab").first.evaluate("e => getComputedStyle(e).color")
    assert pg.locator(".table-play").count() == 0 and pg.locator(".table-title").get_by_role("button", name="Play").count() == 0       # Play left the pane's head
    assert not pg.locator(".table-title").inner_text().count("Play")
    shot(pg, f"b112-bar-{width}.png")
    finish(pg, errors)


def test_the_banner_unfurls_once_on_hover_in_whole_steps_and_not_under_reduced_motion(gui):
    pg, errors = window(gui, Host())
    icon = pg.locator(".table-plus > .ork-icon")
    assert icon.evaluate("e => getComputedStyle(e).animationName") == NO_ANIMATION
    pg.locator(".table-plus").hover()
    assert icon.evaluate("e => [getComputedStyle(e).animationName, getComputedStyle(e).animationIterationCount, getComputedStyle(e).animationDuration]") == ["table-banner-unfurl", "1", "0.36s"]
    pg.context.close()
    still, errs = window(gui, Host(), reduced_motion="reduce")
    still.locator(".table-plus").hover()
    assert still.locator(".table-plus > .ork-icon").evaluate("e => getComputedStyle(e).animationName") == NO_ANIMATION
    finish(still, errs)
    assert not errors, "\n".join(errors)


# -- the die in the hand ------------------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_the_die_lies_in_the_hand_left_of_the_potions_with_its_word_under_it_askew(gui, width):
    pg, errors = window(gui, Host(), {"wide": WIDE, "narrow": {"width": 390, "height": 844}}[width])
    d = die(pg)
    pg.locator(".hand-mana .hand-pot").first.wait_for(timeout=WAIT_MS)
    assert d.evaluate("e => e.closest('.hand') !== null") and d.get_attribute("aria-label") == "Play: the project's preview of dev" and d.get_attribute("title") == d.get_attribute("aria-label")
    assert d.locator(".hand-die__word").inner_text() == "Play" and d.locator(".ork-die").get_attribute("aria-hidden") == "true"
    box, mana, word = d.locator(".ork-die").bounding_box(), pg.locator(".hand-mana").bounding_box(), d.locator(".hand-die__word").bounding_box()
    assert 66 <= box["width"] <= 80 and 69 <= box["height"] <= 82                                                      # 69 x 72 (3 px a cell), turned a little: it keeps its size at the narrow width too
    assert d.bounding_box()["x"] + d.bounding_box()["width"] <= mana["x"] + 7 and box["x"] < mana["x"]                    # left of the potions (at the narrow width its edge lies over the first potion's empty border)
    assert word["y"] >= box["y"] + 56                                                                                   # its word under it
    assert d.locator(".ork-die").evaluate("e => getComputedStyle(e).rotate") == "-6deg"                                 # the lean token the other way
    assert d.locator(".ork-die > .ork-die__cube > .ork-die__face").count() == 6                                         # orkUI's die is a cube in CSS 3D (0.24.0): its six faces
    assert d.locator(".ork-die__cube").evaluate("e => getComputedStyle(e).transformStyle") == "preserve-3d"
    assert d.locator(".ork-die__face.is-front").bounding_box()["height"] > 4 and d.locator(".ork-die__face.is-right").bounding_box()["width"] > 4      # seen from above, its front and right faces show
    narrow.no_sideways(pg)
    shot(pg, f"b112-hand-{width}.png")
    finish(pg, errors)


def test_the_die_wobbles_once_on_hover_stays_lifted_and_presses_open_and_closed(gui):
    pg, errors = window(gui, Host(play=PLAYING))
    d = die(pg)
    d.evaluate("e => { window.__wobbles = 0; e.addEventListener('animationstart', (ev) => { if (ev.animationName === 'ork-die-wobble') window.__wobbles++; }); }")
    d.hover()
    pg.wait_for_function("() => window.__wobbles === 1", timeout=WAIT_MS)
    pg.wait_for_function("() => !document.querySelector('.hand-die .ork-die.is-wobbling')", timeout=WAIT_MS)             # taken off at animationend
    assert d.locator(".ork-die").evaluate("e => getComputedStyle(e).transform") != "none"                               # and stays lifted while hovered
    assert pg.evaluate("() => window.__wobbles") == 1
    d.click()
    pg.locator('.table-over[data-kind="play"]').wait_for(timeout=WAIT_MS)
    assert d.get_attribute("aria-label") == "Close the preview" and d.get_attribute("title") == "Close the preview"
    d.click()
    pg.wait_for_selector(".table-over", state="detached", timeout=WAIT_MS)
    assert d.get_attribute("aria-label") == "Play: the project's preview of dev" and d.locator(".hand-die__word").inner_text() == "Play"
    finish(pg, errors)


def test_with_no_goal_at_all_the_die_still_lies_in_the_hand(gui):
    host = Host(rich=False)
    host.nodes = []
    pg, errors = window(gui, host, cards=False)
    assert die(pg).count() == 1
    press(pg)
    assert pg.locator(".table-over").count() == 1
    finish(pg, errors)


def test_the_phones_upright_hand_has_no_play(gui):
    server, browser = gui
    errors: list[str] = []
    host = Host()
    pg = narrow.context(browser, "phone").new_page()
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".hand, .up-screen, [class*=upright]").first.wait_for(timeout=WAIT_MS)
    pg.wait_for_timeout(500)
    assert pg.locator(".hand-die").count() == 0 and pg.get_by_role("button", name="Play").count() == 0
    pg.context.close()
    assert not errors, "\n".join(errors)


# -- the throw ----------------------------------------------------------------------------------------------------------------------------------------

def test_a_start_is_thrown_rolls_without_the_logo_lands_on_the_tick_then_the_logo_the_frame_and_the_die_glows(gui):
    host = Host(play={**STARTING, "logo": LOGO})
    pg, errors = window(gui, host)
    d = die(pg)
    record_phases(pg)
    d.click()
    pane = pg.locator('.playpane[data-state="starting"]')
    pane.wait_for(timeout=WAIT_MS)
    pg.locator('.play-throw[data-phase="roll"]').wait_for(timeout=WAIT_MS)
    rolling = pg.locator(".playpane .ork-die.big.is-rolling")
    assert rolling.count() == 1 and rolling.evaluate("e => [e.offsetWidth, e.offsetHeight]") == [138, 144]                                    # orkUI's big die
    cube = rolling.locator(".ork-die__cube")
    assert cube.evaluate("e => getComputedStyle(e).animationName") == "ork-die-roll"                                                         # the cube tumbles in 3D
    poses = {cube.evaluate("e => getComputedStyle(e).transform") for _ in range(6) if pg.wait_for_timeout(45) is None}
    assert len(poses) >= 3 and all(p.startswith("matrix3d(") for p in poses)                                                                 # turned out of the screen's plane, pose after pose
    assert pg.locator(".play-die").evaluate("e => getComputedStyle(e).animationName") == "play-die-roll" and "rotate" not in pg.locator(".play-die").evaluate(
        "e => [...document.styleSheets].flatMap(s => { try { return [...s.cssRules]; } catch { return []; } }).find(r => r.name === 'play-die-roll')?.cssText || ''")      # the slot only drifts: no flat spin
    assert pg.locator(".play-logo").count() == 0 and pg.locator(".play-intro .play-title").count() == 0                                      # the logo is not shown while it starts
    assert "npm run dev" in pg.locator(".play-starting").inner_text() and pane.evaluate("e => getComputedStyle(e).backgroundColor") != "rgba(0, 0, 0, 0)"
    assert "is-gone" in d.get_attribute("class") and d.locator(".ork-die").evaluate("e => getComputedStyle(e).visibility") == "hidden"          # the hand's die is out on the pane
    box, pane_box = rolling.bounding_box(), pane.bounding_box()
    assert abs((box["x"] + box["width"] / 2) - (pane_box["x"] + pane_box["width"] / 2)) < 30 and pane_box["y"] < box["y"] < pane_box["y"] + pane_box["height"] / 2   # in the pane's middle
    shot(pg, "b112-rolling.png")
    host.play = {**PLAYING, "logo": LOGO}                                                                                                     # the page answers
    pg.locator('.play-throw[data-phase="ok"]').wait_for(timeout=WAIT_MS)
    landed = pg.locator(".playpane .ork-die.big")
    assert "face-ok" in landed.get_attribute("class") and "is-rolling" not in landed.get_attribute("class") and "face-5" not in landed.get_attribute("class")
    assert landed.evaluate("e => getComputedStyle(e).rotate") == "6deg"                                                                       # askew, the lean token the other way from the hand's
    assert "is-landing" in landed.get_attribute("class") and landed.locator(".ork-die__cube").evaluate("e => getComputedStyle(e).animationName") == "ork-die-land"     # the tick's face rolls in and the cube drops
    assert pg.locator(".play-landed").inner_text() == "It started" and pg.locator(".play-logo").count() == 0
    pg.wait_for_timeout(330)                                                                                                                  # the landing is over: it lies askew on its tick
    shot(pg, "b112-tick.png")
    pg.locator(".play-intro.has-logo .play-logo__img").wait_for(timeout=WAIT_MS)                                                              # today's intro: the logo
    assert pg.locator(".playpane .ork-die").count() == 0 and pg.locator(".play-intro .play-title").inner_text() == pg.locator(".play-title").inner_text()
    assert pg.locator(".play-starting").count() == 0
    shot(pg, "b112-logo.png")
    pg.wait_for_selector(".play-intro", state="detached", timeout=WAIT_MS)                                                                    # the fade, and the frame
    assert [p for p, _ in phases_seen(pg)] == ["fly", "roll", "ok", "ok-leave"] and dict(phases_seen(pg))["ok"] == "play-die-land" and dict(phases_seen(pg))["ok-leave"] == "play-die-fade"
    frame = pg.locator(".play-frame")
    assert frame.is_visible() and pg.locator(".playpane").get_attribute("data-state") == "playing" and pg.locator(".playpane").get_attribute("data-throw") is None
    assert pg.locator(".play-frame").count() == 1                                                                                             # the same iframe all through: never reloaded
    assert "is-gone" not in d.get_attribute("class") and "is-playing" in d.locator(".ork-die").get_attribute("class") and d.locator(".hand-die__word").inner_text() == "Playing"
    assert d.get_attribute("aria-label") == "Close the preview"
    shot(pg, "b112-frame.png")
    d.click()
    pg.wait_for_selector(".table-over", state="detached", timeout=WAIT_MS)
    assert "is-playing" not in d.locator(".ork-die").get_attribute("class") and d.locator(".hand-die__word").inner_text() == "Play"
    finish(pg, errors)


def interior_colors(pg):
    """How many colours the up face shows in a stretch free of pips, tick and edges, low on its left (a clean die: its one fill; seams: more). orkUI's die is a cube (0.24.0): the stretch is
    taken from the up face's own rectangle."""
    import io
    from PIL import Image
    x, y, w, h = pg.evaluate("() => { const r = document.querySelector('.play-die > .ork-die .ork-die__face.is-up').getBoundingClientRect(); return [r.x, r.y, r.width, r.height]; }")
    shot_ = Image.open(io.BytesIO(pg.screenshot())).convert("RGB")
    region = shot_.crop((round(x + 0.16 * w), round(y + 0.82 * h), round(x + 0.3 * w), round(y + 0.9 * h))).tobytes()
    return len({region[i:i + 3] for i in range(0, len(region), 3)})


def test_the_thrown_die_shows_no_seams_between_its_cells_while_it_rolls_and_on_the_tick(gui):
    """A scale on the die's ancestors (the flight once scaled it from half size) fixed its layer's raster at that scale: a grid of seams between its 6 px cells. The flight only moves and turns it, and it grows in whole cells; the cube
    (orkUI 0.24.0) draws its marks as background blocks, not pixels, so its up face stays one fill while it grows and when it lands."""
    pytest.importorskip("PIL")
    host = Host(play=STARTING)
    pg, errors = window(gui, host)
    die(pg).click()
    pg.locator('.play-throw[data-phase="roll"]').wait_for(timeout=WAIT_MS)
    pg.wait_for_timeout(500)
    pg.add_style_tag(content=".play-die, .play-die .ork-die__cube, .play-die .ork-die__face::after { animation: none !important; }")              # one pose, the cube at rest, so the stretch measured lies where it is expected
    pg.wait_for_timeout(250)
    assert interior_colors(pg) == 1
    host.play = PLAYING
    pg.locator('.play-throw[data-phase="ok"]').wait_for(timeout=WAIT_MS)
    pg.wait_for_timeout(340)                                                                                                                  # landed, askew by the lean token
    assert interior_colors(pg) <= 2
    finish(pg, errors)


def test_the_name_alone_comes_up_after_the_tick_when_the_project_has_no_logo(gui):
    host = Host(play=STARTING)
    pg, errors = window(gui, host)
    press(pg)
    pg.locator('.play-throw[data-phase="roll"]').wait_for(timeout=WAIT_MS)
    host.play = PLAYING
    pg.locator('.play-throw[data-phase="ok"]').wait_for(timeout=WAIT_MS)
    pg.locator(".play-intro:not(.play-throw) .play-title").wait_for(timeout=WAIT_MS)
    assert pg.locator(".play-logo").count() == 0 and pg.locator(".play-intro.has-logo").count() == 0
    pg.wait_for_selector(".play-intro", state="detached", timeout=WAIT_MS)
    assert pg.locator(".play-frame").is_visible()
    finish(pg, errors)


def test_a_start_that_fails_lands_on_the_cross_tips_over_and_todays_failure_takes_its_place(gui):
    host = Host(play=STARTING)
    pg, errors = window(gui, host)
    d = die(pg)
    record_phases(pg)
    d.click()
    pg.locator('.play-throw[data-phase="roll"]').wait_for(timeout=WAIT_MS)
    assert "is-gone" in d.get_attribute("class")
    host.play = FAILED
    pg.locator('.play-throw[data-phase="no"]').wait_for(timeout=WAIT_MS)
    landed = pg.locator(".playpane .ork-die.big")
    assert "face-no" in landed.get_attribute("class") and "is-rolling" not in landed.get_attribute("class") and pg.locator(".play-landed").inner_text() == "It did not start"
    assert pg.locator(".playpane").get_attribute("data-state") == "failed"
    pg.wait_for_timeout(330)
    shot(pg, "b112-cross.png")
    pg.locator(".play-error").wait_for(timeout=WAIT_MS)
    assert [p for p, _ in phases_seen(pg)] == ["fly", "roll", "no", "no-leave"] and dict(phases_seen(pg))["no-leave"] == "play-die-tip"        # it landed, then tipped over, then the failure
    assert pg.locator(".playpane .ork-die").count() == 0 and pg.locator(".play-throw").count() == 0
    assert pg.locator(".play-error").inner_text() == "The build would not start: npm run dev stopped (exit 1)" and "Cannot find module" in pg.locator(".play-tail__lines").inner_text()
    assert pg.locator(".playpane").get_attribute("data-state") == "failed" and pg.get_by_role("button", name="Open the build").count() == 1
    assert "is-gone" not in d.get_attribute("class") and "is-playing" not in d.locator(".ork-die").get_attribute("class")                      # the hand's die is back, not glowing
    shot(pg, "b112-failure.png")
    finish(pg, errors)


def test_a_build_already_playing_opens_at_once_with_no_throw_no_intro_and_the_die_wobbles_twice(gui):
    pg, errors = window(gui, Host(play={**PLAYING, "logo": LOGO}))
    pg.evaluate("() => { window.__wobbles = 0; document.addEventListener('animationstart', (ev) => { if (ev.animationName === 'ork-die-wobble') window.__wobbles++; }, true); }")
    die(pg).focus()
    pg.keyboard.press("Enter")                                                                                                                # no hover: only the warm start's wobbles count
    pg.locator('.table-over[data-kind="play"]').wait_for(timeout=WAIT_MS)
    pg.locator(".play-frame").wait_for(timeout=WAIT_MS)
    assert pg.locator(".play-intro").count() == 0 and pg.locator(".play-throw").count() == 0 and pg.locator(".playpane .ork-die").count() == 0 and pg.locator(".play-logo").count() == 0
    d = die(pg)
    assert "is-playing" in d.locator(".ork-die").get_attribute("class") and d.locator(".hand-die__word").inner_text() == "Playing" and "is-gone" not in d.get_attribute("class")
    pg.wait_for_function("() => window.__wobbles >= 2", timeout=WAIT_MS)
    pg.wait_for_timeout(900)
    assert pg.evaluate("() => window.__wobbles") == 2                                                                                         # twice, no more
    finish(pg, errors)


def test_pressing_the_die_starts_a_build_that_is_not_running_at_once_without_a_second_press(gui):
    host = Host(play={"state": "stopped"})
    pg, errors = window(gui, host)
    press(pg)
    pg.wait_for_function("() => true")
    pg.wait_for_timeout(300)
    asked = [a for n, a in host.log if n == "ideas.play"]
    assert {"peek": True} in asked and {} in asked, asked                                                                                    # it looked, then it started
    finish(pg, errors)


def test_a_start_stopped_while_it_rolls_ends_the_throw_and_brings_the_hands_die_back(gui):
    host = Host(play=STARTING)
    pg, errors = window(gui, host)
    d = die(pg)
    d.click()
    pg.locator('.play-throw[data-phase="roll"]').wait_for(timeout=WAIT_MS)
    host.play = {"state": "stopped"}
    pg.wait_for_selector(".play-throw", state="detached", timeout=WAIT_MS)
    assert "is-gone" not in d.get_attribute("class") and pg.get_by_role("button", name="Open the build").count() == 1
    finish(pg, errors)


def test_the_throw_starts_again_from_open_the_build_after_a_failure(gui):
    host = Host(play=FAILED)
    pg, errors = window(gui, host)
    press(pg)
    pg.get_by_role("button", name="Open the build").wait_for(timeout=WAIT_MS)
    host.play = STARTING
    pg.get_by_role("button", name="Open the build").click()
    pg.locator('.play-throw[data-phase="roll"]').wait_for(timeout=WAIT_MS)
    assert pg.locator(".playpane .ork-die.big.is-rolling").count() == 1
    finish(pg, errors)


# -- reduced motion -----------------------------------------------------------------------------------------------------------------------------------

def test_under_reduced_motion_it_is_todays_start_screen_with_no_die_on_the_pane_and_no_wobble(gui):
    host = Host(play={**STARTING, "logo": LOGO})
    pg, errors = window(gui, host, reduced_motion="reduce")
    d = die(pg)
    d.hover()
    assert pg.locator(".hand-die .ork-die.is-wobbling").count() == 0
    d.click()
    pg.locator('.playpane[data-state="starting"]').wait_for(timeout=WAIT_MS)
    pg.locator(".play-intro.has-logo .play-logo__img").wait_for(timeout=WAIT_MS)                                                              # the logo while it starts, as before
    assert pg.locator(".playpane .ork-die").count() == 0 and pg.locator(".play-throw").count() == 0 and pg.locator(".playpane").get_attribute("data-throw") is None
    assert "is-gone" not in d.get_attribute("class")
    assert "npm run dev" in pg.locator(".play-starting").inner_text()
    host.play = {**PLAYING, "logo": LOGO}
    pg.locator(".play-frame").wait_for(timeout=WAIT_MS)
    assert pg.locator(".play-intro").count() == 0 and pg.locator(".play-landed").count() == 0                                                 # no intro after it, as before
    assert "is-playing" in d.locator(".ork-die").get_attribute("class") and d.locator(".ork-die").evaluate("e => getComputedStyle(e, '::after').animationName") == NO_ANIMATION
    finish(pg, errors)


def test_under_reduced_motion_a_failure_is_todays_failure_at_once(gui):
    host = Host(play=STARTING)
    pg, errors = window(gui, host, reduced_motion="reduce")
    press(pg)
    pg.locator(".play-intro").wait_for(timeout=WAIT_MS)
    host.play = FAILED
    pg.locator(".play-error").wait_for(timeout=WAIT_MS)
    assert pg.locator(".playpane .ork-die").count() == 0
    finish(pg, errors)


# -- spec 113 part B: a project with no preview, the die sleeps -----------------------------------------------------------------------------------------

class PreviewHost(Host):
    """The table's host whose snapshot says how the project opens a preview (`preview`: "command" · "static" · ""; None leaves the key out, as before the first snapshot) and, since spec 118, the die's up face
    (`play_face`: "failed" · "new" · ""; None leaves the key out)."""

    def __init__(self, preview: str | None = "", play_face: str | None = None, **kw):
        super().__init__(**kw)
        self.preview = preview
        self.play_face = play_face

    def snapshot(self):
        doc = super().snapshot()
        if self.preview is not None:
            doc["state"]["preview"] = self.preview
        if self.play_face is not None:
            doc["state"]["play_face"] = self.play_face
        return doc


ASLEEP = "Nothing to play yet"
NOTHING = "Nothing here yet"


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_with_no_preview_the_die_sleeps_grey_and_still_and_says_nothing_to_play_yet(gui, width):
    host = PreviewHost("", play=STARTING)                                                                           # were it asked to start, it would
    pg, errors = window(gui, host, {"wide": WIDE, "narrow": {"width": 390, "height": 844}}[width])
    d, face = die(pg), die(pg).locator(".ork-die")
    assert "is-asleep" in d.get_attribute("class") and d.locator(".hand-die__word").inner_text() == "Play"
    assert d.get_attribute("title") == ASLEEP and d.get_attribute("aria-label") == f"{ASLEEP}: say how the project opens"
    assert face.evaluate("e => [getComputedStyle(e).filter, getComputedStyle(e).opacity]") == ["grayscale(1)", "0.4"]
    d.hover()
    pg.wait_for_timeout(150)
    assert pg.locator(".hand-die .ork-die.is-wobbling").count() == 0 and face.evaluate("e => getComputedStyle(e).transform") == "none" and face.evaluate("e => getComputedStyle(e).animationName") == NO_ANIMATION
    shot(pg, f"c113-die-asleep-{width}.png")
    d.click()                                                                                                       # pressed it opens the view that says so, with no throw
    pg.locator('.table-over[data-kind="play"]').wait_for(timeout=WAIT_MS)
    pg.locator('.playpane[data-state="none"]').wait_for(timeout=WAIT_MS)
    assert pg.locator(".assets-none__title").text_content() == NOTHING and "checks.toml" in pg.locator(".assets-none .arena-cap").text_content()
    pg.wait_for_timeout(700)                                                                                        # the throw would be in the air by now
    assert pg.locator(".play-throw").count() == 0 and pg.locator(".playpane .ork-die").count() == 0 and "is-gone" not in d.get_attribute("class")
    assert not [c for c in host.log if c[0] == "ideas.play"], "a project with no preview is not asked to start one"
    assert "is-playing" not in face.get_attribute("class") and d.locator(".hand-die__word").inner_text() == "Play"
    shot(pg, f"c113-die-asleep-pressed-{width}.png")
    d.click()                                                                                                       # and pressed again it closes the view, as the die always does
    pg.wait_for_selector(".table-over", state="detached", timeout=WAIT_MS)
    assert d.get_attribute("title") == ASLEEP
    finish(pg, errors)


@pytest.mark.parametrize("preview", ["command", "static", None])
def test_with_a_preview_or_before_the_first_snapshot_the_die_is_awake_as_before(gui, preview):
    host = PreviewHost(preview, play=PLAYING)
    pg, errors = window(gui, host)
    d = die(pg)
    assert "is-asleep" not in d.get_attribute("class") and d.get_attribute("title") == "Play: the project's preview of dev" and d.get_attribute("aria-label") == d.get_attribute("title")
    assert d.locator(".ork-die").evaluate("e => [getComputedStyle(e).filter, getComputedStyle(e).opacity]") == ["none", "1"]
    d.click()
    pg.locator(".play-frame").wait_for(timeout=WAIT_MS)                                                             # opens the preview, not the empty view
    assert pg.locator('.playpane[data-state="none"]').count() == 0
    finish(pg, errors)


def test_the_die_wakes_when_the_snapshot_says_the_project_has_a_preview_now(gui):
    host = PreviewHost("")
    pg, errors = window(gui, host)
    assert "is-asleep" in die(pg).get_attribute("class")
    host.preview = "command"
    host.push()
    pg.wait_for_function("() => !document.querySelector('.hand-die').classList.contains('is-asleep')", timeout=WAIT_MS)
    assert die(pg).get_attribute("title") == "Play: the project's preview of dev"
    finish(pg, errors)


# -- spec 118 part C: the die's up face ---------------------------------------------------------------------------------------------------------------

FAILED_WORDS = "Play: it did not start last time"
NEW_WORDS = "Play: dev has changed since you last played"
TODAYS_WORDS = "Play: the project's preview of dev"


def face_of(pg):
    return pg.locator(".hand-die .ork-die").get_attribute("class").split()


def watch_landing(pg):
    """Notes whether the hand's die ever wears `is-landing` (a landing of 300 ms is too short to wait for with a poll)."""
    pg.evaluate("""() => { window.__landed = false; const d = document.querySelector('.hand-die .ork-die'), note = () => { if (document.querySelector('.hand-die .ork-die.is-landing')) window.__landed = true; };
      new MutationObserver(note).observe(document.querySelector('.hand-die'), { subtree: true, attributes: true, attributeFilter: ['class'], childList: true }); note(); }""")


@pytest.mark.parametrize("play_face, face, words", [("failed", "face-no", FAILED_WORDS), ("new", "face-new", NEW_WORDS), ("", "face-5", TODAYS_WORDS), (None, "face-5", TODAYS_WORDS)])
def test_the_die_wears_the_face_the_snapshot_says_and_says_it_in_words(gui, play_face, face, words):
    pg, errors = window(gui, PreviewHost("command", play_face))
    d = die(pg)
    classes = face_of(pg)
    assert face in classes and len([c for c in classes if c.startswith("face-")]) == 1
    assert d.get_attribute("title") == words and d.get_attribute("aria-label") == words and d.locator(".hand-die__word").inner_text() == "Play"
    assert "is-landing" not in classes                                                                                # the first snapshot rolls nothing
    shot(pg, f"c118-die-{play_face or 'five'}.png")
    finish(pg, errors)


def test_while_the_view_is_open_the_die_says_close_the_preview_whatever_its_face(gui):
    pg, errors = window(gui, PreviewHost("command", "failed", play=PLAYING))
    d = die(pg)
    d.click()
    pg.locator('.table-over[data-kind="play"]').wait_for(timeout=WAIT_MS)
    assert d.get_attribute("aria-label") == "Close the preview" and d.get_attribute("title") == "Close the preview"
    assert "face-no" in face_of(pg)
    finish(pg, errors)


def test_the_cube_rolls_onto_a_new_face_and_the_landing_is_taken_off_after(gui):
    host = PreviewHost("command", "")
    pg, errors = window(gui, host)
    assert "face-5" in face_of(pg) and "is-landing" not in face_of(pg)
    watch_landing(pg)
    host.play_face = "new"
    host.push()
    pg.wait_for_function("() => document.querySelector('.hand-die .ork-die').classList.contains('face-new')", timeout=WAIT_MS)
    pg.wait_for_function("() => window.__landed === true", timeout=WAIT_MS)
    pg.wait_for_function("() => !document.querySelector('.hand-die .ork-die.is-landing')", timeout=WAIT_MS)             # taken off at the cube's animationend
    assert "face-new" in face_of(pg) and die(pg).get_attribute("title") == NEW_WORDS
    watch_landing(pg)                                                                                                   # and again, onto the cross
    host.play_face = "failed"
    host.push()
    pg.wait_for_function("() => document.querySelector('.hand-die .ork-die').classList.contains('face-no')", timeout=WAIT_MS)
    pg.wait_for_function("() => window.__landed === true", timeout=WAIT_MS)
    pg.wait_for_function("() => !document.querySelector('.hand-die .ork-die.is-landing')", timeout=WAIT_MS)
    assert die(pg).get_attribute("aria-label") == FAILED_WORDS
    finish(pg, errors)


def test_a_snapshot_that_keeps_the_face_rolls_nothing(gui):
    host = PreviewHost("command", "new")
    pg, errors = window(gui, host)
    watch_landing(pg)
    host.push()
    pg.wait_for_timeout(400)
    assert pg.evaluate("() => window.__landed") is False and "face-new" in face_of(pg)
    finish(pg, errors)


def test_under_reduced_motion_the_face_changes_with_no_landing(gui):
    host = PreviewHost("command", "")
    pg, errors = window(gui, host, reduced_motion="reduce")
    watch_landing(pg)
    host.play_face = "new"
    host.push()
    pg.wait_for_function("() => document.querySelector('.hand-die .ork-die').classList.contains('face-new')", timeout=WAIT_MS)
    pg.wait_for_timeout(500)
    assert pg.evaluate("() => window.__landed") is False and "is-landing" not in face_of(pg)
    finish(pg, errors)


def test_asleep_wins_over_the_face_and_a_face_said_asleep_rolls_nothing(gui):
    host = PreviewHost("", "failed")
    pg, errors = window(gui, host)
    d = die(pg)
    assert "face-5" in face_of(pg) and "face-no" not in face_of(pg) and "is-asleep" in d.get_attribute("class")
    assert d.get_attribute("title") == ASLEEP and d.get_attribute("aria-label") == f"{ASLEEP}: say how the project opens"
    watch_landing(pg)
    host.play_face = "new"
    host.push()
    pg.wait_for_timeout(500)
    assert "face-5" in face_of(pg) and pg.evaluate("() => window.__landed") is False and d.get_attribute("title") == ASLEEP
    finish(pg, errors)


def test_a_hover_wobble_and_a_landing_do_not_run_together(gui):
    host = PreviewHost("command", "")
    pg, errors = window(gui, host)
    d = die(pg)
    d.hover()
    pg.locator(".hand-die .ork-die.is-wobbling").wait_for(timeout=WAIT_MS)
    host.play_face = "failed"
    host.push()
    pg.wait_for_function("() => document.querySelector('.hand-die .ork-die').classList.contains('face-no')", timeout=WAIT_MS)
    assert pg.evaluate("() => { const c = document.querySelector('.hand-die .ork-die').classList; return !(c.contains('is-wobbling') && c.contains('is-landing')); }")
    pg.wait_for_function("() => !document.querySelector('.hand-die .ork-die.is-wobbling')", timeout=WAIT_MS)
    assert "is-landing" not in face_of(pg)                                                                              # the landing was skipped while it wobbled
    finish(pg, errors)
