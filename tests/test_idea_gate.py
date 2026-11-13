"""The gate, dev → main (docs/specs/49-one-window.md §2.1): `ideas.gate` and `ideas.gate_merge` on a real fixture repository
(realm/idea_gate.py, gui/ideas_gate.py)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from orkboard.gui.board_host import BoardPhone, CommandError, Orkboard
from orkboard.realm import event_log, idea_gate, ideas
from orkboard.realm.idea_git import IdeaGit


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def commit_in(path: Path, name: str, text: str) -> str:
    (path / name).write_text(text)
    git(path, "add", "-A")
    git(path, "commit", "-m", f"edit {name}")
    return git(path, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """main holds `a.txt` (start) and `old.txt` (older work); dev is cut from it. Nothing else is checked out but main."""
    r = tmp_path / "repo"
    r.mkdir()
    git(r, "init", "-b", "main")
    git(r, "config", "user.email", "t@x")
    git(r, "config", "user.name", "T")
    (r / ".gitignore").write_text(".orkcraft/\n")
    (r / "orkcraft.toml").write_text("[gate]\nrun = \"true\"\n")          # a gate with tests: a project with none is refused its way to main (decisions §274.3)
    (r / "a.txt").write_text("a\n")
    git(r, "add", "-A")
    git(r, "commit", "-m", "start")
    commit_in(r, "old.txt", "older work\n")
    git(r, "branch", "dev")
    return r


@pytest.fixture
def host(repo: Path):
    h = Orkboard(repo)
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def land(repo: Path, slug: str, task: str, name: str, text: str = "x\n") -> str:
    """A task's work landed in dev the way the runner does: its commit is dev's new head."""
    g = IdeaGit(repo)
    path, branch = g.prepare(slug, task, "dev")
    commit_in(path, name, text)
    commit, _subjects, _note = g.land(path, branch, "dev", push=False)
    g.remove(path)
    return commit


def idea(host, text: str) -> str:
    root = host.ideas.root()
    goal = next((t["slug"] for t in ideas.tracks(root, make=False) if t["slug"] != "general"), None) or ideas.add_track(root, "First goal")
    return host.command("ideas.add", {"text": text, "track": goal, "hold": True})["slug"]


def merged(host, slug: str, review: bool = True, **commits: str) -> None:
    """The idea's plan: a merged task per `id=commit` (a commit of "" for a check that landed nothing), a task at Review."""
    tasks = [{"id": tid, "title": f"Task {tid}", "state": "merged", "commit": c, "after": []} for tid, c in commits.items()]
    if review:
        tasks.append({"id": "rv", "title": "Waiting", "state": "review", "commit": "", "after": []})
    ideas.save_plan(host.ideas.state_dir, slug, {"idea": slug, "made_at": "2026-10-21T09:00:00", "passed_at": None, "tasks": tasks})


def events(host, name: str = "gate_merged") -> list[dict]:
    return [r for r in event_log.read(Path(host.repo_root)) if r["event"] == name]


@pytest.fixture
def work(host, repo):
    """dev two tasks of one idea ahead of main (two files), another idea's task already in main, a third's still at Review."""
    first, second = idea(host, "Sync the queue\nwith the server"), idea(host, "Retry on failure")
    c1 = land(repo, first, "k1", "q.txt", "queue\n")
    c2 = land(repo, first, "k2", "r.txt", "retry\n")
    merged(host, first, review=False, k1=c1, k2=c2)
    merged(host, second, k1=git(repo, "rev-parse", "main"), c1="")
    return first, second, c1, c2


# -- ideas.gate ---------------------------------------------------------------------------------------------------

def test_the_gate_counts_what_dev_holds_and_lists_the_ideas_by_their_tasks_commits(host, repo, work, monkeypatch):
    first, _second, c1, c2 = work
    reads = []
    real = idea_gate._git
    monkeypatch.setattr(idea_gate, "_git", lambda cwd, *a, **k: reads.append(a[0]) or real(cwd, *a, **k))
    got = host.command("ideas.gate")
    assert reads.count("rev-list") == 1                                                      # one read for all the ideas
    assert got == {"into": "dev", "main": "main", "same": False, "commits": 2, "files": 2,
                   "ideas": [{"slug": first, "title": "Sync the queue", "goal": "first-goal", "tasks": 2, "main_ready": True, "main_reason": ""}]}
    assert host.command("ideas.gate") == got and BoardPhone.allowed(host, "ideas.gate", {}) and BoardPhone.allowed(host, "ideas.gate_merge", {"sealed": True, "sealed": True})
    assert git(repo, "rev-list", "main..dev").split() == [c2, c1]


# -- ideas.gate_merge ---------------------------------------------------------------------------------------------

