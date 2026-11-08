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


# -- spec 165 C: reach on System and Screens ------------------------------------------------------------------------------------------------

import subprocess

import pytest

from orkboard.realm import screen_map


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


@pytest.fixture
def fixture_repo(tmp_path: Path) -> Path:
    """Parts a, b, c, d: b uses a, c uses b, d uses c; only a has a test."""
    r = tmp_path / "project"
    r.mkdir()
    _git(r, "init", "-q", "-b", "dev")
    _git(r, "config", "user.email", "t@orkcraft.local")
    _git(r, "config", "user.name", "T")
    files = {"pkg/a/a.py": "X = 1\n", "pkg/b/__init__.py": "from pkg.a.a import X\n", "pkg/c/__init__.py": "from pkg.b import X\n",
             "pkg/d/__init__.py": "from pkg.c import X\n", "tests/test_a.py": "def test_a():\n    pass\n", "orkcraft.toml": ""}
    for name, text in files.items():
        (r / name).parent.mkdir(parents=True, exist_ok=True)
        (r / name).write_text(text)
    _git(r, "add", "-A")
    _git(r, "commit", "-q", "-m", "work")
    return r


def _page(pages: Path, slug: str, sections: str, phase: str = "work") -> None:
    (pages / "pages" / "ideas").mkdir(parents=True, exist_ok=True)
    (pages / "pages" / "tracks").mkdir(parents=True, exist_ok=True)
    (pages / "pages" / "tracks" / "tech.md").write_text("---\nowner: board\nkind: track\n---\n# Tech\n")
    (pages / "pages" / "ideas" / f"{slug}.md").write_text(f"---\nowner: board\nkind: idea\ntrack: tech\nphase: {phase}\n---\n# {slug}\n\n## Gist\nx\n\n{sections}")


def test_reach_on_system_is_the_part_lit_the_parts_that_use_it_one_out_and_theirs_two(fixture_repo, tmp_path):
    pages = tmp_path / "pages"
    _page(pages, "g1", "## Tech\n### Will be\n- changed pkg/a — it changes\n")
    got = map_reach.reach(tmp_path / "state", fixture_repo, pages, "tech", "tech")
    assert got["g1"]["lit"] == ["pkg/a"] and got["g1"]["one"] == ["pkg/b"] and got["g1"]["two"] == ["pkg/c"]
    assert got["g1"]["no_test"] == ["pkg/b", "pkg/c"], "a has a test; b and c are reached and have none; d is out of reach"


def test_a_file_of_a_part_lights_its_part_and_a_goal_done_has_no_entry(fixture_repo, tmp_path):
    pages = tmp_path / "pages"
    _page(pages, "g1", "## Tech\n### Will be\n- changed pkg/b/__init__.py — it\n")
    _page(pages, "g2", "## Tech\n### Will be\n- changed pkg/b — it\n", phase="done")
    got = map_reach.reach(tmp_path / "state", fixture_repo, pages, "tech", "tech")
    assert list(got) == ["g1"] and got["g1"]["lit"] == ["pkg/b"] and got["g1"]["one"] == ["pkg/c"] and got["g1"]["two"] == ["pkg/d"]


def test_a_goal_with_no_will_be_or_naming_nothing_has_no_entry(fixture_repo, tmp_path):
    pages = tmp_path / "pages"
    _page(pages, "none", "## Tech\n### Why\n- because\n")
    _page(pages, "nothing", "## Tech\n### Will be\n- changed elsewhere/else — it\n")
    assert map_reach.reach(tmp_path / "state", fixture_repo, pages, "tech", "tech") == {}
    assert map_reach.reach(tmp_path / "state", fixture_repo, pages, "tech", "art") == {}


def test_an_unreadable_map_is_empty_never_an_error(tmp_path):
    pages = tmp_path / "pages"
    _page(pages, "g1", "## Tech\n### Will be\n- changed pkg/a — it\n")
    assert map_reach.reach(tmp_path / "state", tmp_path / "no-repo", pages, "tech", "tech") == {}
    assert map_reach.reach(tmp_path / "state", tmp_path / "no-repo", tmp_path / "no-pages", "tech", "design") == {}


def test_reach_on_screens_names_a_screen_by_id_name_or_path_and_goes_along_the_links_both_ways(tmp_path, monkeypatch):
    pages = tmp_path / "pages"
    _page(pages, "g1", "## Tech\n### Will be\n- changed /Order-Detail — it\n")
    screens = [{"id": i, "name": n, "path": p} for i, n, p in (("home", "Home", "/"), ("orders", "Orders", "/orders"), ("orders-id", "Order detail", "/orders/:id"), ("pay", "Pay", "/pay"), ("done", "Done", "/done"))]
    links = [{"from": "home", "to": "orders"}, {"from": "orders", "to": "orders-id"}, {"from": "orders-id", "to": "pay"}, {"from": "pay", "to": "done"}]
    monkeypatch.setattr(screen_map, "flow", lambda root, ref="dev": {"screens": screens, "links": links})
    got = map_reach.reach(tmp_path / "state", tmp_path, pages, "tech", "design")
    assert got == {"g1": {"lit": ["orders-id"], "one": ["orders", "pay"], "two": ["done", "home"], "no_test": []}}
    monkeypatch.setattr(screen_map, "flow", lambda root, ref="dev": None)
    assert map_reach.reach(tmp_path / "state", tmp_path, pages, "tech", "design") == {}
