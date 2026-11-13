"""Spec 168 H3 (decisions §283.32): the night is a ladder. Each rung's pickup, the caps (one a leader, three a night, a ready spec at most, never built without a press),
the reserve, the morning's *proposed* row with its ways *Take* and *Drop*, and the old `work_at_night` read as before."""
from __future__ import annotations

import datetime as dt
import json
import time
from types import SimpleNamespace

import pytest

from orkboard import settings
from orkboard.core import idea_night
from orkboard.realm import idea_target, ideas
from tests.test_board_35 import FakeRunner, _wait, host, model, runner  # noqa: F401  (fixtures)

WINDOW = "01:00-07:00"
AT = dt.datetime(2026, 11, 10, 3, 0)


# -- the setting: one reader, the old key read as before -------------------------------------------------------------------------------------------

def test_the_rung_and_the_leaders_are_kept_and_work_at_night_follows_the_rung():
    assert settings.night_values("proposals", ["tech", "design", "tech"]) == {"night_rung": "proposals", "work_at_night": True, "night_leaders": ["tech", "design"]}
    assert settings.night_values("ideas")["work_at_night"] is False and settings.night_values("off")["work_at_night"] is False
    assert settings.night_values("builds")["work_at_night"] is True
    for bad in ("", "nights", None):
        with pytest.raises(ValueError):
            settings.night_values(bad)
    with pytest.raises(ValueError):
        settings.night_values("proposals", "tech")
    kept = settings.clean_ideas({"night_rung": "proposals", "work_at_night": True, "night_leaders": ["tech", 3, "Bad Slug", "design"]})
    assert (kept["night_rung"], kept["night_leaders"]) == ("proposals", ["tech", "design"]) and settings.night_rung(kept) == "proposals"
    assert "night_rung" not in settings.clean_ideas({"night_rung": "nope"}) and "night_rung" not in settings.IDEAS


# -- what each rung may pick up --------------------------------------------------------------------------------------------------------------------

# -- the caps and the reserve ----------------------------------------------------------------------------------------------------------------------

def test_one_proposal_a_leader_three_a_night_and_only_on_the_top_rung(tmp_path):
    key = idea_night.night_key(WINDOW, AT)
    assert key == "2026-11-09" or key == "2026-11-10"          # named by the day the window began (01:00-07:00 does not cross midnight)
    assert idea_night.night_key(WINDOW, dt.datetime(2026, 11, 10, 12, 0)) == ""
    leaders = ["tech", "design", "product", "art"]
    assert idea_night.who_may(tmp_path, key, leaders, "builds") == [] and idea_night.who_may(tmp_path, "", leaders, "proposals") == []
    assert idea_night.who_may(tmp_path, key, leaders, "proposals") == ["tech", "design", "product"]          # three at most
    assert idea_night.make(tmp_path, "tech", key, "A", "spec") is not None
    assert idea_night.make(tmp_path, "tech", key, "B", "spec") is None                                            # one a leader, whoever asks
    assert idea_night.who_may(tmp_path, key, leaders, "proposals") == ["design", "product"]
    assert idea_night.make(tmp_path, "design", key, "C", "spec") and idea_night.make(tmp_path, "product", key, "D", "spec")
    assert idea_night.make(tmp_path, "art", key, "E", "spec") is None and idea_night.who_may(tmp_path, key, leaders, "proposals") == []
    assert idea_night.who_may(tmp_path, "2099-01-01", leaders, "proposals") == ["tech", "design", "product"]      # the next night starts again
    assert {r["stage"] for r in idea_night.read(tmp_path)} == {"spec"} and {r["status"] for r in idea_night.read(tmp_path)} == {"proposed"}


def limit(remaining, window="session", provider="claude"):
    return SimpleNamespace(provider=provider, remaining=remaining, window=window, resets_at=None, reset_at=None, resets_in=None)


def test_a_night_that_would_spend_past_the_reserve_stops():
    wall = AT.timestamp()
    s = {"night": WINDOW, "reserve_night": 0.1}
    assert idea_night.within_reserve([], s, wall) and idea_night.within_reserve([limit(0.5)], s, wall)           # nothing read: it goes, as every call does
    assert not idea_night.within_reserve([limit(0.1)], s, wall) and not idea_night.within_reserve([limit(0.5), limit(0.05, "weekly")], s, wall)
    assert idea_night.within_reserve([limit(0.5)], s, wall, share=0.3) and not idea_night.within_reserve([limit(0.5)], s, wall, share=0.45)    # a call that costs more than is above the reserve


# -- the morning's proposal ------------------------------------------------------------------------------------------------------------------------

# -- on the host -----------------------------------------------------------------------------------------------------------------------------------

@pytest.fixture
def at_night(monkeypatch, host):
    """The clock is inside the night's window; no limits are read unless a test sets them."""
    monkeypatch.setattr(idea_target, "night_start", lambda spec, now=None: AT.replace(hour=1))
    monkeypatch.setattr(host.ideas, "_raw_limits", lambda: [])
    return host.ideas


def _party(host) -> str:
    root = host.ideas.root()
    found = [t["slug"] for t in ideas.tracks(root, make=True) if t["slug"] != ideas.GENERAL]
    return found[0] if found else ideas.add_track(root, "Tech")


