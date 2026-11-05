"""The Map (docs/specs/39-map.md §2) as `gui/ideas.py`'s `Ideas` has it: `ideas.map`, a view of what the Board holds
(realm/board_map.py). It changes nothing, but for one thing: a goal of before has no element (spec 50 §2.3), and the first
time the Map reads it one is given and stored (once, ever; `ideas_rev` does not move). A party carries its goal types (spec 52
§2.4: its leader's set, the most used first, with what each misses of the party), read here with the map: the pure
`board_map.build` reads no runs. Split from ideas.py to keep it under ~600 lines.

A party carries what its tab needs besides (spec 111 B): `free_elements`, the shapes no goal of the project holds (the + card's free runes and the field's row; empty
when none is free; a rune is unique across the project, spec 128 G), beside `next_element` (a shape), `next_hue`, and `next_hues` (every shape's predicted hue, in ELEMENTS order); and its sword and shield (decisions §189): `does_tool` and `checks_tool`, the AI tools its Does and its Checks run on (a
`harnesses` id, the Main tool resolved), `does_mixed` / `checks_mixed` when a column's roles run on more than one, and `lean` (no separate check: `checks_tool` is ""); and, per side,
whether it follows the default tool (spec 114 B, decisions §192.4): `does_default`, `checks_default` (neither the party nor any seat of that side is set to a tool; a Lean party's check never is).

A task done or at Review carries `craft_made` (spec 142 D, decisions §249.3; `made_for`, realm/task_made.py): what it made by its party's craft, read by code, the key absent where a craft has none.
"""
from __future__ import annotations

import time
from collections import Counter
from pathlib import Path

