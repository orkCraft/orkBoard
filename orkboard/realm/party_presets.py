"""The presets New party offers (docs/specs/91-the-owners-list.md §7, decisions §107.5): the left half of its dialog.

    listed("game")      # [{id, name, line, group, stage, craft, recipe, whole, leader, build, check, sizes, routines, ops, blocked}, …]

Three groups: **stage** (*By stage of the project*: Ideation, Concept, Build, Release, LiveOps, fitted to the project's kind: `party_recipes.stages_of`),
**craft** (*By craft*: Tech, Design, Data, Marketing, Product, and Art and sound: the library's parties of one craft) and **own** (*Your own party*:
the Taskmaster alone). A row says its leader and the builders and checkers most needed first (`build`, `check`: a party has one seat a stage, so a size seats
the first of each), and `sizes`: `lean` · `standard` · `full` → `{leader, team, tiers, size}` as `party_recipes.sized` gives them, so the dialog shows the seats and
the tiers of a size before anything is saved. `recipe` is the id the party keeps (`goal_team.recipe_of`) when it is made from the row, "" for a craft's. `whole`: Ideation
and Release (their seats are their stages whole). `routines`: the recurring goals the party proposes when it is made (`realm/recurring.py`; the project's running stage has them, a game's LiveOps
too). **Team** (spec 92 §3) is the last of *By craft* for every kind: `ops` is true, it has no seats to fill, and `blocked` says *Team is in <project>* (or *Team is in this project*) when the person
has one already, for the card to be offered greyed. No face, no model, no write.
"""
from __future__ import annotations

from orkboard.realm import idea_target, library, party_recipes, recurring

OWN = {"id": "mixed", "name": "Your own party", "line": "Start from the Taskmaster and add who you need"}
CRAFTS = ("engineering", "design", "data", "marketing", "product", "art")        # *By craft*, in the order it is shown (the library's ids)


def _row(rid: str, name: str, line: str, group: str, leader: str, build: list[str], check: list[str], stage: str = "", craft: str = "",
         recipe: str = "", whole: bool = False, ops: bool = False, blocked: str = "") -> dict:
    sized = {"leader": leader, "build": list(build), "check": list(check)}
    return {"id": rid, "name": name, "line": line, "group": group, "stage": stage, "craft": craft, "recipe": recipe, "whole": whole,
            "leader": leader, "build": list(build), "check": list(check), "routines": recurring.listed(recipe), "ops": ops, "blocked": blocked,
            "sizes": {size: party_recipes.sized(sized, size) for size in idea_target.SIZES}}


def team_words(team_at: str) -> str:
    """Why Team is not offered: "" with no Team party (`team_at` ""), *Team is in this project* ("here"), else *Team is in <project>*."""
    return "" if not team_at else "Team is in this project" if team_at == "here" else f"Team is in {team_at}"


def listed(kind: str = "code", team_at: str = "") -> list[dict]:
    """The rows of New party's left half for a kind of project, in the order they are shown: the stages, the crafts (Team last), then the person's own.
    `team_at`: where the person's Team party is (`ops_team.where`): "" nowhere, "here", or the other project's name."""
    out = [_row(r["id"], r["name"], r["line"], "stage", r["leader"], r["build"], r["check"], stage=s, craft=_craft_of(r["leader"]),
                recipe=r["id"], whole=r["whole"]) for s, r in zip(party_recipes.STAGES, party_recipes.stages_of(kind))]
    crafts = {p["id"]: p for p in library.presets()}
    for cid in CRAFTS:
        p = crafts[cid]
        out.append(_row(p["id"], p["name"], p["line"], "craft", p["lead"], p["build"], p["check"], craft=p["craft"]))
    t = party_recipes.TEAM
    out.append(_row(t["id"], t["name"], t["line"], "craft", t["leader"], t["build"], t["check"], craft="product", recipe=t["id"], ops=True, blocked=team_words(team_at)))
    out.append(_row(OWN["id"], OWN["name"], OWN["line"], "own", "taskmaster", [], [], craft="mixed"))
    return out


def _craft_of(leader: str) -> str:
    a = library.get(leader)
    return a.craft if a is not None else "engineering"
