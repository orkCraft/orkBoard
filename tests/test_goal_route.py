"""Spec 99 C (docs/specs/99-a-goals-way.md §4): a goal's route by code, its cost, its place and its rows. No model, no face."""
from __future__ import annotations

import datetime as dt
import json

import pytest

from orkboard.realm import board_map, goal_route, goal_team, idea_target, library, ideas

AGENTS = ["architect", "grunt", "tester", "reviewer", "product-manager", "product-designer", "artist", "ui-kit", "copywriter", "growth",
          "release-manager", "investor"]


@pytest.fixture
def project(tmp_path):
    """A project with the parties of the crafts: Product, Design, Tech, Marketing, and a Release party."""
    root, state = tmp_path / "wiki", tmp_path / "state"
    library.install(state, AGENTS)

    def party(title, leader, team, craft):
        slug, _new = ideas.save_goal(root, None, title, "About " + title, None, "normal", craft=craft)
        goal_team.set_team(root, slug, team, None, leader)
        return slug

    p = {"product": party("Product", "product-manager", ["copywriter"], "product"),
         "design": party("Design", "product-designer", ["artist", "ui-kit"], "design"),
         "tech": party("Tech", "architect", ["grunt", "tester"], "engineering"),
         "marketing": party("Marketing", "growth", ["copywriter"], "marketing"),
         "release": party("Release", "release-manager", [], "engineering")}
    return root, state, p


def _parties(got):
    return [s["party"] for s in got["route"]]


def test_a_goal_addressed_to_a_party_is_routed_to_it_alone_whatever_it_says(project):
    root, state, p = project
    got = goal_route.route(state, root, "a new logo for the app", p["tech"])
    assert _parties(got) == [p["tech"]] and got["by"] == "party" and got["route"][0]["leader"] == "architect"
    assert got["short"] is False and got["offer"] == []


def test_a_bug_is_techs_alone_the_short_way_and_a_report_with_a_failure_reproduces(project):
    root, state, p = project
    got = goal_route.route(state, root, "Saving crashes when the file is empty")
    assert _parties(got) == [p["tech"]] and got["by"] == "code" and got["kind"] == "bug" and got["short"] is True and got["reproduces"] is False
    for report in ("The build fails:\nTraceback (most recent call last):\n  File \"app.py\", line 3\nValueError: no",
                   "Saving crashes, tests/test_save.py::test_it FAILED", "It breaks\n    at save (src/save.js:12:5)",
                   "Saving crashes with KeyError: 'x' in src/save.py"):
        again = goal_route.route(state, root, report)
        assert _parties(again) == [p["tech"]] and again["short"] and again["reproduces"] is True, report
    assert goal_route.reproduces("Error: it went wrong") is False and goal_route.reproduces("an error in the report") is False   # no path, no failure's lines
    assert goal_route.route(state, root, "the build is broken, FAILED", p["design"])["short"] is False       # a bug addressed to another party is not Tech's short way


def test_a_goal_is_routed_to_the_parties_its_kinds_name_in_the_craft_order_and_release_is_never_a_step(project):
    root, state, p = project
    assert _parties(goal_route.route(state, root, "add a settings screen")) == [p["design"]]       # the more specific kind wins over the general *feature*
    got = goal_route.route(state, root, "write a launch post for the new feature")
    assert _parties(got) == [p["product"], p["marketing"]] and got["by"] == "code" and got["short"] is False   # the product's craft, then the marketing's
    got = goal_route.route(state, root, "a new logo and a launch post")
    assert _parties(got) == [p["product"], p["design"], p["marketing"]]                           # product, the look, then marketing
    assert _parties(goal_route.route(state, root, "add a dark mode option")) == [p["tech"]]        # *feature*, which only Tech's architect takes
    for text in ("release a new version", "release", "submit the store listing for release"):
        assert p["release"] not in _parties(goal_route.route(state, root, text))
    assert p["release"] not in [x["slug"] for x in goal_route.parties(root)]


def test_the_person_edits_the_route_a_party_off_one_added_and_never_release(project):
    root, state, p = project
    current = [goal_route.entry(root, p["design"])]
    got = goal_route.edit(root, current, [p["design"], {"party": p["tech"]}, p["design"]])
    assert [s["party"] for s in got] == [p["design"], p["tech"]] and got[1]["leader"] == "architect"
    assert [s["party"] for s in goal_route.edit(root, got, [p["tech"]])] == [p["tech"]]
    for wanted, why in (([], "A route needs a party"), ("tech", "A route is a list of parties"), ([p["release"]], "Release is never a step"),
                        (["nope"], "That party is gone"), ([3], "A route is a list of parties")):
        with pytest.raises(ValueError, match=why):
            goal_route.edit(root, current, wanted)


