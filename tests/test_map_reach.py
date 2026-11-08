"""Spec 165 B (docs/specs/165-each-leaders-map-a-board-games-shape.md; decisions §280.1, §281.6): `realm/map_reach.py`, heat read uncut and kept per Board rev and dev's head."""
from __future__ import annotations

from pathlib import Path

from orkboard.realm import commit_goal, map_reach, map_signals


def _signals(rows):
    def fake(state_dir, root, craft, pages=None, ref="dev", limit=20):
        assert limit is None
        return rows
    return fake


def test_heat_keeps_the_hints_on_this_map_and_every_one(monkeypatch):
    rows = [{"on": f"p{i}", "kind": "big", "words": "w"} for i in range(30)]
    rows += [{"on": "", "kind": "vague_outcome", "words": "w"}, {"on": "s1", "map": "screens", "kind": "pains", "words": "w"}, {"on": "p1", "map": "system", "kind": "fan_in", "words": "w"}]
    monkeypatch.setattr(map_signals, "signals", _signals(rows))
    got = map_reach.heat(Path("s"), Path("r"), "tech")
    assert len(got) == 31 and got[0] == {"on": "p0", "kind": "big"} and got[-1] == {"on": "p1", "kind": "fan_in"}
    assert map_reach.heat(Path("s"), Path("r"), "nothing") == []


def test_heat_of_design_takes_pains_on_screens(monkeypatch):
    rows = [{"on": "s1", "map": "screens", "kind": "pains", "words": "w"}, {"on": "p", "map": "product", "kind": "pains", "words": "w"}]
    monkeypatch.setattr(map_signals, "signals", _signals(rows))
    assert map_reach.heat(Path("s"), Path("r"), "design") == [{"on": "s1", "kind": "pains"}]


def test_two_refreshes_at_one_rev_run_no_git(monkeypatch):
    rows = [{"on": f"p{i}", "kind": "big", "words": "w"} for i in range(25)]
    monkeypatch.setattr(map_signals, "signals", _signals(rows))
    kept = map_reach.Kept()
    kept.track("heat", "tech")
    heads, computed = [], []

    def compute(what, key):
        computed.append((what, key))
        return map_reach.heat(Path("s"), Path("r"), key)

    def read_head():
        heads.append(1)
        return "abc"

    assert kept.answer("heat", "tech") is None
    assert kept.refresh(1, read_head, compute) == [("heat", "tech")]
    assert len(kept.answer("heat", "tech")) == 25

    def boom(*a, **k):
        raise AssertionError("git ran")
    monkeypatch.setattr(commit_goal, "git", boom)
    assert kept.refresh(1, read_head, compute) == []
    assert len(kept.answer("heat", "tech")) == 25 and len(heads) == 1 and len(computed) == 1


def test_a_moved_rev_with_the_same_head_computes_only_what_uses_the_rev():
    kept = map_reach.Kept()
    kept.track("heat", "tech", ("head",))
    kept.track("heat", "product")
    seen = []
    kept.refresh(1, lambda: "h1", lambda w, k: seen.append(k) or k)
    seen.clear()
    kept.refresh(2, lambda: "h1", lambda w, k: seen.append(k) or k)
    assert seen == ["product"]
    seen.clear()
    kept.refresh(3, lambda: "h2", lambda w, k: seen.append(k) or k)
    assert sorted(seen) == ["product", "tech"]


def test_a_failing_read_keeps_what_was_kept():
    kept = map_reach.Kept()
    kept.track("heat", "tech")
    kept.refresh(1, lambda: "h", lambda w, k: ["x"])

    def bad(w, k):
        raise OSError("no")
    kept.refresh(2, lambda: 1 / 0, bad)
    assert kept.answer("heat", "tech") == ["x"]
