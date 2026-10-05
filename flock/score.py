"""Score for *Flock*: an original miniature in a Tchaikovsky manner (B minor, 80 bpm, 4/4, 42 s).

  bars 1-2   intro: tremolo strings, rising harp, flute flutter-tongue (wings)       0-6 s
  bars 3-5   oboe theme over Bm-G | Em-F#7 | G-C#o7-F#7, swifts landing as pizzicati  6-15 s
  bar  6     the last swift lands: timpani roll -> B major (Picardy), harp glissando 15 s
  bars 7-9   celesta, sugar-plum light, pizzicato bass (the hold: let the eyes relax) 18-27 s
  bars 10-12 the hidden gull beats its wings: the theme returns in the major on strings,
             a harp glissando on every wingbeat, a tearful minor iv (Em) before home  27-36 s
  bars 13-14 cadence on B, celesta sparkles, fade                                     36-42 s

The landing cues come from the animation's own schedule (cues.json): one clock.
    python -m flock.score <builddir>   -> <builddir>/score.wav
"""
import json
import sys
from pathlib import Path

import numpy as np

from common import synth as S
from common.synth import n
from flock import timeline as TL

B = TL.BEAT  # seconds per beat

CHORDS = [  # start beat, end beat, bass, upper voicing
    (0, 4, "B1", ["F#3", "B3", "D4", "F#4"]),
    (4, 8, "G1", ["F#3", "B3", "D4", "G4"]),
    (8, 10, "B1", ["F#3", "B3", "D4", "F#4"]),
    (10, 12, "G1", ["G3", "B3", "D4", "G4"]),
    (12, 14, "E2", ["G3", "B3", "E4", "G4"]),
    (14, 16, "F#1", ["F#3", "A#3", "C#4", "E4"]),
    (16, 18, "G1", ["G3", "B3", "D4", "G4"]),
    (18, 19, "C#2", ["G3", "B3", "C#4", "E4"]),
    (19, 20, "F#1", ["F#3", "A#3", "C#4", "E4"]),
    (20, 28, "B1", ["F#3", "B3", "D#4", "F#4"]),
    (28, 32, "G#1", ["G#3", "B3", "D#4", "G#4"]),
    (32, 34, "E2", ["G#3", "B3", "E4", "G#4"]),
    (34, 36, "F#1", ["F#3", "A#3", "C#4", "E4"]),
    (36, 38, "B1", ["F#3", "B3", "D#4", "F#4"]),
    (38, 40, "G#1", ["G#3", "B3", "D#4", "G#4"]),
    (40, 42, "E2", ["G#3", "B3", "E4", "G#4"]),
    (42, 44, "F#1", ["F#3", "A#3", "C#4", "F#4"]),
    (44, 46, "E2", ["G#3", "B3", "E4", "G#4"]),
    (46, 48, "E2", ["G3", "B3", "E4", "G4"]),
    (48, 56, "B1", ["F#3", "B3", "D#4", "F#4"]),
]

OBOE = [  # beat, beats, note
    (8, 1, "B4"), (9, .5, "D5"), (9.5, .5, "F#5"), (10, 1.5, "G5"), (11.5, .5, "F#5"),
    (12, 1, "E5"), (13, .5, "G5"), (13.5, .5, "B5"), (14, 1.5, "A#5"), (15.5, .5, "C#6"),
    (16, 1.5, "B5"), (17.5, .5, "A5"), (18, .5, "G5"), (18.5, .5, "E5"), (19, .5, "C#5"), (19.5, .5, "A#4"),
    (20, 2, "B4"), (22, 1, "D#5"), (23, 1.5, "F#5"),
]

VIOLINS = [  # the theme, transfigured into B major while the gull flies
    (36, 1, "B4"), (37, .5, "D#5"), (37.5, .5, "F#5"), (38, 1.5, "G#5"), (39.5, .5, "F#5"),
    (40, 1, "E5"), (41, .5, "G#5"), (41.5, .5, "B5"), (42, 1.5, "A#5"), (43.5, .5, "C#6"),
    (44, 1.5, "B5"), (45.5, .5, "G#5"), (46, 1, "G5"), (47, .5, "F#5"), (47.5, .5, "D#5"),
    (48, 2, "F#5"), (50, 2, "D#5"), (52, 4, "B4"),
]

CELESTA = [
    (24, "D#6"), (25, "B5"), (26, "F#5"), (27, "B5"), (27.5, "C#6"),
    (28, "D#6"), (29, "B5"), (30, "G#5"), (31, "B5"), (31.5, "D#6"),
    (32, "E6"), (32.5, "D#6"), (33, "C#6"), (33.5, "B5"), (34, "A#5"), (34.5, "C#6"), (35, "F#6"), (35.5, "E6"),
    (48, "B5"), (48.25, "D#6"), (48.5, "F#6"), (48.75, "B6"),
    (52, "B5"), (52.25, "D#6"), (52.5, "F#6"), (52.75, "B6"), (53.5, "F#6"), (54, "D#7"),
]


def chord_at(beat):
    for c in CHORDS:
        if c[0] <= beat < c[1]:
            return c
    return CHORDS[-1]


def chord_tones(beat, lo, hi):
    pcs = {n(x) % 12 for x in chord_at(beat)[3]} | {n(chord_at(beat)[2]) % 12}
    return [m for m in range(lo, hi + 1) if m % 12 in pcs]


