"""Spec 52 §2.1 (docs/specs/52-goal-types.md): the goal types a party's leader deals, the agent who does a kind of work, whether
a party does it, and what a party misses for a type or a plan. Code, no model, no face."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from orkboard.realm import goal_team, goal_types, ideas, library, roles

ROOT = Path(__file__).resolve().parent.parent
A0_SIGNS = {"feature", "bug", "tidy", "restructure", "screen", "picture", "logo", "target", "flask", "horn", "chart", "page", "abtest", "landing", "post", "tagline",
            "mechanic", "level", "balance", "character", "release", "store", "tune"}   # spec 56 §6 and spec 59 §1.1, orkUI 0.4.1: the twenty-three


@pytest.fixture
def board(tmp_path):
    return tmp_path / "wiki", tmp_path / ".orkcraft"


def _party(root, state, team=(), leader="taskmaster", title="Ship"):
    slug, _new = ideas.save_goal(root, None, title, "About " + title, None, "normal")
    library.install(state, [s for s in (*team, leader) if library.get(s) is not None])
    goal_team.set_team(root, slug, list(team), leader=leader)
    return slug


def _goal(root, state, party, tasks, state_="working"):
    slug = ideas.add_idea(root, f"goal {len(ideas.ideas(root))}", party, state)
    ideas.save_state(state, slug, state=state_)
    ideas.save_plan(state, slug, {"idea": slug, "tasks": tasks, "todos": []})
    return slug


def _all():
    return list(goal_types.CATALOG)


def _offer(board, craft_or_preset):
    """What a party of the library's offers: [(name, [who is missing])], in the catalog's order."""
    root, state = board
    lead, build, check = (library.PARTIES[craft_or_preset] if craft_or_preset in library.PARTIES
                          else next((p[4], p[5], p[6]) for p in library.PRESETS if p[0] == craft_or_preset))
    ship = _party(root, state, [*build, *check], leader=lead)
    return [(t.name, [m["agent"] for m in rows]) for t, rows in goal_types.offered(state, root, ship)]


# -- the catalog ----------------------------------------------------------------------------------------------



def test_a_type_is_read_by_its_id_and_an_old_key_by_the_one_it_was_and_anything_else_reads_none():
    assert goal_types.get("icon").name == "New icon" and goal_types.get("product-designer/icon").id == "icon"
    old = {"taskmaster/feature": "feature", "taskmaster/bug": "bug", "architect/bug": "bug", "taskmaster/tidy": "tidy",
           "architect/feature": "shaped-feature", "architect/restructure": "restructure", "product-designer/screen": "screen",
           "product-designer/icon": "icon", "product-designer/logo": "logo", "product-designer/feature": "flow-feature",
           "product-manager/pain": "pain", "product-manager/experiment": "experiment", "product-manager/launch": "launch",
           "analyst/metric": "metric", "analyst/report": "report", "analyst/abtest": "abtest", "growth/landing": "landing",
           "growth/post": "post", "growth/tagline": "tagline"}
    for key, new in old.items():
        assert goal_types.get(key).id == new, key
    for bad in ("", None, "taskmaster/logo", "nobody/bug", "grunt/bug", "taskmaster", "/bug", "architect/tidy"):
        assert goal_types.get(bad) is None, bad


# -- what a party offers --------------------------------------------------------------------------------------

def test_the_library_parties_are_offered_spec_59s_lists_with_who_each_near_one_misses(board):
    got = {c: _offer(board, c) for c in ("game", "mobile-app", "website")}
    assert [n for n, m in got["game"]] == ["New feature", "Fix a bug", "Clean up", "New icon", "New logo", "New mechanic", "New level",
                                           "New character", "Balance pass", "New sound"]
    assert all(not m for _n, m in got["game"])
    assert [n for n, m in got["mobile-app"] if not m] == ["New feature", "Fix a bug", "Clean up", "New icon", "New logo", "Solve a pain",
                                                         "New character", "Store listing", "A release"]
    assert [(n, m) for n, m in got["mobile-app"] if m] == [("New screen", ["ui-kit"]), ("Try an experiment", ["experimenter"]),
                                                           ("Write the launch", ["copywriter"])]
    assert [n for n, m in got["website"]] == ["New feature", "Fix a bug", "Clean up", "A landing page", "A launch post", "A tagline"]
    assert all(not m for _n, m in got["website"])


def test_code_is_someones_a_type_that_needs_it_is_offered_only_when_a_member_takes_it_itself(board, monkeypatch):
    root, state = board
    names = lambda slug: {t.id for t, _r in goal_types.offered(state, root, slug)}
    no_code = _party(root, state, ["artist"], leader="product-designer")
    assert not names(no_code) & {"feature", "bug", "tidy", "release"}                        # no one of it writes code: not even with the Grunt to fill in
    tester = _party(root, state, ["tester"], leader="product-manager", title="Tester")
    assert not names(tester) & {"feature", "bug", "tidy"}                                    # the Tester takes tests, not code
    grunt = _party(root, state, ["grunt"], leader="product-designer", title="Grunt")
    assert {"feature", "bug", "tidy"} <= names(grunt)
    alone = _party(root, state, [], title="Alone")
    assert {"feature", "bug", "tidy"} <= names(alone)                                        # the Taskmaster leading takes code
    monkeypatch.setattr(goal_types, "CATALOG", (*goal_types.CATALOG, goal_types.GoalType("proof", "Prove it", "bug", "x", ("tests",))))
    assert "proof" in names(tester) and "proof" not in names(no_code)                        # tests: the Tester, not the Grunt filling in
    scribe = roles.save(state, "Coder", "", 1, "Write code.", None, ["code"])
    own = _party(root, state, [scribe], leader="product-manager", title="Own")
    assert "bug" in names(own)                                                               # an agent of the person's own that takes it


def test_a_type_missing_one_agent_is_offered_only_when_the_leader_does_another_part_of_it(board):
    root, state = board
    pm = _party(root, state, ["grunt"], leader="product-manager")
    rows = {t.id: r for t, r in goal_types.offered(state, root, pm)}
    assert [m["agent"] for m in rows["screen"]] == ["ui-kit"] and [m["agent"] for m in rows["experiment"]] == ["experimenter"]
    assert set(rows["screen"][0]) == {"kind", "words", "agent", "name", "band", "free", "out"} and rows["screen"][0]["free"] is True    # the Grunt holds one of the five seats (spec 99 §1.3)
    assert rows["pain"] == []                                                                 # the leader's own work: nothing missing
    assert "tagline" not in rows and "icon" not in rows and "store" not in rows               # one agent missing, but beside the leader's own work
    assert "landing" not in rows and "abtest" not in rows                                     # two missing
    assert "launch" in rows and [m["agent"] for m in rows["launch"]] == ["copywriter"]
    designer = _party(root, state, ["grunt"], leader="game-designer", title="Game")
    assert not {t.id for t, r in goal_types.offered(state, root, designer) if r}               # a Game designer's goals need no one else's craft
    assert "mechanic" in {t.id for t, _r in goal_types.offered(state, root, designer)}
    # a kind with no one to join (`research` is a leader's) leaves the type out, whoever else is missing
    taskless = _party(root, state, ["grunt"], leader="growth", title="Growth")
    assert "launch" not in {t.id for t, _r in goal_types.offered(state, root, taskless)}


def test_the_taker_is_of_the_leaders_craft_first_and_never_a_leader(monkeypatch):
    scribe = library.Agent("scribe", "Scribe", "design", "warrior", ("text",), "Writes a screen's words", "")
    monkeypatch.setattr(library, "LIBRARY", (*library.LIBRARY, scribe))
    assert goal_types.taker("text", "design") == "scribe" and goal_types.taker("text", "marketing") == "copywriter"
    assert goal_types.taker("text", "data") == "copywriter"                                # no one of its craft: the library's order
    assert goal_types.taker("design", "design") == goal_types.taker("metrics", "data") == ""      # a leader's kind: no one is offered


# -- whether a party does it ---------------------------------------------------------------------------------

def test_met_by_a_member_the_leader_the_projects_role_or_the_grunts_own_kinds_never_by_the_grunt_filling_in(board):
    root, state = board
    library.install(state, ["artist", "product-designer"])
    assert goal_types.met(state, "art", ["artist", "taskmaster"])                        # a member who takes it
    assert goal_types.met(state, "design", ["product-designer"])                         # the leader
    assert goal_types.met(state, "code", []) and goal_types.met(state, "tests", ["taskmaster"])   # the Grunt's own
    assert not goal_types.met(state, "art", ["taskmaster"]) and not goal_types.met(state, "uikit", ["product-designer"])   # the Grunt filling in
    pixel = roles.save(state, "Pixel smith", "", 1)
    roles.set_kind(state, "art", pixel)
    assert goal_types.met(state, "art", ["taskmaster"])                                  # the project's role for it


# -- what a party misses -----------------------------------------------------------------------------------------



# -- a party not saved ----------------------------------------------------------------------------------------------

def test_a_party_not_saved_is_read_from_its_leader_and_team_with_no_open_work_and_no_runs(board, monkeypatch):
    root, state = board
    monkeypatch.setattr(goal_types.idea_spend, "by_role", lambda state_dir, days=7: {"grunt": {"finished": 3}, "tester": {"finished": 1}})
    team = ["grunt", "tester", "copywriter", "seo", "ui-kit"]
    saved = _party(root, state, team, leader="product-designer")
    _goal(root, state, saved, [{"id": "k1", "title": "t", "kind": "uikit", "role": "ui-kit", "state": "running"}])
    p = goal_types.Party.of(state, root, "product-designer", team)
    assert (p.slug, p.leader, p.team, p.craft, p.members) == ("", "product-designer", team, "design", [*team, "product-designer"])
    assert p.team is not team and p.busy() == set() and p.runs("grunt") == 0 and p.runs("tester") == 0
    (art,) = goal_types.missing(state, root, "", ("art",), read=p)
    assert art["free"] is False and [(o["slug"], o["runs"]) for o in art["out"]] == [("ui-kit", 0), ("seo", 0), ("copywriter", 0), ("tester", 0), ("grunt", 0)]   # none holds, none ran: the later first
    (own,) = goal_types.missing(state, root, saved, ("art",))
    assert [(o["slug"], o["runs"]) for o in own["out"]] == [("seo", 0), ("copywriter", 0), ("tester", 1), ("grunt", 3)]               # the saved party's: ui-kit holds, the week's runs
    alone = goal_types.Party.of(state, root, "", [])
    assert (alone.leader, alone.team, alone.craft) == (roles.TASKMASTER, [], roles.DEFAULT_CRAFT) and alone.fresh == ()
    assert [t.id for t, _r in goal_types.offered(state, root, "", read=alone)] == ["feature", "bug", "tidy"]


# -- a plan's missing ------------------------------------------------------------------------------------------

def test_a_plans_missing_is_the_kinds_no_one_of_the_party_does_once_each_in_its_order(board):
    root, state = board
    library.install(state, ["grunt", "product-designer"])
    tasks = [{"kind": "code"}, {"kind": "art"}, {"kind": "uikit"}, {"kind": "art"}, {"kind": "design"}, {"kind": "community"}]
    got = goal_types.of_plan(state, tasks, ["grunt", "product-designer"], "product-designer")
    assert got == [{"kind": "art", "agent": "artist"}, {"kind": "uikit", "agent": "ui-kit"}, {"kind": "community", "agent": "community"}]


# -- spec 68 §3.1: A release asks its version and is offered by the Release party alone ----------------------------------------

def _preset(board, preset, title):
    root, state = board
    lead, build, check = next((p[4], p[5], p[6]) for p in library.PRESETS if p[0] == preset)
    return _party(root, state, [*build, *check], leader=lead, title=title)


def test_a_release_asks_its_version_first_and_then_what_is_new():
    t = goal_types.get("release")
    assert [(a.id, a.label, a.hint) for a in t.asks] == [("version", "Version", "1.4"), ("new", "What is new", "in the person's words")]
    assert t.needs == ("aso", "code") and len(t.asks) <= 3


def test_dropping_the_release_party_gives_mobile_app_its_release_back(board):
    root, state = board
    app = _preset(board, "mobile-app", "Mobile app")
    release = _preset(board, "release", "Release")
    assert goal_types.release_party(root) == release and "release" not in {t.id for t, _r in goal_types.offered(state, root, app)}
    (root / ideas.TRACKS / f"{release}.md").unlink()
    assert goal_types.release_party(root) == "" and "release" in {t.id for t, _r in goal_types.offered(state, root, app)}
