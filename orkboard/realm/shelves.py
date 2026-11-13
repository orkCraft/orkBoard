"""A folder the Board reads, kept inside the repository (`inside`): the wiki's (realm/wiki.py `root_of`)."""
from __future__ import annotations

from pathlib import Path


def inside(repo_root: Path, rel: str) -> Path:
    p = (repo_root / rel).resolve() if not Path(rel).expanduser().is_absolute() else Path(rel).expanduser().resolve()
    root = repo_root.resolve()
    if p != root and root not in p.parents:
        raise ValueError(f"{rel} is outside the repository")
    return p
