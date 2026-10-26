"""Spec 88 §3 (docs/specs/88-assets-and-play.md; spec 89 §3 reads it too): a commit of dev → the goal and the task that landed it, through the
tasks' `commit` and `subjects` (core/idea_runner.py keeps them on landing); a commit of the person's own is no goal's. Real git repositories."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from orkboard.realm import commit_goal, ideas
from orkboard.realm.idea_git import IdeaGit


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A project on `dev` (checked out), one commit of the person's."""
    r = tmp_path / "repo"
    r.mkdir()
    git(r, "init", "-b", "main")
    git(r, "config", "user.email", "t@x")
    git(r, "config", "user.name", "T")
    (r / ".gitignore").write_text(".orkcraft/\n")
    (r / "a.txt").write_text("a\n")
    git(r, "add", "-A")
    git(r, "commit", "-m", "start")
    git(r, "checkout", "-q", "-b", "dev")
    return r


def state(repo: Path) -> Path:
    return repo / ".orkcraft"


def commit(path: Path, name: str, text: str, message: str = "") -> str:
    (path / name).parent.mkdir(parents=True, exist_ok=True)
    (path / name).write_text(text)
    git(path, "add", "-A")
    git(path, "commit", "-q", "-m", message or f"edit {name}")
    return git(path, "rev-parse", "HEAD")


def land(repo: Path, slug: str, tid: str, files: dict[str, str]) -> tuple[str, list[str]]:
    """A task as the runner runs it: a worktree off dev, its commits, landed into dev; its plan keeps `commit` and `subjects`."""
    g = IdeaGit(repo)
    path, branch = g.prepare(slug, tid, "dev")
    for name, text in files.items():
        commit(path, name, text)
    sha, subjects, _note = g.land(path, branch, "dev", push=False)
    g.remove(path)
    folder = ideas.state_folder(state(repo), slug)
    folder.mkdir(parents=True, exist_ok=True)
    plan = ideas.plan(state(repo), slug) or {"tasks": []}
    plan["tasks"].append({"id": tid, "title": f"Task {tid}", "state": "merged", "commit": sha, "subjects": subjects})
    (folder / "plan.json").write_text(json.dumps(plan))
    return sha, subjects


def test_a_commit_a_task_landed_is_its_goals_and_both_commits_of_a_two_commit_task_are(repo):
    sha, subjects = land(repo, "dark-mode", "k1", {"x.css": "x\n", "y.css": "y\n"})
    assert len(subjects) == 2
    first = git(repo, "rev-parse", f"{sha}~1")
    assert commit_goal.of(state(repo), repo, sha) == {"goal": "dark-mode", "task": "k1"}
    assert commit_goal.of(state(repo), repo, first) == {"goal": "dark-mode", "task": "k1"}
    assert commit_goal.of(state(repo), repo, sha[:8]) == {"goal": "dark-mode", "task": "k1"}          # a short sha too
    start = git(repo, "rev-parse", "main")
    assert commit_goal.of(state(repo), repo, start) == {}                                              # before any task: the person's own


def test_a_persons_commit_between_two_landings_or_after_the_last_is_no_goals(repo):
    one, _ = land(repo, "dark-mode", "k1", {"x.css": "x\n"})
    own = commit(repo, "notes.md", "mine\n", "my own change")
    two, _ = land(repo, "jingle", "k2", {"sfx/jump.txt": "j\n"})
    after = commit(repo, "later.md", "mine\n", "after")
    s = state(repo)
    assert commit_goal.of(s, repo, one) == {"goal": "dark-mode", "task": "k1"}
    assert commit_goal.of(s, repo, two) == {"goal": "jingle", "task": "k2"}
    assert commit_goal.of(s, repo, own) == {} and commit_goal.of(s, repo, after) == {}
    index = commit_goal.index(s, repo)
    assert set(index) == {one, two} and index[two] == {"goal": "jingle", "task": "k2"}


def test_a_task_that_brought_nothing_or_a_commit_not_in_dev_or_no_sha_is_none(repo):
    sha, _ = land(repo, "dark-mode", "k1", {"x.css": "x\n"})
    plan = ideas.plan(state(repo), "dark-mode")
    plan["tasks"].append({"id": "k2", "state": "merged", "commit": sha, "subjects": []})            # a clean check: nothing landed
    plan["tasks"].append({"id": "k3", "state": "review", "commit": "", "subjects": []})
    (ideas.state_folder(state(repo), "dark-mode") / "plan.json").write_text(json.dumps(plan))
    assert commit_goal.of(state(repo), repo, sha) == {"goal": "dark-mode", "task": "k1"}
    git(repo, "checkout", "-q", "main")
    elsewhere = commit(repo, "m.txt", "m\n")
    git(repo, "checkout", "-q", "dev")
    assert commit_goal.of(state(repo), repo, elsewhere) == {}
    for junk in ("", "zz", "HEAD", "--all", None, 42):
        assert commit_goal.of(state(repo), repo, junk) == {}                       # type: ignore[arg-type]
    assert commit_goal.index(state(repo), repo, "no-such-branch") == {} and commit_goal.head(repo, "../x") == ""


def test_the_index_follows_dev_and_the_plans(repo):
    one, _ = land(repo, "dark-mode", "k1", {"x.css": "x\n"})
    assert set(commit_goal.index(state(repo), repo)) == {one}
    two, _ = land(repo, "dark-mode", "k2", {"y.css": "y\n"})
    assert set(commit_goal.index(state(repo), repo)) == {one, two}                # dev moved, the plan changed: read anew


def test_since_is_a_commit_of_dev_or_a_time(repo):
    first = git(repo, "rev-parse", "HEAD")
    later = commit(repo, "b.txt", "b\n")
    assert commit_goal.resolve(repo, first, "dev") == first and commit_goal.resolve(repo, first[:7], "dev") == first
    assert commit_goal.resolve(repo, "2099-01-01T00:00:00+00:00", "dev") == later
    assert commit_goal.resolve(repo, "1999-01-01", "dev") == ""
    git(repo, "checkout", "-q", "main")
    other = commit(repo, "m.txt", "m\n")
    git(repo, "checkout", "-q", "dev")
    for junk in (other, "", "dev~1", "HEAD", "--output=x", "../../etc", None):
        assert commit_goal.resolve(repo, junk, "dev") == ""                         # not dev's, or not a commit or a time


def test_the_last_commit_that_touched_each_file(repo):
    since = git(repo, "rev-parse", "HEAD")
    a = commit(repo, "art/a.png", "1")
    b = commit(repo, "art/b.png", "1")
    a2 = commit(repo, "art/a.png", "2")
    got = commit_goal.last_touch(repo, "dev", since)
    assert {p: v["sha"] for p, v in got.items()} == {"art/a.png": a2, "art/b.png": b} and a != a2
    assert got["art/a.png"]["at"][:4].isdigit()
    whole = commit_goal.last_touch(repo, "dev")
    assert whole["a.txt"]["sha"] == since and whole["art/a.png"]["sha"] == a2
    assert commit_goal.last_touch(repo, "dev", "not-a-sha") == {}