def _routed(project, text="add a dark mode option", track=None, **state):
    root, state_dir, p = project
    got = goal_route.route(state_dir, root, text, track or "")
    slug = ideas.add_idea(root, text, got["route"][0]["party"] if got["route"] else p["tech"], state_dir)
    how = {k: got[k] for k in ("by", "kind", "short", "reproduces", "failure", "touched", "offer")}
    ideas.save_state(state_dir, slug, state="routed", route=got["route"], route_how=how, **state)
    return slug


def test_the_rows_sit_on_the_boards_needs_you_of_a_goal_and_a_node_names_them(project):
    root, state, p = project
    slug = _routed(project)
    (i,) = [x for x in ideas.ideas(root) if x["slug"] == slug]
    st = ideas.state(state, slug)
    needs = board_map.idea_needs(root, state, i, st, None, [], line={"order": {slug: 1}, "low": False})
    (route,) = needs
    assert route["kind"] == "route" and route["goal"] == p["tech"] and route["title"] == i["title"] and route["blocks"] is False
    assert "route" in board_map.NEEDS and "start" in board_map.NEEDS
    got = board_map.build(root, state, {}, [], dt.datetime(2026, 10, 28, 12, 0).timestamp(), rev=0)
    node = next(n for n in got["nodes"] if n["slug"] == slug)
    assert node["needs_you"] == "route" and node["place"] == "table" and node["asks_you"] is True and node["state"] == "routed"
    json.dumps(got)                                                                                          # all data


# -- spec 115 D: a bug's mark on the live product (docs/specs/115-the-live-product-under-each-leaders-eyes.md §5) ---------------------------------------------------------------------

