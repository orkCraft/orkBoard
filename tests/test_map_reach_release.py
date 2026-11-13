"""Spec 165 E (docs/specs/165-each-leaders-map-a-board-games-shape.md; decisions §281.6, §280.2): Dev and main's reach, the plan kept without git's trial pick."""
from __future__ import annotations

from pathlib import Path

from orkboard.realm import goal_main, map_reach, release_map

S, R, P = Path("s"), Path("r"), Path("p")


def _release(monkeypatch, held: list[str], takes: dict[str, list[str]]) -> list[dict]:
    calls: list[dict] = []
    monkeypatch.setattr(release_map, "read", lambda state_dir, root, pages=None, into="dev": {"goals": [{"idea": g} for g in held]})

    def plan(repo, state_dir, slug, **kw):
        calls.append({"slug": slug, **kw})
        return {"goals": [slug, *takes.get(slug, [])]}
    monkeypatch.setattr(goal_main, "plan", plan)
    return calls


def test_dev_and_main_reach_is_the_goals_the_plan_takes_along_without_its_trial(monkeypatch, tmp_path):
    calls = _release(monkeypatch, ["a", "b", "c"], {"b": ["a", "gone"]})
    got = map_reach.reach(tmp_path / "state", tmp_path, tmp_path, "release", "release")
    assert got["a"] == {"lit": ["a"], "one": [], "two": [], "no_test": []}
    assert got["b"] == {"lit": ["b"], "one": ["a"], "two": [], "no_test": []}, "a goal main does not wait for is no reach"
    assert [c["slug"] for c in calls] == ["a", "b", "c"] and all(c["pick"] is False for c in calls)
    assert not (tmp_path / "state").exists(), "no worktree, nothing written to the state"


def test_dev_and_main_plans_run_once_per_board_change(monkeypatch, tmp_path):
    calls = _release(monkeypatch, ["a", "b"], {"b": ["a"]})
    kept = map_reach.Kept()
    kept.track("reach", "release")

    def compute(what, key):
        return map_reach.reach(tmp_path / "s", tmp_path, tmp_path, "release", key)
    kept.refresh(1, lambda: "h", compute)
    kept.refresh(1, lambda: "h", compute)
    assert len(calls) == 2, "one call a goal a Board change; the second refresh at the same rev runs none"
    assert kept.answer("reach", "release")["b"]["one"] == ["a"]
    kept.refresh(2, lambda: "h", compute)
    assert len(calls) == 4

