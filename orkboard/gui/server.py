"""The GUI's server: the page, the design system and one WebSocket, on 127.0.0.1 only.

One asyncio loop runs it and the host (gui/board_host.py `Orkboard`) on this loop's thread. The page gets a snapshot
whenever the host changes (at most every `FLUSH_S`, and only when it differs from the last one), toasts as they come,
and sends commands back:

    → {"t": "cmd", "id": 7, "name": "ideas.board", "args": {}}
    ← {"t": "reply", "id": 7, "ok": true, "result": {...}}      (or "ok": false, "error": "...")
    ← {"t": "state", "state": {...}}                             (the host's `snapshot`)
    ← {"t": "toast", "message": "...", "title": "...", "severity": "information", "timeout": null}

The socket takes only the page this server gave out: a random token in its address and an Origin
of this server (127.0.0.1 or localhost, its port), so another page open in a browser cannot drive the town.

`GET /api/version` (the same token, as `?t=` or `Authorization: Bearer`) is the handshake a client
other than the page makes first (docs/design/mobile.md): what this server speaks, as JSON.

    ← {"name": "orkcraft", "version": "0.1.0", "protocol": 1, "api": 1}

`GET /media/<goal>/<pick-id>/<file>?s=<signature>` is a pick's file (gui/media.py, spec 51 §3): the address is signed by the host
and is the proof, so it needs no token and an `<img>`, `<audio>` or `<video>` loads it; Range is served (206).

`GET /api/analytics?days=7` (the same token) is the day logs of the last days, with what each day added up to, as one
zip (realm/analytics.py, the host's `day_logs`).

It serves Orkboard's host (gui/board_host.py, spec 37 §4).
"""
from __future__ import annotations

import asyncio
import json
import logging
import mimetypes
import secrets
import threading
from http import HTTPStatus
from pathlib import Path
from urllib.parse import parse_qs, quote, urlsplit

from websockets.asyncio.server import ServerConnection, serve
from websockets.datastructures import Headers
from websockets.exceptions import ConnectionClosed
from websockets.http11 import Request, Response

from orkboard import __version__
from orkboard.design import logo, tokens
from orkboard.gui import command_log, media, phones, pwa
from orkboard.gui.board_host import CommandError

log = logging.getLogger(__name__)
STATIC = Path(__file__).with_name("static")
TICK_S = 1.0
FLUSH_S = 0.05
ROUTES = {"/static/": STATIC, "/ds/": tokens.SYSTEM}
PROTOCOL = 1            # the socket's messages above: a change that breaks a client raises it
mimetypes.add_type("text/javascript", ".mjs")
mimetypes.add_type("font/woff2", ".woff2")
mimetypes.add_type("image/webp", ".webp")


def _response(status: HTTPStatus, body: bytes, content_type: str = "text/plain; charset=utf-8") -> Response:
    headers = Headers([("Content-Type", content_type), ("Content-Length", str(len(body))),
                       ("Cache-Control", "no-store"), ("X-Content-Type-Options", "nosniff")])
    return Response(status.value, status.phrase, headers, body)


def resolve(path: str) -> Path | None:
    """The file a static path names, never one outside its folder."""
    for prefix, root in ROUTES.items():
        if path.startswith(prefix):
            root = root.resolve()
            target = (root / path[len(prefix):]).resolve()
            if target.is_file() and target.is_relative_to(root):
                return target
    return None


