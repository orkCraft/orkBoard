"""What a party's map already has, for the `@` of New goal's field (docs/specs/107-what-the-owners-day-said.md §11.4, decisions §182.13), as `gui/ideas.py`'s `Ideas` has it:

    ideas.pickables {party, q?}      # → {party, map, parts: [{map, id, name, label, group?}]}, at most 30, `q` a subsequence of a part's name or id

A part is what picking takes (docs/specs/102-the-other-maps-and-picking-on-them.md §6): `{map, id, name}` with the very ids the map stamps as `data-pick-map` and
`data-pick-id` (`js/table/picking.js`), so a part taken in the list is the same mark as a card pressed on the map, and sent as one. `label` is what the list shows.
The maps read, as their faces read them (no model, nothing written):
- Tech's System (a party the Architect leads): `system`, a part's path is its id and its name (`syspane.js` `stampParts`), from the snapshot at the merge branch's head;
- Design's screens: `screens`, a screen's id (`screens` of `realm/screen_map.py`) and each step's `step:<n>` named *Step n*;
- Game design's loop: `game-design`, the steps of the loop kept (`loop.json`) and, in a loop of the second version, its loops' steps and its currencies, read defensively.
Another party's map has no parts to offer yet: `parts: []`. The host returns keys and data, never interface words.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from orkboard.gui.ideas_args import IdeasError, _opt, _str
from orkboard.realm import goal_team, ideas, loop, project_map, screen_map

MAX_PARTS = 30
ARCHITECT = "architect"


def _sub(q: str, text: str) -> bool:
    it = iter(text.lower())
    return all(c in it for c in q)


def loop_parts(state_dir: Path) -> list[dict]:
    """The loop's parts as its map stamps them (`table/loopparts.js`): every loop's steps (their `id`, group `loop`), then every currency (`cur:<id>`,
    group `economy`), read through `loop.read`, so a first version reads as its one core loop. `{id, name, group}`."""
    got = loop.read(Path(state_dir))
    out = [{"id": st["id"], "name": st["name"], "group": "loop"} for lp in got.get("loops") or [] for st in lp.get("steps") or [] if st.get("id") and st.get("name")]
    return out + [{"id": f"cur:{c['id']}", "name": c["name"], "group": "economy"} for c in got.get("currencies") or [] if c.get("id") and c.get("name")]


class PickablesMixin:
    """Needs `host`, `state_dir`, `root()` and `_ref()` (gui/ideas_assets.py)."""

    def _party_parts(self, party: str) -> tuple[str, list[dict]]:
        """(the map's id, its parts) of `party`'s map."""
        root = self.root(make=False)
        if goal_team.leader_of(root, party) == ARCHITECT:
            snap = project_map.ensure(self.state_dir, Path(self.host.repo_root), self._ref())
            return "system", [{"id": p["path"], "name": p["path"], "label": p["path"].rsplit("/", 1)[-1] or p["path"]} for p in (snap or {}).get("parts") or [] if p.get("path")]
        craft = goal_team.craft_of(root, party)
        if craft == "design":
            got = screen_map.read(self.state_dir, Path(self.host.repo_root))
            steps = [{"id": screen_map.step_id(n), "name": f"Step {n}", "label": f"Step {n}"} for n in range(1, len(got["steps"]) + 1)]
            return "screens", steps + [{"id": s["id"], "name": s["name"], "label": s["name"]} for s in got["screens"]]
        if craft == "game-design":
            return "game-design", [{**p, "label": p["name"]} for p in loop_parts(self.state_dir)]
        return craft, []

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
