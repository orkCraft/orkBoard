"""Spec 68 A (docs/specs/68-release-and-route.md §2, §5, Tests → A): a goal's route (a pitch, a move, its party, its flag, a release, out), a
move only before the work starts and recorded, a sent pitch's element and its goal's state, the Map's `route` and `goal_state`. Code, no model."""
from __future__ import annotations

import json
import sys

import pytest

from orkboard.gui.board_host import CommandError, Orkboard
from orkboard.realm import board_map, event_log, goal_team, idea_flag, idea_route, ideas, library, pitches, releases

TEAM = [*library.VIEWS, library.SKEPTIC]
PITCH_AT = "2026-10-22T09:00:00"


def stub(tier, prompt, effort="", budget=None):
    """Any call of the keeper answered with an empty, valid JSON (a goal read, a draft): these tests judge no pitch."""
    return json.dumps({"summary": "", "questions": [], "title": "A goal"}), 0.01, 10, ""


def party(h, title, preset):
    lead, build, check = next((p[4], p[5], p[6]) for p in library.PRESETS if p[0] == preset)
    craft = next(p[3] for p in library.PRESETS if p[0] == preset)
    if preset == "ideation":                    # Ideation is no longer made by `ideas.goal_save` (spec 99 §1.1): a party of before, written as it was
        slug, _new = ideas.save_goal(h.ideas.root(), None, title, title + ".", craft=craft)
        library.install(h.ideas.state_dir, [lead, *build, *check])
        goal_team.set_team(h.ideas.root(), slug, [*build, *check], leader=lead)
        return slug
    slug = h.command("ideas.goal_save", {"title": title, "about": title + ".", "craft": craft, "leader": lead, "team": [*build[:1], *check[:1]], "preset": preset})["slug"]
    library.install(h.ideas.state_dir, [*build, *check])
    goal_team.set_team(h.ideas.root(), slug, [*build, *check])          # the library's whole party: made before a party had one seat a stage (spec 87 §5), its team kept
    wait_party(h, slug)
    return slug


def wait_party(h, slug):
    import time
    for _ in range(300):
        if not h.ideas.keeper.busy_goal(slug):
            return
        time.sleep(0.01)


def wait(h, slug):
    import time
    for _ in range(500):
        if not h.ideas.keeper.busy(slug):
            return
        time.sleep(0.01)


@pytest.fixture
def host(fake_repo):
    h = Orkboard(fake_repo)
    h.ideas.keeper.call = stub
    h.root, h.state = h.ideas.root(), h.ideas.state_dir
    h.app = party(h, "Mobile app", "mobile-app")
    h.web = party(h, "Website", "website")
    h.talk = party(h, "Ideation", "ideation")
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def goal(h, party_slug, text="Dark mode", state="raw", tasks=(), **more):
    slug = ideas.add_idea(h.root, text, party_slug, h.state)
    ideas.save_state(h.state, slug, state=state, **more)
    if tasks:
        ideas.save_plan(h.state, slug, {"idea": slug, "todos": [], "tasks": [{"id": f"t{n}", "title": f"T{n}", "state": s} for n, s in enumerate(tasks, 1)]})
    return slug


def flag(h, slug, at="2026-10-23T10:00:00", commit="c" * 40):
    ideas._write_json(idea_flag.flag_path(h.state, slug), {"at": at, "by": "gate", "commit": commit, "tasks": 2, "first_time": 2, "usd": None, "days": 1})


def pitch(h, text="A pitch", answer="invest", **more):
    slug = ideas.add_idea(h.root, text, h.talk, h.state)
    ideas.save_state(h.state, slug, state="judged")
    pitches.save(h.state, slug, decision={"answer": answer, "why": ["It is cheap."], "where": {"party": h.app, "type": ""}, "first": "", "test": "",
                                         "kills": [], "like": "", "reshaped": False}, judged_at=PITCH_AT)
    return slug


def events(h, name):
    return [r for r in event_log.read(h.ideas.host.repo_root) if r["event"] == name]


# -- §2.1: the route, oldest first -----------------------------------------------------------------------------------------

