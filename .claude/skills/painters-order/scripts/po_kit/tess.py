"""Read a tessellation SVG and expose its geometry.

Expected input (the format tessellation tools such as meefs' tessellation lab export): one prototile drawn as an
absolute `M x y C ... Z` path and placed many times, each copy a <path> with the same `d`, a
`transform="matrix(a b c d e f)"` and a `fill`. Everything is derived from the file:

  CLASSES   one entry per distinct orientation (rotation/reflection) of the tile: (hex colour, 2x2 linear part)
  OFFSETS   per class, where its copy sits relative to the pivot of class 0 (zero when all share a pivot)
  LAT_A/B   a reduced basis of the translation lattice (shortest vector first, then the shortest independent one)
  VOICE_CLASS  which class each of the four voices traces (cycled when there are fewer than four classes)

Set the file with the PO_SVG environment variable (run.sh does this).
    PO_SVG=tiles.svg python -m po_kit.tess     -> prints an analysis, including the tile's harmonic spectrum
"""
import colorsys
import math
import os
import re
from collections import Counter
from pathlib import Path

import numpy as np

_NUM = r"-?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"


def _parse_path(d):
    tokens = re.findall(r"[MmCcZzLlHhVvSsQqTtAa]|" + _NUM, d)
    if not tokens or tokens[0] != "M":
        raise ValueError("prototile path must start with an absolute 'M'")
    letters = {t for t in tokens if t.isalpha()}
    if not letters <= {"M", "C", "Z", "z"}:
        raise ValueError(f"prototile path uses {sorted(letters - {'M', 'C', 'Z', 'z'})}; convert it to absolute M/C/Z "
                         "(e.g. Inkscape: Path > Object to Path, then save with absolute coordinates)")
    nums = [float(t) for t in tokens if not t.isalpha()]
    start = np.array(nums[:2])
    rest = nums[2:]
    if len(rest) % 6:
        raise ValueError("prototile path: cubic segments must each have 6 numbers")
    return start, np.array(rest).reshape(-1, 3, 2)


def _parse(svg):
    s = svg.read_text()
    bg = re.search(r'<rect[^>]*\bfill="([^"]+)"', s)
    inst, d0 = [], None
    for tag in re.findall(r"<path\b[^>]*>", s):
        d = re.search(r'\sd="([^"]+)"', tag)
        m = re.search(r'transform="matrix\(([^)]+)\)"', tag)
        if not (d and m):
            continue
        if d0 is None:
            d0 = d.group(1)
        elif d.group(1) != d0:
            continue  # only copies of the first prototile
        a, b, c, dd, e, f = (float(v) for v in re.split(r"[\s,]+", m.group(1).strip()))
        fill = re.search(r'\bfill="([^"]+)"', tag)
        inst.append((np.array([[a, c], [b, dd]]), np.array([e, f]), fill.group(1) if fill else "#8a7ccf"))
    if d0 is None:
        raise ValueError("no <path d=... transform=\"matrix(...)\"> copies found; see SKILL.md for the expected format")
    start, segs = _parse_path(d0)
    return start, segs, inst, (bg.group(1) if bg else "#ede4d3")


SVG = Path(os.environ.get("PO_SVG", ""))
if not SVG.is_file():
    raise SystemExit("Set PO_SVG to the tessellation SVG (run.sh does this for you).")
START, SEGS, INSTANCES, BACKGROUND = _parse(SVG)

# ---- orientation classes ----------------------------------------------------------------------------
_scale = float(np.sqrt(abs(np.linalg.det(INSTANCES[0][0]))))
_groups = {}
for lin, t, col in INSTANCES:
    key = tuple(np.round(lin / _scale, 3).ravel())
    _groups.setdefault(key, []).append((lin, t, col))
_lin0 = INSTANCES[0][0]


def _angle(lin):
    return (math.atan2(lin[1, 0], lin[0, 0]) - math.atan2(_lin0[1, 0], _lin0[0, 0]) + 1e-6) % (2 * math.pi)


_cls = sorted(_groups.values(), key=lambda g: (np.linalg.det(g[0][0]) < 0, _angle(g[0][0])))
CLASSES = [(Counter(c for _, _, c in g).most_common(1)[0][0], g[0][0]) for g in _cls]
PIVOT = _cls[0][0][1].copy()


