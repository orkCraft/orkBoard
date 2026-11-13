"""Spec 120 F (docs/specs/120-a-goal-heard-and-thrown-to-a-side.md §6.3–§6.4): what a goal's card at the Orkmaster carries for its back, as data: the Talk's route, who has been heard, the stances
that are in and the wait. Only a goal routed, in Talk or decided has a back; a goal of the Board's map carries it as `back`."""
from __future__ import annotations

from pathlib import Path

from orkboard.realm import board_back, goal_route, idea_ripe, ideas

ROUTE = [{"party": "design", "leader": "ux", "head": {"race": "dryad", "tier": "elder"}}, {"party": "tech", "leader": "architect", "head": {"race": "shaman", "tier": "elder"}}]


def _seed(tmp_path: Path, monkeypatch, slug="dark"):
    monkeypatch.setattr(goal_route, "steps_of", lambda root, state_dir, st, settings=None: ROUTE)
    monkeypatch.setattr(goal_route, "cost_of", lambda root, state_dir, st, settings=None: {"calls": 3, "usd_low": 0.1, "usd_high": 0.2})
    ideas.state_folder(tmp_path, slug).mkdir(parents=True, exist_ok=True)
    return tmp_path


def test_a_goal_before_its_sections_has_a_back_and_any_other_has_none(tmp_path, monkeypatch):
    state = _seed(tmp_path, monkeypatch)
    for name in ("routed", "talk", "decided", "sketch", "sections"):
        assert board_back.of(tmp_path, state, "dark", {"state": name}) is not None, name
    for name in ("working", "done", "raw"):
        assert board_back.of(tmp_path, state, "dark", {"state": name}) is None, name


def test_a_decided_goal_carries_its_wait_as_it_is_kept(tmp_path, monkeypatch):
    state = _seed(tmp_path, monkeypatch)
    assert board_back.of(tmp_path, state, "dark", {"state": "decided"})["ripe"] is None
    got = idea_ripe.begin(state, "dark", "high", "low")
    assert got is not None
    back = board_back.of(tmp_path, state, "dark", {"state": "decided"})
    assert back["ripe"] == {"left_s": 60.0, "seconds": 60, "risk": "low", "priority": "high", "held": False, "by": "", "why": ""}
    idea_ripe.tick(state, ["dark"], 15)
    assert board_back.of(tmp_path, state, "dark", {"state": "decided"})["ripe"]["left_s"] == 45.0
    idea_ripe.hold(state, "dark", "person")
    held = board_back.of(tmp_path, state, "dark", {"state": "decided"})["ripe"]
    assert held["held"] is True and held["by"] == "person" and held["left_s"] == 0.0
    assert board_back.of(tmp_path, state, "dark", {"state": "talk"})["ripe"] is None, "the wait is the decided goal's"

