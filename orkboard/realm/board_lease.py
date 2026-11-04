"""One holder of the Board at a time, by a lease the push decides (spec 137 B, decisions §244.2–3).

    # `lease.json` on the Board's branch (realm/board_branch.py): {"v": 1, "by": "<machine or run>", "kind": "computer" | "cloud run",
    #                                                               "until": "<ISO, UTC>", "at": "<ISO>"}
    got = board_lease.take(root, state_dir, config, me, kind, now, tree=board_tree)     # {held: True, …} · {held: False, by, kind, until}
    board_lease.renew(root, state_dir, config, me, kind, now, tree=board_tree)          # the lease moved on, the Board pushed with what changed
    board_lease.give_back(root, state_dir, config, me, kind, now, tree=board_tree)      # the lease freed, the Board pushed

**Held** while `until + SKEW_S` is ahead of now (two machines' clocks), unless the holder gave it back (`"back": true`, `until` = that
moment). Only the holder writes the branch. A lease is taken, renewed and given back by a push without force of a commit on the remote's
own tip, so two cannot hold it at once: **the push decides**. A refused push is read again once (fetch, read the lease), then the lease is
not taken. The first `take` makes the branch, with no parent, from this machine's Board.

A worker that takes a Board that is not its own last push unpacks the branch's files first (`board_branch.unpack`); what this machine
changed since its own last push is kept aside, whole, in `<state_dir>/board-aside/<at>/` first, and nothing is merged by itself (B.2.3).
What this machine last pushed is kept in `<state_dir>/board-sync.json` (`tip`, a `digest` of the files, `at`); the file is not on the branch.

Offline (the fetch or the push cannot reach the remote) is a result in words, never an exception: the host goes on working.
Events: `board_taken`, `board_pushed`, `board_refused`, `board_given_back`, `board_aside`; never a word of the Board.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from orkboard.realm import board_branch as bb, event_log

LEASE_S = 600           # a lease runs ten minutes ahead
RENEW_S = 180           # the holder renews it this often
SKEW_S = 60             # a lease is read held this long past its `until`
SYNC_FILE = "board-sync.json"
ASIDE_DIR = "board-aside"
COMPUTER, CLOUD_RUN = "computer", "cloud run"


@dataclass
class _Ctx:
    root: Path
    state_dir: Path
    config: bb.BoardConfig
    me: str
    kind: str
    tree: Any
    wiki_rel: str
    run: Callable


def _utc(now: dt.datetime) -> dt.datetime:
    return now.replace(tzinfo=dt.timezone.utc) if now.tzinfo is None else now.astimezone(dt.timezone.utc)


def _iso(t: dt.datetime) -> str:
    return _utc(t).isoformat(timespec="seconds")


def lease_bytes(me: str, kind: str, now: dt.datetime, back: bool = False) -> bytes:
    """The new `lease.json`: ten minutes ahead, or `until` = now when `back` (given back)."""
    now = _utc(now)
    data: dict[str, Any] = {"v": 1, "by": me, "kind": kind, "until": _iso(now if back else now + dt.timedelta(seconds=LEASE_S)), "at": _iso(now)}
    if back:
        data["back"] = True
    return (json.dumps(data, ensure_ascii=False, indent=1) + "\n").encode("utf-8")


def read_lease(files: dict[str, bytes]) -> dict | None:
    """The lease the files hold: `{by, kind, until (aware datetime), back}`; None when there is none or it cannot be read (nobody holds)."""
    try:
        data = json.loads(files[bb.LEASE].decode("utf-8"))
        until = dt.datetime.fromisoformat(str(data["until"]))
    except (KeyError, ValueError, UnicodeDecodeError, TypeError, AttributeError):
        return None
    if not isinstance(data, dict):
        return None
    return {"by": str(data.get("by") or ""), "kind": str(data.get("kind") or ""), "until": _utc(until), "back": data.get("back") is True}


def is_held(lease: dict | None, now: dt.datetime) -> bool:
    return bool(lease) and not lease["back"] and _utc(now) < lease["until"] + dt.timedelta(seconds=SKEW_S)      # type: ignore[index]


def _not_taken(lease: dict) -> dict:
    return {"held": False, "by": lease["by"], "kind": lease["kind"], "until": _iso(lease["until"])}


# -- what this machine last pushed ----------------------------------------------------------------------------------

def digest(files: dict[str, bytes]) -> str:
    h = hashlib.sha256()
    for name in sorted(files):
        if name != bb.LEASE:
            h.update(name.encode() + b"\0" + files[name] + b"\0")
    return h.hexdigest()


def read_sync(state_dir: Path) -> dict:
    try:
        data = json.loads((Path(state_dir) / SYNC_FILE).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def write_sync(state_dir: Path, tip: str, files_digest: str, now: dt.datetime) -> None:
    try:
        Path(state_dir).mkdir(parents=True, exist_ok=True)
        (Path(state_dir) / SYNC_FILE).write_text(json.dumps({"tip": tip, "digest": files_digest, "at": _iso(now)}), encoding="utf-8")
    except OSError:
        pass


def changed(state_dir: Path, wiki_rel: str = "") -> bool:
    """Whether the Board's files differ from what this machine last pushed (a digest of `pack`)."""
    files, _ = bb.pack(state_dir, wiki_rel)
    return digest(files) != read_sync(state_dir).get("digest")


