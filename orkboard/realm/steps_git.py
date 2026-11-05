"""The git of a task's steps file (docs/specs/129-a-tasks-steps.md H1.1): `.ork-steps.json` is put in the repository's
`.git/info/exclude` when a task's worktree is made, so `git add -A` leaves it out of what the task commits, and a landing
never takes it. Split from realm/idea_git.py, which calls these.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from orkboard import brand
from orkboard.realm import task_steps
from orkboard.realm.jobs import _git, _ok


COMMIT_FILE = ".ork-commit.md"      # what a task settled, for the body of the commit made for it (spec 149 F.2); never committed
COMMIT_NOTE_KEEP = 4000


def take_commit_note(path: Path) -> str:
    """What the task left in `.ork-commit.md` (at most COMMIT_NOTE_KEEP characters), and the file taken away so the next commit does not read it again."""
    file = Path(path) / COMMIT_FILE
    try:
        text = file.read_text(encoding="utf-8", errors="replace").strip()[:COMMIT_NOTE_KEEP]
        file.unlink()
    except OSError:
        text = ""
    return text


def exclude(path: Path) -> None:
    """The steps file and the commit note are added to the exclude file the worktree at `path` shares with its repository (said once: a line there
    already is left). Never raises: a worktree without the line only shows the file as untracked."""
    try:
        got = _git(path, "rev-parse", "--git-path", "info/exclude")
        file = Path(got.stdout.strip())
        file = file if file.is_absolute() else Path(path) / file
        text = file.read_text(encoding="utf-8") if file.exists() else ""
        missing = [n for n in (task_steps.FILE, COMMIT_FILE) if n not in text.splitlines()]
        if got.returncode == 0 and missing:
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(text + ("" if not text or text.endswith("\n") else "\n") + "".join(f"{n}\n" for n in missing), encoding="utf-8")
    except (OSError, subprocess.SubprocessError):
        pass


def leave(path: Path, into: str) -> None:
    """A landing never takes the steps file: it is taken off the disk, and out of the branch if the worker committed it (a
    commit says so), unless `into` has a file of that name of its own (the project's, left as it is)."""
    tracked = lambda: _git(path, "ls-files", "--error-unmatch", "--", task_steps.FILE).returncode == 0  # noqa: E731
    if tracked() and _git(path, "cat-file", "-e", f"{into}:{task_steps.FILE}").returncode != 0:
        _ok(_git(path, "rm", "-q", "--cached", "--", task_steps.FILE))
        _ok(_git(path, *brand.git_identity(), "commit", "-q", "-m",
                 f"{brand.name()}: the steps file is not part of the work"))
    if not tracked():
        try:
            (Path(path) / task_steps.FILE).unlink()
        except OSError:
            pass
    take_commit_note(path)                                  # a note left after the last commit belongs to no commit
