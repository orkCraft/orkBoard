"""One worker at a goal at a time, by a file the push decides (spec 151 D.1, decisions §255.8): a goal is taken on the branch `orkboard/taken`.

    got = goal_take.take(root, slug, by, kind, now, hours=1)     # {taken: True, until} · {taken: False, by, kind, until} · {taken: True, offline: True, why}
    goal_take.renew(root, slug, by, kind, now, hours=1)          # `until` moved on (held by the same one); the same words as `take`
    goal_take.give_back(root, slug, by, now)                     # {given: True} · {given: False, by, kind, until} (another holds it) · {given: False, why}
    goal_take.held(root, slug, now=None)                         # {by, kind, until} while someone holds it (fetched), else None
    goal_take.read_all(root, now=None)                           # {slug: {by, kind, until}} of what is held now; None when the remote could not be reached
    goal_take.rules_written(root)                                # whether the root `AGENTS.md` holds Orkboard's rules (part C): until then none of D runs

The branch holds one file a goal, `<slug>.json`: `{"v": 1, "by", "kind": "orkboard" | "tool", "until": "<ISO, UTC>", "at": "<ISO>"}` (and `"back": true` once
it was given back). **Held** while `until + SKEW_S` is ahead of now (two machines' clocks), by another than `by`. Taken, renewed and given back by a commit of that
one file on the remote's own tip, pushed without force: **the push decides**. A refused push is fetched, read again and committed again on the new tip, at most
`TRIES` times (a goal another took meanwhile is no conflict; the same goal is). A branch that does not exist yet is made by the first take. A repository with
no remote takes locally: always taken, nothing kept. A remote that cannot be reached is a result in words, never an exception: the host goes on working.

The host asks the remote once a tick and keeps who holds what (`cache_set`); the places that start a goal ask that cache only (`blocked`, `refusal`): no
network call sits in the path of a press. Network: `git fetch` and `git push`, nothing else; no model, no face. Events: `goal_taken`, `goal_take_refused`,
`goal_given_back`.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Any, Callable

from orkboard.realm import board_branch, event_log, plumbing
from orkboard.realm.board_lease import SKEW_S

BRANCH = "orkboard/taken"
LOCAL_REF = "refs/orkboard/taken"
REMOTE_REF = "refs/orkboard/taken-remote"
TRIES = 3
ORKBOARD, TOOL = "orkboard", "tool"
RULES_MARK = "<!-- orkboard:begin"
TAKEN_LINE = "Taken by {by} until {time}"            # the words of a goal's card while another holds it (the author adds its TERMS entry)
_SLUG = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}")


def rules_written(root: Path) -> bool:
    """Whether the repository has the Board's rules, Orkboard's block (`<!-- orkboard:begin`) in its root `AGENTS.md`: in the checkout `root`, or in the Board's
    tree (`<root>/.orkcraft/board/`, the work branch, where Orkboard commits them while the person's checkout may be on another branch). Before it, no other
    tool works the Board, and nothing of spec 151 B or D runs. The one test of it (gui/ideas_phase.py asks it too)."""
    from orkboard.realm import agent_rules                 # here: the rules' module is the one that knows its block
    return any(agent_rules.has_rules(base) for base in (Path(root), Path(root) / ".orkcraft" / "board"))


def _utc(now: dt.datetime) -> dt.datetime:
    return now.replace(tzinfo=dt.timezone.utc) if now.tzinfo is None else now.astimezone(dt.timezone.utc)


def _now(now: dt.datetime | None) -> dt.datetime:
    return _utc(now) if now is not None else dt.datetime.now(dt.timezone.utc)


def _iso(t: dt.datetime) -> str:
    return _utc(t).isoformat(timespec="seconds")


def _said(root: Path, event: str, **fields: Any) -> None:
    try:
        event_log.record(root, event, **fields)
    except Exception:
        pass


def _words(e: Exception) -> str:
    return " ".join(str(e).split())[:300] or type(e).__name__


# -- the file --------------------------------------------------------------------------------------------------------

def file_bytes(by: str, kind: str, now: dt.datetime, hours: float = 1, back: bool = False) -> bytes:
    now = _utc(now)
    data: dict[str, Any] = {"v": 1, "by": by, "kind": kind, "until": _iso(now if back else now + dt.timedelta(hours=hours)), "at": _iso(now)}
    if back:
        data["back"] = True
    return (json.dumps(data, ensure_ascii=False, indent=1) + "\n").encode("utf-8")


def read_hold(body: bytes | None) -> dict | None:
    """`{by, kind, until (aware), back}` of a goal's file; None when there is none or it cannot be read (nobody holds)."""
    if body is None:
        return None
    try:
        data = json.loads(body.decode("utf-8"))
        until = dt.datetime.fromisoformat(str(data["until"]))
    except (KeyError, ValueError, UnicodeDecodeError, TypeError, AttributeError):
        return None
    if not isinstance(data, dict):
        return None
    return {"by": str(data.get("by") or ""), "kind": str(data.get("kind") or ""), "until": _utc(until), "back": data.get("back") is True}


def is_held(hold: dict | None, now: dt.datetime) -> bool:
    return bool(hold) and not hold["back"] and _utc(now) < hold["until"] + dt.timedelta(seconds=SKEW_S)      # type: ignore[index]


def _out(hold: dict) -> dict:
    return {"by": hold["by"], "kind": hold["kind"], "until": _iso(hold["until"])}


def _name(slug: str) -> str:
    if not _SLUG.fullmatch(slug or ""):
        raise ValueError(f"No goal {slug!r}")
    return f"{slug}.json"


# -- the remote ------------------------------------------------------------------------------------------------------

def _remote(root: Path, run: Callable) -> str:
    """The remote's name (`[board]`'s, else `origin`); "" when the repository has no such remote (it takes locally)."""
    config = board_branch.read_config(root)
    name = config.remote if config else "origin"
    try:
        plumbing.git(root, run, plumbing.env(), "remote", "get-url", name)
        return name
    except Exception:
        return ""


def _fetch(root: Path, remote: str, run: Callable) -> dict:
    """`{ok, tip, why}`: `orkboard/taken` fetched into a private ref, no checkout; `tip` "" when the branch does not exist yet."""
    try:
        plumbing.git(root, run, plumbing.env(), "fetch", "--quiet", "--no-tags", remote, f"+refs/heads/{BRANCH}:{REMOTE_REF}")
        return {"ok": True, "tip": plumbing.git(root, run, plumbing.env(), "rev-parse", REMOTE_REF), "why": ""}
    except RuntimeError as e:
        if "couldn't find remote ref" in str(e).lower():
            return {"ok": True, "tip": "", "why": ""}
        return {"ok": False, "tip": "", "why": str(e)[:300]}
    except Exception as e:
        return {"ok": False, "tip": "", "why": _words(e)}


def _read(root: Path, remote: str, run: Callable) -> tuple[str, dict[str, bytes], str]:
    """`(tip, files, why)`; `why` set when the remote could not be reached or read."""
    got = _fetch(root, remote, run)
    if not got["ok"]:
        return "", {}, got["why"] or "the remote could not be reached"
    if not got["tip"]:
        return "", {}, ""
    try:
        return got["tip"], board_branch.files_at(root, REMOTE_REF, run), ""
    except RuntimeError as e:
        return "", {}, str(e)[:300]


def _commit(root: Path, files: dict[str, bytes], parent: str, message: str, run: Callable) -> str:
    """A commit of `files` on `parent` (none for the first), by plumbing with a temporary index; the person's tree, index and branches untouched."""
    with tempfile.TemporaryDirectory(prefix="orkboard-taken-") as tmp:
        env = plumbing.env(Path(tmp) / "index")
        tree = plumbing.tree_of(root, run, env, files)
        made = plumbing.git(root, run, env, "commit-tree", tree, *(["-p", parent] if parent else []), "-m", message)
        plumbing.git(root, run, env, "update-ref", LOCAL_REF, made)
        return made


def _write(root: Path, slug: str, by: str, kind: str, now: dt.datetime, hours: float, back: bool, run: Callable) -> dict:
    """The one write: `{ok: True}` · `{ok: False, held: {by, kind, until}}` (another holds it) · `{ok: False, offline: True, why}` · `{ok: False, local: True}` (no remote)."""
    name = _name(slug)
    remote = _remote(root, run)
    if not remote:
        return {"ok": False, "local": True}
    cfg = board_branch.BoardConfig(remote, BRANCH)
    last = None
    for _ in range(TRIES):                               # the push decides; a refused one is read again on the new tip
        tip, files, why = _read(root, remote, run)
        if why:
            return {"ok": False, "offline": True, "why": why}
        hold = read_hold(files.get(name))
        if is_held(hold, now) and hold["by"] != by:      # type: ignore[index]
            return {"ok": False, "held": _out(hold)}     # type: ignore[arg-type]
        last = hold
        message = f"given back: {slug} by {by}" if back else f"taken: {slug} by {by}"
        try:
            made = _commit(root, {**files, name: file_bytes(by, kind, now, hours, back)}, tip, message, run)
        except Exception as e:
            return {"ok": False, "offline": True, "why": _words(e)}
        pushed = board_branch.push(root, cfg, made, run)
        if pushed["ok"]:
            return {"ok": True}
        if not pushed["refused"]:
            return {"ok": False, "offline": True, "why": pushed["why"]}
    again = read_hold(_read(root, remote, run)[1].get(name)) or last
    return {"ok": False, "held": _out(again) if again else {"by": "", "kind": "", "until": ""}}


# -- take, renew, give back, held ------------------------------------------------------------------------------------

def take(root: Path, slug: str, by: str, kind: str, now: dt.datetime, hours: float = 1, run: Callable = subprocess.run, _event: bool = True) -> dict:
    """`{taken: True, until}` when the goal is this one's now; `{taken: False, by, kind, until}` when another holds it (not run out); `{taken: True, until, offline: True,
    why}` when the remote could not be reached (the host goes on; the push decides when it is back). A repository with no remote: always taken. Never raises."""
    root, now = Path(root), _utc(now)
    until = _iso(now + dt.timedelta(hours=hours))
    try:
        got = _write(root, slug, by, kind, now, hours, False, run)
    except Exception as e:
        return {"taken": True, "until": until, "offline": True, "why": _words(e)}
    if got["ok"] or got.get("local"):
        if _event:
            _said(root, event_log.GOAL_TAKEN, slug=slug, by=by, kind=kind, until=until)
        return {"taken": True, "until": until, **({"local": True} if got.get("local") else {})}
    if got.get("offline"):
        return {"taken": True, "until": until, "offline": True, "why": got["why"]}
    _said(root, event_log.GOAL_TAKE_REFUSED, slug=slug, by=got["held"]["by"], until=got["held"]["until"])
    return {"taken": False, **got["held"]}


def renew(root: Path, slug: str, by: str, kind: str, now: dt.datetime, hours: float = 1, run: Callable = subprocess.run) -> dict:
    """`until` moved on: a take that says nothing of itself (the tick does it often)."""
    return take(root, slug, by, kind, now, hours, run, _event=False)


def give_back(root: Path, slug: str, by: str, now: dt.datetime, run: Callable = subprocess.run, kind: str = ORKBOARD) -> dict:
    """`until` set to now (and `back`): freed at once. `{given: True}`; `{given: False, by, kind, until}` when another holds it; `{given: False, why}` when
    it could not be pushed (the hold then runs out by itself). Nothing is written for a goal nobody holds. Never raises."""
    root, now = Path(root), _utc(now)
    try:
        remote = _remote(root, run)
        if not remote:
            _said(root, event_log.GOAL_GIVEN_BACK, slug=slug, by=by)
            return {"given": True, "local": True}
        _tip, files, why = _read(root, remote, run)
        if why:
            return {"given": False, "why": why}
        hold = read_hold(files.get(_name(slug)))
        if is_held(hold, now) and hold["by"] != by:      # type: ignore[index]
            return {"given": False, **_out(hold)}        # type: ignore[arg-type]
        if not is_held(hold, now):
            return {"given": True, "nothing": True}
        got = _write(root, slug, by, kind, now, 0, True, run)
    except Exception as e:
        return {"given": False, "why": _words(e)}
    if got["ok"]:
        _said(root, event_log.GOAL_GIVEN_BACK, slug=slug, by=by)
        return {"given": True}
    return {"given": False, **(got.get("held") or {"why": got.get("why", "")})}


def read_all(root: Path, now: dt.datetime | None = None, run: Callable = subprocess.run) -> dict[str, dict] | None:
    """Who holds what now, from one fetch: `{slug: {by, kind, until}}`; `{}` for no remote or no branch; None when the remote could not be reached. Never raises."""
    root, now = Path(root), _now(now)
    try:
        remote = _remote(root, run)
        if not remote:
            return {}
        _tip, files, why = _read(root, remote, run)
        if why:
            return None
        out = {}
        for name, body in files.items():
            hold = read_hold(body)
            if name.endswith(".json") and is_held(hold, now):
                out[name[:-5]] = _out(hold)                  # type: ignore[arg-type]
        return out
    except Exception:
        return None


def held(root: Path, slug: str, now: dt.datetime | None = None, run: Callable = subprocess.run) -> dict | None:
    """`{by, kind, until}` while the goal is held (fetched now); None when it is free, or the remote cannot be reached."""
    return (read_all(root, now, run) or {}).get(slug)


# -- what the host knows: the start points ask only this -----------------------------------------------------------------

_CACHE: dict[str, dict] = {}
_LOCK = threading.Lock()


def _key(root: Path) -> str:
    return str(Path(root).resolve())


def cache_set(root: Path, holds: dict[str, dict], me: str) -> None:
    """The host's tick: who holds what (`read_all`), and who `me` is (a hold of its own blocks nothing)."""
    with _LOCK:
        _CACHE[_key(root)] = {"holds": dict(holds), "me": me}


def cache_clear(root: Path) -> None:
    with _LOCK:
        _CACHE.pop(_key(root), None)


def blocked(root: Path, slug: str, now: dt.datetime | None = None) -> dict | None:
    """`{by, kind, until}` when the cache says another holds the goal and it has not run out; None otherwise (and always for a project the host has not read).
    The cache only: no git, no wait."""
    with _LOCK:
        seen = _CACHE.get(_key(root))
    if not seen:
        return None
    hold = seen["holds"].get(slug)
    if not hold or hold.get("by") == seen["me"]:
        return None
    try:
        until = dt.datetime.fromisoformat(hold["until"])
    except (KeyError, ValueError, TypeError):
        return None
    return dict(hold) if _now(now) < _utc(until) + dt.timedelta(seconds=SKEW_S) else None


def line_of(hold: dict) -> str:
    """*Taken by <by> until <time>* (the time in this computer's clock)."""
    try:
        when = dt.datetime.fromisoformat(hold["until"]).astimezone().strftime("%H:%M")
    except (KeyError, ValueError, TypeError):
        when = "later"
    return TAKEN_LINE.format(by=hold.get("by") or "another worker", time=when)


def refusal(root: Path, slug: str, now: dt.datetime | None = None) -> str:
    """The one check the start points call: the card's line when another holds the goal, "" when it may start."""
    hold = blocked(root, slug, now)
    return line_of(hold) if hold else ""
