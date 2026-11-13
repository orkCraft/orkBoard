"""The first open, in the Orkmaster's order (docs/specs/130-the-first-open-is-the-orkmasters.md part A; decisions §232.1, §232.3, §232.8): which
question the Orkmaster asks now, and whether the table is laid. Pure reads of the project's folder and its state; the only write is `lay`. No model, no face.

    first_open.laid(state_dir, root)            # True once the project's first Start was pressed, or when it has parties of its own already
    first_open.lay(state_dir)                   # kept in `<state_dir>/project.json` (`laid`); True when it was not laid before
    first_open.step(open=…, git=…, …)           # "tools" · "project" · "git" · "kind" · "parties" · "laid": the question asked now
    first_open.line(step, name, kind_words)     # the Orkmaster's line in its bubble for a step ("" for `laid`)
    first_open.release_branch(state_dir, branches, default)   # the project's main for the portal: the one kept, else the git default (spec 150 G.2.2)
    first_open.keep_release_branch(state_dir, name)           # kept in `<state_dir>/project.json` (`main_branch`); "" forgets it, the git default is read again

**A table is laid at Start.** Until the project's first Start the window is in its frame but not laid (§232.1); a project that has parties of its
own (made by an earlier version) is laid at once. `laid` is the project's, so it lives with the project's other facts and travels with the
Board's branch (realm/board_branch.py `TOP_FILES`).
"""
from __future__ import annotations

from pathlib import Path

from orkboard.realm import ideas

FILE = "project.json"
STEPS = ("tools", "project", "git", "kind", "parties", "laid")


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


def kept_branch(state_dir: Path) -> str:
    """The release branch the person kept for the project (`main_branch` of `<state_dir>/project.json`), "" when none."""
    got = (ideas._json(_path(state_dir)) or {}).get("main_branch")
    return got if isinstance(got, str) else ""


def release_branch(state_dir: Path, branches: list[str], default: str = "") -> str:
    """The project's main as the portal and the gate read it (spec 150 G.2.2, decisions §254.8): the kept branch while it is still a local branch, else `default`
    (git's own default: origin's HEAD, `main`, `master`, the one checked out)."""
    kept = kept_branch(state_dir)
    return kept if kept and kept in branches else default


def keep_release_branch(state_dir: Path, name: str) -> str:
    """Kept in `<state_dir>/project.json`, the file's other keys left as they are; "" forgets it. Returns what is kept."""
    name = name.strip()
    with ideas.LOCK:
        data = ideas._json(_path(state_dir)) or {}
        data = {k: v for k, v in data.items() if k != "main_branch"}
        if name:
            data["main_branch"] = name
        ideas._write_json(_path(state_dir), data)
    return name


def step(*, open: bool, git: bool, kind_kept: bool, hand: int, tools_skipped: bool, laid: bool) -> str:
    """The question asked now (§232.8, spec 150 G): the AI tools first (**only when the hand is empty**: the tools are this computer's, they need no project, the
    second project skips it, and closing the card with none added goes on), then the project (no folder open), git (a folder with none), what it is (its kind not
    answered yet), the parties' card; `laid` once Start was pressed, or at once for a project with parties of its own: nothing is asked."""
    if open and laid:
        return "laid"
    if hand == 0 and not tools_skipped:
        return "tools"
    if not open:
        return "project"
    if not git:
        return "git"
    if not kind_kept:
        return "kind"
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
