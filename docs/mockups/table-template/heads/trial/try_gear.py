"""Gear by code (§288.3), tried: the gear is what a tier's tile adds to the bare one, kept only where it is gear-coloured (iron grey,
violet) plus its outline; laid on a hero from another sheet after aligning the hero's face to the bare head."""
import sys
from pathlib import Path
from PIL import Image, ImageChops
S = Path(__file__).parent; C = Path(sys.argv[1]) if len(sys.argv) > 1 else S / "cut"
def rgba(p): return Image.open(p).convert("RGBA")
def is_gear(px, kind):
    r, g, b, a = px
    if a < 128: return False
    if kind == "elder":   # violet: blue and red over green
        return r > g + 18 and b > g + 18
    mx, mn = max(r, g, b), min(r, g, b)   # iron: low saturation, dark to mid grey
    return mx - mn < 22 and 30 < mx < 150
def gear(race, tier):
    bare, worn = rgba(C / f"t1-{race}-laborer.png"), rgba(C / f"t1-{race}-{tier}.png")
    w, h = worn.size; out = Image.new("RGBA", (w, h)); o = out.load(); wp = worn.load(); bp = bare.load()
    mask = [[False] * h for _ in range(w)]
    for y in range(h):
        for x in range(w):
            p = wp[x, y]
            q = bp[x, y] if x < bare.width and y < bare.height else (0, 0, 0, 0)
            if is_gear(p, tier) and sum(abs(a - b) for a, b in zip(p[:3], q[:3])) > 60: mask[x][y] = True
    R = 9  # the outline: dark pixels within ~one art pixel of the gear
    for y in range(h):
        for x in range(w):
            p = wp[x, y]
            if mask[x][y]: o[x, y] = p
            elif p[3] > 128 and max(p[:3]) < 40:
                if any(mask[xx][yy] for xx in range(max(0, x - R), min(w, x + R + 1), 3) for yy in range(max(0, y - R), min(h, y + R + 1), 3)): o[x, y] = p
    return out
def fit(base, hero, scales, step=4):
    """The scale and offset that lay `hero`'s face over `base`'s (least difference over the base's opaque lower half)."""
    k = 6; b = base.resize((base.width // k, base.height // k), Image.BOX); bp = b.load(); best = None
    pts = [(x, y) for y in range(b.height // 3, b.height) for x in range(b.width // 4, 3 * b.width // 4) if bp[x, y][3] > 200]
    for s in scales:
        hs = hero.resize((max(1, round(hero.width * s / k)), max(1, round(hero.height * s / k))), Image.BOX); hp = hs.load()
        for dx in range(-12, 13):
            for dy in range(-12, 13):
                d = n = 0
                for x, y in pts:
                    X, Y = x - dx, y - dy
                    if 0 <= X < hs.width and 0 <= Y < hs.height and hp[X, Y][3] > 200:
                        d += sum(abs(a - c) for a, c in zip(bp[x, y][:3], hp[X, Y][:3])); n += 1
                    else: d += 300
                if n and (best is None or d < best[0]): best = (d, s, dx * k, dy * k)
    return best
def lay(race, hero_file, out_name):
    bare = rgba(C / f"t1-{race}-laborer.png"); hero = rgba(C / hero_file)
    d, s, dx, dy = fit(bare, hero, [x / 100 for x in range(100, 136, 3)])
    hs = hero.resize((round(hero.width * s), round(hero.height * s)), Image.LANCZOS)
    tiles = []
    for tier in ("laborer", "warrior", "elder"):
        canvas = Image.new("RGBA", (bare.width + 120, bare.height + 120)); canvas.alpha_composite(hs, (60 + dx, 60 + dy))
        if tier != "laborer": canvas.alpha_composite(gear(race, tier), (60, 60))
        bb = canvas.getbbox(); t = canvas.crop(bb); t = t.resize((round(t.width * 44 / t.height), 44), Image.BOX).resize((round(t.width * 44 / t.height) * 4, 176), Image.NEAREST)
        big = canvas.crop(bb); big = big.resize((round(big.width * 300 / big.height), 300), Image.LANCZOS)
        tiles.append((t, big))
    print(out_name, "scale", s, "offset", dx, dy)
    W = sum(b.width for _, b in tiles) + sum(t.width for t, _ in tiles) + 80
    sheet = Image.new("RGBA", (W, 320), (28, 26, 24, 255)); x = 10
    for t, b in tiles: sheet.alpha_composite(b, (x, 10)); x += b.width + 10
    for t, b in tiles: sheet.alpha_composite(t, (x, 70)); x += t.width + 10
    sheet.save(S / out_name)
lay("shaman", "h5-04-fitness.png", "gear-fitness.png")
lay("dryad", "h5-15-sprite.png", "gear-sprite.png")
