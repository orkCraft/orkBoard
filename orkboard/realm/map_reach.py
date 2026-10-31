"""The two rules every leader's map gains (docs/specs/117-each-lens-a-games-shape.md §1; decisions §195): the **heat** code finds on a part (`map_signals`' hints, by part) and the **reach** of a goal before
it starts (the parts its section's *Will be* and its marks name, and how far a change of them spreads by the map's own relation). Read from the files, the Board and git; no model, no face; nothing is written.

    map_reach.heat(state_dir, root, craft, pages=None, ref="dev")             # {part id: [{kind, aspect, words}]}: every hint with an `on`, three a part at most, in `map_signals`' order; {} for none
    map_reach.relation(state_dir, root, craft, pages=None, ref="dev", only=()) # {part id: [part id]}: what a change of a part reaches one step out; {} for a map with none
    map_reach.reach(rel, touched)                                             # {id: 0 | 1 | 2}: the touched 0, one step 1, two steps 2, no further; the nearest wins
    map_reach.touched(state_dir, root, slug, party, craft, pages, ref="dev")  # {state: "ok" | "no_will" | "none", ids}: the map's part ids a goal changes
    map_reach.guard(state_dir, root, ids, ref="dev")                          # System's: {id: True when a test is mapped to the part (`map_signals.tested`)}
    map_reach.links(state_dir, root, ids, ref="dev")                          # System's: [[from, to]], the architecture's links whose two containers both hold one of `ids`

`root` is the project's repository, `pages` where the Board's pages are (`ideas.idea_page`). The relation by map (`map_parts.MAPS`' ids), directed as a change spreads:
- `system`: a part reaches what uses it (`used_by` of the newest snapshot, `project_map`).  `screens`: a screen reaches the screens that link to it (`screen_map`'s links).
- `product`: a job reaches its goals, a goal its job and its experiments, an experiment its goal (`opportunity_tree`).
- `game-design`: a step reaches the next step of its loop (the last the first) and `cur:<id>` of each currency it gives; a currency each step that takes it (`loop`).
- `release`: a goal reaches the goals `goal_main.plan` takes to main with it. It is computed for the goals asked (`only`; none given: for every goal waiting), for each runs git.
- `art`, `marketing`: none.

A map that cannot be read has no heat and no relation, never an error for a caller. Heat of `tech`, `art` and `marketing` (hints that are a function of dev's head) is kept per
(project, craft, head), `CACHE_MAX` entries, since a read runs git; the other crafts' hints read the Board and the state too, so they are read again.
"""
from __future__ import annotations

import copy
import threading
from pathlib import Path
from typing import Iterable

from orkboard.realm import commit_goal, gate_config, goal_main, ideas, lens_rubrics, loop, map_parts, map_signals, opportunity_tree, project_map, release_map, screen_map, spec_sections, system_overview

PER_PART = 3                                  # the hints kept on a part
CACHE_MAX = 8
KEPT = ("tech", "art", "marketing")           # the crafts whose hints depend on the ref's head alone
_LOCK = threading.Lock()
_CACHE: dict[tuple[str, str, str, str], dict] = {}


# -- heat -----------------------------------------------------------------------------------------------------------------------------

def _group(craft: str, rows: list[dict]) -> dict[str, list[dict]]:
    map_id = map_parts.MAPS.get(craft, "")
    out: dict[str, list[dict]] = {}
    for h in rows:
        on = h.get("on") or ""
        if not on or h.get("map", map_id) != map_id:                  # a hint of no part, or of a part of another map (a pain piled on a screen): not drawn here
            continue
        mine = out.setdefault(on, [])
        if len(mine) < PER_PART:
            mine.append({"kind": h["kind"], "aspect": lens_rubrics.aspect_of(craft, h["kind"]), "words": h["words"]})
    return out


def heat(state_dir: Path, root: Path, craft: str, pages: Path | None = None, ref: str = "dev") -> dict[str, list[dict]]:
    """The hints of `craft`'s map by part (see the module): `{part id: [{kind, aspect, words}]}`."""
    state_dir, root = Path(state_dir), Path(root)
    head = commit_goal.head(root, ref) if craft in KEPT else ""
    key = (str(state_dir), str(root), craft, head)
    with _LOCK:
        if head and key in _CACHE:
            return copy.deepcopy(_CACHE[key])
    got = _group(craft, map_signals.signals(state_dir, root, craft, pages, ref, limit=None))
    if head:
        with _LOCK:
            _CACHE[key] = got
            while len(_CACHE) > CACHE_MAX:
                _CACHE.pop(next(iter(_CACHE)))
    return copy.deepcopy(got)


