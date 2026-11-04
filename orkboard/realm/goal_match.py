"""A new goal matched against the face-down pile, by code (docs/specs/135-a-new-goal-matched-against-the-face-down-pile.md §A; decisions §242.1, §242.3–§242.4): the goal's
words against the titles and words of the goals lying face down before their spec, and the parties and places of the map its route gives. Pure code: no model, no write, no face.

    goal_match.words(text)                                  # the significant words of a text, a set
    goal_match.candidates(root, state_dir)                  # the goals face down before their spec, in the Orkmaster's order: [{slug, title, party, state}]
    goal_match.fits(root, state_dir, slug, text, parties)   # joining `text` into goal `slug` stays small: at most one party added to its route, its words under JOIN_CHARS
    goal_match.match(root, state_dir, text, route, marks=(), home="")   # the best candidate: {idea, title, party, state, shared, score, why, adds}, None for none

The score is Dice's over the two sets of words (`2·|shared| / (|A| + |B|)`); the bar it must reach falls where the routes name the same parties and where both point at the same
place of a map. One match at most. Where a goal is offered is `candidates`' rule: before its sections (`goal_refine.in_analysis`), never a pitch, a release, or a decision put off.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable

from orkboard.realm import goal_refine, goal_route, idea_ripe, ideas, pitches

JOIN_CHARS = 2_000          # a goal's words are kept this long when another idea joins it: small goals land better (decisions §242.4)
MIN_SHARED = 2              # the words two goals must share, whatever their score
BAR = 0.30                  # the score a match needs by its words alone
BAR_ROUTE = 0.20            # … when the two routes name the same parties
BAR_PART = 0.15             # … and both point at a same place of a map
STOP = frozenset("""a about above add after again all also an and any are as at be because been before being but by can could did do does done for from get had has have her here his how
if in into is it its just like make makes making may more most much must new not now of off on one only or other our out over please should so some such than that the their them then there these they
this those to too under up use used using want wants was we were what when where which while who will with without would you your""".split())
_WORD = re.compile(r"[a-z0-9]+")
_ENDINGS = ("ing", "ed", "es", "s")


def _stem(word: str) -> str:
    for end in _ENDINGS:
        if word.endswith(end) and len(word) - len(end) >= 3:
            return word[:-len(end)]
    return word


def words(text: object) -> set[str]:
    """The significant words of a text: its lower-case letters-and-digits runs of three characters or more (the first `JOIN_CHARS` characters), the stop words left out, each with a
    trailing *ing*, *ed*, *es* or *s* taken off while three characters stay."""
    return {_stem(w) for w in _WORD.findall(str(text or "")[:JOIN_CHARS].lower()) if len(w) >= 3 and w not in STOP}


def _parties(route: Iterable[Any], home: str) -> list[str]:
    out = [r.get("party") if isinstance(r, dict) else r for r in route or ()]
    return [p for p in dict.fromkeys(out) if p] or ([home] if home else [])


def _places(marks: Iterable[Any]) -> set[tuple[str, str]]:
    return {(str(m.get("map") or ""), str(m.get("id") or m.get("group") or "")) for m in marks or () if isinstance(m, dict) and (m.get("id") or m.get("group"))}


def candidates(root: Path, state_dir: Path) -> list[dict]:
    """The goals lying face down before their spec (`goal_refine.in_analysis`), in the Orkmaster's order (`goal_route.context`): not a goal of an Ideation party (a pitch), not a
    `release`, not a decision worded and put off (`ripe.held`: it lies in *At work · later*). `[{slug, title, party, state}]`."""
    found = ideas.ideas(root)
    states = {i["slug"]: ideas.state(state_dir, i["slug"]) for i in found}
    order = goal_route.context(found, states)["order"]
    out = []
    for i in found:
        st = states[i["slug"]]
        if not goal_refine.in_analysis(state_dir, i["slug"]) or pitches.is_ideation(root, i["track"]) or goal_route.type_id(st) == "release":
            continue
        if st["state"] == "decided" and (idea_ripe.of(state_dir, i["slug"]) or {}).get("held"):
            continue
        out.append({"slug": i["slug"], "title": i["title"], "party": i["track"], "state": st["state"], "_at": order.get(i["slug"], len(order) + 1)})
    return [{k: v for k, v in c.items() if k != "_at"} for c in sorted(out, key=lambda c: c["_at"])]


def _route_parties(state_dir: Path, slug: str, home: str) -> list[str]:
    return _parties(ideas.state(state_dir, slug)["route"], home)


def fits(root: Path, state_dir: Path, slug: str, text: str, parties: Iterable[str]) -> bool:
    """Joining `text` into the goal `slug` stays small (decisions §242.4): it adds no more than one party to the goal's route (`parties`: the new goal's), and its Gist, the line
    `Added: <text>` and two line breaks stay within `JOIN_CHARS`."""
    page = ideas.idea_page(root, slug)
    if page is None:
        return False
    have = set(_route_parties(state_dir, slug, str(page.get("track") or "")))
    if len(set(parties) - have) > 1:
        return False
    return len(page.section("Gist")) + len(goal_refine.added(text)) + 2 <= JOIN_CHARS


def match(root: Path, state_dir: Path, text: str, route: Iterable[Any], marks: Iterable[Any] = (), home: str = "") -> dict | None:
    """The face-down goal the new goal `text` looks like part of, or None. `route`: the new goal's route (`[{party}]`, empty where code found none), `home` its party then; `marks`: the places of a map
    it points at. `{idea, title, party, state, shared (the words, sorted), score, why: ["words", "route"?, "part"?], adds: [the party it would add]}`: the best score that reaches its bar and is
    small enough to join (`fits`); a tie goes to the earlier in the Orkmaster's order."""
    mine, parties, places = words(text), _parties(route, home), _places(marks)
    if len(mine) < MIN_SHARED:
        return None
    found = []
    for n, c in enumerate(candidates(root, state_dir)):
        page = ideas.idea_page(root, c["slug"])
        if page is None:
            continue
        theirs = words(f"{c['title']} {page.section('Gist')}")
        shared = mine & theirs
        if len(shared) < MIN_SHARED:
            continue
        score = 2 * len(shared) / (len(mine) + len(theirs))
        on = _route_parties(state_dir, c["slug"], c["party"])
        same_route = bool(parties) and set(parties) == set(on)
        same_part = same_route and bool(places & _places(ideas.state(state_dir, c["slug"])["marks"]))
        bar = BAR_PART if same_part else BAR_ROUTE if same_route else BAR
        if score >= bar:
            found.append((-score, n, c, shared, ["words", *(["route"] if same_route else []), *(["part"] if same_part else [])], [p for p in parties if p not in on]))
    for _s, _n, c, shared, why, adds in sorted(found, key=lambda f: (f[0], f[1])):
        if fits(root, state_dir, c["slug"], text, parties):
            return {"idea": c["slug"], "title": c["title"], "party": c["party"], "state": c["state"], "shared": sorted(shared), "score": round(-_s, 3), "why": why, "adds": adds}
    return None
