"""A Gemini sheet of one leader's six moods (3 x 2 cells on a flat dark ground) cut into heads, each fitted to the window's
sizes (24 x 22, 36 x 33, 48 x 44, snapped to pixels and to 12 colours), and a sheet beside today's heads.

    python docs/mockups/leader-heads/sketches/check_sheet.py SHEET.jpg OUT_DIR [today's race, default shaman-elder]
OUT_DIR then holds <mood>-<width>@2x.png (what shoot_tab.py puts in the tab) and sizes.png."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

src = Image.open(sys.argv[1]).convert("RGB"); out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
race = sys.argv[3] if len(sys.argv) > 3 else "shaman-elder"
RACES = Path(__file__).resolve().parents[4] / "design-system" / "orkui" / "races"
W, H = src.size; bg = src.getpixel((5, 5))
MOODS = ["calm", "focused", "worried", "no", "pleased", "asleep"]
for i, m in enumerate(MOODS):
    cx, cy = i % 3, i // 3
    cell = src.crop((cx * W // 3, cy * H // 2, (cx + 1) * W // 3, (cy + 1) * H // 2))
    mask = Image.new("L", cell.size, 0); px = cell.load(); mp = mask.load()
    for y in range(cell.height):
        for x in range(cell.width):
            r, g, b = px[x, y]
            if abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2]) > 40:
                mp[x, y] = 255
    box = mask.getbbox(); head = cell.crop(box).convert("RGBA"); head.putalpha(mask.crop(box))
    for w, h in ((24, 22), (36, 33), (48, 44)):
        k = min(w / head.width, h / head.height); tw, th = max(1, round(head.width * k)), max(1, round(head.height * k))
        small = head.resize((tw, th), Image.BOX)
        a = small.getchannel("A").point(lambda v: 255 if v > 120 else 0)
        q = small.convert("RGB").quantize(colors=12, method=Image.Quantize.MEDIANCUT).convert("RGB")
        tile = Image.new("RGBA", (tw, th)); tile.paste(q, mask=a)
        o = Image.new("RGBA", (w, h), (0, 0, 0, 0)); o.paste(tile, ((w - tw) // 2, h - th), tile)
        o.resize((w * 2, h * 2), Image.NEAREST).save(out / f"{m}-{w}@2x.png")
f = ImageFont.truetype("DejaVuSans-Bold.ttf", 16) if Path("/usr/share/fonts/truetype/dejavu").exists() else ImageFont.load_default()
sh = Image.new("RGB", (190 + 6 * 120, 600), (21, 20, 18)); d = ImageDraw.Draw(sh); y = 26
for w, h, lab in ((24, 22, "24 px"), (36, 33, "36 px"), (48, 44, "48 px")):
    d.text((10, y + 10), lab, fill=(240, 208, 80), font=f); d.text((10, y + 34), "today", fill=(170, 166, 160), font=f)
    d.text((10, y + 34 + h * 2 + 12), "new", fill=(170, 166, 160), font=f)
    for i, m in enumerate(MOODS):
        x = 190 + i * 120; name = race if m == "calm" else f"{race}-{m}"
        p = RACES / f"{name}.png"
        if p.exists():
            a = Image.open(p).convert("RGBA").resize((w * 2, h * 2), Image.NEAREST); sh.paste(a, (x, y), a)
        b = Image.open(out / f"{m}-{w}@2x.png"); sh.paste(b, (x, y + h * 2 + 12), b)
        if w == 24:
            d.text((x, 4), m, fill=(200, 196, 190), font=f)
    y += 2 * (h * 2 + 12) + 14
sh.crop((0, 0, sh.width, y)).save(out / "sizes.png")
print(out / "sizes.png")
