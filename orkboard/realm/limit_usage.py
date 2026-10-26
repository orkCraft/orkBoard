"""What used an AI tool's limit, by party and member (docs/specs/91-the-owners-list.md §2, decisions §107). Code, no model, no face.

    limit_usage.split(reads, lines, start=None)      # reads and calls → {"rows", "outside", "tokens_only"}
    limit_usage.window_span("week")                  # a window's length (5h, week), None for one not known
    limit_usage.reads_of(events, provider, window)   # the `limits_read` events of one tool's window → [{"at", "left"}]
    limit_usage.calls_of(root, state_dir, tool)      # the project's `spend.jsonl` lines of a tool → (calls, party titles)

**The reads** are `limits_read` events (`realm/event_log.py`): a tool's tightest window and what was left of it, a fraction
of the whole. Two reads one after the other give what was used between them: `before.left - after.left`. A `left` that goes
up is the window reset, not use: only the reads since the last reset count, and a rise is never negative use.

**The calls** are the project's `spend.jsonl` lines of that tool, each with its party (the goal's party, or the party's own
ledger), its member (the line's `role`) and its tokens. What a pair of reads shows used is split over the calls between the
two in proportion to their tokens (a call with none counts one, when no call of the pair has any); what no call accounts for
(a pair that shows use and has no call, and the window's first stretch from its start to the first read, when the start is
known: the reset less the window's length) is **outside** Orkboard.

**Shares** are whole percents of the window, the largest remainders keeping their sum at the sum of the use (never above 100).
Fewer than two points to pair (no start known and fewer than two reads): `tokens_only`, the rows carry tokens and no share.
Every share is an estimate: the limit read before and after, split by the tokens of each call.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from orkboard.realm import event_log, ideas, idea_spend, library, roles

SPANS = {"5h": dt.timedelta(hours=5), "day": dt.timedelta(days=1), "week": dt.timedelta(days=7), "month": dt.timedelta(days=30)}
RESET = 0.005                    # a rise of the left by more than this is a reset (less is a reading's noise)
ORKMASTER, GONE = "orkmaster", "~gone"      # a party key: the night's proposals, a goal whose page was deleted
PARTY_GONE, PARTY_ORKMASTER = "Goals since removed", "Orkmaster"


def when(value: object) -> dt.datetime | None:
    """A time as aware: the logs' ISO text, a naive one (the ledgers') read as local time; None when it is not one."""
    if isinstance(value, dt.datetime):
        at = value
    else:
        try:
            at = dt.datetime.fromisoformat(str(value or ""))
        except ValueError:
            return None
    return at.astimezone() if at.tzinfo is None else at


def window_span(window: str) -> dt.timedelta | None:
    """A window's length from its name as the top bar says it ("5h", "week", "gemini · week"); None when not known."""
    return SPANS.get(str(window or "").rsplit("·", 1)[-1].strip())


def reads_of(events: list[dict], provider: str, window: str) -> list[dict]:
    """The tool's reads of that window, oldest first: `[{"at": datetime, "left": float}]`."""
    out = []
    for e in events:
        if e.get("event") != event_log.LIMITS_READ or e.get("provider") != provider or str(e.get("window") or "") != window:
            continue
        at, left = when(e.get("at")), e.get("left")
        if at is not None and isinstance(left, (int, float)) and not isinstance(left, bool):
            out.append({"at": at, "left": float(left)})
    return sorted(out, key=lambda r: r["at"])


def _round(parts: list[float], total: int) -> list[int]:
    """Whole numbers for `parts` that add up to `total`, the largest remainders taking the extra ones."""
    floors = [int(p) for p in parts]
    order = sorted(range(len(parts)), key=lambda i: parts[i] - floors[i], reverse=True)
    for i in order[:max(0, total - sum(floors))]:
        floors[i] += 1
    return floors


def _points(reads: list[dict], start: dt.datetime | None) -> list[dict]:
    """The reads since the last reset, with the window's start as a full read before them when it is known and nothing reset
    inside the window."""
    got = [r for r in reads if start is None or r["at"] >= start]
    cut = 0
    for i in range(1, len(got)):
        if got[i]["left"] - got[i - 1]["left"] > RESET:
            cut = i
    got = got[cut:]
    if start is not None and cut == 0 and (not got or got[0]["at"] > start):
        got = [{"at": start, "left": 1.0, "start": True}, *got]
    return got


