"""One turn of a task's Claude session (core/idea_runner.py, which imports this one): its cost counted once, its tokens, its ledger
line. `IdeaRunner` has it through `SessionMixin`. Split from the runner to keep it under ~600 lines.
"""
from __future__ import annotations

import threading
import time
from pathlib import Path

from orkboard.core.sign_ins import HOLD_H
from orkboard.realm import call_log, idea_spend, jobs, status, tool_errors, tool_run


def _r():
    """The runner's module (it imports this one: looked up when a task runs)."""
    from orkboard.core import idea_runner
    return idea_runner


class SessionMixin:
    """Needs the runner's `repo_root`, `state_dir`, `plan`, `_set_task`, `_log`, `sign_ins` and `_read_limits`."""

    def _session(self, slug: str, tid: str, path: Path, cancel: threading.Event, model: str, env: dict,
                 prompt: str, resume: str, spent: dict, effort: str = "", step: str = "task") -> str:
        """One turn of the task's Claude session (work mode); its cost and tokens add up on the task, and its line
        goes to the idea's ledger (spec 36 §1: `task`, or `fix` for the gate's retry).

        A resumed session reports its running total (`total_cost_usd`): the task keeps it as `session_total` and adds only the
        difference, never below 0; a fresh session adds its whole cost (spec 86 §1). `last_tokens` is what the call read (cache
        reads included): a send back past `idea_task.FRESH_TOKENS` starts a fresh session."""
        r = _r()
        task = next((t for t in (self.plan(slug) or {}).get("tasks") or [] if t.get("id") == tid), {"id": tid})
        total = task.get("session_total")
        before = float(total) if resume and isinstance(total, (int, float)) and not isinstance(total, bool) else None
        try:
            with call_log.of_project(self.repo_root), tool_errors.doing("task"):     # its log and spend: this project's
                _text, cost, tokens, session = jobs.run_work(r.HARNESS, prompt, path, cancel, model=model, env=env,
                                                             resume=resume, effort=effort, before_cost=before)
        except tool_errors.ToolError as e:
            if e.kind != tool_errors.LIMIT:
                if self.sign_ins is not None and self.sign_ins.holds(e):      # its sign-in helps: the task waits for it
                    raise r.Held(time.time() + HOLD_H * 3600, tool_errors.plainly(e)) from e
                raise
            now = time.time()
            raise r.Held(status.reset_of(self._read_limits(now), r.HARNESS, now, 1.0)
                         or now + status.UNKNOWN_RESET_S) from e
        own = tool_run.cost_once(cost, before)
        for key, value in (("cost", own), ("tokens", tokens)):
            if value is not None:
                spent[key] = (spent[key] or 0) + value
        session = session or resume
        task = next((t for t in (self.plan(slug) or {}).get("tasks") or [] if t.get("id") == tid), {"id": tid})
        idea_spend.task_line(self.state_dir, slug, task, step, r.HARNESS, model, own, tokens)
        self._log(slug, tid, f"== the session answered\n{_text}\n", env)
        self._set_task(slug, tid, session=session, cost=spent["cost"], tokens=spent["tokens"], last_tokens=tokens,
                       **({"session_total": cost} if cost is not None else {}))
        return session
