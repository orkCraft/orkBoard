"""The piles' words in the page are the glossary's (realm/lexicon.py `column_reading`, `next_in`, `next_at`): table/stages.js writes them as constants, which the phone's menu
(hand/uppiles.js, table/piles.js) reads."""
from __future__ import annotations

import re
from pathlib import Path

from orkboard.realm import lexicon

PILES_JS = Path(__file__).resolve().parents[1] / "orkboard" / "gui" / "static" / "js" / "table" / "stages.js"


def test_the_pages_column_words_are_the_glossarys():
    js = PILES_JS.read_text(encoding="utf-8")
    got = dict(re.findall(r'(\w+) = "([^"]+)"', re.search(r"export const (READING = .*?);", js).group(1).replace(", ", ";\n")))
    assert got == {"READING": lexicon.term("column_reading"), "NEXT_IN": lexicon.term("next_in"), "NEXT_AT": lexicon.term("next_at")}