def _routed_goal(host, text="Add a night mode."):
    slug = host.command("ideas.add", {"text": text, "track": _party(host)})["slug"]
    ideas.save_state(host.ideas.state_dir, slug, state="routed", held_for="", held_until="", queue="")
    return slug


def _tick(host):
    host.ideas._route_at = 0.0
    host.ideas.route_tick(time.time())


def test_night_set_writes_the_rung_with_the_old_key_in_step_and_the_card_says_it(host):
    card = host.command("ideas.night_set", {"rung": "proposals", "leaders": [_party(host)]})
    s = host.ideas.settings_now()
    assert (card["rung"], s["work_at_night"], s["night_rung"]) == ("proposals", True, "proposals") and card["window"] == s["night"] and card["leaders"] == [_party(host)]
    assert host.command("ideas.night_set", {"rung": "ideas"})["rung"] == "ideas" and host.ideas.settings_now()["work_at_night"] is False
    host.command("ideas.board_set", {"work_at_night": True})                                  # the old key, as before
    assert host.command("ideas.night_ladder", {})["rung"] == "builds"
    host.command("ideas.board_set", {"work_at_night": False})
    assert host.command("ideas.night_ladder", {})["rung"] == "ideas"
    for bad in ({"rung": "all"}, {"rung": "ideas", "leaders": ["nobody"]}, {"rung": "ideas", "leaders": "tech"}):
        with pytest.raises(Exception):
            host.command("ideas.night_set", bad)


@pytest.mark.parametrize("rung, talks", [("off", False), ("ideas", True), ("builds", True), ("proposals", True)])
def test_the_night_talks_the_goals_in_line_from_the_ideas_rung_up(host, model, runner, at_night, monkeypatch, rung, talks):
    said = []
    monkeypatch.setattr(host.ideas, "route_talk", lambda args: said.append(args["idea"]) or {"ok": True})
    slug = _routed_goal(host)
    ideas.save_state(host.ideas.state_dir, slug, route=[{"party": _party(host)}], route_how={})
    host.command("ideas.night_set", {"rung": rung})
    _tick(host)
    assert said == ([slug] if talks else [])


def test_the_night_talks_nothing_outside_its_window_nor_a_goal_on_hold_nor_past_the_reserve(host, model, runner, at_night, monkeypatch):
    said = []
    monkeypatch.setattr(host.ideas, "route_talk", lambda args: said.append(args["idea"]) or {"ok": True})
    slug = _routed_goal(host)
    ideas.save_state(host.ideas.state_dir, slug, route=[{"party": _party(host)}], route_how={}, held_for="hold")
    host.command("ideas.night_set", {"rung": "ideas"})
    _tick(host)
    assert said == []                                                                          # on Hold: the person's
    ideas.save_state(host.ideas.state_dir, slug, held_for="")
    monkeypatch.setattr(host.ideas, "_raw_limits", lambda: [limit(0.05)])
    _tick(host)
    assert said == []                                                                          # the night's reserve is spent: the night stops
    monkeypatch.setattr(host.ideas, "_raw_limits", lambda: [])
    monkeypatch.setattr(idea_target, "night_start", lambda spec, now=None: None)
    _tick(host)
    assert said == []                                                                          # the window is closed
    monkeypatch.setattr(idea_target, "night_start", lambda spec, now=None: AT)
    _tick(host)
    assert said == [slug]


def test_the_leaders_proposals_are_laid_on_hold_marked_proposed_and_take_and_drop_answer_them(host, model, runner, at_night, monkeypatch):
    party = _party(host)
    answers = iter([json.dumps({"title": "Faster start", "spec": "Why: slow.\nDone when: fast."})])
    monkeypatch.setattr(host.ideas.keeper, "ask", lambda step, prompt, **k: (next(answers), None, None, ""))
    host.command("ideas.night_set", {"rung": "proposals", "leaders": [party]})
    _tick(host)
    _wait(host, "night-proposals")
    (row,) = idea_night.read(host.ideas.state_dir)
    assert (row["party"], row["title"], row["stage"], row["status"]) == (party, "Faster start", "spec", "proposed")
    st = ideas.state(host.ideas.state_dir, row["goal"])
    assert st["state"] == "raw" and st["queue"] == "hold"                                      # nothing reads, plans or builds it without a press
    assert not FakeRunner.started
    needs = [n for n in host.command("ideas.board", {})["needs_you"] if n["kind"] == "night_proposal"]
    assert [(n["goal"], n["proposed"], n["kinds"]) for n in needs] == [(row["goal"], True, ["take", "drop"])]
    node = next(n for n in host.command("ideas.map", {})["nodes"] if n["slug"] == row["goal"])
    assert node["proposed"] == row["night"] and node["queue"] == "hold"                      # the map's row says *proposed*: the column lays it in Specs
    assert all("proposed" not in n for n in host.command("ideas.map", {})["nodes"] if n["slug"] != row["goal"])
    _tick(host)
    assert len(idea_night.read(host.ideas.state_dir)) == 1                                     # one a leader: not asked again tonight
    host.command("ideas.night_answer", {"id": row["id"], "take": False})
    assert ideas.idea_page(host.ideas.root(), row["goal"]) is None and idea_night.rows(host.ideas.state_dir) == []

