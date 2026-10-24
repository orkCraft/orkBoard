"""Spec 71 A (docs/specs/71-orkmaster-keeps-parties-apart.md §1, §2.1, §4, §8, Tests → A, the code side): what a goal touches (read and normalised),
the overlap with the open goals of other parties (no overlap, no call), the stop's shape on the Board and the Map, a wait across parties
held until the flag, the project's collisions. Code, no model (the judge: tests/test_idea_collide.py)."""
from __future__ import annotations

import json

import pytest

from orkboard.gui.board_host import CommandError
from orkboard.realm import board_map, collide, ideas
from tests.test_idea_route import events, flag, goal, host, party, pitch, wait_party  # noqa: F401  (`host`: the fixture of spec 68's route tests)

EARLY, LATE = "2026-10-24T09:00:00", "2026-10-24T10:00:00"


def planned(h, party_slug, text, touches, made_at=EARLY, done_when="", tasks=None, state="plan", **brief):
    """A goal of a party with a plan: it touches `touches` (its page's field), its plan was made at `made_at`."""
    slug = ideas.add_idea(h.root, text, party_slug, h.state)
    ideas.set_meta(h.root, slug, touches=json.dumps(touches))
    if done_when:
        ideas.set_section(h.root, slug, "Done when", done_when)
    ideas.save_state(h.state, slug, state=state)
    ideas.save_plan(h.state, slug, {"idea": slug, "made_at": made_at, "todos": [], "estimate": {},
                                    "tasks": tasks or [{"id": "k1", "title": "T1", "state": "ready", **brief}]})
    return slug


@pytest.fixture
def two(host):
    """Two parties' goals that both change how a session token is issued: Backend's (planned first) and the Mobile app's."""
    h = host
    h.api = planned(h, h.web, "Auth API", ["orkboard/realm/auth.py", "orkboard/realm/"], EARLY, "- a token is issued once")
    h.screen = planned(h, h.app, "Sign-in screen", ["orkboard/realm/auth.py", "app/screens/signin.js"], LATE, "- the screen asks for a token")
    return h


def node(h, slug):
    return next(n for n in h.command("ideas.map", {})["nodes"] if n["slug"] == slug)


def stop_of(h, a, b, by="plan", asked=None, why="Both change how a session token is issued", first=""):
    pair = collide.pair_id(a, b)
    asked = asked or collide.later_of(h.state, a, b)
    collide.add_open(h.state, pair, by, asked, b if asked == a else a, why, first)
    return pair


# -- §1: what a goal touches -----------------------------------------------------------------------------------------------

def test_touches_are_the_pages_the_plans_files_and_the_merged_files_normalised_and_read_never_written(host):
    h = host
    slug = planned(h, h.app, "Sessions", ["./orkboard\\realm\\x.py", "`orkboard/core/`", "orkboard/gui/*", "src/app", "some prose here", "", "*.py"],
                   tasks=[{"id": "k1", "title": "A", "state": "merged", "files": ["orkboard/design/ui.py"], "brief": "Edit `orkboard/zzz/skipped.py`."},
                          {"id": "k2", "title": "B", "state": "ready", "files": ["tests/test_x.py"],
                           "brief": "Change `orkboard/realm/y.py` and `README` and the folder `docs/specs/`."}])
    before = sorted((p, p.stat().st_mtime_ns) for p in list(h.root.rglob("*")) + list(h.state.rglob("*")) if p.is_file())
    got = collide.touches(h.root, h.state, slug)
    assert got == sorted(["orkboard/realm/x.py", "orkboard/core/", "orkboard/gui/", "src/app/", "orkboard/design/ui.py", "tests/test_x.py",
                          "orkboard/realm/y.py", "docs/specs/"])         # prose, a glob in the middle and an empty one are not paths; a merged task's brief is not read
    assert collide.touches(h.root, h.state, "nowhere") == []
    assert before == sorted((p, p.stat().st_mtime_ns) for p in list(h.root.rglob("*")) + list(h.state.rglob("*")) if p.is_file())      # read, never written


