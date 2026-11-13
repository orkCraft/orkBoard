"""Spec 143 A (decisions §250.1-2): a task is not told to write what the gate refuses, and the Board's pages it touched are put back by code at the
gate: no session called, no try spent, a line in the log and an event. Nothing left after that is a task that changed no file."""
from __future__ import annotations

import threading

from orkboard.realm import event_log

from tests.test_idea_runner import git, plan_of, town  # noqa: F401  (the fixture repository with a stub claude)
from tests.test_runner_35 import _runner

PAGE = "llm-wiki/general/pages/ideas/other.md"
NOT_THE_BOARDS = ("You are one task of a goal Orkboard leads: the Board's rules in AGENTS.md are for a tool that leads a goal, not for you. "
                  "Do not take a goal, move its phase or write the Board's pages, and do not read BOARD.md for this task.")


def _worktree(town):
    plan_of(town, [{"id": "k1"}])
    r, _ = _runner(town, merge_into="main")
    path, _branch = r.git.prepare("demo", "k1", "main")
    return r, path, r.git.head(path)


def _write(path, name, text):
    f = path / name
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text)


def _commit(path):
    git(path, "add", "-A")
    git(path, "-c", "user.name=T", "-c", "user.email=t@x", "commit", "-qm", "work")


def test_a_page_and_code_edited_leave_the_code_the_page_as_it_was_the_gate_run_and_no_session_called(town):
    r, path, start = _worktree(town)
    _write(path, "pkg/new.py", "X = 1\n")
    _write(path, PAGE, "---\nowner: board\n---\n# Other\n")
    _commit(path)
    calls = []
    r._session = lambda *a, **k: calls.append(a)
    problem, out = r._check(path, start, threading.Event(), "t", "demo", "k1")
    assert problem is None and out and calls == []
    assert not (path / PAGE).exists() and (path / "pkg" / "new.py").read_text() == "X = 1\n"
    assert git(path, "log", "-1", "--format=%s").strip() == "The Board's pages put back: a task never edits them"
    assert PAGE not in git(path, "diff", "--name-only", "main...HEAD")
    assert f"== the Board's pages put back: {PAGE}" in (town.state / "ideas" / "demo" / "k1.log").read_text()
    (e,) = [x for x in event_log.read(town.repo) if x["event"] == "task_pages_put_back"]
    assert (e["idea"], e["task"], e["files"]) == ("demo", "k1", [PAGE])
    r.git.remove(path)


def test_a_result_that_edits_only_a_page_is_told_it_changed_no_file_committed_by_itself_or_left_for_commit_left(town):
    for committed in (True, False):
        r, path, start = _worktree(town)
        _write(path, PAGE, "---\nowner: board\n---\n# Other\n")
        if committed:
            _commit(path)
        problem, out = r._check(path, start, threading.Event(), "t", "demo", "k1")
        assert problem == "You changed no file. Make the change the task asks for in this worktree." and out == ""
        assert not (path / PAGE).exists()
        r.git.remove(path)


def test_a_task_that_commits_and_undoes_its_own_change_changed_no_file(town):
    r, path, start = _worktree(town)
    _write(path, "pkg/x.py", "X = 1\n")
    _commit(path)
    git(path, "rm", "-q", "pkg/x.py")
    _commit(path)
    problem, _out = r._check(path, start, threading.Event(), "t", "demo", "k1")
    assert problem is not None and "changed no file" in problem
    r.git.remove(path)


def _prompt(town, size, kind="code"):
    plan_of(town, [{"id": "k1", "kind": kind}])
    _write(town.repo, "llm-wiki/general/pages/ideas/demo.md", "# Demo\n")
    r, _ = _runner(town)
    r.size_of = lambda slug: size
    plan = r.plan("demo")
    plan["tasks"][0]["role"] = "architect"
    return r._prompt("demo", plan, plan["tasks"][0])

