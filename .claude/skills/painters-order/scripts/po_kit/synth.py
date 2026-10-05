"""A small NumPy orchestra: everything is synthesised (no samples), deterministic, and vectorised.

Voices: bowed strings (with optional tremolo), oboe (saw through formant filters), plucked harp /
pizzicato (modal), celesta (struck bar), flute (with flutter-tongue), timpani (modes + roll).
A convolution hall finishes the mix.
"""
import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

SR = 48000


def mtof(m):
    return 440.0 * 2 ** ((np.asarray(m, float) - 69) / 12)


NOTE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def n(name):
    """'F#5' -> MIDI number."""
    base = NOTE[name[0]]
    i = 1
    while i < len(name) and name[i] in "#b":
        base += 1 if name[i] == "#" else -1
        i += 1
    return base + 12 * (int(name[i:]) + 1)


def _t(dur):
    return np.arange(int(dur * SR)) / SR


def _env(nsamp, a, r, hold=None):
    """Attack / sustain / release envelope over nsamp samples."""
    t = np.arange(nsamp) / SR
    dur = nsamp / SR
    e = np.clip(t / max(a, 1e-4), 0, 1)
    rel_start = dur - r
    e *= np.clip((dur - t) / max(r, 1e-4), 0, 1) if rel_start > 0 else 1
    return e


def _saw(freq):
    """Band-limited sawtooth via polyBLEP; freq is a per-sample array (so vibrato is free)."""
    dt = np.asarray(freq, float) / SR
    ph = np.cumsum(dt) % 1.0
    y = 2 * ph - 1
    m1 = ph < dt
    x = ph[m1] / dt[m1]
    y[m1] -= x + x - x * x - 1
    m2 = ph > 1 - dt
    x = (ph[m2] - 1) / dt[m2]
    y[m2] -= x * x + x + x + 1
    return y


def _lp(x, fc, order=2):
    sos = butter(order, min(fc, SR * 0.45), "low", fs=SR, output="sos")
    return sosfilt(sos, x)


def _bp(x, fc, q):
    bw = fc / q
    sos = butter(2, [max(20, fc - bw / 2), min(SR * 0.45, fc + bw / 2)], "band", fs=SR, output="sos")
    return sosfilt(sos, x)


def _vibrato(nsamp, f, rate=5.3, depth=0.004, delay=0.25, seed=0):
    t = np.arange(nsamp) / SR
    rng = np.random.default_rng(seed)
    ramp = np.clip((t - delay) / 0.4, 0, 1)
    return f * (1 + depth * ramp * np.sin(2 * np.pi * rate * t + rng.uniform(0, 6.28)))


# ---- voices ------------------------------------------------------------------------------------
def strings(m, dur, vel=0.5, tremolo=False, seed=0, bright=1.0):
    f = mtof(m)
    ns = int(dur * SR)
    rng = np.random.default_rng(seed + int(m * 7))
    y = np.zeros(ns)
    for det in (-0.0035, 0.0, 0.0042):
        y += _saw(_vibrato(ns, f * (1 + det), rate=5.0 + rng.uniform(-0.4, 0.4), depth=0.0035, seed=seed))
    y = _lp(y, (1400 + 3200 * vel) * bright)
    y = _lp(y, 6000)
    env = _env(ns, 0.18 if not tremolo else 0.05, min(0.45, dur * 0.4))
    if tremolo:
        t = np.arange(ns) / SR
        env *= 0.55 + 0.45 * (0.5 + 0.5 * np.cos(2 * np.pi * 12.5 * t + rng.uniform(0, 6))) ** 2
    return y * env * vel * 0.22


def oboe(m, dur, vel=0.6, seed=0):
    f = mtof(m)
    ns = int(dur * SR)
    src = _saw(_vibrato(ns, f, rate=5.4, depth=0.005, delay=0.3, seed=seed))
    y = 0.9 * _bp(src, 1150, 2.5) + 0.6 * _bp(src, 2900, 3.5) + 0.25 * _lp(src, 900)
    breath = _bp(np.random.default_rng(seed).standard_normal(ns), 2500, 1.5) * 0.03
    env = _env(ns, 0.06, min(0.25, dur * 0.35))
    swell = 0.85 + 0.15 * np.sin(np.pi * np.clip(np.arange(ns) / max(ns - 1, 1), 0, 1))
    return (y + breath) * env * swell * vel * 0.5


def pluck(m, dur, vel=0.6, bright=1.0, decay=1.0, pos=0.18):
    """Harp / pizzicato: a string's modes with frequency-dependent damping."""
    f = mtof(m)
    t = _t(dur)
    y = np.zeros_like(t)
    for k in range(1, 24):
        fk = f * k * (1 + 0.0004 * k * k)
        if fk > SR * 0.45:
            break
        a = abs(np.sin(np.pi * k * pos)) / k ** (1.4 - 0.3 * bright)
        y += a * np.sin(2 * np.pi * fk * t) * np.exp(-t * (0.9 + 0.35 * k ** 1.25) * decay * (f / 300) ** 0.35)
    att = np.clip(t / 0.002, 0, 1)
    return y * att * vel * 0.35


def celesta(m, dur, vel=0.6):
    f = mtof(m)
    t = _t(dur)
    y = (np.sin(2 * np.pi * f * t) * np.exp(-t * 1.6)
         + 0.25 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t * 7)
         + 0.12 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 11)
         + 0.05 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 25))
    click = np.exp(-t * 900) * np.sin(2 * np.pi * 3 * f * t) * 0.3
    return (y + click) * np.clip(t / 0.0015, 0, 1) * vel * 0.32


