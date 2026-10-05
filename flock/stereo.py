"""Autostereogram from a depth map and a periodic pattern cell, plus a numeric decoder for QA.

Separation (Thimbleby, Inglis & Witten 1994):  s(z) = E (1 - mu z) / (2 - mu z), with E = 2P so that
the background (z = 0) repeats at exactly the pattern period P. Wall-eyed viewing; pass cross=True to flip.

Rather than copying colours, we propagate an *unwrapped pattern coordinate* u(x, y):
    u(x) = u(x - s(x)) + P       (seeded by one background period at the left edge)
so colour = cell[u mod P, y mod P] and the owning tile instance = (cell id, floor(u / P), floor(y / P)).
Sub-pixel separations are interpolated, which removes the depth terracing of integer methods.
"""
import numpy as np
from scipy.ndimage import uniform_filter

MU = 1 / 3


def separation(z, P, mu=MU):
    E = 2.0 * P
    return E * (1 - mu * z) / (2 - mu * z)


def depth_from_sep(s, P, mu=MU):
    E = 2.0 * P
    return (E - 2 * s) / (mu * (E - s))


def pattern_coords(depth, P, cross=False):
    z = 1 - depth if cross else depth
    H, W = z.shape
    sep = separation(z.astype(np.float64), P)
    u = np.zeros((H, W))
    rows = np.arange(H)
    # the seed strip must sit on the background plane (its pairs repeat at exactly P); the left edge does
    c0 = 0
    u[:, c0:c0 + P] = np.arange(c0, c0 + P)[None, :]
    for x in range(c0 + P, W):
        src = x - sep[:, x]
        i0 = np.floor(src).astype(int)
        f = src - i0
        u[:, x] = (1 - f) * u[rows, i0] + f * u[rows, i0 + 1] + P
    for x in range(c0 - 1, -1, -1):
        src = x + sep[:, x]
        i0 = np.floor(src).astype(int)
        f = src - i0
        u[:, x] = (1 - f) * u[rows, i0] + f * u[rows, np.minimum(i0 + 1, W - 1)] - P
    return u


def sample_cell(u, cell_blur, P, ss):
    """Bilinear sample of the (pre-blurred) supersampled cell at pattern coords (u, y)."""
    H, W = u.shape
    n = P * ss
    yy = np.broadcast_to(np.arange(H)[:, None], (H, W))
    fx = np.mod(u, P) * ss
    fy = np.mod(yy, P) * ss + 0.5 * ss
    x0 = np.floor(fx).astype(int)
    y0 = np.floor(fy).astype(int)
    ax = (fx - x0)[..., None]
    ay = (fy - y0)[..., None]
    x0 %= n
    y0 %= n
    x1 = (x0 + 1) % n
    y1 = (y0 + 1) % n
    c = cell_blur
    return ((1 - ay) * ((1 - ax) * c[y0, x0] + ax * c[y0, x1]) + ay * ((1 - ax) * c[y1, x0] + ax * c[y1, x1]))


def instance_map(u, cell_ids, P, ss):
    """Global tile-instance key per pixel: (class, lattice i, lattice j) packed into int64."""
    from flock.pattern import decode_id
    H, W = u.shape
    n = P * ss
    yy = np.broadcast_to(np.arange(H)[:, None], (H, W))
    xi = (np.floor(np.mod(u, P) * ss).astype(int)) % n
    yi = (np.floor(np.mod(yy, P) * ss + 0.5 * ss).astype(int)) % n
    c, di, dj = decode_id(cell_ids[yi, xi])
    gi = np.floor(u / P).astype(np.int64) + di + 1000
    gj = yy // P + dj + 1000
    return (c + 4 * gi + 4 * 4096 * gj).astype(np.int64)


def blur_cell(cell, ss):
    """Box pre-filter (wrap) so point sampling at 1x does not alias the 4x cell."""
    return uniform_filter(cell, size=(ss, ss, 1), mode="wrap")


def stereogram(depth, cell, cell_ids, P, ss, cross=False, cell_blur=None):
    u = pattern_coords(depth, P, cross)
    if cell_blur is None:
        cell_blur = blur_cell(cell, ss)
    img = sample_cell(u, cell_blur, P, ss)
    inst = instance_map(u, cell_ids, P, ss)
    return img.astype(np.float32), inst, u


def decode(img, P, win=(11, 21)):
    """Recover depth by matching each pixel with the one s pixels to its left (wall-eyed pairing)."""
    g = img.astype(np.float32)
    H, W, _ = g.shape
    smin, smax = int(np.floor(separation(1.0, P))) - 2, P + 2
    best = np.full((H, W), np.inf, np.float32)
    best_s = np.zeros((H, W), np.float32)
    costs = []
    for s in range(smin, smax + 1):
        d = np.full((H, W), 3.0, np.float32)
        d[:, s:] = np.abs(g[:, s:] - g[:, :-s]).sum(-1)
        # centre the comparison on the midpoint of the pair
        d = np.roll(d, -s // 2, axis=1)
        cst = uniform_filter(d, size=win)
        costs.append(cst)
        m = cst < best
        best[m] = cst[m]
        best_s[m] = s
    z = np.clip(depth_from_sep(best_s, P), 0, 1)
    return z, best


def qa_score(depth_true, z_rec, P, thr=0.25, tol=12):
    """Raw IoU plus an edge-tolerant F-score: block matching fattens foreground edges by about half
    its window, so a recovered pixel within `tol` px of the true shape still counts."""
    from scipy.ndimage import binary_dilation
    H, W = depth_true.shape
    m = np.zeros_like(depth_true, bool)
    m[:, P + 20:W - P - 20] = True  # the outermost repeat has nothing to match against
    a = (depth_true > thr) & m
    b = (z_rec > thr) & m
    iou = (a & b).sum() / max((a | b).sum(), 1)
    k = np.ones((2 * tol + 1, 2 * tol + 1), bool)
    precision = (b & binary_dilation(a, k)).sum() / max(b.sum(), 1)
    recall = (a & binary_dilation(b, k)).sum() / max(a.sum(), 1)
    f = 2 * precision * recall / max(precision + recall, 1e-9)
    inside = a & b
    corr = float(np.corrcoef(depth_true[inside], z_rec[inside])[0, 1]) if inside.sum() > 100 else 0.0
    return dict(f_tolerant=float(f), precision=float(precision), recall=float(recall), iou=float(iou), depth_corr=corr)
