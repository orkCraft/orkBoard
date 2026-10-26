"""The parties each kind of project is proposed, and their three sizes (docs/specs/75-parties-fitted-to-the-project.md §2, decisions §90).

    RECIPES["mobile"]                  # [{id, name, line, leader, build, check, whole, because, when}, …] in the order they are proposed
    for_kind("backend", {"sql": 3})    # a kind's recipes, those that wait for a fact (`when`: "sql") left out when the folder lacks it
    get("mobile-features")             # one recipe by its id, from any kind; None for none
    sized(recipe, "standard")          # {"leader": "product-manager", "team": ["grunt", "artist", "reviewer"], "tiers": {…}, "size": "standard"}
    tiers_for("architect", team, "full")   # {agent: tier} a size gives any party's seats (spec 81 §2)
    TARGET["lean"]                     # "thrift": the Target a size works at (realm/idea_target.py SIZE_TARGET)
    has(recipe, tracks)                # the project already has this recipe's party (same leader, the standard team inside its team)

A recipe is made of the library's agents (realm/library.py), `build` and `check` most needed first; a party's seats are its leader's stages, one
agent a stage (`library.seats_of`, spec 87 §5). Its sizes: **lean**, the leader alone (its tasks go to the leader: spec 81); **standard**, the
leader and its first builder; **full**, the leader, its first builder and its first checker; each size also gives its seats their tiers (`tiers`).
A `whole` recipe (Ideation, Release) is sized the same way (spec 81 §2). Ideation, Release, Game and Art and sound are the library's presets, built on their seats.
No face, no model.
"""
from __future__ import annotations

from orkboard.realm import idea_target, library

TARGET = idea_target.SIZE_TARGET
TECH, TECH_LINE = library.TECH, library.TECH_LINE   # the parties the Architect leads (spec 89 §5, decisions §104.1); a party made before keeps its name
SIZES = idea_target.SIZES


def _preset(pid: str, because: str = "", whole: bool = False) -> dict:
    """A recipe on a library preset's seats (`library.PRESETS`)."""
    _i, name, line, _craft, lead, build, check = next(p for p in library.PRESETS if p[0] == pid)
    return {"id": pid, "name": name, "line": line, "leader": lead, "build": list(build), "check": list(check),
            "whole": whole, "because": because, "when": ""}


def _recipe(rid: str, name: str, line: str, leader: str, build: list[str], check: list[str], because: str = "", when: str = "") -> dict:
    return {"id": rid, "name": name, "line": line, "leader": leader, "build": build, "check": check, "whole": False,
            "because": because, "when": when}


def _tech(because: str) -> dict:
    """The Tech party a kind is offered after its first (spec 89 §5): the Architect, a Grunt and the Tester, the Reviewer."""
    return _recipe("tech", TECH, TECH_LINE, "architect", ["grunt", "tester"], ["reviewer"], because)


def _art(because: str) -> dict:
    """The Art and sound party (the Art director, the library's preset): offered after a kind's first party."""
    return _preset("art", because)


def _ideation(because: str = "small ideas are judged before they cost anything") -> dict:
    return _preset("ideation", because, whole=True)


def _release(because: str = "a version goes out to people") -> dict:
    return _preset("release", because, whole=True)


RECIPES: dict[str, list[dict]] = {
    "empty": [_ideation()],
    "mobile": [
        _recipe("mobile-features", "Mobile app: features", "Screens and what people do on them", "product-manager",
                ["grunt", "artist", "aso", "ui-kit"], ["reviewer", "accessibility-reviewer"], "features are the app's daily work"),
        _recipe("mobile-architecture", TECH, TECH_LINE, "architect",
                ["grunt", "tester"], ["reviewer", "security-reviewer"], "the app's structure needs its own hands"),
        _release(),
    ],
    "web": [
        _recipe("web-pages", "Web: pages", "Pages that say what it does, and are found", "product-designer",
                ["grunt", "ui-kit", "copywriter", "seo"], ["reviewer", "accessibility-reviewer"], "pages are the product here"),
        _tech("the site's code has parts to keep apart and test"),
        _release(),
    ],
    "backend": [
        _recipe("backend", TECH, TECH_LINE, "architect",
                ["grunt", "tester"], ["reviewer", "security-reviewer"], "services are built and kept safe"),
        _recipe("backend-data", "Data", "Queries and the numbers they give", "analyst",
                ["data-engineer", "sql", "experimenter"], ["data-reviewer"], "queries are written here", when="sql"),
    ],
    "game": [_preset("game", "a game is built, played and tuned"), _tech("the game's code has parts to keep apart and test"),
             _art("a game needs its pictures and sounds made in one style"), _release()],
    "data": [
        _recipe("data-work", "Data", "Numbers, queries and reports", "analyst",
                ["data-engineer", "sql", "experimenter"], ["data-reviewer"], "the work is numbers and the questions they answer"),
    ],
    "wiki": [
        _recipe("wiki", "Wiki", "Pages the team writes and keeps true", "product-manager",
                ["copywriter"], ["editor"], "pages are written and kept up to date"),
        _ideation(),
    ],
    "design": [
        _recipe("design-screens", "Design", "Screens, pictures and who can use them", "product-designer",
                ["artist", "ui-kit"], ["accessibility-reviewer"], "screens and pictures are made here"),
        _art("a design needs its pictures, icons and sounds made in one style"),
        _ideation(),
    ],
    "texts": [
        _recipe("texts", "Texts", "Words that are written, checked and found", "growth",
                ["copywriter", "seo"], ["editor"], "the work is words"),
        _ideation(),
    ],
    "code": [
        _recipe("engineering-code", TECH, TECH_LINE, "architect",
                ["grunt", "tester"], ["reviewer"], "there is code to change and test"),
    ],
}