def test_a_route_reads_the_pitch_the_move_the_party_the_flag_the_release_and_out_in_that_order(host):
    h = host
    src = pitch(h, "Dark mode for the night shift")
    slug = goal(h, h.app, "Dark mode", state="working", tasks=("merged", "merged", "running"), from_pitch=src)
    assert idea_route.route(h.root, h.state, slug) == [
        {"step": "pitch", "party": h.talk, "goal": src, "at": PITCH_AT, "answer": "invest", "word": "Invest", "title": "Dark mode for the night shift"},
        {"step": "party", "party": h.app, "goal": slug, "at": "", "state": "working", "done": 2, "total": 3}]
    ideas.save_state(h.state, slug, state="plan")                                          # not started: it may move
    ideas.save_plan(h.state, slug, {"idea": slug, "todos": [], "tasks": [{"id": "t1", "state": "ready"}]})
    got = idea_route.move(h.root, h.state, slug, h.web, None, "person")
    assert got == {"from": h.app, "to": h.web, "moved": True}
    moved = idea_route.moves(h.state, slug)
    assert len(moved) == 1 and (moved[0]["from"], moved[0]["to"], moved[0]["by"]) == (h.app, h.web, "person") and moved[0]["at"]
    ideas.save_state(h.state, slug, state="done")
    flag(h, slug)
    rel = goal(h, h.app, "Release 1.4")
    ideas._write_json(releases._path(h.state, rel), {"version": "1.4", "goals": [slug], "out": "", "at": "2026-10-24T08:00:00"})
    route = idea_route.route(h.root, h.state, slug)
    assert [s["step"] for s in route] == ["pitch", "moved", "party", "main", "release"]
    assert route[1] == {"step": "moved", "party": h.app, "goal": slug, "at": moved[0]["at"], "from": h.app, "to": h.web}
    assert route[2] == {"step": "party", "party": h.web, "goal": slug, "at": moved[0]["at"], "state": "done", "done": 0, "total": 1}
    assert route[3] == {"step": "main", "party": h.web, "goal": slug, "at": "2026-10-23T10:00:00", "by": "gate"}
    assert route[4] == {"step": "release", "at": "2026-10-24T08:00:00", "goal": rel, "party": h.app, "version": "1.4", "out": ""}
    ideas._write_json(releases._path(h.state, rel), {"version": "1.4", "goals": [slug], "out": "2026-10-26T09:00:00", "at": "2026-10-24T08:00:00"})
    last = idea_route.route(h.root, h.state, slug)[-1]
    assert (last["step"], last["version"], last["out"], last["at"]) == ("release", "1.4", "2026-10-26T09:00:00", "2026-10-26T09:00:00")


def test_a_goal_with_only_its_party_step_has_no_route_and_a_dropped_pitch_leaves_none(host):
    h = host
    plain = goal(h, h.app, "Plain")
    assert idea_route.route(h.root, h.state, plain) == [] and [s["step"] for s in idea_route.steps(h.root, h.state, plain)] == ["party"]
    src = pitch(h)
    sent = goal(h, h.app, "Sent", from_pitch=src)
    assert [s["step"] for s in idea_route.route(h.root, h.state, sent)] == ["pitch", "party"]
    ideas.drop(h.root, src, h.state)
    assert idea_route.route(h.root, h.state, sent) == []
    nodes = {n["slug"]: n for n in board_map.build(h.root, h.state, {}, [], 0.0)["nodes"]}
    assert nodes[plain]["route"] == [] and nodes[sent]["route"] == []


# -- §2.2: a move only before the work starts, recorded -------------------------------------------------------------------

def test_a_goal_moves_before_its_work_starts_and_a_started_one_is_refused_in_the_words_of_the_spec(host):
    h = host
    refusal = "Its work has started in Mobile app: a goal moves only before its work starts. Add a new goal there."
    for tasks, state, more in ((("merged",), "plan", {}), (("running",), "plan", {}), (("testing",), "plan", {}), (("review",), "plan", {}),
                               (("failed",), "plan", {}), (("waiting",), "working", {}), ((), "done", {})):
        slug = goal(h, h.app, f"Started {tasks}{state}", state=state, tasks=tasks)
        with pytest.raises(ValueError) as e:
            idea_route.move(h.root, h.state, slug, h.web, None, "person")
        assert str(e.value) == refusal and ideas.idea_page(h.root, slug).get("track") == h.app and idea_route.moves(h.state, slug) == []
    passed = goal(h, h.app, "Plan passed", state="plan", tasks=("waiting", "ready"))
    ideas.edit_plan(h.state, passed, lambda p: p.update(passed_at="2026-10-23T09:00:00"))
    with pytest.raises(ValueError, match="Its work has started"):
        idea_route.move(h.root, h.state, passed, h.web)
    for state in ("raw", "ready", "asks", "plan"):                                          # a draft and a plan not yet passed
        slug = goal(h, h.app, f"Before {state}", state=state, tasks=("waiting", "ready") if state == "plan" else ())
        assert idea_route.move(h.root, h.state, slug, h.web)["moved"] is True and ideas.idea_page(h.root, slug).get("track") == h.web


