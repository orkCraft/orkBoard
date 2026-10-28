"""The project's stage and the crafts it offers (docs/specs/99-a-goals-way.md §1.2, decisions §122.5, §137.1, §151.5, §151.7).

    kept(state_dir)                       # "idea" | "being_made" | "live" the person set; "" when unset
    keep(state_dir, "live")               # kept in `<state_dir>/project.json` (`stage`); ValueError for a stage that is none
    read(repo_root)                       # the stage read from the project by its names: no code → idea; code, no store page and no deploy → being_made; else live
    current(state_dir, repo_root)         # {"stage", "read", "kept"}: the kept stage, else the read one
    offered("game")                       # {"idea": [card, …], "being_made": […], "live": […]}: the crafts offered when the project is at that stage
    crafts("web", "idea")                 # the cards of one stage

**The crafts by stage**: *Idea* the concept's crafts (Game design and Art; Product and Design), lean; *Being made* adds Tech, standard; *Live* adds LiveOps or
Run, and Marketing (§151.7), standard. **Release is in every project at every stage** (§137.1): its card is `locked` (ticked, never unticked, never dropped),
Lean, its leader alone (`squad` is empty) on the cheaper tier (§151.6, §157.2: Seasoned). A card is `{id, name, line, craft, leader, build, check, squad, size,
tiers, from, locked, because}`; `from` is the stage that adds it, so a face groups the cards under the stages' headings. The names `idea` · `being_made` ·
`live` are code's; the face says Idea, Being made and Live (spec 100; the host returns keys, never words). No face, no model; the project's names are read, never
a file's contents.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from orkboard.realm import ideas, library, party_recipes, project_kind

STAGES = ("idea", "being_made", "live")
FROM = {"product": "idea", "game-design": "idea", "design": "idea", "art": "idea", "release": "idea",
        "tech": "being_made", "run": "live", "liveops": "live", "marketing": "live"}          # the stage that adds a craft
SIZE = {"product": "lean", "game-design": "lean", "design": "lean", "art": "lean", "release": "lean",
        "tech": "standard", "run": "standard", "liveops": "standard", "marketing": "standard"}     # the size a craft is proposed in
FILE = "project.json"
STORE_PAGES = ("fastlane/metadata", "fastlane/screenshots", "ios/fastlane/metadata", "android/fastlane/metadata", "store", "appstore", "play-store", "playstore")
DEPLOY_FILES = {"vercel.json", "netlify.toml", "fly.toml", "procfile", "app.yaml", "app.yml", "serverless.yml", "serverless.yaml", "render.yaml", "heroku.yml",
                "railway.json", "railway.toml", "wrangler.toml", "firebase.json", "cname", "docker-compose.prod.yml", "docker-compose.production.yml"}
DEPLOY_DIRS = ("k8s", "helm", "terraform", ".vercel", ".netlify")
DEPLOY_WORKFLOW = ("deploy", "release", "publish")             # a workflow file of `.github/workflows` named so


def _path(state_dir: Path) -> Path:
    return Path(state_dir) / FILE


def _json(state_dir: Path) -> dict:
    try:
        data = json.loads(_path(state_dir).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def kept(state_dir: Path) -> str:
    """The stage the person set (or an earlier read kept), "" when none."""
    got = _json(state_dir).get("stage")
    return got if got in STAGES else ""


def keep(state_dir: Path, stage: str) -> str:
    """The stage kept in `<state_dir>/project.json`, the file's other keys left as they are. ValueError for a stage that is none: *A stage is idea, being_made or live*."""
    if stage not in STAGES:
        raise ValueError("A stage is idea, being_made or live")
    ideas._write_json(_path(state_dir), {**_json(state_dir), "stage": stage})
    return stage


def _has_any(root: Path, rels: tuple[str, ...]) -> bool:
    return any((root / rel).is_dir() for rel in rels)


def _deploys(root: Path) -> bool:
    """A deploy by names: a platform's file at the top, a folder of its kind, or a workflow named for deploying (never a file's contents)."""
    try:
        top = {e.name.lower(): e.is_dir() for e in os.scandir(root)}
        flows = [e.name.lower() for e in os.scandir(root / ".github" / "workflows")] if (root / ".github" / "workflows").is_dir() else []
    except OSError:
        return False
    return any(n in DEPLOY_FILES and not d for n, d in top.items()) or any(top.get(d) for d in DEPLOY_DIRS) or any(w in f for f in flows for w in DEPLOY_WORKFLOW)


def read(repo_root: Path) -> str:
    """The stage read from the project by its names (§1.2): no code is `idea`; code and no store page or deploy is `being_made`; else `live`."""
    root = Path(repo_root)
    if not project_kind.read_full(root)["facts"].get("code"):
        return "idea"
    return "live" if _has_any(root, STORE_PAGES) or _deploys(root) else "being_made"


def current(state_dir: Path, repo_root: Path) -> dict:
    """`{"stage", "read", "kept"}`: the stage the project is at (the one kept, else the one read), the one read from the project, and whether the
    person's is kept."""
    mine, seen = kept(state_dir), read(repo_root)
    return {"stage": mine or seen, "read": seen, "kept": bool(mine)}


def card(recipe: dict) -> dict:
    """A recipe as a stage offers it: its seats, the size it is proposed in, the tiers that size gives, and the stage that adds it."""
    craft = recipe.get("craft") or recipe["id"]
    size = SIZE.get(craft, "standard")
    got = party_recipes.sized(recipe, size)
    return {"id": recipe["id"], "name": recipe["name"], "line": recipe["line"], "craft": craft, "leader": recipe["leader"], "build": list(recipe["build"]),
            "check": list(recipe["check"]), "squad": got["team"], "size": size, "tiers": got["tiers"], "from": FROM.get(craft, "live"),
            "locked": craft == party_recipes.RELEASE, "because": recipe.get("because") or ""}


def crafts(kind: str, stage: str) -> list[dict]:
    """The cards the project's kind is offered at a stage, in the kind's order: the crafts of the stages reached and Release (in every project)."""
    if stage not in STAGES:
        raise ValueError("A stage is idea, being_made or live")
    reached = STAGES[:STAGES.index(stage) + 1]
    return [card(r) for r in party_recipes.for_kind(kind) if FROM.get(r.get("craft") or r["id"], "live") in reached or r["id"] == party_recipes.RELEASE]


def offered(kind: str) -> dict[str, list[dict]]:
    """`{stage: cards}` for the three stages: what is offered when the project is at each."""
    return {stage: crafts(kind, stage) for stage in STAGES}


def release_card() -> dict:
    """Release's card (in every project): Lean, its leader alone."""
    return card(party_recipes.CRAFTS[party_recipes.RELEASE])


def leader_tier() -> str:
    """The tier Release's leader runs on (§151.6, §157.2): the cheaper one, Seasoned."""
    return party_recipes.tiers_for(library.RELEASE_MANAGER, [], "lean")[library.RELEASE_MANAGER]
