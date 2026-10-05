"""Generate two test tessellation SVGs in the expected format (one prototile, matrix transforms, fills)."""
import math
import sys
from pathlib import Path

import numpy as np

# A leaf-like prototile: 6 cubic Beziers, not point-symmetric (so it has even harmonics too)
TILE = [(1.0, 0.0), (0.6, 0.9), (-0.2, 1.1), (-0.9, 0.5), (-1.1, -0.3), (-0.3, -0.8)]


def path_d():
    pts = [np.array(p) for p in TILE]
    d = f"M {pts[0][0]:.4f} {pts[0][1]:.4f}"
    for k in range(len(pts)):
        p0, p3 = pts[k], pts[(k + 1) % len(pts)]
        tang = np.array([-(p3 - p0)[1], (p3 - p0)[0]]) * 0.35
        c1, c2 = p0 + (p3 - p0) / 3 + tang, p0 + 2 * (p3 - p0) / 3 + tang * (0.2 if k % 2 else 1.4)
        d += f" C {c1[0]:.4f} {c1[1]:.4f} {c2[0]:.4f} {c2[1]:.4f} {p3[0]:.4f} {p3[1]:.4f}"
    return d + " Z"


def svg(classes, a, b, scale, n=6, size=(900, 600)):
    d = path_d()
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{size[0]}" height="{size[1]}"><rect width="{size[0]}" height="{size[1]}" fill="#f2efe6"/>']
    c0 = np.array(size) / 2
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            for ang, off, col in classes:
                t = c0 + i * np.array(a) + j * np.array(b) + np.array(off)
                if not (-150 < t[0] < size[0] + 150 and -150 < t[1] < size[1] + 150):
                    continue
                r = math.radians(ang)
                m = (scale * math.cos(r), scale * math.sin(r), -scale * math.sin(r), scale * math.cos(r), t[0], t[1])
                out.append(f'<path d="{d}" transform="matrix({" ".join(f"{v:.6f}" for v in m)})" fill="{col}" stroke="#000" stroke-width="0.02"/>')
    return "\n".join(out + ["</svg>"])


if __name__ == "__main__":
    o = Path(sys.argv[1])
    o.mkdir(parents=True, exist_ok=True)
    hexa, hexb = (90, 0), (45, 90 * math.sin(math.radians(60)))
    (o / "p3_hex.svg").write_text(svg([(0, (0, 0), "#e4572e"), (120, (0, 0), "#29335c"), (240, (0, 0), "#f3a712")], hexa, hexb, 34))
    c, s = math.cos(math.radians(10)), math.sin(math.radians(10))
    (o / "p2_offset.svg").write_text(svg([(0, (0, 0), "#2a9d8f"), (180, (38, 21), "#e76f51")], (80 * c, 80 * s), (-80 * s, 80 * c), 30))
    print("wrote", sorted(p.name for p in o.glob("*.svg")))