def test_main_is_fast_forwarded_to_dev_the_checkout_follows_and_it_is_logged(host, repo, work):
    first, _second, _c1, c2 = work
    rev = host.snapshot()["ideas_rev"]
    got = host.command("ideas.gate_merge", {"sealed": True})
    assert got == {"ok": True, "commit": c2, "note": ""}
    assert git(repo, "rev-parse", "main") == git(repo, "rev-parse", "dev") == c2
    assert (repo / "q.txt").read_text() == "queue\n" and (repo / "r.txt").exists()          # main is checked out: its files follow
    assert git(repo, "status", "--porcelain", "--", "q.txt", "r.txt") == ""
    (e,) = events(host)
    assert (e["commits"], e["ideas"], e["files"], e["how"], e["pushed"], e["device"]) == (2, 1, 2, "fast-forward", False, "desktop")
    assert (e["into"], e["main"]) == ("dev", "main")
    assert host.snapshot()["ideas_rev"] > rev                                                # every face reads again
    assert host.command("ideas.gate")["commits"] == 0 and host.command("ideas.gate")["ideas"] == []
    with pytest.raises(CommandError, match="Nothing in dev waits for main"):
        host.command("ideas.gate_merge", {"sealed": True})
    assert len(events(host)) == 1


def worktrees(repo: Path) -> list[str]:
    return [ln for ln in git(repo, "worktree", "list", "--porcelain").splitlines() if ln.startswith("worktree ")]


def test_a_merge_commit_is_made_when_main_moved_and_no_worktree_is_left(host, repo, work):
    first, _second, c1, c2 = work
    other = commit_in(repo, "main-only.txt", "main moved\n")                                 # main is ahead of where dev was cut
    got = host.command("ideas.gate_merge", {"sealed": True})
    main = git(repo, "rev-parse", "main")
    assert got == {"ok": True, "commit": main, "note": ""} and main not in (other, c2)
    assert git(repo, "log", "-1", "--format=%s", "main") == "Merge dev into main"
    assert git(repo, "rev-parse", "main^1") == other and git(repo, "rev-parse", "main^2") == c2
    assert (repo / "q.txt").exists() and (repo / "main-only.txt").exists() and git(repo, "status", "--porcelain") == ""
    assert git(repo, "rev-parse", "dev") == c2                                               # the gate never moves dev
    assert not (repo / ".orkcraft" / "worktrees" / idea_gate.WORKTREE).exists()
    assert not [w for w in worktrees(repo) if idea_gate.WORKTREE in w]
    (e,) = events(host)
    assert (e["how"], e["commits"], e["ideas"], e["files"]) == ("merge", 2, 1, 2)
    assert host.command("ideas.gate")["commits"] == 0


def test_a_conflict_is_refused_main_is_as_it_was_and_no_worktree_is_left(host, repo):
    land(repo, idea(host, "Change a"), "k1", "a.txt", "dev's a\n")
    other = commit_in(repo, "a.txt", "main's a\n")
    with pytest.raises(CommandError, match=r"^dev and main conflict in a\.txt: merge main into dev first$"):
        host.command("ideas.gate_merge", {"sealed": True})
    assert git(repo, "rev-parse", "main") == other and git(repo, "status", "--porcelain") == ""
    assert (repo / "a.txt").read_text() == "main's a\n"
    assert not (repo / ".orkcraft" / "worktrees" / idea_gate.WORKTREE).exists() and not [w for w in worktrees(repo) if idea_gate.WORKTREE in w]
    assert events(host) == []
    c = commit_in(repo, "z.txt", "z\n")                                                      # the next try is not blocked by a leftover
    with pytest.raises(CommandError, match="conflict in a.txt"):
        host.command("ideas.gate_merge", {"sealed": True})
    assert git(repo, "rev-parse", "main") == c


# -- pushing main -------------------------------------------------------------------------------------------------

def origin(repo: Path, tmp_path: Path) -> Path:
    bare = tmp_path / "origin.git"
    subprocess.run(["git", "init", "--bare", "-b", "main", str(bare)], check=True, capture_output=True)
    git(repo, "remote", "add", "origin", str(bare))
    git(repo, "push", "-q", "origin", "main")
    return bare


def test_main_is_pushed_when_the_project_pushes_after_merging(host, repo, work, tmp_path):
    bare = origin(repo, tmp_path)
    host.command("ideas.into", {"push": True})
    got = host.command("ideas.gate_merge", {"sealed": True})
    assert got["note"] == "" and git(bare, "rev-parse", "main") == git(repo, "rev-parse", "main") == got["commit"]
    assert events(host)[0]["pushed"] is True


def test_a_push_that_fails_is_a_note_and_main_has_moved_all_the_same(host, repo, work, tmp_path):
    git(repo, "remote", "add", "origin", str(tmp_path / "nowhere.git"))
    host.command("ideas.into", {"push": True})
    got = host.command("ideas.gate_merge", {"sealed": True})
    assert got["note"].startswith("push failed") and got["commit"] == git(repo, "rev-parse", "main") == git(repo, "rev-parse", "dev")
    assert events(host)[0]["pushed"] is False

