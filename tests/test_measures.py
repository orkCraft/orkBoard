"""Spec 124 B (docs/specs/124-the-brief-the-measures-and-the-trial.md, hypothesis H1): the measures of the table, read from the project's own event log by
code. A leader's no heeded or overruled; an overruled no that came back at Review beside the goals no leader objected to; concerns made a goal or not a
problem; the Investor's word taken; sketches picked; a goal accepted the first time; the changes after the start. And `orkboard measures`."""
from __future__ import annotations

import json

from orkboard.gui import board_cli
from orkboard.realm import event_log, measures


def _log(root, *events):
    for event, fields in events:
        assert event_log.record(root, event, **fields)


def test_an_empty_log_measures_nothing_and_says_so(tmp_path):
    m = measures.of(tmp_path)
    assert m["talk"]["objections"] == 0 and m["talk"]["heeded_share"] is None and m["results"]["first_time_share"] is None
    assert "nothing in the log yet" in measures.text(m) and "—" in measures.text(m)


def test_the_leaders_no_is_measured_by_what_the_person_did_with_it(tmp_path):
    E = event_log
    _log(tmp_path,
         (E.TALK_HEARD, {"idea": "a", "party": "product"}), (E.TALK_HEARD, {"idea": "b", "party": "tech"}), (E.TALK_HEARD, {"idea": "c", "party": "tech"}),
         (E.LEADER_OBJECTED, {"idea": "a", "party": "product", "verdict": "no", "has_instead": True}),
         (E.LEADER_OBJECTED, {"idea": "b", "party": "tech", "verdict": "doubt", "has_instead": False}),
         (E.LEADER_OBJECTED, {"idea": "c", "party": "tech", "verdict": "no", "has_instead": False}),
         (E.OBJECTION_ANSWERED, {"idea": "a", "party": "product", "answer": "smaller"}),
         (E.OBJECTION_ANSWERED, {"idea": "b", "party": "tech", "answer": "go"}),
         (E.OBJECTION_ANSWERED, {"idea": "c", "party": "tech", "answer": "go"}),
         (E.TALK_VERDICT, {"idea": "b", "party": "tech", "before": "doubt", "after": "go"}),
         (E.TALK_VERDICT, {"idea": "a", "party": "product", "before": "no", "after": "no"}),
         (E.HEARING_THROWN, {"idea": "a", "moment": "talk", "kind": "smaller", "dir": "left", "leaders": 1}))
    t = measures.of(tmp_path)["talk"]
    assert (t["goals_heard"], t["objections"], t["no"], t["doubt"], t["with_instead"]) == (3, 3, 2, 1, 1)
    assert (t["answered"], t["heeded"], t["overruled"], t["heeded_share"]) == (3, 1, 2, 0.333)
    assert t["answers"] == {"drop": 0, "smaller": 1, "later": 0, "go": 2}
    assert (t["minds_changed"], t["toward_go"]) == (1, 1) and t["hearings"] == {"smaller": 1}


