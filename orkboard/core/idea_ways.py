"""A leader's ways of answering, on the keeper (docs/specs/168 H4, decisions §266.5, §283.22, §283.33; the words and the locks are `realm/answer_ways.py`, the lines a leader is told
`realm/seat_talk_rules.py` `way_rule`). A mixin of `IdeaKeeper`, as `idea_pass.py`'s `PassMixin` is; `core/idea_talk.py` calls `way_split` and `way_fork` between a round's cards and the three picked.

    keeper.way_split(root, items, rnd)       # `[(card, blocks, key)]` → `(rest, silent)`: a card of a Silent leader that is no lock and no project question is its leader's decision (`silent`)
    keeper.way_decided(slug, silent, rnd)    # the veto cards of those decisions, as the Talk's record keeps them (`decided`): the card, its answer, why and the goal's phase
    keeper.way_fork(slug, rest)              # a card of a leader whose way is a Fork: one more call at the elder tier, its ways' gains, costs and risks as their lines, its price on the card (`fork`)
    keeper.way_accept(slug, qid)             # *Accepted*: the decision stands, the veto card is gone
    keeper.way_replay(slug, qid)             # *Replay*: the question is back as a card with its ways; only while the goal is still at Talk and the keeper is not at it

- **Pen** and **Choice** change what the leader is told (`way_rule`) and nothing here: a Choice is today's cards, a Pen's cards are answered by the person's words (the face's *Other…*, first).
- **Silent**: the leader's pick is its decision; the card goes among the Talk's `defaults` as any card left to its leader's pick does, and the veto card is kept in `decided`. **Never for §266.5's locks**:
  a question `answer_ways.lock_of` finds a lock is asked as a Choice, whatever the way, and says why (`lock`).
- **Fork**: one call a question, no tools, on the elder tier (`idea_target.MATRIX["fork"]`); its answer is `{"ways": [{"gain", "cost", "risk"}]}`, one a way. A call that fails or says nothing usable leaves the
  card as the leader made it: a Fork never fails a Talk. What the call may cost is on the card (`fork`: `{low, high}` USD, `answer_ways.fork_price`).
- `self` has the keeper's `ask`, `busy`, `publish`, `_tls`, `state_dir`, `wiki_root`, `target`, `_ev`, `_go_on`.
"""
from __future__ import annotations

import re

from orkboard.realm import answer_ways, goal_phase, goal_team, idea_questions, ideas
from orkboard.realm.seat_question_rules import LINE_CHARS

SIDE = 24                    # a gain, a cost or a risk, at most this many characters of its own: three of them are one way's line


def _kw():
    from orkboard.core import idea_keeper
    return idea_keeper


def _line(text: object) -> str:
    return " ".join(str(text or "").split())


