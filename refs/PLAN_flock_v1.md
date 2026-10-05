# Maiden Voyage: *Flock* (a Magic Eye made of birds)
*Plan v1, 2026-10-04. Project: `/Volumes/ExtremeSSD/flock-magic-eye` (linked at `~/FutureSystemResearch/flock-magic-eye`).*

**The piece.** Two-tone tessellated birds (in the spirit of Ken's reference: rows alternating direction, separate wing
pieces, white eye dots, peach / plum / coral / burgundy) fly in one by one, flapping, and settle into their slots. When
the last bird lands, the finished pattern *is* a classic wall-eyed Magic Eye, designed for a screen rather than print.
Relax your eyes and a giant bird made of the flock floats out of the screen. Stretch goal: the hidden bird beats its wings.

Deliverables: a 30–45 s MP4 (fly-in, then a long hold for viewing), a 4K still, and an interactive HTML page
(period calibration, wall-eye/cross-eye toggle, "peek" button that shows the depth map).

---

## 1. First principles: what must be true

1. **Physics of an autostereogram.** Each pixel copies the pixel one *separation* to its left. The separation shrinks as the
   hidden surface comes closer: `s(z) = round(E·(1 − μz)/(2 − μz))`, where E is the eye separation in pixels, μ ≈ 1/3 is
   the depth range, and z ∈ [0,1] with 1 = near (Thimbleby–Inglis–Witten 1994; it also handles hidden surfaces).
   The far-plane separation is the **pattern period P**.
2. **The tile must repeat horizontally at exactly P.** The tessellation's lattice needs a horizontal translation equal to
   P. In the reference style that's two birds (one of each colour), so one "pair" of birds is P wide.
3. **P is set by the screen, not by taste.** It must be comfortably below the viewer's eye separation (about 63 mm). On a
   24-inch 1080p monitor (≈0.277 mm/px), comfortable is 35–50 mm, i.e. **P ≈ 130–180 px** at 1080p and 260–360 px at 4K.
   So each bird is about 65–90 px wide at 1080p. A calibration page settles it for Ken's actual monitor.
4. **Flat colour fuses badly.** Eyes lock onto texture, and large uniform peach or plum areas give them nothing. So the
   birds need **micro-texture**: a fine paper grain or halftone inside every colour (Paper Shaders' `paper-texture` or
   `halftone-dots`), plus crisp edges. This is the one place the flat-design reference must bend.
5. **The flock must be able to land in a warped pattern.** The finished stereogram is a *warped* tessellation: birds over
   the hidden shape get squeezed. So the generator also renders a **bird-ID buffer** through the same warp. Every bird
   instance becomes a sprite with its exact final shape and position. During flight a bird is canonical (unwarped, wings
   flapping); on landing it snaps into its warped slot over 2 frames, which reads as a stop-motion settle.
6. **Correctness can be checked without anyone's eyes.** A decoder (per-row disparity search on the finished image)
   recovers the depth map. If the recovered shape matches the intended one (IoU above a threshold), the stereogram works.
   This is the QA gate, and it costs no tokens.

## 2. Compute-optimal pipeline (all procedural; no Blender or AI image generation needed for v1)

| Step | What | Cost |
|---|---|---|
| 1. Calibration page | HTML with 5 small test stereograms at P = 120/140/160/180/200 px; Ken picks the most comfortable | small script, once |
| 2. Tile generator | Python: lattice (P × H, glide-reflected rows), bird outline as constrained edge curves (what leaves one edge enters the matching edge), wing quads, eye dot; palette from Ken. Renders the pattern strip at 4× supersampling + an ID buffer (bird #, part: body/wing/eye) | one script; reusable for any tile family |
| 3. Depth map | Hidden object = a giant version of the same bird, inflated with a distance transform (rounded dome, like the clay height maps), plus a gentle background plane. Or Ken's own painted or rendered depth map | seconds |
| 4. Stereogram generator | NumPy Thimbleby algorithm with hidden-surface links, applied to colour + ID buffer together; micro-texture added in the pattern domain so it warps consistently | ~2–5 s per frame at 4K |
| 5. QA decoder | Recover depth, compare with ground truth, write a score + side-by-side PNG | seconds |
| 6. Fly-in animation | Sprites from the ID buffer; flight paths as gentle boids-style curves from off-screen in loose flocks; wings rotate about the shoulder on twos (12 fps); landing order sweeps outward from the centre; final frame is pixel-identical to the QA-passed stereogram | compositing only (fast) |
| 7. Hold + optional animated reveal | 20–30 s static hold (fusing takes time), guide dots P apart at the top. Stretch: hidden bird flaps; pattern anchored so only the warp changes (minimal shimmer) | 120 frames × a few s |
| 8. Sound | Wing flutters synced to the flaps, a soft synthesized pad that resolves as the last bird lands, near-silence during the hold (Ken prefers synth) | NumPy synth, existing pattern |
| 9. Assemble | ffmpeg for the MP4; the canvas runtime for the interactive HTML (the period slider rebuilds the stereogram live) | existing |

**Why this is compute-optimal:** nothing is generated by a model, nothing is rendered in 3D for v1, the expensive check
(can it be seen?) is a numeric decoder instead of me looking at images, and every stage is a re-runnable script. I only
review a final contact sheet.

## 3. Ken's pre-load (offline, no AI)
1. **Reference:** save the bird image you shared into `refs/` (I can't save chat images to disk). Add any others.
2. **Palette:** confirm or adjust: peach `#F0A87C`, plum `#6E424B`, coral `#E06A45`, burgundy `#4E002E`, eye `#FFF6EA`.
3. **Hidden object:** "the giant bird" (default), a word, or your own depth map in `depth/` (white = near; any paint app;
   soft edges; or a Blender depth render).
4. **Screen:** your monitor size and resolution, plus typical viewing distance. Then open the calibration page and pick P.
5. **Viewing mode:** wall-eyed (traditional Magic Eye) by default; say if you want cross-eyed.
6. **Optional, your own bird:** I'll provide an Inkscape SVG template of the lattice with linked edges; draw a bird inside
   it and the generator takes your outline.

## 4. Milestones (checkpoints where you look)
- **M1, the still (one session):** calibration page → tile generator → depth → stereogram → decoder passes →
  **you test it with your eyes** on your monitor.
- **M2, the flight:** fly-in animation + sound + MP4.
- **M3, the reveal:** animated hidden bird, HTML page with period slider and peek; becomes a `magic-eye` skill
  (any tessellation + any depth map → stereogram, animated or still, with QA).

## 5. Later voyages this unlocks
Depth from Blender scenes (clay puppets hidden in tessellations), from photos (Depth Pro / Depth Anything), from COLMAP +
Brush splats; random-dot animated stereograms of moving footage; stereograms textured onto walls inside 3D sets; hidden
messages in tile colour sequences (steganography proper).
