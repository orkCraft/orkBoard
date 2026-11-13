"""Spec 144 A (docs/specs/144-a-specs-wait-and-a-change-through-the-orkmaster.md; decisions §224.3, §225.1): the look's wait on the host, the model call and the runner stubbed
(tests/test_board_35.py's), the clock a fake one: `Give me time to look` (`look_wait`: 30m · 2h · tonight · none, 2 h at first, the project's), a spec made waits for it before its plan
is passed by itself, `look_tick` ends it at its clock time, a press passes at once."""
from __future__ import annotations

import datetime as dt
import time

import pytest

from orkboard import settings
from orkboard.gui.board_host import CommandError
from orkboard.realm import event_log, idea_target, ideas, look_wait, spec_change
from tests.test_board_35 import _events, _goal, _sent, _wait, host, model, runner  # noqa: F401  (fixtures)

NOW = dt.datetime(2026, 11, 4, 12, 0, 0).timestamp()


@pytest.fixture
def clock(host, monkeypatch):
    """The host's wall clock, set by the test: `clock.now = …`."""
    class Clock:
        now = NOW
    monkeypatch.setattr(host.ideas, "_wall", lambda: Clock.now)
    monkeypatch.setattr(idea_target, "in_night", lambda spec, now=None: False)
    return Clock


def made(host, text="safe") -> str:
    """A goal sent and drafted to its plan (low risk, normal priority: the board would start it by itself)."""
    g = _goal(host)
    slug = _sent(host, text, g)["slug"]
    _wait(host, slug)
    return slug


def plan_of(host, slug):
    return ideas.plan(host.ideas.state_dir, slug)


def look(host, choice):
    return host.command("ideas.board_set", {"look_wait": choice})


# -- the setting (A.1) ---------------------------------------------------------------------------------------------------------

def test_the_setting_is_2h_at_first_the_projects_cleaned_and_refused_in_plain_words(host):
    assert settings.IDEAS["look_wait"] == "2h" and "look_wait" in settings.BOARD
    assert settings.clean_ideas({})["look_wait"] == "2h" and settings.clean_ideas({"look_wait": "soon"})["look_wait"] == "2h"
    assert [settings.clean_ideas({"look_wait": c})["look_wait"] for c in ("30m", "2h", "tonight", "none")] == ["30m", "2h", "tonight", "none"]
    assert host.command("ideas.board")["look_wait"] == "2h"
    assert look(host, "none")["look_wait"] == "none" and host.command("ideas.board")["look_wait"] == "none"
    assert settings.board_of(host.repo_root, None)["look_wait"] == "none"          # the project's board.json
    with pytest.raises(CommandError, match="Give me time to look is 30 min, 2 h, until tonight or do not wait"):
        look(host, "soon")
    assert host.command("ideas.board")["look_wait"] == "none"


# -- when it applies (A.2) -----------------------------------------------------------------------------------------------------



def test_30m_writes_the_clock_time_1800_s_ahead_and_passes_nothing(host, model, runner, clock):
    look(host, "30m")
    slug = made(host)
    plan = plan_of(host, slug)
    assert runner.started == [] and plan.get("passed_at") is None and ideas.state(host.ideas.state_dir, slug)["state"] == "plan"
    assert plan["look_until"] == NOW + 1800 and plan["start_at"] == look_wait.iso(NOW + 1800) == "2026-11-04T12:30:00"
    (told,) = _events(host, event_log.LOOK_WAITS)
    assert told["idea"] == slug and told["until"] == NOW + 1800
    node = next(n for n in host.command("ideas.board")["ideas"] if n["slug"] == slug)
    assert node["look_until"] == NOW + 1800 and node["start_at"] == "2026-11-04T12:30:00" and node["place"] != "deck"      # a clock time on the table, not put off to a reset
    assert host.ideas.autostart(slug) == "look" and plan_of(host, slug)["look_until"] == NOW + 1800        # decided again: the same wait, not a new one