def test_an_overruled_no_that_came_back_at_review_is_set_beside_the_goals_no_leader_objected_to(tmp_path):
    E = event_log
    _log(tmp_path,
         (E.LEADER_OBJECTED, {"idea": "x", "party": "tech", "verdict": "no"}), (E.OBJECTION_ANSWERED, {"idea": "x", "party": "tech", "answer": "go"}),
         (E.LEADER_OBJECTED, {"idea": "y", "party": "tech", "verdict": "no"}), (E.OBJECTION_ANSWERED, {"idea": "y", "party": "tech", "answer": "go"}),
         (E.LEADER_OBJECTED, {"idea": "z", "party": "tech", "verdict": "no"}), (E.OBJECTION_ANSWERED, {"idea": "z", "party": "tech", "answer": "go"}),
         (E.RESULT_DECIDED, {"idea": "x", "task": "t1", "round": 1, "decision": "back"}), (E.RESULT_DECIDED, {"idea": "x", "task": "t1", "round": 2, "decision": "merge"}),
         (E.RESULT_DECIDED, {"idea": "y", "task": "t1", "round": 1, "decision": "merge"}),
         (E.RESULT_DECIDED, {"idea": "calm1", "task": "t1", "round": 1, "decision": "merge"}),
         (E.RESULT_DECIDED, {"idea": "calm2", "task": "t1", "round": 1, "decision": "merge"}),
         (E.RESULT_DECIDED, {"idea": "calm3", "task": "t1", "round": 1, "decision": "fix"}),
         (E.RESULT_DECIDED, {"idea": "calm4", "task": "t1", "round": 1, "decision": "install"}))           # neither a merge nor a way back: not decided
    m = measures.of(tmp_path)
    t = m["talk"]
    assert (t["overruled_goals"], t["overruled_decided"], t["overruled_came_back"], t["overruled_came_back_share"]) == (3, 2, 1, 0.5)   # z is not decided yet
    assert (t["unobjected_decided"], t["unobjected_came_back_share"]) == (3, 0.333)
    r = m["results"]
    assert (r["decided"], r["first_time"], r["first_time_share"]) == (5, 3, 0.6)                    # y, calm1, calm2 the first time; x and calm3 not
    assert "1 of 2 (50 %)" in measures.text(m) and "3 of 5 (60 %)" in measures.text(m)


def test_concerns_pitches_sketches_and_the_changes_after_the_start(tmp_path):
    E = event_log
    _log(tmp_path,
         (E.CONCERNS_MADE, {"party": "tech", "n": 4, "alerts": 1}), (E.CONCERNS_MADE, {"party": "design", "n": 2}),
         (E.CONCERN_OPENED, {"party": "tech", "level": "alert"}), (E.CONCERN_GOAL, {"party": "tech", "level": "alert", "idea": "g"}),
         (E.CONCERN_DISMISSED, {"party": "design", "level": "note"}), (E.CONCERN_DISMISSED, {"party": "design", "level": "note"}),
         (E.PITCH_JUDGED, {"goal": "p1", "answer": "invest"}), (E.PITCH_JUDGED, {"goal": "p2", "answer": "pass"}), (E.PITCH_JUDGED, {"goal": "p3", "answer": "reshape"}),
         (E.PITCH_SENT, {"goal": "p1", "to": "tech", "as_decided": True}), (E.PITCH_PASSED, {"goal": "p3", "as_decided": False}),
         (E.SKETCH_MADE, {"idea": "s", "craft": "design", "kind": "page", "n": 3}),
         (E.SKETCH_ANSWERED, {"idea": "s", "answer": "again"}), (E.SKETCH_ANSWERED, {"idea": "s", "answer": "picked"}),
         (E.PLAN_PASSED, {"idea": "g1", "tasks": 3}), (E.PLAN_PASSED, {"idea": "g2", "tasks": 2}),
         (E.PLAN_CHANGE_ANSWERED, {"idea": "g1", "take": True}), (E.PLAN_CHANGE_ANSWERED, {"idea": "g1", "take": False}),
         (E.IDEA_EDITED, {"idea": "g1", "section": "Scope", "passed": True}), (E.IDEA_EDITED, {"idea": "g2", "section": "Scope", "passed": False}))
    m = measures.of(tmp_path)
    assert m["concerns"] == {"looks": 2, "found": 6, "opened": 1, "made_goal": 1, "dismissed": 2, "goal_share": 0.333}
    assert m["pitches"] == {"judged": 3, "invest": 1, "reshape": 1, "pass": 1, "decided_by_person": 2, "as_the_investor_said": 1, "agreed_share": 0.5}
    assert m["sketches"] == {"made": 1, "picked": 1, "again": 1, "skipped": 0, "picked_share": 0.5}
    assert m["after_start"] == {"started": 2, "changes": 2, "goals_changed": 1, "per_goal": 1.0}


