"""The journals (docs/specs/125-the-journals.md §A; decisions §203): the project's journal, what the project decided and what came of it,
and each leader's journal, what its party's leader said and what came of it. Written by code where a thing happens, read into the leaders'
calls; a leader's journal is its own lens's history, the project's is everyone's. No model, no face (the digest a leader writes of its own
journal is `core/idea_journal.py`'s; the host's commands `gui/ideas_journal.py`'s).

    journals.add(state_dir, journals.PROJECT, "decision", "Decision 12: no accounts", idea="lobby", ref="12")   # an entry, or None for nothing to keep
    journals.add(state_dir, "tech", "overruled", "You said no to “Add a lobby” …", idea="add-lobby", on=["cache"])
    journals.read(state_dir, "tech")                  # the entries, oldest first, struck ones left out (`struck=True`: with them, marked)
    journals.of_goal(state_dir, "tech", "add-lobby")  # one goal's entries
    journals.refs(state_dir, journals.PROJECT)        # the refs kept (what was read in from the project's documents is never read in twice)
    journals.strike(state_dir, "tech", entry_id, why) # the person's *Not so*: the entry is never read into a call again (kept, marked)
    journals.digest(state_dir, "tech") / save_digest(state_dir, "tech", text, upto)   # the leader's own summary of its journal up to an entry
    journals.since_digest(state_dir, "tech")          # the entries after the digest's last one
    journals.text(state_dir, "tech", idea=, on=, chars=)  # what a call is given: the digest, then this goal's and these parts' entries, then the latest

**A scope** is `PROJECT` or a party's slug (`[a-z0-9-]`, as the Board's). **An entry** is `{id, at, kind, text, idea, on, ref}`: `kind` one of
`KINDS[scope]` (a project's or a leader's), `text` one line in the product's words (at most `TEXT_CHARS`), `idea` the goal's slug or "", `on` the parts
of the party's map it is about (ids, at most 8), `ref` a decision's number, a commit or "". Kept append only in `<state_dir>/journals/<scope>.jsonl`;
a strike is a line of its own (`{strike: id, at, why}`), so nothing is ever rewritten. A journal read keeps its last `KEEP` entries; the digest is
`<scope>.digest.json` (`{text, upto, at}`).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import threading
from pathlib import Path

PROJECT = "_project"                      # the project's own journal (no party's slug starts with "_")
DIR = "journals"
TEXT_CHARS = 300                          # an entry's line, at most
DIGEST_CHARS = 900                        # a digest, at most
KEEP = 5000                               # the entries a read keeps, the newest
CALL_CHARS = 1500                         # what a call is given of one journal, at most
ON_MAX = 8
PROJECT_KINDS = ("decision", "done", "dropped", "hypothesis", "brief", "pitch_passed")
LEADER_KINDS = ("stance", "heeded", "overruled", "came_back", "went_through", "concern_goal", "concern_dismissed", "since", "calibration",
                "decision")                     # a decision of its craft read in from the project's documents (spec 126 B)
KINDS = {"project": PROJECT_KINDS, "leader": LEADER_KINDS}
HEADS = {"project": "What the project decided and what came of it (its journal, newest last)",
         "leader": "What you said before and what came of it (your journal, newest last)"}
_SCOPE = re.compile(r"[a-z0-9-]{1,60}")
_ID = re.compile(r"[a-z0-9-]{1,80}")
_LOCK = threading.Lock()


def _words(v: object, n: int) -> str:
    return " ".join(str(v or "").split())[:n]


def _cut(text: str, n: int) -> str:
    return text if len(text) <= n else text[:max(0, n - 1)].rstrip() + "…"


def kind_of(scope: str) -> str:
    """"project" for the project's journal, "leader" for a party's; ValueError for a scope that is neither."""
    if scope == PROJECT:
        return "project"
    if isinstance(scope, str) and _SCOPE.fullmatch(scope):
        return "leader"
    raise ValueError(f"No journal {scope!r}")


def _file(state_dir: Path, scope: str, suffix: str = ".jsonl") -> Path:
    kind_of(scope)
    return Path(state_dir) / DIR / f"{scope}{suffix}"


def _now() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def add(state_dir: Path, scope: str, kind: str, text: str, *, idea: str = "", on: object = (), ref: str = "", at: str = "") -> dict | None:
    """One entry appended to `scope`'s journal: the entry, or None when there is nothing to keep (no words) or the disk refused. `at`: when it happened, for
    an entry read in from a project's documents (spec 126 B: an ISO day or time; else now). ValueError for a scope or a kind that is none (a writer's mistake,
    never the person's)."""
    if kind not in KINDS[kind_of(scope)]:
        raise ValueError(f"No kind {kind!r} in a {kind_of(scope)}'s journal")
    line = _words(text, TEXT_CHARS)
    if not line:
        return None
    at = _words(at, 25) if re.fullmatch(r"\d{4}-\d{2}-\d{2}(T[\d:]{5,8})?", _words(at, 25)) else _now()
    parts = [p for p in (on if isinstance(on, (list, tuple)) else ()) if isinstance(p, str) and p.strip()][:ON_MAX]
    entry = {"id": "", "at": at, "kind": kind, "text": line, "idea": _words(idea, 80), "on": [_words(p, 120) for p in parts], "ref": _words(ref, 60)}
    entry["id"] = hashlib.sha1(json.dumps(entry, sort_keys=True).encode()).hexdigest()[:12]
    try:
        with _LOCK:
            f = _file(state_dir, scope)
            f.parent.mkdir(parents=True, exist_ok=True)
            with f.open("a", encoding="utf-8") as out:
                out.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        return None
    return entry


