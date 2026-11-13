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


def test_start_at_says_the_files_a_plan_named_and_nothing_with_none_spec_153_b2():
    assert task_brief.start_at({"files": ["a.py", "b/c.py"]}) == "Start at: `a.py`, `b/c.py` (its planner read them; read more as you need)"
    assert task_brief.start_at({"files": ["a.py"]}) == "Start at: `a.py` (its planner read it; read more as you need)"
    assert task_brief.start_at({}) == "" and task_brief.start_at({"files": []}) == "" and task_brief.start_at({"files": [3, ""]}) == ""