def flute(m, dur, vel=0.4, flutter=False, seed=0):
    f = mtof(m)
    ns = int(dur * SR)
    t = np.arange(ns) / SR
    fv = _vibrato(ns, f, rate=5.0, depth=0.004, delay=0.2, seed=seed)
    ph = np.cumsum(fv) / SR
    y = np.sin(2 * np.pi * ph) + 0.18 * np.sin(4 * np.pi * ph) + 0.05 * np.sin(6 * np.pi * ph)
    y += _bp(np.random.default_rng(seed).standard_normal(ns), f * 2, 2) * 0.12
    env = _env(ns, 0.07, min(0.3, dur * 0.4))
    if flutter:
        env *= 0.5 + 0.5 * (0.5 + 0.5 * np.sin(2 * np.pi * 23 * t)) ** 1.5
    return y * env * vel * 0.3


def timpani(m, dur, vel=0.7, seed=0):
    f = mtof(m)
    t = _t(dur)
    y = (np.sin(2 * np.pi * f * t) * np.exp(-t * 1.8) + 0.5 * np.sin(2 * np.pi * f * 1.5 * t) * np.exp(-t * 3)
         + 0.3 * np.sin(2 * np.pi * f * 1.99 * t) * np.exp(-t * 4.5))
    hit = _lp(np.random.default_rng(seed).standard_normal(len(t)), 900) * np.exp(-t * 40) * 0.6
    return (y + hit) * vel * 0.5


def timpani_roll(m, dur, v0=0.15, v1=0.8, seed=0):
    out = np.zeros(int((dur + 2.0) * SR))
    rng = np.random.default_rng(seed)
    tt = 0.0
    while tt < dur:
        v = v0 + (v1 - v0) * (tt / dur) ** 1.5
        h = timpani(m, 1.6, v * rng.uniform(0.8, 1.0), seed=int(tt * 1000))
        i = int(tt * SR)
        out[i:i + len(h)] += h[: len(out) - i]
        tt += 0.055 + rng.uniform(-0.008, 0.008)
    return out


def noise_flutter(dur, vel=0.3, seed=0):
    """Wing flutter: band-passed noise with a fast irregular amplitude."""
    ns = int(dur * SR)
    t = np.arange(ns) / SR
    rng = np.random.default_rng(seed)
    x = _bp(rng.standard_normal(ns), 1800, 1.2)
    am = (0.5 + 0.5 * np.sin(2 * np.pi * (17 + 4 * np.sin(2 * np.pi * 0.7 * t)) * t)) ** 3
    return x * am * _env(ns, 0.05, 0.2) * vel * 0.25


# ---- mixing ------------------------------------------------------------------------------------
class Mix:
    def __init__(self, dur):
        self.buf = np.zeros((int((dur + 4) * SR), 2))

    def add(self, t, sig, pan=0.0, gain=1.0):
        i = int(round(t * SR))
        if i >= len(self.buf):
            return
        sig = sig[: len(self.buf) - i] * gain
        l = np.cos((pan + 1) * np.pi / 4)
        r = np.sin((pan + 1) * np.pi / 4)
        self.buf[i:i + len(sig), 0] += sig * l
        self.buf[i:i + len(sig), 1] += sig * r

    def add_stereo(self, t, lr, gain=1.0):
        i = int(round(t * SR))
        lr = lr[: len(self.buf) - i] * gain
        self.buf[i:i + len(lr)] += lr


def hall_ir(rt60=2.3, seed=7, predelay=0.02):
    n_ = int((rt60 + predelay) * SR)
    t = np.arange(n_) / SR
    rng = np.random.default_rng(seed)
    ir = np.zeros((n_, 2))
    for ch in range(2):
        x = rng.standard_normal(n_) * np.exp(-6.9 * t / rt60)
        # darker tail: blend toward low-passed noise over time
        lo = _lp(x, 2500)
        w = np.clip(t / rt60, 0, 1)
        ir[:, ch] = (1 - w) * x + w * lo
    ir[: int(predelay * SR)] = 0
    for d, g in ((0.011, 0.5), (0.019, 0.35), (0.027, 0.3), (0.041, 0.2)):
        ir[int((predelay + d) * SR), 0] += g
        ir[int((predelay + d * 1.13) * SR), 1] += g
    return ir / np.sqrt((ir ** 2).sum(0))


def finish(dry, wet=0.28, rt60=2.3, peak_db=-1.0, fade_out=2.5, length=None):
    ir = hall_ir(rt60)
    rev = np.stack([fftconvolve(dry[:, c], ir[:, c])[: len(dry)] for c in range(2)], 1)
    y = (1 - wet) * dry + wet * rev * 1.6
    if length:
        y = y[: int(length * SR)]
    if fade_out:
        k = int(fade_out * SR)
        y[-k:] *= np.linspace(1, 0, k)[:, None] ** 2
    y -= y.mean(0)
    y *= 10 ** (peak_db / 20) / (np.abs(y).max() + 1e-9)
    return y.astype(np.float32)


def write_wav(path, y):
    from scipy.io import wavfile
    wavfile.write(path, SR, (np.clip(y, -1, 1) * 32767).astype(np.int16))
