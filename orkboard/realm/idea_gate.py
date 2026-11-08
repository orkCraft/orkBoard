"""The gate: what dev holds that main lacks, and the one merge that moves main (docs/specs/49-one-window.md §2.1,
decisions §49.5). Git reads and the merge, no face.

    shas, files = idea_gate.waiting(git, "dev", "main")      # `git rev-list main..dev` (newest first), the files `main...dev` changes
    shas, files = idea_gate.waiting_by_patch(git, "dev", "main")   # … less what main holds by patch id (a goal sent alone: realm/goal_main.py)
    idea_gate.ideas_in(shas, rows)                          # the ideas with a merged task whose `commit` is among them
    idea_gate.all_in(git, shas, "main")                      # every sha is in main already (a goal's flag, spec 50 §2.2)
    got = idea_gate.merge(git, "dev", "main", push=True)     # main moved to dev's work: {"commit", "how", "commits", "files", "note", "pushed"}

`git` is an `IdeaGit` (realm/idea_git.py). `merge` runs under the repository's lock. When main is an ancestor of dev,
main is fast-forwarded to dev the way a result lands (`IdeaGit._fast_forward`: a root checkout on main moves with
`merge --ff-only` and is refused with its files when they are changed, else `update-ref`). Otherwise (main moved since)
a merge commit is made in a worktree of its own, detached at main, and main is fast-forwarded to it. Whatever is
refused, main is as it was and no worktree is left behind. Nothing here moves dev.
"""
from __future__ import annotations

import re
from typing import Any, Iterable

from orkboard import brand
from orkboard.realm import worktrees
from orkboard.realm.idea_git import BOARD_NAME, BOARD_PAGE, PUSH_TIMEOUT_S, IdeaGit, _git, _ok

_SHA = re.compile(r"[0-9a-f]{7,64}")

WORKTREE = "gate-merge"                      # the merge commit's worktree, under `.orkcraft/worktrees/`


class GateRefused(RuntimeError):
    """The gate does not merge, in plain words; main is as it was."""


def same(into: str, main: str) -> bool:
    """dev and main are one branch, or main does not exist: there is no gate."""
    return not main or main == into


def refusal_same(into: str, main: str) -> str:
    if not main:
        return "This folder has no main branch: there is no gate"
    if into == main:
        return f"Results merge into {main} itself: there is no gate"
    return f"{main} is {into} here: there is no gate"


def _ref(name: str) -> str:
    return f"refs/heads/{name}"


def waiting(git: IdeaGit, into: str, main: str) -> tuple[list[str], int]:
    """(the commits `into` holds that `main` lacks, newest first; the count of files they change): ([], 0) when either
    branch is missing or nothing waits. One read of `rev-list` for all the ideas, one of `diff` for the files."""
    if not all(worktrees.branch_exists(git.root, b) for b in (into, main)):
        return [], 0
    shas = _git(git.root, "rev-list", f"{_ref(main)}..{_ref(into)}", "--").stdout.split()
    if not shas:
        return [], 0
    names = _git(git.root, "diff", "--name-only", "-z", f"{_ref(main)}...{_ref(into)}", "--").stdout.split("\0")
    return shas, sum(1 for n in names if n)


def cherry(git: IdeaGit, into: str, main: str) -> tuple[list[str], set[str]]:
    """(the commits `into` holds that `main` lacks by patch id, oldest first; the commits of `into` main holds under another sha): `git
    cherry`, which tells a commit by what it changes, never by its sha. A commit already behind `main` is in neither."""
    if not all(worktrees.branch_exists(git.root, b) for b in (into, main)):
        return [], set()
    pending: list[str] = []
    equal: set[str] = set()
    for line in _git(git.root, "cherry", _ref(main), _ref(into)).stdout.splitlines():
        mark, _, sha = line.partition(" ")
        sha = sha.strip()
        if _SHA.fullmatch(sha):
            if mark == "+":
                pending.append(sha)
            else:
                equal.add(sha)
    return pending, equal


