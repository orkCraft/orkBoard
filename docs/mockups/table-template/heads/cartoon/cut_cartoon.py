"""Cut the owner's cartoon sheets (§289) into one transparent head per tile: `python3 -I cut_cartoon.py [out-dir]`.

`sheets.json` holds, for each sheet, its file, the frame colour, the frames' columns and rows (measured with
`measure_frames.py`), the tile names, and the erase boxes (sheet pixels) for what the rules forbid (the "z" bubbles).
A new take is re-cut by editing it. Each tile is cropped to the middle of the gap around its frame (some heads cross
the frame), the ground and the frame line are made transparent by a flood from outside (and from just inside the
frame), so a head over the frame keeps its pixels and dark pixels inside the head stay. Then the head is cropped to
its box and saved at full size into `cut/`.
"""
import json
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
GROUND_TOL = 42      # sum of abs RGB difference to the tile's ground
FRAME_TOL = 70       # ... to the frame's colour
MIN_PART = 90        # a leftover speck smaller than this (px) is dropped
FRAME_SEED_TOL = 34  # a seed on a frame line must be this close to the frame's colour
LINE_RUN = 14       # ... for this many px each way along the line
PEEL = 2             # passes that take off the halo of ground-ish pixels at the edge


def label_parts(opaque):
    """Connected parts (4-neighbour) of a boolean mask: list of lists of flat indices."""
    h, w = opaque.shape
    flat = opaque.ravel().tolist()
    seen = bytearray(h * w)
    parts = []
    for s in range(h * w):
        if not flat[s] or seen[s]:
            continue
        seen[s] = 1
        st = [s]
        part = []
        while st:
            i = st.pop()
            part.append(i)
            x = i % w
            for j in (i - w, i + w, i - 1 if x else -1, i + 1 if x < w - 1 else -1):
                if 0 <= j < h * w and flat[j] and not seen[j]:
                    seen[j] = 1
                    st.append(j)
        parts.append(part)
    return parts


def flood(cand, seeds):
    """Flat boolean array of the candidate pixels connected to the seeds."""
    h, w = cand.shape
    c = cand.ravel().tolist()
    seen = bytearray(h * w)
    st = [s for s in seeds if c[s]]
    for s in st:
        seen[s] = 1
    while st:
        i = st.pop()
        x = i % w
        for j in (i - w, i + w, i - 1 if x else -1, i + 1 if x < w - 1 else -1):
            if 0 <= j < h * w and c[j] and not seen[j]:
                seen[j] = 1
                st.append(j)
    return np.frombuffer(bytes(seen), dtype=np.uint8).reshape(h, w).astype(bool)


