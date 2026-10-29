"""The server's own log (spec 107 §2.4, the owner's day of 29 October: a launch from a terminal keeps no log, so the zip had no
`app.log`): `~/.orkcraft/logs/<product>.log`, a rotating `logging` file (1 MB, three files) of the warnings and errors the
process logs and of what the server caught (`Server.capture`, with its traceback). Saved logs take its end when the Mac app
has no log of its own (gui/logs_save.py).

    server_log.install()        # when the GUI server starts, on any launch (board_host `run`); not in a test, not in the demo
    server_log.tail(256_000)    # its last bytes, across the rotated files, oldest first

Nothing here is the person's: a record is a logger's message, never a prompt or a project's file.
"""
from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path

MAX_BYTES = 1_000_000
BACKUPS = 2                                  # the log and two before it: 3 MB at most
FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
_added: list[logging.Handler] = []          # what `install` put on the root logger


def path(product: str = "") -> Path:
    """`~/.orkcraft/logs/<product>.log`; the product is the running one's (the orkGet profile) unless named."""
    if not product:
        from orkboard.orkget import profile
        try:
            product = profile.current().product
        except RuntimeError:
            product = "orkboard"
    return Path.home() / ".orkcraft" / "logs" / f"{product}.log"


def install(demo: bool = False, product: str = "") -> Path | None:
    """Warnings and above go to the file from now on (and still to stderr, which the Mac app's own log keeps). The file it writes;
    None in the demo or when the folder cannot be made. Installing again replaces the handler, never adds a second."""
    uninstall()
    if demo:
        return None
    where = path(product)
    try:
        where.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.handlers.RotatingFileHandler(where, maxBytes=MAX_BYTES, backupCount=BACKUPS, encoding="utf-8", delay=True)
    except OSError:
        return None
    handler.setLevel(logging.WARNING)
    handler.setFormatter(logging.Formatter(FORMAT))
    root = logging.getLogger()
    if not root.handlers:                    # a handler of ours would stop the last-resort one printing warnings to stderr
        err = logging.StreamHandler(sys.stderr)
        err.setLevel(logging.WARNING)
        err.setFormatter(logging.Formatter(FORMAT))
        _added.append(err)
    _added.append(handler)
    for h in _added:
        root.addHandler(h)
    return where


def uninstall() -> None:
    root = logging.getLogger()
    while _added:
        h = _added.pop()
        root.removeHandler(h)
        h.close()


def tail(limit: int, product: str = "") -> bytes:
    """The log's last `limit` bytes, the rotated files before it (oldest first); b"" when there is none."""
    current = path(product)
    files = [current.with_name(f"{current.name}.{n}") for n in range(BACKUPS, 0, -1)] + [current]
    data = b""
    for f in files:
        try:
            data += f.read_bytes()[-limit:]
        except OSError:
            continue
    return data[-limit:]
