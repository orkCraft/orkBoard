"""Spec 120 B (docs/specs/120-a-goal-heard-and-thrown-to-a-side.md §2.1–§2.2, decisions §198.2) on the host: `ideas.add` of a routed goal goes to Talk by itself when nothing stops it, and keeps its
route card when the keeper may not run, the Claude window is spent, the week's limits run low or the route is paid; the short way keeps its card; a route a call found goes to Talk at the next
tick. The model call is stubbed (`keeper.call`) as in tests/test_gui_route.py, whose fixtures these are."""
from __future__ import annotations

import datetime as dt
import json
import time
from types import SimpleNamespace

import pytest

from orkboard.realm import goal_route, ideas
from orkboard.sources.limits import Limit
from tests.test_gui_route import _row, _state, _wait, calls, host, parties  # noqa: F401  (the fixtures and helpers of the route's tests)

pytestmark = pytest.mark.talks_by_itself              # tests/conftest.py: every other test keeps the route card first


@pytest.fixture
def handed(host, monkeypatch):
    """Where the goal goes on from its route: the keeper's Talk stubbed, `[(slug, state)]` of every goal handed to it."""
    went: list = []
    monkeypatch.setattr(host.ideas.keeper, "talk", lambda s: went.append((s, _state(host, s)["state"])), raising=False)
    return went


def test_a_routed_goal_goes_to_talk_by_itself_when_nothing_stops_it(host, parties, calls, handed):
    got = host.command("ideas.add", {"text": "add a dark mode option", "track": parties["tech"]})
    slug = got["slug"]
    assert got["talk"] is True and got["route"] == [parties["tech"]] and handed == [(slug, "talk")]               # the same command: no press of Talk
    st = _state(host, slug)
    assert st["state"] == "talk" and st["route_how"]["auto"] is True and st["route_how"]["changed"] is False
    assert st["route_how"]["said"] == goal_route.cost_of(host.ideas.root(), host.ideas.state_dir, st)               # told the cost, as the press would have
    assert _row(host, slug, "route") is None and calls == []                                                       # no route card; the keeper's Talk is the stub


def test_a_routed_goal_goes_to_talk_by_itself_for_real_and_its_route_stays_editable_while_it_talks(host, parties, calls):
    slug = host.command("ideas.add", {"text": "add a dark mode option", "track": parties["tech"]})["slug"]
    _wait(host, slug)
    assert [c["step"] for c in calls] == ["talk_round", "talk_round"] and all(c["tools"] is False for c in calls)    # the leaders are heard (the stub's answer says no stance: tried once more)
    st = _state(host, slug)
    assert st["state"] == "routed" and "did not answer" in st["error"]                                              # …and the round failed back to its route card, as a pressed Talk does


def test_a_step_added_after_talk_brings_the_start_row_and_taking_it_off_again_takes_it_away(host, parties, calls, handed):
    """The keeper's Talk is the stub's here and keeps no record, so Talk is not going: the edit is a step added after it (what is Talk's own while it runs: tests/test_idea_verdict.py)."""
    slug = host.command("ideas.add", {"text": "add a dark mode option", "track": parties["tech"]})["slug"]
    assert handed == [(slug, "talk")]
    got = host.command("ideas.route_set", {"idea": slug, "route": [parties["tech"], parties["design"]]})
    assert got["changed"] is True and _row(host, slug, "start") is not None and _state(host, slug)["state"] == "talk"
    got = host.command("ideas.route_set", {"idea": slug, "route": [parties["tech"]]})                               # taken off again: as it was told
    assert got["changed"] is False and _row(host, slug, "start") is None


def test_a_goal_sent_is_heard_with_no_press_and_the_leaders_questions_wait_in_the_hand(host, parties):
    def call(tier, prompt, effort="", budget=None):
        asked = {"stance": "For it", "questions": [{"ask": "Which first?", "choices": ["Web", "Phone"], "pick": 1, "why": "most are on phones"}]}
        return json.dumps(asked if host.ideas.keeper.measure()["step"] == "talk_round" else {}), 0.01, 10, ""

    host.ideas.keeper.call = call
    got = host.command("ideas.add", {"text": "add a dark mode option", "track": parties["tech"]})
    slug = got["slug"]
    _wait(host, slug)
    assert got["talk"] is True and _state(host, slug)["state"] == "talk" and _row(host, slug, "route") is None
    row = _row(host, slug, "talk")
    assert [q["q"] for q in row["questions"]] == ["Which first?"] and [s["party"] for s in row["stances"]] == [parties["tech"]]


