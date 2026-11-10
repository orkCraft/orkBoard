"""A goal's own branch (docs/specs/168-the-window-played-as-a-card-games-table.md F1, decisions §283.26): git plans, no face.

    goal_branch.begin(git, state_dir, slug, plan, dev, step)    # the branch a task about to start lands on: `goal/<slug>`, made from dev when the goal's
                                                                #   first step starts; "" (dev) for a goal that is in dev already or began there
    goal_branch.step_started(git, state_dir, slug, n, dev)      # dev is merged into the branch as each step starts (once a step)
    goal_branch.sync(git, branch, dev)                          # dev merged into the branch, in a worktree of its own; a conflict is not forced
    goal_branch.ready(state_dir, slug)                          # the last step was accepted: the goal waits to go into dev
    goal_branch.to_dev(git, state_dir, slug, dev, cancel, ...)  # into dev once: dev merged in, the gate run on that, then dev moved to it
    goal_branch.drop(git, state_dir, slug)                      # a goal dropped before dev: the branch is deleted, dev is untouched
    goal_branch.row(state_dir, slug, review)                    # `{goal_branch, waits_for_dev, dev_why}` for the Board's row (empty for a goal with none)

**The branch is `goal/<slug>`, never `idea/<slug>`**: git cannot hold a ref `idea/x` and `idea/x/k1` (a task's), so the goal's is under `goal/`.
**Old goals and new ones are told apart by a file**: `<state>/ideas/<slug>/goal_branch.json` (`branch`, `from`, `at`, `synced`, `ready`, `blocked`, `blocked_kind`, `untested_ok`, `merged`).
It is laid when a goal's first task starts and nothing of it has landed in dev (no task `merged` with a commit); a goal with such a task and no file is
an old goal at work in dev, and its tasks land in dev as before. Once `merged` is set (the branch is gone) the goal lands in dev as before, so a goal
sent back to work after dev goes on there. Nothing here pushes a goal's branch; dev is pushed when the project pushes after merging.

The merge into dev is a fast-forward to the branch's tip after dev was merged into the branch, so what the gate tested (the branch's tip, dev's head
as its base) is exactly what dev becomes. No ref moves before the gate is green.
"""
from __future__ import annotations

import json
import os
import threading
import uuid
from pathlib import Path
from typing import Any, Callable

from orkboard import brand
from orkboard.realm import dep_links, gate_config, lexicon, worktrees
from orkboard.realm.idea_git import GateRun, IdeaGit, _git, _ok

PREFIX = "goal/"
FILE = "goal_branch.json"
TRIES = 3                                   # dev moved while the tests ran: the merge and the tests are made again, this many times
WHY_MAX = 600


def words(key: str, **fill: str) -> str:
    """A term of the glossary (realm/lexicon_table.py) with its `<name>` places filled: how a goal's reasons are worded, once."""
    text = lexicon.term(key)
    for k, v in fill.items():
        text = text.replace(f"<{k}>", str(v))
    return text


class GoalConflict(RuntimeError):
    """Dev does not merge into the goal's branch cleanly (or the goal's branch into dev): nothing was forced."""

    def __init__(self, message: str, files: list[str] | None = None) -> None:
        super().__init__(message)
        self.files = files or []


class GoalRed(RuntimeError):
    """The gate is red on dev with the goal merged: dev is as it was."""


def name(slug: str) -> str:
    return PREFIX + slug


def _path(state_dir: Path, slug: str) -> Path:
    return Path(state_dir) / "ideas" / slug / FILE


