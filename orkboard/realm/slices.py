"""The leaders' slices of the decisions (docs/specs/131-a-leaders-slices-and-the-cascade.md §A.1; decisions §233): each decision, once it is written, is cut into a slice for every leader it touches,
the key conclusion for that leader's craft and the points it rests on. A decision is the source and a slice is cut from it, so the store is derived. No model, no face (the cut and the fold are
`core/idea_slices.py`'s); never imports `gui/`.

    slices.read(state_dir)                         # the store, `{v, from, cut, slices, digests}`; an empty one for a file that is missing or broken
    slices.from_(state_dir)                        # the first decision cut (§233.4: only the new), None before the first cut
    slices.exists(state_dir)                       # the file is there (only a missing one is cut again from the decisions)
    slices.is_cut(state_dir, 233)                  # the decision was cut (a decision is never cut twice)
    slices.add_cut(state_dir, 233, {"tech": {"says": "…", "points": ["233.3"], "replaces": ["s-…"]}, "art": None})   # the slices added; `None` is *none*, kept as none
    slices.standing(state_dir, "tech")             # the party's slices not replaced, newest first
    slices.resting_on(state_dir, ["240.2"], but="tech")   # the standing slices of the other parties with a point in the list ("240" matches "240.2" and back)
    slices.text(state_dir, "tech")                 # the part a call is given (CALL_CHARS at most), "" with none
    slices.past_bound(state_dir, "tech")           # the standing slices not folded that do not fit beside the digest, oldest first: what the fold reads
    slices.gone(state_dir, "tech")                 # the slices the digest holds that were replaced since, the fold says they have gone
    slices.digest(state_dir, "tech") / slices.save_digest(state_dir, "tech", text, folded_ids)
    slices.link(["233.3", "233.4"])                # §233.3, §233.4
    slices.kept_from(state_dir)                    # `slices_from` of `<state_dir>/project.json`: where the recut starts when the store is missing

**The store** is `<state_dir>/slices.json`, written whole under a lock. `from` is set by the first cut and never moved (it is also kept in `project.json` as `slices_from`, beside the store, so a
store that is lost can be cut again). `cut` holds each decision cut with the parties that were given a slice: **a party a decision touches not is not there, and that is kept** (*none* is an
answer). **A slice is never edited** (§233.2): a replacement adds a slice and sets the old one's `replaced_by`; the new slice's `was` is the old one's `says` with its first link, and goes at its
own next replacement. A reader that cannot make sense of the file reads an empty store; only `add_cut` and `save_digest` write, and they say a disk that refused (OSError).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import threading
from pathlib import Path

FILE = "slices.json"
PROJECT_FILE = "project.json"
SAYS_CHARS = 300            # a slice's words, at most
WAS_CHARS = 160             # the line of what a slice replaced, at most
CALL_CHARS = 1000           # what a call is given of a leader's slices, as the brief is (decisions §233.3)
RECUT_MAX = 12              # the decisions cut again in one go when the store is missing
DIGEST_CHARS = 600          # a leader's digest of its slices past the bound, at most
POINTS_MAX = 8
HEAD = "What you hold of the project's decisions (newest first; read the decision for the rest):"
_POINT = re.compile(r"(\d{1,6})(?:\.(\d{1,3}))?")
_PARTY = re.compile(r"[a-z0-9-]{1,60}")
_ID = re.compile(r"s-[a-z0-9]{4,40}")
_LOCK = threading.Lock()


def _words(v: object, n: int) -> str:
    return " ".join(str(v or "").split())[:n].rstrip()


def _cut(text: str, n: int) -> str:
    return text if len(text) <= n else text[:max(0, n - 1)].rstrip() + "…"


def _now() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def _file(state_dir: Path) -> Path:
    return Path(state_dir) / FILE


def _points(raw: object) -> list[str]:
    """The points an answer names: `"N"` or `"N.k"`, once each, at most POINTS_MAX; anything else is left out."""
    out: list[str] = []
    for p in raw if isinstance(raw, (list, tuple)) else ():
        p = str(p).strip() if isinstance(p, (str, int)) and not isinstance(p, bool) else ""
        if _POINT.fullmatch(p) and p not in out:
            out.append(p)
    return out[:POINTS_MAX]


def _slice(raw: object) -> dict | None:
    """One slice as the store keeps it, or None for a line that is none."""
    if not isinstance(raw, dict) or not isinstance(raw.get("id"), str) or not _ID.fullmatch(raw["id"]):
        return None
    party, says = raw.get("party"), _words(raw.get("says"), SAYS_CHARS)
    n = raw.get("decision")
    if not (isinstance(party, str) and _PARTY.fullmatch(party) and says and isinstance(n, int) and not isinstance(n, bool) and n > 0):
        return None
    return {"id": raw["id"], "party": party, "decision": n, "points": _points(raw.get("points")) or [str(n)], "says": says, "was": _words(raw.get("was"), WAS_CHARS),
            "at": _words(raw.get("at"), 25), "replaced_by": _words(raw.get("replaced_by"), 60), "folded": raw.get("folded") is True}


def _empty() -> dict:
    return {"v": 1, "from": None, "cut": {}, "slices": [], "digests": {}}


def _load(state_dir: Path) -> dict:
    try:
        raw = json.loads(_file(state_dir).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return _empty()
    if not isinstance(raw, dict):
        return _empty()
    out = _empty()
    first = raw.get("from")
    out["from"] = first if isinstance(first, int) and not isinstance(first, bool) and first > 0 else None
    for k, v in (raw.get("cut") if isinstance(raw.get("cut"), dict) else {}).items():
        if isinstance(k, str) and k.isdigit() and isinstance(v, list):
            out["cut"][k] = [p for p in v if isinstance(p, str) and _PARTY.fullmatch(p)]
    out["slices"] = [s for s in (_slice(x) for x in (raw.get("slices") if isinstance(raw.get("slices"), list) else [])) if s]
    for party, d in (raw.get("digests") if isinstance(raw.get("digests"), dict) else {}).items():
        if isinstance(party, str) and _PARTY.fullmatch(party) and isinstance(d, dict) and _words(d.get("text"), 1):
            out["digests"][party] = {"text": _words(d["text"], DIGEST_CHARS), "upto": _words(d.get("upto"), 60), "at": _words(d.get("at"), 25)}
    return out


def _save(state_dir: Path, store: dict) -> None:
    """The store written whole (a temporary file moved over it). OSError for a disk that refused."""
    f = _file(state_dir)
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(store, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(f)


def read(state_dir: Path) -> dict:
    """The store: `{v, from, cut, slices, digests}`. A file that is missing or broken reads as an empty store; a line that is no slice is left out."""
    return _load(state_dir)


def from_(state_dir: Path) -> int | None:
    """The first decision cut; None before the first cut."""
    return _load(state_dir)["from"]


def exists(state_dir: Path) -> bool:
    """The store's file is there (a broken one is there; only a missing file is cut again from the decisions, A.1)."""
    return _file(state_dir).is_file()


