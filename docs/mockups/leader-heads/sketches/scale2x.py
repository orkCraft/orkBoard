"""A sketch of more detailed art for the mockup: orkUI's 12 x 11 heads and 14 x 14 signs doubled with Scale2x (the classic
pixel-art upscale that rounds diagonals), then a dark outline, a highlight on the top-left edges and a shade on the
bottom-right, all on the doubled grid. Written to out/ as PNG at 2 px a cell. Not orkUI's art: a direction to redraw by hand."""
import re
import sys
from pathlib import Path
from PIL import Image

ORKUI = Path("/home/user/orkBoard/design-system/orkui")
OUT = Path(sys.argv[1])
(OUT / "races").mkdir(parents=True, exist_ok=True)
(OUT / "signs").mkdir(parents=True, exist_ok=True)

ELEM = {"meadow": "#6fb8a8", "ice": "#82aaff", "dust": "#b8914f", "void": "#8e88a8", "lava": "#ad6a5a",
        "ink": "#dedbd6", "ok": "#86c062", "danger": "#f5806e", "alert": "#f0d050"}


def scale2x(g):
    h, w = len(g), len(g[0])
    at = lambda x, y: g[min(max(y, 0), h - 1)][min(max(x, 0), w - 1)]
    o = [[None] * (w * 2) for _ in range(h * 2)]
    for y in range(h):
        for x in range(w):
            p, a, b, c, d = at(x, y), at(x, y - 1), at(x + 1, y), at(x - 1, y), at(x, y + 1)
            e0, e1, e2, e3 = p, p, p, p
            if c == a and c != d and a != b: e0 = a
            if a == b and a != c and b != d: e1 = b
            if d == c and d != b and c != a: e2 = c
            if b == d and b != a and d != c: e3 = d
            o[y * 2][x * 2], o[y * 2][x * 2 + 1], o[y * 2 + 1][x * 2], o[y * 2 + 1][x * 2 + 1] = e0, e1, e2, e3
    return o


def mix(c, t, k):
    return tuple(round(c[i] + (t[i] - c[i]) * k) for i in range(3))


def shade(g, light=0.22, dark=0.28, outline=True):
    """Each colour region lit from the top left: a cell whose up-left neighbour is another region (or nothing) is lighter,
    one whose down-right neighbour is another region darker; the silhouette ringed by a dark line."""
    h, w = len(g), len(g[0])
    get = lambda x, y: g[y][x] if 0 <= x < w and 0 <= y < h else None
    o = [row[:] for row in g]
    for y in range(h):
        for x in range(w):
            c = g[y][x]
            if c is None:
                continue
            up, left, down, right = get(x, y - 1), get(x - 1, y), get(x, y + 1), get(x + 1, y)
            if up != c or left != c:
                o[y][x] = mix(c, (255, 248, 230), light)
            elif down != c or right != c:
                o[y][x] = mix(c, (0, 0, 0), dark)
    if outline:
        ring = [[None] * w for _ in range(h)]
        for y in range(h):
            for x in range(w):
                if g[y][x] is None:
                    n = [get(x + dx, y + dy) for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0))]
                    n = [c for c in n if c]
                    if n:
                        ring[y][x] = mix(min(n, key=sum), (0, 0, 0), 0.65)
        for y in range(h):
            for x in range(w):
                if ring[y][x]:
                    o[y][x] = ring[y][x]
    return o


def save(g, path, cell=2):
    h, w = len(g), len(g[0])
    im = Image.new("RGBA", (w * cell, h * cell), (0, 0, 0, 0))
    for y in range(h):
        for x in range(w):
            if g[y][x]:
                for dy in range(cell):
                    for dx in range(cell):
                        im.putpixel((x * cell + dx, y * cell + dy), g[y][x] + (255,))
    im.save(path)


def head_grid(p: Path):
    im = Image.open(p).convert("RGBA")
    W, H = im.size[0] // 2, im.size[1] // 2
    return [[(lambda q: None if q[3] == 0 else q[:3])(im.getpixel((x * 2, y * 2))) for x in range(W)] for y in range(H)]


for p in sorted((ORKUI / "races").glob("*.png")):
    if p.name.endswith("@2x.png"):
        continue
    g = head_grid(p)
    d = shade(scale2x(g))
    save(d, OUT / "races" / p.name, cell=2)                   # 24 x 22 cells at 2 px: 48 x 44
    save(d, OUT / "races" / p.name.replace(".png", "@2x.png"), cell=4)


def sign_grid(p: Path, colour):
    s = p.read_text()
    w, h = map(int, re.search(r'viewBox="0 0 (\d+) (\d+)"', s).groups())
    g = [[None] * w for _ in range(h)]
    for x, y in re.findall(r"M(\d+) (\d+)h1v1h-1z", s):
        g[int(y)][int(x)] = colour
    return g


def hexrgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


for p in sorted((ORKUI / "signs" / "big").glob("*.svg")):
    if p.stem.endswith("-light"):
        continue
    for el, hx in ELEM.items():
        g = shade(scale2x(sign_grid(p, hexrgb(hx))), light=0.3, dark=0.35)
        save(g, OUT / "signs" / f"{p.stem}-{el}.png", cell=2)  # 28 x 28 cells at 2 px: 56 x 56
print("ok")
