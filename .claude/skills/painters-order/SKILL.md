---
name: painters-order
description: Turn a tessellation (an SVG of one prototile repeated with matrix transforms) into "Painter's Order", a four-beam oscilloscope chorale. Each voice sounds by tracing the tile outline as its waveform, the tiling's lattice becomes a just-intonation Tonnetz (fifths one way, major thirds the other), and a comma pump walks the music across the tiles before the tiling is painted in the order the music visited it. Produces a 1080p MP4 with soundtrack, a contact sheet, and a playable browser "tile organ". Use this whenever someone wants to make music or sound from a tessellation, sonify or animate a tiling, build an oscilloscope/vector-scope piece from a drawing, explore just intonation or comma drift on a lattice, or asks for "another Painter's Order", even if they don't use that name.
---

# Painter's Order

A tessellation already contains an instrument and a score:

- **The tile outline is a waveform.** Trace the closed Bézier outline once per period with X on the left channel
  and Y on the right, and an oscilloscope in XY mode draws the tile. The tile's symmetry sets its timbre. A
  point-symmetric tile has only odd harmonics, which sounds clarinet-like.
- **The lattice is a Tonnetz.** One lattice vector is a perfect fifth (×3/2) and the other a major third (×5/4), so
  every lattice site is a pitch in 5-limit just intonation and a triad is a small triangle of sites.
- **The orientation classes are voices.** Each colour/rotation of the tile is one of four voices (bass, tenor, alto,
  soprano). A voice sounds by tracing its own rotated tile at the site of its note.
- **The comma pump is the choreography.** Play C, Am, Dm, G in strict just intonation, holding every common tone, and
  each round comes home a syntonic comma (81/80, about 21.5 cents) flatter. On the lattice that is a shift of
  (−4, +1), so the chorale walks across the tiling and leaves a phosphor trail.
- **Draw order is the reveal.** Overlapping tiles are painted in the order the music first reached them, so the music
  decides how the tiling resolves visually.

Everything is computed from the SVG: no samples and no generated imagery. Picture and sound share one clock, because
the frame brightness is the same envelope function the audio uses.

## Workflow

### 1. Check the input
The engine expects one prototile drawn as an absolute `M … C … Z` path, copied many times as
`<path d="…" transform="matrix(a b c d e f)" fill="…">` (the format tessellation tools such as meefs' tessellation
lab export). Run the analysis first; it is instant and tells you whether the file will work:

```bash
PO_SVG=tiles.svg PYTHONPATH=<skill>/scripts python -m po_kit.tess
```

It reports the orientation classes (colour, angle, pivot offset), the lattice (lengths, angle, tilt) and the tile's
harmonic spectrum. Share the interesting parts with the user. The spectrum is a good hook ("your tile has only odd
harmonics, so it will sound like a clarinet").

If the SVG is in another shape (groups with `<use>`, relative path commands, translate/rotate transforms), convert it
to the expected form with a short script first, rather than modifying the engine. Keep only copies of the main
prototile. The parser ignores paths whose `d` differs from the first one.

### 2. Preview (about a minute)
```bash
PO_PREVIEW=1 <skill>/scripts/run.sh tiles.svg build/po 4
```
This writes `analysis.txt`, `score.wav`, `score.json`, `sheet.png` (six frames: title, walk, the ghost chord, the
reveal) and `web/index.html` (the tile organ). Look at `sheet.png` once. Check that the beams are readable at the
follow-camera scale, that the walk stays in frame, and that the end-card text is legible over the reveal. You cannot
hear the audio, so describe it from the analysis rather than claiming how it sounds.

### 3. Render the film
```bash
PO_TITLE="…" PO_SUBTITLE="…" <skill>/scripts/run.sh tiles.svg build/po $(nproc)
```
Frames render in parallel shards, one process per shard, each piping to ffmpeg. The defaults (6 cycles, 1.6 s chords)
give a 58 s film, which takes about 6 minutes on 4 cores. Output: `build/po/film.mp4` plus `timings.txt`.

Knobs (environment variables):

| Variable | Default | Effect |
|---|---|---|
| `PO_CYCLES` | 6 | rounds of the pump; each adds ~6.4 s and sinks home one more comma |
| `PO_CHORD_DUR` | 1.6 | seconds per chord |
| `PO_CREF` | 130.81 | Hz of the opening C |
| `PO_TITLE`, `PO_SUBTITLE` | Painter's Order / a comma-pump chorale for four beams | title card and organ page title |

### 4. Hand over
- `film.mp4`: the piece. Mention its length, the drift in cents (from `score.json` `drift_cents`) and how many fifths
  the walk covers.
- `web/` (`index.html` + `organ_data.js`): a self-contained page. Click lattice dots to play their pitches (each voice
  is the tile as two WebAudio periodic waves); Space plays the comma pump. It can go straight onto GitHub Pages.
- For a README, GitHub deletes `<video>` tags, so embed an animated WebP of the film:
  `ffmpeg -i film.mp4 -vf fps=12,scale=960:-2 -c:v libwebp_anim -quality 72 -loop 0 -an film.webp`.

To render on GitHub Actions instead of locally, copy `assets/github-workflow.yml` into `.github/workflows/`. It shards
frames across runners and installs the system packages the runner image lacks.

## Requirements
Python 3.10+ with `numpy scipy cairocffi`, the Cairo C library, ffmpeg with libx264, and DejaVu fonts.
`apt-get install ffmpeg libcairo2 fonts-dejavu-core` / `brew install ffmpeg cairo`.

## When things look wrong
- **"no copies found" / "convert it to absolute M/C/Z"**: the SVG isn't in the expected form; normalise it (step 1).
- **Tiles look tiny or huge**: the follow camera shows about 145 px per lattice cell. For tiles much larger or
  smaller than a cell, change `FOLLOW_SCALE` in `po_kit/film.py`.
- **Fewer than four orientation classes**: voices reuse classes cyclically (`VOICE_CLASS`), so two voices share a
  colour. That's expected; say so.
- **Reflections (glide or mirror classes)** are fine: a mirrored class just traces the mirrored outline.

## Going further
`references/theory.md` explains the tuning maths and why the walk goes where it does (read it when the user asks
"why" or wants to explain the piece). `references/variations.md` has other progressions, commas and lattice mappings
to try when the user wants a different piece from the same tiling.