def test_ideas_move_goes_through_the_route_keeps_the_element_and_says_idea_moved_without_the_goals_words(host):
    h = host
    slug = goal(h, h.app, "SECRET-WORDS in a goal")
    ideas.save_state(h.state, slug, element="lava")
    assert h.command("ideas.move", {"slug": slug, "track": h.web}) == {"ok": True}
    assert ideas.idea_page(h.root, slug).get("track") == h.web and ideas.state(h.state, slug)["element"] == "lava"
    assert ideas.idea_page(h.root, slug).get("placed") == "person"
    (ev,) = events(h, event_log.IDEA_MOVED)
    assert (ev["goal"], ev["from"], ev["to"], ev["device"]) == (slug, h.app, h.web, "desktop") and "SECRET-WORDS" not in json.dumps(ev)
    other = goal(h, h.app, "Another")
    h.command("ideas.move", {"slug": other})                                                 # its order only: nothing said
    assert len(events(h, event_log.IDEA_MOVED)) == 1
    ideas.save_state(h.state, other, state="working")
    with pytest.raises(CommandError, match="Its work has started in Mobile app: a goal moves only before its work starts. Add a new goal there."):
        h.command("ideas.move", {"slug": other, "track": h.web})
    assert ideas.idea_page(h.root, other).get("track") == h.app and len(events(h, event_log.IDEA_MOVED)) == 1
    assert event_log.IDEA_MOVED in event_log.EVENTS


# -- §2.3: a sent pitch's goal keeps its element when it is free -----------------------------------------------------------


# -- §2.4: a sent pitch follows its goal ------------------------------------------------------------------------------------


def test_the_route_of_a_sent_goal_is_on_the_map_with_the_pitch_the_goal_came_from(host):
    h = host
    src = pitch(h, "Night mode")
    slug = h.command("ideas.pitch_send", {"slug": src, "party": h.app})["slug"]
    wait(h, slug)
    node = next(n for n in h.command("ideas.map", {})["nodes"] if n["slug"] == slug)
    assert [s["step"] for s in node["route"]] == ["pitch", "party"]
    assert (node["route"][0]["goal"], node["route"][0]["party"], node["route"][0]["answer"]) == (src, h.talk, "invest")
    assert node["route"][1]["party"] == h.app


# -- spec 99 §9: the work by steps, each step history ---------------------------------------------------------------------------------------

def stepped(h, slug, steps, route=None, passed=True):
    """A goal at work on a route (default: Mobile app, then Website), its plan holding `steps`: [(task id, step, state)]."""
    route = route or [h.app, h.web]
    ideas.save_state(h.state, slug, state="working", route=[{"party": p, "leader": ""} for p in route])
    ideas._write_json(ideas.state_folder(h.state, slug) / "plan.json", {"idea": slug, "todos": [], **({"route": [{"party": p, "leader": ""} for p in route]} if len(route) > 1 else {}),
                                    **({"passed_at": "2026-10-28T09:00:00"} if passed else {}),
                                    "tasks": [{"id": i, "title": i.upper(), "state": s, "step": n} for i, n, s in steps]})


def test_a_route_of_two_steps_or_more_has_a_party_step_for_each_the_ones_done_the_one_at_work_and_the_ones_to_come(host):
    h = host
    slug = goal(h, h.app, "Dark mode")
    stepped(h, slug, [("k1", 1, "running"), ("k2", 1, "merged")])
    idea_route.begin(h.state, slug, 1, h.app, "", ["k1", "k2"])
    legs = lambda: [{k: s[k] for k in ("party", "state", "done", "total", "n", "of")} for s in idea_route.route(h.root, h.state, slug)]      # noqa: E731
    assert legs() == [{"party": h.app, "state": "working", "done": 1, "total": 2, "n": 1, "of": 2}, {"party": h.web, "state": "waiting", "done": 0, "total": 0, "n": 2, "of": 2}]
    first = idea_route.route(h.root, h.state, slug)[0]
    assert first["step"] == "party" and first["at"] == idea_route.recorded(h.state, slug)[0]["at"] and first["goal"] == slug
    stepped(h, slug, [("k1", 1, "merged"), ("k2", 1, "merged")])
    assert [(s["state"], s["n"]) for s in idea_route.route(h.root, h.state, slug)] == [("done", 1), ("working", 2)]            # the next step's turn, not planned yet
    stepped(h, slug, [("k1", 1, "merged"), ("k2", 2, "waiting")])
    ideas.save_state(h.state, slug, state="done")
    assert [(s["state"], s["done"], s["total"]) for s in idea_route.route(h.root, h.state, slug)] == [("done", 1, 1), ("done", 0, 1)]
    solo = goal(h, h.app, "One step", state="working", tasks=("merged", "running"))
    ideas.save_state(h.state, solo, route=[{"party": h.app, "leader": ""}])
    assert idea_route.route(h.root, h.state, solo) == [] and idea_route.steps(h.root, h.state, solo)[0].get("n") is None                  # a route of one step is today's


# -- spec 152 B.1: a step is accepted by its leader before the goal goes on or ends -------------------------------------------------------------

def _stepped_plan(*tasks, accepts=None, route=2):
    plan = {"passed_at": "x", "tasks": [{"id": f"k{i}", "step": step, "state": state} for i, (step, state) in enumerate(tasks, start=1)],
            "route": [{"party": f"p{n}", "leader": ""} for n in range(route)] if route > 1 else None}
    if accepts is not None:
        plan["accepts"] = accepts
    return {k: v for k, v in plan.items() if v is not None}


