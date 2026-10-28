"""The Orkmaster (docs/specs/70-orkmaster-and-the-project.md §1, decisions §85): the project's ork. It deals the parties New party offers
and suggests a goal's party. By rules, with no model; it plans nothing, moves nothing, writes nothing.

    ORKMASTER                                   # {"id", "name", "race", "tier"}: the head the faces draw
    deal(root, state_dir)                       # every craft's party once, in the order New party shows: [{"id", "why", "n"}]
    party_for(state_dir, root, "logo")          # the project's parties but General, each how it fits a goal type: [{party, name, fits, missing}]
    suggested(parties)                          # the slug `party_for`'s answer suggests
    install(state_dir) / role(state_dir)        # its role for a collision's judge (spec 71 §2): `orkmaster`, a warrior, takes no task
    proposals(root, state_dir, settings, kind, facts, tracks, ideation_first, told, stage)   # the parties the project's kind needs, each in three sizes (spec 75 §4.1)
    proposal_ids(kind_id, facts, tracks)        # their ids, the ones the project has last: for the deal (spec 75 §4.3)

`why` of a deal row: `flags_wait` (Release first: no party releases and `n` flags wait), `have` (the project has one: last), else "". Ideation is never dealt nor
proposed (decisions §122.3), nor are the mixed parties of before (spec 99 §1.1): a deal row is a craft's party. No face, no model, no write.
"""
from __future__ import annotations

from pathlib import Path

from orkboard.realm import goal_team, goal_types, idea_flag, idea_target, ideas, library, party_price, party_recipes, project_kind, project_stage, roles

ORKMASTER = {"id": "orkmaster", "name": "Orkmaster", "race": "peon", "tier": "crown"}
RELEASE = party_recipes.RELEASE                  # the Release party's id


def flags_by_party(root: Path, state_dir: Path, tracks: list[dict] | None = None) -> dict[str, int]:
    """{party slug: goals with a flag} of every party but General and Ideation's (what a Release party would release from)."""
    out = {}
    for t in tracks if tracks is not None else ideas.tracks(root, make=False):
        if t["slug"] == ideas.GENERAL or (t.get("leader") or "") == library.INVESTOR:
            continue
        out[t["slug"]] = sum(1 for i in ideas.ideas(root, t["slug"]) if idea_flag.flag_of(state_dir, i["slug"]) is not None)
    return out


def deal(root: Path, state_dir: Path, *, tracks: list[dict] | None = None, flags: dict[str, int] | None = None) -> list[dict]:
    """Every craft's party once, as `[{"id", "why", "n"}]` (spec 70 §1.1; spec 99 §1.1: the ids are `party_recipes.CRAFTS`', not the mixed presets'): Release first
    when the project has no party the Release manager leads and flags wait (`flags_wait`, `n` their count); then the others in the crafts' order; last,
    Release when the project has it (`have`). Ideation is not dealt. `tracks`, `flags` (`flags_by_party`): what the
    caller has read already."""
    tracks = ideas.tracks(root, make=False) if tracks is None else tracks
    has_release = library.RELEASE_MANAGER in {t.get("leader") or "" for t in tracks}
    n = 0 if has_release else sum((flags_by_party(root, state_dir, tracks) if flags is None else flags).values())
    ids = list(party_recipes.CRAFTS)
    rows = {i: {"id": i, "why": "", "n": 0} for i in ids}
    head, tail = [], []
    if has_release:
        rows[RELEASE]["why"] = "have"
        tail.append(RELEASE)
    elif n > 0:
        rows[RELEASE].update(why="flags_wait", n=n)
        head.append(RELEASE)
    rest = [i for i in ids if i not in head and i not in tail]
    return [rows[i] for i in [*head, *rest, *tail]]


