import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
S = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent; ORK = Path(__file__).resolve().parents[5] / "design-system/orkui/races"
im = Image.open(S / "test-sheet-six.jpg").convert("RGB")
C = [(82, 688), (981, 1593), (1887, 2493)]; R = [(63, 681), (762, 1380)]
names = ["shaman", "dryad", "unicorn", "lich", "imp", "fairy"]
def cut(box, inset=8):
    x0, y0, x1, y1 = box
    t = im.crop((x0 + inset, y0 + inset, x1 - inset, y1 - inset)).convert("RGBA"); px = t.load(); w, h = t.size
    border = [px[x, 0][:3] for x in range(w)] + [px[0, y][:3] for y in range(h)]
    ref = tuple(sorted(c[i] for c in border)[len(border) // 2] for i in range(3))
    seen = set(); st = [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)]
    while st:
        x, y = st.pop()
        if (x, y) in seen or not (0 <= x < w and 0 <= y < h): continue
        if sum(abs(a - b) for a, b in zip(px[x, y][:3], ref)) > 30: continue
        seen.add((x, y)); px[x, y] = (0, 0, 0, 0); st += [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]
    return t.crop(t.getbbox())
heads = {}
for r, (y0, y1) in enumerate(R):
    for c, (x0, x1) in enumerate(C):
        heads[names[r * 3 + c]] = cut((x0, y0, x1, y1))
for n, h in heads.items(): h.save(S / f"{n}.png")
def fit(img, w, h):          # into a w x h box (12:11), keeping its ratio, smooth (the cartoon is not a pixel grid)
    s = min(w / img.width, h / img.height); t = img.resize((max(1, round(img.width * s)), max(1, round(img.height * s))), Image.LANCZOS)
    box = Image.new("RGBA", (w, h)); box.alpha_composite(t, ((w - t.width) // 2, (h - t.height) // 2)); return box
BG = (21, 20, 18, 255); SIZES = [16, 24, 36, 48]
font = ImageFont.load_default()
def sheet(dpr, zoom):
    pad = 10; cw = sum(round(s * 12 / 11) * dpr * zoom + pad for s in SIZES) + pad
    out = Image.new("RGBA", (cw * 2 + 60, (48 * dpr * zoom + pad) * 6 + 40), BG); d = ImageDraw.Draw(out)
    d.text((pad, 4), f"pixel today (left) | cartoon (right) — {'phone, DPR 3' if dpr == 3 else 'desktop, DPR 1'}, shown x{zoom}", fill=(200, 190, 170, 255), font=font)
    y = 24
    for n in names:
        x = pad
        for side in ("pixel", "cartoon"):
            for s in SIZES:
                W, H = round(s * 12 / 11) * dpr, s * dpr
                if side == "pixel":
                    src = Image.open(ORK / f"{n}-laborer@2x.png").convert("RGBA")
                    t = src.resize((W, H), Image.NEAREST)
                else:
                    t = fit(heads[n], W, H)
                t = t.resize((W * zoom, H * zoom), Image.NEAREST)
                out.alpha_composite(t, (x, y + (48 * dpr * zoom - H * zoom)))
                x += W * zoom + pad
            x += 40
        y += 48 * dpr * zoom + pad
    return out
sheet(1, 3).save(S / "compare-desktop.png"); sheet(3, 1).save(S / "compare-phone.png")
print({n: h.size for n, h in heads.items()})