def _count_files(git: IdeaGit, shas: list[str]) -> int:
    """The files these commits change, each once."""
    names: set[str] = set()
    for at in range(0, len(shas), 200):
        out = _git(git.root, "-c", "core.quotePath=false", "log", "--no-walk=unsorted", "--no-renames", "--name-only", "--format=",
                   *shas[at:at + 200], "--").stdout
        names.update(n for n in out.splitlines() if n)
    return len(names)


def waiting_by_patch(git: IdeaGit, into: str, main: str) -> tuple[list[str], int]:
    """`waiting`, less the commits main holds by patch id (a goal sent to main on its own is cherry-picked, so main holds it under new
    shas): the commits newest first, and the files they change. Where main is behind `into` (nothing was picked) it is `waiting`'s."""
    shas, files = waiting(git, into, main)
    if not shas or _git(git.root, "merge-base", "--is-ancestor", _ref(main), _ref(into)).returncode == 0:
        return shas, files
    pending = set(cherry(git, into, main)[0])
    kept = [s for s in shas if s in pending]
    if len(kept) == len(shas):
        return shas, files
    return kept, _count_files(git, kept) if kept else 0


def without_board_pages(git: IdeaGit, shas: list[str], files: int) -> tuple[list[str], int]:
    """`shas`, less the Board's own commits: those that touch only Board pages (`idea_git.BOARD_PAGE`: a laid table with no work has none to carry,
    spec 143 F.4, decisions §247.1) and those authored by the Board (`idea_git.BOARD_NAME`: the fold's `llm-wiki/<wiki>/specs/<capability>.md` is
    the Board's though it is no Board page, spec 149 G.4, decisions §253.8). They go into main with the next goal as they always did. A commit of
    code that belongs to no goal stays, and so does one that changes no file (a merge). Gives (the kept commits, the count of files they change;
    `files` as given when none is left out)."""
    if not shas:
        return shas, files
    changed: dict[str, list[str]] = {}
    board: set[str] = set()
    authors = {BOARD_NAME, brand.board_author()[0]}           # the Board's commits before spec 149 F.3 (*Orkline board*) and since (*<the product> board*)
    for at in range(0, len(shas), 200):
        out = _git(git.root, "-c", "core.quotePath=false", "log", "--no-walk=unsorted", "--no-renames", "--name-only", "--format=%x00%H%x01%an", *shas[at:at + 200], "--").stdout
        for chunk in out.split("\0")[1:]:
            head, _, names = chunk.partition("\n")
            sha, _, author = head.partition("\x01")
            changed[sha.strip()] = [n for n in names.splitlines() if n]
            if author.strip() in authors:
                board.add(sha.strip())
    kept = [s for s in shas if s not in board and (not changed.get(s) or any(not BOARD_PAGE.search(n) for n in changed[s]))]
    if len(kept) == len(shas):
        return shas, files
    return kept, _count_files(git, kept) if kept else 0


def without_commits(git: IdeaGit, shas: list[str], files: int, left: set[str]) -> tuple[list[str], int]:
    """`shas`, less the commits in `left` (those of goals not ready for main: spec 149 G.3); the files the kept ones change."""
    kept = [s for s in shas if s not in left]
    if len(kept) == len(shas):
        return shas, files
    return kept, _count_files(git, kept) if kept else 0


def ideas_in(shas: Iterable[str], rows: Iterable[tuple[str, str, str, list[dict]]]) -> list[dict]:
    """`rows`: (slug, title, goal, tasks) of each idea in the Board's order. The ideas with a merged task whose `commit`
    is among `shas`, each `{slug, title, goal, tasks}` with the count of such tasks."""
    held = set(shas)
    out = []
    for slug, title, goal, tasks in rows:
        n = sum(1 for t in tasks if t.get("state") == "merged" and str(t.get("commit") or "") in held)
        if n:
            out.append({"slug": slug, "title": title, "goal": goal, "tasks": n})
    return out


