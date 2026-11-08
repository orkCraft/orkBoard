"""Release keeps the chronicle (docs/specs/134-release-keeps-the-chronicle.md A.3–A.5, decisions §238): the past past the portal, read by code from what is kept. No model, no face, nothing written.

    chronicle.goals(state_dir, pages, party="")             # [{idea, title, party, element, hue, at, day, commit, decision}]: the goals through the portal, by `at`
    chronicle.read(state_dir, pages, repo, log, text=False, party="") # {kind, chapters: [{id, kind, name, day, goals, decisions}] newest first, unreleased: {goals, decisions} | None, decisions: {number: row}}
    chronicle.earlier(state_dir, pages, repo, party="")     # {kind, name, day} | None: the last version (or week) for Release's one line
    chronicle.last(state_dir, pages, repo, log, party="", n=3) # the party's last `n` decisions, newest first: [{number, title, element, kind: "decision", parties, version, at}] (spec 150 E1.4)
    chronicle.goal(state_dir, pages, repo, log, slug)       # a goal as it was: its spec, its decision, what changed what it rests on, its living specs (ValueError: not in the chronicle)
    chronicle.decision(state_dir, pages, log, n)            # {number, title, day, entry, changes, changed_by, goal} | None

A goal is **in the chronicle** when its page is on the Board and it has a flag (`idea_flag`: the gate took it into main, or it was done where there is no gate: *played to the end*), and it is not
a release goal (a release is a version). An item's day (a goal's flag, a decision's) belongs to the first version whose day is not before it; after the last version it is `unreleased`, the
next chapter, not out yet. With no version, the chapters are the weeks (`chronicle_versions.week_of`), a chapter only for a week that has something. A chapter's `decisions` are those written in
its span that no goal of the chronicle carries (a decision of no goal is a row of its own); a carried one is `goal: <slug>` and stands under its goal. Keys and data, never words.

**By party** (spec 150 E1.4, decisions §254.7): with a `party` the past is the party's: a goal is its when its route held the party (`held`: the party the goal lies in and the parties of its route), a decision when
that party holds a slice of it (`chronicle_decisions.parties`, standing or replaced). A decision a goal of the party carries stands under that goal; one carried by a goal that is not the party's stands
as a row of its own. No party, the whole project.

**From the pages** (spec 162 D, decisions §277.3): a page's `route:` holds its parties while the state holds no route (the state's wins); a goal carries its spec record's decision, else the newest of its page's
`decisions:` that the log holds. A decision of no goal is on no party's tab unless a party's leader holds a slice of it; it stays whole in the read with no party.
"""
from __future__ import annotations

import bisect
import re
from pathlib import Path

from orkboard.realm import chronicle_decisions, chronicle_versions, decisions_log, idea_element, idea_flag, ideas, living_specs, releases, spec_sections

NOT_IN = "That goal is not in the chronicle"
LAST_MAX = 10                  # the most decisions `last` gives


def held(state_dir: Path, slug: str, home: str, page: object = None) -> set[str]:
    """The parties a goal's route held: the one it lies in and each of its route's. The route is the state's; while the state holds none, the page's own `route:` (spec 162 D; decisions §277.3): the
    state's wins where both are."""
    route = ideas.state(state_dir, slug).get("route") or ()
    if not route and page is not None:
        route = [x.strip() for x in str(page.get("route", "") or "").split(",")]
    mine = {r.get("party") if isinstance(r, dict) else r for r in route}
    return {p for p in (*mine, home) if isinstance(p, str) and p}


def _carried(state_dir: Path, slug: str, page: object, known: "set[int] | None") -> int:
    """The decision a goal carries: the spec record's, else the newest of its page's `decisions:` that the log holds (`known`; None: any named)."""
    number = (spec_sections.record(state_dir, slug).get("decision") or {}).get("number")
    if isinstance(number, int) and not isinstance(number, bool) and number > 0:
        return number
    named = {int(n) for n in re.findall(r"\d+", str(page.get("decisions", "") or ""))} if page is not None else set()
    named = {n for n in named if n > 0 and (known is None or n in known)}
    return max(named, default=0)


def _all(state_dir: Path, pages: Path, rows: "list[dict] | None" = None) -> list[tuple[dict, set[str]]]:
    """Each goal through the portal with the parties its route held, from one read of the pages; `rows` the log's (`chronicle_decisions.read`), for the decisions a page names."""
    known = {r["number"] for r in rows} if rows is not None else None
    listed, by_slug = ideas.ideas_and_pages(pages)
    out = []
    for i in listed:
        slug = i["slug"]
        flag = idea_flag.flag_of(state_dir, slug)
        if flag is None or releases.read(state_dir, slug) is not None:
            continue
        at = str(flag["at"])
        day = chronicle_versions._day(at)
        if not day:
            continue
        page = by_slug.get(slug)
        out.append(({"idea": slug, "title": i["title"], "party": i["track"], "element": idea_element.of(state_dir, slug), "hue": idea_element.hue_of(state_dir, slug),
                     "at": at, "day": day, "commit": str(flag.get("commit") or ""), "decision": _carried(state_dir, slug, page, known)},
                    held(state_dir, slug, i["track"], page)))
    return out


