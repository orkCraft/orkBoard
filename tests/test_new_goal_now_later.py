"""Spec 150 F.2 (decisions §254.9) on the host: the new goal's card sends **Now** (`ideas.add` `now: true`: Talk starts at once when the limits allow and the route's cost fits the window,
else the route card stays) or **Later** (`later: true`: routed and laid in line at the Board's hour, whatever the limits). The model call is stubbed."""
from __future__ import annotations

import datetime as dt
import sys

import pytest

from orkboard.gui.board_host import Orkboard
from orkboard.sources.limits import Limit
from tests.test_gui_route import _party, _row, _state  # noqa: F401


@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


@pytest.fixture
def tech(host, monkeypatch) -> str:
    monkeypatch.setattr(host.ideas.keeper, "talk", lambda s: None, raising=False)
    return _party(host, "Tech", "architect", ["grunt", "tester"], "engineering")


def _add(host, tech, **more):
    return host.command("ideas.add", {"text": "add a dark mode option", "track": tech, **more})


def test_now_starts_talk_at_once_when_the_cost_fits_the_window(host, tech):
    got = _add(host, tech, now=True)
    assert got["talk"] is True and _state(host, got["slug"])["state"] == "talk"
    assert _row(host, got["slug"], "route") is None


def test_now_leaves_the_route_card_when_the_cost_is_over_what_the_window_holds(host, tech, monkeypatch):
    monkeypatch.setattr(host.ideas, "fits_window", lambda *a, **k: False)
    got = _add(host, tech, now=True)
    assert got["talk"] is False and _state(host, got["slug"])["state"] == "routed"
    assert _row(host, got["slug"], "route") is not None, "the route card asks, with its cost"


def test_now_leaves_the_route_card_while_the_limits_run_low(host, tech, monkeypatch):
    monkeypatch.setattr(host, "limits", lambda: [Limit("claude", "", "session", 0.1, dt.datetime.now() + dt.timedelta(hours=2))])
    got = _add(host, tech, now=True)
    assert got["talk"] is False and _state(host, got["slug"])["state"] == "routed" and _row(host, got["slug"], "route") is not None


def test_later_lays_the_goal_in_line_whatever_the_limits(host, tech, monkeypatch):
    reset = dt.datetime.now() + dt.timedelta(hours=3)
    monkeypatch.setattr(host, "limits", lambda: [Limit("claude", "", "session", 0.9, reset)])        # plentiful: the route card's *Later, by itself* is refused here
    got = _add(host, tech, later=True)
    st = _state(host, got["slug"])
    assert got["talk"] is False and st["state"] == "routed" and st["held_until"] == got["held_until"] and st["held_for"] == ""
    assert dt.datetime.fromisoformat(st["held_until"]) > dt.datetime.now()
    node = next(i for i in host.command("ideas.board")["ideas"] if i["slug"] == got["slug"])
    assert (node["place"], node["waits_as"]) == ("deck", "reset") and _row(host, got["slug"], "route") is None


def test_later_with_no_limits_read_still_lays_it_in_line(host, tech):
    got = _add(host, tech, later=True)
    assert _state(host, got["slug"])["held_until"] and _state(host, got["slug"])["state"] == "routed"

