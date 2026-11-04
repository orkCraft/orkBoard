"""The first open, in the Orkmaster's order (docs/specs/130-the-first-open-is-the-orkmasters.md part A; decisions §232.1, §232.3, §232.8): which
question the Orkmaster asks now, and whether the table is laid. Pure reads of the project's folder and its state; the only write is `lay`. No model, no face.

    first_open.laid(state_dir, root)            # True once the project's first Start was pressed, or when it has parties of its own already
    first_open.lay(state_dir)                   # kept in `<state_dir>/project.json` (`laid`); True when it was not laid before
    first_open.step(open=…, git=…, …)           # "project" · "git" · "kind" · "tools" · "parties" · "laid": the question asked now
    first_open.line(step, name, kind_words)     # the Orkmaster's line in its bubble for a step ("" for `laid`)

**A table is laid at Start.** Until the project's first Start the window is in its frame but not laid (§232.1); a project that has parties of its
own (made by Orkline or an earlier Orkboard) is laid at once. `laid` is the project's, so it lives with the project's other facts and travels with the
Board's branch (realm/board_branch.py `TOP_FILES`).
"""
from __future__ import annotations

from pathlib import Path

from orkboard.realm import ideas

FILE = "project.json"
STEPS = ("project", "git", "kind", "tools", "parties", "laid")


def _path(state_dir: Path) -> Path:
    return Path(state_dir) / FILE


def kept(state_dir: Path) -> bool:
    """Start was pressed in this project (`laid` of `<state_dir>/project.json`)."""
    return (ideas._json(_path(state_dir)) or {}).get("laid") is True


def laid(state_dir: Path, root: Path) -> bool:
    """The table is laid: Start was pressed, or the project already has a party of its own (a page in its parties' folder but General's). A folder that cannot be read is not laid."""
    if kept(state_dir):
        return True
    try:
        return any(t["slug"] != ideas.GENERAL for t in ideas.tracks(Path(root), make=False))      # General is written when a goal is first added: it is no party of the person's
    except OSError:
        return False


def lay(state_dir: Path) -> bool:
    """Kept in `<state_dir>/project.json`, the file's other keys left as they are. True when the table was not laid before (the page plays the laying once)."""
    with ideas.LOCK:
        data = ideas._json(_path(state_dir)) or {}
        if data.get("laid") is True:
            return False
        ideas._write_json(_path(state_dir), {**data, "laid": True})
    return True


def step(*, open: bool, git: bool, kind_kept: bool, hand: int, tools_skipped: bool, laid: bool) -> str:
    """The question asked now (§232.8): the project (no folder open), git (a folder with none), what it is (its kind not answered yet), the AI tools (**only
    when the hand is empty**: the tools are this computer's, the second project skips it, and closing the card with none added goes on), the parties' card; `laid`
    once Start was pressed, or at once for a project with parties of its own: nothing is asked."""
    if not open:
        return "project"
    if laid:
        return "laid"
    if not git:
        return "git"
    if not kind_kept:
        return "kind"
    if hand == 0 and not tools_skipped:
        return "tools"
    return "parties"


def line(at: str, name: str = "", kind_words: str = "") -> str:
    """The Orkmaster's line in its bubble for a step; the answers are cards in the hand (no answer is typed that a press could give)."""
    if at == "project":
        return "Which project shall we work on?"
    if at == "git":
        return f"No git in {name} yet. Start git here?"
    if at == "kind":
        return f"{name} is {kind_words}. Right?" if kind_words else f"What is {name} for?"
    if at == "tools":
        return "Which AI tool shall the orks think with?"
    if at == "parties":
        return "Who shall work on it? The parties are on the table."
    return ""
