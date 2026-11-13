"""Spec 44 A (docs/specs/44-week-pace.md §1–§4, Tests → A): the week's pace, the reserve per window, `week_reset`, the Map's waits and This week.
Code, no model. The Board's Low work by the pace, the night and the gate's night are gone (spec 99 §3)."""
from __future__ import annotations

import datetime as dt
import json
import time

import pytest

from orkboard.gui.board_host import Orkboard
from orkboard.realm import event_log, idea_target, ideas
from orkboard.sources.limits import Limit

WEEK = 7 * 24 * 3600


def at(now: float, days: float = 0, hours: float = 0) -> dt.datetime:
    return dt.datetime.fromtimestamp(now + days * 86400 + hours * 3600)


def weekly(left: float, days: float, now: float | None = None) -> Limit:
    now = time.time() if now is None else now
    return Limit("claude", "", "weekly", left, at(now, days))


def session(left: float, hours: float, now: float | None = None) -> Limit:
    now = time.time() if now is None else now
    return Limit("claude", "", "session", left, at(now, hours=hours))


def night_around_now() -> str:
    """A night window the clock is inside, and one it is not (the Board reads the machine's time)."""
    n = dt.datetime.now()
    return f"{(n - dt.timedelta(hours=1)):%H:%M}-{(n + dt.timedelta(hours=1)):%H:%M}"


def day_around_now() -> str:
    n = dt.datetime.now()
    return f"{(n + dt.timedelta(hours=5)):%H:%M}-{(n + dt.timedelta(hours=6)):%H:%M}"


# -- §1: the week, its pace and the reserve per window ---------------------------------------------------------------

@pytest.mark.parametrize("left,expected", [(0.2857 + 0.10 + 0.001, "ahead"), (2 / 7 + 0.10, "ahead"), (2 / 7 + 0.0999, "even"), (2 / 7, "even"),
                                           (2 / 7 - 0.0001, "behind"), (0.0, "behind"), (1.0, "ahead")])
def test_the_pace_is_ahead_from_ten_points_above_the_share_to_come_behind_below_it_else_even(left, expected):
    now = 1_800_000_000.0
    assert idea_target.pace([weekly(left, 2, now)], now) == expected


def _old_reserve(limits, settings, now, provider="claude"):
    """The rule before spec 44 (`reserve_held`): the smallest window against one share."""
    from orkboard.realm import status
    left = idea_target.left_of(limits, provider)
    if left is None:
        return None
    night = idea_target.in_night(str((settings or {}).get("night") or "01:00-07:00"), dt.datetime.fromtimestamp(now))
    share = idea_target.reserve(settings, night)
    if left > share:
        return None
    return status.reset_of(limits, provider, now, share) or now + status.UNKNOWN_RESET_S


def test_the_hour_before_the_five_hours_come_back_eases_their_reserve_by_day_while_the_week_is_not_behind():
    now = time.time()
    day = {"night": day_around_now(), "reserve_day": 0.3, "reserve_night": 0.1}
    ahead = [weekly(0.9, 2, now)]                                       # the week is ahead of its pace
    rows = lambda hours: [session(0.2, hours, now), *ahead]             # noqa: E731
    assert idea_target.reserve_held(rows(3), day, now) is not None                                     # 0.2 ≤ the day's 0.3: held
    assert idea_target.reserve_held(rows(0.9), day, now) is None                                      # within the hour: the night's 0.1 is the share
    assert idea_target.reserve_held(rows(1.1), day, now) is not None                                  # a little more than an hour away: not yet
    assert idea_target.reserve_held([session(0.08, 0.5, now), *ahead], day, now) is not None          # still under the night's share
    even = [weekly(0.4, 2, now)]                                                                       # even: eased too
    assert idea_target.reserve_held([session(0.2, 0.5, now), *even], day, now) is None
    behind = [weekly(0.5, 6, now)]                                                                     # behind (0.5 < 6/7), above the reserve itself
    assert idea_target.pace(behind, now) == "behind"
    assert idea_target.reserve_held([session(0.2, 0.5, now), *behind], day, now) == pytest.approx(now + 0.5 * 3600, abs=1)       # not eased
    assert idea_target.reserve_held([session(0.2, 0.5, now)], day, now) is not None                    # no week read: today's rule
    night = {**day, "night": night_around_now()}
    assert idea_target.reserve_held([session(0.2, 0.5, now), *ahead], night, now) is None              # at night the share is the night's anyway
    assert idea_target.reserve_held([session(0.2, 3, now), weekly(0.9, 2, now)], {**night, "reserve_night": 0.25}, now) is not None


# -- §2: the host -----------------------------------------------------------------------------------------------

@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    return h


def _add(host, text, **more):
    root = host.ideas.root()
    goal = next((t["slug"] for t in ideas.tracks(root, make=False) if t["slug"] != "general"), None) or ideas.add_track(root, "First goal")
    return host.command("ideas.add", {"text": text, "track": goal, **more})["slug"]


def _plan(host, slug, state="plan"):
    ideas.save_plan(host.ideas.state_dir, slug, {"idea": slug, "made_at": "2026-10-20T09:00:00", "passed_at": None, "todos": [],
                                                 "tasks": [{"id": "k1", "title": "Do it", "brief": "b", "tier": "warrior", "after": [], "state": "ready"}]})
    ideas.save_state(host.ideas.state_dir, slug, state=state)


def test_this_week_carries_the_week_and_what_the_last_one_left_unused(host):
    now = time.time()
    assert host.command("ideas.week_work")["week"] is None and host.command("ideas.week_work")["last_unused"] is None
    host.limits.rows = [weekly(0.55, 2, now)]
    got = host.command("ideas.week_work")
    assert got["week"]["left"] == 0.55 and got["week"]["pace"] == "ahead" and got["week"]["rest"] == pytest.approx(2 / 7, abs=0.01)
    assert got["week"]["reset"] == pytest.approx(now + 2 * 86400, abs=5)
    event_log.record(host.repo_root, event_log.WEEK_RESET, left=0.5, provider="claude")
    event_log.record(host.repo_root, event_log.WEEK_RESET, left=0.3, provider="claude")
    assert host.command("ideas.week_work")["last_unused"] == 0.3                                    # the newest
    json.dumps(got)


def test_a_chip_of_a_task_of_a_plan_that_went_by_day_says_pace(host):
    state = host.ideas.state_dir
    s = _add(host, "went by day", priority="low")
    _plan(host, s, "working")
    ideas.edit_plan(state, s, lambda p: p.update(by_pace=True, passed_at="x", tasks=[{**p["tasks"][0], "state": "running"}]))
    other = _add(host, "went at once", priority="high")
    _plan(host, other, "working")
    ideas.edit_plan(state, other, lambda p: p.update(passed_at="x", tasks=[{**p["tasks"][0], "state": "running"}]))
    chips = [c for b in host.command("ideas.agents")["roles"] for c in b["chips"] if c.get("task")]
    assert {c["idea"]: c.get("pace") for c in chips} == {s: True, other: None}

