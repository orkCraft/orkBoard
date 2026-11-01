"""Spec 121 part C (docs/specs/121-the-day-the-morning-and-the-night.md §4, decisions §199.4), on the host with the model call and the runner stubbed
(tests/test_board_35.py's): the setting *Work at night* (off by default); a plan that would start by itself waits for the night's window, in
Product's order, and goes when the window opens; a press and a bug's short way start at once; **Build it now** (`ideas.start_now`, widened) and
**Pick and build now** (`ideas.pick` with `now: true`) build by day, ahead of the queue."""
from __future__ import annotations

from pathlib import Path

import pytest

from orkboard import settings
from orkboard.gui.board_host import CommandError
from orkboard.realm import event_log, idea_questions, idea_risk, idea_target, ideas, night_order
from tests.test_board_35 import FakeRunner, _drafted, _events, _goal, _wait, host, model, runner  # noqa: F401  (fixtures)


@pytest.fixture
def night(monkeypatch):
    """The night's window, shut until a test opens it: `night["open"] = True`."""
    state = {"open": False}
    monkeypatch.setattr(idea_target, "in_night", lambda spec, now=None: state["open"])
    return state


def on(host) -> None:
    host.command("ideas.board_set", {"work_at_night": True})


def sent(host, text: str, goal: str, how: dict | None = None, stances: list | None = None, **more) -> str:
    """A goal sent and drafted to its plan: its route's `how` and Talk's stances (Product's `priority`) kept before the plan is made."""
    slug = host.command("ideas.add", {"text": text, "track": goal, **more})["slug"]
    sd = host.ideas.state_dir
    if how is not None:
        ideas.save_state(sd, slug, route_how=how)
    if stances is not None:
        idea_questions.save_record(sd, slug, {"mode": "talk", "stances": stances})
    _drafted(host, slug)
    _wait(host, slug)
    return slug


def plan_of(host, slug: str) -> dict:
    return ideas.plan(host.ideas.state_dir, slug)


def test_the_board_carries_the_settings_words_with_the_nights_hour_said(host):
    """Spec 121 §1, §7.3: the faces read the setting's words from the host (`ideas.board`'s `night_words`), the night's window said in them."""
    words = host.command("ideas.board", {})["night_words"]
    assert words["label"] == "Work at night" and words["now"] == "Build it now" and words["now_sketch"] == "Pick and build now"
    assert words["waits"] == "Waits for the night (01:00)" and "(01:00–07:00)" in words["hint"]
    host.command("ideas.board_set", {"night": "22:30-06:00"})
    words = host.command("ideas.board", {})["night_words"]
    assert words["waits"] == "Waits for the night (22:30)" and "(22:30–06:00)" in words["hint"]


def product(priority: str) -> list[dict]:
    """Talk's stances as spec 120 C keeps them: Product's carries `priority`."""
    return [{"party": "tech", "leader": "a", "verdict": "go"}, {"party": "product", "leader": "b", "verdict": "go", "priority": priority}]


# -- decide, and the setting ----------------------------------------------------------------------------------------------

@pytest.mark.parametrize("risk,priority,what", [
    ("low", "high", "night"), ("low", "normal", "night"), ("low", "low", "night"),
    ("medium", "high", "night"), ("medium", "normal", "wait"), ("medium", "low", "wait"),
    ("high", "high", "wait"), ("high", "normal", "wait"), ("high", "low", "wait")])
def test_what_would_start_by_itself_is_held_for_the_night_and_what_waits_for_the_person_still_waits(risk, priority, what):
    assert idea_risk.decide(risk, priority, held_for_night=True) == idea_risk.decide(risk, priority, night=True, held_for_night=True) == what
    plain = idea_risk.decide(risk, priority)
    assert idea_risk.decide(risk, priority, held_for_night=False) == plain and (plain == "wait") == (what == "wait")      # off: today's table