def is_cut(state_dir: Path, n: int) -> bool:
    return str(n) in _load(state_dir)["cut"]


def link(points: object) -> str:
    """`§233.3, §233.4` for the points `["233.3", "233.4"]`; "" for none."""
    return ", ".join(f"§{p}" for p in _points(points))


def kept_from(state_dir: Path) -> int | None:
    """`slices_from` of `<state_dir>/project.json`: the first decision cut, kept beside the store so a lost store is cut again from there. None when it is not kept."""
    try:
        got = json.loads((Path(state_dir) / PROJECT_FILE).read_text(encoding="utf-8")).get("slices_from")
    except (OSError, ValueError, AttributeError):
        return None
    return got if isinstance(got, int) and not isinstance(got, bool) and got > 0 else None


def _keep_from(state_dir: Path, n: int) -> None:
    """`slices_from` written into `project.json`, the file's other keys left as they are; a disk that refuses is skipped (the store has `from` too)."""
    f = Path(state_dir) / PROJECT_FILE
    try:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
        data = data if isinstance(data, dict) else {}
        if data.get("slices_from") is None:
            data["slices_from"] = n
            f.parent.mkdir(parents=True, exist_ok=True)
            tmp = f.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            tmp.replace(f)
    except OSError:
        pass


def _new_id(n: int, party: str, says: str, at: str, taken: set[str]) -> str:
    seed = f"{n}|{party}|{says}|{at}"
    for k in range(1000):
        got = "s-" + hashlib.sha1(f"{seed}|{k}".encode()).hexdigest()[:8]
        if got not in taken:
            return got
    raise RuntimeError("no id")


