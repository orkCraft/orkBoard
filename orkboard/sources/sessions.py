"""Where Claude Code, agy and Codex keep their sessions on this machine, and the log their hooks write.

    log_file(repo_root)             `<repo>/.orkcraft/sessions.jsonl`, written from the Claude / agy / Codex hooks
    claude_projects_dir(repo_root)  Claude Code's transcripts of the project: `~/.claude/projects/<path with / → ->`
    agy_brain_dir()                 agy's conversations: `~/.gemini/antigravity-cli/brain/<conversation-id>/`
    codex_bin()                     the Codex CLI

`MAX_LOCAL` is how many of a project's newest sessions a reader looks at.
"""
from __future__ import annotations

import re
from pathlib import Path

from orkboard.env import getenv

MAX_LOCAL = 60


def log_file(repo_root: Path) -> Path:
    return repo_root / ".orkcraft" / "sessions.jsonl"


def claude_projects_dir(repo_root: Path) -> Path:
    base = Path(getenv("CLAUDE_HOME") or Path.home() / ".claude")
    # Claude Code names the folder after the project path with every non-alphanumeric → "-".
    return base / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(repo_root.resolve()))


def agy_brain_dir() -> Path:
    base = getenv("AGY_HOME") or str(Path.home() / ".gemini" / "antigravity-cli")
    return Path(base) / "brain"


def codex_bin() -> str:
    return getenv("CODEX_BIN") or "codex"
