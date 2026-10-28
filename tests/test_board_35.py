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


def _sent(host, text, track, **more):
    """A goal sent (spec 99 §4: no call, it waits as `routed`), then Talk: until part D lands, Talk reads it as the draft did at once."""
    got = host.command("ideas.add", {"text": text, "track": track, **more})
    assert ideas.state(host.ideas.state_dir, got["slug"])["state"] == "routed"
    host.command("ideas.talk", {"idea": got["slug"]})
    return got


def _events(host, name):
    return [r for r in event_log.read(Path(host.town.repo_root)) if r["event"] == name]


def _goal(host, about="Show the runs at a glance.", priority="normal", **more):
    slug = host.command("ideas.goal_save", {"about": about, "priority": priority, **more})["slug"]
    _wait(host, slug, goal=True)
    return slug


def test_the_new_commands_are_the_hosts_and_a_phones(host):
    assert NEW <= set(host.commands) and all(BoardPhone.allowed(host, c, {}) for c in NEW)


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
    host.command("ideas.night_allow", {"allow": True})          # stored for the phone and Orkline, read by nothing here (spec 99 §3)
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


def test_autostart_off_or_a_question_or_a_stopped_plan_waits_for_the_person(host, model, runner):
    g = _goal(host)
    host.command("ideas.board_set", {"autostart": False})
    a = _sent(host, "off", g)["slug"]
    _wait(host, a)
    assert ideas.plan(host.ideas.state_dir, a).get("passed_at") is None and runner.started == []
    host.command("ideas.board_set", {"autostart": True})
    model.answers["draft"] = {**model.answers["draft"], "questions": ["Which columns?"]}
    b = _sent(host, "asks", g)["slug"]
    _wait(host, b)
    assert ideas.state(host.ideas.state_dir, b)["state"] == "asks" and ideas.plan(host.ideas.state_dir, b) is None
    host.command("ideas.start", {"slug": a})                                  # the person passes it …
    assert ideas.plan(host.ideas.state_dir, a)["passed_by"] == "person"
    host.command("ideas.stop", {"slug": a})                                   # … and stops it: it waits for them now
    ideas.edit_plan(host.ideas.state_dir, a, lambda p: p.update(passed_at=None))
    ideas.save_state(host.ideas.state_dir, a, state="plan")
    assert host.ideas.autostart(a) == "" and ideas.plan(host.ideas.state_dir, a).get("passed_at") is None


def test_a_low_safe_plan_starts_at_once_and_a_plan_of_before_the_night_went_waits_for_start_now_or_the_clock(host, model, runner):
    g = _goal(host, priority="low")
    host.command("ideas.night_allow", {"allow": True})          # stored, read by nothing here (spec 99 §3)
    slug = host.command("ideas.add", {"text": "low and safe", "track": g, "priority": "low"})["slug"]
    ideas.save_state(host.ideas.state_dir, slug, state="raw")
    host.ideas.keeper.draft_one(slug)
    plan = ideas.plan(host.ideas.state_dir, slug)
    assert plan.get("start_at") is None and plan["passed_by"] == "auto" and runner.started == [slug]       # no night to wait for
    with pytest.raises(CommandError, match="does not wait for the night"):
        host.command("ideas.start_now", {"slug": slug})
    old = ideas.add_idea(host.ideas.root(), "passed for the night, before it went", g, host.ideas.state_dir)
    ideas.save_plan(host.ideas.state_dir, old, {"idea": old, "passed_at": "x", "passed_by": "auto", "start_at": "night", "todos": [], "tasks": []})
    ideas.save_state(host.ideas.state_dir, old, state="plan")
    row = next(i for i in host.command("ideas.board")["ideas"] if i["slug"] == old)
    assert row["start_at"] == "night" and row["state"] == "plan"
    host.command("ideas.start_now", {"slug": old, "via": "map"})
    assert ideas.plan(host.ideas.state_dir, old)["start_at"] is None and runner.started == [slug, old]
    assert [(e["idea"], e["via"]) for e in _events(host, "plan_started_now")] == [(old, "map")]       # spec 41 §4
    other = ideas.add_idea(host.ideas.root(), "another of before", g, host.ideas.state_dir)
    ideas.save_plan(host.ideas.state_dir, other, {"idea": other, "passed_at": "x", "passed_by": "auto", "start_at": "night", "todos": [], "tasks": []})
    ideas.save_state(host.ideas.state_dir, other, state="plan")
    assert host.ideas.older_night_plans() == 1 and runner.started == [slug, old, other]               # the clock hands it on: it waits for the reserve, not a night
    assert ideas.plan(host.ideas.state_dir, other)["start_at"] == "night" and ideas.state(host.ideas.state_dir, other)["state"] == "working"


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


