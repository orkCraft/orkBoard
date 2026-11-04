"""Stopped and Resume, the project's half (docs/specs/139-the-die-the-door-and-the-bug.md B.2, decisions §246.3): `Ideas` has it through `HaltMixin`.

**Stopped is a state of the project**, kept in its state dir (`<project>/.orkcraft/stopped.json`: when, and `again`, the tasks the halt killed as `[slug, tid]`), so a restart keeps it. `halt` marks every
open project (`mark_stopped`, gui/board_host.py `_halt`) before it stops anything; `resume` clears it (`resume_work`) and starts again each task the halt killed from its start (core/idea_resume.py).

**Nothing starts by itself while stopped** (`stopped()`): the clock's passes return early at each place the Board starts work without the person's press:
  - `Ideas.tick`: the keeper's tick (a goal drafted, a plan made, a plan's next step planned: core/idea_keeper.py `tick`), the runner's tick (a plan's next task, a held task whose window came back), and
    `routines_tick` (a recurring goal that comes back);
  - `route_tick` (gui/ideas_route.py): a route called for, a goal put off that talks at the reset, the §239 queue (`_backlog_next`), and the goals whose route a call found (`route_auto`'s pending set);
  - `ripe_tick` (gui/ideas_route.py): the wait of an agreed goal does not count and its decision is not confirmed by the leaders;
  - `route_auto` itself (a routed goal going to Talk by itself when it is added).
Looking things (`tree_flush`, `mana_tick`, `canvas_tick`, `play_tick`) goes on; they start no work of the orks.

**A goal the person starts by hand wakes the project** (`wake`): `ideas.talk`, `ideas.start`, `ideas.confirm`, `ideas.start_now`, `ideas.route_start` and `ideas.add` (unless it is kept on `hold`) clear stopped first and say
*The orks are back at work* (a toast). A goal that is only edited, answered, dropped or read does not. Needs the host's `toast` and the Ideas' `state_dir`, `runner`, `changed`.
"""
from __future__ import annotations

import json
import time

WAKE = "The orks are back at work"
STARTS = ("ideas.talk", "ideas.start", "ideas.confirm", "ideas.start_now", "ideas.add", "ideas.route_start")     # the person's presses that start something


class HaltMixin:
    @property
    def _stopped_file(self):
        return self.state_dir / "stopped.json"

    def stopped(self) -> bool:
        """The project is stopped: a halt came and no resume (or goal started by hand) since."""
        return self._stopped_file.exists()

    def mark_stopped(self, again: list | tuple = ()) -> None:
        """`halt`: the project is stopped; `again` the tasks it killed, `(slug, tid)`. A second halt before a resume adds to what the first kept."""
        old = self._stopped_read().get("again") or []
        keep: list[list[str]] = []
        for a in [*old, *again]:
            if isinstance(a, (list, tuple)) and len(a) == 2 and list(a) not in keep:
                keep.append([str(a[0]), str(a[1])])
        try:
            self.state_dir.mkdir(parents=True, exist_ok=True)
            self._stopped_file.write_text(json.dumps({"at": time.time(), "again": keep}), encoding="utf-8")
        except OSError:
            pass
        self.changed("")

    def _stopped_read(self) -> dict:
        try:
            got = json.loads(self._stopped_file.read_text(encoding="utf-8"))
            return got if isinstance(got, dict) else {}
        except (OSError, ValueError):
            return {}

    def _stopped_clear(self) -> list[list[str]]:
        again = self._stopped_read().get("again") or []
        try:
            self._stopped_file.unlink()
        except OSError:
            pass
        return again

    def resume_work(self) -> int:
        """`resume`: stopped is cleared and each task the halt killed starts again from its start; how many. Nothing marked: 0."""
        if not self.stopped():
            return 0
        again = self._stopped_clear()
        started = 0
        by_goal: dict[str, list[str]] = {}
        for slug, tid in again:
            by_goal.setdefault(str(slug), []).append(str(tid))
        runner = self.runner() if by_goal else None
        for slug, tids in by_goal.items():
            try:
                started += len(runner.resume(slug, tids)) if runner is not None else 0
            except Exception as e:                  # one goal that cannot start again never keeps the others stopped
                self.host.toast(f"{type(e).__name__}: {e}", title="Resume", severity="error")
        self.changed("")
        return started

    def wake(self) -> bool:
        """A goal was started by hand: stopped ends (what the halt killed stays stopped: that goal's is the person's call) and the page says it. True when it was stopped."""
        if not self.stopped():
            return False
        self._stopped_clear()
        self.host.toast(WAKE, title="Resume")
        self.changed("")
        return True

    def running_tasks(self) -> list[tuple[str, str]]:
        """The tasks that run now, for a halt to keep (none with no runner built)."""
        runner = self._runner
        try:
            return list(runner.running_tasks()) if runner is not None else []
        except Exception:                           # a runner that cannot say leaves the halt as it was: stopped, with nothing to start again
            return []
