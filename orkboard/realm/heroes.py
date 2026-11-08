"""The heroes (docs/specs/157-the-inventory-a-merchants-stall.md §A; decisions §266.3, §267.2): the school a party's leader looks by, one set each. No face, no model.

    HEROES                          # {id: Hero} in the spec's order: eighteen, one default a craft but LiveOps's (none until its map) (Release Night King is Release's, fixed)
    of("tech")                      # the heroes of a craft, in order
    get("sh-xp")                    # one hero by its id; None for none
    default("tech")                 # the craft's default hero (the one whose frame is `lens_rubrics.RUBRICS[craft]`); None for a craft with none

A hero's `places` are its frame's places, `(name, ask)` a place, one plain question each; a default hero has none (its craft's map is its table). Its `framework`, `short` and
`aspects` are the school's, written here; **a default hero's are its craft's rubric, read at call time** (`lens_rubrics.RUBRICS[craft]`, never copied). The aspects of a hero
that is not a default carry no `signals`: code's hints stay with the craft's default rubric. `decides` and `says_no` run 1-3 (asks -> itself, seldom -> often).
"""
from __future__ import annotations

from dataclasses import dataclass

from orkboard.realm.seat_hero_rules import SIZES, LAYOUTS, _FRAME, CUT, STARS, sits_at, Hero, _p, _a, _default, HEROES, of, get, default


def head(hero: Hero) -> dict:
    """The head that draws a hero, `{race, tier}`: orkUI's `hero-<id>` when its copy has the file (spec 157 B), else its craft's leader race at the elder tier."""
    from orkboard.realm import roles
    if (roles.RACE_FILES / f"hero-{hero.id}-elder.png").is_file():
        return {"race": f"hero-{hero.id}", "tier": "elder"}
    return {"race": roles.party_race(hero.craft, True, "elder"), "tier": "elder"}


def _kind(root, state_dir) -> str:
    from pathlib import Path
    from orkboard.realm import project_kind
    return str(project_kind.read_full(Path(root), state_dir=Path(state_dir))["kind"])


def offer(root, state_dir, craft: str) -> list[tuple[Hero, str]]:
    """The heroes of a craft in `of`'s order, each with its why: "" where the project's kind offers it, else its `not_here` (decisions §279.5)."""
    kind = _kind(root, state_dir)
    return [(h, "" if not h.kinds or kind in h.kinds else (h.not_here or "Not offered in this project")) for h in of(craft)]


def star(root, state_dir, craft: str) -> str:
    """The id of the hero the Orkmaster's star marks at a craft for the project's kind, "" for a kind with none (it marks a ware, seats nothing: §281.1)."""
    for hid in STARS.get(_kind(root, state_dir), ()):
        h = get(hid)
        if h is not None and sits_at(h, craft):
            return hid
    return ""


def cut_said(root, state_dir, party: str, craft: str) -> str:
    """The line that says a cut hero once (decisions §281.2): where the party's page keeps a hero of `CUT` and `<state>/heroes_cut.json` does not hold it, the record is written and the line returned; "" otherwise.
    The page's `hero` key and the party's table file are never written here."""
    from pathlib import Path
    from orkboard.realm import ideas, lexicon
    page = ideas.track_page(Path(root), party)
    kept = str((page.get("hero") if page is not None else "") or "")
    if kept not in CUT or default(craft) is None:
        return ""
    path = Path(state_dir) / "heroes_cut.json"
    with ideas.LOCK:
        record = ideas._json(path) or {}
        if record.get(party) == kept:
            return ""
        ideas._write_json(path, {**record, party: kept})
    name, why = CUT[kept]
    return f"{name} was cut: {why}. {lexicon.term(f'hero.{default(craft).id}')}, its craft's default, leads now."
