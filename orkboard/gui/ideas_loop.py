"""Game design's loops (docs/specs/107-what-the-owners-day-said.md §14; docs/specs/102-the-other-maps-and-picking-on-them.md §2), as `gui/ideas.py`'s `Ideas` has them: the commands the loops are read, kept and proposed by.

    ideas.loop {}                  # → {version: 2, loops: [{id, span, name, line, feeds, steps: [{id, name, line, feel, intensity, gives, takes, rests_on, by, at}]}], currencies: [{id, name, kind, line}],
                                   #    hooks: [{when, line}], by, at, was?, findings: [str], proposing: bool, status: "" | "asking" | "done" | "failed", error?, party}
    ideas.loop_set {loops, currencies, hooks}   # the person's loops (limits in realm/loop.py; a version 1 {cards} is one core loop), kept `by: "person"` → {ok, loops, currencies, hooks, by, at, was?, findings, dropped: [{name, path}]}
    ideas.loop_propose {again?}    # the proposal (core/idea_loop.py); with `again` over what is kept, the person's version put aside in `was` → {ok, asked: bool, why?}

`loop` is data only: `party` is Game design's party (or ""), `status` the proposal's, `proposing` true while its call runs, `findings` what the loop says (`loop.findings`, by code, in the words of
the spec). `loop_set` refuses in plain words a count outside the limits, a step with no name or line, two of one name; a `rests_on` path that is not a file or folder of dev's tree is dropped and said
(`dropped`). `loop_propose` is never a refusal: a call that cannot be made (no Game design party, no model, a spent limit) is `asked: false` with why. The host returns keys and data, never interface words.
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
        data = loop.read(self.state_dir)
        out = {**data, "findings": loop.findings(data), "proposing": asking, "status": status, "party": party}
        return {**out, "error": prop["error"]} if prop["status"] == "failed" else out

    def loop_set(self, args: dict) -> dict:
        data = {k: args[k] for k in ("loops", "currencies", "hooks", "cards") if k in args}
        try:
            kept, dropped = loop.keep(self.state_dir, Path(self.host.repo_root), data, "person")
        except ValueError as e:
            raise IdeasError(str(e)) from None
        self.changed("")
        return {"ok": True, **kept, "findings": loop.findings(kept), "dropped": dropped}

    def loop_propose(self, args: dict) -> dict:
        ask = getattr(self.keeper, "loop_propose", None)
        if ask is None:
            return {"ok": True, "asked": False}
        try:
            asked = ask(again=True) if args.get("again") else ask()
        except KeeperError as e:                                  # the keeper's refusals are plain words; none fails the caller
            return {"ok": True, "asked": False, "why": str(e)}
        self.changed("")
        return {"ok": True, "asked": asked}


def loop_commands(ideas_: Any) -> dict:
    """Game design's loop's commands by name (`gui/ideas.py` adds them to its table: `**loop_commands(self)`)."""
    return {"ideas.loop": ideas_.loop, "ideas.loop_set": ideas_.loop_set, "ideas.loop_propose": ideas_.loop_propose}