@pytest.mark.parametrize("why", ["spend", "window", "limits", "paid", "off"])
def test_the_route_card_stays_when_the_keeper_may_not_run_the_window_is_spent_the_limits_are_low_or_the_route_is_paid(host, parties, calls, handed, monkeypatch, why):
    reset = dt.datetime.now() + dt.timedelta(hours=2)
    if why == "spend":
        monkeypatch.setattr(host.ideas.keeper, "_may_run", lambda: "Today's spend limit is reached: the keeper waits")
    elif why == "window":
        monkeypatch.setattr(host.ideas.keeper, "window_until", lambda: time.time() + 3600)
    elif why == "limits":
        monkeypatch.setattr(host, "limits", lambda: [Limit("claude", "", "session", 0.1, reset)])
    elif why == "paid":
        monkeypatch.setattr(host.ideas, "route_paid", lambda: True)
    else:
        monkeypatch.setattr("orkboard.gui.ideas_route.AUTO_TALK", False)
    got = host.command("ideas.add", {"text": "add a dark mode option", "track": parties["tech"]})
    slug = got["slug"]
    assert got["talk"] is False and handed == [] and calls == [] and _state(host, slug)["state"] == "routed"
    row = _row(host, slug, "route")                                                                                # its route card, as before
    assert row is not None and row["low"] is (why == "limits")
    host.command("ideas.talk", {"idea": slug})                                                                      # and Talk is still the person's press
    assert handed == [(slug, "talk")]


def test_a_route_every_ai_tool_is_out_for_is_paid_and_a_tool_billed_by_its_api_by_choice_is_not(host, parties, calls, handed, monkeypatch):
    slug = host.command("ideas.add", {"text": "add a dark mode option", "track": parties["tech"]})["slug"]
    assert handed == [(slug, "talk")] and host.ideas.route_paid() is False
    monkeypatch.setattr(host.ideas, "tool_now", lambda *a, **k: {"main": "claude", "now": None, "until": None, "moved_from": "claude"})        # every subscription is out
    assert host.ideas.route_paid() is True
    monkeypatch.setattr(host.ideas, "tool_now", lambda *a, **k: {"main": "claude", "now": "codex", "until": None, "moved_from": "claude"})      # moved onto a subscription
    assert host.ideas.route_paid() is False
    monkeypatch.setattr(host, "machine", SimpleNamespace(tools={"codex": SimpleNamespace(billing="api"), "claude": SimpleNamespace(billing="subscription")}), raising=False)
    assert host.ideas.route_paid() is True                                                                          # moved onto a tool billed by its API: the yes was asked for (spec 105)
    monkeypatch.setattr(host.ideas, "tool_now", lambda *a, **k: {"main": "codex", "now": "codex", "until": None, "moved_from": None})          # the Main tool, by the person's choice
    assert host.ideas.route_paid() is False


def test_the_short_way_keeps_its_route_card_a_bugs_way_is_the_persons_choice(host, parties, calls, handed):
    bug = host.command("ideas.add", {"text": "Saving crashes: Traceback (most recent call last):\n  File \"a.py\", line 1\nValueError: x"})
    slug = bug["slug"]
    assert bug["talk"] is False and handed == [] and _state(host, slug)["state"] == "routed" and _state(host, slug)["route_how"]["short"] is True
    row = _row(host, slug, "route")
    assert row is not None and row["short"] is True                                                                # *Start* or *Talk*, the person's
    assert host.ideas.route_stop(slug) == "the short way keeps its card"


def test_a_goal_kept_on_hold_or_put_off_does_not_go_to_talk_by_itself(host, parties, calls, handed):
    held = host.command("ideas.add", {"text": "add a dark mode option", "track": parties["tech"], "hold": True})
    assert "talk" not in held and handed == [] and _state(host, held["slug"])["state"] == "raw"
    slug = host.command("ideas.add", {"text": "add a light mode option", "track": parties["tech"]})["slug"]
    assert handed == [(slug, "talk")]
    other = host.command("ideas.add", {"text": "add a quiet mode option", "track": parties["tech"]})["slug"]
    ideas.save_state(host.ideas.state_dir, other, state="routed", held_until="2999-01-01T00:00:00")
    assert host.ideas.route_stop(other) == "it is put off" and host.ideas.route_auto(other) is False


def test_a_route_a_call_found_goes_to_talk_by_itself_at_the_next_tick_once_the_run_has_ended(host, parties, calls, handed):
    calls.answer["route"] = json.dumps({"route": [parties["design"], parties["tech"]]})
    got = host.command("ideas.add", {"text": "make it nicer", "general": True})
    slug = got["slug"]
    assert got["route"] == [] and "talk" not in got                                                                # the call is made in the background
    _wait(host, slug)
    assert [r["party"] for r in _state(host, slug)["route"]] == [parties["design"], parties["tech"]] and handed == []       # found; the run has ended
    host.ideas.route_tick(time.monotonic())
    assert handed == [(slug, "talk")] and _state(host, slug)["state"] == "talk"
    host.ideas.route_tick(time.monotonic() + 100)
    assert handed == [(slug, "talk")]                                                                              # once
