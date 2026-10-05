"""Periodic pattern cell for the stereogram.

The tiling is rotated by -22 deg so one lattice vector is horizontal; then one
square cell (P x P) is an exact horizontal repeat. Tiles overlap, so they are
painted in a *translation-invariant* order: by colour class, then by position
projected on a fixed direction. Any two tiles keep the same relative order
under a lattice shift, so every cell comes out identical.

Outputs, rendered at `ss` x supersampling:
  colour cell  (P*ss, P*ss, 3) float32 in 0..1, two-tone gradients + micro-texture
  id cell      (P*ss, P*ss) int32: class + 4*(di+R) + 4*(2R+1)*(dj+R) of the owning tile
"""
import math

import cairocffi as cairo
import numpy as np

from common import tess

R = 4  # neighbour range in cells; the prototile is ~4.4 units long, ~3 cells at any scale


def frame_linear(P):
    k = P / tess.CELL
    c, s = math.cos(-tess.TILT), math.sin(-tess.TILT)
    return k * np.array([[c, -s], [s, c]])


def class_linear(P):
    F = frame_linear(P)
    return [F @ lin for _, lin in tess.CLASSES]


# Two-tone ramps per class: (deep shade, base, bright tint). Base colours are the SVG's own.
def ramps():
    out = []
    for col, _ in tess.CLASSES:
        base = tess.hex_rgb(col)
        out.append((tess.shade(base, -0.42, 0.25), base, tess.shade(base, 0.38, 0.2)))
    return out


def tile_order(order=(0, 2, 1, 3), direction=(1.0, 0.37)):
    """List of (class, di, dj) in paint order (translation invariant)."""
    items = []
    for rank, c in enumerate(order):
        for di in range(-R, R + 1):
            for dj in range(-R, R + 1):
                items.append((rank, di * direction[0] + dj * direction[1], c, di, dj))
    items.sort()
    return [(c, di, dj) for _, _, c, di, dj in items]


def id_of(c, di, dj):
    return c + 4 * (di + R) + 4 * (2 * R + 1) * (dj + R)


def decode_id(v):
    v = np.asarray(v)
    c = v % 4
    di = (v // 4) % (2 * R + 1) - R
    dj = v // (4 * (2 * R + 1)) - R
    return c, di, dj


def _surface(n):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, n, n)
    return surf, cairo.Context(surf)


def _to_array(surf, n):
    buf = np.frombuffer(surf.get_data(), np.uint8).reshape(n, surf.get_stride() // 4, 4)[:, :n]
    return buf[..., [2, 1, 0]].astype(np.float32) / 255  # BGRA -> RGB


def render_cell(P=150, ss=4, order=(0, 2, 1, 3), direction=(1.0, 0.37), texture=0.07, seed=15,
                stroke_px=1.6, ramp=None):
    n = P * ss
    lins = class_linear(P * ss)
    ramp = ramp or ramps()
    surf, ctx = _surface(n)
    isurf, ictx = _surface(n)
    ictx.set_antialias(cairo.ANTIALIAS_NONE)
    for cx in (ctx, ictx):
        cx.set_source_rgb(*tess.hex_rgb(tess.BACKGROUND))
        cx.paint()
    for c, di, dj in tile_order(order, direction):
        L = lins[c]
        if True:
            m = cairo.Matrix(L[0, 0], L[1, 0], L[0, 1], L[1, 1], di * n, dj * n)
            # colour pass: gradient horn-to-horn, then outline
            ctx.save()
            ctx.transform(m)
            tess.cairo_path(ctx)
            ctx.restore()
            g = cairo.LinearGradient(-1.4, 0.45, 2.4, 0.55)
            dark, base, light = ramp[c]
            g.add_color_stop_rgb(0.0, *dark)
            g.add_color_stop_rgb(0.45, *base)
            g.add_color_stop_rgb(1.0, *light)
            mi = cairo.Matrix(*m.as_tuple())
            mi.invert()
            g.set_matrix(mi)  # pattern lives in prototile units
            ctx.set_source(g)
            ctx.fill_preserve()
            ctx.set_source_rgb(0.05, 0.02, 0.08)
            ctx.set_line_width(stroke_px * ss)
            ctx.set_line_join(cairo.LINE_JOIN_ROUND)
            ctx.stroke()
            # id pass
            ictx.save()
            ictx.transform(m)
            tess.cairo_path(ictx)
            ictx.restore()
            v = id_of(c, di, dj)
            ictx.set_source_rgb((v & 255) / 255, ((v >> 8) & 255) / 255, 0)
            ictx.fill()
    col = _to_array(surf, n)
    ib = np.frombuffer(isurf.get_data(), np.uint8).reshape(n, isurf.get_stride() // 4, 4)[:, :n]
    ids = ib[..., 2].astype(np.int32) + 256 * ib[..., 1].astype(np.int32)
    if texture:
        rng = np.random.default_rng(seed)
        # periodic paper grain: white noise blurred with wrap-around, so the cell still tiles
        from scipy.ndimage import gaussian_filter
        g = gaussian_filter(rng.standard_normal((n, n)), ss * 0.6, mode="wrap")
        g2 = gaussian_filter(rng.standard_normal((n, n)), ss * 2.5, mode="wrap")
        g = g / g.std() * 0.65 + g2 / g2.std() * 0.35
        col = np.clip(col * (1 + texture * g[..., None]), 0, 1)
    return col.astype(np.float32), ids


def contact_sheet(path, P=150):
    from PIL import Image
    import itertools
    tiles = []
    perms = [(0, 2, 1, 3), (1, 3, 0, 2), (0, 1, 2, 3), (3, 2, 1, 0), (2, 0, 3, 1), (1, 0, 3, 2)]
    for o in perms:
        col, _ = render_cell(P, 2, order=o)
        im = Image.fromarray((np.tile(col, (2, 3, 1)) * 255).astype(np.uint8)).resize((3 * P, 2 * P))
        tiles.append(im)
    sheet = Image.new("RGB", (3 * (3 * P + 8), 2 * (2 * P + 8)), "white")
    for k, im in enumerate(tiles):
        sheet.paste(im, ((k % 3) * (3 * P + 8), (k // 3) * (2 * P + 8)))
    sheet.save(path)


if __name__ == "__main__":
    import sys
    contact_sheet(sys.argv[1] if len(sys.argv) > 1 else "cell_sheet.png")
