"""A goal to main on its own (docs/specs/105-the-default-tool-moving-on-and-the-portal.md §5, decisions §177.6). A goal has no branch: each
of its tasks landed on dev rebased, one after the other, with the person's own commits and the Board's pages between. So a goal goes to
main by its commits, cherry-picked in the order they landed, with the goals it stands on that main lacks.

    got = goal_main.plan(repo, state_dir, "lobby", root=root, into="dev", main="main")
        # {"goals": ["lobby", "reconnect"], "commits": [sha…], "sealed": None | "Reconnect is not done yet", "titles": {slug: short title}, "files": 3}
    got = goal_main.merge(repo, state_dir, "lobby", push=False, root=root, into="dev", main="main")
        # {"commit", "goals", "commits", "files", "note", "pushed"}: main moved to the picks, pushed when asked
    goal_main.in_main(git, shas, "dev", "main")    # every sha is in main, by ancestry or by patch id (a goal's flag after the pick)

`goals`: the goal first, then what it stands on. Those are its `depends_on` (deeply) and any goal with a commit before one of its own that
touched a file the same; a goal main has already (flag raised, or all its commits in main) is left out. **Already in main is decided by patch
id (`git cherry`), never by sha**: a pick is a new commit. `sealed` says why it cannot go, in plain words, with the goal's short title as the
page names it: a task of it not landed (*Lobby is not done yet*), a goal it stands on not done (*Reconnect is not done yet*), a pick that
would conflict, tried in a worktree of its own that is gone again (*Lobby does not apply to main cleanly: player.ts*), main behind its origin.
No face, no model. `merge` runs under the repository's lock; whatever is refused, main is as it was and no worktree is left behind.
Nothing here moves dev.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from orkboard.realm import commit_goal, goal_types, idea_flag, idea_gate, ideas, worktrees
from orkboard.realm.idea_git import PUSH_TIMEOUT_S, IdeaGit, _git, _ok

WORKTREE = "gate-main"                       # where the picks are made, under `.orkcraft/worktrees/`
TRIAL = "gate-main-try"                      # … and where a plan tries them first


class GoalRefused(RuntimeError):
    """The goal does not go to main, in plain words; main is as it was."""


def _depends(root: Path | None, slug: str) -> list[str]:
    page = ideas.idea_page(root, slug) if root is not None else None
    try:
        got = json.loads(str(page.get("depends_on") or "[]")) if page else []
    except ValueError:
        return []
    return [str(x) for x in got if isinstance(x, str)] if isinstance(got, list) else []


def _done(state_dir: Path, slug: str) -> bool:
    """The goal has a plan and every task of it that was not dropped has landed."""
    tasks = [t for t in (ideas.plan(state_dir, slug) or {}).get("tasks") or [] if isinstance(t, dict) and not goal_types.is_dropped(t)]
    return bool(tasks) and all(t.get("state") == "merged" for t in tasks)


def _files(git: IdeaGit, shas: list[str]) -> dict[str, set[str]]:
    """The files each commit changes (a rename is a removal and an addition)."""
    out: dict[str, set[str]] = {s: set() for s in shas}
    for at in range(0, len(shas), 200):
        text = _git(git.root, "-c", "core.quotePath=false", "log", "--no-walk=unsorted", "--no-renames", "--name-only",
                    "--format=%x01%H", *shas[at:at + 200], "--").stdout
        sha = ""
        for line in text.splitlines():
            if line.startswith("\x01"):
                sha = line[1:].strip()
            elif line and sha in out:
                out[sha].add(line)
    return out


def _behind_origin(git: IdeaGit, main: str) -> bool:
    """Main lacks commits of its origin's main the person fetched (main moved outside Orkboard)."""
    remote = f"refs/remotes/origin/{main}"
    if _git(git.root, "show-ref", "--verify", "--quiet", remote).returncode != 0:
        return False
    return _git(git.root, "merge-base", "--is-ancestor", remote, f"refs/heads/{main}").returncode != 0


def _compose(git: IdeaGit, state_dir: Path, slug: str, root: Path | None, into: str, main: str) -> dict[str, Any]:
    """The plan before any pick is tried: the goals, their commits in the order dev holds them, and a seal for what is known without git
    trying the picks. `owner` (not in the answer) is each commit's goal."""
    titles = {i["slug"]: i["short"] or i["title"] for i in ideas.ideas(root)} if root is not None else {}

    def name(s: str) -> str:
        return titles.get(s) or s

    out: dict[str, Any] = {"goals": [slug], "commits": [], "sealed": None, "titles": {slug: name(slug)}, "files": 0, "owner": {}}
    if idea_gate.same(into, main):
        out["sealed"] = idea_gate.refusal_same(into, main)
        return out
    if not all(worktrees.branch_exists(git.root, b) for b in (into, main)):
        out["sealed"] = f"{into if worktrees.branch_exists(git.root, main) else main} is not a branch here"
        return out
    pending, _equal = idea_gate.cherry(git, into, main)
    order = {s: n for n, s in enumerate(pending)}
    owner = {s: g["goal"] for s, g in commit_goal.index(state_dir, git.root, into).items() if s in order}
    by_goal: dict[str, list[str]] = {}
    for s in pending:
        if s in owner:
            by_goal.setdefault(owner[s], []).append(s)
    files = _files(git, pending)
    first_touch: dict[str, dict[str, int]] = {}               # goal → file → the earliest of its pending commits that touched it
    for g, shas in by_goal.items():
        touch = first_touch.setdefault(g, {})
        for s in shas:
            for f in files[s]:
                touch.setdefault(f, order[s])

    def lacks(g: str) -> bool:
        lost = ideas.idea_page(root, g) is None if root is not None else not ideas.plan(state_dir, g)
        if lost:
            return False                                      # a goal the Board lost is nothing to stand on
        return idea_flag.flag_of(state_dir, g) is None and (not _done(state_dir, g) or bool(by_goal.get(g)))

    chosen, todo = [slug], [slug]
    while todo:
        x = todo.pop(0)
        for d in _depends(root, x):
            if d not in chosen and d != slug and lacks(d):
                chosen.append(d)
                todo.append(d)
        for h, touch in first_touch.items():
            if h not in chosen and any(touch.get(f, len(order)) < order[c] for c in by_goal.get(x, []) for f in files[c]):
                chosen.append(h)                              # an earlier commit of its on a file this one changed
                todo.append(h)
    for g in chosen:
        out["titles"][g] = name(g)
    out["goals"] = chosen
    commits = sorted((s for g in chosen for s in by_goal.get(g, [])), key=order.__getitem__)
    out["commits"], out["owner"] = commits, {s: owner[s] for s in commits}
    out["files"] = len({f for s in commits for f in files[s]})
    for g in chosen:
        if not _done(state_dir, g):
            out["sealed"] = f"{name(g)} is not done yet"
            return out
    if not commits:
        landed = any(g["goal"] == slug for g in commit_goal.landed(state_dir).values())
        out["sealed"] = f"{name(slug)} is in main already" if landed else f"{name(slug)} has nothing to send to main"
    elif _behind_origin(git, main):
        out["sealed"] = f"{main} is behind origin/{main}: pull it first"
    return out


