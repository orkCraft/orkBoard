"""The journal for a paired phone (spec 136 A.2, A.3; decisions §229, §243.8).

    phone_journal.commands(host)       # journal.phone_ask · journal.turn_on · journal.not_now (the desktop's Settings; not a phone's)
    phone_journal.tick(host)           # each open project with a `[journal]`: the journal sent when due, or at once

**Asked once.** Settings' *Your phone* asks, once per project, whether to follow it from the phone away from home, when a
phone is paired, the project's `origin` is on github.com, it has no `[journal]` yet and the person has not answered before.
*Turn it on* writes `[journal]` with `inbox = "orkboard/inbox"` (realm/remote_journal.py `turn_on`); *Not now* is remembered in
`<state_dir>/journal_asked.json` and asks no more (Settings keep the switch).

**When.** `every` 15 minutes for a user; at once (`urgent`) when a card that needs the person came to the hand since the last
look. One thread a project at a time; a journal
that cannot be sent troubles no work.

"""
from __future__ import annotations

import datetime as dt
import json
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Callable

from orkboard.realm import remote_journal

ASKED_FILE = "journal_asked.json"
ASK_LINE = ("Follow this project from your phone away from home? Its status goes to a branch of its own on origin, "
            "orkboard/journal, and goals from your phone come through orkboard/inbox. No code and no prompts. "
            "The repository must be private.")
NEEDS_EVERY_S = 20                       # the hand's cards are looked at this often per project, for `urgent`
NOT_A_CARD = ("proposal", "party", "pitch", "project_q", "hypothesis")        # the snapshot's own count leaves these out of what needs the person


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
        return cards, goals, before is not None and bool(cards - before[1])

    def run(self, p: Any, config: remote_journal.JournalConfig, now: dt.datetime, needs: frozenset[str], urgent: bool) -> None:
        """The journal sent when due (or `urgent`). Never raises."""
        try:
            state = Path(p.ideas.state_dir)
            pages = p.ideas.root(False)
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
                if not remote_journal.due(state, config, now, urgent):
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
