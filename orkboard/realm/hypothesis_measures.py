"""A hypothesis's measures (docs/specs/133-a-hypothesis-its-two-conditions-its-test-its-file.md B; decisions §235.2, §235.3): a test that is a thing counted, where it is read from, its bar in each condition and the
date it is read on. No model, no face. (`realm/measures.py` is something else: how the arguing turned out, read from the event log.)

    hypothesis_measures.clean(raw)             # strictly → [measure] (four at most); ValueError in plain words for more than four, a measure with no words or no bar, an op or a number that is none
    hypothesis_measures.lenient(raw)           # …a record read: what is not of the shape is dropped
    hypothesis_measures.date_of(started, span_days)   # the day the measure is read on: `started` (YYYY-MM-DD) and the span
    hypothesis_measures.reached(measure, today)       # its date is today or past
    hypothesis_measures.met(item)              # {"holds": True | False | None, "refuted": [the names of the ways met]}: the conditions the values meet, by code
    hypothesis_measures.shown(item, today)     # the item as a face may see it: a measure's `value` is hidden (None) until its date is reached (no number is shown counting before its date)
    hypothesis_measures.day(value)             # "YYYY-MM-DD" or "" for what is no day

A measure is `{id, what, from, by, bars: {holds: {op, n, unit} | None, refuted: [{way, op, n, unit}]}, span_days, date, value: None | {n, by, at, from}}`. `what` and `from` are a line of 120 characters; `by` the slug of the
party whose map holds the source ("" the person's to type); `op` one of `OPS`, `n` a number, `unit` 24 characters; `span_days` 1 to 365 (28 is *four weeks*). A condition with no bar is not judged by that measure; a
condition is **met** when at least one measure has a bar for it, every such measure has a value and every such value meets its bar.
"""
from __future__ import annotations

import datetime as dt
import re

OPS = (">=", ">", "<=", "<", "=")
MAX_MEASURES = 4
LINE, UNIT, SPAN_MAX, SPAN_DEFAULT = 120, 24, 365, 28
_ID = re.compile(r"[a-z0-9][a-z0-9-]{0,19}")
_DAY = re.compile(r"\d{4}-\d\d-\d\d")


def _words(value: object, n: int) -> str:
    return " ".join(value.split())[:n].rstrip() if isinstance(value, str) else ""


