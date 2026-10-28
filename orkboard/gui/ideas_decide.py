"""The decision and the forks (docs/specs/99-a-goals-way.md §6, §7), as `gui/ideas.py`'s `Ideas` has them: the commands the rows `decision` and `fork` are answered by.

    ideas.confirm {idea, text?}            # *Confirm and start* (the row `decision`): `text` the person's correction, kept as written; the entry is appended to the project's decisions
                                           #   file and committed to dev with the Board's pages, then the sections are written at once. Answers {ok, number, title, commit, held, path}
    ideas.fork_answer {idea, side?|text?}  # the row `fork`: a side's party, or the person's own words; the sections the answer changes are written again (core/idea_sections.py)

Both refuse in plain words (`IdeasError`) what the keeper cannot do now. A goal that had a fork is never started by itself: its plan waits for the person's *Start* (`autostart`).
"""
from __future__ import annotations

import time
from typing import Any

from orkboard.gui.ideas_args import IdeasError, _text
from orkboard.realm import event_log, ideas, spec_sections

TEXT_CHARS = 6000


class DecideMixin:
    def _decision_tree(self):
        """The Board's tree where it stands (made when missing); None where the Board keeps its pages in the Wiki (the demo, a folder with no history)."""
        self.root()
        tree = getattr(self, "_board_tree", None)
        return tree if tree is not None and tree.exists() else None

    def confirm(self, args: dict) -> dict:
        slug = _text(args, "idea", 100)
        text = args.get("text", "")
        if not isinstance(text, str):
            raise IdeasError("text is not text")
        began = time.monotonic()
        got = self.keeper.confirm(slug, text[:TEXT_CHARS], self._decision_tree())
        if got.get("commit"):
            self._ev(event_log.BOARD_COMMITTED, commit=got["commit"], pages=got.get("pages") or 0, what="decision", seconds=round(time.monotonic() - began, 2))
        if got.get("held"):
            self._ev(event_log.BOARD_HELD, why=got["held"])
        self._what[slug] = "decided"
        self.changed(slug)
        return {"ok": True, **got}

    def fork_answer(self, args: dict) -> dict:
        slug = _text(args, "idea", 100)
        side, text = args.get("side", ""), args.get("text", "")
        if not isinstance(side, str) or not isinstance(text, str):
            raise IdeasError("side and text are text")
        self.keeper.fork_answer(slug, side, text)
        self._what[slug] = "answered"
        self.changed(slug)
        return {"ok": True}

    def autostart(self, slug: str) -> str:
        """BoardMixin's, except for a goal that had a fork: after the forks, *Start* is the person's."""
        if ideas.idea_page(self.root(), slug) is not None and spec_sections.record(self.state_dir, slug).get("wait"):
            return "wait"
        return super().autostart(slug)


def decide_commands(ideas_: Any) -> dict:
    """The decision's commands by name (`gui/ideas.py` adds them to its table)."""
    return {"ideas.confirm": ideas_.confirm, "ideas.fork_answer": ideas_.fork_answer}