def add_cut(state_dir: Path, n: int, answers: dict, at: str = "") -> list[dict]:
    """Decision `n` cut: `answers` is `{party: {"says", "points", "replaces": [slice ids]} | None}`. A party with an answer gets a slice (the slices added are returned); a party with `None`, or
    with no words, is *none*: it is not in `cut[n]`, and that is kept. A `replaces` id that is not a standing slice of that party is ignored; each one replaced gets its `replaced_by`, and the new
    slice's `was` is the first one's `says` with its first link (cut to WAS_CHARS). A decision already cut is not cut again: []. ValueError for a number that is none; OSError for a disk that refused."""
    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        raise ValueError("A decision has a number")
    at = _words(at, 25) or _now()
    added: list[dict] = []
    with _LOCK:
        store = _load(state_dir)
        if str(n) in store["cut"]:
            return []
        first = store["from"] is None
        if first:
            store["from"] = n
        taken = {s["id"] for s in store["slices"]}
        got_slice: list[str] = []
        for party, a in (answers.items() if isinstance(answers, dict) else ()):
            if not (isinstance(party, str) and _PARTY.fullmatch(party)) or not isinstance(a, dict):
                continue
            says = _words(a.get("says"), SAYS_CHARS)
            if not says:
                continue
            sid = _new_id(n, party, says, at, taken)
            taken.add(sid)
            old = [s for s in store["slices"] if s["party"] == party and not s["replaced_by"] and s["id"] in (a.get("replaces") if isinstance(a.get("replaces"), list) else [])]
            was = "; ".join(f"{_words(s['says'], 200).rstrip('.')} ({link(s['points'][:1])})" for s in old)
            new = {"id": sid, "party": party, "decision": n, "points": _points(a.get("points")) or [str(n)], "says": says, "was": _cut(was, WAS_CHARS), "at": at,
                   "replaced_by": "", "folded": False}
            for s in old:
                s["replaced_by"] = sid
            store["slices"].append(new)
            added.append(new)
            got_slice.append(party)
        store["cut"][str(n)] = got_slice
        _save(state_dir, store)
    if first:
        _keep_from(state_dir, n)
    return added


def standing(state_dir: Path, party: str) -> list[dict]:
    """The party's slices that are not replaced, the newest first."""
    return [s for s in reversed(_load(state_dir)["slices"]) if s["party"] == party and not s["replaced_by"]]


def _match(a: str, b: str) -> bool:
    """Two points are the same place: `"240.2"` and `"240.2"`, or `"240"` (the decision as a whole) and `"240.2"`, either way."""
    ma, mb = _POINT.fullmatch(a), _POINT.fullmatch(b)
    if not (ma and mb) or ma.group(1) != mb.group(1):
        return False
    return ma.group(2) is None or mb.group(2) is None or ma.group(2) == mb.group(2)


def resting_on(state_dir: Path, points: object, but: str = "") -> list[dict]:
    """The standing slices of every party (but `but`) with a point in `points`, the newest first."""
    want = _points(points)
    return [s for s in reversed(_load(state_dir)["slices"]) if not s["replaced_by"] and s["party"] != but and any(_match(p, q) for p in want for q in s["points"])]


