"""What the person was refused and what they were shown red, in the event log (spec 107 §2.1, §2.2): `command_refused` for each
command reply with `ok: false` (the page's: gui/server.py, a phone's: gui/phones.py) and `error_shown` for each toast of severity
`error`. The shown project's log (`host.repo_root`); none with no project open, and none in the demo. A command's arguments are never
written, only its name and what was said back.

    command_log.refused(host, "ideas.add", "Say what the goal is", "desktop")          # kind "refused": the host said no
    command_log.refused(host, "ideas.add", "KeyError: 'x'", "phone", broken=True)      # kind "broken": it raised
    command_log.error_shown(root, "Town clock", "KeyError: 'x'")
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from orkboard.realm import event_log

SILENT = ("logs.", "crash.")            # saving the logs and reporting a crash are not what a day is read for
NAME_MAX = 80


def refused(host: Any, name: str, error: str, device: str = "desktop", broken: bool = False) -> None:
    if name.startswith(SILENT) or name == "watch" or getattr(host, "demo", False):
        return
    root = getattr(host, "repo_root", None)
    if root is not None:
        event_log.record(Path(root), event_log.COMMAND_REFUSED, command=name[:NAME_MAX], error=error, device=device,
                         kind="broken" if broken else "refused")


def error_shown(root: Path | None, title: str, text: str) -> None:
    if root is not None:
        event_log.record(Path(root), event_log.ERROR_SHOWN, title=title, text=text)