def test_the_setting_is_off_by_default_cleaned_and_kept_per_project(host, tmp_path):
    assert settings.IDEAS["work_at_night"] is False and settings.clean_ideas({})["work_at_night"] is False
    assert settings.clean_ideas({"work_at_night": "yes"})["work_at_night"] is False and settings.clean_ideas({"work_at_night": True})["work_at_night"] is True
    assert "work_at_night" in settings.BOARD
    assert host.command("ideas.board")["work_at_night"] is False
    got = host.command("ideas.board_set", {"work_at_night": True, "device": "phone"})
    assert got["work_at_night"] is True and host.command("ideas.board")["work_at_night"] is True
    assert settings.board_of(Path(host.repo_root), None)["work_at_night"] is True           # the project's board.json, not the machine's
    (e,) = _events(host, "board_set")
    assert e["work_at_night"] is True and e["device"] == "phone"
    with pytest.raises(CommandError, match="^Work at night is on or off$"):
        host.command("ideas.board_set", {"work_at_night": "yes"})
    assert host.command("ideas.board_set", {"work_at_night": False})["work_at_night"] is False


def test_the_settings_words_say_the_window_and_what_still_runs_by_day():
    from orkboard.gui.ideas_board import night_words
    words = night_words("01:00-07:00")
    assert words["label"] == "Work at night" and "(01:00–07:00)" in words["hint"]
    assert words["hint"].startswith("What you decide by day is built in the night's window") and "Talk, hearings and sketches still run by day" in words["hint"]
    assert "A bug's short way, and anything you start with a press, starts at once." in words["hint"]
    assert words["waits"] == "Waits for the night (01:00)" and words["now"] == "Build it now" and words["now_sketch"] == "Pick and build now"


# -- what is held, and what is not -----------------------------------------------------------------------------------------

def test_with_the_setting_off_a_safe_plan_starts_at_once_as_before(host, model, runner, night):
    slug = sent(host, "safe", _goal(host))
    assert runner.started == [slug] and plan_of(host, slug)["passed_by"] == "auto" and not plan_of(host, slug).get("held_for_night")
    assert _events(host, "night_held") == []


def test_a_plan_that_would_start_by_itself_waits_for_the_night_and_says_so(host, model, runner, night):
    on(host)
    slug = sent(host, "safe", _goal(host))
    plan = plan_of(host, slug)
    assert runner.started == [] and plan.get("passed_at") is None and plan["held_for_night"] is True and plan["start_at"] == "night"
    assert ideas.state(host.ideas.state_dir, slug)["state"] == "plan"
    row = next(i for i in host.command("ideas.board")["ideas"] if i["slug"] == slug)
    assert row["state"] == "plan" and row["start_at"] == "night"                          # the faces' *starts tonight* and their Start now
    assert host.ideas.autostart(slug) == "night" and [e["idea"] for e in _events(host, "night_held")] == [slug]      # decided again: held once, said once


def test_what_waits_for_the_person_still_waits_and_is_not_marked_as_held(host, model, runner, night):
    on(host)
    model.answers["draft"] = {**model.answers["draft"], "risk": "medium"}
    slug = sent(host, "risky", _goal(host))
    assert runner.started == [] and not plan_of(host, slug).get("held_for_night") and plan_of(host, slug).get("start_at") is None
    assert _events(host, "night_held") == []


def test_a_plan_made_while_the_window_is_open_starts_at_once(host, model, runner, night):
    on(host)
    night["open"] = True
    slug = sent(host, "in the window", _goal(host))
    assert runner.started == [slug] and _events(host, "night_held") == [] and _events(host, "night_started") == []


def test_a_bugs_short_way_starts_at_once(host, model, runner, night):
    on(host)
    g = _goal(host)
    bug = sent(host, "a bug", g, how={"kind": "bug", "short": True, "reproduces": True})
    tidy = sent(host, "a tidy", g, how={"kind": "tidy", "short": True})
    long_bug = sent(host, "a bug that went the long way", g, how={"kind": "bug", "short": False})
    assert runner.started == [bug] and plan_of(host, bug)["passed_by"] == "auto"
    assert all(plan_of(host, s)["held_for_night"] for s in (tidy, long_bug))              # only the bug's short way is exempt (spec 121 §4.2)