def digest(state_dir: Path, party: str) -> dict:
    """The party's digest of its slices past the bound: `{text, upto, at}`, {} when there is none."""
    return dict(_load(state_dir)["digests"].get(party) or {})


def save_digest(state_dir: Path, party: str, text: str, folded_ids: object) -> dict:
    """The digest kept (`folded_ids`: the slices the fold read; they are marked `folded` and are no longer read one by one). ValueError for no words or a party that is none; OSError for a disk that refused."""
    words = _words(text, DIGEST_CHARS)
    if not words:
        raise ValueError("A digest has words")
    if not (isinstance(party, str) and _PARTY.fullmatch(party)):
        raise ValueError("A digest is a party's")
    ids = [i for i in (folded_ids if isinstance(folded_ids, (list, tuple)) else ()) if isinstance(i, str)]
    with _LOCK:
        store = _load(state_dir)
        mine = [s for s in store["slices"] if s["party"] == party and s["id"] in ids]
        for s in mine:
            s["folded"] = True
        store["digests"][party] = {"text": words, "upto": mine[-1]["id"] if mine else "", "at": _now()}
        _save(state_dir, store)
        return dict(store["digests"][party])


def _line(s: dict) -> str:
    return f"- {s['says']} ({link(s['points'])})" + (f"; was {s['was']}" if s["was"] else "")


def _fit(store: dict, party: str, chars: int) -> tuple[str, list[dict], list[dict]]:
    """`(the digest's line, the slices shown, the slices that did not fit)` for `chars`: the newest first, the newest always shown (cut if it must be); those already in the digest are not
    counted among the ones left out."""
    short = f"In short: {store['digests'][party]['text']}" if party in store["digests"] else ""
    mine = [s for s in reversed(store["slices"]) if s["party"] == party and not s["replaced_by"]]
    open_ = [s for s in mine if not s["folded"]]
    used = len(HEAD) + 1 + (len(short) + 1 if short else 0)
    note = len("(99 older not shown)") + 1
    shown: list[dict] = []
    for s in open_:
        line = len(_line(s)) + 1
        if shown and used + line + note > chars:
            break
        if not shown and used + line > chars:                    # the newest is always given, cut to the room there is
            shown.append(s)
            break
        shown.append(s)
        used += line
    return short, shown, open_[len(shown):]


def text(state_dir: Path, party: str, chars: int = CALL_CHARS) -> str:
    """What a call is given of a leader's slices, `chars` at most, "" when it holds none: the heading, the digest (*In short*), then the standing slices not in the digest, the newest first, each
    `- <says> (§240.2); was <what it replaced>`; the ones that did not fit are not shown and the part ends `(N older not shown)`."""
    try:
        store = _load(state_dir)
        short, shown, left = _fit(store, party, chars)
        if not short and not shown:
            return ""
        lines = [HEAD] + ([short] if short else []) + [_line(s) for s in shown] + ([f"({len(left)} older not shown)"] if left else [])
        return _cut("\n".join(lines), chars)
    except Exception:                                      # a store that cannot be read gives no part, never an error
        return ""


def past_bound(state_dir: Path, party: str) -> list[dict]:
    """The party's standing slices not yet folded that do not fit `CALL_CHARS` beside its digest, the oldest first: what the next fold reads."""
    try:
        return list(reversed(_fit(_load(state_dir), party, CALL_CHARS)[2]))
    except Exception:
        return []


def gone(state_dir: Path, party: str) -> list[dict]:
    """The party's slices the digest holds (folded) whose replacement has not been folded yet: the fold says they have gone. Each is `{slice, replaced_by}` (both slices)."""
    store = _load(state_dir)
    by = {s["id"]: s for s in store["slices"]}
    return [{"slice": s, "replaced_by": by[s["replaced_by"]]} for s in store["slices"]
            if s["party"] == party and s["folded"] and s["replaced_by"] in by and not by[s["replaced_by"]]["folded"]]
