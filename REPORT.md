# Report: Flock and Painter's Order, cloud vs GitHub Actions

*2026-10-05. Source: `canon/tessellation_15.svg` (and the matching screen capture).*

## What was made
- **Flock** (42 s, 1080p, 12 fps stop-motion). Paper "swifts" cut from the tile flutter in on twos and land in their
  slots. The finished frame is a wall-eyed Magic Eye hiding a **front-on gull with spread wings** (the fix for last
  time's closed-wing bird). From 27 s the hidden gull beats its wings. The score is an original Tchaikovsky-style
  miniature in B minor: tremolo strings, an oboe theme, harp, a timpani roll into a B-major arrival as the last swift
  lands, celesta for the viewing hold, and the theme returning in the major on strings while the gull flies. Each
  landing is a pizzicato, taken from the animation's own schedule. Interactive viewer:
  `dist/cloud/flock/flock_viewer.html` (repeat slider, wall-eyed or cross-eyed, depth peek).
- **Painter's Order** (58 s, 1080p, 24 fps), my own piece. The lattice becomes a just-intonation Tonnetz: one step
  along one axis is a fifth, one step along the other is a major third. Four voices, one per tile rotation and colour,
  each **sound by tracing the tile outline as an oscilloscope beam**, so the audio waveform is the drawing. The chorale
  plays the comma pump C–Am–Dm–G six times, holding every common tone. Home sinks one syntonic comma per round, six in
  all (−129 cents), and the music visibly walks 24 fifths across the tiles. At the end the opening chord sounds as a
  ghost a whole walk away. Then the tiling is filled in, with tiles stacked in the order the music first reached
  them, so the music decides how the overlapping tiles resolve.

## Findings about the SVG that shaped both pieces
1. **One prototile in four rotations (p4).** Its square lattice is tilted 22°, so the stereogram needed the tiling
   rotated to horizontal. The repeat is then exactly one cell.
2. **The outline crosses itself, so tiles overlap.** Which tile shows is decided by draw order. The SVG draws
   outward from the centre, which is why the screen capture has four differently coloured regions. A
   translation-invariant draw order makes the pattern truly periodic, which the stereogram requires. Painter's Order
   turns this into its subject.
3. **The outline is a clarinet.** It has 180° point symmetry, so traced as a waveform it contains only odd harmonics,
   with nothing above the 11th.

## What ran where
| | Cloud container (Track 1) | GitHub Actions (Track 2) |
|---|---|---|
| Machine | 4 vCPU, 15 GB RAM, Linux 6.18 | `ubuntu-latest` runners: 2 vCPU, 7 GB RAM, Azure |
| Python | 3.11.15 (uv venv) | 3.12 (`actions/setup-python`, pip cache) |
| Libraries | numpy 2.4, scipy 1.17, Pillow 12, cairocffi + Cairo 1.18 | same pins from `requirements.txt` |
| ffmpeg | 6.1.1 (preinstalled) | not on the image; `apt-get install ffmpeg libcairo2 fonts-dejavu-core` |
| Browser | headless Chromium (viewer check) | none needed |
| Parallelism | 4 processes on one box | Flock: 4 frame runners + score runner; Painter's Order: 8 frame runners |
| **Flock wall time** | **2 min 51 s** | **3 min 47 s** (run 37264630478) |
| **Painter's Order wall time** | **6 min 24 s** | **4 min 34 s** (run 37264630463) |
| Overhead per job | none | ~30–37 s setup (apt + pip) + ~5 s checkout, on every one of 17 jobs |
| Outputs | `dist/cloud/<piece>/` on the working branch | `gh/<piece>/` on the `renders` branch (also kept as run artifacts) |
| Reproducibility | stereogram, depth map and both soundtracks are **byte-identical** across the two tracks (SHA-256 in each `checksums.txt`) | |

Approximate Actions cost per full run of both pieces: 17 jobs, about 30–40 runner-minutes. The usage API reported
0 billable ms, which is what it shows when a run is covered by included minutes.

### What happened on each front
- **Cloud.** Wrote the geometry reader, pattern engine, depth map, stereogram and decoder, the swift sprites, the
  NumPy orchestra, the Tonnetz score and the beam renderer. Reviewed contact sheets at each stage. Fixes found there:
  the stereogram's seed strip had to sit on the background, the gull's body had to be wider than one repeat to read,
  and the twisted tile's empty middle had to be filled to give the swifts a belly and an eye.
- **GitHub.** A probe workflow first showed what the runner image has (Python 3.12, Node 22; no ffmpeg, no Cairo). The
  first real runs rendered everything and published, then failed in cleanup, because the publish step switched the
  checkout to another branch underneath the setup action. Publishing from a separate git worktree fixed it: both runs
  are green. Pushing workflow files and dispatching runs both worked through the app connection.

## What would make the next one faster
1. **A ready runner image.** About 35 s of every Actions job is installing ffmpeg and Cairo. A small container image
   (or a self-hosted runner on your Mac) with them preinstalled cuts roughly 10 runner-minutes per run. Alternatively,
   cache the apt packages.
2. **Fewer, bigger GitHub jobs for short pieces.** Flock was slower on Actions than in the cloud because four 2-core
   runners each paid the setup cost for 40–150 s of work. Use matrix sharding only when a piece renders for more than
   about 5 minutes.
3. **Balance the shards by cost, not frame count.** The Flock flap section costs about 4× per frame, so shards 2–3 ran
   150 s while shards 0–1 ran 40 s.
4. **Front-load the decisions you already made here:** screen size, viewing method, palette, hidden subject and
   musical reference. With those in a `brief.md`, a new tessellation goes straight to a render.
5. **Hand over the tessellation as data, as you did this time.** The SVG let the geometry be read exactly, with no
   segmentation. If your tessellation tool can export the lattice vectors and draw order, even better.
6. **Run it yourself.** `flock/run_all.sh` and `painters_order/run_all.sh` rebuild everything on any machine with
   Python, ffmpeg and Cairo. On GitHub: Actions, choose the workflow, then Run workflow.
7. **Listen and look in one pass.** I can't hear the audio, and I judge the visuals from contact sheets. One batched
   list of notes after a full watch is the cheapest feedback loop.