def test_a_press_on_a_held_plan_starts_it_at_once(host, model, runner, night):
    on(host)
    slug = sent(host, "safe", _goal(host))
    host.command("ideas.start", {"slug": slug})
    plan = plan_of(host, slug)
    assert runner.started == [slug] and plan["passed_by"] == "person" and not plan.get("held_for_night") and plan["start_at"] is None
    assert _events(host, "built_now") == []                                               # an ordinary Start is not *Build it now*


# -- the night's window opens: Product's order ------------------------------------------------------------------------------------

def test_the_night_passes_the_held_goals_by_products_priority_then_their_place_in_line(host, model, runner, night):
    on(host)
    g = _goal(host)
    low_by_product = sent(host, "low first in line", g, stances=product("low"), priority="high")
    normal = sent(host, "no word of Product", g, priority="normal")
    high_by_product = sent(host, "high by Product", g, stances=product("high"), priority="low")
    normal_too = sent(host, "normal, later in line", g, stances=product("normal"), priority="normal")
    assert runner.started == []
    assert [plan_of(host, s)["night_priority"] for s in (low_by_product, normal, high_by_product, normal_too)] == ["low", "normal", "high", "normal"]
    assert host.ideas.night_tick() == 0 and runner.started == []                          # the window is shut
    night["open"] = True
    assert host.ideas.older_night_plans() == 4                                            # what the clock calls (gui/ideas.py `tick`)
    assert runner.started == [high_by_product, normal, normal_too, low_by_product]        # Product's word first; the same word: the place in line
    assert all(plan_of(host, s)["passed_by"] == "auto" and not plan_of(host, s).get("held_for_night") for s in runner.started)
    started = _events(host, "night_started")
    assert [e["idea"] for e in started] == runner.started and all(e["at"] for e in started)         # the line's own `at` is when the night began it
    assert host.ideas.night_tick() == 0                                                   # nothing held is left


def test_the_runners_rank_follows_the_nights_order_and_a_plan_built_now_goes_ahead_of_it(host, model, runner, night):
    on(host)
    g = _goal(host)
    first = sent(host, "first", g, stances=product("high"), priority="low")
    second = sent(host, "second", g, stances=product("low"), priority="high")
    assert host.ideas.rank(first) < host.ideas.rank(second)                               # Product's word, not the goal's own priority
    host.command("ideas.start_now", {"slug": second})
    assert host.ideas.rank(second) < host.ideas.rank(first)                               # ahead of the night's queue
    assert host.ideas.rank(second) == (night_order.AHEAD, 0, 0)


def test_turning_the_setting_off_lets_the_held_plans_go_at_once(host, model, runner, night):
    on(host)
    slug = sent(host, "safe", _goal(host))
    assert runner.started == []
    host.command("ideas.board_set", {"work_at_night": False})
    assert runner.started == [slug] and plan_of(host, slug)["passed_by"] == "auto"
    assert _events(host, "night_started") == []                                           # it did not wait for a night: no night began it


def test_a_held_plan_whose_risk_was_raised_waits_for_the_person_not_the_night(host, model, runner, night):
    on(host)
    slug = sent(host, "safe", _goal(host))
    assert plan_of(host, slug)["held_for_night"] is True
    ideas.set_meta(host.ideas.root(), slug, risk="medium")
    assert host.ideas.autostart(slug) == "wait"
    plan = plan_of(host, slug)
    assert not plan.get("held_for_night") and plan["start_at"] is None and runner.started == []
    night["open"] = True
    assert host.ideas.night_tick() == 0 and runner.started == []                          # the night does not pass what waits for the person


# -- Build it now ----------------------------------------------------------------------------------------------------------------

