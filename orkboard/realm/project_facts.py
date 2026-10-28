"""The project's facts by party (docs/specs/99-a-goals-way.md §2.2–§2.3, decisions §153.4, §156.7, §156.10): what a person answered about the
project, and what was read from its files, each with the party it belongs to, kept in `<state_dir>/facts.json` and read into a leader's call.

    project_facts.keep(state_dir, "product", "for_whom", "Players of party games", "person")   # an answer or a fact kept (`by`: person | read)
    project_facts.common(state_dir)                    # the common core as text: whom it is for, what hurts them, what it leaves out (~600 chars)
    project_facts.of(state_dir, "tech")                # one party's facts: [{key, text, by, at}]
    project_facts.for_call(state_dir, "tech", route)   # a leader's: the common core, its party's, another party's only when the route has it
    project_facts.answered(state_dir)                  # the keys answered or read, so a question is never asked again
    project_facts.start_files(root)                    # the README and docs/'s top level, chosen by code, for Product's reading at the start

The file is `{common: {for_whom, hurts, leaves_out}, common_by: {key: {by, at}}, party: {<party>: [{key, text, by, at}]}}`. A common key kept
sets `common` (its `by` and `at` beside it) and is kept in its party's list too; a fact read from the files never replaces an answer of the
person's. A member is given no fact (`for_call(..., member=True)`): its leader's brief carries what it needs. No model, no face.
"""
from __future__ import annotations

import re
from pathlib import Path

from orkboard.hooks.warder import is_secret
from orkboard.realm import ideas

FILE = "facts.json"
COMMON_KEYS = ("for_whom", "hurts", "leaves_out")
LABELS = {"for_whom": "Whom it is for", "hurts": "What hurts them", "leaves_out": "What it leaves out"}
BY = ("person", "read")
COMMON_CHARS = 600                 # the common core as text, at most
FACT_CHARS = 300                   # a fact's text kept, at most
PARTY_FACTS = 12                   # the most facts of one party read into a call
PARTY_CHARS = 900                  # … and their text, at most
START_DOCS = 6                     # the most files of docs/'s top level read at the start
START_CHARS = 2000                 # the first part of each file read at the start
README = ("readme.md", "readme.markdown", "readme.rst", "readme.txt", "readme")
_KEY = re.compile(r"[a-z0-9_]{1,40}")
_PARTY = re.compile(r"[a-z0-9-]{1,60}")


def _words(v: object, n: int) -> str:
    return " ".join(str(v or "").split())[:n]


def _cut(text: str, n: int) -> str:
    return text if len(text) <= n else text[:max(0, n - 1)].rstrip() + "…"


def _file(state_dir: Path) -> Path:
    return Path(state_dir) / FILE


def _read(state_dir: Path) -> dict:
    """The file's content as it is kept, each part checked: whatever is not of the shape reads as empty."""
    got = ideas._json(_file(state_dir)) or {}
    common = got.get("common") if isinstance(got.get("common"), dict) else {}
    by = got.get("common_by") if isinstance(got.get("common_by"), dict) else {}
    party = got.get("party") if isinstance(got.get("party"), dict) else {}
    out = {"common": {k: _words(common.get(k), FACT_CHARS) for k in COMMON_KEYS if _words(common.get(k), FACT_CHARS)},
           "common_by": {k: {"by": v.get("by") if v.get("by") in BY else "read", "at": str(v.get("at") or "")}
                         for k, v in by.items() if k in COMMON_KEYS and isinstance(v, dict)},
           "party": {}}
    for name, rows in party.items():
        if not (isinstance(name, str) and _PARTY.fullmatch(name) and isinstance(rows, list)):
            continue
        facts = [{"key": r["key"], "text": _words(r.get("text"), FACT_CHARS), "by": r.get("by") if r.get("by") in BY else "read",
                  "at": str(r.get("at") or "")}
                 for r in rows if isinstance(r, dict) and isinstance(r.get("key"), str) and _KEY.fullmatch(r["key"]) and _words(r.get("text"), 1)]
        if facts:
            out["party"][name] = facts
    return out


def keep(state_dir: Path, party: str, key: str, text: str, by: str) -> None:
    """A fact or an answer kept for `party` under `key` (`by`: "person" or "read"); the same key kept again is replaced, except that a reading
    never replaces the person's answer. A common key (`COMMON_KEYS`) is also the project's common core. ValueError for a party, a key or a
    `by` that is none, and for no text."""
    if not (isinstance(party, str) and _PARTY.fullmatch(party)):
        raise ValueError(f"No party {party!r}")
    if not (isinstance(key, str) and _KEY.fullmatch(key)):
        raise ValueError(f"Not a fact's key: {key!r}")
    if by not in BY:
        raise ValueError(f"A fact is kept by the person or read, not {by!r}")
    text = _words(text, FACT_CHARS)
    if not text:
        raise ValueError("A fact has words")
    with ideas.LOCK:
        got = _read(state_dir)
        at = ideas._now()
        rows = got["party"].setdefault(party, [])
        mine = next((r for r in rows if r["key"] == key), None)
        if by == "read" and mine is not None and mine["by"] == "person":
            return
        entry = {"key": key, "text": text, "by": by, "at": at}
        rows[:] = [entry if r is mine else r for r in rows] if mine is not None else rows + [entry]
        if key in COMMON_KEYS and not (by == "read" and got["common_by"].get(key, {}).get("by") == "person"):
            got["common"][key] = text
            got["common_by"][key] = {"by": by, "at": at}
        ideas._write_json(_file(state_dir), got)


