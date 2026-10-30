"""The Map (docs/specs/39-map.md §2) as `gui/ideas.py`'s `Ideas` has it: `ideas.map`, a view of what the Board holds
(realm/board_map.py). It changes nothing, but for one thing: a goal of before has no element (spec 50 §2.3), and the first
time the Map reads it one is given and stored (once, ever; `ideas_rev` does not move). A party carries its goal types (spec 52
§2.4: its leader's set, the most used first, with what each misses of the party), read here with the map: the pure
`board_map.build` reads no runs. Split from ideas.py to keep it under ~600 lines.
"""
from __future__ import annotations

import time
from collections import Counter
from pathlib import Path

from orkboard.gui import media
from orkboard.gui.ideas_args import IdeasError, _opt
from orkboard.realm import board_map, collide, goal_team, goal_types, idea_element, ideas, library, orkmaster, party_recipes


class MapMixin:
    def map(self, args: dict) -> dict:
        """`{"goal"?}` one goal's slug (none: every goal): the Map of this project."""
        goal = _opt(args, "goal")
        root = self.root(False)
        if goal and not any(t["slug"] == goal and t["slug"] != ideas.GENERAL for t in ideas.tracks(root, make=False)):
            raise IdeasError("That party is gone")
        got = board_map.build(root, self.state_dir, self.settings_now(), list(self.host.limits() or []), time.time(), goal=goal,
                              rev=self.rev, state_of=self._state, goal_state_of=self.goal_state)
        waiting: dict[str, list[dict]] = {}
        if any(t["state"] == "review" for n in got["nodes"] for t in n["tasks"]):          # the results at Review, each on its idea (spec 48 §1)
            for r in self.results():
                waiting.setdefault(r["idea"], []).append(r)
        used: dict[str, list[str]] = {}                                  # each party's open goals' elements, as they are given
        for n in got["nodes"]:
            if n["element"] and n["state"] != "done":
                used.setdefault(n["goal"], []).append(n["element"])
        for n in got["nodes"]:
            for t in n["tasks"]:                                         # a task's picture gets its signed address (spec 85 §3)
                if t.get("shot") and not t["shot"].get("none"):
                    t["shot"] = {**t["shot"], "url": media.url(n["slug"], t["shot"]["id"], t["shot"]["file"])}
            n["results"] = waiting.get(n["slug"], [])
            if not n["element"]:                                         # a goal of before: one is given now, once
                try:
                    n["element"] = idea_element.give(root, self.state_dir, n["slug"], used.setdefault(n["goal"], []))
                except (OSError, ValueError):
                    continue                                             # a disk that refuses: the faces draw it dim, the next read tries again
                if n["state"] != "done":
                    used[n["goal"]].append(n["element"])
        for g in got["goals"]:
            g["next_element"] = idea_element.pick(used.get(g["slug"], []))                 # what a new goal of this party would be given (`idea_element.next_for`, from the elements read above)
            g["types"] = self.types_of(root, g["slug"], [n["slug"] for n in got["nodes"] if n["goal"] == g["slug"]])
            g["stages"] = self.stages_of(root, g["slug"])
            g["concerns"] = self.concerns_counts(g["slug"])                              # its leader's concerns on its map, for its tab (spec 108 §2.5)
            g["ops"] = goal_team.recipe_of(root, g["slug"]) == party_recipes.TEAM_ID         # the Team party: its Board is the person's Operations (spec 92 §3)
        got["project"] = self.project_of(root, got, goal)
        return got

    def project_of(self, root: Path, got: dict, goal: str | None) -> dict:
        """The project's level (spec 70 §1.1): the Orkmaster and its deal of the parties. The flags are counted from the nodes already read
        when the Map is the whole project's, else read for the project."""
        tracks = ideas.tracks(root, make=False)
        flags = None
        if not goal:
            shut = {t["slug"] for t in tracks if t["slug"] == ideas.GENERAL or (t.get("leader") or "") == library.INVESTOR}
            flags = Counter(n["goal"] for n in got["nodes"] if n["flag"] and n["goal"] not in shut)
        kind, facts = self.kind_now()                    # read by names, kept while the top level is as it was: no walk on every read (spec 75 §4.3)
        deal = orkmaster.deal_first(orkmaster.deal(root, self.state_dir, tracks=tracks, flags=flags), tracks, kind["id"], facts)
        return {"orkmaster": dict(orkmaster.ORKMASTER), "kind": kind, "deal": deal,
                "collisions": collide.collisions(root, self.state_dir, state_of=self._state),          # the open ones (spec 71 §8.4)
                "collide_week": collide.work(self.host.repo_root)}                                     # what its stops did in a week (spec 71 §5)

    @staticmethod
    def stages_of(root: Path, party: str) -> dict:
        """A party's stages (spec 59 §3): the words of its leader's three steps and the seats of its builders and checkers."""
        s = library.stages_of(goal_team.leader_of(root, party))
        return {"lead": {"word": s.lead}, "build": {"word": s.build, "seats": s.seats["build"]}, "check": {"word": s.check, "seats": s.seats["check"]}}

    def types_of(self, root: Path, party: str, goals: list[str]) -> list[dict]:
        """A party's goal types (spec 59 §4.5): what it is offered (`goal_types.offered`), each with what it misses of the party, the
        most used first (`used`: how many of its goals, of any state, have that type; an old key counts as its id), then those
        with nothing missing before those with someone missing, then the catalog's order."""
        p = goal_types.Party(self.state_dir, root, party)
        used = Counter(t.id for slug in goals if (t := goal_types.get(ideas.state(self.state_dir, slug).get("type"))) is not None)
        rows = [{"id": t.id, "name": t.name, "sign": t.sign, "line": t.line, "lens": t.lens,
                 "asks": [{"id": a.id, "label": a.label, "hint": a.hint} for a in t.asks], "refs": t.refs,
                 "used": used[t.id], "missing": missing}
                for t, missing in goal_types.offered(self.state_dir, root, party, read=p)]
        return sorted(rows, key=lambda r: (-r["used"], bool(r["missing"])))
