"""Spec 35 §13 on a fixture repository: the Board's own tree, detached at the work branch; a write is one commit of its
pages only and fast-forwards the branch (in place when the root is on it, by update-ref when not); the person checks
out the branch and back cleanly; uncommitted changes in those files hold it until the next write; writes within 10 s
are one commit; a task's worktree holds the specs; the move copies, commits, then removes only untracked copies."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from orkboard.gui.board_host import Orkboard
from orkboard.realm import event_log, ideas
from orkboard.realm.idea_git import BoardTree, IdeaGit

WIKI = "llm-wiki/general"


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "t@x")
    git(repo, "config", "user.name", "T")
    (repo / ".gitignore").write_text(".orkcraft/\n")
    (repo / "app.py").write_text("x = 1\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "start")
    return repo


def _tree(repo):
    t = BoardTree(repo, repo / ".orkcraft", WIKI, lambda: "dev")
    t.ensure()
    return t


def _page(t, name, text="# Page\n"):
    path = t.root() / "pages" / "ideas" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def _dated_commit(t, day, message):
    import os
    env = {**os.environ, "GIT_AUTHOR_DATE": f"{day}T12:00:00+00:00", "GIT_COMMITTER_DATE": f"{day}T12:00:00+00:00"}
    subprocess.run(["git", "add", "-A"], cwd=t.path, check=True, capture_output=True)
    subprocess.run(["git", "-c", "user.name=T", "-c", "user.email=t@x", "commit", "-qm", message], cwd=t.path, check=True,
                   capture_output=True, env=env)


def test_the_day_each_page_was_laid_and_last_moved_are_read_in_one_log(repo, monkeypatch):
    t = _tree(repo)
    _page(t, "a.md")
    _page(t, "b.md")
    _dated_commit(t, "2026-10-01", "lay a and b")
    _page(t, "b.md", "# Page\nphase: done\n")
    _page(t, "c.md")
    _dated_commit(t, "2026-10-05", "move b, lay c")
    _page(t, "a.md", "# Page\nedited\n")
    _dated_commit(t, "2026-10-09", "edit a")
    calls = []
    real = subprocess.run
    monkeypatch.setattr(subprocess, "run", lambda cmd, *a, **k: (calls.append(cmd), real(cmd, *a, **k))[1])
    laid, moved = t.laid_days(), t.moved_days()
    assert laid == {"a": "2026-10-01", "b": "2026-10-01", "c": "2026-10-05"}
    assert moved == {"a": "2026-10-09", "b": "2026-10-05", "c": "2026-10-05"}
    assert [c[1] for c in calls] == ["log", "log"]                       # one call for all pages, not one a page


def test_a_write_is_one_commit_of_the_pages_only_and_moves_the_branch_by_update_ref(repo):
    t = _tree(repo)
    _page(t, "a.md")
    (t.path / "stray.txt").write_text("not a page\n")
    t.note("Dark mode", "drafted", 0.0)
    got = t.flush(force=True)
    assert got["commit"] and got["pages"] == 1 and got["held"] == ""
    assert git(repo, "rev-parse", "dev") == got["commit"] and git(repo, "rev-parse", "main") != got["commit"]
    assert git(repo, "show", "--name-only", "--format=%an|%s", "dev").splitlines() == [
        "Orkboard board|board: Dark mode — drafted", "", f"{WIKI}/pages/ideas/a.md"]
    assert not (repo / WIKI).exists()                                    # the person's tree is not touched


def test_uncommitted_changes_in_those_files_hold_it_and_the_next_write_lands_it(repo):
    t = _tree(repo)
    _page(t, "c.md", "# one\n")
    t.flush(force=True)
    git(repo, "checkout", "-q", "dev")
    (repo / WIKI / "pages" / "ideas" / "c.md").write_text("# the person's own edit\n")
    _page(t, "c.md", "# two\n")
    got = t.flush(force=True)
    assert got["commit"] and "uncommitted" in got["held"] and git(repo, "rev-parse", "dev") != got["commit"]
    git(repo, "checkout", "--", f"{WIKI}/pages/ideas/c.md")
    _page(t, "d.md")
    got = t.flush(force=True)
    assert got["held"] == "" and git(repo, "rev-parse", "dev") == got["commit"]
    assert (repo / WIKI / "pages" / "ideas" / "c.md").read_text() == "# two\n"


def test_a_tasks_worktree_holds_the_specs_committed_before_it(repo):
    t = _tree(repo)
    _page(t, "spec.md", "# The spec\n")
    t.flush(force=True)
    path, _branch = IdeaGit(repo).prepare("spec", "k1", "dev")
    assert (path / WIKI / "pages" / "ideas" / "spec.md").read_text() == "# The spec\n"


def test_the_host_keeps_its_pages_in_the_tree_and_logs_each_commit(fake_repo):
    (fake_repo / ".gitignore").write_text(".orkcraft/\n")
    host = Orkboard(fake_repo)
    root = host.ideas.root()
    assert ".orkcraft/board" in root.as_posix()
    goal = ideas.add_track(root, "In the tree")
    host.command("ideas.add", {"text": "an idea", "track": goal, "hold": True})
    got = host.ideas.tree_flush(force=True)
    assert got["commit"] and got["held"] == ""
    assert git(fake_repo, "show", "--format=%s", "-s", "dev").startswith("board: ")
    (e,) = [r for r in event_log.read(Path(fake_repo)) if r["event"] == "board_committed"]
    assert e["commit"] == got["commit"] and e["pages"] >= 2 and e["what"]
    assert not (fake_repo / "llm-wiki").exists()


def test_a_file_of_the_project_is_edited_under_the_lock_and_committed_with_the_pages_in_one_commit(repo):
    """Spec 99 E §6.2: a goal's decision is the project's decisions file, edited as the work branch holds it and committed with the Board's pages, nothing else of the tree."""
    t = _tree(repo)
    _page(t, "a.md")
    (t.path / "stray.txt").write_text("not a page\n")
    seen = []
    got = t.edit_file("docs/decisions.md", lambda old: seen.append(old) or "# Decisions\n\n## 1. One\n", lambda: "board: decision 1 — One")
    assert seen == [""] and got["commit"] and got["held"] == "" and git(repo, "rev-parse", "dev") == got["commit"]
    assert git(repo, "show", "--name-only", "--format=%an|%s", "dev").splitlines() == ["Orkboard board|board: decision 1 — One", "", "docs/decisions.md", f"{WIKI}/pages/ideas/a.md"]
    assert not (repo / "docs").exists() and (t.path / "stray.txt").exists()                      # the person's tree is not touched; a stray file is not taken
    got = t.edit_file("docs/decisions.md", lambda old: old + "\n## 2. Two\n", "board: decision 2")
    assert git(repo, "show", "dev:docs/decisions.md").endswith("## 2. Two") and git(repo, "log", "-1", "--format=%s", "dev") == "board: decision 2" and got["held"] == ""


def test_a_tree_asked_where_the_board_goes_keeps_the_work_branch_when_the_answer_is_no(repo):
    answer = {"goes": True}
    t = BoardTree(repo, repo / ".orkcraft", WIKI, lambda: "dev", goes=lambda: answer["goes"])
    t.ensure()
    _page(t, "a.md")
    assert t.flush(force=True)["commit"] and "a.md" in git(repo, "ls-tree", "-r", "--name-only", "dev")
    answer["goes"] = False
    before = git(repo, "rev-parse", "dev")
    _page(t, "b.md")
    t.flush(force=True)
    assert git(repo, "rev-parse", "dev") != before and "a.md" not in git(repo, "ls-tree", "-r", "--name-only", "dev")       # the one commit that takes the pages out
    after = git(repo, "rev-parse", "dev")
    _page(t, "c.md")
    t.flush(force=True)
    assert git(repo, "rev-parse", "dev") == after and "c.md" in git(repo, "ls-tree", "-r", "--name-only", "refs/orkboard/pages")
