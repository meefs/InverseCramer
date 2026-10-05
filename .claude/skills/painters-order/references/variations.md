# Variations: other pieces from the same tiling

All of these change `po_kit/music.py`, mainly `comma_pump()` and `build()`. The film, audio and organ follow the
score automatically, because they only read `score.json`.

| Idea | Change | What you see and hear |
|---|---|---|
| **Sharp pump** | reverse the progression: C → G → Dm → Am → C | home rises a comma per round; the walk heads the other way, (+4, −1) |
| **Diesis pump** (128/125, 41 cents) | cycle through three major thirds, C → E → G# → B#≈C, holding tones | the walk runs up the third axis (j); a big, fast drift |
| **Static JI chorale** | a progression whose path closes (I–IV–V–I with no held-tone constraint) | no drift; the painting stays in one neighbourhood and becomes a dense pinwheel |
| **Septimal** | add a third lattice direction for 7/4 (needs a 3-D lattice or an extra class mapping) | harmonic-seventh chords, bluesy colour; good for tilings with 6 classes |
| **Slow drone** | `PO_CHORD_DUR=4`, `PO_CYCLES=3` | meditative; afterglow trails overlap more |
| **Swap the axes** | map a to the major third and b to the fifth (swap LAT_A/LAT_B in `site_world`) | the same music walks a different path across the tiles |

Rules of thumb:
- Keep chords at 1.2 s or longer. Shorter, and the afterglow and comet heads can't be read.
- Each extra cycle adds about 6.4 s and 21.5 cents of drift. Past about 8 cycles the walk leaves the overview frame
  of a typical SVG; the camera copes, but the reveal shows more empty lattice.
- If a tiling has more than four orientation classes, only four are voiced. For six-fold tilings, consider six
  voices (extend `RANGES`, `GAINS` and `INTRO`).
