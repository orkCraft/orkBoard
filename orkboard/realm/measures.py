"""The measures of the table (docs/specs/124-the-brief-the-measures-and-the-trial.md §B, hypothesis H1): how good the arguing turned out, read from the
project's own event log (`realm/event_log.py`), by code. No model, no face: every number is one the log keeps (the day's, below, needed one event more: `play_mark`).

    measures.of(root, since="2026-11-01")     # {talk, concerns, pitches, sketches, results, after_start, day, since, until}
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
- **day** (spec 121 §G, hypothesis H2: an indie maker's day is three jobs): the morning, the sketches by day and the night's building, each of the criteria H2 names with its numbers and `holds` (True, False, or
  None while there is nothing to read): `first_sketch` (the minutes from a goal's being added to its first `sketch_made`; holds when the median is within 15), `sketches` (picked of the answers, `picked_share`;
  holds when most were picked; the refutation is most skipped), `building` (of the goals started while *Work at night* was on — a `board_set` that said so, or a night hold, a night start or a *Build it now* that
  proves it —: how many started in the night's window (`night_started`), by *Build it now* (`built_now`) or otherwise (a press that starts at once, a bug's short way); holds when most started at night; the
  refutation is *Build it now* for most of the held goals), `morning` (the minutes from the morning's card lifted to the first mark on Play, `play_mark`'s `minutes_since_open`; holds when the median is under 2),
  `went_wrong` (the goals whose building started at night against those started by day, each: a task failed, or a result sent back, fixed or dropped at Review; holds when the night's share is the smaller).
  "Most" is more than half. A goal's start is its first `plan_passed` (or `night_started`, `built_now`).

A goal is its slug (`idea`). The log's lines from before an event existed are simply not counted.
"""
from __future__ import annotations

import datetime as dt
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from orkboard.realm import event_log

HEEDED = ("drop", "smaller", "later")               # an objection answered by giving way: the goal dropped, made smaller, or put later
OVERRULED = "go"                                    # … or by going on anyway
CAME_BACK = ("back", "fix", "drop")                 # a result decided at Review that says the goal was not right as it was
SKETCH_WITHIN_MIN = 15                              # H2: a goal's first sketch comes within this many minutes of the goal
MARK_WITHIN_MIN = 2                                 # H2: from the morning's card to the first mark on Play takes under this many minutes


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


def _when(at: object) -> dt.datetime | None:
    """A line's `at` as a time (a line written without a zone is the machine's own)."""
    try:
        d = dt.datetime.fromisoformat(str(at))
    except ValueError:
        return None
    return d if d.tzinfo else d.astimezone()


def _median(xs: list[float]) -> float | None:
    s = sorted(xs)
    if not s:
        return None
    mid = len(s) // 2
    return round(s[mid] if len(s) % 2 else (s[mid - 1] + s[mid]) / 2, 1)


def _first_sketch(rows: list[dict]) -> dict[str, Any]:
    """Each goal's minutes from `idea_added` to its first `sketch_made`; a goal whose adding is not in the log (before the log, or the window) is not counted."""
    added: dict[str, dt.datetime] = {}
    made: dict[str, dt.datetime] = {}
    for r in rows:
        idea, at = r.get("idea"), _when(r.get("at"))
        if not isinstance(idea, str) or at is None:
            continue
        if r["event"] == event_log.IDEA_ADDED:
            added.setdefault(idea, at)
        elif r["event"] == event_log.SKETCH_MADE:
            made.setdefault(idea, at)
    mins = [max(0.0, (made[i] - added[i]).total_seconds() / 60) for i in made if i in added]
    within = sum(m <= SKETCH_WITHIN_MIN for m in mins)
    median = _median(mins)
    return {"goals": len(mins), "within": within, "within_share": _share(within, len(mins)), "median_minutes": median, "holds": None if median is None else median <= SKETCH_WITHIN_MIN}


