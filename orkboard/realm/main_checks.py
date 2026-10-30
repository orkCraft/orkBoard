"""The checks on a goal's way into main (docs/specs/111-a-goals-rune-release-and-live-at-the-portal.md §4.2, decisions §188.3): the plan's picks are
made onto main's head in a trial worktree (`goal_main.trial`, kept until the checks end, then removed), and each check of `gate_config.main_checks` runs
there in order, with the gate's timeout.

    steps = main_checks.run(repo, state_dir, "lobby", root=root, into="dev", main="main", on_step=lambda steps: ...)
        # [{"name": "The merge", "state": "passed", "words": "3 commits apply to main"}, {"name": "Tests", "state": "failed", "words": "2 failed, 9 passed in 1.1s"}]

`state` is `waiting`, `running`, `passed` or `failed`; `words` says why in a few words (a failed check's reason, the last line of what it printed; a passed
check's note). `on_step` gets the whole list (a copy) at the start and at every change. *The merge* is the picks applying (the plan's own trial), so a pick
that conflicts fails it and leaves the others `waiting`; a check that fails stops the run, the checks after it stay `waiting`. A check that runs the gate (*Tests*)
runs it as a task's result does (`IdeaGit.gate_run`: `[gate]`, else the project's own, on the files the picks touched); a project with no tests has nothing to run
there and the check passes saying so, since this is the last way into main and not a task's result. A check that calls a model would carry its tool's mark (none
does yet). No face and no model. The worktree is gone whatever happens; the repository's lock is held only while it is made and removed, and no ref moves, so the
person's main and dev are never touched.
"""
from __future__ import annotations

import os
import subprocess
import threading
from pathlib import Path
from typing import Any, Callable

from orkboard.realm import gate_config, goal_main, jobs
from orkboard.realm.gate_config import Check
from orkboard.realm.idea_git import IdeaGit

WORDS_MAX = 160


def _long(timeout_s: int) -> str:
    """*It took longer than 15 minutes* (seconds under a minute)."""
    n, unit = (timeout_s // 60, "minute") if timeout_s >= 60 else (timeout_s, "second")
    return f"It took longer than {n} {unit}{'' if n == 1 else 's'}"


def _step(name: str, state: str = "waiting", words: str = "") -> dict[str, str]:
    return {"name": name, "state": state, "words": words}


def last_line(text: str) -> str:
    """The last line that says something, short: a check's reason in a few words (pytest's *2 failed, 9 passed in 1.1s* without its rulers)."""
    for line in reversed(str(text or "").splitlines()):
        line = " ".join(line.strip("=-_*# \t").split())
        if line:
            return line[:WORDS_MAX]
    return ""


def _command(path: Path, line: str, cancel: threading.Event, timeout_s: int) -> tuple[bool, str]:
    """(passed, words) of one written command run in the trial worktree, as the gate runs its own: words, or `sh -c` when it needs a shell."""
    argv = gate_config.test_argv(line)
    if not argv:
        return False, "The check has no command"
    try:
        proc = subprocess.Popen(argv, cwd=path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, start_new_session=True,
                                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    except OSError as e:
        return False, f"{argv[0]} could not start: {e}"[:WORDS_MAX]
    box: list[str] = []
    reader = threading.Thread(target=lambda: box.append(proc.stdout.read() if proc.stdout else ""), daemon=True)
    reader.start()
    try:
        jobs._wait(proc, cancel, timeout_s, "ideas/main-check")
    except RuntimeError:                                       # the time is up (a stop is an InterruptedError, the caller's)
        reader.join(5)
        return False, _long(timeout_s)
    reader.join(5)
    out = box[0] if box else ""
    if proc.returncode == 0:
        return True, ""
    return False, last_line(out) or f"It ended with exit code {proc.returncode}"


def _gate(git: IdeaGit, path: Path, old: str, cancel: threading.Event, timeout_s: int) -> tuple[bool, str]:
    """(passed, words) of the gate's own run on what the picks touched, as a task's result runs it."""
    try:
        run = git.gate_run(path, old, cancel, timeout_s)
    except RuntimeError:
        return False, _long(timeout_s)
    if not run.ran:
        return True, last_line(run.out.split("\n! ")[0]) or "No tests to run"
    if run.ok:
        return True, ""
    return False, run.env or last_line(run.out) or f"It ended with exit code {run.code}"


def run(repo: Path, state_dir: Path, slug: str, *, root: Path | None = None, into: str = "dev", main: str = "",
        on_step: Callable[[list[dict[str, str]]], Any] | None = None, cancel: threading.Event | None = None,
        timeout_s: int | None = None) -> list[dict[str, str]]:
    """Runs the checks (module docstring) and returns the last steps. A stop (`cancel` set) raises InterruptedError, the worktree gone."""
    cancel = cancel or threading.Event()
    gate = gate_config.read(Path(repo))
    checks: list[Check] = gate_config.main_checks(Path(repo))
    timeout = timeout_s or (int(gate.timeout_min * 60) if gate.timeout_min else jobs.TEST_TIMEOUT_S)
    steps = [_step(c.name) for c in checks]

    def say(at: int, state: str, words: str = "") -> None:
        steps[at] = _step(checks[at].name, state, words)
        if on_step is not None:
            on_step([dict(s) for s in steps])

    if on_step is not None:
        on_step([dict(s) for s in steps])
    git = IdeaGit(Path(repo))
    say(0, "running")
    with goal_main.trial(repo, state_dir, slug, root=root, into=into, main=main) as t:
        if cancel.is_set():
            raise InterruptedError("stopped")
        if t.path is None:
            say(0, "failed", (t.words or "Nothing applies to main")[:WORDS_MAX * 2])
            return steps
        n = len(t.plan["commits"])
        say(0, "passed", f"{n} {'commit applies' if n == 1 else 'commits apply'} to {main or 'main'}")
        for at, check in enumerate(checks[1:], 1):
            say(at, "running")
            ok, words = _gate(git, t.path, t.old, cancel, timeout) if check.gate else _command(t.path, check.run, cancel, timeout)
            say(at, "passed" if ok else "failed", words)
            if not ok:
                break
    return steps
