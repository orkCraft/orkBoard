"""Heat and reach, as `gui/ideas.py`'s `Ideas` serves them (docs/specs/165-each-leaders-map-a-board-games-shape.md; decisions §280.1, §281.6): what code found on each part of a party's map,
and what each goal not yet started would change on it, one and two steps out. Read once per Board change in a thread of its own (`realm/map_reach.py`), never on a request. Keys and data, never words.

    ideas.heat {party}     # → {party, map, heat: [{on, kind}]}: every hint of the party's craft that sits on one of its parts, uncut
    ideas.reach {party}    # → {party, map, goals: {slug: {lit, one, two, no_test}}}: the parts of the party's map each goal's *Will be* names (`lit`), those one and two steps out, and those with no test

Both answer what was kept at the last read (empty before the first, for a party gone or with no map, or a map that cannot be read): a request runs no git and never waits. When `self.rev` has moved
past the last read, one thread (never two) reads again: dev's head through `commit_goal.head`, then each party's heat and reach, and the page asks again on the Board's next change.
"""
from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from orkboard.gui.ideas_args import _str
from orkboard.realm import commit_goal, ideas, map_parts, map_reach


class ReachMixin:
    def _reach_kept(self) -> map_reach.Kept:
        return self.__dict__.setdefault("_reach_memory", map_reach.Kept())

    def _reach_lock(self) -> threading.Lock:
        return self.__dict__.setdefault("_reach_lock_", threading.Lock())

    def _reach_refresh(self, rev: int) -> None:
        """Read again at `rev`: the thread's body. Never raises."""
        try:
            pages, repo, state = self.root(make=False), Path(self.host.repo_root), self.state_dir
            ref = self._ref()

            def compute(what: str, party: str) -> object:
                craft = map_parts.craft_of(pages, party)
                if what == "heat":
                    return map_reach.heat(state, repo, craft, pages, ref)
                return map_reach.reach(state, repo, pages, party, craft, ref)

            self._reach_kept().refresh(rev, lambda: commit_goal.head(repo, ref), compute)
        except Exception:
            pass
        finally:
            with self._reach_lock():
                self.__dict__["_reach_busy"] = False

    def _reach_ask(self, party: str) -> tuple[str, str]:
        """Track every party with a map, start the one refresh a moved Board needs (at most one at a time), and give `(party, map id)` of the one asked, or `(party, "")`."""
        pages = self.root(make=False)
        try:
            slugs = [t["slug"] for t in ideas.tracks(pages, make=False)]
        except (OSError, ValueError):
            slugs = []
        kept = self._reach_kept()
        for slug in slugs:
            if map_parts.craft_of(pages, slug) in map_parts.MAPS:
                kept.track("heat", slug)
                kept.track("reach", slug)
        with self._reach_lock():
            if self.__dict__.get("_reach_rev") != self.rev and not self.__dict__.get("_reach_busy"):
                self.__dict__["_reach_busy"] = True
                self.__dict__["_reach_rev"] = self.rev
                threading.Thread(target=self._reach_refresh, args=(self.rev,), daemon=True, name="ideas-reach").start()
        if party not in slugs:
            return party, ""
        return party, map_parts.MAPS.get(map_parts.craft_of(pages, party), "")

    def heat(self, args: dict) -> dict:
        party, map_id = self._reach_ask(_str(args, "party", 100).strip())
        got = self._reach_kept().answer("heat", party) if map_id else None
        return {"party": party, "map": map_id, "heat": list(got or [])}

    def reach(self, args: dict) -> dict:
        party, map_id = self._reach_ask(_str(args, "party", 100).strip())
        got = self._reach_kept().answer("reach", party) if map_id else None
        return {"party": party, "map": map_id, "goals": dict(got or {})}


def reach_commands(ideas_: Any) -> dict:
    """Heat and reach (`gui/ideas.py` adds them to its table: `**reach_commands(self)`)."""
    return {"ideas.heat": ideas_.heat, "ideas.reach": ideas_.reach}
