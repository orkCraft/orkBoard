"""A leader's say, taken (docs/specs/168 §C1, §C2; decisions §283.23–§283.25), as `gui/ideas.py`'s `Ideas` has it: what the person does with the `better` and the `needs` of an idea's leaders
(`realm/idea_say.py` keeps it; the Board's row is the idea node's `say`, `realm/board_map.py`).

    ideas.take_better {idea, id}          # a leader's better taken: the Orkmaster rewrites the goal's words (`core/idea_rewrite.py`); {ok, idea, id, rewriting, why?}
    ideas.take_way {idea, id, way}        # a need's way taken (`way`: its index in the need's `ways`): the same; a need of the old questions (kind question, `legacy`) is answered by `ideas.talk_answer`
    ideas.leave_say {idea, id}            # a better or a need turned down: its leader is judged again; {ok, idea, id, rewriting: false}
    ideas.undo_rewrite {idea}             # the last rewrite put back, the goal's words exactly as they were; {ok, idea, id}
    ideas.say_fork {idea, pick}           # the choice on the fork (what was taken disagrees): the rewrite goes on with it; {ok, idea, rewriting, why?}
    ideas.judge_again {idea}              # *Judge again now*: what was taken is written, then the leaders that doubted or said no, whose proposal was turned down or whose part was touched
                                          # judge again, twice at most, then a hearing; {ok, idea, parties}

A refusal is an `IdeasError` in the keeper's plain words. The faces are told by the goal's change (`changed`), as for every step of the keeper; events: `say_answered`, `goal_rewritten`,
`rewrite_forked`, `rewrite_undone`, `judged_again`.
"""
from __future__ import annotations

from typing import Any

from orkboard.core.idea_keeper import KeeperError
from orkboard.gui.ideas_args import IdeasError, _text


class Say:
    """The say's commands, over the Board's `Ideas` (its keeper and `changed`)."""

    def __init__(self, ideas_: Any) -> None:
        self.i = ideas_

    def _go(self, fn, args: dict, *more: Any) -> dict:
        slug = _text(args, "idea", 100)
        try:
            got = fn(slug, *more)
        except KeeperError as e:
            raise IdeasError(str(e)) from None
        self.i.changed(slug)
        return {"ok": True, "idea": slug, **got}

    def take_better(self, args: dict) -> dict:
        ident = _text(args, "id", 100)
        got = self._go(lambda slug: self.i.keeper.say_take(slug, ident), args)
        return {"ok": True, "idea": got["idea"], "id": ident, "rewriting": got["rewriting"], **({"why": got["why"]} if got.get("why") else {})}

    def take_way(self, args: dict) -> dict:
        ident, way = _text(args, "id", 100), args.get("way")
        if not isinstance(way, int) or isinstance(way, bool):
            raise IdeasError("way is the index of the way taken")
        got = self._go(lambda slug: self.i.keeper.say_take(slug, ident, way), args)
        return {"ok": True, "idea": got["idea"], "id": ident, "way": way, "rewriting": got["rewriting"], **({"why": got["why"]} if got.get("why") else {})}

    def leave_say(self, args: dict) -> dict:
        ident = _text(args, "id", 100)
        got = self._go(lambda slug: self.i.keeper.say_leave(slug, ident), args)
        return {"ok": True, "idea": got["idea"], "id": ident, "rewriting": False}

    def undo_rewrite(self, args: dict) -> dict:
        got = self._go(self.i.keeper.unrewrite, args)
        return {"ok": True, "idea": got["idea"], "id": got["id"]}

    def say_fork(self, args: dict) -> dict:
        pick = args.get("pick")
        if not isinstance(pick, int) or isinstance(pick, bool):
            raise IdeasError("pick is the index of the choice")
        got = self._go(lambda slug: self.i.keeper.say_fork(slug, pick), args)
        return {"ok": True, "idea": got["idea"], "rewriting": got["rewriting"], **({"why": got["why"]} if got.get("why") else {})}

    def judge_again(self, args: dict) -> dict:
        got = self._go(lambda slug: self.i.keeper.judge_again(slug, True), args)
        return {"ok": True, "idea": got["idea"], "parties": got["parties"]}


def say_commands(ideas_: Any) -> dict:
    """The say's commands by name (`gui/ideas.py` adds them to its table: `**say_commands(self)`)."""
    s = Say(ideas_)
    return {"ideas.take_better": s.take_better, "ideas.take_way": s.take_way, "ideas.leave_say": s.leave_say, "ideas.undo_rewrite": s.undo_rewrite, "ideas.say_fork": s.say_fork,
            "ideas.judge_again": s.judge_again}
