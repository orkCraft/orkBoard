"""Reach on the other maps (docs/specs/165-each-leaders-map-a-board-games-shape.md stage D; decisions §280.1), beside `realm/map_reach.py` as `map_signals_crafts` is beside `map_signals`. No face; nothing is written.

    map_reach_crafts.steps_out(lit, links)                              # (one, two): the parts one and two steps out of `lit` by `links` (part -> parts it reaches), none twice, none lit
    map_reach_crafts.reach(state_dir, root, pages, craft, wills, ref)   # {slug: {lit, one, two, no_test}} on `craft`'s map for `wills` ({slug: [the ids its *Will be* names]}); {} for a craft this module has no map for

`lit` are the ids `map_parts.parts` gives the map (the very ones its face stamps): the loop's steps and currencies, the tree's jobs, hypotheses (`hyp:<id>`) and goals, Art's assets, the way in's files. `one` and `two`:
- the loop (Game design): the step before and after in its loop, a loop closing last step to first, then the next out;
- the tree (Product): a job's hypotheses and goals, or a hypothesis' or a goal's job, then the next out;
- Art and the way in (Marketing): none, `lit` only.
`no_test` is always empty off System. Dev and main (Release) is read from the plan kept, not here. A goal that names nothing of the map has no entry; a map that cannot be read gives {}.
"""
from __future__ import annotations

import re
from pathlib import Path

from orkboard.realm import hypotheses, loop, map_parts, opportunity_tree, spec_sections

CRAFTS = ("game-design", "product", "art", "marketing")


def steps_out(lit: set[str], links: dict[str, set[str]]) -> tuple[set[str], set[str]]:
    """The parts one and two steps out of `lit` by `links`, none twice and none lit."""
    one = set().union(*(links.get(p, set()) for p in lit)) - lit if lit else set()
    two = set().union(*(links.get(p, set()) for p in one)) - lit - one if one else set()
    return one, two


def _norm(text: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(text or "").lower())


def _by_id(parts: list[dict], wanted: list[str]) -> set[str]:
    """The parts a *Will be* id names by their id, or their name without case or signs."""
    want = {_norm(w) for w in wanted if _norm(w)}
    return {p["id"] for p in parts if p["id"] in wanted or _norm(p["id"]) in want or _norm(p.get("name")) in want}


def _by_path(parts: list[dict], wanted: list[str]) -> set[str]:
    """The parts whose path a *Will be* id is, or lies inside, or holds."""
    return {p["id"] for p in parts if any(spec_sections.same_part(w, p["id"]) for w in wanted)}


def _loop_links(state_dir: Path) -> dict[str, set[str]]:
    links: dict[str, set[str]] = {}
    for lp in loop.read(Path(state_dir)).get("loops") or []:
        ids = [s["id"] for s in lp.get("steps") or [] if s.get("id")]
        if len(ids) > 1:
            for n, sid in enumerate(ids):
                links.setdefault(sid, set()).update({ids[n - 1], ids[(n + 1) % len(ids)]} - {sid})
    return links


def _tree_links(state_dir: Path, have: set[str]) -> dict[str, set[str]]:
    links: dict[str, set[str]] = {}

    def join(a: str, b: str) -> None:
        if a in have and b in have:
            links.setdefault(a, set()).add(b)
            links.setdefault(b, set()).add(a)
    for h in hypotheses.read(Path(state_dir))["items"]:
        join(f"hyp:{h['id']}", h.get("on") or "")
    for s in opportunity_tree.read(Path(state_dir))["serves"]:
        join(s["goal"], s["job"])
    return links


def reach(state_dir: Path, root: Path, pages: Path | None, craft: str, wills: dict[str, list[str]], ref: str = "dev") -> dict[str, dict]:
    """`{slug: {lit, one, two, no_test}}` on `craft`'s map (see the module); {} for a craft not here or a map that cannot be read, never an error."""
    if craft not in CRAFTS:
        return {}
    try:
        parts = map_parts.parts(Path(state_dir), Path(root), craft, pages, ref)
        if not parts:
            return {}
        have = {p["id"] for p in parts}
        links = _loop_links(state_dir) if craft == "game-design" else _tree_links(state_dir, have) if craft == "product" else {}
        match = _by_id if craft in ("game-design", "product") else _by_path
        out: dict[str, dict] = {}
        for slug, wanted in wills.items():
            lit = match(parts, wanted)
            if lit:
                one, two = steps_out(lit, links)
                out[slug] = {"lit": sorted(lit), "one": sorted(one & have), "two": sorted(two & have), "no_test": []}
        return out
    except Exception:
        return {}
