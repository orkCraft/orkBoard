"""Git's plumbing, shared by the journal (realm/remote_journal.py) and the Board's branch (realm/board_branch.py): a temporary
index, `hash-object`, `update-index`, `write-tree`, `commit-tree`, and the scrub of a secret's shape (decisions §229.3, §244.1).

    env = plumbing.env(index)                                            # author and a private index file; no password asked of no one
    plumbing.git(root, run, env, "rev-parse", "HEAD")                    # the text out; RuntimeError with git's own words on a failure
    plumbing.git_raw(root, run, env, "cat-file", "blob", sha)            # the bytes out
    tree = plumbing.tree_of(root, run, env, {"a/b.txt": b"…"})           # files -> a tree object (the index is `env`'s)
    plumbing.scrub(text)                                                 # (text with the lines of a secret's shape replaced, how many)

The person's working tree, index and branches are never touched: the index is a file of ours.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Callable

HELD = "[held back: it looked like a secret]"
AUTHOR = {"GIT_AUTHOR_NAME": "Orkboard", "GIT_AUTHOR_EMAIL": "orkboard@localhost",
          "GIT_COMMITTER_NAME": "Orkboard", "GIT_COMMITTER_EMAIL": "orkboard@localhost"}

SECRETS = re.compile("|".join((
    r"sk-[A-Za-z0-9_-]{20,}", r"sk-ant-[A-Za-z0-9_-]{20,}", r"ghp_[A-Za-z0-9]{30,}", r"github_pat_[A-Za-z0-9_]{30,}",
    r"xox[baprs]-[A-Za-z0-9-]{10,}", r"AKIA[0-9A-Z]{16}", r"AIza[0-9A-Za-z_-]{35}", r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    r"(?i:(?:api[_-]?key|secret|token|password)\s*[=:]\s*\S{12,})")))


def scrub(text: str) -> tuple[str, int]:
    """The text with every line that has a secret's shape replaced by words, and how many were."""
    held, out = 0, []
    for ln in text.splitlines(keepends=True):
        if SECRETS.search(ln):
            held += 1
            out.append(HELD + ("\n" if ln.endswith("\n") else ""))
        else:
            out.append(ln)
    return "".join(out), held


def env(index: Path | None = None) -> dict:
    out = {**os.environ, **AUTHOR, "GIT_TERMINAL_PROMPT": "0"}          # never a password asked of no one
    if index is not None:
        out["GIT_INDEX_FILE"] = str(index)
    return out


def git_raw(root: Path, run: Callable, env: dict, *args: str, data: bytes | None = None, timeout: int = 120) -> bytes:
    done = run(["git", *args], cwd=str(root), env=env, input=data, capture_output=True, timeout=timeout)
    if done.returncode != 0:
        words = (done.stderr or done.stdout or b"")
        raise RuntimeError(" ".join((words.decode("utf-8", "replace") if isinstance(words, bytes) else str(words)).split()) or f"git {args[0]} failed")
    out = done.stdout
    return out if isinstance(out, bytes) else str(out).encode("utf-8")


def git(root: Path, run: Callable, env: dict, *args: str, data: bytes | None = None, timeout: int = 120) -> str:
    return git_raw(root, run, env, *args, data=data, timeout=timeout).decode("utf-8", "replace").strip()


def tree_of(root: Path, run: Callable, env: dict, files: dict[str, bytes]) -> str:
    """The files (path -> bytes, all `100644`) as a tree object, built in `env`'s index (which is emptied first)."""
    index = Path(env["GIT_INDEX_FILE"])
    index.unlink(missing_ok=True)
    for name, body in files.items():
        sha = git(root, run, env, "hash-object", "-w", "--stdin", data=body)
        git(root, run, env, "update-index", "--add", "--cacheinfo", f"100644,{sha},{name}")
    return git(root, run, env, "write-tree")
