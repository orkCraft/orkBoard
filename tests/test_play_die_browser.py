"""Spec 112 part B (docs/specs/112-the-bars-marks-and-the-play-die.md §3, decisions §190), Chromium against the table's stub host (tests/test_owners_day_desktop_browser.py `Host`, whose Play answers what a test sets).

The bar: New party is orkUI's empty chair (pulled out on hover, not under reduced motion; spec 123 §7.5, it was the banner); Stop all is no door of it any more but the die's front face (spec 139 A, decisions §246: two buttons in the die, the front's mark in the danger colour only while a task runs). Play is no button of the pane's head but a die in the hand, left of the potions, its word under it, turned by the lean token;
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
    die(pg).locator(".hand-die__play").click()
    pg.locator('.table-over[data-kind="play"]').wait_for(timeout=WAIT_MS)


def window(gui, host, width=WIDE, errors=None, cards=True, **ctx):
    errors = [] if errors is None else errors
    pg = start(gui, width, errors, host, **ctx)
    if cards:
        pg.locator(".cards-lane").first.wait_for(timeout=WAIT_MS)
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





# -- Stop all (spec 168 A4, decisions §285.2: from 760 px up under the lamp's chain in the right column's head, `.rh-stop`, so it can be pressed while a card is lifted; under 760 px, where there is no such column, still in words under the die, spec 156 E.2–E.3,
# decisions §261.12; it was the die's front face, spec 139 A, decisions §246) ------------------------------------------------



def token(pg, name):
    return pg.evaluate("(n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim()", name)


def paint(pg, c):
    return pg.evaluate("(c) => { const i = document.createElement('i'); i.style.color = c; document.body.append(i); const v = getComputedStyle(i).color; i.remove(); return v; }", c)


def stop_of(pg):
    """The Stop all button: the right column's head's at the wide width, the die's under 760 px."""
    return pg.locator(".release-lane__head .rh-stop" if pg.viewport_size["width"] >= 760 else ".hand-die__stop")


def nothing_runs(host):
    host.nodes = [n for n in host.nodes if not n.get("tasks")]
    host.rev += 1
    host.ws.send(__import__("json").dumps(host.snapshot()))






def test_a_press_on_stop_all_sends_halt_and_the_button_is_gone_until_work_starts(gui):
    host = Host(n=3)
    pg, errors = window(gui, host)
    d = die(pg)
    pg.wait_for_function("() => document.querySelector('.hand-die.is-orks-running')", timeout=WAIT_MS)
    stop_of(pg).click()
    pg.wait_for_function("() => !document.querySelector('.hand-die.is-orks-running')", timeout=WAIT_MS)
    assert [c for c in host.log if c[0] == "halt"] == [("halt", {})]
    assert pg.locator('.table-over[data-kind="play"]').count() == 0, "Stop all is not Play"
    nothing_runs(host)                                                                                                       # the map is seen with none at work ...
    pg.wait_for_timeout(300)
    assert pg.locator(".rh-stop:not(.is-resume)").count() == 0 and d.locator(".hand-die__stop:not(.is-resume)").count() == 0, "no Stop all while stopped"
    pg.evaluate("() => import('/static/js/board/store.js').then((m) => m.ask('ideas.add', { text: 'A new goal' }))")                  # a goal is started from this page: Stopped goes
    pg.wait_for_function("() => !document.querySelector('.hand-die__stopped') && !document.querySelector('.hand-die.is-orks-stopped')", timeout=WAIT_MS)
    finish(pg, errors)


def test_the_play_press_does_not_halt_and_the_stop_press_opens_no_preview(gui):
    host = Host(n=3, play=PLAYING)
    pg, errors = window(gui, host)
    pg.wait_for_function("() => document.querySelector('.hand-die.is-orks-running')", timeout=WAIT_MS)
    press(pg)
    assert not [c for c in host.log if c[0] == "halt"]
    die(pg).locator(".hand-die__play").click()
    pg.wait_for_selector(".table-over", state="detached", timeout=WAIT_MS)
    stop_of(pg).click()
    pg.wait_for_function("() => !document.querySelector('.hand-die.is-orks-running')", timeout=WAIT_MS)
    assert pg.locator(".table-over").count() == 0
    finish(pg, errors)


# -- the die in the hand ------------------------------------------------------------------------------------------------------------------------------









# -- the throw ----------------------------------------------------------------------------------------------------------------------------------------









def test_a_start_that_fails_lands_on_the_cross_tips_over_and_todays_failure_takes_its_place(gui):
    host = Host(play=STARTING)
    pg, errors = window(gui, host)
    d = die(pg)
    record_phases(pg)
    d.locator(".hand-die__play").click()
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
    die(pg).locator(".hand-die__play").focus()
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





# -- spec 113 part B: a project with no preview, the die sleeps -----------------------------------------------------------------------------------------

class PreviewHost(Host):
    """The table's host whose snapshot says how the project opens a preview (`preview`: "command" · "static" · ""; None leaves the key out, as before the first snapshot) and, since spec 118, the die's up face
    (`play_face`: "failed" · "new" · ""; None leaves the key out)."""

    def __init__(self, preview: str | None = "", play_face: str | None = None, new_n: int | None = None, **kw):
        super().__init__(**kw)
        self.preview = preview
        self.play_face = play_face
        self.new_n = new_n                                                                                              # decisions §200.5: the goals landed in dev since the last play (None leaves the key out)

    def snapshot(self):
        doc = super().snapshot()
        if self.preview is not None:
            doc["state"]["preview"] = self.preview
        if self.play_face is not None:
            doc["state"]["play_face"] = self.play_face
        if self.new_n is not None:
            doc["state"]["new_n"] = self.new_n
        return doc


