"""Save logs (the owner's notes of 19 October): an error's **Save logs** and the gear's day logs are written to the
Downloads folder, since the app's window downloads nothing a link gives it; the page then says where and shows it.

The zip is the Board's analytics zip of the shown project (`BoardLogs.pack_period`: every model call of the day with
what went in and came out, the event log, the ideas' state and plans) and beside it `about.json` (realm/diagnostics.py:
where Orkboard runs and its build, each AI tool as it finds it, the project's gate and installs), `on-screen.txt` (the words
the person saved it from), `page.json` (what the page said of itself, spec 107 §2.4), `crashes/` (the crash files of the
period) and `app.log`: the end of the Mac app's own log, else of the server's (gui/server_log.py). Desktop only: a phone
saves nothing on the computer (gui/board_host.py `BoardPhone`).

    logs.save {"days"?, "said"?, "page"?}  → {"path", "name", "folder"}
    logs.show {"path"}            → the file shown in Finder (or the folder opened); only a zip saved here
"""
from __future__ import annotations

import datetime as dt
import io
import json
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any, Callable

from orkboard.core import crashes
from orkboard.gui import server_log
from orkboard.realm import diagnostics
from orkboard import brand

PREFIX = "orkboard-logs-"
SAID_CHARS = 20_000
APP_LOG = Path("~/Library/Logs/Orkboard.log")       # the Mac app's output (gui/mac_app.py)
APP_LOG_TAIL = 256 * 1024
CRASHES_MAX = 2 * 1024 * 1024               # the crash files of a period, in all
PAGE_TEXT = 600                             # a word of the page (an error, a tab's name) is cut at this


class LogsError(RuntimeError):
    """What the page says when the logs cannot be saved or shown."""


def folder(home: Path | None = None) -> Path:
    """Where logs are saved: the Downloads folder, else the home folder."""
    home = Path.home() if home is None else Path(home)
    downloads = home / "Downloads"
    return downloads if downloads.is_dir() else home


def crash_files(days: int = 1, today: dt.date | None = None, limit: int = CRASHES_MAX) -> list[tuple[str, bytes]]:
    """The crash files (`core/crashes.log_dir()`) written in the last `days` days, newest first, `limit` bytes in all (the one that
    passes it is cut, the older ones are left out)."""
    since = dt.datetime.combine((today or dt.date.today()) - dt.timedelta(days=max(1, days) - 1), dt.time()).timestamp()
    try:
        found = sorted((p for p in crashes.log_dir().glob("crash-*.txt") if p.stat().st_mtime >= since),
                       key=lambda p: p.stat().st_mtime, reverse=True)
    except OSError:
        return []
    out: list[tuple[str, bytes]] = []
    for p in found:
        try:
            data = p.read_bytes()[:limit]
        except OSError:
            continue
        out.append((p.name, data))
        limit -= len(data)
        if limit <= 0:
            break
    return out


def page_of(page: Any) -> dict:
    """What the page said of itself with `logs.save`, as plain data: the window's size and pixel ratio, the face, the open tab, what
    lies over the pane, the System's lens and its last errors. Anything else it sent is left out; {} when it said nothing."""
    if not isinstance(page, dict):
        return {}
    num = lambda v: v if isinstance(v, (int, float)) and not isinstance(v, bool) else None
    text = lambda v: v[:PAGE_TEXT] if isinstance(v, str) else ""
    errors = page.get("errors")
    return {"w": num(page.get("w")), "h": num(page.get("h")), "dpr": num(page.get("dpr")), "face": text(page.get("face")),
            "tab": text(page.get("tab")), "over": text(page.get("over")), "lens": text(page.get("lens")),
            "errors": [text(e) for e in errors[-20:] if isinstance(e, str)] if isinstance(errors, list) else []}


