"""The project's running and the person's Team (docs/specs/92-running-and-the-team.md, decisions §108) as `gui/ideas.py`'s `Ideas` has them.

    ideas.repeat {slug, every, words?}   # a goal comes back every "day", "week" or "month" once it is done; "" stops it
    ideas.team                           # {at: "" | "here" | <project>, party, name}: where the person's Team party is (Operations are the person's, decisions §51)

The recurring goals a running party proposes (`ideas.party_presets` rows' `routines`) are added when the party is made (`goal_save {routines: [ids]}`), each a goal of the
party with a repeat; the host's clock renews a done one when its period has passed (`routines_tick`, realm/recurring.py). Only one Team party may exist across the person's
projects: `goal_save` refuses a second (*Team is in <project>*), and the note of which project it is in (realm/ops_team.py) lives with Operations' state in the person's folder.
Split from ideas.py to keep it under ~600 lines.
"""
from __future__ import annotations

import datetime as dt
import logging

from orkboard.gui.ideas_args import IdeasError, _opt, _text
from orkboard.realm import goal_team, ideas, ops_team, party_presets, party_recipes, recurring

log = logging.getLogger(__name__)
ROUTINES_S = 60.0                      # the clock looks for a recurring goal that is due this often


class RunningMixin:
    # -- the person's Team party ---------------------------------------------------------------------------------------

    def _ops_base(self):
        ops = getattr(self.host, "ops", None)
        return getattr(ops, "base", None)

    def team_at(self) -> str:
        """Where the person's Team party is: "" nowhere (or this host has no Operations), "here", or the other project's name."""
        base = self._ops_base()
        if base is None:
            return ""
        self.team_heal()
        return ops_team.where(base, self.host.repo_root)

    def team_heal(self) -> None:
        """The person's note says the Team party is in this project but the Board has parties and none is it (its file was removed by hand): the note goes, and Operations are in the left
        column again. A Board with no parties yet (its tree is still being made) is left alone."""
        base = self._ops_base()
        got = ops_team.get(base) if base is not None else None
        if got is None or got["project"] != str(self.host.repo_root):
            return
        here = ideas.tracks(self.root(False), make=False)
        if here and not any(t["slug"] == got["party"] and party_recipes.is_team(t) for t in here):
            ops_team.clear(base, got["project"], got["party"])

    def team_refuse(self) -> None:
        """A second Team party is refused, in plain words: *Team is in <project>*."""
        if self.team_at():
            raise IdeasError(party_presets.team_words(self.team_at()))

    def team_made(self, slug: str) -> None:
        """The Team party was saved here: the person's note says where it is. The left column and the phone read it from the snapshot."""
        base = self._ops_base()
        if base is None:
            return
        ops_team.set(base, self.host.repo_root, self.host.repo_root.name, slug)
        self.host.ops.moved()

    def team_dropped(self, slug: str) -> None:
        """A party was removed here: when it was the Team party the note goes, and Operations are in the left column again."""
        base = self._ops_base()
        if base is not None and ops_team.clear(base, self.host.repo_root, slug):
            self.host.ops.moved()

    def team(self, args: dict) -> dict:
        """`ideas.team`: where the Team party is, to say so: `{at, party, name}`; `at` is "" with none, "here" or the project's name."""
        got = ops_team.get(self._ops_base()) if self._ops_base() is not None else None
        return {"at": self.team_at(), "party": (got or {}).get("party", ""), "name": (got or {}).get("name", "")}

    # -- recurring goals -------------------------------------------------------------------------------------------------

    def running_made(self, party: str, recipe: str, routines: list[dict], args: dict) -> None:
        """A new party of a recipe that has to be told of (the Team party, a running party with recurring goals): the recipe kept, Team's note written, the goals added."""
        if party_recipes.get(recipe) is not None and not goal_team.recipe_of(self.root(), party):
            goal_team.set_recipe(self.root(), party, recipe)
        if recipe == party_recipes.TEAM_ID:
            self.team_made(party)
        if routines:
            self.routines_started(party, routines, args)

    def routines_asked(self, args: dict, recipe: str) -> list[dict]:
        """`routines` of `ideas.goal_save` (spec 92 §2): the ids of the recurring goals the recipe proposes that the person kept; refused: *No recurring goal <id>*."""
        ids = args.get("routines")
        if ids is None:
            return []
        if not isinstance(ids, list) or not all(isinstance(i, str) for i in ids):
            raise IdeasError("routines are a list of ids")
        out = []
        for rid in dict.fromkeys(ids):
            r = recurring.get(recipe, rid)
            if r is None:
                raise IdeasError(f"No recurring goal {rid}")
            out.append(r)
        return out

    def routines_started(self, party: str, routines: list[dict], args: dict) -> list[str]:
        """Each kept recurring goal added to the new party as the person's New goal is (drafted at once), with its repeat; the slugs."""
        out = []
        for r in routines:
            got = self.add({"text": recurring.text_of(r), "track": party, "device": args.get("device")})
            recurring.set_every(self.root(), got["slug"], r["every"], recurring.text_of(r))
            out.append(got["slug"])
        return out

    def repeat(self, args: dict) -> dict:
        """`{slug, every, words?}`: a goal comes back "day", "week" or "month" after it is done; "" stops it."""
        slug, every = _text(args, "slug", 100), _opt(args, "every")
        if ideas.idea_page(self.root(False), slug) is None:
            raise IdeasError("That goal is gone")
        try:
            recurring.set_every(self.root(), slug, every, _opt(args, "words"))
        except ValueError as e:
            raise IdeasError(str(e)) from None
        self.changed(slug)
        return {"ok": True, "every": recurring.every_of(self.root(False), slug)}

    def routines_tick(self, now: float) -> None:
        """From the host's clock, at most every `ROUTINES_S`: each recurring goal that is due is added again."""
        if now - getattr(self, "_routines_at", float("-inf")) < ROUTINES_S:
            return
        self._routines_at = now
        root = self.keeper_root()                       # a project with no pages has no tree made for it
        for slug in recurring.due(root, self.state_dir, dt.datetime.now()):
            self.routines_renew(slug)

    def routines_renew(self, slug: str) -> str:
        """A done recurring goal comes back: a goal with the same words in the same party, which carries the repeat from now on; "" when it could not (the repeat then
        waits another period)."""
        root = self.root()
        page = ideas.idea_page(root, slug)
        every = recurring.every_of(root, slug)
        if page is None or not every:
            return ""
        track, words = page.get("track") or ideas.GENERAL, recurring.words_of(root, slug)
        if track == ideas.GENERAL or not any(t["slug"] == track for t in ideas.tracks(root, make=False)):
            recurring.set_every(root, slug, "")             # its party is gone (its goals moved to General): the repeat ends with it
            return ""
        try:
            recurring.set_every(root, slug, "")                  # first stopped on the old one, so a failure below never adds a second
            got = self.add({"text": words, "track": track, "priority": page.get("priority")})
            recurring.set_every(root, got["slug"], every, words)
        except Exception as e:                                    # a disk that refuses, a spent window: the repeat goes on from the old goal
            log.info("recurring goal %s did not come back: %s", slug, e)
            if ideas.idea_page(root, slug) is not None:
                recurring.set_every(root, slug, every, words)
            return ""
        return got["slug"]
