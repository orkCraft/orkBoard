"""Spec 168 A5 (decisions §285.3): the hand's right end holds the places that change the table, the die (*Play*), the backpack (*Inventory*) and the book (*History*), one size (a box of 48 × 60 each, the same top), each drawn open while its table is on;
the backpack opens the inventory, the book the history over the pane, the die the play view; they sink with the hand's row while a card is lifted. Under 760 px the places stay as they were (the backpack at the tabs' end, no book). Against the stall's stub host."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import open_hand  # noqa: E402
from tests.test_stall_browser import StallHost  # noqa: E402

pytestmark = pytest.mark.browser

BOXES = ".hand-die__box, .hand-end .stall-pack .place-box, .hand-end .hand-book .place-box"
WORDS = ".hand-end .hand-die__word, .hand-end .stall-pack__word, .hand-end .hand-book__word"


def boxes(pg):
    return pg.locator(BOXES).evaluate_all("els => els.map((e) => { const b = e.getBoundingClientRect(); return [Math.round(b.x), Math.round(b.y), Math.round(b.width * 10) / 10, Math.round(b.height * 10) / 10]; })")


def test_the_three_places_are_one_size_with_their_words_under_them_at_the_hands_right_end(gui):
    pg, host, log = open_hand(gui, host=StallHost())
    try:
        pg.locator(".hand-book").wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(300)
        b = boxes(pg)
        assert len(b) == 3 and all(x[2:] == [48, 60] for x in b), b                                                                  # a box of 48 × 60 each
        assert len({x[1] for x in b}) == 1 and b[0][0] < b[1][0] < b[2][0], "the die, the backpack, the book: side by side, the same top"
        assert pg.locator(WORDS).all_inner_texts() == ["Play", "Inventory", "History"]
        words = pg.locator(WORDS).evaluate_all("els => els.map((e) => Math.round(e.getBoundingClientRect().y))")
        assert len(set(words)) == 1 and words[0] >= b[0][1] + 60, "each word under its box"
        end, vw = pg.locator(".hand-end").bounding_box(), pg.viewport_size["width"]
        assert end["x"] + end["width"] <= vw + 1 and all(x[0] + x[2] <= vw for x in b)
        assert pg.locator(".release-lane__head .stall-pack, .release-lane__head .hand-book").count() == 0, "none in the column's head"
        assert pg.locator(".hand-end .ork-die.small").count() == 1 and pg.locator(".hand-end .ork-pack").evaluate("e => [e.offsetWidth, e.offsetHeight]") == [42, 54] and pg.locator(".hand-end .ork-book").evaluate("e => [e.offsetWidth, e.offsetHeight]") == [48, 50]
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_backpack_opens_the_inventory_the_book_the_past_and_each_is_drawn_open_while_its_table_is_on(gui):
    pg, host, log = open_hand(gui, host=StallHost())
    try:
        pg.locator(".hand-book").wait_for(timeout=WAIT_MS)
        assert pg.locator(".ork-pack.is-open, .ork-book.is-open").count() == 0
        pg.locator("[data-backpack]").click()                                                                                      # the inventory
        pg.locator(".stall").wait_for(timeout=WAIT_MS)
        assert pg.locator(".hand-end .ork-pack.is-open").count() == 1 and pg.locator(".ork-book.is-open").count() == 0
        pg.locator("[data-book]").click()                                                                                          # the history takes the pane
        pg.locator('.table-over[data-kind="history"]').wait_for(timeout=WAIT_MS)
        assert pg.locator(".hand-end .ork-book.is-open").count() == 1 and pg.locator("[data-book]").get_attribute("aria-pressed") == "true"
        assert pg.locator(".table-over .hist").count() == 1 and pg.locator(".table-over input[type=search]").count() == 1, "the history, with its search"
        pg.wait_for_timeout(300)
        assert len({x[1] for x in boxes(pg)}) == 1 and all(x[2:] == [48, 60] for x in boxes(pg)), "nothing changes size while a table is on"
        pg.locator("[data-book]").click()                                                                                          # again: shut
        pg.locator('.table-over[data-kind="history"]').wait_for(state="detached", timeout=WAIT_MS)
        assert pg.locator(".ork-book.is-open").count() == 0
        pg.locator(".hand-die__play").click()                                                                                      # the die: the play view, the die open
        pg.locator('.table-over[data-kind="play"]').wait_for(timeout=WAIT_MS)
        assert pg.locator(".hand-die").get_attribute("data-open") == "1" and pg.locator(".ork-book.is-open").count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_places_sink_with_the_hand_while_a_card_is_lifted(gui):
    pg, host, log = open_hand(gui, host=StallHost())
    try:
        pg.locator(".hand-book").wait_for(timeout=WAIT_MS)
        pg.locator('.hand-card[data-kind="failed"]').first.click(position={"x": 10, "y": 24})
        pg.locator(".hand-lifted").wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(300)
        assert pg.locator(".hand-row.is-sunk .hand-end .hand-book").count() == 1 and pg.locator(".hand-row[inert]").count() == 1, "the places lie in the sunk, inert row"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_under_760_px_the_places_stay_as_they_were(gui):
    pg, host, log = open_hand(gui, host=StallHost(), width="narrow")
    try:
        pg.locator(".hand-die").wait_for(timeout=WAIT_MS)
        assert pg.locator(".hand-book, [data-book]").count() == 0
        assert pg.locator(".table-tabs__end .stall-pack").count() == 1 and pg.locator(".hand-end .stall-pack").count() == 0, "the backpack at the tabs' end"
        narrow.no_sideways(pg)
    finally:
        pg.close()
    assert not log, "\n".join(log)