def _said(root: Path, event: str, **fields: Any) -> None:
    try:
        event_log.record(root, event, **fields)
    except Exception:
        pass


def _ctx(root, state_dir, config, me, kind, tree, wiki_rel, run) -> _Ctx:
    return _Ctx(Path(root), Path(state_dir), config, me, kind, tree, (getattr(tree, "wiki_rel", None) if tree is not None else None) or wiki_rel, run)


# -- the plumbing of one push --------------------------------------------------------------------------------------

def _read_remote(c: _Ctx) -> tuple[str, dict[str, bytes], str]:
    """`(tip, files, why)`: the remote's tip fetched and its files; `why` set when it could not be reached."""
    got = bb.fetch(c.root, c.config, c.run)
    if not got["ok"]:
        return "", {}, got["why"] or "the remote could not be reached"
    if not got["tip"]:
        return "", {}, ""
    try:
        return got["tip"], bb.files_at(c.root, bb.REMOTE_REF, c.run), ""
    except RuntimeError as e:
        return "", {}, str(e)[:300]


def _publish(c: _Ctx, now: dt.datetime, files: dict[str, bytes], parent: str, message: str, back: bool = False) -> dict:
    """The files and a lease on `parent`, committed and pushed without force: `{ok, refused, why, commit}`."""
    try:
        made = bb.commit(c.root, c.state_dir, c.config, {**files, bb.LEASE: lease_bytes(c.me, c.kind, now, back)}, message, parent, c.run)
    except Exception as e:
        return {"ok": False, "refused": False, "why": " ".join(str(e).split())[:300] or type(e).__name__, "commit": ""}
    if not made:
        return {"ok": True, "refused": False, "why": "", "commit": parent}
    return {**bb.push(c.root, c.config, made, c.run), "commit": made}


def _aside(c: _Ctx, now: dt.datetime) -> str:
    """This machine's Board files, whole, in `<state_dir>/board-aside/<at>/`; "" when there were none."""
    files, _ = bb.pack(c.state_dir, c.wiki_rel)
    if not files:
        return ""
    where = c.state_dir / ASIDE_DIR / _utc(now).strftime("%Y%m%dT%H%M%SZ")
    for rel, body in files.items():
        f = where / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(body)
    return str(where)


def _unpack(c: _Ctx, remote: dict[str, bytes], tip: str, now: dt.datetime, by: str) -> dict:
    got = bb.unpack(c.state_dir, remote, c.tree, by=by, wiki_rel=c.wiki_rel)
    after, _ = bb.pack(c.state_dir, c.wiki_rel)
    write_sync(c.state_dir, tip, digest(after), now)
    return got