def of(state_dir: Path, party: str) -> list[dict]:
    """The facts kept for `party`: `[{key, text, by, at}]`, in the order they were first kept."""
    return [dict(r) for r in _read(state_dir)["party"].get(party, [])]


def answered(state_dir: Path) -> set[str]:
    """The keys answered or read, whatever their party: a question of the project is never asked again."""
    got = _read(state_dir)
    return set(got["common"]) | {r["key"] for rows in got["party"].values() for r in rows}


def common(state_dir: Path) -> str:
    """The common core as text, COMMON_CHARS at most: one line each of what is kept of whom it is for, what hurts them, what it leaves out;
    "" when none is."""
    kept = _read(state_dir)["common"]
    have = [k for k in COMMON_KEYS if k in kept]
    if not have:
        return ""
    share = max(20, (COMMON_CHARS - sum(len(LABELS[k]) + 3 for k in have)) // len(have))
    return "\n".join(f"{LABELS[k]}: {_cut(kept[k], share)}" for k in have)


def _party_text(rows: list[dict]) -> str:
    """A party's facts as lines (PARTY_FACTS of them, PARTY_CHARS at most); the common keys are the core's, not repeated."""
    out, used = [], 0
    for r in [r for r in rows if r["key"] not in COMMON_KEYS][:PARTY_FACTS]:
        line = f"- {r['text']}"
        if used + len(line) + 1 > PARTY_CHARS:
            break
        out.append(line)
        used += len(line) + 1
    return "\n".join(out)


def for_call(state_dir: Path, party: str, route: object = (), member: bool = False) -> str:
    """What a leader's call is given of the project's facts: the common core, its own party's facts, and another party's only when the goal's
    `route` has that party (`[{party, leader}]`, or the parties' names). A member (`member`) is given none."""
    if member:
        return ""
    got = _read(state_dir)
    names = [party] + [n for n in (r.get("party") if isinstance(r, dict) else r for r in (route if isinstance(route, (list, tuple)) else ()))
                       if isinstance(n, str)]
    blocks = [f"What the project is:\n{core}" for core in [common(state_dir)] if core]
    seen: set[str] = set()
    for name in names:
        if name in seen:
            continue
        seen.add(name)
        text = _party_text(got["party"].get(name, []))
        if text:
            blocks.append(f"What is known for {name}:\n{text}")
    return "\n\n".join(blocks)


# -- Product's reading at the start (§156.10) ---------------------------------------------------------------------------------------------

def _head(root: Path, f: Path) -> str | None:
    """The first START_CHARS characters of a file of the project (no link, not secret), None for one that cannot be read."""
    try:
        rel = f.relative_to(root).as_posix()
        if f.is_symlink() or not f.is_file() or is_secret(rel):
            return None
        with f.open("rb") as fh:
            raw = fh.read(START_CHARS * 4)
    except (OSError, ValueError):
        return None
    return raw.decode("utf-8", errors="replace").replace("\r\n", "\n").strip()[:START_CHARS]


def start_files(root: Path) -> list[dict]:
    """`[{path, text}]`: the project's README and the Markdown files at the top of `docs/` (START_DOCS at most, by name), the first START_CHARS
    characters of each, chosen by code; for the one call that reads them (spec 99 §8.1). The decisions file is never one
    of them (spec 97 §1: a leader gets its entries by code)."""
    root = Path(root)
    try:
        top = sorted(root.iterdir(), key=lambda e: e.name.lower())
    except OSError:
        return []
    paths = [next((e for e in top if e.name.lower() in README), None)]
    docs = root / "docs"
    try:
        found = sorted((e for e in docs.iterdir() if e.suffix.lower() == ".md" and e.is_file() and e.name.lower() != "decisions.md"), key=lambda e: (e.name.lower(), e.name)) \
            if docs.is_dir() and not docs.is_symlink() else []
    except OSError:
        found = []
    out, docs_read = [], 0
    for f in paths + found:
        if f is not None and f.parent == docs and docs_read >= START_DOCS:
            break
        text = _head(root, f) if f is not None else None
        if text:
            out.append({"path": f.relative_to(root).as_posix(), "text": text})
            docs_read += f.parent == docs
    return out
