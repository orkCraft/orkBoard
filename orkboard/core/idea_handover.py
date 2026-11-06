"""A goal between its steps and at its end (docs/specs/99-a-goals-way.md §9), split from core/idea_runner.py to keep it under ~600 lines. `IdeaRunner` has it through
`HandoverMixin`.

    runner._hand_over(slug, plan, tasks, running, failed, changed)   # the runner's tick found every task of the plan merged or dropped, or one failed: the goal is held
                                                                     #   for the next step, or ended (`_finish`)

`self` is the runner: `_active`, `_save_tasks`, `_changed`, `_state_of`, `_finish`.
"""
from __future__ import annotations

from orkboard.realm import idea_route


class HandoverMixin:
    def _hand_over(self, slug: str, plan: dict, tasks: list[dict], running: list[dict], failed: dict | None, changed: bool) -> None:
        if changed:
            self._save_tasks(slug, tasks)
        if not running and failed is None and idea_route.steps_left(plan):
            if self._state_of(slug) != "working":        # the keeper could not plan the next step (it put the goal at `failed`): Start goes on from here
                self._active.remove(slug)
                self._changed(slug)
            elif changed:
                self._changed(slug)
        elif not running:
            self._finish(slug, failed)
        elif changed:
            self._changed(slug)
