"""Painter's Order: the score, which is also the choreography.

The tessellation's square lattice is read as a Tonnetz in 5-limit just intonation:
    one lattice step along a  = a perfect fifth (x 3/2)
    one lattice step along b  = a major third   (x 5/4)
so every lattice site is a pitch, and a triad is a little triangle of sites.

Four voices, one per colour class (the four 90-degree rotations of the tile). A voice sounds by tracing
its tile around the site of its current note, once per period: the waveform *is* the outline.

The progression is the classic comma pump  C - Am - Dm - G - C  played strictly in tune, holding every
common tone. Each round trip comes home a syntonic comma (81/80, 21.5 cents) flatter, and on the lattice
that is a shift of (-4, +1): the chorale walks across the tessellation and paints it as it goes.
"""
import itertools
import json
import os

import numpy as np

from po_kit import tess

C_REF = float(os.environ.get("PO_CREF", 130.8128))  # C3 (equal-tempered reference for the opening C)
CYCLES = int(os.environ.get("PO_CYCLES", 6))
DIRECTION = os.environ.get("PO_DIRECTION", "down").lower()  # "down": the classic pump sinks; "up": reversed, it rises
if DIRECTION not in ("down", "up"):
    raise SystemExit("PO_DIRECTION must be 'down' or 'up'")
CHORD_DUR = float(os.environ.get("PO_CHORD_DUR", 1.6))
INTRO = [(0.0, 0), (2.0, 1), (2.5, 2), (3.0, 3)]   # (entry time, voice): bass alone, then the rest
FIRST_CHANGE = 4.4
RANGES = [(60, 200), (125, 330), (190, 520), (250, 800)]  # bass, tenor, alto, soprano in Hz
NAMES = ["bass", "tenor", "alto", "soprano"]
ATTACK, RELEASE = 0.03, 0.30


PROGRESSION = ["C", "Am", "Dm", "G"] if DIRECTION == "down" else ["C", "G", "Dm", "Am"]
PUMP_STEP = (-4, 1) if DIRECTION == "down" else (4, -1)  # home's lattice move per round: 80/81 flat or 81/80 sharp


def comma_pump(home):
    """Four chords of the pump starting from C at `home`; returns list of (root, [three sites])."""
    hi, hj = home
    S = lambda di, dj: (hi + di, hj + dj)
    if DIRECTION == "up":  # the pump reversed: C - G - Dm - Am, every common tone held
        return [
            (S(0, 0), [S(0, 0), S(0, 1), S(1, 0)]),      # C  : C E G
            (S(1, 0), [S(1, 0), S(1, 1), S(2, 0)]),      # G  : G B D   (G held)
            (S(2, 0), [S(2, 0), S(3, -1), S(3, 0)]),     # Dm : D F A   (D held)
            (S(3, 0), [S(3, 0), S(4, -1), S(4, 0)]),     # Am : A C E   (A held) - this C is a comma above the first
        ]
    return [
        (S(0, 0), [S(0, 0), S(0, 1), S(1, 0)]),      # C  : C E G
        (S(-1, 1), [S(-1, 1), S(0, 0), S(0, 1)]),    # Am : A C E   (C, E held)
        (S(-2, 1), [S(-2, 1), S(-1, 0), S(-1, 1)]),  # Dm : D F A   (A held)
        (S(-3, 1), [S(-3, 1), S(-3, 2), S(-2, 1)]),  # G  : G B D   (D held) - this G is a comma below the first
    ]


def ratio(site):
    i, j = site
    return 3.0 ** i * 5.0 ** j


def pitch_class_freq(site):
    """Frequency of the site folded into the octave above C3."""
    f = C_REF * ratio(site)
    return f / 2 ** np.floor(np.log2(f / C_REF))


def _candidates(site, lo, hi):
    f = pitch_class_freq(site)
    return [f * 2.0 ** o for o in range(-4, 4) if lo <= f * 2.0 ** o <= hi]


def voice_chords(chords):
    """Assign sites and octaves to the four voices with smooth, common-tone-preserving voice leading."""
    if DIRECTION == "down":
        prev = [C_REF / 2 * 1.0, C_REF * 1.5, C_REF * 2.5, C_REF * 4]  # loose starting registers
    else:  # close C2 E3 G3 C4: the rising pump's steady register, so no voice sags in the first round
        prev = [C_REF / 2, C_REF * 1.25, C_REF * 1.5, C_REF * 2]
    out = []
    for root, sites in chords:
        bass = min(_candidates(root, *RANGES[0]), key=lambda f: abs(np.log2(f / prev[0])))
        best = None
        for perm in itertools.permutations(sites):
            fs, cost = [], 0.0
            for v, s in zip((1, 2, 3), perm):
                f = min(_candidates(s, *RANGES[v]), key=lambda f: abs(np.log2(f / prev[v])))
                fs.append(f)
                cost += abs(np.log2(f / prev[v]))
            if not (bass < fs[0] < fs[1] < fs[2]):
                cost += 10
            if best is None or cost < best[0]:
                best = (cost, perm, fs)
        _, perm, fs = best
        notes = [(root, bass)] + list(zip(perm, fs))
        out.append(notes)
        prev = [f for _, f in notes]
    return out


