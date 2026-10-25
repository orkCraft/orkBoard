"""Orkboard in an editor (vscode/, the VS Code extension): `orkboard --serve <folder>` serves the page with no window
of its own, says where it is on stdout and lives as long as the editor keeps its stdin open.

    $ orkboard --serve ~/code/app
    {"url": "http://127.0.0.1:52011/?t=…&app=1", "origin": "http://127.0.0.1:52011", "version": "0.4.2"}

The editor shows `url` in a panel (an iframe: its origin is the server's, so the socket takes it, gui/server.py).
`app=1` tells the page it is not in a browser of its own: a web link goes to the host, which opens the person's
browser (board_host `open_link`), and the page's own right-click menu is shown.
"""
from __future__ import annotations

import json
import sys
import threading
from typing import Any, Callable

from orkboard import __version__


def serve(host: Any, server: Any, thread: Any, close: Callable[[Any, Any, Callable[[], None]], None],
          stop: Callable[[], None] = lambda: None, stdin: Any = None, out: Any = None) -> None:
    """`orkboard --serve`, for an editor's extension: no window and no browser. The page's address goes out as one line
    of JSON on stdout (`url`, `origin`, `version`), the editor shows it in a panel of its own, and Orkboard stops when
    stdin closes (the editor went away) or on Ctrl+C; `close` stops the server (board_host `_stop`). An update restarts
    the process in place (core/updates.py `restart`), so the editor reads a new line with the new address."""
    stdin = sys.stdin if stdin is None else stdin
    out = sys.stdout if out is None else out
    host.updates.quit = server.stop
    url = server.url + ("&" if "?" in server.url else "?") + "app=1"      # as the app's window: it opens no tab
    out.write(json.dumps({"url": url, "origin": server.origin, "version": __version__}) + "\n")
    out.flush()

    def watch() -> None:
        for _ in stdin:
            pass
        server.stop()
    threading.Thread(target=watch, name="orkcraft-stdin", daemon=True).start()
    try:
        thread.join()
    except KeyboardInterrupt:
        pass
    finally:
        close(server, thread, stop)
