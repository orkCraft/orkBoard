"""The files of a pick (docs/specs/51-pick-one.md §3, §8 A): `GET /media/<goal>/<pick-id>/<file>?s=<signature>` on the page's server and
on the phones' listener: a signed address served with its stored type and the headers of §3, Range (206), and a 404 for a wrong or
missing signature, a name with `..` or `/`, a file the pick does not list and the address of another pick."""
from __future__ import annotations

import asyncio
import http.client
import re
from pathlib import Path

import pytest

from orkboard.gui import media
from orkboard.gui.board_host import Orkboard
from orkboard.gui.server import Server
from tests import pick_files as pf
from tests.test_phones import _pair, _pinned, _serve

PNG, SVG, WAV, TEXT = pf.png(5, 4), pf.svg(), pf.wav(0.5), pf.text("Take it easy.")


@pytest.fixture
def host(fake_repo: Path):
    h = Orkboard(fake_repo)
    yield h
    h.close()


@pytest.fixture
def pick(host, tmp_path: Path) -> dict:
    """k1's first round: a picture, an SVG and a sound; k2's, in another goal, beside it."""
    state = host.ideas.state_dir
    pf.make_pick(state, tmp_path / "s2", {"a.png": pf.png(9, 9), "b.png": pf.png(8, 8)}, slug="other-goal", tid="k2")
    return pf.make_pick(state, tmp_path / "s1", {"a.png": PNG, "b.svg": SVG}, slug="dark-mode") | {"slug": "dark-mode"}


def dirs(host) -> list[Path]:
    return media.state_dirs(host)


def get(host, target: str, range_header: str = "", method: str = "GET") -> media.Reply:
    return media.serve(method, target, range_header, dirs(host))


def headers(reply: media.Reply) -> dict[str, str]:
    return {k.lower(): v for k, v in reply.headers}


# -- the signature ------------------------------------------------------------------------------------------------------

def test_an_address_is_signed_with_a_secret_of_the_process_and_only_its_own_path_is_proved():
    u = media.url("dark-mode", "k1-r1", "a.png")
    path, sig = u.split("?s=")
    assert path == "/media/dark-mode/k1-r1/a.png" and re.fullmatch(r"[0-9a-f]{32}", sig)
    assert media.check(path, sig) and not media.check(path, sig[:-1] + ("0" if sig[-1] != "0" else "1"))
    assert not media.check("/media/dark-mode/k1-r1/b.png", sig) and not media.check(path, "") and not media.check(path, "x")
    assert media.url("dark-mode", "k1-r1", "a.png") == u                                          # the same path, the same proof
    assert media.sign(path) != media.sign(path + "x") and media._SECRET and len(media._SECRET) == 32


# -- serving ------------------------------------------------------------------------------------------------------------

def test_a_signed_address_is_served_with_its_stored_type_and_the_headers_of_the_spec(host, pick):
    reply = get(host, media.url("dark-mode", "k1-r1", "a.png"))
    h = headers(reply)
    assert reply.status == 200 and reply.read() == PNG
    assert h["content-type"] == "image/png" and h["content-length"] == str(len(PNG)) and h["accept-ranges"] == "bytes"
    assert h["cache-control"] == "private, max-age=31536000, immutable" and h["x-content-type-options"] == "nosniff"
    assert h["content-security-policy"] == "sandbox; default-src 'none'"
    assert h["content-disposition"].startswith("inline; filename=") and "a.png" in h["content-disposition"]
    svg = get(host, media.url("dark-mode", "k1-r1", "b.svg"))                                      # an SVG on its own screen runs nothing
    assert headers(svg)["content-type"] == "image/svg+xml" and headers(svg)["content-security-policy"] == "sandbox; default-src 'none'"
    assert svg.read() == SVG