def party_for(state_dir: Path, root: Path, type_id: str | None = None) -> list[dict]:
    """The project's parties but General, in the Board's order, each `{"party", "name", "fits", "missing": [{"agent", "name"}]}` (spec 70
    §1.2). With a goal type (a catalog id): `fits` is `whole` (the party is offered it with nothing missing), then `missing` (offered with
    someone missing, `missing` says who), then `none`; Ideation's party is always `none`. Without: `fits` is "", Ideation's last with `pitch`.
    ValueError for a type the catalog lacks."""
    t = None
    if type_id:
        t = goal_types.get(type_id)
        if t is None:
            raise ValueError(f"No goal type {type_id!r}")
    rows, pitch = [], []
    for track in ideas.tracks(root, make=False):
        if track["slug"] == ideas.GENERAL or party_recipes.is_team(track):      # the Team party holds Operations, not goals (spec 92 §3)
            continue
        row = {"party": track["slug"], "name": track["title"], "fits": "", "missing": []}
        if (track.get("leader") or "") == library.INVESTOR:
            row["fits"] = "none" if t else "pitch"
            (rows if t else pitch).append(row)
            continue
        if t:
            got = next((m for o, m in goal_types.offered(state_dir, root, track["slug"]) if o.id == t.id), None)
            row["fits"] = "none" if got is None else "missing" if got else "whole"
            row["missing"] = [{"agent": m["agent"], "name": m["name"]} for m in got or []]
        rows.append(row)
    if t:
        return sorted(rows, key=lambda r: ("whole", "missing", "none").index(r["fits"]))
    return rows + pitch


def suggested(parties: list[dict]) -> str:
    """The first party that takes the type whole, else the first that misses someone, else the first; "" with no party."""
    for fit in ("whole", "missing"):
        for r in parties:
            if r["fits"] == fit:
                return r["party"]
    return parties[0]["party"] if parties else ""


# -- its role (spec 71 §2): the judge of a collision speaks as the Orkmaster ---------------------------------------------------------

ROLE, ROLE_MODEL = "orkmaster", "warrior"
INSTRUCTION = ("You keep the project's parties from colliding. You are given two goals of different parties that touch the same files, "
               "and say only whether they change the same thing or just sit near each other. Answer from the two goals and what they touch; "
               "invent nothing; when you cannot tell, say they do not collide.")


def install(state_dir: Path) -> None:
    """The Orkmaster as a role of the project (`roles/orkmaster.md`): a warrior, an ork, taking no task type. Written once, never over the
    person's own."""
    roles.install(state_dir, ROLE, ORKMASTER["name"], ROLE_MODEL, roles.DEFAULT_CRAFT, INSTRUCTION, (), ORKMASTER["race"])


def role(state_dir: Path) -> dict:
    """The role a collision is judged as: the project's file (the person may have set its model or its words on Agents), else the default
    one as `install` writes it."""
    return roles.role(state_dir, ROLE) or {"slug": ROLE, "name": ORKMASTER["name"], "model": ROLE_MODEL, "instruction": INSTRUCTION,
                                          "craft": roles.DEFAULT_CRAFT, "takes": []}


def speak(state_dir: Path) -> str:
    """What the Orkmaster is told before a call: who it is, and its instruction."""
    return f"You are the Orkmaster of this project. {role(state_dir).get('instruction') or ''}\n\n"


# -- the proposals (spec 75 §4): the parties the project's kind needs, each in three sizes ------------------------------------------------------

WHY_CHARS = 120
EMPTY_WHY = "the folder is empty"
BARE_WHY = "nothing here says more"
TOLD_WHY = "by what you said"


def recipes_of(kind_id: str, facts: dict | None, ideation_first: bool = False, stage: str | None = None) -> list[dict]:
    """The recipes a kind is proposed in order (one craft a party: `party_recipes.for_kind`). `stage` (`project_stage.STAGES`): only the crafts of the stages
    the project has reached, Release always (spec 99 §1.2); None: all of the kind's. `ideation_first` is kept for the host's call and means nothing: Ideation
    is never proposed (decisions §122.3)."""
    rows = party_recipes.for_kind(kind_id, facts)
    if stage is None:
        return rows
    return [r for r in rows if r["id"] in {c["id"] for c in project_stage.crafts(kind_id, stage)}]


def _ordered(rows: list[dict], tracks: list[dict]) -> list[tuple[dict, bool]]:
    """[(recipe, have)]: those the project has not, in their order, then those it has."""
    got = [(r, party_recipes.has(r, tracks)) for r in rows]
    return [x for x in got if not x[1]] + [x for x in got if x[1]]


def proposal_ids(kind_id: str, facts: dict | None, tracks: list[dict], ideation_first: bool = False, stage: str | None = None) -> list[str]:
    """The ids of the proposals in the order they are shown, those the project has last (no price, no call)."""
    return [r["id"] for r, _h in _ordered(recipes_of(kind_id, facts, ideation_first, stage), tracks)]


