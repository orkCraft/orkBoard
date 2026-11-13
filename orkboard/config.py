"""Where the project is: its root, found by walking up from a folder (`find_project_root`)."""
from __future__ import annotations

from pathlib import Path


def find_project_root(start_path: Path | None = None) -> Path:
    """Find project root by walking up looking for .orkcraft.json or .git.

    Can start from start_path or Path.cwd().
    Raises FileNotFoundError if not inside a valid project.
    """
    p = (start_path or Path.cwd()).resolve()
    for c in [p, *p.parents]:
        if (c / ".orkcraft.json").exists() or (c / ".git").exists():
            return c
    raise FileNotFoundError(
        f"orkcraft: project root (.orkcraft.json or .git) not found starting from {p}"
    )
