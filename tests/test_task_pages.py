"""Spec 143 A (decisions §250.1-2): a task is not told to write what the gate refuses, and the Board's pages it touched are put back by code at the
gate: no session called, no try spent, a line in the log and an event. Nothing left after that is a task that changed no file."""
from __future__ import annotations

import threading

from orkboard.realm import event_log, library, roles

from tests.test_idea_runner import git, plan_of, town  # noqa: F401  (the fixture repository with a stub claude)
from tests.test_runner_35 import _runner

PAGE = "llm-wiki/general/pages/ideas/other.md"
LEAN = "You do this task yourself. It is not to be planned: make the change it asks for, in this worktree."


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


def test_a_page_that_was_on_main_gets_its_text_back_and_a_file_that_is_no_page_is_never_touched(town):
    _write(town.repo, PAGE, "# Other\n\nold\n")
    git(town.repo, "add", "-A")
    git(town.repo, "commit", "-qm", "page")
    r, path, start = _worktree(town)
    _write(path, PAGE, "# Other\n\nPLAN\n")
    _write(path, "notes.md", "mine\n")
    _commit(path)
    problem, _out = r._check(path, start, threading.Event(), "t", "demo", "k1")
    assert problem is None and (path / PAGE).read_text() == "# Other\n\nold\n" and (path / "notes.md").read_text() == "mine\n"
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


def test_the_architect_is_not_told_to_write_a_plan_in_a_file_and_no_role_asks_for_one():
    assert "own file" not in library.get("architect").instruction
    assert "commit's message" in library.get("architect").instruction and "~600 lines" in library.get("architect").instruction
    assert "one job and the imports one way" in library.get("architect").instruction
    assert not [a.id for a in library.LIBRARY if "own file" in a.instruction]


def test_a_lean_code_task_is_told_it_does_it_a_standard_one_and_a_check_are_not_and_the_page_is_the_boards(town):
    roles.install(town.state, "architect", "Architect", "", "engineering", library.get("architect").instruction, ("code",))
    assert LEAN in _prompt(town, "lean")
    standard = _prompt(town, "standard")
    assert LEAN not in standard and "That page is the Board's: read it, never write to it." in standard
    assert LEAN not in _prompt(town, "lean", kind="review")
