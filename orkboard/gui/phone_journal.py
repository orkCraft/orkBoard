"""The journal and the inbox, for a paired phone (spec 136 A.2, A.3, B; decisions §229, §243).

    phone_journal.commands(host)       # journal.phone_ask · journal.turn_on · journal.not_now (the desktop's Settings; not a phone's)
    phone_journal.tick(host)           # each open project with a `[journal]`: the inbox read and taken, the journal sent when due

**Asked once.** Settings' *Your phone* asks, once per project, whether to follow it from the phone away from home, when a
phone is paired, the project's `origin` is on github.com, it has no `[journal]` yet and the person has not answered before.
*Turn it on* writes `[journal]` with `inbox = "orkboard/inbox"` (realm/remote_journal.py `turn_on`); *Not now* is remembered in
`<state_dir>/journal_asked.json` and asks no more (Settings keep the switch).

**When.** `every` 15 minutes for a user; at once (`urgent`) when a card that needs the person came to the hand since the last
look, and the inbox's own taking sends the journal at once (realm/remote_inbox.py). One thread a project at a time; a journal
that cannot be sent, or an inbox that cannot be read, troubles no work.

**Laying a goal.** `lay` is `Ideas.add` as the + card calls it, with `via = "inbox"` and the `inbox_id` it came with, which the add
keeps in the goal's `state.json`; `find` reads the Board for a goal with that id, so one is never laid twice.
"""
from __future__ import annotations

import datetime as dt
import json
import socket
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Callable

from orkboard.realm import board_branch, goal_types, ideas, remote_inbox, remote_journal

ASKED_FILE = "journal_asked.json"
ASK_LINE = ("Follow this project from your phone away from home? Its status goes to a branch of its own on origin, "
            "orkboard/journal, and goals from your phone come through orkboard/inbox. No code and no prompts. "
            "The repository must be private.")
NEEDS_EVERY_S = 20                       # the hand's cards are looked at this often per project, for `urgent`
NOT_A_CARD = ("proposal", "party", "pitch", "project_q", "hypothesis", "quality", "finding")        # the snapshot's own count leaves these out of what needs the person


def _asked(state_dir: Path) -> str:
    try:
        data = json.loads((Path(state_dir) / ASKED_FILE).read_text(encoding="utf-8"))
        return str(data.get("answer") or "") if isinstance(data, dict) else ""
    except (OSError, ValueError):
        return ""


def _remember(state_dir: Path, answer: str) -> None:
    Path(state_dir).mkdir(parents=True, exist_ok=True)
    (Path(state_dir) / ASKED_FILE).write_text(json.dumps({"answer": answer, "at": dt.datetime.now().isoformat(timespec="seconds")}), encoding="utf-8")


def origin_on_github(root: Path, run: Callable = subprocess.run) -> bool:
    """`git remote get-url origin` names github.com."""
    try:
        done = run(["git", "remote", "get-url", "origin"], cwd=str(root), capture_output=True, timeout=20)
    except Exception:
        return False
    url = done.stdout.decode("utf-8", "replace") if isinstance(done.stdout, bytes) else str(done.stdout or "")
    return done.returncode == 0 and "github.com" in url.lower()


def paired() -> bool:
    from orkboard.gui.pairing import Pairing
    try:
        return bool(Pairing().devices())
    except Exception:
        return False


