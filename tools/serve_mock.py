"""Serve the page on mocks with no host (goal 170, stage M): the page's own files, orkUI's copy and the roles' sheet, at the
paths the host serves them (gui/server.py), and the page opened with `?mock=1` (js/mock/mocklink.js).

    uv run python tools/serve_mock.py [port]     # then open http://127.0.0.1:<port>/?mock=1
"""
import functools, http.server, mimetypes, sys
from pathlib import Path
from orkboard.design import tokens
from orkboard.gui import server

STATIC, SYSTEM = server.STATIC, tokens.SYSTEM


class Page(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            return self.send(STATIC / "index.html")
        if path == "/roles.css":
            return self.send(None, tokens.roles_css().encode(), "text/css; charset=utf-8")
        for route, root in (("/static/", STATIC), ("/ds/", SYSTEM)):
            if path.startswith(route):
                f = (root / path[len(route):]).resolve()
                if f.is_file() and root.resolve() in f.parents:
                    return self.send(f)
        self.send_error(404)

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


def serve(port: int = 8765) -> http.server.ThreadingHTTPServer:
    return http.server.ThreadingHTTPServer(("127.0.0.1", port), Page)


if __name__ == "__main__":
    s = serve(int(sys.argv[1]) if len(sys.argv) > 1 else 8765)
    print(f"http://127.0.0.1:{s.server_port}/?mock=1")
    s.serve_forever()
