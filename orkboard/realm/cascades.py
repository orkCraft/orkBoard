"""The cascades a leader's proposal runs (docs/specs/131-a-leaders-slices-and-the-cascade.md §B.1–B.3; decisions §233.5–§233.9, §237.6): a leader that finds a slice of its own wrong for its craft proposes its change; the slices
that rest on it are asked, step by step, and the result waits as one card in the hand. No model and no face (the run is `core/idea_cascade.py`'s, the commands `gui/ideas_cascade.py`'s); never imports `gui/`.

    cascades.read(state_dir) / get(state_dir, cid) / save(state_dir, rec) / drop(state_dir, cid)   # <state_dir>/cascades.json {"cascades": [record]}, written whole under a lock
    cascades.add(state_dir, party, proposal, from_step, idea="", before="")   # a record `asking` for a cleaned proposal
    cascades.open_for(state_dir, slice_id)             # the cascade of the slice that is not confirmed or put back (asking, ready), else None
    cascades.clean_proposal(raw, party, standing)      # a leader's `propose`, strictly: {slice, says, why, points}; None drops it (and never the answer it came in)
    cascades.clean_answer(raw, current)                # a leader's answer in a step, strictly: {answer: "agrees"|"disagrees", says, why}; None for none
    cascades.chain(rec) / cascades.agreeing(rec)       # the leaders' slices before and after, in order; the parties that agree (the proposer first)
    cascades.rows(state_dir, root=None)                # the Needs you rows (`kind: "cascade"`) of the cascades `ready`

A record is `{id, at, party, from_step, idea, slice, before, says, why, points, status, steps, forks, stopped, changed, decision, sections, cost, error}`: `status` asking · ready · failed, then confirmed or put_back; `steps`
`[{n, party, slice, answer, says, why, cost, before, points, changed, forked}]`; `forks` `[{party, slice, says, now, why}]` (a leader that disagreed, or whose agreeing slice would change a point a second time); `stopped` the
words of where the cascade stopped ("" when it ended by itself); `changed` the points changed once; `decision` `{title, text, changes: [n]}`; `sections` `[{idea, party}]` (what follows).
"""
from __future__ import annotations

import datetime as dt
import json
import secrets
import threading
from pathlib import Path

from orkboard.realm import lexicon, slices

FILE = "cascades.json"
WHY_CHARS = 300                  # a proposal's reason, at most (and an answer's)
STATUS = ("asking", "ready", "failed", "confirmed", "put_back")
OPEN = ("asking", "ready")       # a slice with a cascade in these is not proposed on again
KEEP_CLOSED = 20                 # the closed cascades kept, the oldest go first
_LOCK = threading.Lock()


def _words(v: object, n: int) -> str:
    return " ".join(str(v or "").split())[:n].rstrip() if isinstance(v, (str, int, float)) and not isinstance(v, bool) else ""


def _now() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def new_id() -> str:
    return "c-" + secrets.token_hex(4)


def _file(state_dir: Path) -> Path:
    return Path(state_dir) / FILE


# -- the store ----------------------------------------------------------------------------------------------------------------------------------