def test_autostart_off_still_waits_for_the_person_and_writes_no_look(host, model, runner, clock):
    host.command("ideas.board_set", {"autostart": False})
    slug = made(host)
    assert runner.started == [] and "look_until" not in plan_of(host, slug) and host.ideas.autostart(slug) == "wait"


def test_a_press_passes_at_once_and_drops_the_wait(host, model, runner, clock):
    slug = made(host)
    assert runner.started == [] and plan_of(host, slug)["look_until"]
    host.command("ideas.start_now", {"slug": slug})
    plan = plan_of(host, slug)
    assert runner.started == [slug] and plan["passed_by"] == "person" and "look_until" not in plan and plan["start_at"] is None
    other = made(host, "another")
    host.command("ideas.start", {"slug": other})
    assert plan_of(host, other)["passed_by"] == "person" and "look_until" not in plan_of(host, other)


# -- when it ends (A.3) --------------------------------------------------------------------------------------------------------

def test_look_tick_before_the_time_passes_nothing_and_after_it_passes_the_plan(host, model, runner, clock):
    look(host, "30m")
    slug = made(host)
    clock.now = NOW + 1799
    assert host.ideas.look_tick(clock.now) == 0 and runner.started == []
    clock.now = NOW + 1801
    assert host.ideas.look_tick(clock.now) == 1 and runner.started == [slug]
    plan = plan_of(host, slug)
    assert plan["passed_by"] == "auto" and "look_until" not in plan and plan["start_at"] is None
    (ended,) = _events(host, event_log.LOOK_ENDED)
    assert ended["idea"] == slug and ended["how"] == "started"
    clock.now += 600
    assert host.ideas.look_tick(clock.now) == 0                       # nothing twice


def test_work_at_night_on_and_the_night_closed_the_plan_is_held_for_the_night_when_the_look_ends(host, model, runner, clock):
    look(host, "30m")
    host.command("ideas.board_set", {"work_at_night": True})
    slug = made(host)
    assert runner.started == [] and "held_for_night" not in plan_of(host, slug)          # the look first
    clock.now = NOW + 2000
    host.ideas.look_tick(clock.now)
    plan = plan_of(host, slug)
    assert runner.started == [] and plan["held_for_night"] is True and plan["start_at"] == "night" and plan.get("passed_at") is None
    assert _events(host, event_log.LOOK_ENDED)[0]["how"] == "night"


# -- held while it is being changed (A.4) --------------------------------------------------------------------------------------

def test_a_change_open_on_the_goal_makes_the_tick_skip_it(host, model, runner, clock):
    look(host, "30m")
    slug = made(host)
    spec_change.put(host.ideas.state_dir, slug, {"id": "s1", "idea": slug, "status": "asking"})
    clock.now = NOW + 5000
    assert host.ideas.look_tick(clock.now) == 0 and runner.started == []
    spec_change.drop(host.ideas.state_dir, slug, "s1")
    clock.now += 10
    assert host.ideas.look_tick(clock.now) == 1 and runner.started == [slug]



def test_tonight_is_the_nights_next_start_today_or_tomorrow(host):
    noon = dt.datetime(2026, 11, 4, 12, 0).timestamp()
    assert look_wait.until("tonight", noon, "22:30-06:00") == dt.datetime(2026, 11, 4, 22, 30).timestamp()
    assert look_wait.until("tonight", noon, "01:00-07:00") == dt.datetime(2026, 11, 5, 1, 0).timestamp()       # tomorrow's: today's has gone
    late = dt.datetime(2026, 11, 4, 23, 0).timestamp()
    assert look_wait.until("tonight", late, "22:30-06:00") == dt.datetime(2026, 11, 5, 22, 30).timestamp()
    assert look_wait.until("none", noon) is None and look_wait.until("2h", noon) == noon + 7200
