"""Settings' switch for the Board's branch (spec 137 E, decisions §244.1, §244.11, §244.14).

    board_switch.commands(host)      # board.switch (what Settings shows) · board.turn_on · board.not_now (the desktop's Settings; not a phone's)

**Written only by the person's yes.** *Turn it on* asks `board_branch.private_check` (a public GitHub repository is refused in words, a
remote not on GitHub goes on with the line that it must be private), then writes `[board]` into `orkcraft.toml` (`board_branch.turn_on`);
the host's tick (gui/board_sync.py) takes it from there. *Not now* is remembered in `<state_dir>/board_asked.json` and the switch stays in
Settings, with *Turn it on* alone. Once on, the switch says so, and says in words when a cloud run or another computer holds the Board or
when changes were kept aside (`board_sync.status`).

The cloud run's own settings (which secret pays, the schedule, its ceiling) are spec 137 D's and are not here.
"""
from __future__ import annotations

import datetime as dt
import json
import subprocess
from pathlib import Path
from typing import Any, Callable

from orkboard.gui import board_sync
from orkboard.realm import board_branch, board_lease, plumbing

ASKED_FILE = "board_asked.json"
LABEL = "Keep the Board in the repository"
LINE = ("Its pages and its state go to a branch of their own, orkboard/board. Secrets, sign-ins and logs stay on this computer. "
        "The repository must be private.")
ON_LINE = "The Board is kept on {branch} on {remote}."

http_status: Callable[[str], int] = board_branch.http_status       # tests put a fake here


def _asked(state_dir: Path) -> bool:
    try:
        data = json.loads((Path(state_dir) / ASKED_FILE).read_text(encoding="utf-8"))
        return isinstance(data, dict) and data.get("answer") == "no"
    except (OSError, ValueError):
        return False


def _remember(state_dir: Path, answer: str) -> None:
    Path(state_dir).mkdir(parents=True, exist_ok=True)
    (Path(state_dir) / ASKED_FILE).write_text(json.dumps({"answer": answer, "at": dt.datetime.now().isoformat(timespec="seconds")}), encoding="utf-8")


def has_remote(root: Path, remote: str = "origin", run: Callable = subprocess.run) -> bool:
    try:
        plumbing.git(root, run, plumbing.env(), "remote", "get-url", remote)
        return True
    except Exception:
        return False


def _clock(iso: str) -> str:
    try:
        return dt.datetime.fromisoformat(iso).astimezone().strftime("%H:%M")
    except (ValueError, TypeError):
        return "the last push"


class BoardSwitch:
    def __init__(self, host: Any) -> None:
        self.host = host

    def commands(self) -> dict[str, Callable[[dict], Any]]:
        return {"board.switch": lambda a: self.switch(), "board.turn_on": lambda a: self.turn_on(), "board.not_now": lambda a: self.not_now()}

    def _project(self):
        p = self.host.project
        if p is None:
            raise ValueError("No project is open")
        return p

    def switch(self) -> dict:
        """`{show, on, asked, label, line, status, held, aside}` for the shown project. Nothing is shown with no project or no remote to keep it on."""
        p = self.host.project
        out: dict = {"show": False, "on": False, "asked": False, "label": LABEL, "line": LINE, "status": "", "held": "", "aside": ""}
        if p is None:
            return out
        config = board_branch.read_config(p.root)
        if config is not None:
            out.update(show=True, on=True, status=ON_LINE.format(branch=config.branch, remote=config.remote))
            sync = getattr(self.host, "board_sync", None)
            seen = sync.status(p) if sync is not None else {}
            held = seen.get("board_held")
            if held:
                out["held"] = board_sync.CLOUD_HELD if held.get("kind") == board_lease.CLOUD_RUN else board_sync.COMPUTER_HELD
            aside = seen.get("board_aside")
            if aside:
                out["aside"] = board_sync.ASIDE_LINE.format(since=_clock(str(aside.get("since") or "")))
            return out
        if has_remote(p.root):
            out.update(show=True, asked=_asked(Path(p.ideas.state_dir)))
        return out

    def turn_on(self) -> dict:
        p = self._project()
        config = board_branch.BoardConfig()
        if board_branch.read_config(p.root) is not None:
            return {"ok": True, "line": ""}
        ok, line = board_branch.private_check(p.root, config, http_status)
        if not ok:
            raise ValueError(line)
        try:
            config = board_branch.turn_on(p.root, config)
        except OSError as e:
            raise ValueError(f"orkcraft.toml could not be written: {e}") from None
        _remember(Path(p.ideas.state_dir), "yes")
        return {"ok": True, "remote": config.remote, "branch": config.branch, "line": line}

    def not_now(self) -> dict:
        _remember(Path(self._project().ideas.state_dir), "no")
        return {"ok": True}


def commands(host: Any) -> dict[str, Callable[[dict], Any]]:
    host.board_switch = BoardSwitch(host)
    return host.board_switch.commands()
