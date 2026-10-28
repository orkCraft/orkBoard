"""Game design's loop (docs/specs/102-the-other-maps-and-picking-on-them.md §2), as `gui/ideas.py`'s `Ideas` has them: the commands its cards are read, kept and proposed by.

    ideas.loop {}                  # → {cards: [{id, name, line, rests_on, by, at}], proposing: bool, status: "" | "asking" | "done" | "failed", error?, party}
    ideas.loop_set {cards}         # the person's cards (4 to 6, each {id?, name, line, rests_on}), kept `by: "person"` → {ok, cards, dropped: [{name, path}]}
    ideas.loop_propose {}          # the first proposal (core/idea_loop.py) → {ok, asked: bool, why?}

`loop` is data only: `party` is Game design's party (or ""), `status` the first proposal's, `proposing` true while its call runs. `loop_set` refuses in plain words a count outside four to
six, a card with no name or line, two of one name; a `rests_on` path that is not a file or folder of dev's tree is dropped and said (`dropped`). `loop_propose` is never a refusal: a call that
cannot be made (no Game design party, no model, a spent limit) is `asked: false` with why. The host returns keys and data, never interface words.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from orkboard.core.idea_keeper import KeeperError
from orkboard.gui.ideas_args import IdeasError
from orkboard.realm import loop


class LoopMixin:
    def loop(self, args: dict) -> dict:
        party = self.keeper.loop_party() if hasattr(self.keeper, "loop_party") else ""
        prop = loop.proposal(self.state_dir)
        asking = prop["status"] == "asking" and bool(party) and bool(self.keeper.busy_goal(party))      # a call lost with the process is no longer asked: the next press asks again
        status = prop["status"] if prop["status"] != "asking" or asking else ""
        out = {"cards": loop.read(self.state_dir), "proposing": asking, "status": status, "party": party}
        return {**out, "error": prop["error"]} if prop["status"] == "failed" else out

    def loop_set(self, args: dict) -> dict:
        try:
            kept, dropped = loop.keep(self.state_dir, Path(self.host.repo_root), args.get("cards"), "person")
        except ValueError as e:
            raise IdeasError(str(e)) from None
        self.changed("")
        return {"ok": True, "cards": kept, "dropped": dropped}

    def loop_propose(self, args: dict) -> dict:
        ask = getattr(self.keeper, "loop_propose", None)
        if ask is None:
            return {"ok": True, "asked": False}
        try:
            asked = ask()
        except KeeperError as e:                                  # the keeper's refusals are plain words; none fails the caller
            return {"ok": True, "asked": False, "why": str(e)}
        self.changed("")
        return {"ok": True, "asked": asked}


def loop_commands(ideas_: Any) -> dict:
    """Game design's loop's commands by name (`gui/ideas.py` adds them to its table: `**loop_commands(self)`)."""
    return {"ideas.loop": ideas_.loop, "ideas.loop_set": ideas_.loop_set, "ideas.loop_propose": ideas_.loop_propose}