def test_a_module_and_its_folder_overlap_and_tests_and_docs_are_left_out_unless_both_are_only_docs():
    assert collide.shared(["orkboard/realm/x.py"], ["orkboard/realm/"]) == ["orkboard/realm/x.py"]
    assert collide.shared(["orkboard/realm/"], ["orkboard/"]) == ["orkboard/realm/"]
    assert collide.shared(["orkboard/realm/x.py"], ["orkboard/realm/y.py"]) == []                 # two modules in one folder are not the same thing
    assert collide.shared(["tests/test_a.py", "docs/a.md"], ["tests/test_a.py", "docs/a.md", "src/x.py"]) == []
    assert collide.shared(["docs/specs/", "src/a.py"], ["docs/specs/71.md"]) == []                # one of them touches code: docs are left out
    assert collide.shared(["docs/specs/", "README.md"], ["docs/specs/71.md"]) == ["docs/specs/71.md"]      # both only docs
    assert collide.shared([], ["src/"]) == []


# -- §2.1: the overlap, before the work; none, nothing more ---------------------------------------------------------------

def test_a_goal_overlaps_the_open_goals_of_other_parties_only(two):
    h = two
    assert collide.overlaps(h.root, h.state, h.api) == [{"other": h.screen, "paths": ["orkboard/realm/auth.py"]}]
    assert collide.overlaps(h.root, h.state, h.screen) == [{"other": h.api, "paths": ["orkboard/realm/auth.py"]}]
    same = planned(h, h.web, "Auth docs", ["orkboard/realm/auth.py"])                             # the same party: not another party's
    assert [o["other"] for o in collide.overlaps(h.root, h.state, h.api)] == [h.screen]
    assert [o["other"] for o in collide.overlaps(h.root, h.state, same)] == [h.screen]
    ideas.save_state(h.state, h.screen, state="done")                                              # done: not open
    assert collide.overlaps(h.root, h.state, h.api) == []
    ideas.save_state(h.state, h.screen, state="working")
    assert [o["other"] for o in collide.overlaps(h.root, h.state, h.api)] == [h.screen]
    releasing = planned(h, h.app, "Release 1.4", ["orkboard/realm/auth.py"])                       # a release: not a goal that changes things
    ideas._write_json(collide.releases._path(h.state, releasing), {"version": "1.4", "goals": [], "out": "", "at": "2026-10-24T08:00:00"})
    pit = pitch(h, "A pitch")
    ideas.set_meta(h.root, pit, touches=json.dumps(["orkboard/realm/auth.py"]))                   # a pitch: never built
    assert [o["other"] for o in collide.overlaps(h.root, h.state, h.api)] == [h.screen]
    nothing = planned(h, h.app, "Elsewhere", ["app/other/"])
    assert collide.overlaps(h.root, h.state, nothing) == [] and collide.overlaps(h.root, h.state, "nowhere") == []
    bare = goal(h, h.app, "Names none")                                                            # touches nothing: nothing to compare
    assert collide.overlaps(h.root, h.state, bare) == []


def test_the_later_goal_is_the_one_asked_about_by_its_plan_and_a_goal_with_no_plan_is_later(two):
    h = two
    assert collide.later_of(h.state, h.api, h.screen) == h.screen and collide.later_of(h.state, h.screen, h.api) == h.screen
    unplanned = goal(h, h.app, "Not planned yet")
    assert collide.later_of(h.state, h.api, unplanned) == unplanned and collide.later_of(h.state, unplanned, h.api) == unplanned
    assert collide.later_of(h.state, unplanned, goal(h, h.web, "Another")) == unplanned           # neither has a plan: the one just planned
    assert collide.pair_id(h.screen, h.api) == collide.pair_id(h.api, h.screen) == f"{h.api}|{h.screen}"


# -- §8.1: the stop on the Board and the Map ---------------------------------------------------------------------------------

def test_the_stop_is_a_needs_you_row_on_the_later_goal_with_the_shape_of_the_spec(two):
    h = two
    assert [n for n in h.command("ideas.board", {})["needs_you"] if n["kind"] == "collide"] == []
    pair = stop_of(h, h.api, h.screen, first=h.api)
    rows = [n for n in h.command("ideas.board", {})["needs_you"] if n["kind"] == "collide"]
    assert rows == [{
        "kind": "collide", "idea": h.screen, "goal": h.app, "title": "Sign-in screen", "priority": "normal", "blocks": False, "at": rows[0]["at"],
        "text": "Mobile app «Sign-in screen» and Website «Auth API» change the same thing",
        "collide": {"id": pair, "by": "plan", "why": "Both change how a session token is issued", "first": h.api,
                    "goals": [{"idea": h.api, "party": h.web, "party_name": "Website", "title": "Auth API", "element": rows[0]["collide"]["goals"][0]["element"]},
                              {"idea": h.screen, "party": h.app, "party_name": "Mobile app", "title": "Sign-in screen",
                               "element": rows[0]["collide"]["goals"][1]["element"]}],
                    "answers": [f"first:{h.api}", f"first:{h.screen}", "one", "leave"]}}]
    assert rows[0]["at"] and len(rows[0]["collide"]["why"]) <= 200
    assert pair == f"{h.api}|{h.screen}"


