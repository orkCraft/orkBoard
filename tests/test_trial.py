"""Spec 124 C (docs/specs/124-the-brief-the-measures-and-the-trial.md, docs/trials/h1-head-to-head.md): hypothesis H1's head-to-head. A CSV to fill, each way
shown blind as A or B; its rows checked in plain words; the tally over the tasks done both ways and H1's verdict: Orkboard accepted the first time 20 points
more often at no more than twice the minutes, over ten tasks at least. And `orkboard trial`."""
from __future__ import annotations

import csv
import json

import pytest

from orkboard.gui import board_cli
from orkboard.realm import trial


def _fill(path, results):
    """`results`: {task: {way: (accepted, changes, questions, minutes, tokens)}} written into the template's rows."""
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        got = results.get(r["task"], {}).get(r["way"])
        if got:
            r.update(accepted="yes" if got[0] else "no", changes=got[1], questions=got[2], minutes=got[3], tokens="" if got[4] is None else got[4])
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=trial.COLUMNS)
        w.writeheader()
        w.writerows(rows)


def test_the_template_is_two_rows_a_task_each_way_shown_as_a_or_b_at_random(tmp_path):
    p = trial.template(tmp_path / "h1.csv", ["Add a lobby", "  Fix the  timer "], seed=7)
    with p.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert [(r["task"], r["way"]) for r in rows] == [("Add a lobby", "orkboard"), ("Add a lobby", "plan"), ("Fix the timer", "orkboard"), ("Fix the timer", "plan")]
    for a, b in (rows[0:2], rows[2:4]):
        assert {a["shown_as"], b["shown_as"]} == {"A", "B"}
    assert all(r["accepted"] == "" for r in rows) and trial.read(p) == []                       # nothing done yet
    seen = {tuple(r["shown_as"] for r in csv.DictReader((trial.template(tmp_path / f"s{s}.csv", [f"t{i}" for i in range(8)], seed=s)).open())) for s in range(4)}
    assert len(seen) > 1                                                                           # the draw changes with the seed
    with pytest.raises(ValueError, match="named twice"):
        trial.template(tmp_path / "x.csv", ["a", "a"])
    with pytest.raises(ValueError, match="Name the tasks"):
        trial.template(tmp_path / "x.csv", [])


def _results(n, ork_yes, plan_yes, ork_min=20, plan_min=15):
    return {f"t{i}": {"orkboard": (i < ork_yes, 0, 1, ork_min, 1000), "plan": (i < plan_yes, 2, 3, plan_min, None)} for i in range(n)}


def test_it_holds_when_orkboard_wins_by_twenty_points_at_no_more_than_twice_the_minutes(tmp_path):
    p = trial.template(tmp_path / "h1.csv", [f"t{i}" for i in range(10)], seed=1)
    _fill(p, _results(10, 8, 5))
    t = trial.tally(trial.read(p))
    assert (t["tasks"], t["gap_points"], t["minutes_ratio"], t["verdict"]) == (10, 30.0, 1.33, "holds")
    o, pl = t["ways"]["orkboard"], t["ways"]["plan"]
    assert (o["accepted_share"], pl["accepted_share"], o["changes"], pl["changes"], o["tokens"], pl["tokens"]) == (0.8, 0.5, 0.0, 2.0, 1000.0, None)
    assert "Verdict: holds" in trial.text(t)


def test_orkboard_trial_new_and_the_tally(tmp_path, capsys):
    tasks = tmp_path / "tasks.txt"
    tasks.write_text("\n".join(f"t{i}" for i in range(10)) + "\n\n", encoding="utf-8")
    out = tmp_path / "h1.csv"
    assert board_cli.run(["trial", "new", str(out), "--tasks", str(tasks), "--seed", "3"]) == 0
    assert "10 tasks, two rows each" in capsys.readouterr().out
    assert board_cli.run(["trial", "new", str(out), "--tasks", str(tasks)]) == 2 and "is there already" in capsys.readouterr().err
    _fill(out, _results(10, 9, 4))
    assert board_cli.run(["trial", str(out)]) == 0 and "Verdict: holds" in capsys.readouterr().out
    assert board_cli.run(["trial", str(out), "--json"]) == 0 and json.loads(capsys.readouterr().out)["verdict"] == "holds"
    assert board_cli.run(["trial", str(tmp_path / "none.csv")]) == 2 and "cannot be read" in capsys.readouterr().err
    assert board_cli.run(["trial", "new", str(tmp_path / "x.csv")]) == 2