def _pick(git: IdeaGit, where: str, old: str, commits: list[str]) -> tuple[str, tuple[str, list[str]] | None]:
    """The commits cherry-picked in order onto `old` in a worktree of its own, detached there: (the new head, None), or (`old`, (the
    commit that did not apply, the files in conflict)). The worktree is gone either way."""
    path = worktrees.worktree_path(git.root, where)
    git.remove(path)                                           # a leftover of an earlier try
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        _ok(_git(git.root, "worktree", "add", "--detach", str(path), old))
        for sha in commits:
            done = _git(path, *idea_gate.IDENTITY, "cherry-pick", sha, timeout=PUSH_TIMEOUT_S)
            if done.returncode == 0:
                continue
            files = _git(path, "diff", "--name-only", "--diff-filter=U").stdout.split()
            if not files and _git(path, "diff", "--cached", "--quiet").returncode == 0 and \
                    _git(path, *idea_gate.IDENTITY, "cherry-pick", "--skip").returncode == 0:
                continue                                       # it came out empty: main has what it brings
            _git(path, "cherry-pick", "--abort")
            return old, (sha, files)
        return git.head(path), None
    finally:
        git.remove(path)


def _conflict(plan: dict[str, Any], slug: str, hit: tuple[str, list[str]]) -> str:
    sha, files = hit
    goal = plan["owner"].get(sha) or slug
    return f"{plan['titles'].get(goal) or goal} does not apply to main cleanly" + (f": {', '.join(files)}" if files else "")


def plan(repo: Path, state_dir: Path, slug: str, *, root: Path | None = None, into: str = "dev", main: str = "") -> dict[str, Any]:
    """`{goals, commits, sealed, titles, files}` (the module's docstring). `root`: where the Board's pages are (the goals' titles and
    `depends_on`; without it a goal is named by its slug and stands on nothing). `main`: the repository's default branch when empty."""
    git = IdeaGit(Path(repo))
    with git.lock:
        main = main or git.default_branch()
        got = _compose(git, Path(state_dir), slug, root, into, main)
        if got["sealed"] is None and got["commits"]:
            try:
                old = _ok(_git(git.root, "rev-parse", f"refs/heads/{main}"))
                _tip, hit = _pick(git, TRIAL, old, got["commits"])
            except RuntimeError as e:                          # git could not make the worktree
                got["sealed"] = " ".join(str(e).split())[:300] or "Git could not try the picks"
            else:
                if hit:
                    got["sealed"] = _conflict(got, slug, hit)
    got.pop("owner")
    return got


def merge(repo: Path, state_dir: Path, slug: str, push: bool = False, *, root: Path | None = None, into: str = "dev",
          main: str = "") -> dict[str, Any]:
    """The plan's commits cherry-picked in order onto main in the `gate-main` worktree, main fast-forwarded to the result (a root checkout
    on main moves with it, and is refused with its files when they are changed), then pushed when asked: `{commit, goals, commits, files,
    note, pushed}`. Raises GoalRefused in plain words when the plan is sealed or a pick does not apply; RuntimeError when git cannot
    move main. Either way main is as it was."""
    git = IdeaGit(Path(repo))
    with git.lock:
        main = main or git.default_branch()
        got = _compose(git, Path(state_dir), slug, root, into, main)
        if got["sealed"]:
            raise GoalRefused(got["sealed"])
        old = _ok(_git(git.root, "rev-parse", f"refs/heads/{main}"))
        tip, hit = _pick(git, WORKTREE, old, got["commits"])
        if hit:
            raise GoalRefused(_conflict(got, slug, hit))
        git._fast_forward(main, old, tip)
        note = git.push(main) if push else ""
        pushed = bool(push and not note and "origin" in _git(git.root, "remote").stdout.split())
    return {"commit": tip, "goals": got["goals"], "commits": got["commits"], "files": got["files"], "note": note, "pushed": pushed}


def in_main(git: IdeaGit, shas: list[str], into: str, main: str) -> bool:
    """Every sha is in main: behind it, or there under another sha with the same patch (a pick). No sha is False."""
    held = [s for s in dict.fromkeys(str(s) for s in shas if s)]
    if not held:
        return False
    equal = idea_gate.cherry(git, into, main)[1]
    return idea_gate.all_in(git, [s for s in held if s not in equal], main) if any(s not in equal for s in held) else True
