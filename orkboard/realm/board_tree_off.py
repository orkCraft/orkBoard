"""The Board's tree when the Board is not in the code (spec 151 F.2, decisions §255.10): its commits stay on `refs/orkboard/pages`, local and never
pushed, and the work branch never gets one. Split from realm/board_tree.py, which calls these; `BoardTree(…, goes=…)` says which way it is.

    leave(tree)      # the first time off: the pages the work branch holds leave it in ONE commit (`board: the Board's pages leave the repository`;
                     # its history keeps them); the tree goes on from a commit of its own on top of that, and `refs/orkboard/pages` follows it
    keep(tree)       # off already: the ref moved to the tree's tip
    enter(tree)      # the yes later: the pages go into the work branch in ONE commit (`board: the Board goes into the code`), the ref is dropped
    merge_tip(tree, tip)   # the tree follows the work branch by a merge (its own commits are never replayed); False when it cannot

The tree's mark is `<state_dir>/board_tree_off.json` (`{"off": true}`): which lineage the tree is on. All of it runs under the repository's lock,
by plumbing where the person's checkout could be touched: the work branch moves only by `IdeaGit._fast_forward`'s rules. No face, no model.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from orkboard import brand
from orkboard.realm.jobs import _git, _ok

REF = "refs/orkboard/pages"
MARK = "board_tree_off.json"
LEAVE = "board: the Board's pages leave the repository"
KEPT = "board: the Board's pages (kept off the repository)"
ENTER = "board: the Board goes into the code"


def is_off(tree) -> bool:
    """Whether the tree is on the lineage of its own (the ref's), by its mark."""
    try:
        return json.loads((tree.path.parent / MARK).read_text(encoding="utf-8")).get("off") is True
    except (OSError, ValueError, AttributeError):
        return False


def _mark(tree, off: bool) -> None:
    file = tree.path.parent / MARK
    if off:
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(json.dumps({"off": True}) + "\n", encoding="utf-8")
    else:
        file.unlink(missing_ok=True)


def has_ref(tree) -> bool:
    return _git(tree.git.root, "rev-parse", "-q", "--verify", REF).returncode == 0


def _commit_tree(tree, tree_sha: str, parent: str, message: str) -> str:
    who, email = brand.board_author()
    return _ok(_git(tree.git.root, "-c", f"user.name={who}", "-c", f"user.email={email}", "commit-tree", tree_sha, "-p", parent, "-m", message))


def _without_pages(tree, tip: str) -> str:
    """The tree object of the work branch's `tip` with the Board's pages taken out, by a private index file: nothing of the person's is touched."""
    index = tree.path.parent / "board-off.index"
    env = {**os.environ, "GIT_INDEX_FILE": str(index)}
    root = str(tree.git.root)
    try:
        def run(*args: str) -> str:
            done = subprocess.run(["git", *args], cwd=root, env=env, capture_output=True, text=True, timeout=120)
            return _ok(done)
        run("read-tree", tip)
        run("rm", "--cached", "-r", "-q", "-f", "--ignore-unmatch", "--", *tree.pages())
        return run("write-tree")
    finally:
        index.unlink(missing_ok=True)


def merge_tip(tree, tip: str) -> bool:
    """The work branch's `tip` merged into the tree (its pages and the code never touch the same file); the merge aborted and False when git refuses."""
    who, email = brand.board_author()
    done = _git(tree.path, "-c", f"user.name={who}", "-c", f"user.email={email}", "merge", "-q", "--no-edit", "-m", f"board: follows {tree.branch()}", tip)
    if done.returncode != 0:
        _git(tree.path, "merge", "--abort")
        return False
    return True


def leave(tree) -> str:
    """The tree goes off. "" when done, else why it is held (the work branch could not take the commit: the person's files are not clean). The tree is
    followed already and holds no uncommitted page (the flush committed them)."""
    tip, head = tree._tip(), tree.git.head(tree.path)
    if _ok(_git(tree.git.root, "ls-tree", "-r", "--name-only", tip, "--", *tree.pages())):
        gone = _commit_tree(tree, _without_pages(tree, tip), tip, LEAVE)
        mine = _commit_tree(tree, _ok(_git(tree.path, "rev-parse", f"{head}^{{tree}}")), gone, KEPT)
        tree.git._fast_forward(tree.branch(), tip, gone)            # RuntimeError: held, and nothing has moved
        _ok(_git(tree.path, "reset", "-q", "--soft", mine))
        head = mine
    _mark(tree, True)
    _ok(_git(tree.git.root, "update-ref", REF, head))
    return ""


def keep(tree) -> None:
    _ok(_git(tree.git.root, "update-ref", REF, tree.git.head(tree.path)))


def enter(tree) -> str:
    """The yes: the tree's pages (it is followed, so its tree is the work branch's code and the pages) go into the work branch in one commit; the ref
    is dropped. "" when done, else why it is held."""
    tip, head = tree._tip(), tree.git.head(tree.path)
    want = _ok(_git(tree.path, "rev-parse", f"{head}^{{tree}}"))
    if want != _ok(_git(tree.git.root, "rev-parse", f"{tip}^{{tree}}")):
        new = _commit_tree(tree, want, tip, ENTER)
        tree.git._fast_forward(tree.branch(), tip, new)            # RuntimeError: held
        _ok(_git(tree.path, "reset", "-q", "--soft", new))
    _mark(tree, False)
    _git(tree.git.root, "update-ref", "-d", REF)
    return ""