def test_a_proposal_that_waits_is_taken_and_drafted_at_once_or_dropped_and_none_is_kept_for_a_night(host, model, runner):
    g = _goal(host)
    root, sd = host.ideas.root(), host.ideas.state_dir
    take = ideas.add_idea(root, "why take", g, sd)
    no = ideas.add_idea(root, "why not", g, sd)
    for s in (take, no):
        ideas.save_state(sd, s, state="proposed")
    host.command("ideas.proposal", {"slug": take, "take": True, "priority": "low"})
    _wait(host, take)
    assert ideas.state(sd, take)["state"] not in ("proposed", "raw") and ideas.state(sd, take)["queue"] != "night"        # drafted at once: Low waits for no night
    host.command("ideas.proposal", {"slug": no, "take": False, "reason": "not now"})
    assert ideas.idea_page(root, no) is None
    assert not (sd / "ideas" / "declined.jsonl").exists()
    assert [(e["take"], e["has_reason"]) for e in _events(host, "proposal_answered")] == [(True, False), (False, True)]


def test_queue_read_stop_and_board_set(host, model, runner):
    g = _goal(host)
    host.command("ideas.night_allow", {"allow": True})          # stored, read by nothing here (spec 99 §3)
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
    assert got == {"target": "quality", "autostart": True, "night": "22:00-05:00", "review": False, "review_notice": False, "night_low": True}      # spec 84 §4: review is off by default
    board = host.command("ideas.board")
    assert (board["target"], board["autostart"], board["night"]) == ("quality", True, "22:00-05:00")
    with pytest.raises(CommandError, match="thrift, balance or quality"):
        host.command("ideas.board_set", {"target": "cheap"})
    (e,) = _events(host, "board_set")
    assert e["target"] == "quality" and e["night"] == "22:00-05:00" and e["device"] == "phone"
    assert [e["idea"] for e in _events(host, "keeper_stopped")] == [slug]
    assert _events(host, "night_allowed") == []                                         # the answer is stored and nothing more


def test_the_nights_answer_is_stored_for_the_phone_and_orkline_and_read_by_nothing(host, model, runner):
    assert host.command("ideas.board")["night_low"] is None
    assert host.command("ideas.night_allow", {"allow": True}) == {"ok": True, "moved": 0}
    assert host.command("ideas.board")["night_low"] is True
    host.command("ideas.night_allow", {"allow": False})
    assert host.command("ideas.board")["night_low"] is False
    with pytest.raises(CommandError, match="on or off"):
        host.command("ideas.night_allow", {"allow": "yes"})


