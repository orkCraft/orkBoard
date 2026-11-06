"""Settings' line for the Board's rules (spec 151 C.4–C.5, decisions §255.5): *Let any AI tool work the Board*, under spec 137 E's *Keep the Board in the repository*.

    agent_rules_switch.commands(host)    # rules.switch (what Settings shows) · rules.write (the yes) · rules.not_now
    host.agent_rules.start()             # at the host's start: a project that has the rules gets the package's text where it differs (C.5)

**Written only by the person's yes.** *Write the rules* writes `realm/agent_rules.py`'s files into the Board's tree and commits them with the Board's pages in one commit, `board: the Board's rules
(schema 1)`, as a decision is committed (`BoardTree.flush(files=…)`): Board-authored, so `idea_gate.without_board_pages` carries it into main with the next goal. *Not now* is remembered in
`<state_dir>/rules_asked.json` and the line stays, with *Write the rules* alone. Once written the line says so. At the host's start, a project that has the rules and whose package text differs gets
only Orkboard's blocks and files written again; one changed by hand is written back and said once (a toast, and this line for the run).

**A public repository is refused** until spec 151 F asks its question (decisions §255.10): the rules would let the journals and the brief go to the work
branch (part B), and nothing of the Board goes into a public repository's code without the person's yes to that.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any, Callable

from orkboard.realm import agent_rules, agent_rules_text, board_branch, event_log, lexicon

ASKED_FILE = "rules_asked.json"
LABEL = "Let any AI tool work the Board"
LINE = ("Writes the Board's rules into AGENTS.md and CLAUDE.md, so Claude Code, Codex, Cursor and others take your goals, hold Talk, write specs and run the gate as Orkboard does, "
        "and stop to ask you what is yours to decide.")
WRITE = "Write the rules"
NOT_NOW = "Not now"
ON_LINE = "{rules} are in this project (schema {schema}): AGENTS.md, CLAUDE.md, the Board's folder, and Claude Code's roles and skill. Your own rules in those files win over them."
NO_TREE = "The Board's rules go into a project with git history; this one has none."
PUBLIC_WAIT = ("This repository is public: your goals, their specs and the leaders' words would be public too. "
               "Orkboard asks you about that first, in a later version.")
HELD_LINE = "The Board's rules are written in the Board's tree; your work branch takes them when its files are clean: {why}"


def message() -> str:
    """The Board commit's words: `board: the Board's rules (schema 1)`."""
    return f"board: {lexicon.term('board_rules')} (schema {agent_rules_text.SCHEMA})"


def _public(root: Path) -> bool:
    """Whether GitHub says the project's remote is public (an anonymous check, as the Board's branch makes it: spec 137 A.1)."""
    ok, _line = board_branch.private_check(Path(root), board_branch.read_config(Path(root)) or board_branch.BoardConfig())
    return not ok


def _sentence(text: str) -> str:
    return text[:1].upper() + text[1:]


def _has(p) -> bool:
    """The project has the rules: in its working copy, or in the Board's tree where the work branch has not taken them yet."""
    return agent_rules.has_rules(p.root) or agent_rules.has_rules(Path(p.ideas.state_dir) / "board")


def _asked(state_dir: Path) -> bool:
    try:
        data = json.loads((Path(state_dir) / ASKED_FILE).read_text(encoding="utf-8"))
        return isinstance(data, dict) and data.get("answer") == "no"
    except (OSError, ValueError):
        return False


def _remember(state_dir: Path, answer: str) -> None:
    Path(state_dir).mkdir(parents=True, exist_ok=True)
    (Path(state_dir) / ASKED_FILE).write_text(json.dumps({"answer": answer, "at": dt.datetime.now().isoformat(timespec="seconds")}), encoding="utf-8")


class AgentRules:
    def __init__(self, host: Any) -> None:
        self.host = host
        self.said: dict[str, list[str]] = {}                     # a project's lines of what was written back this run (shown once more in the line; the toast was the first)

    def commands(self) -> dict[str, Callable[[dict], Any]]:
        return {"rules.switch": lambda a: self.switch(), "rules.write": lambda a: self.write(), "rules.not_now": lambda a: self.not_now()}

    def _project(self):
        p = self.host.project
        if p is None:
            raise ValueError("No project is open")
        return p

    @staticmethod
    def _tree(p):
        """The Board's tree where it stands (made when missing); None for the demo and a folder with no git history."""
        ideas = getattr(p, "ideas", None)
        return ideas._decision_tree() if ideas is not None and hasattr(ideas, "_decision_tree") else None

    @staticmethod
    def _chosen(p) -> str:
        keeper = getattr(getattr(p, "ideas", None), "keeper", None)
        try:
            return keeper._chosen() if keeper is not None else ""
        except Exception:
            return ""

    def _wiki(self, p, tree) -> str:
        return str(getattr(tree, "wiki_rel", "") or "")

    def switch(self) -> dict:
        """`{show, on, asked, label, line, write, not_now, status, said}` for the shown project. Shown for a project with git history; nothing is written by reading it."""
        p = self.host.project
        out: dict = {"show": False, "on": False, "asked": False, "label": LABEL, "line": LINE, "write": WRITE, "not_now": NOT_NOW, "status": "", "said": []}
        if p is None or getattr(self.host, "demo", False) or not (Path(p.root) / ".git").exists():
            return out
        out.update(show=True, asked=_asked(Path(p.ideas.state_dir)), said=list(self.said.get(str(p.root), [])))
        if _has(p):
            out.update(on=True, status=ON_LINE.format(rules=_sentence(lexicon.term("board_rules")), schema=agent_rules_text.SCHEMA))
        return out

    def write(self) -> dict:
        """The person's yes: the files written into the Board's tree and committed in one Board commit. ValueError in plain words where it cannot be."""
        p = self._project()
        if _public(p.root):
            raise ValueError(PUBLIC_WAIT)
        tree = self._tree(p)
        if tree is None:
            raise ValueError(NO_TREE)
        written, out = self._commit(p, tree, lambda base: agent_rules.write(base, self._wiki(p, tree), decisions=agent_rules.decisions_of(base, self._chosen(p))))
        _remember(Path(p.ideas.state_dir), "yes")
        return {"ok": True, "written": written, "commit": out.get("commit") or "", "line": HELD_LINE.format(why=out["held"]) if out.get("held") else ""}

    def _commit(self, p, tree, make: Callable[[Path], list[str]]) -> tuple[list[str], dict]:
        """`make(tree path)` writes the files into the Board's tree under the repository's lock; the paths written are committed with the Board's pages and the work branch moved."""
        try:
            with tree.git.lock:
                tree.follow()
                written = make(tree.path)
                out = tree.flush(force=True, message=message(), files=tuple(written)) if written else {}
        except (OSError, RuntimeError, ValueError) as e:
            raise ValueError(f"The Board's rules could not be written: {' '.join(str(e).split())[:200]}") from None
        out = out or {}
        try:
            if out.get("commit"):
                p.ideas._ev(event_log.BOARD_COMMITTED, commit=out["commit"], pages=out.get("pages") or 0, what="rules", seconds=None)
            if out.get("held"):
                p.ideas._ev(event_log.BOARD_HELD, why=out["held"])
        except Exception:                                         # a log never stops the Board
            pass
        return written, out

    def not_now(self) -> dict:
        _remember(Path(self._project().ideas.state_dir), "no")
        return {"ok": True}

    def start(self) -> None:
        """At the host's start (C.5): each open project that has the rules gets the package's text where it differs, only Orkboard's blocks and files, in one Board commit; a block or file changed by
        hand is written back and said once. Never raises: a Board that cannot be written troubles no start."""
        for p in list(getattr(getattr(self.host, "projects", None), "open_ones", None) or []):
            try:
                if getattr(self.host, "demo", False) or not _has(p):
                    continue
                tree = self._tree(p)
                if tree is None:
                    continue
                lines: list[str] = []

                def make(base: Path) -> list[str]:
                    got = agent_rules.refresh(base, self._wiki(p, tree), decisions=agent_rules.decisions_of(base, self._chosen(p)))
                    lines.extend(got["by_hand"])
                    return got["written"]

                self._commit(p, tree, make)
                if lines:
                    self.said[str(p.root)] = lines
                    for line in lines:
                        p.toast(line, title="The Board", severity="warning")
            except Exception:
                continue


def commands(host: Any) -> dict[str, Callable[[dict], Any]]:
    host.agent_rules = AgentRules(host)
    return host.agent_rules.commands()
