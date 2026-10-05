"""M1: the still. Pattern cell -> gull depth -> stereogram -> decoder QA.

    python -m flock.still [outdir]

Writes: flock_still.png, depth.png, cell.png, qa.png (truth | recovered), qa.json,
and core.npz (everything the animation stage needs).
Exits non-zero if the decoder cannot find the gull (the QA gate).
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

from flock import depth as D
from flock import pattern, stereo

P = 150          # pattern period at 1080p on a ~24" monitor (about 42 mm)
SS = 4           # supersampling of the pattern cell
ORDER = (3, 2, 1, 0)
GULL_SCALE = 0.9
F_GATE = 0.90


def u8(a):
    return (np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)


def main(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    t = {}
    t0 = time.time()
    cell, ids = pattern.render_cell(P, SS, order=ORDER)
    t["cell"] = time.time() - t0
    t0 = time.time()
    z = D.gull_depth(0.0, scale=GULL_SCALE)
    t["depth"] = time.time() - t0
    t0 = time.time()
    cell_blur = stereo.blur_cell(cell, SS)
    img, inst, u = stereo.stereogram(z, cell, ids, P, SS, cell_blur=cell_blur)
    t["stereogram"] = time.time() - t0
    t0 = time.time()
    zr, _ = stereo.decode(img, P)
    score = stereo.qa_score(z, zr, P)
    t["decode"] = time.time() - t0

    Image.fromarray(u8(img)).save(out / "flock_still.png")
    Image.fromarray(u8(z)).save(out / "depth.png")
    Image.fromarray(u8(cell_blur)).resize((P, P), Image.LANCZOS).save(out / "cell.png")
    Image.fromarray(u8(cell_blur)).save(out / "cell_ss.png")
    side = np.concatenate([u8(z), np.full((z.shape[0], 16), 255, np.uint8), u8(zr)], axis=1)
    Image.fromarray(side).resize((side.shape[1] // 2, side.shape[0] // 2)).save(out / "qa.png")
    np.savez_compressed(out / "core.npz", img=u8(img), inst=inst, depth=u8(z), cell=cell_blur.astype(np.float16), ids=ids)
    report = dict(P=P, ss=SS, order=ORDER, **score, gate_f_tolerant=F_GATE, passed=score["f_tolerant"] >= F_GATE,
                  timings_s={k: round(v, 2) for k, v in t.items()})
    (out / "qa.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "build/flock"))
