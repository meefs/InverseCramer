"""Hidden object: a front-on gull, wings spread in the classic 'M'.

flap in [-1, 1]: 0 = gliding M, +1 = wings raised into a V, -1 = downstroke.
Depth convention: 1 = near (out of the screen), 0 = background plane.
"""
import math

import cairocffi as cairo
import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter

W, H = 1920, 1080


def _lerp(a, b, t):
    return a + (b - a) * t


def wing_pose(flap):
    """Shoulder, wrist, tip (right wing, relative to body centre) for a flap value."""
    rest = dict(wrist=(360, -230), tip=(820, 10))
    up = dict(wrist=(320, -330), tip=(660, -460))
    down = dict(wrist=(400, 20), tip=(740, 250))
    tgt = up if flap >= 0 else down
    t = abs(flap)
    wrist = (_lerp(rest["wrist"][0], tgt["wrist"][0], t), _lerp(rest["wrist"][1], tgt["wrist"][1], t))
    tip = (_lerp(rest["tip"][0], tgt["tip"][0], t), _lerp(rest["tip"][1], tgt["tip"][1], t))
    return (55, -40), wrist, tip


def _mask(draw):
    surf = cairo.ImageSurface(cairo.FORMAT_A8, W, H)
    ctx = cairo.Context(surf)
    draw(ctx)
    a = np.frombuffer(surf.get_data(), np.uint8).reshape(H, surf.get_stride())[:, :W]
    return a.astype(np.float32) / 255


def _tapered_stroke(ctx, pts, widths, n=160):
    """Union of discs along a polyline whose radius tapers between the given widths."""
    pts = np.array(pts, float)
    seg = np.hypot(*np.diff(pts, axis=0).T)
    cum = np.concatenate([[0], np.cumsum(seg)])
    for s in np.linspace(0, cum[-1], n):
        k = min(np.searchsorted(cum, s, side="right") - 1, len(seg) - 1)
        t = (s - cum[k]) / seg[k]
        p = pts[k] + (pts[k + 1] - pts[k]) * t
        w = widths[k] + (widths[k + 1] - widths[k]) * t
        ctx.arc(p[0], p[1], w / 2, 0, 2 * math.pi)
        ctx.fill()


def _smooth_curve(p0, p1, p2, n=24):
    """Quadratic-ish smooth path through shoulder, wrist, tip (Catmull-Rom sampling)."""
    p0, p1, p2 = map(np.array, (p0, p1, p2))
    # round the wrist with a quadratic blend
    out = []
    for t in np.linspace(0, 1, 2 * n):
        q0 = p0 + (p1 - p0) * t
        q1 = p1 + (p2 - p1) * t
        out.append(q0 + (q1 - q0) * t)
    return np.array(out)


def gull_depth(flap=0.0, cx=960, cy=600, scale=1.0):
    def wings(ctx):
        for side in (-1, 1):
            sh, wr, tp = wing_pose(flap)
            pts = [(cx + side * sh[0] * scale, cy + sh[1] * scale),
                   (cx + side * wr[0] * scale, cy + wr[1] * scale),
                   (cx + side * tp[0] * scale, cy + tp[1] * scale)]
            curve = _smooth_curve(*pts)
            # leading edge thick at the arm, slimmer through the hand, but never thinner than ~P/2
            widths = np.interp(np.linspace(0, 1, len(curve)), [0, 0.5, 1], [165, 130, 84]) * scale
            for i in range(len(curve) - 1):
                _tapered_stroke(ctx, curve[i:i + 2], widths[i:i + 2], n=6)

    def body(ctx):
        ctx.save()
        ctx.translate(cx, cy)
        ctx.scale(105 * scale, 150 * scale)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        ctx.fill()
        ctx.arc(cx, cy - 170 * scale, 88 * scale, 0, 2 * math.pi)  # head
        ctx.fill()
        # beak: a short wedge pointing at the viewer reads as a lighter nub
        ctx.arc(cx, cy - 150 * scale, 26 * scale, 0, 2 * math.pi)
        ctx.fill()

    wm = _mask(wings) > 0.5
    bm = _mask(body) > 0.5
    z = np.zeros((H, W), np.float32)
    dw = distance_transform_edt(wm)
    zw = 0.42 + 0.28 * np.sqrt(np.clip(dw / 60, 0, 1))
    # wings sweep back toward the far plane at the tips: fade by horizontal distance
    fade = 1 - 0.30 * np.clip(np.abs(np.arange(W) - cx) / (800 * scale), 0, 1)
    z = np.where(wm, zw * fade[None, :], z)
    db = distance_transform_edt(bm)
    zb = 0.62 + 0.38 * np.sqrt(np.clip(db / 95, 0, 1))
    z = np.where(bm, np.maximum(z, zb), z)
    # beak nub, nearest point of all
    yy, xx = np.mgrid[0:H, 0:W]
    beak = np.exp(-(((xx - cx) / (16 * scale)) ** 2 + ((yy - (cy - 150 * scale)) / (14 * scale)) ** 2))
    z = np.maximum(z, np.where(bm, np.minimum(1.0, zb + 0.1 * beak), 0))
    return gaussian_filter(z, 1.5).astype(np.float32)


if __name__ == "__main__":
    import sys
    from PIL import Image
    Image.fromarray((gull_depth(float(sys.argv[2]) if len(sys.argv) > 2 else 0) * 255).astype(np.uint8)).save(sys.argv[1])
