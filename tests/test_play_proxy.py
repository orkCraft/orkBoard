"""Spec 115 part A (docs/specs/115-the-live-product-under-each-leaders-eyes.md §2): the proxy in front of Play's preview. A fake dev server
(plain, chunked, gzip, CSP, a hand-made websocket upgrade) and a static page through `gui/play_proxy.py`: the probe's script first in
`<head>`, `Content-Length` right, the CSP headers dropped, `/__ork/probe.js` the host's own, a websocket tunnelled byte for byte, anything
else as it is; and Play's side: `url` the proxy's, `preview_probe = false`, a proxy that cannot start, the command's lines kept with
their time, secrets out."""
from __future__ import annotations

import gzip
import http.client
import http.server
import re
import socket
import subprocess
import threading
import time
import urllib.request
from pathlib import Path

import pytest

from orkboard.gui import ideas_assets, play_lines, play_proxy
from orkboard.gui.board_host import Orkboard

PAGE = b'<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><title>Game</title></head><body><h1>dev build</h1></body></html>'
PLAIN = b"<!doctype html><title>no head</title><p>hello"


class Dev(http.server.BaseHTTPRequestHandler):
    """A fake dev server: what each path answers is in `answer`."""
    protocol_version = "HTTP/1.1"
    seen: list[dict] = []

    def log_message(self, *_a) -> None:
        pass

    def send(self, status: int, body: bytes, ctype: str, *extra: tuple[str, str]) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in extra:
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        Dev.seen.append({"path": self.path, "host": self.headers.get("Host"), "accept-encoding": self.headers.get("Accept-Encoding"),
                         "origin": self.headers.get("Origin"), "referer": self.headers.get("Referer")})
        path = self.path.split("?")[0]
        if self.headers.get("Upgrade", "").lower() == "websocket":
            return self.echo()
        if path == "/":
            return self.send(200, PAGE, "text/html; charset=utf-8", ("Content-Security-Policy", "default-src 'self'"),
                             ("Content-Security-Policy-Report-Only", "default-src 'none'"), ("X-Dev", "yes"))
        if path == "/nohead":
            return self.send(200, PLAIN, "text/html")
        if path == "/chunked":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()
            for part in (PAGE[:30], PAGE[30:60], PAGE[60:]):
                self.wfile.write(f"{len(part):x}\r\n".encode() + part + b"\r\n")
            self.wfile.write(b"0\r\n\r\n")
            return
        if path == "/gzip":
            return self.send(200, gzip.compress(PAGE), "text/html", ("Content-Encoding", "gzip"))
        if path == "/app.js":
            return self.send(200, b"console.log(1)", "text/javascript", ("Content-Security-Policy", "x"))
        if path == "/json":
            return self.send(200, b'{"ok": true}', "application/json")
        if path == "/missing":
            return self.send(404, b"<h1>not here</h1>", "text/html")
        if path == "/redirect":
            return self.send(302, b"", "text/plain", ("Location", f"http://127.0.0.1:{self.server.server_address[1]}/"))
        if path == "/empty":
            self.send_response(204)
            self.end_headers()
            return
        self.send(404, b"no", "text/plain")

    def do_HEAD(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(PAGE)))
        self.end_headers()

    def do_POST(self) -> None:
        size = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(size)
        self.send(200, b"got " + body, "text/plain")

    def echo(self) -> None:
        """A websocket in all but its framing: the 101, then every byte back in capitals until the client closes."""
        self.wfile.write(b"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n\r\n")
        self.wfile.flush()
        self.close_connection = True
        while data := self.connection.recv(4096):
            self.connection.sendall(data.upper())


@pytest.fixture
def dev():
    Dev.seen = []
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Dev)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield server.server_address[1]
    server.shutdown()
    server.server_close()


@pytest.fixture
def proxy(dev):
    p = play_proxy.PlayProxy(dev, "abc123", "http://127.0.0.1:9").start()
    yield p
    p.stop()


def get(proxy, path: str, headers: dict | None = None) -> tuple[int, dict, bytes]:
    conn = http.client.HTTPConnection("127.0.0.1", proxy.port, timeout=5)
    conn.request("GET", path, headers=headers or {})
    res = conn.getresponse()
    out = (res.status, {k.lower(): v for k, v in res.getheaders()}, res.read())
    conn.close()
    return out


