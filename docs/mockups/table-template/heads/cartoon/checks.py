"""The check pictures for the owner (§289): `python3 -I checks.py` after `cut_cartoon.py` and `member_tiers.py`.

Heads are drawn into the window's head boxes (48 x 44, 36 x 33, 24 x 22 px; 16 x 15 from the K2 drawing), bottom-centred,
smooth, on the room's dark #1a1816. DPR 1 is drawn at the CSS size and the whole picture is then scaled x3 with nearest
neighbour so it can be inspected; the phone picture is drawn at DPR 3 (the head at 3x its CSS size, smooth).
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
CUT = HERE / "cut"
OUT = HERE / "checks"
BG = (26, 24, 22, 255)
INK = (200, 190, 170, 255)
DIM = (140, 132, 118, 255)
BOXES = {48: (48, 44), 36: (36, 33), 24: (24, 22), 16: (16, 15)}
RACES = ["shaman", "dryad", "knight", "lich", "imp", "gnome-fairy", "orkmaster", "grunt"]
MOODS = ["focused", "worried", "no", "pleased", "asleep"]
OFF = json.loads((CUT / "offsets.json").read_text())
try:
    FONT = ImageFont.load_default(size=13)
    FONT_S = ImageFont.load_default(size=11)
except TypeError:                                        # an old Pillow: the bitmap font
    FONT = FONT_S = ImageFont.load_default()


def load(name):
    return Image.open(CUT / f"{name}.png").convert("RGBA")


def smooth(im, w, h):
    """Resize with premultiplied alpha, so no dark fringe comes in from the transparent pixels."""
    w, h = max(1, round(w)), max(1, round(h))
    return im.convert("RGBa").resize((w, h), Image.LANCZOS).convert("RGBA")


def union(names):
    """The box of several tiles of one sheet in the frame's coordinates: (x0, y0, x1, y1)."""
    xs0, ys0, xs1, ys1 = [], [], [], []
    for n in names:
        im = load(n)
        x, y = OFF[n]
        xs0.append(x); ys0.append(y); xs1.append(x + im.width); ys1.append(y + im.height)
    return min(xs0), min(ys0), max(xs1), max(ys1)


def draw_set(canvas, names, ref_names, cell_x, base_y, box, dpr, headroom=0):
    """Draw the heads `names` (tiles of one sheet) in one cell at one scale, taken from `ref_names`' union box, bottom-centred
    on that box; each head sits where it is in its tile, so the eye line and the top line are one."""
    bw, bh = box[0] * dpr, box[1] * dpr
    ux0, uy0, ux1, uy1 = union(ref_names)
    s = min(bw / (ux1 - ux0), bh / (uy1 - uy0))
    px0 = cell_x + (bw - (ux1 - ux0) * s) / 2          # where the union box's left edge goes
    py0 = base_y - (uy1 - uy0) * s                      # ... and its top
    for n in names:
        im = load(n)
        x, y = OFF[n]
        t = smooth(im, im.width * s, im.height * s)
        canvas.alpha_composite(t, (round(px0 + (x - ux0) * s), round(py0 + (y - uy0) * s)))


def bare_and_moods(dpr, path):
    gap_g, pad = 16, 4
    sizes = [48, 36, 24]
    cell_w = {s: BOXES[s][0] for s in BOXES}
    row_h = 44 + 8
    # x positions of every cell (CSS px)
    xs, x = {}, 0
    for s in sizes:
        for i in range(6):
            xs[(s, i)] = x
            x += cell_w[s] + pad
        x += gap_g
    xs[(16, 0)] = x
    W = x + cell_w[16] + 2
    H = row_h * len(RACES) + 4
    canvas = Image.new("RGBA", (W * dpr, H * dpr), BG)
    for r, race in enumerate(RACES):
        base = (r * row_h + 48) * dpr
        mood_names = [f"mood-{race}-{m}" for m in MOODS]
        for s in sizes:
            draw_set(canvas, [f"bare-{race}"], [f"bare-{race}"], xs[(s, 0)] * dpr, base, BOXES[s], dpr)
            for i, mn in enumerate(mood_names):
                draw_set(canvas, [mn], mood_names, xs[(s, i + 1)] * dpr, base, BOXES[s], dpr)
        draw_set(canvas, [f"small-{race}"], [f"small-{race}"], xs[(16, 0)] * dpr, base, BOXES[16], dpr)
    zoom = 3 if dpr == 1 else 1
    if zoom > 1:
        canvas = canvas.resize((canvas.width * zoom, canvas.height * zoom), Image.NEAREST)
    k = zoom * dpr                                       # final px per CSS px
    left, top = 130, 58
    out = Image.new("RGBA", (left + canvas.width + 10, top + canvas.height + 10), BG)
    out.alpha_composite(canvas, (left, top))
    d = ImageDraw.Draw(out)
    title = ("DPR 1, drawn at CSS size, picture scaled x3 (nearest)" if dpr == 1 else "DPR 3, the head drawn at 3x its CSS size, smooth")
    d.text((8, 6), f"calm + 5 moods at 48 / 36 / 24 px, and the K2 head at 16 px  |  {title}", fill=INK, font=FONT)
    for s in sizes:
        d.text((left + xs[(s, 0)] * k, 24), f"{s} px", fill=INK, font=FONT)
        for i, lab in enumerate(["calm"] + MOODS):
            d.text((left + xs[(s, i)] * k + 2, 42 + (i % 2) * 0), lab, fill=DIM, font=FONT_S)
    d.text((left + xs[(16, 0)] * k, 24), "16 px (K2)", fill=INK, font=FONT)
    for r, race in enumerate(RACES):
        d.text((8, top + (r * row_h + 30) * k), race, fill=INK, font=FONT)
    out.convert("RGB").save(path)
    print(path.name, out.size)


