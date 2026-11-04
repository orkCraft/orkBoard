"""A goal refined before Confirm (docs/specs/132-four-levels-the-way-down-and-findings.md §A; decisions §234.5, §237.3), as `gui/ideas.py`'s `Ideas` has it: the commands the
bubble's *Add to the goal* and the decision's one *Change…* are answered by. Host only: the faces call them.

    ideas.add_to_goal {idea, text}                 # words added to a goal in analysis, kept as written (a line `Added: <text>` under the goal's words); a goal whose decision is
                                                   #   worded already has it worded again (`keeper.reword`, one `decide` call, in the background). {ok, idea, reworded, cost?, why?}
    ideas.decision_change {idea, text?, say?}      # the decision's *Change…*: `text` is the entry kept as written (`by: "person"`), `say` is worded again by the Orkmaster (`keeper.reword`);
                                                   #   both: the text first, then the words said on it. {ok, idea, kept, reworded, cost?}

Both refuse in plain words (`IdeasError`): a goal gone, a pitch, a goal agreed already (*This goal is agreed: ask its leader for a change*), the keeper busy with it. `cost` is what the
one call is capped at (`{calls: 1, usd_high}`, `idea_target.budget("decide", …)`): the face says it on the button. The host returns keys and data, never interface words.
"""
from __future__ import annotations

import datetime as dt
from typing import Any

from orkboard.core import idea_decide
from orkboard.core.idea_keeper import KeeperError
from orkboard.gui.ideas_args import IdeasError, _str, _text
from orkboard.realm import event_log, goal_refine, idea_ripe, idea_target, ideas, spec_sections

AGREED = "This goal is agreed: ask its leader for a change"
BUSY = "The keeper is busy with this goal: a moment"
TOO_LONG = "The goal's words are too long: shorten what is added"


class RefineMixin:
    def _refinable(self, slug: str) -> None:
        """The goal can take words in, else IdeasError in plain words."""
        if ideas.idea_page(self.root(), slug) is None:
            raise IdeasError("That goal is gone")
        if self.keeper.is_pitch(slug):
            raise IdeasError("A pitch is judged, not built: send it to a party first")
        if not goal_refine.in_analysis(self.state_dir, slug):
            raise IdeasError(AGREED)
        if self.keeper.busy(slug):
            raise IdeasError(BUSY)

    def _decision_of(self, slug: str) -> dict | None:
        d = spec_sections.record(self.state_dir, slug).get("decision")
        return d if isinstance(d, dict) and ideas.state(self.state_dir, slug)["state"] == "decided" else None

    def _cost_of_word(self, slug: str) -> dict:
        """What one worded-again decision is capped at, as the line says it (the Target of the goal's party)."""
        route = ideas.state(self.state_dir, slug)["route"]
        party = next((r.get("party") for r in route if isinstance(r, dict)), "") if route else ""
        target = idea_target.target_for(self.settings_now(), ideas.track_page(self.root(), party) if party else None)
        return {"calls": 1, "usd_high": idea_target.budget("decide", target)}

    def add_to_goal(self, args: dict) -> dict:
        slug, text = _text(args, "idea", 100), _text(args, "text", ideas.SECTION_CHARS)
        self._refinable(slug)
        with ideas.LOCK:
            page = ideas.idea_page(self.root(), slug)
            gist = page.section("Gist")
            new = f"{gist.rstrip()}\n\n{goal_refine.added(text)}" if gist.strip() else goal_refine.added(text)
            if len(new) > ideas.SECTION_CHARS:
                raise IdeasError(TOO_LONG)
            ideas.update(self.root(), slug, {"Gist": new})
        ideas.add_turn(self.state_dir, slug, "you", text, "Gist")
        out: dict[str, Any] = {"ok": True, "idea": slug, "reworded": False}
        if self._decision_of(slug) is not None:                  # worded already: worded again with the person's words among the goal's
            try:
                self.keeper.reword(slug)
                out.update(reworded=True, cost=self._cost_of_word(slug))
            except KeeperError as e:                             # the words are kept either way; the decision keeps its old wording, said why
                out["why"] = str(e)
        self._ev(event_log.GOAL_ADDED_TO, args, idea=slug, chars=len(text), reworded=out["reworded"])
        self.changed(slug)
        return out

    def decision_change(self, args: dict) -> dict:
        slug = _text(args, "idea", 100)
        text, say = _str(args, "text", idea_decide.BODY_CHARS).strip(), _str(args, "say", ideas.SECTION_CHARS).strip()
        if not text and not say:
            raise IdeasError("Write the decision, or say what to change")
        self._refinable(slug)
        d = self._decision_of(slug)
        if d is None:
            raise IdeasError("This goal has no decision to change now")
        out: dict[str, Any] = {"ok": True, "idea": slug, "kept": False, "reworded": False}
        if text:
            title, body = idea_decide.corrected(text, str(d.get("title") or ""))
            if not body.strip():
                raise IdeasError("A decision needs its words")
            with ideas.LOCK:
                way = spec_sections.record(self.state_dir, slug)
                way["decision"] = {**d, "title": title, "text": body, "by": "person", "at": dt.datetime.now().isoformat(timespec="seconds")}
                spec_sections.save_record(self.state_dir, slug, way)
            idea_ripe.drop(self.state_dir, slug)                  # the person's own words: the leaders' wait is over, the person confirms
            ideas.add_turn(self.state_dir, slug, "you", f"Changed the decision: {title}", "Decided")
            out["kept"] = True
        if say:
            try:
                self.keeper.reword(slug, say)
            except KeeperError as e:
                if not out["kept"]:
                    raise IdeasError(str(e)) from None
                out["why"] = str(e)                              # the text is kept; the words said were not taken in
            else:
                out.update(reworded=True, cost=self._cost_of_word(slug))
        self._ev(event_log.DECISION_CHANGED, args, idea=slug, kept=out["kept"], said=out["reworded"])
        self.changed(slug)
        return out


def refine_commands(ideas_: Any) -> dict:
    """The refining commands by name (`gui/ideas.py` adds them to its table: `**refine_commands(self)`)."""
    return {"ideas.add_to_goal": ideas_.add_to_goal, "ideas.decision_change": ideas_.decision_change}