def goals(state_dir: Path, pages: Path, party: str = "", rows: "list[dict] | None" = None) -> list[dict]:
    """See the module."""
    out = [g for g, mine in _all(state_dir, pages, rows) if not party or party in mine]
    return sorted(out, key=lambda g: (g["at"], g["idea"]))


def _public(row: dict) -> dict:
    return {k: v for k, v in row.items() if k != "text"}


def _row(row: dict, text: bool) -> dict:
    return row if text else _public(row)


def read(state_dir: Path, pages: Path, repo: Path, log: "str | Path", text: bool = False, party: str = "") -> dict:
    """See the module."""
    found = chronicle_versions.read(repo)
    rows = chronicle_decisions.read(log, text)
    every = _all(state_dir, pages, rows)
    everyone = [g for g, _ in every]
    mine = [g for g, h in every if not party or party in h]
    carried: dict[int, str] = {}
    for g in everyone:
        if g["decision"]:
            carried.setdefault(g["decision"], g["idea"])
    mine_slugs = {g["idea"] for g in mine}
    for r in rows:
        r["goal"] = carried.get(r["number"], "")
    kept = chronicle_decisions.parties(state_dir) if party else {}
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
        if party and party not in kept.get(r["number"], ()) and r["goal"] not in mine_slugs:
            continue
        if (not r["goal"] or (party and r["goal"] not in mine_slugs)) and r["day"] and (c := chapter(r["day"])) is not None:
            c["decisions"].append(_row(r, text))
    out = sorted(chapters.values(), key=lambda c: c["day"], reverse=True)
    return {"kind": found["kind"], "chapters": out, "unreleased": unreleased, "decisions": {r["number"]: _row(r, text) for r in rows}}


def earlier(state_dir: Path, pages: Path, repo: Path, party: str = "") -> dict | None:
    """See the module: the versions are read, and the flags only where there is no version."""
    found = chronicle_versions.read(repo)
    if found["versions"]:
        last = found["versions"][-1]
        return {"kind": found["kind"], "name": last["name"], "day": last["day"]}
    days = [g["day"] for g in goals(state_dir, pages, party)]
    return {"kind": "week", "name": "", "day": chronicle_versions.week_of(max(days))} if days else None


def _entry(log: "str | Path", row: dict) -> dict:
    return {**{k: row[k] for k in ("number", "title", "day", "changes", "changed_by")}, "entry": decisions_log.entry(log, row["number"])}


def goal(state_dir: Path, pages: Path, repo: Path, log: "str | Path", slug: str) -> dict:
    """See the module."""
    mine = next((g for g in goals(state_dir, pages, rows=chronicle_decisions.read(log)) if g["idea"] == slug), None)
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
    return {**_entry(log, row), "goal": next((g["idea"] for g in goals(state_dir, pages, rows=chronicle_decisions.read(log)) if g["decision"] == n), "")}


def last(state_dir: Path, pages: Path, repo: Path, log: "str | Path", party: str = "", n: int = 3) -> list[dict]:
    """See the module: by code, no call. `element` is its goal's rune ("" for a decision of no goal), `version` the version whose span the decision is in ("" when it is not out yet, or the past has only weeks),
    `at` the moment the goal's decision was confirmed, else the entry's day."""
    n = n if isinstance(n, int) and not isinstance(n, bool) and 1 <= n <= LAST_MAX else 3
    rows = chronicle_decisions.read(log)
    kept = chronicle_decisions.parties(state_dir)
    carrier: dict[int, str] = {}
    mine_carried: set[int] = set()
    for g, h in _all(state_dir, pages, rows):                      # the goals' carried decisions (spec 162 D), as `read` places them
        if g["decision"]:
            carrier.setdefault(g["decision"], g["idea"])
            if party and party in h:
                mine_carried.add(g["decision"])
    if party:
        rows = [r for r in rows if party in kept.get(r["number"], ()) or r["number"] in mine_carried]
    rows = sorted(rows, key=lambda r: -r["number"])[:n]
    found = chronicle_versions.read(repo)
    versions = found["versions"] if found["kind"] != "week" else []
    days = [v["day"] for v in versions]
    by_number: dict[int, tuple[str, dict]] = {}
    for i in ideas.ideas(pages):
        d = spec_sections.record(state_dir, i["slug"]).get("decision")
        if isinstance(d, dict) and isinstance(d.get("number"), int) and d.get("confirmed"):
            by_number.setdefault(d["number"], (i["slug"], d))
    out = []
    for r in rows:
        slug, d = by_number.get(r["number"], (carrier.get(r["number"], ""), {}))
        at = bisect.bisect_left(days, r["day"]) if r["day"] else len(days)
        out.append({"number": r["number"], "title": r["title"], "element": idea_element.of(state_dir, slug) if slug else "", "kind": "decision",
                    "parties": [*kept.get(r["number"], []), *([party] if party and party not in kept.get(r["number"], []) else [])], "version": versions[at]["name"] if at < len(versions) else "", "at": str(d.get("confirmed_at") or r["day"] or "")})
    return out
