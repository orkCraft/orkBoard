"""The ork shaman on a true 24 x 24 grid, ugly-cute: a head like an upturned pear (a low narrow forehead, a huge jaw),
a heavy brow with the eyes in its shadow and bags under them, a flat pig's nose, an underbite with a big tusk and a chipped
one, a wart, a scar through one brow, stubble, ram's horns out of the forehead sweeping down beside the jaw, a braid with
bone beads. Six moods as overlays (eyes, brows, mouth, one sign). A working sketch, not orkUI art. Usage: OUT_DIR"""
import math
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
N = 24
P = {"O": (22, 18, 15), "S": (74, 146, 116), "s": (55, 116, 92), "l": (106, 176, 142), "D": (36, 82, 64),
     "H": (214, 198, 150), "h": (166, 146, 100), "k": (118, 100, 68), "W": (238, 232, 214), "P": (18, 14, 12),
     "T": (226, 212, 162), "t": (178, 160, 108), "M": (44, 20, 20), "R": (136, 58, 58), "B": (50, 62, 54),
     "b": (200, 184, 140), "w": (150, 200, 238), "v": (226, 242, 252), "y": (240, 216, 116)}

# the head's skin, row by row: (first column, last column)
SPAN = {3: (9, 14), 4: (8, 15), 5: (7, 16), 6: (6, 17), 7: (6, 17), 8: (6, 17), 9: (6, 17), 10: (5, 18), 11: (5, 18),
        12: (4, 19), 13: (4, 19), 14: (3, 20), 15: (3, 20), 16: (3, 20), 17: (3, 20), 18: (4, 19), 19: (4, 19), 20: (5, 18),
        21: (7, 16)}


def put(g, pts, c):
    for x, y in pts:
        if 0 <= x < N and 0 <= y < N:
            g[y][x] = c


def row(x0, x1, y):
    return [(x, y) for x in range(x0, x1 + 1)]


