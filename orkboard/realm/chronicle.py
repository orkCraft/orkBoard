"""Release keeps the chronicle (docs/specs/134-release-keeps-the-chronicle.md A.3–A.5, decisions §238): the past past the portal, read by code from what is kept. No model, no face, nothing written.

    chronicle.goals(state_dir, pages)                       # [{idea, title, party, element, hue, at, day, commit, decision}]: the goals through the portal, by `at`
    chronicle.read(state_dir, pages, repo, log, text=False) # {kind, chapters: [{id, kind, name, day, goals, decisions}] newest first, unreleased: {goals, decisions} | None, decisions: {number: row}}
    chronicle.earlier(state_dir, pages, repo)               # {kind, name, day} | None: the last version (or week) for Release's one line
    chronicle.goal(state_dir, pages, repo, log, slug)       # a goal as it was: its spec, its decision, what changed what it rests on, its living specs (ValueError: not in the chronicle)
    chronicle.decision(state_dir, pages, log, n)            # {number, title, day, entry, changes, changed_by, goal} | None

A goal is **in the chronicle** when its page is on the Board and it has a flag (`idea_flag`: the gate took it into main, or it was done where there is no gate: *played to the end*), and it is not
a release goal (a release is a version). An item's day (a goal's flag, a decision's) belongs to the first version whose day is not before it; after the last version it is `unreleased`, the
next chapter, not out yet. With no version, the chapters are the weeks (`chronicle_versions.week_of`), a chapter only for a week that has something. A chapter's `decisions` are those written in
its span that no goal of the chronicle carries (a decision of no goal is a row of its own); a carried one is `goal: <slug>` and stands under its goal. Keys and data, never words.
"""
from __future__ import annotations

import bisect
from pathlib import Path

from orkboard.realm import chronicle_decisions, chronicle_versions, decisions_log, idea_element, idea_flag, ideas, living_specs, releases, spec_sections

NOT_IN = "That goal is not in the chronicle"


def goals(state_dir: Path, pages: Path) -> list[dict]:
    """See the module."""
    out = []
    for i in ideas.ideas(pages):
        slug = i["slug"]
        flag = idea_flag.flag_of(state_dir, slug)
        if flag is None or releases.read(state_dir, slug) is not None:
            continue
        at = str(flag["at"])
        day = chronicle_versions._day(at)
        if not day:
            continue
        number = ((spec_sections.record(state_dir, slug).get("decision") or {}).get("number"))
        out.append({"idea": slug, "title": i["title"], "party": i["track"], "element": idea_element.of(state_dir, slug), "hue": idea_element.hue_of(state_dir, slug),
                    "at": at, "day": day, "commit": str(flag.get("commit") or ""),
                    "decision": number if isinstance(number, int) and not isinstance(number, bool) and number > 0 else 0})
    return sorted(out, key=lambda g: (g["at"], g["idea"]))


def _public(row: dict) -> dict:
    return {k: v for k, v in row.items() if k != "text"}


def _row(row: dict, text: bool) -> dict:
    return row if text else _public(row)


def read(state_dir: Path, pages: Path, repo: Path, log: "str | Path", text: bool = False) -> dict:
    """See the module."""
    found = chronicle_versions.read(repo)
    rows = chronicle_decisions.read(log, text)
    mine = goals(state_dir, pages)
    carried: dict[int, str] = {}
    for g in mine:
        if g["decision"]:
            carried.setdefault(g["decision"], g["idea"])
    for r in rows:
        r["goal"] = carried.get(r["number"], "")
    weeks = found["kind"] == "week"
    versions = found["versions"]
    days = [v["day"] for v in versions]
    chapters: dict[str, dict] = {v["id"]: {"id": v["id"], "kind": found["kind"], "name": v["name"], "day": v["day"], "goals": [], "decisions": []} for v in versions}
    unreleased: dict | None = None if weeks else {"goals": [], "decisions": []}

    def chapter(day: str) -> dict | None:
        if weeks:
            monday = chronicle_versions.week_of(day)
            return chapters.setdefault(f"w:{monday}", {"id": f"w:{monday}", "kind": "week", "name": "", "day": monday, "goals": [], "decisions": []}) if monday else None
        at = bisect.bisect_left(days, day)
        return chapters[versions[at]["id"]] if at < len(versions) else unreleased

    for g in sorted(mine, key=lambda g: (g["at"], g["idea"]), reverse=True):
        if (c := chapter(g["day"])) is not None:
            c["goals"].append(g)
    for r in sorted(rows, key=lambda r: -r["number"]):
        if not r["goal"] and r["day"] and (c := chapter(r["day"])) is not None:
            c["decisions"].append(_row(r, text))
    out = sorted(chapters.values(), key=lambda c: c["day"], reverse=True)
    return {"kind": found["kind"], "chapters": out, "unreleased": unreleased, "decisions": {r["number"]: _row(r, text) for r in rows}}


def earlier(state_dir: Path, pages: Path, repo: Path) -> dict | None:
    """See the module: the versions are read, and the flags only where there is no version."""
    found = chronicle_versions.read(repo)
    if found["versions"]:
        last = found["versions"][-1]
        return {"kind": found["kind"], "name": last["name"], "day": last["day"]}
    days = [g["day"] for g in goals(state_dir, pages)]
    return {"kind": "week", "name": "", "day": chronicle_versions.week_of(max(days))} if days else None


def _entry(log: "str | Path", row: dict) -> dict:
    return {**{k: row[k] for k in ("number", "title", "day", "changes", "changed_by")}, "entry": decisions_log.entry(log, row["number"])}


def goal(state_dir: Path, pages: Path, repo: Path, log: "str | Path", slug: str) -> dict:
    """See the module."""
    mine = next((g for g in goals(state_dir, pages) if g["idea"] == slug), None)
    page = ideas.idea_page(pages, slug) if mine is not None else None
    if mine is None or page is None:
        raise ValueError(NOT_IN)
    tracks = [{"slug": t["slug"], "title": t["title"]} for t in ideas.tracks(pages, make=False)]
    got = spec_sections.read(page, tracks, mine["party"])
    by = {r["number"]: r for r in chronicle_decisions.read(log)}
    row = by.get(mine["decision"])
    rests = ({row["number"]} | {c["n"] for c in row["changes"]}) if row else set()
    later: dict[int, dict] = {}
    for n in rests:
        for c in (by[n]["changed_by"] if n in by else []):
            if c["number"] > mine["decision"]:
                prev = later.setdefault(c["number"], {**c, "points": []})
                prev["points"] = sorted({*prev["points"], *c["points"]})
    board = Path(pages)
    how = []
    for cap in living_specs.list_(board):
        spec = living_specs.read(board, cap["capability"])
        if spec is not None and slug in (spec.get("goals") or []):
            how.append({"capability": cap["capability"], "title": cap["title"]})
    return {**{k: mine[k] for k in ("idea", "title", "party", "at", "day", "commit", "element", "hue")},
            "spec": {"asked": got["common"].get("Asked", ""), "gist": got["common"].get("Gist", ""),
                     "sections": [{"party": s.party, "title": s.title, "parts": dict(s.parts)} for s in got["sections"]]},
            "decision": _entry(log, row) if row else None, "changed_by": [later[n] for n in sorted(later)], "how_now": how}


def decision(state_dir: Path, pages: Path, log: "str | Path", n: int) -> dict | None:
    """See the module."""
    row = next((r for r in chronicle_decisions.read(log) if r["number"] == n), None)
    if row is None:
        return None
    return {**_entry(log, row), "goal": next((g["idea"] for g in goals(state_dir, pages) if g["decision"] == n), "")}