def test_a_stop_by_a_changed_spec_is_on_the_goal_whose_spec_did_not_change_and_says_replan_or_leave(two):
    h = two
    pair = stop_of(h, h.api, h.screen, by="change", asked=h.api, why="The token's shape changed", first="")
    row = next(n for n in h.command("ideas.board", {})["needs_you"] if n["kind"] == "collide")
    assert (row["idea"], row["goal"], row["title"]) == (h.api, h.web, "Auth API")
    assert row["text"] == "Mobile app changed «Sign-in screen»: «Auth API» in Website rests on what it was"
    assert [g["idea"] for g in row["collide"]["goals"]] == [h.screen, h.api]                         # goals[0] is the goal whose spec changed
    assert row["collide"]["answers"] == ["replan", "leave"] and row["collide"]["by"] == "change" and row["collide"]["id"] == pair


def test_the_stop_counts_in_the_snapshot_sorts_not_last_and_not_blocking_and_is_the_nodes_needs_you(two):
    h = two
    for slug in (h.api, h.screen):
        ideas.save_state(h.state, slug, state="working")                       # (a goal in `plan` says its plan first: NEEDS' order)
    h.ideas._cache = None
    before = h.ideas.snapshot()["needs_you"]
    assert node(h, h.screen)["needs_you"] == "" and "collide" in board_map.NEEDS
    stop_of(h, h.api, h.screen)
    h.ideas._cache = None
    assert h.ideas.snapshot()["needs_you"] == before + 1
    assert node(h, h.screen)["needs_you"] == "collide" and node(h, h.api)["needs_you"] == ""
    pitch(h, "A judged pitch")
    ideas.save_state(h.state, h.api, state="failed", error="Broke")
    kinds = [n["kind"] for n in h.command("ideas.board", {})["needs_you"]]
    assert sorted(kinds) == ["collide", "failed", "pitch"] and kinds[-1] == "pitch"        # as a plan's: among the goals' own rows, before a judged pitch


def test_a_stop_whose_goal_is_gone_or_done_is_not_shown(two):
    h = two
    stop_of(h, h.api, h.screen)
    ideas.save_state(h.state, h.api, state="done")
    assert [n for n in h.command("ideas.board", {})["needs_you"] if n["kind"] == "collide"] == []
    assert h.command("ideas.map", {})["project"]["collisions"] == []
    ideas.save_state(h.state, h.api, state="plan")
    h.command("ideas.drop", {"slug": h.api})
    assert [n for n in h.command("ideas.board", {})["needs_you"] if n["kind"] == "collide"] == []


def test_the_project_level_lists_the_open_collisions_on_every_map_and_none_without_a_file(two):
    h = two
    assert h.command("ideas.map", {})["project"]["collisions"] == []
    pair = stop_of(h, h.screen, h.api)
    want = [{"id": pair, "a": h.api, "b": h.screen}]                                                 # the pair sorted, as its id is
    assert h.command("ideas.map", {})["project"]["collisions"] == want
    assert h.command("ideas.map", {"goal": h.app})["project"]["collisions"] == want                 # the project's, whatever party the Map is of
    assert h.command("ideas.map", {})["project"]["collide_week"] == {"asked": 0, "answered": 0, "taken": 0, "usd": None}


# -- §4: a goal waits for another party's ---------------------------------------------------------------------------------

def test_a_node_says_what_it_waits_for_in_another_party_until_that_goals_flag(two):
    h = two
    assert node(h, h.screen)["waits_for"] == []
    ideas.set_meta(h.root, h.screen, depends_on=json.dumps([h.api, "gone-goal", h.screen]))
    assert node(h, h.screen)["waits_for"] == [{"goal": h.api, "party": h.web, "party_name": "Website", "title": "Auth API", "flag": ""}]
    assert h.command("ideas.map", {"goal": h.app})["nodes"][0]["waits_for"] == node(h, h.screen)["waits_for"]       # also a Map of one party
    flag(h, h.api, at="2026-10-24T12:00:00")
    assert node(h, h.screen)["waits_for"][0]["flag"] == "2026-10-24T12:00:00"
    inside = planned(h, h.app, "Second screen", ["app/x/"])
    ideas.set_meta(h.root, inside, depends_on=json.dumps([h.screen]))
    assert node(h, inside)["waits_for"] == [] and node(h, inside)["waits_on"] == [h.screen]         # a goal of its own party: spec 35's `waits_on`, not across parties


