"""Spec 165 F (docs/specs/165-each-leaders-map-a-board-games-shape.md; decisions §280.1, §281.6): `ideas.heat` and `ideas.reach` answer what was kept, off the request's thread."""
from __future__ import annotations

import threading
from pathlib import Path
from types import SimpleNamespace

from orkboard.gui import ideas_reach
from orkboard.gui.ideas_reach import ReachMixin
from orkboard.realm import commit_goal, map_parts, map_reach


class Face(ReachMixin):
    def __init__(self):
        self.rev = 1
        self.state_dir = Path("state")
        self.host = SimpleNamespace(repo_root="repo")

    def root(self, make=True):
        return Path("pages")

    def _ref(self):
        return "dev"


def setup(monkeypatch, gate=None):
    calls = {"heat": [], "reach": [], "git": 0, "head": 0}
    monkeypatch.setattr(ideas_reach.ideas, "tracks", lambda pages, make=True: [{"slug": "tech-party"}, {"slug": "empty-party"}])
    monkeypatch.setattr(map_parts, "craft_of", lambda pages, party: "tech" if party == "tech-party" else "nothing")

    def heat(state, root, craft, pages, ref):
        if gate:
            gate.wait(5)
        calls["heat"].append(craft)
        return [{"on": "p", "kind": "big"}]

    def reach(state, root, pages, party, craft, ref):
        calls["reach"].append(party)
        return {"g": {"lit": ["p"], "one": [], "two": [], "no_test": []}}

    def head(root, ref="dev"):
        calls["head"] += 1
        return "abc"

    def git(*a, **k):
        calls["git"] += 1
        raise AssertionError("git ran")
    monkeypatch.setattr(map_reach, "heat", heat)
    monkeypatch.setattr(map_reach, "reach", reach)
    monkeypatch.setattr(commit_goal, "head", head)
    monkeypatch.setattr(commit_goal, "git", git)
    return calls


def join():
    for t in threading.enumerate():
        if t.name == "ideas-reach":
            t.join(5)


def test_a_request_does_not_wait_and_the_next_answers_what_was_kept(monkeypatch):
    gate = threading.Event()
    calls = setup(monkeypatch, gate)
    f = Face()
    first = f.heat({"party": "tech-party"})
    assert first == {"party": "tech-party", "map": "system", "heat": []} and f.reach({"party": "tech-party"})["goals"] == {}
    gate.set()
    join()
    assert f.heat({"party": "tech-party"})["heat"] == [{"on": "p", "kind": "big"}]
    assert f.reach({"party": "tech-party"})["goals"]["g"]["lit"] == ["p"]
    assert calls["git"] == 0


def test_a_second_request_at_the_same_rev_starts_no_refresh(monkeypatch):
    calls = setup(monkeypatch)
    f = Face()
    f.heat({"party": "tech-party"})
    join()
    n = calls["head"]
    f.heat({"party": "tech-party"})
    f.reach({"party": "tech-party"})
    join()
    assert calls["head"] == n == 1 and calls["heat"] == ["tech"]
    f.rev = 2
    f.heat({"party": "tech-party"})
    join()
    assert calls["head"] == 2


def test_at_most_one_refresh_runs_at_a_time(monkeypatch):
    gate = threading.Event()
    calls = setup(monkeypatch, gate)
    f = Face()
    f.heat({"party": "tech-party"})
    f.rev = 2
    f.heat({"party": "tech-party"})
    assert sum(1 for t in threading.enumerate() if t.name == "ideas-reach") == 1
    gate.set()
    join()
    assert calls["head"] == 1


def test_a_party_gone_or_without_a_map_is_empty_without_an_error(monkeypatch):
    setup(monkeypatch)
    f = Face()
    assert f.heat({"party": "gone"}) == {"party": "gone", "map": "", "heat": []}
    assert f.reach({"party": "empty-party"}) == {"party": "empty-party", "map": "", "goals": {}}
    join()


def test_the_commands_are_registered():
    f = Face()
    assert set(ideas_reach.reach_commands(f)) == {"ideas.heat", "ideas.reach"}