def _lines(state_dir: Path, scope: str) -> list[dict]:
    try:
        raw = _file(state_dir, scope).read_text(encoding="utf-8")
    except OSError:
        return []
    out = []
    for line in raw.splitlines():
        try:
            got = json.loads(line)
        except ValueError:
            continue
        if isinstance(got, dict):
            out.append(got)
    return out


def read(state_dir: Path, scope: str, struck: bool = False) -> list[dict]:
    """The entries, oldest first, the last `KEEP`; a struck one is left out, or (`struck`) kept with `struck: {at, why}`. A line that is not an entry is skipped."""
    kinds = KINDS[kind_of(scope)]
    rows = _lines(state_dir, scope)
    strikes = {r["strike"]: {"at": str(r.get("at") or ""), "why": _words(r.get("why"), TEXT_CHARS)} for r in rows
               if isinstance(r.get("strike"), str)}
    out = []
    for r in rows:
        if not (isinstance(r.get("id"), str) and r.get("kind") in kinds and isinstance(r.get("text"), str) and r["text"].strip()):
            continue
        e = {"id": r["id"], "at": str(r.get("at") or ""), "kind": r["kind"], "text": _words(r["text"], TEXT_CHARS), "idea": str(r.get("idea") or ""),
             "on": [p for p in r.get("on") or [] if isinstance(p, str)][:ON_MAX] if isinstance(r.get("on"), list) else [], "ref": str(r.get("ref") or "")}
        if e["id"] in strikes:
            if not struck:
                continue
            e["struck"] = strikes[e["id"]]
        out.append(e)
    return out[-KEEP:]


def refs(state_dir: Path, scope: str) -> set[str]:
    """The `ref` of every entry, struck ones too: what was read in once is never read in twice (spec 126 B)."""
    return {e["ref"] for e in read(state_dir, scope, struck=True) if e["ref"]}


def of_goal(state_dir: Path, scope: str, idea: str) -> list[dict]:
    return [e for e in read(state_dir, scope) if idea and e["idea"] == idea]