def test_a_goal_of_another_partys_depends_on_holds_its_start_until_the_flag_then_starts(two, monkeypatch):
    h = two
    started = []
    monkeypatch.setattr(h.ideas, "pass_plan", lambda slug, by, night=False, args=None: started.append((slug, by)))
    ideas.set_meta(h.root, h.screen, risk="low")
    assert h.ideas.autostart(h.screen) == "start" and started == [(h.screen, "auto")] and not collide.holds(h.root, h.state, h.screen)
    started.clear()
    ideas.set_meta(h.root, h.screen, depends_on=json.dumps([h.api]))
    assert collide.holds(h.root, h.state, h.screen) == [h.api] and collide.waiters(h.root, h.api) == [h.screen]
    assert h.ideas.autostart(h.screen) == "wait" and started == []                                   # held
    assert collide.holds(h.root, h.state, h.api) == []
    ideas.save_state(h.state, h.api, state="done")                                                    # done in dev, not in main: still held
    assert h.ideas.autostart(h.screen) == "wait" and started == []
    h.ideas._raise_flag(h.api, "done")                                                                # the flag: the waiting goal is decided again
    assert started == [(h.screen, "auto")] and collide.holds(h.root, h.state, h.screen) == []
    started.clear()
    ideas.set_meta(h.root, h.screen, depends_on=json.dumps(["gone-goal"]))                           # a goal that is gone holds nothing
    assert collide.holds(h.root, h.state, h.screen) == []


def test_a_dependency_joins_the_page_and_its_depends_on_section_and_never_closes_a_cycle(two):
    h = two
    assert collide.add_dependency(h.root, h.screen, h.api, "Auth API") is True
    assert collide.add_dependency(h.root, h.screen, h.api, "Auth API") is False
    page = ideas.idea_page(h.root, h.screen)
    assert json.loads(page.get("depends_on")) == [h.api] and f"- {h.api} — Auth API" in page.section("Depends on")
    assert collide.chain(h.root, h.screen) == {h.api} and h.screen not in collide.chain(h.root, h.api)
    assert not ideas.state(h.state, h.screen).get("changed")                                           # a wait changes no plan
    with pytest.raises(ValueError):
        collide.add_dependency(h.root, "nowhere", h.api, "x")


# -- §8.2: the command's refusals -------------------------------------------------------------------------------------------

def test_collide_answer_refuses_an_answered_pair_an_unknown_id_and_an_answer_the_stop_does_not_offer(two):
    h = two
    with pytest.raises(CommandError, match="No such question"):
        h.command("ideas.collide_answer", {"id": "a|b", "answer": "leave"})
    pair = stop_of(h, h.api, h.screen)
    for bad in ("replan", "first:somebody-else", "LEAVE", "first:"):
        with pytest.raises(CommandError, match="Pick one of its answers"):
            h.command("ideas.collide_answer", {"id": pair, "answer": bad})
    assert collide.open_of(h.state, pair) is not None                                                  # a refused answer leaves it open
    assert h.command("ideas.collide_answer", {"id": pair, "answer": "leave"}) == {"ok": True}
    with pytest.raises(CommandError, match="That is answered already"):
        h.command("ideas.collide_answer", {"id": pair, "answer": "leave"})
    assert collide.known(h.state, pair, "plan") and not collide.known(h.state, pair, "change") and collide.open_of(h.state, pair) is None


def test_the_last_two_hundred_answers_are_kept_and_the_open_ones_are_capped(host):
    h = host
    for n in range(230):
        collide.add_answered(h.state, f"a{n}|b{n}", "plan", "leave")
    kept = collide.read(h.state)["answered"]
    assert len(kept) == collide.KEEP == 200 and kept[0]["id"] == "a30|b30" and kept[-1]["id"] == "a229|b229"
    for n in range(60):
        collide.add_open(h.state, f"c{n}|d{n}", "plan", f"d{n}", f"c{n}", "why", "")
    assert len(collide.read(h.state)["open"]) == collide.OPEN_MAX == 50
