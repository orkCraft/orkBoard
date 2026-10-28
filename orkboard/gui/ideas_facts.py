"""The host's few for the parties form and Talk (docs/specs/100-a-goals-way-as-cards.md §5b), as `gui/ideas.py`'s `Ideas` has them: what the project's facts and kind and a goal's Talk
are read and changed by. The host returns keys and data, never interface words but a refusal's.

    ideas.project_facts {party}                       # the facts kept for that party's calls (`project_facts.for_call`'s source)
    ideas.project_fact_set {party, key, text}         # *From the next goal*: a fact kept as the person's; an empty text drops it
    ideas.project_kind_set {kind}                     # the person's correction of what the project is, read before its files from then on
    ideas.talk_read {idea}                            # a goal's Talk as kept: each leader's stance, for, against, its questions (for the stances' *More*)

`project_facts` answers `{"facts": [{key, text, by}]}`, `by` "person" or "read", in the order they were first kept. `project_fact_set` answers `{"ok": true, "facts": [...]}`, the
party's facts as they are now (`dropped: true` when an empty text took one away; an empty text for a fact that is none is not a refusal). A party is one of the project's, or the Orkmaster's
(the card at the first start is kept under it); a key is `a-z`, `0-9` and `_`, up to 40; a text is kept to 300 characters, whitespace squeezed. `project_kind_set` answers
`{"ok": true, "kind": {"id", "words", "signs", "kept": true}}`, as `ideas.proposals`' `kind` has it (the signs gone: the person said so); a kind that is none is refused, in plain words,
with the list of those that are. `talk_read` answers `{"idea", "mode", "round", "done", "stances": [{party, leader, stance, for, against, questions: [{id, q, choices, pick, why,
project, state, answer?, how?, round?}]}], "cause"}` (realm/idea_questions.py `talk_of`); `state` is "waiting", "answered" or "closed" (left to the leader's pick).
"""
from __future__ import annotations

from typing import Any

from orkboard.gui.ideas_args import IdeasError, _str, _text
from orkboard.realm import ideas, project_facts, project_kind, project_questions
from orkboard.realm.idea_questions import talk_of


class FactsMixin:
    def _fact_party(self, args: dict) -> str:
        """The party a command names: one of the project's (or the Orkmaster's); *No such party* for any other."""
        party = _text(args, "party", 100)
        if party != project_questions.ORKMASTER_FACT and ideas.track_page(self.root(False), party) is None:
            raise IdeasError("No such party")
        return party

    @staticmethod
    def _facts_of(rows: list[dict]) -> list[dict]:
        return [{"key": r["key"], "text": r["text"], "by": r["by"]} for r in rows]

    def project_facts(self, args: dict) -> dict:
        party = self._fact_party(args)
        return {"facts": self._facts_of(project_facts.of(self.state_dir, party))}

    def project_fact_set(self, args: dict) -> dict:
        party, key, text = self._fact_party(args), _text(args, "key", 100), _str(args, "text", 4000)
        dropped = False
        try:
            if text.strip():
                project_facts.keep(self.state_dir, party, key, text, "person")
            else:
                dropped = project_facts.drop(self.state_dir, party, key)
        except ValueError as e:
            raise IdeasError(str(e)) from None
        self.changed("")
        return {"ok": True, **({"dropped": True} if dropped else {}), "facts": self._facts_of(project_facts.of(self.state_dir, party))}

    def project_kind_set(self, args: dict) -> dict:
        kind = _text(args, "kind", 100)
        try:
            project_kind.keep(self.state_dir, kind)
        except ValueError as e:
            raise IdeasError(str(e)) from None
        self.changed("")
        got = project_kind.read_full(self.host.repo_root)
        return {"ok": True, "kind": {"id": got["kind"], "words": project_kind.words(got["kind"]), "signs": list(got["signs"]), "kept": True}}

    def talk_read(self, args: dict) -> dict:
        slug = _text(args, "idea", 100)
        if ideas.idea_page(self.root(False), slug) is None:
            raise IdeasError("That goal is gone")
        return {"idea": slug, **talk_of(self.state_dir, slug)}


def facts_commands(ideas_: Any) -> dict:
    """The facts', kind's and Talk's reads by name (`gui/ideas.py` adds them to its table: `**facts_commands(self)`)."""
    return {"ideas.project_facts": ideas_.project_facts, "ideas.project_fact_set": ideas_.project_fact_set, "ideas.project_kind_set": ideas_.project_kind_set,
            "ideas.talk_read": ideas_.talk_read}
