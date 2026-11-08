"""The journals' commands (docs/specs/125-the-journals.md §B; decisions §203), as `gui/ideas.py`'s `Ideas` has them: what the project's journal and each leader's journal hold, and the person's
*Not so* on an entry. The store is `realm/journals.py`'s; the entries are written where things happen (`realm/journal_notes.py`).

    ideas.journal {party?}                          # → {entries: [entry], digest: {text, upto, at} | {}}: the party's journal, or the project's with no party; a struck entry is in it, marked `struck: {at, why}`
    ideas.journal_strike {party?, id, why?}         # *Not so*: the entry is struck and never read into a call again → {ok: true, entry}; *No such entry* when the journal has none

    ideas.view {party}                              # → {view: {text, at, read} | {}, leader, looking}: a leader's view (its journal's digest, spec 167 I); logs `view_opened` (party, at), never the words
    ideas.view_look {party}                         # → {ok, asked, why?}: one view call is begun ("ask"); a refusal or a view already being made begins none, its plain words in `why`

An entry is `{id, at, kind, text, idea, on, ref}`. A party is one of the project's (*No such party* for any other). The host returns data, never interface words but a refusal's.
"""
from __future__ import annotations

from typing import Any

from orkboard.gui.ideas_args import IdeasError, _str, _text
from orkboard.realm import event_log, goal_team, ideas, journals


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

    def _view_party(self, args: dict) -> str:
        party = _str(args, "party", 100).strip()
        if not party or party == ideas.GENERAL or ideas.track_page(self.root(False), party) is None:
            raise IdeasError("No such party")
        return party

    def view(self, args: dict) -> dict:
        """A leader's view as the face reads it; the opening is logged with the view's date, never its words (H6's signal)."""
        party = self._view_party(args)
        got = journals.digest(self.state_dir, party)
        view = {"text": got["text"], "at": got["at"], "read": got["read"]} if got else {}
        self._ev(event_log.VIEW_OPENED, args, party=party, at=view.get("at", ""))
        return {"view": view, "leader": goal_team.leader_of(self.root(False), party), "looking": bool(self.keeper.busy_goal(party))}

    def view_look(self, args: dict) -> dict:
        """*Look now*: one view call is begun; a second ask while one runs begins none."""
        party = self._view_party(args)
        if self.keeper.busy_goal(party):
            return {"ok": True, "asked": False, "why": "The leader is looking already"}
        if self.keeper.journal_view(party, "ask"):
            return {"ok": True, "asked": True}
        why = self.keeper._may_run()
        if not why:
            try:
                self.keeper.refuse_spent()
            except Exception as e:                             # a spent limit or window says so in its own words
                why = str(e)
        return {"ok": True, "asked": False, "why": why or "The leader cannot look now"}

    def journal_strike(self, args: dict) -> dict:
        scope = self._journal_scope(args)
        got = journals.strike(self.state_dir, scope, _text(args, "id", 100), _str(args, "why", 300))
        if got is None:
            raise IdeasError("No such entry")
        return {"ok": True, "entry": got}


def journal_commands(ideas_: Any) -> dict:
    """The journals' commands by name (`gui/ideas.py` adds them to its table: `**journal_commands(self)`)."""
    return {"ideas.journal": ideas_.journal, "ideas.journal_strike": ideas_.journal_strike,
            "ideas.view": ideas_.view, "ideas.view_look": ideas_.view_look}
