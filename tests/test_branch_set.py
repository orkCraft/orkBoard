"""Spec 168 F2 (decisions §283.27): the branches a discard plate deals to the hand (realm/branch_offer.py) and the command that sets them for the project (`ideas.branch_set`, gui/ideas_review.py):
the lower pile's plate (*dev*, `merge_into`) offers any local branch and a new one from dev, the upper (*main*, the release branch) main or dev; `orkboard/*`, `goal/*` and `idea/*` are never offered."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from orkboard.gui.board_host import CommandError, Orkboard
from orkboard.realm import branch_offer, event_log, first_open, goal_branch
from orkboard.realm.idea_git import IdeaGit


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    r = tmp_path / "repo"
    r.mkdir()
    git(r, "init", "-b", "main")
    git(r, "config", "user.email", "t@x")
    git(r, "config", "user.name", "T")
    (r / ".gitignore").write_text(".orkcraft/\n")
    (r / "a.txt").write_text("a\n")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "start")
    for b in ("dev", "next", "release", "orkboard/board", "orkboard/inbox", "goal/lobby", "idea/lobby/k1"):
        git(r, "branch", b)
    return r


@pytest.fixture
def host(repo: Path):
    h = Orkboard(repo)
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def events(repo: Path, name: str) -> list[dict]:
    return [r for r in event_log.read(repo) if r["event"] == name]


def test_the_boards_and_the_works_branches_are_never_offered(repo):
    for name in ("orkboard/board", "orkboard/inbox", "goal/lobby", "idea/lobby/k1", "idea/x", "orkboard/"):
        assert not branch_offer.allowed(name), name
    for name in ("main", "dev", "feature/x", "release-1.2", "my.orkboard"):
        assert branch_offer.allowed(name), name
    lower = branch_offer.offered(IdeaGit(repo), "dev", "dev", "main")
    assert lower[0] == "dev" and sorted(lower) == ["dev", "main", "next", "release"], "any local branch, the one now first, none of the Board's or the work's"
    upper = branch_offer.offered(IdeaGit(repo), "main", "dev", "main")
    assert upper == ["main", "dev"], "the upper pile's plate: main or dev"
    with pytest.raises(ValueError):
        branch_offer.offered(IdeaGit(repo), "other", "dev", "main")


def test_the_branch_now_is_first_even_when_it_is_a_branch_that_is_not_in_the_list(repo):
    assert branch_offer.offered(IdeaGit(repo), "dev", "main", "main")[0] == "main"
    assert branch_offer.offered(IdeaGit(repo), "main", "dev", "release")[:2] == ["release", "main"]


def test_a_plate_reads_what_it_stands_for_what_it_offers_and_where_a_new_branch_starts(host):
    lower = host.command("ideas.branch_set", {"which": "dev"})
    assert (lower["now"], lower["from"], lower["at_work"]) == ("dev", "dev", 0) and lower["branches"][0] == "dev" and "next" in lower["branches"]
    assert not [b for b in lower["branches"] if b.startswith(("orkboard/", "goal/", "idea/"))]
    upper = host.command("ideas.branch_set", {"which": "main"})
    assert upper["now"] == "main" and upper["branches"] == ["main", "dev"]


def test_choosing_the_lower_plates_branch_sets_the_projects_work_branch(host, repo):
    got = host.command("ideas.branch_set", {"which": "dev", "branch": "next"})
    assert got == {"ok": True, "which": "dev", "branch": "next"}
    assert host.command("ideas.review_list")["into"] == "next" and host.ideas.settings_now()["merge_into"] == "next"
    assert host.command("ideas.gate")["into"] == "next"
    ev = events(repo, event_log.BRANCH_SET)
    assert ev[-1]["which"] == "dev" and ev[-1]["branch"] == "next" and ev[-1]["was"] == "dev"


def test_choosing_the_upper_plates_branch_keeps_the_release_branch_where_the_first_open_kept_it(host, repo):
    got = host.command("ideas.branch_set", {"which": "main", "branch": "dev"})
    assert got["branch"] == "dev" and first_open.kept_branch(host.ideas.state_dir) == "dev"
    assert host.command("ideas.gate")["main"] == "dev"
    assert host.command("ideas.branch_set", {"which": "main"})["now"] == "dev"


def test_a_branch_not_on_offer_is_refused_in_words_and_nothing_changes(host, repo):
    for which, name in (("dev", "goal/lobby"), ("dev", "orkboard/board"), ("dev", "idea/lobby/k1"), ("dev", "nowhere"), ("main", "next"), ("main", "orkboard/inbox")):
        with pytest.raises(CommandError, match="is not a branch this pile can use"):
            host.command("ideas.branch_set", {"which": which, "branch": name})
    with pytest.raises(CommandError, match="which is dev or main"):
        host.command("ideas.branch_set", {"which": "table"})
    assert host.ideas.settings_now()["merge_into"] == "dev" and first_open.kept_branch(host.ideas.state_dir) in ("", None)
    assert not events(repo, event_log.BRANCH_SET)


def test_the_lower_plate_makes_a_new_branch_from_dev(host, repo):
    git(repo, "checkout", "-q", "dev")
    (repo / "dev.txt").write_text("d\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "dev work")
    git(repo, "checkout", "-q", "main")
    got = host.command("ideas.branch_set", {"which": "dev", "new": "spring"})
    assert got["branch"] == "spring" and host.ideas.settings_now()["merge_into"] == "spring"
    assert git(repo, "rev-parse", "spring") == git(repo, "rev-parse", "dev") != git(repo, "rev-parse", "main"), "cut from dev's head, not from main's"
    with pytest.raises(CommandError, match="a branch here already"):
        host.command("ideas.branch_set", {"which": "dev", "new": "next"})


def test_a_new_branch_is_refused_for_a_name_that_is_none_and_for_the_upper_plate(host, repo):
    for name in ("goal/x", "orkboard/x", "..", "a b", "-x"):
        with pytest.raises(CommandError, match="is not a name for a branch|is not|too long|missing|text"):
            host.command("ideas.branch_set", {"which": "dev", "new": name})
    with pytest.raises(CommandError, match="only the lower pile makes one"):
        host.command("ideas.branch_set", {"which": "main", "new": "spring"})
    assert not git(repo, "branch", "--list", "goal/x", "orkboard/x")


def test_the_warning_counts_the_goals_with_a_task_running(host):
    from orkboard.realm import ideas
    root, state = host.ideas.root(), host.ideas.state_dir
    party = next((t["slug"] for t in ideas.tracks(root, make=False) if t["slug"] != "general"), None) or ideas.add_track(root, "First party")
    slug = host.command("ideas.add", {"text": "Lobby", "track": party, "hold": True})["slug"]
    ideas.save_plan(state, slug, {"idea": slug, "made_at": "2026-10-21T09:00:00", "passed_at": None, "tasks": [{"id": "k1", "title": "T", "state": "running", "after": [], "round": 1}]})
    assert host.command("ideas.branch_set", {"which": "dev"})["at_work"] == 1
    ideas.save_plan(state, slug, {"idea": slug, "made_at": "2026-10-21T09:00:00", "passed_at": None, "tasks": [{"id": "k1", "title": "T", "state": "review", "after": [], "round": 1}]})
    assert host.command("ideas.branch_set", {"which": "dev"})["at_work"] == 0


def test_a_goals_reasons_are_said_through_the_glossary(repo):
    from orkboard.realm import lexicon
    assert lexicon.term("to_dev") == "To dev" and lexicon.term("to_dev_untested") == "To dev without the tests" and lexicon.term("try_again") == "Try again"
    assert goal_branch.words("dev_conflict", dev="next", branch="goal/x", files="a.py, b.py") == "next conflicts with goal/x in a.py, b.py"
    assert goal_branch.words("dev_no_tests", dev="next").endswith("send it with To dev without the tests") and "safe for next" in goal_branch.words("dev_no_tests", dev="next")