def read(state_dir: Path) -> list[dict]:
    """The cascades, the oldest first; a file that is missing or broken reads as none, a line that is no record is left out."""
    try:
        raw = json.loads(_file(state_dir).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    rows = raw.get("cascades") if isinstance(raw, dict) else None
    return [dict(r) for r in rows if isinstance(r, dict) and isinstance(r.get("id"), str) and r.get("status") in STATUS] if isinstance(rows, list) else []


def _write(state_dir: Path, rows: list[dict]) -> None:
    f = _file(state_dir)
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_suffix(".json.tmp")
    tmp.write_text(json.dumps({"cascades": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(f)


def get(state_dir: Path, cid: str) -> dict | None:
    return next((r for r in read(state_dir) if r["id"] == cid), None)


def save(state_dir: Path, rec: dict) -> dict:
    """A record kept: replaces the one of its id, else added last; the closed ones past KEEP_CLOSED go, the oldest first. OSError for a disk that refused."""
    with _LOCK:
        rows = [r for r in read(state_dir) if r["id"] != rec["id"]] + [rec]
        closed = [r for r in rows if r.get("status") not in OPEN]
        gone = {id(r) for r in closed[:-KEEP_CLOSED]} if len(closed) > KEEP_CLOSED else set()
        _write(state_dir, [r for r in rows if id(r) not in gone])
    return rec


def drop(state_dir: Path, cid: str) -> bool:
    """A record taken away (a run that was stopped keeps nothing); False when there was none."""
    with _LOCK:
        rows = read(state_dir)
        left = [r for r in rows if r["id"] != cid]
        if len(left) == len(rows):
            return False
        _write(state_dir, left)
    return True


def open_for(state_dir: Path, slice_id: str) -> dict | None:
    return next((r for r in read(state_dir) if r.get("slice") == slice_id and r.get("status") in OPEN), None)


def add(state_dir: Path, party: str, proposal: dict, from_step: str, idea: str = "", before: str = "") -> dict:
    """A cascade `asking` for a cleaned proposal (`clean_proposal`'s). OSError for a disk that refused."""
    rec = {"id": new_id(), "at": _now(), "party": party, "from_step": _words(from_step, 40), "idea": _words(idea, 100), "slice": proposal["slice"], "before": _words(before, slices.SAYS_CHARS),
           "says": proposal["says"], "why": proposal["why"], "points": list(proposal["points"]), "status": "asking", "steps": [], "forks": [], "stopped": "", "changed": list(proposal["points"]),
           "decision": {}, "sections": [], "cost": 0.0, "error": ""}
    return save(state_dir, rec)


# -- the proposal and the answers, strictly ------------------------------------------------------------------------------------------------------

def same(a: str, b: str) -> bool:
    """Two points are the same place (`"240.2"` and `"240.2"`, or `"240"` and `"240.2"`, either way)."""
    return slices._match(a, b)


def clean_proposal(raw: object, party: str, standing: list[dict]) -> dict | None:
    """A leader's `propose`, strictly: `{slice, says, why, points}`. `slice` must be a standing slice of the answering party (`standing`: its standing slices); `says` and `why` one line each (SAYS_CHARS,
    WHY_CHARS) and both needed, and `says` must say something other than the slice does; `points` the points of the slice that the change touches (the slice's own by default). Anything else drops it."""
    if not isinstance(raw, dict):
        return None
    mine = next((s for s in standing if s.get("id") == raw.get("slice") and s.get("party") == party and not s.get("replaced_by")), None)
    if mine is None:
        return None
    says, why = _words(raw.get("says"), slices.SAYS_CHARS), _words(raw.get("why"), WHY_CHARS)
    if not says or not why or says.lower() == mine["says"].lower():
        return None
    given = slices._points(raw.get("points"))
    points = [p for p in given if any(same(p, q) for q in mine["points"])] or list(mine["points"])
    return {"slice": mine["id"], "says": says, "why": why, "points": points}


def clean_answer(raw: object, current: str = "") -> dict | None:
    """A leader's answer in a step, strictly: `{answer, says, why}`. `answer` is `agrees` or `disagrees`; `says` is its slice as it would read (one line; an agreeing answer with none leaves the slice as it is, a
    `current` it keeps); a disagreement needs its `why`. None for an answer that is no such object."""
    if not isinstance(raw, dict) or raw.get("answer") not in ("agrees", "disagrees"):
        return None
    says, why = _words(raw.get("says"), slices.SAYS_CHARS), _words(raw.get("why"), WHY_CHARS)
    if raw["answer"] == "disagrees":
        return {"answer": "disagrees", "says": says, "why": why} if why else None
    return {"answer": "agrees", "says": says or _words(current, slices.SAYS_CHARS), "why": why}


# -- the chain, the words ---------------------------------------------------------------------------------------------------------------------

def chain(rec: dict) -> list[dict]:
    """The leaders' slices before and after, in order: the proposer's first, then each agreeing step whose slice changed and was not made a fork."""
    out = [{"party": rec.get("party", ""), "slice": rec.get("slice", ""), "before": rec.get("before", ""), "after": rec.get("says", "")}]
    out += [{"party": s["party"], "slice": s.get("slice", ""), "before": s.get("before", ""), "after": s.get("says", "")}
            for s in rec.get("steps") or [] if isinstance(s, dict) and s.get("answer") == "agrees" and s.get("changed") and not s.get("forked")]
    return out


def agreeing(rec: dict) -> list[str]:
    """The parties that agree, the proposer first, once each (a leader that agreed and left its slice as it is agrees too)."""
    got = [rec.get("party", "")] + [s["party"] for s in rec.get("steps") or [] if isinstance(s, dict) and s.get("answer") == "agrees" and not s.get("forked")]
    return list(dict.fromkeys(p for p in got if p))


def joined(names: list[str]) -> str:
    """`Tech`, `Tech and Art`, `Tech, Art and Gnome`."""
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1] if names else ""


def stopped_words(kind: str, n: int, names: list[str]) -> str:
    """Where a cascade stopped, in plain words: *Stopped after 3 steps: Marketing was not asked*, or, at its price, *Stopped at its price: Marketing was not asked*."""
    head = lexicon.term("stopped_after_steps").replace("<n>", str(n)) if kind == "steps" else lexicon.term("stopped_at_price")
    return f"{head}: {joined(names)} {'was' if len(names) == 1 else 'were'} not asked"


def line_of(rec: dict, name_of) -> str:
    """The card's one line (§237.6): *Tech and Art agree* when no leader disagreed; else the forks first, each *<Leader> disagrees: <why>*. A cascade that asked no one says *<Leader> proposes*."""
    forks = [f for f in rec.get("forks") or [] if isinstance(f, dict)]
    if forks:
        return "; ".join(f"{name_of(f['party'])} {lexicon.term('disagrees').lower()}: {f.get('why', '')}".rstrip(": ") for f in forks)
    names = [name_of(p) for p in agreeing(rec)]
    if len(names) < 2:
        return f"{names[0] if names else ''} {lexicon.term('proposes').lower()}".strip()
    return lexicon.term("agree_line").replace("<A> and <B>", joined(names))


# -- the Needs you rows ---------------------------------------------------------------------------------------------------------------------

def rows(state_dir: Path, root: Path | None = None) -> list[dict]:
    """The Needs you rows of the cascades `ready` (a row of no goal's: `realm/board_rows.py` lays it): `{kind: "cascade", id, party, title, text, line, proposal: {party, says, why, before}, chain: [{party, name, before,
    after}], forks: [{party, name, slice, says, now, why}], stopped, cost, sections: [{idea, party}], level: "decision", pulls (realm/way_down.py: the goals not done that rest on the decisions changed and what their
    sections cost; `root` given), blocks, priority, at}`. Nothing changes until Confirm."""
    from orkboard.realm import ideas, way_down

    def name_of(party: str) -> str:
        page = ideas.track_page(Path(root), party) if root is not None else None
        return (page.title if page is not None else "") or party

    out = []
    for r in read(state_dir):
        if r["status"] != "ready":
            continue
        d = r.get("decision") if isinstance(r.get("decision"), dict) else {}
        parties = list(dict.fromkeys(c["party"] for c in chain(r)))
        pulls = way_down.empty("decision")
        if root is not None:
            try:
                pulls = way_down.pulls(state_dir, Path(root), "decision", changes=d.get("changes") or [], parties=parties)
            except Exception:                                          # a row is never lost to its price
                pulls = way_down.empty("decision")
        title = str(d.get("title") or r.get("says") or "")
        out.append({"kind": "cascade", "id": r["id"], "party": r.get("party", ""), "title": title, "text": title, "line": line_of(r, name_of),
                    "proposal": {"party": r.get("party", ""), "says": r.get("says", ""), "why": r.get("why", ""), "before": r.get("before", "")},
                    "chain": [{**c, "name": name_of(c["party"])} for c in chain(r)],
                    "forks": [{**f, "name": name_of(f["party"])} for f in r.get("forks") or [] if isinstance(f, dict)],
                    "stopped": str(r.get("stopped") or ""), "cost": r.get("cost"), "sections": pulls["sections"] or [s for s in r.get("sections") or [] if isinstance(s, dict)],
                    "level": "decision", "pulls": pulls, "usd_low": pulls["estimate"]["usd_low"], "usd_high": pulls["estimate"]["usd_high"],
                    "blocks": False, "priority": "normal", "at": str(r.get("at") or "")})
    return out
