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
    pg.locator(".hand :is(.hand-plus, [data-blank-deck])").first.click()
    pg.locator(".hand-fieldbox textarea").wait_for(timeout=WAIT_MS)
    pg.wait_for_timeout(600)
    return pg, host, log


def box(loc):
    b = loc.bounding_box()
    return {**b, "width": round(b["width"]), "height": round(b["height"])}                  # a card is 144 x 201.6 (5 : 7): the page's own size is the rounded one


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
        pg.locator(".hand :is(.hand-plus, [data-blank-deck])").first.click()
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
