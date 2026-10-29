"""A party's concerns (docs/specs/108-a-leader-says-no-and-shows-where-it-hurts.md §1, §2.4; decisions §183.4–§183.6): what its leader says is wrong or at risk in one part of its party's map, with why and
what would fix it, kept beside the Board's state. Read, kept and strictly parsed here; the leader's look is `core/idea_concerns.py`. No model, no face.

    concerns.read(state_dir, party)                      # the record, each part checked: see below
    concerns.save(state_dir, party, **changes)           # the record changed and kept (under the Board's lock)
    concerns.look_due(rec, map_hash, now, again=False)   # whether a look is due: none yet · the map changed since and the last look is a day old or more · asked again
    concerns.map_hash(text) / part_hash(text, part)      # the map text's hash; the lines of the text that name a part, hashed (what *the part changed* means)
    concerns.parse(party, answer, parts, dismissed, hashes, signals)   # the leader's answer, strictly → [{id, on, name, level, what, why, fix, signal}], at most MAX, an `on` that is no part dropped
    concerns.dismiss(state_dir, party, id, part_hash)    # *Not a problem*: the concern moves to `dismissed` → the concern, or None when it is not there
    concerns.made_goal(state_dir, party, id, idea)       # the concern notes the goal made of it (`idea`: its slug) → the concern, or None
    concerns.counts(rec)                                 # {alerts, notes}: the concerns no goal was made of
    concerns.text(rec, parts)                            # the concerns as lines a leader reads in Talk (*Your concerns on your map*)

`<state_dir>/concerns/<party>.json` is `{at, map_hash, by (the leader's role), status ("" | "looking" | "ready" | "failed"), error, measure, concerns: [{id, on, name, level ("alert" | "note"), what, why,
fix, signal, idea?}], dismissed: [{on, what, at, map_hash, part_hash}]}`. `at` is when the last look ended (or failed): none before the first. A concern's `id` is a hash of its part and its
words, so a look that says it again keeps the id; `signal` is the kind of hint of code (`realm/map_signals.py`) that is on its part, else "". A concern dismissed is not raised again while its part is as
it was (`part_hash`); the leader is told what was dismissed, and a concern that repeats one dismissed, its part unchanged, is dropped.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import re
from pathlib import Path

from orkboard.realm import ideas

FOLDER = "concerns"
MAX = 7                              # the most concerns a look keeps
LINE = 200                           # a concern's what, why and fix: a line each, at most
LEVELS = ("alert", "note")
DISMISSED = 40                       # the most dismissed concerns a record keeps (the newest)
EVERY_S = 24 * 3600                  # a look again, a map changed: when the last look is this old
_PARTY = re.compile(r"[a-z0-9][a-z0-9-]{0,99}")


def _file(state_dir: Path, party: str) -> Path:
    if not _PARTY.fullmatch(party or ""):
        raise ValueError(f"No party {party!r}")
    return Path(state_dir) / FOLDER / f"{party}.json"


def _line(value: object, n: int = LINE) -> str:
    return " ".join(value.split())[:n] if isinstance(value, str) else ""


def _id(party: str, on: str, what: str) -> str:
    return "c-" + hashlib.sha1(f"{party}\n{on}\n{' '.join(what.lower().split())}".encode()).hexdigest()[:10]


def map_hash(text: str | None) -> str:
    """The hash of a map's text: the map, as a leader reads it, is as it was while this is."""
    return hashlib.sha1((text or "").encode()).hexdigest()[:16]


def part_hash(text: str | None, part: dict) -> str:
    """The hash of the lines of the map's text that name `part` (its name, else its id): what the map says of the part. "" when it says nothing of it."""
    keys = [k for k in {part.get("name") or "", part.get("id") or ""} if k]
    lines = [ln for ln in (text or "").splitlines() if any(k in ln for k in keys)]
    return hashlib.sha1("\n".join(lines).encode()).hexdigest()[:12] if lines else ""


def now() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


# -- the record ------------------------------------------------------------------------------------------------------------------------

def _empty() -> dict:
    return {"at": "", "map_hash": "", "by": "", "status": "", "error": "", "measure": None, "concerns": [], "dismissed": []}


def read(state_dir: Path, party: str) -> dict:
    """The record, each part checked (whatever is not of the shape reads as absent; the file is not trusted)."""
    try:
        raw = ideas._json(_file(state_dir, party))
    except ValueError:
        return _empty()
    if not isinstance(raw, dict):
        return _empty()
    out = _empty()
    out.update(at=_line(raw.get("at"), 40), map_hash=_line(raw.get("map_hash"), 40), by=_line(raw.get("by"), 80), error=_line(raw.get("error"), 300),
               status=raw["status"] if raw.get("status") in ("looking", "ready", "failed") else "", measure=raw["measure"] if isinstance(raw.get("measure"), dict) else None)
    for r in raw.get("concerns") if isinstance(raw.get("concerns"), list) else []:
        if isinstance(r, dict) and isinstance(r.get("id"), str) and r.get("level") in LEVELS and _line(r.get("on"), 300) and _line(r.get("what")):
            out["concerns"].append({"id": r["id"][:40], "on": _line(r["on"], 300), "name": _line(r.get("name"), 300), "level": r["level"], "what": _line(r["what"]), "why": _line(r.get("why")),
                                    "fix": _line(r.get("fix")), "signal": _line(r.get("signal"), 40), **({"idea": _line(r["idea"], 100)} if _line(r.get("idea"), 100) else {})})
    for r in raw.get("dismissed") if isinstance(raw.get("dismissed"), list) else []:
        if isinstance(r, dict) and _line(r.get("on"), 300) and _line(r.get("what")):
            out["dismissed"].append({"on": _line(r["on"], 300), "what": _line(r["what"]), "at": _line(r.get("at"), 40), "map_hash": _line(r.get("map_hash"), 40),
                                     "part_hash": _line(r.get("part_hash"), 40)})
    out["dismissed"] = out["dismissed"][-DISMISSED:]
    return out