def pack(host: Any, days: int = 1, said: str = "", about: dict | None = None, page: Any = None) -> bytes:
    """The shown project's analytics zip (an empty one when nothing is kept yet) with about.json, on-screen.txt, page.json, the
    period's crash files and the end of the app's log (else of the server's)."""
    packed = host.day_logs.pack_period(days)
    buf = io.BytesIO(packed[1] if packed else b"")
    with zipfile.ZipFile(buf, "a" if packed else "w", zipfile.ZIP_DEFLATED) as z:
        if not packed:
            z.writestr("README.md", f"# {brand.name()}'s logs\n\nNo model call is kept for this project yet: `about.json` "
                                    f"says where {brand.name()} runs, its build, how it finds each AI tool and the project's gate; "
                                    f"`crashes/`, `app.log` and `page.json` say what broke.\n")
        info = about if about is not None else diagnostics.about(getattr(host, "machine", None), root=getattr(host, "repo_root", None))
        z.writestr("about.json", json.dumps(info, ensure_ascii=False, indent=1))
        if said.strip():
            z.writestr("on-screen.txt", said.strip()[:SAID_CHARS] + "\n")
        if seen := page_of(page):
            z.writestr("page.json", json.dumps(seen, ensure_ascii=False, indent=1))
        for name, data in crash_files(days):
            z.writestr(f"crashes/{name}", data)
        log = APP_LOG.expanduser()
        if log.is_file():
            with log.open("rb") as f:
                f.seek(max(0, log.stat().st_size - APP_LOG_TAIL))
                z.writestr("app.log", f.read())
        elif own := server_log.tail(APP_LOG_TAIL):
            z.writestr("app.log", own)
    return buf.getvalue()


def save(host: Any, days: int = 1, said: str = "", where: Path | None = None, now: dt.datetime | None = None,
         about: dict | None = None, page: Any = None) -> dict:
    """The zip written to `where` (the Downloads folder): {"path", "name", "folder"}."""
    where = folder() if where is None else Path(where)
    now = now or dt.datetime.now()
    name = f"{PREFIX}{now.strftime('%Y-%m-%d-%H%M%S')}.zip"
    path = where / name
    try:
        path.write_bytes(pack(host, days, said, about, page))
    except OSError as e:
        raise LogsError(f"The logs could not be saved in {where}: {e.strerror or e}") from None
    return {"path": str(path), "name": name, "folder": str(where)}


def reveal_cmd(path: Path, platform: str = sys.platform) -> list[str]:
    """The system's way to show a file: Finder with it selected, Explorer, else its folder opened."""
    if platform == "darwin":
        return ["open", "-R", str(path)]
    if platform.startswith("win"):
        return ["explorer", f"/select,{path}"]
    return ["xdg-open", str(path.parent)]


def show(path: str, where: Path | None = None, start: Callable[..., Any] = subprocess.Popen) -> dict:
    """A zip saved here, shown in the system's file manager; nothing else is ever opened."""
    where = folder() if where is None else Path(where)
    p = Path(path)
    if p.parent != where or not p.name.startswith(PREFIX) or p.suffix != ".zip" or not p.is_file():
        raise LogsError(f"Only logs saved by {brand.name()} are shown")
    try:
        start(reveal_cmd(p), stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
              start_new_session=True)
    except OSError as e:
        raise LogsError(f"It could not be shown: {e.strerror or e}") from None
    return {"ok": True}


def commands(host: Any) -> dict[str, Callable[[dict], Any]]:
    def save_cmd(args: dict) -> dict:
        days = args.get("days")
        said = args.get("said")
        try:
            return save(host, days if isinstance(days, int) and not isinstance(days, bool) and 0 < days <= 30 else 1,
                        said if isinstance(said, str) else "", page=args.get("page"))
        except LogsError as e:
            return {"error": str(e)}

    def show_cmd(args: dict) -> dict:
        try:
            return show(str(args.get("path") or ""))
        except LogsError as e:
            return {"error": str(e)}

    return {"logs.save": save_cmd, "logs.show": show_cmd}
