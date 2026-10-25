"""A goal's team (decisions §53): the agents of the project who do its tasks, picked from the library when the goal is
made (realm/library.py). It is kept on the goal's page (`team`, a JSON list of role slugs); the Taskmaster plans for
every team and is never in the list.

    set_team(root, "ship", ["product-designer", "reviewer"], every=["reviewer"])   # kept, at most SEATS; `every`: checkers
                                                                # whose check applies to every idea (realm/idea_checks.py)
    team_of(root, "ship")                                       # ["product-designer", "reviewer"]; [] with none
    every_of(root, "ship")                                      # ["reviewer"]
    for_idea(root, "dark-mode")                                 # the team of the idea's goal; every_for_idea, its every

A goal's party (library.seats_of): one leader — the goal's steps (its reading, its ideas' drafts, answers and plans, and
accepting the goal) run as it; the Taskmaster when none is picked —, and its builders and checkers (the team): three and two,
or the seats its leader sets (a Game designer's four and one; spec 59 §2.3).

    leader_of(root, "ship")                                     # "product-manager"; "taskmaster" when none was picked
    seats(team, leader)                                         # the error of a party that has too many in a band, else ""
                                                                # (Ideation: its four views and the skeptic, or a size's part of them; a view nowhere else)

A party's AI tool and its size's tiers (spec 81): `tool_of` / `set_tool` (a `harnesses.REGISTRY` id; "" is the Main tool), `tiers_of` /
`set_tiers` ({agent: tier} the size gave the party's seats) and `seat_role` (a role as this party's seat runs it).

A goal with no team works as before: each task type goes to the project's role for it (Grunt when none).

No face, no model.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from orkboard.realm import ideas

SEATS = 5
IDEATION_WHOLE = "Ideation reads every pitch from all four sides: its views and the skeptic stay"
PITCH_ONLY = "The views judge pitches: they are in Ideation only"


def clean(team: object) -> list[str]:
    """The slugs of a team as given: known shapes only, no Taskmaster, each once, at most SEATS."""
    if not isinstance(team, (list, tuple)):
        raise ValueError("A team is a list of agents")
    got = [str(s).strip() for s in team if re.fullmatch(r"[a-z0-9-]{1,60}", str(s).strip()) and str(s).strip() != "taskmaster"]
    if len(dict.fromkeys(got)) > SEATS:
        raise ValueError(f"A team has at most {SEATS} agents")
    return list(dict.fromkeys(got))


def band_of(slug: str) -> str:
    """An agent's band in a party: the library's, a person's own agent a builder."""
    from orkboard.realm import library
    a = library.get(slug)
    return a.band if a is not None else "build"


def seats(team: list[str], leader: str = "") -> str:
    """Why a party does not fit its seats ("" when it does): one leader, and at most the builders and checkers its leader's stages
    give (library.seats_of)."""
    from orkboard.realm import library
    if leader and band_of(leader) != "lead":
        return f"{leader} does not lead: pick a leader of the library"
    if leader == library.INVESTOR:               # Ideation is its four views and the skeptic (spec 65 §1), or a size's part of them (spec 81 §2)
        views, skeptic = list(library.VIEWS), library.SKEPTIC
        if sorted(team) not in (sorted([*views, skeptic]), sorted([*views[:2], skeptic]), []):
            return IDEATION_WHOLE
        return ""
    if any((a := library.get(s)) is not None and a.pitch for s in team):
        return PITCH_ONLY
    have = library.seats_of(leader or "taskmaster")
    name = library.get(leader).name if leader and library.get(leader) is not None else "Taskmaster"
    for band, words in (("build", "builders"), ("check", "checkers")):
        if sum(1 for s in team if band_of(s) == band) > have[band]:
            return f"A party led by {name} has at most {have[band]} {words}"
    if any(band_of(s) == "lead" for s in team):
        return "A leader leads: it is not one of the builders or checkers"
    return ""


def leader_of(root: Path, slug: str) -> str:
    page = ideas.track_page(root, slug)
    return (page.get("leader") if page is not None else "") or "taskmaster"


def set_team(root: Path, slug: str, team: list[str], every: list[str] | None = None, leader: str | None = None, party: str = "") -> None:
    """The goal's party kept. `party`: the id of the saved party it was picked from (realm/own_parties.py); any change of the party without
    one clears it (a goal never changes a saved party, and a changed party is no longer that one)."""
    with ideas.LOCK:
        page = ideas.track_page(root, slug)
        if page is None:
            raise ValueError(f"No party {slug!r}")
        kept = clean(team)
        page.set("team", json.dumps(kept))
        page.set("team_every", json.dumps([s for s in clean(every or []) if s in kept]))
        if re.fullmatch(r"p-[0-9a-f]{8}", party or ""):
            page.set("party", party)
        elif page.get("party"):
            page.set("party", "")
        if leader is not None:
            page.set("leader", leader if leader != "taskmaster" else "")
        ideas._write(Path(root) / ideas.TRACKS / f"{slug}.md", page.text())


SIZES = ("lean", "standard", "full")                 # a party's size (spec 75 §3): its Target, for its goals


def size_of(root: Path, slug: str) -> str:
    """A party's size (lean · standard · full) kept on its page; "" for a party made before sizes (it works as the setting says)."""
    page = ideas.track_page(root, slug)
    return page.get("size") if page is not None and page.get("size") in SIZES else ""


