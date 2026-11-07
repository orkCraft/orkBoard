"""Lay the tables (docs/specs/157-the-inventory-a-merchants-stall.md part F; decisions §267.3-4): the goals that ask each leader to lay its hero's table. No model, no face.

    lay_tables.lay_first(root, state_dir)           # the slug of the goal *Lay the tables* laid, once a project (`tables_laid` of `<state_dir>/project.json`); "" when laid before or nothing to lay
    lay_tables.lay_party(root, state_dir, party)    # the slug of *Lay <party>'s table*; "" for a party with no table to lay, or while a goal of that name waits in line

A table needs what only a leader keeps, and that is a model's pass, the person's money (§57.3): so these goals are only laid, priority low, in `new`, routed to the parties, and wait in line
as any goal. Opening a project, or taking a hero, starts nothing.
"""
from __future__ import annotations

from pathlib import Path

from orkboard.realm import goal_route, goal_team, heroes, ideas

FILE = "project.json"
FIRST = "Lay the tables"
TABLES = "pages/tables"


def _parties(root: Path) -> list[tuple[dict, heroes.Hero]]:
    """The parties with a leader and a hero, in the Board's order: not General, not Release's, none of a craft without a hero."""
    out = []
    for t in ideas.tracks(root, make=False):
        if t["slug"] == ideas.GENERAL or not t.get("leader"):
            continue
        hero = goal_team.hero_of(root, t["slug"])
        if hero is None or hero.craft == "release":
            continue
        out.append((t, hero))
    return out


def _seated(root: Path) -> list[tuple[dict, heroes.Hero]]:
    """The parties whose hero has a frame to lay (§267.2): a craft's default hero lays its craft's map, read from the code, so it has nothing to keep."""
    return [(t, h) for t, h in _parties(root) if not h.default and h.places]


def _where(root: Path) -> str:
    """The folder of the tables from the project's top (`llm-wiki/general/pages/tables`), else from the Board's folder."""
    root = Path(root).resolve()
    for up in root.parents:
        if (up / ".git").exists():
            return f"{root.relative_to(up).as_posix()}/{TABLES}"
    return TABLES


def _frame(hero: heroes.Hero) -> str:
    return ", ".join(name for name, _ask in hero.places)


def _line(party: dict, hero: heroes.Hero) -> str:
    return f"- {party['title']}: {hero.name} ({hero.school}), its places: {_frame(hero)}."


def _rule(root: Path) -> str:
    return (f"Each leader writes its party's table in `{_where(root)}/<party>.md`, its places and their lines as its hero keeps them, every line a thing it read and no number it did not read. "
            "A model's pass is the person's money, so nothing starts by itself: this goal waits in line until the person starts it.")


def _lay(root: Path, state_dir: Path, title: str, body: str, route: list[str]) -> str:
    slug = ideas.add_idea(root, f"{title}\n\n{body}", state_dir=state_dir, priority="low")
    ideas.save_state(state_dir, slug, route=[goal_route.entry(root, p) for p in route])
    return slug


def lay_first(root: Path, state_dir: Path) -> str:
    """*Lay the tables* for every party whose hero has a frame, once. Records `tables_laid` in `<state_dir>/project.json` (its other keys kept), also when
    every hero is its craft's default and nothing is laid: a hero taken later lays its own goal (`lay_party`)."""
    root, state_dir = Path(root), Path(state_dir)
    path = state_dir / FILE
    with ideas.LOCK:
        if (ideas._json(path) or {}).get("tables_laid") is True:
            return ""
        if not _parties(root):
            return ""                                  # no party seated yet: asked again at the next start
        seated = _seated(root)
        if not seated:                                 # every hero its craft's default: its map is read from the code, nothing to lay (§267.2)
            ideas._write_json(path, {**(ideas._json(path) or {}), "tables_laid": True})
            return ""
        body = "Lay each party's table as its hero keeps it:\n\n" + "\n".join(_line(t, h) for t, h in seated) + "\n\n" + _rule(root)
        slug = _lay(root, state_dir, FIRST, body, [t["slug"] for t, _h in seated])
        ideas._write_json(path, {**(ideas._json(path) or {}), "tables_laid": True})
    return slug


def _waits(root: Path, state_dir: Path, title: str) -> bool:
    """A goal of this name is in line: not done."""
    return any(g["title"] == title and ideas.state(state_dir, g["slug"])["state"] != "done" for g in ideas.ideas(root))


def lay_party(root: Path, state_dir: Path, party: str) -> str:
    """*Lay <party>'s table*, routed to that party alone, unless a goal of that name waits in line."""
    root, state_dir = Path(root), Path(state_dir)
    with ideas.LOCK:
        found = [(t, h) for t, h in _seated(root) if t["slug"] == party]
        if not found:
            return ""
        t, hero = found[0]
        title = f"Lay {t['title']}'s table"
        if _waits(root, state_dir, title):
            return ""
        body = f"Lay the table of {t['title']}:\n\n{_line(t, hero)}\n\n{_rule(root)}"
        return _lay(root, state_dir, title, body, [party])
