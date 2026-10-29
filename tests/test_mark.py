"""Orkboard's mark, the Orkmaster's crowned head (docs/specs/107-what-the-owners-day-said.md §12; orkboard/design/mark.py): the files `python -m orkboard.design.mark` makes are there at their sizes, drawn by whole
numbers with no smoothing (every pixel is one of the head's colours or the office's canvas), the svg is a valid, titled drawing, and the product that runs says which of the two marks it shows (Orkboard's or Orkline's).
The pixel checks need Pillow (a dev extra) and are skipped without it."""
from __future__ import annotations

import http.client
import struct
import xml.etree.ElementTree as ET

import pytest

from orkboard.design import logo, tokens
from orkboard.gui import mac_app, pwa
from orkboard.orkget import profile

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


def test_the_extensions_icon_is_the_256():
    assert (REPO / "vscode" / "media" / "icon.png").read_bytes() == (logo.BOARD / "icon-256.png").read_bytes()


def test_the_svg_is_a_valid_drawing_titled_orkboard_with_crisp_edges():
    root = ET.fromstring((logo.BOARD / "mark.svg").read_text(encoding="utf-8"))
    ns = "{http://www.w3.org/2000/svg}"
    assert root.tag == f"{ns}svg" and root.get("shape-rendering") == "crispEdges"
    assert root.find(f"{ns}title").text == "Orkboard"
    rects = root.findall(f"{ns}rect")
    assert rects and all(r.get("height") == "1" and r.get("fill", "").startswith("#") for r in rects)


def test_nothing_is_smoothed_every_pixel_is_the_heads_or_the_canvas():
    Image = pytest.importorskip("PIL.Image")
    head = Image.open(tokens.ORKUI / "races" / "peon-crown@2x.png").convert("RGBA")
    colours = {p[:3] for _, p in head.getcolors(1000) if p[3] == 255}
    for name in ("icon-512.png", "icon-192.png", "apple-touch-icon.png"):
        image = Image.open(logo.BOARD / name)
        assert image.mode == "RGB" and {p for _, p in image.getcolors(1000)} == colours | {_canvas()}, name       # opaque, on the canvas
    clear = Image.open(logo.BOARD / "icon-256.png").convert("RGBA")
    assert {p[3] for _, p in clear.getcolors(1000)} == {0, 255} and {p[:3] for _, p in clear.getcolors(1000) if p[3] == 255} == colours
    assert clear.getpixel((0, 0))[3] == 0                                                       # clear where nothing is drawn


def test_the_512_is_the_head_at_a_whole_number_of_times_centred():
    """The head is drawn on a 12 × 11 grid (the @2x is 48 × 44, four pixels a head pixel): the 512 holds it 34 times as large (the most that leaves a margin of a fifth), each head pixel a square of one colour."""
    Image = pytest.importorskip("PIL.Image")
    head = Image.open(tokens.ORKUI / "races" / "peon-crown@2x.png").convert("RGBA")
    big, times, (w, h) = Image.open(logo.BOARD / "icon-512.png").convert("RGB"), 34, (12, 11)
    left, top = (512 - w * times) // 2, (512 - h * times) // 2
    for y in range(512):
        for x in range(512):
            ax, ay = (x - left) // times, (y - top) // times
            inside = 0 <= x - left and 0 <= y - top and ax < w and ay < h
            source = head.getpixel((ax * 4, ay * 4)) if inside else (0, 0, 0, 0)
            assert big.getpixel((x, y)) == (source[:3] if source[3] == 255 else _canvas()), (x, y)


def test_the_mark_is_made_again_the_same(tmp_path):
    Image = pytest.importorskip("PIL.Image")
    from orkboard.design import mark
    made = tmp_path / "mark"
    mark.write(made)
    assert {p.name for p in made.iterdir()} == {p.name for p in logo.BOARD.iterdir()}
    for path in made.iterdir():
        if path.suffix == ".png":                                                                # a Pillow's PNG coder may write other bytes, never other pixels
            assert Image.open(path).convert("RGBA").tobytes() == Image.open(logo.BOARD / path.name).convert("RGBA").tobytes(), path.name
        else:
            assert path.read_bytes() == (logo.BOARD / path.name).read_bytes(), path.name


# -- served by the brand ---------------------------------------------------------------------------------------

ORKLINE = profile.Profile(product="orkline", name="Orkline", package="orkcraft", version="0", agent="orkline", manifest="", source="")


def _body(raw: bytes) -> bytes:
    return raw.partition(b"\r\n\r\n")[2]


def test_orkboard_shows_its_own_mark_to_the_phone_and_the_dock():
    for name in logo.PHONE:
        assert _body(pwa.serve("GET", f"/app/{name}")) == (logo.BOARD / name).read_bytes(), name
    assert mac_app.ICON == logo.BOARD / "icon-512.png" and logo.favicon() == logo.BOARD / "favicon.ico"


def test_where_orkline_runs_them_it_keeps_its_ork(monkeypatch):
    monkeypatch.setattr(profile, "_current", ORKLINE)
    for name in logo.PHONE:
        assert _body(pwa.serve("GET", f"/app/{name}")) == (pwa.ROOT / name).read_bytes(), name
    assert logo.favicon() == logo.ROOT / "favicon.ico"


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


def test_the_servers_favicon_is_by_the_brand(fake_repo, monkeypatch):
    assert _favicon(fake_repo) == (logo.BOARD / "favicon.ico").read_bytes()
    monkeypatch.setattr(profile, "_current", ORKLINE)
    assert _favicon(fake_repo) == (logo.ROOT / "favicon.ico").read_bytes()


def test_onboarding_draws_the_mark_by_the_product():
    page = (pwa.ROOT.parent / "js" / "onboarding.js").read_text(encoding="utf-8")
    assert "/ds/logo/orkboard/mark.svg" in page and "/ds/logo/orkcraft-dark.svg" in page          # Orkboard's, and Orkline's as it was
