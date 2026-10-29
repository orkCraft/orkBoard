"""The person's answer to a leader's no (docs/specs/108-a-leader-says-no-and-shows-where-it-hurts.md §4.3; decisions §183.3): a round's `no` is a Needs you row of kind
`objection` (`realm/idea_objections.py`), and the decision waits until each is answered. A mixin of `IdeaKeeper`, as `idea_talk.py` is.

    keeper.objection_answer(slug, party, answer)    # `answer`: drop · smaller · later · go; the leader is the party's (one no a leader)

- **drop**: the goal is dropped (`ideas.drop`).
- **smaller** (only when the leader named one, `instead`): the goal's words become `instead` and Talk is not run again; the decision goes on once the other answers are in.
- **later** (only for a no that names a goal in line, `after`): the goal waits on that goal (`collide.add_dependency`) and goes back to the deck, held, its Talk forgotten; the
  person starts it when the goal it waits on is done.
- **go**: the decision goes on; the leader is noted as overruled (`idea_objections.lines`), which the decision says.

When the last objection is answered and Talk has nothing else to ask, the decision is worded (`self._on(slug, "decide")`); with questions still waiting, `talk_answer` goes on
as it did. Each answer is the event `objection_answered`. `self` has the keeper's `busy`, `wiki_root`, `state_dir`, `_on`, `_ev`, `_name`.
"""
from __future__ import annotations

from orkboard.realm import collide, event_log, idea_objections, idea_questions, ideas

SAID = {"drop": "Drop the goal", "smaller": "Do the smaller one", "later": "Not now", "go": "Go on anyway"}      # what the person pressed, for the talk's record


def _kw():
    from orkboard.core import idea_keeper
    return idea_keeper


class ObjectionMixin:
    def objection_answer(self, slug: str, party: str, answer: str) -> None:
        """The person's answer to `party`'s leader's no on the goal at Talk; KeeperError in plain words for an answer that does not apply or a leader that said no such thing."""
        kw = _kw()
        root = self.wiki_root()
        if ideas.idea_page(root, slug) is None:
            raise kw.KeeperError("That goal is gone")
        if answer not in idea_objections.ANSWERS:
            raise kw.KeeperError("The answer is drop, smaller, later or go")
        with ideas.LOCK:
            rec = idea_questions.record(self.state_dir, slug)
            o = next((x for x in idea_objections.pending(rec) if x["party"] == party), None)
            if ideas.state(self.state_dir, slug)["state"] != "talk" or rec.get("mode") != "talk" or o is None:
                raise kw.KeeperError("That leader has no objection to answer now")
            if self.busy(slug):
                raise kw.KeeperError("The keeper is busy with this goal: a moment")
            rows = idea_objections.open_rows(root, self.state_dir, slug, rec)
            if answer not in next(r["answers"] for r in rows if r["party"] == party):
                raise kw.KeeperError("That answer does not apply to this leader's no")
            after = next(r["after"] for r in rows if r["party"] == party)
            if answer == "later" and slug in collide.chain(root, after):
                raise kw.KeeperError("That goal waits for this one: this one cannot wait for it")
            o["answer"] = answer
            idea_questions.save_record(self.state_dir, slug, rec)
            if answer == "smaller":
                idea_objections.reword(root, slug, o["instead"])
            clear = rec.get("done") is True and not rec.get("waiting") and not idea_objections.pending(rec)        # Talk has nothing else to wait for
            go_on = answer in ("go", "smaller") and clear
        self._ev(event_log.OBJECTION_ANSWERED, idea=slug, party=party, answer=answer)
        self._left(slug, o, answer, after)
        if answer == "drop":
            ideas.drop(root, slug, self.state_dir)
        elif go_on:
            self._on(slug, "decide")

    def _left(self, slug: str, o: dict, answer: str, after: str) -> None:
        """What an answer leaves besides the record: the talk's line, and for *Not now* the wait and the goal back in the deck, held."""
        root = self.wiki_root()
        if answer == "later":
            collide.add_dependency(root, slug, after, (ideas.idea_page(root, after) or ideas.Page()).title or after)
            ideas.save_state(self.state_dir, slug, state="raw", queue="hold", route=[], route_how={}, held_until="", held_for="", error="")
            idea_questions.save_record(self.state_dir, slug, {})
        if answer != "drop":
            ideas.add_turn(self.state_dir, slug, "you", f"{SAID[answer]}: {self._name(o['leader'])} said no — {o['why']}", "Talk")
