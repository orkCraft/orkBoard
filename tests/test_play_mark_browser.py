"""Spec 115 part E (docs/specs/115-the-live-product-under-each-leaders-eyes.md §6.4–§6.5; mockup docs/mockups/play-lenses/ states 4–8), Chromium against the table's stub host and a made-up dev server through the probe's proxy (the harness is
tests/test_play_lens_browser.py's).

**Mark** in the bar (and the key `M`; Esc cancels) lays a still layer over the frame (*Draw a box or press a part* · *Cancel*); a drag draws the dashed box, a press takes the rectangle of the first element under it; the field beside the box,
inside the pane: the line, the kinds, *→ <Party> ×*, *With:* and its chips (each with its ×), *Add to "<goal>"* when the host offers one, **Send**; the page asks the probe for its picture and its state, then `ideas.play_mark`; sent, the box
stays a moment in the goal's element's colour, the bar says *Sent to <Party>: <title>*, Play stays open; a canvas under the box (the game's state, *At which step?* under Game design's tab); a hint made into a goal; a Play with no probe;
reduced motion (the sent box's moment is still). Screenshots to the directory ORKCRAFT_SHOTS_DIR names when set."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_play_lens_browser import MAIN, SNOOZE, WATERED, bare, finish, frame_box, open_play, rect_of, rig, shot, strip_text, wait_place  # noqa: E402,F401
from tests.test_table_desktop_browser import open_tab  # noqa: E402

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


def box_of(pg) -> dict:
    return rect_of(pg, pg.locator(".play-box"))


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

def test_mark_lays_a_still_layer_saying_draw_a_box_and_cancel_esc_and_the_key_m_each_leave_play_open(gui, rig):
    pg, errors = open_play(gui, rig.host, "tech")
    button = mark_button(pg)
    assert button.get_attribute("aria-keyshortcuts") == "M" and button.locator("kbd").inner_text() == "M" and button.get_attribute("aria-pressed") == "false"
    button.click()
    assert pg.locator(".play-bar").inner_text().count("Draw a box or press a part") == 1 and pg.get_by_role("button", name="Cancel", exact=True).count() == 1
    assert button.get_attribute("aria-pressed") == "true" and "is-on" in button.get_attribute("class")
    f = frame_box(pg)
    assert pg.evaluate("([x, y]) => document.elementFromPoint(x, y).className", [f["x"] + 100, f["y"] + 100]) == "play-still"        # the product takes no press now
    shot(pg, "e115-mark-still.png")
    pg.get_by_role("button", name="Cancel", exact=True).click()
    assert pg.locator(".play-still").count() == 0 and pg.locator(".play-frame").count() == 1
    pg.keyboard.press("m")                                                                                          # the key starts it, Esc cancels it: the pane's own Esc (which would close Play) does not
    pg.locator(".play-still").wait_for(timeout=WAIT_MS)
    pg.keyboard.press("Escape")
    assert pg.locator(".play-still").count() == 0 and pg.locator('.table-over[data-kind="play"] .play-frame').count() == 1
    pg.keyboard.press("m")
    pg.locator(".play-still").wait_for(timeout=WAIT_MS)
    drag(pg)
    pg.locator(".play-field textarea").press("Escape")                                                               # Esc in the field cancels the mark too, not Play
    assert pg.locator(".play-field").count() == 0 and pg.locator(".play-still").count() == 0 and pg.locator(".play-frame").count() == 1
    pg.keyboard.press("Escape")                                                                                      # and with nothing to cancel it is the pane's again: it closes Play
    pg.wait_for_selector(".table-over", state="detached", timeout=WAIT_MS)
    finish(pg, errors)


# -- the box and the field ----------------------------------------------------------------------------------------------------------------------------

def test_a_drag_draws_the_dashed_box_and_the_field_opens_beside_it_inside_the_pane_with_its_chips(gui, rig):
    pg, errors = open_play(gui, rig.host, "tech")
    mark_button(pg).click()
    drag(pg)
    box = pg.locator(".play-box")
    assert box.evaluate("e => getComputedStyle(e).borderStyle") == "dashed" and abs(box_of(pg)["x"] - DRAG[0]) <= 1 and abs(box_of(pg)["w"] - (DRAG[2] - DRAG[0])) <= 1 and abs(box_of(pg)["h"] - (DRAG[3] - DRAG[1])) <= 1
    field = pg.locator(".play-field")
    fb, pane, hand = field.bounding_box(), pg.locator("#table-pane").bounding_box(), pg.locator(".hand").bounding_box()
    assert fb["x"] >= pane["x"] and fb["x"] + fb["width"] <= pane["x"] + pane["width"] and fb["y"] + fb["height"] <= hand["y"] and fb["x"] >= box.bounding_box()["x"] + box.bounding_box()["width"]      # inside the pane, never over the hand, beside the box
    assert field.locator("textarea").evaluate("e => e === document.activeElement")
    assert kinds(pg) == {"Bug": "true", "Looks wrong": "false", "Missing": "false", "Confusing": "false"}                  # under Tech's tab a bug first
    assert " ".join(field.locator(".play-to").inner_text().split()) == "→ Tech ×" and field.locator(".play-to .ork-race__head").count() == 1
    pg.wait_for_function("() => document.querySelectorAll('.play-field .play-with').length >= 4", timeout=WAIT_MS)
    assert chips(pg) == ["the screen: Today", "the part: web/src/components", "the server's last lines", "the game's state"]          # no error and no failed request yet: no chip for them
    assert pg.locator(".play-field .play-addto").count() == 0 and pg.get_by_role("button", name="Send", exact=True).is_disabled()      # no line yet: nothing to send
    type_line(pg)
    assert pg.get_by_role("button", name="Send", exact=True).is_enabled()
    shot(pg, "e115-mark-field.png")
    pg.get_by_role("radio", name="Looks wrong").click()
    assert kinds(pg)["Looks wrong"] == "true" and kinds(pg)["Bug"] == "false"
    pg.get_by_role("radio", name="Looks wrong").press("ArrowRight")                                                  # the kinds are one radio group: arrows move through it
    assert kinds(pg)["Missing"] == "true"
    finish(pg, errors)


def test_a_press_takes_the_rectangle_of_the_first_element_under_it(gui, rig):
    pg, errors = open_play(gui, rig.host, "tech")
    mark_button(pg).click()
    press_at(pg, WATERED["x"] + 10, WATERED["y"] + 10)
    assert box_of(pg) == WATERED and pg.locator(".play-box").evaluate("e => getComputedStyle(e).borderStyle") == "dashed"
    assert "the part: web/src/components" in chips(pg)
    type_line(pg)
    mark = send(pg, rig.host)
    assert mark["under"][0]["selector"].endswith("#watered") and mark["under"][0]["file"] == "web/src/ui/Button.tsx"
    finish(pg, errors)


def test_the_chips_count_the_pages_errors_and_failed_requests_and_each_takes_off_with_its_cross(gui, rig):
    pg, errors = open_play(gui, rig.host, "tech")
    inside = pg.frame_locator(".play-frame")
    inside.locator("#boom").click()                                                                                  # the probe hears an error and a failed request
    inside.locator("#fail").click()
    pg.wait_for_timeout(300)
    mark_button(pg).click()
    drag(pg)
    assert "1 error" in chips(pg) and "1 failed request" in chips(pg)
    assert "It reproduces" in pg.locator(".play-field").inner_text()                                                 # a bug with its failure takes the short way
    chip = pg.locator('.play-with[data-with="errors"]')
    assert chip.get_attribute("aria-pressed") == "true"
    chip.click()
    assert chip.get_attribute("aria-pressed") == "false" and "is-off" in chip.get_attribute("class")
    pg.locator('.play-with[data-with="lines"]').click()
    type_line(pg)
    mark = send(pg, rig.host)
    assert sorted(mark["with"]) == ["part", "requests", "screen", "state"]                                           # what was taken off is not sent
    pg.wait_for_timeout(2300)                                                                                         # the probe's events reach the host in batches
    assert {e["event"] for e in rig.host.events} >= {"error", "request", "press"}
    finish(pg, errors)


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


def test_a_goal_not_started_with_a_mark_of_this_kind_here_is_offered_ticked_and_send_adds_to_it(gui, rig):
    rig.host.offer = {"slug": "bigger-targets", "title": "Bigger touch targets"}
    pg, errors = open_play(gui, rig.host, "art")
    mark_button(pg).click()
    press_at(pg, WATERED["x"] + 10, WATERED["y"] + 10)
    assert kinds(pg)["Looks wrong"] == "true"                                                                         # under Design's tab the first kind is how it looks
    offer = pg.locator(".play-addto")
    offer.wait_for(timeout=WAIT_MS)
    assert 'Add to "Bigger touch targets"' in offer.inner_text() and offer.locator("input").is_checked()
    assert ("ideas.play_mark_offer", {"path": "/today", "kind": "looks"}) in rig.host.calls
    shot(pg, "e115-mark-add-to.png")
    type_line(pg, "Watered looks like a tag, not the main action.")
    assert send(pg, rig.host)["add_to"] == "bigger-targets"
    pg.wait_for_selector(".play-sent", state="detached", timeout=WAIT_MS)
    mark_button(pg).click()                                                                                           # unticked, the mark is a goal of its own
    press_at(pg, WATERED["x"] + 10, WATERED["y"] + 10)
    pg.locator(".play-addto input").uncheck()
    type_line(pg)
    assert "add_to" not in send(pg, rig.host, 2)
    finish(pg, errors)


def test_the_kind_asks_the_host_again_and_a_kind_with_no_offer_has_none(gui, rig):
    rig.host.offer = {"slug": "bigger-targets", "title": "Bigger touch targets"}
    pg, errors = open_play(gui, rig.host, "art")
    mark_button(pg).click()
    drag(pg)
    pg.locator(".play-addto").wait_for(timeout=WAIT_MS)
    rig.host.offer = None
    pg.get_by_role("radio", name="Missing").click()
    pg.wait_for_selector(".play-addto", state="detached", timeout=WAIT_MS)
    assert ("ideas.play_mark_offer", {"path": "/today", "kind": "missing"}) in rig.host.calls
    finish(pg, errors)


def test_on_the_project_tab_the_orkmaster_routes_the_mark_and_a_party_can_be_taken_off(gui, rig):
    rig.host.made = {**rig.host.made, "party": "", "party_title": ""}
    pg, errors = open_play(gui, rig.host)
    mark_button(pg).click()
    drag(pg)
    assert pg.locator(".play-to").count() == 0 and "The Orkmaster routes it" in pg.locator(".play-field").inner_text() and pg.locator(".play-lens").count() == 0
    type_line(pg)
    sent = send(pg, rig.host)
    assert "party" not in sent and pg.locator(".play-say.is-sent").inner_text().strip() == "Sent to the Orkmaster: Watered fails"
    pg.wait_for_selector(".play-sent", state="detached", timeout=WAIT_MS)
    open_tab(pg, "tech")                                                                                              # under a party's tab the × takes the party off
    mark_button(pg).click()
    drag(pg)
    pg.get_by_role("button", name="Do not send it to Tech").click()
    assert pg.locator(".play-to").count() == 0 and "The Orkmaster routes it" in pg.locator(".play-field").inner_text()
    type_line(pg)
    assert "party" not in send(pg, rig.host, 2)
    finish(pg, errors)


# -- a hint made into a goal -------------------------------------------------------------------------------------------------------------------------

def test_make_it_a_goal_on_a_hint_opens_the_field_as_a_bug_on_its_element_and_the_hint_is_gone_once_sent(gui, rig):
    rig.host.hints = [{"kind": "dead_press", "on": {"selector": "button#snooze", "rect": SNOOZE}, "words": "A press did nothing", "at": 1}]
    pg, errors = open_play(gui, rig.host, "art")
    pg.locator('.play-mark[data-kind="hint"] .play-tag').click()
    pg.get_by_role("button", name="Make it a goal").click()
    pg.locator(".play-field").wait_for(timeout=WAIT_MS)
    assert kinds(pg)["Bug"] == "true" and pg.locator(".play-field textarea").input_value() == "A press did nothing" and box_of(pg) == SNOOZE
    assert pg.locator(".play-back").count() == 0 and pg.locator(".play-bar").inner_text().count("Draw a box or press a part") == 1
    sent = send(pg, rig.host)
    assert sent["kind"] == "bug" and sent["under"][0]["selector"] == "button#snooze"
    pg.wait_for_selector('.play-mark[data-kind="hint"]', state="detached", timeout=WAIT_MS)
    finish(pg, errors)


# -- a game -----------------------------------------------------------------------------------------------------------------------------------------

def test_a_canvas_under_the_box_gains_the_games_state_and_under_game_designs_tab_asks_at_which_step(gui, rig):
    pg, errors = open_play(gui, rig.host, "game")
    wait_place(pg, "on Today")
    mark_button(pg).click()
    drag(pg, (430, 130, 600, 230))                                                                                    # over the canvas
    field = pg.locator(".play-field")
    field.get_by_role("radiogroup", name="At which step?").wait_for(timeout=WAIT_MS)
    steps = [c.inner_text() for c in field.get_by_role("radiogroup", name="At which step?").get_by_role("radio").all()]
    assert steps == ["Place a tower", "Survive the wave", "Spend the gold"] and "the game's state" in chips(pg) and "the part: Survive the wave" in chips(pg)
    assert kinds(pg)["Bug"] == "true"
    field.get_by_role("radio", name="Survive the wave").click()
    type_line(pg, "Wave 3 comes in from both lanes at once.")
    shot(pg, "e115-mark-game.png")
    sent = send(pg, rig.host)
    assert sent["text"] == "Wave 3 comes in from both lanes at once.\n\nAt the step: Survive the wave" and sent["state"] == {"level": 3, "gold": 40} and "state" in sent["with"]
    assert sent["under"][0]["role"] == "canvas"
    pg.wait_for_selector(".play-sent", state="detached", timeout=WAIT_MS)
    open_tab(pg, "tech")                                                                                              # no code knows the step under another tab: it is not asked
    mark_button(pg).click()
    drag(pg, (430, 130, 600, 230))
    pg.wait_for_function("() => document.querySelectorAll('.play-field .play-with').length >= 4", timeout=WAIT_MS)
    assert pg.get_by_role("radiogroup", name="At which step?").count() == 0 and "the game's state" in chips(pg)
    finish(pg, errors)


# -- no probe ---------------------------------------------------------------------------------------------------------------------------------------

def test_with_no_probe_marking_still_works_with_the_box_and_the_path_alone(gui, bare):
    pg, errors = open_play(gui, bare.host, "tech")
    assert strip_text(pg) == "Marks keep the picture and the place only"
    mark_button(pg).click()
    f = frame_box(pg)
    press_at(pg, 100, 100)                                                                                            # a press takes no element: a small box around it
    box = box_of(pg)
    assert abs(box["x"] + box["w"] / 2 - 100) <= 1 and abs(box["y"] + box["h"] / 2 - 100) <= 1 and (box["w"], box["h"]) == (64, 40) and f["width"] > 0
    pg.wait_for_function("() => document.querySelectorAll('.play-field .play-with').length >= 2", timeout=WAIT_MS)
    assert chips(pg) == ["the screen: Today", "the part: web/src/components", "the server's last lines"]                 # no error, no request, no game's state: nothing sees them
    type_line(pg)
    sent = send(pg, bare.host)
    assert sent["path"] == "/today" and "picture" not in sent and "state" not in sent and sent["under"] == [] and sorted(sent["with"]) == ["lines", "part", "screen"]
    assert pg.locator(".play-say.is-sent").inner_text().strip() == "Sent to Tech: Watered fails"
    finish(pg, errors)


# -- reduced motion ---------------------------------------------------------------------------------------------------------------------------------

def test_under_reduced_motion_the_sent_boxs_moment_is_still(gui, rig):
    pg, errors = open_play(gui, rig.host, "tech", reduced_motion="reduce")
    mark_button(pg).click()
    drag(pg)
    type_line(pg)
    watch_sent(pg)
    send(pg, rig.host)
    seen = pg.evaluate("() => window.__sent")
    assert seen["animation"] == "none" and seen["opacity"] == "1"
    pg.wait_for_selector(".play-sent", state="detached", timeout=WAIT_MS)                                           # it still goes
    finish(pg, errors)


# -- the narrow width -------------------------------------------------------------------------------------------------------------------------------

def test_at_the_narrow_width_the_field_stays_inside_the_pane(gui, rig):
    pg, errors = open_play(gui, rig.host, "tech", width={"width": 390, "height": 844})
    mark_button(pg).click()
    drag(pg, (40, 40, 160, 120))
    field = pg.locator(".play-field")
    fb, pane = field.bounding_box(), pg.locator("#table-pane").bounding_box()
    assert fb["x"] >= pane["x"] and fb["x"] + fb["width"] <= pane["x"] + pane["width"] + 1 and fb["y"] >= pane["y"]
    narrow.no_sideways(pg)
    finish(pg, errors)
