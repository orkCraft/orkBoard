"""Spec 149 F (decisions §253.6): a session is told what its sandbox allows, what it settled reaches the commit's message, and a commit is authored by the
running product's name."""
from __future__ import annotations

import subprocess
from pathlib import Path

from orkboard import brand
from orkboard.core import idea_task
from orkboard.realm import harnesses, steps_git
from orkboard.realm.idea_git import IdeaGit
from tests.test_idea_runner import plan_of, reviewing, town  # noqa: F401  (town is a fixture)


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def prompt_on(town, monkeypatch, tool: str) -> str:
    plan_of(town, [{"id": "k1"}])
    runner, _ = reviewing(town)
    monkeypatch.setattr(runner, "tool_of", lambda slug, task=None: tool)
    return runner._prompt("demo", runner.plan("demo"), runner.plan("demo")["tasks"][0])


def test_a_session_on_codex_is_told_not_to_commit_and_not_to_look_for_a_browser(town, monkeypatch):
    prompt = prompt_on(town, monkeypatch, "codex")
    assert "Git cannot write in this sandbox: do not commit; what you leave is committed for you" in prompt
    assert "A browser cannot start here: do not look for one; the gate runs the browser tests." in prompt
    assert ".ork-commit.md" in prompt and "Commit your work with git if you can" not in prompt


def test_a_session_on_a_tool_that_can_is_told_neither(town, monkeypatch):
    prompt = prompt_on(town, monkeypatch, "claude")
    assert "Commit your work with git if you can" in prompt
    assert "Git cannot write" not in prompt and "A browser cannot start here" not in prompt


def test_what_the_task_settled_goes_under_the_title_and_the_note_is_never_committed(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-b", "main")
    git(root, "config", "user.email", "t@x")
    git(root, "config", "user.name", "T")
    (root / "a.txt").write_text("a\n")
    git(root, "add", "-A")
    git(root, "commit", "-m", "start")
    g = IdeaGit(root)
    path, _ = g.prepare("demo", "k1", "main")
    (path / "k1.txt").write_text("done\n")
    (path / steps_git.COMMIT_FILE).write_text("Chose a list over a map: the order matters.\n")
    assert g.commit_left(path, "k1: add k1.txt") is True
    assert git(path, "log", "-1", "--format=%s") == "k1: add k1.txt"
    assert git(path, "log", "-1", "--format=%b") == "Chose a list over a map: the order matters."
    assert git(path, "log", "-1", "--format=%an|%ae") == f"{brand.name()}|{brand.name().lower()}@localhost"
    assert steps_git.COMMIT_FILE not in git(path, "ls-files") and not (path / steps_git.COMMIT_FILE).exists()
    (path / "k2.txt").write_text("more\n")
    g.commit_left(path, "k2")
    assert git(path, "log", "-1", "--format=%b") == ""                      # the note was read once


def test_the_commits_the_product_makes_say_its_name_and_the_boards_pages_say_its_board():
    assert brand.board_author() == (f"{brand.name()} board", f"board@{brand.name().lower()}.local")
    assert brand.git_identity() == ["-c", "user.name=Orkboard", "-c", "user.email=orkboard@localhost"]
    assert idea_task.CANNOT_COMMIT.startswith("Git cannot write in this sandbox")
