"""The measures of the table (docs/specs/124-the-brief-the-measures-and-the-trial.md §B, hypothesis H1): how good the arguing turned out, read from the
project's own event log (`realm/event_log.py`), by code. No model, no face, no new event: every number is one the log already keeps.

    measures.of(root, since="2026-11-01")     # {talk, concerns, pitches, sketches, results, after_start, since, until}
    measures.text(m)                          # the same as lines a person reads (`orkboard measures`)
    measures.of_party(root, "tech")           # one party's own record of its no's (spec 125 §C): what a leader's call is told of its calibration
    measures.calibration(m)                   # … as the one line a call is given, "" until a no of the party was overruled and decided

What a measure says (H1: *what would prove it*):

- **talk**: the leaders' *no* and *doubt* (`leader_objected`), what the person did with them (`objection_answered`: `drop` · `smaller` · `later` heeded,
  `go` overruled), the share heeded, and the leaders who changed their verdict after the person's answers (`talk_verdict`). **An overruled no that came
  back** is the calibration: of the goals whose objection the person overruled, how many were sent back, fixed or dropped at Review afterwards, beside
  the same share of the goals no leader objected to. A *no* is worth its noise when the goals it lost came back more often than the others.
- **concerns**: what the leaders' looks found on their maps (`concerns_made`) and what the person did: made a goal of it, or *Not a problem*.
- **pitches**: Ideation's decisions (invest · reshape · pass) and how often the person took the Investor's (`as_decided`).
- **sketches**: a sketch picked, asked again or skipped (`sketch_answered`).
- **results**: a goal **accepted the first time**: a merge at Review with no send back, fix or drop before it, of the goals decided at Review.
- **after_start**: the plan changes the person took and the sections written by hand after a plan passed, a started goal's average.

A goal is its slug (`idea`). The log's lines from before an event existed are simply not counted.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from orkboard.realm import event_log

HEEDED = ("drop", "smaller", "later")               # an objection answered by giving way: the goal dropped, made smaller, or put later
OVERRULED = "go"                                    # … or by going on anyway
CAME_BACK = ("back", "fix", "drop")                 # a result decided at Review that says the goal was not right as it was


def _share(part: int, whole: int) -> float | None:
    return round(part / whole, 3) if whole else None


def _came_back(rows: list[dict]) -> dict[str, bool]:
    """Each goal decided at Review: True when a result of it was sent back, fixed or dropped, False when it was merged with none of those."""
    out: dict[str, bool] = {}
    for r in rows:
        if r["event"] != event_log.RESULT_DECIDED or not isinstance(r.get("idea"), str):
            continue
        d = r.get("decision")
        if d in CAME_BACK:
            out[r["idea"]] = True
        elif d == "merge":
            out.setdefault(r["idea"], False)
    return out


def _first_time(rows: list[dict]) -> dict[str, bool]:
    """Each goal decided at Review: True when its first decisive answer was a merge (no send back, fix or drop before it)."""
    out: dict[str, bool] = {}
    for r in rows:
        if r["event"] == event_log.RESULT_DECIDED and isinstance(r.get("idea"), str) and r["idea"] not in out and r.get("decision") in ("merge", *CAME_BACK):
            out[r["idea"]] = r.get("decision") == "merge"
    return out


def _talk(rows: list[dict], back: dict[str, bool]) -> dict[str, Any]:
    objected = [r for r in rows if r["event"] == event_log.LEADER_OBJECTED]
    answered = [r for r in rows if r["event"] == event_log.OBJECTION_ANSWERED]
    kinds = Counter(r.get("answer") for r in answered)
    heeded = sum(kinds[k] for k in HEEDED)
    moved = [r for r in rows if r["event"] == event_log.TALK_VERDICT and r.get("before") != r.get("after")]
    heard = {r.get("idea") for r in rows if r["event"] == event_log.TALK_HEARD}
    overruled = {r.get("idea") for r in answered if r.get("answer") == OVERRULED}
    objected_ideas = {r.get("idea") for r in objected}
    over_decided = [i for i in overruled if i in back]
    calm_decided = [i for i in back if i not in objected_ideas]
    return {"goals_heard": len(heard), "objections": len(objected), "no": sum(r.get("verdict") == "no" for r in objected),
            "doubt": sum(r.get("verdict") == "doubt" for r in objected), "with_instead": sum(bool(r.get("has_instead")) for r in objected),
            "answered": len(answered), "heeded": heeded, "overruled": kinds[OVERRULED], "heeded_share": _share(heeded, len(answered)),
            "answers": {k: kinds[k] for k in (*HEEDED, OVERRULED)},
            "minds_changed": len(moved), "toward_go": sum(r.get("after") == "go" for r in moved),
            "hearings": dict(Counter(str(r.get("kind") or "") for r in rows if r["event"] == event_log.HEARING_THROWN)),
            "overruled_goals": len(overruled), "overruled_decided": len(over_decided),
            "overruled_came_back": sum(back[i] for i in over_decided), "overruled_came_back_share": _share(sum(back[i] for i in over_decided), len(over_decided)),
            "unobjected_decided": len(calm_decided), "unobjected_came_back_share": _share(sum(back[i] for i in calm_decided), len(calm_decided))}


def _concerns(rows: list[dict]) -> dict[str, Any]:
    made = [r for r in rows if r["event"] == event_log.CONCERNS_MADE]
    to_goal = sum(r["event"] == event_log.CONCERN_GOAL for r in rows)
    dismissed = sum(r["event"] == event_log.CONCERN_DISMISSED for r in rows)
    return {"looks": len(made), "found": sum(int(r.get("n") or 0) for r in made if isinstance(r.get("n"), int)),
            "opened": sum(r["event"] == event_log.CONCERN_OPENED for r in rows), "made_goal": to_goal, "dismissed": dismissed,
            "goal_share": _share(to_goal, to_goal + dismissed)}


def _pitches(rows: list[dict]) -> dict[str, Any]:
    judged = Counter(str(r.get("answer") or "") for r in rows if r["event"] == event_log.PITCH_JUDGED)
    taken = [r for r in rows if r["event"] in (event_log.PITCH_SENT, event_log.PITCH_PASSED)]
    agreed = sum(r.get("as_decided") is True for r in taken)
    return {"judged": sum(judged.values()), "invest": judged["invest"], "reshape": judged["reshape"], "pass": judged["pass"],
            "decided_by_person": len(taken), "as_the_investor_said": agreed, "agreed_share": _share(agreed, len(taken))}


def _sketches(rows: list[dict]) -> dict[str, Any]:
    got = Counter(str(r.get("answer") or "") for r in rows if r["event"] == event_log.SKETCH_ANSWERED)
    whole = got["picked"] + got["again"] + got["skipped"]
    return {"made": sum(r["event"] == event_log.SKETCH_MADE for r in rows), "picked": got["picked"], "again": got["again"],
            "skipped": got["skipped"], "picked_share": _share(got["picked"], whole)}


def _after_start(rows: list[dict]) -> dict[str, Any]:
    started = {r.get("idea") for r in rows if r["event"] == event_log.PLAN_PASSED}
    changes = defaultdict(int)
    for r in rows:
        if r["event"] == event_log.PLAN_CHANGE_ANSWERED and r.get("take") is True and r.get("idea") in started:
            changes[r["idea"]] += 1
        elif r["event"] == event_log.IDEA_EDITED and r.get("passed") is True and r.get("idea") in started:
            changes[r["idea"]] += 1
    n = sum(changes.values())
    return {"started": len(started), "changes": n, "goals_changed": len(changes), "per_goal": round(n / len(started), 2) if started else None}


def of(root: Path, since: str = "", until: str = "") -> dict[str, Any]:
    """The measures of the project at `root` from its event log, `since` / `until` as `event_log.read` takes them."""
    rows = event_log.read(Path(root), since, until)
    back, first = _came_back(rows), _first_time(rows)
    return {"since": since or (rows[0]["at"] if rows else ""), "until": until or (rows[-1]["at"] if rows else ""),
            "talk": _talk(rows, back), "concerns": _concerns(rows), "pitches": _pitches(rows), "sketches": _sketches(rows),
            "results": {"decided": len(first), "first_time": sum(first.values()), "first_time_share": _share(sum(first.values()), len(first))},
            "after_start": _after_start(rows)}


def of_party(root: Path, party: str) -> dict[str, Any]:
    """One party's record of its objections (spec 125 §C; decisions §203.5), from the party's own `leader_objected` / `objection_answered` lines and the goals' `result_decided`:
    `objections` (its doubts and no's), `overruled` (answered *go on anyway*), `overruled_decided` (of the goals it was overruled on, those decided at Review),
    `overruled_came_back` (of those, sent back, fixed or dropped) and `unobjected_came_back_share` (the same share over the goals no leader objected to; None with none)."""
    rows = event_log.read(Path(root))
    back = _came_back(rows)
    mine = [r for r in rows if r.get("party") == party]
    objections = sum(r["event"] == event_log.LEADER_OBJECTED for r in mine)
    overruled = [r for r in mine if r["event"] == event_log.OBJECTION_ANSWERED and r.get("answer") == OVERRULED]
    decided = [i for i in {r.get("idea") for r in overruled} if i in back]
    objected_any = {r.get("idea") for r in rows if r["event"] == event_log.LEADER_OBJECTED}
    calm = [i for i in back if i not in objected_any]
    return {"objections": objections, "overruled": len(overruled), "overruled_decided": len(decided),
            "overruled_came_back": sum(back[i] for i in decided), "unobjected_came_back_share": _share(sum(back[i] for i in calm), len(calm))}


def calibration(m: dict[str, Any]) -> str:
    """The line a leader's call is given of its record (`of_party`), "" until it has had a no overruled and decided at Review: *Your record: 3 of your 5 no's were overruled;
    2 of the 3 decided came back at Review (67 %), against 20 % of the goals no one objected to.*"""
    decided = int(m.get("overruled_decided") or 0)
    if decided <= 0:
        return ""
    came = int(m.get("overruled_came_back") or 0)
    other = m.get("unobjected_came_back_share")
    against = f", against {_pct(other)} of the goals no one objected to" if other is not None else ""
    return (f"Your record: {int(m.get('overruled') or 0)} of your {int(m.get('objections') or 0)} no's were overruled; {came} of the {decided} decided "
            f"came back at Review ({_pct(_share(came, decided))}){against}.")


def _pct(x: float | None) -> str:
    return "—" if x is None else f"{round(x * 100)} %"


def text(m: dict[str, Any]) -> str:
    """The measures as lines a person reads, in the product's words."""
    t, c, p, s, r, a = m["talk"], m["concerns"], m["pitches"], m["sketches"], m["results"], m["after_start"]
    span = f"{m['since'][:10]} – {m['until'][:10]}" if m["since"] else "nothing in the log yet"
    lines = [f"Orkboard's measures ({span})", "",
             "The leaders' word on goals",
             f"  goals talked over: {t['goals_heard']} · a no: {t['no']} · a doubt: {t['doubt']} (with a smaller or other goal named: {t['with_instead']})",
             f"  you gave way to {t['heeded']} of {t['answered']} ({_pct(t['heeded_share'])}): dropped {t['answers']['drop']}, made smaller "
             f"{t['answers']['smaller']}, put later {t['answers']['later']}; went on anyway {t['overruled']}",
             f"  leaders who changed their verdict after your answers: {t['minds_changed']} ({t['toward_go']} toward go)",
             f"  goals you went on with against a no, then sent back, fixed or dropped at Review: {t['overruled_came_back']} of {t['overruled_decided']} "
             f"({_pct(t['overruled_came_back_share'])}); of the goals no leader objected to: {_pct(t['unobjected_came_back_share'])} of {t['unobjected_decided']}",
             "", "Concerns on the maps",
             f"  looks: {c['looks']} · concerns found: {c['found']} · made a goal: {c['made_goal']} · not a problem: {c['dismissed']} ({_pct(c['goal_share'])} made a goal)",
             "", "Ideation",
             f"  pitches judged: {p['judged']} (invest {p['invest']}, reshape {p['reshape']}, pass {p['pass']}) · you took the Investor's word on "
             f"{p['as_the_investor_said']} of {p['decided_by_person']} ({_pct(p['agreed_share'])})",
             "", "Sketches",
             f"  made: {s['made']} · picked: {s['picked']} · asked again: {s['again']} · skipped: {s['skipped']} ({_pct(s['picked_share'])} picked)",
             "", "What came out",
             f"  goals accepted the first time at Review: {r['first_time']} of {r['decided']} ({_pct(r['first_time_share'])})",
             f"  changes after the start (plan changes taken, sections written by hand): {a['changes']} on {a['goals_changed']} of {a['started']} goals started"
             + (f" ({a['per_goal']} a goal)" if a["per_goal"] is not None else "")]
    return "\n".join(lines)
