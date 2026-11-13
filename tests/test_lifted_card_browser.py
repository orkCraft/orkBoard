"""A lifted card is a card (docs/specs/104 §5, decisions §176.4), in a real browser against the hand's stub host at the two widths of `tests/narrow.py`: the hand card's frame and anatomy at twice its width (the screen's width
less a gutter a side at the narrow one), turned a degree or two, its foot on the hand's line, its body between the window and the foot holding the answers, the cost's words and *Put it back*, scrolling inside at the card's
most height and never growing wider; the focus on it, Esc lowering it. Screenshots to $LIFT_SHOTS when it is set. At the wide width a lifted question or failure is no opened card but a hand card with its ways as cards (decisions §270, spec 158 F: tests/test_answer_cards_browser.py); the opened card stays for the rest of the kinds and for the narrow page."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["LIFT_SHOTS"]) if os.environ.get("LIFT_SHOTS") else None
LONG = " ".join(["The timer does not reset after a reconnect, so every phone that joins late shows the old round and the host has to restart the room by hand."] * 14)



class LongHost(HandHost):
    """The hand's host with a failed task whose error is far longer than a card."""

    def __init__(self):
        super().__init__()
        for n in self.nodes:
            if n["slug"] == "timer":
                n["tasks"][0]["error"] = LONG


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


def lift(pg, kind):
    pg.locator(f'.hand-card[data-kind="{kind}"]').first.click(position={"x": 10, "y": 20})
    card = pg.locator(".hand-lifted")
    card.wait_for(timeout=WAIT_MS)
    pg.wait_for_timeout(250)
    return card






















def test_the_opened_cards_words_are_the_glossarys():
    import re
    from orkboard.realm import lexicon
    js = (Path(__file__).resolve().parents[1] / "orkboard/gui/static/js/hand/openwords.js").read_text(encoding="utf-8")
    got = dict(re.findall(r'(\w+) = "([^"]+)"', re.search(r"export const (SLOT_RUNE = .*?);\n", js).group(1)))
    assert got == {"SLOT_RUNE": lexicon.term("slot_rune"), "SLOT_WHO": lexicon.term("slot_who"), "SLOT_KIND": lexicon.term("slot_kind"), "NOW": lexicon.term("now"), "LATER": lexicon.term("later"), "SLOT_MUCH": lexicon.term("slot_much"), "ATTACH_HINT": lexicon.term("attach_hint"), "LEADER": lexicon.term("opened_leader"), "ASKS": lexicon.term("opened_asks")}
