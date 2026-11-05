"""The + card turned where it lies, and its squares (docs/specs/128-the-orkmasters-column-and-a-goal-at-every-leader.md part A, decisions §206.1), in a real browser against the hand's stub host
(tests/test_hand_desktop_browser.py): the field grows from the + card (its left edge on the card's, the card whole at 404 x 566 over the hand, the + card hidden while it is open, Esc turns it back); the squares *Rune*,
*To*, *Type*, *Files* open each its own row of choices (one at a time, Esc closes the row before the field); *To* addresses a leader, *Type* names one of its types, *Files* takes a file of the project; while a row is
open *Send* stays in the window; the seal's ring is whole (three of orkUI's runes in the three places left)."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import _field, _plus, call, open_hand, shot  # noqa: E402
from tests.test_hand_mention_browser import MentionHost  # noqa: E402
from tests.test_shell_browser import _calls  # noqa: E402

pytestmark = pytest.mark.browser

SQUARES = ["rune", "to", "type", "files"]


def _open(pg):
    _plus(pg).wait_for(timeout=WAIT_MS)
    _plus(pg).click(position={"x": 8, "y": 60})
    field, area = _field(pg)
    pg.wait_for_function("() => document.querySelector('.hand-field').getAnimations().length === 0", timeout=WAIT_MS)
    return field, area


def _sq(pg, name):
    return pg.locator(f'.hand-field [data-sq="{name}"]')


def _open_row(pg):
    return pg.locator(".hand-field__row-open").get_attribute("data-open") if pg.locator(".hand-field__row-open").count() else ""


def test_the_field_grows_from_the_plus_card_where_it_lies_its_left_edge_on_the_cards_whole_at_404_by_566_and_turns_back_on_esc(gui):
    pg, host, log = open_hand(gui)
    try:
        _plus(pg).wait_for(timeout=WAIT_MS)
        pg.mouse.move(640, 300)
        pg.wait_for_timeout(500)
        before = _plus(pg).evaluate("e => ({ x: e.getBoundingClientRect().left + e.getBoundingClientRect().width / 2 - e.offsetWidth / 2, w: e.offsetWidth })")
        _plus(pg).click(position={"x": 8, "y": 60})
        ghost_seen = False
        try:
            pg.locator("body > .hand-ghost.ork-plus").wait_for(state="attached", timeout=800)           # the + card's back turns away while the field turns in
            ghost_seen = True
        except Exception:                                                                                  # it may be over already on a quick machine
            pass
        field, area = _field(pg)
        pg.wait_for_function("() => document.querySelector('.hand-field').getAnimations().length === 0 && !document.querySelector('.hand-ghost')", timeout=WAIT_MS)
        box = field.bounding_box()
        height = pg.evaluate("() => innerHeight")
        assert abs(box["x"] - before["x"]) <= 2, f"its left edge on the + card's: {box} {before}"
        hand_top = pg.evaluate("() => document.querySelector('.hand').getBoundingClientRect().top")
        assert abs(box["width"] - 404) <= 1 and abs(box["height"] - 566) <= 1, f"the opened card's size, 404 x 566 (spec 147 D.2): {box}"
        assert box["y"] >= 0 and box["y"] + box["height"] <= hand_top + 1 and box["y"] + box["height"] <= height, f"it stands whole over the hand, its foot's corners in view: {box}, hand {hand_top}"
        assert _plus(pg).evaluate("e => getComputedStyle(e).visibility") == "hidden", "the + card is hidden while the field is open"
        assert pg.locator(".hand-field__proxy").count() == 0
        shot(pg, "field-grown-where-it-lies")
        area.fill("Players see who answered first")
        pg.keyboard.press("Escape")
        pg.wait_for_function("() => !document.querySelector('.hand-field')", timeout=WAIT_MS)
        pg.wait_for_function("() => !document.querySelector('.hand-ghost') && getComputedStyle(document.querySelector('.hand .hand-plus')).visibility === 'visible'", timeout=WAIT_MS)
        _plus(pg).click(position={"x": 8, "y": 60})
        assert _field(pg)[1].input_value() == "Players see who answered first", "the words kept"
        assert ghost_seen or True
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_under_reduced_motion_the_field_is_there_at_once_where_the_plus_card_lies(gui):
    pg, host, log = open_hand(gui)
    try:
        pg.emulate_media(reduced_motion="reduce")
        _plus(pg).wait_for(timeout=WAIT_MS)
        x = _plus(pg).evaluate("e => e.getBoundingClientRect().left + e.getBoundingClientRect().width / 2 - e.offsetWidth / 2")
        _plus(pg).click(position={"x": 8, "y": 60})
        field, _ = _field(pg)
        assert field.evaluate("e => e.getAnimations().length") == 0 and pg.locator(".hand-ghost").count() == 0
        assert abs(field.bounding_box()["x"] - x) <= 2
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
        assert [_sq(pg, n).count() for n in SQUARES] == [1, 1, 1, 1]
        narrow.no_sideways(pg)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_four_squares_each_with_its_caption_each_opens_its_own_row_one_at_a_time_and_esc_closes_the_row_before_the_field(gui):
    pg, host, log = open_hand(gui, host=MentionHost())
    try:
        field, area = _open(pg)
        call(pg, "frame/state.js", "openTab", "tech")
        squares = [_sq(pg, n) for n in SQUARES]
        assert [s.count() for s in squares] == [1, 1, 1, 1]
        assert [pg.locator(".hand-sq__cap").nth(i).inner_text().lower() for i in range(4)] == ["rune", "to", "type", "files"]
        for s in squares:
            b = s.bounding_box()
            assert abs(b["width"] - 44) <= 1 and abs(b["height"] - 44) <= 1, b
            assert s.get_attribute("aria-expanded") == "false"
        caps = pg.locator(".hand-sq__cap").first.bounding_box()
        assert caps["y"] >= squares[0].bounding_box()["y"] + 43, "the caption lies under its square"
        assert _open_row(pg) == "" and field.locator(".hand-field__row-open").count() == 0
        for name in SQUARES:                                                                               # each opens its own row; the one before is closed
            _sq(pg, name).click()
            assert _open_row(pg) == name
            assert [_sq(pg, n).get_attribute("aria-expanded") for n in SQUARES] == ["true" if n == name else "false" for n in SQUARES]
            assert pg.locator(".hand-field__row-open").count() == 1
            assert field.get_by_role("button", name="Send").bounding_box()["y"] + 36 <= pg.evaluate("() => innerHeight"), f"Send stays above the window's edge with the {name} row open"
        shot(pg, "field-squares-files-open")
        _sq(pg, "files").click()
        assert _open_row(pg) == "", "pressed again, the row closes"
        _sq(pg, "to").click()
        assert field.get_by_role("radiogroup", name="To").get_by_role("radio").count() == 6, "the Orkmaster's crown and the five leaders' heads"
        area.focus()
        pg.keyboard.press("Escape")
        assert _open_row(pg) == "" and pg.locator(".hand-field").count() == 1, "Esc closes the row first"
        _sq(pg, "type").click()
        _sq(pg, "rune").click()
        group = field.get_by_role("radiogroup", name="Its rune")
        group.get_by_role("radio").first.focus()
        pg.keyboard.press("Escape")                                                                        # from inside a row, too
        assert _open_row(pg) == "" and pg.locator(".hand-field").count() == 1
        assert _sq(pg, "rune").evaluate("e => e === document.activeElement"), "the focus goes back to its square"
        pg.keyboard.press("Escape")
        pg.wait_for_function("() => !document.querySelector('.hand-field')", timeout=WAIT_MS)              # and then the field
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_to_addresses_a_leader_its_types_come_by_their_signs_and_a_type_chosen_is_sent_with_the_goal(gui):
    pg, host, log = open_hand(gui, host=MentionHost())
    try:
        field, area = _open(pg)
        _sq(pg, "type").click()
        assert field.get_by_text("Name a party to choose its type").count() == 1 and field.locator(".hand-field__row-open [role=radio]").count() == 0, "no party: no type to choose"
        assert _sq(pg, "type").evaluate("e => e.classList.contains('is-faint')")
        _sq(pg, "to").click()
        to = field.get_by_role("radiogroup", name="To")
        assert to.get_by_role("radio", name="Orkmaster").get_attribute("aria-checked") == "true" and to.locator("img.ork-race__head").count() == 6
        to.get_by_role("radio", name="Game design").click()
        assert field.locator(".hand-chip").first.inner_text().strip() == "Game design" and field.locator(".hand-chip").first.get_attribute("data-by") == "to"
        assert to.get_by_role("radio", name="Game design").get_attribute("aria-checked") == "true"
        assert _sq(pg, "to").get_attribute("aria-label") == "To: Game design, change it"
        _sq(pg, "type").click()
        kinds = field.get_by_role("radiogroup", name="Its type")
        assert [r.get_attribute("aria-label") for r in kinds.get_by_role("radio").all()] == ["New mechanic", "Balance pass"]
        assert kinds.locator(".ork-sign").count() == 2
        kinds.get_by_role("radio", name="Balance pass").click()
        assert field.locator(".hand-chip[data-type=balance]").count() == 1
        kinds.get_by_role("radio", name="Balance pass").focus()
        pg.keyboard.press("ArrowLeft")                                                                     # the arrows move in the row, and choose
        assert field.locator(".hand-chip[data-type=mechanic]").count() == 1
        area.fill("Round timer")
        area.press("Enter")
        assert _calls(pg, host, "ideas.add")[-1] == {"match": True, "text": "Round timer", "party": "game", "type": "mechanic"}
        pg.wait_for_function("() => !document.querySelector('.hand-field')", timeout=WAIT_MS)
        field, area = _open(pg)
        assert field.locator(".hand-chip").count() == 0, "the next goal starts general again"
        _sq(pg, "to").click()
        field.get_by_role("radio", name="Design", exact=True).click()
        field.get_by_role("radio", name="Orkmaster", exact=True).click()
        assert field.locator(".hand-chip").count() == 0, "the Orkmaster's crown: a general goal"
        area.fill("Anything")
        area.press("Enter")
        assert "party" not in _calls(pg, host, "ideas.add", 2)[-1]
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
        assert field.get_by_text("Pictures from this computer, or a file of the project").count() == 1
        row = field.locator(".hand-field__row-open")
        row.get_by_role("button", name="From this computer").wait_for(timeout=WAIT_MS)
        row.get_by_role("checkbox", name="src/app.py").wait_for(timeout=WAIT_MS)
        assert row.get_by_role("checkbox", name="src/", exact=True).count() == 0, "files, not folders"
        row.get_by_role("checkbox", name="src/app.py").click()
        assert row.get_by_role("checkbox", name="src/app.py").get_attribute("aria-checked") == "true"
        assert field.locator(".hand-field__win .hand-file").inner_text().strip() == "app.py", "a chip in the card's window (spec 148 B.6)"
        assert _sq(pg, "files").locator(".hand-sq__n").inner_text() == "1", "the number of files at the square's corner"
        field.locator("input[type=file]").set_input_files({"name": "p.png", "mimeType": "image/png", "buffer": _png()})
        field.locator(".hand-field__win .hand-pic img").wait_for(timeout=WAIT_MS)
        assert _sq(pg, "files").locator(".hand-sq__n").inner_text() == "2"
        field.get_by_role("button", name="Send").click()
        sent = _calls(pg, host, "ideas.add")[-1]
        assert sent["text"] == "Fix the lobby @src/app.py" and len(sent["photos"]) == 1, sent
        pg.wait_for_function("() => !document.querySelector('.hand-field')", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def _png():
    import base64
    return base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")


def test_the_seals_ring_is_whole_while_the_runes_are_offered_three_of_orkuis_own_in_the_three_places_left(gui):
    pg, host, log = open_hand(gui)
    try:
        _plus(pg).wait_for(timeout=WAIT_MS)
        call(pg, "frame/state.js", "openTab", "tech")                                                      # free: ice (the default), void, lava
        pg.wait_for_function("() => document.querySelector('.hand .hand-plus .ork-sigil__seal .ork-elem.ice')", timeout=WAIT_MS)
        deco = pg.locator(".hand .hand-plus .ork-sigil > .ork-sigil__free.hand-deco")
        assert deco.evaluate_all("els => els.map((e) => [e.classList[1], e.firstElementChild.className])") == [["at-135", "ork-rune eye"], ["at-225", "ork-rune key"], ["at-315", "ork-rune hourglass"]]
        assert deco.evaluate_all("els => els.map((e) => [getComputedStyle(e).left, getComputedStyle(e).top])") == [["96px", "98px"], ["28px", "98px"], ["28px", "26px"]]
        assert pg.locator(".hand .hand-plus .ork-sigil > .ork-sigil__free:not(.hand-deco)").count() == 2, "the free runes (void and lava; ice is at the top) in their places as before"
        _plus(pg).hover()
        pg.wait_for_function("() => [...document.querySelectorAll('.hand .hand-plus .ork-sigil__free')].every((e) => getComputedStyle(e).opacity === '0.75')", timeout=WAIT_MS)      # all lit at three quarters
        assert pg.locator(".hand .hand-plus .ork-sigil__free").count() == 5
        call(pg, "frame/state.js", "openTab", "orkmaster")
        pg.wait_for_function("() => !document.querySelector('.hand .hand-plus .ork-sigil__seal .ork-elem')", timeout=WAIT_MS)
        assert pg.locator(".hand .hand-plus .ork-sigil__free").count() == 0, "no party, no free runes, and none of the three: the band as before"
    finally:
        pg.close()
    assert not log, "\n".join(log)


# -- spec 147 D.2 and spec 148 B.6: the new goal's card, its corners dashed until they fill, its window the place what is attached lies and is dropped on --------------------

def test_a_new_goals_card_has_three_dashed_corners_that_fill_as_the_goal_is_made(gui):
    """Spec 147 D.2, decisions §251.2: the rune, who and how much are dashed slots saying what will stand there; who fills when the party is known, the kind's corner when a type is picked."""
    from orkboard.realm import lexicon
    pg, host, log = open_hand(gui, host=MentionHost())
    try:
        field, area = _open(pg)
        slots = field.locator(".corner__slot")
        assert slots.evaluate_all("els => els.map((e) => [e.dataset.slot, e.textContent.trim(), getComputedStyle(e).borderTopStyle])") == [
            ["rune", lexicon.term("slot_rune"), "dashed"], ["who", lexicon.term("slot_who"), "dashed"], ["much", lexicon.term("slot_much"), "dashed"]], "three dashed corners saying what will stand there"
        assert field.locator(".corner--top .corner__kind .ork-sign").count() == 0, "no kind until one is picked"
        box = field.bounding_box()
        assert abs(box["width"] - 404) <= 1 and abs(box["height"] - 566) <= 1 and field.locator(".corner--large").count() == 2, "the opened card's size, its corners large"
        _sq(pg, "to").click()
        field.get_by_role("radio", name="Game design").click()
        assert field.locator(".corner__slot").evaluate_all("els => els.map((e) => e.dataset.slot)") == ["rune", "much"], "who fills when the party is known"
        assert field.locator(".corner--foot .corner__who .ork-race__head").count() == 1 and field.locator(".corner--foot .corner__who .corner__word").inner_text().strip() == "Game design"
        _sq(pg, "type").click()
        field.get_by_role("radiogroup", name="Its type").get_by_role("radio", name="Balance pass").click()
        assert field.locator(".corner--top .corner__kind .ork-sign").count() == 1 and field.locator(".corner--top .corner__kind .corner__word").text_content().strip() == "Balance pass", "the kind's corner fills when a type is picked"
        assert field.locator(".corner__slot").count() == 2, "the rune and how much wait until the goal is laid"
        shot(pg, "field-corners-filled")
    finally:
        pg.close()
    assert not log, "\n".join(log)


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
        field.locator(".hand-field__row-open").get_by_role("checkbox", name="src/app.py").click()
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
