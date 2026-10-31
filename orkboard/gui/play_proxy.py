"""The probe's proxy (docs/specs/115-the-live-product-under-each-leaders-eyes.md §2): a reverse proxy on 127.0.0.1, a port of its own, in front of the
preview's page port while Play plays. The page in Play's frame is the proxy's, so the host can put the probe (gui/static/play/probe.js) in it.

    proxy = PlayProxy(upstream_port, play_id, page_origin="")
    proxy.start()                    # listening; `proxy.url_of("/")` is the address Play's frame opens
    proxy.stop()                     # closes the listener and every connection through it
    inject(html: bytes, tag: bytes)  # the document with `tag` as the first child of `<head>` (else after `<html>`, the doctype, or at the start)

Every request goes to the preview as it is and every answer comes back as it is, but:
  - a `text/html` answer (the preview is asked with `Accept-Encoding: identity`; a gzip one is unpacked, a chunked one read whole) gets
    `<script src="/__ork/probe.js?o=<the page's origin>&p=<play id>"></script>` first in `<head>`, its `Content-Length` set again;
  - `Content-Security-Policy` and `Content-Security-Policy-Report-Only` are dropped (dev only: the proxy serves no one else);
  - `/__ork/*` is the host's (the files of gui/static/play/), never passed on;
  - an `Upgrade: websocket` request is tunnelled byte for byte (Vite's and Next's hot reload);
  - the `Host` header says the preview's own address, and an `Origin` or `Referer` of the proxy's says it too, so a dev server that checks them
    sees itself; an absolute `Location` of the preview's address says the proxy's.
The answers close their connection (HTTP/1.0): a stream (server-sent events) ends when the preview ends it.

**The page's origin** (`o=`): the host does not know the origin it is shown at (the server's port is the server's, and an editor may reach it
through a forwarded address), so `page_origin` is what a caller knows ("" when it does not; several, separated by commas). The probe takes its
parent's origin from `o`, else from the browser (`location.ancestorOrigins`), else from the first message its parent sends (probe.js).
"""
from __future__ import annotations

import http.client
import http.server
import logging
import re
import secrets
import socket
import threading
import zlib
from pathlib import Path
from urllib.parse import quote

from orkboard.core import idea_shot

log = logging.getLogger(__name__)

