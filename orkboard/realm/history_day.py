"""The day of a page laid done from history (docs/specs/162-the-past-from-history-on-the-parties-tables.md A; decisions §277.2): the day its decisions say, not the day it was laid. Pure code: no git, no model, no face.

    history_day.day(page, spec_text, log_rows, laid)   # "YYYY-MM-DD": the day of the newest of the page's `decisions:` the log holds, else of the highest §N the spec names that the log holds, else `laid`
    history_day.cited(spec_text)                       # the numbers a text names as §N (§N.k counts as §N): a set

`page` is a `Page` (or anything with `get(key, default)`) whose `decisions:` is a list of numbers (`270, 274`); `spec_text` the page's spec file ("" for none); `log_rows` the decisions log's rows
(`chronicle_decisions.read`: `number`, `day`); `laid` the day the host gives (the commit that laid the page). A number the log does not hold, or holds with no day, is never counted. Decisions
are written in order, so the newest is the highest number the log holds; a spec's cites are only cited, never decided, so they date a page only when the page names none of its own.
"""
from __future__ import annotations

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