def test_build_it_now_passes_a_held_plan_at_once_as_the_persons_press_from_the_phone_too(host, model, runner, night):
    on(host)
    g = _goal(host)
    other = sent(host, "other", g, stances=product("high"))
    slug = sent(host, "built by day", g)
    assert runner.started == []
    host.command("ideas.start_now", {"slug": slug, "via": "hand", "device": "phone"})
    plan = plan_of(host, slug)
    assert runner.started == [slug] and plan["passed_by"] == "person" and plan["start_at"] is None and not plan.get("held_for_night") and plan["ahead"] is True
    assert ideas.state(host.ideas.state_dir, slug)["state"] == "working"
    assert plan_of(host, other)["held_for_night"] is True                                 # the others still wait for the night
    (now,) = _events(host, "built_now")
    assert (now["idea"], now["from"], now["device"]) == (slug, "card", "phone")
    assert [(e["idea"], e["via"]) for e in _events(host, "plan_started_now")] == [(slug, "hand")]
    (passed,) = [e for e in _events(host, "plan_passed") if e["idea"] == slug]
    assert passed["by"] == "person"
    with pytest.raises(CommandError, match="does not wait for the night or for your reserve"):
        host.command("ideas.start_now", {"slug": slug})                                   # nothing held any more


def test_a_plan_that_does_not_wait_for_the_night_is_still_refused(host, model, runner, night):
    slug = sent(host, "safe", _goal(host))                                                # the setting off: it started at once
    with pytest.raises(CommandError, match="does not wait for the night or for your reserve"):
        host.command("ideas.start_now", {"slug": slug})


# -- Pick and build now ------------------------------------------------------------------------------------------------------------

class RunnerError(Exception):
    """Named as the runner's (gui/ideas.py `commands` turns the exception of that name into the refusal the person reads)."""


class Answering(FakeRunner):
    """The runner's answer to a pick: kept, or refused."""
    started: list = []
    answers: list = []
    refuse = False

    def start(self, slug):
        Answering.started.append(slug)

    def pick(self, slug, tid, key, note="", device="desktop", via=""):
        if Answering.refuse:
            raise RunnerError("Answered already")
        Answering.answers.append((slug, tid, key, note, device))


@pytest.fixture
def answering(monkeypatch, runner):
    import sys
    import types
    monkeypatch.setitem(sys.modules, "orkboard.core.idea_runner", types.SimpleNamespace(IdeaRunner=Answering))
    Answering.started, Answering.answers, Answering.refuse = [], [], False
    return Answering


def raw_goal(host, text: str, goal: str) -> str:
    """A goal that has not been drafted yet: what a pick leaves (its sections and plan come after the answer). The pick is a task `k1`'s, answered by the runner stubbed here; a goal's own sketch
    (the task `sketch`, spec 121 A) is answered by the keeper (tests/test_idea_sketch.py `test_pick_and_build_now_keeps_the_press_with_the_goal_and_a_refused_answer_builds_nothing`)."""
    slug = host.command("ideas.add", {"text": text, "track": goal})["slug"]
    ideas.save_state(host.ideas.state_dir, slug, state="raw", queue="now")
    return slug


def build(host, slug: str) -> None:
    host.ideas.keeper.draft(slug)
    _wait(host, slug)


def test_pick_and_build_now_passes_the_plan_at_once_when_it_is_made(host, model, answering, night):
    on(host)
    g = _goal(host)
    plain, now = raw_goal(host, "plain pick", g), raw_goal(host, "pick and build now", g)
    host.command("ideas.pick", {"slug": plain, "task": "k1", "key": "A"})
    host.command("ideas.pick", {"slug": now, "task": "k1", "key": "B", "note": "bigger", "now": True, "device": "phone"})
    assert answering.answers == [(plain, "k1", "A", "", "desktop"), (now, "k1", "B", "bigger", "phone")]
    build(host, plain)
    build(host, now)
    assert answering.started == [now] and plan_of(host, plain)["held_for_night"] is True      # the plain pick's plan waits for the night
    assert plan_of(host, now)["passed_by"] == "auto" and not plan_of(host, now).get("held_for_night")
    (built,) = _events(host, "built_now")
    assert (built["idea"], built["from"], built["device"]) == (now, "sketch", "phone")
    assert host.ideas._build_now_of(now) is None                                           # said once: the flag goes when the plan is passed


