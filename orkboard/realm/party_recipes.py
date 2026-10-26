"""The parties each kind of project is proposed, and their three sizes (docs/specs/75-parties-fitted-to-the-project.md §2, decisions §90).

    RECIPES["mobile"]                  # [{id, name, line, leader, build, check, whole, because, when}, …] in the order they are proposed
    for_kind("backend", {"sql": 3})    # a kind's recipes, those that wait for a fact (`when`: "sql") left out when the folder lacks it
    get("mobile-features")             # one recipe by its id, from any kind; None for none
    sized(recipe, "standard")          # {"leader": "product-manager", "team": ["grunt", "artist", "reviewer"], "tiers": {…}, "size": "standard"}
    tiers_for("architect", team, "full")   # {agent: tier} a size gives any party's seats (spec 81 §2)
    stages_of("game")                  # [ideation, game-concept, game-build, release, game-liveops]: New party's *By stage of the project* (spec 91 §7)
    running_name("wiki")               # "Upkeep": what the fifth stage, the project's running, is called for a kind (LiveOps · Run · Upkeep: spec 92 §1)
    TEAM                               # the Team party's recipe: the person's Operations, put in one project (spec 92 §3)
    TARGET["lean"]                     # "thrift": the Target a size works at (realm/idea_target.py SIZE_TARGET)
    has(recipe, tracks)                # the project already has this recipe's party (same leader, the standard team inside its team)

A recipe is made of the library's agents (realm/library.py), `build` and `check` most needed first; a party's seats are its leader's stages, one
agent a stage (`library.seats_of`, spec 87 §5). Its sizes: **lean**, the leader alone (its tasks go to the leader: spec 81); **standard**, the
leader and its first builder; **full**, the leader, its first builder and its first checker; each size also gives its seats their tiers (`tiers`).
A `whole` recipe (Ideation, Release) is sized the same way (spec 81 §2). Ideation, Release, Game and Art and sound are the library's presets, built on their seats.
**The stages** (spec 91 §7): beside a kind's recipes, `STAGE_RECIPES[kind]` has its **Concept**, **Build** and **LiveOps**, made of the library's agents fitted to the kind
(a game's Concept is the Game designer's, a mobile app's the Product designer's); they are proposed to no one (`for_kind` does not list them) and are New party's, with Ideation
and Release, which every kind has. A stage recipe's id is `<kind>-<stage>`, kept with the party as its recipe, so a Lean party can grow back.
**The project's running** (spec 92 §1) is the fifth stage, `<kind>-liveops` as an id and *LiveOps* for a game, *Run* for what runs (an app, a site, a service, code, data) and *Upkeep* for
what is kept true (a wiki, a design, texts) as a name (`running_name`); it proposes its recurring goals (`realm/recurring.py`).
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


# The Team party (spec 92 §3): the person's Operations (decisions §51) put in one project of their choosing. Its leader is the Product manager (a lich); it has no builders and no checkers:
# the work is the Operations' templates, which run as they always did. It is New party's, under *By craft*, for every kind; proposed to no one, and only one may exist across the person's projects.
TEAM_ID = "team"
TEAM = _recipe(TEAM_ID, "Team", "Your work with people: the daily, 1:1s, the retro, mail and Jira", "product-manager", [], [],
               "your work with people belongs to you, not to a project")


STAGES = ("ideation", "concept", "build", "release", "liveops")      # New party's *By stage of the project*, in the order they are shown (spec 91 §7)
STAGE_NAMES = {"ideation": "Ideation", "concept": "Concept", "build": "Build", "release": "Release", "liveops": "Run"}
RUNNING_NAMES = {"game": "LiveOps", "wiki": "Upkeep", "design": "Upkeep", "texts": "Upkeep"}      # the fifth stage's name by kind (spec 92 §1); the rest run: *Run*


def running_name(kind: str) -> str:
    """What the project's running is called for a kind: *LiveOps* for a game, *Upkeep* for what is kept true (a wiki, a design, texts), *Run* for the rest and for an empty folder."""
    return RUNNING_NAMES.get(kind, STAGE_NAMES["liveops"])