PROBE_DIR = Path(__file__).resolve().parent / "static" / "play"
PREFIX = "/__ork/"
MAX_HTML = 16 * 1024 * 1024                         # a larger HTML answer passes untouched
MAX_BODY = 256 * 1024 * 1024
CONNECT_S = 5.0
DROPPED = {"content-security-policy", "content-security-policy-report-only"}
HOP = {"connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "proxy-connection", "te", "trailer", "transfer-encoding", "upgrade"}
OWN = {"server", "date"}                            # the proxy's own handler writes these
_HEAD = re.compile(rb"<head(?:\s[^>]*)?>", re.I)
_HTML = re.compile(rb"<html(?:\s[^>]*)?>", re.I)
_DOCTYPE = re.compile(rb"<!doctype[^>]*>", re.I)
BOM = b"\xef\xbb\xbf"


def tag_of(page_origin: str, play_id: str) -> bytes:
    """The script element the probe is put in by."""
    return f'<script src="{PREFIX}probe.js?o={quote(page_origin, safe="")}&p={quote(play_id, safe="")}"></script>'.encode()


def inject(html: bytes, tag: bytes) -> bytes:
    """`tag` as the first child of `<head>`; with no head after `<html>`, else after the doctype (before it a page falls into quirks mode), else at the start."""
    for pattern in (_HEAD, _HTML, _DOCTYPE):
        if m := pattern.search(html):
            return html[:m.end()] + tag + html[m.end():]
    start = len(BOM) if html.startswith(BOM) else 0
    return html[:start] + tag + html[start:]


class _Server(http.server.ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 128
    proxy: "PlayProxy"


class _Limited:
    """A request's body read from the client as it goes to the preview (`http.client` takes a file-like with `read`)."""

    def __init__(self, rfile, size: int) -> None:
        self.rfile, self.left = rfile, size

    def read(self, n: int = -1) -> bytes:
        n = self.left if n is None or n < 0 else min(n, self.left)
        data = self.rfile.read(n) if n else b""
        self.left -= len(data)
        return data


class _Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def log_message(self, *_args) -> None:
        pass

    # -- a request -------------------------------------------------------------------------------------------

    def _pass(self) -> None:
        proxy = self.server.proxy
        if self.path.split("?", 1)[0].startswith(PREFIX):
            return self._own()
        if self.headers.get("Upgrade", "").lower() == "websocket" and "upgrade" in self.headers.get("Connection", "").lower():
            return self._tunnel()
        try:
            body, size = self._body()
        except (ValueError, OSError):
            return self._plain(400, "That request could not be read")
        headers = proxy.request_headers(self.headers, self.headers.get("Host", ""))
        if size is not None:
            headers["Content-Length"] = str(size)
        host = proxy.upstream_host()
        conn = http.client.HTTPConnection(host, proxy.upstream, timeout=CONNECT_S)
        try:
            conn.connect()
            conn.sock.settimeout(None)               # a long poll or a stream waits as long as the preview does
            proxy.track(conn.sock)
            conn.request(self.command, self.path, body, headers)
            res = conn.getresponse()
        except (OSError, http.client.HTTPException, ValueError):
            conn.close()
            proxy.forget_host()
            return self._plain(502, "The preview is not answering")
        try:
            self._answer(res, proxy)
        except (OSError, http.client.HTTPException, zlib.error, ValueError):
            pass                                   # the page went away, or the preview cut its answer short
        finally:
            proxy.untrack(conn.sock)
            conn.close()

    def _body(self):
        """(what to send on, its size or None): a body of known size streams; a chunked one is read whole."""
        if "chunked" in self.headers.get("Transfer-Encoding", "").lower():
            data = bytearray()
            while True:
                size = int(self.rfile.readline(64).split(b";", 1)[0].strip() or b"0", 16)
                if size == 0:
                    while self.rfile.readline(65536) not in (b"\r\n", b"\n", b""):
                        pass
                    break
                data += self.rfile.read(size)
                self.rfile.readline(8)
                if len(data) > MAX_BODY:
                    raise ValueError("too large")
            return bytes(data), len(data)
        size = int(self.headers.get("Content-Length") or 0)
        if size < 0 or size > MAX_BODY:
            raise ValueError("too large")
        return (_Limited(self.rfile, size), size) if size else (None, None)

    def _answer(self, res: http.client.HTTPResponse, proxy: "PlayProxy") -> None:
        """The preview's answer to the page: `text/html` read whole and given the probe, anything else as it comes."""
        head = [(k, v) for k, v in res.getheaders() if k.lower() not in DROPPED | HOP | OWN]
        head = [(k, proxy.location(v, self.headers.get("Host", "")) if k.lower() == "location" else v) for k, v in head]
        coding = (res.getheader("Content-Encoding") or "").strip().lower()
        html = ((res.getheader("Content-Type") or "").lower().lstrip().startswith("text/html") and self.command != "HEAD"
                and res.status >= 200 and res.status not in (204, 304) and int(res.getheader("Content-Length") or 0) <= MAX_HTML
                and coding in ("", "identity", "gzip", "x-gzip", "deflate"))
        if html:
            data = res.read()
            if coding in ("gzip", "x-gzip", "deflate"):
                data = zlib.decompress(data, 47) if coding != "deflate" else _inflate(data)
                head = [(k, v) for k, v in head if k.lower() != "content-encoding"]
            data = inject(data, proxy.tag)
            head = [(k, v) for k, v in head if k.lower() != "content-length"] + [("Content-Length", str(len(data)))]
            self._head(res.status, res.reason, head)
            if self.command != "HEAD":
                self.wfile.write(data)
            return
        self._head(res.status, res.reason, head)
        if self.command == "HEAD" or res.status in (204, 304):
            return
        while chunk := res.read1(65536):
            self.wfile.write(chunk)

    def _head(self, status: int, reason: str, head: list[tuple[str, str]]) -> None:
        self.send_response(status, reason)
        for k, v in head:
            self.send_header(k, v)
        self.send_header("Connection", "close")
        self.end_headers()

    def _plain(self, status: int, words: str) -> None:
        data = words.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    # -- /__ork/ ---------------------------------------------------------------------------------------------

    def _own(self) -> None:
        """The host's own files (the probe), never the preview's."""
        if self.command not in ("GET", "HEAD"):
            return self._plain(405, "Not allowed")
        name = self.path.split("?", 1)[0][len(PREFIX):]
        file = PROBE_DIR / name
        if not name or "/" in name or name.startswith(".") or not file.is_file():
            return self._plain(404, "Not found")
        data = file.read_bytes()
        kind = "text/javascript; charset=utf-8" if file.suffix == ".js" else "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command == "GET":
            self.wfile.write(data)

    # -- a websocket -----------------------------------------------------------------------------------------

    def _tunnel(self) -> None:
        """The request to the preview, then bytes both ways until either side ends."""
        proxy = self.server.proxy
        try:
            up = socket.create_connection((proxy.upstream_host(), proxy.upstream), CONNECT_S)
            up.settimeout(None)
        except OSError:
            proxy.forget_host()
            return self._plain(502, "The preview is not answering")
        proxy.track(up)
        client = self.connection
        try:
            lines = [f"{self.command} {self.path} HTTP/1.1"]
            lines += [f"{k}: {v}" for k, v in proxy.request_headers(self.headers, self.headers.get("Host", ""), keep=True).items()]
            up.sendall(("\r\n".join(lines) + "\r\n\r\n").encode("latin-1", "replace"))
            back = threading.Thread(target=_pipe, args=(self.rfile.read1, up), daemon=True, name="play-proxy-ws")
            back.start()
            _pipe(lambda n: up.recv(n), client)
            back.join(1.0)
        except OSError:
            pass
        finally:
            self.close_connection = True
            for s in (up, client):
                try:
                    s.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
            up.close()
            proxy.untrack(up)

    do_GET = do_HEAD = do_POST = do_PUT = do_PATCH = do_DELETE = do_OPTIONS = _pass


def _pipe(read, sink: socket.socket) -> None:
    """Bytes from `read` to `sink` until the end; then `sink` is told no more is coming."""
    try:
        while data := read(65536):
            sink.sendall(data)
    except (OSError, ValueError):
        pass
    try:
        sink.shutdown(socket.SHUT_WR)
    except OSError:
        pass


def _inflate(data: bytes) -> bytes:
    try:
        return zlib.decompress(data)
    except zlib.error:
        return zlib.decompress(data, -15)             # `deflate` that is the bare stream


class PlayProxy:
    """One play's proxy: the listener, and what it needs to rewrite."""

    def __init__(self, upstream: int, play_id: str, page_origin: str = "") -> None:
        self.upstream, self.play_id, self.page_origin = upstream, play_id, page_origin
        self.tag = tag_of(page_origin, play_id)
        self.port = 0
        self._server: _Server | None = None
        self._host: str | None = None
        self._lock = threading.Lock()
        self._socks: set[socket.socket] = set()

    # -- start and stop --------------------------------------------------------------------------------------

    def start(self) -> "PlayProxy":
        server = _Server(("127.0.0.1", 0), _Handler)
        server.proxy = self
        self._server, self.port = server, server.server_address[1]
        threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.2}, daemon=True, name="play-proxy").start()
        return self

    def stop(self) -> None:
        server, self._server = self._server, None
        if server is not None:
            server.shutdown()
            server.server_close()
        with self._lock:
            socks, self._socks = list(self._socks), set()
        for s in socks:                               # a tunnel or a stream still open ends with Play
            try:
                s.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

    @property
    def origin(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def url_of(self, path: str = "/") -> str:
        return self.origin + (path if path.startswith("/") else "/")

    # -- the preview -----------------------------------------------------------------------------------------

    def upstream_host(self) -> str:
        """The loopback address the preview's port listens on (127.0.0.1, else ::1: `idea_shot._host_of`)."""
        if self._host is None:
            self._host = idea_shot._host_of(self.upstream) or idea_shot.LOOPBACK[0]
        return self._host

    def forget_host(self) -> None:
        self._host = None

    def track(self, sock: socket.socket | None) -> None:
        if sock is not None:
            with self._lock:
                self._socks.add(sock)

    def untrack(self, sock: socket.socket | None) -> None:
        with self._lock:
            self._socks.discard(sock)

    def _own_origins(self, host: str) -> tuple[str, ...]:
        return (f"http://{host}",) if host else ()

    def _theirs(self) -> tuple[str, ...]:
        return tuple(f"http://{h}:{self.upstream}" for h in ("127.0.0.1", "localhost", "[::1]", "0.0.0.0"))

    def request_headers(self, headers, host: str, keep: bool = False) -> dict[str, str]:
        """The page's request as the preview should see it: no hop-by-hop headers (`keep`: a websocket's own), identity coding, the preview's
        `Host`, and its own address where the proxy's stood in `Origin` or `Referer`."""
        bracket = f"[{self.upstream_host()}]" if ":" in self.upstream_host() else self.upstream_host()
        mine = f"{bracket}:{self.upstream}"
        out: dict[str, str] = {}
        for k, v in headers.items():
            low = k.lower()
            if low in ("host", "accept-encoding", "content-length") or (low in HOP and not (keep and low in ("connection", "upgrade"))):
                continue
            if low in ("origin", "referer"):
                for own in self._own_origins(host):
                    if v.startswith(own):
                        v = f"http://{mine}" + v[len(own):]
            out[k] = v if k not in out else out[k] + ", " + v
        out["Host"] = mine
        if not keep:
            out["Accept-Encoding"] = "identity"
            out["Connection"] = "close"
        return out

    def location(self, value: str, host: str) -> str:
        """An absolute `Location` of the preview's address, as the proxy's."""
        for theirs in self._theirs():
            if value.startswith(theirs) and host:
                return f"http://{host}" + value[len(theirs):]
        return value


def new_id() -> str:
    return secrets.token_hex(4)
