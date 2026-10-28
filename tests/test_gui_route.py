"""Spec 99 C (docs/specs/99-a-goals-way.md §4) on the host: a goal sent makes no model call and waits as `routed` with its route row; the route's
edits, Talk, *Later, by itself*, the short way's Start and the `start` row. The model call is stubbed (`keeper.call`)."""
from __future__ import annotations

import datetime as dt
import json
import sys
import time

import pytest

from orkboard.gui.board_host import BoardPhone, CommandError, Orkboard
from orkboard.realm import goal_route, goal_team, idea_spend, ideas, library
from orkboard.sources.limits import Limit

ROUTE_COMMANDS = {"ideas.route_set", "ideas.talk", "ideas.route_later", "ideas.route_start"}


@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


@pytest.fixture
def calls(host):
    """The keeper's model call stubbed: `calls` holds every one; it answers a draft with a spec that asks nothing, a route with `answer["route"]`."""
    class Seen(list):
        answer: dict
    seen = Seen()
    answer = {"route": ""}

    def call(tier, prompt, effort="", budget=None):
        seen.append({"tier": tier, "prompt": prompt, "effort": effort, "budget": budget, "tools": getattr(host.ideas.keeper._tls, "tools", True),
                     "step": host.ideas.keeper.measure()["step"]})
        if "Say which of the project's parties" in prompt:
            return answer["route"], 0.01, 10, ""
        return json.dumps({"summary": "", "questions": [], "title": "A goal"}), 0.01, 10, ""

    host.ideas.keeper.call = call
    seen.answer = answer
    return seen


def _party(host, title, leader, team, craft):
    root, state = host.ideas.root(), host.ideas.state_dir
    library.install(state, [s for s in (*team, leader) if library.get(s) is not None])
    slug, _new = ideas.save_goal(root, None, title, "About " + title, None, "normal", craft=craft)
    goal_team.set_team(root, slug, list(team), leader=leader)
    return slug


@pytest.fixture
def parties(host):
    return {"product": _party(host, "Product", "product-manager", ["copywriter"], "product"),
            "design": _party(host, "Design", "product-designer", ["artist", "ui-kit"], "design"),
            "tech": _party(host, "Tech", "architect", ["grunt", "tester"], "engineering"),
            "release": _party(host, "Release", "release-manager", [], "engineering")}


def _state(host, slug):
    return ideas.state(host.ideas.state_dir, slug)


def _wait(host, slug):
    for _ in range(500):
        if not host.ideas.keeper.busy(slug):
            return
        time.sleep(0.01)
    raise AssertionError("the keeper never finished")


def _row(host, slug, kind):
    return next((n for n in host.command("ideas.board")["needs_you"] if n["idea"] == slug and n["kind"] == kind), None)


def test_the_route_commands_are_the_hosts_and_a_phones(host):
    assert ROUTE_COMMANDS <= set(host.commands) and all(BoardPhone.allowed(host, c, {}) for c in ROUTE_COMMANDS)


def test_a_goal_sent_makes_no_call_and_waits_routed_with_its_route_row(host, parties, calls):
    got = host.command("ideas.add", {"text": "A new logo for the app", "track": parties["tech"]})
    slug = got["slug"]
    assert calls == [] and got["route"] == [parties["tech"]] and got["queue"] == "now"
    st = _state(host, slug)
    assert st["state"] == "routed" and st["queue"] == "" and st["route"] == [{"party": parties["tech"], "leader": "architect"}]
    assert st["route_how"]["by"] == "party" and st["route_how"]["short"] is False
    host.ideas.keeper.tick()                                                    # the keeper's clock drafts nothing that is routed
    assert calls == [] and not host.ideas.keeper.busy(slug)
    row = _row(host, slug, "route")
    assert row["route"][0]["party"] == parties["tech"] and row["place"] == 1 and row["short"] is False and row["low"] is False
    assert row["cost"]["calls"] == 4 and row["goal"] == parties["tech"] and row["blocks"] is False
    node = next(i for i in host.command("ideas.board")["ideas"] if i["slug"] == slug)
    assert node["state"] == "routed" and node["place"] == "hand" and node["asks_you"] is False
    page = host.command("ideas.page", {"slug": slug})
    assert page["state"] == "routed" and page["busy"] is False
    mapped = next(n for n in host.command("ideas.map", {})["nodes"] if n["slug"] == slug)
    assert mapped["needs_you"] == "route" and mapped["place"] == "hand"
    assert host.ideas.snapshot()["needs_you"] == 1