# ---- lattice ------------------------------------------------------------------------------------------
def _lattice():
    pts = np.array([t for _, t, _ in _cls[0]])
    dv = (pts[None] - pts[:, None]).reshape(-1, 2)
    dv = dv[np.hypot(*dv.T) > 1e-6 * _scale]
    if len(dv) == 0:
        raise ValueError("only one copy per orientation; the SVG needs several translated copies to find the lattice")
    L = np.hypot(*dv.T)
    order = np.argsort(L + 1e-9 * (-dv[:, 0]))
    a = dv[order[0]]
    tol = 1e-3 * L[order[0]]
    shortest = dv[L < L[order[0]] + tol]
    a = shortest[np.argmax(shortest[:, 0] + 1e-6 * shortest[:, 1])]
    cand = [v for v in dv[order] if abs(a[0] * v[1] - a[1] * v[0]) > 1e-3 * np.hypot(*a) * np.hypot(*v)]
    if not cand:
        raise ValueError("all copies lie on one line; a 2-D lattice is needed")
    Lb = np.hypot(*cand[0])
    b_opts = [v for v in cand if np.hypot(*v) < Lb + tol and a[0] * v[1] - a[1] * v[0] > 0]
    b = b_opts[0] if b_opts else -cand[0]
    return a, b


LAT_A, LAT_B = _lattice()
CELL = float(np.hypot(*LAT_A))
_basis_inv = np.linalg.inv(np.stack([LAT_A, LAT_B], 1))


def _reduce(v):
    ij = _basis_inv @ v
    return v - np.stack([LAT_A, LAT_B], 1) @ np.round(ij)


OFFSETS = []
for g in _cls:
    ts = np.array([_reduce(t - PIVOT) for _, t, _ in g])
    OFFSETS.append(ts[np.argmin(np.hypot(*ts.T))])
VOICE_CLASS = [v % min(len(CLASSES), 4) for v in range(4)]


# ---- the outline as a curve and as a sound ----------------------------------------------------------------
def trace(phase):
    """Point on the outline at phase in [0,1) (each Bezier segment gets an equal share). Vectorised."""
    phase = np.asarray(phase) % 1.0
    n = len(SEGS)
    k = np.minimum((phase * n).astype(int), n - 1)
    t = (phase * n - k)[..., None]
    ctrl = np.concatenate([np.vstack([START, SEGS[:-1, 2]])[:, None], SEGS], axis=1)
    p0, c1, c2, p3 = (ctrl[k, i] for i in range(4))
    return ((1 - t) ** 3) * p0 + 3 * ((1 - t) ** 2) * t * c1 + 3 * (1 - t) * t * t * c2 + t ** 3 * p3


def bezier_points(n_per_seg=24):
    return trace(np.arange(len(SEGS) * n_per_seg) / (len(SEGS) * n_per_seg))


def cairo_path(ctx):
    ctx.move_to(*START)
    for c1, c2, p3 in SEGS:
        ctx.curve_to(*c1, *c2, *p3)
    ctx.close_path()


def spectrum(n=16):
    """Relative harmonic amplitudes of the outline traced as a waveform (x and y channels)."""
    p = trace(np.arange(4096) / 4096)
    p = p - p.mean(0)
    out = []
    for ch in range(2):
        X = np.abs(np.fft.rfft(p[:, ch]))[1:n + 1]
        out.append(X / max(X[0], 1e-12))
    return np.array(out)


def hex_rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def shade(rgb, light=0.0, sat=0.0):
    h, l, s = colorsys.rgb_to_hls(*rgb)
    l = min(1, max(0, l + light * (1 - l if light > 0 else l)))
    s = min(1, max(0, s + sat * (1 - s if sat > 0 else s)))
    return colorsys.hls_to_rgb(h, l, s)


if __name__ == "__main__":
    print(f"{SVG.name}: {len(INSTANCES)} copies of one prototile ({len(SEGS)} cubic Beziers)")
    for k, ((col, lin), off) in enumerate(zip(CLASSES, OFFSETS)):
        kind = "reflection" if np.linalg.det(lin) < 0 else "rotation"
        print(f"  class {k}: {col}  {kind} {math.degrees(_angle(lin)):6.1f} deg  offset {np.round(off, 2)}  copies {len(_cls[k])}")
    ang = math.degrees(math.acos(np.dot(LAT_A, LAT_B) / (np.hypot(*LAT_A) * np.hypot(*LAT_B))))
    print(f"lattice: |a| = {CELL:.2f}, |b| = {np.hypot(*LAT_B):.2f}, angle {ang:.1f} deg, a tilted "
          f"{math.degrees(math.atan2(LAT_A[1], LAT_A[0])):.1f} deg")
    print("voices -> classes:", VOICE_CLASS)
    sp = spectrum()
    odd_only = sp[:, 1::2].max() < 0.02
    print("harmonics x:", " ".join(f"{v:.2f}" for v in sp[0]))
    print("harmonics y:", " ".join(f"{v:.2f}" for v in sp[1]))
    print("timbre:", "odd harmonics only (point-symmetric tile, clarinet-like)" if odd_only else "odd and even harmonics")
