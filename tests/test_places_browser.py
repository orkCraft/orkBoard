"""Spec 168 A5 (decisions §285.3): the hand's right end holds the places that change the table, the die (*Play*), the backpack (*Inventory*) and the book (*History*), one size (a box of 48 × 60 each, the same top), each drawn open while its table is on;
the backpack opens the inventory, the book the history over the pane, the die the play view; they sink with the hand's row while a card is lifted. Under 760 px the places stay as they were (the backpack at the tabs' end, no book). Against the stall's stub host."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import open_hand  # noqa: E402
from tests.test_stall_browser import StallHost  # noqa: E402

pytestmark = pytest.mark.browser

BOXES = ".hand-die__box, .hand-end .stall-pack .place-box, .hand-end .hand-book .place-box"
WORDS = ".hand-end .hand-die__word, .hand-end .stall-pack__word, .hand-end .hand-book__word"


def boxes(pg):
    return pg.locator(BOXES).evaluate_all("els => els.map((e) => { const b = e.getBoundingClientRect(); return [Math.round(b.x), Math.round(b.y), Math.round(b.width * 10) / 10, Math.round(b.height * 10) / 10]; })")




def test_the_backpack_opens_the_inventory_the_book_the_past_and_each_is_drawn_open_while_its_table_is_on(gui):
    pg, host, log = open_hand(gui, host=StallHost())
    try:
        pg.locator(".hand-book").wait_for(timeout=WAIT_MS)
        assert pg.locator(".ork-pack.is-open, .ork-book.is-open").count() == 0
        pg.locator("[data-backpack]").click()                                                                                      # the inventory
        pg.locator(".slots-table").wait_for(timeout=WAIT_MS)
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




