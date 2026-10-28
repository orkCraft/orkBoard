"""Spec 99 H (docs/specs/99-a-goals-way.md §9, §11): a goal's work goes by steps. After the join the first step's party plans its own step; its tasks run on its party's seats;
when they are merged in dev the next step's party plans its step and its tasks join the plan; the goal is done when the last step's tasks are in dev. Through the host, the
keeper's call stubbed (as test_idea_sections.py's) and the runner's sessions not spawned (a task's state is set as its session would)."""
from __future__ import annotations

import json
import time
from threading import Event

import pytest

from orkboard.realm import goal_team, idea_route, ideas, roles
from tests.test_idea_sections import _confirmed, _page, _state, host, model, parties, section  # noqa: F401  (the fixtures of the sections' tests)


def _plan_by_step(row):
    """The plan the stub answers: the step the prompt says it is for (the first's on step 1, the second's after it)."""
    text = " ".join(row["prompt"].split())
    if "step 2 of 2" in text:
        return {"tasks": [{"id": "a", "title": "Build the setting", "brief": "Build it", "kind": "code", "tier": "warrior"},
                          {"id": "b", "title": "Test the setting", "brief": "Test it", "kind": "tests", "after": ["a"]}]}
    return {"tasks": [{"id": "a", "title": "Make the settings screen", "brief": "Make it", "kind": "design"}]}


@pytest.fixture
def work(host, parties, model):                                                 # noqa: F811
    """A two-step goal (Product, then Tech) planned and started, its runner spawning nothing: `work.merge(*ids)` as a session that landed."""
    model.said[("plan", "")] = _plan_by_step
    goal_team.set_tool(host.ideas.root(), parties["tech"], "agy")                # Tech's seats run on another AI tool than Product's
    slug = _confirmed(host, parties, model, ("product", "tech"))
    runner = host.ideas.runner(need=True)
    spawned = []

    def spawn(slug_, tid, cancel, again):
        spawned.append((slug_, tid))
        runner._runs[(slug_, tid)] = type("Run", (), {"thread": None, "cancel": Event(), "why": "", "role": ""})()

    runner._spawn = spawn

    class Work:
        pass
    w = Work()
    w.host, w.slug, w.parties, w.model, w.runner, w.spawned = host, slug, parties, model, runner, spawned
    w.merge = lambda *ids: [(runner._runs.pop((slug, i), None), runner._set_task(slug, i, state="merged", commit="c" * 40, subjects=[f"{i} landed"], finished="x")) for i in ids]
    w.tasks = lambda: {t["id"]: t for t in ideas.plan(host.ideas.state_dir, slug)["tasks"]}
    w.until = lambda: [time.sleep(0.01) for _ in range(1000) if host.ideas.keeper.busy(slug)]
    return w


def test_a_two_step_goal_goes_step_by_step_and_is_done_when_the_last_steps_tasks_are_merged(work):
    h, slug, p = work.host, work.slug, work.parties
    state = lambda: ideas.state(h.ideas.state_dir, slug)["state"]                    # noqa: E731
    assert state() == "plan" and ideas.idea_page(h.ideas.root(), slug).get("track") == p["product"]
    assert list(work.tasks()) == ["k1"] and work.tasks()["k1"]["party"] == p["product"]
    h.command("ideas.start", {"slug": slug})
    assert state() == "working" and work.spawned == [(slug, "k1")] and work.tasks()["k1"]["tool"] != "agy"            # Product's seats
    work.runner.tick()
    assert state() == "working" and list(work.tasks()) == ["k1"]                                                         # the step is not merged yet
    work.merge("k1")
    work.runner.tick()
    assert state() == "working" and slug in work.runner._active                                                          # not done: Tech's step follows
    assert h.ideas.keeper.tick(time.time() + 100) is True                                                                 # the clock has Tech plan its step
    work.until()
    assert ideas.idea_page(h.ideas.root(), slug).get("track") == p["tech"] and state() == "working"
    assert [(i, t["step"], t["party"]) for i, t in work.tasks().items()] == [("k1", 1, p["product"]), ("k2", 2, p["tech"]), ("k3", 2, p["tech"])]
    work.runner.tick()
    assert work.spawned[-1] == (slug, "k2") and work.tasks()["k2"]["tool"] == "agy"                                       # its tasks run on Tech's seats: Tech's tool
    assert work.tasks()["k3"]["state"] == "waiting"                                                                      # after k2
    work.merge("k2")
    work.runner.tick()
    assert work.spawned[-1] == (slug, "k3") and state() == "working"
    work.merge("k3")
    work.runner.tick()
    assert state() == "done" and slug not in work.runner._active                                                         # the last step's tasks are in dev
    assert h.ideas.keeper.tick(time.time() + 200) is False


