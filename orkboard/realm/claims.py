"""📍 Areas in work: the files and folders a task changes, compared with another's (design:
docs/design/barracks-designs.md §3–4).

    narrow(paths)               a claim never holds the root or a whole top-level folder: it would overlap
                                every task
    meets(a, b)                 the paths of `a` that meet one of `b`

No model: paths are compared as `plans.overlap` compares a plan's parts.
"""
from __future__ import annotations

from orkboard.realm import plans

MAX_PATHS = 40


def norm(path: str) -> str:
    return str(path or "").strip().strip("`").removeprefix("./").strip("/")


def too_wide(path: str) -> bool:
    """The root, or one top-level folder (`src/`, `docs`): a claim on it would meet every task."""
    p = norm(path)
    return not p or p == "." or ("/" not in p and "." not in p)


def narrow(paths: list[str]) -> list[str]:
    out = [norm(p) for p in paths if not too_wide(p)]
    return list(dict.fromkeys(out))[:MAX_PATHS]


def meets(a: list[str], b: list[str]) -> list[str]:
    """The paths of `a` that meet one of `b` (a folder holds what is under it)."""
    return [x for x in a if b and plans.overlap([x], b)]
