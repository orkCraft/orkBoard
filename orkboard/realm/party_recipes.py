"""The parties each kind of project is proposed, one craft a party, and their three sizes (docs/specs/99-a-goals-way.md §1, decisions §109.1, §122, §137.1, §151, §158).

    RECIPES["game"]                    # [{id, name, line, leader, build, check, squad, craft, whole, because, when}, …] in the order they are proposed
    for_kind("mobile")                 # a kind's recipes (an unknown kind: code's); General, Team and Ideation are in none
    get("tech")                        # one recipe by its id: a craft's, else one made before (`party_recipes_before`: it keeps its seats and its name); None for none
    craft_of("tech", "architect")      # "tech": the craft of a party (its recipe's, else its leader's); "" for a party with none (the Taskmaster's, Ideation's)
    sized(recipe, "standard")          # {"leader", "team": the squad, "tiers": {…}, "size", "basis": the squad's part a price counts}
    tiers_for("architect", team, "full")   # {agent: tier} a size gives any party's seats (spec 81 §2)
    squad_of(recipe)                   # the seats a recipe ticks by default, at most `goal_team.SEATS`
    routines_of("run", "web")          # "web-liveops": the recipe whose recurring goals a running party proposes (`realm/recurring.py`)
    TEAM                               # the Team party's recipe: never offered nor made, a party the project has stays
    TARGET["lean"]                     # "thrift": the Target a size works at (realm/idea_target.py SIZE_TARGET)
    has(recipe, tracks)                # the project already has this recipe's party

**One craft a party** (§1.1): a game has *Game design*, *Tech*, *Art*, *Release*, *LiveOps* and *Marketing*; an app, a site and any other kind *Product*,
*Design*, *Tech*, *Release*, *Run* and *Marketing* (what it makes, its look, its code, its release, its running, its marketing). A recipe is made of the
library's agents, `build` (who does) and `check` (who checks) most needed first: the craft's roles the person ticks from; `squad` is who is ticked by default
(Release's is its leader alone). The mixed recipes of before are not offered. **The squad and the size are apart** (§1.3): a size never changes the squad; it
sets how a task goes (`goal_team.WAY`) and the seats' tiers by default (`tiers_for`). Which craft is offered at which stage of the project is
`realm/project_stage.py`. No face, no model.
"""
from __future__ import annotations

from orkboard.realm import idea_target, library
from orkboard.realm.party_recipes_before import BEFORE, STAGE_RECIPES, TEAM, TEAM_ID

TARGET = idea_target.SIZE_TARGET
TECH, TECH_LINE = library.TECH, library.TECH_LINE
SIZES = idea_target.SIZES
SQUAD_DOES, SQUAD_CHECKS = 2, 1                     # the default squad: the first two who do and the first who checks (the person ticks the rest)


def _craft(cid: str, name: str, line: str, leader: str, build: list[str], check: list[str], because: str, squad: list[str] | None = None) -> dict:
    """A craft's recipe. `squad`: who is ticked by default (the first two who do and the first who checks when none is given)."""
    got = [*build[:SQUAD_DOES], *check[:SQUAD_CHECKS]] if squad is None else list(squad)
    return {"id": cid, "name": name, "line": line, "leader": leader, "build": build, "check": check, "squad": got, "craft": cid, "whole": False,
            "because": because, "when": ""}


CRAFTS: dict[str, dict] = {r["id"]: r for r in (
    _craft("product", "Product", "Who it is for, what it moves, what it leaves out", "product-manager", ["copywriter", "experimenter"], ["editor"],
           "what it is for comes before how it is built"),
    _craft("game-design", "Game design", "The rules, the loop and the balance, tried on paper and played", "game-designer",
           ["level-designer", "copywriter", "experimenter"], ["playtester"], "a game's idea is shaped before it is built"),
    _craft("design", "Design", "Screens, flows and words on them", "product-designer", ["ui-kit", "artist", "copywriter"], ["accessibility-reviewer"],
           "screens are drawn before they are built"),
    _craft("art", "Art", "Pictures, icons, motion, sounds and music, in one style", "art-director",
           ["artist", "sound-designer", "animator", "composer", "icon-artist"], ["art-reviewer"], "a game needs its pictures and sounds made in one style"),
    _craft("tech", TECH, TECH_LINE, "architect", ["grunt", "tester"], ["reviewer", "security-reviewer"], "the code has parts to keep apart and test"),
    _craft("run", "Run", "Errors and speed, dependencies, what people write", "analyst", ["grunt", "data-engineer", "community"],
           ["data-reviewer", "reviewer"], "what runs is watched and kept up to date"),
    _craft("liveops", "LiveOps", "Events, the numbers of play, what players say, small fixes", "analyst",
           ["data-engineer", "grunt", "community", "copywriter"], ["data-reviewer"], "a game that is out is read by its numbers"),
    _craft("marketing", "Marketing", "Pages, posts and search; the store page and the way people come", "growth",
           ["copywriter", "seo", "aso", "community"], ["editor"], "people come to what is told well"),
    _craft("release", "Release", "A version out: what goes in, its notes, the stores' list", "release-manager",
           ["release-engineer", "release-notes", "aso"], ["release-checker"], "a version goes out to people", squad=[]),
)}
APP = ("product", "design", "tech", "release", "run", "marketing")        # what it makes, its look, its code, its release, its running, its marketing
GAME = ("game-design", "tech", "art", "release", "liveops", "marketing")
RECIPES: dict[str, list[dict]] = {kind: [CRAFTS[c] for c in (GAME if kind == "game" else APP)]
                                  for kind in ("empty", "mobile", "web", "backend", "game", "data", "wiki", "design", "texts", "code")}
