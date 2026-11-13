"""Spec 35 on the host, the model call stubbed (`jobs.run_read`): a goal from a description, an idea that needs a goal,
the queue, autostart and Start now, Needs you as one list, proposals, a file to-do, the Board's commands and events."""
from __future__ import annotations

import base64
import json
import sys
import time
import types
from pathlib import Path

import pytest

from orkboard.gui.board_host import BoardPhone, CommandError, Orkboard
from orkboard.realm import event_log, idea_secrets, ideas, jobs

NEW = {"ideas.answer", "ideas.queue", "ideas.read_stop", "ideas.start_now", "ideas.proposal", "ideas.board_set"}


@pytest.fixture
def host(fake_repo) -> Orkboard:
    (fake_repo / "src" / "board.py").write_text("x = 1\n")
    h = Orkboard(fake_repo)
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


@pytest.fixture
def model(monkeypatch):
    """The keeper's calls: answered by step; every call's arguments kept."""
    seen, answers = [], {
        "goal": {"title": "Runs at a glance", "summary": "The table lives in src/app.py.\nIt reads runs.",
                 "metrics": [{"name": "done when the table shows", "target": "1 table", "how": "a browser test"},
                             {"name": "done when it sorts", "target": "3 keys", "how": "a unit test"}],
                 "links": ["src/app.py", "src/nope.py", "https://example.com", "../outside.md"], "questions": []},
        "draft": {"title": "The table", "gist": "A table.", "why": "w", "done_when": ["it shows"], "risk": "low",
                  "touches": ["src/app.py"], "questions": []},
        "plan": {"tasks": [{"id": "k1", "title": "Add the table", "brief": "b", "tier": "warrior"}]}}

    def run_read(harness, prompt, workdir, cancel, model="", env=None, resume="", timeout_s=0, effort="", budget=None,
                 one_shot=False, tools=True):
        step = ("goal" if "saved a goal" in prompt else "draft" if "write its spec" in prompt
                else "plan" if "turn it into a plan" in prompt else "other")
        seen.append({"step": step, "model": model, "resume": resume, "effort": effort, "budget": budget,
                     "one_shot": one_shot, "prompt": prompt})
        return json.dumps(answers.get(step, {})), None, 10, ""

    monkeypatch.setattr(jobs, "run_read", run_read)
    run_read.seen, run_read.answers = seen, answers
    return run_read


class FakeRunner:
    started: list = []
    released = ""
    ticked = False

    def __init__(self, *a, **k):
        FakeRunner.started = []

    def start(self, slug):
        FakeRunner.started.append(slug)

    def stop(self, slug):
        pass

    def tick(self):
        FakeRunner.ticked = True

    def release_holds(self, slug):
        FakeRunner.released = slug

    def stop_all(self):
        pass


@pytest.fixture
def runner(monkeypatch):
    monkeypatch.setitem(sys.modules, "orkboard.core.idea_runner", types.SimpleNamespace(IdeaRunner=FakeRunner))
    FakeRunner.started = []
    return FakeRunner


def _wait(host, slug="", goal=False):
    k = host.ideas.keeper
    for _ in range(500):
        if not (k.busy_goal(slug) if goal else k.busy(slug)):
            return
        time.sleep(0.01)
    raise AssertionError("the keeper never finished")


def _drafted(host, slug):
    """Talk is part D's (the leaders heard: tests/test_idea_talk.py); these tests are of the draft, so the goal is handed to it as the keeper's seam did before D."""
    ideas.save_state(host.ideas.state_dir, slug, state="raw", queue="now")
    host.ideas.keeper.draft(slug)


def _sent(host, text, track, **more):
    """A goal sent (spec 99 §4: no call, it waits as `routed`), then Talk: until part D lands, Talk reads it as the draft did at once."""
    got = host.command("ideas.add", {"text": text, "track": track, **more})
    assert ideas.state(host.ideas.state_dir, got["slug"])["state"] == "routed"
    _drafted(host, got["slug"])
    return got


def _events(host, name):
    return [r for r in event_log.read(Path(host.town.repo_root)) if r["event"] == name]


def _goal(host, about="Show the runs at a glance.", priority="normal", **more):
    slug = host.command("ideas.goal_save", {"about": about, "priority": priority, **more})["slug"]
    _wait(host, slug, goal=True)
    return slug


