"""Spec 138 B and spec 139 C.1 (docs/specs/138-the-day-read-from-the-resets.md, docs/specs/139-the-die-the-door-and-the-bug.md; decisions §245.4–5, §246.4): the person's hours and the presence read from them
(`realm/hours.py`, the host's `presence` and `presence.set`), a step that asks laid in the hours while the person is Away and a step that asks nothing not, the push while Away, and with no hours set today's behaviour."""
from __future__ import annotations

import datetime as dt
import json
import sys
import time

import pytest

from orkboard.gui.board_host import Orkboard
from orkboard.realm import goal_route, goal_team, hours, ideas, library
from orkboard.sources.limits import Limit

MON = dt.datetime(2026, 11, 2)                                                       # a Monday
EVENINGS = {"hours": [{"days": [0, 1, 2, 3, 4], "from": "19:00", "to": "23:00"}]}
DAY = dt.datetime(2026, 11, 3, 12, 0)                                                # a Tuesday noon: Away under EVENINGS


def at(day, hour, minute=0):
    return MON.replace(day=MON.day + day, hour=hour, minute=minute)


# -- presence from the hours and a hold (pure) ---------------------------------------------------------------------------------------------------

def test_presence_is_here_inside_the_hours_and_away_outside_them_with_the_next_edge():
    away = hours.presence(EVENINGS, at(1, 12))
    assert away == {"here": False, "until": "2026-11-03T19:00", "held": False}
    here = hours.presence(EVENINGS, at(1, 20))
    assert here == {"here": True, "until": "2026-11-03T23:00", "held": False}


def test_a_press_holds_the_other_state_until_the_hours_next_edge_and_the_hold_ends_by_itself():
    hold = hours.hold_for(EVENINGS, True, at(1, 12))                                   # Away at noon, the person says Here: held until 19:00
    assert hold == {"here": True, "until": "2026-11-03T19:00"}
    s = {**EVENINGS, "presence": hold}
    assert hours.presence(s, at(1, 12)) == {"here": True, "until": "2026-11-03T19:00", "held": True}
    assert hours.presence(s, at(1, 18, 59))["held"] is True
    assert hours.presence(s, at(1, 19)) == {"here": True, "until": "2026-11-03T23:00", "held": False}, "the hours say Here too: the hold is over"
    assert hours.presence(s, at(1, 23, 30))["here"] is False, "and it does not come back"
    held_away = hours.hold_for(EVENINGS, False, at(1, 20))                             # Here at 20:00, the person says Away: held until 23:00
    assert held_away == {"here": False, "until": "2026-11-03T23:00"} and hours.presence({**EVENINGS, "presence": held_away}, at(1, 21))["here"] is False
    assert hours.hold_for(EVENINGS, True, at(1, 20)) is None and hours.hold_for(EVENINGS, False, at(1, 12)) is None, "a press that agrees with the hours only lifts a hold"


# -- the host: the snapshot, the command and the setting -----------------------------------------------------------------------------------------

@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def around_now(host, here: bool):
    """Hours that make the person Here (a span round now) or Away (a span hours ahead), every day of the week."""
    now = dt.datetime.now().replace(second=0, microsecond=0)
    a, b = (now - dt.timedelta(minutes=30), now + dt.timedelta(minutes=30)) if here else (now + dt.timedelta(hours=3), now + dt.timedelta(hours=4))
    host.command("ideas.board_set", {"hours": [{"days": [0, 1, 2, 3, 4, 5, 6], "from": f"{a:%H:%M}", "to": f"{b:%H:%M}"}]})


def test_the_door_tells_the_faces_when_it_turns(host):
    told = []
    host.on_change = lambda: told.append(1)
    host._door_tick()
    assert told == []
    host.command("presence.set", {"here": False})
    told.clear()
    host._door_tick()
    assert told == [1]


# -- Away lays a step that asks in the hours; a step that asks nothing goes on ------------------------------------------------------------------

def _party(host, title, leader, team, craft):
    root, state = host.ideas.root(), host.ideas.state_dir
    library.install(state, [s for s in (*team, leader) if library.get(s) is not None])
    slug, _new = ideas.save_goal(root, None, title, "About " + title, None, "normal", craft=craft)
    goal_team.set_team(root, slug, list(team), leader=leader)
    return slug


@pytest.fixture
def tech(host):
    host.ideas.keeper.call = lambda tier, prompt, effort="", budget=None: (json.dumps({"summary": "", "questions": [], "title": "A goal"}), 0.01, 10, "")
    return _party(host, "Tech", "architect", ["grunt", "tester"], "engineering")


@pytest.fixture
def went(host, monkeypatch):
    seen = []
    monkeypatch.setattr(host.ideas.keeper, "talk", lambda s: seen.append(s), raising=False)
    return seen


def _state(host, slug):
    return ideas.state(host.ideas.state_dir, slug)


def _due(host, slug):
    ideas.save_state(host.ideas.state_dir, slug, held_until=(dt.datetime.now() - dt.timedelta(minutes=1)).isoformat(timespec="seconds"))


