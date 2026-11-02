"""Passing a question on (docs/specs/128-the-orkmasters-column-and-a-goal-at-every-leader.md §D.2), as `gui/ideas.py`'s `Ideas` has it: the two commands the page's small card over the
Orkmaster's column asks by. The questions themselves are the keeper's (`core/idea_pass.py`) and the snapshot's `passing` is `keeper.passing_rows()`.

    ideas.pass_take {id}     # *Answer it myself*: the question is the person's now, dealt to the hand as any is
    ideas.pass_now {id}      # *Pass it now*: the party it is for answers it at once, in one call

`id` is a passing row's (`<idea>~<card id>`). Both answer `{"ok": true}`; a question not passing (answered, taken or gone) is an IdeasError in the keeper's words. The snapshot's
`passing` is `[{id, idea, task, by, to, q, left_s, answering}]`: `by` the party that asked, `to` the one it is passed to, `left_s` the seconds left to take it or pass it now.
"""
from __future__ import annotations

from typing import Any

from orkboard.core.idea_keeper import KeeperError
from orkboard.gui.ideas_args import IdeasError, _str


class PassMixin:
    def pass_take(self, args: dict) -> dict:
        try:
            self.keeper.pass_take(_str(args, "id", 300))
        except KeeperError as e:
            raise IdeasError(str(e)) from None
        self.changed("")
        return {"ok": True}

    def pass_now(self, args: dict) -> dict:
        try:
            self.keeper.pass_now(_str(args, "id", 300))
        except KeeperError as e:
            raise IdeasError(str(e)) from None
        self.changed("")
        return {"ok": True}


def pass_commands(ideas_: Any) -> dict:
    """The commands by name (`gui/ideas.py` adds them to its table: `**pass_commands(self)`)."""
    return {"ideas.pass_take": ideas_.pass_take, "ideas.pass_now": ideas_.pass_now}