def test_the_days_bound_what_is_counted(tmp_path):
    lines = [{"event": event_log.LEADER_OBJECTED, "at": f"2026-10-{d:02d}T10:00:00", "idea": f"i{d}", "verdict": "no"} for d in (1, 15, 30)]
    event_log.path(tmp_path).parent.mkdir(parents=True)
    event_log.path(tmp_path).write_text("\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8")
    assert measures.of(tmp_path, since="2026-10-10")["talk"]["objections"] == 2
    m = measures.of(tmp_path, since="2026-10-10", until="2026-10-20")
    assert m["talk"]["objections"] == 1 and m["since"] == "2026-10-10"


def test_orkboard_measures_prints_them_or_their_data(tmp_path, capsys):
    _log(tmp_path, (event_log.LEADER_OBJECTED, {"idea": "a", "verdict": "no"}), (event_log.OBJECTION_ANSWERED, {"idea": "a", "answer": "drop"}))
    assert board_cli.run(["measures", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert out.startswith("Orkboard's measures") and "you gave way to 1 of 1 (100 %)" in out
    assert board_cli.run(["measures", str(tmp_path), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["talk"]["heeded"] == 1
    assert board_cli.run(["measures", str(tmp_path / "none")]) == 2 and "no folder" in capsys.readouterr().err


# -- spec 121 §G: hypothesis H2, the day (docs/hypotheses.md) ------------------------------------------------------------------------------------

def _at(root, *rows):
    """Lines with their own times: `(at, event, fields)`."""
    event_log.path(root).parent.mkdir(parents=True, exist_ok=True)
    event_log.path(root).write_text("\n".join(json.dumps({"at": at, "event": e, **f}) for at, e, f in rows) + "\n", encoding="utf-8")


def test_the_days_measures_say_nothing_where_the_log_has_nothing(tmp_path):
    d = measures.of(tmp_path)["day"]
    assert d["first_sketch"]["holds"] is None and d["sketches"]["holds"] is None and d["building"]["holds"] is None and d["morning"]["holds"] is None and d["went_wrong"]["holds"] is None
    assert "The day, the morning and the night (H2)" in measures.text(measures.of(tmp_path)) and "nothing to read yet" in measures.text(measures.of(tmp_path))


def test_h2_holds_when_the_sketch_comes_soon_most_are_picked_the_night_builds_the_mark_comes_fast_and_the_night_fails_less(tmp_path):
    E = event_log
    _at(tmp_path,
        ("2026-11-02T10:00:00+00:00", E.IDEA_ADDED, {"idea": "g1"}), ("2026-11-02T10:05:00+00:00", E.SKETCH_MADE, {"idea": "g1", "craft": "design"}),          # 5 minutes
        ("2026-11-02T11:00:00+00:00", E.IDEA_ADDED, {"idea": "g2"}), ("2026-11-02T11:12:00+00:00", E.SKETCH_MADE, {"idea": "g2", "craft": "design"}),          # 12
        ("2026-11-02T12:00:00+00:00", E.IDEA_ADDED, {"idea": "g3"}), ("2026-11-02T13:30:00+00:00", E.SKETCH_MADE, {"idea": "g3", "craft": "design"}),          # 90
        ("2026-11-02T12:10:00+00:00", E.SKETCH_ANSWERED, {"idea": "g1", "answer": "picked"}), ("2026-11-02T12:11:00+00:00", E.SKETCH_ANSWERED, {"idea": "g2", "answer": "picked"}),
        ("2026-11-02T13:40:00+00:00", E.SKETCH_ANSWERED, {"idea": "g3", "answer": "again"}), ("2026-11-02T13:50:00+00:00", E.SKETCH_ANSWERED, {"idea": "g3", "answer": "picked"}),
        ("2026-11-02T14:00:00+00:00", E.SKETCH_SKIPPED, {"idea": "g4", "why": "the media tools are not set up"}),
        ("2026-11-02T20:00:00+00:00", E.BOARD_SET, {"work_at_night": True}),
        ("2026-11-02T20:05:00+00:00", E.NIGHT_HELD, {"idea": "n1"}), ("2026-11-02T20:06:00+00:00", E.NIGHT_HELD, {"idea": "n2"}), ("2026-11-02T20:07:00+00:00", E.NIGHT_HELD, {"idea": "n3"}),
        ("2026-11-03T01:00:00+00:00", E.NIGHT_STARTED, {"idea": "n1"}), ("2026-11-03T01:00:00+00:00", E.PLAN_PASSED, {"idea": "n1", "tasks": 2}),
        ("2026-11-03T01:01:00+00:00", E.NIGHT_STARTED, {"idea": "n2"}), ("2026-11-03T01:01:00+00:00", E.PLAN_PASSED, {"idea": "n2", "tasks": 1}),
        ("2026-11-03T01:02:00+00:00", E.NIGHT_STARTED, {"idea": "n3"}), ("2026-11-03T01:02:00+00:00", E.PLAN_PASSED, {"idea": "n3", "tasks": 1}),
        ("2026-11-03T09:00:00+00:00", E.BUILT_NOW, {"idea": "d1", "from": "card"}), ("2026-11-03T09:00:01+00:00", E.PLAN_PASSED, {"idea": "d1", "tasks": 1}),
        ("2026-11-03T10:00:00+00:00", E.PLAN_PASSED, {"idea": "d2", "tasks": 1}),
        ("2026-11-03T08:00:00+00:00", E.NIGHT_CARD_OPENED, {"goals": 3}), ("2026-11-03T08:01:00+00:00", E.PLAY_AT_PATH, {"idea": "n1", "path": "/lobby"}),
        ("2026-11-03T08:01:30+00:00", E.PLAY_MARK, {"idea": "m1", "kind": "bug", "joined": False, "minutes_since_open": 1.5}),
        ("2026-11-03T08:02:00+00:00", E.PLAY_MARK, {"idea": "m2", "kind": "looks", "joined": False, "minutes_since_open": None}),
        ("2026-11-04T08:00:00+00:00", E.NIGHT_CARD_OPENED, {"goals": 1}), ("2026-11-04T08:00:30+00:00", E.PLAY_MARK, {"idea": "m3", "kind": "bug", "joined": False, "minutes_since_open": 0.5}),
        ("2026-11-04T09:00:00+00:00", E.TASK_STATE, {"idea": "d1", "task": "t", "state": "failed"}),
        ("2026-11-04T09:10:00+00:00", E.RESULT_DECIDED, {"idea": "d2", "task": "t", "decision": "back"}), ("2026-11-04T09:20:00+00:00", E.RESULT_DECIDED, {"idea": "n1", "task": "t", "decision": "merge"}))
    m = measures.of(tmp_path)
    d = m["day"]
    f = d["first_sketch"]
    assert (f["goals"], f["within"], f["median_minutes"], f["holds"]) == (3, 2, 12.0, True) and f["within_share"] == 0.667
    k = d["sketches"]
    assert (k["answered"], k["picked"], k["picked_share"], k["not_made"], k["again_three_times"], k["holds"], k["refuted"]) == (4, 3, 0.75, 1, 0, True, False)
    b = d["building"]
    assert (b["started"], b["at_night"], b["built_now"], b["other"], b["night_share"], b["holds"]) == (5, 3, 1, 1, 0.6, True)
    assert (b["held"], b["built_now_share"], b["refuted"]) == (4, 0.25, False), "the goals the night held: n1, n2, n3 and d1, which Build it now took by day"
    mo = d["morning"]
    assert (mo["opened"], mo["first_marks"], mo["under"], mo["median_minutes"], mo["holds"]) == (2, 2, 2, 1.0, True)
    w = d["went_wrong"]
    assert w["night"] == {"goals": 3, "failed": 0, "sent_back": 0, "wrong": 0, "wrong_share": 0.0} and w["day"] == {"goals": 2, "failed": 1, "sent_back": 1, "wrong": 2, "wrong_share": 1.0} and w["holds"] is True
    assert d["play_at_path"] == 1
    out = measures.text(m)
    assert "The day, the morning and the night (H2)" in out and "2 of 3 (67 %), median 12 min: holds" in out and "in the night's window 3 (60 %)" in out and "median 1 min, the card lifted 2 times: holds" in out
    json.dumps(m)


def test_h2_is_refuted_by_sketches_mostly_skipped_build_it_now_for_most_and_a_slow_first_mark(tmp_path):
    E = event_log
    _at(tmp_path,
        ("2026-11-02T10:00:00+00:00", E.IDEA_ADDED, {"idea": "g1"}), ("2026-11-02T11:00:00+00:00", E.SKETCH_MADE, {"idea": "g1"}),
        ("2026-11-02T11:05:00+00:00", E.SKETCH_ANSWERED, {"idea": "g1", "answer": "skipped"}), ("2026-11-02T11:06:00+00:00", E.SKETCH_ANSWERED, {"idea": "g2", "answer": "skipped"}),
        ("2026-11-02T11:07:00+00:00", E.SKETCH_ANSWERED, {"idea": "g3", "answer": "picked"}),
        *[("2026-11-02T11:08:00+00:00", E.SKETCH_ANSWERED, {"idea": "g4", "answer": "again"}) for _ in range(3)],
        ("2026-11-02T20:00:00+00:00", E.NIGHT_HELD, {"idea": "a"}), ("2026-11-02T20:00:00+00:00", E.NIGHT_HELD, {"idea": "b"}), ("2026-11-02T20:00:00+00:00", E.NIGHT_HELD, {"idea": "c"}),
        ("2026-11-03T09:00:00+00:00", E.BUILT_NOW, {"idea": "a", "from": "card"}), ("2026-11-03T09:01:00+00:00", E.BUILT_NOW, {"idea": "b", "from": "sketch"}),
        ("2026-11-03T08:00:00+00:00", E.NIGHT_CARD_OPENED, {"goals": 1}), ("2026-11-03T08:05:00+00:00", E.PLAY_MARK, {"idea": "m", "kind": "bug", "minutes_since_open": 5.0}),
        ("2026-11-03T09:10:00+00:00", E.TASK_STATE, {"idea": "c", "task": "t", "state": "failed"}), ("2026-11-03T09:11:00+00:00", E.NIGHT_STARTED, {"idea": "c"}))
    d = measures.of(tmp_path)["day"]
    assert d["first_sketch"]["median_minutes"] == 60.0 and d["first_sketch"]["holds"] is False
    k = d["sketches"]
    assert (k["answered"], k["skipped"], k["picked"], k["again_three_times"], k["holds"], k["refuted"]) == (6, 2, 1, 1, False, False), "skipped 2 of 6 is not most"
    b = d["building"]
    assert (b["started"], b["at_night"], b["built_now"], b["held"], b["built_now_share"], b["holds"], b["refuted"]) == (3, 1, 2, 3, 0.667, False, True)
    assert d["morning"]["median_minutes"] == 5.0 and d["morning"]["holds"] is False and d["morning"]["under"] == 0
    w = d["went_wrong"]
    assert w["night"]["wrong"] == 1 and w["night"]["wrong_share"] == 1.0 and w["day"]["wrong_share"] == 0.0 and w["holds"] is False


def test_a_goal_started_before_work_at_night_was_on_is_not_counted_in_the_nights_building_and_a_board_set_off_ends_it(tmp_path):
    E = event_log
    _at(tmp_path,
        ("2026-11-01T10:00:00+00:00", E.PLAN_PASSED, {"idea": "before", "tasks": 1}),
        ("2026-11-02T10:00:00+00:00", E.BOARD_SET, {"work_at_night": True}), ("2026-11-02T11:00:00+00:00", E.PLAN_PASSED, {"idea": "on", "tasks": 1}),
        ("2026-11-03T10:00:00+00:00", E.BOARD_SET, {"work_at_night": False}), ("2026-11-03T11:00:00+00:00", E.PLAN_PASSED, {"idea": "after", "tasks": 1}))
    b = measures.of(tmp_path)["day"]["building"]
    assert (b["started"], b["other"], b["at_night"]) == (1, 1, 0) and b["holds"] is False