@pytest.mark.parametrize("asked, status, first, last", [
    ("bytes=0-9", 206, 0, 9), ("bytes=10-", 206, 10, None), ("bytes=-12", 206, None, None), ("bytes=5-5", 206, 5, 5),
    ("bytes=0-99999999", 206, 0, None), ("bytes=-99999999", 206, 0, None),
])
def test_a_range_is_a_206_with_its_bytes_so_a_sound_or_a_clip_seeks(host, tmp_path, asked, status, first, last):
    pf.make_pick(host.ideas.state_dir, tmp_path / "w", {"a.wav": pf.wav(1.0), "b.wav": pf.wav(0.5)}, slug="jingle", kind="audio")
    whole = pf.wav(1.0)
    reply = get(host, media.url("jingle", "k1-r1", "a.wav"), asked)
    size = len(whole)
    if first is None:                                                    # a suffix
        first, last = size - 12, size - 1
    last = size - 1 if last is None else min(last, size - 1)
    h = headers(reply)
    assert reply.status == status and h["content-range"] == f"bytes {first}-{last}/{size}"
    assert h["content-length"] == str(last - first + 1) and h["content-type"] == "audio/wav" and h["accept-ranges"] == "bytes"
    assert reply.read() == whole[first:last + 1]


def test_no_signature_a_wrong_one_or_the_signature_of_another_path_is_a_404(host, pick):
    path = "/media/dark-mode/k1-r1/a.png"
    other = media.url("other-goal", "k2-r1", "a.png")
    for target in (path, path + "?s=", path + "?s=deadbeef", path + "?t=" + media.sign(path), path + "?s=" + media.sign(path)[::-1],
                   path + "?s=" + other.split("?s=")[1],                                               # another pick's proof on this path
                   "/media/dark-mode/k1-r1/b.svg?s=" + media.sign(path)):
        reply = get(host, target)
        assert reply.status == 404 and reply.read() == b"Not found", target
        assert "private" not in headers(reply).get("cache-control", "")


def test_the_address_of_another_pick_serves_that_picks_file_only_and_a_file_it_does_not_list_is_a_404(host, pick):
    mine, theirs = media.url("dark-mode", "k1-r1", "a.png"), media.url("other-goal", "k2-r1", "a.png")
    assert get(host, mine).read() == PNG and get(host, theirs).read() == pf.png(9, 9)                   # each its own
    assert get(host, media.url("dark-mode", "k2-r1", "a.png")).status == 404                            # k2's round is in another goal
    assert get(host, media.url("dark-mode", "k1-r2", "a.png")).status == 404                            # a round that was never made
    assert get(host, media.url("dark-mode", "k1-r1", "c.png")).status == 404                            # a name the pick does not list
    assert get(host, media.url("dark-mode", "k1-r1", "pick.json")).status == 404                        # … its own manifest too
    assert get(host, media.url("no-such-goal", "k1-r1", "a.png")).status == 404
    folder = host.ideas.state_dir / "ideas" / "dark-mode" / "picks" / "k1-r1"
    (folder / "extra.png").write_bytes(PNG)                                                             # a file there that the pick never listed
    assert get(host, media.url("dark-mode", "k1-r1", "extra.png")).status == 404
    (folder / "a.png").unlink()
    (folder / "a.png").symlink_to(host.ideas.state_dir.parent / "README.md")                            # a link out of its folder
    assert get(host, mine).status == 404


# -- over HTTP --------------------------------------------------------------------------------------------------------------

def _fetch(origin: str, target: str, headers: dict | None = None, method: str = "GET") -> tuple[int, dict, bytes]:
    host, port = origin.removeprefix("http://").rsplit(":", 1)
    conn = http.client.HTTPConnection(host, int(port), timeout=5)
    try:
        conn.request(method, target, headers=headers or {})
        r = conn.getresponse()
        return r.status, {k.lower(): v for k, v in r.getheaders()}, r.read()
    finally:
        conn.close()


def test_the_pages_server_serves_a_signed_address_without_its_token_and_a_range(host, pick):
    server = Server(host)
    thread = server.start_thread()
    try:
        status, h, body = _fetch(server.origin, media.url("dark-mode", "k1-r1", "a.png"))
        assert (status, body, h["content-type"]) == (200, PNG, "image/png")
        assert h["cache-control"] == "private, max-age=31536000, immutable" and h["x-content-type-options"] == "nosniff"
        assert h["content-security-policy"] == "sandbox; default-src 'none'" and h["accept-ranges"] == "bytes"
        status, h, body = _fetch(server.origin, media.url("dark-mode", "k1-r1", "a.png"), {"Range": "bytes=4-9"})
        assert (status, body, h["content-range"]) == (206, PNG[4:10], f"bytes 4-9/{len(PNG)}")
        assert _fetch(server.origin, "/media/dark-mode/k1-r1/a.png")[0] == 404
        assert _fetch(server.origin, "/media/dark-mode/k1-r1/a.png?s=nope")[0] == 404
        assert _fetch(server.origin, "/media/dark-mode/k1-r1/..%2fa.png?s=" + media.sign("/media/dark-mode/k1-r1/..%2fa.png"))[0] == 404
        assert _fetch(server.origin, media.url("dark-mode", "k1-r1", "a.png"), method="HEAD")[2] == b""
        assert _fetch(server.origin, "/api/version")[0] == 403                                  # the rest of the server is as it was
    finally:
        server.stop()
        thread.join(10)


