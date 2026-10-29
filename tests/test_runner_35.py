"""Spec 35 §1, §5, §6, §9, §12, §13 on the runner: the Target's tier and effort with the tool and model recorded, the
night gate and Start now, the reserve for what started by itself (never the person's press), High first, a file
to-do's path in the environment only, and the gate refusing a result that edits the Board's pages."""
from __future__ import annotations

import datetime as dt
import json
import threading
import time
from types import SimpleNamespace

import pytest

from orkboard.core.idea_runner import IdeaRunner
from orkboard.realm import event_log, idea_secrets, idea_target
from orkboard.sources.limits import Limit

from tests.test_idea_runner import git, plan_of, town  # noqa: F401  (the fixture repository with a stub claude)


def _runner(town, limits=None, night="01:00-07:00", **more):
    settings = SimpleNamespace(ideas={"max_parallel": 1, "merge_into": "main", "push": False, "review": True,
                                      "night": night, "reserve_day": 0.3, "reserve_night": 0.1, **more})
    r = IdeaRunner(town.repo, town.state, settings, None, limits=limits or (lambda: []), events=True)
    launched = []
    r._spawn = lambda slug, tid, cancel, again: launched.append((slug, tid))    # no session: only who starts
    return r, launched


def _pass(town, slug="demo", **plan):
    path = town.state / "ideas" / slug / "plan.json"
    data = json.loads(path.read_text())
    data.update(plan)
    path.write_text(json.dumps(data))


def _now_in(night: bool) -> str:
    """A night window that holds now, or one that does not."""
    h = dt.datetime.now().hour
    return f"{h:02d}:00-{(h + 1) % 24:02d}:00" if night else f"{(h + 2) % 24:02d}:00-{(h + 3) % 24:02d}:00"


def test_a_task_runs_on_the_targets_tier_with_its_tool_and_model_recorded(town):
    plan_of(town, [{"id": "k1", "tier": "warrior"}])
    r, launched = _runner(town, target="thrift")
    r.start("demo")
    (task,) = r.plan("demo")["tasks"]
    assert launched == [("demo", "k1")] and task["ran_tier"] == "laborer" and task["effort"] == "low"
    assert task["tool"] == "claude" and "haiku" in task["model"] and task["tier"] == "warrior"
    (e,) = [x for x in event_log.read(town.repo) if x["event"] == "task_state" and x["state"] == "running"]
    assert (e["ran_tier"], e["effort"], e["tool"]) == ("laborer", "low", "claude") and "haiku" in e["model"]
    assert e["ran_why"] == "target thrift"                                      # spec 107 §2.3: it ran lighter than planned, and says why


def test_a_task_on_its_own_tier_says_no_reason_and_a_failed_one_its_error_spec_107(town):
    plan_of(town, [{"id": "k1", "tier": "warrior"}])
    r, _ = _runner(town)
    r.start("demo")
    r._set_task("demo", "k1", state="failed", error="sh: vitest: command not found " + "x" * 900)
    running, failed = [x for x in event_log.read(town.repo) if x["event"] == "task_state" and x["state"] in ("running", "failed")]
    assert running["ran_why"] == "" and "error" not in running
    assert failed["error"].startswith("sh: vitest: command not found") and len(failed["error"]) == 600
    assert idea_target.ran_why("elder", "warrior", "balance", "standard") == "target balance (standard party)"
    assert idea_target.ran_why("elder", "warrior", "balance", "", "sonnet") == "role model sonnet"
    assert idea_target.ran_why("", "warrior", "balance") == ""


def test_a_plan_of_before_the_night_went_waits_for_the_reserve_as_one_the_board_passed_and_never_for_a_window(town):
    reset = dt.datetime.now() + dt.timedelta(hours=2)
    limits = lambda: [Limit("claude", "", "session", 0.2, reset)]               # noqa: E731  above NEARLY, below the day's 0.3
    plan_of(town, [{"id": "k1"}])
    _pass(town, start_at="night", passed_by="person")
    r, launched = _runner(town, night=_now_in(False))
    r.start("demo")
    assert launched == [("demo", "k1")]                                         # outside the window it starts: there is no night to wait for
    plan_of(town, [{"id": "k1"}])
    _pass(town, start_at="night", passed_by="person")
    r, launched = _runner(town, limits=limits, night=_now_in(False))
    r.start("demo")
    (task,) = r.plan("demo")["tasks"]
    assert launched == [] and task["state"] == "held" and task["note"] == f"reserve · after {reset:%H:%M}"      # held for the reserve, as a plan passed by itself
    assert idea_target.gate({"start_at": "night"}, [], {}, time.time()) is None and idea_target.gate({"start_at": None}, limits(), {}, time.time()) is None