# -- the relation -----------------------------------------------------------------------------------------------------------------------

def _add(rel: dict[str, list[str]], a: str, b: str) -> None:
    if a != b and b not in rel.setdefault(a, []):
        rel[a].append(b)


def _system(state_dir: Path, root: Path, ref: str) -> dict[str, list[str]]:
    snap = project_map.ensure(state_dir, root, ref)
    by = {p["path"]: p for p in (snap or {}).get("parts") or [] if isinstance(p, dict) and p.get("path")}
    rel: dict[str, list[str]] = {}
    for path, p in by.items():
        for user in p.get("used_by") or []:
            if user in by:
                _add(rel, path, user)
    return rel


def _screens(state_dir: Path, root: Path) -> dict[str, list[str]]:
    got = screen_map.read(state_dir, root)
    ids = {s["id"] for s in got.get("screens") or []}
    rel: dict[str, list[str]] = {}
    for k in got.get("links") or []:
        if k["from"] in ids and k["to"] in ids:
            _add(rel, k["to"], k["from"])
    return rel


def _product(state_dir: Path, pages: Path | None) -> dict[str, list[str]]:
    rec = opportunity_tree.read(state_dir)
    have = set(opportunity_tree.goals(state_dir, Path(pages))) if pages is not None else None         # a goal the Board dropped is no part

    def ok(goal: str) -> bool:
        return have is None or goal in have

    rel: dict[str, list[str]] = {}
    for s in rec["serves"]:
        if ok(s["goal"]):
            _add(rel, s["job"], s["goal"])
            _add(rel, s["goal"], s["job"])
    for t in rec["tests"]:
        if ok(t["goal"]) and ok(t["experiment"]):
            _add(rel, t["goal"], t["experiment"])
            _add(rel, t["experiment"], t["goal"])
    return rel


def _game(state_dir: Path) -> dict[str, list[str]]:
    rel: dict[str, list[str]] = {}
    takers: dict[str, list[str]] = {}
    for lp in loop.read(state_dir).get("loops") or []:
        steps = lp.get("steps") or []
        for n, st in enumerate(steps):
            _add(rel, st["id"], steps[(n + 1) % len(steps)]["id"])              # the ring closes: the last step reaches the first
            for c in st.get("gives") or []:
                _add(rel, st["id"], f"cur:{c}")
            for c in st.get("takes") or []:
                takers.setdefault(c, []).append(st["id"])
    for c, steps_ in takers.items():
        for sid in steps_:
            _add(rel, f"cur:{c}", sid)
    return rel


def _release(state_dir: Path, root: Path, pages: Path | None, ref: str, only: Iterable[str]) -> dict[str, list[str]]:
    slugs = list(only) or [g["idea"] for g in release_map.read(state_dir, root, pages, ref)["goals"]]
    rel: dict[str, list[str]] = {}
    for slug in slugs:
        try:
            goals = goal_main.plan(root, state_dir, slug, root=pages, into=ref, pick=False)["goals"]
        except Exception:                                    # a goal git cannot plan reaches nothing
            continue
        for g in goals[1:]:
            _add(rel, slug, g)
    return rel


def relation(state_dir: Path, root: Path, craft: str, pages: Path | None = None, ref: str = "dev", only: Iterable[str] = ()) -> dict[str, list[str]]:
    """What a change of a part reaches one step out (see the module): `{part id: [part id]}`. `only`: Release's goals to compute it for."""
    state_dir, root = Path(state_dir), Path(root)
    try:
        return {"tech": lambda: _system(state_dir, root, ref), "design": lambda: _screens(state_dir, root), "product": lambda: _product(state_dir, pages),
                "game-design": lambda: _game(state_dir), "release": lambda: _release(state_dir, root, pages, ref, only)}.get(craft, lambda: {})()
    except Exception:                                        # a relation that cannot be read is none, never an error for a caller
        return {}


