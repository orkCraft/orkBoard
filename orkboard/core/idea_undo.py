"""One Undo in the Board's history (docs/specs/171 stage D; decisions §302.4): the hand's moves by kind, and the reverse of each one-press move.

    idea_undo.way("drop")                                # "press": one press, its Undo kept · "sealed": it goes only on its seal · KeyError for a kind that is neither
    idea_undo.snapshot(root, state_dir, slug)            # the goal's page and state as text (None: not there), before and after a move
    idea_undo.keep(state_dir, slug, kind, before, after, publish)   # the one writer of `<state_dir>/goals/<slug>/undo.json`; publishes `bus.MOVE_PLAYED`
    idea_undo.keep(state_dir, slug, "fix_goal", {"page": None, "state": None}, after, publish, laid=fix)   # a move on `slug` that laid another goal (`fix`): its record names the goal laid
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
from orkboard.realm import ideas, lexicon

# The hand's moves, a closed table: each kind is one press with its reverse, or sealed (a move that cannot be undone). No kind is neither.
ONE_PRESS = {"drop": "put the page and its state back",
             "hold": "put the state back",
             "answer": "put the page and its state back",
             "fix_goal": "remove the Fix goal it laid"}          # Fix it on a goal done whose way to main went red (decisions §303.5): the record keeps the goal laid, none before
SEALED = {"merge_main": "Merge into main", "send_branch": "Send to a branch", "ship_release": "Ship a release", "paid_pass": "a paid pass", "start_work": "Start the work",
          "fix_stage": lexicon.term("fix_stage")}          # Fix it on a goal unmerged on its branch whose way to dev went red: one task added, the goal at work (core/idea_fix_stage.py)

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


def record_path(state_dir: Path, slug: str, party: bool = False) -> Path:
    return Path(state_dir) / "goals" / _slug(slug) / ("party-undo.json" if party else "undo.json")


def _files(root: Path, state_dir: Path, slug: str, party: bool = False) -> dict[str, Path]:
    """The page and state a move changes: a goal's, or (`party`) a party's own page and state, whose questions were once called a goal's."""
    if party:
        return {"page": Path(root) / ideas.TRACKS / f"{_slug(slug)}.md", "state": ideas.goal_folder(Path(state_dir), slug) / "state.json"}
    return {"page": Path(root) / ideas.IDEAS / f"{_slug(slug)}.md", "state": ideas.state_folder(Path(state_dir), slug) / "state.json"}


def snapshot(root: Path, state_dir: Path, slug: str, party: bool = False) -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    for name, path in _files(root, state_dir, slug, party).items():
        try:
            out[name] = path.read_text(encoding="utf-8")
        except OSError:
            out[name] = None
    return out


def keep(state_dir: Path, slug: str, kind: str, before: dict, after: dict, publish: Callable[..., None] | None = None, origin: str = "", party: bool = False,
         laid: str = "") -> bool:
    """The Undo of a one-press move just played: the bytes before and after. False when the move changed nothing (nothing to undo). KeyError for a sealed kind.
    `laid`: a goal the move laid, whose page and state `before` and `after` are (Fix it lays a new goal from a done one's gate): the record is `slug`'s, its Undo too."""
    if way(kind) != "press":
        raise KeyError(kind)
    if before == after:
        return False
    path = record_path(state_dir, slug, party)
    row = {"kind": kind, **({"laid": _slug(laid)} if laid and laid != slug else {}), "before": before, "after": after}
    with ideas.LOCK:
        ideas._write(path, json.dumps(row, ensure_ascii=False, indent=1) + "\n")
    if publish is not None:
        publish(bus.MOVE_PLAYED, idea=slug, kind=kind, origin=origin)
    return True


def read(state_dir: Path, slug: str, party: bool = False) -> dict | None:
    try:
        row = json.loads(record_path(state_dir, slug, party).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    ok = isinstance(row, dict) and row.get("kind") in ONE_PRESS and isinstance(row.get("before"), dict) and isinstance(row.get("after"), dict) \
        and re.fullmatch(r"[a-z0-9-]+", str(row.get("laid", slug))) is not None
    return row if ok else None


def undo(root: Path, state_dir: Path, slug: str, publish: Callable[..., None] | None = None, kind: str = "", party: bool = False) -> dict:
    """The last one-press move of a goal put back, byte for byte, only while what it changed is still as the move left it. ValueError in plain words
    where there is nothing to undo or the goal changed since (nothing is written then)."""
    with ideas.LOCK:
        row = read(state_dir, slug, party)
        if row is None or (kind and row["kind"] != kind):
            raise ValueError(NOTHING)
        whose = row.get("laid") or slug                          # the goal whose page and state the move changed: `slug`, or the one it laid
        now, files = snapshot(root, state_dir, whose, party), _files(root, state_dir, whose, party)
        names = [n for n in files if row["before"].get(n) != row["after"].get(n)]
        if any(now.get(n) != row["after"].get(n) for n in names):
            raise ValueError(CHANGED_SINCE)
        for n in names:
            if row["before"].get(n) is None:
                files[n].unlink(missing_ok=True)
                if n == "state":                                   # a goal the move laid leaves no folder of its state behind
                    try:
                        files[n].parent.rmdir()
                    except OSError:
                        pass
            else:
                ideas._write(files[n], row["before"][n])
        ideas._reindex(Path(root))
        record_path(state_dir, slug, party).unlink(missing_ok=True)
    if publish is not None:
        publish(bus.MOVE_UNDONE, idea=slug, kind=row["kind"])
    return {"kind": row["kind"]}
