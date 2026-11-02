"""The git of a task's steps file (docs/specs/129-a-tasks-steps.md H1.1): `.ork-steps.json` is put in the repository's
`.git/info/exclude` when a task's worktree is made, so `git add -A` leaves it out of what the task commits, and a landing
never takes it. Split from realm/idea_git.py, which calls these.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from orkboard.realm import task_steps
from orkboard.realm.jobs import _git, _ok


def exclude(path: Path) -> None:
    """The steps file is added to the exclude file the worktree at `path` shares with its repository (said once: a line there
    already is left). Never raises: a worktree without the line only shows the file as untracked."""
    try:
        got = _git(path, "rev-parse", "--git-path", "info/exclude")
        file = Path(got.stdout.strip())
        file = file if file.is_absolute() else Path(path) / file
        text = file.read_text(encoding="utf-8") if file.exists() else ""
        if got.returncode == 0 and task_steps.FILE not in text.splitlines():
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(text + ("" if not text or text.endswith("\n") else "\n") + task_steps.FILE + "\n", encoding="utf-8")
    except (OSError, subprocess.SubprocessError):
        pass


def leave(path: Path, into: str) -> None:
    """A landing never takes the steps file: it is taken off the disk, and out of the branch if the worker committed it (a
    commit says so), unless `into` has a file of that name of its own (the project's, left as it is)."""
    tracked = lambda: _git(path, "ls-files", "--error-unmatch", "--", task_steps.FILE).returncode == 0  # noqa: E731
    if tracked() and _git(path, "cat-file", "-e", f"{into}:{task_steps.FILE}").returncode != 0:
        _ok(_git(path, "rm", "-q", "--cached", "--", task_steps.FILE))
        _ok(_git(path, "-c", "user.name=Orkline", "-c", "user.email=orkline@localhost", "commit", "-q", "-m",
                 "Orkline: the steps file is not part of the work"))
    if not tracked():
        try:
            (Path(path) / task_steps.FILE).unlink()
        except OSError:
            pass