def test_each_step_is_recorded_as_history_and_the_route_reads_where_the_goal_is(work):
    h, slug, p = work.host, work.slug, work.parties
    legs = lambda: [(s["n"], s["party"], s["state"], s["done"], s["total"]) for s in idea_route.route(h.ideas.root(), h.ideas.state_dir, slug) if s["step"] == "party"]      # noqa: E731
    assert legs() == [(1, p["product"], "plan", 0, 1), (2, p["tech"], "waiting", 0, 0)]
    h.command("ideas.start", {"slug": slug})
    work.merge("k1")
    work.runner.tick()
    assert legs() == [(1, p["product"], "done", 1, 1), (2, p["tech"], "working", 0, 0)]                                  # the next step's turn, not planned yet
    h.ideas.keeper.tick(time.time() + 100)
    work.until()
    assert legs() == [(1, p["product"], "done", 1, 1), (2, p["tech"], "working", 0, 2)]
    assert [(s["n"], s["party"], s["tasks"]) for s in idea_route.recorded(h.ideas.state_dir, slug)] == [(1, p["product"], ["k1"]), (2, p["tech"], ["k2", "k3"])]
    node = next(n for n in h.command("ideas.map", {})["nodes"] if n["slug"] == slug)
    assert [s["n"] for s in node["route"]] == [1, 2] and json.dumps(node["route"])
    work.merge("k2", "k3")
    work.runner.tick()
    assert legs() == [(1, p["product"], "done", 1, 1), (2, p["tech"], "done", 2, 2)]


def test_a_tasks_head_is_its_steps_partys_race_in_the_board_and_in_review(work):
    h, slug, p = work.host, work.slug, work.parties
    h.command("ideas.start", {"slug": slug})
    work.merge("k1")
    work.runner.tick()
    h.ideas.keeper.tick(time.time() + 100)
    work.until()
    page = h.command("ideas.page", {"slug": slug})
    heads = {t["id"]: t["head"] for t in page["plan"]["tasks"]}
    assert heads["k1"]["race"] in ("knight", "unicorn") and heads["k2"]["race"] in ("peon", "shaman") and heads["k3"]["race"] in ("peon", "shaman")
    assert roles.task_head(h.ideas.state_dir, work.tasks()["k2"], "balance")["race"] in ("peon", "shaman")


def test_a_goal_that_cannot_plan_its_next_step_is_taken_off_the_runner_and_start_goes_on_from_there(work):
    h, slug, p = work.host, work.slug, work.parties
    h.command("ideas.start", {"slug": slug})
    work.merge("k1")
    work.model.said[("plan", "")] = "no plan at all"
    work.runner.tick()
    h.ideas.keeper.tick(time.time() + 100)
    work.until()
    st = ideas.state(h.ideas.state_dir, slug)
    assert st["state"] == "failed" and st["error"].startswith("No plan for the next step:") and list(work.tasks()) == ["k1"]
    work.runner.tick()
    assert slug not in work.runner._active                                                                               # it waits for the person, not for the clock
    work.model.said[("plan", "")] = _plan_by_step
    h.command("ideas.start", {"slug": slug})                                                                              # Start: the runner has it again; the clock plans the step
    work.runner.tick()
    assert ideas.state(h.ideas.state_dir, slug)["state"] == "working" and slug in work.runner._active
    h.ideas.keeper.tick(time.time() + 300)
    work.until()
    assert list(work.tasks()) == ["k1", "k2", "k3"]


def test_a_goal_of_one_step_is_done_when_its_tasks_are_merged_as_today(host, parties, model):                       # noqa: F811
    model.said[("plan", "")] = _plan_by_step
    slug = _confirmed(host, parties, model, ("tech",))
    runner = host.ideas.runner(need=True)
    runner._spawn = lambda *a: None
    plan = ideas.plan(host.ideas.state_dir, slug)
    assert "route" not in plan and idea_route.legs_of(plan) == [] and not idea_route.steps_left(plan)
    host.command("ideas.start", {"slug": slug})
    for t in ideas.plan(host.ideas.state_dir, slug)["tasks"]:
        runner._runs.pop((slug, t["id"]), None)
        runner._set_task(slug, t["id"], state="merged", commit="c" * 40, subjects=["landed"], finished="x")
    runner.tick()
    assert ideas.state(host.ideas.state_dir, slug)["state"] == "done"
    assert [s["step"] for s in idea_route.steps(host.ideas.root(), host.ideas.state_dir, slug)] == ["party"]
    assert "n" not in idea_route.steps(host.ideas.root(), host.ideas.state_dir, slug)[0]
