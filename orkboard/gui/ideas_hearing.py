"""The hearing's commands (docs/specs/120-a-goal-heard-and-thrown-to-a-side.md §4.3–§4.5; decisions §198.6), as `gui/ideas.py`'s `Ideas` has them: the goal's card in the middle and the
sides its leaders argue (`realm/idea_hearing.py`), thrown to the one the person takes.

    ideas.hearing {idea}                          # the goal's open hearing, Talk's first, else its first open fork: {idea, moment, id?, title, sides, left_out, own}; null with none
    ideas.throw {idea, moment, dir | text}        # `moment`: "talk" or "fork"; `dir`: right · left · up, the side's place; `text`: the person's own words (they win over `dir`)
    ideas.ripe_hold {idea}                        # *Hold* on a goal waiting to start by itself (the part that runs the wait: `keeper.ripe_hold` or `realm/idea_ripe.hold`)

`ideas.throw` of a Talk's hearing is `keeper.throw` (core/idea_objection.py): `go` confirms the decision once it is worded and the sections follow, `smaller` words the goal as the side's
`instead` and does the same, `later` waits on the goal named, `drop` drops the goal, `text` confirms with the person's words as written. A fork's throw is `fork_answer(side=)` or
`fork_answer(text=)`. A throw of a hearing no longer open is refused in plain words: *This was decided already*. Each answers `{ok: true, moment, kind, dir, outcome, to: [name]}`.

**The seam of the wait** (spec 120 §3.5, part C): `ideas.ripe_hold` calls the keeper's `ripe_hold(slug)` when it has one, else `idea_ripe.hold(state_dir, slug)` of `realm/idea_ripe.py` when
that module has one; with neither the goal is told nothing waits to start by itself.
"""
from __future__ import annotations

import importlib
from typing import Any

from orkboard.gui.ideas_args import IdeasError, _text
from orkboard.realm import event_log, idea_hearing, idea_objections, idea_questions, ideas, spec_sections

TEXT_CHARS = 6000
MOMENTS = ("talk", "fork")
NOTHING_WAITS = "Nothing waits to start by itself here"


class Hearing:
    """The commands of the hearing, over the Board's `Ideas` (its keeper, root, state and `changed`)."""

    def __init__(self, ideas_: Any) -> None:
        self.i = ideas_

    def _goal(self, args: dict) -> str:
        slug = _text(args, "idea", 100)
        if ideas.idea_page(self.i.root(), slug) is None:
            raise IdeasError("That goal is gone")
        return slug

    def _fork(self, slug: str) -> dict | None:
        """The first fork open of the goal's sections, as a hearing has it."""
        if ideas.state(self.i.state_dir, slug)["state"] != "sections":
            return None
        f = next((f for f in spec_sections.record(self.i.state_dir, slug).get("forks") or [] if isinstance(f, dict) and f.get("status") == "open"), None)
        return idea_hearing.of_fork(f, self.i.keeper._name) if f else None

    def _talk(self, slug: str) -> dict | None:
        if ideas.state(self.i.state_dir, slug)["state"] != "talk":
            return None
        return idea_objections.open_hearing(self.i.root(), self.i.state_dir, slug, idea_questions.record(self.i.state_dir, slug), self.i.keeper._name)

    def hearing(self, args: dict) -> dict | None:
        slug = self._goal(args)
        got = self._talk(slug) or self._fork(slug)
        return {"idea": slug, **got} if got else None

    def throw(self, args: dict) -> dict:
        slug = self._goal(args)
        moment, dir_, text = args.get("moment"), args.get("dir", ""), args.get("text", "")
        if moment not in MOMENTS:
            raise IdeasError("moment is talk or fork")
        if not isinstance(dir_, str) or not isinstance(text, str):
            raise IdeasError("dir and text are text")
        if dir_ and dir_ not in idea_hearing.DIRS:
            raise IdeasError("dir is right, left or up")
        text = text.strip()[:TEXT_CHARS]
        if not text and not dir_:
            raise IdeasError("Throw it to a side, or say it in your own words")
        got = self._talk(slug) if moment == "talk" else self._fork(slug)
        if got is None:                                         # a late throw, a hearing another face answered
            raise IdeasError(idea_hearing.DECIDED)
        if moment == "talk":
            done = self.i.keeper.throw(slug, dir_, text, self.i._decision_tree())       # a KeeperError is told in plain words by the table's guard
        else:
            side = None if text else next((s for s in got["sides"] if s["dir"] == dir_), None)
            if not text and side is None:
                raise IdeasError("That side is not on this hearing")
            self.i.fork_answer({"idea": slug, "text": text} if text else {"idea": slug, "side": side["party"]})
            self.i._ev(event_log.HEARING_THROWN, args, idea=slug, moment="fork", kind="own" if text else "side", dir="" if text else dir_, leaders=0 if text else 1)
            done = {"kind": "own" if text else "side", "dir": "" if text else dir_, "outcome": text or side["outcome"], "to": [] if text else side["names"], "moment": "fork"}
        self.i._what[slug] = "answered"
        self.i.changed(slug)
        return {"ok": True, **done}

    def ripe_hold(self, args: dict) -> dict:
        slug = self._goal(args)
        keeper_hold = getattr(self.i.keeper, "ripe_hold", None)
        if callable(keeper_hold):
            keeper_hold(slug)
        else:
            try:
                module_hold = getattr(importlib.import_module("orkboard.realm.idea_ripe"), "hold", None)
            except ImportError:
                module_hold = None
            if not callable(module_hold):
                raise IdeasError(NOTHING_WAITS)
            module_hold(self.i.state_dir, slug)
        self.i.changed(slug)
        return {"ok": True}


def hearing_commands(ideas_: Any) -> dict:
    """The hearing's commands by name (`gui/ideas.py` adds them to its table)."""
    h = Hearing(ideas_)
    return {"ideas.hearing": h.hearing, "ideas.throw": h.throw, "ideas.ripe_hold": h.ripe_hold}
