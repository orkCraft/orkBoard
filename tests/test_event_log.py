"""The local event log (realm/event_log.py, docs/design/dogfood-logs.md §3): exact, local, never sent."""
import datetime as dt
import json

from orkboard.realm import event_log


def test_an_event_is_one_exact_line_in_the_towns_folder(tmp_path):
    assert event_log.record(tmp_path, event_log.ASKED, building="pool", ork="Grunt", task="t1", harness="claude",
                            text="Which port?", options=["8080", "3000"], via="block")
    [row] = event_log.read(tmp_path)
    assert (tmp_path / ".orkcraft" / "usage" / "events.jsonl").is_file()
    assert row["event"] == "question_asked" and row["text"] == "Which port?" and row["options"] == ["8080", "3000"]
    assert dt.datetime.fromisoformat(row["at"]).tzinfo is not None


def test_counts_and_the_weeks_summary(tmp_path):
    old = dt.datetime(2026, 10, 1, 9, tzinfo=dt.timezone.utc)
    (tmp_path / event_log.PATH).parent.mkdir(parents=True)
    (tmp_path / event_log.PATH).write_text(json.dumps(event_log.line(event_log.ASKED, at=old)) + "\nnot json\n")
    for who, waited in (("person", 600), ("person", 60), ("steward", 5), ("person", 120)):
        event_log.record(tmp_path, event_log.ANSWERED, building="pool", task="t", who=who, waited_s=waited)
    event_log.record(tmp_path, event_log.STOPPED, building="pool", task="t")
    c = event_log.counts(tmp_path, since="2026-10-10")
    assert c["question_answered"] == 4 and c["run_stopped_on_question"] == 1 and c["question_asked"] == 0
    assert event_log.counts(tmp_path)["question_asked"] == 1
    s = event_log.summary(tmp_path, since="2026-10-10")
    assert s["answer_wait_median_s"] == 120 and s["counts"]["quest_done"] == 0


def test_the_gate_merging_dev_into_main_is_an_event_with_its_counts(tmp_path):
    assert event_log.GATE_MERGED == "gate_merged" and event_log.GATE_MERGED in event_log.EVENTS
    assert event_log.record(tmp_path, event_log.GATE_MERGED, commits=3, ideas=2, files=5, how="merge", pushed=False,
                            into="dev", main="main", device="desktop")
    [row] = event_log.read(tmp_path)
    assert (row["event"], row["commits"], row["ideas"], row["files"], row["how"], row["pushed"]) == ("gate_merged", 3, 2, 5, "merge", False)
    assert event_log.counts(tmp_path)["gate_merged"] == 1 and len(set(event_log.EVENTS)) == len(event_log.EVENTS)


def test_a_goal_raising_its_flag_is_an_event_with_what_it_took(tmp_path):
    """Spec 50 §2.2: `idea_flagged` — the goal, its party, who raised it, its tally (usd null when unpriced, never 0)."""
    assert event_log.IDEA_FLAGGED == "idea_flagged" and event_log.IDEA_FLAGGED in event_log.EVENTS
    assert event_log.record(tmp_path, event_log.IDEA_FLAGGED, idea="dark-mode", goal="ux", by="gate", tasks=4, first_time=3, usd=None, days=2)
    [row] = event_log.read(tmp_path)
    assert (row["event"], row["idea"], row["goal"], row["by"], row["tasks"], row["first_time"], row["usd"], row["days"]) == (
        "idea_flagged", "dark-mode", "ux", "gate", 4, 3, None, 2)
    assert event_log.counts(tmp_path)["idea_flagged"] == 1


