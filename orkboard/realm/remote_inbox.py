"""The phone's inbox on the project's own remote, read on the host (spec 136 B, decisions §243.2–4).

    # orkcraft.toml: `inbox` in the `[journal]` of realm/remote_journal.py turns the reading on
    #   [journal]
    #   inbox = "orkboard/inbox"

    remote_inbox.fetch(root, config)                      # {"ok": True, "empty": False} · {"ok": False, "why": "…"}; refs/orkboard/inbox, no checkout
    remote_inbox.entries(root)                            # [Entry]: the inbox/<device>/<id>.json on it, with the photos beside each
    remote_inbox.clean(raw, entry, ctx)                   # ({"text", "party", …, "photos": [bytes]}, "") · (None, "Could not read this goal: …")
    remote_inbox.take(root, state_dir, config, ctx, lay=…, find=…, name="my-computer")      # one tick: read, take in the journal, lay

The branch `orkboard/inbox` is the phone's: one file a goal, `inbox/<device>/<id>.json` (`id` a ULID the phone made, so the files
sort by time), its photos beside it as `<id>.<n>.jpg`. **Nothing here ever writes it**: the host fetches it into
`refs/orkboard/inbox` and reads the objects with `git ls-tree -r` and `git cat-file`; the working tree, the index and the
branch the person works on are untouched. Anything else on the branch is read as nothing.

A goal is **taken first and laid after** (§243.4): the goals read are written into `taken.json` (`remote_journal.read_taken`,
with an empty `slug`) and the journal is sent at once; only when that push went through is each goal laid on the Board by
`lay` (the host's `Ideas.add`, as the + card calls it), and its slug (or the add's words as `error`) goes into the next
journal. The journal's push without force is the lock: when it is refused (another took first), the journal is fetched, its
`taken.json` merged in, and what is left is taken once more, at most `TRIES` times a tick. A goal is laid once: `find` says
whether the Board already holds one with that inbox id (a host that stopped between the add and its journal), and a goal
taken here and not yet laid is laid on the next tick.

No face (the host passes `lay` and `find`), no model, no network but `git fetch` and the journal's `git push`.
"""
from __future__ import annotations

import base64
import datetime as dt
import json
import re
import socket
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from orkboard.realm import event_log, idea_element, idea_photos, ideas, remote_journal as rj

INBOX_REF = "refs/orkboard/inbox"
STATE_FILE = "inbox.json"
EVERY_S = 120                        # the inbox is read at most this often (§243.1)
TRIES = 3                            # a refused push is taken again this many times a tick
MAX_PER_TICK = 20                    # goals taken in one tick: a long inbox goes on in the next
PHOTO_BYTES = 2 * 2**20
_ENTRY = re.compile(r"inbox/([A-Za-z0-9._-]+)/([A-Za-z0-9_-]+)\.json")
_PHOTO = re.compile(r"inbox/([A-Za-z0-9._-]+)/([A-Za-z0-9_-]+)\.(\d{1,2})\.(jpg|jpeg|png|webp)")
_ID = re.compile(r"[A-Za-z0-9_-]{8,40}")


@dataclass(frozen=True)
class Entry:
    id: str
    device: str
    path: str
    photos: tuple[tuple[str, int], ...] = ()      # (path, size) of the photos beside it, in order


@dataclass
class Context:
    """What of the project `clean` decides by (the + card's rules): the parties, the types a party is offered, the runes."""
    parties: set[str] = field(default_factory=set)
    types: Callable[[str], set[str]] = lambda party: set()
    elements: tuple[str, ...] = tuple(idea_element.ELEMENTS)
    chars: int = ideas.SECTION_CHARS


# -- reading, never writing ----------------------------------------------------------------------------------------

def _git(root: Path, run: Callable, *args: str, data: bytes | None = None, raw: bool = False) -> str | bytes:
    env = {"GIT_TERMINAL_PROMPT": "0"}
    import os
    done = run(["git", *args], cwd=str(root), env={**os.environ, **env}, input=data, capture_output=True, timeout=120)
    if done.returncode != 0:
        words = done.stderr or done.stdout or b""
        raise RuntimeError(" ".join((words.decode("utf-8", "replace") if isinstance(words, bytes) else str(words)).split())[:300] or f"git {args[0]} failed")
    if raw:
        return done.stdout
    out = done.stdout
    return (out.decode("utf-8", "replace") if isinstance(out, bytes) else str(out)).strip()


