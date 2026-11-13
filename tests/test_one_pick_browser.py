"""Spec 156 part B (docs/specs/156-one-pick-and-the-release-column.md, decisions §261.1-3, §261.5-6, §262.4), in a real browser against a stub host: one goal picked at most, by a hand's card lifted; the pick in the address (`#goal=<slug>`, written and read by frame/state.js alone);
the grey tabs' words the lexicon's; at 390 px a file over a pick closes on the first back, the pick on the second."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from orkboard.realm import lexicon  # noqa: E402
from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.column_kit import ColumnHost, open_column  # noqa: E402
from tests.test_hand_desktop_browser import HandHost, call, open_hand, sig  # noqa: E402

pytestmark = pytest.mark.browser

STATE = "frame/state.js"


def picked(pg):
    return sig(pg, STATE, "picked")


def hash_of(pg):
    return pg.evaluate("() => location.hash")


def press(pg, slug):
    """A press on a goal's card; the backs of the hand overlap, so one is pressed at its left edge."""
    card = pg.locator(f'.col-card[data-goal="{slug}"]')
    if "col-card--fan" in card.get_attribute("class"):
        card.click(position={"x": 6, "y": 40})
    else:
        card.click()


def wait_picked(pg, slug):
    pg.wait_for_function("(s) => import('/static/js/frame/state.js').then((m) => m.picked.value === s)", arg=slug, timeout=WAIT_MS)


def test_the_address_is_read_on_load_and_a_goal_the_snapshot_has_not_reads_as_none(gui):
    server, browser = gui
    for slug, want in (("raw2", "raw2"), ("nowhere", "")):
        pg = narrow.page(browser, "wide")
        host = ColumnHost()
        pg.route_web_socket("**/ws*", host.on_socket)
        pg.goto(f"{server.url}#goal={slug}")
        pg.wait_for_selector(".hand :is(.hand-plus, [data-blank-deck])", timeout=WAIT_MS)
        try:
            wait_picked(pg, want)
            pg.wait_for_function("(h) => location.hash === h", arg=f"#goal={want}" if want else "", timeout=WAIT_MS)
        finally:
            pg.close()


def test_a_hands_card_lifted_picks_its_goal_and_its_lowering_leaves_the_pick_and_the_goals_cards_wear_the_ink_edge(gui):
    pg, host, log = open_hand(gui, host=HandHost(), width="wide")
    try:
        pg.locator(".hand-stack").first.wait_for(timeout=WAIT_MS)
        pg.locator('.table-tab[data-tab="design"]').click()
        stack = pg.locator('.hand-stack[data-goal="timer"]')
        stack.locator(".hand-card").first.click()
        wait_picked(pg, "timer")
        assert hash_of(pg) == "#goal=timer"
        assert sig(pg, STATE, "tab") == "tech", "the failure is Tech's: the card in play opens its asker's tab (spec 168 D1, decisions §283.19), as the pick leaves it"
        card = stack.locator(".hand-card").first
        assert "ork-picked" in card.get_attribute("class").split(), "the picked goal's cards in the hand wear the ink edge"
        assert card.evaluate("e => getComputedStyle(e).borderTopColor") == pg.evaluate("() => { const s = document.createElement('i'); s.style.color = 'var(--ork-ink)'; document.body.append(s); const c = getComputedStyle(s).color; s.remove(); return c; }")
        pg.get_by_role("button", name="Put it back").click()                            # lowered (the lifted card is the table's now, decisions §270.1: it is put back by its button, not pressed again)
        pg.locator(".hand-lifted").wait_for(state="detached", timeout=WAIT_MS)
        assert picked(pg) == "timer", "its lowering leaves the pick"
        assert pg.locator(".hand-stack.is-picked").count() >= 1
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_at_390_px_a_file_over_a_pick_closes_on_the_first_back_and_the_pick_on_the_second(gui):
    pg, host, log = open_hand(gui, host=ColumnHost(), width="narrow")
    try:
        pg.locator(".hand").first.wait_for(timeout=WAIT_MS)
        call(pg, STATE, "pick", "raw1")
        wait_picked(pg, "raw1")
        assert hash_of(pg) == "#goal=raw1"
        pg.evaluate("() => import('/static/js/frame/state.js').then((m) => m.openOver('file', {path: 'README.md'}, {title: 'Board', key: ''}, 'README.md'))")
        pg.locator(".table-over").wait_for(timeout=WAIT_MS)
        pg.go_back()
        pg.wait_for_function("() => !document.querySelector('.table-over')", timeout=WAIT_MS)
        assert picked(pg) == "raw1" and hash_of(pg) == "#goal=raw1", "the first back closes the file only"
        pg.go_back()
        wait_picked(pg, "")
        assert hash_of(pg) == "", "the second back puts the pick away"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_grey_tabs_words_are_the_lexicons(gui):
    pg, host, log = open_column(gui)
    try:
        got = pg.evaluate("() => import('/static/js/table/tabs.js').then((m) => ({OFF_IS: m.OFF_IS, OFF_PRESS: m.OFF_PRESS}))")
        assert got == {"OFF_IS": lexicon.term("tab_off_is"), "OFF_PRESS": lexicon.term("tab_off_press")}
    finally:
        pg.close()
    assert not log, "\n".join(log)
