"""The desktop hand's three new things of docs/specs/107-what-the-owners-day-said.md, in a real browser against the hand's stub host (tests/test_hand_desktop_browser.py):
J, the bug under the glass (the button by the mana, shown with no mana too, its panel and `logs.save` with the line); K, @ in New goal (a party offered as one types and taken with Enter, which does not send; a file
from `files.find`; who, then what, then on what: a party's goal types, its map's parts as marks; a word that names a type offers it with its party); M, New goal's frame and that it lies under no other card."""
from __future__ import annotations

import copy

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, _field, _plus, open_hand, party  # noqa: E402
from tests.test_shell_browser import _calls, _sent  # noqa: E402

pytestmark = pytest.mark.browser

TYPES = [{"id": "mechanic", "name": "New mechanic", "sign": "mechanic", "line": "A rule of play", "lens": "", "asks": [], "refs": False, "used": 2, "missing": []},
         {"id": "balance", "name": "Balance pass", "sign": "balance", "line": "Tune the numbers", "lens": "", "asks": [], "refs": False, "used": 0, "missing": []}]
FILES = [{"path": "src/", "name": "src", "dir": True}, {"path": "src/app.py", "name": "app.py", "dir": False}, {"path": "README.md", "name": "README.md", "dir": False}]
PARTS = [{"map": "game-design", "id": "spawn", "name": "Spawn", "label": "Spawn", "group": "loop"}, {"map": "game-design", "id": "loot", "name": "Loot", "label": "Loot", "group": "loop"}]


class MentionHost(HandHost):
    """The hand's project with a fifth party, Game design, that offers two goal types; `files.find` and `ideas.pickables` answer."""

    def __init__(self, **more):
        super().__init__(**more)
        game = party("game", "Game design", "unicorn", "product")
        game["types"] = copy.deepcopy(TYPES)
        self.parties.append(game)
        for p in self.parties:
            p.setdefault("types", [])

    def handle(self, name, a):
        if name == "files.find":
            self.log.append((name, a))
            q = a.get("q", "").lower()
            return {"entries": [f for f in FILES if q in f["path"].lower()]}
        if name == "ideas.pickables":
            self.log.append((name, a))
            return {"party": a["party"], "map": "game-design", "parts": copy.deepcopy(PARTS)}
        return super().handle(name, a)


