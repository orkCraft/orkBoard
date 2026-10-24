"""The project's level (docs/specs/70-orkmaster-and-the-project.md §1.2) and the Orkmaster's keeping of the parties from colliding
(docs/specs/71-orkmaster-keeps-parties-apart.md) as `gui/ideas.py`'s `Ideas` has them. Split from ideas.py to keep it under ~600 lines.

    ideas.party_for {type?}      # the Orkmaster's suggestion of a goal's party: {parties: [{party, name, fits, missing}], suggested: slug}
    ideas.collide_answer {id, answer}   # the person's answer to a collision: `first:<slug>` · `one` · `replan` · `leave` → {ok: true}

`party_for` reads the project's parties and their teams; it writes nothing and asks no model (realm/orkmaster.py). A collision is found by code
(realm/collide.py) when a plan is made (`collide_plan`) or a spec changed after its plan (`collide_changed`, from the bus), judged by one call
of the cheaper tier only when the code found an overlap (core/idea_collide.py), and kept as a stop in the hand until the person answers; the
Orkmaster edits no other party's spec or plan and moves nothing before then. No model, no judge: the plan or the change goes on as it did.
"""
from __future__ import annotations

import logging
import threading

from orkboard.core import idea_collide
from orkboard.core.idea_keeper import KeeperError
from orkboard.gui.ideas_args import IdeasError, _opt, _text
from orkboard.realm import collide, event_log, idea_change, ideas, orkmaster

log = logging.getLogger(__name__)
_BUSY_LOCK = threading.Lock()      # the pairs being judged now: one thread judges a pair (the bus and the hook may both find it)
CHANGE_WORDS = 1_200               # of a changed spec's words, the most a judge reads