def all_in(git: IdeaGit, shas: Iterable[str], main: str) -> bool:
    """Every sha is in `main` (an ancestor of it); no sha is False. One `rev-list` of the shas that main does not hold: a sha
    git does not know, or a branch that is not there, is not in main either."""
    held = list(dict.fromkeys(str(s) for s in shas if s))
    if not held or not main or not all(_SHA.fullmatch(s) for s in held):
        return False
    got = _git(git.root, "rev-list", "--max-count=1", *held, "--not", _ref(main), "--")
    return got.returncode == 0 and not got.stdout.strip()


def merge(git: IdeaGit, into: str, main: str, push: bool = False, *, tested: tuple[str, str] | None = None) -> dict[str, Any]:
    """Main moved to the work in `into`, then pushed when asked. {"commit" (main's new head), "how" ("fast-forward" |
    "merge"), "commits" (the shas it brought), "files", "note" (the push's, as `land`'s: "" when pushed or no origin),
    "pushed"}. Raises GateRefused in plain words; RuntimeError when git cannot move main (a root checkout with the
    files changed): either way main is as it was. `tested` (`heads` when the checks began): main or `into` moved since is refused."""
    with git.lock:
        if same(into, main):
            raise GateRefused(refusal_same(into, main))
        shas, files = waiting_by_patch(git, into, main)
        if not shas:
            raise GateRefused(f"Nothing in {into} waits for {main}")
        old, new = heads(git, into, main)
        if tested is not None and (old, new) != tuple(tested):
            raise GateRefused(f"{main} or {into} moved while the tests ran: press again to test what is there now")
        if _git(git.root, "merge-base", "--is-ancestor", old, new).returncode == 0:
            how, tip = "fast-forward", new
        else:
            how, tip = "merge", _merge_commit(git, into, main, old)
        git._fast_forward(main, old, tip)
        note = git.push(main) if push else ""
        pushed = bool(push and not note and "origin" in _git(git.root, "remote").stdout.split())
    return {"commit": tip, "how": how, "commits": shas, "files": files, "note": note, "pushed": pushed}


def heads(git: IdeaGit, into: str, main: str) -> tuple[str, str]:
    """(main's head, `into`'s head) now."""
    return tuple(_ok(_git(git.root, "rev-parse", _ref(b))) for b in (main, into))


def tip(git: IdeaGit, into: str, main: str) -> str:
    """The commit main would become if `into` were merged now (`into` itself on a fast-forward, else the merge commit, made in a worktree that is gone); no ref moves."""
    with git.lock:
        old, new = (_ok(_git(git.root, "rev-parse", _ref(b))) for b in (main, into))
        return new if _git(git.root, "merge-base", "--is-ancestor", old, new).returncode == 0 else _merge_commit(git, into, main, old)


def _merge_commit(git: IdeaGit, into: str, main: str, old: str) -> str:
    """*Merge dev into main*, made in a worktree of its own detached at main (`old`); the commit. A conflict aborts the
    merge. The worktree is gone either way."""
    path = worktrees.worktree_path(git.root, WORKTREE)
    git.remove(path)                                           # a leftover of an earlier try
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        _ok(_git(git.root, "worktree", "add", "--detach", str(path), old))
        done = _git(path, *brand.git_identity(), "merge", "--no-ff", "-m", f"Merge {into} into {main}", _ref(into), timeout=PUSH_TIMEOUT_S)
        if done.returncode != 0:
            files = _git(path, "diff", "--name-only", "--diff-filter=U").stdout.split()
            _git(path, "merge", "--abort")
            if files:
                raise GateRefused(f"{into} and {main} conflict in {', '.join(files)}: merge {main} into {into} first")
            raise GateRefused(" ".join((done.stderr or done.stdout).split())[:300] or "The merge failed")
        return git.head(path)
    finally:
        git.remove(path)