def _lost(c: _Ctx, now: dt.datetime, tip: str, remote: dict[str, bytes], lease: dict | None) -> dict:
    """Another worker had the Board: this machine's state since its last push kept aside, the branch's Board unpacked. Nothing is merged."""
    since = str(read_sync(c.state_dir).get("at") or "")
    aside = _aside(c, now)
    _unpack(c, remote, tip, now, lease["by"] if lease else "")
    _said(c.root, event_log.BOARD_ASIDE, by=lease["by"] if lease else "", files=len(bb.pack(c.state_dir, c.wiki_rel)[0]), since=since)
    return {"held": False, "lost": True, "aside": aside, "since": since,
            **(_not_taken(lease) if lease else {"by": "", "kind": "", "until": ""})}


# -- take, renew, give back ---------------------------------------------------------------------------------------

def take(root: Path, state_dir: Path, config: bb.BoardConfig, me: str, kind: str, now: dt.datetime, tree: Any = None,
         wiki_rel: str = "", run: Callable = subprocess.run) -> dict:
    """`{held: True, files, aside}` when the lease is this one's; `{held: False, by, kind, until}` when another holds it;
    `{held: False, offline: True, why}` when the remote could not be reached (the host goes on as it was). Never raises."""
    c, now = _ctx(root, state_dir, config, me, kind, tree, wiki_rel, run), _utc(now)
    try:
        return _take(c, now)
    except Exception as e:
        return {"held": False, "offline": True, "why": " ".join(str(e).split())[:300] or type(e).__name__}


def _take(c: _Ctx, now: dt.datetime) -> dict:
    last: dict | None = None
    for _ in range(2):                                   # the push decides; a refused one is read again once
        tip, remote, why = _read_remote(c)
        if why:
            return {"held": False, "offline": True, "why": why}
        lease = read_lease(remote)
        if tip and is_held(lease, now) and lease["by"] != c.me:             # type: ignore[index]
            _said(c.root, event_log.BOARD_REFUSED, by=lease["by"], kind=lease["kind"], until=_iso(lease["until"]))      # type: ignore[index]
            return _not_taken(lease)                                         # type: ignore[arg-type]
        local, held = bb.pack(c.state_dir, c.wiki_rel)
        got = _publish(c, now, remote if tip else local, tip, f"board: taken by {c.me} ({c.kind})")
        if got["ok"]:
            return _taken(c, now, tip, remote, local, got["commit"])
        last = lease
        if not got["refused"]:
            return {"held": False, "offline": True, "why": got["why"]}
    again, remote, why = _read_remote(c)
    lease = read_lease(remote) or last
    out = _not_taken(lease) if lease else {"held": False, "by": "", "kind": "", "until": ""}
    _said(c.root, event_log.BOARD_REFUSED, by=out["by"], kind=out["kind"], until=out["until"])
    return out


def _taken(c: _Ctx, now: dt.datetime, tip: str, remote: dict[str, bytes], local: dict[str, bytes], commit: str) -> dict:
    sync, aside = read_sync(c.state_dir), ""
    if not tip:                                              # the first take made the branch from this Board
        write_sync(c.state_dir, commit, digest(local), now)
    elif sync.get("tip") == tip:                             # the remote is this machine's own last push: what changed since is pushed next
        write_sync(c.state_dir, commit, str(sync.get("digest") or ""), now)
    else:                                                    # a Board that is another's: this machine's changes aside first, then the branch's files
        if local and (not sync or digest(local) != sync.get("digest")):
            aside = _aside(c, now)
            if aside:
                _said(c.root, event_log.BOARD_ASIDE, by=c.me, files=len(local), since=str(sync.get("at") or ""))
        before = read_lease(remote)
        _unpack(c, remote, commit, now, before["by"] if before and before["by"] else "the branch")
    _said(c.root, event_log.BOARD_TAKEN, by=c.me, kind=c.kind, files=len(remote or local))
    return {"held": True, "files": len(remote or local), "aside": aside, "commit": commit}


