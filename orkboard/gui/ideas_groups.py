"""The backlog's groups (docs/specs/135-a-new-goal-matched-against-the-face-down-pile.md §B.2–B.3; decisions §242.5, §239), as `gui/ideas.py`'s `Ideas` has it: the queue's wait and the card's three
commands. The call is the keeper's (`core/idea_groups.py`), the record `realm/backlog_groups.py`'s; its Needs you row is `kind: "groups"` (`realm/board_rows.py` lays it, a row of no goal's).
Nothing is joined without the person's yes.

    ideas.groups_answer {id, join?: [group id], apart?: [group id]}   # every group of the card is answered, an unnamed one is *Keep apart*. **Join**: the first goal in the Orkmaster's order takes the
                                                   #   others' words (`add_words`, the rune of each kept in the added-words record, `via: "groups"`), its decision worded again once where it is worded
                                                   #   (`keeper.reword`), then each other goal is dropped as `ideas.drop` drops one, its journal line *joined into <title>*. A group with a goal that is not
                                                   #   in analysis any more (or is busy) is kept apart alone, the others join. {ok, joined: [{idea, dropped: [slug], reworded, cost?}], apart: [{id, why?}]}
    ideas.groups_now {}                            # **Not now**: nothing joined, the groups are not asked again at this reset. {ok}
    ideas.groups_open {id, open}                   # the face says the card lies lifted or put down; the queue waits for it only while it lies lifted, at most LIFT_S. {ok}
"""
from __future__ import annotations

import time
from typing import Any

from orkboard.core.idea_keeper import KeeperError
from orkboard.gui.ideas_args import IdeasError, _text
from orkboard.realm import backlog_groups, event_log, goal_refine, goal_route, idea_element, ideas

GONE = "A goal of it is not in analysis any more"


