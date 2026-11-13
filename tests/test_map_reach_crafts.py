"""Spec 165 D (docs/specs/165-each-leaders-map-a-board-games-shape.md; decisions §280.1): `realm/map_reach_crafts.py`, reach on the loop, the tree, Art and the way in; one map each."""
from __future__ import annotations

from pathlib import Path

from orkboard.realm import hypotheses, loop, map_parts, map_reach, map_reach_crafts, opportunity_tree

S, R, P = Path("s"), Path("r"), Path("p")


def _parts(monkeypatch, map_id: str, rows: list[dict]) -> None:
    monkeypatch.setattr(map_parts, "parts", lambda state_dir, root, craft, pages=None, ref="dev": [{"map": map_id, **r} for r in rows])


def test_the_loop_reaches_the_step_before_and_after_and_the_next_out(monkeypatch):
    steps = [{"id": f"s{n}", "name": f"Step {n}"} for n in range(1, 7)]
    _parts(monkeypatch, "game-design", [{**s, "group": "loop"} for s in steps] + [{"id": "cur:gold", "name": "Gold", "group": "economy"}])
    monkeypatch.setattr(loop, "read", lambda state_dir: {"loops": [{"steps": steps}], "currencies": [{"id": "gold", "name": "Gold"}]})
    got = map_reach_crafts.reach(S, R, P, "game-design", {"g": ["s3"], "c": ["cur:gold"], "n": ["nothing"]})
    assert got["g"] == {"lit": ["s3"], "one": ["s2", "s4"], "two": ["s1", "s5"], "no_test": []}
    assert got["c"] == {"lit": ["cur:gold"], "one": [], "two": [], "no_test": []} and "n" not in got
    assert map_reach_crafts.reach(S, R, P, "game-design", {"g": ["s1"]})["g"]["one"] == ["s2", "s6"], "a ring: the last step is before the first"


def test_the_tree_reaches_a_jobs_hypotheses_and_goals_and_a_hypothesis_or_goals_job(monkeypatch):
    rows = [{"id": "j1", "name": "Pay", "group": "jobs"}, {"id": "j2", "name": "Pick", "group": "jobs"}, {"id": "hyp:h1", "name": "H one", "group": "hypotheses"},
            {"id": "hyp:h2", "name": "H two", "group": "hypotheses"}, {"id": "g-a", "name": "A", "group": "goals"}, {"id": "g-b", "name": "B", "group": "goals"}]
    _parts(monkeypatch, "product", rows)
    monkeypatch.setattr(hypotheses, "read", lambda state_dir: {"items": [{"id": "h1", "on": "j1"}, {"id": "h2", "on": "j2"}]})
    monkeypatch.setattr(opportunity_tree, "read", lambda state_dir: {"serves": [{"job": "j1", "goal": "g-a"}, {"job": "j2", "goal": "g-b"}]})
    got = map_reach_crafts.reach(S, R, P, "product", {"job": ["j1"], "hyp": ["hyp:h1"], "goal": ["g-b"]})
    assert got["job"] == {"lit": ["j1"], "one": ["g-a", "hyp:h1"], "two": [], "no_test": []}
    assert got["hyp"] == {"lit": ["hyp:h1"], "one": ["j1"], "two": ["g-a"], "no_test": []}
    assert got["goal"]["lit"] == ["g-b"] and got["goal"]["one"] == ["j2"] and got["goal"]["two"] == ["hyp:h2"]


def test_map_reach_reads_a_goals_will_be_for_these_crafts(monkeypatch, tmp_path):
    pages = tmp_path / "pages"
    (pages / "pages" / "ideas").mkdir(parents=True)
    (pages / "pages" / "tracks").mkdir(parents=True)
    (pages / "pages" / "tracks" / "tech.md").write_text("---\nowner: board\nkind: track\n---\n# Tech\n")
    (pages / "pages" / "ideas" / "g1.md").write_text("---\nowner: board\nkind: idea\ntrack: tech\nphase: work\n---\n# g1\n\n## Gist\nx\n\n## Tech\n### Will be\n- changed assets — it\n")
    _parts(monkeypatch, "art", [{"id": "assets/a.png", "name": "a.png"}])
    assert map_reach.reach(tmp_path / "state", tmp_path, pages, "tech", "art") == {"g1": {"lit": ["assets/a.png"], "one": [], "two": [], "no_test": []}}
