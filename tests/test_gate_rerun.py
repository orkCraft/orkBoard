"""Spec 149 E (decisions §253.5): a red from before is not the task's. The red tests run again alone, then on the base; flaky and red before are
said, spend no try and call no session; what is left is the task's. Real pytest on a small repository, the gate's first output written by hand."""
from __future__ import annotations

import subprocess
import sys
import threading
from pathlib import Path

from orkboard.realm import gate_rerun
from orkboard.realm.idea_git import GateRun, IdeaGit
from tests.test_idea_runner import calls, events_of, plan_of, reviewing, town, wait_task  # noqa: F401  (town is a fixture)

TESTS = """import pathlib


def test_before():
    assert False


def test_flaky():
    assert True


def test_mine():
    assert not pathlib.Path("broken.flag").exists()
"""


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def red_output(*names: str) -> str:
    lines = "\n".join(f"FAILED tests/test_red.py::{n} - assert False" for n in names)
    return f"$ pytest\n=== short test summary info ===\n{lines}\n=== {len(names)} failed, 3 passed in 0.5s ===\n"


def task_with(town, files: dict[str, str]):
    (town.repo / "tests").mkdir(exist_ok=True)
    (town.repo / "tests" / "test_red.py").write_text(TESTS)
    git(town.repo, "add", "-A")
    git(town.repo, "commit", "-m", "tests that are red")
    g = IdeaGit(town.repo)
    path, _ = g.prepare("demo", "k1", "main")
    start = g.head(path)
    for name, text in files.items():
        (path / name).write_text(text)
    g.commit_left(path, "k1")
    return g, path, start


def test_flaky_red_before_and_the_tasks_own_are_told_apart(town):
    g, path, start = task_with(town, {"broken.flag": "x"})
    run = GateRun(False, red_output("test_before", "test_flaky", "test_mine"), True, "pytest", 1, 1.0)
    found = gate_rerun.sort_out(g, path, start, "main", run, threading.Event(), 300)
    assert found.flaky == ("tests/test_red.py::test_flaky",)
    assert found.red_before == ("tests/test_red.py::test_before",)
    assert found.left == ("tests/test_red.py::test_mine",)
    assert not list((town.repo / ".orkcraft" / "worktrees").glob("red-before-*"))           # the throwaway worktree is gone
    assert gate_rerun.words(found) == ["== red before this task: tests/test_red.py::test_before", "== flaky: tests/test_red.py::test_flaky"]
    told = gate_rerun.told(found, "long output")
    assert "test_mine" in told and "test_before" not in told.split("more were red")[0] and "1 more were red before your task" in told


def test_a_test_file_the_task_made_was_not_there_to_be_red_before(town):
    g, path, start = task_with(town, {"tests/test_new.py": "def test_new():\n    assert False\n"})
    out = "=== short test summary info ===\nFAILED tests/test_new.py::test_new - assert False\n=== 1 failed in 0.1s ===\n"
    found = gate_rerun.sort_out(g, path, start, "main", GateRun(False, out, True, "pytest", 1, 1.0), threading.Event(), 300)
    assert found.left == ("tests/test_new.py::test_new",)
    assert found.red_before == () and found.flaky == ()


def test_nothing_is_sorted_without_pytests_summary_with_more_failures_than_names_or_without_clock(town):
    g, path, start = task_with(town, {"x.txt": "x"})
    stop = threading.Event()
    assert gate_rerun.sort_out(g, path, start, "main", GateRun(False, "boom\n", True, "make", 2, 1.0), stop, 300) is None
    many = "FAILED tests/test_red.py::test_before - x\n=== 3 failed in 1s ===\n"
    assert gate_rerun.sort_out(g, path, start, "main", GateRun(False, many, True, "pytest", 1, 1.0), stop, 300) is None
    assert gate_rerun.sort_out(g, path, start, "main", GateRun(False, red_output("test_before"), True, "pytest", 1, 1.0), stop, 3) is None


def test_an_id_cut_at_a_space_is_its_test_alone():
    assert gate_rerun.node_key("tests/x.py::t[a") == "tests/x.py::t"
    assert gate_rerun.node_key("tests/x.py::t[a-b]") == "tests/x.py::t[a-b]"


def test_a_task_whose_only_red_was_there_before_it_is_green_and_no_session_is_sent_the_red(town):
    (town.repo / "tests").mkdir(exist_ok=True)
    (town.repo / "tests" / "test_red.py").write_text("def test_before():\n    assert False\n")
    (town.repo / "orkcraft.toml").write_text(f'[gate]\nrun = "{sys.executable} -m pytest -q tests/test_red.py"\n', encoding="utf-8")
    git(town.repo, "add", "-A")
    git(town.repo, "commit", "-m", "a red from before")
    plan_of(town, [{"id": "k1"}])
    runner, _ = reviewing(town)
    runner.events = True
    runner.start("demo")
    task = wait_task(runner, "k1", "review")
    assert len(calls(town)) == 1                                                       # the session worked once; none was sent the red
    tests = task["tests"]
    assert tests["green"] is True and tests["failed"] == 0 and tests["red_before"] == ["tests/test_red.py::test_before"] and tests["flaky"] == []
    log = runner.log("demo", "k1")
    assert log.count("== the gate, try") == 1 and "== red before this task: tests/test_red.py::test_before" in log
    (ran,) = events_of(town, "gate_ran")
    assert ran["verdict"] == "green" and ran["red_before"] == ["tests/test_red.py::test_before"] and ran["flaky"] == []


