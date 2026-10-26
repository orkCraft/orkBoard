"""The runner's holds (core/idea_runner.py, which imports this one): a task held for its tool's sign-in, held until its window
comes back, and the quota the runner reads. `IdeaRunner` has them through `HoldsMixin`. Split from the runner to keep it under ~600 lines.
"""
from __future__ import annotations

import datetime as dt
import threading
import time

from orkboard.core.sign_ins import HOLD_H


class Held(Exception):
    """A task held, not failed: until `until` (its window, else its sign-in's hold). Here, not in the runner, so a session that looks
    the runner's module up again (a test that drops it) raises the class the runner catches."""

    def __init__(self, until: float, line: str = "") -> None:
        """`line`: the tool's refused sign-in in words, when the work is held for the tool's sign-in (spec 45 §6)."""
        super().__init__("held")
        self.until, self.line = until, line


def _r():
    """The runner's module (it imports this one: looked up when a hold is made)."""
    from orkboard.core import idea_runner
    return idea_runner


class HoldsMixin:
    """Needs the runner's `state_dir`, `repo_root`, `sign_ins`, `_until`, `_limits_fn`, `_limits`, `_limits_at` and `_read`."""

    def signed_out(self, harness: str = "") -> bool:
        """Whether the host says this tool needs its sign-in: what runs by itself waits for it."""
        return self.sign_ins is not None and bool(self.sign_ins.blocked(harness or _r().HARNESS))

    def _hold_sign_in(self, task: dict, line: str, harness: str = "") -> None:
        """The task waits for its tool's sign-in: at most `HOLD_H` hours, then it fails with `line`."""
        task.update(state="held", note="", held_for="sign_in", harness=harness or _r().HARNESS, held_line=line[:600],
                    held_until=dt.datetime.fromtimestamp(time.time() + HOLD_H * 3600).isoformat(timespec="seconds"))

    def held_for(self, harness: str) -> int:
        """How many tasks wait for this tool's sign-in now."""
        n = 0
        for state_file in (self.state_dir / "ideas").glob("*/plan.json"):
            plan = self._read(state_file) or {}
            n += sum(1 for t in plan.get("tasks") or [] if isinstance(t, dict) and t.get("state") == "held"
                     and t.get("held_for") == "sign_in" and (t.get("harness") or _r().HARNESS) == harness)
        return n

    def _hold(self, slug: str, task: dict, until: float, why: str = "", line: str = "") -> None:
        """`line`: what the hold means, in words, for the person's reserve or the week's pace (realm/idea_target.py `hold_line`)."""
        self._until[(slug, task.get("id"))] = until
        task.update(state="held", note=f"{why}after {dt.datetime.fromtimestamp(until):%H:%M}", held_why=line)

    def release_holds(self, slug: str) -> int:
        """The person's Start now: what the reserve or the week's pace holds of this goal's tasks goes on. How many were let go."""
        with self._lock:
            plan = self.plan(slug)
            if plan is None:
                return 0
            n = 0
            for t in plan["tasks"]:
                if t.get("state") == "held" and str(t.get("note") or "").startswith(("reserve", "week")):
                    t.update(state="waiting", note="", held_why="")
                    self._until.pop((slug, t.get("id")), None)
                    n += 1
            if n:
                self._save_tasks(slug, plan["tasks"])
                self._changed(slug)
            return n

    def _read_limits(self, now: float) -> list:
        if self._limits_fn is not None:
            try:
                return list(self._limits_fn() or [])
            except Exception:
                return []
        if now - self._limits_at > _r().LIMITS_EVERY_S:
            self._limits_at = now

            def read() -> None:
                from orkboard.sources.limits import fetch_limits
                try:
                    self._limits = list(fetch_limits(self.repo_root))
                except Exception:          # a quota never stops the work
                    pass
            threading.Thread(target=read, daemon=True, name="ideas-limits").start()
        return self._limits