def test_a_file_todo_is_kept_outside_the_repository_and_off_the_plan(host, model, runner):
    g = _goal(host)
    slug = host.command("ideas.add", {"text": "needs a file", "track": g, "hold": True})["slug"]
    ideas.save_plan(host.ideas.state_dir, slug, {"idea": slug, "made_at": "x", "passed_at": None, "tasks": [
        {"id": "k1", "title": "Use it", "brief": "b", "state": "waiting", "after": []}], "todos": [
        {"id": "t2", "title": "the Firebase config", "kind": "file", "why": "", "steps": ["Download it"], "accept": ["json"],
         "for": ["k1"], "done": False, "value": None}]})
    ideas.save_state(host.ideas.state_dir, slug, state="plan")
    data = base64.b64encode(b'{"project": "x-secret"}').decode()
    with pytest.raises(CommandError, match="paired link"):
        host.command("ideas.todo", {"idea": slug, "id": "t2", "done": True, "file": {"name": "g.json", "data": data},
                                    "device": "phone"})
    with pytest.raises(CommandError, match="not one it takes"):
        host.command("ideas.todo", {"idea": slug, "id": "t2", "done": True, "file": {"name": "g.txt", "data": data}})
    host.command("ideas.todo", {"idea": slug, "id": "t2", "done": True, "file": {"name": "google-services.json", "data": data}})
    plan_text = (host.ideas.state_dir / "ideas" / slug / "plan.json").read_text()
    assert "x-secret" not in plan_text and json.loads(plan_text)["todos"][0]["value"] == "google-services.json"
    path = idea_secrets.file_path(host.ideas.state_dir, slug, "t2")
    assert path.read_bytes() == b'{"project": "x-secret"}' and oct(path.stat().st_mode & 0o777) == "0o600"
    assert host.ideas.state_dir in path.parents and not list(Path(host.town.repo_root).glob("**/google-services.json"))[1:]
    guarded = BoardPhone.guard("ideas.todo", {"idea": slug, "link": "paired"}, {"id": "p1", "name": "Phone"})
    assert guarded["link"] == "paired" and BoardPhone.guard("ideas.todo", {"link": "paired"}, {})["device"] == "phone"
    assert "link" not in BoardPhone.guard("ideas.todo", {"link": "paired"}, {})
    host.command("ideas.drop", {"slug": slug})
    assert not path.exists()


def test_the_agents_chips_say_by_itself_tonight_and_why_held(host, runner):
    root, sd = host.ideas.root(), host.ideas.state_dir
    g = ideas.add_track(root, "Chips")
    a = ideas.add_idea(root, "auto", g, sd)
    b = ideas.add_idea(root, "night", g, sd)
    task = lambda tid, state, note="": {"id": tid, "title": tid, "brief": "b", "tier": "warrior", "kind": "code",  # noqa: E731
                                        "after": [], "state": state, "note": note, "started": ""}
    ideas.save_plan(sd, a, {"idea": a, "passed_at": "x", "passed_by": "auto", "todos": [],
                            "tasks": [task("k1", "held", "reserve · after 18:00"), task("k2", "held", "after 19:00")]})
    ideas.save_plan(sd, b, {"idea": b, "passed_at": "x", "passed_by": "auto", "start_at": "night", "todos": [],
                            "tasks": [task("k1", "ready")]})
    chips = [c for r in host.command("ideas.agents")["roles"] for c in r.get("chips") or [] if c.get("task")]
    got = {(c["idea"], c["task"]): c for c in chips}
    assert got[(a, "k1")]["by"] == "auto" and got[(a, "k1")]["note"].startswith("reserve") and not got[(a, "k1")]["night"]
    assert got[(a, "k2")]["note"] == "after 19:00" and got[(b, "k1")]["night"] is True


def test_board_set_turns_looking_at_each_result_on_and_the_notice_is_said_once(host):
    """Spec 84 §1, §4: `review` is off by default and the Board says so; the person's switch writes it, and the face clears the notice."""
    assert host.command("ideas.board")["review"] is False
    host.machine.review_notice = True
    assert host.command("ideas.board")["review_notice"] is True
    got = host.command("ideas.board_set", {"review": True, "review_notice": False})
    assert got["review"] is True and got["review_notice"] is False and host.machine.review_notice is False
    assert host.command("ideas.board")["review"] is True
    with pytest.raises(CommandError, match="Looking at each result"):
        host.command("ideas.board_set", {"review": "yes"})


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
