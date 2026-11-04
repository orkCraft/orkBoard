"""A change to a spec asked of the Orkmaster (docs/specs/144-a-specs-wait-and-a-change-through-the-orkmaster.md C; decisions §224.4, §225.2–3), as `gui/ideas.py`'s `Ideas` has it: the commands the
field on the Orkmaster's head of a goal picked and the one card in the hand send. The record (`realm/spec_change.py`) waits in the goal's state folder; its Needs you row is `kind: "spec_change"`
(`realm/board_map.py` reads it), asked by the Orkmaster; the Orkmaster and the leaders make it (`core/idea_spec_change.py`).

    ideas.spec_change_preview {idea, text}   # nothing started: `{ok, id: "", parties: [{party, title}], estimate: {calls, usd_low, usd_high}, via}`, read by code: *It goes to Tech, Art · about 3 calls*
    ideas.spec_change {idea, text}           # the Orkmaster routes the words to the leaders whose sections they touch (in the background); the same answer, with the record's `id`. `@Tech` in the
                                             # words is §224.5's one leader: it goes to `ideas.change` as built (`via: "change"`)
    ideas.spec_change_take {idea, id, via?}  # *Accept*: every party's lines written into its section, each plan change taken, the person's words written into the goal's Decisions once; then the wait
                                             # begins again from now (`look_until` anew), and when the limits run low not before their reset. `{ok, added, changed, dropped, left, starts}`
    ideas.spec_change_more {idea, id, via?}  # *Talk more*: the record dropped; `{ok, text}`, the words, for the field to open with
    ideas.spec_change_drop {idea, id, via?}  # *Drop it*: the record dropped, nothing else changes; `{ok}`
"""
from __future__ import annotations

import time
from typing import Any

from orkboard.gui.ideas_args import IdeasError, _text, _via
from orkboard.realm import event_log, idea_change, idea_target, ideas, leader_change, look_wait, spec_change

NOT_READY = "That change did not come: ask the Orkmaster again"
NONE_WAITS = "No change waits for this goal"


