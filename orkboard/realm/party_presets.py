"""The parties New party offers (docs/specs/99-a-goals-way.md §1, decisions §122.5, §151.5): the crafts of the project's kind, under the stages that offer them.

    listed("game")      # [{id, name, line, group, stage, craft, recipe, whole, leader, build, check, squad, size, locked, sizes, routines, ops, blocked}, …]

One row a craft of the kind (`party_recipes.for_kind`: a game's Game design, Tech, Art, Release, LiveOps and Marketing; the rest's Product, Design, Tech, Release, Run and
Marketing), `group` "stage" and `stage` the stage that offers it (`project_stage.FROM`: `idea`, `being_made` or `live`; a face grouping them under the stages' headings
ticks the stages the project has reached), then the person's own (`group` "own": the Taskmaster alone). A row says its leader, the roles to tick from (`build`
who do, `check` who check, most needed first), `squad` who is ticked by default, `size` the size it is proposed in, and `sizes`: `lean` · `standard` · `full` →
`{leader, team, tiers, size, basis}` as `party_recipes.sized` gives them: **the same team in every size** (the squad and the size are apart), so the dialog shows the
tiers of a size before anything is saved. `recipe` is the id the party keeps (`goal_team.recipe_of`). `locked`: Release, ticked and never unticked (§137.1).
`routines`: the recurring goals the running party proposes when it is made (`realm/recurring.py`; Run's are its kind's, LiveOps' a game's). General, Team and Ideation
are not offered (decisions §122); `team_at` and `ops` are kept for the host's call and say nothing now. No face, no model, no write.
"""
from __future__ import annotations

from orkboard.realm import idea_target, library, party_recipes, project_stage, recurring

OWN = {"id": "mixed", "name": "Your own party", "line": "Start from the Taskmaster and add who you need"}


def _row(rid: str, name: str, line: str, group: str, leader: str, build: list[str], check: list[str], stage: str = "", craft: str = "",
         recipe: str = "", squad: list[str] | None = None, size: str = "", locked: bool = False, routines: str = "") -> dict:
    asked = {"leader": leader, "build": list(build), "check": list(check), "squad": list(squad or [])}
    return {"id": rid, "name": name, "line": line, "group": group, "stage": stage, "craft": craft, "recipe": recipe, "whole": False,
            "leader": leader, "build": list(build), "check": list(check), "squad": list(squad or []), "size": size, "locked": locked,
            "routines": recurring.listed(routines or recipe), "ops": False, "blocked": "",
            "sizes": {s: party_recipes.sized(asked, s) for s in idea_target.SIZES}}


def team_words(team_at: str) -> str:
    """Why Team is not made: "" with no Team party (`team_at` ""), *Team is in this project* ("here"), else *Team is in <project>*. A Team party the project has stays."""
    return "" if not team_at else "Team is in this project" if team_at == "here" else f"Team is in {team_at}"


def listed(kind: str = "code", team_at: str = "", ops: bool = True) -> list[dict]:
    """The rows of New party's left half for a kind of project, in the order they are shown: the kind's crafts, then the person's own."""
    out = [_row(r["id"], r["name"], r["line"], "stage", r["leader"], r["build"], r["check"], stage=project_stage.FROM[r["id"]], craft=_craft_of(r["leader"]),
                recipe=r["id"], squad=party_recipes.squad_of(r), size=project_stage.SIZE[r["id"]], locked=r["id"] == party_recipes.RELEASE,
                routines=party_recipes.routines_of(r["id"], kind)) for r in party_recipes.for_kind(kind)]
    out.append(_row(OWN["id"], OWN["name"], OWN["line"], "own", "taskmaster", [], [], craft="mixed"))
    return out


def _craft_of(leader: str) -> str:
    a = library.get(leader)
    return a.craft if a is not None else "engineering"