def test_pick_and_build_now_leaves_it_to_the_person_when_autostart_says_wait(host, model, answering, night):
    on(host)
    model.answers["draft"] = {**model.answers["draft"], "risk": "medium"}
    slug = raw_goal(host, "risky", _goal(host))
    host.command("ideas.pick", {"slug": slug, "task": "k1", "key": "A", "now": True})
    build(host, slug)
    assert answering.started == [] and plan_of(host, slug).get("passed_at") is None and not plan_of(host, slug).get("held_for_night")
    assert _events(host, "built_now") == []
    host.command("ideas.start", {"slug": slug})                                               # *Start* is the hand's card, as today
    assert answering.started == [slug] and plan_of(host, slug)["passed_by"] == "person" and host.ideas._build_now_of(slug) is None


def test_now_is_kept_only_with_a_picked_variant_and_a_refused_answer_builds_nothing(host, model, answering, night):
    on(host)
    g = _goal(host)
    asked_again = raw_goal(host, "new ones asked", g)
    host.command("ideas.pick", {"slug": asked_again, "task": "k1", "key": None, "note": "other", "now": True})
    assert host.ideas._build_now_of(asked_again) is None                                        # none picked: nothing to build yet
    refused = raw_goal(host, "refused", g)
    answering.refuse = True
    with pytest.raises(CommandError):
        host.command("ideas.pick", {"slug": refused, "task": "k1", "key": "A", "now": True})
    assert host.ideas._build_now_of(refused) is None
    with pytest.raises(CommandError, match="^now is on or off$"):
        host.command("ideas.pick", {"slug": refused, "task": "k1", "key": "A", "now": "yes"})
    # a task's pick in the work of a plan passed already keeps nothing
    answering.refuse = False
    running = raw_goal(host, "running", g)
    build(host, running)
    host.command("ideas.start", {"slug": running})
    host.command("ideas.pick", {"slug": running, "task": "k1", "key": "A", "now": True})
    assert host.ideas._build_now_of(running) is None


def test_with_the_setting_off_pick_and_build_now_changes_nothing(host, model, answering, night):
    slug = raw_goal(host, "off", _goal(host))
    host.command("ideas.pick", {"slug": slug, "task": "k1", "key": "A", "now": True})
    build(host, slug)
    assert answering.started == [slug] and plan_of(host, slug)["passed_by"] == "auto"
    assert [e["from"] for e in _events(host, "built_now")] == ["sketch"]                      # (it started at once anyway: the event still says what the person pressed)


# -- the order, alone ----------------------------------------------------------------------------------------------------------------

def test_products_priority_is_read_defensively_and_is_normal_without_a_word():
    read = night_order.priority_of
    assert read({}) == read(None) == read({"stances": "x"}) == read({"stances": [None, 3, {}]}) == "normal"
    assert read({"stances": [{"party": "tech"}, {"party": "product", "priority": "High"}]}) == "high"
    assert read({"stances": [{"priority": "urgent"}, {"priority": "low"}]}) == "low"          # a word out of the three is not a word
    assert read({"stances": [], "weigher": {"priority": "low"}}) == "low"
    assert night_order.key("high", (1, 2)) < night_order.key("normal", (0, 0)) < night_order.key("low", (0, 0))
    assert night_order.key("normal", (0, 0)) < night_order.key("nonsense", (0, 1)) < night_order.key("low", (0, 0))       # a word out of the three is the middle one
    assert night_order.index("nonsense") == night_order.index("normal") == 1
    assert sorted(["low", "high", "normal"], key=night_order.index) == ["high", "normal", "low"]
