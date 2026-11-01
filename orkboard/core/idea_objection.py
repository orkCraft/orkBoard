"""The person's answer to a leader's no (docs/specs/108-a-leader-says-no-and-shows-where-it-hurts.md §4.3; decisions §183.3): a round's `no` is held in the Talk's record
(`realm/idea_objections.py`), and the decision waits until each is answered. Since spec 120 §4 the person is shown them as one `hearing` row a goal and answers by a throw. A
mixin of `IdeaKeeper`, as `idea_talk.py` is.

    keeper.objection_answer(slug, party, answer)    # `answer`: drop · smaller · later · go; the leader is the party's (one no a leader)
    keeper.throw(slug, dir="", text="", tree=None)  # a hearing thrown (spec 120 §4.3): to the side at `dir` (right · left · up), or `text`, the person's own words

A throw is each of these answers for the leaders of its side (the others' no is overruled, `go`): `go` (right, *Do it*) goes on to the decision and confirms it as soon as it is worded;
`smaller` words the goal as the side's `instead`, then the same; `later` waits on the goal named; `drop` drops the goal; `text` confirms with the person's words kept as written.
A hearing that is no longer open is refused in plain words (`idea_hearing.DECIDED`). The confirm after the decision's call is the record's `thrown`; `tree` (the Board's tree) is kept in
memory for it, and without it (the host restarted meanwhile) the decision's card waits for the person's own press.

- **drop**: the goal is dropped (`ideas.drop`).
- **smaller** (only when the leader named one, `instead`): the goal's words become `instead` and Talk is not run again; the decision goes on once the other answers are in.
- **later** (only for a no that names a goal in line, `after`): the goal waits on that goal (`collide.add_dependency`) and goes back to the deck, held, its Talk forgotten; the
  person starts it when the goal it waits on is done.
- **go**: the decision goes on; the leader is noted as overruled (`idea_objections.lines`), which the decision says.

When the last objection is answered and Talk has nothing else to ask, the decision is worded (`self._on(slug, "decide")`); with questions still waiting, `talk_answer` goes on
as it did. Each answer is the event `objection_answered`. `self` has the keeper's `busy`, `wiki_root`, `state_dir`, `_on`, `_ev`, `_name`.
"""
from __future__ import annotations

import time

from orkboard.realm import collide, event_log, idea_hearing, idea_objections, idea_questions, ideas

SAID = {"drop": "Drop the goal", "smaller": "Do the smaller one", "later": "Not now", "go": "Go on anyway"}      # what the person pressed, for the talk's record


def _kw():
    from orkboard.core import idea_keeper
    return idea_keeper


class ObjectionMixin:
    # -- a hearing thrown (spec 120 §4.3) ---------------------------------------------------------------------------------------------

    def throw(self, slug: str, dir: str = "", text: str = "", tree=None) -> dict:
        """The person's throw of the goal's Talk hearing: `{kind, dir, outcome, to: [name], moment: "talk"}`; KeeperError in plain words for a hearing that is not open (*This was
        decided already*), a side that is not there, a goal that must wait for this one, or a keeper that is busy with the goal."""
        kw = _kw()
        root = self.wiki_root()
        text = str(text or "").strip()[:6000]
        if ideas.idea_page(root, slug) is None:
            raise kw.KeeperError("That goal is gone")
        with ideas.LOCK:
            rec = idea_questions.record(self.state_dir, slug)
            hearing = idea_objections.open_hearing(root, self.state_dir, slug, rec, self._name) if ideas.state(self.state_dir, slug)["state"] == "talk" else None
            if hearing is None:
                raise kw.KeeperError(idea_hearing.DECIDED)
            side = None if text else next((x for x in hearing["sides"] if x["dir"] == dir), None)
            if not text and side is None:
                raise kw.KeeperError("Throw it to a side, or say it in your own words")
            if self.busy(slug):
                raise kw.KeeperError("The keeper is busy with this goal: a moment")
            kind = "own" if text else side["kind"]
            after = side["after"] if kind == "later" else ""
            if after and slug in collide.chain(root, after):
                raise kw.KeeperError("That goal waits for this one: this one cannot wait for it")
            mine = set(side["leaders"]) if side else set()
            said = {"drop": "drop", "smaller": "smaller", "later": "later"}.get(kind, "go")
            answered = [(o["party"], said if o["party"] in mine else "go") for o in idea_objections.pending(rec)]
            if kind == "smaller":
                idea_objections.reword(root, slug, side["instead"])
            if kind in ("go", "smaller", "own"):
                for o in idea_objections.pending(rec):
                    o["answer"] = said if o["party"] in mine else "go"
                rec["hearing"] = False
                rec["thrown"] = {"kind": kind, "text": text}
                idea_questions.save_record(self.state_dir, slug, rec)
                self.__dict__.setdefault("_throw_trees", {})[slug] = tree
            clear = rec.get("done") is True and not rec.get("waiting")           # Talk has nothing else to wait for
            who = next((x for x in rec.get("stances") or [] if isinstance(x, dict) and side and x.get("party") in mine), None)
        outcome = side["outcome"] if side else "Said in the person's own words"
        for party, answer in answered:
            self._ev(event_log.OBJECTION_ANSWERED, idea=slug, party=party, answer=answer)
        self._ev(event_log.HEARING_THROWN, idea=slug, moment="talk", kind=kind, dir="" if text else dir, leaders=len(mine))
        if kind == "drop":
            ideas.drop(root, slug, self.state_dir)
        elif kind == "later":
            self._left(slug, {"leader": (who or {}).get("leader", ""), "why": side["line"]}, "later", after)
        else:
            ideas.add_turn(self.state_dir, slug, "you", f"Thrown to {', '.join(side['names'])}: {outcome}" if side else outcome, "Talk")
            if clear:
                self._on(slug, "decide")
        return {"kind": kind, "dir": "" if text else dir, "outcome": outcome, "to": list(side["names"]) if side else [], "moment": "talk"}

    def decision_run(self, slug: str, after: list) -> None:
        """The decision's call as `DecideMixin` has it; when the goal came here by a throw, the decision is then confirmed (`thrown_confirm`), for the throw was the person's yes."""
        super().decision_run(slug, after)
        if not after and idea_questions.record(self.state_dir, slug).get("thrown") and ideas.state(self.state_dir, slug)["state"] == "decided":
            after.append("thrown_confirm")

    def thrown_confirm(self, slug: str) -> None:
        """The decision worded after a throw is confirmed as the person would (the person's own words, if they threw those) and the sections follow. Without the Board's tree kept
        at the throw the decision's card waits for the person."""
        with ideas.LOCK:
            rec = idea_questions.record(self.state_dir, slug)
            thrown = rec.pop("thrown", None)
            if not thrown:
                return
            idea_questions.save_record(self.state_dir, slug, rec)
        trees = self.__dict__.setdefault("_throw_trees", {})
        if slug not in trees:
            return
        began = time.monotonic()
        got = self.confirm(slug, str(thrown.get("text") or ""), trees.pop(slug))
        if got.get("commit"):
            self._ev(event_log.BOARD_COMMITTED, commit=got["commit"], pages=got.get("pages") or 0, what="decision", seconds=round(time.monotonic() - began, 2))
        if got.get("held"):
            self._ev(event_log.BOARD_HELD, why=got["held"])
        self.publish(slug)

    # -- a leader's no, answered ----------------------------------------------------------------------------------------------------

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
            rows = idea_objections.objection_rows(root, self.state_dir, slug, rec)
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