def test_a_goal_sent_to_no_party_is_routed_by_code_and_a_bug_is_techs_alone(host, parties, calls):
    bug = host.command("ideas.add", {"text": "Saving crashes: Traceback (most recent call last):\n  File \"a.py\", line 1\nValueError: x"})
    assert calls == [] and bug["route"] == [parties["tech"]]
    st = _state(host, bug["slug"])
    assert st["route_how"]["short"] is True and st["route_how"]["reproduces"] is True and st["route_how"]["by"] == "code"
    row = _row(host, bug["slug"], "route")
    assert row["short"] is True and row["reproduces"] is True and row["cost"]["calls"] == 2           # no Talk, no decision
    assert ideas.idea_page(host.ideas.root(), bug["slug"]).get("track") == parties["tech"]                 # it lies in the first party of its route
    two = host.command("ideas.add", {"text": "a new logo and a launch post", "general": True, "track": "general", "marks": ["orkboard/gui"]})
    assert two["route"] == [parties["product"], parties["design"]] and ideas.idea_page(host.ideas.root(), two["slug"]).get("track") == parties["product"]
    assert _row(host, two["slug"], "route")["offer"] == [parties["tech"]]                                    # the marks of System offer Tech, which the route lacks


def test_a_goal_code_cannot_route_is_routed_by_one_call_on_the_cheaper_tier_with_no_tools(host, parties, calls):
    calls.answer["route"] = json.dumps({"route": [parties["design"], parties["tech"], parties["release"], "nope"]})
    got = host.command("ideas.add", {"text": "make it nicer", "general": True})
    slug = got["slug"]
    assert got["route"] == []                                            # nothing yet: the call is made in the background
    _wait(host, slug)
    (call,) = calls
    assert "make it nicer" in call["prompt"] and call["tools"] is False and call["tier"] == "warrior" and call["effort"] == "low"
    assert call["budget"] == 0.15                                        # the step's cap, never under the tier's floor
    assert [r["party"] for r in _state(host, slug)["route"]] == [parties["design"], parties["tech"]]           # Release is never a step
    assert _state(host, slug)["route_how"]["by"] == "call" and _state(host, slug)["state"] == "routed"
    assert idea_spend.of_idea(host.ideas.state_dir, slug)["usd"] == pytest.approx(0.01)                     # its cost is the goal's
    assert _row(host, slug, "route")["route"][0]["party"] == parties["design"]


def test_a_call_that_names_none_or_fails_leaves_the_goal_on_the_first_party_to_change(host, parties, calls):
    calls.answer["route"] = "I cannot say"
    slug = host.command("ideas.add", {"text": "make it nicer", "general": True})["slug"]
    _wait(host, slug)
    assert [r["party"] for r in _state(host, slug)["route"]] == [parties["product"]] and _state(host, slug)["route_how"]["by"] == "default"

    def broken(*a, **k):
        raise RuntimeError("no model")
    host.ideas.keeper.call = broken
    again = host.command("ideas.add", {"text": "make it prettier", "general": True})["slug"]
    _wait(host, again)
    assert _state(host, again)["route"] and _state(host, again)["route_how"]["by"] == "default"


def test_the_route_is_edited_with_no_call_and_the_cost_is_answered_again(host, parties, calls):
    slug = host.command("ideas.add", {"text": "add a dark mode option", "general": True})["slug"]
    assert _state(host, slug)["route"][0]["party"] == parties["tech"]
    one = _row(host, slug, "route")["cost"]
    got = host.command("ideas.route_set", {"idea": slug, "route": [parties["design"], parties["tech"]]})
    assert calls == [] and [r["party"] for r in got["route"]] == [parties["design"], parties["tech"]] and got["cost"]["calls"] == 8
    assert got["cost"]["usd_high"] > one["usd_high"] and got["short"] is False and got["changed"] is False
    assert _row(host, slug, "route")["cost"] == got["cost"] and _state(host, slug)["route_how"]["by"] == "person"
    host.command("ideas.route_set", {"idea": slug, "route": [{"party": parties["design"]}]})              # a party taken off
    assert [r["party"] for r in _state(host, slug)["route"]] == [parties["design"]]
    for wanted, why in (([parties["release"]], "Release is never a step"), ([], "needs a party"), (["nope"], "That party is gone")):
        with pytest.raises(CommandError, match=why):
            host.command("ideas.route_set", {"idea": slug, "route": wanted})
    with pytest.raises(CommandError, match="gone"):
        host.command("ideas.route_set", {"idea": "nope", "route": [parties["tech"]]})
    assert calls == []