def renew(root: Path, state_dir: Path, config: bb.BoardConfig, me: str, kind: str, now: dt.datetime, tree: Any = None,
          wiki_rel: str = "", run: Callable = subprocess.run, back: bool = False) -> dict:
    """The holder's push: the lease moved ten minutes on, the Board packed and committed with what changed, pushed without force.
    `{held: True, pushed: True, commit, files, held_back}`; `{held: True, offline: True, why}` when it could not reach the remote (the host
    goes on working); `{held: False, lost: True, aside, since, by, kind, until}` when another had the Board meanwhile (this machine's
    changes since its last push are kept aside, the branch's Board unpacked). Never raises."""
    c, now = _ctx(root, state_dir, config, me, kind, tree, wiki_rel, run), _utc(now)
    try:
        return _renew(c, now, back)
    except Exception as e:
        return {"held": True, "offline": True, "why": " ".join(str(e).split())[:300] or type(e).__name__}


def _renew(c: _Ctx, now: dt.datetime, back: bool = False) -> dict:
    why = ""
    for _ in range(2):
        tip, remote, why = _read_remote(c)
        if why:
            return {"held": True, "offline": True, "why": why}
        if tip and tip != read_sync(c.state_dir).get("tip"):
            lease = read_lease(remote)
            if not (lease and lease["by"] == c.me and not lease["back"]):          # not this machine's own push: another had the Board
                return _lost(c, now, tip, remote, lease)
        local, held = bb.pack(c.state_dir, c.wiki_rel)
        got = _publish(c, now, local, tip, f"board: {'given back' if back else 'pushed'} by {c.me} ({c.kind})", back)
        why = got["why"]
        if got["ok"]:
            write_sync(c.state_dir, got["commit"], digest(local), now)
            _said(c.root, event_log.BOARD_PUSHED, commit=got["commit"], files=len(local), held_back=len(held), why="")
            return {"held": True, "pushed": True, "commit": got["commit"], "files": len(local), "held_back": len(held)}
        if not got["refused"]:
            _said(c.root, event_log.BOARD_PUSHED, commit="", files=len(local), held_back=len(held), why=why)
            return {"held": True, "offline": True, "why": why}
    return {"held": True, "offline": True, "why": why or "another pushed first"}


def follow(root: Path, state_dir: Path, config: bb.BoardConfig, me: str, now: dt.datetime, tree: Any = None, wiki_rel: str = "",
           run: Callable = subprocess.run) -> dict:
    """A worker that does not hold the Board reads it from the branch's files (B.2.1): unpacked when the tip is not what this machine last
    pushed or read, its own changes since kept aside first. `{followed: bool, aside}`; never raises, nothing is pushed."""
    c, now = _ctx(root, state_dir, config, me, COMPUTER, tree, wiki_rel, run), _utc(now)
    try:
        tip, remote, why = _read_remote(c)
        sync = read_sync(c.state_dir)
        if why or not tip or sync.get("tip") == tip:
            return {"followed": False, "aside": ""}
        local, _ = bb.pack(c.state_dir, c.wiki_rel)
        aside = ""
        if local and (not sync or digest(local) != sync.get("digest")):
            aside = _aside(c, now)
            _said(c.root, event_log.BOARD_ASIDE, by=c.me, files=len(local), since=str(sync.get("at") or ""))
        before = read_lease(remote)
        _unpack(c, remote, tip, now, before["by"] if before and before["by"] else "the branch")
        return {"followed": True, "aside": aside, "since": str(sync.get("at") or "")}
    except Exception as e:
        return {"followed": False, "aside": "", "why": " ".join(str(e).split())[:300]}


def give_back(root: Path, state_dir: Path, config: bb.BoardConfig, me: str, kind: str, now: dt.datetime, tree: Any = None,
              wiki_rel: str = "", run: Callable = subprocess.run) -> dict:
    """`until` set to now (and `back`), pushed with the Board: the computer's quit and a cloud run's last step. `{given: True}`; `{given: False,
    why}` when it could not be pushed (the lease then runs out by itself); `{given: False, lost: True, …}` when it was not this one's any more."""
    got = renew(root, state_dir, config, me, kind, now, tree, wiki_rel, run, back=True)
    if got.get("pushed"):
        _said(Path(root), event_log.BOARD_GIVEN_BACK, by=me, kind=kind)
        return {"given": True, "commit": got["commit"]}
    return {"given": False, **{k: v for k, v in got.items() if k not in ("held",)}}
