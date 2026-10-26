"""Spec 83 A (docs/specs/83-one-field-and-the-night-asked.md): the night is Low work's, on the person's one standing word,
`ideas.night_low` (null, true, false), set by `ideas.night_allow`. Code, no model (the model call stubbed)."""
from __future__ import annotations

import pytest

from orkboard import settings
from orkboard.gui.board_host import BoardPhone, CommandError
from orkboard.realm import event_log, ideas
from tests.test_board_35 import _events, _goal, _wait, host, model, runner  # noqa: F401  (fixtures)
from tests.test_idea_night import _goal as _party, keeper  # noqa: F401  (a fixture)
from tests.test_idea_draft import DRAFT, PLAN, Model


def _add(host, text="A goal", **more):
    root = host.ideas.root()
    goal = next((t["slug"] for t in ideas.tracks(root, make=False) if t["slug"] != "general"), None) or ideas.add_track(root, "First goal")
    return host.command("ideas.add", {"text": text, "track": goal, **more})


def _quiet(host, monkeypatch):
    monkeypatch.setattr(host.ideas.keeper, "draft", lambda slug: None)      # nothing is read: only where the goal waits matters here


def test_the_permission_is_asked_never_assumed_and_the_command_is_the_hosts_and_a_phones(host):
    assert "ideas.night_allow" in host.commands and BoardPhone.allowed(host, "ideas.night_allow", {})
    assert settings.IDEAS["night_low"] is None and settings.clean_ideas({})["night_low"] is None
    assert host.command("ideas.board")["night_low"] is None                       # what every Board has, older ones included
    assert [settings.clean_ideas({"night_low": v})["night_low"] for v in (True, False, None, "yes", 1)] == [True, False, None, None, None]
    assert "night_low" in settings.BOARD


def test_night_allow_is_set_and_said_and_kept_for_the_project(host):
    assert host.command("ideas.night_allow", {"allow": True}) == {"ok": True, "moved": 0}
    assert host.command("ideas.board")["night_low"] is True and settings.board_of(host.repo_root, None)["night_low"] is True
    assert host.command("ideas.night_allow", {"allow": False}) == {"ok": True, "moved": 0}
    assert host.command("ideas.board")["night_low"] is False
    for bad in ({}, {"allow": "yes"}, {"allow": None}, {"allow": 1}):
        with pytest.raises(CommandError):
            host.command("ideas.night_allow", bad)
    assert [(e["allow"], e["moved"], e["face"], e["device"]) for e in _events(host, "night_allowed")] == [
        (True, 0, "desktop", "desktop"), (False, 0, "desktop", "desktop")]
    host.command("ideas.night_allow", {"allow": True, "device": "phone"})
    assert _events(host, "night_allowed")[-1]["face"] == "phone"
    assert event_log.NIGHT_ALLOWED in event_log.EVENTS


def test_a_low_goal_waits_for_the_night_only_on_the_word_and_otherwise_goes_by_day(host, monkeypatch):
    _quiet(host, monkeypatch)
    assert _add(host, "unasked", priority="low")["queue"] == "now"                  # null: nothing goes at night
    host.command("ideas.night_allow", {"allow": False})
    assert _add(host, "no", priority="low")["queue"] == "now" and _add(host, "no too", priority="low", night=True)["queue"] == "now"
    host.command("ideas.night_allow", {"allow": True})
    assert _add(host, "yes", priority="low")["queue"] == "night" and _add(host, "mine", priority="low", night=True)["queue"] == "night"
    assert _add(host, "normal")["queue"] == "now" and _add(host, "kept", priority="low", hold=True)["queue"] == "hold"


def test_night_is_refused_without_low_and_never_puts_another_priority_to_the_night(host, monkeypatch):
    _quiet(host, monkeypatch)
    host.command("ideas.night_allow", {"allow": True})
    for priority in ("high", "normal", ""):
        with pytest.raises(CommandError, match="Only Low work waits for the night"):
            _add(host, "x", priority=priority, night=True)
    assert [ideas.state(host.ideas.state_dir, i["slug"])["queue"] for i in ideas.ideas(host.ideas.root())] == []


def test_tonight_on_a_held_goal_makes_it_low_and_asks_the_word(host, monkeypatch):
    _quiet(host, monkeypatch)
    slug = _add(host, "kept", priority="normal", hold=True)["slug"]
    with pytest.raises(CommandError, match="Low work may run at night is off"):
        host.command("ideas.queue", {"slug": slug, "queue": "night"})                        # null or false: refused, in words
    host.command("ideas.night_allow", {"allow": False})
    with pytest.raises(CommandError, match="Low work may run at night is off"):
        host.command("ideas.queue", {"slug": slug, "queue": "night"})
    assert ideas.idea_page(host.ideas.root(), slug).get("priority") == "normal"
    host.command("ideas.night_allow", {"allow": True})
    host.command("ideas.queue", {"slug": slug, "queue": "night"})
    assert ideas.idea_page(host.ideas.root(), slug).get("priority") == "low"
    assert ideas.state(host.ideas.state_dir, slug)["queue"] == "night"


def test_a_low_plan_of_low_risk_starts_by_day_without_the_word_and_at_night_with_it(host, model, runner):
    g = _goal(host, priority="low")
    for allow, start_at in ((None, None), (False, None), (True, "night")):
        if allow is not None:
            host.command("ideas.night_allow", {"allow": allow})
        slug = host.command("ideas.add", {"text": f"low and safe {allow}", "track": g, "priority": "low", "hold": True})["slug"]
        ideas.save_state(host.ideas.state_dir, slug, state="raw", queue="")
        host.ideas.keeper.draft_one(slug)
        plan = ideas.plan(host.ideas.state_dir, slug)
        assert plan["passed_by"] == "auto" and plan["start_at"] == start_at
        assert (slug in runner.started) == (start_at is None)


