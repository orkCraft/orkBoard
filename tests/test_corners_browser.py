"""A card's four corners (docs/specs/147-one-card-four-corners.md part A, decisions §251.2), in a real browser: a lane's card and the discard's card have one top row (the goal's rune first, the kind's sign last) and one foot row (who, how much);
a sign is 14 px and a head 16 on every card; a lane's card is 5 : 7 at the frame's card width. The bottom right's one figure (`muchOf`: the spend, decisions §283.17, which changes §251.2's time; the time is in the preview and the tooltip) and the words of the corners (realm/lexicon.py `corner_*`) are kept here too."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from orkboard.realm import lexicon  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_table_desktop_browser import start  # noqa: E402

CORNERS_JS = Path(__file__).resolve().parents[1] / "orkboard" / "gui" / "static" / "js" / "table" / "corners.js"






@pytest.fixture
def table(gui):
    errors: list[str] = []
    pg, host = start(gui, "wide", errors)
    yield pg, host
    pg.context.close()
    assert not errors, "\n".join(errors)




@pytest.mark.browser
def test_the_pages_corner_words_are_the_glossarys():
    js = CORNERS_JS.read_text(encoding="utf-8")
    got = dict(re.findall(r'(\w+) = "([^"]+)"', re.search(r"export const (ASKS = .*?);", js).group(1).replace(", ", ";\n")))
    assert got == {"ASKS": lexicon.term("corner_asks"), "LEFT": lexicon.term("corner_left"), "TOOK": lexicon.term("corner_took"), "WORKED": lexicon.term("corner_worked"), "IN_MAIN": lexicon.term("corner_in_main"), "TOK": lexicon.term("corner_tokens"), "ESTIMATE": lexicon.term("corner_estimate")}
