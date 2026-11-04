"""Spec 130 E.3 (decisions §239.3, named by §247.2) on the host: **Hold** on the route card: a goal held is not sent to Talk by `route_auto`, not started by the queue after the reset, starts by the person's
**Talk**, and costs nothing. Its route card leaves the hand and the pile's list says *Held*. The model call is stubbed."""
from __future__ import annotations

import datetime as dt
import sys
import time
from pathlib import Path

import pytest

from orkboard.gui.board_host import CommandError, Orkboard
from orkboard.realm import event_log, ideas
from orkboard.sources.limits import Limit
from tests.test_gui_route import _party, _row, _state  # noqa: F401


@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


@pytest.fixture
def tech(host) -> str:
    return _party(host, "Tech", "architect", ["grunt", "tester"], "engineering")


@pytest.fixture
def goal(host, tech, monkeypatch) -> str:
    """A goal at its route card: Talk by itself is kept from sending it on, as a limit would."""
    monkeypatch.setattr("orkboard.gui.ideas_route.AUTO_TALK", False)
    return host.command("ideas.add", {"text": "add a dark mode option", "track": tech})["slug"]


def test_hold_puts_the_goal_by_with_nothing_spent_and_its_route_card_leaves_the_hand(host, goal, monkeypatch):
    spent = []
    monkeypatch.setattr(host.ideas.keeper, "call", lambda *a, **k: spent.append(a) or ("", 0, 0, ""))
    assert _row(host, goal, "route") is not None
    assert host.command("ideas.route_hold", {"idea": goal}) == {"ok": True}
    st = _state(host, goal)
    assert (st["state"], st["held_for"], st["held_until"]) == ("routed", "hold", "")
    assert _row(host, goal, "route") is None, "the person's move is no longer waiting in the hand"
    node = next(i for i in host.command("ideas.board")["ideas"] if i["slug"] == goal)
    assert (node["place"], node["waits_as"], node["asks_you"], node["held_for"]) == ("deck", "held", False, "hold"), "it asks nothing, and the page can say Held"
    assert spent == []
    assert any(e.get("event") == event_log.ROUTE_HELD and e.get("idea") == goal for e in event_log.read(Path(host.repo_root)))


def test_a_held_goal_is_not_sent_to_talk_by_itself(host, goal, monkeypatch):
    monkeypatch.setattr("orkboard.gui.ideas_route.AUTO_TALK", True)
    host.command("ideas.route_hold", {"idea": goal})
    assert host.ideas.route_stop(goal) == "it is held"
    assert host.ideas.route_auto(goal) is False and _state(host, goal)["state"] == "routed"


def test_the_queue_after_the_reset_does_not_start_a_held_goal(host, goal, monkeypatch):
    host.command("ideas.route_hold", {"idea": goal})
    went = []
    monkeypatch.setattr(host.ideas.keeper, "talk", lambda s: went.append(s), raising=False)
    monkeypatch.setattr(host, "limits", lambda: [Limit("claude", "", "session", 0.9, dt.datetime.now() + dt.timedelta(hours=2))])
    host.ideas.route_tick(time.monotonic() + 1000)
    assert went == [] and _state(host, goal)["state"] == "routed" and _state(host, goal)["held_for"] == "hold"


def test_talk_starts_a_held_goal_and_clears_the_hold(host, goal, monkeypatch):
    host.command("ideas.route_hold", {"idea": goal})
    went = []
    monkeypatch.setattr(host.ideas.keeper, "talk", lambda s: went.append(s), raising=False)
    assert host.command("ideas.talk", {"idea": goal})["ok"] is True
    st = _state(host, goal)
    assert went == [goal] and (st["state"], st["held_for"]) == ("talk", "")


def test_hold_is_refused_for_a_goal_not_at_its_route_card_and_for_one_that_is_gone(host, goal, monkeypatch):
    monkeypatch.setattr(host.ideas.keeper, "talk", lambda s: None, raising=False)
    host.command("ideas.talk", {"idea": goal})
    with pytest.raises(CommandError, match="no route to answer"):
        host.command("ideas.route_hold", {"idea": goal})
    with pytest.raises(CommandError, match="That goal is gone"):
        host.command("ideas.route_hold", {"idea": "no-such-goal"})


def test_a_goal_put_off_by_later_is_no_held_goal(host, goal, monkeypatch):
    monkeypatch.setattr(host, "limits", lambda: [Limit("claude", "", "session", 0.1, dt.datetime.now() + dt.timedelta(hours=2))])
    host.command("ideas.route_later", {"idea": goal})
    st = _state(host, goal)
    assert st["held_until"] and st["held_for"] == ""


def test_the_cards_word_is_hold_and_never_keep_it():
    src = (Path(ideas.__file__).parent.parent / "gui/static/js/hand/routecard.js").read_text(encoding="utf-8")
    assert ">Hold</button>" in src and "Nothing starts it until you press Talk" in src
    assert "Keep it" not in src