def split(reads: list[dict], lines: list[dict], start: dt.datetime | None = None) -> dict:
    """`reads`: `reads_of` (the live read of the limit may be the last); `lines`: `[{"at": datetime, "party", "agent",
    "tokens"}]`; `start`: the window's start when known. → `{"rows": [{"party", "share", "tokens", "members": [{"agent",
    "share", "tokens"}]}], "outside": int, "tokens_only": bool}`, rows by share, then tokens. With `tokens_only` every
    share is None, `outside` 0 and the tokens are those of the calls since the window's start (all of `lines`, when none)."""
    points = _points(reads, start)
    if len(points) < 2:
        return {"rows": _rows(lines), "outside": 0, "tokens_only": True}
    by: dict[tuple[str, str], float] = {}           # (party, agent) → the percent of the window
    tokens: dict[tuple[str, str], int] = {}
    outside = 0.0
    for a, b in zip(points, points[1:]):
        used = max(0.0, a["left"] - b["left"]) * 100
        mine = [l for l in lines if a["at"] <= l["at"] < b["at"]]
        weight = sum(l["tokens"] for l in mine)
        for l in mine:
            tokens[(l["party"], l["agent"])] = tokens.get((l["party"], l["agent"]), 0) + l["tokens"]
        if not used:
            continue
        if not mine:
            outside += used
            continue
        for l in mine:
            key = (l["party"], l["agent"])
            by[key] = by.get(key, 0.0) + used * ((l["tokens"] / weight) if weight else 1 / len(mine))
    total = min(100, round(sum(by.values()) + outside))
    parties: dict[str, dict[str, float]] = {}
    for (party, agent), pct in by.items():
        parties.setdefault(party, {})[agent] = pct
    keys = list(parties)
    sums = [sum(parties[k].values()) for k in keys]
    whole = _round([*sums, outside], total)
    rows = []
    for k, share in zip(keys, whole):
        members = parties[k]
        shares = _round(list(members.values()), share)
        rows.append({"party": k, "share": share, "tokens": sum(tokens.get((k, a), 0) for a in members),
                     "members": sorted(({"agent": a, "share": s, "tokens": tokens.get((k, a), 0)} for a, s in zip(members, shares)),
                                       key=lambda m: (-m["share"], -m["tokens"], m["agent"]))})
    rows.sort(key=lambda r: (-r["share"], -r["tokens"], r["party"]))
    return {"rows": rows, "outside": whole[-1], "tokens_only": False}


def _rows(lines: list[dict]) -> list[dict]:
    """The rows of tokens only: a party's calls and each member's, by tokens."""
    parties: dict[str, dict[str, int]] = {}
    for l in lines:
        parties.setdefault(l["party"], {})
        parties[l["party"]][l["agent"]] = parties[l["party"]].get(l["agent"], 0) + l["tokens"]
    rows = [{"party": p, "share": None, "tokens": sum(m.values()),
             "members": sorted(({"agent": a, "share": None, "tokens": t} for a, t in m.items()), key=lambda x: (-x["tokens"], x["agent"]))}
            for p, m in parties.items()]
    return sorted(rows, key=lambda r: (-r["tokens"], r["party"]))


# -- the project's calls -----------------------------------------------------------------------------------------------

def _ledgers(state_dir: Path):
    """`(file, kind, name)` of every ledger: an idea's (its goal's party is read from its page), a party's own, the
    removed goals', the night's proposals'."""
    base = Path(state_dir)
    for p in sorted((base / "ideas").glob(f"*/{idea_spend.FILE}")):
        yield p, "idea", p.parent.name
    for p in sorted((base / "goals").glob(f"*/{idea_spend.FILE}")):
        yield p, "party", p.parent.name
    yield base / "ideas" / idea_spend.GONE, "idea", ""
    yield base / "ideas" / idea_spend.BOARD, "board", ""


def calls_of(root: Path, state_dir: Path, tool: str, since: dt.datetime | None = None) -> tuple[list[dict], dict[str, str]]:
    """The project's calls on `tool` (since `since`), each `{"at", "party", "agent", "tokens"}`, and the parties' titles
    `{key: title}`. `root`: where the Board's pages are (a goal's party is its page's `track`)."""
    tracks = {t["slug"]: t["title"] for t in ideas.tracks(Path(root), make=False)}
    page_of: dict[str, str] = {}

    def party_of_idea(slug: str) -> str:
        if slug not in page_of:
            page = ideas.idea_page(Path(root), slug) if slug else None
            page_of[slug] = (page.get("track") or ideas.GENERAL) if page is not None else GONE
        return page_of[slug]

    out, titles = [], {GONE: PARTY_GONE, ORKMASTER: PARTY_ORKMASTER}
    for path, kind, name in _ledgers(state_dir):
        for row in idea_spend.read(path):
            if row.get("tool") != tool:
                continue
            at = when(row.get("at"))
            if at is None or (since is not None and at < since):
                continue
            party = ORKMASTER if kind == "board" else name if kind == "party" else party_of_idea(name or str(row.get("idea") or ""))
            if party not in (GONE, ORKMASTER):
                titles.setdefault(party, tracks.get(party) or "A removed party")
            out.append({"at": at, "party": party, "agent": str(row.get("role") or roles.GRUNT),
                        "tokens": idea_spend.token_count(row)})
    return out, titles


def names_of(state_dir: Path, agents: set[str]) -> dict[str, str]:
    """`{agent: name}` for the members seen: the project's role, else the library's agent, else the slug."""
    known = roles.known(Path(state_dir))[0]
    out = {}
    for slug in agents:
        r = known.get(slug)
        a = library.get(slug) if r is None else None
        out[slug] = str((r or {}).get("name") or (a.name if a is not None else "") or ("Orkmaster" if slug == ORKMASTER else slug))
    return out


def events_of(root: Path) -> list[dict]:
    """A project's events (its `.orkcraft/usage/events.jsonl`), oldest first."""
    return event_log.read(Path(root))

