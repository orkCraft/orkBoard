"""Spec 168 A3 (decisions §283.5): nothing changes size by what is open. The Orkmaster's column, the table, the discard's column and the hand keep their boxes with nothing open, a goal picked, a card lifted,
the inventory open and Settings open (the carried cards lie in the hand's shown height, cut by its rim; a form over the pane keeps the discard's column). 1280 × 800 against the stall's stub host."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import call, open_hand  # noqa: E402
from tests.test_night_card_browser import open_settings  # noqa: E402
from tests.test_stall_browser import StallHost  # noqa: E402

pytestmark = pytest.mark.browser

BOXES = """() => Object.fromEntries([[".frame-column", "column"], [".frame-table", "table"], [".release-lane", "discard"], [".hand", "hand"]].map(([sel, name]) => {
  const el = document.querySelector(sel); if (!el) return [name, null];
  const b = el.getBoundingClientRect(); return [name, [b.x, b.y, b.width, b.height].map((v) => Math.round(v * 10) / 10)];
}))"""


def boxes(pg):
    pg.wait_for_timeout(500)                                                  # the springs and the slides settle
    return pg.evaluate(BOXES)


def test_the_four_boxes_are_the_same_whatever_is_open(gui):
    pg, host, log = open_hand(gui, host=StallHost())
    try:
        pg.locator(".hand-card").first.wait_for(timeout=WAIT_MS)
        pg.locator(".release-lane").wait_for(timeout=WAIT_MS)
        rest = boxes(pg)
        assert all(rest.values()), rest
        slug = pg.evaluate("() => import('/static/js/shell/store.js').then((m) => (m.mapData.value.nodes || [])[0].slug)")
        call(pg, "frame/state.js", "pick", slug)
        assert boxes(pg) == rest, "a goal picked"
        call(pg, "frame/state.js", "pick", slug)
        pg.locator(".hand-card").first.click()
        pg.locator(".hand-lifted").first.wait_for(timeout=WAIT_MS)
        assert boxes(pg) == rest, "a card lifted"
        call(pg, "frame/state.js", "lower")
        pg.locator("[data-backpack]").click()
        pg.locator(".slots-table .slot-card").first.wait_for(timeout=WAIT_MS)
        assert boxes(pg) == rest, "the inventory open"
        assert pg.locator(".hand .carry, .hand .carry-card").count() == 0, "no card is carried (spec 168 H1)"
        pg.locator(".slots-table .slot-card").first.click()                                                      # a slot pressed deals its ways to the hand: the four boxes keep their size
        pg.locator(".hand .slot-way").first.wait_for(timeout=WAIT_MS)
        assert boxes(pg) == rest, "a slot's ways dealt"
        pg.locator('.hand [data-act="put"]').click()                                                             # the hand is sunk while a card is played, its places inert as for every card played: it goes back first
        pg.locator(".hand .slot-way").first.wait_for(state="detached", timeout=WAIT_MS)
        pg.locator("[data-backpack]").click()
        pg.locator(".slots-table").wait_for(state="detached", timeout=WAIT_MS)
        open_settings(pg)
        assert pg.locator(".release-lane").count() == 1
        assert boxes(pg) == rest, "Settings open"
    finally:
        pg.close()
    assert not log, "\n".join(log)
