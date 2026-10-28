"""The project's questions (docs/specs/99-a-goals-way.md §8), as `gui/ideas.py`'s `Ideas` has them: the commands the row `project_q` (realm/board_rows.py) is asked and answered by.

    ideas.project_ask {}                                         # begins the first start's questions (core/idea_project_q.py); `ideas.party_save` with `first: true` does the same
    ideas.project_answer {answers: [{id, pick?|text?}], decide?: bool}   # the cards of the `project_q` row, together; `decide` (*Let … decide*) answers the rest with the leader's picks

`project_ask` answers `{"ok": true, "asked": bool, "why"?}`: a call that cannot be made (no model, a spent limit) is `asked: false` with why in plain words, never a refusal, so a
party made at the first start is never refused for it. `project_answer` answers `{"ok": true, "kept": [{key, by}]}`: each answer is kept as the project's (`project_facts.keep`, `by` "person"; a
pick kept by *Let … decide* `by` "read"), read into every leader's calls from then on (`project_facts.for_call`) and never asked again. Product's *whom* and *hurts* are also kept as a
segment and its pain (`idea_lens.keep_segment`) for Product's map. Answered or let go, the stack leaves the hand. The host returns keys and data, never interface words.
"""
from __future__ import annotations

from typing import Any

from orkboard.core.idea_keeper import KeeperError
from orkboard.gui.ideas_args import IdeasError
from orkboard.realm import goal_team, idea_lens, project_facts, project_questions

SEGMENT_CHARS, PAIN_CHARS = 120, 300                 # `idea_lens`: a segment's name, a pain


class ProjectQMixin:
    def project_start(self) -> dict:
        """Begin the first start's questions, quietly: `{asked, why?}`. A keeper without them (or a call that cannot be made) asks nothing and refuses nothing."""
        ask = getattr(self.keeper, "project_ask", None)
        if ask is None:
            return {"asked": False}
        try:
            asked = ask()
        except KeeperError as e:                                 # the keeper's refusals (a spent limit, no model, busy) are plain words; none may fail the caller
            return {"asked": False, "why": str(e)}
        self.changed("")
        return {"asked": asked}

    def project_ask(self, args: dict) -> dict:
        return {"ok": True, **self.project_start()}

    def project_answer(self, args: dict) -> dict:
        rec = project_questions.record(self.state_dir)
        answers = args.get("answers", [])
        if not isinstance(answers, list) or not all(isinstance(a, dict) and isinstance(a.get("id"), str) for a in answers):
            raise IdeasError("answers are a list of {id, pick or text}")
        if rec.get("status") != "waiting" or not rec.get("questions"):
            raise IdeasError("The project asks nothing now")
        try:
            taken = project_questions.take(rec, answers, args.get("decide") is True)
        except ValueError as e:
            raise IdeasError(str(e)) from None
        party = str(rec.get("party") or "") or project_questions.ORKMASTER_FACT
        for a in taken:
            project_facts.keep(self.state_dir, party, a["key"], a["answer"], a["by"])
        self._segment(party, {a["key"] for a in taken})
        project_questions.save_record(self.state_dir, {**rec, "status": "done", "questions": [], "answered": [{k: a[k] for k in ("key", "by")} for a in taken]})
        self.changed("")
        return {"ok": True, "kept": [{"key": a["key"], "by": a["by"]} for a in taken]}

    def _segment(self, party: str, keys: set[str]) -> None:
        """Product's *whom* and *hurts* also kept as a segment and its pain for Product's map (spec 99 §8.3), when one of them was answered now."""
        if not keys & {"for_whom", "hurts"} or goal_team.craft_of(self.root(False), party) != "product":
            return
        said = {f["key"]: f["text"] for f in project_facts.of(self.state_dir, party)}
        if said.get("for_whom"):
            idea_lens.keep_segment(self.state_dir, said["for_whom"][:SEGMENT_CHARS], (said.get("hurts") or "")[:PAIN_CHARS])


def project_q_commands(ideas_: Any) -> dict:
    """The project's questions' commands by name (`gui/ideas.py` adds them to its table: `**project_q_commands(self)`)."""
    return {"ideas.project_ask": ideas_.project_ask, "ideas.project_answer": ideas_.project_answer}