def _play(state, slug, kind="bug", **more):
    from orkboard.realm import idea_play
    idea_play.save(state, slug, {"kind": kind, "text": "It does nothing", "path": "/orders", "box": {"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2}, **more})


def test_a_bug_with_a_mark_that_holds_an_error_or_a_failed_request_reproduces_the_short_way_with_no_diagnosis(project):
    root, state, p = project
    how = {"by": "party", "kind": "", "failure": False, "touched": False}
    route_ = [goal_route.entry(root, p["tech"])]
    assert goal_route.with_play(root, state, "g", how, route_) == how                                  # no play: as it was
    _play(state, "g")
    seen = goal_route.with_play(root, state, "g", how, route_)
    assert seen["kind"] == "bug" and seen["short"] is True and seen["reproduces"] is False             # a bug of Tech's alone, but its report holds no failure: Talk is its diagnosis
    _play(state, "g", errors=[{"message": "TypeError: x is undefined"}])
    seen = goal_route.with_play(root, state, "g", how, route_)
    assert seen["failure"] is True and seen["short"] is True and seen["reproduces"] is True            # the failure is kept: no diagnosis call
    _play(state, "h", requests=[{"method": "POST", "path": "/api/orders", "status": 500, "ms": 5}])
    assert goal_route.with_play(root, state, "h", how, route_)["reproduces"] is True
    assert goal_route.cost(state, route_, True, root=root, kind="bug", reproduces=True)["calls"] < goal_route.cost(state, route_, True, root=root, kind="bug")["calls"]


# -- spec 149 A: the route ----------------------------------------------------------------------------------------------------------------

def test_a_type_chosen_is_the_routes_kind_and_a_bug_chosen_stays_a_bug_with_or_without_its_lines(project):
    root, state, p = project
    line = "Predictions fixed per shape; the host says wrong rune\nTraceback (most recent call last):\n  File \"a.py\", line 1\nValueError: x"
    got = goal_route.route(state, root, line, p["tech"], chosen="shaped-feature")
    assert got["kind"] == "shaped-feature" and got["failure"] is False and got["short"] is False and got["reproduces"] is False       # the person's word, not the lines'
    assert goal_route.route(state, root, "a new look", p["tech"], chosen="bug")["kind"] == "bug"
    assert goal_route.route(state, root, "a new look", chosen="bug")["short"] is True
    old = goal_route.route(state, root, "Saving crashes", p["tech"])                                   # nothing chosen: the line says it, as before
    assert old["kind"] == "bug"
    assert goal_route.route(state, root, "Saving crashes", p["tech"], chosen="no-such-type")["kind"] == "bug"       # an unknown id is no choice


# -- spec 149 H.3: dollars only where there is a price ---------------------------------------------------------------------------------------


def test_the_cost_counts_calls_by_rule_and_prices_them_from_the_tiers_they_run_on(project, monkeypatch):
    root, state, p = project
    monkeypatch.setattr(idea_target, "floor", lambda tier, tool="claude": {"elder": 1.0, "warrior": 0.5, "laborer": 0.1}[tier])
    one = [goal_route.entry(root, p["tech"])]
    two = [*one, goal_route.entry(root, p["design"])]
    long_one = goal_route.cost(state, one, False, root=root)
    # balance: Talk (the cheaper tier's talk_round), the decision (the Orkmaster, warrior 0.5), the section (elder 1.0), the plan (elder 1.0), the leader's acceptance of its step (elder 1.0, spec 152 B.4), two tasks of a Grunt at its learned cost
    from orkboard.realm import idea_spend
    task = idea_spend.tier_costs(state)[idea_target.tier_of(idea_target.task_pick("warrior", "balance")[0])]
    talk = {"elder": 1.0, "warrior": 0.5, "laborer": 0.1}[idea_target.tier_of(idea_target.keeper_pick("talk_round", "balance", idea_target.TIER_ROLE)[0])]
    base = talk + 0.5 + 1.0 + 1.0 + 1.0 + goal_route.TASKS_PER_STEP * task
    assert long_one == {"calls": 5, "usd_low": round(base * 0.5, 2), "usd_high": round(base * 1.5, 2)}
    long_two = goal_route.cost(state, two, False, root=root)
    assert long_two["calls"] == 10 and long_two["usd_low"] > long_one["usd_low"] * 1.8             # a call a leader a round, a section each, the join, a plan and an acceptance each
    short = goal_route.cost(state, one, True, root=root, kind="bug")
    assert short["calls"] == 4 and short["usd_high"] < long_one["usd_high"]                       # the bug's diagnosis, the section, the plan, the acceptance: no decision
    assert goal_route.cost(state, one, True, root=root, kind="bug", reproduces=True)["calls"] == 3    # the report holds the failure: no Talk
    quality = goal_route.cost(state, one, False, root=root, settings={"target": "quality"})
    goal_team.set_size(root, p["tech"], "lean")                                                    # a party's size is no Target (spec 168 H4): the price is the same
    assert goal_route.cost(state, one, False, root=root, settings={"target": "quality"}) == quality
    goal_team.set_lead_tier(root, p["tech"], "laborer")                                            # its leader's own tier prices its own calls (Talk, its section, its acceptance)
    cheap = goal_route.cost(state, one, False, root=root, settings={"target": "quality"})
    assert cheap["calls"] == quality["calls"] and cheap["usd_high"] < quality["usd_high"]
    goal_team.set_lead_tier(root, p["tech"], "")
    assert goal_route.cost(state, [], False)["calls"] == 5                                         # a route not found yet is counted as one party's


def test_the_route_row_is_data_with_its_cost_place_and_flags(project):
    root, state, p = project
    slug = _routed(project)
    (i,) = [x for x in ideas.ideas(root) if x["slug"] == slug]
    st = ideas.state(state, slug)
    ctx = {"order": {slug: 3}, "low": True}
    (row,) = goal_route.rows(root, state, i, st, ctx)
    assert set(row) == {"kind", "idea", "route", "cost", "place", "short", "reproduces", "low", "offer", "type", "text"}
    assert row["type"] == "feature"                                                                          # no type kept: the kind its line was routed as
    assert row["kind"] == "route" and row["idea"] == slug and row["place"] == 3 and row["low"] is True and row["short"] is False and row["offer"] == []
    (step,) = row["route"]
    assert step["party"] == p["tech"] and step["leader"] == "architect" and set(step["head"]) == {"craft", "race", "tier"}
    assert set(row["cost"]) == {"calls", "usd_low", "usd_high"} and row["cost"]["calls"] == 5
    assert goal_route.rows(root, state, i, {**st, "held_until": "2026-10-28T14:00:00"}, ctx) == []         # put off with Later, by itself: nothing to decide
    assert goal_route.rows(root, state, i, {**st, "route": []}, ctx) == []                                   # still waiting for the call
    assert goal_route.rows(root, state, i, {**st, "state": "working"}, ctx) == []
