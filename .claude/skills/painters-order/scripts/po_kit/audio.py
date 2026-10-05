"""The soundtrack is the picture: each voice traces its tile outline once per period.

Left channel = scope X, right channel = scope Y (up is positive). The tile's shape is the waveform,
so its timbre comes straight from the outline (`python -m po_kit.tess` prints the spectrum).
The scope picture is drawn from the raw signal; the speaker feed is DC-blocked and lightly smoothed.
    python -m po_kit.audio <builddir>
"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy.signal import butter, sosfilt

from po_kit import synth as S
from po_kit import tess
from po_kit import music as M

GAINS = [0.85, 0.62, 0.5, 0.42]
GHOST_GAIN = 0.55


def class_rotation(v):
    """Unit-scale linear part of the class that voice v traces."""
    L = tess.CLASSES[tess.VOICE_CLASS[v]][1]
    return L / np.hypot(*L[:, 0])


def tile_centre():
    ph = np.arange(4096) / 4096
    return tess.trace(ph).mean(0)


def render_stream(notes, voice, t, gain):
    """One voice's (x, y) signal over the sample times t."""
    freq = np.zeros_like(t)
    for nt in notes:
        freq[t >= nt["t0"]] = nt["freq"]
    phase = np.cumsum(freq) / S.SR
    p = tess.trace(phase) - tile_centre()
    xy = p @ class_rotation(voice).T
    amp = M.envelope(notes, t, gain)
    return np.stack([xy[:, 0], -xy[:, 1]], 1) * amp[:, None]


def main(build):
    build = Path(build)
    build.mkdir(parents=True, exist_ok=True)
    score = M.build()
    (build / "score.json").write_text(json.dumps(score, default=float))
    t = np.arange(int(score["duration"] * S.SR)) / S.SR
    mix = np.zeros((len(t), 2))
    for v, notes in enumerate(score["voices"]):
        mix += render_stream(notes, v, t, GAINS[v])
    for g in score["ghost"]:
        mix += render_stream([g], g["voice"], t, GAINS[g["voice"]] * GHOST_GAIN)
    for g in score["coda"]:
        mix += render_stream([g], g["voice"], t, GAINS[g["voice"]] * 0.8)
    np.save(build / "scope_raw.npy", mix[::4].astype(np.float32))  # what the scope sees (12 kHz)
    hp = butter(2, 25, "high", fs=S.SR, output="sos")
    lp = butter(2, 7000, "low", fs=S.SR, output="sos")
    speaker = sosfilt(lp, sosfilt(hp, mix, axis=0), axis=0)
    y = S.finish(speaker, wet=0.32, rt60=3.2, peak_db=-1.5, fade_out=4.0, length=score["duration"])
    S.write_wav(build / "score.wav", y)
    print("score.wav", round(len(y) / S.SR, 1), "s; drift", round(score["drift_cents"], 1), "cents")


if __name__ == "__main__":
    main(sys.argv[1])