class WaysMixin:
    # -- Silent -------------------------------------------------------------------------------------------------------------------------

    def way_split(self, root, items: list[tuple[dict, bool, str]], rnd: int) -> tuple[list[tuple[dict, bool, str]], list[tuple[dict, bool, str]]]:
        """`(rest, silent)`: the cards of a Silent leader's that it may decide (no project question, no lock) are `silent`, the others `rest`; a card a lock keeps says why (`lock`)."""
        rest: list[tuple[dict, bool, str]] = []
        silent: list[tuple[dict, bool, str]] = []
        for c, blocks, key in items:
            lock = answer_ways.lock_of(c)
            if lock:
                c = {**c, "lock": lock}
            if answer_ways.way_of(goal_team.answers_of(root, c["by"])) == "silent" and not c.get("project") and not lock:
                silent.append((c, blocks, key))
            else:
                rest.append((c, blocks, key))
        return rest, silent

    def way_decided(self, slug: str, silent: list[tuple[dict, bool, str]], rnd: int) -> list[dict]:
        """The veto cards of what Silent leaders decided in this round, as the Talk's record keeps them (`answer_ways.carries`), in the phase the goal is in now."""
        phase = goal_phase.of(ideas.state(self.state_dir, slug))
        return [answer_ways.carries(c, c["by"], rnd, phase) for c, _b, _k in silent]

    # -- Fork ---------------------------------------------------------------------------------------------------------------------------

    def fork_prompt(self, slug: str, card: dict) -> str:
        goal = (ideas.idea_page(self.wiki_root(), slug) or ideas.Page()).section("Gist")
        ways = "\n".join(f"{n + 1}. {w}" for n, w in enumerate(card["choices"]))
        return (f"Lay out the ways of one question, so the person can see what each leads to. Read no file; answer from what is here.\n\nThe goal, in the person's words:\n{goal}\n\n"
                f"The question: {card['q']}\nThe ways:\n{ways}\n\nFor each way, in the ways' order, say in a few words what the person gains, what it costs and what it risks "
                f"({SIDE} characters at most each). Answer only this JSON: {{\"ways\": [{{\"gain\": \"…\", \"cost\": \"…\", \"risk\": \"…\"}}]}}")

    @staticmethod
    def fork_lines(card: dict, answer: object) -> list[str] | None:
        """One line a way from the Fork's answer: *Gain …; cost …; risk …*; None when the answer is not one usable line for each way."""
        got = answer.get("ways") if isinstance(answer, dict) else None
        if not isinstance(got, list) or len(got) != len(card["choices"]):
            return None
        out = []
        for w in got:
            if not isinstance(w, dict):
                return None
            parts = [(k, _line(w.get(k))[:SIDE]) for k in ("gain", "cost", "risk")]
            if not all(v for _k, v in parts):
                return None
            out.append(re.sub(r"\s+", " ", "; ".join(f"{k} {v}" for k, v in parts)).capitalize()[:LINE_CHARS])
        return out

    def way_fork(self, slug: str, rest: list[tuple[dict, bool, str]]) -> list[tuple[dict, bool, str]]:
        """The cards of a leader whose way is a Fork laid out: one more call each, at the elder tier; the card keeps what the leader made where the call fails. Locked cards are forked too (a Fork is
        a way that asks)."""
        kw = _kw()
        root = self.wiki_root()
        out = []
        for c, blocks, key in rest:
            if answer_ways.way_of(goal_team.answers_of(root, c["by"])) != "fork":
                out.append((c, blocks, key))
                continue
            price = answer_ways.fork_price(self.target())
            lines = None
            self._tls.party = c["by"]
            try:
                lines = self.fork_lines(c, kw.first_json(self.ask("fork", self.fork_prompt(slug, c), tools=False)[0]))
            except InterruptedError:
                raise
            except Exception:                                   # a call that cannot be made leaves the card as it is
                lines = None
            finally:
                self._tls.party = ""
            out.append(({**c, "fork": price, **({"lines": lines} if lines else {})}, blocks, key))
        return out

    # -- the veto card ------------------------------------------------------------------------------------------------------------------

    def way_accept(self, slug: str, qid: str) -> dict:
        """*Accepted*: the decision stands as it is and the veto card is gone. KeeperError when it is not there."""
        kw = _kw()
        with ideas.LOCK:
            rec = idea_questions.record(self.state_dir, slug)
            if not any(d.get("id") == qid for d in rec.get("decided") or []):
                raise kw.KeeperError("That decision is not there now")
            rec["decided"] = [d for d in rec["decided"] if d.get("id") != qid]
            idea_questions.save_record(self.state_dir, slug, rec)
        self.publish(slug)
        return {"ok": True, "idea": slug}

    def way_replay(self, slug: str, qid: str) -> dict:
        """*Replay*: the question comes back as a card with its ways and the leader's decision is undone (its answer leaves `defaults`). Only while the goal is at Talk and the keeper is not at it:
        once the decision is made the goal has gone on (the veto card is gone with the stage). KeeperError in plain words else."""
        kw = _kw()
        with ideas.LOCK:
            rec = idea_questions.record(self.state_dir, slug)
            d = next((x for x in rec.get("decided") or [] if x.get("id") == qid), None)
            if d is None:
                raise kw.KeeperError("That decision is not there now")
            if goal_phase.of(ideas.state(self.state_dir, slug)) != d.get("phase") or rec.get("mode") != "talk":
                raise kw.KeeperError("The goal has gone on: this decision can no longer be replayed")
            if self.busy(slug):
                raise kw.KeeperError("The keeper is busy with this goal: a moment")
            rec.update(decided=[x for x in rec["decided"] if x.get("id") != qid], defaults=[x for x in rec.get("defaults") or [] if x.get("id") != qid],
                       waiting=[*(rec.get("waiting") or []), {**d["card"], "replayed": True}], done=False)
            idea_questions.save_record(self.state_dir, slug, rec)
        self.publish(slug)
        return {"ok": True, "idea": slug}
