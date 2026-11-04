"""Resume, the runner's half (docs/specs/139-the-die-the-door-and-the-bug.md B.2, decisions §246.3): **Stop all** (`IdeaRunner.stop_all`) puts each task that ran at `failed` with *stopped by Stop all*,
and the idea with it; `resume(slug, tids)` starts again each task the halt killed, **from its start as a plan's task starts** (`waiting`, then the tick takes it when its turn comes; its worktree and the
commits on its branch are kept), and the idea is `working` again. A task that is not at `failed` for the halt's reason any more (the person dropped it, sent it back, merged it meanwhile) is left as it is.
Split from the runner to keep it under ~600 lines; `IdeaRunner` has it through `ResumeMixin`. Needs the runner's `_lock`, `plan`, `_save_tasks`, `_set_idea`, `_active`, `_until`, `_changed` and `tick`.
"""
from __future__ import annotations

STOPPED_BY = "stopped by Stop all"


class ResumeMixin:
    def resume(self, slug: str, tids: list[str]) -> list[str]:
        """Start `tids` of `slug` anew; the ids that were started again."""
        started: list[str] = []
        with self._lock:
            plan = self.plan(slug)
            if plan is None:
                return []
            for t in plan["tasks"]:
                if t.get("id") in tids and t.get("state") == "failed" and t.get("error") == STOPPED_BY:
                    t.update(state="waiting", error="", note="", finished="")
                    for key in ("held_for", "held_until", "held_line", "held_why"):
                        t.pop(key, None)
                    self._until.pop((slug, t.get("id")), None)
                    started.append(t["id"])
            if not started:
                return []
            self._save_tasks(slug, plan["tasks"])
            self._set_idea(slug, "working")
            if slug not in self._active:
                self._active.append(slug)
        self._changed(slug)
        self.tick()
        return started
