"""Fix Orkboard in the window (core/repair.py, docs/specs/119-the-hammer-and-the-bug.md, decisions §197): the bug at the end of the
tabs' row starts Claude Code on Orkboard's own code with the person's line and the logs; when Claude pushes to `main` the bug offers
**Update and restart**, which is the restart gui/updates.py already makes (`restart_wanted`, `quit`), checked first and rolled back by
`board_host.main` when the new code does not start.

    fix = Repair(host)
    fix.tick(now)                          # from the host's clock: asks `landed()` every 30 s on a thread, only while a fix runs
    host.commands.update(fix.commands())   # repair.start · repair.stop · repair.update

The snapshot's `repair` is {"can", "why", "state": idle · working · ready · updating · failed, "started_at", "landed", "error"}. A
fix started before Orkboard restarted is still followed (`state.json`); after a restart on the fix the state is idle. A phone may
start, stop and update a fix (an exception to spec 37 §8: gui/board_host.py `BoardPhone`); it edits nothing itself.
"""
from __future__ import annotations

import threading
import time
from typing import Any, Callable

from orkboard import brand
from orkboard.core import repair as core
from orkboard.gui import logs_save

CHECK_EVERY_S = 30.0          # while a fix runs, main is looked at this often


class RepairError(Exception):
    """Said to the person as it is."""


