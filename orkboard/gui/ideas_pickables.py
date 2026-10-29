"""What a party's map already has, for the `@` of New goal's field (docs/specs/107-what-the-owners-day-said.md §11.4, decisions §182.13), as `gui/ideas.py`'s `Ideas` has it:

    ideas.pickables {party, q?}      # → {party, map, parts: [{map, id, name, label, group?}]}, at most 30, `q` a subsequence of a part's name or id

A part is what picking takes (docs/specs/102-the-other-maps-and-picking-on-them.md §6): `{map, id, name}` with the very ids the map stamps as `data-pick-map` and
`data-pick-id` (`js/table/picking.js`), so a part taken in the list is the same mark as a card pressed on the map, and sent as one. `label` is what the list shows.
The parts are read by `realm/map_parts.py` (spec 108 §2.1: its logic moved there from here), as the maps' faces stamp them: Tech's System (a party the Architect leads), Design's screens and
steps, Game design's loops' steps and currencies, Product's jobs and goals, Art's assets, Release's goals and Marketing's files of the way in; a party with no map has `parts: []`.
The host returns keys and data, never interface words.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from orkboard.gui.ideas_args import IdeasError, _opt, _str
from orkboard.realm import ideas, map_parts
from orkboard.realm.map_parts import loop_parts  # noqa: F401  (it moved to realm/map_parts.py; the tests read it from here)

MAX_PARTS = 30


def _sub(q: str, text: str) -> bool:
    it = iter(text.lower())
    return all(c in it for c in q)


class PickablesMixin:
    """Needs `host`, `state_dir`, `root()` and `_ref()` (gui/ideas_assets.py)."""

    def _party_parts(self, party: str) -> tuple[str, list[dict]]:
        """(the map's id, its parts) of `party`'s map."""
        root = self.root(make=False)
        craft = map_parts.craft_of(root, party)
        got = map_parts.parts(self.state_dir, Path(self.host.repo_root), craft, root, self._ref())
        label = (lambda p: p["name"].rsplit("/", 1)[-1] or p["name"]) if craft == "tech" else (lambda p: p["name"])        # a System part is shown by its folder's name
        return map_parts.MAPS.get(craft) or craft, [{**{k: v for k, v in p.items() if k != "map"}, "label": label(p)} for p in got]

    def pickables(self, args: dict) -> dict:
        party = _str(args, "party", 100).strip()
        if not party or party not in {t["slug"] for t in ideas.tracks(self.root(make=False), make=False)}:
            raise IdeasError("That party is gone")
        q = _opt(args, "q").lower()[:100]
        map_id, parts = self._party_parts(party)
        shown = [p for p in parts if not q or _sub(q, p["name"]) or _sub(q, p["id"])]
        shown.sort(key=lambda p: (q not in p["name"].lower(), 0))                    # a name that holds it before a spread subsequence (stable: the map's order otherwise)
        return {"party": party, "map": map_id, "parts": [{"map": map_id, **p} for p in shown[:MAX_PARTS]]}


def pickables_commands(ideas_: Any) -> dict:
    """The parts of a party's map by name (`gui/ideas.py` adds them to its table: `**pickables_commands(self)`)."""
    return {"ideas.pickables": ideas_.pickables}