def _open_field(pg):
    _plus(pg).wait_for(timeout=WAIT_MS)
    for _ in range(3):                                   # a press while the hand is still being dealt (a loaded machine) may land before the card is there: press again
        _plus(pg).click(position={"x": 8, "y": 60})
        try:
            pg.locator(".hand-field").wait_for(timeout=WAIT_MS // 3)
            break
        except Exception:
            continue
    return _field(pg)


def _rows(pg):
    return pg.locator(".hand-mention__row").evaluate_all("els => els.map((e) => e.innerText.replace(/\\s+/g, ' ').trim())")


def _rows_are(pg, want):
    """The list shows exactly `want` (a moment is given: the page draws after the keys)."""
    try:
        pg.wait_for_function("(want) => JSON.stringify([...document.querySelectorAll('.hand-mention__row')].map((e) => e.innerText.replace(/\\s+/g, ' ').trim())) === JSON.stringify(want)", arg=want, timeout=WAIT_MS)
    except Exception:
        raise AssertionError(f"the list shows {_rows(pg)}, not {want}") from None


def test_at_offers_the_parties_and_enter_takes_the_first_without_sending(gui):
    pg, host, log = open_hand(gui, host=MentionHost())
    try:
        field, area = _open_field(pg)
        area.type("Fix it @Te")
        pg.locator(".hand-mention").wait_for(timeout=WAIT_MS)
        assert _rows(pg)[0] == "@Tech" and pg.locator(".hand-mention__row").count() <= 8
        area.press("Enter")                                                          # takes the party: the list had the key, nothing was sent
        assert area.input_value() == "Fix it @Tech " and not host.added
        assert pg.locator(".hand-chip[data-by='text']").inner_text().strip().startswith("Tech"), "the address chip follows the text"
        area.type("now")
        assert pg.locator(".hand-mention").count() == 0
        area.press("Enter")                                                          # no list: it sends, as always
        assert _sent(pg, host, ("ideas.add", {"text": "Fix it now", "party": "tech"}))
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_arrows_move_tab_takes_and_esc_closes_the_list_only(gui):
    pg, host, log = open_hand(gui, host=MentionHost())
    try:
        field, area = _open_field(pg)
        area.type("@")
        pg.locator(".hand-mention").wait_for(timeout=WAIT_MS)
        _rows_are(pg, ["@Tech", "@Design", "@Product", "@Release", "@Game design", "src/", "src/app.py", "README.md"])
        area.press("ArrowDown")
        area.press("ArrowDown")
        assert pg.locator(".hand-mention__row.is-on").inner_text().strip() == "@Product"
        area.press("ArrowUp")
        assert pg.locator(".hand-mention__row.is-on").inner_text().strip() == "@Design"
        area.press("Escape")
        assert pg.locator(".hand-mention").count() == 0 and pg.locator(".hand-field").count() == 1, "Esc closed the list, not the field"
        area.type("D")
        assert pg.locator(".hand-mention").count() == 0, "the list stays closed for this @"
        area.press("Control+a")
        area.type("a @De")
        pg.locator(".hand-mention").wait_for(timeout=WAIT_MS)
        area.press("Tab")
        assert area.input_value() == "a @Design "
        area.press("Escape")                                                        # Design's second step (the stub gives every party parts) is a list too: Esc closes it first
        area.press("Escape")
        assert pg.locator(".hand-field").count() == 0, "Esc with no list closes the field"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_an_at_in_a_word_is_no_mention_and_a_file_is_offered_and_written(gui):
    pg, host, log = open_hand(gui, host=MentionHost())
    try:
        field, area = _open_field(pg)
        area.type("write to me@exa")
        pg.wait_for_timeout(200)
        assert pg.locator(".hand-mention").count() == 0
        area.press("Control+a")
        area.type("Look at @app")
        pg.locator(".hand-mention__row[data-kind='file']").wait_for(timeout=WAIT_MS)
        _rows_are(pg, ["src/app.py"])
        assert _calls(pg, host, "files.find")[-1] == {"q": "app", "limit": 20}
        area.press("Enter")
        assert area.input_value() == "Look at @src/app.py "
        area.press("Enter")
        assert _sent(pg, host, ("ideas.add", {"text": "Look at @src/app.py"}))                 # the host turns the path into `path` (realm/goal_mentions.py)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_who_then_what_then_on_what_a_type_and_a_part_of_its_map(gui):
    pg, host, log = open_hand(gui, host=MentionHost())
    try:
        field, area = _open_field(pg)
        area.type("@Game des")
        pg.locator(".hand-mention__row").first.wait_for(timeout=WAIT_MS)
        _rows_are(pg, ["@Game design"])
        area.press("Enter")
        assert area.input_value() == "@Game design "
        _rows_are(pg, ["New mechanic", "Balance pass", "Spawn", "Loot"])
        assert _calls(pg, host, "ideas.pickables")[-1] == {"party": "game"}
        area.type("mech")                                                           # filtered by what is typed after the party
        _rows_are(pg, ["New mechanic"])
        area.press("Enter")
        chip = pg.locator(".hand-chip[data-type='mechanic']")
        assert chip.inner_text().strip() == "New mechanic" and chip.locator(".ork-sign.mechanic").count() == 1
        assert area.input_value() == "@Game design ", "the type is never a word in the text"
        _rows_are(pg, ["Balance pass", "Spawn", "Loot"])                           # what was taken is not offered again
        pg.locator(".hand-mention__row[data-kind='part']").first.click()           # a part of its map: a mark, a chip as a picked card's
        assert pg.locator(".pick-chip[data-map='game-design'][data-mark='spawn']").count() == 1
        assert area.input_value() == "@Game design "
        area.type("Add a dash")
        assert pg.locator(".hand-mention").count() == 0
        area.press("Enter")
        assert _sent(pg, host, ("ideas.add", {"text": "Add a dash", "party": "game", "type": "mechanic", "marks": [{"map": "game-design", "id": "spawn", "name": "Spawn", "group": "loop"}]}))
        pg.wait_for_function("() => !document.querySelector('.hand-field')", timeout=WAIT_MS)
        _plus(pg).click(position={"x": 8, "y": 60})
        _field(pg)
        assert pg.locator(".hand-chip[data-type]").count() == 0 and pg.locator(".pick-chip").count() == 0, "the type and the marks are sent with the goal"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_backspace_on_the_empty_second_step_goes_back_to_the_parties_and_a_type_chip_comes_off(gui):
    pg, host, log = open_hand(gui, host=MentionHost())
    try:
        field, area = _open_field(pg)
        area.type("@Game design ")
        pg.locator(".hand-mention__row[data-kind='type']").first.wait_for(timeout=WAIT_MS)
        area.press("Backspace")
        pg.wait_for_function("() => document.querySelector('.hand-mention__row')?.dataset.kind === 'party'", timeout=WAIT_MS)
        _rows_are(pg, ["@Game design"])
        area.press("Enter")
        pg.locator(".hand-mention__row[data-kind='type']").first.click()
        chip = pg.locator(".hand-chip[data-type='mechanic']")
        assert chip.count() == 1
        chip.get_by_role("button").click()
        assert pg.locator(".hand-chip[data-type]").count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_word_that_names_a_type_offers_it_with_its_party_and_takes_both(gui):
    pg, host, log = open_hand(gui, host=MentionHost())
    try:
        field, area = _open_field(pg)
        area.type("@mech")
        pg.locator(".hand-mention__row[data-kind='ptype']").wait_for(timeout=WAIT_MS)
        _rows_are(pg, ["New mechanic Game design"])
        area.press("Enter")
        assert area.input_value() == "@Game design " and pg.locator(".hand-chip[data-type='mechanic']").count() == 1
        area.type("A double jump")
        area.press("Enter")
        assert _sent(pg, host, ("ideas.add", {"text": "A double jump", "party": "game", "type": "mechanic"}))
    finally:
        pg.close()
    assert not log, "\n".join(log)


# -- J: the bug under the glass -----------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_the_logs_button_ends_the_tabs_row_after_stop_all_opens_its_panel_downward_and_saves_with_the_line(gui, width):
    pg, host, log = open_hand(gui, host=MentionHost(), width=width)
    try:
        button = pg.locator(".table-tabs__end .table-logs")
        button.wait_for(timeout=WAIT_MS)
        assert pg.locator(".hand .table-logs, .hand-end .table-logs").count() == 0, "not in the hand any more (decisions §190.6)"
        assert button.get_attribute("aria-label") == "Save the logs" and button.get_attribute("title") == "Save the logs" and button.inner_text().strip() == "", "an icon with no word"
        assert button.locator(".ork-sign.bug").count() == 1 and button.locator("svg.ork-icon use").get_attribute("href").endswith("#search")
        b, stop = button.bounding_box(), pg.locator(".table-stop").bounding_box()
        assert b["x"] >= stop["x"] + stop["width"] - 1, "after Stop all"
        button.click()
        panel = pg.locator(".table-logs__panel")
        panel.wait_for(timeout=WAIT_MS)
        assert "What went wrong? (optional)" in panel.inner_text() and panel.locator("input").evaluate("e => e === document.activeElement")
        p, size = panel.bounding_box(), pg.viewport_size
        assert p["y"] >= b["y"] + b["height"] - 1, "under the button"
        assert p["x"] >= 0 and p["x"] + p["width"] <= size["width"] + 1 and p["y"] + p["height"] <= size["height"], "inside the window"
        pg.keyboard.press("Escape")
        assert pg.locator(".table-logs__panel").count() == 0
        button.click()
        pg.mouse.click(size["width"] / 2, size["height"] - 200)
        assert pg.locator(".table-logs__panel").count() == 0, "a press away closes it"
        button.click()
        panel.locator("input").fill("The timer froze")
        panel.get_by_role("button", name="Save logs").click()
        assert any("The timer froze" in a.get("said", "") for a in _calls(pg, host, "logs.save"))
        assert pg.locator(".table-logs__panel").count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_logs_button_is_there_with_no_mana_and_with_no_goal(gui):
    for empty in (False, True):
        host = MentionHost(empty=empty)
        host.limits = []
        pg, host, log = open_hand(gui, host=host)
        try:
            pg.locator(".table-logs").wait_for(timeout=WAIT_MS)
            assert pg.locator(".table-logs").count() == 1
            pg.locator(".table-logs").click()
            pg.locator(".table-logs__panel").wait_for(timeout=WAIT_MS)
        finally:
            pg.close()
        assert not log, "\n".join(log)


# -- M: New goal's frame, never under another card ----------------------------------------------------------------------------------------------

@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_new_goal_is_framed_and_lies_under_no_other_card(gui, width):
    for extra in (False, True):
        pg, host, log = open_hand(gui, host=MentionHost(extra=extra), width=width)
        try:
            pg.locator(".hand-stack").first.wait_for(timeout=WAIT_MS)
            pg.wait_for_timeout(700)
            plus = _plus(pg)
            box = plus.bounding_box()
            style = plus.evaluate("e => { const s = getComputedStyle(e); return [s.borderTopStyle, s.borderTopWidth, s.backgroundImage.includes('repeating-linear-gradient'), getComputedStyle(e, '::after').backgroundImage.includes('linear-gradient')] }")
            assert style[0] == "double" and style[1] == "3px" and not style[2] and style[3], style                        # the double frame and the corner brackets; the hatch is gone (spec 110, decisions §185.4)
            others = pg.locator(".hand .hand-card, .hand .hand-back:not(.edge), .hand .hand-stack > .hand-back.edge").evaluate_all(
                "els => els.map((e) => { const r = e.getBoundingClientRect(); return [r.x, r.y, r.width, r.height]; })")
            slack = 6                                                        # turned a little (§167.5): a corner reaches a few pixels
            for x, y, w, h in others:
                apart = x >= box["x"] + box["width"] - slack or x + w <= box["x"] + slack or y >= box["y"] + box["height"] - slack or y + h <= box["y"] + slack
                assert apart, f"a card at {(x, y, w, h)} lies under New goal {box}"
            top = plus.evaluate("e => { const r = e.getBoundingClientRect(); const el = document.elementFromPoint(r.x + r.width / 2, r.y + 30); return el === e || e.contains(el); }")
            assert top, "nothing lies over it"
            first = pg.locator(".hand-lane").first.locator(".hand-slot")
            assert "is-plus" in first.first.get_attribute("class") and first.count() == (3 if extra else 1)
        finally:
            pg.close()
        assert not log, "\n".join(log)


def test_the_plus_card_stands_still_under_reduced_motion(gui):
    server, browser = gui
    ctx = browser.new_context(**narrow.WIDE, reduced_motion="reduce")
    pg = ctx.new_page()
    host = MentionHost()
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    try:
        _plus(pg).wait_for(timeout=WAIT_MS)
        _plus(pg).hover()
        pg.wait_for_timeout(300)
        assert _plus(pg).evaluate("e => getComputedStyle(e, '::before').animationName") == "none"
    finally:
        pg.close()