def test_a_goal_of_a_type_who_joins_and_a_plans_missing_are_in_the_events_spec_52(tmp_path):
    """Spec 52 §2.7: `idea_added` with its type, asks answered, Refs' pictures, who joined and who left; `goal_saved` with
    joined, out and via; `plan_passed` with who joined and how many kinds the plan missed."""
    assert event_log.record(tmp_path, event_log.IDEA_ADDED, idea="logo", track="brand", type="logo", asks=1,
                            refs=2, joined="artist", out="", offered=9, near=2, device="desktop")
    assert event_log.record(tmp_path, event_log.GOAL_SAVED, goal="brand", new=False, joined="artist", out="ui-kit", via="type", preset="game", stages="4/1")
    assert event_log.record(tmp_path, event_log.PLAN_PASSED, idea="logo", tasks=3, by="person", joined="", missing=1)
    added, saved, passed = event_log.read(tmp_path)
    assert (added["type"], added["asks"], added["refs"], added["joined"], added["out"]) == ("logo", 1, 2, "artist", "")
    assert (added["offered"], added["near"]) == (9, 2)
    assert (saved["joined"], saved["out"], saved["via"]) == ("artist", "ui-kit", "type")
    assert (saved["preset"], saved["stages"]) == ("game", "4/1")                                   # spec 59 §5
    assert (passed["joined"], passed["missing"]) == ("", 1)
    from pathlib import Path
    source = Path(event_log.__file__).read_text(encoding="utf-8")
    assert "type (its goal type's id" in source and 'via ("type"' in source and "missing (how many kinds" in source     # the fields named where the events are
    assert "offered (how many types" in source and "near (how many of them" in source and "preset (the library's party" in source and '"<builders>/<checkers>"' in source


def test_the_maps_events_are_spec_89s(tmp_path):
    """Spec 89 §1, §4: a leader's map opened (its lens, the parts, how many changed, hours since the last look), a part pressed, and a
    snapshot that failed after a landing."""
    for name, value in (("MAP_OPENED", "map_opened"), ("MAP_PART_PRESSED", "map_part_pressed"), ("MAP_SNAPSHOT_FAILED", "map_snapshot_failed")):
        assert getattr(event_log, name) == value and value in event_log.EVENTS
    assert len(set(event_log.EVENTS)) == len(event_log.EVENTS)
    event_log.record(tmp_path, event_log.MAP_OPENED, lens="system", party="tech", parts=12, changed=3, hours=17.5, device="desktop")
    event_log.record(tmp_path, event_log.MAP_PART_PRESSED, lens="system", party="tech", changed="new", goals=1, device="desktop")
    event_log.record(tmp_path, event_log.MAP_SNAPSHOT_FAILED, commit="0123456789ab", why="disk full")
    opened, pressed, failed = event_log.read(tmp_path)
    assert (opened["lens"], opened["parts"], opened["changed"], opened["hours"]) == ("system", 12, 3, 17.5)
    assert (pressed["changed"], pressed["goals"], failed["commit"], failed["why"]) == ("new", 1, "0123456789ab", "disk full")
    assert event_log.counts(tmp_path)["map_opened"] == 1


def test_a_refused_command_and_a_red_toast_are_the_events_of_spec_107(tmp_path):
    """Spec 107 §2.1, §2.2: what the host refused (its name, what it said, who asked, whether it broke) and what was shown red."""
    for name, value in (("COMMAND_REFUSED", "command_refused"), ("ERROR_SHOWN", "error_shown")):
        assert getattr(event_log, name) == value and value in event_log.EVENTS
    assert len(set(event_log.EVENTS)) == len(event_log.EVENTS)
    event_log.record(tmp_path, event_log.COMMAND_REFUSED, command="ideas.add", error="x" * 5000, device="phone", kind="broken")
    event_log.record(tmp_path, event_log.ERROR_SHOWN, title="Town clock", text="KeyError: 'x'")
    refused, shown = event_log.read(tmp_path)
    assert (refused["command"], refused["device"], refused["kind"], len(refused["error"])) == ("ideas.add", "phone", "broken", event_log.TEXT_MAX)
    assert (shown["title"], shown["text"]) == ("Town clock", "KeyError: 'x'")
    assert event_log.counts(tmp_path)["command_refused"] == 1 and event_log.counts(tmp_path)["error_shown"] == 1


def test_the_moves_of_the_hand_are_events(tmp_path):
    """Spec 171 D: a one-press move played and put back, idea, kind and from only."""
    assert event_log.MOVE_PLAYED == "move_played" and event_log.MOVE_UNDONE == "move_undone"
    assert {"move_played", "move_undone"} <= set(event_log.EVENTS) and len(set(event_log.EVENTS)) == len(event_log.EVENTS)
    assert event_log.record(tmp_path, event_log.MOVE_PLAYED, idea="goal", kind="drop", **{"from": "hand"})
    assert event_log.counts(tmp_path)["move_played"] == 1