def _day_sketches(rows: list[dict], s: dict[str, Any]) -> dict[str, Any]:
    """The sketches picked of the answers (`_sketches`), those skipped (by the person's answer or because the sketch was not made: `sketch_skipped`) and the goals asked again three times."""
    again = Counter(r.get("idea") for r in rows if r["event"] == event_log.SKETCH_ANSWERED and r.get("answer") == "again")
    answered = s["picked"] + s["again"] + s["skipped"]
    return {"made": s["made"], "answered": answered, "picked": s["picked"], "picked_share": s["picked_share"], "skipped": s["skipped"],
            "not_made": sum(r["event"] == event_log.SKETCH_SKIPPED for r in rows), "again_three_times": sum(n >= 3 for n in again.values()),
            "holds": None if not answered else s["picked"] * 2 > answered, "refuted": None if not answered else s["skipped"] * 2 > answered}


def _starts(rows: list[dict]) -> dict[str, dict[str, Any]]:
    """Each goal's start: `{at, how: "night" | "now" | "other", on}`: `night` (`night_started`), `now` (*Build it now*, `built_now`) or `other`; `on`: *Work at night* was on when it began (a `board_set` that said so, or the
    night's own events, which prove it). A goal is started once: its first `plan_passed`, `night_started` or `built_now`."""
    on, out, held = False, {}, set()
    for r in rows:
        e, idea = r["event"], r.get("idea")
        if e == event_log.BOARD_SET and isinstance(r.get("work_at_night"), bool):
            on = r["work_at_night"]
        elif e in (event_log.NIGHT_HELD, event_log.NIGHT_STARTED, event_log.BUILT_NOW):
            on = True
        if not isinstance(idea, str):
            continue
        if e == event_log.NIGHT_HELD:
            held.add(idea)
        how = {event_log.NIGHT_STARTED: "night", event_log.BUILT_NOW: "now", event_log.PLAN_PASSED: "other"}.get(e)
        if how is None:
            continue
        if idea not in out:
            out[idea] = {"at": r.get("at"), "how": how, "on": on}
        elif how != "other" and out[idea]["how"] == "other":
            out[idea]["how"], out[idea]["on"] = how, True                        # the plan passed line came first, the night's own says how
    for idea in held:
        out.setdefault(idea, {"at": None, "how": "held", "on": True})            # held and not started yet
    return out


