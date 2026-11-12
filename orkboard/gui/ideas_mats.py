"""The cards' commands, over the Board's `Ideas` (docs/specs/171; decisions §301): what the table of cards asks of the host, read from the Board's own pages.

    ideas.turns {}      # the moves that wait for the person (`realm/board_turns.py`): {turns: [{goal, kind, at, questions?}]}; read only, no model, no write
"""
from __future__ import annotations

from typing import Any

from orkboard.realm import board_turns, ideas


class Mats:
    """The cards' commands, as `gui/ideas_say.py`'s `Say` is the say's."""

    def __init__(self, ideas_: Any) -> None:
        self.i = ideas_

    def turns(self, args: dict) -> dict:
        root = self.i.root(make=False)
        found, pages = ideas.ideas_and_pages(root)
        parties = [{"slug": t["slug"], "title": t["title"]} for t in ideas.tracks(root, make=False)]
        at = {i["slug"]: ideas.touched_at(root, self.i.state_dir, i["slug"]) for i in found}
        return {"turns": board_turns.turns({i["slug"]: pages[i["slug"]] for i in found}, parties, at)}


def mats_commands(ideas_: Any) -> dict:
    """The cards' commands by name (`gui/ideas.py` adds them to its table: `**mats_commands(self)`)."""
    m = Mats(ideas_)
    return {"ideas.turns": m.turns}
