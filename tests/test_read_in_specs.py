"""A folder of numbered specs laid as goals (realm/read_in_specs.py; `orkboard import --goals`; spec 151 H.1, H.2, H.4): a fixture repository in `tmp_path` with its commits, no app and no model."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from orkboard.gui import board_cli
from orkboard.realm import board_check, goal_phase, ideas, read_in_specs as specs

WIKI = "llm-wiki/general"
TABLE = "| Part | What |\n|---|---|\n| **A. The first** | one |\n| **B. The second** | two |\n| **E1. The host** | three |\n"


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


def spec(root: Path, name: str, body: str) -> None:
    (root / "docs" / "specs").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "specs" / name).write_text(body, encoding="utf-8")


@pytest.fixture
def repo(tmp_path: Path, monkeypatch) -> Path:
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "config", "user.email", "t@x")
    git(tmp_path, "config", "user.name", "T")
    spec(tmp_path, "7-the-seven.md", f"# 7. The seven: what it builds\n\nDecisions §254. **Builds:** it.\n\n{TABLE}\n## Done when\n\nIt works.\n")
    spec(tmp_path, "8-no-parts.md", "# 8. No parts here\n\nDecisions §12 and §13.\n\nJust text.\n\n## Done when\n\nIt works.\n")
    spec(tmp_path, "29a-the-letter.md", "# 29a. The letter spec\n\n## Done when\n\nIt works.\n")
    spec(tmp_path, "30-not-numbered-heading.md", "The spec that starts with words\n\n## Done when\n\nIt works.\n")
    spec(tmp_path, "AGENTS.md", "# not a spec\n")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-qm", "start")
    git(tmp_path, "commit", "-q", "--allow-empty", "-m", "Spec 7 A: the first part")
    git(tmp_path, "commit", "-q", "--allow-empty", "-m", "Spec 7 E1: the host")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def planned(repo: Path, **kw) -> dict[str, dict]:
    return {p["slug"]: p for p in specs.goals_from_specs(repo, "docs/specs", WIKI, **kw)}


def ob(*argv: str) -> int:
    return board_cli.run(["import", *argv])


def test_each_numbered_spec_is_one_goal_with_its_title_spec_decisions_and_stages(repo: Path) -> None:
    got = planned(repo)
    assert list(got) == ["7-the-seven", "8-no-parts", "29a-the-letter", "30-not-numbered-heading"]      # AGENTS.md is no spec; numbers sort as numbers
    seven = got["7-the-seven"]
    assert (seven["title"], seven["spec"], seven["decisions"], seven["party"], seven["exists"]) == ("The seven", "docs/specs/7-the-seven.md", [254], "tech", False)
    assert seven["stages"] == [("A", "The first", True), ("B", "The second", False), ("E1", "The host", True)]
    assert got["8-no-parts"]["decisions"] == [12, 13]
    assert got["29a-the-letter"]["title"] == "The letter spec"
    assert got["30-not-numbered-heading"]["title"] == "Not numbered heading"             # no heading: the file name says it


def test_a_spec_with_no_table_is_one_stage_built_by_a_commit_of_its_number(repo: Path) -> None:
    assert planned(repo)["8-no-parts"]["stages"] == [("", "No parts here", False)]
    for subject in ("Spec 8: it", "Spec 8 anything at all"):
        got = specs.goals_from_specs(repo, "docs/specs", WIKI, log=[subject])
        assert got[1]["stages"][0][2] and got[1]["phase"] == "done"
    assert not specs.goals_from_specs(repo, "docs/specs", WIKI, log=["Spec 80: other"])[1]["stages"][0][2]
    assert not specs.goals_from_specs(repo, "docs/specs", WIKI, log=["Spec 7 A: of another"])[1]["stages"][0][2]


def test_the_phase_is_done_through_then_all_built_some_or_none(repo: Path) -> None:
    got = planned(repo)
    assert got["7-the-seven"]["phase"] == "work"                       # two of three
    assert got["8-no-parts"]["phase"] == "spec"                        # none
    git(repo, "commit", "-q", "--allow-empty", "-m", "Spec 7 B: the second part")
    assert planned(repo)["7-the-seven"]["phase"] == "done"             # all
    through = planned(repo, done_through=8)
    assert [p["phase"] for p in through.values()] == ["done", "done", "spec", "spec"]
    assert all(s[2] for s in through["8-no-parts"]["stages"])
    assert planned(repo, done_through=28)["29a-the-letter"]["phase"] == "spec"
    assert planned(repo, done_through=29)["29a-the-letter"]["phase"] == "done"        # 29a is spec 29's
    assert specs.goals_from_specs(repo, "docs/specs", WIKI, parts=None)[0]["phase"] == "spec"   # a project whose commits say nothing


def test_the_commits_are_read_once(repo: Path, monkeypatch) -> None:
    calls = []
    real = specs.commits
    monkeypatch.setattr(specs, "commits", lambda root: calls.append(root) or real(root))
    specs.goals_from_specs(repo, "docs/specs", WIKI)
    assert len(calls) == 1


def test_lay_writes_the_page_as_the_board_writes_one_and_never_over_one(repo: Path) -> None:
    plan = specs.goals_from_specs(repo, "docs/specs", WIKI)
    assert specs.lay(repo, WIKI, plan) == ["7-the-seven", "8-no-parts", "29a-the-letter", "30-not-numbered-heading"]
    path = repo / WIKI / "pages" / "ideas" / "7-the-seven.md"
    page = ideas.idea_page(repo / WIKI, "7-the-seven")
    assert (page.get("owner"), page.get("kind"), page.get("track"), page.get("phase"), page.get("spec"), page.get("decisions"), page.get("by"), page.get("schema")) == (
        "board", "idea", "tech", "work", "docs/specs/7-the-seven.md", "254", "person", goal_phase.SCHEMA)
    assert page.title == "The seven"
    assert [n for n, _t in page.sections] == ["Gist", "Stages"]
    assert page.section("Gist") == "The seven"
    assert page.section("Stages") == "- [x] A. The first\n- [ ] B. The second\n- [x] E1. The host"
    path.write_text(path.read_text(encoding="utf-8") + "\nmine\n", encoding="utf-8")
    again = specs.goals_from_specs(repo, "docs/specs", WIKI)
    assert all(p["exists"] for p in again)
    assert specs.lay(repo, WIKI, again) == []                                   # laid twice, written once
    assert path.read_text(encoding="utf-8").endswith("mine\n")


def test_the_pages_are_read_by_the_board_in_their_phase_and_pass_the_check(repo: Path) -> None:
    git(repo, "commit", "-q", "--allow-empty", "-m", "Spec 7 B: the second part")
    specs.lay(repo, WIKI, specs.goals_from_specs(repo, "docs/specs", WIKI, done_through=8))
    by_slug = {i["slug"]: i for i in ideas.ideas(repo / WIKI)}
    assert set(by_slug) == {"7-the-seven", "8-no-parts", "29a-the-letter", "30-not-numbered-heading"}
    assert {s: goal_phase.phase_of_page(ideas.idea_page(repo / WIKI, s)) for s in by_slug} == {
        "7-the-seven": "done", "8-no-parts": "done", "29a-the-letter": "spec", "30-not-numbered-heading": "spec"}
    assert {t["slug"] for t in ideas.tracks(repo / WIKI, make=False)} >= {"tech"}
    ours = [f for f in board_check.run(repo) if f["path"].startswith(f"{WIKI}/pages/ideas/") and not f["path"].endswith("index.md")]
    assert ours == []                                                                           # a goal laid as done from the history carries `laid: history`: no gate record is asked of it


def test_the_pages_that_are_not_done_pass_the_check_whole(repo: Path) -> None:
    specs.lay(repo, WIKI, specs.goals_from_specs(repo, "docs/specs", WIKI))
    assert [f for f in board_check.run(repo) if f["path"].startswith(f"{WIKI}/pages/")] == []


def test_dry_run_says_a_line_a_spec_and_the_counts_and_writes_nothing(repo: Path, capsys) -> None:
    assert ob(".", "--goals", "docs/specs", "--done-through", "8", "--dry-run") == 0
    out = capsys.readouterr().out.splitlines()
    assert out[0] == "7 · The seven · done · 3/3 parts · tech"
    assert out[2] == "29a · The letter spec · spec · 0/1 parts · tech"
    assert out[-1] == "4 goals: 2 done, 0 work, 2 spec; 0 already laid"
    assert not (repo / "llm-wiki").exists()
    assert git(repo, "status", "--porcelain").strip() == ""


def test_import_goals_writes_the_working_tree_and_commits_nothing(repo: Path, capsys) -> None:
    before = git(repo, "rev-parse", "HEAD")
    assert ob("--goals", "docs/specs", "--party", "design") == 0
    assert "4 goal pages written" in capsys.readouterr().out
    assert git(repo, "rev-parse", "HEAD") == before
    assert git(repo, "log", "--format=%s").count("\n") == 3
    assert (repo / WIKI / "pages" / "ideas" / "29a-the-letter.md").is_file()
    assert ideas.idea_page(repo / WIKI, "7-the-seven").get("track") == "design"
    assert git(repo, "status", "--porcelain").strip().startswith("??")
    assert ob("--goals", "docs/specs", "--dry-run") == 0
    assert capsys.readouterr().out.splitlines()[-1] == "4 goals: 0 done, 1 work, 3 spec; 4 already laid"


def test_exit_codes(repo: Path, capsys, tmp_path_factory) -> None:
    assert ob("--goals", "docs/nothing") == 2                                    # a folder that is not there
    assert ob("--goals", "docs/specs", "--party", "Not A Slug") == 2
    assert ob("--done-through", "3") == 2                                        # without --goals
    (repo / "docs" / "empty").mkdir()
    assert ob("--goals", "docs/empty") == 1                                      # refused in words
    assert "no numbered spec" in capsys.readouterr().err
    assert ob("--goals", str(tmp_path_factory.mktemp("elsewhere"))) == 1         # not inside the project


def test_a_part_built_in_pieces_counts_as_built_unless_the_table_has_its_pieces(tmp_path):
    folder = tmp_path / "docs" / "specs"
    folder.mkdir(parents=True)
    (folder / "151-pieces.md").write_text("# 151. Pieces\n\n| Part | What |\n|---|---|\n| **E. One** | e |\n| **F. Two** | f |\n")
    (folder / "150-own.md").write_text("# 150. Own\n\n| Part | What |\n|---|---|\n| **E. Zero** | e |\n| **E1. One** | e1 |\n| **E2. Two** | e2 |\n")
    log = ["Spec 151 E: e", "Spec 151 F1: f one", "Spec 151 F2: f two", "Spec 150 E1: one", "Spec 150 E2: two"]
    got = {p["slug"]: p for p in specs.goals_from_specs(tmp_path, "docs/specs", "llm-wiki/general", log=log)}
    assert [b for _i, _n, b in got["151-pieces"]["stages"]] == [True, True] and got["151-pieces"]["phase"] == "done"
    assert [(i, b) for i, _n, b in got["150-own"]["stages"]] == [("E", False), ("E1", True), ("E2", True)]      # E has pieces of its own in the table: its own commit is needed


def test_an_older_heading_spec_nn_dash_loses_its_number(tmp_path):
    folder = tmp_path / "docs" / "specs"
    folder.mkdir(parents=True)
    (folder / "40-design.md").write_text("# Spec 40 — Orkboard in orkUI: the office look\n")
    (folder / "33-v1.md").write_text("# Spec 33 — v1: three windows, Board · Agents · Review\n")
    got = {p["slug"]: p["title"] for p in specs.goals_from_specs(tmp_path, "docs/specs", "llm-wiki/general", log=[])}
    assert got == {"33-v1": "v1: three windows, Board · Agents · Review", "40-design": "Orkboard in orkUI"}


def test_only_a_goal_laid_done_says_it_was_laid_from_the_history(tmp_path):
    """A spec still to build is checked as any goal is: its `done` will need a gate record."""
    folder = tmp_path / "docs" / "specs"
    folder.mkdir(parents=True)
    (folder / "1-old.md").write_text("# 1. Old\n")
    (folder / "2-new.md").write_text("# 2. New\n\n| Part | What |\n|---|---|\n| **A. One** | a |\n")
    specs.lay(tmp_path, "llm-wiki/general", specs.goals_from_specs(tmp_path, "docs/specs", "llm-wiki/general", done_through=1, log=[]))
    pages = tmp_path / "llm-wiki/general/pages/ideas"
    assert "laid: history" in (pages / "1-old.md").read_text() and "laid:" not in (pages / "2-new.md").read_text()


def test_a_spec_named_with_dots_is_a_goal_of_a_slug_laid_once(repo: Path) -> None:
    spec(repo, "96-orkui-0.15.0-copied.md", "# 96. OrkUI copied\n\n## Done when\n\nIt works.\n")
    got = planned(repo)
    assert "96-orkui-0-15-0-copied" in got and "96-orkui-0.15.0-copied" not in got
    p = got["96-orkui-0-15-0-copied"]
    assert p["spec"] == "docs/specs/96-orkui-0.15.0-copied.md" and not p["exists"]
    assert specs.line(p).startswith("96 · OrkUI copied")
    assert "96-orkui-0-15-0-copied" in specs.lay(repo, WIKI, [p])
    assert (repo / WIKI / "pages/ideas/96-orkui-0-15-0-copied.md").exists()
    assert planned(repo)["96-orkui-0-15-0-copied"]["exists"]
    assert specs.lay(repo, WIKI, [planned(repo)["96-orkui-0-15-0-copied"]]) == []