from orkboard import settings as machine
from orkboard.gui import media
from orkboard.gui.ideas_args import IdeasError, _opt
from orkboard.realm import board_map, collide, goal_team, goal_types, hypotheses, idea_element, idea_photos, ideas, library, orkmaster, party_recipes, task_made


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
        # the runes the project's goals hold (open, or done and its result not yet seen: `idea_element.holds`), as they are given; one party's Map reads the others' from their states
        used: list[tuple[str, str]] = ([(n["element"], n["hue"]) for n in got["nodes"] if n["element"] and (n["state"] != "done" or not n["seen"])]
                                       if goal is None else idea_element.open_runes(root, self.state_dir))
        for n in got["nodes"]:
            for t in n["tasks"]:                                         # a task's picture gets its signed address (spec 85 §3)
                if t.get("shot") and not t["shot"].get("none"):
                    t["shot"] = {**t["shot"], "url": media.url(n["slug"], t["shot"]["id"], t["shot"]["file"])}
            n["results"] = waiting.get(n["slug"], [])
            if not n["element"]:                                         # a goal of before: one is given now, once
                try:
                    n["element"] = idea_element.give(root, self.state_dir, n["slug"], used)
                except (OSError, ValueError):
                    continue                                             # a disk that refuses: the faces draw it dim, the next read tries again
                n["hue"] = idea_element.hue_of(self.state_dir, n["slug"])
                if n["state"] != "done" or not n["seen"]:
                    used.append((n["element"], n["hue"]))
        self.made_for(got)
        self.pictures_for(got)
        main = machine.main_tool(getattr(self.host, "machine", None))              # what a party with no tool of its own runs on
        next_element, next_hue = idea_element.pick_rune(used)                           # what a new goal would be given (`idea_element.next_rune_for`, from the runes read above)
        free_elements = idea_element.free([e for e, _h in used])                        # the shapes no goal holds (`idea_element.free_for`): [] when none is free
        next_hues = {shape: idea_element.pick_hue(used, shape) for shape in idea_element.ELEMENTS}  # predictions only; includes the legacy assignments above
        for g in got["goals"]:
            g["next_element"], g["next_hue"], g["free_elements"] = next_element, next_hue, free_elements       # the project's, the same at every party
            g["next_hues"] = next_hues
            g.update(self.marks_of(g, main))                                                # its sword and shield on its tab (decisions §189)
            g["types"] = self.types_of(root, g["slug"], [n["slug"] for n in got["nodes"] if n["goal"] == g["slug"]])
            g["stages"] = self.stages_of(root, g["slug"])
            g["concerns"] = self.concerns_counts(g["slug"])                              # its leader's concerns on its map, for its tab (spec 108 §2.5)
            g["ops"] = goal_team.recipe_of(root, g["slug"]) == party_recipes.TEAM_ID         # the Team party: its Board is the person's Operations (spec 92 §3)
        got["project"] = self.project_of(root, got, goal)
        return got

    def pictures_for(self, got: dict) -> None:
        """A goal's node carries `picture` (a signed address) when it has an attached photo the card can show (realm/idea_photos.py `thumb`, spec 148 A); the key is absent otherwise."""
        for n in got["nodes"]:
            try:
                shown = idea_photos.thumb(self.state_dir, n["slug"])
            except (OSError, ValueError):
                shown = None
            if shown is not None:
                n["picture"] = media.photo_url(n["slug"], shown.name)

    def made_for(self, got: dict) -> None:
        """Each task done or at Review gets `craft_made` by its party's craft (realm/task_made.py, spec 142 D): Tech's files and Art's image from git (cached per tip commit), Design's shot (signed
        above), Release's checks on the way into main, Product's hypothesis. Never a failure of the Map: a kind that cannot be read leaves the key out."""
        craft = {g["slug"]: g.get("party_craft") or "" for g in got["goals"]}
        wanted = [(n, t) for n in got["nodes"] for t in n["tasks"] if t.get("state") in task_made.MADE_STATES and craft.get(n["goal"])]
        if not wanted:
            return
        checks = self.main_checks_now() if any(craft[n["goal"]] == "release" for n, _t in wanted) else {}
        hyps = hypotheses.read(self.state_dir)["items"] if any(craft[n["goal"]] == "product" for n, _t in wanted) else []
        for n, t in wanted:
            kind, made = craft[n["goal"]], None
            try:
                if kind in ("tech", "art"):
                    made = task_made.git_made(Path(self.host.repo_root), n["slug"], t, kind, media.asset_url)
                elif kind == "design":
                    made = task_made.screen_of("", (t.get("shot") or {}).get("url") or "")
                elif kind == "release":
                    made = task_made.checks_of(checks.get(n["slug"]))
                elif kind == "product":
                    made = task_made.hypothesis_of(hyps, n["slug"])
            except (OSError, ValueError, KeyError):
                made = None
            if made:
                t["craft_made"] = made

    @staticmethod
    def marks_of(g: dict, main: str) -> dict:
        """The tools of a party's sword and shield (decisions §189.1): `{does_tool, checks_tool, does_mixed, checks_mixed, lean, does_default, checks_default}`. A seat runs on its own tool,
        else the party's (`goal_team.tool_for`), else the Main tool `main`; **Does** is the tool most of its doing seats run on (its leader's when it has none), **Checks** the tool most
        of its checking seats run on (its leader's when none checks: the leader checks, `goal_team.checkers`); a column that mixes tools is `*_mixed`. A **Lean** party has no
        separate check: `lean`, and `checks_tool` is "" (the shield stands faint, no mark). A side **follows the default** (`does_default`, `checks_default`; decisions §192.4) when
        the party has no tool and no seat of that side has one of its own: it goes where the work goes, the tool now (`town.mana.now`, which the page puts on the mark; the Main tool
        here stands for it). A Lean party's check follows nothing."""
        mine = goal_team.clean_tools(g.get("tools") or {})
        set_of = lambda agent: mine.get(agent) or g.get("tool") or ""                  # noqa: E731  (a tool set on purpose; "" follows the default)
        of = lambda agent: set_of(agent) or main                                       # noqa: E731  (`tool_for`, from what the map has read, the Main tool at the end)
        squad = [m["slug"] for m in g.get("team") or []]
        lead = (g.get("leader") or {}).get("slug") or "taskmaster"
        does_seats = [s for s in squad if goal_team.band_of(s) != "check"] or [lead]
        checks_seats = [s for s in squad if goal_team.band_of(s) == "check"] or [lead]
        does, checks = [of(s) for s in does_seats], [of(s) for s in checks_seats]
        lean = g.get("size") == "lean"
        most = lambda tools: Counter(tools).most_common(1)[0][0]                       # noqa: E731  (ties: the first seat's)
        return {"does_tool": most(does), "does_mixed": len(set(does)) > 1, "checks_tool": "" if lean else most(checks), "checks_mixed": not lean and len(set(checks)) > 1, "lean": lean,
                "does_default": not any(set_of(s) for s in does_seats), "checks_default": not lean and not any(set_of(s) for s in checks_seats)}

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
