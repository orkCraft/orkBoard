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
import time
import threading
import uuid
from pathlib import Path
from typing import Any, Callable

from orkboard.realm import gate_config, gate_rerun, goal_main, jobs, worktrees
from orkboard.realm.gate_config import Check
from orkboard.realm.idea_git import GateRun, IdeaGit, _git, _ok

WORDS_MAX = 160
SAID_MAX = 3                         # a red check's words name this many failed tests, the rest counted (its record keeps them all)


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


def failed_test(out: str) -> str:
    """The first test pytest reports failed or errored (`-rfEs`: *FAILED tests/test_a.py::test_b - assert 1 == 2*), short: `tests/test_a.py::test_b`; "" when none is named."""
    for line in str(out or "").splitlines():
        head, _, rest = line.partition(" ")
        if head in ("FAILED", "ERROR") and rest.strip():
            return rest.split(" - ")[0].strip()[:WORDS_MAX]
    return ""


def _command(path: Path, line: str, cancel: threading.Event, timeout_s: int, details: dict | None = None) -> tuple[bool, str]:
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
        if details is not None:
            details["run"] = GateRun(False, box[0] if box else "", timed_out=True)
        return False, _long(timeout_s)
    reader.join(5)
    out = box[0] if box else ""
    if details is not None:
        details["run"] = GateRun(proc.returncode == 0, out, True, line, proc.returncode)
    if proc.returncode == 0:
        return True, ""
    return False, last_line(out) or f"It ended with exit code {proc.returncode}"


def _gate(git: IdeaGit, path: Path, old: str, cancel: threading.Event, timeout_s: int, details: dict | None = None) -> tuple[bool, str]:
    """(passed, words) of the gate's own run on what the picks touched, as a task's result runs it."""
    try:
        run = git.gate_run(path, old, cancel, timeout_s, whole=True)         # the browser folders whole: what a task's gate left runs here (spec 149 C.3)
    except RuntimeError:
        return False, _long(timeout_s)
    if details is not None:
        details["run"] = run
    if not run.ran:
        return True, last_line(run.out.split("\n! ")[0]) or "No tests to run"
    if run.ok:
        return True, ""
    if run.env:
        return False, run.env
    name, said = failed_test(run.out), last_line(run.out) or f"It ended with exit code {run.code}"
    return False, f"{name} failed ({said})"[:WORDS_MAX * 2] if name else said


def _alone(check: Check, gate: gate_config.Gate) -> bool:
    """The check is pytest and nothing else (the gate's own run, not a command the project wrote): only then is a red it names all that failed,
    so only then may a red from before or a flaky one be let through. A written command may run more after the tests, or not reach it (trial 152 E)."""
    return check.gate and not gate.custom


def _checked(git, path, base, check, cancel, timeout, alone: bool = False):
    """(passed, words, record) of one check: a red check's failed tests sorted (`flaky`, `pre-existing`, `new`, `unresolved`), and passed when every
    one is flaky or red before. `alone` (`_alone`) says the run was pytest alone; a red of any other command is never excused, its tests unresolved."""
    began = time.monotonic()
    details = {}
    ok, words = (_gate(git, path, base, cancel, timeout, details) if check.gate
                 else _command(path, check.run, cancel, timeout, details))
    run = details.get("run")
    record = {}
    if not ok and run is not None:
        ids = gate_rerun.ids_failing(run.out)
        try:
            found = gate_rerun.sort_out(git, path, base, "", run, cancel,
                                        timeout - (time.monotonic() - began), exact_main_base=True) if alone and ids else None
        except InterruptedError:
            raise
        except Exception:
            found = None
        record = {"failures": [{"id": i, "classification":
                   "flaky" if found and i in found.flaky else
                   "pre-existing" if found and i in found.red_before else
                   "new" if found and i in found.left else "unresolved"} for i in ids]} if ids else {}
        ok = bool(ids and found and not found.left and not found.unresolved
                  and gate_rerun._complete(run.out, ids))
        if ids:
            told = record["failures"][:SAID_MAX]
            more = len(ids) - len(told)
            words += "; " + "; ".join(f"{f['classification']}: {f['id']}" for f in told) + (f"; and {more} more" if more else "")
    return ok, words, record


def verify(repo: Path, tip: str, base: str, cancel: threading.Event | None = None, timeout_s: int | None = None) -> tuple[bool, str, str]:
    """The checks after *The merge* run on the commit `tip` (what a press that takes dev whole would make main; `base` is main's head now), in a worktree
    of its own that is gone whatever happens: (passed, the check that stopped it, its words). No ref moves."""
    cancel = cancel or threading.Event()
    git = IdeaGit(Path(repo))
    gate = gate_config.read(Path(repo))
    timeout = timeout_s or int((gate.main_timeout_min or gate_config.MAIN_TIMEOUT_MIN) * 60)
    path = worktrees.worktree_path(git.root, f"{goal_main.TRIAL}-{uuid.uuid4().hex[:8]}")
    try:
        with git.lock:
            path.parent.mkdir(parents=True, exist_ok=True)
            _ok(_git(git.root, "worktree", "add", "--detach", str(path), tip))
        for check in gate_config.main_checks(Path(repo))[1:]:
            ok, words, _ = _checked(git, path, base, check, cancel, timeout, _alone(check, gate))
            if not ok:
                return False, check.name, words
        return True, "", ""
    finally:
        git.remove(path)


def run(repo: Path, state_dir: Path, slug: str, *, root: Path | None = None, into: str = "dev", main: str = "",
        on_step: Callable[[list[dict[str, str]]], Any] | None = None, cancel: threading.Event | None = None,
        timeout_s: int | None = None, on_binding: Callable | None = None) -> list[dict[str, str]]:
    """Runs the checks (module docstring) and returns the last steps. A stop (`cancel` set) raises InterruptedError, the worktree gone."""
    cancel = cancel or threading.Event()
    gate = gate_config.read(Path(repo))
    checks: list[Check] = gate_config.main_checks(Path(repo))
    timeout = timeout_s or int((gate.main_timeout_min or gate_config.MAIN_TIMEOUT_MIN) * 60)       # `[gate.main] timeout_min`, 30 by default (spec 149 C.3)
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
        if on_binding is not None:
            on_binding(t.plan["commits"], t.old)
        n = len(t.plan["commits"])
        say(0, "passed", f"{n} {'commit applies' if n == 1 else 'commits apply'} to {main or 'main'}")
        for at, check in enumerate(checks[1:], 1):
            say(at, "running")
            ok, words, record = _checked(git, t.path, t.old, check, cancel, timeout, _alone(check, gate))
            say(at, "passed" if ok else "failed", words)
            if record:
                steps[at].update(record)
                if on_step is not None:
                    on_step([dict(s) for s in steps])
            if not ok:
                break
    return steps