class Repair:
    def __init__(self, host, engine=core) -> None:
        self.host = host
        self.core = engine
        self.phase = "idle"            # idle · working · updating · failed (ready is working with something landed)
        self.error = ""
        self.started_at: float | None = None
        self.landed: list[dict] = []
        self._starting = False
        self._asking = False
        self._asked_at: float | None = None
        self._rolled = ""              # the sha the checkout went back to, until the person has been told
        self._resume()

    # -- what the page sees ------------------------------------------------------------------------

    def can(self) -> tuple[bool, str]:
        if self.host.town.demo:
            return False, ""
        try:
            return self.core.can()
        except Exception as e:                       # never breaks the snapshot
            return False, f"{type(e).__name__}: {e}"

    def state(self) -> str:
        if self.phase in ("updating", "failed"):
            return self.phase
        if self.phase == "working" and self.landed:
            return "ready"
        return self.phase

    def snapshot(self) -> dict[str, Any]:
        can, why = self.can()
        state = self.state()
        return {"can": can, "why": why, "state": state, "started_at": self.started_at if state != "idle" else None,
                "landed": [dict(c) for c in self.landed], "error": self.error if state == "failed" else ""}

    # -- the state kept on disk --------------------------------------------------------------------

    def _resume(self) -> None:
        """A fix started before this Orkboard opened is followed again; one already in this copy (the restart on it came up) is done."""
        if self.host.town.demo:
            return
        try:
            if (sha := self.core.rolled_back()):
                self._rolled = sha
                self.phase = "failed"
                self.error = self._rollback_words(sha)
                return
            state = self.core.read_state()
            if not state or not state.get("pid"):
                return
            if self.core.applied(str(state.get("base") or "")):
                self.core.clear_state()
                return
            self.phase, self.started_at = "working", float(state.get("started_at") or time.time())
        except Exception:                            # a broken folder is no fix
            self.phase = "idle"

    @staticmethod
    def _rollback_words(sha: str) -> str:
        return f"{brand.name()} did not start on the fix: it went back to {sha[:7]}"

    # -- the clock ---------------------------------------------------------------------------------

    def tick(self, now: float) -> None:
        if self.host.town.demo:
            return
        if self._rolled:
            sha, self._rolled = self._rolled, ""
            self.core.told()
            self.host.town.toast(self._rollback_words(sha), title="Fix", severity="error", timeout=20)
        if self.phase != "working" or self._starting or self._asking:
            return
        if self.landed and not self.core.alive():
            return                                   # in, and Claude has finished: nothing more to wait for
        if self._asked_at is not None and now - self._asked_at < CHECK_EVERY_S:
            return
        self._asked_at, self._asking = now, True
        state = self.core.read_state()

        def work() -> None:
            try:
                found = self.core.landed(str(state.get("base") or ""))
                runs = self.core.alive()
            except Exception:
                found, runs = [], True
            self.host.town.call(self._read, found, runs)

        self._spawn(work, "repair-landed")

    def _read(self, found: list[dict], runs: bool) -> None:
        """What the thread found, applied on the host's loop."""
        self._asking = False
        if self.phase != "working" or self._starting:
            return
        before = (self.state(), [c["sha"] for c in self.landed])
        if found:
            self.landed = found
        elif not runs:
            self.phase = "failed"
            self.error = ("Claude Code stopped and nothing came in to main. Look at the session in the Claude app, "
                          "or Try again.")
        if (self.state(), [c["sha"] for c in self.landed]) != before:
            self.host.on_change()

    @staticmethod
    def _spawn(fn: Callable[[], None], name: str) -> None:
        threading.Thread(target=fn, daemon=True, name=name).start()

    # -- the page's commands -----------------------------------------------------------------------

    def start(self, args: dict) -> dict[str, Any]:
        """Claude Code started on Orkboard's own code with the person's line and the logs; the worktree is made on a thread."""
        can, why = self.can()
        if not can:
            raise RepairError(why or f"{brand.name()} cannot be fixed from here")
        if self.phase == "updating":
            raise RepairError("The update is running")
        if self._starting:
            return self.snapshot()
        said = args.get("said") if isinstance(args.get("said"), str) else ""
        try:
            zipped = logs_save.pack(self.host, 1, said, page=args.get("page"))
        except Exception as e:
            raise RepairError(f"The logs could not be packed: {type(e).__name__}: {e}") from None
        self.phase, self.error, self.landed = "working", "", []
        self.started_at, self._starting = time.time(), True
        self.core.forget_can()

        def work() -> None:
            try:
                state = self.core.start(said, zipped, self.started_at, cmd=list(self.host.town.machine.repair_command))
                self.host.town.call(self._started, state, "")
            except self.core.RepairError as e:
                self.host.town.call(self._started, None, str(e))
            except Exception as e:                   # nothing here ends the thread unsaid
                self.host.town.call(self._started, None, f"{type(e).__name__}: {e}")

        self._spawn(work, "repair-start")
        self.host.on_change()
        return self.snapshot()

    def _started(self, state: dict | None, error: str) -> None:
        self._starting = False
        if state is None:
            self.phase, self.error = "failed", error
        else:
            self.started_at = float(state.get("started_at") or self.started_at or time.time())
            self._asked_at = None
            self.host.town.toast(f"Claude Code started on {brand.name()}'s code: open Fix Orkboard in the Claude app",
                                 title="Fix")
        self.host.on_change()

    def stop(self, args: dict) -> dict[str, Any]:
        """The fix stopped (its worktree stays) and the bug is idle again."""
        if self.phase == "updating":
            raise RepairError("The update is running")
        self.core.stop()
        self.core.clear_state()
        self.phase, self.error, self.landed, self.started_at = "idle", "", [], None
        self.host.on_change()
        return self.snapshot()

    def update(self, args: dict) -> dict[str, Any]:
        """The fix pulled and checked on a thread; the window restarts when the new code imports and says its version."""
        if self.phase == "updating":
            return self.snapshot()
        if self.state() != "ready":
            raise RepairError("There is no fix to update to")
        self.phase, self.error = "updating", ""

        def work() -> None:
            try:
                old = self.core.head()
                result = self.core.update()
            except Exception as e:
                old, result = "", self.core.updates.Result(False, f"{type(e).__name__}: {e}")
            self.host.town.call(self._updated, result, old)

        self._spawn(work, "repair-update")
        self.host.on_change()
        return self.snapshot()

    def _updated(self, result, old: str) -> None:
        if result.ok:
            if old:
                self.core.remember_good(old)
            self.host.town.toast(f"{brand.name()} is updated on the fix; it restarts now", title="Fix")
            self.host.on_change()                    # the phase stays `updating` until the window closes on the restart
            self.host.updates.restart_wanted = True
            self.host.updates.quit()
            return
        self.phase, self.error = "failed", result.output
        self.host.town.toast(f"The fix did not install. {brand.name()} keeps running as it was.", title="Fix",
                             severity="error", timeout=15)
        self.host.on_change()

    def commands(self) -> dict[str, Callable[[dict], Any]]:
        return {"repair.start": self.start, "repair.stop": self.stop, "repair.update": self.update}
