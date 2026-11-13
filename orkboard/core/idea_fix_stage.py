"""Fix it before dev (goal "The battle and the gate", stage H; decisions §303.5): a goal unmerged on its own branch whose way to dev went red runs its stage again.
Split from core/idea_runner.py, which is past 600 lines: `IdeaRunner` has it through `FixStageMixin`. The page sends it as `ideas.gate_fix_stage` (gui/ideas_battle.py), sealed.

    runner.fix_stage(slug)    # one task *Make the failing tests pass: <ids>* (the ids the red gate kept, realm/goal_branch.py) added to the goal's plan through the runner's own
                              #   plan writer (`revise_tasks`), then the goal set to work (`start`): `{task, ids}`; RunnerError in words where the goal is in dev, its way is not red, or a task runs
    COST                      # what running the stage again is capped at, said before it runs (`ideas.gate_guards`, `ideas.gate_fix_stage`): `{calls, usd_high}`

**Its cost is not known yet.** A task's run is one session of its tool in work mode (`jobs.run_work`) and the gate's one fix on that session after, as many turns as the work takes;
the runner gives it no cap in money (`Harness.work` passes no `--max-budget-usd`, unlike a keeper's call under `idea_target.budget`, whose `CAPS` have no `task`). So both are None,
never a number made up, and the seal says *cost not known yet*, as *Start the work* does.

The task is of the plan's last step (`idea_route.at_step`), stamped as that step's tasks are, so once it lands the step is done again and the goal waits for dev as before.
No face and no model here: the work is the runner's, as any task's.
"""
from __future__ import annotations

from orkboard.realm import goal_branch, idea_route, lexicon

COST = {"calls": None, "usd_high": None}
TITLE_CHARS = 300            # the task's title names its failing tests up to this; its brief names every one
STAMPED = ("party", "craft", "leader", "section")       # what a task of the step carries that the added one carries too


def _r():
    from orkboard.core import idea_runner
    return idea_runner


def task_title(ids: list[str]) -> str:
    """*Make the failing tests pass: <ids>*, cut with … past `TITLE_CHARS`."""
    title = lexicon.term("fix_stage_task").replace("<tests>", ", ".join(ids))
    return title if len(title) <= TITLE_CHARS else title[:TITLE_CHARS - 1].rstrip(", ") + "…"


def _brief(ids: list[str], files: list[str], said: str) -> str:
    lines = [lexicon.term("fix_goal_named").replace("<tests>", ", ".join(ids))]
    if files:
        lines.append(f"The gate ran: {', '.join(files)}")
    if said:
        lines.append(f"It said: {said}")
    return "\n".join([*lines, "Make them pass without changing what they test."])


class FixStageMixin:
    """Needs the runner's `state_dir`, `_lock`, `_runs`, `board_held`, `plan`, `_dev`, `revise_tasks` and `start`."""

    def fix_stage(self, slug: str) -> dict:
        """The goal's stage again: one task of its failing tests added, the goal at work. Refused in words (RunnerError), nothing written, where the goal is in dev
        (Fix it lays a new goal there), where its way to dev is not red with a failing test named, where a task of it still runs, or where it has no plan."""
        RunnerError = _r().RunnerError
        if why := self.board_held():
            raise RunnerError(why)
        with self._lock:
            if not goal_branch.in_use(self.state_dir, slug):
                raise RunnerError(lexicon.term("fix_in_dev"))
            got = goal_branch.read(self.state_dir, slug)
            ids = list(dict.fromkeys(str(x) for x in got.get("failing") or [] if str(x).strip()))
            if got.get("blocked_kind") != "red" or not ids:
                raise RunnerError(lexicon.term("fix_not_red").replace("<way>", self._dev()))
            if any(k[0] == slug for k in self._runs):
                raise RunnerError(goal_branch.words("dev_task_running"))
            plan = self.plan(slug)
            if plan is None:
                raise RunnerError("This goal has no plan yet")
            n = idea_route.at_step(plan)
            of_step = next((t for t in reversed(plan["tasks"]) if isinstance(t, dict) and idea_route.step_of(t) == n), {})
            add = {"key": "fix", "title": task_title(ids), "kind": "code", "tier": "warrior", "after": [], "step": n,
                   "brief": _brief(ids, [str(x) for x in got.get("files") or []], str(got.get("blocked") or "")), **{k: of_step[k] for k in STAMPED if k in of_step}}
            self.revise_tasks(slug, {"add": [add]})
            tid = next((str(t.get("id")) for t in reversed((self.plan(slug) or {}).get("tasks") or []) if t.get("title") == add["title"]), "")
        self.start(slug)
        return {"task": tid, "ids": ids}
