"""What a leader's map shows over its cards, read once per Board change (docs/specs/165-each-leaders-map-a-board-games-shape.md; decisions §280.1, §281.6): heat, the hints code found on each part
(`realm/map_signals.py`), and the memory the host keeps them in. No face; nothing is written to the state.

    map_reach.heat(state_dir, root, craft, pages, ref)    # [{on, kind}]: every hint of the craft's map that sits on one of its parts, uncut (`limit=None`); [] for a craft with no map or a map that cannot be read
    map_reach.Kept()                                      # the host's memory of what was read, per Board rev and dev's head
    kept.track(what, key, uses=("rev", "head"))           # a thing to keep: `what` its kind ("heat"), `key` which one (a craft); `uses` what moves it
    kept.answer(what, key)                                # what was kept, or None; never runs git, never waits
    kept.refresh(rev, read_head, compute)                 # when the Board `rev` moved: reads dev's head once (`read_head()`), then `compute(what, key)` again for each tracked thing the new rev or head changed

A hint with no `on`, or about a part of another map (`map`), is no heat of this map. A refresh whose `compute` fails keeps what it had; it never raises.
"""
from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable

from orkboard.realm import map_parts, map_signals


def heat(state_dir: Path, root: Path, craft: str, pages: Path | None = None, ref: str = "dev") -> list[dict]:
    """The hints of `craft`'s map as heat: `[{on, kind}]`, every one (not cut at MAX_SIGNALS), those on no part or on another map's apart."""
    map_id = map_parts.MAPS.get(craft)
    if map_id is None:
        return []
    rows = map_signals.signals(Path(state_dir), Path(root), craft, pages, ref, limit=None)
    return [{"on": h["on"], "kind": h["kind"]} for h in rows if h.get("on") and h.get("kind") and h.get("map", map_id) == map_id]


class Kept:
    """What the host has read, per Board rev and dev's head. `answer` only looks; `refresh` reads."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._rev: object = None
        self._head: object = None
        self._uses: dict[tuple[str, str], tuple[str, ...]] = {}
        self._data: dict[tuple[str, str], object] = {}

    def track(self, what: str, key: str, uses: tuple[str, ...] = ("rev", "head")) -> None:
        """Keep `what` for `key` from the next refresh on (a thing tracked already keeps its uses)."""
        with self._lock:
            self._uses.setdefault((what, key), tuple(uses))

    def answer(self, what: str, key: str) -> object | None:
        """What was kept for `what` and `key`, or None. No git, no wait."""
        with self._lock:
            return self._data.get((what, key))

    def refresh(self, rev: object, read_head: Callable[[], object], compute: Callable[[str, str], object]) -> list[tuple[str, str]]:
        """Bring what is kept up to `rev`: nothing at all when the rev has not moved (dev's head is not read); else read the head once and compute again what the rev or the head moved. Returns what was computed."""
        with self._lock:
            if rev == self._rev:
                return []
            todo = dict(self._uses)
            old_head = self._head
            first = self._rev is None
            have = set(self._data)
        try:
            head = read_head()
        except Exception:
            head = old_head
        moved = {"rev"} | ({"head"} if first or head != old_head else set())
        done: list[tuple[str, str]] = []
        for k, uses in todo.items():
            if not moved & set(uses) and k in have:
                continue
            try:
                got = compute(*k)
            except Exception:
                continue
            with self._lock:
                self._data[k] = got
            done.append(k)
        with self._lock:
            self._rev, self._head = rev, head
        return done
