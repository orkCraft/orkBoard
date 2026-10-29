"""Spec 102 §6 (decisions §141, §152): `ideas.add` takes the marks picking on a party's map sent with an idea, `[{map, id, name, group?}]` and `[{map, group, name}]`, keeps them in the idea's state
as `marks` (realm/idea_lens.py `clean_marks`) and reads them into the prompts of the leaders' calls (`idea_lens.attached`); the whole map reads as no mark."""
from __future__ import annotations

import sys

import pytest

from orkboard.gui.board_host import Orkboard
from orkboard.realm import goal_route, idea_lens, ideas


@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def _add(host, text="Players who drop out get their seat back", **more):
    root = host.ideas.root()
    goal = next((t["slug"] for t in ideas.tracks(root, make=False) if t["slug"] != "general"), None) or ideas.add_track(root, "First goal")
    return host.command("ideas.add", {"text": text, "track": goal, "hold": True, **more})


LOBBY = {"map": "system", "id": "server/lobby.ts", "name": "server/lobby.ts", "group": "server"}


def test_the_marks_are_kept_in_the_ideas_state_and_read_into_its_prompts(host):
    got = _add(host, marks=[LOBBY, {"map": "system", "group": "client", "name": "client/"}, {"map": "screens", "id": "/lobby", "name": "Lobby"}])
    state = ideas.state(host.ideas.state_dir, got["slug"])
    assert state["marks"] == [LOBBY, {"map": "system", "name": "client/", "group": "client"}, {"map": "screens", "id": "/lobby", "name": "Lobby"}]
    said = idea_lens.attached(host.ideas.state_dir, got["slug"])
    assert "- On the system map: server/lobby.ts, everything in client/" in said and "- On the screens map: /lobby" in said


def test_an_idea_with_no_marks_has_none_and_says_nothing_of_them(host):
    got = _add(host)
    assert ideas.state(host.ideas.state_dir, got["slug"])["marks"] == []
    assert idea_lens.attached(host.ideas.state_dir, got["slug"]) == ""
    got = _add(host, marks="server/lobby.ts")
    assert ideas.state(host.ideas.state_dir, got["slug"])["marks"] == [], "a list of marks or none"


def test_the_whole_map_a_mark_with_no_place_a_repeat_and_what_is_no_mark_are_left_out_and_the_words_cut(host):
    got = _add(host, marks=[{"map": "system", "all": True, "name": "all of System"}, {"map": "system", "name": "nowhere"}, {"id": "x", "name": "no map"}, "server", None,
                            LOBBY, dict(LOBBY), {"map": "assets", "id": "hero.png", "name": "h" * 500}])
    marks = ideas.state(host.ideas.state_dir, got["slug"])["marks"]
    assert [m["id"] for m in marks] == ["server/lobby.ts", "hero.png"] and len(marks[1]["name"]) == 120


def test_at_most_forty_marks_are_kept(host):
    got = _add(host, marks=[{"map": "system", "id": f"p{i}", "name": f"p{i}"} for i in range(60)])
    assert [m["id"] for m in ideas.state(host.ideas.state_dir, got["slug"])["marks"]] == [f"p{i}" for i in range(idea_lens.MAX_PICKS)]


def test_only_marks_on_systems_map_offer_tech_on_the_route():
    system = {"map": "system", "id": "orkboard/realm", "name": "orkboard/realm"}
    assert goal_route._touches_system([system]) and goal_route._touches_system([{"map": "system", "group": "orkboard", "name": "orkboard/"}])
    assert not goal_route._touches_system([{"map": "screens", "id": "/lobby", "name": "Lobby"}, {"map": "assets", "group": "sprites", "name": "sprites/"}])
