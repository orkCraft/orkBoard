"""Goal "The battle and the gate", stage H (decisions §303.5): Fix it before dev. On a goal unmerged on its own branch whose way to dev went red, `ideas.gate_fix_stage` goes only
on its seal and adds one task of the failing tests to the goal's plan through the runner's own plan writer, the goal set to work (core/idea_fix_stage.py), its cost the one
`ideas.gate_guards` said before. The runner is the host's own with its launch faked: no model, no work. Refused in words, nothing written, unsealed and on a goal done in dev."""
from __future__ import annotations

import hashlib
import sys
import threading
from pathlib import Path

import pytest

from orkboard.core import idea_fix_stage, idea_undo
from orkboard.core.idea_plan import _task
from orkboard.gui.board_host import CommandError, Orkboard
from orkboard.realm import event_log, goal_branch, harnesses, ideas, jobs

PAGE = "---\nowner: board\nkind: idea\ntrack: tech\norder: 1\nphase: work\nschema: 3\n---\n# Lobby\n\n## Gist\nA goal.\n"
IDS = ["tests/test_red.py::test_a", "tests/test_bare.py::test_c"]
ENTRIES = ("ask", "call", "work_call", "_claude", "_claude_work", "board_ask", "read_now", "draft", "answer", "reword", "decide", "accept_step")


def _boom(*a, **k):
    raise AssertionError("a model was reached")


def _red(state: Path, **more) -> None:
    """The goal's way to dev red on two failing tests, as realm/goal_branch.py keeps it (stage E)."""
    goal_branch.update(state, "goal", branch="goal/goal", ready=True, blocked="The tests are red on dev with the goal: 2 failed", blocked_kind="red",
                       failing=IDS, files=["tests/test_red.py", "tests/test_bare.py"], **more)


@pytest.fixture
def host(fake_repo, monkeypatch):
    h = Orkboard(fake_repo)
    root, state = h.ideas.root(), h.ideas.state_dir
    ideas.add_track(root, "Tech")
    (root / ideas.IDEAS).mkdir(parents=True, exist_ok=True)
    (root / ideas.IDEAS / "goal.md").write_text(PAGE, encoding="utf-8")
    ideas.save_state(state, "goal", state="done")
    merged = {**_task("k1", "Build the lobby", "Build it", "code", "warrior", []), "state": "merged", "commit": "abc1234", "step": 1, "party": "tech"}
    ideas._write_json(ideas.state_folder(state, "goal") / "plan.json", {"idea": "goal", "made_at": "2026-11-13T09:00:00", "passed_at": "2026-11-13T09:30:00",
                                                                         "passed_by": "person", "todos": [], "tasks": [merged], "accepts": {"1": {"verdict": "accepted"}}})
    _red(state)
    for entry in ENTRIES:
        if hasattr(h.ideas.keeper, entry):
            monkeypatch.setattr(h.ideas.keeper, entry, _boom)
    monkeypatch.setattr(harnesses.Harness, "call", _boom)
    monkeypatch.setattr(jobs, "run_work", _boom)
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


@pytest.fixture
def launched(host, monkeypatch):
    """The host's runner, its launch faked: a task that would start is only noted, as running."""
    runner = host.ideas.runner(True)
    from orkboard.core.idea_runner import Run
    got: list[tuple[str, str]] = []

    def launch(slug, task):
        task.update(state="running")
        runner._runs[(slug, task["id"])] = Run(threading.current_thread(), threading.Event())
        got.append((slug, task["id"]))
    monkeypatch.setattr(runner, "_launch", launch)
    monkeypatch.setattr(runner, "signed_out", lambda tool: False)
    return got


def _bytes(host):
    return {p.as_posix(): hashlib.sha1(p.read_bytes()).hexdigest() for base in (Path(host.repo_root), host.ideas.state_dir)
            for p in sorted(base.rglob("*")) if p.is_file() and "/.git/" not in p.as_posix()}


