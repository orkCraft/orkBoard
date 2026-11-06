"""`orkboard check` (realm/board_check.py; spec 151 E.2, E.3, decisions §255.9): a clean Board says nothing, and each fault is found in words with its path and line; the CI step's file; the Board's folder
found from the checkout. Fixture repositories in `tmp_path`, no app, no model."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from orkboard.gui import board_cli
from orkboard.realm import agent_rules, agent_rules_text as T, board_branch, board_check, goal_phase, ideas
from tests.test_board_branch import git, make_clone, make_origin

WIKI = "llm-wiki/general"
GREEN = "abc1234 · 2 files · green"


@pytest.fixture
def repo(tmp_path: Path, monkeypatch) -> Path:
    """A clone with the Board's rules written (`orkboard init`), as a pull request's checkout has them; no `.orkcraft/` in it."""
    clone = make_clone(make_origin(tmp_path), tmp_path / "work")
    monkeypatch.chdir(clone)
    monkeypatch.setattr(board_branch, "private_check", lambda *a, **k: (True, ""))
    assert board_cli.run(["init"]) == 0
    return clone


def goal(repo: Path, slug: str = "a-goal", **meta: str) -> Path:
    """A goal's page written by hand, as a tool would (the Board's folder made by the first `goal add`)."""
    assert board_cli.run(["goal", "add", "A goal", "--by", "codex"]) == 0 if slug == "a-goal" and not (repo / WIKI / "pages/ideas/a-goal.md").exists() else True
    path = repo / WIKI / "pages" / "ideas" / f"{slug}.md"
    page = ideas.idea_page(repo / WIKI, slug)
    for k, v in meta.items():
        page.set(k, v)
    path.write_text(page.text(), encoding="utf-8")
    return path


def found(repo: Path) -> list[str]:
    return [board_check.say(f) for f in board_check.run(repo)]


def only(repo: Path, needle: str) -> dict:
    got = [f for f in board_check.run(repo) if needle in f["what"]]
    assert len(got) == 1, board_check.run(repo)
    return got[0]


def test_a_clean_board_says_nothing_and_a_clone_without_orkcraft_is_read_as_well(repo, capsys):
    goal(repo)
    assert not (repo / ".orkcraft").exists()
    assert board_check.run(repo) == []
    assert board_cli.run(["check"]) == 0 and "clean" in capsys.readouterr().out


def test_a_board_that_went_all_the_way_is_clean(repo, capsys):
    path = goal(repo, phase="done", gate=GREEN)
    page = ideas.idea_page(repo / WIKI, "a-goal")
    page.set_section("Done when", "- it scores")
    page.set_section("Stages", "- [x] the code")
    path.write_text(page.text(), encoding="utf-8")
    assert found(repo) == []


def test_a_page_that_cannot_be_read_or_whose_front_matter_is_open(repo):
    goal(repo)
    folder = repo / WIKI / "pages" / "ideas"
    (folder / "broken.md").write_bytes(b"\xff\xfe not text")
    (folder / "open.md").write_text("---\nowner: board\n# Open\n\n## Gist\nno second fence\n", encoding="utf-8")
    assert only(repo, "cannot be read")["path"] == f"{WIKI}/pages/ideas/broken.md"
    assert only(repo, "not closed") == {"path": f"{WIKI}/pages/ideas/open.md", "line": 1, "what": "its front matter is not closed with a second ---"}


def test_a_phase_orkboard_does_not_know_is_found_at_its_line(repo):
    path = goal(repo, phase="launched")
    f = only(repo, "'launched'")
    assert f["path"] == f"{WIKI}/pages/ideas/a-goal.md"
    assert path.read_text(encoding="utf-8").splitlines()[f["line"] - 1] == "phase: launched"
    assert "talk, spec" in f["what"] and "new, talk" in f["what"]


def test_a_done_with_no_green_gate_record_is_found(repo):
    goal(repo, phase="done")
    assert only(repo, "no green gate record")
    goal(repo, phase="done", gate="abc1234 · 2 files · red")
    assert only(repo, "no green gate record")["line"] > 1
    goal(repo, phase="done", gate="abc1234 · 1 file · green")
    assert not [f for f in board_check.run(repo) if "gate record" in f["what"]]


def test_a_phase_that_skips_one_without_its_sections_is_found(repo):
    goal(repo, phase="spec")
    assert only(repo, "no *Done when*")["what"] == "the phase is spec but the page has no *Done when*"
    path = goal(repo, phase="work")
    assert [f["what"] for f in board_check.run(repo)] == ["the phase is work but the page has no *Done when*",
                                                         "the phase is work but the page has no stages (*Stages*, or *Plan* in a party's section)"]
    page = ideas.idea_page(repo / WIKI, "a-goal")
    page.set_section("Done when", "- it scores")
    page.set_section("Tech", "### Plan\n- the code")                              # the new format: a party's section
    path.write_text(page.text(), encoding="utf-8")
    assert found(repo) == []


def test_a_goal_whose_spec_is_a_file_of_its_own_has_its_sections_there(repo):
    (repo / "docs").mkdir()
    (repo / "docs" / "spec.md").write_text("# Spec\n\n## Done when\n- it scores\n", encoding="utf-8")
    goal(repo, phase="work", spec="docs/spec.md")
    assert found(repo) == []
    goal(repo, phase="work", spec="../outside.md")
    assert len(board_check.run(repo)) == 2


def test_a_secrets_shape_is_found_in_the_boards_files_only_and_never_echoed(repo):
    path = goal(repo)
    page = ideas.idea_page(repo / WIKI, "a-goal")
    page.set_section("Decisions", "use this: token = abcdefghijklmnopqrstuvwxyz0123456789")
    path.write_text(page.text(), encoding="utf-8")
    (repo / "notes.md").write_text("api_key = abcdefghijklmnopqrstuvwxyz0123456789\n", encoding="utf-8")        # the project's own file: not the Board's
    f = only(repo, "secret")
    assert f["path"] == f"{WIKI}/pages/ideas/a-goal.md" and "abcdefghij" not in f["what"]
    assert path.read_text(encoding="utf-8").splitlines()[f["line"] - 1].startswith("use this")
    (repo / WIKI / "journals").mkdir()
    (repo / WIKI / "journals" / "project.md").write_text("---\norkboard-journal: _project\n---\n- 2026-11-01 · decision · key sk-abcdefghijklmnopqrstuvwxyz\n", encoding="utf-8")
    assert [f["path"] for f in board_check.run(repo) if "secret" in f["what"]] == [f"{WIKI}/journals/project.md", f"{WIKI}/pages/ideas/a-goal.md"]


def test_rules_that_are_missing_changed_by_hand_or_of_an_older_schema_are_found(repo):
    assert board_check.run(repo) == []
    (repo / WIKI / "BOARD.md").write_text((repo / WIKI / "BOARD.md").read_text(encoding="utf-8") + "\nmy own line\n", encoding="utf-8")
    assert "changed by hand" in only(repo, "changed by hand")["what"]
    agent_rules.write(repo, WIKI)
    (repo / ".claude" / "skills" / "orkboard" / "SKILL.md").unlink()
    f = only(repo, "is missing")
    assert f == {"path": ".claude/skills/orkboard/SKILL.md", "line": 0, "what": "Orkboard's file is missing: run uvx orkboard init"}
    agent_rules.write(repo, WIKI)
    agents = repo / "AGENTS.md"
    agents.write_text(agents.read_text(encoding="utf-8").replace(f"schema={T.SCHEMA} ", "schema=0 "), encoding="utf-8")
    f = only(repo, "v0")
    assert f["path"] == "AGENTS.md" and f["what"] == f"The Board's rules are v0, this Orkboard writes v{T.SCHEMA}: run uvx orkboard init"


def test_a_project_with_no_rules_at_all_is_told_once(repo):
    for rel in ("AGENTS.md", "CLAUDE.md", ".claude", WIKI):
        p = repo / rel
        shutil.rmtree(p) if p.is_dir() else p.unlink()
    assert board_check.run(repo) == [{"path": "AGENTS.md", "line": 0, "what": "The Board's rules are not written in this project: run uvx orkboard init"}]


def test_a_journal_line_of_an_unknown_kind_is_found_at_its_line(repo):
    folder = repo / WIKI / "journals"
    folder.mkdir()
    text = "---\norkboard-journal: _project\n---\n\n# Project's journal\n\n- 2026-11-01 · decision · fine <!-- id=aaaaaaaaaaaa -->\n- 2026-11-02 · whim · not a kind <!-- id=bbbbbbbbbbbb -->\n"
    (folder / "project.md").write_text(text, encoding="utf-8")
    f = only(repo, "'whim'")
    assert (f["path"], f["line"]) == (f"{WIKI}/journals/project.md", 8)
    assert not (repo / ".orkcraft").exists()                                      # reading it wrote nothing


def test_an_older_page_schema_is_found_and_a_page_of_before_is_not(repo):
    goal(repo, schema="0")
    assert only(repo, "schema 0")["line"] > 1
    path = goal(repo, schema=goal_phase.SCHEMA)
    page = ideas.idea_page(repo / WIKI, "a-goal")
    page.meta = [(k, v) for k, v in page.meta if k not in ("phase", "schema", "by")]
    path.write_text(page.text(), encoding="utf-8")
    assert found(repo) == []


def test_check_prints_each_fault_and_exits_1(repo, capsys):
    goal(repo, phase="launched")
    assert board_cli.run(["check"]) == 1
    err = capsys.readouterr().err
    assert f"{WIKI}/pages/ideas/a-goal.md:" in err and "'launched'" in err and "1 fault in the Board" in err


def test_the_boards_folder_is_the_one_the_block_names_when_two_hold_pages(repo):
    (repo / "elsewhere" / "pages" / "ideas").mkdir(parents=True)
    (repo / WIKI / "pages" / "ideas").mkdir(parents=True)
    assert board_check.wiki_of(repo) == WIKI                                      # the root AGENTS.md block names it
    agent_rules.write(repo, "elsewhere")
    assert board_check.wiki_of(repo) == "elsewhere"
    (repo / "AGENTS.md").unlink()
    with pytest.raises(ValueError, match="More than one folder"):
        board_check.wiki_of(repo)
    assert board_cli.run(["check"]) == 1


def test_the_ci_steps_file_runs_on_pull_requests_for_the_boards_files_only():
    text = board_check.workflow(WIKI)
    assert "on:\n  pull_request:\n    paths:\n" in text and f'      - "{WIKI}/**"\n      - "AGENTS.md"\n      - "CLAUDE.md"\n' in text
    assert "push" not in text and "uvx orkboard check" in text and "astral-sh/setup-uv" in text
    assert "Checks the Board on each pull request; your tests stay your CI's." in text