def test_the_reserve_holds_what_started_by_itself_and_never_the_persons_press(town):
    reset = dt.datetime.now() + dt.timedelta(hours=2)
    limits = lambda: [Limit("claude", "", "session", 0.2, reset)]               # noqa: E731  above NEARLY, below 0.3
    plan_of(town, [{"id": "k1"}])
    _pass(town, passed_by="auto")
    r, launched = _runner(town, limits=limits, night=_now_in(False))
    r.start("demo")
    (task,) = r.plan("demo")["tasks"]
    assert launched == [] and task["state"] == "held" and task["note"] == f"reserve · after {reset:%H:%M}"
    plan_of(town, [{"id": "k1"}])
    _pass(town, passed_by="person")
    r, launched = _runner(town, limits=limits, night=_now_in(False))
    r.start("demo")
    assert launched == [("demo", "k1")]
    plan_of(town, [{"id": "k1"}])
    _pass(town, passed_by="auto")
    r, launched = _runner(town, limits=limits, night=_now_in(True))            # at night the reserve is 0.10
    r.start("demo")
    assert launched == [("demo", "k1")]


def test_the_reserve_is_read_on_the_tool_the_task_runs_on_not_on_claudes(town):
    """The owner's 26 October: a Game party's task (Antigravity, 99 % left) was held by Claude's low week."""
    reset = dt.datetime.now() + dt.timedelta(hours=2)
    limits = lambda: [Limit("claude", "", "weekly", 0.14, reset), Limit("agy", "", "weekly", 0.99, reset)]      # noqa: E731
    for tool, held in (("agy", False), ("claude", True)):
        plan_of(town, [{"id": "k1"}])
        _pass(town, passed_by="auto")
        r, launched = _runner(town, limits=limits, night=_now_in(False))
        r.party_of = lambda slug, tool=tool: {"tool": tool}
        r.start("demo")
        (task,) = r.plan("demo")["tasks"]
        assert (task["state"] == "held") is held, (tool, task)
        assert (launched == []) is held
        if held:
            assert task["note"] == f"reserve · after {reset:%H:%M}"
    plan_of(town, [{"id": "k1"}])                                              # a tool with no limits read has no reserve
    _pass(town, passed_by="auto")
    r, launched = _runner(town, limits=lambda: [Limit("claude", "", "weekly", 0.05, reset)], night=_now_in(False))
    r.party_of = lambda slug: {"tool": "agy"}
    r.start("demo")
    assert launched == [("demo", "k1")]


def test_high_goes_before_normal(town):
    for slug in ("normal-one", "high-one"):
        plan_of(town, [{"id": "k1"}], slug=slug)
        _pass(town, slug, passed_by="person")
    r, launched = _runner(town)
    r.rank = lambda slug: (0 if slug.startswith("high") else 1,)
    r._active = ["normal-one", "high-one"]
    for slug in r._active:
        (town.state / "ideas" / slug / "state.json").write_text(json.dumps({"state": "working"}))
    r.tick()
    assert launched == [("high-one", "k1")]                                     # one slot: High takes it


def test_a_file_todos_path_is_in_the_tasks_environment_and_only_named_in_its_prompt(town):
    plan_of(town, [{"id": "k1"}], todos=[{"id": "t2", "title": "the config", "kind": "file", "for": ["k1"], "done": True,
                                          "value": "conf.json"}])
    path = idea_secrets.put_file(town.state, "demo", "t2", "conf.json", b'{"k": "file-secret"}')
    r, _ = _runner(town)
    plan = r.plan("demo")
    env = r._env("demo", "k1", plan)
    assert env["ORKCRAFT_FILE_T2"] == str(path) and str(town.repo / ".orkcraft") in str(path)
    prompt = r._prompt("demo", plan, plan["tasks"][0])
    assert "The file is at $ORKCRAFT_FILE_T2" in prompt and str(path) not in prompt and "file-secret" not in prompt
    assert "file-secret" not in (town.state / "ideas" / "demo" / "plan.json").read_text()
    assert not git(town.repo, "status", "--porcelain", "--ignored", "--", "llm-wiki").count("conf.json")