def test_a_page_gets_the_probe_first_in_head_and_its_length_is_right(proxy):
    status, headers, body = get(proxy, "/")
    tag = b'<script src="/__ork/probe.js?o=http%3A%2F%2F127.0.0.1%3A9&p=abc123"></script>'
    assert status == 200 and body.count(tag) == 1
    assert body.index(b"<head>") + len(b"<head>") == body.index(tag)                     # the first child of head, before the charset
    assert body.replace(tag, b"") == PAGE
    assert int(headers["content-length"]) == len(body) and "transfer-encoding" not in headers
    assert headers["x-dev"] == "yes" and headers["content-type"] == "text/html; charset=utf-8"


def test_the_csp_headers_are_dropped_from_every_answer(proxy):
    _, headers, _ = get(proxy, "/")
    assert "content-security-policy" not in headers and "content-security-policy-report-only" not in headers
    _, headers, body = get(proxy, "/app.js")
    assert "content-security-policy" not in headers and body == b"console.log(1)"       # a script is not touched


def test_an_html_answer_with_no_head_gets_it_after_the_doctype(proxy):
    _, _, body = get(proxy, "/nohead")
    assert body.startswith(b"<!doctype html><script src=") and body.endswith(b"<title>no head</title><p>hello")
    assert play_proxy.inject(b"<p>x", b"<s>") == b"<s><p>x"
    assert play_proxy.inject(b"\xef\xbb\xbf<p>x", b"<s>") == b"\xef\xbb\xbf<s><p>x"
    assert play_proxy.inject(b"<html><body>x", b"<s>") == b"<html><s><body>x"
    assert play_proxy.inject(b"<header>x</header><HEAD data-a=1><title>t", b"<s>") == b"<header>x</header><HEAD data-a=1><s><title>t"


def test_a_chunked_answer_is_read_whole_and_sent_with_its_length(proxy):
    status, headers, body = get(proxy, "/chunked")
    assert status == 200 and b"/__ork/probe.js" in body and body.replace(play_proxy.tag_of("http://127.0.0.1:9", "abc123"), b"") == PAGE
    assert int(headers["content-length"]) == len(body) and "transfer-encoding" not in headers


def test_a_gzip_answer_is_unpacked_and_the_preview_is_asked_for_identity(proxy):
    _, headers, body = get(proxy, "/gzip", {"Accept-Encoding": "gzip, br"})
    assert b"/__ork/probe.js" in body and "content-encoding" not in headers and int(headers["content-length"]) == len(body)
    assert Dev.seen[-1]["accept-encoding"] == "identity"


def test_the_probe_file_is_the_hosts_own_and_never_passed_on(proxy):
    status, headers, body = get(proxy, "/__ork/probe.js?o=x&p=y")
    assert status == 200 and headers["content-type"].startswith("text/javascript") and headers["cache-control"] == "no-store"
    assert body == (play_proxy.PROBE_DIR / "probe.js").read_bytes()
    assert not Dev.seen                                                                  # the preview was never asked
    assert get(proxy, "/__ork/nothing.js")[0] == 404 and get(proxy, "/__ork/../x")[0] == 404
    conn = http.client.HTTPConnection("127.0.0.1", proxy.port)
    conn.request("POST", "/__ork/probe.js", body=b"x")
    assert conn.getresponse().status == 405
    conn.close()


def test_everything_else_passes_as_it_is(proxy):
    status, headers, body = get(proxy, "/json")
    assert (status, body, headers["content-type"]) == (200, b'{"ok": true}', "application/json")
    status, _, body = get(proxy, "/missing")
    assert status == 404 and b"not here" in body and b"/__ork/probe.js" in body         # a 404 page is HTML too
    assert get(proxy, "/empty")[0] == 204
    conn = http.client.HTTPConnection("127.0.0.1", proxy.port)
    conn.request("POST", "/post", body=b"hello", headers={"Content-Type": "text/plain"})
    res = conn.getresponse()
    assert res.status == 200 and res.read() == b"got hello"
    conn.close()
    conn = http.client.HTTPConnection("127.0.0.1", proxy.port)
    conn.request("HEAD", "/")
    res = conn.getresponse()
    assert res.status == 200 and res.read() == b""
    conn.close()


