"""The answers to Talk (docs/specs/99-a-goals-way.md §5), as `gui/ideas.py`'s `Ideas` has them: the commands the rows `talk` and `cause` are answered by. `ideas.talk`
(the press of **Talk**) is `gui/ideas_route.py`'s; it hands the goal to `keeper.talk(slug)` (core/idea_talk.py).

    ideas.talk_answer {idea, answers: [{id, pick?|text?}], decide?: bool}   # the cards of the `talk` row, together; `decide` (*Let … decide*) answers the rest with the picks
    ideas.cause_answer {idea, yes: bool, text?, answers?: [{id, pick?|text?}]}   # a bug's `cause` row: *Yes*, *No, it's elsewhere* (+ `text`: one more guess, once), *Other…*
                                                                              #   (`yes` with `text`: the person's own words); `answers`: the case cards of the row's `q`

Both answer `{"ok": true}`; what the keeper cannot do it refuses in plain words (`IdeasError`), and the goal goes on in the background.
"""
from __future__ import annotations

from typing import Any

from orkboard.gui.ideas_args import IdeasError, _text
from orkboard.realm import ideas

ANSWER_CHARS = 2000


class TalkMixin:
    def _talked(self, args: dict) -> tuple[str, list]:
        """`{idea, answers}` of a command: the goal (it must exist) and its answers, each `{id, pick?|text?}`."""
        slug = _text(args, "idea", 100)
        if ideas.idea_page(self.root(), slug) is None:
            raise IdeasError("That goal is gone")
        answers = args.get("answers", [])
        if not isinstance(answers, list) or not all(isinstance(a, dict) and isinstance(a.get("id"), str) for a in answers):
            raise IdeasError("answers are a list of {id, pick or text}")
        return slug, answers

    def talk_answer(self, args: dict) -> dict:
        slug, answers = self._talked(args)
        self.keeper.talk_answer(slug, answers, args.get("decide") is True)
        self._what[slug] = "answered"
        self.changed(slug)
        return {"ok": True}

    def cause_answer(self, args: dict) -> dict:
        slug, answers = self._talked(args)
        if not isinstance(args.get("yes"), bool):
            raise IdeasError("yes is true or false")
        text = args.get("text", "")
        if not isinstance(text, str):
            raise IdeasError("text is not text")
        self.keeper.cause_answer(slug, args["yes"], text[:ANSWER_CHARS], answers)
        self._what[slug] = "answered"
        self.changed(slug)
        return {"ok": True}


def talk_commands(ideas_: Any) -> dict:
    """Talk's commands by name (`gui/ideas.py` adds them to its table)."""
    return {"ideas.talk_answer": ideas_.talk_answer, "ideas.cause_answer": ideas_.cause_answer}