def test_the_gate_refuses_a_result_that_edits_the_boards_pages(town):
    plan_of(town, [{"id": "k1"}])
    r, _ = _runner(town)
    path, _branch = r.git.prepare("demo", "k1", "main")
    start = r.git.head(path)
    page = path / "llm-wiki" / "general" / "pages" / "ideas" / "other.md"
    page.parent.mkdir(parents=True)
    page.write_text("---\nowner: board\n---\n# Other\n")
    git(path, "add", "-A")
    git(path, "-c", "user.name=T", "-c", "user.email=t@x", "commit", "-qm", "edit a page")
    problem, out = r._check(path, start, threading.Event(), "t")
    assert "never edits the Board's pages" in problem and "pages/ideas/other.md" in problem and out == ""
    r.git.remove(path)


def test_a_held_task_says_whose_limit_how_much_is_left_and_until_when_and_start_now_lets_it_go(town):
    """The owner, 26 October: *Waits for Claude's limit: 14 % of the week left, kept for you until 12:00*; the person's press releases it."""
    reset = dt.datetime.now() + dt.timedelta(hours=2)
    limits = lambda: [Limit("claude", "", "weekly", 0.14, reset), Limit("claude", "", "session", 0.9, reset)]      # noqa: E731
    plan_of(town, [{"id": "k1"}, {"id": "k2", "after": ["k1"]}])
    _pass(town, passed_by="auto")
    r, launched = _runner(town, limits=limits, night=_now_in(False))
    r.start("demo")
    task = r.plan("demo")["tasks"][0]
    until = f"{reset:%H:%M}" if reset.date() == dt.datetime.now().date() else f"{reset:%a %H:%M}"     # past midnight the day is said too
    assert task["held_why"] == f"Waits for Claude Code's limit: 14 % of the week left, kept for you until {until}", task
    assert idea_target.hold_line([Limit("agy", "", "session", 0.2, reset)], "agy", "reserve", reset.timestamp(), time.time()) \
        == f"Waits for Antigravity's limit: 20 % of the five hours left, kept for you until {until}"
    assert idea_target.hold_line([], "agy", "reserve", reset.timestamp(), time.time()) == f"Waits for Antigravity's limit: kept for you until {until}"
    _pass(town, passed_by="person")                                         # the person's press: no reserve for it
    assert r.release_holds("demo") == 1
    assert r.plan("demo")["tasks"][0]["state"] == "waiting" and r.plan("demo")["tasks"][0]["held_why"] == ""
    r.tick()
    assert launched == [("demo", "k1")]


# -- spec 99 §9: the work by steps -------------------------------------------------------------------------------------------------------

def _by_steps(town, tasks, route=("design", "tech"), slug="demo", **plan):
    """A passed plan whose tasks are `[(id, step, state)]`, made for `route` (a goal of two steps or more keeps it in its plan)."""
    plan_of(town, [{"id": i} for i, _s, _st in tasks], slug=slug)
    path = town.state / "ideas" / slug / "plan.json"
    data = json.loads(path.read_text())
    for t, (_i, step, state) in zip(data["tasks"], tasks):
        t.update(step=step, state=state, party=route[step - 1] if step <= len(route) else "")
    data.update(passed_by="person", **({"route": [{"party": p, "leader": ""} for p in route]} if len(route) > 1 else {}), **plan)
    path.write_text(json.dumps(data))
    (town.state / "ideas" / slug / "state.json").write_text(json.dumps({"state": "working", "route": [{"party": p, "leader": ""} for p in route]}))


def _state(town, slug="demo"):
    return json.loads((town.state / "ideas" / slug / "state.json").read_text())["state"]