def test_a_goal_from_a_description_and_a_priority_is_read_at_once_and_written(host, model):
    slug = _goal(host, priority="high")
    (call,) = model.seen
    assert call["step"] == "goal" and "opus" in call["model"] and call["effort"] == "high" and call["budget"] == 1.0
    assert call["resume"] == "" and call["one_shot"] is True and "Show the runs at a glance." in call["prompt"]
    g = host.command("ideas.goal", {"slug": slug})
    assert g["title"] == "Runs at a glance" and g["title_by"] == "keeper" and g["priority"] == "high"
    assert g["summary"].startswith("The table lives in src/app.py.") and g["state"] == "ready"
    assert g["metrics"] == [] and '"metrics"' not in call["prompt"]            # spec 50 §2.5: a party has no end, the keeper asks no metrics (and the answer's are not read)
    assert g["links"] == ["src/app.py"]                                      # only paths that exist, never a URL
    st = ideas.goal_state(host.ideas.state_dir, slug)
    assert len(st["read_at"]) == 40 and st["read_at"] == host.ideas.keeper.head()
    (read,) = _events(host, "goal_read")
    assert read["tier"] and read["effort"] == "high" and read["step"] == "goal" and read["cost"] is None
    host.command("ideas.goal_save", {"slug": slug, "about": "Show runs.", "priority": "high", "title": "My own title"})
    _wait(host, slug, goal=True)
    assert host.command("ideas.goal", {"slug": slug})["title"] == "My own title"   # the person's: never rewritten
    assert host.command("ideas.goal", {"slug": slug})["title_by"] == "person"
    assert next(t for t in host.command("ideas.board")["tracks"] if t["slug"] == slug)["title_by"] == "person"


def test_a_goal_needs_a_party_and_is_drafted_at_once_whatever_its_priority_for_there_is_no_night(host, model, runner):
    with pytest.raises(CommandError, match="^A goal needs a party$"):
        host.command("ideas.add", {"text": "x"})
    with pytest.raises(CommandError, match="^A goal needs a party$"):
        host.command("ideas.add", {"text": "x", "track": "general"})
    g = _goal(host)
    seen = len(model.seen)
    high = _sent(host, "a high one", g, priority="high")
    _wait(host, high["slug"])
    normal = _sent(host, "a normal one", g)
    _wait(host, normal["slug"])
    low = _sent(host, "a low one", g, priority="low")
    _wait(host, low["slug"])
    closed = _sent(host, "closed dialog", g, priority="low", night=True)        # `night` is no longer a thing
    _wait(host, closed["slug"])
    assert [high["queue"], normal["queue"], low["queue"], closed["queue"]] == ["now", "now", "now", "now"]
    drafted = [c["prompt"] for c in model.seen[seen:] if c["step"] == "draft"]
    assert len(drafted) == 4 and "a high one" in drafted[0] and "a normal one" in drafted[1] and "a low one" in drafted[2]
    kept = host.command("ideas.add", {"text": "kept back", "track": g, "hold": True})
    assert kept["queue"] == "hold" and ideas.state(host.ideas.state_dir, kept["slug"])["state"] == "raw"
    added = _events(host, "idea_added")
    assert [(e["priority"], e["queue"]) for e in added] == [("high", "now"), ("normal", "now"), ("low", "now"), ("low", "now"), ("normal", "hold")]
    assert all(c["resume"] == "" and c["one_shot"] for c in model.seen)       # §0: no call ever resumes a session


def test_autostart_starts_what_is_safe_and_passed_by_says_who(host, model, runner):
    g = _goal(host)
    slug = _sent(host, "safe", g)["slug"]
    _wait(host, slug)
    plan = ideas.plan(host.ideas.state_dir, slug)
    assert plan["passed_by"] == "auto" and runner.started == [slug] and plan.get("start_at") is None
    (passed,) = _events(host, "plan_passed")
    assert passed["by"] == "auto" and passed["risk"] == "low" and passed["priority"] == "normal"
    (made,) = _events(host, "plan_made")
    assert made["step"] == "plan" and made["prompt_chars"] > 0 and made["tokens"] == {"total": 10} and made["cost"] is None


def test_needs_you_is_one_list_blocks_then_priority_then_age_proposals_last(host, model, runner):
    g = _goal(host)
    root, sd = host.ideas.root(), host.ideas.state_dir
    mk = lambda text, prio, state: (lambda s: (ideas.save_state(sd, s, state=state), s)[1])(ideas.add_idea(root, text, g, sd, prio))  # noqa: E731
    prop = mk("a proposal", "high", "proposed")
    asks_low = mk("asks low", "low", "asks")
    asks_high = mk("asks high", "high", "asks")
    work = mk("working", "low", "working")
    ideas.save_plan(sd, work, {"idea": work, "made_at": "2026-10-18T09:00:00", "passed_at": "x", "todos": [
        {"id": "t1", "title": "API_KEY", "kind": "secret", "why": "", "steps": ["Open the console"], "for": ["k1"], "done": False}],
        "tasks": [{"id": "k1", "title": "Use it", "state": "waiting", "after": []},
                  {"id": "k2", "title": "Broke", "state": "failed", "error": "boom", "after": []},
                  {"id": "k3", "title": "Waits", "state": "held", "note": "after 18:00", "after": []}]})
    needs = host.command("ideas.board")["needs_you"]
    kinds = [(n["kind"], n["title"]) for n in needs]
    assert kinds[:2] in ([("todo", "working"), ("failed", "working")], [("failed", "working"), ("todo", "working")])
    assert all(n["blocks"] for n in needs[:2]) and kinds[2:] == [("asks", "asks high"), ("asks", "asks low"), ("proposal", "a proposal")]
    assert needs[0]["goal"] == g and {"kind", "idea", "goal", "title", "text", "priority", "blocks", "at"} <= set(needs[0])
    assert not any(n["kind"] == "held" or "18:00" in n["text"] for n in needs)          # held leaves Needs you
    todo = next(n for n in needs if n["kind"] == "todo")["todo"]
    assert todo["steps"] == ["Open the console"]                              # steps on a secret
    assert host.snapshot()["needs_you"] == 4 and prop                          # the count leaves proposals out
    assert asks_low and asks_high


