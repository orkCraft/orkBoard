"""Spec 149 D (decisions §253.4): a gate that ran out of its clock could not run; its words, its output and its event are kept, and Test again
calls no session."""
from __future__ import annotations

import json
import sys
import threading

import pytest

from orkboard.realm import idea_git
from orkboard.realm.idea_git import IdeaGit
from tests.test_idea_runner import calls, events_of, plan_of, reviewing, town, wait_task  # noqa: F401  (town is a fixture)

SLOW = f"{sys.executable} -c \"import time; print('started', flush=True); time.sleep(60)\""
FAST = f"{sys.executable} -c \"print('3 passed')\""


def gate_with_clock(town, run: str, minutes: float = 0.02) -> None:
    (town.repo / "orkcraft.toml").write_text(f"[gate]\nrun = {json.dumps(run)}\ntimeout_min = {minutes}\n", encoding="utf-8")


def committed(town, task: str = "k1"):
    g = IdeaGit(town.repo)
    path, _branch = g.prepare("demo", task, "main")
    (path / f"{task}.txt").write_text("x\n")
    g.commit_left(path, task)
    return g, path


def test_a_gate_run_that_ran_out_of_time_is_a_run_that_could_not_run_with_its_output_so_far(town):
    gate_with_clock(town, SLOW)
    g, path = committed(town)
    run = g.gate_run(path, "main", threading.Event())
    assert run.ok is False and run.ran and run.timed_out and run.code is None
    assert run.env.startswith("The tests did not finish in ") and run.env.endswith(("file", "files"))
    assert "started" in run.out and run.out.startswith("$ ")


def test_the_words_name_the_minutes_and_the_files():
    assert idea_git.DID_NOT_FINISH.format(minutes=15, s="s", n=1, f="") == "The tests did not finish in 15 minutes: 1 file"
    assert idea_git.DID_NOT_FINISH.format(minutes=1, s="", n=3, f="s") == "The tests did not finish in 1 minute: 3 files"


def test_a_task_whose_gate_timed_out_goes_to_review_with_its_commit_no_try_spent_and_test_again_calls_no_session(town):
    gate_with_clock(town, SLOW)
    plan_of(town, [{"id": "k1"}])
    runner, _ = reviewing(town)
    runner.events = True
    runner.start("demo")
    task = wait_task(runner, "k1", "review")
    assert len(calls(town)) == 1                                                       # the session worked once; none was sent the clock
    tests = task["tests"]
    assert tests["green"] is False and tests["env"].startswith("The tests did not finish in ") and tests["install"] == [] and "setup" not in tests
    assert task["look"] == "the tests could not run" and task["round"] == 1 and "no answer within" not in task["error"]
    log = runner.log("demo", "k1")
    assert log.count("== the gate, try") == 1 and "started" in log
    (ran,) = events_of(town, "gate_ran")
    assert ran["verdict"] == "could_not_run" and ran["exit"] is None and ran["task"] == "k1"
    assert runner.git.commits(runner.git.reopen("demo", "k1"), "dev")                  # its commit is kept on its branch
    gate_with_clock(town, FAST, 5)                                                     # the person raised the clock; Test again
    runner.regate("demo", "k1", False)
    task = wait_task(runner, "k1", "review")
    assert task["tests"]["green"] is True and not task["tests"].get("env") and len(calls(town)) == 1 and task["round"] == 1


def test_a_stop_is_still_a_stop(town):
    gate_with_clock(town, SLOW, 5)
    g, path = committed(town)
    cancel = threading.Event()
    cancel.set()
    with pytest.raises(InterruptedError):
        g.gate_run(path, "main", cancel)