def test_a_goal_is_not_done_when_a_step_is_merged_and_its_route_has_another_it_waits_for_that_steps_plan(town):
    _by_steps(town, [("k1", 1, "merged")])
    r, launched = _runner(town)
    r.start("demo")
    assert _state(town) == "working" and r._active == ["demo"] and launched == []
    r.tick()
    assert _state(town) == "working" and r._active == ["demo"]                                  # the keeper's clock plans the next step; the runner waits
    path = town.state / "ideas" / "demo" / "plan.json"
    data = json.loads(path.read_text())
    data["tasks"].append({**data["tasks"][0], "id": "k2", "step": 2, "state": "waiting", "after": []})      # the next step's party planned: its task joined the plan
    path.write_text(json.dumps(data))
    r.tick()
    assert launched == [("demo", "k2")] and _state(town) == "working"
    r._set_task("demo", "k2", state="merged")
    r.tick()
    assert _state(town) == "done" and r._active == []                                           # the last step's tasks are in dev


def test_a_goal_whose_last_step_is_merged_or_whose_task_failed_or_whose_step_landed_nothing_ends_as_it_always_did(town):
    _by_steps(town, [("k1", 1, "merged"), ("k2", 2, "merged")])
    r, _ = _runner(town)
    r.start("demo")
    assert _state(town) == "done"
    _by_steps(town, [("k1", 1, "merged"), ("k2", 1, "waiting")])                                # a failed task: the goal fails, no step follows
    r, _ = _runner(town)
    r.start("demo")
    r._set_task("demo", "k2", state="failed", error="it failed")
    r._runs.clear()
    r.tick()
    assert _state(town) == "failed" and r._active == []
    _by_steps(town, [("k1", 1, "dropped")])                                                     # everything dropped: nothing landed, nothing follows (the goal waits as before)
    r, _ = _runner(town)
    r.start("demo")
    assert _state(town) == "plan" and r._active == []
    _by_steps(town, [("k1", 1, "merged")], route=("design",))                                   # a route of one step: done when its tasks are merged
    r, _ = _runner(town)
    r.start("demo")
    assert _state(town) == "done"


def test_a_goal_the_keeper_could_not_plan_the_next_step_of_leaves_the_runner_until_start(town):
    _by_steps(town, [("k1", 1, "merged")])
    r, launched = _runner(town)
    r.start("demo")
    assert r._active == ["demo"]
    (town.state / "ideas" / "demo" / "state.json").write_text(json.dumps({"state": "failed", "error": "No plan for the next step: x", "route": [{"party": "design"}, {"party": "tech"}]}))
    r.tick()
    assert r._active == [] and _state(town) == "failed"
    r.start("demo")                                                                             # Start: the goal is the runner's again, waiting for the step's plan
    assert r._active == ["demo"] and _state(town) == "working"


def test_a_task_names_what_it_reads_of_its_spec_never_the_whole_page(town):
    page = town.repo / "pages" / "ideas" / "demo.md"
    page.parent.mkdir(parents=True)
    page.write_text("---\nowner: board\n---\n# Dark mode\n\n## Asked\nadd a dark mode\n\n## Gist\nDark mode\n\n## Route\n1. Design\n2. Tech\n\n"
                    "## Design\n### Why\nBecause.\n\n### Done when\n- A screen\n\n### Will be\nchanged ui/settings\n\n## Tech\n### Why\nTech's why.\n\n### Done when\n- A file\n")
    plan_of(town, [{"id": "k1"}, {"id": "k2"}])
    path = town.state / "ideas" / "demo" / "plan.json"
    data = json.loads(path.read_text())
    data["tasks"][0]["section"] = "Tech"
    path.write_text(json.dumps(data))
    r, _ = _runner(town)
    plan = r.plan("demo")
    prompt = r._prompt("demo", plan, plan["tasks"][0])
    assert "`pages/ideas/demo.md` in this worktree: read the common part (`## Asked`, `## Gist`, `## Route`)" in prompt
    assert "your party's section `## Tech` whole, and of the other sections (`## Design`) only their `### Done when` and `### Will be`" in prompt
    assert "Read nothing else of it" in prompt and "Tech's why." not in prompt and "Because." not in prompt          # named, never pasted
    older = r._prompt("demo", plan, plan["tasks"][1])                                           # a task of a page of before (no section): as it was
    assert "in this worktree: read it if you need it." in older and "your party's section" not in older
