"""The files a goal's text names with `@` (docs/specs/107-what-the-owners-day-said.md part K, decisions §182.13): `@src/lobby/room.py` in New goal's field.

    text, n = goal_mentions.files(root, "Fix @src/lobby/room.py, then @docs/")   # "Fix `src/lobby/room.py`, then `docs/`", 2

Each `@path` that exists in the project (a file or a folder, never outside it, never `.git/` or `.orkcraft/`) becomes the path in backticks, so the route's
reading of a path (`goal_route._PATH`) and the leaders read it as code; an `@word` that is no path of the project stays as the person wrote it (`@Tech` is the
address, taken off before this, and an e-mail address is not a mention). What lies in backticks already is left as it is. No face, no call, nothing read: only
whether the path exists.
"""
from __future__ import annotations

import re
from pathlib import Path

HIDDEN = (".git", ".orkcraft")
_SPAN = re.compile(r"```.*?```|`[^`\n]*`", re.S)                                  # code the person already marked: left alone
_AT = re.compile(r"(?<![\w@.`/-])@((?:[\w.+~-]+/)*[\w.+~-]+/?)")                 # an `@` at a word's start, then a path of the project's
_TAIL = ".,;:!?)]}'\""                                                              # what a sentence puts after a path


def exists(root: Path, rel: str) -> bool:
    """Whether `rel` (a path with `/`) is a file or a folder of the project at `root`: not absolute, no `..`, not in the repository's own state."""
    parts = [p for p in rel.split("/") if p and p != "."]
    if not parts or ".." in parts or any(p in HIDDEN for p in parts):
        return False
    try:
        return (root.joinpath(*parts)).exists()
    except OSError:
        return False


def _mention(root: Path, m: re.Match[str], found: list[int]) -> str:
    path = m.group(1)
    tail = ""
    while path and not exists(root, path) and path[-1] in _TAIL:                     # `@README.md.` is the file and a full stop
        path, tail = path[:-1], path[-1] + tail
    if not path or not exists(root, path):
        return m.group(0)
    found.append(1)
    return f"`{path}`{tail}"


def files(root: Path, text: str) -> tuple[str, int]:
    """`text` with each `@path` that exists written as `` `path` ``, and how many there were."""
    found: list[int] = []
    out, at = [], 0
    for span in _SPAN.finditer(text):
        out.append(_AT.sub(lambda m: _mention(root, m, found), text[at:span.start()]))
        out.append(span.group(0))
        at = span.end()
    out.append(_AT.sub(lambda m: _mention(root, m, found), text[at:]))
    return "".join(out), len(found)
