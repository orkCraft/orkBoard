"""Serve the page on mocks with no host (goal 170, stage M): the page's own files, orkUI's copy and the roles' sheet, at the
paths the host serves them (gui/server.py), and the page opened with `?mock=1` (js/mock/mocklink.js).

    uv run python tools/serve_mock.py [port]     # then open http://127.0.0.1:<port>/?mock=1

The phone's page too (goal 170, stage P), at the path the phone listener serves it (gui/pwa.py `PREFIX`): the app's own files,
the desktop's page as `/app/page/...` and orkUI as `/ds/orkui/`, so `http://127.0.0.1:<port>/app/?mock=1` is the phone's page
with no computer (open it at 390 x 844 with touch, or as a phone in the browser's tools). The recording is served there as
`/app/page/mock/`, which js/mock/mocklink.js reads beside its own folder; the phone listener never serves it.

A test serves the recording with what it presses laid in it: `serve(port, lay)` calls `lay(recording)` on a copy of
`static/mock/board.json` and serves that copy (tests/mock_kit.py has the lays); the recording on disk is never changed.
"""
import functools, http.server, json, mimetypes, sys
from pathlib import Path
from orkboard.design import tokens
from orkboard.gui import pwa, server

STATIC, SYSTEM = server.STATIC, tokens.SYSTEM


app_files, ds_files = functools.cache(pwa.files), functools.cache(pwa.ds_files)


class Page(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/static/mock/board.json", "/app/page/mock/board.json") and getattr(self.server, "recording", None) is not None:
            return self.send(None, self.server.recording, "application/json")
        if path in ("/", "/index.html"):
            return self.send(STATIC / "index.html")
        if path == "/roles.css":
            return self.send(None, tokens.roles_css().encode(), "text/css; charset=utf-8")
        if path.startswith("/app/page/mock/"):                              # the recording, for the phone's page (the listener does not serve it)
            f = (STATIC / "mock" / path[len("/app/page/mock/"):]).resolve()
            if f.is_file() and (STATIC / "mock").resolve() in f.parents:
                return self.send(f)
        if pwa.wants(path):
            return self.phone(path)
        for route, root in (("/static/", STATIC), ("/ds/", SYSTEM)):
            if path.startswith(route):
                f = (root / path[len(route):]).resolve()
                if f.is_file() and root.resolve() in f.parents:
                    return self.send(f)
        self.send_error(404)

    def phone(self, path):
        """The phone's page: its page and manifest as the listener serves them (CSP and all, `pwa.serve`); the rest, which that call
        would look up again among hundreds of files each time, from the maps made once."""
        under_ds = path.startswith(pwa.DS)
        name = path[len(pwa.DS if under_ds else pwa.PREFIX):] or "index.html"
        f = (ds_files() if under_ds else app_files()).get(name)
        if f and f.suffix in pwa.TYPES and not name.endswith((".html", "sw.js", ".webmanifest")):
            return self.send(f)
        self.wfile.write(pwa.serve("GET", self.path))

    def send(self, f, body=None, kind=None):
        body = f.read_bytes() if f else body
        kind = kind or mimetypes.guess_type(f.name)[0] or "application/octet-stream"
        if kind.startswith("text/") or kind.endswith(("javascript", "json")):
            kind += "; charset=utf-8" if "charset" not in kind else ""
        self.send_response(200)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def serve(port: int = 8765, lay=None) -> http.server.ThreadingHTTPServer:
    """The page's server; with `lay`, it serves the recording after `lay(recording)` has laid into a copy of it."""
    s = http.server.ThreadingHTTPServer(("127.0.0.1", port), Page)
    s.recording = None
    if lay:
        data = json.loads((STATIC / "mock" / "board.json").read_text(encoding="utf-8"))
        lay(data)
        s.recording = json.dumps(data, ensure_ascii=False).encode("utf-8")
    return s


if __name__ == "__main__":
    s = serve(int(sys.argv[1]) if len(sys.argv) > 1 else 8765)
    print(f"http://127.0.0.1:{s.server_port}/?mock=1")
    s.serve_forever()