def _phone_get(address: str, target: str, headers: dict | None = None, method: str = "GET") -> tuple[int, dict, bytes]:
    import http.client as hc
    host, port = address.removeprefix("https://").rsplit(":", 1)
    conn = hc.HTTPSConnection(host, int(port), context=_pinned(), timeout=5)
    try:
        conn.request(method, target, headers=headers or {})
        r = conn.getresponse()
        return r.status, {k.lower(): v for k, v in r.getheaders()}, r.read()
    finally:
        conn.close()


@pytest.mark.asyncio
async def test_the_phones_listener_serves_it_too_with_a_range_and_two_requests_on_one_connection(fake_repo, tmp_path):
    server, task = await _serve(fake_repo)
    try:
        await _pair(server)
        state = server.host.ideas.state_dir
        pf.make_pick(state, tmp_path / "s", {"a.png": PNG, "b.svg": SVG}, slug="dark-mode")
        pf.make_pick(state, tmp_path / "w", {"a.wav": pf.wav(1.0), "b.wav": pf.wav(0.5)}, slug="jingle", kind="audio")
        addr = server.phones.address
        status, h, body = await asyncio.to_thread(_phone_get, addr, media.url("dark-mode", "k1-r1", "a.png"))
        assert (status, body, h["content-type"]) == (200, PNG, "image/png")
        assert h["cache-control"] == "private, max-age=31536000, immutable" and h["x-content-type-options"] == "nosniff"
        assert h["content-security-policy"] == "sandbox; default-src 'none'" and h["accept-ranges"] == "bytes"
        status, h, body = await asyncio.to_thread(_phone_get, addr, media.url("jingle", "k1-r1", "a.wav"), {"Range": "bytes=100-199"})
        assert (status, len(body), h["content-range"]) == (206, 100, f"bytes 100-199/{len(pf.wav(1.0))}")
        assert body == pf.wav(1.0)[100:200]
        status, h, body = await asyncio.to_thread(_phone_get, addr, media.url("dark-mode", "k1-r1", "b.svg"))
        assert (status, h["content-type"], body) == (200, "image/svg+xml", SVG) and "sandbox" in h["content-security-policy"]
        for target in ("/media/dark-mode/k1-r1/a.png", "/media/dark-mode/k1-r1/a.png?s=0", "/media/dark-mode/k1-r2/a.png?s=0",
                       "/media/dark-mode/k1-r1/%2e%2e%2fa.png?s=0"):
            assert (await asyncio.to_thread(_phone_get, addr, target))[0] == 404, target
        assert (await asyncio.to_thread(_phone_get, addr, media.url("dark-mode", "k1-r1", "a.png"), None, "HEAD"))[2] == b""
        raw = await asyncio.to_thread(_phone_keepalive, server, [media.url("dark-mode", "k1-r1", "a.png"), media.url("dark-mode", "k1-r1", "b.svg")])
        assert raw.count(b"HTTP/1.1 200 OK") == 2 and PNG in raw and SVG in raw
    finally:
        server.stop()
        await asyncio.wait_for(task, 10)


def _phone_keepalive(server, targets: list[str]) -> bytes:
    """GETs on one connection, the last one asking to close it: every one answered, in order."""
    import socket
    host, port = server.phones.address.removeprefix("https://").rsplit(":", 1)
    raw = b""
    with socket.create_connection((host, int(port)), timeout=5) as sock, _pinned().wrap_socket(sock, server_hostname=host) as tls:
        for n, target in enumerate(targets):
            last = n == len(targets) - 1
            tls.sendall((f"GET {target} HTTP/1.1\r\nHost: x\r\n" + ("Connection: close\r\n" if last else "") + "\r\n").encode())
            if last:
                while chunk := tls.recv(65536):
                    raw += chunk
                continue
            got = b""
            while b"\r\n\r\n" not in got:
                got += tls.recv(65536)
            head, _, rest = got.partition(b"\r\n\r\n")
            assert b"Connection: keep-alive" in head, head
            length = int(re.search(rb"Content-Length: (\d+)", head).group(1))
            while len(rest) < length:
                rest += tls.recv(65536)
            raw += head + b"\r\n\r\n" + rest
    return raw


