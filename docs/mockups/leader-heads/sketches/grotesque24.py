"""The ork shaman on a true 24 x 24 grid in the grotesque round's look (references/12 for the light and the silhouette,
references/11 for the faces): a small dome, ram horns curled tight to the skull, a heavy brow ledge, a huge jaw with two
tusks past the lip, grey-olive skin lit from the upper left, a cold pale rim on the top and the shadowed edges, a braid
with beads from the left horn. Six moods as overlays of the eyes, the brows and the mouth; no signs. A working sketch,
not orkUI art.

    python docs/mockups/leader-heads/sketches/grotesque24.py OUT_DIR
OUT_DIR then holds <mood>-24@2x.png and <mood>-48@2x.png (what shoot_tab.py puts in the tab), big.png and sheet.png."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

N = 24
P = {"O": (10, 9, 8), "R": (196, 214, 198), "r": (150, 166, 150),
     "L": (140, 145, 121), "S": (112, 115, 96), "s": (86, 87, 73), "D": (62, 60, 52), "d": (44, 37, 34),
     "H": (178, 168, 138), "h": (136, 127, 104), "k": (88, 80, 66), "x": (30, 26, 23),
     "T": (224, 214, 190), "t": (168, 158, 136), "W": (230, 226, 210), "P": (10, 9, 8), "M": (42, 28, 32),
     "B": (54, 50, 44), "b": (196, 186, 160), "g": (96, 148, 138), "w": (196, 214, 222)}

# The left half (columns 0-11); the right half is its mirror, then shaded: the light comes from the upper left.
HALF = [
    "............",  # 0
    "..hHHHh.....",  # 1  the horn: a ribbed C out of the temple, round the outside, its tip turned in at the cheek
    ".hHkHHHh.LLL",  # 2  the dome, narrow
    "hHHk..kHhLLL",  # 3
    "hkH....hSLLL",  # 4
    "HhH....SSLLL",  # 5
    "hHk...sSLLLL",  # 6  the brow ledge, lit
    "HhHh..sdddds",  # 7  the sockets in its shadow
    ".khH.sSddddS",  # 8
    "..hHkSSSddSL",  # 9
    "....sSSSSDLL",  # 10 the nose plate, the creases from it to the tusks
    "...sSSSSDsDd",  # 11 the nostrils
    "..sSSSSSDSSs",  # 12
    "..sSSSSSSSSS",  # 13
    "..sSSSSSSSSS",  # 14
    "..sSSSSSSSSS",  # 15 the mouth
    "..sSSSSSSSSS",  # 16
    "..sSSSLLLLLL",  # 17 the jaw's lit plate
    "..ssSSSLLLLL",  # 18
    "...ssSSSSSSS",  # 19
    "....ssssssss",  # 20
    "......sDDDDD",  # 21
    "............",  # 22
    "............",  # 23
]

# Coarser (--rough): a low small dome, a wider brow ledge, a square jaw the whole width, a flat chin; a scar, a wart.
HALF_ROUGH = [
    "............",  # 0
    "..hHHHh.....",  # 1
    ".hHkHHHh....",  # 2
    "hHHk..kHh.LL",  # 3  the dome, low and small
    "hkH....hSLLL",  # 4
    "HhH....SSLLL",  # 5
    "hHk..sSLLLLL",  # 6  the brow ledge, wider
    "HhHhsSddddds",  # 7
    ".khHsSddddDS",  # 8
    "..hHSSSSddSL",  # 9
    "...sSSSSSDLL",  # 10
    "..sSSSSSDsDd",  # 11
    ".sSSSSSSDSSs",  # 12 the jaw spreading to the whole width
    ".sSSSSSSSSSS",  # 13
    ".sSSSSSSSSSS",  # 14
    ".sSSSSSSSSSS",  # 15
    ".sSSSSSSSSSS",  # 16
    ".sSSSSLLLLLL",  # 17
    ".ssSSSLLLLLL",  # 18
    ".ssSSSSSSSSS",  # 19
    "..ssssssssss",  # 20 a flat chin
    "............",  # 21
    "............",  # 22
    "............",  # 23
]
ROUGH = "--rough" in sys.argv
DOWN = {"L": "S", "S": "s", "s": "D", "H": "h", "h": "k"}


def base():
    half = [list(line) for line in (HALF_ROUGH if ROUGH else HALF)]
    g = [[None] * N for _ in range(N)]
    for y, line in enumerate(half):
        for x, c in enumerate(line):
            if c != ".":
                g[y][x] = c
                m = N - 1 - x                                     # the mirror, one tone darker away from the light
                g[y][m] = DOWN.get(c, c) if (m >= 15 or c in "Ll") else c
    # the right cheek and jaw in shadow
    for y in range(11, 21):
        for x in range(18, 22):
            if g[y][x] in ("S", "L"):
                g[y][x] = "s"
    # tusks: out of the lower jaw, past the upper lip, outside the mouth's corners; the right one chipped
    for x, y in ((5, 10), (5, 11), (6, 11), (5, 12), (6, 12), (6, 13), (7, 13), (6, 14), (7, 14), (7, 15), (8, 15)):
        g[y][x] = "T"
    g[13][7] = g[14][7] = g[15][8] = "t"
    for x, y in ((17, 12), (18, 12), (16, 13), (17, 13), (16, 14), (17, 14), (15, 15), (16, 15)):
        g[y][x] = "T"
    g[13][17] = g[14][17] = g[15][16] = g[12][18] = "t"
    # the inner lines that make the face heavy: the brow ledge's shadow, the knot between the brows, the creases,
    # the lower lip over the jutting jaw, the blotches on the dome
    for x in range(6, 18):
        if g[7][x] in ("d", "s", "S"):
            g[7][x] = "O" if x not in (11, 12) else "D"
    g[6][11] = g[6][12] = "D"; g[5][11] = "s"
    for x, y in ((9, 12), (8, 13), (14, 12), (15, 13)):
        g[y][x] = "D"
    for x, y in ((5, 16), (6, 17), (18, 16), (17, 17)):            # the jowls
        g[y][x] = "D"
    g[3][10] = g[4][13] = "S"; g[2][12] = "S"
    if ROUGH:
        for x, y in ((8, 4), (9, 5), (10, 6)):                     # a scar down into the left brow
            g[y][x] = "D"
        g[13][3] = "L"; g[14][3] = "D"                             # a wart
        for y in range(12, 20):                                    # the jaw's corners, square
            g[y][1] = g[y][1] and "s"; g[y][22] = g[y][22] and "D"
    # a crack in the right horn, the braid with its beads from under the left horn
    g[3][22] = g[4][23] = "x"
    for y in range(10, 21):
        g[y][0] = "B"
    g[13][0] = g[16][0] = "b"; g[19][0] = "g"; g[21][0] = "B"
    return g


def rim(g):
    """The cold pale rim: on every top edge and on the right-hand outer edges."""
    o = [r[:] for r in g]
    for y in range(N):
        for x in range(N):
            c = g[y][x]
            if c is None or c in "TtBbgWPMx":
                continue
            up = y == 0 or g[y - 1][x] is None
            right = x >= 12 and (x == N - 1 or g[y][x + 1] is None)
            if up and y <= 6:
                o[y][x] = "R"
            elif right:
                o[y][x] = "r" if y > 8 else "R"
    return o


def outline(g):
    o = [r[:] for r in g]
    for y in range(N):
        for x in range(N):
            if g[y][x] is None and any(0 <= x + dx < N and 0 <= y + dy < N and g[y + dy][x + dx] is not None
                                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                o[y][x] = "O"
    return o


def put(g, pts, c):
    for x, y in pts:
        if 0 <= x < N and 0 <= y < N:
            g[y][x] = c


def row(x0, x1, y):
    return [(x, y) for x in range(x0, x1 + 1)]


def box(x0, x1, y0, y1):
    return [(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)]


L_EYE, R_EYE = (7, 10), (13, 16)


def mood(m):
    g = base()
    if m == "calm":                       # heavy lids over the top half, looking ahead, the mouth shut: unimpressed
        put(g, box(*L_EYE, 8, 9) + box(*R_EYE, 8, 9), "W")
        put(g, row(*L_EYE, 7) + row(*R_EYE, 7), "D")
        put(g, [(9, 9), (14, 9)], "P")
        put(g, row(8, 15, 15), "M"); put(g, [(8, 16), (15, 16)], "M")
    elif m == "focused":                  # the left eye squeezed to a line under a knotted brow, the right one wide and glaring
        put(g, row(7, 10, 6), "d"); put(g, [(10, 7), (9, 7)], "d"); put(g, row(7, 10, 8), "P"); put(g, row(7, 10, 9), "s")
        put(g, box(13, 16, 6, 9), "W"); put(g, [(14, 7), (14, 8)], "P"); put(g, row(13, 16, 5), "d")
        put(g, row(9, 13, 15), "M"); put(g, [(14, 16), (15, 16)], "M")
    elif m == "worried":                  # both eyes wide, pupils tiny, the brows up in the middle, a clenched grimace
        put(g, box(7, 10, 6, 9) + box(13, 16, 6, 9), "W"); put(g, [(9, 8), (14, 8)], "P")
        put(g, [(7, 5), (8, 5), (9, 4), (10, 4), (13, 4), (14, 4), (15, 5), (16, 5)], "d")
        put(g, row(8, 15, 14) + row(8, 15, 16), "M"); put(g, row(8, 15, 15), "T"); put(g, [(10, 15), (13, 15)], "M"); put(g, [(5, 15), (18, 15)], "M")
    elif m == "no":                       # a hard side-eye under flat low brows, the mouth flat and pulled down at one corner
        put(g, row(7, 10, 6) + row(13, 16, 6), "d"); put(g, box(7, 10, 7, 9) + box(13, 16, 7, 9), "W")
        put(g, row(7, 10, 7) + row(13, 16, 7), "D")
        put(g, [(10, 8), (10, 9), (16, 8), (16, 9)], "P")
        put(g, row(8, 15, 15), "M"); put(g, [(14, 16), (15, 16)], "M"); put(g, [(10, 16), (11, 16), (12, 16)], "L")
    elif m == "pleased":                  # smug: relaxed brows, the cheeks push the eyes into upturned slits, a wide crooked grin
        put(g, [(7, 9), (8, 8), (9, 8), (10, 9), (13, 9), (14, 8), (15, 8), (16, 9)], "d")
        put(g, box(7, 10, 7, 7) + box(13, 16, 7, 7), "S")
        put(g, row(6, 9, 10) + row(14, 17, 10), "L")
        put(g, [(5, 13), (18, 12), (18, 13)] + row(8, 15, 14), "M")
        put(g, row(8, 15, 15), "T"); put(g, [(10, 15), (13, 15)], "M"); put(g, row(9, 14, 16), "M")
    elif m == "asleep":                   # the eyes shut as flat lines, the jaw slack and open, a thread of drool
        put(g, row(7, 10, 8) + row(13, 16, 8), "d"); put(g, row(7, 10, 7) + row(13, 16, 7), "s")
        put(g, box(9, 14, 15, 18) + row(10, 13, 14), "M"); put(g, row(10, 13, 18), "d")
        put(g, [(14, 19), (14, 20)], "w")
    return outline(rim(g))


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
    OUT = Path([a for a in sys.argv[1:] if not a.startswith("--")][0]); OUT.mkdir(parents=True, exist_ok=True)
    f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    big = Image.new("RGB", (6 * 210 + 20, 230), (21, 20, 18)); db = ImageDraw.Draw(big)
    sheet = Image.new("RGB", (40 + 6 * 130, 140), (21, 20, 18)); d = ImageDraw.Draw(sheet)
    for i, m in enumerate(MOODS):
        g = mood(m)
        save(g, OUT / f"{m}-24@2x.png", 2); save(g, OUT / f"{m}-36@2x.png", 3); save(g, OUT / f"{m}-48@2x.png", 4)
        a = save(g, None, 8); big.paste(a, (10 + i * 210, 30), a); db.text((10 + i * 210, 6), m, fill=(240, 208, 80), font=f)
        x = 30 + i * 130
        mid = save(g, None, 2); sheet.paste(mid, (x, 40), mid)
        sm = save(g, None, 1); sheet.paste(sm, (x + 60, 52), sm)
        d.text((x, 8), m, fill=(240, 208, 80), font=f)
    d.text((30, 110), "48 px (2 px a cell) · 24 px (1 px a cell)", fill=(170, 166, 160), font=f)
    big.save(OUT / "big.png"); sheet.save(OUT / "sheet.png")
    print(OUT / "big.png")
