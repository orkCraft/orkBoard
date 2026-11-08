"""What a leader's map shows over its cards, read once per Board change (docs/specs/165-each-leaders-map-a-board-games-shape.md; decisions §280.1, §281.6): heat, the hints code found on each part
(`realm/map_signals.py`), and the memory the host keeps them in. No face; nothing is written to the state.

    map_reach.heat(state_dir, root, craft, pages, ref)    # [{on, kind}]: every hint of the craft's map that sits on one of its parts, uncut (`limit=None`); [] for a craft with no map or a map that cannot be read
    map_reach.reach(state_dir, root, pages, party, craft, ref)  # {slug: {lit, one, two, no_test}}: what each goal not done would change on `craft`'s map (System, Screens), one and two steps out
    map_reach.Kept()                                    # the host's memory of what was read, per Board rev and dev's head
    kept.track(what, key, uses=("rev", "head"))           # a thing to keep: `what` its kind ("heat"), `key` which one (a craft); `uses` what moves it
    kept.answer(what, key)                                # what was kept, or None; never runs git, never waits
    kept.refresh(rev, read_head, compute)                 # when the Board `rev` moved: reads dev's head once (`read_head()`), then `compute(what, key)` again for each tracked thing the new rev or head changed

A goal's reach is read from its section for `party` (`spec_sections`): the parts its *Will be* lines name are `lit`, those they reach by the map's own relation (System: the parts that use a part; Screens:
the links both ways) one step out `one`, the next out `two`, none twice; `no_test` the lit and reached System parts `map_signals.tested` finds no test for. A goal with no *Will be*, one that names nothing of the
map, a map that cannot be read: no entry, never an error.

A hint with no `on`, or about a part of another map (`map`), is no heat of this map. A refresh whose `compute` fails keeps what it had; it never raises.
"""
from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable

import re

from orkboard.realm import gate_config, ideas, map_parts, map_reach_crafts, map_signals, project_map, screen_map, spec_sections


def heat(state_dir: Path, root: Path, craft: str, pages: Path | None = None, ref: str = "dev") -> list[dict]:
    """The hints of `craft`'s map as heat: `[{on, kind}]`, every one (not cut at MAX_SIGNALS), those on no part or on another map's apart."""
    map_id = map_parts.MAPS.get(craft)
    if map_id is None:
        return []
    rows = map_signals.signals(Path(state_dir), Path(root), craft, pages, ref, limit=None)
    return [{"on": h["on"], "kind": h["kind"]} for h in rows if h.get("on") and h.get("kind") and h.get("map", map_id) == map_id]


_out = map_reach_crafts.steps_out


def _system(state_dir: Path, root: Path, ref: str):
    snap = project_map.ensure(Path(state_dir), Path(root), ref)
    by = {p["path"]: p for p in (snap or {}).get("parts") or [] if isinstance(p, dict) and p.get("path")}
    if not by:
        return None
    links = {p: set(v.get("used_by") or []) & set(by) for p, v in by.items()}
    gate, tracked = gate_config.read(Path(root)), set(map_signals._tracked(Path(root), snap["commit"]))

    def no_test(ids: set[str]) -> list[str]:
        return sorted(p for p in ids if not map_signals.tested(p, list(by[p].get("files") or []), tracked, gate, Path(root)))
    return list(by), links, no_test


def _norm(text: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(text or "").lower())


def _screens(root: Path, ref: str):
    got = screen_map.flow(Path(root), ref)
    if not got or not got.get("screens"):
        return None
    links: dict[str, set[str]] = {s["id"]: set() for s in got["screens"]}
    for link in got.get("links") or []:
        a, b = link.get("from"), link.get("to")
        if a in links and b in links:
            links[a].add(b)
            links[b].add(a)
    return got["screens"], links


def _wills(pages: Path, party: str) -> dict[str, list[str]]:
    """`{slug: [ids]}` of every goal not done whose section for `party` has a *Will be* that names something."""
    pages = Path(pages)
    parties = [{"slug": t["slug"], "title": t["title"]} for t in ideas.tracks(pages, make=False)]
    rows, by_slug = ideas.ideas_and_pages(pages)
    out: dict[str, list[str]] = {}
    for row in rows:
        page = by_slug.get(row["slug"])
        if page is None or page.get("phase") == "done":
            continue
        for sec in spec_sections.read(page, parties, row["track"])["sections"]:
            if sec.party == party and not sec.older:
                ids = [w["id"] for w in spec_sections.will_be(sec.parts.get("Will be", ""))]
                if ids:
                    out[row["slug"]] = ids
    return out


def reach(state_dir: Path, root: Path, pages: Path, party: str, craft: str, ref: str = "dev") -> dict[str, dict]:
    """`{slug: {lit, one, two, no_test}}` for every goal not done whose section for `party` has a *Will be* that names a part of `craft`'s map (see the module's doc). Never raises: {} for a map
    that cannot be read or a craft with no reach (the other crafts are `map_reach_crafts`'s; Dev and main's is each goal's plan without its trial pick, read here only in the host's refresh)."""
    try:
        if craft == "release":
            return map_reach_crafts.release_reach(state_dir, root, pages, ref)
        wills = _wills(pages, party)
        if not wills:
            return {}
        if craft in map_reach_crafts.CRAFTS:
            return map_reach_crafts.reach(state_dir, root, pages, craft, wills, ref)
        if craft not in ("tech", "design"):
            return {}
        out: dict[str, dict] = {}
        if craft == "tech":
            system = _system(state_dir, root, ref)
            if system is None:
                return {}
            ids, links, no_test = system
            for slug, wanted in wills.items():
                lit = {p for p in ids if any(spec_sections.same_part(w, p) for w in wanted)}
                if lit:
                    one, two = _out(lit, links)
                    out[slug] = {"lit": sorted(lit), "one": sorted(one), "two": sorted(two), "no_test": no_test(lit | one | two)}
            return out
        got = _screens(root, ref)
        if got is None:
            return {}
        screens, links = got
        for slug, wanted in wills.items():
            lit = {s["id"] for s in screens if any(_norm(w) and _norm(w) in {_norm(s.get("id")), _norm(s.get("name")), _norm(s.get("path"))} for w in wanted)}
            if lit:
                one, two = _out(lit, links)
                out[slug] = {"lit": sorted(lit), "one": sorted(one), "two": sorted(two), "no_test": []}
        return out
    except Exception:
        return {}


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
