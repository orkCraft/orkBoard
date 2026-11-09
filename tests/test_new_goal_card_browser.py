"""A new goal is a card in play (docs/specs/168 D2, decisions §286), in a real browser at 1366 x 768 against the hand's stub host: the + card pressed raises a 144 x 202 card whole at the table's foot at its left; a field as large as the hand
takes the hand's place (its cards sunk), focused at once; a corner pressed (its rune, its kind, who, *Now* or *Later*) deals its choices to the hand in the field's place and the field comes back with its words once one is played;
Enter sends, Shift+Enter is a new line, Esc lays the card back and keeps the words as a draft; a picture dropped on the field is attached and shown in the card's window. Screenshots to $PLAY_SHOTS when it is set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, PNG, open_hand, sig  # noqa: E402
from tests.test_shell_browser import _calls  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["PLAY_SHOTS"]) if os.environ.get("PLAY_SHOTS") else None
VIEW = {"width": 1366, "height": 768}


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


def opened(gui):
    pg, host, log = open_hand(gui, host=HandHost())
    pg.set_viewport_size(VIEW)
    pg.wait_for_timeout(300)
    pg.locator(".hand-plus").first.click()
    pg.locator(".hand-fieldbox textarea").wait_for(timeout=WAIT_MS)
    pg.wait_for_timeout(600)
    return pg, host, log


def box(loc):
    b = loc.bounding_box()
    return {**b, "width": round(b["width"]), "height": round(b["height"])}                  # a card is 144 x 201.6 (5 : 7): the page's own size is the rounded one


def test_the_plus_card_raises_a_whole_card_at_the_tables_foot_and_a_field_as_large_as_the_hand_takes_its_place(gui):
    pg, host, log = opened(gui)
    try:
        card, field, hand, pane = box(pg.locator(".hand-field__card")), box(pg.locator(".hand-fieldbox")), box(pg.locator(".hand")), box(pg.locator(".frame-table"))
        assert [card["width"], card["height"]] == [144, 202], "whole: all four corners show"
        assert card["y"] + card["height"] <= hand["y"] + 1 and pane["x"] <= card["x"] <= pane["x"] + 60, "at the table's foot, at its left"
        assert abs(field["y"] - hand["y"]) <= 4 and abs(field["height"] - hand["height"]) <= 4, "the field's box is the hand's"
        end = box(pg.locator(".hand-end"))
        assert abs(field["x"] - card["x"]) <= 2 and end["x"] - 40 <= field["x"] + field["width"] <= end["x"], ("from the card's left edge to the places", field, end)
        sizes = [(round(b["width"]), round(b["height"])) for b in (e.bounding_box() for e in pg.locator(".hand-end .place-box").all()) if b]
        assert sizes and all(x == (48, 60) for x in sizes), ("the places keep their one size and their place (decisions §283.5, §284.4)", sizes)
        assert pg.locator(".hand-fieldbox textarea").evaluate("e => e === document.activeElement"), "focused at once"
        row = pg.locator(".hand-row")
        assert "is-sunk" in row.get_attribute("class").split() and row.evaluate("e => e.inert"), "the hand's cards sink"
        for corner in ("rune", "type", "to", "go"):
            assert pg.locator(f'.hand-field__card [data-corner="{corner}"]').is_visible(), corner
        no = pg.evaluate("() => [...document.querySelectorAll('body *')].filter((e) => { const r = e.getBoundingClientRect(); return Math.round(r.width) === 404 && Math.round(r.height) === 566; }).length")
        assert no == 0, "no card of 404 x 566"
        shot(pg, "new-goal")
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("corner, choice, want", [("rune", '[data-rune="lava"]', ("rune", "lava")), ("type", '[data-type=""]', None), ("to", '[data-to="design"]', ("to", "design"))])
def test_a_corner_deals_its_choices_to_the_hand_and_the_field_comes_back_with_its_words(gui, corner, choice, want):
    pg, host, log = opened(gui)
    try:
        pg.keyboard.type("Make the timer bigger")
        pg.locator(f'.hand-field__card [data-corner="{corner}"]').click()
        dealt = pg.locator(".hand-dealt")
        dealt.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(500)
        assert pg.locator(".hand-fieldbox").count() == 0, "the field gives its place to the choices"
        hand = box(pg.locator(".hand"))
        cards = dealt.locator(".hand-deal")
        assert cards.count() >= 1
        for i in range(cards.count()):
            b = box(cards.nth(i))
            assert [b["width"], b["height"]] == [144, 202] and hand["y"] < b["y"] < hand["y"] + 30, "cards of the hand's size, cut by its rim"
        if corner == "rune":
            assert cards.count() == 5
            shot(pg, "new-goal-rune")
        elif corner == "type":
            shot(pg, "new-goal-kind")
        dealt.locator(choice).first.click(position={"x": 20, "y": 30})
        pg.locator(".hand-fieldbox textarea").wait_for(timeout=WAIT_MS)
        assert pg.locator(".hand-dealt").count() == 0
        assert pg.locator(".hand-fieldbox textarea").input_value() == "Make the timer bigger", "the field comes back with its words"
        assert pg.locator(".hand-fieldbox textarea").evaluate("e => e === document.activeElement")
        if want:
            assert sig(pg, "hand/state.js", {"rune": "fieldRune", "to": "fieldTo"}[want[0]]) == want[1]
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_now_and_later_are_dealt_by_the_last_corner_and_playing_one_sends(gui):
    pg, host, log = opened(gui)
    try:
        pg.locator('.hand-field__card [data-corner="go"]').click()
        pg.locator(".hand-dealt").wait_for(timeout=WAIT_MS)
        assert pg.locator(".hand-dealt [data-go]").evaluate_all("els => els.map((e) => e.dataset.go + ':' + e.disabled)") == ["now:true", "later:true"], "nothing is written: nothing is sent"
        pg.keyboard.press("Escape")
        pg.locator(".hand-fieldbox textarea").wait_for(timeout=WAIT_MS)
        pg.keyboard.type("Add a sound")
        pg.locator('.hand-field__card [data-corner="go"]').click()
        shot(pg, "new-goal-go")
        pg.locator('.hand-dealt [data-go="later"]').click(position={"x": 20, "y": 30})
        got = _calls(pg, host, "ideas.add")
        assert got and got[0]["text"] == "Add a sound" and got[0]["later"] is True, got
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_enter_sends_shift_enter_is_a_new_line_and_esc_lays_the_card_back_keeping_a_draft(gui):
    pg, host, log = opened(gui)
    try:
        pg.keyboard.type("A draft")
        pg.keyboard.press("Shift+Enter")
        pg.keyboard.type("on two lines")
        assert pg.locator(".hand-fieldbox textarea").input_value() == "A draft\non two lines"
        assert not _calls(pg, host, "ideas.add", at_least=0), "Shift+Enter sent nothing"
        pg.keyboard.press("Escape")
        pg.wait_for_selector(".hand-field", state="detached", timeout=WAIT_MS)
        assert pg.locator(".hand-row.is-sunk").count() == 0 and not pg.locator(".hand-row").evaluate("e => e.inert"), "the hand's cards come back"
        assert sig(pg, "hand/state.js", "fieldText") == "A draft\non two lines", "the draft is kept"
        pg.locator(".hand-plus").first.click()
        pg.locator(".hand-fieldbox textarea").wait_for(timeout=WAIT_MS)
        assert pg.locator(".hand-fieldbox textarea").input_value() == "A draft\non two lines"
        pg.keyboard.press("Enter")
        got = _calls(pg, host, "ideas.add")
        assert got and got[0]["text"] == "A draft\non two lines" and got[0]["now"] is True, got
        pg.wait_for_selector(".hand-field", state="detached", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_picture_dropped_on_the_field_is_attached_and_shown_in_the_cards_window(gui):
    pg, host, log = opened(gui)
    try:
        import base64  # noqa: PLC0415
        assert pg.locator(".hand-field__win .hand-pic").count() == 0
        pg.evaluate("""(b64) => {
          const f = new File([Uint8Array.from(atob(b64), (c) => c.charCodeAt(0))], 'p.png', { type: 'image/png' }), dt = new DataTransfer();
          dt.items.add(f);
          document.querySelector('.hand-fieldbox textarea').dispatchEvent(new DragEvent('drop', { dataTransfer: dt, bubbles: true, cancelable: true }));
        }""", base64.b64encode(PNG).decode())
        pg.locator(".hand-field__win .hand-pic img").wait_for(timeout=WAIT_MS)
        assert pg.locator(".hand-field__win .hand-pic").count() == 1
        shot(pg, "new-goal-picture")
    finally:
        pg.close()
    assert not log, "\n".join(log)
