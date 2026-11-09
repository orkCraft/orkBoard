"""What a step needs of its seats' tools (docs/specs/168 C4, decisions §283.16.6): `harnesses.can` for Codex's sandbox (no git index, no browser, no network) and for Claude Code, and `step_needs.steps`, the rows the map gives the page:
a seat whose tool cannot do what its step needs is marked."""
from __future__ import annotations

import pytest

from orkboard.realm import harnesses, step_needs


def test_codexs_sandbox_has_no_git_index_no_browser_and_no_network():
    for need in ("git", "browser", "network"):
        assert harnesses.can("codex", need) is False, need
    assert harnesses.can("codex", []) is True
    assert harnesses.lacking("codex", ["network", "git", "browser", "git"]) == ["network", "git", "browser"]       # in the order asked, each once


def test_claude_code_has_them_all():
    assert harnesses.can("claude", ["git", "browser", "network"]) is True
    assert harnesses.lacking("claude", ("git", "network")) == []


def test_a_command_is_on_the_machines_path_whatever_the_tool():
    path = {"npm": "/usr/bin/npm"}
    assert harnesses.can("claude", "command:npm", which=path.get) and harnesses.can("codex", "command:npm", which=path.get)
    assert harnesses.lacking("claude", ["git", "command:cargo"], which=path.get) == ["command:cargo"]


def test_the_main_tool_and_an_unknown_one_lack_nothing_that_is_not_known_and_a_bad_need_is_refused():
    assert harnesses.can("", ["git", "browser", "network"]) and harnesses.can("main", ["git"]) and harnesses.can("nobody", ["browser"])
    with pytest.raises(ValueError):
        harnesses.can("claude", ["wifi"])
    with pytest.raises(ValueError):
        harnesses.can("claude", "command:")


def test_the_work_of_a_kind_says_what_it_needs():
    assert step_needs.of_kinds(["tests", "code", "art"]) == []                  # the host commits for a tool that cannot, the gate runs the browser tests (spec 149 F.1)
    assert step_needs.of_kinds(["research"]) == ["network"]
    assert step_needs.of_kinds(["research", "playtest"]) == ["browser", "network"]
    assert step_needs.of_kinds(["review"]) == []


def _party(slug, tool="", tools=None, craft="engineering"):
    head = {"craft": craft, "race": "peon", "tier": "warrior"}
    return {"slug": slug, "title": slug.title(), "short": slug.title(), "party_craft": craft, "tool": tool, "tools": tools or {},
            "leader": {"slug": f"{slug}-lead", "name": f"{slug} lead", "head": head},
            "team": [{"slug": "grunt", "name": "Grunt", "head": head, "checks": False, "every": False}, {"slug": "tester", "name": "Tester", "head": head, "checks": False, "every": False}]}


def test_a_seat_whose_tool_cannot_do_its_step_is_marked_and_the_others_are_not():
    goals = [_party("tech", tool="claude", tools={"tester": "codex"}), _party("art", tool="codex", craft="art")]
    node = {"slug": "x", "goal": "tech", "route": [{"step": "party", "party": "tech"}, {"step": "party", "party": "art"}, {"step": "moved", "party": "web"}],
            "tasks": [{"id": "1", "tag": "Code", "party": "tech", "state": "running", "by": {"slug": "grunt"}}, {"id": "2", "tag": "Tests", "party": "tech", "state": "waiting", "by": {"slug": "tester"}},
                      {"id": "3", "tag": "Research", "party": "tech", "state": "waiting", "by": {"slug": "tester"}}]}
    steps = step_needs.steps(node, goals)
    assert [s["party"] for s in steps] == ["tech", "art"] and steps[0]["own"] and not steps[1]["own"]
    tech = {s["slug"]: s for s in steps[0]["seats"]}
    assert tech["grunt"]["lacks"] == [] and not tech["grunt"]["marked"]                                    # Claude Code: code needs nothing of the tool
    assert tech["tester"]["lacks"] == ["network"] and tech["tester"]["marked"] and tech["tester"]["tool_name"] == "Codex"     # its tests are made on Codex; its research is not
    assert steps[0]["marked"] is True
    art = steps[1]                                                                                           # no task yet: its craft's kind; pixel art is made on Codex, its commit by the host
    assert art["needs"] == [] and not art["marked"] and all(s["lacks"] == [] for s in art["seats"])


def test_a_goal_with_no_route_is_one_step_of_its_own_party():
    node = {"slug": "x", "goal": "tech", "route": [], "tasks": []}
    assert [s["party"] for s in step_needs.steps(node, [_party("tech", tool="claude")])] == ["tech"]