def for_kind(kind: str, facts: dict | None = None) -> list[dict]:
    """A kind's recipes in the order they are proposed (an unknown kind: `code`'s); those that wait for a fact (`when`) only when the folder has it."""
    rows = RECIPES.get(kind) or RECIPES["code"]
    return [r for r in rows if not r["when"] or (facts or {}).get(r["when"])]


def get(recipe_id: str) -> dict | None:
    return next((r for rows in RECIPES.values() for r in rows if r["id"] == recipe_id), None)


def kind_of(recipe_id: str, prefer: str = "") -> str:
    """The kind a recipe is proposed to: `prefer`'s when it has it (the project's own), else the first that has it; "" for none."""
    if any(r["id"] == recipe_id for r in RECIPES.get(prefer, ())):
        return prefer
    return next((k for k, rows in RECIPES.items() if any(r["id"] == recipe_id for r in rows)), "")


def tiers_for(leader: str, team: list[str], size: str) -> dict[str, str]:
    """`{agent: tier}` a size gives a party's seats (spec 81 §2), for any leader and team: **lean** every seat Seasoned (`warrior`);
    **standard** the leader Veteran (`elder`), the first builder Seasoned, the other seats as the library has them (no entry); **full** the
    leader and the checkers Veteran, the builders Seasoned (spec 87 §5): none below Seasoned. The Taskmaster
    (no leader picked) is no seat."""
    from orkboard.realm import goal_team
    build = [s for s in team if goal_team.band_of(s) == "build"]
    check = [s for s in team if goal_team.band_of(s) == "check"]
    lead = [] if leader in ("", "taskmaster") else [leader]
    if size == "lean":
        return {s: "warrior" for s in [*lead, *team]}
    if size == "standard":
        return {**{s: "elder" for s in lead}, **{s: "warrior" for s in build[:1]}}
    return {**{s: "elder" for s in lead}, **{s: "warrior" for s in build}, **{s: "elder" for s in check}}


def sized(recipe: dict, size: str) -> dict:
    """`{"leader", "team", "tiers", "size"}` of a recipe in a size (spec 87 §5; `tiers`: `tiers_for`). **lean**: the leader alone, at Seasoned
    (a task with no taker goes to the leader, not the Grunt); **standard**: the leader Veteran and its first builder Seasoned; **full**: the
    leader, its first builder and its first checker, the leader and the checker Veteran, the builder Seasoned. A `whole` recipe (Ideation,
    Release) is sized the same way. ValueError for a size that is not lean, standard or full."""
    if size not in SIZES:
        raise ValueError(f"No size {size!r}: lean, standard or full")
    seats = library.seats_of(recipe["leader"])                # one seat a stage: the first builder, the first checker
    build, check = recipe["build"][:seats["build"]], recipe["check"][:seats["check"]]
    if size == "full":
        team = [*build, *check]
    elif size == "standard":
        team = list(build)
    else:
        team = []
    return {"leader": recipe["leader"], "team": team, "tiers": tiers_for(recipe["leader"], team, size), "size": size}


def has(recipe: dict, tracks: list[dict]) -> bool:
    """The project has the recipe's party already (§2.3): a party with its leader and a team that holds the recipe's standard team."""
    want = set(sized(recipe, "standard")["team"])
    return any((t.get("leader") or "") == recipe["leader"] and want <= set(t.get("team") or []) for t in tracks)
