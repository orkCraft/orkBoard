"""The merchant mockup's heads: four variants of three leaders (Tech's shaman, Product's unicorn knight, Design's dryad) and
two of two more (Run's imp, Marketing's fairy),
each its race's elder head with a few colours and cells changed, and the moods laid over it from orkUI's own mood heads
(the cells where a mood differs from the calm head). Drawn here first; they would go into orkUI's races.json after a yes.
Run from the repository's root: python docs/mockups/merchant/heads/make_heads.py"""
from pathlib import Path
from PIL import Image

RACES = Path("design-system/orkui/races")
OUT = Path(__file__).parent
MOODS = ["", "focused", "worried", "pleased", "no", "asleep"]


def grid(path: Path) -> list[list[tuple | None]]:
    im = Image.open(path).convert("RGBA")
    return [[(lambda p: None if p[3] == 0 else p[:3])(im.getpixel((x * 2, y * 2))) for x in range(12)] for y in range(11)]


def hexrgb(h: str) -> tuple:
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def save(cells, name: str) -> None:
    for scale, suffix in ((2, ""), (4, "@2x")):
        im = Image.new("RGBA", (12 * scale, 11 * scale), (0, 0, 0, 0))
        for y, row in enumerate(cells):
            for x, c in enumerate(row):
                if c:
                    for dy in range(scale):
                        for dx in range(scale):
                            im.putpixel((x * scale + dx, y * scale + dy), c + (255,))
        im.save(OUT / f"{name}{suffix}.png")


# name: (race, {old colour: new}, [(x, y, colour)]); the hood (#967b9e) is the tier's gear and is never changed
VARIANTS = {
    # Tech's shaman: the skin (#40836c, shade #2f6b4f), the horns (#d3c29a, #a8946a), a detail
    "sh-c4": ("shaman", {}, []),
    "sh-ddd": ("shaman", {"#40836c": "#3f7a80", "#2f6b4f": "#2e5f66", "#d3c29a": "#8f7150", "#a8946a": "#6b5340"},
               [(x, 10, "#8f7150") for x in range(4, 8)]),
    "sh-xp": ("shaman", {"#40836c": "#4e6e3a", "#2f6b4f": "#3b5a2c"},
              [(x, 7, "#6b5a7e") for x in range(2, 10)] + [(2, 0, "#ece4cf"), (9, 0, "#ece4cf")]),
    "sh-fit": ("shaman", {"#40836c": "#5f7f6e", "#2f6b4f": "#4a6658", "#d3c29a": "#9aa0a8", "#a8946a": "#72777d"},
               [(5, 4, "#d3c29a"), (6, 5, "#d3c29a")]),
    # Product's unicorn knight: the helm (#d2ae6d, a warm metal always: grey is the plain knight's), the wings (#f0ede4), the horn (#d9cdf2)
    "uni-ost": ("unicorn", {}, []),
    "uni-jtbd": ("unicorn", {"#d2ae6d": "#c08850", "#f0ede4": "#d3c29a", "#d9cdf2": "#ece4cf"}, []),
    "uni-lean": ("unicorn", {"#d2ae6d": "#e0c88a", "#f0ede4": "#c9c0e6", "#d9cdf2": "#a99bd0"}, []),
    "uni-shape": ("unicorn", {"#d2ae6d": "#cf9a80"}, [(4, 0, "#d3c29a"), (5, 0, "#d3c29a"), (6, 0, "#d3c29a")]),
    # Design's dryad: the skin (#eadcc2), the antlers (#a98259), the hair (#d8c38a)
    "dry-heur": ("dryad", {}, []),
    "dry-diamond": ("dryad", {"#eadcc2": "#d9c09c", "#a98259": "#cac7c1", "#d8c38a": "#ac8b4d"}, []),
    "dry-atom": ("dryad", {"#eadcc2": "#d6dcc8", "#a98259": "#6e5034", "#d8c38a": "#aca8a1"}, []),
    "dry-sprint": ("dryad", {"#eadcc2": "#e6c9b4", "#d8c38a": "#9a6b4a"}, [(0, 0, "#f0ede4"), (11, 0, "#f0ede4")]),
    # Run's imp: the skin (#b07259, shade #9e686a), the horns (#d3c29a), a detail
    "imp-slo": ("imp", {}, []),
    "imp-obs": ("imp", {"#b07259": "#8c6f86", "#9e686a": "#77596f", "#d3c29a": "#aca8a1"}, [(3, 5, "#cac7c1"), (6, 5, "#cac7c1")]),
    # Marketing's fairy: the skin (#e3b58c, shade #c99a74), the wings (#d8e6ea), the beard (#ece4cf)
    "fairy-aarrr": ("fairy", {}, []),
    "fairy-aso": ("fairy", {"#e3b58c": "#d4a07c", "#c99a74": "#b8845e", "#d8e6ea": "#e6d8b0", "#ece4cf": "#aca8a1"}, []),
}

for name, (race, swap, cells) in VARIANTS.items():
    calm = grid(RACES / f"{race}-elder.png")
    for mood in MOODS:
        base = calm if not mood else grid(RACES / f"{race}-elder-{mood}.png")
        swaps = {hexrgb(k): hexrgb(v) for k, v in swap.items()}
        out = [[swaps.get(c, c) if c else None for c in row] for row in calm]
        for x, y, c in cells:
            out[y][x] = hexrgb(c)
        for y in range(11):                       # the mood: the cells where orkUI's mood head differs from the calm one
            for x in range(12):
                if base[y][x] != calm[y][x]:
                    out[y][x] = swaps.get(base[y][x], base[y][x]) if base[y][x] else None
        save(out, name + (f"-{mood}" if mood else ""))
print("ok", len(VARIANTS) * len(MOODS) * 2)