def _stage(kind: str, stage: str, line: str, leader: str, build: list[str], check: list[str], because: str) -> dict:
    return _recipe(f"{kind}-{stage}", running_name(kind) if stage == "liveops" else STAGE_NAMES[stage], line, leader, build, check, because)


# Each kind's Concept, Build and LiveOps (spec 91 §7): the leader, then the builders and the checkers most needed first (a party has one seat a stage, so the
# first of each is the one a size seats; the others are who the person may put there). Only the library's agents.
STAGE_RECIPES: dict[str, list[dict]] = {
    "game": [
        _stage("game", "concept", "The rules, the loop and the first levels, tried on paper", "game-designer", ["level-designer", "artist"], ["playtester"],
               "a game's idea is shaped before it is built"),
        _stage("game", "build", "Rules, levels, pictures and sounds, played through", "game-designer", ["grunt", "artist", "sound-designer"], ["playtester", "reviewer"],
               "a game is built, played and tuned"),
        _stage("game", "liveops", "The numbers of play, what players say, small fixes", "analyst", ["data-engineer", "grunt", "copywriter"], ["data-reviewer"],
               "a game that is out is read by its numbers"),
    ],
    "mobile": [
        _stage("mobile", "concept", "Who it is for, the flow and the screens", "product-designer", ["ui-kit", "artist"], ["accessibility-reviewer"],
               "an app's idea is drawn before it is built"),
        _stage("mobile", "build", "Screens, code and the pictures, checked before they land", "product-manager", ["grunt", "ui-kit", "artist", "aso"],
               ["reviewer", "accessibility-reviewer"], "features are the app's daily work"),
        _stage("mobile", "liveops", "Crashes, the store's reviews, dependencies, small fixes", "product-manager", ["grunt", "tester", "community"], ["reviewer"],
               "an app in the stores is watched and kept up to date"),
    ],
    "web": [
        _stage("web", "concept", "What the site says, for whom, and its pages", "product-designer", ["copywriter", "ui-kit"], ["accessibility-reviewer"],
               "a site's pages are planned before they are made"),
        _stage("web", "build", "Pages, code and words, checked before they land", "product-designer", ["grunt", "ui-kit", "copywriter", "seo"],
               ["reviewer", "accessibility-reviewer"], "pages are the product here"),
        _stage("web", "liveops", "Errors and speed, dependencies, what people write", "architect", ["grunt", "tester", "community"], ["reviewer"],
               "a site that is up is watched and kept up to date"),
    ],
    "backend": [
        _stage("backend", "concept", "The parts, the data and what each calls", "architect", ["data-engineer", "grunt"], ["security-reviewer"],
               "a service is shaped before it is written"),
        _stage("backend", "build", "Code and tests, checked before they land", "architect", ["grunt", "tester"], ["reviewer", "security-reviewer"],
               "services are built and kept safe"),
        _stage("backend", "liveops", "Incidents, slow calls, dependencies, small fixes", "architect", ["grunt", "tester", "data-engineer"], ["reviewer", "security-reviewer"],
               "a service that runs is watched and kept up to date"),
    ],
    "data": [
        _stage("data", "concept", "The questions, and where the numbers come from", "analyst", ["experimenter", "sql"], ["data-reviewer"],
               "the questions come before the queries"),
        _stage("data", "build", "Queries, tables and reports, recounted before they land", "analyst", ["data-engineer", "sql", "experimenter"], ["data-reviewer"],
               "the work is numbers and the questions they answer"),
        _stage("data", "liveops", "Pipelines that ran, tables that are fresh, numbers recounted", "analyst", ["data-engineer", "sql", "grunt"], ["data-reviewer"],
               "reports that are read are kept fresh and true"),
    ],
    "wiki": [
        _stage("wiki", "concept", "What the pages are for and how they are laid out", "product-manager", ["copywriter"], ["editor"],
               "a wiki is laid out before it is written"),
        _stage("wiki", "build", "Pages written and edited", "product-manager", ["copywriter", "seo"], ["editor"],
               "pages are written and kept up to date"),
        _stage("wiki", "liveops", "Stale pages found, links checked, new sources taken in", "product-manager", ["copywriter", "community"], ["editor"],
               "pages that are read are kept true"),
    ],
    "design": [
        _stage("design", "concept", "Flows and first screens, tried on paper", "product-designer", ["artist", "ui-kit"], ["accessibility-reviewer"],
               "a design is drawn rough before it is drawn well"),
        _stage("design", "build", "Screens, pictures and motion, checked before they land", "product-designer", ["ui-kit", "artist", "animator"],
               ["accessibility-reviewer", "art-reviewer"], "screens and pictures are made here"),
        _stage("design", "liveops", "What drifted from the kit, contrast and tap sizes", "product-designer", ["ui-kit", "artist", "copywriter"], ["accessibility-reviewer"],
               "a design in use is kept true to its kit"),
    ],
    "texts": [
        _stage("texts", "concept", "Who reads it, what it says, its outline", "growth", ["copywriter"], ["editor"],
               "a text is outlined before it is written"),
        _stage("texts", "build", "Words written, edited and found", "growth", ["copywriter", "seo"], ["editor"],
               "the work is words"),
        _stage("texts", "liveops", "Stale texts found, links checked, readers answered", "growth", ["copywriter", "seo", "community"], ["editor"],
               "words that are read are kept true"),
    ],
    "code": [
        _stage("code", "concept", "What it should do and for whom, before the code", "product-manager", ["grunt", "copywriter"], ["reviewer"],
               "a change is thought through before it is written"),
        _stage("code", "build", "Code and tests, checked before they land", "architect", ["grunt", "tester"], ["reviewer", "security-reviewer"],
               "there is code to change and test"),
        _stage("code", "liveops", "Failing builds, dependencies, small fixes", "architect", ["grunt", "tester", "copywriter"], ["reviewer", "security-reviewer"],
               "code that runs is watched and kept up to date"),
    ],
}