def deal_first(deal: list[dict], tracks: list[dict], kind_id: str, facts: dict | None) -> list[dict]:
    """The deal (spec 70 §1.1) with the proposals' ids first (spec 75 §4.3): each proposal the project has not is a first row, in the
    proposals' order, as the deal has it (a craft's party: `party_recipes.CRAFTS`), else `{"id", "why": "proposal", "n": 0}`;
    the others follow as they were (the parties the project has still last)."""
    by_id = {r["id"]: r for r in deal}
    head = [by_id.get(r["id"]) or {"id": r["id"], "why": "proposal", "n": 0}
            for r, have in _ordered(recipes_of(kind_id, facts), tracks) if not have]
    return [*head, *[r for r in deal if r["id"] not in {h["id"] for h in head}]]


def _why(recipe: dict, signs: list[str], kind_id: str, told: bool) -> str:
    """A line of why for this project: what was seen (or said), then why the recipe's party fits it."""
    seen = project_kind.in_words(signs) or (TOLD_WHY if told else EMPTY_WHY if kind_id == "empty" else BARE_WHY)
    return f"{seen}: {recipe['because']}"[:WHY_CHARS] if recipe.get("because") else seen[:WHY_CHARS]


def _head(state_dir: Path, slug: str, target: str, tiers: dict[str, str] | None = None, party: str = "", leader: str = "") -> dict:
    """The head a member wears: its role's when the project has it, else as installing it would make it (a role on its library tier); at
    the tier the size gives its seat (`tiers`, spec 81 §2) unless the person set its model by hand. As a seat of the party of craft `party` (spec 99 §1.4)
    it wears the party's race, the party's `leader` that race's higher form."""
    r = roles.role(state_dir, slug)
    if r is None:
        a = library.get(slug)
        r = {"slug": slug, "craft": a.craft, "race": a.race, "model": a.tier} if a else {}
    got = roles.head(goal_team.seat_role(r, tiers or {}) or r, target, party=party, lead=bool(leader) and slug == leader)
    return {"race": got["race"], "tier": got["tier"]}


def proposals(root: Path, state_dir: Path, settings: dict, kind: dict, facts: dict | None = None, tracks: list[dict] | None = None,
              ideation_first: bool = False, told: bool = False, stage: str | None = None) -> list[dict]:
    """`ideas.proposals`' list (spec 75 §4.1): a card per recipe of the kind, those the project has last (`have`), each `sizes`: lean ·
    standard · full with the leader, the team (the squad: the same in every size), how many agents, the Target it works as, its price a goal (`low`, `high`:
    a size's price, never a squad's: `goal_team.price_team`) and the members' heads in seat order, each its party's race and the leader's its higher form.
    A card says its `craft`, the stage that adds it (`from`), the `size` it is proposed in, its `squad` and whether it is `locked` (Release). `kind`:
    `{"id", "words", "signs"}`; `told`: the kind was read from the person's line; `stage`: only the crafts of the stages reached (`project_stage`), else all."""
    tracks = ideas.tracks(root, make=False) if tracks is None else tracks
    out = []
    for recipe, have in _ordered(recipes_of(kind["id"], facts, ideation_first, stage), tracks):
        craft = recipe.get("craft") or recipe["id"]
        sizes = {}
        for size in idea_target.SIZES:
            party = party_recipes.sized(recipe, size)
            target = idea_target.SIZE_TARGET[size]
            got = party_price.price(root, state_dir, {**(settings or {}), "target": target}, party["leader"], party["basis"], [], tiers=party["tiers"])
            sizes[size] = {"leader": party["leader"], "team": party["team"], "agents": 1 + len(party["team"]), "target": target,
                           "price": {"low": got["low"], "high": got["high"]},
                           "tiers": party["tiers"], "heads": [_head(state_dir, s, target, party["tiers"], craft, party["leader"]) for s in [party["leader"], *party["team"]]]}
        out.append({"id": recipe["id"], "name": recipe["name"], "line": recipe["line"], "why": _why(recipe, kind["signs"], kind["id"], told),
                    "craft": craft, "from": project_stage.FROM.get(craft, "live"), "size": project_stage.SIZE.get(craft, "standard"),
                    "squad": party_recipes.squad_of(recipe), "locked": craft == party_recipes.RELEASE, "have": have, "sizes": sizes})
    return out
