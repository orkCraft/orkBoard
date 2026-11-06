"""The host's look at whether the Board may be in the code (spec 151 F.3, decisions §255.10): the visibility asked once a day, a repository found public since
put off the branch at once.

    board_in_code_host.tick(host)      # each open project with a git history: one thread a project, never blocking the clock

At each tick (at most every `LOOK_S`, and GitHub only when the last answer is a day old: `realm/board_in_code.py`): the goals kept off put in the
repository's `info/exclude` (F.4); a tree on the wrong side of `goes` (the Board in the code that must be off, or off and the person said yes) flushed at
once, which is when the pages leave or enter the work branch (realm/board_tree_off.py). A repository that turned public with no `in_code` says so in a toast, once:
Orkboard's own pushes wait (`board_in_code.push_hold`), and the face reads `board_in_code.pending_question(root)` for the card. No face of its own.
"""
from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any

from orkboard.realm import board_in_code, board_tree_off

LOOK_S = 600             # the cache and the exclude file are looked at this often, at most (GitHub is asked once a day by `board_in_code.visibility`)
FOUND_PUBLIC = board_in_code.HELD


class _State:
    def __init__(self) -> None:
        self.next_look = 0.0
        self.thread: threading.Thread | None = None


class BoardInCodeHost:
    def __init__(self, host: Any) -> None:
        self.host = host
        self._states: dict[str, _State] = {}

    def tick(self) -> None:
        try:
            for p in list(getattr(self.host.projects, "open_ones", None) or []):
                if self.host.demo or not (Path(p.root) / ".git").exists():
                    continue
                st = self._states.setdefault(p.path, _State())
                if (st.thread is not None and st.thread.is_alive()) or time.monotonic() < st.next_look:
                    continue
                st.thread = threading.Thread(target=self.run, args=(p, st), daemon=True, name="orkboard-in-code")
                st.thread.start()
        except Exception:                         # a look that cannot be made troubles no work
            pass

    def run(self, p: Any, st: _State, get=None) -> dict:
        """One look at one project. Never raises. Answers `board_in_code.check`'s answer ({} when it could not be made)."""
        try:
            st.next_look = time.monotonic() + LOOK_S
            root, state = Path(p.root), Path(p.ideas.state_dir)
            got = board_in_code.check(root, state, get)
            tree = p.ideas._tree(p.ideas.wiki())
            if tree is not None and tree.exists():
                tree._keep_off()
                if board_tree_off.is_off(tree) == tree._goes():          # off and it may go in, or in and it must go off: one forced write does either
                    p.ideas.tree_flush(force=True)
            if got["found_public"]:
                try:
                    p.toast(FOUND_PUBLIC, title="The Board", severity="warning")
                except Exception:
                    pass
            if got["found_public"] or got["visibility"] != got["was"]:
                p.ideas._publish("")
            return got
        except Exception:
            return {}


def tick(host: Any) -> None:
    look = getattr(host, "board_in_code", None)
    if look is not None:
        look.tick()
