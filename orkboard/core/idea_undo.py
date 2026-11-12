"""One Undo in the Board's history (docs/specs/171 stage D; decisions §302.4): the hand's moves by kind, and the reverse of each one-press move.

    idea_undo.way("drop")                                # "press": one press, its Undo kept · "sealed": it goes only on its seal · KeyError for a kind that is neither
    idea_undo.snapshot(root, state_dir, slug)            # the goal's page and state as text (None: not there), before and after a move
    idea_undo.keep(state_dir, slug, kind, before, after, publish)   # the one writer of `<state_dir>/goals/<slug>/undo.json`; publishes `bus.MOVE_PLAYED`
    idea_undo.undo(root, state_dir, slug, publish, kind="")         # puts the bytes back only while they are still the after; ValueError in plain words else

A reverse writes the page into `root`, which is the Board's tree (`realm/board_tree.py`: the host's `Ideas.root()`), so the Board's next commit takes it;
the caller notes the write in the tree. A service never shows a toast: it publishes on the bus (`core/bus.py`).
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Callable

from orkboard.core import bus
from orkboard.realm import ideas

# The hand's moves, a closed table: each kind is one press with its reverse, or sealed (a move that cannot be undone). No kind is neither.
ONE_PRESS = {"drop": "put the page and its state back",
             "hold": "put the state back",
             "answer": "put the page and its state back"}
SEALED = {"merge_main": "Merge into main", "send_branch": "Send to a branch", "ship_release": "Ship a release", "paid_pass": "a paid pass"}

CHANGED_SINCE = "It changed since: nothing undone"
NOTHING = "Nothing to undo"


def way(kind: str) -> str:
    if kind in ONE_PRESS:
        return "press"
    if kind in SEALED:
        return "sealed"
    raise KeyError(kind)


def _slug(slug: str) -> str:
    if not re.fullmatch(r"[a-z0-9-]+", slug or ""):
        raise ValueError(f"No goal {slug!r}")
    return slug


def record_path(state_dir: Path, slug: str) -> Path:
    return Path(state_dir) / "goals" / _slug(slug) / "undo.json"


def _files(root: Path, state_dir: Path, slug: str) -> dict[str, Path]:
    return {"page": Path(root) / ideas.IDEAS / f"{_slug(slug)}.md", "state": ideas.state_folder(Path(state_dir), slug) / "state.json"}


def snapshot(root: Path, state_dir: Path, slug: str) -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    for name, path in _files(root, state_dir, slug).items():
        try:
            out[name] = path.read_text(encoding="utf-8")
        except OSError:
            out[name] = None
    return out


def keep(state_dir: Path, slug: str, kind: str, before: dict, after: dict, publish: Callable[..., None] | None = None, origin: str = "") -> bool:
    """The Undo of a one-press move just played: the bytes before and after. False when the move changed nothing (nothing to undo). KeyError for a sealed kind."""
    if way(kind) != "press":
        raise KeyError(kind)
    if before == after:
        return False
    path = record_path(state_dir, slug)
    with ideas.LOCK:
        ideas._write(path, json.dumps({"kind": kind, "before": before, "after": after}, ensure_ascii=False, indent=1) + "\n")
    if publish is not None:
        publish(bus.MOVE_PLAYED, idea=slug, kind=kind, origin=origin)
    return True


def read(state_dir: Path, slug: str) -> dict | None:
    try:
        row = json.loads(record_path(state_dir, slug).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    ok = isinstance(row, dict) and row.get("kind") in ONE_PRESS and isinstance(row.get("before"), dict) and isinstance(row.get("after"), dict)
    return row if ok else None


def undo(root: Path, state_dir: Path, slug: str, publish: Callable[..., None] | None = None, kind: str = "") -> dict:
    """The last one-press move of a goal put back, byte for byte, only while what it changed is still as the move left it. ValueError in plain words
    where there is nothing to undo or the goal changed since (nothing is written then)."""
    with ideas.LOCK:
        row = read(state_dir, slug)
        if row is None or (kind and row["kind"] != kind):
            raise ValueError(NOTHING)
        now, files = snapshot(root, state_dir, slug), _files(root, state_dir, slug)
        names = [n for n in files if row["before"].get(n) != row["after"].get(n)]
        if any(now.get(n) != row["after"].get(n) for n in names):
            raise ValueError(CHANGED_SINCE)
        for n in names:
            if row["before"].get(n) is None:
                files[n].unlink(missing_ok=True)
            else:
                ideas._write(files[n], row["before"][n])
        ideas._reindex(Path(root))
        record_path(state_dir, slug).unlink(missing_ok=True)
    if publish is not None:
        publish(bus.MOVE_UNDONE, idea=slug, kind=row["kind"])
    return {"kind": row["kind"]}
