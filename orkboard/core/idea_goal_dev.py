"""Where a goal's tasks land, and a goal into dev (docs/specs/168-the-window-played-as-a-card-games-table.md F1, decisions §283.26), split from core/idea_runner.py.
`IdeaRunner` has it through `GoalDevMixin`. The git is realm/goal_branch.py.

    runner._landing(slug)             # the branch a task of the goal lands on: its `goal/<slug>` while its work is on it, else dev (`merge_into`)
    runner._begin_goal(slug, plan, task)  # a task about to start: the branch made on the goal's first start, dev merged into it as a step starts; the branch to cut from
    runner._goal_finished(slug)       # the goal's last step was accepted: it waits to go into dev, and goes by itself where `ideas.review` is off
    runner.goal_to_dev(slug)          # the person's act (or the runner's own): the goal into dev once, the gate green on dev with it (raises RunnerError)
    runner.on_dev                     # the host's wire: called with the slug when a goal went into dev

**Before**: every task landed in dev when accepted. **After**: a goal begun now has `goal/<slug>`: its tasks land there (rebased onto it, fast-forwarded), a
later step is cut from it with dev merged in as the step starts, and dev moves once, when the goal is `done` (its last step accepted) and the gate is green on dev
with it. `ideas.review` (*Lands in dev by itself*) is that one level up: on, the goal goes by itself; off, it waits on its branch (`waits_for_dev`).
A goal already at work in dev has no `goal_branch.json` and a task of it merged: it lands in dev as before.
"""
from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from orkboard.realm import goal_branch, idea_route


def _r():
    from orkboard.core import idea_runner
    return idea_runner


class GoalDevMixin:
    """Needs the runner's `git`, `state_dir`, `settings`, `_lock`, `_runs`, `_changed`, `_log`."""

    on_dev: Any = None                    # the host's wire: `on_dev(slug)` after a goal went into dev
    _dev_threads: dict[str, threading.Thread]

    def _dev(self) -> str:
        return str(_r().setting(self.settings, "merge_into") or "dev")

    def _landing(self, slug: str) -> str:
        """The branch the goal's tasks land on and are checked against: its own branch while its work is on it, else dev."""
        return goal_branch.in_use(self.state_dir, slug) or self._dev()

    def _pushes_into(self, into: str) -> bool:
        """The project's `push` setting, for a landing in dev; a goal's own branch is never pushed."""
        return bool(_r().setting(self.settings, "push")) and into == self._dev()

    def _begin_goal(self, slug: str, plan: dict, task: dict) -> str:
        """A task of the goal is about to be cut: the branch it is cut from and lands on. The goal's branch is made from dev when its first step starts, and dev is merged
        into it as each later step starts; a conflict there fails the task with the files named (the goal's file keeps it), nothing forced."""
        dev = self._dev()
        self.git.ensure_branch(dev)
        if not self.goal_branches and not goal_branch.in_use(self.state_dir, slug):
            return dev
        step = idea_route.step_of(task)
        branch = goal_branch.begin(self.git, self.state_dir, slug, plan, dev, step)
        if not branch:
            return dev
        goal_branch.step_started(self.git, self.state_dir, slug, step, dev)
        goal_branch.ready(self.state_dir, slug, False)
        return branch

    # -- the goal's end ------------------------------------------------------------------------------------------

    def _goal_finished(self, slug: str) -> None:
        """The goal is `done` (its last step accepted, every task merged): it waits on its branch for dev. Where *Lands in dev by itself* is on it goes now, on a thread of its
        own (the gate takes minutes and the runner's lock is not held through it)."""
        plan = self.plan(slug)
        if not goal_branch.in_use(self.state_dir, slug) or idea_route.steps_left(plan) or idea_route.due(plan):       # a step still to plan or to accept: not the last
            return
        goal_branch.ready(self.state_dir, slug)
        if not _r().setting(self.settings, "review"):
            self._dev_async(slug)

    def _dev_async(self, slug: str) -> None:
        with self._lock:
            threads = self.__dict__.setdefault("_dev_threads", {})
            if (t := threads.get(slug)) is not None and t.is_alive():
                return
            t = threading.Thread(target=self._dev_run, args=(slug,), daemon=True, name=f"goal-dev-{slug}")
            threads[slug] = t
            t.start()

    def _dev_run(self, slug: str) -> None:
        try:
            self.goal_to_dev(slug)
        except Exception:                                   # the reason is in the goal's file (`blocked`) and on its row
            pass
        finally:
            self._changed(slug)

    def dev_busy(self) -> bool:
        return any(t.is_alive() for t in self.__dict__.get("_dev_threads", {}).values())

    def resume_dev(self) -> None:
        """After a restart: a goal that was done on its branch, not blocked, goes into dev by itself where that is on (a goal that waited for the person still waits)."""
        if _r().setting(self.settings, "review"):
            return
        for file in sorted((Path(self.state_dir) / "ideas").glob(f"*/{goal_branch.FILE}")):
            slug = file.parent.name
            got = goal_branch.read(self.state_dir, slug)
            if goal_branch.in_use(self.state_dir, slug) and got.get("ready") and not got.get("blocked"):
                self._dev_async(slug)

    def goal_to_dev(self, slug: str, untested: bool = False) -> dict:
        """The goal into dev once. `{commit, subjects, note, branch}`; refused in words (RunnerError) when it is not done on its branch, dev conflicts with it, or the gate is red
        on dev with it (dev as it was; the reason is kept on the goal's row)."""
        RunnerError = _r().RunnerError
        with self._lock:
            if any(k[0] == slug for k in self._runs):
                raise RunnerError("That goal still has a task running")
            if not goal_branch.in_use(self.state_dir, slug):
                raise RunnerError("That goal has no branch waiting for dev")
            if not goal_branch.read(self.state_dir, slug).get("ready"):
                raise RunnerError("That goal is not done: its last step is not accepted yet")
        dev = self._dev()
        try:
            self.git.ensure_branch(dev)
            got = goal_branch.to_dev(self.git, self.state_dir, slug, dev, threading.Event(), push=bool(_r().setting(self.settings, "push")), untested=untested)
        except (goal_branch.GoalConflict, goal_branch.GoalRed) as e:
            self._changed(slug)
            raise RunnerError(" ".join(str(e).split())[:goal_branch.WHY_MAX]) from None
        except Exception as e:
            raise RunnerError(" ".join(str(e).split())[:300] or "The merge failed") from None
        self._log_goal(slug, f"== the goal went into {dev} · {got['commit'][:10]}\n")
        self._changed(slug)
        if self.on_dev is not None:
            try:
                self.on_dev(slug)
            except Exception:
                pass
        return {**got, "branch": goal_branch.name(slug)}

    def _log_goal(self, slug: str, line: str) -> None:
        plan = self.plan(slug) or {}
        last = next((t for t in reversed(plan.get("tasks") or []) if isinstance(t, dict) and t.get("id")), None)
        if last is not None:
            self._log(slug, str(last["id"]), line)
