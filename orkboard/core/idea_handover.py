"""A goal between its steps and at its end (docs/specs/99-a-goals-way.md §9), split from core/idea_runner.py to keep it under ~600 lines. `IdeaRunner` has it through
`HandoverMixin`.

    runner._hand_over(slug, plan, tasks, running, failed, changed)   # the runner's tick found every task of the plan merged or dropped, or one failed: the goal is held
                                                                     #   for the next step, or ended (`_finish`)

`self` is the runner: `_active`, `_save_tasks`, `_changed`, `_read`, `_dir`, `plan`, `_set_idea`. A step of the goal that landed waits for its leader's acceptance (spec 152 B.1).
"""
from __future__ import annotations

from orkboard.realm import idea_route


class HandoverMixin:
    def _hand_over(self, slug: str, plan: dict, tasks: list[dict], running: list[dict], failed: dict | None, changed: bool) -> None:
        if changed:
            self._save_tasks(slug, tasks)
        if not running and failed is None and (idea_route.steps_left(plan) or idea_route.due(plan)):       # another step to plan, or the step waits for its leader's acceptance (spec 152 B.1)
            if self._state_of(slug) != "working":        # the keeper could not plan the next step (it put the goal at `failed`): Start goes on from here
                self._active.remove(slug)
                self._changed(slug)
            elif changed:
                self._changed(slug)
        elif not running:
            self._finish(slug, failed)
        elif changed:
            self._changed(slug)

    def _state_of(self, slug: str) -> str:
        return str((self._read(self._dir(slug) / "state.json") or {}).get("state") or "")

    def _finish(self, slug: str, failed: dict | None) -> None:
        self._active.remove(slug)
        if failed is None:
            tasks = (self.plan(slug) or {}).get("tasks") or []
            self._set_idea(slug, "plan" if tasks and not any(t.get("state") == "merged" for t in tasks) else "done")       # all dropped: nothing landed, nothing to run
        else:
            why = failed.get("error") or "it failed"
            self._set_idea(slug, "failed", f"{failed.get('title') or failed.get('id')}: {why}")
        self._changed(slug)