def read(state_dir: Path, slug: str) -> dict:
    """The goal's branch file; {} for a goal with none (an old goal, or one that has not begun)."""
    try:
        got = json.loads(_path(state_dir, slug).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return got if isinstance(got, dict) else {}


def _write(state_dir: Path, slug: str, data: dict) -> None:
    path = _path(state_dir, slug)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def update(state_dir: Path, slug: str, **fields: Any) -> dict:
    got = {**read(state_dir, slug), **fields}
    _write(state_dir, slug, got)
    return got


def in_use(state_dir: Path, slug: str) -> str:
    """The goal's branch while its work is on it (not yet in dev, not dropped); "" for an old goal, one in dev, or one that has not begun."""
    got = read(state_dir, slug)
    branch = got.get("branch")
    return branch if isinstance(branch, str) and branch and not got.get("merged") and not got.get("dropped") else ""


def waits_for_dev(state_dir: Path, slug: str) -> bool:
    """The goal's last step was accepted and it is on its branch, not in dev."""
    return bool(in_use(state_dir, slug) and read(state_dir, slug).get("ready"))


def _landed_in_dev(plan: dict | None) -> bool:
    """A task of the plan landed (merged, with a commit) with no branch to land on: the goal is at work in dev."""
    return any(isinstance(t, dict) and t.get("state") == "merged" and t.get("commit") for t in (plan or {}).get("tasks") or [])


def begin(git: IdeaGit, state_dir: Path, slug: str, plan: dict | None, dev: str, step: int = 1) -> str:
    """The branch a task of the goal about to start lands on and is cut from: `goal/<slug>`, made from dev now when this is the goal's first start and nothing
    of it is in dev; "" when it lands in dev (an old goal, or one already in dev). Raises RuntimeError when the goal's branch was deleted from under its work."""
    with git.lock:
        got = read(state_dir, slug)
        if got.get("dropped"):
            got = {}
        if got.get("branch"):
            if got.get("merged"):
                return ""
            if not worktrees.branch_exists(git.root, got["branch"]):
                raise RuntimeError(f"The goal's branch {got['branch']} is gone: its work cannot go on")
            return str(got["branch"])
        if _landed_in_dev(plan):
            return ""
        branch = name(slug)
        if not worktrees.valid_branch(git.root, branch):
            raise RuntimeError(f"{branch!r} is not a valid branch name")
        if worktrees.branch_exists(git.root, branch):                    # a leftover of a goal dropped with the same name
            _ok(_git(git.root, "branch", "-D", branch))
        _ok(_git(git.root, "rev-parse", "--verify", f"refs/heads/{dev}"))
        _ok(_git(git.root, "branch", branch, dev))
        _write(state_dir, slug, {"branch": branch, "from": _ok(_git(git.root, "rev-parse", dev)), "at": _now(),
                                 "synced": [int(step)], "ready": False, "blocked": "", "merged": ""})
        return branch


def _now() -> str:
    import datetime as dt
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def sync(git: IdeaGit, branch: str, dev: str) -> bool:
    """Dev merged into `branch` (True when the branch moved). It happens in a worktree of its own at the branch's head, so no checkout is touched; a conflict
    aborts the merge, leaves the branch as it was and raises GoalConflict with the files."""
    with git.lock:
        if _git(git.root, "merge-base", "--is-ancestor", dev, branch).returncode == 0:
            return False
        old = _ok(_git(git.root, "rev-parse", f"refs/heads/{branch}"))
        path = worktrees.worktree_path(git.root, f"goal-sync-{uuid.uuid4().hex[:8]}")
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            _ok(_git(git.root, "worktree", "add", "--detach", str(path), old))
            done = _git(path, *brand.git_identity(), "merge", "--no-edit", dev)
            if done.returncode != 0:
                files = _git(path, "diff", "--name-only", "--diff-filter=U").stdout.split()
                _git(path, "merge", "--abort")
                if not files:
                    raise RuntimeError((done.stderr or done.stdout).strip()[:300] or "the merge failed")
                raise GoalConflict(words("dev_conflict", dev=dev, branch=branch, files=", ".join(files)), files)
            new = _ok(_git(path, "rev-parse", "HEAD"))
            _ok(_git(git.root, "update-ref", f"refs/heads/{branch}", new, old))
            return new != old
        finally:
            git.remove(path)


def step_started(git: IdeaGit, state_dir: Path, slug: str, n: int, dev: str) -> None:
    """Step `n` of the goal starts: dev is merged into its branch, once a step. A conflict stops the start, says why in the goal's file and is raised."""
    branch = in_use(state_dir, slug)
    if not branch:
        return
    with git.lock:
        got = read(state_dir, slug)
        if n in (got.get("synced") or []):
            return
        try:
            sync(git, branch, dev)
        except GoalConflict as e:
            update(state_dir, slug, blocked=str(e)[:WHY_MAX], blocked_kind="conflict")
            raise
        update(state_dir, slug, synced=sorted({*(got.get("synced") or []), int(n)}), blocked="", blocked_kind="")


def ready(state_dir: Path, slug: str, yes: bool = True) -> None:
    """The last step was accepted (`yes`), or the goal is at work again."""
    if in_use(state_dir, slug):
        update(state_dir, slug, ready=bool(yes), **({} if yes else {"blocked": "", "blocked_kind": ""}))


def accepted_untested(state_dir: Path, root: Path, slug: str) -> bool:
    """The person merged a result no test ran on (a project with no test at all, or none that covers what the result touched): that was the one yes a goal is asked for, so a gate that runs no
    test on dev with the goal does not stop it a second time (a red one still does). True when it was kept."""
    if not in_use(state_dir, slug):
        return False
    update(state_dir, slug, untested_ok=True)
    return True


def _trial(git: IdeaGit, tip: str) -> Path:
    path = worktrees.worktree_path(git.root, f"goal-dev-{uuid.uuid4().hex[:8]}")
    path.parent.mkdir(parents=True, exist_ok=True)
    _ok(_git(git.root, "worktree", "add", "--detach", str(path), tip))
    dep_links.link(git.root, path)
    return path


def _red(run: GateRun, dev: str = "dev") -> str:
    if run.env:
        return words("dev_could_not_run", why=run.env)
    if run.ok and not run.ran:
        return words("dev_no_test_ran", dev=dev)
    tail = [ln for ln in run.out.strip().splitlines() if ln.strip()][-3:]
    return words("dev_red", dev=dev, tail=" | ".join(tail))[:WHY_MAX]


def to_dev(git: IdeaGit, state_dir: Path, slug: str, dev: str, cancel: threading.Event | None = None, push: bool = False,
           untested: bool = False, say: Callable[[str], Any] | None = None) -> dict:
    """The goal into dev, once: dev is merged into its branch, the gate (`[gate]`: `always`, then the tests of what the goal touched) is run on that tip with dev's head as
    its base, and only a green gate moves dev, by fast-forward, to the tip; the branch is deleted then. `{commit, subjects, note}`. A conflict is GoalConflict, a red gate
    GoalRed, a project with no tests GoalRed too unless `untested`; each is kept in the goal's file (`blocked`) and dev is as it was. Dev moving while the tests ran makes the
    merge and the tests again, `TRIES` times. Nothing is pushed but dev, and only when `push`."""
    cancel = cancel or threading.Event()
    say = say or (lambda _s: None)
    got = read(state_dir, slug)
    branch = got.get("branch") or ""
    if not branch or got.get("merged") or got.get("dropped"):
        raise RuntimeError("That goal has no branch waiting for dev")
    if not untested and gate_config.read(git.root).none:
        if not got.get("untested_ok"):                              # a project with no test: asked once a goal, at its result's Merge or here (`accepted_untested`)
            why = words("dev_no_tests", dev=dev)
            update(state_dir, slug, blocked=why, blocked_kind="no_tests")
            raise GoalRed(why)
        untested = True
    last = "dev moved while the tests ran"
    for _ in range(TRIES):
        try:
            with git.lock:
                if not worktrees.branch_exists(git.root, branch):
                    raise RuntimeError(f"The goal's branch {branch} is gone")
                sync(git, branch, dev)
                tip = _ok(_git(git.root, "rev-parse", f"refs/heads/{branch}"))
                old = _ok(_git(git.root, "rev-parse", f"refs/heads/{dev}"))
        except GoalConflict as e:
            update(state_dir, slug, blocked=str(e)[:WHY_MAX], blocked_kind="conflict")
            raise
        if tip == old:                                           # dev holds everything the goal has: nothing to move
            return _done(git, state_dir, slug, branch, tip, [], "")
        if not untested:
            say("the tests run on dev with the goal")
            path = _trial(git, tip)
            try:
                run = git.gate_run(path, old, cancel)
            finally:
                git.remove(path)
            if not run.ok or run.env or not (run.ran or run.docs or got.get("untested_ok")):         # a gate that ran no test is no green (a goal of documents only has none to run), unless the person merged a result no test ran on
                why = _red(run, dev)
                update(state_dir, slug, blocked=why, blocked_kind="env" if run.env else "red" if not run.ok else "no_tests")
                raise GoalRed(why)
        with git.lock:
            if _ok(_git(git.root, "rev-parse", f"refs/heads/{dev}")) != old \
                    or _ok(_git(git.root, "rev-parse", f"refs/heads/{branch}")) != tip:
                continue
            subjects = [s for s in _git(git.root, "log", "--reverse", "--format=%s", f"{old}..{tip}").stdout.splitlines() if s.strip()]
            try:
                git._fast_forward(dev, old, tip)
            except RuntimeError as e:
                update(state_dir, slug, blocked=" ".join(str(e).split())[:WHY_MAX], blocked_kind="other")
                raise
            note = git.push(dev) if push else ""
            return _done(git, state_dir, slug, branch, tip, subjects, note)
    update(state_dir, slug, blocked=last, blocked_kind="other")
    raise RuntimeError(last)


def _done(git: IdeaGit, state_dir: Path, slug: str, branch: str, tip: str, subjects: list[str], note: str) -> dict:
    with git.lock:
        update(state_dir, slug, merged=tip, blocked="", blocked_kind="", ready=False)
        _git(git.root, "branch", "-D", branch)                  # merged: the ref is no more use (it can fail where the branch is checked out; it is left then)
    return {"commit": tip, "subjects": subjects, "note": note}


def drop(git: IdeaGit, state_dir: Path, slug: str) -> bool:
    """A goal dropped before dev: its branch is deleted and its file marked; dev and every task branch are untouched, nothing is reverted. True when a branch went.
    A goal in dev (or one without a branch) is left as `ideas.drop` has always left it."""
    branch = in_use(state_dir, slug)
    if not branch:
        return False
    with git.lock:
        gone = not worktrees.branch_exists(git.root, branch) or _git(git.root, "branch", "-D", branch).returncode == 0
        update(state_dir, slug, dropped=True, ready=False)
    return gone


def row(state_dir: Path, slug: str, review: bool = False) -> dict:
    """What the Board's row of the goal says of its branch: `{goal_branch, waits_for_dev, dev_why, dev_blocked, dev_kind}`; {} for a goal with no branch on it (an old goal, or one in dev).
    `dev_blocked`: it is done on its branch and something stopped it before dev (`dev_kind`: "conflict", "red", "no_tests" (no test ran), "env" (the tests could not run) or "other"): the hand holds a card for it
    whatever *Lands in dev by itself* says (spec 168 F2, decisions §283.27).
    `waits_for_dev`: the last step was accepted and the goal is on its branch (drawn in the discard's lower pile, F2); `dev_why` says why it waits: a conflict or a red
    gate (kept), else that *Lands in dev by itself* is off (`review`), else ""."""
    branch = in_use(state_dir, slug)
    if not branch:
        return {}
    got = read(state_dir, slug)
    waits = bool(got.get("ready"))
    why = str(got.get("blocked") or "") if waits or got.get("blocked") else ""
    if waits and not why and review:
        why = words("dev_why_off")
    kind = str(got.get("blocked_kind") or "other") if got.get("blocked") else ""
    return {"goal_branch": branch, "waits_for_dev": waits, "dev_why": why, "dev_blocked": waits and bool(got.get("blocked")), "dev_kind": kind}