def build():
    chords = []
    home = (0, 0)
    for c in range(CYCLES):
        chords += comma_pump(home)
        home = (home[0] + PUMP_STEP[0], home[1] + PUMP_STEP[1])
    chords.append((home, [home, (home[0], home[1] + 1), (home[0] + 1, home[1])]))  # the final C, drifted
    voiced = voice_chords(chords)

    times = [FIRST_CHANGE + k * CHORD_DUR for k in range(len(voiced))]
    times[0] = 0.0
    final_start = times[-1]
    final_end = final_start + 6.2
    ghost = (final_start + 2.4, final_start + 4.8)

    # per voice: list of notes {t0, t1, site, freq}; consecutive identical notes merge (held tones)
    voices = [[] for _ in range(4)]
    for k, notes in enumerate(voiced):
        t0 = times[k]
        t1 = times[k + 1] if k + 1 < len(voiced) else final_end
        for v, (site, f) in enumerate(notes):
            start = t0 if k else dict((vv, tt) for tt, vv in INTRO)[v]
            last = voices[v][-1] if voices[v] else None
            if last and last["site"] == list(site) and abs(last["freq"] - f) < 1e-6:
                last["t1"] = t1
            else:
                voices[v].append(dict(t0=start, t1=t1, site=list(site), freq=f))
    # the ghost: the opening chord sounds once more, a whole walk away, a little quieter
    ghost_notes = [dict(t0=ghost[0] + 0.07 * v, t1=ghost[1], site=list(site), freq=f, voice=v)
                   for v, (site, f) in enumerate(voiced[0])]
    c = 1200 * np.log2(ratio(home))
    cents = c - 1200 * round(c / 1200)  # pitch-class drift of "home": CYCLES syntonic commas flat (down) or sharp (up)
    # coda: when the painting is revealed the drifted chord is struck once more, rolled upward
    reveal = final_end + 1.0
    coda = [dict(t0=reveal + 0.22 * v, t1=reveal + 5.0, site=list(site), freq=f, voice=v)
            for v, (site, f) in enumerate(voiced[-1])]
    return dict(voices=voices, ghost=ghost_notes, coda=coda, reveal=reveal, final_start=final_start, final_end=final_end,
                ghost_span=ghost, drift_cents=float(cents), direction=DIRECTION, progression=PROGRESSION, home_final=list(home), cycles=CYCLES,
                chord_times=times, duration=final_end + 9.0)


def envelope(notes, t, gain=1.0):
    """Amplitude of one voice at times t (array). Shared by the audio and the picture."""
    t = np.asarray(t, float)
    a = np.zeros_like(t)
    for k, nt in enumerate(notes):
        prev_same = k > 0 and abs(notes[k - 1]["t1"] - nt["t0"]) < 1e-6
        att = np.clip((t - nt["t0"]) / ATTACK, 0, 1) if not prev_same else (t >= nt["t0"]).astype(float)
        rel = np.clip(1 - (t - nt["t1"]) / RELEASE, 0, 1)
        a = np.maximum(a, np.where(t < nt["t1"], att, rel) * (t >= nt["t0"]))
    return a * gain


def note_at(notes, t):
    """The note a voice is on (or last released) at time t, or None before it enters."""
    cur = None
    for nt in notes:
        if nt["t0"] <= t:
            cur = nt
    return cur


def site_world(site):
    i, j = site
    return tess.PIVOT + i * tess.LAT_A + j * tess.LAT_B


FIFTHS = ["Fb", "Cb", "Gb", "Db", "Ab", "Eb", "Bb", "F", "C", "G", "D", "A", "E", "B",
          "F#", "C#", "G#", "D#", "A#", "E#", "B#"]


def note_name(site):
    """Spelling on the line of fifths plus a syntonic-comma count (Helmholtz-Ellis style): each major-third
    step (5/4) sits a comma below the Pythagorean third (81/64), so E reached as C+third is 'E-1'."""
    i, j = site
    pos = i + 4 * j
    name = FIFTHS[pos + 8] if 0 <= pos + 8 < len(FIFTHS) else f"q{pos}"
    commas = -j
    return name if commas == 0 else f"{name}{commas:+d}"


if __name__ == "__main__":
    s = build()
    for v, notes in enumerate(s["voices"]):
        print(NAMES[v], len(notes), "notes, first", round(notes[0]["freq"], 1), "Hz, last", round(notes[-1]["freq"], 1), "Hz")
    print("drift", round(s["drift_cents"], 1), "cents; final home", s["home_final"], "duration", s["duration"])
    print("soprano:", " ".join(note_name(n["site"]) for n in s["voices"][3]))
    print("bass:   ", " ".join(note_name(n["site"]) for n in s["voices"][0]))