def test_queue_read_stop_and_board_set(host, model, runner):
    g = _goal(host)
    slug = host.command("ideas.add", {"text": "kept", "track": g, "hold": True})["slug"]
    host.command("ideas.read_stop", {"slug": slug})
    assert ideas.state(host.ideas.state_dir, slug)["queue"] == "hold"
    host.command("ideas.queue", {"slug": slug, "queue": "night"})                       # the name of before the night went: read as hold
    assert ideas.state(host.ideas.state_dir, slug)["queue"] == "hold"
    with pytest.raises(CommandError, match="The queue is now or hold"):
        host.command("ideas.queue", {"slug": slug, "queue": "later"})
    host.command("ideas.queue", {"slug": slug, "queue": "now", "via": "map"})
    _wait(host, slug)
    assert [(e["queue"], e["via"]) for e in _events(host, "idea_queued")] == [("hold", "idea"), ("now", "map")]   # spec 41 §4
    assert ideas.state(host.ideas.state_dir, slug)["state"] != "raw"
    got = host.command("ideas.board_set", {"target": "quality", "night": "22:00-05:00", "device": "phone"})
    assert got == {"target": "quality", "autostart": True, "night": "22:00-05:00", "review": False, "review_notice": False,
                   "work_at_night": False, "look_wait": "none", "build_start": "now", "night_rung": "off", "max_parallel": 1, "hours": []}      # spec 168 H2: the build starts as one value, the night's rung and goals at once; spec 121 §4.1: off by default; spec 84 §4: review is off by default; spec 144: the tests do not wait to look (tests/conftest.py)
    board = host.command("ideas.board")
    assert (board["target"], board["autostart"], board["night"]) == ("quality", True, "22:00-05:00")
    with pytest.raises(CommandError, match="thrift, balance or quality"):
        host.command("ideas.board_set", {"target": "cheap"})
    (e,) = _events(host, "board_set")
    assert e["target"] == "quality" and e["night"] == "22:00-05:00" and e["device"] == "phone"
    assert [e["idea"] for e in _events(host, "keeper_stopped")] == [slug]


def test_start_now_lets_the_reserves_held_task_go_as_the_persons_press_and_says_so(host, runner):
    """The owner, 26 October: *now I have this state and I don't know what to do next*. A task the reserve holds has a Start now: the press
    is the person's (the reserve is only for what starts by itself), the goal's held tasks are let go, the runner ticks, and the event
    says how many were held."""
    root, sd = host.ideas.root(), host.ideas.state_dir
    g = ideas.add_track(root, "Chips")
    a = ideas.add_idea(root, "auto", g, sd)
    task = lambda tid, state, note="", **more: {"id": tid, "title": tid, "brief": "b", "tier": "warrior", "kind": "code",  # noqa: E731
                                                "after": [], "state": state, "note": note, "started": "", **more}
    why = "Waits for Antigravity's limit: 14 % of the week left, kept for you until 12:00"
    ideas.save_plan(sd, a, {"idea": a, "passed_at": "x", "passed_by": "auto", "todos": [],
                            "tasks": [task("k1", "held", "reserve · after 12:00", held_why=why), task("k2", "waiting")]})
    ideas.save_state(sd, a, state="working", error="")
    chips = [c for r in host.command("ideas.agents")["roles"] for c in r.get("chips") or [] if c.get("task")]
    assert next(c for c in chips if c["task"] == "k1")["why"] == why                  # the Agents' chip carries the sentence
    assert host.command("ideas.task", {"slug": a, "task": "k1"})["held_why"] == why
    host.command("ideas.start_now", {"slug": a, "via": "hand"})
    assert ideas.plan(sd, a)["passed_by"] == "person" and runner.released == a and runner.ticked is True
    assert [(e["idea"], e["via"], e["held"]) for e in _events(host, "plan_started_now")] == [(a, "hand", 1)]
    with pytest.raises(CommandError, match="does not wait for the night or for your reserve"):
        ideas.edit_plan(sd, a, lambda p: p.update(tasks=[task("k1", "held", "after 12:00")]))      # a tool's own window is not the person's to override
        host.command("ideas.start_now", {"slug": a})
