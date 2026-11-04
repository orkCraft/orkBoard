"""Where the project's hypotheses file is read and how it is written (docs/specs/133-a-hypothesis-its-two-conditions-its-test-its-file.md C.1, C.3; decisions §235.6): the record's side of
`realm/hypotheses_file.py`. No model, no face; `realm/hypotheses.py` calls it, and nothing else needs to.

    hypotheses_bind.base(state_dir)                  # the folder the file is read in: the Board's tree (`<state_dir>/board`) where it stands (dev's own copy), else the project's folder (`state_dir`'s parent)
    hypotheses_bind.file(state_dir)                  # the bound file's path from the root (`hypotheses.json` `file`), when it is still a regular file inside `base`; else None
    hypotheses_bind.text(state_dir)                  # the file's text, None when no file is bound
    hypotheses_bind.set_writer(state_dir, put)       # the host's writer: `put(rel, edit, message)` is `BoardTree.edit_file` (commits with the Board's pages); None: the working copy is written, not committed
    hypotheses_bind.write(state_dir, items, drop=(), message="")   # the file with `items` written into it → {id: id it got}; ValueError in plain words when it cannot be written, nothing changed

The binding is `<state_dir>/hypotheses.json` `file`; **no file bound reads and writes the record as it always did**. A file that is gone reads as no file.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from orkboard.realm import hypotheses_file, ideas

FILE = "hypotheses.json"
_WRITERS: dict[str, Callable] = {}


def base(state_dir: Path) -> Path:
    board = Path(state_dir) / "board"
    return board if (board / ".git").exists() else Path(state_dir).parent


def _kept(state_dir: Path) -> str:
    got = (ideas._json(Path(state_dir) / FILE) or {}).get("file")
    return got.strip() if isinstance(got, str) else ""


def file(state_dir: Path) -> str | None:
    rel = _kept(state_dir)
    if not rel:
        return None
    root = base(state_dir)
    return hypotheses_file.find(root, rel) if (root / rel).is_file() else None


def text(state_dir: Path) -> str | None:
    rel = file(state_dir)
    if rel is None:
        return None
    try:
        return (base(state_dir) / rel).read_text("utf-8", errors="replace")
    except OSError:
        return None


def set_writer(state_dir: Path, put: Callable | None) -> None:
    if put is None:
        _WRITERS.pop(str(state_dir), None)
    else:
        _WRITERS[str(state_dir)] = put


def write(state_dir: Path, items: list[dict], drop=(), message: str | Callable[[dict], str] = "", rel: str = "") -> dict:
    """The file's new text from its text now and `items` (the record's, the proposed ones ignored) → `{id: id it got}`. Written through the host's writer (one commit with the Board's pages) or, with
    none, in the working copy. ValueError in plain words for no file, and for a write that failed: nothing is changed then."""
    rel = rel or file(state_dir) or ""
    if not rel:
        raise ValueError("The hypotheses file is not there")
    renames: dict = {}

    def edit(old: str) -> str:
        new, got = hypotheses_file.apply(old, items, drop)
        renames.clear()
        renames.update(got)
        return new

    put = _WRITERS.get(str(state_dir))
    say = (lambda: message(dict(renames))) if callable(message) else message          # the commit's words, read after the file is made (the ids the new sections got)
    try:
        if put is not None:
            put(rel, edit, say)
        else:
            path = base(state_dir) / rel
            path.write_text(edit(path.read_text("utf-8", errors="replace") if path.is_file() else ""), "utf-8")
    except (OSError, RuntimeError) as e:
        raise ValueError(f"The hypotheses file could not be written: {' '.join(str(e).split())[:200]}") from None
    return dict(renames)
