"""Cut a mat's corner props sheet (docs/pictures-cartoon.md, C1 to C8) into four PNGs with a clear background.

A sheet is a 2x2 grid of tiles in grey-brown frames; tile 1 holds the top left corner's prop, 2 the top right's, 3 the bottom
left's, 4 the bottom right's, each lying on a patch of its surface, the rest of the tile flat grey. The grey is made clear by a
flood fill from the tile's empty corner (so a steel blade or a key, grey too, stays opaque), and each PNG is cropped to its prop.

    python3 docs/mockups/mat-scenes/cut.py docs/mockups/mat-scenes/sheets/c2-gate.jpg gate
    -> docs/mockups/mat-scenes/props/gate-tl.png, gate-tr.png, gate-bl.png, gate-br.png

Mockup tooling only (Pillow); the final cut is orkUI's.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).parent / "props"
CORNERS = (("tl", 0, 0), ("tr", 1, 0), ("bl", 0, 1), ("br", 1, 1))
MAGIC = (255, 0, 255)


def lum(p) -> float:
    return 0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]


def walk(img, x, y, dx, dy, limit):
    """From an empty grey point, step until the frame's dark line; return the last point inside."""
    for _ in range(limit):
        nx, ny = x + dx, y + dy
        if lum(img.getpixel((nx, ny))) < 50:
            return x, y
        x, y = nx, ny
    return x, y


def cut(sheet: Path, name: str) -> list[Path]:
    img = Image.open(sheet).convert("RGB")
    w, h = img.size
    tw, th = w // 2, h // 2
    out = []
    for corner, col, row in CORNERS:
        ox, oy = col * tw, row * th
        # the tile's empty side: away from its prop's corner
        ex = ox + (int(tw * 0.8) if col == 0 else int(tw * 0.2))
        ey = oy + (int(th * 0.8) if row == 0 else int(th * 0.2))
        left = walk(img, ex, ey, -1, 0, tw)[0] + 4
        right = walk(img, ex, ey, 1, 0, tw)[0] - 4
        top = walk(img, ex, ey, 0, -1, th)[1] + 4
        bottom = walk(img, ex, ey, 0, 1, th)[1] - 4
        tile = img.crop((left, top, right, bottom))
        seed = (ex - left, ey - top)
        ImageDraw.floodfill(tile, seed, MAGIC, thresh=34)
        rgba = tile.convert("RGBA")
        px = rgba.load()
        for y in range(rgba.height):
            for x in range(rgba.width):
                if px[x, y][:3] == MAGIC:
                    px[x, y] = (0, 0, 0, 0)
        rgba = rgba.crop(rgba.getbbox())
        OUT.mkdir(parents=True, exist_ok=True)
        path = OUT / f"{name}-{corner}.png"
        rgba.save(path)
        out.append(path)
    return out


if __name__ == "__main__":
    for p in cut(Path(sys.argv[1]), sys.argv[2]):
        print(p, Image.open(p).size)