def stages_of(kind: str) -> list[dict]:
    """New party's *By stage of the project* for a kind (spec 91 §7), in the order they are shown: Ideation, its Concept, its Build, Release, its LiveOps.
    Ideation and Release are the library's presets (`whole`), the same for every kind; an unknown kind (and an empty folder) has `code`'s."""
    mine = {r["id"].rsplit("-", 1)[1]: r for r in STAGE_RECIPES.get(kind) or STAGE_RECIPES["code"]}
    own = {"ideation": _ideation(), "release": _release(), **mine}
    return [own[s] for s in STAGES]


def for_kind(kind: str, facts: dict | None = None) -> list[dict]:
    """A kind's recipes in the order they are proposed (an unknown kind: `code`'s); those that wait for a fact (`when`) only when the folder has it."""
    rows = RECIPES.get(kind) or RECIPES["code"]
    return [r for r in rows if not r["when"] or (facts or {}).get(r["when"])]


def is_team(track: dict) -> bool:
    """Whether a party of `ideas.tracks` is the Team party: it holds the person's Operations, not goals (spec 92 §3)."""
    return track.get("recipe") == TEAM_ID


def get(recipe_id: str) -> dict | None:
    if recipe_id == TEAM_ID:
        return TEAM
    return next((r for rows in (*RECIPES.values(), *STAGE_RECIPES.values()) for r in rows if r["id"] == recipe_id), None)


def kind_of(recipe_id: str, prefer: str = "") -> str:
    """The kind a recipe is proposed to: `prefer`'s when it has it (the project's own), else the first that has it; "" for none."""
    if any(r["id"] == recipe_id for r in (*RECIPES.get(prefer, ()), *STAGE_RECIPES.get(prefer, ()))):
        return prefer
    return next((k for k in RECIPES if any(r["id"] == recipe_id for r in (*RECIPES[k], *STAGE_RECIPES.get(k, ())))), "")


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