def test_talk_sets_the_state_and_hands_the_goal_to_the_keepers_talk_when_it_has_one(host, parties, calls, monkeypatch):
    slug = host.command("ideas.add", {"text": "add a dark mode option", "track": parties["tech"]})["slug"]
    went = []
    monkeypatch.setattr(host.ideas.keeper, "talk", lambda s: went.append((s, _state(host, s)["state"])), raising=False)       # part D's seam
    assert host.command("ideas.talk", {"idea": slug}) == {"ok": True}
    assert went == [(slug, "talk")] and calls == [] and _state(host, slug)["state"] == "talk"
    said = _state(host, slug)["route_how"]
    assert said["said"] == goal_route.cost_of(host.ideas.root(), host.ideas.state_dir, _state(host, slug)) and said["changed"] is False
    assert _row(host, slug, "route") is None and _row(host, slug, "start") is None
    node = next(i for i in host.command("ideas.board")["ideas"] if i["slug"] == slug)
    assert node["place"] == "table" and node["asks_you"] is False
    with pytest.raises(CommandError, match="no route to answer"):
        host.command("ideas.talk", {"idea": slug})                                                          # Talk is pressed once


def test_talk_is_the_keepers_now_it_calls_the_leaders_of_the_route_and_does_not_draft_the_goal(host, parties, calls):
    slug = host.command("ideas.add", {"text": "add a dark mode option", "track": parties["tech"]})["slug"]
    assert hasattr(host.ideas.keeper, "talk")                                                              # part D is in this build
    host.command("ideas.talk", {"idea": slug})
    _wait(host, slug)
    assert not any("write its spec straight away" in c["prompt"] for c in calls)                          # no draft: the leaders are heard
    assert [c["step"] for c in calls] == ["talk_round", "talk_round"] and all(c["tools"] is False for c in calls)       # an answer that says no stance is tried once more
    assert _state(host, slug)["state"] == "routed" and "did not answer" in _state(host, slug)["error"]    # and fails the round back to its route card


def test_a_step_added_after_talk_brings_the_start_row_with_the_old_cost_beside_the_new(host, parties, calls, monkeypatch):
    slug = host.command("ideas.add", {"text": "add a dark mode option", "track": parties["tech"]})["slug"]
    monkeypatch.setattr(host.ideas.keeper, "talk", lambda s: None, raising=False)
    host.command("ideas.talk", {"idea": slug})
    was = _state(host, slug)["route_how"]["said"]
    got = host.command("ideas.route_set", {"idea": slug, "route": [parties["tech"], parties["design"]]})
    assert got["changed"] is True
    row = _row(host, slug, "start")
    assert row["was"] == was and row["cost"]["calls"] > was["calls"] and row["cost"]["usd_high"] > was["usd_high"] and "cost" in row
    node = next(i for i in host.command("ideas.board")["ideas"] if i["slug"] == slug)
    assert node["place"] == "table" and node["asks_you"] is True                                           # on the table, asking
    back = host.command("ideas.route_set", {"idea": slug, "route": [parties["tech"]]})                      # back to the route it was told
    assert back["changed"] is False and _row(host, slug, "start") is None
    host.command("ideas.route_set", {"idea": slug, "route": [parties["tech"], parties["design"]]})
    assert host.command("ideas.start", {"idea": slug}) == {"ok": True}                                      # `ideas.start` answers the row
    assert _row(host, slug, "start") is None and _state(host, slug)["route_how"]["said"]["calls"] == row["cost"]["calls"]
    with pytest.raises(CommandError, match="no plan yet"):
        host.command("ideas.start", {"slug": slug})                                                         # the plan's start is as it was