class GroupsMixin:
    # -- the queue's wait (§239) ----------------------------------------------------------------------------------------------------------------

    def groups_wait(self, states: dict, ripe: list[str], order: dict, wall: float) -> bool:
        """True while the queue waits in front of the groups: the call is running, or the card of this reset lies lifted (and fresh). Asks the call itself the first time a reset has two goals ripe or
        more and no record: once for a reset, never twice (the process remembers a call it began or could not make). A card not lifted, answered or gone stale never holds the queue."""
        if len(ripe) < 2:
            return False
        rec = backlog_groups.read(self.state_dir)
        key = backlog_groups.reset_key(states[s]["held_until"] for s in ripe)
        if backlog_groups.asked(rec, key):
            return backlog_groups.lifted(rec, wall)
        if self.keeper.busy("groups"):
            return True
        if self.__dict__.get("_groups_tried") == key:
            return False
        self.__dict__["_groups_tried"] = key
        root = self.root(False)
        goals = []
        for s in sorted(ripe, key=lambda s: order.get(s, len(order) + 1))[:backlog_groups.GOALS_MAX]:
            page = ideas.idea_page(root, s)
            if page is not None:
                goals.append({"slug": s, "title": page.title, "party": str(page.get("track") or ""), "parties": backlog_groups.parties_of(root, self.state_dir, s)})
        return self.keeper.groups_begin(key, goals)

    # -- the card -------------------------------------------------------------------------------------------------------------------------------

    def _groups_ready(self, rid: str) -> dict:
        rec = backlog_groups.read(self.state_dir)
        if not rec or rec["status"] != "ready" or rec["reset"] != rid:
            raise IdeasError("No goals wait to be joined")
        return rec

    def _group_ids(self, rec: dict, args: dict, key: str) -> set[str]:
        got = args.get(key)
        if got is None:
            return set()
        have = {g["id"] for g in rec["groups"]}
        if not isinstance(got, list) or not all(isinstance(x, str) and x in have for x in got):
            raise IdeasError(f"{key} names the groups of the card")
        return set(got)

    def _group_order(self, slugs: list[str]) -> list[str]:
        found = ideas.ideas(self.root(False))
        order = goal_route.context(found, {i["slug"]: ideas.state(self.state_dir, i["slug"]) for i in found})["order"]
        return sorted(slugs, key=lambda s: order.get(s, len(order) + 1))

    def _group_ready(self, slugs: list[str]) -> list[str]:
        """The goals of the group in the Orkmaster's order; IdeasError in plain words when one of them cannot be joined now."""
        for s in slugs:
            if ideas.idea_page(self.root(), s) is None or not goal_refine.in_analysis(self.state_dir, s) or self.keeper.is_pitch(s):
                raise IdeasError(GONE)
            if self.keeper.busy(s):
                raise IdeasError("The keeper is busy with a goal of it: a moment")
        ordered = self._group_order(slugs)
        if not backlog_groups.fits_group(self.root(False), self.state_dir, ordered):
            raise IdeasError("Joined, these goals would be too big")
        return ordered

    def _join_group(self, slugs: list[str]) -> dict:
        """One group joined: the first takes the others' words, its decision worded again once, the others dropped."""
        root = self.root()
        first, rest = slugs[0], slugs[1:]
        title = ideas.idea_page(root, first).title
        self._refinable(first)
        taken = []
        for s in rest:
            text, element = goal_refine.words(ideas.idea_page(root, s)).strip(), idea_element.of(self.state_dir, s)
            self.add_words(first, text, element, "groups")
            taken.append(s)
            self._ev(event_log.GOAL_ADDED_TO, {}, idea=first, chars=len(text), reworded=False, via="groups", element=element)
        out: dict[str, Any] = {"idea": first, "dropped": taken, "reworded": False}
        if self._decision_of(first) is not None:
            try:
                self.keeper.reword(first)
                out.update(reworded=True, cost=self._cost_of_word(first))
            except KeeperError as e:                           # the words are kept; the decision keeps its old wording
                out["why"] = str(e)
        for s in taken:
            self.drop({"slug": s, "why": f"joined into {title}"})
        self.changed(first)
        return out

    def groups_answer(self, args: dict) -> dict:
        rid = _text(args, "id", 100)
        rec = self._groups_ready(rid)
        join, apart = self._group_ids(rec, args, "join"), self._group_ids(rec, args, "apart")
        if join & apart:
            raise IdeasError("A group is joined or kept apart, not both")
        joined, kept, answers = [], [], {}
        for g in rec["groups"]:
            if g["id"] not in join:
                answers[g["id"]] = "apart"
                kept.append({"id": g["id"]})
                continue
            try:
                ordered = self._group_ready(g["goals"])
                joined.append(self._join_group(ordered))
                answers[g["id"]] = "join"
            except (IdeasError, KeeperError) as e:             # that group alone is kept apart, the others join
                answers[g["id"]] = "apart"
                kept.append({"id": g["id"], "why": str(e)})
        backlog_groups.update(self.state_dir, rid, status="answered", open=False, open_at="",
                              groups=[{**g, "answer": answers.get(g["id"], "apart")} for g in rec["groups"]])
        self._ev(event_log.GROUPS_ANSWERED, args, joined=len(joined), apart=len(kept), dropped=sum(len(j["dropped"]) for j in joined), not_now=False)
        self.changed("")
        return {"ok": True, "joined": joined, "apart": kept}

    def groups_now(self, args: dict) -> dict:
        """**Not now**: nothing is joined; the groups are not asked again at this reset."""
        rid = _text(args, "id", 100) if args.get("id") else ""
        rec = backlog_groups.read(self.state_dir)
        if not rec or rec["status"] != "ready" or (rid and rec["reset"] != rid):
            return {"ok": True}
        backlog_groups.update(self.state_dir, rec["reset"], status="none", open=False, open_at="")
        self._ev(event_log.GROUPS_ANSWERED, args, joined=0, apart=len(rec["groups"]), dropped=0, not_now=True)
        self.changed("")
        return {"ok": True}

    def groups_open(self, args: dict) -> dict:
        rid, up = _text(args, "id", 100), args.get("open")
        if not isinstance(up, bool):
            raise IdeasError("open is true or false")
        backlog_groups.set_open(self.state_dir, rid, up)
        return {"ok": True}


def groups_commands(ideas_: Any) -> dict:
    """The groups' commands by name (`gui/ideas.py` adds them to its table: `**groups_commands(self)`)."""
    return {"ideas.groups_answer": ideas_.groups_answer, "ideas.groups_now": ideas_.groups_now, "ideas.groups_open": ideas_.groups_open}
