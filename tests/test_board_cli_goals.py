"""`orkboard init | goal … | gate | check` (gui/board_cli_goals.py; spec 151 E, decisions §255.9): each word on a fixture repository in `tmp_path`, with no app, no model and no AI tool.
`goal add` then `list`; `take` against a bare remote; `phase` refusing an unknown phase, a skipped one and a `done` with no gate; `ask` and `answer` read back by A; `gate --record`;
`init` writing the rules and refusing a public repository; and no word makes a commit."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest

from orkboard.gui import board_cli, board_cli_goals as goals
from orkboard.realm import agent_rules, board_branch, goal_phase, goal_take, idea_questions, ideas
from orkboard.realm.idea_git import GateRun, IdeaGit
from tests.test_board_branch import git, make_clone, make_origin

WIKI = "llm-wiki/general"
STAGES = "- [ ] the code\n- [ ] its tests"


@pytest.fixture
def repo(tmp_path: Path, monkeypatch) -> Path:
    """A clone of a bare origin, the working folder; the repository is private (the HTTP check is faked)."""
    clone = make_clone(make_origin(tmp_path), tmp_path / "work")
    monkeypatch.chdir(clone)
    monkeypatch.setattr(board_branch, "private_check", lambda *a, **k: (True, ""))
    return clone


def head(repo: Path) -> str:
    return git(repo, "rev-parse", "HEAD").strip()


def ob(*argv: str) -> int:
    return board_cli.run(list(argv))


def page(repo: Path, slug: str):
    return ideas.idea_page(repo / WIKI, slug)


def fill(repo: Path, slug: str, **sections: str) -> None:
    for name, text in sections.items():
        name = name.replace("_", " ")
        if name in ideas.SECTIONS:
            ideas.set_section(repo / WIKI, slug, name, text)
        else:                                                                   # a party's section (the new format): the page is written whole
            pg = page(repo, slug)
            pg.set_section(name, text)
            ideas._write(repo / WIKI / "pages" / "ideas" / f"{slug}.md", pg.text())


def a_goal(repo: Path, capsys, words: str = "Add a score board", by: str = "codex") -> str:
    assert ob("goal", "add", words, "--by", by) == 0
    return capsys.readouterr().out.split()[0]


def fake_gate(monkeypatch, ok: bool = True, ran: bool = True, env: str = "") -> None:
    monkeypatch.setattr(IdeaGit, "gate_run", lambda self, path, base, cancel, *a, **k: GateRun(ok, "$ pytest\n3 passed", ran, "pytest", 0 if ok else 1, 0.1, env))


# -- goal add, list ------------------------------------------------------------------------------------------------------------------

def test_a_goal_added_by_a_tool_is_a_page_in_new_and_listed(repo, capsys):
    slug = a_goal(repo, capsys)
    assert slug == "add-a-score-board"
    p = page(repo, slug)
    assert (p.get("phase"), p.get("by"), p.get("schema"), p.title) == ("new", "codex", goal_phase.SCHEMA, "Add a score board")
    assert p.section("Gist") == "Add a score board"
    assert ob("goal", "list") == 0
    out = capsys.readouterr().out
    assert slug in out and "new" in out and "Add a score board" in out
    assert ob("goal", "list", "--phase", "work") == 0 and "No goals in work" in capsys.readouterr().out


def test_a_goal_needs_its_tool_a_known_party_and_a_phase_that_exists(repo, capsys):
    with pytest.raises(SystemExit) as e:
        ob("goal", "add", "Without a tool")
    assert e.value.code == 2
    capsys.readouterr()
    assert ob("goal", "add", "Lost", "--by", "codex", "--party", "nowhere") == 1 and "No party 'nowhere'" in capsys.readouterr().err
    assert ob("goal", "add", "Odd", "--by", "co\ndex") == 2
    capsys.readouterr()
    assert ob("goal", "add", "   ", "--by", "codex") == 2
    assert ob("goal", "add", "A party's goal", "--by", "codex", "--party", ideas.GENERAL) == 0
    assert ob("goal", "list", "--phase", "work") == 0


def test_the_boards_folder_is_found_from_the_checkout_as_the_app_does(repo, capsys):
    (repo / "board" / "pages" / "ideas").mkdir(parents=True)
    ideas.add_track(repo / "board", "General")
    slug = a_goal(repo, capsys, "In another folder")
    assert (repo / "board/pages/ideas" / f"{slug}.md").is_file() and not (repo / WIKI).exists()
    (repo / "elsewhere" / "pages" / "ideas").mkdir(parents=True)
    assert ob("goal", "list") == 1 and "More than one folder" in capsys.readouterr().err
    agent_rules.write(repo, "board")
    assert ob("goal", "list") == 0 and slug in capsys.readouterr().out


# -- take ----------------------------------------------------------------------------------------------------------------------------

def test_taking_a_goal_against_a_bare_remote_is_refused_while_another_holds_it(repo, tmp_path, capsys, monkeypatch):
    slug = a_goal(repo, capsys)
    assert ob("goal", "take", slug, "--by", "codex") == 0
    assert "taken by codex" in capsys.readouterr().out
    origin = tmp_path / "origin.git"
    held = json.loads(git(origin, "show", f"refs/heads/{goal_take.BRANCH}:{slug}.json"))
    assert (held["by"], held["kind"]) == ("codex", "tool")
    other = make_clone(origin, tmp_path / "other")
    (other / WIKI / "pages" / "ideas").mkdir(parents=True)
    (other / WIKI / "pages" / "ideas" / f"{slug}.md").write_text(page(repo, slug).text(), encoding="utf-8")
    monkeypatch.chdir(other)
    assert ob("goal", "take", slug, "--by", "cursor") == 1
    assert "Taken by codex" in capsys.readouterr().err
    assert ob("goal", "list") == 0 and "codex" in capsys.readouterr().out
    monkeypatch.chdir(repo)
    assert ob("goal", "take", slug, "--by", "codex") == 0                      # the same taker renews
    assert ob("goal", "take", "no-such-goal", "--by", "codex") == 1


def test_taking_with_no_remote_is_always_taken(tmp_path, monkeypatch, capsys):
    solo = tmp_path / "solo"
    solo.mkdir()
    git(solo, "init", "-q", "-b", "main")
    git(solo, "config", "user.email", "t@x")
    git(solo, "config", "user.name", "T")
    (solo / "a.txt").write_text("x")
    git(solo, "add", "-A")
    git(solo, "commit", "-qm", "start")
    monkeypatch.chdir(solo)
    slug = a_goal(solo, capsys)
    assert ob("goal", "take", slug) == 0 and "no remote" in capsys.readouterr().out


# -- phase ---------------------------------------------------------------------------------------------------------------------------

def test_a_phase_that_is_unknown_skipped_or_without_its_sections_is_refused(repo, capsys):
    slug = a_goal(repo, capsys)
    assert ob("goal", "phase", slug, "launched") == 2 and "No phase 'launched'" in capsys.readouterr().err
    assert ob("goal", "phase", slug, "spec") == 1 and "one phase on (talk)" in capsys.readouterr().err
    assert ob("goal", "phase", slug, "talk") == 0 and page(repo, slug).get("phase") == "talk"
    capsys.readouterr()
    assert ob("goal", "phase", slug, "spec") == 1 and "Done when" in capsys.readouterr().err
    fill(repo, slug, Done_when="- the board shows scores")
    assert ob("goal", "phase", slug, "spec") == 0
    assert ob("goal", "phase", slug, "work") == 1 and "stages" in capsys.readouterr().err
    fill(repo, slug, Stages=STAGES)
    assert ob("goal", "phase", slug, "work") == 0
    assert ob("goal", "phase", slug, "done") == 1 and "green gate record" in capsys.readouterr().err
    assert ob("goal", "phase", slug, "talk") == 0                              # any step back
    assert page(repo, slug).get("phase") == "talk"
    assert ob("goal", "phase", "no-such", "talk") == 1


def test_the_new_formats_plan_and_done_when_count_as_stages_and_a_done_when(repo, capsys):
    slug = a_goal(repo, capsys)
    ideas.set_meta(repo / WIKI, slug, phase="talk")
    fill(repo, slug, Tech="### Done when\n- it scores\n\n### Plan\n- the code")
    assert ob("goal", "phase", slug, "spec") == 0
    assert ob("goal", "phase", slug, "work") == 0


# -- ask, answer ---------------------------------------------------------------------------------------------------------------------

def test_a_question_and_its_answer_are_read_back_by_the_page_and_the_hand(repo, capsys):
    slug = a_goal(repo, capsys)
    assert ob("goal", "ask", slug, "Which store first?", "--choices", "App Store/Google Play", "--pick", "App Store", "--why", "most of its users are on iPhone") == 0
    assert "question 1" in capsys.readouterr().out
    p = page(repo, slug)
    assert p.get("asks") == "person"
    assert p.section("Open questions") == "- Which store first? (**App Store** / Google Play) — most of its users are on iPhone"
    (card,) = goal_phase.outside_cards(p)
    assert (card["q"], card["choices"], card["pick"], card["by"]) == ("Which store first?", ["App Store", "Google Play"], 0, "codex")
    assert ob("goal", "ask", slug, "And the name?") == 0                       # a question with no choices
    assert ob("goal", "list") == 0 and "person" in capsys.readouterr().out
    assert ob("goal", "answer", slug, "1", "App Store") == 0
    capsys.readouterr()
    p = page(repo, slug)
    assert idea_questions.answers(p.section("Open questions")) == ["App Store", ""]
    assert f"  - Answered: App Store (the person, {dt.date.today().isoformat()})" in p.section("Open questions")
    assert p.get("asks") == "person" and goal_phase.outside_cards(p) == []     # the one with choices is answered; one question is left, so the goal still asks
    assert ob("goal", "answer", slug, "2", "Scoreboard") == 0 and "asks is cleared" in capsys.readouterr().out
    assert page(repo, slug).get("asks") == ""
    assert "asks" not in [k for k, _ in page(repo, slug).meta]
    assert ob("goal", "answer", slug, "3", "x") == 1 and "no question 3" in capsys.readouterr().err
    assert ob("goal", "answer", slug, "0", "x") == 1


def test_a_bad_question_is_a_bad_call(repo, capsys):
    slug = a_goal(repo, capsys)
    assert ob("goal", "ask", slug, "Which?", "--choices", "only one") == 2
    assert ob("goal", "ask", slug, "Which?", "--choices", "a/b", "--pick", "c") == 2
    assert ob("goal", "ask", slug, "   ") == 2
    assert page(repo, slug).section("Open questions") == "" and page(repo, slug).get("asks") == ""


# -- gate ----------------------------------------------------------------------------------------------------------------------------

def test_a_green_gate_is_recorded_in_the_pages_format_and_lets_a_goal_be_done(repo, capsys, monkeypatch):
    slug = a_goal(repo, capsys)
    for phase, sections in (("talk", {}), ("spec", {"Done_when": "- it scores"}), ("work", {"Stages": STAGES})):
        fill(repo, slug, **sections)
        assert ob("goal", "phase", slug, phase) == 0
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "the goal")
    fake_gate(monkeypatch)
    assert ob("gate", "--base", "HEAD", "--record", slug) == 0
    out = capsys.readouterr().out
    assert "3 passed" in out and "gate: green" in out
    short = git(repo, "rev-parse", "--short=7", "HEAD").strip()
    assert page(repo, slug).get("gate") == f"{short} · 0 files · green" == goal_phase.gate_of(
        {"tasks": [{"commit": short, "finished": "1", "diff": {"files": 0}, "tests": {"green": True, "ran": True}}]})
    assert ob("goal", "phase", slug, "done") == 0 and page(repo, slug).get("phase") == "done"
    # the record is for a commit; a later commit is a record for another
    (repo / "b.txt").write_text("more")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "more")
    assert ob("goal", "phase", slug, "work") == 0
    assert ob("goal", "phase", slug, "done") == 1 and "not for HEAD" in capsys.readouterr().err


def test_a_red_or_unfinished_gate_is_recorded_as_it_is_and_never_lets_a_goal_be_done(repo, capsys, monkeypatch):
    slug = a_goal(repo, capsys)
    fake_gate(monkeypatch, ok=False)
    assert ob("gate", "--base", "HEAD", "--record", slug) == 1
    assert page(repo, slug).get("gate").endswith("· red")
    fake_gate(monkeypatch, ok=False, env="pytest is not installed")
    assert ob("gate", "--base", "HEAD", "--record", slug) == 1
    assert page(repo, slug).get("gate").endswith("· did not finish")
    capsys.readouterr()
    fake_gate(monkeypatch, ran=False)
    before = page(repo, slug).get("gate")
    assert ob("gate", "--base", "HEAD", "--record", slug) == 1 and "no tests ran" in capsys.readouterr().err
    assert page(repo, slug).get("gate") == before


def test_the_gate_runs_the_projects_own_command_on_the_checkout_itself(repo, capsys):
    (repo / "orkcraft.toml").write_text('[gate]\nrun = "true"\nalways = []\n', encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "gate")
    slug = a_goal(repo, capsys)
    assert ob("gate", "--base", "HEAD", "--record", slug) == 0
    assert "gate: green" in capsys.readouterr().out and page(repo, slug).get("gate").endswith("· green")
    (repo / "orkcraft.toml").write_text('[gate]\nrun = "false"\nalways = []\n', encoding="utf-8")
    assert ob("gate", "--base", "HEAD") == 1 and "gate: red" in capsys.readouterr().out
    assert ob("gate", "--base", "nowhere") == 2


def test_a_record_is_refused_while_tracked_files_have_uncommitted_changes(repo, capsys, monkeypatch):
    slug = a_goal(repo, capsys)
    (repo / "a.txt").write_text("changed")
    fake_gate(monkeypatch)
    assert ob("gate", "--record", slug) == 1 and "a.txt has changes" in capsys.readouterr().err
    assert ob("gate", "--base", "HEAD") == 0                                   # saying the result needs no clean tree


# -- init ----------------------------------------------------------------------------------------------------------------------------

def test_init_writes_the_rules_and_the_ci_step_and_commits_nothing(repo, capsys):
    before = head(repo)
    assert ob("init", "--ci") == 0
    out = capsys.readouterr().out
    assert "wrote AGENTS.md" in out and f"wrote {WIKI}/BOARD.md" in out and "wrote .github/workflows/orkboard-check.yml" in out and "commits nothing" in out
    assert agent_rules.has_rules(repo) and agent_rules.check(repo, WIKI, decisions=agent_rules.decisions_of(repo)) == []
    text = (repo / ".github/workflows/orkboard-check.yml").read_text(encoding="utf-8")
    assert "pull_request:" in text and f'"{WIKI}/**"' in text and "uvx --from git+https://github.com/orkCraft/orkBoard orkboard check" in text and "push" not in text
    assert ob("init") == 0 and "nothing to write" in capsys.readouterr().out    # twice changes nothing
    assert head(repo) == before


def test_init_leaves_a_workflow_that_is_the_persons_own(repo, capsys):
    mine = repo / ".github" / "workflows" / "orkboard-check.yml"
    mine.parent.mkdir(parents=True)
    mine.write_text("name: mine\n", encoding="utf-8")
    assert ob("init", "--ci") == 0 and "is your own file" in capsys.readouterr().out
    assert mine.read_text(encoding="utf-8") == "name: mine\n"


def public(repo, monkeypatch):
    """The repository's remote is on GitHub, and GitHub's anonymous check answers 200: public."""
    git(repo, "remote", "set-url", "origin", "https://github.com/acme/public.git")
    monkeypatch.setattr(board_branch, "http_status", lambda url: 200)


def test_init_refuses_a_public_repository_in_words_naming_both_answers(repo, capsys, monkeypatch):
    public(repo, monkeypatch)
    assert ob("init", "--ci") == 1
    err = capsys.readouterr().err
    assert "This repository is public." in err and "init --publish" in err and "init --keep-off" in err and "a later No does not take them back" in err
    assert not (repo / "AGENTS.md").exists() and not (repo / ".github").exists() and not (repo / "orkcraft.toml").exists()


def test_init_publish_answers_f_first_and_then_writes_the_rules(repo, capsys, monkeypatch):
    public(repo, monkeypatch)
    assert ob("init", "--publish") == 0
    assert "in_code = true" in capsys.readouterr().out and agent_rules.has_rules(repo)
    assert ob("init") == 0
    assert not (repo / ".orkcraft").exists(), "the look at GitHub leaves nothing in the checkout"


def test_init_keep_off_answers_f_and_writes_no_rules(repo, capsys, monkeypatch):
    public(repo, monkeypatch)
    assert ob("init", "--keep-off") == 0
    assert "in_code = false" in capsys.readouterr().out and not (repo / "AGENTS.md").exists()


# -- no word commits -----------------------------------------------------------------------------------------------------------------

def test_no_word_makes_a_commit(repo, capsys, monkeypatch):
    fake_gate(monkeypatch)
    before, branches = head(repo), git(repo, "for-each-ref", "--format=%(refname)", "refs/heads")
    slug = a_goal(repo, capsys)
    for argv in (("init", "--ci"), ("goal", "list"), ("goal", "take", slug, "--by", "codex"), ("goal", "phase", slug, "talk"),
                 ("goal", "ask", slug, "Which?", "--choices", "a/b"), ("goal", "answer", slug, "1", "a"), ("gate", "--base", "HEAD", "--record", slug), ("check",)):
        ob(*argv)
        assert head(repo) == before, argv
    capsys.readouterr()
    assert git(repo, "for-each-ref", "--format=%(refname)", "refs/heads") == branches
    assert git(repo, "log", "--oneline").count("\n") == 1                      # the one commit of the fixture, none of ours
    assert git(repo, "status", "--porcelain").strip()                           # the files are in the working tree, for the person to commit


def test_outside_a_checkout_a_word_is_refused_in_words(tmp_path, monkeypatch, capsys):
    bare = tmp_path / "not-git"
    bare.mkdir()
    monkeypatch.chdir(bare)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    assert ob("goal", "list") == 1 and goals.NO_GIT in capsys.readouterr().err
    assert ob("check") == 1


def test_init_writes_a_subagent_and_a_forked_skill_for_each_seat_the_project_has_spec_154_c(repo, capsys):
    assert ob("init") == 0
    out = capsys.readouterr().out
    for path in (".claude/agents/ork-orkmaster.md", ".claude/agents/ork-grunt.md", ".claude/skills/orkmaster/SKILL.md", ".claude/skills/taskmaster/SKILL.md", ".claude/skills/orkboard/SKILL.md"):
        assert f"wrote {path}" in out and (repo / path).is_file(), path
    assert "context: fork\nagent: ork-orkmaster\n" in (repo / ".claude/skills/orkmaster/SKILL.md").read_text(encoding="utf-8")
    assert not (repo / ".claude/skills/grunt").exists() and not list((repo / ".claude/skills").glob("*-leader"))      # a project with no party has no leader's files
    assert "isolation: worktree" in (repo / ".claude/agents/ork-grunt.md").read_text(encoding="utf-8")
    assert agent_rules.check(repo, WIKI, decisions=agent_rules.decisions_of(repo)) == []


def test_a_question_a_written_decision_settles_is_answered_by_its_reference_and_a_made_up_one_is_refused(repo, capsys):
    """Decisions §259: `--decided-by` writes the reference as the answer's who; a reference the project does not hold is refused, a malformed one is a bad call."""
    (repo / "docs").mkdir(exist_ok=True)
    (repo / "docs" / "decisions.md").write_text("# Decisions\n\n## 7. The score board shows three players (1 November 2026, the owner)\n\nThree.\n")
    (repo / "docs" / "specs").mkdir(exist_ok=True)
    (repo / "docs" / "specs" / "12-the-board.md").write_text("# 12. The board\n")
    slug = a_goal(repo, capsys)
    for q in ("How many players?", "Which order?", "What colour?"):
        assert ob("goal", "ask", slug, q) == 0
    capsys.readouterr()
    assert ob("goal", "answer", slug, "1", "three", "--decided-by", "§7") == 0 and "answered by §7" in capsys.readouterr().out
    assert ob("goal", "answer", slug, "2", "by score", "--decided-by", "spec 12 B.2") == 0
    capsys.readouterr()
    assert ob("goal", "answer", slug, "3", "green", "--decided-by", "§99") == 1 and "not in this project" in capsys.readouterr().err
    assert ob("goal", "answer", slug, "3", "green", "--decided-by", "the owner said so") == 2
    today = dt.date.today().isoformat()
    text = page(repo, slug).section("Open questions")
    assert f"  - Answered: three (decided by §7, {today})" in text and f"  - Answered: by score (decided by spec 12 B.2, {today})" in text
    assert idea_questions.answers(text) == ["three", "by score", ""] and page(repo, slug).get("asks") == "person"     # the third is still the person's
