"""The read-in commands (docs/specs/126-read-in-and-write-out.md §B.4; decisions §204), as `gui/ideas.py`'s `Ideas` has them: what the project's own documents hold (ADRs, specs, notes,
a changelog) and the person's *read it in* of them into the journals. The reading is `realm/read_in.py`'s.

    ideas.read_in_scan {}      # → {found: [{framework, kind, path, n}]}: the shapes the project keeps
    ideas.read_in_take {}      # → {decisions, leaders, done, releases, journals, specs_read}: the entries added to the journals (a thing read in once is never read in twice)

The host returns data, never interface words.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from orkboard.realm import read_in


class ReadInMixin:
    def read_in_scan(self, args: dict) -> dict:
        return {"found": read_in.scan(Path(self.host.repo_root), self.state_dir)["found"]}

    def read_in_take(self, args: dict) -> dict:
        got = read_in.take(Path(self.host.repo_root), self.state_dir, board=self.root(False))
        if got.get("specs_read"):
            self.tree_note("", "specs read in")             # the living specs read in are committed with the Board's pages (spec 127 C.4)
        return got


def read_in_commands(ideas_: Any) -> dict:
    """The read-in commands by name (`gui/ideas.py` adds them to its table: `**read_in_commands(self)`)."""
    return {"ideas.read_in_scan": ideas_.read_in_scan, "ideas.read_in_take": ideas_.read_in_take}