ASLEEP = "Nothing to play yet"
NOTHING = "Nothing here yet"


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_with_no_preview_the_die_sleeps_grey_and_still_and_says_nothing_to_play_yet(gui, width):
    host = PreviewHost("", play=STARTING)                                                                           # were it asked to start, it would
    pg, errors = window(gui, host, {"wide": WIDE, "narrow": {"width": 390, "height": 844}}[width])
    d, face = die(pg), die(pg).locator(".ork-die")
    assert "is-asleep" in d.get_attribute("class") and d.locator(".hand-die__word").inner_text() == "Play"
    assert d.locator(".hand-die__play").get_attribute("title") == ASLEEP and d.locator(".hand-die__play").get_attribute("aria-label") == f"{ASLEEP}: say how the project opens"
    d.locator(".hand-die__play").hover()
    pg.wait_for_timeout(150)
    shot(pg, f"c113-die-asleep-{width}.png")
    d.locator(".hand-die__play").click()                                                                                                       # pressed it opens the view that says so, with no throw
    pg.locator('.table-over[data-kind="play"]').wait_for(timeout=WAIT_MS)
    pg.locator('.playpane[data-state="none"]').wait_for(timeout=WAIT_MS)
    assert pg.locator(".assets-none__title").text_content() == NOTHING and "checks.toml" in pg.locator(".assets-none .arena-cap").text_content()
    pg.wait_for_timeout(700)                                                                                        # the throw would be in the air by now
    assert pg.locator(".play-throw").count() == 0 and pg.locator(".playpane .ork-die").count() == 0 and "is-gone" not in d.get_attribute("class")
    assert not [c for c in host.log if c[0] == "ideas.play"], "a project with no preview is not asked to start one"
    assert "is-playing" not in face.get_attribute("class") and d.locator(".hand-die__word").inner_text() == "Play"
    shot(pg, f"c113-die-asleep-pressed-{width}.png")
    d.locator(".hand-die__play").click()                                                                                                       # and pressed again it closes the view, as the die always does
    pg.wait_for_selector(".table-over", state="detached", timeout=WAIT_MS)
    assert d.locator(".hand-die__play").get_attribute("title") == ASLEEP
    finish(pg, errors)






# -- spec 118 part C: the die's up face ---------------------------------------------------------------------------------------------------------------































# -- Stopped and Resume (spec 139 B.3, decisions §246.3) ------------------------------------------------------------------------------------------------

class StopHost(Host):
    """A host that keeps *stopped* as the real one does: the snapshot carries it, `halt` sets it and `resume` clears it."""

    def __init__(self, **kw):
        super().__init__(**kw)
        self.stopped = False

    def snapshot(self):
        snap = super().snapshot()
        snap["state"]["stopped"] = self.stopped
        return snap

    def handle(self, name, a):
        if name in ("halt", "resume"):
            self.log.append((name, a))
            self.stopped = name == "halt"
            if name == "halt":
                self.nodes = [n for n in self.nodes if not n.get("tasks")]
            self.push()
            return 0
        return super().handle(name, a)


def test_the_button_says_resume_while_stopped_sends_resume_and_goes_back_to_stop_all(gui):
    host = StopHost(n=3)
    pg, errors = window(gui, host)
    d = die(pg)
    stop = stop_of(pg)
    assert stop.inner_text() == "Stop all" and stop.get_attribute("aria-label").startswith("Stop all")
    stop.click()
    pg.wait_for_function("() => document.querySelector('.rh-stop')?.textContent === 'Resume'", timeout=WAIT_MS)
    cls = d.locator(".ork-die").get_attribute("class")
    assert "front-stop" not in cls and "front-resume" not in cls and "is-turning" not in cls, "a die's face again: no mark, no turn"
    assert stop.get_attribute("aria-label") == "Resume: the orks go back to work" and stop.get_attribute("aria-disabled") is None and stop.evaluate("e => e.tagName") == "BUTTON"
    assert d.locator(".hand-die__word").inner_text() == "Play" and "is-orks-stopped" in d.get_attribute("class")
    shot(pg, "e156-die-resume.png")
    stop.click()
    pg.wait_for_function("() => !document.querySelector('.hand-die.is-orks-stopped')", timeout=WAIT_MS)             # the stub's halt took the tasks and its resume gives none back: Resume is gone and no Stop all stands for a run
    assert [c[0] for c in host.log if c[0] in ("halt", "resume")] == ["halt", "resume"]
    assert stop_of(pg).count() == 0 and d.locator(".hand-die__stop").count() == 0
    finish(pg, errors)




def test_stop_all_can_be_pressed_while_a_card_is_lifted_and_the_hand_is_inert(gui):
    """Spec 168 A4 (decisions §285.2): Stop all is the right column's, not the hand's: a failure lifted sinks the hand's row (`inert`), Stop all stays live."""
    host = Host(n=3)
    pg, errors = window(gui, host)
    pg.wait_for_function("() => document.querySelector('.hand-die.is-orks-running')", timeout=WAIT_MS)
    pg.locator('.hand-card[data-kind="failed"]').first.click(position={"x": 10, "y": 24})                                      # a failure: it rises and the rest of the hand sinks
    pg.locator(".hand-lifted").wait_for(timeout=WAIT_MS)
    assert pg.locator(".hand-row").get_attribute("inert") is not None, "the hand's row is inert while a card is lifted"
    assert pg.locator(".rh-stop").evaluate("e => e.closest('[inert]') === null"), "Stop all is outside it"
    pg.locator(".rh-stop").click()
    for _ in range(40):
        if ("halt", {}) in host.log:
            break
        pg.wait_for_timeout(50)
    assert ("halt", {}) in host.log
    finish(pg, errors)
