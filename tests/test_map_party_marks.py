"""A party's sword and shield on the Map (docs/specs/111-a-goals-rune-release-and-live-at-the-portal.md §3.4, decisions §189): the party nodes carry `does_tool`, `checks_tool`, `does_mixed`,
`checks_mixed` and `lean` (gui/ideas_map.py `marks_of`), from the party's tool and its seats' own (`goal_team.tool_of`, `clean_tools`), the Main tool where none is set; and, per side, `does_default` /
`checks_default`: whether it follows the default tool (spec 114 B, decisions §192.4). Code, no model."""
from __future__ import annotations

import pytest

from orkboard import settings as machine
from orkboard.gui.board_host import Orkboard
from orkboard.gui.ideas_map import MapMixin
from orkboard.realm import goal_team, ideas, library


@pytest.fixture
def host(fake_repo) -> Orkboard:
    return Orkboard(fake_repo)


def goal(**more) -> dict:
    """A party node as the Map builds it, with only what `marks_of` reads."""
    team = [{"slug": s} for s in more.pop("team", [])]
    return {"leader": {"slug": "architect"}, "size": "standard", "tool": "", "tools": {}, **more, "team": team}


def test_the_partys_tool_is_both_columns_and_a_seats_own_tool_is_its_own():
    g = goal(team=["grunt", "tester", "reviewer"], tool="codex", tools={"reviewer": "claude"})
    got = MapMixin.marks_of(g, "claude")
    assert got["does_tool"] == "codex" and not got["does_mixed"]                           # the party's tool: its doers run on it
    assert got["checks_tool"] == "claude" and not got["checks_mixed"]                      # the checker's own tool


def test_a_lean_partys_shield_is_its_leaders_tool_its_acceptance_is_the_check():
    got = MapMixin.marks_of(goal(team=["grunt", "reviewer"], size="lean", tool="codex"), "claude")
    assert got == {"does_tool": "codex", "checks_tool": "codex", "does_mixed": False, "checks_mixed": False, "lean": True, "does_default": False, "checks_default": False}
    lone = MapMixin.marks_of(goal(team=["grunt", "reviewer"], size="lean", tools={"architect": "agy", "reviewer": "claude"}), "claude")
    assert lone["checks_tool"] == "agy" and lone["lean"] is True        # at Lean the checking seats are not read: the leader accepts (spec 152 A.7)


def test_a_side_follows_the_default_when_neither_the_party_nor_a_seat_of_that_side_is_set_to_a_tool():
    both = MapMixin.marks_of(goal(team=["grunt", "tester", "reviewer"]), "claude")
    assert both["does_default"] is True and both["checks_default"] is True
    party = MapMixin.marks_of(goal(team=["grunt", "tester", "reviewer"], tool="codex"), "claude")
    assert party["does_default"] is False and party["checks_default"] is False                 # the party's tool is set on purpose for both sides
    same = MapMixin.marks_of(goal(team=["grunt", "reviewer"], tool="claude"), "claude")
    assert same["does_tool"] == "claude" and same["does_default"] is False                     # set to the Main tool on purpose is still set: it does not move on with the default


def test_the_maps_party_nodes_carry_them_from_the_pages_and_the_machines_main_tool(host):
    root = host.ideas.root()
    library.install(host.ideas.state_dir, ["grunt", "tester", "reviewer", "architect"])                       # the seats the Map reads are the installed ones
    p, q = ideas.add_track(root, "First party"), ideas.add_track(root, "Second party")
    goal_team.set_team(root, p, ["grunt", "tester", "reviewer"], [], "architect")
    goal_team.set_tool(root, p, "codex")
    goal_team.set_tools(root, p, {"reviewer": "claude"})
    goal_team.set_size(root, q, "lean")
    parties = {g["slug"]: g for g in host.command("ideas.map", {})["goals"]}
    main = machine.main_tool(host.machine)
    assert (parties[p]["does_tool"], parties[p]["checks_tool"], parties[p]["lean"]) == ("codex", "claude", False)
    assert (parties[q]["does_tool"], parties[q]["checks_tool"], parties[q]["lean"]) == (main, main, True)
    assert all(parties[s]["does_mixed"] is False and parties[s]["checks_mixed"] is False for s in (p, q))
    assert (parties[p]["does_default"], parties[p]["checks_default"]) == (False, False)                      # the party is set to Codex
    assert (parties[q]["does_default"], parties[q]["checks_default"]) == (True, True)                       # nothing set; Lean's check is its leader's