def test_exact_main_uses_checked_sha_and_preserves_mixed_identities(tmp_path, monkeypatch):
    from types import SimpleNamespace
    base = tmp_path / "base"
    (base / "tests").mkdir(parents=True)
    (base / "tests/test_red.py").touch()
    removed, forks = [], []
    g = SimpleNamespace(python=lambda: "python", remove=removed.append)
    ids = [f"tests/test_red.py::{n}" for n in ("flaky", "before", "new")]
    answers = iter([{ids[1], ids[2]}, {ids[1]}])
    monkeypatch.setattr(gate_rerun, "run_ids", lambda *a: next(answers))
    monkeypatch.setattr(gate_rerun, "_base_tree", lambda git, sha: forks.append(sha) or base)
    found = gate_rerun.sort_out(g, tmp_path, "exact-sha", "moving-main", GateRun(False, red_output("flaky", "before", "new"), code=1), threading.Event(), 30, exact_main_base=True)
    assert found.flaky == (ids[0],) and found.red_before == (ids[1],) and found.left == (ids[2],)
    assert forks == ["exact-sha"] and removed == [base]


def test_exact_mode_incomplete_budget_and_different_identity_are_unresolved(tmp_path, monkeypatch):
    from types import SimpleNamespace
    g = SimpleNamespace(python=lambda: "python")
    output = red_output("before")
    key = "tests/test_red.py::before"
    for out, budget in [(output, 0), (output.replace("1 failed", "2 failed"), 30)]:
        found = gate_rerun.sort_out(g, tmp_path, "sha", "main", GateRun(False, out, code=1), threading.Event(), budget, exact_main_base=True)
        assert found.unresolved == (key,)
    monkeypatch.setattr(gate_rerun, "run_ids", lambda *a: {"tests/test_other.py::other"})
    assert gate_rerun.sort_out(g, tmp_path, "sha", "main", GateRun(False, output, code=1), threading.Event(), 30, exact_main_base=True).unresolved == (key,)


def test_all_reported_identities_are_kept():
    assert len(gate_rerun.ids_failing(red_output(*(f"test_{n}" for n in range(31))))) == 31


def test_exact_cancel_removes_base_tree(tmp_path, monkeypatch):
    import pytest
    from types import SimpleNamespace
    base = tmp_path / "base"
    (base / "tests").mkdir(parents=True)
    (base / "tests/test_red.py").touch()
    removed = []
    g = SimpleNamespace(python=lambda: "python", remove=removed.append)
    key = "tests/test_red.py::before"
    def rerun(python, cwd, *args):
        if cwd == base:
            raise InterruptedError("stopped")
        return {key}
    monkeypatch.setattr(gate_rerun, "run_ids", rerun)
    monkeypatch.setattr(gate_rerun, "_base_tree", lambda *a: base)
    with pytest.raises(InterruptedError):
        gate_rerun.sort_out(g, tmp_path, "sha", "main", GateRun(False, red_output("before"), code=1), threading.Event(), 30, exact_main_base=True)
    assert removed == [base]


def test_same_base_diagnostics_own_distinct_worktrees(town):
    g, _, start = task_with(town, {"x.txt": "x"})
    first = second = None
    try:
        first = gate_rerun._base_tree(g, start)
        second = gate_rerun._base_tree(g, start)
        assert first is not None and second is not None and first != second
        g.remove(first)
        assert second.is_dir()
    finally:
        for path in (first, second):
            if path is not None:
                g.remove(path)


def test_exact_mode_abnormal_exit_keeps_failures_unresolved(tmp_path, monkeypatch):
    from types import SimpleNamespace
    g = SimpleNamespace(python=lambda: "python")
    def must_not_rerun(*args):
        raise AssertionError("an incomplete initial run cannot be excused")
    monkeypatch.setattr(gate_rerun, "run_ids", must_not_rerun)
    for code in (None, 2, 3, 4, 5, 127):
        found = gate_rerun.sort_out(g, tmp_path, "sha", "main",
                                   GateRun(False, red_output("before"), code=code),
                                   threading.Event(), 30, exact_main_base=True)
        assert found.unresolved == ("tests/test_red.py::before",)
        assert not found.flaky and not found.red_before


def test_strict_rerun_rejects_abnormal_exit_even_with_complete_summary(tmp_path, monkeypatch):
    from io import StringIO
    from types import SimpleNamespace
    key = "tests/test_red.py::before"
    monkeypatch.setattr(gate_rerun.jobs, "_wait", lambda *args: None)
    for code in (2, 3, 4, 5):
        monkeypatch.setattr(gate_rerun.subprocess, "Popen", lambda *a, **kw: SimpleNamespace(
            stdout=StringIO(red_output("before")), returncode=code))
        assert gate_rerun.run_ids("python", tmp_path, [key], threading.Event(), 30, strict=True) is None


def test_parameter_identity_with_separator_survives_real_rerun(tmp_path):
    test = tmp_path / "test_parameter.py"
    test.write_text('import pytest\n@pytest.mark.parametrize("x", [1], ids=["a - b"])\n'
                    'def test_value(x):\n    assert False\n')
    key = "test_parameter.py::test_value[a - b]"
    output = f"\x1b[31mFAILED\x1b[0m {key} - AssertionError: a - b\n=== 1 failed in 0.1s ==="
    assert gate_rerun.ids_failing(output) == [key]
    assert gate_rerun.run_ids(sys.executable, tmp_path, [key], threading.Event(), 30, strict=True) == {key}