def tier_cells(canvas, names, cell_x, base_y, box, dpr, ref):
    """The three tiers of one person at one scale (the bare's), side by side."""
    bw, bh = box[0] * dpr, box[1] * dpr
    ux0, uy0, ux1, uy1 = union([ref])
    s = min(bw / (ux1 - ux0), bh / (uy1 - uy0))
    cw = bw + 16 * dpr
    for i, n in enumerate(names):
        px0 = cell_x + i * cw + 8 * dpr + (bw - (ux1 - ux0) * s) / 2
        py0 = base_y - (uy1 - uy0) * s
        im = load(n)
        x, y = OFF[n]
        t = smooth(im, im.width * s, im.height * s)
        canvas.alpha_composite(t, (round(px0 + (x - ux0) * s), round(py0 + (y - uy0) * s)))
    return cw * len(names)


PEOPLE = [("shaman", "grunt"), ("dryad", "elf"), ("knight", "knight"), ("lich", "skeleton"), ("imp", "goblin"),
          ("gnome-fairy", "gnome")]
TIERS = ("laborer", "warrior", "elder")


def tiers(path):
    dpr, zoom = 1, 3
    head, rowh = 26, 74                                   # headroom for a plume
    sizes = [48, 24]
    width = 0
    # one row: leader at 48, leader at 24, member at 48, member at 24
    W = sum((BOXES[s][0] + 16) * 3 + 14 for s in sizes) * 2 + 4
    canvas = Image.new("RGBA", (W, rowh * 6 + 4), BG)
    xs = []
    for r, (leader, member) in enumerate(PEOPLE):
        x = 0
        base = r * rowh + head + 44 + 2
        for who, kind in ((leader, "leader"), (member, "member")):
            for s in sizes:
                if kind == "leader":
                    names, ref = [f"tier-{who}-{t}" for t in TIERS], f"tier-{who}-laborer"
                else:
                    names, ref = [f"member-{who}-{t}" for t in TIERS], f"member-{who}-laborer"
                x += tier_cells(canvas, names, x, base, BOXES[s], dpr, ref) + 14
                if r == 0:
                    xs.append((x, kind, s))
    canvas = canvas.resize((canvas.width * zoom, canvas.height * zoom), Image.NEAREST)
    left, top = 130, 58
    out = Image.new("RGBA", (left + canvas.width + 10, top + canvas.height + 10), BG)
    out.alpha_composite(canvas, (left, top))
    d = ImageDraw.Draw(out)
    d.text((8, 6), "tiers (laborer, warrior, elder) at 48 and 24 px, x3 nearest: leaders, then members (gear by code)", fill=INK, font=FONT)
    x = 0
    for kind in ("leader", "member"):
        for s in sizes:
            d.text((left + x * zoom, 28), f"{kind} {s}", fill=INK, font=FONT)
            for i, t in enumerate(TIERS):
                d.text((left + (x + i * (BOXES[s][0] + 16)) * zoom + 4, 44), t[:4], fill=DIM, font=FONT_S)
            x += (BOXES[s][0] + 16) * 3 + 14
    for r, (leader, member) in enumerate(PEOPLE):
        d.text((8, top + (r * rowh + head + 14) * zoom), f"{leader}", fill=INK, font=FONT)
        d.text((8, top + (r * rowh + head + 14) * zoom + 16), f"/ {member}", fill=DIM, font=FONT)
    out.convert("RGB").save(path)
    print(path.name, out.size)


HEROES = ["scene", "spike", "domain", "fitness", "jobwise", "pivot", "appetite", "pillar", "economy", "dungeon-master",
          "diamond", "atom", "sprint", "inclusive", "sprite", "lantern", "store", "position"]


def heroes(path):
    zoom = 3
    cols, rows = 6, 3
    cw, rh = 48 + 4 + 24 + 12, 44 + 20
    canvas = Image.new("RGBA", (cols * cw, rows * rh), BG)
    for i, h in enumerate(HEROES):
        r, c = divmod(i, cols)
        im = load(f"hero-{h}")
        x, base = c * cw, r * rh + 44 + 2
        for j, s in enumerate((48, 24)):
            bw, bh = BOXES[s]
            k = min(bw / im.width, bh / im.height)
            t = smooth(im, im.width * k, im.height * k)
            canvas.alpha_composite(t, (x + (0 if s == 48 else 52) + (bw - t.width) // 2, base - t.height))
    canvas = canvas.resize((canvas.width * zoom, canvas.height * zoom), Image.NEAREST)
    top = 36
    out = Image.new("RGBA", (canvas.width + 10, top + canvas.height + 10), BG)
    out.alpha_composite(canvas, (5, top))
    d = ImageDraw.Draw(out)
    d.text((8, 6), "the 18 heroes at 48 and 24 px, fitted whole (with their tool) into the head box, x3 nearest", fill=INK, font=FONT)
    for i, h in enumerate(HEROES):
        r, c = divmod(i, cols)
        d.text((5 + c * cw * zoom, top + (r * rh + 50) * zoom), h, fill=DIM, font=FONT_S)
    out.convert("RGB").save(path)
    print(path.name, out.size)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    bare_and_moods(1, OUT / "bare-and-moods-at-sizes.png")
    bare_and_moods(3, OUT / "bare-and-moods-at-sizes-phone-dpr3.png")
    tiers(OUT / "tiers.png")
    heroes(OUT / "heroes.png")
