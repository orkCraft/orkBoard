"""Cut each tile of T1 and H5: background grey to transparent, crop to the head, save at full size."""
import sys
from pathlib import Path
from PIL import Image
S = Path(__file__).parent; SHEETS = S.parent / "sheets"
def bg_like(p, ref):
    return sum(abs(a - b) for a, b in zip(p, ref)) < 28
def cut(im, box, inset=10):
    x0, y0, x1, y1 = box
    t = im.crop((x0 + inset, y0 + inset, x1 - inset, y1 - inset)).convert("RGBA")
    px = t.load(); w, h = t.size
    # the tile's ground: the median of its border
    border = [px[x, 0][:3] for x in range(w)] + [px[x, h - 1][:3] for x in range(w)] + [px[0, y][:3] for y in range(h)] + [px[w - 1, y][:3] for y in range(h)]
    ref = tuple(sorted(c[i] for c in border)[len(border) // 2] for i in range(3))
    # flood from the border so dark ground inside the head (eyes, mouths) stays
    seen = set(); stack = [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)]
    while stack:
        x, y = stack.pop()
        if (x, y) in seen or not (0 <= x < w and 0 <= y < h): continue
        if not bg_like(px[x, y][:3], ref): continue
        seen.add((x, y)); px[x, y] = (0, 0, 0, 0)
        stack += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    return t.crop(t.getbbox()), ref, (x0 + inset, y0 + inset)
t1 = Image.open(SHEETS / "t1-tiers.jpg").convert("RGB"); h5 = Image.open(SHEETS / "h5-heroes.jpg").convert("RGB")
T1C = [(39, 490), (622, 1073), (1205, 1656)]
T1R = [(25, 471), (502, 960), (972, 1370), (1383, 1755), (1767, 2126), (2138, 2497)]
races = ["shaman", "dryad", "knight", "lich", "imp", "gnome-fairy"]; tiers = ["laborer", "warrior", "elder"]
out = Path(sys.argv[1]) if len(sys.argv) > 1 else S / "cut"; out.mkdir(exist_ok=True)
info = {}
for r, (y0, y1) in enumerate(T1R):
    for c, (x0, x1) in enumerate(T1C):
        img, ref, off = cut(t1, (x0, y0, x1, y1))
        img.save(out / f"t1-{races[r]}-{tiers[c]}.png"); info[f"t1-{races[r]}-{tiers[c]}"] = (img.size, ref)
H5C = [(42, 408), (461, 837), (890, 1266), (1319, 1696), (1749, 2114), (2168, 2544)]
H5R = [(25, 457), (498, 918), (970, 1412)]
heroes = ["scene", "spike", "domain", "fitness", "jobwise", "pivot", "appetite", "pillar", "economy", "dungeon-master", "diamond", "atom",
          "sprint", "inclusive", "sprite", "lantern", "store", "position"]
i = 0
for (y0, y1) in H5R:
    for (x0, x1) in H5C:
        img, ref, off = cut(h5, (x0, y0, x1, y1)); img.save(out / f"h5-{i+1:02d}-{heroes[i]}.png"); info[f"h5-{heroes[i]}"] = (img.size, ref); i += 1
for k, v in info.items(): print(k, v)
