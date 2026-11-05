"""A red from before is not the task's (docs/specs/149-what-a-goal-on-local-codex-found.md §E, decisions §253.5).

    sorted = sort_out(git, path, start_sha, into, run, cancel, budget_s)    # Sorted(flaky, red_before, left, seconds) | None
    keys = ids_failing(output)                                              # the tests a pytest output names as failed, by `node_key`

A red gate whose run has pytest's summary: the tests it names run again alone in the task's worktree (green now: *flaky*); those still red run on
the base the task started from, in a throwaway worktree (red there too: *red before this task*); what is left is the task's. No model, no session.
A run that does not finish, or says nothing a test can be told by, counts its tests as the task's. Nothing here moves a branch.
"""
from __future__ import annotations

import os
import subprocess
import threading
import time
from pathlib import Path
from typing import NamedTuple

from orkboard.realm import dep_links, jobs, worktrees
from orkboard.realm.idea_git import GateRun, IdeaGit, _git, _ok, has_summary, parse_tests

MAX_IDS = 20
MIN_BUDGET_S = 10                    # less of the gate's clock than this left: nothing is run again


class Sorted(NamedTuple):
    flaky: tuple[str, ...]           # red in the gate, green run again alone
    red_before: tuple[str, ...]      # still red alone, and red on the base the task started from
    left: tuple[str, ...]            # the task's: still red alone and green (or absent, or not run) on the base
    seconds: float = 0.0


def node_key(name: str) -> str:
    """A test's id as it is compared: pytest prints `FAILED path::test[a b - why` cut at a space, so an id with an unclosed `[` is its test alone."""
    return name if name.count("[") == name.count("]") else name.split("[", 1)[0]


def ids_failing(output: str) -> list[str]:
    return list(dict.fromkeys(node_key(n) for n in parse_tests(output)["failing"]))


def run_ids(python: str, cwd: Path, ids: list[str], cancel: threading.Event, timeout_s: float) -> set[str] | None:
    """The ids that are red when `ids` run in `cwd`: an empty set when all are green, None when the run said nothing a test can be told by or
    did not finish in `timeout_s` (the caller counts those tests as the task's). A stop raises InterruptedError."""
    argv = [python, "-m", "pytest", "-q", "-rfE", "-p", "no:cacheprovider", *ids]
    try:
        proc = subprocess.Popen(argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, start_new_session=True,
                                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    except OSError:
        return None
    box: list[str] = []
    reader = threading.Thread(target=lambda: box.append(proc.stdout.read() if proc.stdout else ""), daemon=True)
    reader.start()
    try:
        jobs._wait(proc, cancel, max(1, int(timeout_s)), "ideas/gate")
    except RuntimeError:
        return None
    reader.join(5)
    out = box[0] if box else ""
    if proc.returncode == 0:
        return set()
    names = ids_failing(out)
    return set(names) if names and has_summary(out) else None


def sort_out(git: IdeaGit, path: Path, start_sha: str, into: str, run: GateRun, cancel: threading.Event, budget_s: float) -> Sorted | None:
    """The red tests of `run` sorted into flaky, red before and the task's; None when there is nothing to sort (no summary, more failures than
    names, no clock left, no Python to run them with)."""
    began = time.monotonic()
    summary = parse_tests(run.out)
    ids = ids_failing(run.out)
    if run.ok or not ids or not has_summary(run.out) or summary["failed"] > len(summary["failing"]) or budget_s < MIN_BUDGET_S:
        return None
    left_s = lambda: budget_s - (time.monotonic() - began)                  # noqa: E731
    python = git.python()
    again = run_ids(python, path, ids, cancel, left_s())
    still = [i for i in ids if again is None or i in again]
    flaky = [i for i in ids if i not in still]
    red_before: list[str] = []
    if still and left_s() >= MIN_BUDGET_S:
        fork = _git(path, "merge-base", start_sha, into).stdout.strip() or start_sha
        base_tree = _base_tree(git, fork)
        try:
            if base_tree is not None:
                there = [i for i in still if (base_tree / i.split("::", 1)[0]).is_file()]      # a test file the task made was not there to be red
                red = run_ids(python, base_tree, there, cancel, left_s()) if there else set()
                red_before = [i for i in still if i in (red or set())]
        finally:
            if base_tree is not None:
                git.remove(base_tree)
    left = [i for i in still if i not in red_before]
    return Sorted(tuple(flaky), tuple(red_before), tuple(left), round(time.monotonic() - began, 1))


def _base_tree(git: IdeaGit, sha: str) -> Path | None:
    """A throwaway worktree at `sha` (detached, the main checkout's dependencies linked in); None when git cannot make one. The caller removes it."""
    with git.lock:
        path = worktrees.worktree_path(git.root, f"red-before-{sha[:10]}")
        git.remove(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            _ok(_git(git.root, "worktree", "add", "--detach", str(path), sha))
        except RuntimeError:
            return None
        dep_links.link(git.root, path)
    return path


def words(found: Sorted) -> list[str]:
    """The lines the task's log gets (`== red before this task: …`, `== flaky: …`)."""
    lines = []
    if found.red_before:
        lines.append(f"== red before this task: {', '.join(found.red_before)}")
    if found.flaky:
        lines.append(f"== flaky: {', '.join(found.flaky)}")
    return lines


def told(found: Sorted, output: str) -> str:
    """What a session is told of a red gate that has something left: only the task's tests, and how to see them; the others are not its to mend."""
    names = "\n".join(f"- {n}" for n in found.left)
    return (f"The tests failed. These are yours to mend:\n{names}\nRun them with `python -m pytest -q {' '.join(found.left)}`."
            + (f"\n({len(found.red_before)} more were red before your task and are left alone.)" if found.red_before else "")
            + (f"\n\n{output[-3000:]}" if not found.red_before else ""))