def test_its_stage_runs_again_on_the_seal_one_task_of_the_failing_tests(host, launched):
    state = host.ideas.state_dir
    said = host.command("ideas.gate_guards", {"idea": "goal"})["cost"]
    got = host.command("ideas.gate_fix_stage", {"idea": "goal", "sealed": True, "from": "mat"})
    assert got["ok"] and got["ids"] == IDS and got["cost"] == said == idea_fix_stage.COST == {"calls": None, "usd_high": None}     # said before: not known yet, no cap
    tasks = ideas.plan(state, "goal")["tasks"]
    assert [t["id"] for t in tasks] == ["k1", got["task"]] and tasks[0]["state"] == "merged"
    added = tasks[1]
    assert added["title"] == "Make the failing tests pass: tests/test_red.py::test_a, tests/test_bare.py::test_c"
    assert added["step"] == 1 and added["party"] == "tech" and all(i in added["brief"] for i in IDS)              # of the plan's last step, stamped as its tasks are
    assert ideas.state(state, "goal")["state"] == "working" and launched == [("goal", got["task"])]               # the goal at work; the faked launch took its one task
    kept = goal_branch.read(state, "goal")
    assert goal_branch.in_use(state, "goal") == "goal/goal" and not kept["blocked"] and kept["failing"] == [] and kept["ready"] is False
    played = [r for r in event_log.read(host.repo_root) if r["event"] == "move_played"]
    assert [(r["idea"], r["kind"], r["from"]) for r in played] == [("goal", "fix_stage", "mat")]       # B: played() reads the goal from `idea`
    assert idea_undo.read(state, "goal") is None                                                                 # sealed: it keeps no Undo


def test_unsealed_it_is_refused_and_nothing_is_written(host, launched):
    before = _bytes(host)
    for origin in ("hand", "mat"):
        with pytest.raises(CommandError, match="Run its stage again cannot be undone: it goes only on its seal"):
            host.command("ideas.gate_fix_stage", {"idea": "goal", "from": origin})
    assert _bytes(host) == before and launched == []
    assert not [r for r in event_log.read(host.repo_root) if r["event"] == "move_played"]


def test_on_a_goal_done_in_dev_it_is_refused_in_words_and_nothing_is_written(host, monkeypatch):
    goal_branch.update(host.ideas.state_dir, "goal", merged="abc1234", blocked="", blocked_kind="", failing=[], files=[])
    monkeypatch.setattr(type(host.ideas), "runner", lambda self, need=False: _boom())
    before = _bytes(host)
    with pytest.raises(CommandError, match="That goal is in dev already: Fix it lays a new Fix goal"):
        host.command("ideas.gate_fix_stage", {"idea": "goal", "sealed": True, "from": "mat"})
    assert _bytes(host) == before


def test_a_way_to_dev_that_is_not_red_is_refused_and_nothing_is_written(host, launched):
    goal_branch.update(host.ideas.state_dir, "goal", blocked="dev conflicts with goal/goal in a.py", blocked_kind="conflict", failing=[], files=[])
    before = _bytes(host)
    with pytest.raises(CommandError, match="No test failed on its way to dev: nothing to fix"):
        host.command("ideas.gate_fix_stage", {"idea": "goal", "sealed": True, "from": "hand"})
    assert _bytes(host) == before and launched == []


def test_the_runner_adds_it_once_and_refuses_while_a_task_of_the_goal_runs(fake_repo):
    """The runner's own half, with no host: `fix_stage` adds the task under the next free id and starts the goal; a second press while its task runs is refused."""
    from orkboard.core.idea_runner import IdeaRunner, Run, RunnerError
    state = fake_repo / ".orkcraft"
    ideas.save_state(state, "goal", state="done")
    ideas._write_json(ideas.state_folder(state, "goal") / "plan.json", {"idea": "goal", "passed_at": "2026-11-13T09:30:00", "todos": [],
                                                                         "tasks": [{**_task("k1", "Build", "b", "code", "warrior", []), "state": "merged", "commit": "abc"}]})
    _red(state)
    runner = IdeaRunner(fake_repo, state, {"ideas": {"max_parallel": 4}}, None, limits=lambda: [], events=False)
    runner._launch = lambda slug, task: (task.update(state="running"), runner._runs.__setitem__((slug, task["id"]), Run(threading.current_thread(), threading.Event())))
    runner.signed_out = lambda tool: False
    assert runner.fix_stage("goal") == {"task": "k2", "ids": IDS}
    assert [t["state"] for t in ideas.plan(state, "goal")["tasks"]] == ["merged", "running"]
    _red(state)
    with pytest.raises(RunnerError, match="still has a task running"):
        runner.fix_stage("goal")
    assert [t["id"] for t in ideas.plan(state, "goal")["tasks"]] == ["k1", "k2"]
    sys.modules.pop("orkboard.core.idea_runner", None)
