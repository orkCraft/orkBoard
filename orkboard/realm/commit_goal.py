"""Which goal made a commit of dev (docs/specs/88-assets-and-play.md §3; spec 89 §3 reads it too): a task that landed keeps the new
head of its branch as `commit` and the subjects it brought as `subjects` (core/idea_runner.py), so the commits a task brought are its
`commit` and the newest of its ancestors no earlier task had, as many as its subjects. A commit no task brought is the person's own.

    commit_goal.of(state_dir, root, sha)              # {"goal": "dark-mode", "task": "k2"} · {} for the person's own (or one not in dev)
    commit_goal.index(state_dir, root, "dev")         # {sha: {"goal", "task"}}: every commit of dev a task brought (cached by dev's head)
    commit_goal.resolve(root, "2026-10-26T09:00", "dev")   # the commit `since` names: a sha, or dev's last commit at or before a time
    commit_goal.last_touch(root, "dev", since)        # {path: {"sha", "at"}}: the last commit of since..dev (or of dev) that touched each file

Read from git and the goals' plan.json, no model, no face. Every git call has fixed arguments (no shell), `--` before a path.
"""
from __future__ import annotations

import re
import subprocess
from collections import deque
from pathlib import Path

from orkboard.realm import ideas

GIT_TIMEOUT_S = 60
HISTORY_MAX = 20_000                 # the newest commits of dev read for the index
LOG_MAX = 5_000                      # … and for the last touch of each file
SHA = re.compile(r"[0-9a-f]{7,64}")
FULL_SHA = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")
TIME = re.compile(r"\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?)?")
REF = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,99}")
_CACHE: dict[tuple, dict[str, dict]] = {}
_CACHE_MAX = 8


def git(root: Path, *args: str, timeout: int = GIT_TIMEOUT_S) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-c", "core.quotePath=false", *args], cwd=root, capture_output=True, text=True,
                          errors="replace", timeout=timeout)


def head(root: Path, ref: str = "dev") -> str:
    """The commit `ref` (a branch) stands at; "" when there is none."""
    if not REF.fullmatch(ref or "") or ".." in ref:
        return ""
    try:
        got = git(root, "rev-parse", "--verify", "--quiet", f"refs/heads/{ref}^{{commit}}")
    except (OSError, subprocess.SubprocessError):
        return ""
    out = got.stdout.strip()
    return out if got.returncode == 0 and FULL_SHA.fullmatch(out) else ""


def resolve(root: Path, since: object, ref: str = "dev") -> str:
    """The full commit `since` names, "" for none: a sha of a commit (short or full) that is `ref`'s or one of its ancestors, or a time
    (ISO), read as `ref`'s last commit at or before it. Anything else is none (nothing is marked)."""
    if not isinstance(since, str) or not (tip := head(root, ref)):
        return ""
    text = since.strip()
    try:
        if SHA.fullmatch(text):
            got = git(root, "rev-parse", "--verify", "--quiet", f"{text}^{{commit}}")
            sha = got.stdout.strip()
            if got.returncode != 0 or not FULL_SHA.fullmatch(sha):
                return ""
            return sha if git(root, "merge-base", "--is-ancestor", sha, tip).returncode == 0 else ""
        if TIME.fullmatch(text):
            got = git(root, "rev-list", "-1", f"--before={text}", tip)
            sha = got.stdout.strip()
            return sha if got.returncode == 0 and FULL_SHA.fullmatch(sha) else ""
    except (OSError, subprocess.SubprocessError):
        return ""
    return ""


def landed(state_dir: Path) -> dict[str, dict]:
    """`{commit: {"goal", "task", "n"}}` of every task that landed with commits (`state` merged, a `commit`, `n` its subjects)."""
    out: dict[str, dict] = {}
    folder = Path(state_dir) / "ideas"
    if not folder.is_dir():
        return out
    for d in sorted(folder.iterdir()):
        if not d.is_dir() or not re.fullmatch(r"[a-z0-9-]+", d.name):
            continue
        for t in (ideas.plan(state_dir, d.name) or {}).get("tasks") or []:
            if not isinstance(t, dict) or t.get("state") != "merged":
                continue
            sha, subjects = str(t.get("commit") or ""), t.get("subjects")
            n = len(subjects) if isinstance(subjects, list) else 0
            if FULL_SHA.fullmatch(sha) and n and sha not in out:
                out[sha] = {"goal": d.name, "task": str(t.get("id") or ""), "n": n}
    return out


