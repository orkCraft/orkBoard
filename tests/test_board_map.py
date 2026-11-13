"""Spec 39 A (docs/specs/39-map.md, Tests → A): the Map's data on a fixture board, `ideas.map` on the host and the phone,
and `opened` with `via`. Code, no model."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from orkboard.gui.board_host import BoardPhone, CommandError, Orkboard
from orkboard.realm import board_map, event_log, goal_team, idea_change, idea_questions, ideas, library, map_party, spec_sections


@pytest.fixture
def host(fake_repo) -> Orkboard:
    return Orkboard(fake_repo)


def _goal(root, title, priority="normal", metrics=None):
    slug, _new = ideas.save_goal(root, None, title, "About " + title, metrics, priority)
    return slug


def _idea(root, state_dir, goal, text, state="ready", depends=(), **more):
    slug = ideas.add_idea(root, text, goal, state_dir)
    if depends:
        ideas.set_meta(root, slug, depends_on=json.dumps(list(depends)))
    ideas.save_state(state_dir, slug, state=state, **more)
    return slug


def _plan(state_dir, slug, tasks, **more):
    folder = state_dir / "ideas" / slug
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "plan.json").write_text(json.dumps({"idea": slug, "made_at": "2026-10-18T09:00:00", "todos": [],
                                                  "tasks": tasks, **more}))


def _t(tid, state, after=(), note=""):
    return {"id": tid, "title": f"Task {tid}", "tier": "warrior", "state": state, "after": list(after), "note": note}


def _roles(state, *slugs):
    """Library agents as roles of the project (a party's members are roles of it)."""
    library.install(state, list(slugs))


def _board(host):
    ideas_ = host.ideas
    return ideas_.root(), ideas_.state_dir


def _node(got, slug):
    return next(n for n in got["nodes"] if n["slug"] == slug)


@pytest.fixture
def fixture(host):
    root, state = _board(host)
    one = _goal(root, "Speed", "high", [{"name": "done when it is fast", "target": "1s", "how": "a test"}])
    two = _goal(root, "Docs")
    a = _idea(root, state, one, "Cache the table", "done")
    b = _idea(root, state, one, "Index the runs", "working", depends=[a])
    c = _idea(root, state, one, "Page the runs", "ready", depends=[a, b])
    d = _idea(root, state, two, "Write the guide", "ready", depends=[c])        # another goal's idea: no edge
    loose = _idea(root, state, ideas.GENERAL, "A loose idea", "ready")
    return host, root, state, {"one": one, "two": two, "a": a, "b": b, "c": c, "d": d, "loose": loose}


def test_goals_nodes_tiers_and_edges(fixture):
    host, root, state, f = fixture
    got = host.command("ideas.map", {})
    assert [g["slug"] for g in got["goals"]] == [f["one"], f["two"]] and f["loose"] not in {n["slug"] for n in got["nodes"]}
    assert (_node(got, f["a"])["tier"], _node(got, f["b"])["tier"], _node(got, f["c"])["tier"]) == (1, 2, 3)   # two parents: the deeper
    assert _node(got, f["d"])["tier"] == 1 and _node(got, f["d"])["depends_on"] == [f["c"]]
    assert {(e["from"], e["to"]) for e in got["edges"]} == {(f["a"], f["b"]), (f["a"], f["c"]), (f["b"], f["c"])}
    assert [n["slug"] for n in got["nodes"] if n["goal"] == f["one"]] == [f["a"], f["b"], f["c"]]
    g = got["goals"][0]
    assert g["done_when"] == ["done when it is fast"] and (g["ideas"], g["done"]) == (3, 1) and g["priority"] == "high"
    assert got["rev"] == host.ideas.rev


def test_one_goal_and_a_goal_that_is_gone(fixture):
    host, _root, _state, f = fixture
    got = host.command("ideas.map", {"goal": f["two"]})
    assert [g["slug"] for g in got["goals"]] == [f["two"]] and {n["goal"] for n in got["nodes"]} == {f["two"]}
    for bad in ("nope", ideas.GENERAL):
        with pytest.raises(CommandError, match="That party is gone"):
            host.command("ideas.map", {"goal": bad})


def test_a_node_carries_its_boards_row_for_every_state(host):
    root, state = _board(host)
    g = _goal(root, "Every state")
    slugs = [_idea(root, state, g, f"Idea {s}", s) for s in ideas.STATES]
    _plan(state, slugs[ideas.STATES.index("working")], [_t("k1", "merged"), _t("k2", "running")], start_at="night")
    row_of = {r["slug"]: r for r in host.command("ideas.board")["ideas"]}
    nodes = {n["slug"]: n for n in host.command("ideas.map", {})["nodes"]}
    assert set(nodes) == set(row_of)
    for slug, n in nodes.items():
        for k in ("state", "queue", "held_until", "start_at", "priority", "size", "risk", "depends_on", "waits_on",
                  "progress", "updated", "place", "asks_you", "waits_as", "seen"):
            assert n[k] == row_of[slug][k], (slug, k)


def test_waits_come_in_the_specs_order(host):
    root, state = _board(host)
    g = _goal(root, "Waits")
    base = _idea(root, state, g, "Base idea", "working")
    other = _idea(root, state, g, "Other idea", "working")
    plan_only = {"made_at": "2026-10-18T09:00:00"}

    waiting = _idea(root, state, g, "Waits for base", "plan", depends=[base])        # a plan waiting: you, before idea
    _plan(state, waiting, [_t("k1", "ready")], **plan_only)
    follower = _idea(root, state, g, "Follows base", "ready", depends=[base])
    files = _idea(root, state, g, "Same files", "working")
    _plan(state, files, [_t("k1", "held", note=f"files · {other}")], passed_at="x")
    limits = _idea(root, state, g, "Limits", "working")
    _plan(state, limits, [_t("k1", "held", note="after 18:00")], passed_at="x")
    reserve = _idea(root, state, g, "Reserve", "working")
    _plan(state, reserve, [_t("k1", "held", note="reserve · after 19:30")], passed_at="x")
    held = _idea(root, state, g, "Held keeper", "raw", queue="now", held_until="2026-10-19T20:00:00")
    night = _idea(root, state, g, "Tonight", "raw", queue="night")
    night_plan = _idea(root, state, g, "Night plan", "working")
    _plan(state, night_plan, [_t("k1", "ready")], start_at="night", passed_at="x")
    stopped = _idea(root, state, g, "Stopped", "raw", queue="hold")
    free = _idea(root, state, g, "Free", "working")
    _plan(state, free, [_t("k1", "running")], passed_at="x")

    n = {x["slug"]: x for x in host.command("ideas.map", {})["nodes"]}
    none = {"ref": "", "title": "", "until": ""}
    assert n[waiting]["waits"] == {"kind": "you", **none} and n[waiting]["needs_you"] == "plan"
    assert n[follower]["waits"] == {"kind": "idea", "ref": base, "title": "Base idea", "until": ""} and n[follower]["needs_you"] == ""
    assert n[files]["waits"] == {"kind": "files", "ref": other, "title": "Other idea", "until": ""}
    assert n[limits]["waits"] == {"kind": "limits", "ref": "", "title": "", "until": "18:00"}
    assert n[reserve]["waits"] == {"kind": "reserve", "ref": "", "title": "", "until": "19:30"}
    assert n[held]["waits"] == {"kind": "limits", "ref": "", "title": "", "until": "2026-10-19T20:00:00"}
    assert n[night]["waits"]["kind"] == "stopped" and n[night]["queue"] == "hold" and n[night_plan]["waits"]["kind"] == "night"      # a raw `night` is held (spec 99 §3)
    assert n[stopped]["waits"]["kind"] == "stopped"
    assert n[free]["waits"] is None and n[base]["waits"] is None


def test_needs_you_names_the_kind(host):
    root, state = _board(host)
    g = _goal(root, "Needs")
    asks = _idea(root, state, g, "Asks", "asks")
    proposed = _idea(root, state, g, "Proposed", "proposed")
    failed = _idea(root, state, g, "Failed", "failed", error="boom")
    todo = _idea(root, state, g, "Todo", "working")
    _plan(state, todo, [_t("k1", "ready")], passed_at="x", todos=[{"id": "t1", "title": "Paste the key", "kind": "secret", "for": ["k1"]}])
    n = {x["slug"]: x for x in host.command("ideas.map", {})["nodes"]}
    assert (n[asks]["needs_you"], n[proposed]["needs_you"], n[failed]["needs_you"], n[todo]["needs_you"]) == \
        ("asks", "proposal", "failed", "todo")
    assert all(n[s]["waits"]["kind"] == "you" for s in (asks, proposed, failed, todo))
    # spec 41 §9: an asking idea's row carries each question's choices, pick and why; its line is the ask alone
    ideas.set_section(root, asks, "Open questions", "- Which store first? (**App Store** / Google Play) — iPhone first")
    row = next(r for r in host.command("ideas.board")["needs_you"] if r.get("idea") == asks)
    assert row["text"] == "Which store first?" and row["asked"] == [
        {"ask": "Which store first?", "choices": ["App Store", "Google Play"], "kinds": ["other", "other"], "pick": 0, "why": "iPhone first", "look": False}]


def test_a_dropped_task_is_not_a_failure_in_the_hand_and_not_a_task_to_do(host):
    """The owner's 26 October: a card of a failed task stayed in the hand after Drop in the ticket itself."""
    root, state = _board(host)
    g = _goal(root, "Dropped")
    slug = _idea(root, state, g, "Idea", "working")
    tasks = [_t("k1", "dropped"), _t("k2", "waiting"), _t("k3", "merged")]
    _plan(state, slug, tasks, passed_at="x", todos=[{"id": "t1", "title": "Paste the key", "kind": "secret", "for": ["k1"]}])
    i = next(x for x in ideas.ideas(root) if x["slug"] == slug)

    def kinds():
        return [n["kind"] for n in board_map.idea_needs(root, state, i, ideas.state(state, slug), ideas.plan(state, slug), [])]
    assert kinds() == []                                                       # it waits for nothing: no failed stop, no to-do for a task gone
    _plan(state, slug, [_t("k1", "failed"), *tasks[1:]], passed_at="x")
    assert kinds() == ["failed"]                                               # a task that failed for real is still a stop
    _plan(state, slug, [{**_t("k1", "failed"), "error": "dropped by you"}, *tasks[1:]], passed_at="x")
    assert kinds() == []                                                       # a plan written before a dropped task had its own state
    ideas.save_state(state, slug, state="failed", error="Task k1: dropped by you")
    assert kinds() == []                                                       # … and the goal that failed over it needs no one
    _plan(state, slug, [_t("k1", "dropped"), _t("k2", "failed")], passed_at="x")
    assert kinds() == ["failed"]                                               # another task failed for real: the goal's stop stays
    _plan(state, slug, [_t("k1", "dropped"), _t("k2", "merged")], passed_at="x")
    node = next(n for n in host.command("ideas.map", {})["nodes"] if n["slug"] == slug)
    assert node["progress"] == {"done": 1, "total": 1} and [t["state"] for t in node["tasks"]] == ["dropped", "merged"]      # a dropped task is not counted


def test_the_command_is_the_phones_too_and_needs_a_project():
    assert BoardPhone.allowed(Orkboard(), "ideas.map", {})
    with pytest.raises(CommandError, match="Open a folder first"):
        Orkboard().command("ideas.map", {})


def test_opened_with_via_is_written_and_an_old_line_reads_empty(host):
    host.command("ideas.log", {"event": "opened", "what": "map"})
    host.command("ideas.log", {"event": "opened", "what": "idea", "ref": "x", "via": "map"})
    with pytest.raises(CommandError, match="via"):
        host.command("ideas.log", {"event": "opened", "what": "idea", "ref": "x", "via": "elsewhere"})
    rows = [r for r in event_log.read(Path(host.town.repo_root)) if r["event"] == "opened"]
    assert [(r["what"], r.get("via")) for r in rows] == [("map", ""), ("idea", "map")]
    event_log.path(Path(host.town.repo_root)).open("a", encoding="utf-8").write(
        json.dumps({"at": "2026-10-01T09:00:00", "event": "opened", "what": "idea", "ref": "old", "device": "desktop"}) + "\n")
    assert event_log.read(Path(host.town.repo_root))[-1]["via"] == ""


def test_a_goal_accepted_has_its_verdict_at_and_a_met_one_its_tally_spec_42(fixture):
    from orkboard.realm import goal_verdict
    host, root, state, f = fixture
    goal_verdict.save(state, f["one"], {"met": True, "verdict": "x"}, by="Product manager")
    goal_verdict.save(state, f["two"], {"met": False, "verdict": "x"}, by="Growth")
    got = {g["slug"]: g for g in host.command("ideas.map", {})["goals"]}
    met, no = got[f["one"]]["verdict"], got[f["two"]]["verdict"]
    assert met["at"] and met["met"] is True and set(met["tally"]) == {"ideas", "results", "first_time", "usd", "days"}
    assert met["tally"]["ideas"] == 1                                  # "Cache the table" is done
    assert no["at"] and "tally" not in no


# -- spec 48 A: the stage, the party's states, the idea's card ------------------------------------------------------

def test_a_node_has_its_stage_round_spend_and_estimate_spec_48(host):
    root, state = _board(host)
    g = _goal(root, "Stages")
    est = {"tasks": 2, "usd_low": 0.4, "usd_high": 1.2}
    raw = _idea(root, state, g, "Raw", "raw")
    waiting = _idea(root, state, g, "Waiting", "plan")
    _plan(state, waiting, [_t("k1", "ready")], estimate=est)
    building = _idea(root, state, g, "Building", "working")
    _plan(state, building, [{**_t("k1", "merged"), "round": 1}, {**_t("k2", "running", after=["k1"]), "round": 2}], estimate=est, passed_at="x")
    _roles(state, "reviewer")
    check = _t("k9", "ready", after=["k1"])
    checking = _idea(root, state, g, "Checking", "working")
    _plan(state, checking, [_t("k1", "merged"), {**check, "kind": "review", "role": "reviewer"}], passed_at="x", estimate=est)
    done = _idea(root, state, g, "Done", "done")
    n = {x["slug"]: x for x in host.command("ideas.map", {})["nodes"]}
    assert [n[s]["stage"] for s in (raw, waiting, building, checking, done)] == ["planning", "planning", "implementation", "checking", "done"]
    assert (n[building]["round"], n[raw]["round"]) == (2, 1)
    assert n[raw]["usd"] is None and n[raw]["plan_estimate"] is None
    assert n[building]["plan_estimate"] == {"usd_low": 0.4, "usd_high": 1.2} and n[building]["estimate"] is None     # `estimate` is before it starts
    assert n[waiting]["plan_estimate"] == n[waiting]["estimate"]
    assert [(t["wave"], t["band"]) for t in n[checking]["tasks"]] == [(1, "build"), (2, "check")]
    assert n[checking]["tasks"][1]["by"]["slug"] == "reviewer"


def test_the_partys_states_and_todays_merges_spec_48(host):
    root, state = _board(host)
    g = _goal(root, "Party")
    _roles(state, "reviewer", "architect")
    goal_team.set_team(root, g, ["grunt", "reviewer"], leader="architect")
    hot = _idea(root, state, g, "Hot", "working")
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    _plan(state, hot, [{**_t("k1", "merged"), "finished": now, "cost": 0.3}, _t("k2", "running", after=["k1"]),
                       {**_t("k3", "ready", after=["k2"]), "kind": "review", "role": "reviewer"}], passed_at="x")
    got = host.command("ideas.map", {"goal": g})["goals"][0]
    states = {m["slug"]: (m["state"], m["why"], m["band"]) for m in got["party"]}
    assert states["grunt"] == ("work", "", "build") and states["reviewer"] == ("next", "", "check") and states["architect"][0] == "free"
    assert got["today"] == {"merged": 1, "usd": 0.3}
    ideas.save_state(state, hot, state="plan")
    _plan(state, hot, [_t("k1", "ready")])
    assert {m["slug"]: m["state"] for m in host.command("ideas.map", {"goal": g})["goals"][0]["party"]}["architect"] == "needs"
    ideas.save_state(state, hot, state="working")
    _plan(state, hot, [_t("k1", "failed")], passed_at="x")
    got = {m["slug"]: (m["state"], m["why"]) for m in host.command("ideas.map", {"goal": g})["goals"][0]["party"]}
    assert got["grunt"] == ("needs", "failed")


def test_a_task_that_waits_for_a_pick_is_picking_with_its_pick_and_its_member_and_goal_wait_for_you_spec_51(host):
    root, state = _board(host)
    g = _goal(root, "Brand")
    _roles(state, "architect")
    goal_team.set_team(root, g, ["grunt"], leader="architect")
    slug = _idea(root, state, g, "A logo", "working")
    logo = {**_t("k1", "picking"), "round": 2, "pick": {"n": 4, "kind": "audio", "ask": "A jingle", "target": "assets/jingle.mp3"}}
    _plan(state, slug, [logo, _t("k2", "waiting", after=["k1"])], passed_at="x")
    got = host.command("ideas.map", {"goal": g})
    node = got["nodes"][0]
    assert [(t["id"], t["state"], t["pick"]) for t in node["tasks"]] == [("k1", "picking", {"n": 4, "media": "audio", "round": 2}), ("k2", "waiting", None)]
    assert node["waits"] == {"kind": "you", "ref": "", "title": "", "until": ""} and node["stage"] == "implementation"
    assert {m["slug"]: (m["state"], m["why"]) for m in got["goals"][0]["party"]}["grunt"] == ("needs", "pick")
    _plan(state, slug, [{**logo, "state": "running"}, _t("k2", "waiting", after=["k1"])], passed_at="x")        # no longer picking: no pick, no wait
    node = host.command("ideas.map", {"goal": g})["nodes"][0]
    assert node["tasks"][0]["pick"] is None and node["waits"] is None


# -- spec 49 A: what a task's run left, and the recommended answer --------------------------------------------------

def test_a_node_has_its_element_and_its_flag_and_a_party_its_flags_waits_and_brief_spec_50(host):
    from orkboard.realm import idea_flag
    root, state = _board(host)
    g = _goal(root, "Speed")
    other = _goal(root, "Docs")
    flagged = _idea(root, state, g, "Cache the table", "done")
    waiting = _idea(root, state, g, "Index the runs", "done")
    open_one = _idea(root, state, g, "Page the runs", "working", element="lava")
    _idea(root, state, other, "Write the guide", "done")
    _plan(state, flagged, [_t("k1", "merged"), _t("k2", "merged")])
    pure = board_map.build(root, state, {}, [], time.time(), rev=0)                               # the pure read gives none: it writes nothing
    assert {n["slug"]: n["element"] for n in pure["nodes"]} == {n["slug"]: "" if n["slug"] != open_one else "lava" for n in pure["nodes"]}
    assert all(n["flag"] is None for n in pure["nodes"]) and all((p["flags"], p["waits_main"]) == (0, 1 if p["slug"] == other else 2) for p in pure["goals"])
    flag = idea_flag.raise_flag(root, state, flagged, "gate", "c" * 40)
    got = host.command("ideas.map", {})
    nodes = {n["slug"]: n for n in got["nodes"]}
    assert nodes[flagged]["flag"] == {**flag, "release": None} and set(flag) == {"at", "by", "commit", "tasks", "first_time", "usd", "days"} and flag["tasks"] == 2
    assert nodes[waiting]["flag"] is None and nodes[open_one]["flag"] is None
    assert all(n["element"] in ("meadow", "ice", "dust", "void", "lava") for n in nodes.values()) and nodes[open_one]["element"] == "lava"
    parties = {p["slug"]: p for p in got["goals"]}
    assert (parties[g]["flags"], parties[g]["waits_main"]) == (1, 1)                              # one flagged; one done, waiting for main; one at work
    assert (parties[other]["flags"], parties[other]["waits_main"]) == (0, 1)
    json.dumps(got)


def test_a_plan_change_waiting_is_one_stop_of_kind_change_beside_the_plans_spec_62(host):
    """Spec 62 §4.1–§4.2: while `plan_change.json` is there and can be taken, a stop `{idea, goal, title, priority, blocks: false, at: made_at, kind:
    "change", text, why, added, changed, dropped, usd_low, usd_high}`; the Map's node keeps its needs_you; the hand sorts it as a plan."""
    root, state = _board(host)
    g = _goal(root, "Speed")
    slug = _idea(root, state, g, "Cache the table", "working", priority="normal")
    planning = _idea(root, state, g, "Index the runs", "plan")
    _plan(state, slug, [_t("k1", "merged"), _t("k2", "ready", ["k1"]), _t("k3", "waiting", ["k2"])], passed_at="2026-10-23T09:30:00")
    _plan(state, planning, [_t("k1", "ready")], passed_at=None)
    stops = lambda: [n for n in host.command("ideas.board")["needs_you"] if n["kind"] == "change"]      # noqa: E731
    assert stops() == []
    change = {"made_at": "2026-10-23T11:00:00", "why": "csv only now", "changed": ["Out"], "estimate": {"usd_low": 0.1, "usd_high": 0.4},
              "change": [{"id": "k2", "title": "Write csv"}], "drop": ["k3"], "add": [{"key": "n1", "title": "Stream", "brief": "b"}] * 2}
    idea_change.write(state, slug, change)
    before = (state / "ideas" / slug / "plan_change.json").stat().st_mtime_ns
    (stop,) = stops()
    assert stop == {"idea": slug, "goal": g, "title": "Cache the table", "priority": "normal", "blocks": False, "at": "2026-10-23T11:00:00",
                    "kind": "change", "text": "The plan changes · +2 · 1 changed · −1", "why": "csv only now", "added": 2, "changed": 1,
                    "dropped": 1, "usd_low": 0.1, "usd_high": 0.4, "level": "work", "pulls": stop["pulls"]}
    assert stop["pulls"]["level"] == "work" and [t["id"] for t in stop["pulls"]["tasks"]] == ["k2", "k3", "", ""]      # spec 132 C.2: what it redoes below it (the two added tasks have no id yet)
    kinds = [(n["idea"], n["kind"]) for n in host.command("ideas.board")["needs_you"]]
    assert kinds == [(planning, "plan"), (slug, "change")]                                         # as a plan: by priority, then the oldest
    nodes = {n["slug"]: n for n in host.command("ideas.map", {})["nodes"]}
    assert nodes[slug]["needs_you"] == "change" and nodes[planning]["needs_you"] == "plan"        # the Map's node names it: its goal's row is marked
    party = next(m for x in host.command("ideas.map", {})["goals"] if x["slug"] == g for m in x["party"] if m.get("band") == "lead")
    assert (party["state"], party["why"]) == ("needs", "plan")                                   # the leader stops on its plan first, then on its change
    assert map_party.leader_state("working", [{"state": "working", "needs_you": "change"}]) == ("needs", "change")
    assert (state / "ideas" / slug / "plan_change.json").stat().st_mtime_ns == before            # a read writes nothing
    # what cannot be taken any more is shown nowhere; a change of nothing says so
    ideas.edit_plan(state, slug, lambda p: [p["tasks"][1].update(state="running", started="x"), p["tasks"][2].update(state="running", started="x")])
    (stop,) = stops()
    assert (stop["added"], stop["changed"], stop["dropped"], stop["text"]) == (2, 0, 0, "The plan changes · +2")
    idea_change.write(state, slug, {**change, "add": []})
    assert stops() == []
    idea_change.write(state, slug, {**change, "change": [], "drop": [], "add": []})
    (stop,) = stops()
    assert stop["text"] == "The plan stays as it is" and (stop["added"], stop["changed"], stop["dropped"]) == (0, 0, 0)
    ideas.save_state(state, slug, state="done")
    assert stops() == []


def test_the_hosts_map_signs_a_pictures_address_and_review_carries_it_spec_85(host, tmp_path):
    from orkboard.gui import media
    from orkboard.realm import idea_shots
    from tests import pick_files as pf
    root, state = _board(host)
    party = _goal(root, "Shots")
    slug = _idea(root, state, party, "With a picture", "working")
    png = tmp_path / "in.png"
    png.write_bytes(pf.png(8, 6))
    kept = idea_shots.store(state, slug, "k1", 1, png)
    _plan(state, slug, [{**_t("k1", "review"), "shot": kept}, {**_t("k2", "merged"), "shot": {"none": True}}])
    got = host.command("ideas.map")
    tasks = {t["id"]: t for t in _node(got, slug)["tasks"]}
    shot = tasks["k1"]["shot"]
    assert (shot["id"], shot["w"], shot["h"]) == ("k1-shot-r1", 8, 6) and shot["url"].startswith(f"/media/{slug}/k1-shot-r1/shot.png?s=")
    assert media.serve("GET", shot["url"], "", [state]).status == 200 and tasks["k2"]["shot"] == {"none": "no picture: no preview"}
    (result,) = [r for r in host.command("ideas.review_list")["results"] if r["task"] == "k1"]
    assert result["shot"]["url"] == shot["url"]


def _stops(host, slug):
    """The kinds of the Needs you rows of one idea (the same rows the map's node names its `needs_you` from)."""
    return [r["kind"] for r in host.command("ideas.board")["needs_you"] if r.get("idea") == slug]


def test_a_todo_is_a_stop_only_when_it_blocks_and_a_line_of_the_plan_until_then_spec_87(host):
    root, state = _board(host)
    g = _goal(root, "Boss")
    slug = _idea(root, state, g, "Spawn the boss", "working")
    todos = [{"id": "t1", "title": "record the boss's sounds", "kind": "confirm", "for": ["k2"]},
             {"id": "t2", "title": "paste the key", "kind": "secret", "for": ["k1"], "done": True},
             {"id": "t3", "title": "pick the arena", "kind": "choice", "choices": ["a", "b"], "for": ["k3", "k2"]}]
    _plan(state, slug, [_t("k1", "ready"), _t("k2", "waiting", ["k1"]), _t("k3", "waiting", ["k2"])], passed_at="x", todos=todos)
    node = _node(host.command("ideas.map", {}), slug)
    assert _stops(host, slug) == [] and node["needs_you"] == ""                       # k2 and k3 wait for k1: neither to-do blocks yet
    assert node["todo_lines"] == ["Before Task k2: record the boss's sounds", "Before Task k2: pick the arena", "Before Task k3: pick the arena"]      # (the done one is not said)
    _plan(state, slug, [_t("k1", "merged"), _t("k2", "ready", ["k1"]), _t("k3", "waiting", ["k2"])], passed_at="x", todos=todos)
    node = _node(host.command("ideas.map", {}), slug)
    got = [r for r in host.command("ideas.board")["needs_you"] if r.get("idea") == slug]
    assert [(r["kind"], r["blocks"], r["todo"]["id"]) for r in got] == [("todo", True, "t1"), ("todo", True, "t3")] and node["needs_you"] == "todo"
    _plan(state, slug, [_t("k1", "merged"), _t("k2", "merged", ["k1"]), _t("k3", "ready", ["k2"])], passed_at="x",
          todos=[{**todos[0], "done": True}, todos[1], todos[2]])
    node = _node(host.command("ideas.map", {}), slug)
    assert _stops(host, slug) == ["todo"] and node["todo_lines"] == ["Before Task k3: pick the arena"]
    _plan(state, slug, [_t("k1", "merged"), _t("k2", "merged", ["k1"]), _t("k3", "merged", ["k2"])], passed_at="x", todos=todos)
    assert _stops(host, slug) == [] and _node(host.command("ideas.map", {}), slug)["todo_lines"] == []
    ready = _idea(root, state, g, "Not started", "plan")                                # a plan waiting for the start: its to-dos are lines, not stops
    _plan(state, ready, [_t("k1", "ready")], todos=[{"id": "t1", "title": "paste the key", "kind": "secret", "for": ["k1"]}])
    assert _stops(host, ready) == ["plan"] and _node(host.command("ideas.map", {}), ready)["todo_lines"] == ["Before Task k1: paste the key"]


def test_the_route_and_start_rows_are_needs_you_of_a_goal_on_its_way_and_a_node_names_them(host):
    """Spec 99 §4: `route` (a goal routed, waiting for Talk) and `start` (a step added after Talk) sit on the goal, first among its kinds; the node's place follows."""
    root, state = _board(host)
    g = _goal(root, "Way")
    assert board_map.NEEDS[:2] == ("route", "start")
    route = [{"party": g, "leader": "taskmaster"}]
    a = _idea(root, state, g, "Routed goal", "routed", route=route, route_how={"by": "party", "kind": "feature", "short": False})
    b = _idea(root, state, g, "Talked goal", "talk", route=route, route_how={"by": "person", "said": {"calls": 4, "usd_low": 1.0, "usd_high": 3.0},
                                                                          "said_route": [], "changed": True})
    c = _idea(root, state, g, "Talked quietly", "decided", route=route, route_how={"said": {"calls": 4}, "changed": False})
    got = host.command("ideas.map", {})
    n = {x["slug"]: x for x in got["nodes"]}
    assert (n[a]["needs_you"], n[a]["place"], n[a]["asks_you"]) == ("route", "table", True)
    assert (n[b]["needs_you"], n[b]["place"], n[b]["asks_you"]) == ("start", "table", True)
    assert (n[c]["needs_you"], n[c]["place"], n[c]["asks_you"]) == ("", "table", False)
    rows = {r["kind"]: r for r in host.command("ideas.board")["needs_you"] if r["idea"] in (a, b)}
    assert rows["route"]["place"] == 1 and rows["start"]["was"] == {"calls": 4, "usd_low": 1.0, "usd_high": 3.0} and rows["start"]["cost"]["calls"] > 0
    assert [r["state"] for r in host.command("ideas.board")["ideas"] if r["slug"] == c] == ["decided"]


def test_the_decision_and_fork_rows_are_the_wording_to_confirm_and_the_first_disagreement_open_and_a_node_names_them(host):
    """Spec 99 §6–§7: `decision` {number, title, text, confirmed, error} on a goal `decided`; `fork` {id, about, sides} on a goal at `sections` while one is open."""
    root, state = _board(host)
    g = _goal(root, "Way")
    assert board_map.NEEDS[:7] == ("route", "start", "talk", "hearing", "cause", "decision", "fork")      # a goal's hearing (once a leader's no, spec 108 §4.3) between Talk and the decision (spec 120 §4.4)
    route = [{"party": g, "leader": "taskmaster"}]
    a = _idea(root, state, g, "Decided", "decided", route=route)
    b = _idea(root, state, g, "Forked", "sections", route=route)
    c = _idea(root, state, g, "Writing", "sections", route=route)
    d = _idea(root, state, g, "Being worded", "decided", route=route)
    sides = [{"party": g, "leader": "architect", "says": "Ten waves", "why": "the pace"}, {"party": "art", "leader": "artist", "says": "Six waves", "why": "the budget"}]
    spec_sections.save_record(state, a, {"decision": {"title": "Dark mode", "text": "Why: x.\n\n1. One", "number": 12, "confirmed": False}})
    spec_sections.save_record(state, b, {"forks": [{"id": "f1", "about": "Done", "sides": sides, "status": "answered"}, {"id": "f2", "about": "Waves", "sides": sides, "status": "open"}]})
    spec_sections.save_record(state, c, {"forks": [{"id": "f1", "about": "Done", "sides": sides, "status": "answered"}]})
    got = host.command("ideas.map", {})
    n = {x["slug"]: x for x in got["nodes"]}
    assert (n[a]["needs_you"], n[b]["needs_you"], n[c]["needs_you"], n[d]["needs_you"]) == ("decision", "fork", "", "")           # nothing waits for the person where nothing was worded or no fork is open
    rows = {r["idea"]: r for r in host.command("ideas.board")["needs_you"] if r["kind"] in ("decision", "fork")}
    assert set(rows) == {a, b} and rows[a]["kind"] == "decision" and rows[b]["kind"] == "fork"
    assert (rows[a]["number"], rows[a]["title"], rows[a]["text"], rows[a]["confirmed"], rows[a]["error"]) == (12, "Dark mode", "Why: x.\n\n1. One", False, "")
    assert (rows[b]["id"], rows[b]["about"], rows[b]["sides"], rows[b]["text"]) == ("f2", "Waves", sides, "Waves")                  # the first fork open, in the order the join found them
    assert [(x["dir"], x["kind"], x["party"], x["outcome"]) for x in rows[b]["hearing"]["sides"]] == [("right", "side", g, "Ten waves"), ("left", "side", "art", "Six waves")]      # a fork's lifted face is a hearing (spec 120 §4.2)
    ideas.save_state(state, a, error="The sections failed: x")
    spec_sections.save_record(state, a, {"decision": {"title": "Dark mode", "text": "t", "number": 12, "confirmed": True}})
    row = next(r for r in host.command("ideas.board")["needs_you"] if r["idea"] == a and r["kind"] == "decision")
    assert row["confirmed"] is True and row["error"] == "The sections failed: x"


def _cards(party, n=3):
    return [{"id": f"r1-{party}-{k}", "by": party, "leader": "taskmaster", "q": f"Question {k}?", "choices": ["A", "B"], "pick": 0, "why": "because", "project": False, "kinds": ["other", "other"]}
            for k in range(1, n + 1)]


def test_the_talk_and_cause_rows_are_the_stances_with_the_cards_and_the_guess_with_the_cases_and_a_node_names_them(host):
    """Spec 99 §5.3–§5.4: `talk` {round, stances, questions: [card]} and `cause` {cause, where, q: [card]} sit on a goal at Talk while something waits; none while the leaders are heard."""
    root, state = _board(host)
    g = _goal(root, "Way")
    assert board_map.NEEDS[:5] == ("route", "start", "talk", "hearing", "cause")
    route = [{"party": g, "leader": "taskmaster"}]
    stances = [{"party": g, "leader": "taskmaster", "stance": "For it", "for": "Players want it", "against": "Costs a week"}]
    a = _idea(root, state, g, "A talk", "talk", route=route)
    b = _idea(root, state, g, "A bug", "talk", route=route)
    c = _idea(root, state, g, "Being heard", "talk", route=route)
    idea_questions.save_record(state, a, {"mode": "talk", "round": 2, "stances": stances, "waiting": _cards(g), "second": [], "answers": [], "defaults": []})
    idea_questions.save_record(state, b, {"mode": "bug", "round": 1, "waiting": _cards(g, 2),
                                          "cause": {"text": "The lobby's timer is not reset on reconnect", "where": ["server/lobby.ts"], "pending": True, "guesses": 1}})
    idea_questions.save_record(state, c, {"mode": "talk", "round": 1, "waiting": [], "stances": stances})
    got = host.command("ideas.map", {})
    n = {x["slug"]: x for x in got["nodes"]}
    assert (n[a]["needs_you"], n[a]["place"], n[a]["asks_you"]) == ("talk", "table", True)
    assert (n[b]["needs_you"], n[b]["place"], n[b]["asks_you"]) == ("cause", "table", True)
    assert (n[c]["needs_you"], n[c]["place"], n[c]["asks_you"]) == ("", "table", False)                  # the leaders are being heard: nothing waits
    rows = {r["idea"]: r for r in host.command("ideas.board")["needs_you"] if r["kind"] in ("talk", "cause")}
    assert set(rows) == {a, b}
    assert rows[a]["kind"] == "talk" and rows[a]["round"] == 2 and rows[a]["stances"] == stances and rows[a]["questions"] == _cards(g) and rows[a]["text"] == "Question 1?"
    assert rows[b]["kind"] == "cause" and rows[b]["cause"] == "The lobby's timer is not reset on reconnect" and rows[b]["where"] == ["server/lobby.ts"]
    assert rows[b]["q"] == _cards(g, 2) and rows[b]["blocks"] is False
    idea_questions.save_record(state, b, {"mode": "bug", "round": 1, "waiting": [], "cause": {"text": "x", "pending": False, "guesses": 2}})       # answered, or the second guess being made
    assert not [r for r in host.command("ideas.board")["needs_you"] if r["idea"] == b and r["kind"] in ("talk", "cause")]
