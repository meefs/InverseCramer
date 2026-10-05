"""Data for the web tile organ: tile outline, lattice, the tile as WebAudio Fourier series, and the score.
    python -m po_kit.web <score.json> <out.js>
The tile's (x, -y) trace becomes two PeriodicWaves per rotation (left = scope X, right = scope Y)."""
import json
import sys

import numpy as np

from po_kit import tess
from po_kit import audio as A
from po_kit import music as M

N_HARM = 24


def fourier(sig):
    X = np.fft.rfft(sig) / len(sig)
    real = 2 * X.real[: N_HARM + 1]
    imag = -2 * X.imag[: N_HARM + 1]
    real[0] = imag[0] = 0.0
    return [round(float(v), 6) for v in real], [round(float(v), 6) for v in imag]


def main(score_path, out):
    ph = np.arange(4096) / 4096
    p = tess.trace(ph) - A.tile_centre()
    waves = []
    for c in range(4):
        xy = p @ A.class_rotation(c).T  # c is the voice index
        waves.append(dict(x=fourier(xy[:, 0]), y=fourier(-xy[:, 1])))
    score = json.load(open(score_path))
    keep = lambda n: dict(t0=round(n["t0"], 3), t1=round(n["t1"], 3), site=n["site"], freq=round(n["freq"], 3))
    data = dict(title=__import__("os").environ.get("PO_TITLE", "Tile organ"),
        start=[float(v) for v in tess.START], segs=np.round(tess.SEGS, 4).tolist(),
        classes=[dict(color=tess.CLASSES[c][0], lin=np.round(tess.CLASSES[c][1] / np.hypot(*tess.CLASSES[c][1][:, 0]), 6).tolist(),
                      off=(tess.OFFSETS[c] / tess.CELL).round(6).tolist()) for c in tess.VOICE_CLASS],
        latA=(tess.LAT_A / tess.CELL).round(6).tolist(), latB=(tess.LAT_B / tess.CELL).round(6).tolist(),
        tileScale=round(float(np.hypot(*tess.CLASSES[0][1][:, 0]) / tess.CELL), 6),
        waves=waves, cRef=M.C_REF, ranges=M.RANGES,
        voices=[[keep(n) for n in v] for v in score["voices"]],
        ghost=[dict(keep(n), voice=n["voice"]) for n in score["ghost"]],
        duration=score["final_end"] + 1.0, drift=round(score["drift_cents"], 1))
    with open(out, "w") as f:
        f.write("window.ORGAN = " + json.dumps(data, separators=(",", ":")) + ";\n")
    print(out, len(json.dumps(data)) // 1024, "KB")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