def _history(root: Path, tip: str) -> list[tuple[str, list[str]]]:
    """(sha, parents) of the newest HISTORY_MAX commits of `tip`, parents before children."""
    got = git(root, "log", "--topo-order", "--reverse", f"-n{HISTORY_MAX}", "--format=%H %P", tip)
    if got.returncode != 0:
        return []
    rows = []
    for line in got.stdout.splitlines():
        parts = line.split()
        if parts and FULL_SHA.fullmatch(parts[0]):
            rows.append((parts[0], parts[1:]))
    return rows


def index(state_dir: Path, root: Path, ref: str = "dev") -> dict[str, dict]:
    """`{sha: {"goal", "task"}}` of every commit of `ref` a task brought. The tasks are taken in the order they landed; a task's own are
    its `commit` and the commits behind it no earlier task reached, nearest first (its first parents first), as many as its subjects:
    a commit of the person's made between two landings is reached and left to no one."""
    tip = head(root, ref)
    if not tip:
        return {}
    tasks = landed(state_dir)
    key = (str(Path(root).resolve()), tip, tuple(sorted((c, t["goal"], t["task"], t["n"]) for c, t in tasks.items())))
    if key in _CACHE:
        return _CACHE[key]
    out: dict[str, dict] = {}
    if tasks:
        try:
            rows = _history(root, tip)
        except (OSError, subprocess.SubprocessError):
            rows = []
        parents = dict(rows)
        covered: set[str] = set()
        for sha, _p in rows:                                   # parents first: the order the tasks landed in
            task = tasks.get(sha)
            if task is None or sha in covered:
                continue
            seen, order, todo = {sha}, [], deque([sha])
            while todo:
                c = todo.popleft()
                order.append(c)
                for p in parents.get(c, []):
                    if p in parents and p not in covered and p not in seen:
                        seen.add(p)
                        todo.append(p)
            covered |= seen
            for c in order[:task["n"]]:
                out.setdefault(c, {"goal": task["goal"], "task": task["task"]})
    if len(_CACHE) >= _CACHE_MAX:
        _CACHE.pop(next(iter(_CACHE)))
    _CACHE[key] = out
    return out


def of(state_dir: Path, root: Path, sha: str, ref: str = "dev") -> dict:
    """`{"goal", "task"}` of the task that brought the commit `sha` (short or full) into `ref`; `{}` for a commit no task landed."""
    if not isinstance(sha, str) or not SHA.fullmatch(sha.strip()):
        return {}
    sha = sha.strip()
    if not FULL_SHA.fullmatch(sha):
        try:
            got = git(root, "rev-parse", "--verify", "--quiet", f"{sha}^{{commit}}")
        except (OSError, subprocess.SubprocessError):
            return {}
        sha = got.stdout.strip() if got.returncode == 0 else ""
    return dict(index(state_dir, root, ref).get(sha) or {})


def last_touch(root: Path, ref: str = "dev", since: str = "", limit: int = LOG_MAX) -> dict[str, dict]:
    """`{path: {"sha", "at"}}`: for each file a commit of `since..ref` (of `ref`'s newest `limit` commits without `since`) touched, the
    newest such commit and its time (ISO). A rename is a removal and an addition. A path git would quote is left out."""
    tip = head(root, ref)
    if not tip or (since and not FULL_SHA.fullmatch(since)):
        return {}
    try:
        got = git(root, "log", "--no-renames", f"-n{max(1, int(limit))}", "--format=%x01%H %cI", "--name-only",
                  f"{since}..{tip}" if since else tip, "--")
    except (OSError, subprocess.SubprocessError):
        return {}
    out: dict[str, dict] = {}
    sha = at = ""
    for line in got.stdout.splitlines() if got.returncode == 0 else []:
        if line.startswith("\x01"):
            sha, _, at = line[1:].partition(" ")
        elif line and sha and not line.startswith('"'):
            out.setdefault(line, {"sha": sha, "at": at})
    return out
