"""`realm/idea_page.py` and the spec's new format (docs/specs/99-a-goals-way.md §7.1): a page of the new format answers for the old sections it lacks, so what reads the old names
(today's plan) reads it; a page of before is read as it always was."""
from __future__ import annotations

from orkboard.realm import idea_page

NEW = """---
owner: board
---
# Goal

## Gist
One line

## Why

## Done when

## Tech
### Why
Because.

### Done when
- It works

### Out
- No scheduling

## Art
### Why
Look.

### Done when
- Pretty
"""


def test_a_page_of_before_is_read_as_it_always_was():
    p = idea_page.parse("---\nowner: board\n---\n# Goal\n\n## Gist\nG\n\n## Why\nOld why.\n\n## Done when\n- old\n")
    assert p.section("Why") == "Old why." and p.section("Done when") == "- old" and p.section("Out") == "" and p.parts("Why") == {}


def test_a_page_of_the_new_format_answers_for_the_old_sections_it_lacks_by_its_first_section():
    p = idea_page.parse(NEW)
    assert p.section("Why") == "Because." and p.section("Out") == "- No scheduling" and p.section("Risks") == ""
    assert p.section("Done when") == "- It works\nArt: Pretty" and p.section("Gist") == "One line"                    # an empty old section is answered for; a section the page has is its own
    assert p.parts("Tech") == {"Why": "Because.", "Done when": "- It works", "Out": "- No scheduling"} and p.parts("Gist") == {}


def test_an_old_section_with_words_is_never_overridden_and_the_text_is_written_back_whole():
    p = idea_page.parse(NEW)
    p.set_section("Risks", "Risk: Low")
    assert p.section("Risks") == "Risk: Low"
    again = idea_page.parse(p.text())
    assert [n for n, _t in again.sections] == [n for n, _t in p.sections] and again.section("Tech").count("### ") == 3
