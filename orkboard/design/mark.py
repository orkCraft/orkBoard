"""Orkboard's mark: the Orkmaster's crowned head (decisions §91, §182.14; docs/specs/107-what-the-owners-day-said.md §12), orkUI's `races/peon-crown@2x.png`, drawn large by whole numbers only, nearest, never smoothed.
The head is a pixel picture: it is read at its own pixel (the @2x is that head twice as large, so the 48 × 44 comes back to 24 × 22) and every icon is that picture at a whole number of times, centred, on a square of the size
asked: the favicon (32 and 64), the phone's icons, the Dock's, VS Code's. A dev tool, never imported when Orkboard runs (Pillow is a dev extra): the files it writes are committed, and `gui/server.py`, `gui/pwa.py` and
`design/logo.py` only serve them.

    python -m orkboard.design.mark         # writes design-system/logo/orkboard/ again (mark.svg, favicon.ico, icon-192.png, icon-512.png, apple-touch-icon.png, icon-256.png)
    mark.build()                           # the same files as {name: bytes}
    mark.fit(art, 512, canvas)             # the picture at the largest whole number that fits 4/5 of the square, centred; `canvas` None: transparent
"""
from __future__ import annotations

import io
import struct
import sys
from pathlib import Path

from orkboard.design import logo, tokens

SOURCE = tokens.ORKUI / "races" / "peon-crown@2x.png"
FILL = (4, 5)                                  # the picture takes at most this much of the square's width: the rest is the icon's margin
TITLE = "Orkboard"
UNIT = 10                                      # px a pixel of the picture is in mark.svg's own size
ICONS = {"icon-192.png": 192, "icon-512.png": 512, "apple-touch-icon.png": 180}       # on the office's canvas (the phone's, the Dock's)
FAVICON = (32, 64)


def _image():
    try:
        from PIL import Image
    except ImportError as e:           # pragma: no cover - the message is the point
        raise SystemExit("Pillow is needed to draw the mark again (pip install pillow): it is a dev tool") from e
    return Image


def canvas() -> tuple[int, int, int, int]:
    """The office's canvas colour, orkUI's own (`tokens.json`), as RGBA."""
    hexed = tokens.system()["color"]["canvas"].lstrip("#")
    return (*(int(hexed[i:i + 2], 16) for i in (0, 2, 4)), 255)


def art():
    """The crowned head at its own pixel: `peon-crown@2x.png` with every block of n × n equal pixels made one (24 × 22 from the 48 × 44). RGBA, each pixel opaque or clear."""
    image = _image().open(SOURCE).convert("RGBA")
    px, (w, h) = image.load(), image.size
    if any(px[x, y][3] not in (0, 255) for x in range(w) for y in range(h)):
        raise ValueError(f"{SOURCE.name} has a pixel that is neither opaque nor clear: it would be smoothed")
    for n in range(min(w, h), 0, -1):
        if w % n or h % n:
            continue
        if all(px[x, y] == px[x - x % n, y - y % n] for x in range(w) for y in range(h)):
            return image.resize((w // n, h // n), _image().NEAREST) if n > 1 else image
    return image


def fit(head, size: int, fill=None):
    """`head` at the largest whole number of times that takes at most FILL of a `size` square's width (one at the least), centred on that square: `fill` its colour, None for clear."""
    Image = _image()
    times = max(1, size * FILL[0] // FILL[1] // head.width)
    big = head.resize((head.width * times, head.height * times), Image.NEAREST)
    out = Image.new("RGBA", (size, size), fill or (0, 0, 0, 0))
    out.paste(big, ((size - big.width) // 2, (size - big.height) // 2), big)
    return out


def png(image, opaque: bool = False) -> bytes:
    out = io.BytesIO()
    (image.convert("RGB") if opaque else image).save(out, "PNG", optimize=True)
    return out.getvalue()


def ico(images: list[bytes], sizes: list[int]) -> bytes:
    """An .ico of PNG pictures, each at its own size as drawn (Pillow would draw the smaller ones from the largest, smoothed)."""
    head, body, at = struct.pack("<HHH", 0, 1, len(images)), b"", 6 + 16 * len(images)
    entries = b""
    for data, size in zip(images, sizes):
        entries += struct.pack("<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(data), at + len(body))
        body += data
    return head + entries + body


def svg(head) -> str:
    """mark.svg: a `rect` for every run of one colour in a row of the picture (a pixel at the least), crisp edges, titled."""
    px, rects = head.load(), []
    for y in range(head.height):
        x = 0
        while x < head.width:
            colour = px[x, y]
            if colour[3] == 0:
                x += 1
                continue
            end = x + 1
            while end < head.width and px[end, y] == colour:
                end += 1
            rects.append(f'<rect x="{x}" y="{y}" width="{end - x}" height="1" fill="#{colour[0]:02x}{colour[1]:02x}{colour[2]:02x}"/>')
            x = end
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {head.width} {head.height}" width="{head.width * UNIT}" height="{head.height * UNIT}" shape-rendering="crispEdges" role="img">'
            f'<title>{TITLE}</title>{"".join(rects)}</svg>\n')


def build() -> dict[str, bytes]:
    head, ground = art(), canvas()
    files = {"mark.svg": svg(head).encode("utf-8"),
             "favicon.ico": ico([png(fit(head, s)) for s in FAVICON], list(FAVICON)),
             "icon-256.png": png(fit(head, 256))}
    for name, size in ICONS.items():
        files[name] = png(fit(head, size, ground), opaque=True)
    return files


def write(folder: Path = logo.BOARD) -> list[Path]:
    folder.mkdir(parents=True, exist_ok=True)
    out = []
    for name, data in build().items():
        (folder / name).write_bytes(data)
        out.append(folder / name)
    return out


def main(argv: list[str] | None = None) -> int:
    for path in write():
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