def cut_tile(im, box, frame_rgb, erases, inset, line_seeds=()):
    """im: RGB sheet; box: crop box in sheet pixels; inset: how far inside the frame the inner seeds sit."""
    x0, y0, x1, y1 = box
    a = np.asarray(im.crop(box)).astype(int)
    h, w, _ = a.shape
    # the ground: the median of the flat mid-grey pixels of the crop (a head can reach any corner, a wing the top ones)
    flat = a.reshape(-1, 3)
    grey = flat[(flat.max(1) - flat.min(1) < 8) & (flat.mean(1) > 48) & (flat.mean(1) < 72)]
    ground = np.median(grey, axis=0)
    yy, xx = np.mgrid[0:h, 0:w]
    for e in erases:                                         # what the rules forbid becomes ground
        if e[0] == "e":                                      # ["e", cx, cy, rx, ry]: an ellipse, where a box would bite the head
            _, cx, cy, rx, ry = e
            a[((xx + x0 - cx) / rx) ** 2 + ((yy + y0 - cy) / ry) ** 2 <= 1] = ground
        elif e[0] == "p":                                    # ["p", [[x, y], ...]]: a polygon (sheet pixels)
            from PIL import ImageDraw
            m = Image.new("L", (w, h), 0)
            ImageDraw.Draw(m).polygon([(px - x0, py - y0) for px, py in e[1]], fill=255)
            a[np.asarray(m) > 0] = ground
        else:                                                # [x0, y0, x1, y1]: a box
            ex0, ey0, ex1, ey1 = e
            a[max(0, ey0 - y0):max(0, ey1 - y0), max(0, ex0 - x0):max(0, ex1 - x0)] = ground
    d_g = np.abs(a - ground).sum(2)
    d_f = np.abs(a - np.array(frame_rgb)).sum(2)
    spread = a.max(2) - a.min(2)
    cand = (d_g < GROUND_TOL) | ((d_f < FRAME_TOL) & (spread < 32))     # the frame is neutral; a purple hair is not
    seeds = [x for x in range(w)] + [(h - 1) * w + x for x in range(w)] + [y * w for y in range(h)] + [y * w + w - 1 for y in range(h)]
    seeds += [py * w + px for (px, py) in inset]
    # a stretch of frame line between two crossing parts of a head (the dryad's antlers) is cut off from the outside:
    # seed it from the line's own pixels, where they are exactly the frame's colour
    for (px, py, ox, oy) in line_seeds:
        # a seed sits on a stretch of the line that is frame-coloured for a good way along it (a head's outline ends such a run)
        if not (0 <= px < w and 0 <= py < h and d_f[py, px] < FRAME_SEED_TOL):
            continue
        ax, ay = (1, 0) if ox == 0 else (0, 1)
        ok = True
        for k in range(-LINE_RUN, LINE_RUN + 1):
            qx, qy = px + ax * k, py + ay * k
            if not (0 <= qx < w and 0 <= qy < h and d_f[qy, qx] < FRAME_TOL):
                ok = False
                break
        if ok:
            seeds.append(py * w + px)
    bg = flood(cand, seeds)
    opaque = ~bg
    # peel the halo: edge pixels that are close to the ground (JPEG blend of ground and outline)
    for _ in range(PEEL):
        near = np.zeros_like(opaque)
        near[1:, :] |= ~opaque[:-1, :]
        near[:-1, :] |= ~opaque[1:, :]
        near[:, 1:] |= ~opaque[:, :-1]
        near[:, :-1] |= ~opaque[:, 1:]
        opaque &= ~(near & (d_g < GROUND_TOL * 2))
    # the halo of the frame line's blend: neutral dull grey-brown next to the ground goes too
    a_max, a_min, a_mean = a.max(2), a.min(2), a.mean(2)
    dull = ((a_max - a_min) < 30) & (a_mean > 50) & (a_mean < 118)
    for _ in range(4):
        near = np.zeros_like(opaque)
        near[1:, :] |= ~opaque[:-1, :]
        near[:-1, :] |= ~opaque[1:, :]
        near[:, 1:] |= ~opaque[:, :-1]
        near[:, :-1] |= ~opaque[:, 1:]
        opaque &= ~(near & dull)
    # drop specks, and what belongs to a neighbour: a part, other than the head itself, that touches the crop's edge
    parts = label_parts(opaque)
    main = max(parts, key=len) if parts else []
    for part in parts:
        edge = any(i % w in (0, w - 1) or i // w in (0, h - 1) for i in part)
        if len(part) < MIN_PART or (part is not main and edge):
            for i in part:
                opaque[i // w, i % w] = False
    rgba = np.dstack([a.clip(0, 255).astype(np.uint8), (opaque * 255).astype(np.uint8)])
    out = Image.fromarray(rgba, "RGBA")
    bb = out.getbbox() or (0, 0, w, h)
    return out.crop(bb), (x0 + bb[0], y0 + bb[1])       # the head, and where its corner is in the sheet


def tile_boxes(sheet):
    cols, rows = sheet["cols"], sheet["rows"]

    def edges(spans, size):
        res = []
        for i, (a, b) in enumerate(spans):
            lo = (spans[i - 1][1] + a) // 2 if i else max(0, a - (spans[1][0] - spans[0][1]) // 2)
            hi = (b + spans[i + 1][0]) // 2 if i + 1 < len(spans) else min(size, b + (spans[1][0] - spans[0][1]) // 2)
            res.append((lo, hi))
        return res
    return cols, rows, edges


def line_seeds(sh, box):
    """Points on the middle of every frame line of the sheet that fall in the crop, in the crop's coordinates."""
    t = sh.get("line", 6) // 2
    o = t + 11
    pts = []
    for (a, b) in sh["cols"]:
        for x in (a + t, b - t):
            pts += [(x - box[0], y - box[1], o, 0) for y in range(box[1], box[3], 5)]
    for (a, b) in sh["rows"]:
        for y in (a + t, b - t):
            pts += [(x - box[0], y - box[1], 0, o) for x in range(box[0], box[2], 5)]
    return pts


def main():
    cfg = json.loads((HERE / "sheets.json").read_text())
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "cut"
    out.mkdir(exist_ok=True)
    n = 0
    offsets = {}
    for sname, sh in cfg["sheets"].items():
        im = Image.open(HERE / sh["file"]).convert("RGB")
        cols, rows, edges = tile_boxes(sh)
        ce, re_ = edges(cols, im.width), edges(rows, im.height)
        for r, row in enumerate(sh["names"]):
            for c, name in enumerate(row):
                box = [ce[c][0], re_[r][0], ce[c][1], re_[r][1]]
                for key, pad in cfg.get("pad", {}).items():     # a head that crosses beyond the gap: its crop is larger
                    if name.startswith(key):
                        box = [max(0, box[0] - pad[0]), max(0, box[1] - pad[1]), min(im.width, box[2] + pad[2]), min(im.height, box[3] + pad[3])]
                        break
                box = tuple(box)
                fx0, fx1 = cols[c]
                fy0, fy1 = rows[r]
                k = 30
                inset = [(fx0 - box[0] + k, fy0 - box[1] + k), (fx1 - box[0] - k, fy0 - box[1] + k),
                         (fx0 - box[0] + k, fy1 - box[1] - k), (fx1 - box[0] - k, fy1 - box[1] - k)]
                erases = cfg["erase"].get(name, [])
                tile, corner = cut_tile(im, box, sh["frame_rgb"], erases, inset, line_seeds(sh, box))
                tile.save(out / f"{name}.png")
                offsets[name] = [corner[0] - fx0, corner[1] - fy0]   # the head's corner from its frame's: lays tiles of one sheet on each other
                n += 1
        print(sname, "done", flush=True)
    (out / "offsets.json").write_text(json.dumps(offsets))
    print(n, "heads in", out)


if __name__ == "__main__":
    main()