def _building(starts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Of the goals started while *Work at night* was on: how many started in the night's window, by *Build it now*, otherwise; and *Build it now* as a share of the goals the night held."""
    mine = [s for s in starts.values() if s["on"] and s["how"] != "held"]
    night, now = sum(s["how"] == "night" for s in mine), sum(s["how"] == "now" for s in mine)
    held = sum(s["on"] for s in starts.values() if s["how"] in ("held", "night", "now"))
    return {"started": len(mine), "at_night": night, "built_now": now, "other": len(mine) - night - now, "night_share": _share(night, len(mine)), "held": held,
            "built_now_share": _share(now, held), "holds": None if not mine else night * 2 > len(mine), "refuted": None if not held else now * 2 > held}


def _morning(rows: list[dict]) -> dict[str, Any]:
    """The morning's card lifted and the first marks on Play after it: `minutes_since_open` of a `play_mark` (the host puts it on the first mark after an opening only)."""
    mins = [float(r["minutes_since_open"]) for r in rows if r["event"] == event_log.PLAY_MARK and isinstance(r.get("minutes_since_open"), (int, float)) and not isinstance(r.get("minutes_since_open"), bool)]
    under = sum(m < MARK_WITHIN_MIN for m in mins)
    median = _median(mins)
    return {"opened": sum(r["event"] == event_log.NIGHT_CARD_OPENED for r in rows), "first_marks": len(mins), "under": under, "under_share": _share(under, len(mins)),
            "median_minutes": median, "holds": None if median is None else median < MARK_WITHIN_MIN}


def _went_wrong(rows: list[dict], starts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """The goals started at night against those started by day: each how many had a task fail or a result sent back, fixed or dropped at Review (the work taken back)."""
    failed = {r.get("idea") for r in rows if r["event"] == event_log.TASK_STATE and r.get("state") == "failed"}
    back = {r.get("idea") for r in rows if r["event"] == event_log.RESULT_DECIDED and r.get("decision") in CAME_BACK}
    out: dict[str, Any] = {}
    for kind, in_kind in (("night", lambda s: s["how"] == "night"), ("day", lambda s: s["how"] in ("now", "other"))):
        ideas_ = [i for i, s in starts.items() if in_kind(s)]
        wrong = [i for i in ideas_ if i in failed or i in back]
        out[kind] = {"goals": len(ideas_), "failed": sum(i in failed for i in ideas_), "sent_back": sum(i in back for i in ideas_), "wrong": len(wrong), "wrong_share": _share(len(wrong), len(ideas_))}
    n, d = out["night"]["wrong_share"], out["day"]["wrong_share"]
    out["holds"] = None if n is None or d is None else n < d
    return out


def _day(rows: list[dict], sketches: dict[str, Any]) -> dict[str, Any]:
    """Hypothesis H2 (docs/hypotheses.md; spec 121 §G): the criteria the owner's week is read against, from the events of spec 121 (`sketch_*`, `night_*`, `built_now`, `play_at_path`, `play_mark`)."""
    starts = _starts(rows)
    return {"first_sketch": _first_sketch(rows), "sketches": _day_sketches(rows, sketches), "building": _building(starts), "morning": _morning(rows),
            "went_wrong": _went_wrong(rows, starts), "play_at_path": sum(r["event"] == event_log.PLAY_AT_PATH for r in rows)}


def of(root: Path, since: str = "", until: str = "") -> dict[str, Any]:
    """The measures of the project at `root` from its event log, `since` / `until` as `event_log.read` takes them."""
    rows = event_log.read(Path(root), since, until)
    back, first, sketches = _came_back(rows), _first_time(rows), _sketches(rows)
    return {"since": since or (rows[0]["at"] if rows else ""), "until": until or (rows[-1]["at"] if rows else ""),
            "talk": _talk(rows, back), "concerns": _concerns(rows), "pitches": _pitches(rows), "sketches": sketches,
            "results": {"decided": len(first), "first_time": sum(first.values()), "first_time_share": _share(sum(first.values()), len(first))},
            "after_start": _after_start(rows), "day": _day(rows, sketches)}


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
    t, c, p, s, r, a, d = m["talk"], m["concerns"], m["pitches"], m["sketches"], m["results"], m["after_start"], m["day"]
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
             + (f" ({a['per_goal']} a goal)" if a["per_goal"] is not None else ""),
             *_day_lines(d)]
    return "\n".join(lines)


def _says(holds: bool | None) -> str:
    return "holds" if holds is True else "does not hold" if holds is False else "nothing to read yet"


def _mins(x: float | None) -> str:
    return "—" if x is None else f"{x:g} min"


def _day_lines(d: dict[str, Any]) -> list[str]:
    """The day's measures (H2) as lines: each criterion, its numbers and what they say."""
    f, k, b, mo, w = d["first_sketch"], d["sketches"], d["building"], d["morning"], d["went_wrong"]
    return ["", "The day, the morning and the night (H2)",
            f"  a goal's first sketch within {SKETCH_WITHIN_MIN} min of the goal: {f['within']} of {f['goals']} ({_pct(f['within_share'])}), median {_mins(f['median_minutes'])}: {_says(f['holds'])}",
            f"  sketches picked, not skipped: {k['picked']} of {k['answered']} answered ({_pct(k['picked_share'])}); skipped {k['skipped']}, not made {k['not_made']}, asked again three times on {k['again_three_times']} goals: {_says(k['holds'])}",
            f"  goals started with Work at night on: {b['started']}, of them in the night's window {b['at_night']} ({_pct(b['night_share'])}), built now {b['built_now']}, otherwise {b['other']}: {_says(b['holds'])}",
            f"  Build it now on {b['built_now']} of {b['held']} goals the night held ({_pct(b['built_now_share'])})",
            f"  from the morning's card to the first mark under {MARK_WITHIN_MIN} min: {mo['under']} of {mo['first_marks']} ({_pct(mo['under_share'])}), median {_mins(mo['median_minutes'])}, the card lifted {mo['opened']} times: {_says(mo['holds'])}",
            f"  goals that went wrong (a task failed, a result sent back, fixed or dropped): at night {w['night']['wrong']} of {w['night']['goals']} ({_pct(w['night']['wrong_share'])}), by day "
            f"{w['day']['wrong']} of {w['day']['goals']} ({_pct(w['day']['wrong_share'])}): {_says(w['holds'])}"]
