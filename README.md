# InverseCramer

Two short films made from one source drawing, `canon/tessellation_15.svg`. Each film is rendered twice: once in a
Claude cloud container and once entirely by GitHub Actions, from the same code.

| Piece | What it is | Run locally | Run on GitHub |
|---|---|---|---|
| **Flock** | Paper swifts flutter in and land as a Magic Eye stereogram that hides a front-on gull with spread wings. Score: an original miniature in a Tchaikovsky manner (B minor, oboe, tremolo strings, harp, celesta). | `flock/run_all.sh build/flock 4` | Actions → **flock** → Run workflow |
| **Painter's Order** | A four-beam oscilloscope chorale. Each voice traces the tile outline as its waveform; the lattice is read as a just-intonation Tonnetz; a comma pump walks the music across the tiles and then fills them in. | `painters_order/run_all.sh build/painters_order 4` | Actions → **painters-order** → Run workflow |

GitHub results are committed to the `renders` branch under `gh/<piece>/`; cloud results are in `dist/cloud/<piece>/`.

## What the SVG turned out to be
- One prototile (16 cubic Béziers) placed 964 times, in four 90° rotations, one colour each, sharing a pivot (wallpaper group p4).
- A square lattice of 83.07 px, tilted 22°.
- The outline **crosses itself**, so neighbouring tiles overlap and the *draw order* decides what is visible. The SVG is
  drawn outward from the centre, which is why the screen capture shows four different-looking regions. Painting in a
  translation-invariant order (colour class, then position along a fixed direction) gives a truly periodic pattern.
- Traced as a waveform, the outline has 180° point symmetry, so it contains **only odd harmonics** (clarinet-like),
  and nothing above the 11th.

## Layout
```
canon/            the source SVG
refs/             the brief documents and the screen capture
common/tess.py    geometry read from the SVG (lattice, classes, Bézier trace)
common/synth.py   NumPy orchestra and hall reverb (no samples)
flock/            pattern cell, gull depth, stereogram + QA decoder, fly-in, score, viewer
painters_order/   Tonnetz comma pump, scope audio, glowing-beam film
.github/          setup + publish composite actions, one workflow per piece
```

## Requirements
Python 3.11+ with `pip install -r requirements.txt`, plus ffmpeg, the Cairo library and DejaVu fonts
(`apt-get install ffmpeg libcairo2 fonts-dejavu-core`; on macOS `brew install ffmpeg cairo`).

## QA
`flock.still` decodes its own stereogram (per-row block matching) and compares the recovered depth with the gull.
It exits non-zero below an edge-tolerant F-score of 0.90, which fails the GitHub job before any frames render.