class Server:
    def __init__(self, host, port: int = 0) -> None:
        self.host = host
        self.port = port
        self.token = secrets.token_urlsafe(24)
        self.clients: set[ServerConnection] = set()
        self.loop: asyncio.AbstractEventLoop | None = None
        self.ready = threading.Event()
        self._stop: asyncio.Event | None = None
        self._last = ""
        self._dirty = False
        host.on_change = self._changed
        host.on_toast = lambda data: self._send_all({"t": "toast", **data})
        host.faces = lambda: len(self.clients) + len(self.phones.phones)      # the faces open now: a goal the leaders agreed on starts by itself only while one is (spec 120 §3.5)
        # The listener for phones (gui/phones.py): on the LAN, TLS, a device token; only while one is paired.
        self.phones = phones.Listener(host)
        host.commands.update(self.phones.commands())
        self.tail_watch = pwa.TailWatch(self.phones)   # Tailscale that came after the server (gui/pwa.py)
        host.commands.update(pwa.commands(self.phones))   # the app in a phone's browser: Tailscale's state

    def capture(self, e: BaseException, where: str, **kw) -> None:
        """An error the server caught, to the host's crash reports (core/crashes.py), when it keeps them, and with its traceback to the
        server's log (gui/server_log.py)."""
        log.error("%s caught in %s%s", type(e).__name__, where, f" ({kw['command']})" if kw.get("command") else "", exc_info=e)
        capture = getattr(self.host, "capture", None)
        if capture is not None:
            capture(e, where, **kw)

    @property
    def origin(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    @property
    def origins(self) -> tuple[str, str]:
        """The origins the socket takes: this server's, by its number or as `localhost` (an editor's panel reaches it
        through `asExternalUri`, which may name it so: gui/extension.py)."""
        return self.origin, f"http://localhost:{self.port}"

    @property
    def url(self) -> str:
        return f"{self.origin}/?t={self.token}"

    # -- HTTP ----------------------------------------------------------------------------------

    def _token_ok(self, request: Request) -> bool:
        """The server's token, from the address (`?t=`) or an `Authorization: Bearer` header."""
        token = parse_qs(urlsplit(request.path).query).get("t", [""])[0]
        auth = request.headers.get("Authorization", "")
        if not token and auth.startswith("Bearer "):
            token = auth.removeprefix("Bearer ").strip()
        return bool(token) and secrets.compare_digest(token, self.token)

    def version(self) -> dict:
        return {"name": "orkcraft", "version": __version__, "protocol": PROTOCOL, "api": phones.API}

    def _http(self, connection: ServerConnection, request: Request) -> Response | None:
        parts = urlsplit(request.path)
        if parts.path == "/ws":
            token = parse_qs(parts.query).get("t", [""])[0]
            origin = request.headers.get("Origin", "")
            if not secrets.compare_digest(token, self.token) or origin not in self.origins:
                return _response(HTTPStatus.FORBIDDEN, b"Forbidden")
            return None                                   # go on with the WebSocket handshake
        if parts.path == "/api/version":
            if not self._token_ok(request):
                return _response(HTTPStatus.FORBIDDEN, b"Forbidden")
            return _response(HTTPStatus.OK, json.dumps(self.version()).encode(), "application/json")
        if parts.path.startswith(media.PREFIX):                  # a pick's files, by a signed address (spec 51 §3): no token, the address is the proof
            return self._media(request)
        if parts.path == "/api/analytics":
            if not self._token_ok(request):
                return _response(HTTPStatus.FORBIDDEN, b"Forbidden")
            days = parse_qs(parts.query).get("days", ["7"])[0]
            return self._zip(self.host.day_logs.pack_period(int(days) if days.isdigit() else 7))
        if parts.path in ("/", "/index.html"):
            return _response(HTTPStatus.OK, self.page(), "text/html; charset=utf-8")
        if parts.path == "/favicon.ico":                  # Orkboard's mark (design/logo.py)
            return _response(HTTPStatus.OK, logo.favicon().read_bytes(), "image/x-icon")
        if parts.path == "/roles.css":
            return _response(HTTPStatus.OK, tokens.roles_css().encode(), "text/css; charset=utf-8")
        target = resolve(parts.path)
        if target is None:
            return _response(HTTPStatus.NOT_FOUND, b"Not found")
        kind = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        if kind.startswith("text/") or kind.endswith(("javascript", "json")):
            kind += "; charset=utf-8"
        return _response(HTTPStatus.OK, target.read_bytes(), kind)

    def _media(self, request: Request) -> Response:
        """A file of a pick (gui/media.py): 200, 206 for a range, 416, or 404 for anything wrong."""
        reply = media.serve("GET", request.path, request.headers.get("Range", ""), media.state_dirs(self.host))
        return Response(reply.status, HTTPStatus(reply.status).phrase, Headers(reply.headers), reply.read())

    @staticmethod
    def _zip(packed: tuple[str, bytes] | None) -> Response:
        """A zip to download (the day logs); 404 when there is nothing of that name."""
        if packed is None:
            return _response(HTTPStatus.NOT_FOUND, b"Not found")
        name, data = packed
        resp = _response(HTTPStatus.OK, data, "application/zip")
        resp.headers["Content-Disposition"] = f'attachment; filename="{quote(name)}"'
        return resp

    def page(self) -> bytes:
        """The page: `static/index.html`, its script `board.js`."""
        return (STATIC / "index.html").read_bytes()

    # -- the socket ----------------------------------------------------------------------------

    async def _client(self, ws: ServerConnection) -> None:
        self.clients.add(ws)
        try:
            await ws.send(json.dumps({"t": "state", "state": self.host.snapshot()}, ensure_ascii=False))
            async for raw in ws:
                await ws.send(json.dumps(self._handle(raw, ws), ensure_ascii=False))
        except ConnectionClosed:
            pass
        finally:
            self.clients.discard(ws)

    def _handle(self, raw: str | bytes, ws: ServerConnection | None = None) -> dict:
        try:
            msg = json.loads(raw)
            cid = msg.get("id")
        except (ValueError, AttributeError):
            return {"t": "reply", "id": None, "ok": False, "error": "Not a command"}
        if msg.get("t") != "cmd":
            return {"t": "reply", "id": cid, "ok": False, "error": "Not a command"}
        try:
            name, args = str(msg.get("name", "")), msg.get("args") or {}
            if not isinstance(args, dict):
                raise CommandError("Arguments are an object")
            args.pop("device_id", None)                 # a paired phone's to say (`BoardPhone.guard`), never the page's
            if name.startswith(("ideas.", "projects.", "files.")) or name in ("halt", "resume"):
                args.pop("link", None)                  # (the onboarding's `link` is a person's own words)
            result = self.host.command(name, args)
            return {"t": "reply", "id": cid, "ok": True, "result": result}
        except CommandError as e:
            command_log.refused(self.host, str(msg.get("name", "")), str(e))
            return {"t": "reply", "id": cid, "ok": False, "error": str(e)}
        except Exception as e:                            # a broken command never closes the page
            known = str(msg.get("name", ""))
            self.capture(e, "command", command=known if known in self.host.commands else "")
            command_log.refused(self.host, known, f"{type(e).__name__}: {e}", broken=True)
            return {"t": "reply", "id": cid, "ok": False, "error": f"{type(e).__name__}: {e}"}

    def _send_all(self, msg: dict) -> None:
        text = json.dumps(msg, ensure_ascii=False)
        for ws in list(self.clients):
            asyncio.ensure_future(self._send(ws, text))

    @staticmethod
    async def _send(ws: ServerConnection, text: str | bytes) -> None:
        try:
            await ws.send(text)
        except ConnectionClosed:
            pass

    def _changed(self) -> None:
        """The town changed: flush a snapshot soon (many changes in one moment make one send)."""
        if self._dirty or self.loop is None:
            return
        self._dirty = True
        self.loop.call_later(FLUSH_S, self._flush)

    def _flush(self) -> None:
        self._dirty = False
        if not self.clients:
            return
        text = json.dumps({"t": "state", "state": self.host.snapshot()}, ensure_ascii=False)
        if text != self._last:
            self._last = text
            for ws in list(self.clients):
                asyncio.ensure_future(self._send(ws, text))

    # -- its life ------------------------------------------------------------------------------

    async def _ticker(self) -> None:
        while True:
            await asyncio.sleep(TICK_S)
            try:
                self.host.tick()
                self.phones.tick()
                self.tail_watch.tick()
            except Exception as e:
                self.capture(e, "clock")
                self.host.town.toast(f"{type(e).__name__}: {e}", title="Town clock", severity="error")

    async def run(self) -> None:
        self.loop = asyncio.get_running_loop()
        self._stop = asyncio.Event()
        self.host.town.call = lambda fn, *a: self.loop.call_soon_threadsafe(fn, *a)
        reporter = getattr(self.host, "crashes", None)
        if reporter is not None:
            self.loop.set_exception_handler(reporter.asyncio_handler)   # a task's error nobody awaited
        async with serve(self._client, "127.0.0.1", self.port, process_request=self._http,
                         max_size=8 * 2**20) as server:
            self.port = server.sockets[0].getsockname()[1]
            ticker = asyncio.create_task(self._ticker())
            self._phones_start()
            self.ready.set()
            await self._stop.wait()
            ticker.cancel()
            self.phones.stop()
        self.host.close()

    def _phones_start(self) -> None:
        """A machine with a paired phone listens for it from the start."""
        try:
            if self.phones.wanted():
                self.phones.start()
        except phones.PhoneError as e:
            self.host.town.toast(str(e), title="Phones", severity="warning")

    def stop(self) -> None:
        """Ask the server to stop; once it has, asking again does nothing (its loop is closed by then)."""
        if self.loop is not None and self._stop is not None and not self.loop.is_closed():
            try:
                self.loop.call_soon_threadsafe(self._stop.set)
            except RuntimeError:                 # it closed between the look and the call
                pass

    def start_thread(self) -> threading.Thread:
        """Serve on a thread of its own (the window takes the main thread); returns once it listens."""
        t = threading.Thread(target=lambda: asyncio.run(self.run()), name="orkcraft-gui", daemon=True)
        t.start()
        self.ready.wait(10)
        return t