def test_the_preview_sees_its_own_address_and_a_redirect_comes_back_to_the_proxy(proxy, dev):
    get(proxy, "/", {"Origin": f"http://127.0.0.1:{proxy.port}", "Referer": f"http://127.0.0.1:{proxy.port}/a?b=1"})
    seen = Dev.seen[-1]
    assert seen["host"] == f"127.0.0.1:{dev}" and seen["origin"] == f"http://127.0.0.1:{dev}" and seen["referer"] == f"http://127.0.0.1:{dev}/a?b=1"
    status, headers, _ = get(proxy, "/redirect", {"Host": f"127.0.0.1:{proxy.port}"})
    assert status == 302 and headers["location"] == f"http://127.0.0.1:{proxy.port}/"


def test_an_upgrade_to_a_websocket_is_tunnelled_byte_for_byte(proxy):
    with socket.create_connection(("127.0.0.1", proxy.port), timeout=5) as s:
        s.sendall(b"GET /ws?token=1 HTTP/1.1\r\nHost: x\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: abc\r\nSec-WebSocket-Version: 13\r\n\r\n")
        got = b""
        while b"\r\n\r\n" not in got:
            got += s.recv(4096)
        assert got.startswith(b"HTTP/1.1 101") and b"Upgrade: websocket" in got
        s.sendall(b"\x81\x05hello")
        echoed = b""
        while len(echoed) < 7:
            echoed += s.recv(4096)
        assert echoed == b"\x81\x05HELLO"                                                # the bytes as they are (the fake upper-cases letters)
    assert Dev.seen[-1]["path"] == "/ws?token=1"


def test_an_unreachable_preview_is_a_502_and_stopping_closes_the_listener(dev):
    p = play_proxy.PlayProxy(1, "x").start()                                              # nothing listens on port 1
    status, _, body = get(p, "/")
    assert status == 502 and b"not answering" in body
    port = p.port
    p.stop()
    with pytest.raises(OSError):
        socket.create_connection(("127.0.0.1", port), timeout=1)


def test_stopping_ends_a_tunnel_that_is_open(proxy):
    s = socket.create_connection(("127.0.0.1", proxy.port), timeout=5)
    s.sendall(b"GET /ws HTTP/1.1\r\nHost: x\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n\r\n")
    assert s.recv(4096).startswith(b"HTTP/1.1 101")
    proxy.stop()
    s.settimeout(5)
    assert s.recv(4096) == b""                                                            # the tunnel ended with Play
    s.close()


# -- Play ----------------------------------------------------------------------------------------------------------------------------------------------

def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def host(fake_repo: Path):
    (fake_repo / ".gitignore").write_text(".orkcraft/\n")
    git(fake_repo, "checkout", "-q", "-b", "dev")
    (fake_repo / "index.html").write_bytes(PAGE)
    git(fake_repo, "add", "-A")
    git(fake_repo, "commit", "-q", "-m", "work")
    h = Orkboard(fake_repo)
    yield h
    play = h.ideas._play if h.ideas is not None else None
    if play is not None:
        play.stop("stopped", wait=True)
    h.close()


def settle(host, seconds: float = 25.0) -> dict:
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        got = host.command("ideas.play", {"peek": True})
        if got["state"] != "starting":
            return got
        time.sleep(0.1)
    raise AssertionError("Play never settled")


def fetch(url: str) -> str:
    with urllib.request.urlopen(url, timeout=5) as r:
        return r.read().decode()


def test_play_answers_with_the_proxys_url_and_stops_it_with_play(host):
    host.command("ideas.play", {})
    got = settle(host)
    assert got["state"] == "playing" and got["probe"] is True and re.fullmatch(r"[0-9a-f]{8}", got["play"])
    port = int(got["url"].rsplit(":", 1)[1].split("/")[0])
    assert port != host.ideas.player.port                                                 # not the preview's own port
    assert f"p={got['play']}" in fetch(got["url"]) and "<h1>dev build</h1>" in fetch(got["url"])
    assert fetch(got["url"].rstrip("/") + "/__ork/probe.js").startswith("// The probe")
    host.command("ideas.play_stop", {})
    host.ideas.player.wait()
    with pytest.raises(OSError):
        socket.create_connection(("127.0.0.1", port), timeout=1)
    assert host.command("ideas.play", {"peek": True}) == {"state": "stopped"}


