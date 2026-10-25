"""The parties each kind of project is proposed, and their three sizes (docs/specs/75-parties-fitted-to-the-project.md §2, decisions §90).

    RECIPES["mobile"]                  # [{id, name, line, leader, build, check, whole, because, when}, …] in the order they are proposed
    for_kind("backend", {"sql": 3})    # a kind's recipes, those that wait for a fact (`when`: "sql") left out when the folder lacks it
    get("mobile-features")             # one recipe by its id, from any kind; None for none
    sized(recipe, "standard")          # {"leader": "product-manager", "team": ["grunt", "artist", "reviewer"], "size": "standard"}
    TARGET["lean"]                     # "thrift": the Target a size works at (realm/idea_target.py SIZE_TARGET)
    has(recipe, tracks)                # the project already has this recipe's party (same leader, the standard team inside its team)

A recipe is made of the library's agents (realm/library.py), `build` and `check` most needed first. Its sizes: **lean**, the leader alone
(its tasks go to the Grunt as any party's with no taker); **standard**, the leader, the first two builders and the first checker; **full**,
every builder and checker of the recipe up to its leader's seats (`library.seats_of`). A `whole` recipe (Ideation, Release) keeps its
whole seats in every size: its size only sets the Target. Ideation, Release and Game are the library's presets, built on their seats.
No face, no model.
"""
from __future__ import annotations

from orkboard.realm import idea_target, library

TARGET = idea_target.SIZE_TARGET
SIZES = idea_target.SIZES


def _preset(pid: str, because: str = "", whole: bool = False) -> dict:
    """A recipe on a library preset's seats (`library.PRESETS`)."""
    _i, name, line, _craft, lead, build, check = next(p for p in library.PRESETS if p[0] == pid)
    return {"id": pid, "name": name, "line": line, "leader": lead, "build": list(build), "check": list(check),
            "whole": whole, "because": because, "when": ""}


def _recipe(rid: str, name: str, line: str, leader: str, build: list[str], check: list[str], because: str = "", when: str = "") -> dict:
    return {"id": rid, "name": name, "line": line, "leader": leader, "build": build, "check": check, "whole": False,
            "because": because, "when": when}


def _ideation(because: str = "small ideas are judged before they cost anything") -> dict:
    return _preset("ideation", because, whole=True)


def _release(because: str = "a version goes out to people") -> dict:
    return _preset("release", because, whole=True)


RECIPES: dict[str, list[dict]] = {
    "empty": [_ideation()],
    "mobile": [
        _recipe("mobile-features", "Mobile app: features", "Screens and what people do on them", "product-manager",
                ["grunt", "artist", "aso", "ui-kit"], ["reviewer", "accessibility-reviewer"], "features are the app's daily work"),
        _recipe("mobile-architecture", "Mobile app: architecture", "How the app is built, tested and kept safe", "architect",
                ["grunt", "tester"], ["reviewer", "security-reviewer"], "the app's structure needs its own hands"),
        _release(),
    ],
    "web": [
        _recipe("web-pages", "Web: pages", "Pages that say what it does, and are found", "product-designer",
                ["grunt", "ui-kit", "copywriter", "seo"], ["reviewer", "accessibility-reviewer"], "pages are the product here"),
        _release(),
    ],
    "backend": [
        _recipe("backend", "Backend", "Services, tests and what keeps them safe", "architect",
                ["grunt", "tester"], ["reviewer", "security-reviewer"], "services are built and kept safe"),
        _recipe("backend-data", "Data", "Queries and the numbers they give", "analyst",
                ["data-engineer", "sql", "experimenter"], ["data-reviewer"], "queries are written here", when="sql"),
    ],
    "game": [_preset("game", "a game is built, played and tuned"), _release()],
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
        _ideation(),
    ],
    "texts": [
        _recipe("texts", "Texts", "Words that are written, checked and found", "growth",
                ["copywriter", "seo"], ["editor"], "the work is words"),
        _ideation(),
    ],
    "code": [
        _recipe("engineering-code", "Engineering", "Code, tests and the build", "architect",
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


def sized(recipe: dict, size: str) -> dict:
    """`{"leader", "team", "size"}` of a recipe in a size (§2.2). ValueError for a size that is not lean, standard or full."""
    if size not in SIZES:
        raise ValueError(f"No size {size!r}: lean, standard or full")
    seats = library.seats_of(recipe["leader"])
    build, check = recipe["build"][:seats["build"]], recipe["check"][:seats["check"]]
    if recipe["whole"] or size == "full":
        team = [*build, *check]
    elif size == "standard":
        team = [*build[:2], *check[:1]]
    else:
        team = []
    return {"leader": recipe["leader"], "team": team, "size": size}


def has(recipe: dict, tracks: list[dict]) -> bool:
    """The project has the recipe's party already (§2.3): a party with its leader and a team that holds the recipe's standard team."""
    want = set(sized(recipe, "standard")["team"])
    return any((t.get("leader") or "") == recipe["leader"] and want <= set(t.get("team") or []) for t in tracks)
