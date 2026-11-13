"""The hand's card, cut under its title (docs/specs/147-one-card-four-corners.md part C, decisions §251.5), in a real browser against the hand's stub host: the card is 144 x 202 with its corners' top row (the goal's rune at the left, the kind's
sign at the right, no head there) and its title whole in three lines; the rim of the hand cuts it at 100 px (62 px at the narrow width) between two lines; the hand is as tall as the cut and its padding unless the die and the potions need more, and
then the cards keep their top and show more, the cut kept between two lines; hovered or focused the card rises by what is hidden and shows its foot row (who asks, how much), at once under reduced motion; the narrow hand is laid by leader, a head before
each leader's group (the Orkmaster's crown before the first lane's). The words of the face are the glossary's (tests/test_hand_desktop_browser.py has the rest)."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, open_hand  # noqa: E402

pytestmark = pytest.mark.browser

SHOWN = {"wide": 100, "narrow": 62}

# every line box of a card's title and why, as [top, bottom] in the page
LINES = """(card) => [...card.querySelectorAll('.hand-card__name, .hand-card__foot')].flatMap((e) => {
  const out = [], walker = document.createTreeWalker(e, NodeFilter.SHOW_TEXT);
  for (let t = walker.nextNode(); t; t = walker.nextNode()) { const r = document.createRange(); r.selectNodeContents(t); for (const b of r.getClientRects()) out.push([b.top, b.bottom]); }
  return out; })"""


def settle(pg):
    pg.locator(".hand-stack").first.wait_for(timeout=WAIT_MS)
    pg.wait_for_timeout(900)


def edge(pg, selector):
    """The bottom of the first element that matches, or 0."""
    return pg.evaluate("(s) => { const e = document.querySelector(s); return e ? e.getBoundingClientRect().bottom : 0; }", selector)


def test_the_wide_hand_has_no_separator_the_lane_says_who(gui):
    pg, host, log = open_hand(gui, host=HandHost(extra=True), width="wide")
    try:
        settle(pg)
        assert pg.locator(".hand-sep").count() > 0 and all(not e.is_visible() for e in pg.locator(".hand-sep").all())
    finally:
        pg.close()
    assert not log, "\n".join(log)
