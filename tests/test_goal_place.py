"""Spec 98 §2 (B): a goal's place (deck · hand · table · discard · history), `asks_you`, `waits_as` and `seen`, on a node of
`ideas.map` and on its row of `ideas.board`, and `ideas.seen`. Code, no model."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from orkboard.gui.board_host import CommandError, Orkboard
from orkboard.realm import event_log, goal_place, ideas


def _row(state, **more):
    return {"state": state, "queue": "", "held_until": "", "start_at": "", "waits_on": [], **more}


def _of(state, kinds=(), *, passed=False, picking=False, seen="", **more):
    return goal_place.place_of(_row(state, **more), kinds, passed=passed, picking=picking, seen=seen)


def _is(got, place, asks_you=False, waits_as=""):
    return got == {"place": place, "asks_you": asks_you, "waits_as": waits_as}


def test_a_goal_not_started_and_asking_nothing_is_in_the_deck():
    assert _is(_of("raw", queue="hold"), "deck", waits_as="held")
    assert _is(_of("raw", queue="night"), "deck", waits_as="held")                  # the night is gone: a raw `night` reads as `hold`
    assert _is(_of("raw", queue="now", held_until="2026-10-29T08:00:00"), "deck", waits_as="reset")
    assert _is(_of("ready", held_until="2026-10-29T08:00:00"), "deck", waits_as="reset")
    assert _is(_of("plan", ["plan"], start_at="2026-10-29T08:00:00"), "deck", waits_as="reset")      # a plan that starts later
    assert _is(_of("plan", start_at="night", passed=True), "deck", waits_as="reset")                 # …a plan of before the night went
    assert _is(_of("raw", queue="hold", waits_on=["a"]), "deck", waits_as="held")                    # what the person did is said first
    assert _is(_of("failed"), "deck")                                                                # failed with nothing to answer
    assert _is(_of("failed", waits_on=["a"]), "deck", waits_as="line")


def test_a_goal_not_at_work_with_a_needs_you_row_is_in_the_hand():
    assert _is(_of("plan", ["plan"]), "hand")
    assert _is(_of("asks", ["asks"]), "hand")
    assert _is(_of("failed", ["failed"]), "hand")
    assert _is(_of("proposed", ["proposal"]), "hand")
    assert _is(_of("judged", ["pitch"]), "hand")                                    # a pitch with its answer waiting
    assert _is(_of("raw", ["collide"], queue="hold"), "hand")                       # a collision's question on a goal held in the deck
    assert _is(_of("plan", ["plan", "collide"], start_at="2026-10-29T08:00:00"), "hand")


def test_a_goal_the_orkmaster_reads_or_plans_or_at_work_is_on_the_table():
    assert _is(_of("raw", queue="now"), "table")
    assert _is(_of("ready"), "table")
    assert _is(_of("reading"), "table") and _is(_of("planning"), "table") and _is(_of("judging"), "table")
    assert _is(_of("working"), "table")
    assert _is(_of("plan", passed=True), "table")
    assert _is(_of("asks"), "table")                                                # asked, with no question left to answer


def test_a_goal_at_work_that_asks_is_on_the_table_and_asks_you():
    assert _is(_of("working", ["failed"], passed=True), "table", True)
    assert _is(_of("working", ["todo"], passed=True), "table", True)
    assert _is(_of("working", ["collide"], passed=True), "table", True)
    assert _is(_of("working", picking=True, passed=True), "table", True)            # a task waits for the person's pick
    assert _is(_of("raw", ["collide"], queue="now"), "hand")
    assert _is(_of("working", passed=True, start_at="night"), "table")              # a plan passed whose tasks are held stays on the table
    assert _of("working", ["failed"])["place"] == "table"


def test_a_pitch_lies_on_the_table_while_someone_works_on_it_and_in_the_hand_with_a_row():
    assert _is(_of("judging"), "table")
    assert _is(_of("judged", ["pitch"]), "hand")
    assert _is(_of("sent"), "history", False) and _is(_of("passed"), "history")
    assert _is(_of("proposed", ["proposal"]), "hand")


def test_a_goal_done_is_in_the_discard_until_its_result_is_seen_then_in_the_history():
    assert _is(_of("done"), "discard")
    assert _is(_of("done", ["asks"]), "discard")                                    # a done goal asks nothing
    assert _is(_of("done", seen="2026-10-28T10:00:00"), "history")


def test_a_goal_routed_lies_on_the_table_asking_and_waits_in_the_deck_when_put_off_and_the_ways_other_states_are_on_the_table():
    """Spec 107 §5 (spec 99 §4): `routed` → the table, asking at once (its route row is in the hand too: an asking goal on the table is); *Later, by itself*
    sets `held_until`, and it waits for the reset in the deck; `talk`, `decided` and `sections` lie on the table, asking when a row waits."""
    assert _is(_of("routed", ["route"]), "table", True) and _is(_of("routed"), "table", True)
    assert _is(_of("routed", held_until="2026-10-29T08:00:00"), "deck", waits_as="reset")
    for state in ("talk", "decided", "sections"):
        assert _is(_of(state), "table") and _is(_of(state, ["asks"]), "table", True) and _is(_of(state, ["start"]), "table", True)
        assert _is(_of(state, ["route"], waits_on=["a"]), "table", True)


def test_every_state_has_a_place():
    for state in ideas.STATES:
        got = _of(state, ["plan"] if state == "plan" else [])
        assert got["place"] in goal_place.PLACES and got["waits_as"] in ("", *goal_place.WAITS_AS)
        assert got["waits_as"] == "" or got["place"] == "deck"


# -- on the host ---------------------------------------------------------------------------------------------

@pytest.fixture
def host(fake_repo) -> Orkboard:
    return Orkboard(fake_repo)


def _idea(host, text, state, track=None, **more):
    root, state_dir = host.ideas.root(), host.ideas.state_dir
    slug = ideas.add_idea(root, text, track or ideas.GENERAL, state_dir)
    ideas.save_state(state_dir, slug, state=state, **more)
    return slug


def _plan(host, slug, tasks, **more):
    folder = host.ideas.state_dir / "ideas" / slug
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "plan.json").write_text(json.dumps({"idea": slug, "made_at": "2026-10-28T09:00:00", "todos": [], "tasks": tasks, **more}))


def _task(tid, state):
    return {"id": tid, "title": f"Task {tid}", "tier": "warrior", "state": state, "after": [], "note": ""}


def test_a_node_and_its_row_carry_the_same_place(host):
    root = host.ideas.root()
    g, _new = ideas.save_goal(root, None, "Places", "About places", None, "normal")
    mk = lambda text, state, **more: _idea(host, text, state, g, **more)           # noqa: E731
    held, now = mk("Held", "raw", queue="hold"), mk("Now", "raw", queue="now")
    night = mk("Night", "raw", queue="night")
    reset = mk("Reset", "raw", queue="now", held_until="2026-10-29T08:00:00")
    ask = mk("Ask", "asks")
    ideas.idea_page(root, ask)
    plan = mk("Plan", "plan")
    _plan(host, plan, [_task("k1", "ready")])
    later = mk("Later", "plan")
    _plan(host, later, [_task("k1", "ready")], start_at="2026-10-29T08:00:00")
    work, picking = mk("Work", "working"), mk("Picking", "working")
    _plan(host, work, [_task("k1", "running")], passed_at="x")
    _plan(host, picking, [_task("k1", "picking")], passed_at="x")
    failed = mk("Failed", "working")
    _plan(host, failed, [_task("k1", "failed")], passed_at="x")
    done, seen = mk("Done", "done"), mk("Seen", "done", seen_at="2026-10-28T10:00:00")
    rows = {r["slug"]: r for r in host.command("ideas.board")["ideas"]}
    nodes = {n["slug"]: n for n in host.command("ideas.map", {})["nodes"]}
    assert set(rows) == set(nodes)
    want = {held: ("deck", False, "held"), night: ("deck", False, "held"), reset: ("deck", False, "reset"), now: ("table", False, ""),
            later: ("deck", False, "reset"), plan: ("hand", False, ""), work: ("table", False, ""), picking: ("table", True, ""),
            failed: ("table", True, ""), done: ("discard", False, ""), seen: ("history", False, "")}
    for slug, (place, asks_you, waits_as) in want.items():
        for got in (rows[slug], nodes[slug]):
            assert (got["place"], got["asks_you"], got["waits_as"]) == (place, asks_you, waits_as), (slug, got["state"])
    assert nodes[seen]["seen"] == rows[seen]["seen"] == "2026-10-28T10:00:00" and nodes[done]["seen"] == rows[done]["seen"] == ""
    assert nodes[ask]["place"] == rows[ask]["place"] in ("hand", "table")
    for slug in nodes:
        assert nodes[slug]["place"] == rows[slug]["place"] and nodes[slug]["asks_you"] == rows[slug]["asks_you"]


def test_today_s_waits_and_the_rows_asks_count_stay(host):
    root = host.ideas.root()
    g, _new = ideas.save_goal(root, None, "Stay", "About stay", None, "normal")
    held = _idea(host, "Held", "raw", g, queue="hold")
    row = next(r for r in host.command("ideas.board")["ideas"] if r["slug"] == held)
    node = next(n for n in host.command("ideas.map", {})["nodes"] if n["slug"] == held)
    assert row["asks"] == 0 and isinstance(row["asks"], int) and not isinstance(row["asks"], bool)
    assert node["waits"] == {"kind": "stopped", "ref": "", "title": "", "until": ""} and node["waits_as"] == "held"


def test_a_collision_asks_on_the_row_of_a_goal_at_work(host, monkeypatch):
    from orkboard.realm import collide
    root = host.ideas.root()
    g, _new = ideas.save_goal(root, None, "Collides", "About collisions", None, "normal")
    work = _idea(host, "Work", "working", g)
    _plan(host, work, [_task("k1", "running")], passed_at="x")
    monkeypatch.setattr(collide, "rows", lambda *a, **k: [{"kind": "collide", "idea": work, "goal": g, "title": "t", "priority": "normal",
                                                           "blocks": False, "at": "2026-10-28T09:00:00", "text": "x"}])
    row = next(r for r in host.command("ideas.board")["ideas"] if r["slug"] == work)
    assert (row["place"], row["asks_you"]) == ("table", True)


def test_ideas_seen_writes_seen_at_once_and_moves_a_done_goal_to_the_history(host):
    root = host.ideas.root()
    g, _new = ideas.save_goal(root, None, "Seen", "About seen", None, "normal")
    done = _idea(host, "Done", "done", g)
    node = lambda: next(n for n in host.command("ideas.map", {})["nodes"] if n["slug"] == done)      # noqa: E731
    assert (node()["place"], node()["seen"]) == ("discard", "")
    got = host.command("ideas.seen", {"idea": done})
    assert got["ok"] is True and got["seen"] == ideas.state(host.ideas.state_dir, done)["seen_at"] != ""
    assert (node()["place"], node()["seen"]) == ("history", got["seen"])
    assert host.command("ideas.seen", {"idea": done})["seen"] == got["seen"]                   # the first time is kept
    (e,) = [r for r in event_log.read(Path(host.town.repo_root)) if r["event"] == "result_seen"]
    assert e["idea"] == done and e["device"] == "desktop"


def test_ideas_seen_refuses_a_goal_not_done_or_gone(host):
    working = _idea(host, "Working", "working")
    with pytest.raises(CommandError, match="Only a goal that is done"):
        host.command("ideas.seen", {"idea": working})
    with pytest.raises(CommandError, match="That goal is gone"):
        host.command("ideas.seen", {"idea": "nope"})
    assert ideas.state(host.ideas.state_dir, working)["seen_at"] == ""


def test_result_seen_is_an_event():
    assert event_log.RESULT_SEEN == "result_seen" and event_log.RESULT_SEEN in event_log.EVENTS


def test_a_goal_at_talk_with_a_row_waiting_is_on_the_table_and_asks_you_and_with_none_it_does_not():
    """Spec 99 §5: while the leaders are heard (or the decision is made) nothing waits and the goal only lies on the table; a `talk` row (the cards) or a bug's `cause`
    row makes it ask, in the hand too (`asks_you`), never in two piles."""
    assert _is(_of("talk"), "table") and _is(_of("talk", ["talk"]), "table", True) and _is(_of("talk", ["cause"]), "table", True)
    assert _is(_of("talk", ["talk", "start"]), "table", True) and _is(_of("decided"), "table")
    assert _is(_of("talk", ["talk"], held_until="2026-10-29T08:00:00"), "table", True)         # a Talk that is answered is never put in the deck
    assert _is(_of("talk", ["objection"]), "table", True) and _is(_of("talk", ["talk", "objection"]), "table", True)         # a leader's no (spec 108 §4.3): the same place, asking


def test_a_goal_at_talk_with_cards_waiting_is_a_node_and_a_row_that_ask_you(host):
    from orkboard.realm import idea_questions
    root, state = host.ideas.root(), host.ideas.state_dir
    slug, _new = ideas.save_goal(root, None, "Way", "About", None, "normal")
    idea = ideas.add_idea(root, "Add a dark mode", slug, state)
    ideas.save_state(state, idea, state="talk", route=[{"party": slug, "leader": "taskmaster"}])
    row = lambda: next(i for i in host.command("ideas.board")["ideas"] if i["slug"] == idea)           # noqa: E731
    assert (row()["place"], row()["asks_you"]) == ("table", False)                                     # the leaders are being heard
    card = {"id": "r1-way-1", "by": slug, "leader": "taskmaster", "q": "Which?", "choices": ["A", "B"], "pick": 0, "why": "", "project": False}
    idea_questions.save_record(state, idea, {"mode": "talk", "round": 1, "waiting": [card], "stances": []})
    assert (row()["place"], row()["asks_you"]) == ("table", True)                                      # cards wait: on the table, asking