def reach(rel: dict[str, list[str]], touched: Iterable[str]) -> dict[str, int]:
    """`{id: 0 | 1 | 2}`: the touched ids 0, what they reach one step out 1, two steps 2, nothing further; a part nearest wins."""
    near = {t: 0 for t in touched}
    edge = list(near)
    for step in (1, 2):
        nxt = []
        for a in edge:
            for b in rel.get(a, []):
                if b not in near:
                    near[b] = step
                    nxt.append(b)
        edge = nxt
    return near


# -- touched ----------------------------------------------------------------------------------------------------------------------------

def _matches(will: str, ids: list[str]) -> list[str]:
    """The parts a *Will be* id names: the part it is, holds or lies in (`spec_sections.same_part`). The top part (".") holds only the files at the project's top, and is itself."""
    w = will.strip("/") or "."
    if w == ".":
        return ["."] if "." in ids else []
    got = [i for i in ids if i != "." and spec_sections.same_part(w, i)]
    return got or (["."] if "/" not in w and "." in ids else [])


def touched(state_dir: Path, root: Path, slug: str, party: str, craft: str, pages: Path, ref: str = "dev") -> dict:
    """`{state, ids}`: the part ids of `craft`'s map the goal `slug` changes for `party` (see the module). `state`: `ok` with ids; `no_will` when the party has a section and no *Will be* line
    matched and no mark; `none` when the goal has no section for the party and no mark on the map (for Release: when the goal does not wait in `ref`)."""
    state_dir, root, pages = Path(state_dir), Path(root), Path(pages)
    map_id = map_parts.MAPS.get(craft, "")
    page = ideas.idea_page(pages, slug)
    if not map_id or page is None:
        return {"state": "none", "ids": []}
    parts = map_parts.parts(state_dir, root, craft, pages, ref)
    if map_id == "release":
        return {"state": "ok", "ids": [slug]} if any(p["id"] == slug for p in parts) else {"state": "none", "ids": []}
    ids = [p["id"] for p in parts]
    tracks = [{"slug": t["slug"], "title": t["title"]} for t in ideas.tracks(pages, make=False)]
    mine = [s for s in spec_sections.read(page, tracks, page.get("track") or ideas.GENERAL)["sections"] if s.party == party]
    hit: set[str] = set()
    for s in mine:
        for w in spec_sections.will_be(s.parts.get("Will be", "")):
            hit.update(_matches(w["id"], ids))
    for m in ideas.state(state_dir, slug).get("marks") or []:
        if not isinstance(m, dict) or m.get("map") != map_id:
            continue
        if m.get("id"):
            hit.add(m["id"])
        elif m.get("group"):                                 # a whole group of the map
            hit.update(p["id"] for p in parts if p.get("group") == m["group"])
    found = [i for i in ids if i in hit]
    return {"state": "ok" if found else "no_will" if mine else "none", "ids": found}


# -- System: what checks a part, which links a reach crosses ---------------------------------------------------------------------------

def guard(state_dir: Path, root: Path, ids: Iterable[str], ref: str = "dev") -> dict[str, bool]:
    """System's `{id: True when a test is mapped to the part}` (`map_signals.tested`); False for an id that is no part of the newest snapshot."""
    state_dir, root = Path(state_dir), Path(root)
    ids = list(ids)
    try:
        snap = project_map.ensure(state_dir, root, ref)
        by = {p["path"]: p for p in (snap or {}).get("parts") or [] if isinstance(p, dict) and p.get("path")}
        if not by or not ids:
            return {i: False for i in ids}
        got = commit_goal.git(root, "ls-tree", "-r", "--name-only", snap["commit"])
        tracked = {p for p in got.stdout.splitlines() if p} if got.returncode == 0 else set()
        gate = gate_config.read(root)
        return {i: i in by and map_signals.tested(i, list(by[i].get("files") or []), tracked, gate, root) for i in ids}
    except Exception:
        return {i: False for i in ids}


def links(state_dir: Path, root: Path, ids: Iterable[str], ref: str = "dev") -> list[list[str]]:
    """System's `[[from, to]]`: each link of the architecture (container paths) whose two containers both hold a part among `ids`."""
    try:
        ov = (project_map.ensure(Path(state_dir), Path(root), ref) or {}).get("overview") or {}
        containers = [c["path"] for c in ov.get("containers") or [] if isinstance(c, dict) and c.get("path")]
        held = {system_overview.owner(i, containers) for i in ids}
        return [[k["from"], k["to"]] for k in ov.get("links") or [] if isinstance(k, dict) and k.get("from") in held and k.get("to") in held]
    except Exception:
        return []