def compose(cues):
    mix = S.Mix(TL.DURATION)
    sec = lambda beat: beat * B

    # strings: tremolo crescendo -> warm arrival -> hush -> singing pad
    for b0, b1, bass, voicing in CHORDS:
        dur = (b1 - b0) * B + 0.3
        if b0 < 20:
            vel, trem = 0.22 + 0.4 * (b0 / 20) ** 1.3, True
        elif b0 < 28:
            vel, trem = 0.7, False
        elif b0 < 36:
            vel, trem = 0.14, False
        else:
            vel, trem = 0.32 if b0 < 48 else 0.26, False
        for i, v in enumerate(voicing):
            mix.add(sec(b0), S.strings(n(v), dur, vel, tremolo=trem, seed=i), pan=-0.5 + i / 3)
        mix.add(sec(b0), S.strings(n(bass) + 12, dur, vel * 0.9, seed=9, bright=0.6), pan=0.35)  # cellos
        mix.add(sec(b0), S.strings(n(bass), dur, vel * 0.8, seed=11, bright=0.4), pan=0.45)      # basses

    # harp: rising sixteenths under the intro and theme
    for k in range(0, 80):
        beat = k * 0.25
        tones = chord_tones(beat, n("B2"), n("B5"))
        idx = k % 16
        seq = tones[: 9]
        note = seq[idx if idx < 9 else 16 - idx] if seq else None
        if note:
            mix.add(sec(beat), S.pluck(note, 2.5, 0.28 + 0.1 * (idx == 0)), pan=-0.35)

    # flute flutter-tongue: the first wings
    for beat, a, bnote in ((1, "F#5", "G5"), (5, "D5", "E5")):
        for j in range(16):
            mix.add(sec(beat + j * 0.125), S.flute(n(a if j % 2 == 0 else bnote), 0.16, 0.35, flutter=True, seed=j), pan=0.4)
    for j in range(10):  # a soft bed of wing noise while the flock is in the air
        mix.add(sec(2 + j * 1.8), S.noise_flutter(2.2, 0.25 * np.sin(np.pi * (j + 0.5) / 10), seed=j), pan=np.sin(j) * 0.7)

    # oboe theme
    for beat, beats, note in OBOE:
        mix.add(sec(beat), S.oboe(n(note), beats * B + 0.08, 0.62, seed=int(beat * 10)), pan=0.1)

    # every landing is a pizzicato on a chord tone (colour class chooses the register)
    for t, counts in cues["landings"]:
        beat = t / B
        tones = chord_tones(beat, n("F#4"), n("F#6"))
        for c, cnt in enumerate(counts):
            if cnt:
                note = tones[(c * 3 + int(beat * 4)) % len(tones)]
                mix.add(t, S.pluck(note, 1.2, min(0.35, 0.1 + 0.06 * cnt), bright=1.3, decay=2.4, pos=0.3),
                        pan=(-0.6, -0.2, 0.2, 0.6)[c])

    # arrival: timpani roll into the downbeat as the last swift lands, harp glissando
    mix.add(sec(17.5), S.timpani_roll(n("F#2"), 2.5 * B, 0.08, 0.55), pan=0.2)
    mix.add(sec(20), S.timpani(n("B2"), 3.0, 0.9), pan=0.2)
    gl = chord_tones(20, n("B2"), n("B6"))
    for j, note in enumerate(gl):
        mix.add(sec(20) - 0.5 + j * (0.5 / len(gl)), S.pluck(note, 2.5, 0.3), pan=-0.4 + 0.8 * j / len(gl))

    # celesta and pizzicato bass for the hold
    for beat, note in CELESTA:
        mix.add(sec(beat), S.celesta(n(note), 2.0, 0.55), pan=-0.15)
    for beat, note in ((24, "B2"), (26, "F#2"), (28, "G#2"), (30, "D#2"), (32, "E2"), (34, "F#2")):
        mix.add(sec(beat), S.pluck(n(note), 1.5, 0.45, bright=0.6, decay=2.0), pan=0.3)

    # the gull: a harp sweep on every wingbeat, the theme on violins (with an octave below)
    f0, f1, per = cues["flap"]
    k = 0
    while f0 + k * per < f1 - 0.1:
        t = f0 + k * per
        env = np.sin(np.pi * (k + 0.5) / round((f1 - f0) / per)) ** 0.6
        tones = chord_tones(t / B, n("B3"), n("B6"))
        for j, note in enumerate(tones):
            mix.add(t + j * (0.55 / len(tones)), S.pluck(note, 1.8, 0.12 + 0.2 * env), pan=-0.5 + j / len(tones))
        k += 1
    for beat, beats, note in VIOLINS:
        d = beats * B + 0.12
        mix.add(sec(beat), S.strings(n(note), d, 0.55, seed=3, bright=1.2), pan=-0.2)
        mix.add(sec(beat), S.strings(n(note) - 12, d, 0.35, seed=5), pan=0.05)
    mix.add(sec(48), S.timpani(n("B2"), 3.0, 0.35), pan=0.2)
    return mix


def main(build):
    build = Path(build)
    cues = json.loads((build / "cues.json").read_text())
    mix = compose(cues)
    y = S.finish(mix.buf, wet=0.3, rt60=2.4, length=TL.DURATION, fade_out=3.0)
    S.write_wav(build / "score.wav", y)
    print("score.wav", y.shape[0] / S.SR, "s")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "build/flock")
