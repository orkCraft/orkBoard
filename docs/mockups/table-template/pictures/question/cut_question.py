"""Cut sheet 4, the kinds of a question, into eight pixel pictures: `python3 -I cut_question.py`.

The cards' pictures stay pixel for the beta. Sheet 4 came in two takes: `sheets/q4-take1.jpg` (a 2x2 grid of wide tiles: question,
fork, conflict, risk) and `sheets/q4-take2.jpg` (a 4x2 grid; its bottom row: concern, failure, cost-grew, hypothesis; those
tiles are almost square, so each is cropped to 1.8 : 1 keeping its bottom, the table's edge). Cut the way the pictures beside
(`../*.png`, `../settings/`, `../leader/`) were: the tile inside its frame, brought down with nearest neighbour to about 300 px
wide (a JPEG whose pixels are not on one grid), laid on 48 colours (a palette image, no dither).
Frames were measured on the sheets (the grey-brown lines); edit the boxes below for a new take.
"""
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
WIDTH = 300
RATIO = 1.8
COLOURS = 48
INSET = 4                    # px inside the frame line's inner edge

# (name, sheet, inner box x0, y0, x1, y1 inside the frame, crop to RATIO keeping the bottom)
TILES = [
    ("question", "q4-take1.jpg", (46, 51, 1257, 649), False),
    ("fork", "q4-take1.jpg", (1321, 51, 2532, 649), False),
    ("conflict", "q4-take1.jpg", (46, 711, 1257, 1311), False),
    ("risk", "q4-take1.jpg", (1321, 711, 2532, 1311), False),
    ("concern", "q4-take2.jpg", (27, 566, 627, 1073), True),
    ("failure", "q4-take2.jpg", (667, 566, 1266, 1073), True),
    ("cost-grew", "q4-take2.jpg", (1308, 566, 1898, 1073), True),
    ("hypothesis", "q4-take2.jpg", (1940, 566, 2547, 1073), True),
]


def main():
    sheets = {}
    for name, sheet, (x0, y0, x1, y1), crop in TILES:
        im = sheets.setdefault(sheet, Image.open(HERE / "sheets" / sheet).convert("RGB"))
        x0, y0, x1, y1 = x0 + INSET, y0 + INSET, x1 - INSET, y1 - INSET
        if crop:
            y0 = max(y0, round(y1 - (x1 - x0) / RATIO))
        t = im.crop((x0, y0, x1, y1))
        t = t.resize((WIDTH, round(WIDTH * t.height / t.width)), Image.NEAREST)
        t = t.quantize(colors=COLOURS, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        t.save(HERE / f"{name}.png")
        print(name, t.size, t.mode)


if __name__ == "__main__":
    main()