# -- a sketch's page (docs/specs/121-the-day-the-morning-and-the-night.md §3) ------------------------------------------------------

PAGE_HTML = b"<!doctype html><title>A</title><style>b{color:red}</style><b>Hi</b><script>document.title='B'</script>"
PAGE_CSP = ("default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:; font-src data:; media-src data:; "
            "base-uri 'none'; form-action 'none'; frame-ancestors 'self'")


def all_values(pairs, name: str) -> list[str]:
    return [v for k, v in pairs if k.lower() == name.lower()]


def _fetch_pairs(origin: str, target: str, https_context=None) -> tuple[int, list[tuple[str, str]], bytes]:
    host, port = origin.removeprefix("https://").removeprefix("http://").rsplit(":", 1)
    conn = http.client.HTTPSConnection(host, int(port), context=https_context, timeout=5) if https_context else http.client.HTTPConnection(host, int(port), timeout=5)
    try:
        conn.request("GET", target)
        r = conn.getresponse()
        return r.status, r.getheaders(), r.read()
    finally:
        conn.close()


def test_the_pages_server_serves_a_sketchs_page_with_its_headers(host, tmp_path):
    pf.make_page_pick(host.ideas.state_dir, tmp_path / 'pg', PAGE_HTML)
    server = Server(host)
    thread = server.start_thread()
    try:
        status, pairs, body = _fetch_pairs(server.origin, media.url("sketched", "sketch-r1", "a.html"))
        assert (status, body) == (200, PAGE_HTML)
        assert all_values(pairs, "Content-Security-Policy") == ["sandbox allow-scripts", PAGE_CSP]
        assert all_values(pairs, "X-Content-Type-Options") == ["nosniff"] and "text/html" in all_values(pairs, "Content-Type")[0]
        assert _fetch_pairs(server.origin, "/media/sketched/sketch-r1/a.html")[0] == 404                      # unsigned: no page
    finally:
        server.stop()
        thread.join(10)


# -- an asset of the project (docs/specs/88-assets-and-play.md §1, §4) ----------------------------------------------------------

def _commit_assets(repo: Path, files: dict[str, bytes]) -> str:
    import subprocess
    for name, data in files.items():
        (repo / name).parent.mkdir(parents=True, exist_ok=True)
        (repo / name).write_bytes(data)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-q", "-m", "assets"], cwd=repo, check=True, capture_output=True)
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def asset_commit(host) -> str:
    return _commit_assets(Path(host.repo_root), {"art/hero.png": PNG, "sfx/jump.wav": pf.wav(1.0), "art/ç a.svg": SVG})


def test_a_signed_asset_is_served_from_its_commit_with_a_range_never_from_the_working_tree(host, asset_commit):
    repo = Path(host.repo_root)
    (repo / "art" / "hero.png").write_bytes(b"the working tree's own")                           # never what is served
    reply = get(host, media.asset_url(asset_commit, "art/hero.png"))
    h = headers(reply)
    assert reply.status == 200 and reply.read() == PNG and h["content-type"] == "image/png"
    assert h["cache-control"] == "private, max-age=31536000, immutable" and h["x-content-type-options"] == "nosniff"
    assert h["content-security-policy"] == "sandbox; default-src 'none'" and h["content-disposition"] == 'inline; filename="hero.png"'
    cached = host.ideas.state_dir / "assets-before" / asset_commit / "art" / "hero.png"
    assert cached.read_bytes() == PNG                                                                  # written once, served from there
    wav = pf.wav(1.0)
    part = get(host, media.asset_url(asset_commit, "sfx/jump.wav"), "bytes=100-199")
    assert part.status == 206 and part.read() == wav[100:200] and headers(part)["content-range"] == f"bytes 100-199/{len(wav)}"
    assert headers(part)["content-type"] == "audio/wav"
    svg = get(host, media.asset_url(asset_commit, "art/ç a.svg"))
    assert svg.status == 200 and svg.read() == SVG and headers(svg)["content-type"] == "image/svg+xml"
    assert headers(svg)["content-disposition"] == 'inline; filename="__a.svg"'