def test_away_a_goal_put_off_whose_reset_passed_does_not_start_talk_and_waits_for_the_hours(host, tech, went, monkeypatch):
    slug = host.command("ideas.add", {"text": "a goal to talk over", "track": tech})["slug"]
    _due(host, slug)
    around_now(host, here=False)
    host.ideas._route_at = float("-inf")
    host.ideas.route_tick(time.monotonic() + 1000)
    st = _state(host, slug)
    assert went == [] and st["state"] == "routed" and dt.datetime.fromisoformat(st["held_until"]) > dt.datetime.now() + dt.timedelta(hours=2), "laid at the hours' start (no reset is read)"
    assert hours.in_hours(host.ideas.settings_now(), dt.datetime.fromisoformat(st["held_until"]) + dt.timedelta(minutes=1)), "…inside the hours"


def test_a_goal_the_person_starts_by_hand_goes_at_once_even_when_away_and_a_step_that_asks_nothing_is_not_laid(host, tech, went):
    around_now(host, here=False)
    slug = host.command("ideas.add", {"text": "start this by hand", "track": tech})["slug"]
    assert _state(host, slug)["held_until"] == "", "adding it lays nothing: only what would start by itself waits"
    host.command("ideas.talk", {"idea": slug})
    assert went == [slug] and _state(host, slug)["state"] == "talk"
    short = host.command("ideas.add", {"text": "a second goal", "track": tech})["slug"]
    assert host.ideas.lay_in_hours([short]) is True and _state(host, short)["held_until"], "a step that asks (Talk) is laid"
    assert host.ideas.here() is False
    ideas.save_state(host.ideas.state_dir, short, held_until="")
    host.command("ideas.board_set", {"hours": []})
    assert host.ideas.lay_in_hours([short]) is False and _state(host, short)["held_until"] == "", "no hours: nothing is laid"


def test_the_wait_of_an_agreed_goal_keeps_its_time_while_away_when_each_result_waits_for_the_person(host, tech):
    from orkboard.realm import idea_ripe
    slug = host.command("ideas.add", {"text": "an agreed goal", "track": tech})["slug"]
    ideas.save_state(host.ideas.state_dir, slug, state="decided")
    idea_ripe._keep(host.ideas.state_dir, slug, {"left_s": 3.0, "seconds": 60, "risk": "low", "priority": "high", "held": False, "by": "", "why": ""})
    ran = []
    host.faces = lambda: 1
    host.ideas.ripe_end = lambda s: ran.append(s)
    around_now(host, here=False)
    host.command("ideas.board_set", {"review": True})
    now = time.monotonic()
    host.ideas.ripe_tick(now)
    host.ideas.ripe_tick(now + 10)
    assert ran == [] and idea_ripe.of(host.ideas.state_dir, slug)["left_s"] == 3.0, "away, with each result waiting for a look: the wait is kept"
    around_now(host, here=True)
    host.ideas.ripe_tick(now + 20)
    assert ran == [slug], "here: it runs out as before"
    host.command("ideas.board_set", {"hours": [], "review": False})


# -- the push while Away ------------------------------------------------------------------------------------------------------------------------


# -- the cost against the window --------------------------------------------------------------------------------------------------------------

def test_the_cost_of_a_goals_next_step_is_read_against_what_the_window_holds_above_the_reserve(host, tech, monkeypatch):
    slug = host.command("ideas.add", {"text": "a goal with a route", "track": tech})["slug"]
    st = _state(host, slug)
    cost = goal_route.cost_of(host.ideas.root(), host.ideas.state_dir, st, host.ideas.settings_now())
    mid = (cost["usd_low"] + cost["usd_high"]) / 2
    assert mid > 0
    settings = host.ideas.settings_now()
    wall = dt.datetime.now().replace(hour=12, minute=0, second=0, microsecond=0).timestamp()          # midday: the day's reserve, whatever the hour the suite runs at (the night's is another test's)
    monkeypatch.setattr("orkboard.sources.window_rate.shown", lambda machine: {"usd_per_pct": mid / 10})           # the goal costs 10 % of the window
    rows = lambda left: [Limit("claude", "", "session", left, dt.datetime.now() + dt.timedelta(hours=2))]            # noqa: E731
    assert host.ideas.fits_window(slug, st, rows(0.5), settings, wall) is True, "10 % against 20 % above the day's reserve"
    assert host.ideas.fits_window(slug, st, rows(0.35), settings, wall) is False, "10 % against 5 %"
    assert host.ideas.fits_window(slug, st, [], settings, wall) is True, "no limits read: nothing to read it against"
    monkeypatch.setattr("orkboard.sources.window_rate.shown", lambda machine: None)
    assert host.ideas.fits_window(slug, st, rows(0.35), settings, wall) is True, "no rate learnt: it goes, as before"
    monkeypatch.setattr("orkboard.sources.window_rate.shown", lambda machine: {"usd_per_pct": mid / 150})          # more than a whole window: it would never fit, so it is not held for ever
    assert host.ideas.fits_window(slug, st, rows(0.35), settings, wall) is True