def test_preview_probe_false_leaves_play_as_it_was(host):
    (host.ideas.state_dir).mkdir(parents=True, exist_ok=True)
    (host.ideas.state_dir / "checks.toml").write_text("preview_probe = false\n")
    host.command("ideas.play", {})
    got = settle(host)
    assert got["state"] == "playing" and got["probe"] is False and got["play"] == ""
    assert got["url"] == f"http://127.0.0.1:{host.ideas.player.port}/"                    # the preview's own address
    assert "/__ork/" not in fetch(got["url"])


def test_a_proxy_that_cannot_start_falls_back_to_the_direct_url(host, monkeypatch, caplog):
    def broken(self):
        raise OSError("no port")
    monkeypatch.setattr(play_proxy.PlayProxy, "start", broken)
    with caplog.at_level("WARNING"):
        host.command("ideas.play", {})
        got = settle(host)
    assert got["state"] == "playing" and got["probe"] is False and got["url"] == f"http://127.0.0.1:{host.ideas.player.port}/"
    assert "probe proxy did not start" in caplog.text


# -- the command's lines ------------------------------------------------------------------------------------------------------------------------------

def test_the_commands_lines_are_kept_with_their_time_colour_and_secrets_out():
    tail = play_lines.Tail()
    before = time.time()
    for line in ("ready in 300 ms", "\x1b[32m  ➜ Local: http://127.0.0.1:5173/\x1b[0m", "loaded .env.local", "key sk-abcdefghijkl1234 in use",
                 "reading /home/a/.ssh/id_rsa", "[vite] src/App.tsx hot updated", "   "):
        tail.append(line)
    middle = time.time()
    time.sleep(0.01)
    tail.append("later")
    assert [text for _at, text in tail.lines] == ["ready in 300 ms", "  ➜ Local: http://127.0.0.1:5173/", "[vite] src/App.tsx hot updated", "later"]
    assert all(at >= before for at, _ in tail.lines)
    assert tail.before(middle) == ["ready in 300 ms", "  ➜ Local: http://127.0.0.1:5173/", "[vite] src/App.tsx hot updated"]
    assert tail.before(middle, n=1) == ["[vite] src/App.tsx hot updated"] and tail.before(before - 1) == [] and tail.before()[-1] == "later"
    assert len(tail) == 8                                                                 # the list a failed start shows is as before


def test_only_the_last_four_hundred_lines_are_kept():
    tail = play_lines.Tail()
    for n in range(450):
        tail.append(f"line {n}")
    assert len(tail.lines) == 400 and tail.lines[0][1] == "line 50" and tail.before(n=3) == ["line 447", "line 448", "line 449"]


def test_play_keeps_the_lines_of_a_command_that_prints(fake_repo, tmp_path):
    """A preview command that prints lines: `Play.lines_before` reads them (the command is a stub server, as tests/test_idea_shot.py's)."""
    (fake_repo / ".gitignore").write_text(".orkcraft/\n")
    git(fake_repo, "checkout", "-q", "-b", "dev")
    (fake_repo / "server.py").write_text("import http.server, os, sys\nprint('starting', flush=True)\nprint('token ghp_abcdefgh12345', flush=True)\n"
                                         "print('Local: http://127.0.0.1:%s/' % os.environ['PORT'], flush=True)\n"
                                         "http.server.ThreadingHTTPServer(('127.0.0.1', int(os.environ['PORT'])), http.server.SimpleHTTPRequestHandler).serve_forever()\n")
    (fake_repo / "index.html").write_bytes(PAGE)
    git(fake_repo, "add", "-A")
    git(fake_repo, "commit", "-q", "-m", "work")
    h = Orkboard(fake_repo)
    try:
        (h.ideas.state_dir).mkdir(parents=True, exist_ok=True)
        (h.ideas.state_dir / "checks.toml").write_text(f'preview = "{__import__("sys").executable} server.py"\n')
        h.command("ideas.play", {})
        got = settle(h)
        assert got["state"] == "playing", got
        lines = h.ideas.player.lines_before()
        assert lines[0] == "starting" and any("Local: http://127.0.0.1:" in line for line in lines) and not any("ghp_" in line for line in lines)
        assert h.ideas.player.lines_before(time.time() - 3600) == []
    finally:
        play = h.ideas._play
        if play is not None:
            play.stop("stopped", wait=True)
        h.close()


def test_play_module_is_not_too_long():
    assert len(Path(ideas_assets.__file__).read_text().splitlines()) < 600
