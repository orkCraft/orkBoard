"""`orkboard check` (realm/board_check.py; spec 151 E.2, E.3, decisions §255.9): a clean Board says nothing, and each fault is found in words with its path and line; the CI step's file; the Board's folder
found from the checkout. Fixture repositories in `tmp_path`, no app, no model."""
from __future__ import annotations

from pathlib import Path

import pytest

from orkboard.gui import board_cli
from orkboard.realm import agent_rules, agent_rules_text as T, board_branch, board_check, ideas
from tests.test_board_branch import make_clone, make_origin

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
    assert f == {"path": ".claude/skills/orkboard/SKILL.md", "line": 0, "what": f"Orkboard's file is missing: run {T.RUN} init"}
    agent_rules.write(repo, WIKI)
    agents = repo / "AGENTS.md"
    agents.write_text(agents.read_text(encoding="utf-8").replace(f"schema={T.SCHEMA} ", "schema=0 "), encoding="utf-8")
    f = only(repo, "v0")
    assert f["path"] == "AGENTS.md" and f["what"] == f"The Board's rules are v0, this Orkboard writes v{T.SCHEMA}: run {T.RUN} init"


def test_check_prints_each_fault_and_exits_1(repo, capsys):
    goal(repo, phase="launched")
    assert board_cli.run(["check"]) == 1
    err = capsys.readouterr().err
    assert f"{WIKI}/pages/ideas/a-goal.md:" in err and "'launched'" in err and "1 fault in the Board" in err


def test_a_goal_laid_from_the_history_is_asked_neither_a_gate_record_nor_a_done_when(tmp_path):
    """Spec 151 H.1: a spec written before the Board's format, laid by `import --goals`, has no *Done when* and its `done` no gate record."""
    import subprocess
    from orkboard.realm import agent_rules
    repo = tmp_path / "p"
    (repo / "docs" / "specs").mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    (repo / "docs" / "specs" / "33-old.md").write_text("# Spec 33 — Old\n\nNo Done when here.\n")
    page = repo / "llm-wiki/general/pages/ideas/33-old.md"
    page.parent.mkdir(parents=True)
    head = "---\nowner: board\nkind: idea\ntrack: tech\nphase: done\nspec: docs/specs/33-old.md\nby: person\n{laid}schema: {schema}\n---\n# Old\n\n## Gist\nOld\n\n## Stages\n- [x] Old\n"
    agent_rules.write(repo, "llm-wiki/general")
    from orkboard.realm import goal_phase
    page.write_text(head.format(laid="laid: history\n", schema=goal_phase.SCHEMA))
    assert [f for f in board_check.run(repo) if f["path"].endswith("33-old.md")] == []
    page.write_text(head.format(laid="", schema=goal_phase.SCHEMA))
    assert {f["what"].split(" (")[0] for f in board_check.run(repo) if f["path"].endswith("33-old.md")} == {
        "the phase is done but the page has no green gate record", "the phase is done but the page has no *Done when*"}


TECH = "### Why\nBecause.\n\n### Done when\n- the board shows the best three players\n- [test] a tie is ordered by the earlier score\n- the board loads in under a second\n"


def with_section(repo: Path, extra: str, slug: str = "a-goal") -> Path:
    path = goal(repo, slug)
    path.write_text(path.read_text(encoding="utf-8").rstrip("\n") + "\n\n## Tech\n" + TECH + extra, encoding="utf-8")
    return path


def test_a_talk_it_cannot_read_a_verdict_it_does_not_know_and_a_free_line_are_found_with_their_line(repo):
    path = with_section(repo, "\n### Talk\n- verdict: maybe — unsure\n- stance: ok\nI think it is fine\n- assumes: it is quick\n")
    text = path.read_text(encoding="utf-8").split("\n")
    n = next(i for i, ln in enumerate(text, 1) if ln.startswith("- verdict: maybe"))
    got = {f["line"]: f["what"] for f in board_check.run(repo)}
    assert "verdict 'maybe' is not one Orkboard knows (go, doubt, no)" in got[n]
    assert "'I think it is fine'" in got[n + 2] and "none Orkboard can read" in got[n + 2]
    assert "no `— shown by: <signal>`" in got[n + 3] and len(got) == 3


def test_an_answer_decided_by_a_reference_the_project_does_not_hold_is_found(tmp_path):
    """Decisions §259: `(decided by §N, day)` must name a decision of the log or a spec; one that does not exist is a finding, one that does is none."""
    from orkboard.realm import agent_rules, goal_phase
    repo = tmp_path / "p"
    (repo / "docs" / "specs").mkdir(parents=True)
    (repo / "docs" / "decisions.md").write_text("# Decisions\n\n## 3. Three (1 November 2026, the owner)\n")
    (repo / "docs" / "specs" / "5-five.md").write_text("# 5. Five\n")
    agent_rules.write(repo, "llm-wiki/general")
    pg = repo / "llm-wiki/general/pages/ideas/g.md"
    pg.parent.mkdir(parents=True, exist_ok=True)
    body = ("---\nowner: board\nkind: idea\ntrack: tech\nphase: new\nby: person\nschema: {s}\n---\n# G\n\n## Gist\nG\n\n## Open questions\n"
            "- A?\n  - Answered: x (decided by §3, 2026-11-06)\n- B?\n  - Answered: y (decided by spec 5 A.1, 2026-11-06)\n"
            "- C?\n  - Answered: z (the person, 2026-11-06)\n{bad}")
    pg.write_text(body.format(s=goal_phase.SCHEMA, bad=""))
    assert [f for f in board_check.run(repo) if f["path"].endswith("/g.md")] == []
    pg.write_text(body.format(s=goal_phase.SCHEMA, bad="- D?\n  - Answered: w (decided by §40, 2026-11-06)\n"))
    assert [f["what"] for f in board_check.run(repo) if f["path"].endswith("/g.md")] == [
        "the answer is decided by §40, which this project's decisions and specs do not hold"]
    assert board_check.reference_exists(repo, "§3.2") and board_check.reference_exists(repo, "spec 5") and not board_check.reference_exists(repo, "spec 6")