class PhoneJournal:
    def __init__(self, host: Any) -> None:
        self.host = host
        self._threads: dict[str, threading.Thread] = {}
        self._needs: dict[str, tuple[float, set[tuple[str, str]], frozenset[str]]] = {}     # path -> (looked at, the cards, the goals they are for)
        self._came: dict[str, float] = {}                 # path -> when (monotonic) a card for the person last came to the hand

    # -- A.2: asked for once ---------------------------------------------------------------------------------

    def commands(self) -> dict[str, Callable[[dict], Any]]:
        return {"journal.phone_ask": lambda a: self.ask(), "journal.turn_on": lambda a: self.turn_on(), "journal.not_now": lambda a: self.not_now()}

    def _project(self):
        p = self.host.project
        if p is None:
            raise ValueError("No project is open")
        return p

    def ask(self) -> dict:
        """`{ask: bool, line}`: whether Settings asks now, for the shown project."""
        p = self.host.project
        if p is None:
            return {"ask": False, "line": ASK_LINE}
        state = Path(p.ideas.state_dir)
        ask = (paired() and remote_journal.read_config(p.root) is None and not _asked(state) and origin_on_github(p.root))
        return {"ask": bool(ask), "line": ASK_LINE}

    def turn_on(self) -> dict:
        p = self._project()
        try:
            config = remote_journal.turn_on(p.root, "orkboard/inbox")
        except OSError as e:
            raise ValueError(f"orkcraft.toml could not be written: {e}") from None
        _remember(Path(p.ideas.state_dir), "yes")
        return {"ok": True, "remote": config.remote, "branch": config.branch, "inbox": config.inbox, "every": config.every}

    def not_now(self) -> dict:
        _remember(Path(self._project().ideas.state_dir), "no")
        return {"ok": True}

    # -- A.3 and B: the clock --------------------------------------------------------------------------------

    def _cards(self, p: Any, now: float) -> tuple[set[tuple[str, str]], frozenset[str], bool]:
        """The cards that wait for the person (goal, kind), the goals they are for, and whether one came since the last look."""
        before = self._needs.get(p.path)
        if before is not None and now - before[0] < NEEDS_EVERY_S:
            return before[1], before[2], False
        rows = p.ideas.board(make=False)["needs_you"]
        cards = {(str(n.get("idea") or ""), str(n.get("kind") or "")) for n in rows if n.get("idea") and n.get("kind") not in NOT_A_CARD}
        goals = frozenset(i for i, _ in cards)
        self._needs[p.path] = (now, cards, goals)
        new = before is not None and bool(cards - before[1])
        if new:
            self._came[p.path] = now
        return cards, goals, new

    def came_at(self, p: Any) -> float:
        """When (`time.monotonic()`) a card for the person last came to the hand of this project; 0.0 when none has since this host began. The
        Board's branch pushes at once on it (spec 137 B.2, `urgent`)."""
        try:
            self._cards(p, time.monotonic())
        except Exception:
            pass
        return self._came.get(p.path, 0.0)

    def lay(self, p: Any) -> Callable[[dict, str], str]:
        def lay(goal: dict, inbox_id: str) -> str:
            return str(p.ideas.add({**goal, "via": "inbox", "inbox_id": inbox_id})["slug"])
        return lay

    @staticmethod
    def find(p: Any) -> Callable[[str], str]:
        def find(inbox_id: str) -> str:
            folder = Path(p.ideas.state_dir) / "ideas"
            for d in sorted(folder.iterdir()) if folder.is_dir() else []:
                try:
                    if json.loads((d / "state.json").read_text(encoding="utf-8")).get("inbox_id") == inbox_id:
                        return d.name
                except (OSError, ValueError, AttributeError):
                    continue
            return ""
        return find

    def context(self, p: Any) -> remote_inbox.Context:
        root, state = p.ideas.root(False), Path(p.ideas.state_dir)
        parties = {t["slug"] for t in ideas.tracks(root, make=False)}
        return remote_inbox.Context(parties=parties, types=lambda party: {t.id for t, _ in goal_types.offered(state, root, party)})

    def holds_board(self, p: Any) -> bool:
        """Whether this computer may take the inbox's goals: with the Board's branch on (`[board]`), only its holder does (spec 137 B.2.4, decisions
        §244.4); with none, as before."""
        if board_branch.read_config(p.root) is None:
            return True
        sync = getattr(self.host, "board_sync", None)
        return bool(sync is not None and sync.holds(p))

    def run(self, p: Any, config: remote_journal.JournalConfig, now: dt.datetime, needs: frozenset[str], urgent: bool) -> None:
        """The inbox read and taken (when the project has one), then the journal sent when due (or `urgent`). Never raises."""
        try:
            state = Path(p.ideas.state_dir)
            pages = p.ideas.root(False)
            if config.inbox and self.holds_board(p):
                remote_inbox.take(p.root, state, config, self.context(p), self.lay(p), self.find(p), socket.gethostname(), now,
                                  pages=pages, needs=needs)
            if remote_journal.due(state, config, now, urgent):
                remote_journal.send(p.root, state, config, now, pages=pages, needs=needs)
        except Exception:
            pass

    def tick(self) -> None:
        try:
            now = dt.datetime.now()
            for p in list(getattr(self.host.projects, "open_ones", None) or []):
                t = self._threads.get(p.path)
                if t is not None and t.is_alive():
                    continue
                config = remote_journal.read_config(p.root)
                if config is None:
                    continue
                state = Path(p.ideas.state_dir)
                try:
                    _, needs, urgent = self._cards(p, time.monotonic())
                except Exception:
                    needs, urgent = frozenset(), False
                inbox_due = bool(config.inbox) and remote_inbox.due(state, now)
                if not (inbox_due or remote_journal.due(state, config, now, urgent)):
                    continue
                self._threads[p.path] = t = threading.Thread(target=self.run, args=(p, config, now, needs, urgent), daemon=True,
                                                             name="orkboard-journal")
                t.start()
        except Exception:                         # a journal that cannot be sent troubles no work
            pass


def commands(host: Any) -> dict[str, Callable[[dict], Any]]:
    host.phone_journal = PhoneJournal(host)
    return host.phone_journal.commands()


def tick(host: Any) -> None:
    pj = getattr(host, "phone_journal", None)
    if pj is not None:
        pj.tick()
