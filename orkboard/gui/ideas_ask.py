"""A quick question (docs/specs/106-a-quick-question.md §2; decisions §181), as `gui/ideas.py`'s `Ideas` has it: the commands the line on the open tab asks and puts its answer away
by. The record itself (`realm/board_ask.py`) is the snapshot's `ask`, read at each snapshot.

    ideas.ask {party: ""|<slug>, q}    # begins the call (core/idea_ask.py); "" is the Orkmaster's tab; a refusal is an IdeasError in the keeper's words
    ideas.ask_clear {}                 # × : the call being answered is stopped and the record removed
    ideas.ask_goal {}                  # *Make it a goal* pressed under an answer: `ask_made_goal` recorded, nothing else (the page opens the new goal's field)

All answer `{"ok": true}`. The snapshot's `ask` is `{status: "asking"|"answered"|"failed", party, q, answer, sources, goal, at, error}`, or None. The host returns keys and data,
never interface words (the keeper's refusals are plain words already).
"""
from __future__ import annotations

from typing import Any

from orkboard.core.idea_keeper import KeeperError
from orkboard.gui.ideas_args import IdeasError, _str
from orkboard.realm import board_ask, event_log


class AskMixin:
    def ask(self, args: dict) -> dict:
        party = args.get("party", "")
        if not isinstance(party, str):
            raise IdeasError("party is not text")
        try:
            self.keeper.board_ask(party.strip(), _str(args, "q", board_ask.Q_CHARS * 2))
        except KeeperError as e:
            raise IdeasError(str(e)) from None
        self.changed("")
        return {"ok": True}

    def ask_clear(self, args: dict) -> dict:
        self.keeper.board_ask_stop()
        board_ask.clear(self.state_dir)
        self.changed("")
        return {"ok": True}

    def ask_goal(self, args: dict) -> dict:
        self._ev(event_log.ASK_MADE_GOAL, args, party=(board_ask.record(self.state_dir) or {}).get("party", ""))
        return {"ok": True}


def ask_commands(ideas_: Any) -> dict:
    """The quick question's commands by name (`gui/ideas.py` adds them to its table: `**ask_commands(self)`)."""
    return {"ideas.ask": ideas_.ask, "ideas.ask_clear": ideas_.ask_clear, "ideas.ask_goal": ideas_.ask_goal}