class ProjectMixin:
    def party_for(self, args: dict) -> dict:
        """`{type?}`: the project's parties but General, how each fits a goal type (`whole`, `missing`, `none`; without a type "" and Ideation's
        `pitch`), and the one suggested. A type the catalog lacks is refused (*No goal type 'x'*)."""
        try:
            parties = orkmaster.party_for(self.state_dir, self.root(False), _opt(args, "type") or None)
        except ValueError as e:
            raise IdeasError(str(e)) from None
        return {"parties": parties, "suggested": orkmaster.suggested(parties)}

    # -- finding (spec 71 §2, §3): code finds, one cheap call judges, nothing moves ----------------------------------------

    def collide_plan(self, slug: str) -> None:
        """A plan was made (from `_state_event`): the finder and, on an overlap, the judge, in the background."""
        self._collide_spawn(slug, "plan", "")

    def collide_changed(self, slug: str) -> None:
        """From the bus, whenever a goal changed: a plan-making section written since its plan (`changed`) that was not there before is a spec
        changed after the start; the goals of other parties that touch what this one touches are compared (spec 71 §3). The words judged are
        the changed sections' text."""
        seen = self.__dict__.setdefault("_collide_seen", {})
        now = idea_change.changed_of(ideas.state(self.state_dir, slug))
        before = seen.get(slug, ())
        seen[slug] = tuple(now)
        if not now or set(now) <= set(before):
            return
        page = ideas.idea_page(self.root(False), slug)
        words = "\n".join(f"{n}: {page.section(n).strip()}" for n in now if page is not None)[:CHANGE_WORDS]
        self._collide_spawn(slug, "change", words)

    def _collide_spawn(self, slug: str, by: str, words: str) -> None:
        if self.host.demo:
            return
        t = threading.Thread(target=self.collide_run, args=(slug, by, words), daemon=True, name="idea-collide")
        self.__dict__.setdefault("_collide_threads", []).append(t)
        t.start()

    def collide_join(self) -> None:
        """Wait for the finders and judges started (the tests', and Close project's)."""
        for t in list(self.__dict__.get("_collide_threads", [])):
            t.join(10)
        self.__dict__["_collide_threads"] = [t for t in self.__dict__.get("_collide_threads", []) if t.is_alive()]

    def collide_run(self, slug: str, by: str = "plan", words: str = "") -> None:
        """The finder, on this thread, and the judge for each overlap not asked before. `slug` is the goal whose plan was made (`plan`) or
        whose spec changed (`change`). A judge that cannot run (no model, a spent budget or window, an answer that is no JSON) is logged and
        skipped: the plan goes on as it did and the pair is asked again next time."""
        try:
            found = collide.overlaps(self.root(False), self.state_dir, slug, planned=by == "change")
        except Exception:                      # a finder never breaks a plan being made
            log.exception("collide: the finder failed on %s", slug)
            return
        for o in found:
            other = o["other"]
            pair = collide.pair_id(slug, other)
            busy = self.__dict__.setdefault("_collide_busy", set())
            with _BUSY_LOCK:
                if pair in busy or collide.known(self.state_dir, pair, by):
                    continue
                busy.add(pair)
            try:
                self._collide_pair(slug, other, pair, by, words)
            finally:
                busy.discard(pair)

    def _collide_pair(self, slug: str, other: str, pair: str, by: str, words: str) -> None:
        """The judge for one pair the finder found, and what it said kept (a stop, or `no` answered)."""
        asked = collide.later_of(self.state_dir, slug, other) if by == "plan" else other     # a changed spec: the question is on the goal beside it
        beside = slug if asked == other else other
        try:
            if why := self.keeper._may_run():
                raise KeeperError(why)
            self.keeper.refuse_spent()
            got = idea_collide.judge(self.keeper, asked, beside, by, words)
        except Exception as e:
            log.info("collide: %s not judged: %s", pair, e)
            self._ev(event_log.COLLIDE_FOUND, None, pair=pair, by=by, judged=False, collide=False, tokens=None, cost=None)
            return
        self._ev(event_log.COLLIDE_FOUND, None, pair=pair, by=by, judged=True, collide=got["collide"], tokens=got["tokens"], cost=got["cost"])
        if got["collide"]:
            collide.add_open(self.state_dir, pair, by, asked, beside, got["why"], got["first"])
        else:
            collide.add_answered(self.state_dir, pair, by, "no")
        self.changed(asked)

    # -- the person's answer (spec 71 §2.3, §3, §8.2) -------------------------------------------------------------------------

    def collide_answer(self, args: dict) -> dict:
        """`{id, answer}`: one of the stop's `answers`. `first:<slug>` makes the other goal wait for `<slug>`'s flag, `one` joins the later goal
        into the earlier (spec 62's change) and drops it, `replan` has the leader of the goal asked about re-plan what is left (the change told
        to it), `leave` keeps them as they are. Refused: *That is answered already*, *No such question*, *Pick one of its answers*."""
        pair, answer = _text(args, "id", 200), _text(args, "answer", 200)
        if collide.answered(self.state_dir, pair):
            raise IdeasError("That is answered already")
        stop = collide.take_open(self.state_dir, pair)           # claimed: a second press finds none
        if stop is None:
            raise IdeasError("No such question")
        by = stop.get("by") or "plan"
        try:
            if answer not in collide.answers_of(stop):
                raise IdeasError("Pick one of its answers")
            collide.add_answered(self.state_dir, pair, by, answer)      # kept first: a plan made while it applies does not ask the pair again
            note = self._collide_apply(stop, answer)
        except Exception:
            collide.put_back(self.state_dir, stop)               # it did not apply: it waits as it did
            raise
        if note:
            collide.add_answered(self.state_dir, pair, by, answer, note)
        self._ev(event_log.COLLIDE_ANSWERED, args, pair=pair, answer=answer)
        for s in (stop["asked"], stop["other"]):
            self.changed(s)
        return {"ok": True}

    def _collide_apply(self, stop: dict, answer: str) -> str:
        """What an answer does; the note kept with it (*joined into «…»*), else "". Raises IdeasError when it cannot be done."""
        root, asked, other = self.root(), stop["asked"], stop["other"]
        title = {s: (ideas.idea_page(root, s) or ideas.Page()).title or s for s in (asked, other)}
        if answer == "leave":
            return ""
        if answer.startswith("first:"):
            first = answer[6:]
            wait = other if first == asked else asked              # the other goal waits for the one that goes first
            if wait in collide.chain(root, first):
                raise IdeasError(f"«{title[first]}» waits for «{title[wait]}» already")
            collide.add_dependency(root, wait, first, title[first])
            self.autostart(wait)                                   # (a flag raised already frees it at once)
            return ""
        if answer == "one":
            return self._collide_join(stop, title)
        return self._collide_replan(stop, title)

    def _collide_join(self, stop: dict, title: dict[str, str]) -> str:
        """*One goal*: the later goal's text joins the earlier's as a change (spec 62: `changed` is kept, the leader re-plans when asked), and
        the later is dropped."""
        root, later, earlier = self.root(), stop["asked"], stop["other"]
        if self.keeper.busy(later) or self.keeper.busy(earlier):
            raise IdeasError("The keeper is busy with this goal: a moment")
        plan = ideas.plan(self.state_dir, later) or {}
        if any(not idea_change.open_task(t) for t in plan.get("tasks") or [] if isinstance(t, dict)):
            raise IdeasError(f"«{title[later]}» has started: leave it, or let it finish")
        src, dst = ideas.idea_page(root, later), ideas.idea_page(root, earlier)
        if src is None or dst is None:
            raise IdeasError("That goal is gone")
        gist = f"{dst.section('Gist').strip()}\n\nJoined from «{title[later]}»: {src.section('Gist').strip()}".strip()
        have = dst.section("Done when").strip()
        extra = [ln for ln in src.section("Done when").splitlines() if ln.strip() and ln.strip() not in have]
        sections = {"Gist": gist, **({"Done when": f"{have}\n" + "\n".join(extra)} if extra else {})}
        idea_change.update(root, self.state_dir, earlier, sections, [f"Joined «{title[later]}» of another party into this goal"])
        self.drop({"slug": later})
        return f"joined into «{title[earlier]}»"

    def _collide_replan(self, stop: dict, title: dict[str, str]) -> str:
        """*Re-plan it*: the leader of the goal asked about re-plans what is left (spec 62's way: a plan not passed is planned again), and
        is told which goal changed and why."""
        asked, other = stop["asked"], stop["other"]
        plan = ideas.plan(self.state_dir, asked)
        if plan is None:
            raise IdeasError("This goal has no plan yet")
        collide.set_told(self.state_dir, asked, f"«{title[other]}», a goal of another party, changed its spec; this goal rests on what it was. {stop.get('why') or ''}")
        try:
            (self.keeper.revise if plan.get("passed_at") else self.keeper.plan)(asked)
        except Exception:
            collide.clear_told(self.state_dir, asked)
            raise
        return ""

    def collide_released(self, slug: str) -> None:
        """A goal's flag was raised: the goals of other parties that waited for it are decided again (autostart), once their other waits
        are over (spec 71 §4)."""
        for w in collide.waiters(self.root(False), slug):
            try:
                self.autostart(w)
            except Exception:                  # a start that cannot be made waits for the person
                log.info("collide: %s not started after the flag of %s", w, slug, exc_info=True)
