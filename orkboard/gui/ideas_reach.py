"""Heat and reach on the open tab's map (docs/specs/117-each-lens-a-games-shape.md §1.4; decisions §195, realm/map_reach.py), as `gui/ideas.py`'s `Ideas` has them: the commands the maps' faces
paint their cards by. Read by code, no model; nothing is written.

    ideas.heat {party}                 # → {map, parts: {part id: [{kind, aspect, words}]}}: the hints of the party's map by part, three a part at most (`words` is a hint's plain English)
    ideas.reach {party, slug}          # → {map, slug, element, state: "ok" | "no_will" | "none", near: {part id: 0 | 1 | 2}, guard?: {part id: bool}, links?: [[from, to]]}

`near` is what the goal changes (0), what that reaches one step out (1) and two (2), by the map's own relation; `state` says why it is empty (`no_will`: the goal's section for the party names no part of
the map yet, `none`: the goal has no section for the party and no mark on the map). `guard` (whether a test is mapped to the part) and `links` (the architecture's links, as container pairs, whose two
containers both hold a part in `near`) are System's alone. A party with no map answers `map` "" and nothing. An unknown party or goal is refused in plain words. The host returns keys and data,
never interface words. Needs `ConcernsMixin._concern_party` (gui/ideas_concerns.py), `_ref` (gui/ideas_assets.py), `root` and `host` (gui/ideas.py).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from orkboard.gui.ideas_args import IdeasError, _text
from orkboard.realm import idea_element, ideas, map_parts, map_reach

SYSTEM = "system"


class ReachMixin:
    def heat(self, args: dict) -> dict:
        party = self._concern_party(args)
        pages = self.root(False)
        craft = map_parts.craft_of(pages, party)
        map_id = map_parts.MAPS.get(craft, "")
        parts = map_reach.heat(self.state_dir, Path(self.host.repo_root), craft, pages, self._ref()) if map_id else {}
        return {"map": map_id, "parts": parts}

    def reach(self, args: dict) -> dict:
        party = self._concern_party(args)
        slug = _text(args, "slug", 100)
        pages = self.root(False)
        if ideas.idea_page(pages, slug) is None:
            raise IdeasError("That goal is gone")
        repo, ref = Path(self.host.repo_root), self._ref()
        craft = map_parts.craft_of(pages, party)
        map_id = map_parts.MAPS.get(craft, "")
        out = {"map": map_id, "slug": slug, "element": idea_element.of(self.state_dir, slug), "state": "none", "near": {}}
        if not map_id:
            return out
        got = map_reach.touched(self.state_dir, repo, slug, party, craft, pages, ref)
        near = map_reach.reach(map_reach.relation(self.state_dir, repo, craft, pages, ref, only=got["ids"]) if got["ids"] else {}, got["ids"])
        out.update(state=got["state"], near=near)
        if map_id == SYSTEM:
            out.update(guard=map_reach.guard(self.state_dir, repo, near, ref), links=map_reach.links(self.state_dir, repo, near, ref))
        return out


def reach_commands(ideas_: Any) -> dict:
    """Heat and reach by name (`gui/ideas.py` adds them to its table: `**reach_commands(self)`)."""
    return {"ideas.heat": ideas_.heat, "ideas.reach": ideas_.reach}
