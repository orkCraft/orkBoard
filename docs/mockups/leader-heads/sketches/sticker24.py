"""A sticker-style ork drawn straight on a 24 x 24 grid (not scaled down): a round blob, big eyes with heavy lids, tusks,
a 2-tone body with a highlight, a 1-cell outline, and one accessory. Moods change only the eyes, brows and mouth.
Variants: the reference's topknot + bow tie, and our shaman's ram horns. A sketch for the conversation, not orkUI art."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
N = 24
C = {
    "out": (38, 62, 48), "g": (150, 190, 100), "gs": (118, 158, 78), "gl": (190, 220, 140),
    "teal": (79, 154, 124), "teals": (59, 125, 99), "teall": (116, 191, 156), "tout": (28, 56, 46),
    "w": (240, 236, 224), "p": (24, 22, 22), "lid": (124, 106, 154), "lids": (96, 80, 124),
    "tusk": (232, 220, 184), "horn": (211, 194, 154), "hornS": (168, 148, 106), "hornO": (90, 74, 50),
    "hair": (58, 52, 48), "tie": (120, 36, 44), "ties": (90, 24, 32), "mouth": (40, 30, 34), "red": (170, 70, 80),
    "z": (200, 200, 230), "sweat": (150, 200, 240),
}


def blank():
    return [[None] * N for _ in range(N)]


def ell(cx, cy, rx, ry, x, y):
    return ((x + .5 - cx) / rx) ** 2 + ((y + .5 - cy) / ry) ** 2 <= 1


def outline(g, col):
    o = [r[:] for r in g]
    for y in range(N):
        for x in range(N):
            if g[y][x] is None and any(0 <= x + dx < N and 0 <= y + dy < N and g[y + dy][x + dx] is not None
                                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                o[y][x] = col
    return o


def head(skin="g", horns=False, topknot=False, tie=False):
    base, shade, light, out = (C["g"], C["gs"], C["gl"], C["out"]) if skin == "g" else (C["teal"], C["teals"], C["teall"], C["tout"])
    g = blank()
    cx, cy, rx, ry = 12, 13.5, 9.6, 8.6
    for y in range(N):
        for x in range(N):
            if ell(cx, cy, rx, ry, x, y):
                g[y][x] = base
                if not ell(cx - 1.2, cy - 1.4, rx - .4, ry - .6, x, y):
                    g[y][x] = shade                                  # the shadow: bottom right
                if ell(cx - 4, cy - 4.5, 3.2, 1.7, x, y):
                    g[y][x] = light                                  # the shine: top left
    if topknot:
        for y, xs in ((1, (11, 12)), (2, (10, 11, 12, 13)), (3, (11, 12)), (4, (12,))):
            for x in xs:
                g[y][x] = C["hair"]
    if horns:                                                        # ram horns curling out of the sides
        L = [(2, 7), (1, 6), (1, 5), (2, 4), (3, 3), (4, 3), (5, 4), (5, 5), (4, 6), (3, 7), (0, 7), (0, 8), (1, 9), (2, 9), (3, 8)]
        for x, y in L:
            for xx in (x, N - 1 - x):
                g[y][xx] = C["horn"]
        for x, y in ((3, 4), (4, 4), (4, 5), (1, 8)):
            for xx in (x, N - 1 - x):
                g[y][xx] = C["hornS"]
    g = outline(g, out)
    if tie:
        for x, y in ((9, 22), (10, 22), (10, 21), (9, 21), (11, 22), (12, 22), (13, 22), (14, 22), (13, 21), (14, 21), (12, 21), (11, 21), (9, 23), (14, 23)):
            g[y][x] = C["tie"]
        for x, y in ((11, 22), (12, 22)):
            g[y][x] = C["ties"]
    return g


def put(g, pts, col):
    for x, y in pts:
        if 0 <= x < N and 0 <= y < N:
            g[y][x] = col


def eyes(g, mood):
    # two big eyes: 5 wide, 4 high, at x 5..9 and 14..18, y 9..12
    for ex in (5, 14):
        if mood in ("pleased", "asleep"):
            arc = [(ex, 11), (ex + 1, 10), (ex + 2, 10), (ex + 3, 10), (ex + 4, 11)] if mood == "pleased" else [(ex, 11), (ex + 1, 11), (ex + 2, 11), (ex + 3, 11), (ex + 4, 11)]
            put(g, arc, C["mouth"]); continue
        white = [(x, y) for y in range(9, 13) for x in range(ex, ex + 5) if not ((x in (ex, ex + 4)) and (y in (9, 12)))]
        put(g, white, C["w"])
        ring = [(ex - 1, 10), (ex - 1, 11), (ex + 5, 10), (ex + 5, 11), (ex, 8), (ex + 4, 8)] + [(x, 8) for x in range(ex + 1, ex + 4)] + [(x, 13) for x in range(ex + 1, ex + 4)] + [(ex, 13), (ex + 4, 13)]
        put(g, ring, C["out"])
        if mood == "calm":                                            # the deadpan: a heavy lid over the top half, the pupil low
            put(g, [(x, 9) for x in range(ex, ex + 5)] + [(x, 10) for x in range(ex, ex + 5)], C["lid"])
            put(g, [(x, 8) for x in range(ex, ex + 5)], C["lids"])
            put(g, [(ex + 2, 11)], C["p"])
        elif mood == "worried":                                       # wide open, tiny pupils, brows up in the middle
            put(g, [(ex + 2, 11)], C["p"])
            brow = [(ex, 7), (ex + 1, 7), (ex + 2, 6), (ex + 3, 6)] if ex == 5 else [(ex + 1, 6), (ex + 2, 6), (ex + 3, 7), (ex + 4, 7)]
            put(g, brow, C["out"])
        elif mood == "no":                                            # brows down to the middle, eyes narrowed
            put(g, [(x, 9) for x in range(ex, ex + 5)], C["lid"])
            put(g, [(ex + 2, 11), (ex + 2, 10)], C["p"])
            brow = [(ex, 6), (ex + 1, 6), (ex + 2, 7), (ex + 3, 7), (ex + 4, 8)] if ex == 5 else [(ex, 8), (ex + 1, 7), (ex + 2, 7), (ex + 3, 6), (ex + 4, 6)]
            put(g, brow, C["out"])
        elif mood == "focused":                                       # one eye squinting, pupils to the side
            if ex == 5:
                put(g, [(x, 9) for x in range(ex, ex + 5)] + [(x, 10) for x in range(ex, ex + 5)] + [(x, 12) for x in range(ex, ex + 5)], C["lid"])
                put(g, [(ex + 3, 11)], C["p"])
            else:
                put(g, [(ex + 3, 10), (ex + 3, 11)], C["p"])


def mouth(g, mood, skin_out):
    if mood == "calm":
        put(g, [(x, 17) for x in range(9, 15)], C["mouth"])
    elif mood == "worried":
        put(g, [(9, 18), (10, 17), (11, 18), (12, 17), (13, 18), (14, 17)], C["mouth"])
        put(g, [(19, 9), (19, 10)], C["sweat"])
    elif mood == "no":
        put(g, [(x, 17) for x in range(8, 16)], C["mouth"]); put(g, [(8, 18), (15, 18)], C["mouth"])
    elif mood == "pleased":
        put(g, [(8, 16), (15, 16)] + [(x, 17) for x in range(9, 15)], C["mouth"]); put(g, [(x, 18) for x in range(10, 14)], C["red"])
    elif mood == "focused":
        put(g, [(x, 17) for x in range(10, 14)], C["mouth"]); put(g, [(14, 16)], C["mouth"])
    elif mood == "asleep":
        put(g, [(11, 17), (12, 17), (11, 18), (12, 18)], C["mouth"]); put(g, [(19, 4), (20, 4), (20, 5), (19, 6), (20, 6)], C["z"])
    # the tusks: up from the jaw, either side of the mouth
    put(g, [(7, 16), (7, 15), (16, 16), (16, 15), (6, 15) if mood == "no" else (7, 14)], C["tusk"])


def draw(skin, horns, topknot, tie, mood):
    g = head(skin, horns, topknot, tie); eyes(g, mood); mouth(g, mood, C["out"]); return g


def save(g, path, cell):
    im = Image.new("RGBA", (N * cell, N * cell), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for y in range(N):
        for x in range(N):
            if g[y][x]:
                d.rectangle([x * cell, y * cell, x * cell + cell - 1, y * cell + cell - 1], fill=g[y][x] + (255,))
    im.save(path)
    return im


MOODS = ["calm", "focused", "worried", "no", "pleased", "asleep"]
sets = [("ork", dict(skin="g", horns=False, topknot=True, tie=True)), ("shaman", dict(skin="t", horns=True, topknot=False, tie=False))]
f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 15)
sheet = Image.new("RGB", (40 + 6 * 130, 40 + 2 * 250), (21, 20, 18)); d = ImageDraw.Draw(sheet)
for r, (name, kw) in enumerate(sets):
    for c, m in enumerate(MOODS):
        g = draw(mood=m, **kw)
        save(g, OUT / f"{name}-{m}.png", 2); save(g, OUT / f"{name}-{m}@2x.png", 4)
        x, y = 30 + c * 130, 30 + r * 250
        big = save(g, OUT / "_tmp.png", 4); sheet.paste(big, (x, y), big)
        mid = save(g, OUT / "_tmp.png", 2); sheet.paste(mid, (x, y + 104), mid)
        sm = save(g, OUT / "_tmp.png", 1); sheet.paste(sm, (x + 60, y + 116), sm)
        d.text((x, y + 160), m, fill=(200, 196, 190), font=f)
sheet.save(OUT / "sheet.png")
print("ok")
