"""Tessellation 15: read the source SVG and expose its geometry.

The SVG is one prototile (12 cubic Beziers, self-intersecting) placed 964 times.
Four rotations (90 deg apart, one colour each) share a pivot, and a square
lattice (83.07 px, tilted 22 deg) translates the pinwheel. Because the outline
crosses itself, neighbouring tiles overlap and the draw order decides what is
visible. Everything here is derived from the file, nothing is hand-copied.
"""
import math
import re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SVG = ROOT / "canon" / "tessellation_15.svg"


def _parse():
    s = SVG.read_text()
    paths = re.findall(r'<path d="([^"]+)" transform="matrix\(([^)]+)\)" fill="([^"]+)"', s)
    d = paths[0][0]
    nums = [float(v) for v in re.findall(r"-?\d+\.\d+", d)]
    start = nums[:2]
    segs = np.array(nums[2:]).reshape(-1, 3, 2)  # (12, 3 control points, xy)
    inst = []
    for _, m, col in paths:
        a, b, c, dd, e, f = map(float, m.split())
        inst.append((np.array([[a, c], [b, dd]]), np.array([e, f]), col))
    return np.array(start), segs, inst


START, SEGS, INSTANCES = _parse()
BACKGROUND = "#ede4d3"

# Colour classes in the order of their rotation angle (0, 90, 180, 270 deg from class 0).
_lin0 = INSTANCES[0][0]
CLASSES = []  # (hex colour, 2x2 linear part) ; all four share the pivot of instance 0
for lin, t, col in INSTANCES:
    if np.allclose(t, INSTANCES[0][1]) and col not in [c for c, _ in CLASSES]:
        CLASSES.append((col, lin))
CLASSES.sort(key=lambda cl: (math.atan2(cl[1][1, 0], cl[1][0, 0]) - math.atan2(_lin0[1, 0], _lin0[0, 0]) + 1e-6) % (2 * math.pi))
PIVOT = INSTANCES[0][1].copy()


def _lattice():
    # shortest translation between same-class instances
    col0, lin0 = CLASSES[0]
    pts = np.array([t for lin, t, c in INSTANCES if c == col0 and np.allclose(lin, lin0)])
    dv = pts - PIVOT
    dv = dv[np.hypot(*dv.T) > 1e-6]
    a = dv[np.argmin(np.hypot(*dv.T) + 1e-3 * (dv[:, 0] < 0) + 1e-3 * (dv[:, 1] < 0))]
    b = np.array([-a[1], a[0]])
    return a, b


LAT_A, LAT_B = _lattice()
CELL = float(np.hypot(*LAT_A))              # 83.07 px in the SVG
TILT = math.atan2(LAT_A[1], LAT_A[0])       # 22.0 deg


def bezier_points(n_per_seg=24):
    """Flattened prototile outline in prototile units, (12*n, 2)."""
    out = []
    p0 = START
    t = np.linspace(0, 1, n_per_seg, endpoint=False)[:, None]
    for c1, c2, p3 in SEGS:
        pts = ((1 - t) ** 3) * p0 + 3 * ((1 - t) ** 2) * t * c1 + 3 * (1 - t) * t * t * c2 + t ** 3 * p3
        out.append(pts)
        p0 = p3
    return np.concatenate(out)


def trace(phase):
    """Position on the outline at phase in [0,1) (each Bezier gets 1/12 of a turn). Vectorised."""
    phase = np.asarray(phase) % 1.0
    k = np.minimum((phase * len(SEGS)).astype(int), len(SEGS) - 1)
    t = (phase * len(SEGS) - k)[..., None]
    ctrl = np.concatenate([np.vstack([START, SEGS[:-1, 2]])[:, None], SEGS], axis=1)  # (12,4,2)
    p0, c1, c2, p3 = (ctrl[k, i] for i in range(4))
    return ((1 - t) ** 3) * p0 + 3 * ((1 - t) ** 2) * t * c1 + 3 * (1 - t) * t * t * c2 + t ** 3 * p3


def cairo_path(ctx):
    """Append the prototile outline (prototile units) to a cairo context."""
    ctx.move_to(*START)
    for c1, c2, p3 in SEGS:
        ctx.curve_to(*c1, *c2, *p3)
    ctx.close_path()


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def shade(rgb, light=0.0, sat=0.0):
    """Shift lightness (-1..1) and saturation (-1..1) in HLS."""
    import colorsys
    h, l, s = colorsys.rgb_to_hls(*rgb)
    l = min(1, max(0, l + light * (1 - l if light > 0 else l)))
    s = min(1, max(0, s + sat * (1 - s if sat > 0 else s)))
    return colorsys.hls_to_rgb(h, l, s)


if __name__ == "__main__":
    print(f"{len(INSTANCES)} instances, {len(SEGS)} Bezier segments")
    print("classes:", [c for c, _ in CLASSES])
    print(f"lattice {CELL:.3f} px, tilt {math.degrees(TILT):.3f} deg, pivot {PIVOT}")
    print("prototile scale", np.hypot(*_lin0[:, 0]))
