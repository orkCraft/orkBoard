"""Release's chronicle, as `gui/ideas.py`'s `Ideas` has it (docs/specs/134-release-keeps-the-chronicle.md A.7, decisions §238): the past past the portal, read by code (realm/chronicle.py). Each command
reads; none writes and none records an event. Keys and data, never words.

    ideas.chronicle {}                  # {kind, earlier, chapters: [{id, kind, name, day, open, goals?, decisions?}], unreleased}: only the newest chapter is open
    ideas.chronicle_line {}             # {earlier}: Release's lens, one line, nothing else read
    ideas.chronicle_chapter {id}        # {id, kind, name, day, goals, decisions}; refused in words for a chapter that is gone
    ideas.chronicle_find {query}        # {query, found, more, chapters, unreleased}: the search
    ideas.chronicle_goal {idea}         # a goal as it was (realm/chronicle.py `goal`) and its `quality` record (`ideas.quality`; None when it fails)
    ideas.chronicle_decision {number}   # {number, title, day, entry, changes, changed_by, goal}
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from orkboard.gui.ideas_args import IdeasError, _text
from orkboard.realm import chronicle, chronicle_find

GONE = "That chapter is gone"
NO_DECISION = "That decision is not in the log"


class ChronicleMixin:
    """Needs `host`, `state_dir`, `root()`, `keeper` and `quality()` (gui/ideas.py, gui/ideas_findings.py)."""

    def _chronicle_args(self) -> tuple[Path, Path, Path, Any]:
        return self.state_dir, Path(self.root(make=False)), Path(self.host.repo_root), self.keeper._log_text()

    def chronicle(self, args: dict) -> dict:
        state, pages, repo, log = self._chronicle_args()
        got = chronicle.read(state, pages, repo, log)
        chapters = [{**c, "open": n == 0} if n == 0 else {"id": c["id"], "kind": c["kind"], "name": c["name"], "day": c["day"], "open": False}
                    for n, c in enumerate(got["chapters"])]
        return {"kind": got["kind"], "earlier": chronicle.earlier(state, pages, repo), "chapters": chapters, "unreleased": got["unreleased"]}

    def chronicle_line(self, args: dict) -> dict:
        state, pages, repo, _log = self._chronicle_args()
        return {"earlier": chronicle.earlier(state, pages, repo)}

    def chronicle_chapter(self, args: dict) -> dict:
        want = _text(args, "id", 40)
        state, pages, repo, log = self._chronicle_args()
        got = next((c for c in chronicle.read(state, pages, repo, log)["chapters"] if c["id"] == want), None)
        if got is None:
            raise IdeasError(GONE)
        return {**got, "open": True}

    def chronicle_find(self, args: dict) -> dict:
        state, pages, repo, log = self._chronicle_args()
        return chronicle_find.find(state, pages, repo, log, args.get("query"))

    def chronicle_goal(self, args: dict) -> dict:
        slug = _text(args, "idea", 100)
        state, pages, repo, log = self._chronicle_args()
        try:
            got = chronicle.goal(state, pages, repo, log, slug)
        except ValueError as e:
            raise IdeasError(str(e)) from None
        try:
            quality = self.quality({"idea": slug})
        except Exception:
            quality = None
        return {**got, "quality": quality}

    def chronicle_decision(self, args: dict) -> dict:
        number = args.get("number")
        state, pages, _repo, log = self._chronicle_args()
        got = chronicle.decision(state, pages, log, number) if isinstance(number, int) and not isinstance(number, bool) else None
        if got is None:
            raise IdeasError(NO_DECISION)
        return got


def chronicle_commands(c: Any) -> dict:
    """The chronicle's reads by name (`gui/ideas.py` adds them to its table: `**chronicle_commands(self)`)."""
    return {"ideas.chronicle": c.chronicle, "ideas.chronicle_line": c.chronicle_line, "ideas.chronicle_chapter": c.chronicle_chapter, "ideas.chronicle_find": c.chronicle_find,
            "ideas.chronicle_goal": c.chronicle_goal, "ideas.chronicle_decision": c.chronicle_decision}
