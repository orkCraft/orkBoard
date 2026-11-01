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
