"""Cut a Gemini sheet laid as a grid of framed tiles into one PNG a tile, its flat background made clear.

    python3 docs/mockups/mat-scenes/cut_grid.py <sheet> <cols> <rows> <out-dir> <name,name,...> [--white]

Each tile is cropped a little inside its frame; the flat background is cleared by a flood fill from the crop's four corners (so an
object of the background's grey stays opaque); the PNG is trimmed to what is left. With --white the tile is a white silhouette:
alpha from its lightness, colour pure white (a mask for code to tint). Mockup tooling only (Pillow); the final cut is orkUI's.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

MAGIC = (255, 0, 255)


def cut(sheet: Path, cols: int, rows: int, out: Path, names: list[str], white: bool) -> None:
    img = Image.open(sheet).convert("RGB")
    w, h = img.size
    tw, th = w / cols, h / rows
    out.mkdir(parents=True, exist_ok=True)
    for i, name in enumerate(names):
        if not name:
            continue
        c, r = i % cols, i // cols
        inset = 0.06
        box = (int((c + inset) * tw), int((r + inset) * th), int((c + 1 - inset) * tw), int((r + 1 - inset) * th))
        tile = img.crop(box)
        if white:
            a = tile.convert("L").point(lambda v: 0 if v < 150 else (255 if v > 235 else int((v - 150) * 255 / 85)))
            res = Image.new("RGBA", tile.size, (255, 255, 255, 0))
            res.putalpha(a)
        else:
            for seed in [(2, 2), (tile.width - 3, 2), (2, tile.height - 3), (tile.width - 3, tile.height - 3)]:
                if tile.getpixel(seed) != MAGIC:
                    ImageDraw.floodfill(tile, seed, MAGIC, thresh=30)
            res = tile.convert("RGBA")
            px = res.load()
            for y in range(res.height):
                for x in range(res.width):
                    if px[x, y][:3] == MAGIC:
                        px[x, y] = (0, 0, 0, 0)
        bbox = res.getbbox()
        if bbox:
            res = res.crop(bbox)
        res.save(out / f"{name}.png")
        print(out / f"{name}.png", res.size)


if __name__ == "__main__":
    a = sys.argv
    cut(Path(a[1]), int(a[2]), int(a[3]), Path(a[4]), a[5].split(","), "--white" in a)
