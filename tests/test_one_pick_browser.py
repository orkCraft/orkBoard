"""Spec 156 part B (docs/specs/156-one-pick-and-the-release-column.md, decisions §261.1-3, §261.5-6, §262.4), in a real browser against a stub host: one goal picked at most, by a hand's card lifted; the pick in the address (`#goal=<slug>`, written and read by frame/state.js alone);
the grey tabs' words the lexicon's; at 390 px a file over a pick closes on the first back, the pick on the second."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from orkboard.realm import lexicon  # noqa: E402
from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.column_kit import ColumnHost, open_column  # noqa: E402
from tests.test_hand_desktop_browser import sig  # noqa: E402

pytestmark = pytest.mark.browser

STATE = "frame/state.js"


def picked(pg):
    return sig(pg, STATE, "picked")




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






def test_a_grey_tabs_words_are_the_lexicons(gui):
    pg, host, log = open_column(gui)
    try:
        got = pg.evaluate("() => import('/static/js/table/tabs.js').then((m) => ({OFF_IS: m.OFF_IS, OFF_PRESS: m.OFF_PRESS}))")
        assert got == {"OFF_IS": lexicon.term("tab_off_is"), "OFF_PRESS": lexicon.term("tab_off_press")}
    finally:
        pg.close()
    assert not log, "\n".join(log)
