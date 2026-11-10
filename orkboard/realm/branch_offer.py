"""The branches the discard's plates deal to the hand (docs/specs/168-the-window-played-as-a-card-games-table.md F2, decisions §283.27): git reads, no face.

    branch_offer.allowed("feature/x")                              # False for the Board's own and the work's: `orkboard/*`, `goal/*`, `idea/*` are never offered
    branch_offer.offered(git, "dev", dev="dev", main="main")       # the lower pile's plate (*dev*): any local branch the project may land in, the one now first
    branch_offer.offered(git, "main", dev="dev", main="main")      # the upper pile's plate (*main*): main or dev (the release branch the project keeps, git's default, the work branch)
    branch_offer.make_from(git, "next", "dev")                     # a new branch cut from dev's head (True when made); never from the default branch, as `IdeaGit.ensure_branch` cuts

The branches are the project's setting (`merge_into` in its Board settings; the release branch in `<state>/project.json`, realm/first_open.py), never a view.
"""
from __future__ import annotations

from orkboard.realm import worktrees
from orkboard.realm.idea_git import BRANCH_NAME, IdeaGit, _git, _ok

NEVER = ("orkboard/", "goal/", "idea/")                 # the Board's branches, a goal's and a task's: the project does not land in them or send from them (§283.27)
WHICH = ("dev", "main")


def allowed(name: str) -> bool:
    return bool(BRANCH_NAME.fullmatch(name or "")) and ".." not in name and not name.startswith(NEVER)


def offered(git: IdeaGit, which: str, dev: str, main: str) -> list[str]:
    """The branches the plate `which` ("dev": where goals land, "main": where they are sent) offers, the one now first, none twice, none that is never offered."""
    if which not in WHICH:
        raise ValueError("which is dev or main")
    local = [b for b in git.branches() if allowed(b)]
    now = dev if which == "dev" else main
    if which == "dev":
        rest = local
    else:
        rest = [b for b in (git.default_branch(), main, dev) if b and b in local]
    out: list[str] = []
    for b in (now, *rest):
        if b and allowed(b) and b not in out and (b in local or b == now):
            out.append(b)
    return out


def make_from(git: IdeaGit, name: str, base: str) -> bool:
    """A new branch `name` cut from `base`'s head; False when it is there already. Raises RuntimeError in words for a name that is not one, one that is never offered, or a base that is gone."""
    if not allowed(name) or not worktrees.valid_branch(git.root, name):
        raise RuntimeError(f"{name!r} is not a name for a branch")
    with git.lock:
        if worktrees.branch_exists(git.root, name):
            return False
        if not worktrees.branch_exists(git.root, base):
            raise RuntimeError(f"{base} is not a branch here, so a new one cannot start from it")
        _ok(_git(git.root, "branch", name, base))
    return True