def set_size(root: Path, slug: str, size: str) -> None:
    """The party's size kept (ValueError for one that is not lean, standard or full)."""
    if size not in SIZES:
        raise ValueError("A size is lean, standard or full")
    with ideas.LOCK:
        page = ideas.track_page(root, slug)
        if page is None:
            raise ValueError(f"No party {slug!r}")
        page.set("size", size)
        ideas._write(Path(root) / ideas.TRACKS / f"{slug}.md", page.text())


def tool_of(root: Path, slug: str) -> str:
    """The AI tool a party's goals run on (a `harnesses.REGISTRY` id), kept on its page; "" is the Main tool (spec 81 §1)."""
    page = ideas.track_page(root, slug)
    return (page.get("tool") or "") if page is not None else ""


def set_tool(root: Path, slug: str, tool: str) -> None:
    """The party's AI tool kept ("" the Main tool). ValueError for one that is not an AI tool: *No AI tool <id>*."""
    from orkboard.realm import harnesses
    if tool and harnesses.get(tool) is None:
        raise ValueError(f"No AI tool {tool}")
    with ideas.LOCK:
        page = ideas.track_page(root, slug)
        if page is None:
            raise ValueError(f"No party {slug!r}")
        page.set("tool", tool)
        ideas._write(Path(root) / ideas.TRACKS / f"{slug}.md", page.text())


def tiers_of(root: Path, slug: str) -> dict[str, str]:
    """The tiers a party's size gave its seats, {agent: tier}, kept on its page; {} for a party with none."""
    page = ideas.track_page(root, slug)
    return clean_tiers(page.get("tiers")) if page is not None else {}


def clean_tiers(raw: object) -> dict[str, str]:
    """`{agent: tier}` from a front-matter value (JSON text) or a dict: known tiers and slug-shaped agents only."""
    if isinstance(raw, str):
        try:
            raw = json.loads(raw) if raw.strip() else {}
        except ValueError:
            raw = {}
    if not isinstance(raw, dict):
        return {}
    return {str(a): str(t) for a, t in raw.items() if re.fullmatch(r"[a-z0-9-]{1,60}", str(a)) and t in ("elder", "warrior", "laborer")}


def set_tiers(root: Path, slug: str, tiers: dict[str, str]) -> None:
    """The party's seats' tiers kept (spec 81 §2); {} clears them."""
    with ideas.LOCK:
        page = ideas.track_page(root, slug)
        if page is None:
            raise ValueError(f"No party {slug!r}")
        page.set("tiers", json.dumps(clean_tiers(tiers)) if tiers else "")
        ideas._write(Path(root) / ideas.TRACKS / f"{slug}.md", page.text())


def seat_role(r: dict | None, tiers: dict[str, str]) -> dict | None:
    """A role as its party's seat runs it (spec 81 §2): the tier its size gave the seat in place of the library's tier it was installed
    with (or By Target). A model the person set by hand on Agents (not that library tier) keeps it; so does a role the size gave no tier."""
    if r is None or not tiers or tiers.get(str(r.get("slug"))) is None:
        return r
    from orkboard.realm import library
    a = library.get(str(r.get("slug")))
    model = str(r.get("model") or "")
    if model and model != (a.tier if a is not None else ""):
        return r
    return {**r, "model": tiers[str(r["slug"])]}


def lean_role(root: Path, slug: str) -> str:
    """In a Lean party the leader does every task no one else takes (spec 81 §2): its slug; "" for any other party or no leader."""
    lead = leader_of(root, slug)
    return lead if size_of(root, slug) == "lean" and lead != "taskmaster" else ""


def party_of(root: Path, slug: str) -> str:
    """The id of the saved party the goal's party was picked from; "" with none."""
    page = ideas.track_page(root, slug)
    return (page.get("party") or "") if page is not None else ""


def team_of(root: Path, slug: str) -> list[str]:
    page = ideas.track_page(root, slug)
    return ideas._json_list(page.get("team")) if page is not None else []


def every_of(root: Path, slug: str) -> list[str]:
    page = ideas.track_page(root, slug)
    return ideas._json_list(page.get("team_every")) if page is not None else []


def for_idea(root: Path, idea: str) -> list[str]:
    page = ideas.idea_page(root, idea)
    return team_of(root, page.get("track") or ideas.GENERAL) if page is not None else []


def every_for_idea(root: Path, idea: str) -> list[str]:
    page = ideas.idea_page(root, idea)
    return every_of(root, page.get("track") or ideas.GENERAL) if page is not None else []


def recipe_of(root: Path, slug: str) -> str:
    """The id of the recipe (realm/party_recipes.py) a party was made from, kept on its page; "" with none."""
    page = ideas.track_page(root, slug)
    return (page.get("recipe") or "") if page is not None else ""


def set_recipe(root: Path, slug: str, recipe: str) -> None:
    """The party recipe kept, so a change of size finds the team of each size again (spec 81 section 3)."""
    with ideas.LOCK:
        page = ideas.track_page(root, slug)
        if page is None:
            raise ValueError(f"No party {slug!r}")
        page.set("recipe", recipe)
        ideas._write(Path(root) / ideas.TRACKS / f"{slug}.md", page.text())