RELEASE = "release"
ROUTINES = {"run": "{kind}-liveops", "liveops": "game-liveops"}           # the recipe whose recurring goals a running party proposes (realm/recurring.py)
LEADER_CRAFT = {"product-manager": "product", "game-designer": "game-design", "product-designer": "design", "art-director": "art", "architect": "tech",
                "analyst": "run", "growth": "marketing", "release-manager": "release"}      # a party made before spec 99 has its leader's craft


def craft_of(recipe: str = "", leader: str = "") -> str:
    """The craft of a party (`roles.PARTY_RACES` has its races): its recipe's when it is a craft's, else its leader's; "" for a party of the Taskmaster's or
    Ideation's (the Investor), whose seats wear their roles' own heads."""
    return recipe if recipe in CRAFTS else "" if recipe == TEAM_ID else LEADER_CRAFT.get(leader, "")


def is_release(track: dict) -> bool:
    """Whether a party of `ideas.tracks` is the Release party (§137.1): the one way into main, in every project; it is never dropped."""
    return track.get("recipe") == RELEASE or (track.get("leader") or "") == library.RELEASE_MANAGER


def routines_of(recipe: str, kind: str) -> str:
    """The id whose recurring goals a recipe proposes (`recurring.listed`): *Run*'s are its kind's `<kind>-liveops`, *LiveOps*' a game's; the recipe itself else."""
    return ROUTINES[recipe].format(kind=kind) if recipe in ROUTINES else recipe


def for_kind(kind: str, facts: dict | None = None) -> list[dict]:
    """A kind's recipes in the order they are proposed (an unknown kind: `code`'s); those that wait for a fact (`when`) only when the folder has it (none does today)."""
    rows = RECIPES.get(kind) or RECIPES["code"]
    return [r for r in rows if not r["when"] or (facts or {}).get(r["when"])]


def is_team(track: dict) -> bool:
    """Whether a party of `ideas.tracks` is the Team party: it holds the person's Operations, not goals (spec 92 §3). Never made since decisions §122.2."""
    return track.get("recipe") == TEAM_ID


def get(recipe_id: str) -> dict | None:
    """A recipe by id: a craft's, else one of before (the Team party's, a kind's of before, a stage's)."""
    if recipe_id in CRAFTS:
        return CRAFTS[recipe_id]
    if recipe_id == TEAM_ID:
        return TEAM
    return next((r for rows in (*BEFORE.values(), *STAGE_RECIPES.values()) for r in rows if r["id"] == recipe_id), None)


def kind_of(recipe_id: str, prefer: str = "") -> str:
    """The kind a recipe is proposed to: `prefer`'s when it has it (the project's own), else the first that has it; "" for none."""
    def has_it(kind: str) -> bool:
        return any(r["id"] == recipe_id for r in (*RECIPES.get(kind, ()), *BEFORE.get(kind, ()), *STAGE_RECIPES.get(kind, ())))
    return prefer if has_it(prefer) else next((k for k in (*RECIPES, *BEFORE) if has_it(k)), "")


def squad_of(recipe: dict) -> list[str]:
    """The seats a recipe ticks by default: its `squad`; a recipe of before has the first two who do and the first who checks."""
    got = recipe.get("squad")
    return list(got) if got is not None else [*recipe["build"][:SQUAD_DOES], *recipe["check"][:SQUAD_CHECKS]]


def tiers_for(leader: str, team: list[str], size: str) -> dict[str, str]:
    """`{agent: tier}` a size gives a party's seats (spec 81 §2), for any leader and team: **lean** every seat Seasoned (`warrior`);
    **standard** the leader Veteran (`elder`), the first who does Seasoned, the other seats as the library has them (no entry); **full** the
    leader and the checkers Veteran, those who do Seasoned (spec 87 §5): none below Seasoned. The Taskmaster
    (no leader picked) is no seat. Release's leader alone is Seasoned at every size (§151.6: the cheaper tier)."""
    from orkboard.realm import goal_team
    build = [s for s in team if goal_team.band_of(s) == "build"]
    check = [s for s in team if goal_team.band_of(s) == "check"]
    lead = [] if leader in ("", "taskmaster") else [leader]
    if size == "lean" or leader == library.RELEASE_MANAGER and not team:
        return {s: "warrior" for s in [*lead, *team]}
    if size == "standard":
        return {**{s: "elder" for s in lead}, **{s: "warrior" for s in build[:1]}}
    return {**{s: "elder" for s in lead}, **{s: "warrior" for s in build}, **{s: "elder" for s in check}}


def sized(recipe: dict, size: str) -> dict:
    """`{"leader", "team", "tiers", "size", "basis"}` of a recipe in a size (§1.3): `team` is its squad, **the same in every size**; the size sets the tiers
    (`tiers_for`) and how a task goes (`goal_team.WAY`); `basis` is the part of the squad a price counts (`goal_team.price_team`). ValueError for a size that
    is not lean, standard or full."""
    from orkboard.realm import goal_team
    if size not in SIZES:
        raise ValueError(f"No size {size!r}: lean, standard or full")
    team = squad_of(recipe)
    return {"leader": recipe["leader"], "team": team, "tiers": tiers_for(recipe["leader"], team, size), "size": size,
            "basis": goal_team.price_team(size, team)}


def has(recipe: dict, tracks: list[dict]) -> bool:
    """The project has the recipe's party already: a party of that recipe (kept on its page), else, when it was made from no other craft's, one with the recipe's
    leader and its squad inside its team (a party made before spec 99 is its leader's craft)."""
    want = set(squad_of(recipe))
    return any(t.get("recipe") == recipe["id"] or (t.get("recipe") not in CRAFTS and (t.get("leader") or "") == recipe["leader"] and want <= set(t.get("team") or []))
               for t in tracks)
