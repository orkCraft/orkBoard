"""The journals' commands (docs/specs/125-the-journals.md §B; decisions §203), as `gui/ideas.py`'s `Ideas` has them: what the project's journal and each leader's journal hold, and the person's
*Not so* on an entry. The store is `realm/journals.py`'s; the entries are written where things happen (`realm/journal_notes.py`).

    ideas.journal {party?}                          # → {entries: [entry], digest: {text, upto, at} | {}}: the party's journal, or the project's with no party; a struck entry is in it, marked `struck: {at, why}`
    ideas.journal_strike {party?, id, why?}         # *Not so*: the entry is struck and never read into a call again → {ok: true, entry}; *No such entry* when the journal has none

An entry is `{id, at, kind, text, idea, on, ref}`. A party is one of the project's (*No such party* for any other). The host returns data, never interface words but a refusal's.
"""
from __future__ import annotations

from typing import Any

from orkboard.gui.ideas_args import IdeasError, _str, _text
from orkboard.realm import ideas, journals


class JournalMixin:
    def _journal_scope(self, args: dict) -> str:
        """The journal a command names: a party's (one of the project's), else the project's."""
        party = _str(args, "party", 100).strip()
        if not party:
            return journals.PROJECT
        if party == ideas.GENERAL or ideas.track_page(self.root(False), party) is None:
            raise IdeasError("No such party")
        return party

    def journal(self, args: dict) -> dict:
        scope = self._journal_scope(args)
        return {"entries": journals.read(self.state_dir, scope, struck=True), "digest": journals.digest(self.state_dir, scope)}

    def views_when_done(self, slug: str) -> int:
        """A goal became done (spec 167 H): one view call is begun for each party of its `route` (its page's, else its party), none when the window or the limit is spent; how many were begun."""
        page = ideas.idea_page(self.root(False), slug)
        if page is None:
            return 0
        parties = [x.strip() for x in page.get("route").split(",") if x.strip()] or [page.get("track")]
        begin = getattr(self.keeper, "journal_view_for", None)
        return begin(parties, "done") if begin is not None else 0

    def journal_strike(self, args: dict) -> dict:
        scope = self._journal_scope(args)
        got = journals.strike(self.state_dir, scope, _text(args, "id", 100), _str(args, "why", 300))
        if got is None:
            raise IdeasError("No such entry")
        return {"ok": True, "entry": got}


def journal_commands(ideas_: Any) -> dict:
    """The journals' commands by name (`gui/ideas.py` adds them to its table: `**journal_commands(self)`)."""
    return {"ideas.journal": ideas_.journal, "ideas.journal_strike": ideas_.journal_strike}
