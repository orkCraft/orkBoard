"""Every error of a goal's work, by code, no model (docs/specs/168-the-window-played-as-a-card-games-table.md G2, decisions §283.16.11): what the result tables lay out as a line or a card at the leader whose work it was.

    goal_errors.of(tasks, home)      # [{party, kind, task, title, line}] in the plan's order, at most MAX

`kind` says what went wrong: `failed` (a task that failed, its error as the runner wrote it), `sent_back` (a task that ran more than one round: it was sent back), `test` (a test that was red on the task's gate and not red before
the goal: `tests.failing`), `finding` (a check task's finding left unfixed; `env` too when it is of the place it ran in). A task the plan dropped has none. `party` is the task's own, else `home` (the goal's party).
"""
from __future__ import annotations

from orkboard.realm import idea_checks

MAX = 40
LINE_MAX = 200
TEST_MAX = 5                     # the red tests one task names, at most


def _cut(text: object, n: int = LINE_MAX) -> str:
    s = " ".join(str(text or "").split())
    return s if len(s) <= n else s[:n - 1].rstrip() + "…"


def of(tasks: list[dict], home: str = "") -> list[dict]:
    """The errors of the goal's tasks, see the module."""
    out: list[dict] = []
    for t in tasks or []:
        if not isinstance(t, dict) or t.get("state") == "dropped":
            continue
        base = {"party": str(t.get("party") or home), "task": str(t.get("id") or ""), "title": _cut(t.get("short") or t.get("title"), 80)}

        def add(kind: str, line: str, **more: object) -> None:
            out.append({**base, "kind": kind, "line": _cut(line), **more})

        if t.get("state") == "failed":
            add("failed", t.get("error") or "it failed")
        rounds = t.get("round")
        if isinstance(rounds, int) and not isinstance(rounds, bool) and rounds > 1:
            add("sent_back", f"sent back {rounds - 1} time{'s' if rounds > 2 else ''}")
        tests = t.get("tests") if isinstance(t.get("tests"), dict) else {}
        before = {str(i) for i in tests.get("red_before") or []}
        red = [str(i) for i in tests.get("failing") or [] if str(i) not in before]
        for i in red[:TEST_MAX]:
            add("test", i)
        if not red and isinstance(tests.get("failed"), int) and tests["failed"] > 0 and not before:
            add("test", f"{tests['failed']} test{'s' if tests['failed'] > 1 else ''} failed")
        for f in (t.get("findings") if isinstance(t.get("findings"), list) else []):
            if isinstance(f, dict) and not f.get("fixed"):
                add("finding", f"{f.get('where') or ''}: {f.get('what') or ''}".strip(": "), **({"env": True} if idea_checks.is_env(f) else {}))
    return out[:MAX]
