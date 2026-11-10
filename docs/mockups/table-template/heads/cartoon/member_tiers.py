"""The members' tiers by code (there is no members' tiers sheet): `python3 -I member_tiers.py` after `cut_cartoon.py`.

As `trial/try_gear.py` did for the pixel take: a tier's gear is what its K3 tile adds to the leader's bare K3 tile, kept only
where it is gear-coloured (iron grey, violet), with its outline. A scale and an offset lay the member's head on the leader's
bare head (a least-squares fit over the leader's face, by FFT); then the gear is laid on the member.
Saves `cut/member-<race>-<laborer|warrior|elder>.png` (all three at one scale, so a tier's head is as big as the bare one's)
and `cut/member-<race>-<tier>.json` with the fit, and each tier's corner from the bare one's (`lay` returns it).
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I leaves the script's folder out
from cut_cartoon import label_parts  # noqa: E402

HERE = Path(__file__).resolve().parent
CUT = HERE / "cut"
PAIRS = [("grunt", "shaman"), ("elf", "dryad"), ("goblin", "imp"), ("gnome", "gnome-fairy"),
         ("skeleton", "lich"), ("knight", "knight")]          # member <- the leader whose K3 gear it wears
TIERS = ("laborer", "warrior", "elder")
K = 4                                                          # the fit is made on a picture this many times smaller
OFFSETS = json.loads((CUT / "offsets.json").read_text()) if (CUT / "offsets.json").exists() else {}


def rgba(name):
    return Image.open(CUT / f"{name}.png").convert("RGBA")


def is_gear(a, tier):
    r, g, b, al = (a[..., i].astype(int) for i in range(4))
    if tier == "elder":                                         # violet: blue and red over green
        col = (r > g + 18) & (b > g + 18)
    else:                                                       # iron: low saturation, dark to mid grey
        mx, mn = np.maximum(np.maximum(r, g), b), np.minimum(np.minimum(r, g), b)
        col = (mx - mn < 30) & (mx > 45) & (mx < 205)
    return col & (al > 128)


def tile_canvas(names):
    """The tiles of one sheet laid on a common canvas (their offsets are from the frame's corner): {name: RGBA} + origin."""
    x0 = min(OFFSETS[n][0] for n in names)
    y0 = min(OFFSETS[n][1] for n in names)
    ims = {n: rgba(n) for n in names}
    W = max(OFFSETS[n][0] - x0 + ims[n].width for n in names)
    H = max(OFFSETS[n][1] - y0 + ims[n].height for n in names)
    out = {}
    for n, im in ims.items():
        c = Image.new("RGBA", (W, H))
        c.alpha_composite(im, (OFFSETS[n][0] - x0, OFFSETS[n][1] - y0))
        out[n] = c
    return out, (x0, y0)


def gear(leader, tier):
    """(gear RGBA, bare RGBA, origin): the gear on the K3 canvas, and the bare K3 tile on the same canvas."""
    tiles, origin = tile_canvas([f"tier-{leader}-{t}" for t in TIERS])
    bare, worn = tiles[f"tier-{leader}-laborer"], tiles[f"tier-{leader}-{tier}"]
    wa, ba = np.asarray(worn), np.asarray(bare)
    changed = np.abs(wa[..., :3].astype(int) - ba[..., :3].astype(int)).sum(2) > 60
    changed |= (wa[..., 3] > 128) & (ba[..., 3] < 128)
    mask = is_gear(wa, tier) & changed
    for part in label_parts(mask):                                      # a speck of grey is JPEG noise, not gear
        if len(part) < 150:
            for i in part:
                mask[i // mask.shape[1], i % mask.shape[1]] = False
    # the outline: dark pixels within a few px of the gear
    R = 3
    near = np.zeros_like(mask)
    ys, xs = np.nonzero(mask)
    for dy in range(-R, R + 1):
        for dx in range(-R, R + 1):
            yy, xx = np.clip(ys + dy, 0, mask.shape[0] - 1), np.clip(xs + dx, 0, mask.shape[1] - 1)
            near[yy, xx] = True
    bare_dark = (ba[..., 3] > 128) & (ba[..., :3].max(2) < 70)        # the leader's own outline (horns, wings, antlers) is not gear's
    outline = near & ~mask & ~bare_dark & (wa[..., 3] > 128) & (wa[..., :3].max(2) < 60)
    keep = mask | outline
    out = np.zeros_like(wa)
    out[keep] = wa[keep]
    return Image.fromarray(out, "RGBA"), bare, origin


def xcorr(f, g, shape):
    """C(d) = sum_q f(q + d) g(q) for every shift d, by FFT (f and g zero-padded to `shape`)."""
    return np.fft.irfft2(np.fft.rfft2(f, shape) * np.conj(np.fft.rfft2(g, shape)), shape)


def fit(base, member, scales):
    """The scale and offset (full-size px) that lay `member`'s face on `base`'s: least squares over the base's face."""
    b = base.resize((max(1, base.width // K), max(1, base.height // K)), Image.BOX)
    ba = np.asarray(b).astype(float)
    h, w = ba.shape[:2]
    M = np.zeros((h, w))
    M[int(h * 0.30):, int(w * 0.24):int(w * 0.76)] = 1                 # the face: lower part, the middle
    M *= ba[..., 3] > 200
    B = ba[..., :3]
    P = 255.0 ** 2 * 0.5                                                # what a bare patch under a face costs
    best = None
    for s in scales:
        m = member.resize((max(1, round(member.width * s / K)), max(1, round(member.height * s / K))), Image.BOX)
        ma = np.asarray(m).astype(float)
        hh, ww = ma.shape[:2]
        A = (ma[..., 3] > 200).astype(float)
        H = ma[..., :3]
        shape = (h + hh, w + ww)
        cost = xcorr(M * (B ** 2).sum(2), A, shape)
        for c in range(3):
            cost -= 2 * xcorr(M * B[..., c], H[..., c] * A, shape)
        cost += xcorr(M, A * (H ** 2).sum(2), shape)
        cost += P * (M.sum() - xcorr(M, A, shape))
        # a shift d that leaves the member far outside the base is not a fit: keep the member's centre inside the base
        ys, xs = np.mgrid[0:shape[0], 0:shape[1]]
        dy = np.where(ys > shape[0] // 2, ys - shape[0], ys)
        dx = np.where(xs > shape[1] // 2, xs - shape[1], xs)
        cx, cy = dx + ww / 2, dy + hh / 2
        ok = (cx > w * 0.2) & (cx < w * 0.8) & (cy > h * 0.25) & (cy < h * 0.95)
        cost = np.where(ok, cost, np.inf)
        i = np.unravel_index(np.argmin(cost), cost.shape)
        v = cost[i] / max(M.sum(), 1)
        if best is None or v < best[0]:
            best = (v, s, int(dx[i]) * K, int(dy[i]) * K)
    return best


def lay(member, leader, fits=None):
    """{tier: RGBA} on one canvas (the leader's K3 canvas, grown to fit), with the fit; and the canvas origin."""
    mem = rgba(f"member-{member}")
    gears = {}
    for t in TIERS[1:]:
        g, bare, origin = gear(leader, t)
        gears[t] = g
    v, s, dx, dy = fit(bare, mem, [x / 100 for x in range(30, 161, 3)])
    if fits and member in fits:
        s, dx, dy = fits[member]
    ms = mem.resize((round(mem.width * s), round(mem.height * s)), Image.LANCZOS)
    # canvas: the union of the scaled member and the gear, in the K3 canvas's coordinates
    x0 = min(0, dx)
    y0 = min(0, dy)
    x1 = max(bare.width, dx + ms.width)
    y1 = max(bare.height, dy + ms.height)
    out = {}
    for t in TIERS:
        c = Image.new("RGBA", (x1 - x0, y1 - y0))
        c.alpha_composite(ms, (dx - x0, dy - y0))
        if t != "laborer":
            c.alpha_composite(gears[t], (-x0, -y0))
        out[t] = c
    return out, {"score": float(v), "scale": s, "dx": dx, "dy": dy}, (origin[0] + x0, origin[1] + y0)


def main():
    cfg = json.loads((HERE / "sheets.json").read_text())
    fits = cfg.get("member_fit", {})                  # a fit by hand, where the automatic one is wrong: {member: [scale, dx, dy]}
    info = {}
    for member, leader in PAIRS:
        tiers, f, origin = lay(member, leader, fits)
        for t, im in tiers.items():
            bb = im.getbbox()
            im.crop(bb).save(CUT / f"member-{member}-{t}.png")
            OFFSETS_OUT[f"member-{member}-{t}"] = [origin[0] + bb[0], origin[1] + bb[1]]
        f["leader"] = leader
        info[member] = f
        print(member, "<-", leader, f)
    (CUT / "member-fits.json").write_text(json.dumps(info, indent=1))
    offs = dict(OFFSETS)
    offs.update(OFFSETS_OUT)
    (CUT / "offsets.json").write_text(json.dumps(offs))


OFFSETS_OUT = {}

if __name__ == "__main__":
    main()
