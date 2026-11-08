"""The heroes (docs/specs/157-the-inventory-a-merchants-stall.md §A; decisions §266.3, §267.2): the school a party's leader looks by, one set each. No face, no model.

    HEROES                          # {id: Hero} in the spec's order: eleven, one default a craft (Release Night King is Release's, fixed)
    of("tech")                      # the heroes of a craft, in order
    get("sh-xp")                    # one hero by its id; None for none
    default("tech")                 # the craft's default hero (the one whose frame is `lens_rubrics.RUBRICS[craft]`); None for a craft with none

A hero's `places` are its frame's places, `(name, ask)` a place, one plain question each; a default hero has none (its craft's map is its table). Its `framework`, `short` and
`aspects` are the school's, written here; **a default hero's are its craft's rubric, read at call time** (`lens_rubrics.RUBRICS[craft]`, never copied). The aspects of a hero
that is not a default carry no `signals`: code's hints stay with the craft's default rubric. `decides` and `says_no` run 1-3 (asks -> itself, seldom -> often).
"""
from __future__ import annotations

from dataclasses import dataclass

from orkboard.realm.seat_hero_rules import SIZES, LAYOUTS, _FRAME, CUT, Hero, _p, _a, _default, HEROES, of, get, default


def head(hero: Hero) -> dict:
    """The head that draws a hero, `{race, tier}`: orkUI's `hero-<id>` when its copy has the file (spec 157 B), else its craft's leader race at the elder tier."""
    from orkboard.realm import roles
    if (roles.RACE_FILES / f"hero-{hero.id}-elder.png").is_file():
        return {"race": f"hero-{hero.id}", "tier": "elder"}
    return {"race": roles.party_race(hero.craft, True, "elder"), "tier": "elder"}