def _num(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        return None
    try:
        n = float(value)
    except ValueError:
        return None
    return n if n == n and abs(n) != float("inf") else None


def day(value: object) -> str:
    """`value` when it is a real day `YYYY-MM-DD` (a time's first ten characters too), else ""."""
    text = str(value or "")[:10]
    try:
        return dt.date.fromisoformat(text).isoformat() if _DAY.fullmatch(text) else ""
    except ValueError:
        return ""


def date_of(started: str, span_days: int) -> str:
    """The day `span_days` after `started` (today when `started` is no day)."""
    start = dt.date.fromisoformat(day(started)) if day(started) else dt.date.today()
    return (start + dt.timedelta(days=int(span_days))).isoformat()


def reached(measure: dict, today: str) -> bool:
    return bool(measure.get("date")) and measure["date"] <= today


def _bar(raw: object) -> dict | None:
    if not isinstance(raw, dict):
        return None
    n = _num(raw.get("n"))
    return {"op": raw["op"], "n": n, "unit": _words(raw.get("unit"), UNIT)} if raw.get("op") in OPS and n is not None else None


def _value(raw: object) -> dict | None:
    n = _num(raw.get("n")) if isinstance(raw, dict) else None
    return {"n": n, "by": _words(raw.get("by"), 40), "at": str(raw.get("at") or ""), "from": _words(raw.get("from"), LINE)} if n is not None else None


def _one(raw: object, strict: bool) -> dict | None:
    if not isinstance(raw, dict):
        if strict:
            raise ValueError("A measure says what is counted and its bar")
        return None
    what = _words(raw.get("what"), LINE)
    bars = raw.get("bars") if isinstance(raw.get("bars"), dict) else {}
    holds = _bar(bars.get("holds"))
    ways = [{**b, "way": _words(w.get("way"), 40)} for w in (bars.get("refuted") if isinstance(bars.get("refuted"), list) else []) if (b := _bar(w))]
    if strict and (bars.get("holds") not in (None, "") and holds is None or any(_bar(w) is None for w in bars.get("refuted") or [])):
        raise ValueError(f"A bar is one of {', '.join(OPS)} and a number")
    if strict and not (what and (holds or ways)):
        raise ValueError("A measure says what is counted and its bar: a number it holds at or a way it is refuted at")
    if not (what and (holds or ways)):
        return None
    span = raw.get("span_days")
    span = span if isinstance(span, int) and not isinstance(span, bool) and 1 <= span <= SPAN_MAX else SPAN_DEFAULT
    mid = raw.get("id") if isinstance(raw.get("id"), str) and _ID.fullmatch(raw["id"]) else ""
    return {"id": mid, "what": what, "from": _words(raw.get("from"), LINE), "by": raw["by"].strip() if isinstance(raw.get("by"), str) and re.fullmatch(r"[a-z0-9-]{1,80}", raw["by"].strip()) else "",
            "bars": {"holds": holds, "refuted": ways}, "span_days": span, "date": day(raw.get("date")), "value": _value(raw.get("value"))}


def _ids(items: list[dict]) -> list[dict]:
    seen: set[str] = set()
    for m in items:
        if not m["id"] or m["id"] in seen:
            n = 1
            while f"m{n}" in seen or any(f"m{n}" == o["id"] for o in items if o is not m and o["id"]):
                n += 1
            m["id"] = f"m{n}"
        seen.add(m["id"])
    return items


def clean(raw: object) -> list[dict]:
    """The measures a person or code gives, strictly (see the module); ids given where missing."""
    if raw in (None, ""):
        return []
    if not isinstance(raw, (list, tuple)):
        raise ValueError("Measures are a list")
    if len(raw) > MAX_MEASURES:
        raise ValueError(f"A hypothesis has {MAX_MEASURES} measures at most")
    return _ids([_one(r, True) for r in raw])


def lenient(raw: object) -> list[dict]:
    return _ids([m for r in (raw if isinstance(raw, list) else []) if (m := _one(r, False))][:MAX_MEASURES])


def _meets(n: float, bar: dict) -> bool:
    return {">=": n >= bar["n"], ">": n > bar["n"], "<=": n <= bar["n"], "<": n < bar["n"], "=": n == bar["n"]}[bar["op"]]


def met(item: dict) -> dict:
    """The conditions the values meet (see the module): `holds` None while no value has come for it, False when a value misses its bar; `refuted` the names of the ways met."""
    measures = item.get("measures") or []

    def judged(bars: list[dict]) -> bool | None:
        if not bars:
            return None
        values = [b.get("value") for b in bars]
        if any(v is None for v in values):
            return None
        return all(_meets(v["n"], b["bar"]) for v, b in zip(values, bars))

    holds = judged([{"bar": m["bars"]["holds"], "value": m["value"]} for m in measures if m["bars"]["holds"]])
    names = list(dict.fromkeys(b["way"] for m in measures for b in m["bars"]["refuted"]))
    ways = [w for w in names if judged([{"bar": b, "value": m["value"]} for m in measures for b in m["bars"]["refuted"] if b["way"] == w]) is True]
    return {"holds": holds, "refuted": ways}


def shown(item: dict, today: str) -> dict:
    """The item with every measure's `value` hidden until its date is reached (the number is kept all the same)."""
    return {**item, "measures": [m if reached(m, today) else {**m, "value": None} for m in item.get("measures") or []]}


def overlay(from_file: list[dict], kept: list[dict], started: str) -> list[dict]:
    """The measures a bound file says (spec 133 C.2: `hypotheses_file.parse`), each with what the file has no place for from the record's copy of the same words: its id and its value. A measure read as a
    span has its date `started` + the span (the record's own date where `started` is not known); one read as a day has the span that day lies from `started`. Four at most, ids unique."""
    key = lambda m: " ".join(str(m.get("what") or "").lower().split())          # noqa: E731
    by_what: dict[str, dict] = {}
    for r in kept:
        by_what.setdefault(key(r), r)
    out: list[dict] = []
    used: set[str] = set()
    for f in from_file[:MAX_MEASURES]:
        r = by_what.pop(key(f), None)
        m = {**f, "id": r["id"] if r and r["id"] not in used else "", "value": r["value"] if r else None}
        if m["id"]:
            used.add(m["id"])
        if m["date"] and started:
            m["span_days"] = min(SPAN_MAX, max(1, (dt.date.fromisoformat(m["date"]) - dt.date.fromisoformat(started)).days))
        elif not m["date"]:
            m["date"] = date_of(started, m["span_days"]) if started else (r["date"] if r else "")
        out.append(m)
    return _ids(out)
