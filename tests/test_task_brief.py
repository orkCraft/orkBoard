"""Spec 99 §9.3 (docs/specs/99-a-goals-way.md; decisions §118.5, §156.13) on `realm/task_brief.py`: a plan and a task read a spec's common part, their party's section whole, and of
the others only *Done when* and *Will be*; a page of before is read as it was. Pure code."""
from __future__ import annotations

from orkboard.realm import idea_page, spec_sections, task_brief

PAGE = """---
owner: board
track: design
---
# Dark mode

## Asked
add a dark mode

## Gist
Dark mode as a setting

## Route
1. Design
2. Tech

## Design
### Why
Design's why.

### Done when
- A settings screen

### Will be
changed ui/settings — the toggle

### Out
- Icons

## Tech
### Why
Tech's why.

### Done when
- The theme is one file

### Checks
- A test

### Will be
new src/theme
"""


def page():
    return idea_page.parse(PAGE)


def test_a_section_reads_the_common_part_its_own_whole_and_of_the_others_their_contract():
    got = task_brief.reading(page(), "Tech")
    assert list(got["common"]) == ["Asked", "Gist", "Route"] and got["common"]["Asked"] == "add a dark mode"
    assert got["own"][0] == "Tech" and "Tech's why." in got["own"][1] and "### Checks" in got["own"][1]                     # whole
    (other,) = got["others"]
    assert other[0] == "Design" and other[1] == "### Done when\n- A settings screen\n\n### Will be\nchanged ui/settings — the toggle"
    assert "Design's why." not in other[1] and "Icons" not in other[1]                                                      # nothing else of it
    assert task_brief.reading(page(), "tech")["own"][0] == "Tech"


def test_a_page_of_before_or_a_section_the_page_lacks_is_read_as_it_was():
    old = idea_page.parse("---\ntrack: web\n---\n# Old\n\n## Gist\nA goal\n\n## Why\nBecause\n\n## Done when\n- It works\n")
    assert task_brief.reading(old, "Web") is None and task_brief.note(old, "Web") == ""
    assert task_brief.reading(page(), "Nobody") is None and task_brief.reading(page(), "") is None and task_brief.note(page(), "Nobody") == ""


def test_the_contract_is_done_when_and_will_be_as_the_leader_wrote_them_and_nothing_when_it_wrote_neither():
    assert task_brief.contract("### Why\nx\n\n### Done when\n- a\n\n### Out\n- b") == "### Done when\n- a"
    assert task_brief.contract("### Why\nx") == "" and task_brief.contract("") == ""


def test_the_note_names_what_a_task_reads_and_a_lone_section_has_no_contract_to_keep():
    note = task_brief.note(page(), "Design")
    assert note == ("read the common part (`## Asked`, `## Gist`, `## Route`), your party's section `## Design` whole, and of the other sections (`## Tech`) only their "
                    "`### Done when` and `### Will be`: they are the contract your work must not break. Read nothing else of it: the other parties' sections are theirs.")
    lone = idea_page.parse(PAGE.split("## Tech")[0])
    assert "of the other sections" not in task_brief.note(lone, "Design") and "your party's section `## Design` whole" in task_brief.note(lone, "Design")


def test_a_page_is_found_in_the_boards_worktree_first_then_the_repository(tmp_path):
    repo, state = tmp_path / "repo", tmp_path / "state"
    for base, title in ((repo, "Repository"), (state / "board", "Board")):
        (base / "pages" / "ideas").mkdir(parents=True)
        (base / "pages" / "ideas" / "x.md").write_text(f"# {title}\n\n## Design\n### Why\nw\n")
    assert task_brief.page_of(repo, state, "pages/ideas/x.md").title == "Board"
    (state / "board" / "pages" / "ideas" / "x.md").unlink()
    assert task_brief.page_of(repo, state, "pages/ideas/x.md").title == "Repository"
    assert task_brief.page_of(repo, state, "pages/ideas/none.md") is None
    assert spec_sections.sections_of(task_brief.page_of(repo, state, "pages/ideas/x.md"))
