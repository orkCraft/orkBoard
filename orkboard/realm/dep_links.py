"""A task's worktree has the project's installed dependencies (docs/specs/86-what-the-logs-said.md §2).

    linked = link(repo_root, worktree)      # ["node_modules", "web/node_modules", ".venv"]: the symlinks laid
    n = present(repo_root, worktree)        # how many lie there now, linked to the main checkout (spec 107 §1.2)

A fresh worktree holds only what git tracks, so a task could not run the project's tests until it installed them (`npm ci`
in every worktree, which a task is never allowed: realm/task_commands.py). Code lays them instead: the main checkout's
`node_modules/` (of each folder with a `package.json`, two levels deep at most) and `.venv/`, each a symlink where the
worktree has none, removed with the worktree. The names go to the repository's `info/exclude`, so `git add -A` never
commits a link (a pattern without a trailing slash, which matches a symlink too). No face.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from orkboard.realm import task_commands


def link(repo_root: Path, worktree: Path) -> list[str]:
    """Symlink the main checkout's dependencies into `worktree` where it has none; the relative paths linked."""
    root, tree = Path(repo_root), Path(worktree)
    linked: list[str] = []
    for src in [d / "node_modules" for d in task_commands.package_dirs(root)] + [root / ".venv"]:
        rel = src.relative_to(root)
        dst = tree / rel
        if not src.is_dir() or src.is_symlink() or dst.exists() or dst.is_symlink() or not dst.parent.is_dir():
            continue
        try:
            dst.symlink_to(src, target_is_directory=True)
        except OSError:
            continue
        linked.append(rel.as_posix())
    if linked:
        exclude(tree, sorted({Path(r).name for r in linked}))
    return linked


def present(repo_root: Path, worktree: Path) -> int:
    """How many dependency folders lie linked in `worktree`: the symlinks (of the names `link` lays) that point into the main checkout."""
    root, tree = Path(repo_root).resolve(), Path(worktree)
    n = 0
    for src in [d / "node_modules" for d in task_commands.package_dirs(Path(repo_root))] + [Path(repo_root) / ".venv"]:
        dst = tree / src.relative_to(repo_root)
        try:
            if dst.is_symlink() and dst.resolve().is_relative_to(root):
                n += 1
        except OSError:
            continue
    return n


def exclude(worktree: Path, names: list[str]) -> None:
    """`names` (matched at any depth) added to the repository's `info/exclude`, once each."""
    try:
        got = subprocess.run(["git", "rev-parse", "--git-path", "info/exclude"], cwd=worktree, capture_output=True,
                             text=True, timeout=30)
        if got.returncode != 0 or not got.stdout.strip():
            return
        where = Path(got.stdout.strip())
        where = where if where.is_absolute() else Path(worktree) / where
        have = where.read_text(encoding="utf-8").splitlines() if where.is_file() else []
        new = [n for n in names if n not in have]
        if new:
            where.parent.mkdir(parents=True, exist_ok=True)
            with where.open("a", encoding="utf-8") as f:
                f.write(("\n" if have and have[-1] != "" else "") + "\n".join(new) + "\n")
    except (OSError, subprocess.SubprocessError):
        pass
