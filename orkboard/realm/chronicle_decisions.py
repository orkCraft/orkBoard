"""The decisions of the past (docs/specs/134-release-keeps-the-chronicle.md A.2, decisions §238.3–§238.4): by their dates, what each changes and what changed it. No model, no face.

    chronicle_decisions.read(log, text=False)   # [{number, title, day, changes: [{n, point, title}], changed_by: [{number, title, day, points}], goal: ""}], by number
    chronicle_decisions.parties(state_dir)      # {number: [party]}: the parties that hold a slice of each decision, standing or replaced (spec 150 E1.4), in the order the slices were cut
    chronicle_decisions.why_line(text, limit)   # the first line of an entry's *Why* (spec 150 E1.2), at most `limit` characters; "" for none

`log` is the decisions file's text, or the folder of ADR files (`keeper._log_text()`). `day` is the entry's own; an entry with none takes the day of the last dated one before it (decisions are
written in order), the first ones the first dated after; "" when none has one. `changes` are read here: the `Changes:` line among the first four lines of the entry (a folder's record:
`decisions_log.changes_of`), the words `spec <n>` and `§<k>` dropped, each `N` or `N.k` → `{n, point}` (`point` 0 for the whole), an `n` not below the entry's own dropped, each once.
`changed_by` of an entry are the later entries whose `changes` name it. `goal` is for `chronicle.read` to set. `text`: the entry's body, for the search.
"""
from __future__ import annotations

import re
from pathlib import Path

from orkboard.realm import decisions_log, doc_formats, slices

_CHANGES = re.compile(r"^\s*Changes:\s*(.+?)\s*$", re.I)
_SPEC = re.compile(r"\bspec\s+\d+(?:\s*§[\d.]*\d)?", re.I)
_SECTION = re.compile(r"§[\d.]*\d")
_REF = re.compile(r"(\d+)(?:\.(\d+))?")


def refs(text: str, number: int) -> list[dict]:
    """The `{n, point}` a `Changes:` line's text names (see the module)."""
    out: list[dict] = []
    for m in _REF.finditer(_SECTION.sub(" ", _SPEC.sub(" ", text))):
        ref = {"n": int(m.group(1)), "point": int(m.group(2) or 0)}
        if ref["n"] < number and ref not in out:
            out.append(ref)
    return out


def _changes(rec: dict) -> list[dict]:
    if rec.get("format") == "log":
        for line in str(rec.get("body") or "").splitlines()[:4]:
            if m := _CHANGES.match(line):
                return refs(m.group(1), rec["number"])
        return []
    return refs(" ".join(str(n) for n in decisions_log.changes_of(rec)), rec["number"])


def _records(log: "str | Path") -> list[dict]:
    try:
        recs = doc_formats.records(log) if isinstance(log, Path) else doc_formats.parse_log(str(log or ""))
    except (OSError, ValueError):
        return []
    return sorted(recs, key=lambda r: r["number"])


def read(log: "str | Path", text: bool = False) -> list[dict]:
    """See the module."""
    recs = _records(log)
    days = [doc_formats.day_of(r.get("day") or r.get("date")) for r in recs]
    last = ""
    for n, d in enumerate(days):                         # an undated entry: the day of the one before it
        last = d or last
        days[n] = d or last
    first = next((d for d in days if d), "")
    rows = [{"number": r["number"], "title": r["title"], "day": days[n] or first, "changes": _changes(r), "changed_by": [], "goal": "",
             **({"text": str(r.get("body") or "")} if text else {})} for n, r in enumerate(recs)]
    by = {r["number"]: r for r in rows}
    for r in rows:
        for ref in r["changes"]:
            target = by.get(ref["n"])
            ref["title"] = target["title"] if target else ""
            if target is None:
                continue
            mine = target["changed_by"]
            if not mine or mine[-1]["number"] != r["number"]:
                mine.append({"number": r["number"], "title": r["title"], "day": r["day"], "points": []})
            if ref["point"] and ref["point"] not in mine[-1]["points"]:
                mine[-1]["points"].append(ref["point"])
    return rows


def why_line(text: object, limit: int = 140) -> str:
    """The first line of the *Why* of an entry's body: what follows `Why:` (or, when that is empty, the next line with words); an entry with no *Why* gives its first line that is no `Changes:` line."""
    lines = [x.strip() for x in str(text or "").splitlines()]
    at = next((n for n, x in enumerate(lines) if x.lower().startswith("why:")), None)
    if at is not None:
        own = lines[at][4:].strip()
        pick = own or next((x for x in lines[at + 1:] if x and not x.startswith("#")), "")
    else:
        pick = next((x for x in lines if x and not x.startswith("#") and not _CHANGES.match(x)), "")
    pick = " ".join(pick.split())
    return pick if len(pick) <= limit else pick[:max(0, limit - 1)].rstrip() + "…"


def parties(state_dir: Path) -> dict[int, list[str]]:
    """See the module: a decision is a party's when that party holds a slice of it (`slices.read`); a decision cut before the slices began, or touching no one, has none."""
    out: dict[int, list[str]] = {}
    for s in slices.read(state_dir)["slices"]:
        mine = out.setdefault(s["decision"], [])
        if s["party"] not in mine:
            mine.append(s["party"])
    return out