def test_later_by_itself_is_offered_only_when_the_limits_run_low_and_talk_starts_at_the_reset(host, parties, calls, monkeypatch):
    slug = host.command("ideas.add", {"text": "add a dark mode option", "track": parties["tech"]})["slug"]
    with pytest.raises(CommandError, match="only when the limits run low"):
        host.command("ideas.route_later", {"idea": slug})
    reset = dt.datetime.now() + dt.timedelta(hours=2)
    rows = [Limit("claude", "", "session", 0.1, reset)]                                                    # 0.1 ≤ the reserve
    monkeypatch.setattr(host, "limits", lambda: rows)
    assert _row(host, slug, "route")["low"] is True
    went = []
    monkeypatch.setattr(host.ideas.keeper, "talk", lambda s: went.append(s), raising=False)
    got = host.command("ideas.route_later", {"idea": slug})
    assert got["ok"] is True and _state(host, slug)["held_until"] == got["held_until"] and _state(host, slug)["state"] == "routed"
    node = next(i for i in host.command("ideas.board")["ideas"] if i["slug"] == slug)
    assert (node["place"], node["waits_as"]) == ("deck", "reset") and _row(host, slug, "route") is None      # waits in the deck, nothing to decide
    host.ideas.route_tick(time.monotonic())
    assert went == [] and _state(host, slug)["state"] == "routed"                                          # before the reset: nothing
    ideas.save_state(host.ideas.state_dir, slug, held_until=(dt.datetime.now() - dt.timedelta(minutes=1)).isoformat(timespec="seconds"))
    host.ideas.route_tick(time.monotonic() + 100)
    assert went == [] and _state(host, slug)["held_until"] > dt.datetime.now().isoformat(timespec="seconds")   # the reserve is spent again: it waits for the next reset
    rows[:] = []                                                                                           # the window is back
    ideas.save_state(host.ideas.state_dir, slug, held_until=(dt.datetime.now() - dt.timedelta(minutes=1)).isoformat(timespec="seconds"))
    host.ideas.route_tick(time.monotonic() + 200)
    assert went == [slug] and _state(host, slug)["state"] == "talk" and _state(host, slug)["held_until"] == ""


def test_the_short_ways_start_skips_talk_and_the_decision_and_a_bug_without_a_failure_goes_to_talk(host, parties, calls, monkeypatch):
    went = []
    monkeypatch.setattr(host.ideas.keeper, "sections", lambda s: went.append(("sections", s)), raising=False)       # part E's seam
    monkeypatch.setattr(host.ideas.keeper, "talk", lambda s: went.append(("talk", s)), raising=False)             # part D's
    failing = host.command("ideas.add", {"text": "Saving crashes, tests/test_save.py::test_it FAILED"})["slug"]
    assert host.command("ideas.route_start", {"idea": failing}) == {"ok": True}
    assert went == [("sections", failing)] and _state(host, failing)["state"] == "sections"
    reported = host.command("ideas.add", {"text": "Saving crashes when the file is empty"})["slug"]
    assert _state(host, reported)["route_how"]["short"] is True and _state(host, reported)["route_how"]["reproduces"] is False
    host.command("ideas.route_start", {"idea": reported})                                                  # nothing to start from: Talk is the diagnosis
    assert went[-1] == ("talk", reported) and _state(host, reported)["state"] == "talk" and _state(host, reported)["route_how"]["short"] is True
    long = host.command("ideas.add", {"text": "add a dark mode option", "track": parties["tech"]})["slug"]
    with pytest.raises(CommandError, match="Only the short way"):
        host.command("ideas.route_start", {"idea": long})
    again = host.command("ideas.add", {"text": "Saving crashes, tests/test_save.py::test_it FAILED"})["slug"]
    host.command("ideas.talk", {"idea": again})                                                            # *The long way*
    assert _state(host, again)["route_how"]["short"] is False and went[-1] == ("talk", again)
    assert calls == []


def test_a_goal_kept_on_hold_and_a_pitch_are_not_routed(host, parties, calls):
    held = host.command("ideas.add", {"text": "add a dark mode option", "track": parties["tech"], "hold": True})
    assert _state(host, held["slug"])["state"] == "raw" and "route" not in held and _state(host, held["slug"])["queue"] == "hold"
    root = host.ideas.root()
    ideation = _party(host, "Ideation", "investor", ["skeptic"], "product")
    pitch = host.command("ideas.add", {"text": "a pitch about a thing", "track": ideation})
    assert _state(host, pitch["slug"])["state"] != "routed" and "route" not in pitch
    assert ideas.idea_page(root, held["slug"]) is not None
