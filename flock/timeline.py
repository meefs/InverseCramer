"""One clock for picture and music.

Tempo 80 bpm, 4/4: a bar is 3 s. The last swift lands on the downbeat of bar 6 (15.0 s), where the
score resolves; the hidden gull beats its wings bars 10-12 (27-36 s), one beat of the wings per two beats.
Landings are quantised to sixteenth notes so each one can sound as a pizzicato in the score.
"""
import json
from pathlib import Path

import numpy as np

BPM = 80
BEAT = 60 / BPM
SIXTEENTH = BEAT / 4
FPS = 12
DURATION = 42.0
FIRST_LAND = 3.0
LAST_LAND = 15.0
FLAP_START, FLAP_END, FLAP_PERIOD = 27.0, 36.0, 2 * BEAT
GUIDE_DOTS_AT = 16.5
CENTRE = (960, 560)


def flap_at(t):
    """Hidden gull wing value in [-1, 1]; zero (rest pose) outside the flap section."""
    if t <= FLAP_START or t >= FLAP_END:
        return 0.0
    x = (t - FLAP_START) / (FLAP_END - FLAP_START)
    env = np.sin(np.pi * x) ** 0.6
    return float(env * np.sin(2 * np.pi * (t - FLAP_START) / FLAP_PERIOD))


def landing_schedule(inst, seed=15):
    """Label tile instances in the finished stereogram and give each a landing time and flight."""
    keys, labels = np.unique(inst.ravel(), return_inverse=True)
    labels = labels.reshape(inst.shape)
    n = len(keys)
    H, W = inst.shape
    yy, xx = np.mgrid[0:H, 0:W]
    cnt = np.bincount(labels.ravel(), minlength=n)
    cx = np.bincount(labels.ravel(), xx.ravel(), n) / cnt
    cy = np.bincount(labels.ravel(), yy.ravel(), n) / cnt
    rng = np.random.default_rng(seed)
    dist = np.hypot(cx - CENTRE[0], (cy - CENTRE[1]) * 1.6) + rng.uniform(0, 60, n)
    rank = np.empty(n, int)
    rank[np.argsort(dist)] = np.arange(n)
    frac = rank / max(n - 1, 1)
    t = FIRST_LAND + (LAST_LAND - FIRST_LAND) * frac ** 0.85
    t = np.floor(t / SIXTEENTH + 1e-6) * SIXTEENTH
    t[np.argmax(rank)] = LAST_LAND
    # flights: loose flocks of ~10 consecutive landers share an entry point beyond the nearest edge
    flock = rank // 10
    n_flocks = flock.max() + 1
    ang_f = rng.uniform(-np.pi, np.pi, n_flocks)
    entry = []
    for i in range(n):
        a = np.arctan2(cy[i] - CENTRE[1], cx[i] - CENTRE[0]) * 0.6 + ang_f[flock[i]] * 0.4
        r = 1250 + rng.uniform(0, 250)
        entry.append((CENTRE[0] + r * np.cos(a) + rng.normal(0, 70), CENTRE[1] + 0.75 * r * np.sin(a) + rng.normal(0, 70)))
    entry = np.array(entry)
    dur = rng.uniform(1.8, 2.8, n)
    bend = rng.uniform(-0.45, 0.45, n_flocks)[flock] + rng.normal(0, 0.06, n)
    phase = rng.integers(0, 4, n)
    keys_c = keys % 4
    return dict(labels=labels, n=n, count=cnt, cx=cx, cy=cy, t_land=t, t_start=t - dur, entry=entry,
                bend=bend, flap_phase=phase, cls=keys_c)


def write_audio_cues(sched, path):
    """Landing cues for the score: per sixteenth, how many swifts land (and which colour class)."""
    slots = {}
    for t, c in zip(sched["t_land"], sched["cls"]):
        k = round(float(t) / SIXTEENTH)
        slots.setdefault(k, [0, 0, 0, 0])[int(c)] += 1
    cues = dict(bpm=BPM, sixteenth=SIXTEENTH, landings=[[k * SIXTEENTH, v] for k, v in sorted(slots.items())],
                last_land=LAST_LAND, flap=[FLAP_START, FLAP_END, FLAP_PERIOD], duration=DURATION)
    Path(path).write_text(json.dumps(cues))
    return cues