def test_setting_it_false_moves_what_waited_for_the_night_to_the_day(host, model, runner):
    g = _goal(host, priority="low")
    host.command("ideas.night_allow", {"allow": True})
    a = host.command("ideas.add", {"text": "waits", "track": g, "priority": "low", "hold": True})["slug"]
    ideas.save_state(host.ideas.state_dir, a, state="raw", queue="night", night_by="board")
    b = host.command("ideas.add", {"text": "kept", "track": g, "priority": "low", "hold": True})["slug"]       # held: not the night's
    c = host.command("ideas.add", {"text": "planned", "track": g, "priority": "low", "hold": True})["slug"]
    ideas.save_plan(host.ideas.state_dir, c, {"idea": c, "made_at": "x", "passed_at": "x", "start_at": "night", "start_at_by": "board",
                                              "todos": [], "tasks": [{"id": "k1", "title": "t", "brief": "b", "tier": "warrior", "after": [], "state": "ready"}]})
    ideas.save_state(host.ideas.state_dir, c, state="plan", queue="")
    assert host.command("ideas.night_allow", {"allow": False}) == {"ok": True, "moved": 2}
    _wait(host, a)
    assert ideas.state(host.ideas.state_dir, b)["queue"] == "hold"
    assert ideas.state(host.ideas.state_dir, a)["state"] in ("plan", "ready", "working") and ideas.state(host.ideas.state_dir, a)["queue"] != "night"
    assert ideas.plan(host.ideas.state_dir, c)["start_at"] is None and c in runner.started
    assert _events(host, "night_allowed")[-1]["moved"] == 2
    assert host.command("ideas.night_allow", {"allow": False})["moved"] == 0                    # nothing left


def test_null_leaves_the_queued_ones_queued_until_it_is_answered(host, monkeypatch):
    _quiet(host, monkeypatch)
    slug = _add(host, "queued before", priority="low", hold=True)["slug"]
    ideas.save_state(host.ideas.state_dir, slug, state="raw", queue="night", night_by="board")
    host.command("ideas.board")
    assert ideas.state(host.ideas.state_dir, slug)["queue"] == "night"


def test_a_taken_proposal_of_low_priority_goes_to_the_night_only_on_the_word(host, monkeypatch):
    _quiet(host, monkeypatch)
    g = _add(host, "first")["slug"] and next(t["slug"] for t in ideas.tracks(host.ideas.root(), make=False) if t["slug"] != "general")
    queues = []
    for allow in (None, True):
        if allow is not None:
            host.command("ideas.night_allow", {"allow": allow})
        s = ideas.add_idea(host.ideas.root(), "proposed", g, host.ideas.state_dir)
        ideas.save_state(host.ideas.state_dir, s, state="proposed", queue="")
        host.command("ideas.proposal", {"slug": s, "take": True, "priority": "low"})
        queues.append(ideas.state(host.ideas.state_dir, s)["queue"])
    assert queues == ["now", "night"]


# -- the night's own runs (§5) ------------------------------------------------------------------------------------

def _night_work(keeper):
    g = _party(keeper, "Table", links=["src/app.py"], summary="It lives in `docs/notes.md`.")
    low = ideas.add_idea(keeper.root, "a low idea", g, keeper.state, priority="low", queue="night")
    tonight = ideas.add_idea(keeper.root, "passed for tonight", g, keeper.state)
    ideas.save_plan(keeper.state, tonight, {"idea": tonight, "passed_at": "x", "start_at": "night", "tasks": [], "todos": []})
    ideas.save_state(keeper.state, tonight, state="plan")
    keeper.call = model = Model(draft=lambda p: {**DRAFT, "questions": []}, plan=PLAN, goal={"summary": "Again.", "questions": []},
                                propose={"proposals": [{"goal": g, "title": "Sort the table", "why": "People sort."}]})
    return low, tonight, model


@pytest.mark.parametrize("word", [None, False])
def test_without_the_word_the_night_runs_nothing(keeper, word):
    keeper.settings_now["night_low"] = word
    low, tonight, model = _night_work(keeper)
    counts = keeper.run_night("2026-10-25T01:00")
    assert counts == {"drafted": 0, "started": 0, "refreshed": 0, "proposed": 0, "held": 0}
    assert model.asked == [] and keeper.started == [] and ideas.state(keeper.state, low)["state"] == "raw"
    assert not keeper.night_allowed()


def test_with_the_word_the_night_runs_its_steps(keeper):
    keeper.settings_now["night_low"] = True
    low, tonight, model = _night_work(keeper)
    counts = keeper.run_night("2026-10-25T01:00")
    assert counts["drafted"] == 1 and counts["started"] == 1 and counts["proposed"] == 1 and keeper.started == [tonight]
    assert keeper.night_allowed()


@pytest.mark.parametrize("word,runs", [(None, False), (False, False), (True, True)])
def test_the_week_pace_by_day_goes_under_the_same_word(keeper, word, runs):
    import datetime as dt
    from orkboard.realm import idea_target
    keeper.settings_now["night_low"] = word
    keeper.settings_now["night"] = "03:00-04:00"
    keeper._pace_at = float("-inf")
    noon = dt.datetime.now().replace(hour=12, minute=0, second=0, microsecond=0).timestamp()          # by day
    keeper._limits_read = lambda: []
    orig = idea_target.pace
    idea_target.pace = lambda limits, at, provider="claude": "ahead"
    try:
        keeper._may_run = lambda: False
        keeper._reserved = lambda: False
        keeper.run_pace = lambda at=None: {}
        got = keeper.pace_tick(noon)
    finally:
        idea_target.pace = orig
    assert got is runs