def fetch(root: Path, config: rj.JournalConfig, run: Callable = subprocess.run) -> dict:
    """`git fetch <remote> +refs/heads/<inbox>:refs/orkboard/inbox`: no checkout, nothing of the working tree touched. `empty`: the
    remote has no such branch yet (nothing to read, not a failure). Never raises."""
    if not config.inbox:
        return {"ok": True, "empty": True}
    try:
        _git(root, run, "fetch", "--quiet", "--no-tags", config.remote, f"+refs/heads/{config.inbox}:{INBOX_REF}")
        return {"ok": True, "empty": False}
    except RuntimeError as e:
        why = str(e)
        if "couldn't find remote ref" in why.lower():
            return {"ok": True, "empty": True}
        return {"ok": False, "why": why}
    except Exception as e:                      # no git, a timeout
        return {"ok": False, "why": " ".join(str(e).split())[:300] or type(e).__name__}


def entries(root: Path, run: Callable = subprocess.run) -> list[Entry]:
    """The goals on the fetched inbox, by id (a ULID sorts by time), the photos beside each in order. Nothing else is read."""
    try:
        listing = str(_git(root, run, "ls-tree", "-r", "-l", "-z", INBOX_REF))
    except RuntimeError:
        return []
    files: dict[str, int] = {}
    for rec in listing.split("\0"):
        meta, _, name = rec.partition("\t")
        parts = meta.split()
        if len(parts) == 4 and parts[1] == "blob" and name:
            files[name] = int(parts[3]) if parts[3].isdigit() else 0
    photos: dict[tuple[str, str], list[tuple[int, str, int]]] = {}
    for name, size in files.items():
        m = _PHOTO.fullmatch(name)
        if m:
            photos.setdefault((m.group(1), m.group(2)), []).append((int(m.group(3)), name, size))
    out = []
    for name in sorted(files):
        m = _ENTRY.fullmatch(name)
        if m and _ID.fullmatch(m.group(2)):
            out.append(Entry(m.group(2), m.group(1), name, tuple((n, s) for _, n, s in sorted(photos.get((m.group(1), m.group(2)), [])))))
    return sorted(out, key=lambda e: (e.id, e.device))


def read(root: Path, path: str, run: Callable = subprocess.run) -> bytes:
    return _git(root, run, "cat-file", "blob", f"{INBOX_REF}:{path}", raw=True)           # type: ignore[return-value]


# -- cleaning ----------------------------------------------------------------------------------------------------------

def clean(raw: bytes | str, entry: Entry, ctx: Context, photo: Callable[[str], bytes] | None = None) -> tuple[dict | None, str]:
    """A goal as `Ideas.add` takes it, from the phone's file, or `(None, "Could not read this goal: <why>")`. `v` is 1; `text` is
    non-empty and cut to `ctx.chars`; `element`, `party` and `type` are dropped when not the project's (the route then decides);
    `asks` keep only text; `marks` pass as a list (the add cleans them); `photos` are only those beside it, each within
    `PHOTO_BYTES`, at most `idea_photos.MAX_PHOTOS`, an image (`photo(path)` reads one; none: no photos)."""
    def bad(why: str) -> tuple[None, str]:
        return None, f"Could not read this goal: {why}"
    try:
        data = json.loads(raw.decode("utf-8") if isinstance(raw, bytes) else raw)
    except (ValueError, UnicodeDecodeError):
        return bad("it is not a goal's file")
    if not isinstance(data, dict):
        return bad("it is not a goal's file")
    if data.get("v") != 1:
        return bad("it is of a version this Orkboard does not know")
    text = data.get("text")
    if not isinstance(text, str) or not text.strip():
        return bad("it holds no words")
    goal: dict = {"text": text.strip()[:ctx.chars]}
    party = data.get("party")
    if isinstance(party, str) and party in ctx.parties:
        goal["party"] = party
        kind = data.get("type")
        if isinstance(kind, str) and kind in ctx.types(party):
            goal["type"] = kind
            asks = data.get("asks")
            if isinstance(asks, dict):
                goal["asks"] = {str(k)[:60]: str(v)[:300] for k, v in asks.items() if isinstance(v, str) and v.strip()}
    if isinstance(data.get("element"), str) and data["element"] in ctx.elements:
        goal["element"] = data["element"]
    if isinstance(data.get("marks"), list):
        goal["marks"] = data["marks"][:20]
    kept: list[bytes] = []
    for path, size in entry.photos if photo else ():
        if len(kept) >= idea_photos.MAX_PHOTOS or size > PHOTO_BYTES:
            continue
        try:
            body = photo(path)
        except Exception:
            continue
        if len(body) <= PHOTO_BYTES and idea_photos._kind(body):
            kept.append(body)
    if kept:
        goal["photos"] = [{"data": base64.b64encode(b).decode("ascii")} for b in kept]
    return goal, ""


