"""What a party's map draws, card by card (docs/specs/108-a-leader-says-no-and-shows-where-it-hurts.md §2.1; spec 102 §6; decisions §183.4): the parts a person can press, pick, and a leader can
say is wrong, with the very ids the maps' faces stamp as `data-pick-map` and `data-pick-id` (`js/table/picking.js`). Read by code, no model, no face.

    map_parts.parts(state_dir, root, craft)                    # [{map, id, name, group?}], in the order the map draws them; [] for a craft with no map or a map with nothing yet
    map_parts.parts(state_dir, root, craft, pages=pages)       # `pages`: where the Board's pages are, for the goals Product's and Release's maps hold
    map_parts.craft_of(pages, party)                           # the map's craft of a party (a party the Architect leads is Tech's): "tech" · "design" · "game-design" · "product" · "art" · "release" · "marketing", else its craft or ""
    map_parts.loop_parts(state_dir)                            # Game design's alone: {id, name, group}

`craft` is the party's craft, as `realm/map_text.py` `of` takes it. The maps and where their ids come from (each as the face's own module stamps it):
- Tech, `system`: a part's path is its id and its name (`syspane.js`), from the snapshot of the ref's head; its group the container it lies in.
- Design, `screens`: each step `step:<n>` named *Step n* (`screensmap.js`), then each screen by its id (`screenparts.js`), its group the step it lies in.
- Game design, `game-design`: every loop's steps by their id (group `loop`), then every currency `cur:<id>` (group `economy`) (`loopparts.js`).
- Product, `product`: each job by its id, named by its want (group `jobs`), then each hypothesis `hyp:<id>` named by its text, proposed ones too (group `hypotheses`, spec 116 E; in the order the tree draws them:
  the row under the outcome, then each job's), then each goal the tree names that the Board still has, by its slug and title (group `goals`) (`treemap.js`).
- Art, `art`: each asset by its path (group its kind) (`artmap.js`).
- Release, `release`: each goal waiting for main by its slug and title (group the branch it waits in) (`releasemap.js`).
- Marketing, `marketing`: each file of the way in by its path, named by its file's name (group its step) (`waymap.js`).
A map that cannot be read is `[]`: a part is never a reason for a call to fail.
"""
from __future__ import annotations

from pathlib import Path

from orkboard.realm import art_map, goal_team, hypotheses, loop, opportunity_tree, project_map, release_map, screen_map, system_overview, way_map

ARCHITECT = "architect"
MAPS = {"tech": "system", "design": "screens", "game-design": "game-design", "product": "product", "art": "art", "release": "release", "marketing": "marketing"}
MAX_PARTS = 400                                  # the most parts of one map (System's and the assets' can be many)


def craft_of(pages: Path, party: str) -> str:
    """The craft whose map a party shows: a party the Architect leads is Tech's (as the System's face reads it), else the party's craft (`goal_team.craft_of`)."""
    return "tech" if goal_team.leader_of(pages, party) == ARCHITECT else goal_team.craft_of(pages, party)


def loop_parts(state_dir: Path) -> list[dict]:
    """The loop's parts as its map stamps them (`table/loopparts.js`): every loop's steps (their `id`, group `loop`), then every currency (`cur:<id>`, group `economy`), read through
    `loop.read`, so a first version reads as its one core loop. `{id, name, group}`."""
    got = loop.read(Path(state_dir))
    out = [{"id": st["id"], "name": st["name"], "group": "loop"} for lp in got.get("loops") or [] for st in lp.get("steps") or [] if st.get("id") and st.get("name")]
    return out + [{"id": f"cur:{c['id']}", "name": c["name"], "group": "economy"} for c in got.get("currencies") or [] if c.get("id") and c.get("name")]


def _system(state_dir: Path, root: Path, ref: str) -> list[dict]:
    snap = project_map.ensure(Path(state_dir), Path(root), ref)
    parts = [p["path"] for p in (snap or {}).get("parts") or [] if isinstance(p, dict) and p.get("path")]
    containers = [c["path"] for c in ((snap or {}).get("overview") or {}).get("containers") or [] if isinstance(c, dict) and c.get("path")]
    return [{"id": p, "name": p, **({"group": g} if (g := system_overview.owner(p, containers)) else {})} for p in parts]


def screens_of(got: dict) -> list[dict]:
    """Design's parts of a screen map already read (`screen_map.read`): the steps, then the screens, each in the step it lies in."""
    step_of = {sid: screen_map.step_id(n) for n, row in enumerate(got.get("steps") or [], 1) for sid in row}
    steps = [{"id": screen_map.step_id(n), "name": f"Step {n}"} for n in range(1, len(got.get("steps") or []) + 1)]
    return steps + [{"id": s["id"], "name": s["name"], **({"group": step_of[s["id"]]} if s["id"] in step_of else {})} for s in got.get("screens") or []]


def _product(state_dir: Path, pages: Path | None) -> list[dict]:
    rec = opportunity_tree.read(Path(state_dir))
    out = [{"id": j["id"], "name": j["want"], "group": "jobs"} for j in rec["jobs"]]
    items, jobs = hypotheses.read(Path(state_dir))["items"], [j["id"] for j in rec["jobs"]]
    out += [{"id": f"hyp:{h['id']}", "name": h["text"], "group": "hypotheses"} for h in [*(h for h in items if h["on"] not in jobs), *(h for j in jobs for h in items if h["on"] == j)]]     # as treemap.js draws them
    if pages is not None:
        out += [{"id": g["slug"], "name": g["title"], "group": "goals"} for g in opportunity_tree.goals(Path(state_dir), Path(pages)).values()]
    return out


def _art(state_dir: Path, root: Path, ref: str) -> list[dict]:
    return [{"id": a["id"], "name": a["name"], "group": k["kind"]} for k in art_map.read(Path(state_dir), Path(root), ref=ref)["kinds"] for a in k["assets"]]


def _release(state_dir: Path, root: Path, pages: Path | None) -> list[dict]:
    got = release_map.read(Path(state_dir), Path(root), pages)
    return [{"id": g["idea"], "name": g["title"], "group": got["into"]} for g in got["goals"]]


def _marketing(state_dir: Path, root: Path, ref: str) -> list[dict]:
    got = way_map.read(Path(state_dir), Path(root), ref)
    return [{"id": h["path"], "name": h["path"].rsplit("/", 1)[-1], "group": step} for step in got["steps"] for h in (got.get(step) or {}).get("holds") or []]


def parts(state_dir: Path, root: Path, craft: str, pages: Path | None = None, ref: str = "dev") -> list[dict]:
    """The parts of the map of `craft`'s party: `[{map, id, name, group?}]` (see the module), at most MAX_PARTS; [] for a craft with no map and for a map that cannot be read."""
    map_id = MAPS.get(craft)
    if map_id is None:
        return []
    state_dir, root = Path(state_dir), Path(root)
    try:
        rows = {"tech": lambda: _system(state_dir, root, ref),
                "design": lambda: screens_of(screen_map.read(state_dir, root)),
                "game-design": lambda: loop_parts(state_dir),
                "product": lambda: _product(state_dir, pages),
                "art": lambda: _art(state_dir, root, ref),
                "release": lambda: _release(state_dir, root, pages),
                "marketing": lambda: _marketing(state_dir, root, ref)}[craft]()
    except Exception:                            # a map that cannot be read has no parts, never an error for a caller
        return []
    return [{"map": map_id, **r} for r in rows[:MAX_PARTS]]
