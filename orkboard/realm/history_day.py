"""The day of a page laid done from history (docs/specs/162-the-past-from-history-on-the-parties-tables.md A; decisions §277.2): the day its decisions say, not the day it was laid. Pure code: no git, no model, no face.

    history_day.day(page, spec_text, log_rows, laid)   # "YYYY-MM-DD": the day of the newest of the page's `decisions:` the log holds, else of the highest §N the spec names that the log holds, else `laid`
    history_day.cited(spec_text)                       # the numbers a text names as §N (§N.k counts as §N): a set
    history_day.dates(confirmed_at, decision_day, finished, flag)   # {"agreed", "done", "main"}: the three days the history book dates a goal by (spec 168 G3, decisions §283.16.14)

`page` is a `Page` (or anything with `get(key, default)`) whose `decisions:` is a list of numbers (`270, 274`); `spec_text` the page's spec file ("" for none); `log_rows` the decisions log's rows
(`chronicle_decisions.read`: `number`, `day`); `laid` the day the host gives (the commit that laid the page). A number the log does not hold, or holds with no day, is never counted. Decisions
are written in order, so the newest is the highest number the log holds; a spec's cites are only cited, never decided, so they date a page only when the page names none of its own.
"""
from __future__ import annotations

import datetime as dt
import re

_NUMBER = re.compile(r"\d+")
_SECTION = re.compile(r"§\s*(\d+)")


def cited(spec_text: object) -> set[int]:
    """See the module: `§261.9` is §261; a `§` with no number after it names none."""
    return {int(m.group(1)) for m in _SECTION.finditer(str(spec_text or ""))}


def _days(log_rows: object) -> dict[int, str]:
    return {int(r["number"]): str(r["day"]) for r in log_rows or () if r.get("day") and r.get("number") is not None}


def day(page: object, spec_text: object, log_rows: object, laid: object) -> str:
    """See the module."""
    held = _days(log_rows)
    own = {int(n) for n in _NUMBER.findall(str(page.get("decisions", "") or ""))} & held.keys() if page is not None else set()
    pick = own or (cited(spec_text) & held.keys())
    return held[max(pick)] if pick else str(laid or "")


def _ymd(text: object) -> str:
    """The `YYYY-MM-DD` a stamp begins with, else "" (a stamp that is no day is no date)."""
    head = str(text or "").strip()[:10]
    try:
        return dt.date.fromisoformat(head).isoformat()
    except ValueError:
        return ""


def dates(confirmed_at: object, decision_day: object, finished: object, flag: object) -> dict[str, str]:
    """The three days a goal is dated by in the history book (spec 168 G3, decisions §283.16.14; §277's dates are kept), each `YYYY-MM-DD` or "" where the goal has none:

    - **agreed**: the day its decision was confirmed (`confirmed_at`); else the day of the decision it carries in the log (`decision_day`: the day a history page's decision says, §277.2);
    - **done**: the day its last task was merged (`finished`: the merged tasks' finish stamps, the newest); else, for a goal done where there is no gate (a flag `by: done`), its flag's day;
    - **in main**: its flag's day (the gate took it into main, or it was laid done from history).
    A goal missing one keeps the others; the book lays it in a row of its own for the one it lacks."""
    flag = flag if isinstance(flag, dict) else {}
    made = max((d for d in (_ymd(x) for x in (finished or ())) if d), default="")
    main = _ymd(flag.get("at"))
    return {"agreed": _ymd(confirmed_at) or _ymd(decision_day),
            "done": made or (main if flag.get("by") == "done" else ""),
            "main": main}
