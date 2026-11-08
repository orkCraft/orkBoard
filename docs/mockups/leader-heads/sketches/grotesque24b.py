"""The ork shaman on a true 24 x 24 grid, coarser: a three-quarter view facing right (the way an old strategy game's small
portraits read: by the profile, the brow, the nose and the jaw, not by the eyes), lit from the upper right, a small dome,
a brow ledge jutting over the sockets, a bulb of a nose, an underslung jaw jutting past the nose, a tusk at the near
corner of the mouth, the near horn curled round the ear at the back, the far horn's tip over the dome, a braid. Six moods
as overlays. The palette and the helpers are grotesque24.py's. A working sketch, not orkUI art.

    python docs/mockups/leader-heads/sketches/grotesque24b.py OUT_DIR"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from grotesque24 import N, P, box, outline, put, row, save  # noqa: E402

HEAD = [
    #0         1         2
    #012345678901234567890123
    "................hhh.....",  # 0  the far horn's tip
    "...hHHHh.......hHHHh....",  # 1
    "..hHkHHHh.LLLLhHkhHh....",  # 2  the near horn over the back, the dome
    ".hHk..khSSLLLLLhh..Hh...",  # 3
    ".hH...ssSSSLLLLLL...hh..",  # 4
    ".Hk..sssSSSSLLLLLL......",  # 5
    ".hH.ssDsSSSSSLLLLLL.....",  # 6  the ear in the horn's curl
    ".hHksssSSSSSLLLLLLLLLL..",  # 7  the brow ledge jutting right
    "..hHssSSSSDDDDDDDDDDd...",  # 8  its shadow over the sockets
    "..hHHsSSSSSdddSddd......",  # 9  the sockets set deep under it
    "...hHHsSSSSSSSSSLLLLL...",  # 10 the nose's bulb
    "....hHHSSSSSSSSSLLLLLL..",  # 11 the horn's tip under the ear
    "...BsSSSSSSSSSSSSSsDdL..",  # 12 the nostril
    "...BsSSSSSSSSSSSSSSS....",  # 13 the lip set back
    "...BsSSSSSSSSSSSSSSS....",  # 14 the mouth
    "...bssSSSSSSSSSSSSSSLLL.",  # 15 the jaw jutting past the nose
    "...BssSSSSSSSLLLLLLLLLL.",  # 16
    "...BssSSSSSSLLLLLLLLLL..",  # 17
    "...bsssSSSSSSLLLLLLLL...",  # 18
    "...B.sssSSSSSSSSSSSS....",  # 19
    "...g...ssssssssssss.....",  # 20
    "...B......ssssss........",  # 21
    "........................",  # 22
    "........................",  # 23
]


def base():
    g = [[None if c == "." else c for c in line] for line in HEAD]
    for x, y in ((10, 11), (10, 12), (11, 12), (10, 13), (11, 13), (11, 14)):      # the near tusk
        g[y][x] = "T"
    g[13][11] = g[14][11] = "t"
    g[13][18] = g[13][19] = "t"                                                  # the far one, small
    for x, y in ((7, 11), (8, 12), (16, 16), (15, 17)):                          # creases, the jowl
        g[y][x] = "D"
    return g


def rim(g):
    """The cold rim on the back (left) edge and the top edges; the lit face needs none."""
    o = [r[:] for r in g]
    for y in range(N):
        for x in range(N):
            c = g[y][x]
            if c is None or c in "TtBbgWPMD":
                continue
            if (y == 0 or g[y - 1][x] is None) and y <= 5:
                o[y][x] = "R"
            elif (x == 0 or g[y][x - 1] is None) and c in "sShH":
                o[y][x] = "r"
    return o


def mood(m):
    g = base()
    if m == "calm":                      # half lids, looking ahead, the mouth a flat line turned down at the near corner
        put(g, row(11, 13, 9) + row(15, 16, 9), "W"); put(g, [(13, 9), (16, 9)], "P")
        put(g, row(11, 18, 14), "M"); put(g, [(11, 15)], "M")
    elif m == "focused":                 # the near eye a slit under a pressed brow, the far one wide
        put(g, row(11, 13, 9), "P"); put(g, row(10, 13, 8), "d")
        put(g, box(15, 17, 8, 10), "W"); put(g, [(16, 9)], "P"); put(g, row(15, 17, 7), "D")
        put(g, row(13, 18, 14), "M")
    elif m == "worried":                 # eyes wide, pupils tiny, the brows up, a clenched grimace
        put(g, box(11, 13, 8, 10) + box(15, 17, 8, 10), "W"); put(g, [(12, 9), (16, 9)], "P")
        put(g, [(11, 7), (12, 6), (13, 6), (15, 6), (16, 6), (17, 7)], "D")
        put(g, row(11, 19, 13) + row(11, 19, 15), "M"); put(g, row(12, 19, 14), "T"); put(g, [(14, 14), (17, 14)], "M")
    elif m == "no":                      # a side-eye at you (the pupils to the back), the brow low, the near corner down
        put(g, row(11, 13, 9) + row(15, 17, 9), "W"); put(g, [(11, 9), (15, 9)], "P"); put(g, row(10, 18, 8), "d")
        put(g, row(12, 18, 14), "M"); put(g, [(11, 15), (10, 15)], "M")
    elif m == "pleased":                 # the cheeks push the eyes into arcs, a wide grin to the far side
        put(g, [(11, 9), (12, 8), (13, 9), (15, 9), (16, 8), (17, 9)], "d"); put(g, row(11, 17, 7), "L")
        put(g, row(10, 14, 10), "L")
        put(g, [(12, 12), (19, 12)] + row(12, 19, 13), "M"); put(g, row(13, 19, 14), "T"); put(g, [(15, 14), (18, 14)], "M")
        put(g, row(13, 18, 15), "M")
    elif m == "asleep":                  # the eyes shut as lines, the jaw slack, drool
        put(g, row(11, 13, 9) + row(15, 17, 9), "d")
        put(g, box(13, 17, 14, 16) + row(14, 16, 17), "M"); put(g, [(13, 18), (13, 19)], "w")
    return outline(rim(g))


MOODS = ["calm", "focused", "worried", "no", "pleased", "asleep"]
if __name__ == "__main__":
    OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
    f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    big = Image.new("RGB", (6 * 210 + 20, 230), (21, 20, 18)); db = ImageDraw.Draw(big)
    for i, m in enumerate(MOODS):
        g = mood(m)
        save(g, OUT / f"{m}-24@2x.png", 2); save(g, OUT / f"{m}-36@2x.png", 3); save(g, OUT / f"{m}-48@2x.png", 4)
        a = save(g, None, 8); big.paste(a, (10 + i * 210, 30), a); db.text((10 + i * 210, 6), m, fill=(240, 208, 80), font=f)
    big.save(OUT / "big.png")
    print(OUT / "big.png")
