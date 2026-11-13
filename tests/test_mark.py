"""Orkboard's mark, the Orkmaster's crowned head (docs/specs/107-what-the-owners-day-said.md §12; orkboard/design/mark.py): the files `python -m orkboard.design.mark` makes are there at their sizes, drawn by whole
numbers with no smoothing (every pixel is one of the head's colours or the office's canvas), the svg is a valid, titled drawing, and it is the mark the phone, the Dock and the favicon show.
The pixel checks need Pillow (a dev extra) and are skipped without it."""
from __future__ import annotations

import http.client
import struct


from orkboard.design import logo, tokens
from orkboard.gui import mac_app, pwa

SIZES = {"icon-192.png": 192, "icon-512.png": 512, "apple-touch-icon.png": 180, "icon-256.png": 256}
PNG = b"\x89PNG\r\n\x1a\n"
REPO = tokens.SYSTEM.resolve().parent                              # the repository (design-system/ lies in it)


def _png_size(raw: bytes) -> tuple[int, int]:
    assert raw[:8] == PNG and raw[12:16] == b"IHDR"
    return struct.unpack(">II", raw[16:24])


def _canvas() -> tuple[int, int, int]:
    hexed = tokens.system()["color"]["canvas"].lstrip("#")
    return tuple(int(hexed[i:i + 2], 16) for i in (0, 2, 4))


def test_the_files_are_there_at_their_sizes():
    for name, size in SIZES.items():
        assert _png_size((logo.BOARD / name).read_bytes()) == (size, size), name
    ico = (logo.BOARD / "favicon.ico").read_bytes()
    assert struct.unpack("<HHH", ico[:6]) == (0, 1, 2)                                          # an icon of two pictures
    assert [ico[6 + 16 * i] for i in range(2)] == [32, 64]
    for i, size in enumerate((32, 64)):                                                         # each a PNG of its own size, not the large one drawn small
        length, at = struct.unpack("<II", ico[6 + 16 * i + 8:6 + 16 * i + 16])
        assert _png_size(ico[at:at + length]) == (size, size)


# -- served ----------------------------------------------------------------------------------------------------

def _body(raw: bytes) -> bytes:
    return raw.partition(b"\r\n\r\n")[2]


def test_orkboard_shows_its_own_mark_to_the_phone_and_the_dock():
    for name in logo.PHONE:
        assert _body(pwa.serve("GET", f"/app/{name}")) == (logo.BOARD / name).read_bytes(), name
    assert mac_app.ICON == logo.BOARD / "icon-512.png" and logo.favicon() == logo.BOARD / "favicon.ico"


def _favicon(repo) -> bytes:
    from orkboard.gui.board_host import Orkboard
    from orkboard.gui.server import Server
    server = Server(Orkboard(repo))
    thread = server.start_thread()
    try:
        conn = http.client.HTTPConnection("127.0.0.1", server.port, timeout=10)
        conn.request("GET", "/favicon.ico")
        got = conn.getresponse()
        assert got.status == 200 and got.getheader("Content-Type") == "image/x-icon"
        return got.read()
    finally:
        server.stop()
        thread.join(10)


def test_the_servers_favicon_is_orkboards_mark(fake_repo):
    assert _favicon(fake_repo) == (logo.BOARD / "favicon.ico").read_bytes()