def thick(pts, w):
    out = set()
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(abs(x1 - x0), abs(y1 - y0)) * 4 + 1
        for i in range(n + 1):
            x = x0 + (x1 - x0) * i / n; y = y0 + (y1 - y0) * i / n
            for dx in range(w):
                for dy in range(w):
                    out.add((int(round(x)) + dx - w // 2, int(round(y)) + dy - w // 2))
    return out


def base():
    g = [[None] * N for _ in range(N)]
    for y, (a, b) in SPAN.items():
        put(g, row(a, b, y), "S")
        put(g, [(b, y), (b - 1, y)], "s")                        # the shade down the right side
    put(g, row(8, 11, 3) + row(8, 10, 4), "l")                    # the light on the low forehead
    for y in (19, 20):                                            # under the jaw
        a, b = SPAN[y]; put(g, row(a, b, y), "s")
    put(g, row(7, 16, 21), "s")
    # the brow: a lit ridge wider than the forehead, a deep shadow under it where the eyes sit
    put(g, row(6, 17, 6), "S"); put(g, row(7, 9, 6), "l")
    put(g, row(6, 17, 7), "D")
    put(g, [(15, 5), (16, 6), (16, 7)], "D")                      # the scar through the right brow
    # bags under the eyes
    put(g, row(7, 10, 10) + row(13, 16, 10), "s")
    # the pig's nose: a flat plate, lit on top, two nostrils far apart
    put(g, row(10, 13, 11), "l"); put(g, row(10, 13, 12), "S"); put(g, [(10, 12), (13, 12)], "D"); put(g, row(11, 12, 10), "s")
    # the upper lip's crease and the jaw's bulk
    put(g, row(6, 17, 15), "s")
    # a wart on the left cheek, stubble on the chin
    put(g, [(5, 12)], "D"); put(g, [(5, 11)], "l")
    put(g, [(8, 19), (11, 20), (14, 19), (16, 18)], "D")
    # ears, small, under the horns
    put(g, [(4, 9), (5, 9), (3, 10), (4, 10)], "S"); put(g, [(18, 9), (19, 9), (19, 10), (20, 10)], "s")
    # the horns: out of the forehead's corners, up, round the outside and down beside the jaw, the tip pointing forward
    L = [(8, 3), (6, 1), (3, 1), (1, 3), (1, 7), (2, 10), (4, 12)]
    horn = {(x, y) for x, y in thick(L, 3) if 0 <= x < N and 0 <= y < N and (y not in SPAN or not (SPAN[y][0] <= x <= SPAN[y][1]) or y <= 4)}
    for mirror in (False, True):
        for x, y in horn:
            xx = N - 1 - x if mirror else x
            a = math.atan2(y + .5 - 5.5, x + .5 - 4)
            c = "h" if (y >= 7 and x <= 2) or y >= 10 else "H"
            if (a % (math.pi / 4)) < 0.2 and 1 <= y <= 11:
                c = "k"
            put(g, [(xx, y)], c)
    put(g, [(2, 2), (3, 3), (3, 4)], "O")                         # a crack in the left horn
    # the braid from behind the right horn's tip, down the jaw
    put(g, [(21, y) for y in range(12, 21)] + [(22, y) for y in range(12, 21)], "B")
    put(g, [(21, 15), (22, 15), (21, 18), (22, 18)], "b"); put(g, [(21, 21)], "B")
    return g


def outline(g):
    o = [r[:] for r in g]
    for y in range(N):
        for x in range(N):
            if g[y][x] is None and any(0 <= x + dx < N and 0 <= y + dy < N and g[y + dy][x + dx] is not None
                                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                o[y][x] = "O"
    return o


def tusks(g, lip=16, chipped=True):
    """Out of the lower jaw past the upper lip: a big one on the left, a chipped one on the right."""
    put(g, [(6, lip - 1), (7, lip - 1), (6, lip - 2), (7, lip - 2), (6, lip - 3), (7, lip - 3), (7, lip - 4)], "T")
    put(g, [(7, lip - 1)], "t")
    put(g, [(16, lip - 1), (17, lip - 1), (16, lip - 2), (17, lip - 2)] + ([] if chipped else [(16, lip - 3)]), "T")
    put(g, [(17, lip - 1)], "t"); put(g, [(17, lip - 2)], "t")


def eyes_small(g, lids=True, pupils=((9, 9), (15, 9))):
    """The everyday eyes: a slit of white under heavy lids, in the brow's shadow; the right one a row bigger."""
    put(g, row(7, 10, 9) + row(13, 16, 9) + row(13, 16, 10), "W")
    if lids:
        put(g, row(7, 10, 8) + row(13, 16, 8), "s")
    put(g, list(pupils), "P")


def mood(m):
    g = base()
    if m == "calm":                                               # grumpy deadpan
        eyes_small(g)
        put(g, row(7, 16, 16), "M"); put(g, [(6, 17), (17, 17)], "M"); tusks(g)
    elif m == "focused":                                          # the suspicious squint: one eye a line, the other wide, its brow up
        put(g, row(7, 10, 8), "s"); put(g, row(7, 10, 9), "O"); put(g, [(9, 9)], "W")
        put(g, row(13, 16, 8) + row(13, 16, 9) + row(13, 16, 10), "W"); put(g, [(13, 8), (13, 9)], "P")
        put(g, row(13, 16, 5) + [(12, 6)], "O")
        put(g, row(10, 15, 16), "M"); put(g, [(15, 15), (16, 15)], "M"); tusks(g)
    elif m == "worried":                                          # eyes too big, pupils tiny, brows up in the middle, a forced grin, sweat
        put(g, row(7, 10, 7) + row(7, 10, 8) + row(7, 10, 9) + row(13, 16, 7) + row(13, 16, 8) + row(13, 16, 9), "W")
        put(g, [(7, 7), (10, 7), (13, 7), (16, 7), (7, 9), (10, 9), (13, 9), (16, 9)], "D")
        put(g, [(9, 8), (14, 8)], "P")
        put(g, [(7, 6), (8, 6), (9, 5), (10, 5), (13, 5), (14, 5), (15, 6), (16, 6)], "O")
        put(g, row(5, 18, 15) + row(5, 18, 17), "M"); put(g, row(6, 17, 16), "T"); put(g, [(8, 16), (11, 16), (14, 16)], "M")
        put(g, [(4, 16), (19, 16)], "M")
        put(g, [(20, 4), (20, 5), (19, 5), (21, 5), (20, 6)], "w")
    elif m == "no":                                               # judging side-eye: lids down, pupils in the right corners, brows to the middle
        put(g, row(7, 10, 8) + row(13, 16, 8), "s"); put(g, row(7, 10, 9) + row(13, 16, 9), "W"); put(g, [(10, 9), (16, 9)], "P")
        put(g, [(7, 6), (8, 6), (9, 7), (10, 7), (13, 7), (14, 7), (15, 6), (16, 6)], "O")
        put(g, [(11, 10), (12, 10)], "D")                         # the nose wrinkled
        put(g, row(6, 17, 16), "M"); put(g, [(5, 17), (18, 17)], "M"); tusks(g)
    elif m == "pleased":                                          # smug: eyes shut in arcs, a wide toothy grin, a sparkle
        put(g, row(8, 9, 8) + [(7, 9), (10, 9)] + row(14, 15, 8) + [(13, 9), (16, 9)], "O")
        put(g, row(5, 18, 15) + [(4, 14), (19, 14)], "M"); put(g, row(6, 17, 16), "T"); put(g, [(9, 16), (13, 16)], "M")
        put(g, row(6, 17, 17), "M"); put(g, row(9, 14, 18), "R"); put(g, row(8, 15, 19), "M")
        put(g, [(6, 13), (6, 14), (17, 13), (17, 14)], "T")
        put(g, [(12, 0), (11, 1), (12, 1), (13, 1), (12, 2)], "y")
    elif m == "asleep":                                           # eyes as lines, the jaw dropped, a snot bubble out of the nose
        put(g, row(7, 10, 8) + row(13, 16, 8), "s"); put(g, row(7, 10, 9) + row(13, 16, 9), "O")
        put(g, row(9, 14, 16) + row(9, 14, 17) + row(10, 13, 18), "M"); put(g, row(10, 13, 17), "R"); tusks(g)
        bub = [(x, y) for y in range(11, 17) for x in range(14, 20) if (x - 16.5) ** 2 + (y - 13.5) ** 2 <= 5.5]
        put(g, bub, "w"); put(g, [(15, 12)], "v")
    return outline(g)


def save(g, path, cell):
    im = Image.new("RGBA", (N * cell, N * cell), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for y in range(N):
        for x in range(N):
            if g[y][x]:
                d.rectangle([x * cell, y * cell, x * cell + cell - 1, y * cell + cell - 1], fill=P[g[y][x]] + (255,))
    if path:
        im.save(path)
    return im


MOODS = ["calm", "focused", "worried", "no", "pleased", "asleep"]
if __name__ == "__main__":
    f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    big = Image.new("RGB", (6 * 200 + 20, 230), (21, 20, 18)); db = ImageDraw.Draw(big)
    sheet = Image.new("RGB", (40 + 6 * 130, 230), (21, 20, 18)); d = ImageDraw.Draw(sheet)
    for i, m in enumerate(MOODS):
        g = mood(m)
        save(g, OUT / f"{m}-24.png", 1); save(g, OUT / f"{m}-24@2x.png", 2)
        save(g, OUT / f"{m}-48.png", 2); save(g, OUT / f"{m}-48@2x.png", 4)
        a = save(g, None, 8); big.paste(a, (10 + i * 200, 30), a); db.text((10 + i * 200, 6), m, fill=(240, 208, 80), font=f)
        x = 30 + i * 130
        mid = save(g, None, 2); sheet.paste(mid, (x, 40), mid)
        sm = save(g, None, 1); sheet.paste(sm, (x + 60, 52), sm)
        d.text((x, 8), m, fill=(240, 208, 80), font=f)
    d.text((30, 120), "48 px (2 px a cell) · 24 px (1 px a cell)", fill=(170, 166, 160), font=f)
    big.save(OUT / "big.png"); sheet.save(OUT / "sheet.png")
    print("ok")
