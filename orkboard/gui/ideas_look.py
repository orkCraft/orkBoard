"""The look's wait on the host (docs/specs/144-a-specs-wait-and-a-change-through-the-orkmaster.md A; decisions §224.3, §225.1): a spec made waits for the person's look,
`look_wait` (*Give me time to look*), before its plan is passed by itself. The wait is a clock time kept with the plan (`look_until`, epoch seconds; `start_at`, the same as the
local time the faces read); it passes with no face open too. A mixin of `Ideas`, beside `BoardMixin`'s `autostart` and `night_tick`.

    look_begin(slug, plan)        # `autostart`'s: True when the plan now waits for its look (written, published, `look_waits`); False when it goes on to be decided
    look_tick(now=None)           # the host's clock: each plan whose look ended is decided again by `autostart` with the wait done (`look_done`); how many ended
    look_again(slug)              # a new look from now (an accepted change begins the wait again, C.4); False with no wait
"""
from __future__ import annotations

import time

from orkboard import settings
from orkboard.realm import event_log, ideas, look_wait, spec_change

SCAN_S = 5.0                         # the plans are looked through this often


class LookMixin:
    def _wall(self) -> float:
        return time.time()

    def _look_choice(self) -> str:
        return look_wait.clean(self.settings_now().get("look_wait", settings.IDEAS["look_wait"]))

    def _look_set(self, slug: str, until: float, choice: str) -> None:
        def write(p: dict) -> None:
            p.update(look_until=until, start_at=look_wait.iso(until))
            p.pop("look_done", None)
        ideas.edit_plan(self.state_dir, slug, write)
        self._ev(event_log.LOOK_WAITS, idea=slug, until=until, choice=choice)
        self._publish(slug)

    def look_begin(self, slug: str, plan: dict) -> bool:
        """A plan that would start by itself (A.2): it waits for its look when `look_wait` is not `none`, no look is over for it, and none is set yet."""
        choice = self._look_choice()
        if choice == "none" or plan.get("look_done"):
            return False
        now = self._wall()
        if plan.get("look_until"):
            return float(plan["look_until"]) > now          # kept: it ends at its time (the tick), not before
        self._look_set(slug, look_wait.until(choice, now, str(self.settings_now().get("night") or settings.IDEAS["night"])), choice)
        return True

    def look_again(self, slug: str) -> bool:
        """The wait begins again from now (an accepted change: C.4); False with `look_wait` `none` (the plan is decided at once by the caller)."""
        choice = self._look_choice()
        if choice == "none" or ideas.plan(self.state_dir, slug) is None:
            return False
        self._look_set(slug, look_wait.until(choice, self._wall(), str(self.settings_now().get("night") or settings.IDEAS["night"])), choice)
        return True

    def look_drop(self, slug: str) -> None:
        """A plan passed by the person: its wait is dropped with it."""
        plan = ideas.plan(self.state_dir, slug)
        if plan and (plan.get("look_until") or plan.get("look_done")):
            def lift(p: dict) -> None:
                if p.get("look_until") and p.get("start_at") == look_wait.iso(p["look_until"]):
                    p["start_at"] = None
                p.pop("look_until", None)
                p.pop("look_done", None)
            ideas.edit_plan(self.state_dir, slug, lift)

    def look_tick(self, now: float | None = None) -> int:
        """The host's clock (A.3): each plan with `look_until <= now`, not passed, not stopped, in `plan`, and with no change open on its goal, is decided again by `autostart`, so the money rule, the
        night, the collisions and the open questions still hold it. A clock time, not a countdown: it passes with no face open. How many ended."""
        if now is None:                                           # the clock's call: the plans are looked through every few seconds; a call with a time given always looks
            gone = time.monotonic()
            if gone - self.__dict__.get("_look_scan", float("-inf")) < SCAN_S:
                return 0
            self.__dict__["_look_scan"] = gone
            now = self._wall()
        if self.stopped():
            return 0
        ended = 0
        off = self._look_choice() == "none"                       # the setting turned off meanwhile: every look is over
        for i in ideas.ideas(self.root(False)):
            slug = i["slug"]
            plan = ideas.plan(self.state_dir, slug)
            if not plan or not plan.get("look_until") or plan.get("passed_at") or plan.get("stopped"):
                continue
            if not off and float(plan["look_until"]) > now:
                continue
            if ideas.state(self.state_dir, slug)["state"] != "plan" or spec_change.open_on(self.state_dir, slug):
                continue
            def done(p: dict) -> None:
                p.pop("look_until", None)
                p["look_done"] = True
                p["start_at"] = None
            ideas.edit_plan(self.state_dir, slug, done)
            what = ""
            try:
                what = self.autostart(slug)
            except Exception:                                    # whether it starts never breaks the clock
                what = "wait"
            how = "night" if what == "night" else "wait" if what in ("", "wait") else "started"
            self._ev(event_log.LOOK_ENDED, idea=slug, how=how)
            self._publish(slug)
            ended += 1
        return ended
