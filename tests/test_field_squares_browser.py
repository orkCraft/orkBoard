"""The + card turned where it lies, and its corners to pick (docs/specs/128-the-orkmasters-column-and-a-goal-at-every-leader.md part A, docs/specs/150 F, decisions §206.1, §254.9), in a real browser against the hand's stub host
(tests/test_hand_desktop_browser.py): the field grows from the + card (spec 168 D2, decisions §286: the card 144 x 202 whole at the table's foot at its left, the field as large as the hand, the + card hidden while it is open, Esc turns it back); its corners *rune* (top left),
*kind* (top right) and *who* (bottom left) are dashed buttons saying their defaults and *Now or Later* (bottom right) a fourth, each dealing its choices to the hand in the field's place (one at a time, Esc brings the field back before it lays the card back); *who* addresses a leader, *kind* names a type, *Files* (the
window's square) takes a file of the project; *Now* and *Later* are at the bottom right; the seal's ring is whole (three of orkUI's runes in the three places left)."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import _field, _plus, open_hand, shot  # noqa: E402
from tests.test_hand_mention_browser import MentionHost  # noqa: E402
from tests.test_shell_browser import _calls  # noqa: E402

pytestmark = pytest.mark.browser

CORNERS = ["rune", "type", "to"]                                                                         # the rune, the kind (the goal's `type`) and who (`to`)


def _open(pg):
    _plus(pg).wait_for(timeout=WAIT_MS)
    _plus(pg).click(position={"x": 8, "y": 60})
    field, area = _field(pg)
    pg.wait_for_function("() => document.querySelector('.hand-field__card').getAnimations().every((a) => a.playState === 'finished') && !document.querySelector('.hand-ghost')", timeout=WAIT_MS)
    return field, area


def _sq(pg, name):
    return pg.locator(f'.hand-field [data-sq="{name}"]')


def _co(pg, name):
    return pg.locator(f'.hand-field [data-corner="{name}"]')


def _open_row(pg):
    return pg.locator(".hand-field__row-open").get_attribute("data-open") if pg.locator(".hand-field__row-open").count() else ""


def _list(pg):
    return pg.locator(".hand-field .hand-pick").get_attribute("data-open") if pg.locator(".hand-field .hand-pick").count() else ""


def test_under_reduced_motion_the_field_is_there_at_once(gui):
    pg, host, log = open_hand(gui)
    try:
        pg.emulate_media(reduced_motion="reduce")
        _plus(pg).wait_for(timeout=WAIT_MS)
        _plus(pg).click(position={"x": 8, "y": 60})
        field, _ = _field(pg)
        assert pg.locator(".hand-field__card").evaluate("e => e.getAnimations().length") == 0 and pg.locator(".hand-ghost").count() == 0
        pg.keyboard.press("Escape")
        pg.wait_for_function("() => !document.querySelector('.hand-field')", timeout=WAIT_MS)
        assert pg.locator(".hand-ghost").count() == 0 and _plus(pg).evaluate("e => getComputedStyle(e).visibility") == "visible"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_on_a_narrow_window_the_field_is_as_wide_as_the_screen_as_before(gui):
    pg, host, log = open_hand(gui, width="narrow")
    try:
        _plus(pg).wait_for(timeout=WAIT_MS)
        _plus(pg).click(position={"x": 8, "y": 60})
        field, _ = _field(pg)
        pg.wait_for_function("() => document.querySelector('.hand-field').getAnimations().length === 0 && !document.querySelector('.hand-ghost')", timeout=WAIT_MS)
        box = field.bounding_box()
        assert abs(box["x"] + box["width"] / 2 - 195) <= 1 and box["width"] >= 390 - 40, box          # the screen's width less its gutters
        assert box["y"] + box["height"] <= pg.evaluate("() => innerHeight") + 1, "at the hand's foot, not under the edge"
        assert [_co(pg, n).count() for n in CORNERS] == [1, 1, 1] and _sq(pg, "files").count() == 1
        narrow.no_sideways(pg)
    finally:
        pg.close()
    assert not log, "\n".join(log)




def _dealt(pg):
    return pg.locator(".hand-dealt").get_attribute("data-open") if pg.locator(".hand-dealt").count() else ""


def test_who_addresses_a_leader_the_kinds_come_by_their_signs_and_a_kind_picked_is_sent_as_type(gui):
    from orkboard.realm import lexicon
    pg, host, log = open_hand(gui, host=MentionHost())
    try:
        field, area = _open(pg)
        _co(pg, "type").click()
        kinds = pg.locator(".hand-dealt[data-open=type]")
        assert kinds.get_by_role("menuitemradio").count() > 2 and kinds.get_by_role("menuitemradio", name=lexicon.term("slot_kind")).get_attribute("aria-checked") == "true", "no party: every party's kinds, and *the Orkmaster reads it* in force"
        pg.keyboard.press("Escape")
        _co(pg, "to").click()
        to = pg.locator(".hand-dealt[data-open=to]")
        assert to.get_by_role("menuitemradio", name=lexicon.term("slot_who")).get_attribute("aria-checked") == "true" and to.locator("img.ork-race__head").count() == 6
        to.get_by_role("menuitemradio", name="Game design").click(position={"x": 20, "y": 30})
        assert _dealt(pg) == "" and _co(pg, "to").get_attribute("data-set") == "1"
        assert _co(pg, "to").get_attribute("aria-label") == "To: Game design, change it"
        _co(pg, "type").click()
        kinds = pg.locator(".hand-dealt[data-open=type]")
        assert [r.get_attribute("aria-label") for r in kinds.get_by_role("menuitemradio").all()] == ["New mechanic", "Balance pass", lexicon.term("slot_kind")]
        kinds.get_by_role("menuitemradio", name="Balance pass").click(position={"x": 20, "y": 30})
        assert _co(pg, "type").get_attribute("data-set") == "1" and _co(pg, "type").get_attribute("aria-label") == "Its kind: Balance pass, change it"
        _co(pg, "type").click()
        pg.locator(".hand-dealt[data-open=type]").get_by_role("menuitemradio", name="New mechanic").click(position={"x": 20, "y": 30})
        area.fill("Round timer")
        area.press("Enter")
        assert _calls(pg, host, "ideas.add")[-1] == {"match": True, "now": True, "text": "Round timer", "party": "game", "type": "mechanic"}, "a leader picked is the party, a kind picked the type; Enter is Now"
        pg.wait_for_function("() => !document.querySelector('.hand-field')", timeout=WAIT_MS)
        field, area = _open(pg)
        assert _co(pg, "to").get_attribute("data-set") == "0" and _co(pg, "type").get_attribute("data-set") == "0", "the next goal starts with its defaults again"
        _co(pg, "to").click()
        pg.locator(".hand-dealt[data-open=to]").get_by_role("menuitemradio", name="Design", exact=True).click(position={"x": 20, "y": 30})
        _co(pg, "to").click()
        pg.locator(".hand-dealt[data-open=to]").get_by_role("menuitemradio", name=lexicon.term("slot_who")).click(position={"x": 20, "y": 30})
        assert _co(pg, "to").get_attribute("data-set") == "0", "the Orkmaster's crown: a general goal"
        area.fill("Anything")
        area.press("Enter")
        assert "party" not in _calls(pg, host, "ideas.add", 2)[-1]
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_now_sends_with_now_and_later_with_later_and_both_wait_for_words(gui):
    from orkboard.realm import lexicon
    pg, host, log = open_hand(gui, host=MentionHost())
    try:
        field, area = _open(pg)
        assert field.get_by_role("button", name="Send", exact=True).count() == 0, "Send is gone"
        _co(pg, "go").click()
        now, later = pg.locator('.hand-dealt [data-go="now"]'), pg.locator('.hand-dealt [data-go="later"]')
        assert now.get_by_text(lexicon.term("now"), exact=True).count() == 1 and later.get_by_text(lexicon.term("later"), exact=True).count() == 1
        assert now.is_disabled() and later.is_disabled(), "nothing to send without words"
        pg.keyboard.press("Escape")
        area.fill("Round timer")
        _co(pg, "go").click()
        pg.locator('.hand-dealt [data-go="later"]').click(position={"x": 20, "y": 30})
        assert _calls(pg, host, "ideas.add")[-1] == {"match": True, "later": True, "text": "Round timer"}
        pg.wait_for_function("() => !document.querySelector('.hand-field')", timeout=WAIT_MS)
        field, area = _open(pg)
        area.fill("Round timer two")
        _co(pg, "go").click()
        pg.locator('.hand-dealt [data-go="now"]').click(position={"x": 20, "y": 30})
        assert _calls(pg, host, "ideas.add", 2)[-1] == {"match": True, "now": True, "text": "Round timer two"}
        pg.wait_for_function("() => !document.querySelector('.hand-field')", timeout=WAIT_MS)
        field, area = _open(pg)
        area.fill("one")                                                                                   # Shift+Enter is a new line
        area.press("End")
        area.press("Shift+Enter")
        assert pg.locator(".hand-field").count() == 1 and "\n" in area.input_value()
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_files_takes_pictures_from_this_computer_and_files_of_the_project_as_chips_in_the_new_goals_window(gui):
    pg, host, log = open_hand(gui, host=MentionHost())
    try:
        field, area = _open(pg)
        assert pg.get_by_role("button", name="Add a picture").count() == 0, "Add a picture is gone"
        area.fill("Fix the lobby")
        _sq(pg, "files").click()
        row = pg.locator(".hand-dealt .hand-field__row-open")
        assert row.get_by_text("Pictures from this computer, or a file of the project").count() == 1
        row.get_by_role("button", name="From this computer").wait_for(timeout=WAIT_MS)
        row.get_by_role("checkbox", name="src/app.py").wait_for(timeout=WAIT_MS)
        assert row.get_by_role("checkbox", name="src/", exact=True).count() == 0, "files, not folders"
        row.get_by_role("checkbox", name="src/app.py").click()
        assert row.get_by_role("checkbox", name="src/app.py").get_attribute("aria-checked") == "true"
        assert pg.locator(".hand-field__win .hand-file").inner_text().strip() == "app.py", "a chip in the card's window (spec 148 B.6)"
        pg.keyboard.press("Escape")
        assert _sq(pg, "files").locator(".hand-sq__n").inner_text() == "1", "the number of files at the square's corner"
        field.locator("input[type=file]").set_input_files({"name": "p.png", "mimeType": "image/png", "buffer": _png()})
        pg.locator(".hand-field__win .hand-pic img").wait_for(timeout=WAIT_MS)
        assert _sq(pg, "files").locator(".hand-sq__n").inner_text() == "2"
        area.press("Enter")
        sent = _calls(pg, host, "ideas.add")[-1]
        assert sent["text"] == "Fix the lobby @src/app.py" and len(sent["photos"]) == 1, sent
        pg.wait_for_function("() => !document.querySelector('.hand-field')", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def _png():
    import base64
    return base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")


# -- spec 147 D.2 and spec 148 B.6: the new goal's card, its corners dashed until they fill, its window the place what is attached lies and is dropped on --------------------


def test_a_new_goals_window_shows_what_is_attached_and_is_where_a_picture_is_dropped(gui):
    """Spec 148 B.6, decisions §252.4: the hint while nothing is attached; then the pictures as thumbnails and the files as chips; a picture dropped on the window is attached."""
    from orkboard.realm import lexicon
    pg, host, log = open_hand(gui, host=MentionHost())
    try:
        field, area = _open(pg)
        win = field.locator(".hand-field__win")
        assert win.get_attribute("data-window") == "hint" and win.inner_text().strip() == lexicon.term("attach_hint"), "with nothing attached, the hint words"
        assert "is-window" in win.get_attribute("class").split(), "the lanes' window frame"
        win.dispatch_event("drop", {"dataTransfer": pg.evaluate_handle("""([b64]) => { const dt = new DataTransfer(), bin = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
          dt.items.add(new File([bin], 'p.png', { type: 'image/png' })); return dt; }""", [_png_b64()])})
        win.locator(".hand-pic img").wait_for(timeout=WAIT_MS)
        assert win.get_attribute("data-window") == "attached" and win.locator(".hand-pic img").count() == 1 and win.locator(".hand-field__attach").count() == 0, "a picture dropped on the window lies in it as a thumbnail"
        assert pg.evaluate("() => document.querySelector('.hand-field__win .hand-pic img').getBoundingClientRect().width") >= 48
        _sq(pg, "files").click()
        pg.locator(".hand-dealt .hand-field__row-open").get_by_role("checkbox", name="src/app.py").click()
        assert win.locator(".hand-file").inner_text().strip() == "app.py" and win.locator(".hand-pic").count() == 1, "a file as a chip beside it"
        win.get_by_role("button", name="Remove picture 1").click()
        win.get_by_role("button", name="Take src/app.py off").click()
        assert win.get_attribute("data-window") == "hint", "taken off, the hint is back"
        shot(pg, "field-window-attached")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def _png_b64():
    return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