def strike(state_dir: Path, scope: str, entry_id: str, why: str = "") -> dict | None:
    """The person's *Not so*: the entry is struck (a line of its own; never read into a call again). The entry, or None when there is none to strike."""
    if not (isinstance(entry_id, str) and _ID.fullmatch(entry_id)):
        return None
    mine = next((e for e in read(state_dir, scope) if e["id"] == entry_id), None)
    if mine is None:
        return None
    line = {"strike": entry_id, "at": _now(), "why": _words(why, TEXT_CHARS)}
    try:
        with _LOCK:
            with _file(state_dir, scope).open("a", encoding="utf-8") as out:
                out.write(json.dumps(line, ensure_ascii=False) + "\n")
    except OSError:
        return None
    return {**mine, "struck": {"at": line["at"], "why": line["why"]}}


def digest(state_dir: Path, scope: str) -> dict:
    """The leader's (or the project's) digest of its journal: `{text, upto, at}`, {} when there is none."""
    try:
        got = json.loads(_file(state_dir, scope, ".digest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(got, dict) or not _words(got.get("text"), 1):
        return {}
    return {"text": _words(got["text"], DIGEST_CHARS), "upto": str(got.get("upto") or ""), "at": str(got.get("at") or "")}


def save_digest(state_dir: Path, scope: str, text: str, upto: str) -> dict:
    """The digest kept (`upto`: the id of the last entry it read). ValueError for no words."""
    got = {"text": _words(text, DIGEST_CHARS), "upto": _words(upto, 80), "at": _now()}
    if not got["text"]:
        raise ValueError("A digest has words")
    f = _file(state_dir, scope, ".digest.json")
    with _LOCK:
        f.parent.mkdir(parents=True, exist_ok=True)
        tmp = f.with_suffix(".tmp")
        tmp.write_text(json.dumps(got, ensure_ascii=False), encoding="utf-8")
        tmp.replace(f)
    return got


def since_digest(state_dir: Path, scope: str) -> list[dict]:
    """The entries after the digest's last one (all of them with no digest, or when its last one is gone)."""
    rows = read(state_dir, scope)
    upto = digest(state_dir, scope).get("upto")
    ids = [e["id"] for e in rows]
    return rows[ids.index(upto) + 1:] if upto in ids else rows


def _line(e: dict) -> str:
    return f"- {e['at'][:10]} · {e['text']}"


def text(state_dir: Path, scope: str, *, idea: str = "", on: object = (), chars: int = CALL_CHARS) -> str:
    """What a call is given of a journal, `chars` at most, "" when it holds nothing: its heading, the digest (*In short*), then the entries on this goal
    (`idea`) and on these map parts (`on`), then the latest entries after the digest, each once, oldest first within each part."""
    rows = read(state_dir, scope)
    d = digest(state_dir, scope)
    if not rows and not d:
        return ""
    head = HEADS[kind_of(scope)] + ":"
    blocks = [head]
    used = len(head) + 1
    if d:
        short = f"In short: {d['text']}"
        blocks.append(short)
        used += len(short) + 1
    parts = set(p for p in (on if isinstance(on, (list, tuple)) else ()) if isinstance(p, str))
    near = [e for e in rows if (idea and e["idea"] == idea) or (parts and parts & set(e["on"]))]
    seen = {e["id"] for e in near}
    later = [e for e in since_digest(state_dir, scope) if e["id"] not in seen]
    picked: list[tuple[dict, str]] = []
    for e in near[-12:] + later[::-1]:                       # this goal's and these parts' first, then the newest back
        line = _line(e)
        if used + len(line) + 1 > chars:
            break
        picked.append((e, line))
        used += len(line) + 1
    order = {e["id"]: i for i, e in enumerate(rows)}
    picked.sort(key=lambda x: order.get(x[0]["id"], 0))
    blocks += [line for _e, line in picked]
    return _cut("\n".join(blocks), chars) if len(blocks) > 1 else ""