def save(state_dir: Path, party: str, **changes: object) -> dict:
    """The record with `changes` (any of its keys) made and kept; the record."""
    with ideas.LOCK:
        rec = {**read(state_dir, party), **changes}
        ideas._write_json(_file(state_dir, party), rec)
        return read(state_dir, party)


def look_due(rec: dict, hash_now: str, at: dt.datetime | None = None, again: bool = False) -> bool:
    """Whether a look is due (spec 108 §2.3): the person asked again; or none was ever made; or the map changed since the last look and that look is a day old or more.
    A look being made is never due again."""
    if rec.get("status") == "looking":
        return False
    if again or not rec.get("at"):
        return True
    if rec.get("map_hash") == hash_now:
        return False
    try:
        age = (at or dt.datetime.now()).timestamp() - dt.datetime.fromisoformat(rec["at"]).timestamp()
    except ValueError:
        return True
    return age >= EVERY_S


# -- the leader's answer ---------------------------------------------------------------------------------------------------------------

def parse(party: str, answer: object, parts: list[dict], dismissed: list[dict] | None = None, hashes: dict[str, str] | None = None,
          signals: list[dict] | None = None) -> list[dict] | None:
    """The leader's `{"concerns": [...]}` strictly: a concern is kept when its `on` is one of `parts` (`[{map, id, name}]`, a concern on another part is dropped), it says a `what` and its `level` is
    `alert` or `note` (an unsaid or unknown level is `note`); `what`, `why` and `fix` are a line of LINE characters at most; the same part and words once. Alerts come before notes, at most MAX are kept.
    A concern that says again one the person dismissed while its part is as it was (`dismissed`: [{on, what, part_hash}]; `hashes`: {part id: part_hash now}) is dropped. `signal` is the kind of the
    hint of code (`signals`) on its part, else "". None when the answer is no object with a `concerns` list."""
    if not isinstance(answer, dict) or not isinstance(answer.get("concerns"), list):
        return None
    by = {p["id"]: p for p in parts}
    hint = {}
    for s in signals or []:
        hint.setdefault(s.get("on"), s.get("kind") or "")
    skip = {_id(party, d["on"], d["what"]) for d in dismissed or [] if (hashes or {}).get(d["on"], "") == d.get("part_hash", "")}
    out, seen = [], set()
    for r in answer["concerns"]:
        if not isinstance(r, dict):
            continue
        on, what = _line(r.get("on"), 300), _line(r.get("what"))
        if on not in by or not what:
            continue
        cid = _id(party, on, what)
        if cid in seen or cid in skip:
            continue
        seen.add(cid)
        out.append({"id": cid, "on": on, "name": by[on]["name"], "level": r["level"] if r.get("level") in LEVELS else "note", "what": what, "why": _line(r.get("why")), "fix": _line(r.get("fix")),
                    "signal": hint.get(on, "")})
    out.sort(key=lambda c: LEVELS.index(c["level"]))
    return out[:MAX]


# -- the person's answers ---------------------------------------------------------------------------------------------------------------

def dismiss(state_dir: Path, party: str, cid: str, part_hash_: str = "") -> dict | None:
    """*Not a problem*: the concern leaves `concerns` for `dismissed` (with the map's hash of the look it came from and `part_hash_`, what the map said of its part then). The concern; None when it is not there."""
    with ideas.LOCK:
        rec = read(state_dir, party)
        mine = next((c for c in rec["concerns"] if c["id"] == cid), None)
        if mine is None:
            return None
        save(state_dir, party, concerns=[c for c in rec["concerns"] if c is not mine],
             dismissed=[*rec["dismissed"], {"on": mine["on"], "what": mine["what"], "at": now(), "map_hash": rec["map_hash"], "part_hash": part_hash_}][-DISMISSED:])
        return mine


def made_goal(state_dir: Path, party: str, cid: str, idea: str) -> dict | None:
    """*Make it a goal*: the concern notes the goal made of it. The concern; None when it is not there."""
    with ideas.LOCK:
        rec = read(state_dir, party)
        mine = next((c for c in rec["concerns"] if c["id"] == cid), None)
        if mine is None:
            return None
        mine["idea"] = idea
        save(state_dir, party, concerns=rec["concerns"])
        return dict(mine)


def counts(rec: dict) -> dict:
    """`{alerts, notes}`: how many concerns of the record are open, none made a goal of."""
    open_ = [c for c in rec.get("concerns") or [] if not c.get("idea")]
    return {"alerts": sum(1 for c in open_ if c["level"] == "alert"), "notes": sum(1 for c in open_ if c["level"] == "note")}


def text(rec: dict) -> str:
    """The open concerns as lines a leader reads (Talk's *Your concerns on your map*): `- [alert] <part name> (<id>): what. Why: … Fix: …`; "" with none."""
    rows = [f"- [{c['level']}] {c['name']} ({c['on']}): {c['what']}" + (f" Why: {c['why']}" if c["why"] else "") + (f" Fix: {c['fix']}" if c["fix"] else "")
            for c in rec.get("concerns") or [] if not c.get("idea")]
    return "\n".join(rows)
