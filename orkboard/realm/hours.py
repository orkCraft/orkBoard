"""The person's hours and their presence (docs/specs/138-the-day-read-from-the-resets.md B.1–B.2, spec 139 C.1; decisions §245.5, §246.4): the days and hours the
person is at the computer, in the machine's local time, and from them whether they are *Here* or *Away* now. Pure: no face, no model, no clock of its own.

    in_hours(settings, now)            # True inside one of the settings' `hours`; False outside them and with none set
    next_edge(settings, now)           # the next moment the hours begin or end (local, naive), None with none set
    next_start(settings, now)          # the next moment the hours begin (now, when inside them)
    presence(settings, now)            # {here: bool, until: iso | "", held: bool}: the door
    hold_for(settings, here, now)      # the `presence` setting a press leaves: {here, until}, or None when the press only agrees with the hours

`hours` is `[{days: [0..6], from: "19:00", to: "23:00"}]`, a day 0 = Monday (Python's `weekday()`); a span whose `to` is not after its `from` runs over midnight
into the next day (`from` = `to` is the whole day: *Sat–Sun all day* is `00:00`–`00:00`). Spans that touch are one (no edge at midnight between Saturday and
Sunday). **A press holds the other state until the hours' next edge** (`presence.set`): the setting `presence` = `{here, until}` says it and ends by itself;
with no hours the door is the person's alone, *Here* at first, and a press has no end.
"""
from __future__ import annotations

import datetime as dt
import re

TIME = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")
SPAN_DAYS = 9                                            # how far ahead the spans are laid: a week and the nights across its ends
ISO = "%Y-%m-%dT%H:%M"


def clean_hours(raw: object) -> list[dict]:
    """The rows as stored: each with its days (0–6, each once, in order), its `from` and `to` as HH:MM; a broken row is dropped; at most 14 rows."""
    out: list[dict] = []
    for r in raw if isinstance(raw, list) else []:
        if not isinstance(r, dict) or not isinstance(r.get("from"), str) or not isinstance(r.get("to"), str):
            continue
        a, b = r["from"].strip(), r["to"].strip()
        got = r.get("days")
        days = sorted({d for d in got if isinstance(d, int) and not isinstance(d, bool) and 0 <= d <= 6}) if isinstance(got, list) else []
        if days and TIME.match(a) and TIME.match(b):
            out.append({"days": days, "from": a, "to": b})
    return out[:14]


def clean_hold(raw: object) -> dict | None:
    """`{here, until}` as stored (`until` an ISO local time or ""), else None."""
    if isinstance(raw, dict) and isinstance(raw.get("here"), bool) and isinstance(raw.get("until", ""), str):
        until = str(raw.get("until") or "")
        return {"here": raw["here"], "until": until if re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d", until) else ""}
    return None


def _local(now: dt.datetime) -> dt.datetime:
    return now.astimezone().replace(tzinfo=None) if now.tzinfo else now


def _minutes(text: str) -> int:
    hh, mm = text.split(":")
    return int(hh) * 60 + int(mm)


def spans(settings: dict | None, now: dt.datetime) -> list[tuple[dt.datetime, dt.datetime]]:
    """The hours laid on the calendar from the day before `now` for SPAN_DAYS days, sorted, touching spans joined; [] with no hours."""
    rows = clean_hours((settings or {}).get("hours"))
    if not rows:
        return []
    now = _local(now)
    first = now.replace(hour=0, minute=0, second=0, microsecond=0) - dt.timedelta(days=1)
    found: list[tuple[dt.datetime, dt.datetime]] = []
    for n in range(SPAN_DAYS + 1):
        day = first + dt.timedelta(days=n)
        for r in rows:
            if day.weekday() not in r["days"]:
                continue
            a, b = _minutes(r["from"]), _minutes(r["to"])
            end = b if b > a else b + 24 * 60                     # not after its start: over midnight (equal: the whole day)
            found.append((day + dt.timedelta(minutes=a), day + dt.timedelta(minutes=end)))
    found.sort()
    joined: list[tuple[dt.datetime, dt.datetime]] = []
    for a, b in found:
        if joined and a <= joined[-1][1]:
            joined[-1] = (joined[-1][0], max(joined[-1][1], b))
        else:
            joined.append((a, b))
    return joined


def in_hours(settings: dict | None, now: dt.datetime | None = None) -> bool:
    now = _local(now or dt.datetime.now())
    return any(a <= now < b for a, b in spans(settings, now))


def next_edge(settings: dict | None, now: dt.datetime | None = None) -> dt.datetime | None:
    """The next moment after `now` the hours begin or end; None with no hours (or none within the days laid)."""
    now = _local(now or dt.datetime.now())
    edges = [t for a, b in spans(settings, now) for t in (a, b) if t > now]
    return min(edges) if edges else None


def next_start(settings: dict | None, now: dt.datetime | None = None) -> dt.datetime | None:
    """When the person is next at the computer: `now` inside the hours, else the next span's start; None with no hours."""
    now = _local(now or dt.datetime.now())
    if in_hours(settings, now):
        return now
    starts = [a for a, _b in spans(settings, now) if a > now]
    return min(starts) if starts else None


def hold_for(settings: dict | None, here: bool, now: dt.datetime | None = None) -> dict | None:
    """What a press on the door leaves (`presence.set {here}`): the other state held until the hours' next edge, or, with no hours, the state itself with no end.
    None when the hours already say it (the press only lifts a hold)."""
    now = _local(now or dt.datetime.now())
    if not clean_hours((settings or {}).get("hours")):
        return {"here": bool(here), "until": ""}
    if bool(here) == in_hours(settings, now):
        return None
    edge = next_edge(settings, now)
    return {"here": bool(here), "until": edge.strftime(ISO) if edge else ""}


def presence(settings: dict | None, now: dt.datetime | None = None) -> dict:
    """`{here, until, held}` (spec 139 C.1): with hours, *Here* inside them and *Away* outside, `until` the next edge; a hold (`presence` setting) that has not ended says
    the other, `held` true, `until` its end. With none, the hold is the person's alone (*Here* with none), no end, never `held`."""
    now = _local(now or dt.datetime.now())
    hold = clean_hold((settings or {}).get("presence"))
    if not clean_hours((settings or {}).get("hours")):
        return {"here": hold["here"] if hold else True, "until": "", "held": False}
    if hold is not None and hold["until"] and now < dt.datetime.strptime(hold["until"], ISO) and hold["here"] != in_hours(settings, now):
        return {"here": hold["here"], "until": hold["until"], "held": True}
    edge = next_edge(settings, now)
    return {"here": in_hours(settings, now), "until": edge.strftime(ISO) if edge else "", "held": False}


def away(settings: dict | None, now: dt.datetime | None = None) -> bool:
    return not presence(settings, now)["here"]
