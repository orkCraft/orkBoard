"""A task on Antigravity (the owner's logs of 26 October, afternoon): its prompt names the project's own gate, a run that is
not unchained is told to edit with its file tools, and a work turn that ended with no answer because a command was refused
fails the task once, in plain words, with no gate round that cannot help."""
from __future__ import annotations

import json
import shutil
import threading
from types import SimpleNamespace

import pytest

from orkboard.core.idea_runner import IdeaRunner
from orkboard.realm import harnesses, jobs, tool_errors, tool_run

from tests.test_idea_runner import plan_of, runner_of, tasks_of, town, wait_idle  # noqa: F401  (the fixture repository)

# agy's envelope from the logs: a docs task that asked for a terminal command, refused headless, and said nothing.
REFUSED = json.dumps({"conversation_id": "c1", "status": "SUCCESS", "response": "", "num_turns": 1,
                      "usage": {"input_tokens": 26158, "output_tokens": 1819, "total_tokens": 27977},
                      "denied_actions": [{"action": "command", "display_name": "RunCommand"}]})
JETSKI = ('jetski: no output produced — a tool required the "command" permission that headless mode cannot prompt for, '
          "so it was auto-denied.")


def _prompt(town) -> str:
    plan_of(town, [{"id": "k1"}])
    runner, _ = runner_of(town)
    plan = runner.plan("demo")
    return runner._prompt("demo", plan, plan["tasks"][0])


def test_the_prompt_names_orkboards_critical_tests_only_for_a_project_that_has_them(town):
    prompt = _prompt(town)
    assert ("the gate runs `python -m pytest -q tests/test_architecture.py tests/test_cli.py tests/test_updates.py` "
            "and the test files of the modules you touch") in prompt
    assert "a red gate comes back to you once" in prompt


def test_the_prompt_names_a_node_projects_npm_test(town):
    shutil.rmtree(town.repo / "tests")
    (town.repo / "orkcraft.toml").unlink()                       # no gate written: the project's own is derived
    (town.repo / "server").mkdir()
    (town.repo / "server" / "package.json").write_text(json.dumps({"scripts": {"test": "node --test"}}))
    prompt = _prompt(town)
    assert "the gate runs `npm test --prefix server`" in prompt
    assert "pytest" not in prompt and "test_architecture" not in prompt


def test_the_prompt_names_the_run_of_the_projects_own_file(town):
    (town.repo / "orkcraft.toml").write_text('[gate]\nrun = "make check"\n')
    prompt = _prompt(town)
    assert "the gate runs `make check`" in prompt and "pytest" not in prompt


def test_the_prompt_says_a_project_with_no_tests_waits_for_a_look(town):
    shutil.rmtree(town.repo / "tests")
    (town.repo / "orkcraft.toml").unlink()                       # no gate written: the project's own is derived
    prompt = _prompt(town)
    assert "This project has no tests" in prompt and "waits for a person's look" in prompt
    assert "pytest" not in prompt and "the gate runs" not in prompt


def test_agy_works_running_its_commands_in_its_sandbox_and_reads_running_none(tmp_path):
    # the owner, 26 October (decisions §107.7): a task's tests and builds are its work, so agy's work never asks
    h = harnesses.need("agy")
    said = lambda cmd: cmd[cmd.index("--print") + 1]                            # noqa: E731
    for cmd in (h.work("fix it", tmp_path), h.work("fix it", tmp_path, free=True)):
        assert said(cmd) == "fix it" and cmd.count("--dangerously-skip-permissions") == 1 and "--sandbox" in cmd
        assert cmd[cmd.index("--add-dir") + 1] == str(tmp_path)                 # its sandbox is the task's worktree
    read = h.read("spec it", tmp_path)
    assert said(read) == f"spec it\n\n{harnesses.AGY_NO_COMMANDS}" and "--dangerously-skip-permissions" not in read
    assert "--dangerously-skip-permissions" not in harnesses.need("claude").work("fix it", tmp_path)


def test_a_work_run_that_ended_with_no_answer_because_a_command_was_refused_is_a_failure_that_is_still_counted(tmp_path, monkeypatch):
    from orkboard.sources import telemetry
    spent = []
    monkeypatch.setattr(telemetry, "charge", lambda cost, *a, **k: spent.append(cost))
    monkeypatch.setattr(telemetry, "noted", lambda cost, *a, **k: spent.append(cost))
    monkeypatch.setattr(tool_run, "run_proc", lambda *a, **k: (0, REFUSED, JETSKI))
    with pytest.raises(tool_errors.ToolError) as got:
        jobs.run_work("agy", "write it", tmp_path, threading.Event())
    assert str(got.value) == ("Antigravity wanted to run RunCommand, which a run without a window refuses, and ended "
                              "with no answer. Pick another AI tool for this party.")
    assert got.value.kind == tool_errors.OTHER and spent                           # the spend was counted first
    good = json.dumps({"response": "done", "denied_actions": [{"action": "command", "display_name": "RunCommand"}]})
    monkeypatch.setattr(tool_run, "run_proc", lambda *a, **k: (0, good, ""))
    assert jobs.run_work("agy", "write it", tmp_path, threading.Event())[0] == "done"       # an answer given is used


def test_an_agy_task_refused_its_command_fails_once_in_plain_words_with_no_round_about_a_change_it_did_not_make(town, monkeypatch):
    plan_of(town, [{"id": "k1", "title": "Write the architecture"}])
    asked = []

    def agy(cmd, *a, **k):
        asked.append(cmd)
        return 0, REFUSED, JETSKI

    monkeypatch.setattr(tool_run, "run_proc", agy)
    settings = SimpleNamespace(ideas={"max_parallel": 1, "merge_into": "main", "push": False, "review": False})
    runner = IdeaRunner(town.repo, town.state, settings, SimpleNamespace(publish=lambda t, **d: None),
                        limits=lambda: [], party_of=lambda slug: {"tool": "agy"})
    runner.start("demo")
    assert wait_idle(runner)["state"] == "failed"
    task = tasks_of(town)["k1"]
    assert task["state"] == "failed"
    assert task["error"].startswith("Antigravity wanted to run RunCommand") and "Pick another AI tool" in task["error"]
    assert "changed no file" not in task["error"] and "still red" not in task["error"]
    assert len(asked) == 1                                                            # no second turn: sending it back could not help
    assert "--dangerously-skip-permissions" in asked[0]                               # it may run its commands, in its sandbox
