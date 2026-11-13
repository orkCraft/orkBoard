"""Spec 139 part B (docs/specs/139-the-die-the-door-and-the-bug.md B, decisions §246.3): Stopped and Resume. `halt_all` keeps what it stopped; `halt` marks the project stopped (kept in its state dir: a restart keeps it);
while it holds nothing starts by itself (the clock's passes); `resume` starts again each task the halt killed from its start; a goal the person starts by hand clears it and says *The orks are back at work*."""
from __future__ import annotations

import json
import subprocess
import sys
import threading
import time

import pytest

from orkboard.gui.board_host import BoardPhone, Orkboard
from orkboard.realm import halt, ideas


@pytest.fixture
def host(fake_repo) -> Orkboard:
    halt.reset()
    h = Orkboard(fake_repo)
    yield h
    halt.reset()
    sys.modules.pop("orkboard.core.idea_runner", None)


def _toasts(host) -> list[str]:
    seen: list[str] = []
    host.bus.subscribe("toast", lambda e: seen.append(e.data.get("message", "")))
    return seen


def _party(host) -> str:
    slug, _new = ideas.save_goal(host.ideas.root(), None, "Tech", "About tech", None, "normal", craft="engineering")
    return slug


def _plan(host, slug="demo", state="running", error=""):
    d = host.ideas.state_dir / "ideas" / slug
    d.mkdir(parents=True, exist_ok=True)
    task = {"id": "k1", "title": "k1", "brief": "do it", "tier": "laborer", "kind": "code", "after": [], "state": state, "branch": "idea/demo/k1",
            "commit": "", "session": "", "cost": None, "tokens": None, "started": "x", "finished": "", "error": error, "note": ""}
    (d / "plan.json").write_text(json.dumps({"idea": slug, "made_at": "x", "passed_at": "y", "todos": [], "tasks": [task]}))
    (d / "state.json").write_text(json.dumps({"state": "working"}))


def _task(host, slug="demo"):
    return json.loads((host.ideas.state_dir / "ideas" / slug / "plan.json").read_text())["tasks"][0]


def _running(host):
    """A runner with one task at work (a thread that is not started), as the runner has it while a task runs."""
    runner = host.ideas.runner(need=True)
    _plan(host)
    run = sys.modules[type(runner).__module__].Run(threading.Thread(), threading.Event())
    runner._runs[("demo", "k1")] = run
    runner._active.append("demo")
    started = []
    runner.tick = lambda: started.append(_task(host)["state"])           # the tick that follows a resume: the task waits for its turn, nothing launches
    return runner, started


def test_halt_all_keeps_who_it_killed_and_what_to_start_again_and_resume_clears_it():
    halt.reset()
    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"], start_new_session=True)
    halt.started(proc, "tech/grunt")
    assert halt.stopped() == [] and not halt.halted()
    assert halt.halt_all(again=[("demo", "k1")]) == 1
    proc.wait(timeout=10)
    assert {"who": "tech/grunt", "again": None} in halt.stopped() and {"who": "", "again": ("demo", "k1")} in halt.stopped() and halt.halted()
    assert halt.halt_all() == 0 and len(halt.stopped()) == 2, "a second halt adds nothing it has"
    got = halt.resume()
    assert len(got) == 2 and halt.stopped() == [] and not halt.halted()
    with pytest.raises(halt.Halted):                                                              # the API as it was: the killed process's caller gets Halted
        halt.ended(proc)
    halt.reset()


def test_halt_marks_the_project_stopped_the_snapshot_says_it_and_a_restart_keeps_it(host, fake_repo):
    assert host.snapshot()["stopped"] is False
    host.command("halt")
    assert host.snapshot()["stopped"] is True and host.phone_snapshot()["stopped"] is True
    assert (fake_repo / ".orkcraft" / "stopped.json").exists()
    again = Orkboard(fake_repo)                                                                   # a restart: the same project's state dir
    assert again.snapshot()["stopped"] is True and again.ideas.stopped()
    again.command("resume")
    assert again.snapshot()["stopped"] is False and not (fake_repo / ".orkcraft" / "stopped.json").exists()
    assert "resume" in BoardPhone.COMMANDS


def test_the_clocks_passes_start_nothing_while_stopped(host, monkeypatch):
    ideas_ = host.ideas
    seen = []
    monkeypatch.setattr(ideas_.keeper, "tick", lambda *a, **k: seen.append("keeper"))
    monkeypatch.setattr(ideas_, "routines_tick", lambda now: seen.append("routines"))
    monkeypatch.setattr(ideas_, "route_call", lambda *a: seen.append("route_call"))
    monkeypatch.setattr(ideas_, "route_talk", lambda a: seen.append("talk"))
    added = host.command("ideas.add", {"text": "a goal", "track": _party(host), "hold": True})["slug"]
    ideas.save_state(ideas_.state_dir, added, state="routed", route=[], held_until="")                  # a goal that waits for its route's call
    host.command("halt")
    now = time.monotonic() + 1000
    ideas_.tick(now)
    ideas_.route_tick(now + 100)
    assert seen == [] and ideas_.route_auto(added) is False
    ideas_.ripe_tick(now)
    ideas_.ripe_tick(now + 100)
    assert ideas_.state_of(added) == "routed"
    host.command("resume")
    ideas_.route_tick(now + 200)
    assert "route_call" in seen, "the clock goes on after Resume"


def test_the_runner_is_not_ticked_while_stopped_and_resume_starts_the_killed_task_from_its_start(host):
    runner, started = _running(host)
    host.command("halt")
    assert _task(host)["state"] == "failed" and _task(host)["error"] == "stopped by Stop all"
    assert host.ideas.stopped() and json.loads((host.ideas.state_dir / "stopped.json").read_text())["again"] == [["demo", "k1"]]
    runner._runs.clear()
    host.ideas._runner_at = float("-inf")
    host.ideas.tick(time.monotonic() + 1000)
    assert started == [], "a plan's next task does not start by itself"
    toasts = _toasts(host)
    assert host.command("resume") == 1
    assert started == ["waiting"], "the task starts anew: waiting, then the tick takes it as it takes any task"
    assert _task(host)["error"] == "" and json.loads((host.ideas.state_dir / "ideas" / "demo" / "state.json").read_text())["state"] == "working"
    assert "demo" in runner._active and not host.ideas.stopped() and "The orks are back at work" in toasts




@pytest.mark.parametrize("name,args", [("ideas.add", {"text": "a goal by hand"}), ("ideas.talk", {"idea": "nothing"}), ("ideas.start", {"slug": "nothing"}),
                                       ("ideas.confirm", {"slug": "nothing"}), ("ideas.start_now", {"slug": "nothing"})])
def test_a_goal_started_by_hand_clears_stopped_and_says_the_orks_are_back(host, name, args):
    toasts = _toasts(host)
    host.command("halt")
    assert host.ideas.stopped()
    if name == "ideas.add":
        args = {**args, "track": _party(host)}
    try:
        host.command(name, args)
    except Exception:                                                                              # the command itself may refuse a goal that is not there: stopped was cleared first
        pass
    assert not host.ideas.stopped() and host.snapshot()["stopped"] is False
    assert toasts.count("The orks are back at work") == 1