# -- when -----------------------------------------------------------------------------------------------------------------

def _stamp(state_dir: Path) -> dict:
    try:
        data = json.loads((Path(state_dir) / STATE_FILE).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def due(state_dir: Path, now: dt.datetime) -> bool:
    """At most every `EVERY_S` seconds since the last reading (kept in `<state_dir>/inbox.json`)."""
    try:
        last = dt.datetime.fromisoformat(str(_stamp(state_dir).get("at") or ""))
    except ValueError:
        return True
    return (now - last).total_seconds() >= EVERY_S


def _mark(state_dir: Path, now: dt.datetime) -> None:
    try:
        Path(state_dir).mkdir(parents=True, exist_ok=True)
        (Path(state_dir) / STATE_FILE).write_text(json.dumps({"at": now.isoformat(timespec="seconds")}), encoding="utf-8")
    except OSError:
        pass


# -- taking ----------------------------------------------------------------------------------------------------------------

def _journal_taken(root: Path, config: rj.JournalConfig, run: Callable) -> list[dict] | None:
    """The `taken.json` of what the remote's journal holds now: the local journal ref is moved to it (`send`'s rule: the next pack
    is built on what the remote really has). None: the journal could not be fetched (offline, no such branch)."""
    try:
        _git(root, run, "fetch", "--quiet", "--no-tags", config.remote, f"+refs/heads/{config.branch}:{rj.LOCAL_REF}")
    except RuntimeError:
        return None
    try:
        data = json.loads(str(_git(root, run, "cat-file", "blob", f"{rj.LOCAL_REF}:{rj.TAKEN_FILE}")))
    except (RuntimeError, ValueError):
        return []
    rows = data.get("taken") if isinstance(data, dict) else None
    return [r for r in rows if isinstance(r, dict) and isinstance(r.get("id"), str)] if isinstance(rows, list) else []


def _merge(mine: list[dict], theirs: list[dict]) -> list[dict]:
    """Theirs win: a goal another took is theirs, with their slug."""
    by_id = {r["id"]: r for r in mine}
    by_id.update({r["id"]: {"id": r["id"], "by": str(r.get("by") or ""), "at": str(r.get("at") or ""), "slug": str(r.get("slug") or ""),
                            "error": str(r.get("error") or "")} for r in theirs})
    return sorted(by_id.values(), key=lambda r: (r.get("at") or "", r["id"]))


def _said(root: Path, **fields) -> None:
    try:
        event_log.record(root, event_log.INBOX_TAKEN, **fields)
    except Exception:
        pass


def take(root: Path, state_dir: Path, config: rj.JournalConfig, ctx: Context, lay: Callable[[dict, str], str],
         find: Callable[[str], str], name: str = "", now: dt.datetime | None = None, run: Callable = subprocess.run,
         pages: Path | None = None, needs: frozenset[str] | set[str] = frozenset(), force: bool = False) -> dict:
    """One tick of the inbox. `lay(goal, id)`: the goal laid on the Board, its slug (raises with the add's words when refused);
    `find(id)`: the slug of the goal the Board already has for that inbox id, else "". Returns `{read, taken, laid, errors, why}`;
    never raises. Nothing is written to the inbox."""
    root, state_dir = Path(root), Path(state_dir)
    now = now or dt.datetime.now()
    name = name or socket.gethostname()
    out = {"read": 0, "taken": 0, "laid": 0, "errors": 0, "why": ""}
    if not config.inbox or (not force and not due(state_dir, now)):
        return out
    _mark(state_dir, now)
    try:
        got = fetch(root, config, run)
        if not got["ok"]:
            out["why"] = got["why"]
            _said(root, ok=False, id="", by=name, slug="", error=got["why"])
            return out
        found = [] if got["empty"] else entries(root, run)
        out["read"] = len(found)
        taken_now = rj.read_taken(state_dir, now)
        todo = [e for e in found if e.id not in {t["id"] for t in taken_now}][:MAX_PER_TICK]
        mine: list[dict] = []
        goals: dict[str, dict | None] = {}
        for e in todo:
            goal, err = _read_one(root, e, ctx, run)
            goals[e.id] = goal
            mine.append({"id": e.id, "by": name, "at": now.isoformat(timespec="seconds"), "slug": "", "error": err})
        if mine:
            mine = _take_in_journal(root, state_dir, config, mine, now, run, pages, needs, out)
        for m in mine:
            if m["error"]:                       # one that could not be read is taken with its error, so it is not read again
                out["errors"] += 1
                _said(root, ok=True, id=m["id"], by=name, slug="", error=m["error"])
        _lay_all(root, state_dir, config, ctx, goals, found, lay, find, name, now, run, pages, needs, out)
    except Exception as e:                       # the inbox troubles no work
        out["why"] = " ".join(str(e).split())[:300] or type(e).__name__
    return out


def _read_one(root: Path, e: Entry, ctx: Context, run: Callable) -> tuple[dict | None, str]:
    try:
        raw = read(root, e.path, run)
    except Exception as err:
        return None, f"Could not read this goal: {' '.join(str(err).split())[:120]}"
    return clean(raw, e, ctx, lambda p: read(root, p, run))


def _take_in_journal(root: Path, state_dir: Path, config: rj.JournalConfig, mine: list[dict], now: dt.datetime,
                     run: Callable, pages: Path | None, needs, out: dict) -> list[dict]:
    """Write `mine` into `taken.json` and send the journal; refused (another took first): merge the remote's `taken.json`, drop what is
    in it, take what is left again, `TRIES` times. Returns the goals this machine took (the push went through); [] when none."""
    before = rj.read_taken(state_dir, now)
    for _ in range(TRIES):
        if not mine:
            break
        rj.write_taken(state_dir, before + mine)
        sent = rj.send(root, state_dir, config, now, run, pages, needs)
        if sent["sent"]:
            out["taken"] = len(mine)
            return mine
        theirs = _journal_taken(root, config, run)
        rj.write_taken(state_dir, before)                 # not taken: nothing of ours is kept
        if theirs is None:                                # offline, or no journal to read: nothing was taken
            out["why"] = sent.get("why", "")
            return []
        before = _merge(before, theirs)
        rj.write_taken(state_dir, before)
        mine = [m for m in mine if m["id"] not in {t["id"] for t in theirs}]
    out["why"] = out["why"] or "The journal was taken by another before this one"
    return []


def _lay_all(root: Path, state_dir: Path, config: rj.JournalConfig, ctx: Context, goals: dict, found: list[Entry], lay: Callable,
             find: Callable, name: str, now: dt.datetime, run: Callable, pages: Path | None, needs, out: dict) -> None:
    """Lay what this machine took and has not laid (this tick's, and a tick's before that stopped): never twice (`find`)."""
    taken = rj.read_taken(state_dir, now)
    by_path = {e.id: e for e in found}
    changed = False
    for row in taken:
        if row["by"] != name or row["slug"] or row["error"]:
            continue
        slug = find(row["id"])
        error = ""
        if not slug:
            goal = goals.get(row["id"])
            if goal is None and row["id"] in by_path:                 # taken before, in a tick that stopped: read again
                goal, error = _read_one(root, by_path[row["id"]], ctx, run)
            if goal is None and not error:
                continue                                              # the inbox no longer shows it: nothing to lay
            if goal is not None:
                try:
                    slug = lay(goal, row["id"])
                except Exception as e:
                    error = " ".join(str(e).split())[:300] or type(e).__name__
        row["slug"], row["error"] = slug, error
        out["laid" if slug else "errors"] += 1
        changed = True
        _said(root, ok=True, id=row["id"], by=name, slug=slug, error=error)
    if changed:
        rj.write_taken(state_dir, taken)
        rj.send(root, state_dir, config, now, run, pages, needs)       # the slugs, at once; a failure is for the next tick
