"""A party's change of size (docs/specs/81-a-party-its-tool-and-size.md §3, changed by spec 99 §1.3): the size is how the work goes, apart from the squad. A size
sets the seats' tiers and the party's Target; it joins no one and removes no one (`joins` and `leaves` stay for the faces of before, always empty).

    recipe_for("architect", ["grunt", "tester"])         # the recipe a party is of: its kept one, else the one its team fits; None for none
    resized(root, "ship", "lean")                        # {"recipe", "size", "team", "tiers", "joins", "leaves"}: what the size would make of it
    resizes(root, "ship")                                # the same for each size, for the face to show before the press

No face, no model, nothing written: `ideas.goal_save` writes what this says.
"""
from __future__ import annotations

from pathlib import Path

from orkboard.realm import goal_team, idea_target, party_recipes


def recipe_for(leader: str, team: list[str], kept: str = "") -> dict | None:
    """The recipe a party is of: the one its page kept (`recipe`, when its leader is still the party's), else the recipe of its leader whose
    seats hold every member of its team (the most of them first); None for a party of the Taskmaster's, or with no team to tell by."""
    got = party_recipes.get(kept) if kept else None
    if got is not None and got["leader"] == leader:
        return got
    if not team or leader in ("", "taskmaster"):
        return None
    seen, best, most = set(), None, 0
    for rows in party_recipes.RECIPES.values():
        for r in rows:
            if r["id"] in seen or r["leader"] != leader:
                continue
            seen.add(r["id"])
            seats = {*r["build"], *r["check"]}
            have = len(seats & set(team))
            if set(team) <= seats and have > most:
                best, most = r, have
    return best


def resized(root: Path, slug: str, size: str) -> dict:
    """What a party in `size` would have (ValueError for a size that is none): `{"recipe": id or "", "size", "team", "tiers", "joins", "leaves"}`.
    The team is the recipe's size when the party is of one, else the party's own; `joins` / `leaves` are the agents that come or go."""
    if size not in goal_team.SIZES:
        raise ValueError("A size is lean, standard or full")
    leader, team = goal_team.leader_of(root, slug), goal_team.team_of(root, slug)
    recipe = recipe_for(leader, team, goal_team.recipe_of(root, slug))
    new = list(team)                            # the size is how the work goes, apart from the squad (spec 99 §1.3): it joins no one and removes no one
    return {"recipe": recipe["id"] if recipe is not None else "", "size": size, "team": new,
            "tiers": party_recipes.tiers_for(leader, new, size),
            "joins": [s for s in new if s not in team], "leaves": [s for s in team if s not in new]}


def resizes(root: Path, slug: str) -> dict[str, dict]:
    """`resized` for each size: {lean, standard, full}."""
    return {size: resized(root, slug, size) for size in idea_target.SIZES}