class SpecChangeFace:
    def _spec_parties(self, slug: str, text: str) -> tuple[list[dict], dict]:
        """`([{party, title}], estimate)` as code reads them from the words, before any model."""
        root = self.root()
        if ideas.idea_page(root, slug) is None:
            raise IdeasError("That goal is gone")
        parties = spec_change.by_code(root, self.state_dir, slug, text)
        return [{"party": p, "title": self._title_of(p)} for p in parties], spec_change.estimate(self.state_dir, root, parties, self.settings_now())

    def spec_change_preview(self, args: dict) -> dict:
        slug, text = _text(args, "idea", 100), args.get("text")
        if not isinstance(text, str):
            raise IdeasError("text is not text")
        mention = spec_change.mention(self.root(), text)
        if mention:
            return {"ok": True, "id": "", "parties": [{"party": mention, "title": self._title_of(mention)}], "estimate": {"calls": 1, "usd_low": None, "usd_high": None}, "via": "change"}
        parties, estimate = self._spec_parties(slug, text)
        return {"ok": True, "id": "", "parties": parties, "estimate": estimate, "via": "spec_change"}

    def spec_change(self, args: dict) -> dict:
        slug, text = _text(args, "idea", 100), args.get("text")
        if not isinstance(text, str):
            raise IdeasError("text is not text")
        mention = spec_change.mention(self.root(), text)
        if mention:                                                    # §224.5: one leader directly, as built
            got = self.change({**args, "party": mention, "text": text})
            return {**got, "parties": [{"party": mention, "title": self._title_of(mention)}], "estimate": {"calls": 1, "usd_low": None, "usd_high": None}, "via": "change"}
        parties, estimate = self._spec_parties(slug, text)
        cid = self.keeper.spec_change_ask(slug, text, [p["party"] for p in parties], estimate)
        self.changed(slug)
        return {"ok": True, "id": cid, "parties": parties, "estimate": estimate, "via": "spec_change"}

    def spec_change_take(self, args: dict) -> dict:
        slug, cid = _text(args, "idea", 100), _text(args, "id", 40)
        with ideas.LOCK:                                              # claimed: a second press finds none waiting
            rec = spec_change.get(self.state_dir, slug, cid)
            if rec is None:
                raise IdeasError(NONE_WAITS)
            if rec.get("status") != "ready":
                raise IdeasError(NOT_READY)
            if self.keeper.busy(slug):
                raise IdeasError("The keeper is busy with this goal: a moment")
            parties = [p for p in rec.get("parties") or [] if isinstance(p, dict) and p.get("party")]
            ops = [p["change"] for p in parties if isinstance(p.get("change"), dict) and (p["change"].get("change") or p["change"].get("drop") or p["change"].get("add"))]
            ops = ops if ideas.plan(self.state_dir, slug) is not None else []
            runner = self.runner(need=True) if ops else None
            spec_change.drop(self.state_dir, slug, cid)
        got = {"added": 0, "changed": 0, "dropped": 0, "left": []}
        try:
            for change in ops:
                one = runner.revise_tasks(slug, change)
                got = {"added": got["added"] + one["added"], "changed": got["changed"] + one["changed"], "dropped": got["dropped"] + one["dropped"],
                       "left": [*got["left"], *one["left"]]}
            if ops:
                now = ideas.plan(self.state_dir, slug) or {}
                self.keeper.write_stages(slug, {**now, "tasks": idea_change.in_order(now.get("tasks") or [])})
        except Exception:
            spec_change.put(self.state_dir, slug, rec)                   # it did not apply: it waits as it did
            raise
        wrote = [p["party"] for p in parties if (p.get("after") or {}).get("lines") and leader_change.write_lines(self.root(), slug, p["party"], p["after"]["lines"])]
        names = ", ".join(str(p.get("title") or p["party"]) for p in parties)
        ideas.update(self.root(), slug, {}, [f"The person decided, {names}: {rec['text']}"])
        starts = self._look_after_change(slug)
        self._ev(event_log.SPEC_CHANGE_ANSWERED, args, idea=slug, answer="take", parties=[p["party"] for p in parties], wrote=wrote, added=got["added"], changed_n=got["changed"],
                 dropped=got["dropped"], via=_via(args))
        self.changed(slug)
        return {"ok": True, **got, "starts": starts}

    def _look_after_change(self, slug: str) -> str:
        """The wait begins again from the accepting (C.4): `look_until` anew, and when the limits run low not before their reset (the reading is done, the work waits: §221.5). Where there is no wait to set
        (`do not wait`, the limits fine) the plan is decided at once. What it did: "wait" · "reset" · "now" · "".

        The plan is decided again with its look not done: a plan of a goal with none (the spec is still being made) waits for `autostart` when it is made."""
        plan = ideas.plan(self.state_dir, slug)
        if plan is None or plan.get("passed_at"):
            return ""
        until = idea_target.reserve_held(self._raw_limits(), self.settings_now(), time.time())
        ideas.edit_plan(self.state_dir, slug, lambda p: (p.pop("look_done", None), p.pop("look_until", None)))
        if self.look_again(slug, floor=until):
            return "reset" if until is not None else "wait"
        what = self.autostart(slug)
        return "now" if what not in ("", "wait", "night", "look") else ""

    def spec_change_more(self, args: dict) -> dict:
        slug, cid = _text(args, "idea", 100), _text(args, "id", 40)
        rec = spec_change.get(self.state_dir, slug, cid)
        if rec is None or not spec_change.drop(self.state_dir, slug, cid):
            raise IdeasError(NONE_WAITS)
        self._ev(event_log.SPEC_CHANGE_ANSWERED, args, idea=slug, answer="more", parties=[p.get("party") for p in rec.get("parties") or []], wrote=[], added=0, changed_n=0, dropped=0, via=_via(args))
        self.changed(slug)
        return {"ok": True, "text": str(rec.get("text") or "")}

    def spec_change_drop(self, args: dict) -> dict:
        slug, cid = _text(args, "idea", 100), _text(args, "id", 40)
        rec = spec_change.get(self.state_dir, slug, cid)
        if rec is None:
            raise IdeasError(NONE_WAITS)
        spec_change.drop(self.state_dir, slug, cid)
        self._ev(event_log.SPEC_CHANGE_ANSWERED, args, idea=slug, answer="drop", parties=[p.get("party") for p in rec.get("parties") or []], wrote=[], added=0, changed_n=0, dropped=0, via=_via(args))
        self.changed(slug)
        return {"ok": True}


def spec_change_commands(ideas_: Any) -> dict:
    """The change to a spec asked of the Orkmaster's commands by name (`gui/ideas.py` adds them to its table: `**spec_change_commands(self)`)."""
    return {"ideas.spec_change": ideas_.spec_change, "ideas.spec_change_preview": ideas_.spec_change_preview, "ideas.spec_change_take": ideas_.spec_change_take,
            "ideas.spec_change_more": ideas_.spec_change_more, "ideas.spec_change_drop": ideas_.spec_change_drop}
