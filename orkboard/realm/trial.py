"""The head-to-head of hypothesis H1 (docs/hypotheses.md, docs/specs/124-the-brief-the-measures-and-the-trial.md §C, the protocol
docs/trials/h1-head-to-head.md): the same real tasks done twice, in Orkboard and with an AI tool's plan mode alone, judged blind, tallied by code.

    trial.template(path, tasks, seed)     # a CSV to fill: two rows a task, each way shown as A or B at random (the person judges A and B, never the way)
    trial.read(path)                      # the rows, checked: ValueError in plain words for a row that is not one
    trial.tally(rows)                     # {ways: {orkboard, plan}, tasks, gap_points, minutes_ratio, verdict, why}
    trial.text(t)                         # the tally as lines a person reads (`orkboard trial <file.csv>`)

A row is `task, way, shown_as, accepted, changes, questions, minutes, tokens`: `way` `orkboard` or `plan`; `shown_as` `A` or `B` (what the judge saw);
`accepted` `yes` or `no` (taken the first time, by the person, blind); `changes` the plan changes and forks after the start; `questions` asked during
the work; `minutes` the person's own; `tokens` the tools' (empty when unknown). **It holds** (H1) when Orkboard's share accepted the first time beats
plan mode's by `GAP` points or more, at no more than `MINUTES_RATIO` times the person's minutes, over `MIN_TASKS` tasks or more done both ways.
No model, no face, no network.
"""
from __future__ import annotations

import csv
import random
from pathlib import Path
from typing import Any

WAYS = ("orkboard", "plan")
COLUMNS = ("task", "way", "shown_as", "accepted", "changes", "questions", "minutes", "tokens")
GAP = 20                     # points of first-time acceptance Orkboard must win by
MINUTES_RATIO = 2.0          # … at no more than this many times the person's minutes
MIN_TASKS = 10               # … over this many tasks done both ways, at least


def template(path: Path, tasks: list[str], seed: int | None = None) -> Path:
    """A CSV to fill, two rows a task (one a way), each way shown to the judge as A or B at random; the results' columns empty. ValueError for no task or a task twice."""
    names = [" ".join(str(t).split()) for t in tasks]
    if not names or not all(names):
        raise ValueError("Name the tasks, one a line")
    if len(set(names)) != len(names):
        raise ValueError("A task is named twice")
    rng = random.Random(seed)
    path = Path(path)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(COLUMNS)
        for name in names:
            labels = ["A", "B"]
            rng.shuffle(labels)
            for way, label in zip(WAYS, labels):
                w.writerow([name, way, label, "", "", "", "", ""])
    return path


def _num(row: dict, key: str, n: int, whole: bool, need: bool = True) -> float | None:
    raw = str(row.get(key) or "").strip()
    if not raw:
        if need:
            raise ValueError(f"Row {n}: {key} is empty")
        return None
    try:
        v = int(raw) if whole else float(raw)
    except ValueError:
        raise ValueError(f"Row {n}: {key} is a number, not {raw!r}") from None
    if v < 0:
        raise ValueError(f"Row {n}: {key} is never below 0")
    return v


def read(path: Path) -> list[dict[str, Any]]:
    """The filled rows, checked; a row whose `accepted` is still empty is not done yet and left out. ValueError, in plain words, for a row that is not one."""
    try:
        with Path(path).open(newline="", encoding="utf-8") as f:
            raw = list(csv.DictReader(f))
    except OSError as e:
        raise ValueError(f"The file cannot be read: {e.strerror or e}") from None
    out = []
    for n, row in enumerate(raw, start=2):
        way = str(row.get("way") or "").strip().lower()
        if way not in WAYS:
            raise ValueError(f"Row {n}: the way is orkboard or plan, not {row.get('way')!r}")
        accepted = str(row.get("accepted") or "").strip().lower()
        if not accepted:
            continue
        if accepted not in ("yes", "no"):
            raise ValueError(f"Row {n}: accepted is yes or no, not {row.get('accepted')!r}")
        out.append({"task": " ".join(str(row.get("task") or "").split()), "way": way, "accepted": accepted == "yes",
                    "changes": _num(row, "changes", n, True), "questions": _num(row, "questions", n, True),
                    "minutes": _num(row, "minutes", n, False), "tokens": _num(row, "tokens", n, True, need=False)})
    return out


def _avg(xs: list[float]) -> float | None:
    return round(sum(xs) / len(xs), 2) if xs else None


def tally(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Each way's measures over the tasks done both ways, and the verdict: `holds`, `does not hold` or `too few` (fewer than `MIN_TASKS`), with why."""
    by: dict[str, dict[str, dict]] = {w: {} for w in WAYS}
    for r in rows:
        by[r["way"]][r["task"]] = r
    both = sorted(set(by["orkboard"]) & set(by["plan"]))
    ways = {}
    for w in WAYS:
        mine = [by[w][t] for t in both]
        tokens = [r["tokens"] for r in mine if r["tokens"] is not None]
        ways[w] = {"tasks": len(mine), "accepted": sum(r["accepted"] for r in mine),
                   "accepted_share": round(sum(r["accepted"] for r in mine) / len(mine), 3) if mine else None,
                   "changes": _avg([r["changes"] for r in mine]), "questions": _avg([r["questions"] for r in mine]),
                   "minutes": _avg([r["minutes"] for r in mine]), "tokens": _avg(tokens)}
    o, p = ways["orkboard"], ways["plan"]
    gap = round((o["accepted_share"] - p["accepted_share"]) * 100, 1) if both else None
    ratio = round(o["minutes"] / p["minutes"], 2) if both and p["minutes"] else None
    if len(both) < MIN_TASKS:
        verdict, why = "too few", f"{len(both)} tasks done both ways; the trial needs {MIN_TASKS} at least"
    elif gap is not None and gap >= GAP and (ratio is None or ratio <= MINUTES_RATIO):
        verdict, why = "holds", f"Orkboard is accepted the first time {gap} points more often, at {ratio if ratio is not None else '—'}× the minutes"
    else:
        gap_ok = gap is not None and gap >= GAP
        verdict = "does not hold"
        why = (f"Orkboard wins by {gap} points, but takes {ratio}× the minutes (at most {MINUTES_RATIO}×)" if gap_ok
               else f"Orkboard wins by {gap} points; it needs {GAP} or more")
    return {"ways": ways, "tasks": len(both), "gap_points": gap, "minutes_ratio": ratio, "verdict": verdict, "why": why,
            "one_way_only": sorted(set(by["orkboard"]) ^ set(by["plan"]))}


def text(t: dict[str, Any]) -> str:
    """The tally as lines a person reads."""
    def cell(v: Any, pct: bool = False) -> str:
        return "—" if v is None else f"{round(v * 100)} %" if pct else str(v)
    lines = [f"H1 head-to-head: {t['tasks']} tasks done both ways", "",
             f"{'':28}{'Orkboard':>12}{'plan mode':>12}"]
    o, p = t["ways"]["orkboard"], t["ways"]["plan"]
    for label, key, pct in (("accepted the first time", "accepted_share", True), ("changes after the start", "changes", False),
                            ("questions during the work", "questions", False), ("your minutes", "minutes", False), ("tokens", "tokens", False)):
        lines.append(f"{label:28}{cell(o[key], pct):>12}{cell(p[key], pct):>12}")
    lines += ["", f"Verdict: {t['verdict']}: {t['why']}"]
    if t["one_way_only"]:
        lines.append(f"Done one way only (not counted): {', '.join(t['one_way_only'])}")
    return "\n".join(lines)
