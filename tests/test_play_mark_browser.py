"""Spec 115 part E (docs/specs/115-the-live-product-under-each-leaders-eyes.md §6.4–§6.5; mockup docs/mockups/play-lenses/ states 4–8), Chromium against the table's stub host and a made-up dev server through the probe's proxy (the harness is
tests/test_play_lens_browser.py's).

**Mark** in the bar (and the key `M`; Esc cancels) lays a still layer over the frame (*Draw a box or press a part* · *Cancel*); a drag draws the dashed box, a press takes the rectangle of the first element under it; the field beside the box,
inside the pane: the line, the kinds, *→ <Party> ×*, *With:* and its chips (each with its ×), *Add to "<goal>"* when the host offers one, **Send**; the page asks the probe for its picture and its state, then `ideas.play_mark`; sent, the box
stays a moment in the goal's element's colour, the bar says *Sent to <Party>: <title>*, Play stays open; a canvas under the box (the game's state, *At which step?* under Game design's tab); a hint made into a goal; a Play with no probe;
reduced motion (the sent box's moment is still). Screenshots to the directory ORKCRAFT_SHOTS_DIR names when set."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_play_lens_browser import MAIN, SNOOZE, WATERED, bare, finish, frame_box, open_play, rect_of, rig, shot, strip_text, wait_place  # noqa: E402,F401

pytestmark = pytest.mark.browser

DRAG = (170, 215, 250, 250)                                                                               # a box over *Snooze*, in the frame's pixels


def mark_button(pg):
    return pg.get_by_role("button", name="Mark", exact=True)


def stage(pg) -> dict:
    return pg.locator(".play-stage").evaluate("e => ({w: e.clientWidth, h: e.clientHeight})")


def drag(pg, box=DRAG):
    """A drag over the frame, in its own pixels."""
    f = frame_box(pg)
    x0, y0, x1, y1 = box
    pg.mouse.move(f["x"] + x0, f["y"] + y0)
    pg.mouse.down()
    pg.mouse.move(f["x"] + (x0 + x1) / 2, f["y"] + (y0 + y1) / 2, steps=3)
    pg.mouse.move(f["x"] + x1, f["y"] + y1, steps=3)
    pg.mouse.up()
    pg.locator(".play-field").wait_for(timeout=WAIT_MS)


def press_at(pg, x, y):
    f = frame_box(pg)
    pg.mouse.click(f["x"] + x, f["y"] + y)
    pg.locator(".play-field").wait_for(timeout=WAIT_MS)




def chips(pg) -> list[str]:
    return [" ".join(c.inner_text().split()).rstrip(" ×") for c in pg.locator(".play-field .play-with").all()]


def kinds(pg) -> dict:
    return pg.evaluate("() => Object.fromEntries([...document.querySelectorAll('.play-field [role=radio][data-kind]')].map((e) => [e.textContent.trim(), e.getAttribute('aria-checked')]))")


def type_line(pg, text="Watered shows an error on the second plant."):
    pg.locator(".play-field textarea").fill(text)


def send(pg, host, n=1):
    pg.get_by_role("button", name="Send", exact=True).click()
    pg.wait_for_function("() => document.querySelector('.play-say.is-sent')", timeout=WAIT_MS)
    assert len(host.marks) == n
    return host.marks[-1]


def watch_sent(pg):
    """Records the sent box the moment it appears (it stays 1.2 s: a test under load must not race it): `window.__sent` is its element, its border colour, its animation, its box and its opacity."""
    pg.evaluate("""() => { const f = document.querySelector('.play-frame').getBoundingClientRect();
      new MutationObserver(() => { const e = document.querySelector('.play-sent'); if (!e || window.__sent) return; const s = getComputedStyle(e), b = e.getBoundingClientRect();
        window.__sent = { elem: e.dataset.elem, colour: s.borderTopColor, animation: s.animationName, opacity: s.opacity, x: Math.round(b.left - f.left), y: Math.round(b.top - f.top) }; })
        .observe(document.body, { subtree: true, childList: true }); }""")


def colour(pg, token: str) -> str:
    return pg.evaluate("(t) => { const e = document.createElement('i'); e.style.color = `var(${t})`; document.body.append(e); const c = getComputedStyle(e).color; e.remove(); return c; }", token)


# -- Mark and Cancel ----------------------------------------------------------------------------------------------------------------------------------



# -- the box and the field ----------------------------------------------------------------------------------------------------------------------------







# -- sending ----------------------------------------------------------------------------------------------------------------------------------------

def test_send_asks_the_probe_for_its_picture_and_state_makes_the_goal_and_the_box_stays_a_moment_in_its_elements_colour(gui, rig):
    pg, errors = open_play(gui, rig.host, "tech")
    mark_button(pg).click()
    drag(pg)
    type_line(pg)
    watch_sent(pg)
    sent = send(pg, rig.host)
    size = stage(pg)
    assert sent["text"] == "Watered shows an error on the second plant." and sent["kind"] == "bug" and sent["party"] == "tech" and sent["path"] == "/today" and "add_to" not in sent
    assert sent["viewport"] == {"w": size["w"], "h": size["h"]}
    for key, want in (("x", DRAG[0] / size["w"]), ("y", DRAG[1] / size["h"]), ("w", (DRAG[2] - DRAG[0]) / size["w"]), ("h", (DRAG[3] - DRAG[1]) / size["h"])):
        assert abs(sent["box"][key] - want) < 0.003, (key, sent["box"], size)                                       # the box in shares of the frame
    assert sorted(sent["with"]) == ["lines", "part", "screen", "state"] and sent["state"] == {"level": 3, "gold": 40}
    assert "<html" in sent["picture"]["html"] and "Needs you" in sent["picture"]["html"] and sent["picture"]["w"] > 0 and "<script" not in sent["picture"]["html"]
    assert any(u["selector"].endswith("#snooze") for u in sent["under"])
    assert pg.locator(".play-say.is-sent").inner_text().strip() == "Sent to Tech: Watered fails"
    seen = pg.evaluate("() => window.__sent")
    assert seen["elem"] == "lava" and seen["colour"] == colour(pg, "--ork-elem-lava") and abs(seen["x"] - DRAG[0]) <= 1 and abs(seen["y"] - DRAG[1]) <= 1 and seen["animation"] == "play-sent"
    assert pg.locator(".play-field").count() == 0 and pg.locator(".play-still").count() == 0 and pg.locator('.table-over[data-kind="play"] .play-frame').count() == 1        # Play stays open
    assert pg.get_by_role("button", name="Mark", exact=True).get_attribute("aria-pressed") == "false"
    shot(pg, "e115-mark-sent.png")
    pg.wait_for_selector(".play-sent", state="detached", timeout=WAIT_MS)                                           # about a second and a fifth
    assert sum(1 for n, _ in rig.host.log if n == "ideas.map") >= 2                                                    # the Board is read again: the goal is in the first lane as a new goal is
    finish(pg, errors)


def test_a_failed_send_says_why_in_the_field_and_keeps_what_was_written(gui, rig):
    rig.host.refuse = {"ideas.play_mark": "That goal has started: send the mark as a goal of its own"}
    pg, errors = open_play(gui, rig.host, "tech")
    mark_button(pg).click()
    drag(pg)
    type_line(pg)
    pg.get_by_role("button", name="Send", exact=True).click()
    pg.locator(".play-field__error").wait_for(timeout=WAIT_MS)
    assert pg.locator(".play-field__error").inner_text() == "That goal has started: send the mark as a goal of its own" and pg.locator(".play-field textarea").input_value() == "Watered shows an error on the second plant."
    assert pg.get_by_role("button", name="Send", exact=True).is_enabled() and pg.locator(".play-say.is-sent").count() == 0
    finish(pg, errors)








# -- a hint made into a goal -------------------------------------------------------------------------------------------------------------------------



# -- a game -----------------------------------------------------------------------------------------------------------------------------------------



# -- no probe ---------------------------------------------------------------------------------------------------------------------------------------



# -- reduced motion ---------------------------------------------------------------------------------------------------------------------------------



# -- the narrow width -------------------------------------------------------------------------------------------------------------------------------

