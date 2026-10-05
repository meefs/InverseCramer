# Creative pathways: what you can pre-load, what I build, what to add

*2026-10-04, written for Meefs after Inverse Cramer II.*

## 0. Why Cramer II went fast, and how to repeat it

Cramer II was quick for two reasons:
- **A kit already existed.** Your card was cut into 62 clean layers with a manifest of where each one sits. Turning them into clay was a script.
- **The film was driven by one clock.** A single function of time, `animate(t)`, posed everything, and the voice track set the times. Once that worked, the rest was rendering, which costs no tokens.

Where my tokens actually go: deciding things, finding and cutting source material, writing new code, and looking at review images. Rendering costs nothing, and you can run a render yourself from the command line.

So the general recipe for every idea below is the same:

| You do, offline, no AI | I do |
|---|---|
| Make decisions: a brief, a palette, a mood board, the beats | Write the grammar: scripts that turn your kit into motion |
| Build the **kit**: the physical or digital source pieces, in a normalized format | Rig, time and light it, and review the frames |
| Capture: photos, scans, recordings, crease patterns, voxel models | Build new tools when the kit hits a wall |
| Run the renders and exports from the scripts I leave behind | Fix what the renders reveal |

**Project folder template** (copy it for each new idea):
```
<project>/
  brief.md      one screen: feeling, length, aspect ratio, must-haves, avoids
  refs/         images and clips you like (named for what you like about them)
  canon/        YOUR source pieces: layers, scans, crease patterns, .vox, stems, .scl
  kit.json      what each piece is and where it lives (I can write this from a folder listing)
  audio/        voice script, stems, MIDI
  scripts/      mine. Re-runnable without me.
  renders/  dist/  review/
```

**Habits that save the most tokens:**
1. **Decide before we start.** A brief.md with "must have, avoid, feeling" removes most iteration.
2. **Hand me clean pieces.** Shoot on a plain background (white, black or magenta), keep the light even, name files meaningfully. Every minute of your capture discipline saves me a segmentation pass.
3. **Batch your notes.** One list of changes after a full watch costs far less than a note per frame.
4. **Run renders yourself.** Every script I write has one command. For example: `Blender -b -P hollow.py -- <root> anim 0 516 100` followed by `./assemble.sh`.
5. **Reuse skills.** Each new domain should end with a skill (as animated-short, shape-forge and tape-warble did), so the second project in that domain is cheap.

**What you already have** (checked on this Mac):
- Blender 5.2, DaVinci Resolve (Fusion compositor and DCTL shaders inside), MagicaVoxel
- Ableton Live 12 Suite (includes Max for Live), Bitwig, REAPER, VCV Rack 2
- MuseScore 4, LilyPond, full TeX plus MetaPost
- Inkscape, potrace, ImageMagick, ffmpeg
- Python with torch, MLX, librosa, pretty_midi and mido; Node with headless Chrome
- An M1 Pro with 16 GB

Missing: SuperCollider, COLMAP, a Gaussian-splat trainer, glslViewer.

---

## 1. Claymation, entirely in the box (Meefs: digital only)

Everything here is made on the computer. "Clay" is three separable layers, and each one can be a **foundry**: a repeatable pipeline that takes a small record and produces an asset.

| Layer | What makes it read as clay | In-the-box technique |
|---|---|---|
| **Form** | Soft, slightly lumpy volumes that blend into each other | Metaballs or signed-distance (SDF) blends in Blender Geometry Nodes; inflated drawings (the Cramer II relief); Blender sculpt mode |
| **Surface** | Thumbprints, tool smears, slight translucency, a little sheen | The Cramer II clay shader (rings + noise bump, subsurface scattering), saved as a `clay.blend` library you tweak by eye |
| **Time** | Boil, stepped motion, replacement faces, gentle squash | `animate(t)` at 12 fps; per-frame thumbprint reseed; puppet jitter; mouth swaps from voice timing |

### The clay foundry (proposed `clay-forge` skill, shape-forge's sibling)
```
character record (YAML)          →  form grammar (Blender Python)   →  clay material + boil
  body: pear, 0.28 m, palette        metaball / SDF primitives            from clay.blend
  head: egg, nose: bulb, ears: cup   smooth-blended, lumped,
  mouth_set: 8 visemes               slightly asymmetric per seed
  eyes: button | pinned | painted                    │
                                                     ▼
                         face kit: replacement mouths, eyes and brows generated from a viseme grammar
                                                     │
                                                     ▼
                         rig (Rigify or simple pivots) → cast sheet + turntable QA → blind-judged rounds of 8
```
- **Form grammar:** primitives such as egg, pear, sausage, ball, ribbon and flattened coin are blended with a smoothing radius, which is literally how real clay joins. Lumpiness comes from a seeded noise displacement, so every character is reproducibly "hand-made" and you can ask for "seed 12, but rounder".
- **Replacement face kit:** mouths are *generated*. A small 2D grammar (in MetaPost, or Python drawing) produces the 8 viseme shapes. They're inflated into clay pieces and pressed onto the head. That's the Jack Skellington box, made in code.
- **Self-improving rounds:** like shape-forge's headstones. Eight candidates per round, a fixed rubric (read at a glance, appeal, silhouette, clay authenticity, expressiveness), a control candidate kept for comparison, and a stop when scores plateau.

### Your in-the-box pre-load
- **Character records:** write the YAML: proportions, palette (hex), personality notes, which expressions they need. This is pure design thinking, no AI.
- **Digital sketches:** turnarounds or expression sheets drawn in any drawing app. Even rough ones fix proportions so I don't guess.
- **Sculpt hero pieces yourself** in Blender sculpt mode with a pen tablet (Clay Strips and Blob brushes). I'll take any sculpt, rig it, and give it the shared clay surface.
- **Tune `clay.blend`:** open the material library in Blender and adjust colour, roughness and thumbprint strength by eye. Every future puppet inherits your taste.
- **Set dressing from existing pipelines:** shape-forge for props, MagicaVoxel or MagicaCSG blockouts (they voxelize or convert to smooth meshes cleanly).

### Extra in-the-box tools (optional)
| Tool | Why |
|---|---|
| **Blender sculpt** (have) | Digital clay with real brushes; the default |
| **MagicaCSG** (free, MagicaVoxel's author) | Fast SDF blob modelling that already looks like clay |
| **Nomad Sculpt** (iPad, cheap) | If you want to sculpt on the couch; exports OBJ/GLB |
| **ZBrush** (paid) | The industry sculpting tool; only if Blender sculpt feels limiting |

**First project:** run the foundry on one character (record → 8 candidates → pick → mouth kit), then make a 15 s talking-head commercial in the Cramer II lighting rig.

---

## 2. Origami and papercraft: from fold to film

The key fact is that **origami is already data**. A crease pattern (CP) is a flat drawing of mountain and valley folds, and there are good open tools that simulate folding from it.

**The normalized pathway:**
```
paper model / diagram
  └─► crease pattern  (SVG: red = mountain, blue = valley, black = cut/border;  or .fold / .cp file)
        └─► Origami Simulator (browser, free) — folds the CP from 0→100%, exports meshes at any fold %
              └─► Blender: fold states become shape keys → "folds itself" on stepped frames,
                  paper material (fibre, thickness, soft shadows), then a motion rig (flap / hop / roll)
                    └─► render → assemble with sound
```

| Tool | Role |
|---|---|
| **Origami Simulator** (Amanda Ghassaei, origamisimulator.org, open source) | Takes an SVG or `.fold` CP, simulates the fold, exports OBJ/STL at any fold percentage |
| **FOLD format** + **Rabbit Ear** (JS library) | The standard origami file format, plus a library to read, write and validate it. This is how I'd script whole families |
| **ORIPA** (free, Java) | CP editor that checks whether a pattern can fold flat; reads and writes `.cp` |
| **Tess** (Alex Bateman) / Origamizer (Tachi) | Generators for origami tessellations (twist folds, Resch patterns) |
| **Inkscape** (you have it) | Drawing CPs by hand from diagrams using the colour convention |

**Your offline pre-load (the big one):**
1. **Collect CPs.** Many models (crane, flapping bird, waterbomb, Miura-ori, kusudama units) have published CPs. Save them as `canon/cp/<model>.svg` or `.fold`.
2. **Convert diagrams to CPs.** Diagrams are step-by-step. For traditional models the trick is to unfold your folded model and trace the creases in Inkscape. It's very satisfying, and it makes you intimate with the model.
3. **Note the step states.** Simulators fold all creases at once, which works for simple and tessellated pieces. A crane needs *sequences*: fold step 1, then 2, and so on. Mark which creases belong to which step (one colour or layer per step), and I'll chain the stages.
4. **Write the motion verb** for each model: crane flaps (the flapping bird is a real mechanism and rigs beautifully), frog hops, waterbomb inflates and rolls, turtle paddles.
5. **Scan your papers.** Washi, kami and foil, flat-scanned, become the materials.
6. **For unit origami:** design one unit. Geometry Nodes instances it into the whole assembly (sonobe cube, kusudama), and the units can fly in and lock together.

**First project:** a Miura-ori sheet folds itself, then a crane folds in three stages and flaps away. That establishes the CP → simulator → Blender pipe, and the skill (say, `fold-forge`) makes every later model cheap.

---

## 3. Music (big thread, and the deepest toolkit you have)

### What you already have, and what each piece is best at
| Tool | Superpower for us |
|---|---|
| **Ableton Live 12 Suite** | **Native tuning systems.** It imports Scala `.scl` files and has MPE. **Max for Live** (included) lets custom devices, JS and Jitter visuals live inside Live |
| **Bitwig** | Best-in-class MPE and The Grid (modular inside the DAW) |
| **REAPER** | Fully scriptable (Lua/Python ReaScript, OSC). Batch rendering and stem chores without touching the mouse |
| **VCV Rack 2** | Eurorack modular, good for generative patches |
| **MuseScore 4 / LilyPond / TeX** | Engraving. LilyPond (+ Ekmelily) can engrave microtonal accidentals properly. MusicXML moves between MuseScore and code |
| **Python (pretty_midi, mido, librosa)** | I generate and analyse MIDI and audio, extract beats, onsets and chroma to drive animation |

### What to add (all free)
| Add | Why |
|---|---|
| **SuperCollider** (`brew install --cask supercollider`) | Still the reference language for synthesis and algorithmic composition. It can **render non-real-time** (a score file in, a WAV out, no live audio), which fits my offline pipeline perfectly and sounds far better than my NumPy synths for less code |
| **Surge XT** | Free, deep synth with full `.scl`/`.kbm` microtuning and MPE |
| **MTS-ESP Mini** (ODDSound) | One tuning broadcast to every compatible plugin at once. Change the scale and the whole project retunes |
| **Faust** (optional) | Write a DSP algorithm once and compile it to an AU/VST plugin *and* WebAudio, so the same instrument lives in Ableton and in our browser films |
| **Strudel** (browser, nothing to install) | TidalCycles patterns live-coded in the browser; great for sketching rhythms |
| **AbletonOSC** (open-source remote script) | Exposes Live over OSC, so scripts (me) can create clips, write notes, set tempo and fire scenes **inside your Live set**. That's the bridge between my generation and your performance |

On "SuperCollider's successor": there isn't one that replaced it. The modern neighbours are Cmajor, Faust, Glicol and Strudel. SuperCollider plus Faust covers almost everything.

### The pipeline I'd set up
```
tuning math (me)  ──► .scl/.kbm/.ascl  ──► Ableton 12 native tuning / Surge XT / MTS-ESP  ──► you play it (MPE)
composition (you or me) ──► MIDI / MusicXML  ──► Live (perform) · MuseScore/LilyPond (engrave)
SuperCollider NRT score ──► WAV stems  ──► film mixes (replaces my NumPy synth)
your Live stems + MIDI ──► librosa feature JSON (beats, onsets, chroma, loudness)  ──► drives Blender/canvas animation
```

### Your offline pre-load
- **Tuning ideas as numbers:** ratio lists, EDOs, generators (for example "13-EDO, 7-limit JI, Bohlen–Pierce"). I turn them into `.scl` files plus a reference sheet engraved in LilyPond.
- **Performances as MIDI:** record MPE takes in Live and export MIDI with the stems. A few minutes of you playing saves me hours of guessing at feel.
- **Your instruments, sampled:** one-shots across the range of your acoustic instruments. That gives handmade timbres for the films, a middle path between cheesy synth and too-real SoundFonts.
- **A sound palette folder** per project: references, plus "this kind of organ, not that".

### Ideas worth a chat of their own
- **Story-driven tuning:** a film score whose tuning drifts with the plot (12-EDO comfort sliding into 13-EDO unease at the twist), engraved with microtonal notation shown on screen.
- **A playable instrument from a tessellation:** tile symmetries become rhythm (rotation order sets meter) and harmony (lattice position sets ratio). The tiling and the music share one data structure (see §4).
- **Tonnetz / tuning-lattice motion design** for explainers of your xenharmonic work (see §5).
- **Shaders that make sound:** Shadertoy supports GLSL that renders audio, so one shader can generate both the picture and the soundtrack.

---

## 4. Tessellations with time (the pleasantly shocking part)

Tessellations become animatable when you treat them as **parameterized systems**, not drawings.

| Idea | How it moves | Tools |
|---|---|---|
| **Escher metamorphosis** | Tiles morph between shapes over time (a bird becomes a fish becomes a lizard) | Craig Kaplan's **Tactile** library: every isohedral tiling type with editable edge parameters, so animating the parameters animates the tiling |
| **Tiles that peel off** (Escher's *Reptiles*) | A tile lifts out of the flat pattern, becomes a 3D clay or origami creature, walks off, and comes back | Blender: the tile is an SVG outline, then inflated or folded, then rigged; it returns to its slot |
| **Material tilings** | The same tiling built from twigs, pipe cleaners, felt, clay, matchsticks or paper; tiles hop into place one by one | Geometry Nodes instancing on the lattice. Pipe cleaner = curve plus fuzzy hair; twig = curve with bark texture |
| **Aperiodic infinite zoom** | Penrose, or the 2023 "hat"/spectre monotile, zooming forever by substitution (each tile subdivides into smaller tiles) | A Python substitution generator into Blender or canvas. A seamless loop that never repeats |
| **Truchet / Wang tiles as cellular automata** | Each frame, tiles rotate by a rule, so patterns evolve like Game of Life on a tiling | Your tessellation-lab engine plus a rule table |
| **Origami tessellations** | Miura-ori and Resch patterns fold and unfold: a floor that breathes | Origami Simulator (§2) |
| **Hyperbolic tilings** | Poincaré-disk tilings flowing under Möbius transforms: wormhole energy | A shader (§9). Tile edges can carry music (§3) |
| **3D honeycombs** | Space-filling polyhedra (truncated octahedra, rhombic dodecahedra) build and dissolve. Voxels are just the cubic honeycomb, which links to §7 | Geometry Nodes |

**The big swing:** an Escher-style stop-motion short. The floor is a bird tessellation; one bird peels off as a folded paper crane, flies through a clay world, and lands back in its slot as the pattern flips to fish. It joins tessellation, origami, clay and a tuning that changes with the pattern.

**Your pre-load:**
- Your existing tessellation SVGs, organised by symmetry type.
- **A physical tiling for real stop motion:** pipe cleaners or twigs on a table, shot top-down with a locked camera while you move pieces between frames. I can turn your physical frames into a hybrid with CG tiles continuing the pattern beyond the table.
- Photos of the materials on a plain background, for textures and shape reference.

---

## 4b. Magic Eye: autostereograms and steganography, in 2D and 3D

**How it works:** an autostereogram is a horizontally repeating pattern. Where the hidden surface is closer, the repeat distance shrinks slightly. Your eyes, crossed or relaxed past the page, fuse neighbouring repeats, and the differences in distance read as depth. All it needs is a **depth map** (white = near) and a **pattern** (random dots, or any tile whose width is about the repeat distance).

**Why it belongs with tessellations:** a tessellation strip is a perfect pattern source. Tiled at the eye's repeat distance, the Escher tiles warp around the hidden shape. Even a plain tessellation with slightly varied tile widths produces the "wallpaper effect", where whole rows float at different depths. Your tiling *is* the stereogram.

| Form | What it is | Pipeline |
|---|---|---|
| **2D still** | Classic single-image stereogram: hidden shape in random dots or a tessellation pattern | Depth map + pattern tile → stereogram generator (the 1994 Thimbleby–Inglis–Witten algorithm with hidden-surface handling, in NumPy) → print or screen |
| **2D animated** | The hidden shape moves: a crane flaps, Cramer swings, a tile peels off | Depth video (Blender Z-pass per frame) → per-frame stereogram. Anchor the pattern so it doesn't shimmer, or let random dots crawl deliberately for that vintage TV look |
| **3D: depth from our worlds** | Any Blender or voxel or splat scene becomes the hidden object | Blender renders a normalized Z-pass instead of beauty; clay puppets, origami folds, voxel landscapes and splats all export depth |
| **3D: stereograms inside 3D scenes** | A Magic Eye poster on the wall of the clay diorama that still works when the camera faces it; a tessellated floor that hides a message | Generate the stereogram image, then texture it onto set pieces facing camera |
| **True stereo 3D** | Side-by-side (cross-eye), anaglyph (red/cyan) or VR pairs of the same scenes | Blender stereoscopy (two cameras) → combine in ffmpeg |
| **Steganography proper** | Hidden *messages*: text or a QR code in the depth layer, data in tile colour choices, a secret image revealed only when two tessellations overlay | Encode into depth (stereogram), into the tiling's colour sequence, or as a two-layer reveal |

**Your pre-load (all offline):**
- **Depth maps:** render a Z-pass in Blender yourself (a View Layer pass, normalized, white near), or paint one in any image editor with a soft brush. Text depth maps are easy: type, blur slightly, and that's your hidden word.
- **Pattern tiles:** your tessellation SVGs exported at the repeat width. For screen viewing that's roughly 80–140 px; for print, about 2.5–3 cm.
- **Viewing method:** wall-eyed (relaxed, the classic Magic Eye) or cross-eyed. The generator flips depth for each.
- **Print or screen:** target size and DPI, because the repeat distance is physical.

**First project:** a still stereogram where a tessellation of birds hides a flying crane, then the animated version. It ties §2, §4 and this section into one piece.

---

## 5. Motion design: a primer, and where we'd use it

Motion design is **timing applied to shapes, type and cameras**. The vocabulary you'll use with me:

- **Easing:** ease-in/out, overshoot and settle, anticipation (a small move the opposite way first).
- **Stagger:** the same move offset per element (a wave). This is what makes motion feel designed.
- **Follow-through:** loose parts lag and settle (tassels, ears, threads).
- **Match cuts and masks:** a circle becomes the moon becomes a coin; reveals through shapes.
- **Seamless loops:** first frame equals last frame. Perfect for social posts and tessellations.
- **Kinetic type:** words that move with the voice. We already do this with word timestamps.

| Tool | Use |
|---|---|
| **Our canvas runtime** (animated-short) | 2D paper and stop-motion style; proven |
| **Motion Canvas** (TypeScript, open source) | Code-driven motion graphics with excellent timing tools; fits how I work |
| **Manim** (Python, 3Blue1Brown's engine) | Mathematical animation: tunings, lattices, tessellation proofs |
| **Blender Geometry Nodes** | 3D motion design: instancing, procedural stagger, simulation |
| **DaVinci Resolve / Fusion** (you have it) | **You** composite, grade and finish without me: node compositing, DCTL shaders, Fairlight audio |

**Your pre-load:** style frames (1–3 stills of the look), a motion reference reel (5–10 clips with a note on what you like in each), and type and palette choices. Then I time and build.

**Natural first fit:** a 45 s explainer of one of your tuning systems, using Manim or Motion Canvas for the lattice, your engraving as a cut-paper prop, and your sound.

---

## 6. NeRFs and Gaussian splats: video to dreamy 3D

**What a splat is:** millions of soft, coloured, semi-transparent blobs fitted to photos so that, from any angle, they reproduce the scene. It's photoreal yet painterly, and blobs can be animated individually, which is where the dreamy effects come from.

**Pipeline:**
```
capture (phone video / photos)
  └─► camera poses   (COLMAP, or the trainer's built-in solver)
        └─► train splats   → .ply
              └─► clean/crop in SuperSplat (free, browser, PlayCanvas)
                    ├─► Blender: KIRI Engine's "3DGS Render" add-on (render splats in Eevee alongside our clay)
                    └─► Web: PlayCanvas, three.js (Spark, GaussianSplats3D) — our browser films can host them
```

| Training option | Fit on your M1 Pro (16 GB) |
|---|---|
| **Scaniverse** or **KIRI Engine** (phone apps) | Easiest. They capture and train on the phone or in the cloud, then export PLY |
| **Brush** (open source, WebGPU) | Trains locally on a Mac. Good for small objects and dioramas |
| **OpenSplat** (open source, Metal) | Local CLI trainer; pairs with COLMAP |
| nerfstudio / Postshot | CUDA or Windows only; skip unless you rent a GPU |

**Capture rules (your offline craft):**
- Walk slowly in two or three orbits at different heights.
- Use 150–300 photos, or 1–2 minutes of steady 4K video.
- Lock exposure and focus, and avoid motion blur.
- Matte subjects work best; shiny or transparent ones are hard.
- Overlap each frame by about 70%.

**Dreamy effects I can build:**
- Splats inflated into brush strokes, a painterly bokeh world.
- Dissolving into drifting particles.
- Morphing one scene into another.
- Per-splat jitter on stepped frames, which is stop motion for a photoreal world.
- Depth-of-field pulls.
- Your clay or origami puppets acting *inside* a splat of a real place.

**First project:** splat your desk diorama or a houseplant, then fly an impossible camera move through it with a paper crane (§2) in the scene.

---

## 7. Voxels: lo-fi as a language

**Flow:** you build in **MagicaVoxel** (models, 256-colour palette, multiple frames for animation). Export `.vox` or OBJ into Blender, where I light, rig and animate. Or keep MagicaVoxel's own path-traced renderer for stills.

| Approach | What it gives |
|---|---|
| **Frame-by-frame voxel models** | True stop motion in voxels. MagicaVoxel has frames, so you can animate by hand with no AI |
| **Procedural voxelization** (Geometry Nodes: mesh → volume → points → cubes) | Any animated mesh becomes voxels. Cramer's clay relief as voxels; resolution as a dial (8×8 → 256³) |
| **Resolution as narrative** | A story that gains resolution as it goes: 8-bit blocks melting into clay. The "lo-fi callback" becomes a plot device |
| **Cellular automata in 3D** | 3D Game of Life, sandpiles, growth, erosion. Living voxel landscapes |
| **Voxel physics** | Worlds crumbling and rebuilding, Teardown-style |
| **MagicaCSG** (same author) | SDF modelling: smooth shapes you can voxelize at any resolution |

For game development, Godot (free) has mature voxel plugins, and three.js InstancedMesh handles web voxels.

**Your pre-load:** learn MagicaVoxel by building a character, a palette and a small set (that's the craft part), and save `.vox` files to `canon/vox/`. Palette design is a creative constraint worth owning; treat it like an 8-bit console palette.

---

## 8. Glitch: pixel sorting, datamosh, and doing it in 3D

**2D toolkit:**
- **Pixel sorting:** sort runs of pixels by brightness or hue between thresholds. A Python/NumPy script; I'll write one with masks so only chosen regions sort.
- **Datamosh:** delete keyframes from compressed video so motion data smears one shot into the next. **ffglitch** is the power tool: an ffmpeg fork that lets you **script the motion vectors**, so you can control the smear.
- **Databending:** open images as raw audio and run audio effects on them. **Channel shifts, scanlines, JPEG rot** happen in ffmpeg or shaders.

**In 3D (the new territory):**

| Effect | How |
|---|---|
| **3D pixel sort** | Blender's **Sort Elements** node (in your 5.2) reorders vertices or points by height, colour or noise. Sorted geometry smears like sorted pixels, in true depth. Splat sorting (§6) works the same way |
| **Render-pass datamosh** | Render Blender's motion-vector pass, then advect the *previous* frame with the *current* vectors (feedback warp). A controllable, beat-synced mosh with no codec tricks |
| **Vertex-order glitch** | Scramble vertex order between shape keys, so a morph explodes into ribbons and re-forms. This is datamosh's 3D twin |
| **Depth-driven glitch** | Use the depth pass as the threshold for sorting or displacement, so the glitch respects the 3D structure |
| **Voxel and resolution glitch** | Snap resolution down on the beat (§7) |

**Your pre-load:** source footage you like, a glitch grammar (when it happens: on beats, story turns or cuts), and install **ffglitch**. TouchDesigner (free non-commercial) is an optional real-time playground for this style.

---

## 9. Shaders: demoscene energy, unconventional places

**Where shaders can run in our world:**

| Place | How |
|---|---|
| **Our browser films** | Add WebGL post passes (CRT bloom, halftone, plasma, chromatic aberration, Gaussian blur) to the canvas runtime. Frames export through headless Chrome as now |
| **Offline frame processing** | A small GLSL runner (Python moderngl or glslViewer) applies any Shadertoy-style shader to Blender or canvas frames. (Your ffmpeg lacks the libplacebo shader filter, so a runner is the route) |
| **Blender** | Shader nodes for materials (the clay fingerprints were a shader). OSL for custom shaders in Cycles. The compositor for post |
| **DaVinci Resolve** | **DCTL**: write your own colour and glitch shaders and use them in your edits, entirely offline |
| **Ableton / Max for Live** | Jitter and gen shaders reacting to your music live |
| **Live coding** | **Hydra** (browser) for demoscene-style visual jams; KodeLife or Bonzomatic for shader-jam editing |

**Paper Shaders (already cloned at `~/yougonelearn/tcp/shaders`, from github.com/paper-design/shaders, Apache 2.0):**
30 zero-dependency WebGL shaders as plain code: `paper-texture`, `halftone-cmyk`, `halftone-dots`, `dithering`, `image-dithering`, `grain-gradient`, `fluted-glass`, `liquid-metal`, `metaballs`, `voronoi`, `warp`, `water`, `god-rays`, `heatmap`, `mesh-gradient`, `neuro-noise`, `smoke-ring`, `spiral`, `swirl`, `waves` and more.
- **They plug straight into our browser films.** The canvas runtime renders in headless Chrome, so any of them can be a background, a texture masked to a shape, or a post pass.
- **The image shaders process any frame:** `image-dithering`, `halftone-cmyk`, `halftone-dots`, `fluted-glass`, `water` and `heatmap`. A frame-sequence pass applies them to Blender renders too: Cramer II through CMYK halftone, or the graveyard through 1-bit dithering.
- **Their GLSL is plain source,** so the offline runner can use it outside the browser.
- **Thematic fits:** `paper-texture` for the origami and papercraft world, `metaballs` for clay blobs, `voronoi` for organic tilings and cracked-glaze clay, `halftone-cmyk` and `dithering` as demoscene and print finishes.
- **You can design them visually:** in the Paper app or the docs playground (shaders.paper.design), then hand me the parameter values. That's zero-token design work.

**Unconventional places:**
- **Shaders as materials for physical paper:** print shader output (a plasma, a hyperbolic tiling) as origami paper, fold it, scan it, and animate it.
- **Shaders as sound** (§3).
- **Shaders that are tessellations:** domain repetition and hyperbolic tilings in a fragment shader.
- **Raymarched SDFs voxelized** (§7).
- **CRT and halftone as storytelling:** the image degrades as the narrator lies.

**Your pre-load:** keep a shader sketchbook (Shadertoy favourites, plus your own experiments in KodeLife). If you write shaders in **Shadertoy conventions** (`iTime`, `iResolution`, `iChannel0`), anything you write plugs into my runner and the canvas runtime unchanged.

---

## 10. How it all connects

```
           your offline crafts                 shared formats                     engines
  ┌────────────────────────────┐   ┌──────────────────────────────┐   ┌──────────────────────────┐
  │ drawing / sculpting clay   │──►│ layered PNG/SVG · scans · OBJ│──►│ Blender (clay, paper,    │
  │ folding / tracing CPs      │──►│ CP SVG · .fold               │──►│  voxels, splats, GN)     │
  │ MagicaVoxel building       │──►│ .vox                         │──►│ canvas runtime (2D)      │
  │ phone capture (splats)     │──►│ .ply                         │──►│ web (three/PlayCanvas)   │
  │ playing / composing        │──►│ MIDI · MusicXML · .scl · WAV │──►│ SuperCollider NRT · Live │
  │ shader sketching           │──►│ GLSL (Shadertoy uniforms)    │──►│ GLSL runner · Resolve    │
  └────────────────────────────┘   └──────────────────────────────┘   └──────────────────────────┘
                                            one clock: animate(t) driven by the soundtrack
```

The rule that makes it all combine is **one clock**: every engine takes time `t` and the soundtrack's timeline. Clay, origami, tiles, voxels and shaders can then share a shot.

## 11. A suggested ladder (each rung builds a reusable skill)
1. **Fold** (§2): Miura-ori then a crane that folds and flaps. Gives the CP → simulator → Blender skill.
   **Clay foundry** (§1) can run in parallel: records you write, and I build `clay-forge`.
   **Magic Eye** (§4b) is a quick early win: the generator is small, and your tessellations and Blender depth maps feed it.
2. **Tune** (§3): install SuperCollider, Surge XT and AbletonOSC; one xenharmonic piece in your tuning that drives a short film.
3. **Tile** (§4): an Escher metamorphosis loop, then the bird-peels-off-the-floor short.
4. **Scan** (§1, §6): a clay head with a mouth set, plus a splat of a real place for it to live in.
5. **Break** (§8, §9): a glitch and shader post-stack as a skill applied to everything above.
6. **Voxel** (§7): resolution-as-narrative.

**Things to install** (all free): SuperCollider, Surge XT, MTS-ESP Mini, AbletonOSC, ffglitch, ORIPA (needs Java), Brush or OpenSplat with COLMAP, and Scaniverse on your phone. Optional: TouchDesigner, Godot, KodeLife.

---

## 12. Addendum (2026-10-04, round 2)

### 12a. Shaders as sound sources
A shader is a function of position and time. Sound is a function of time. Any shader can be *read* as audio:

| Technique | How it works | Bridge to your gear |
|---|---|---|
| **Sound shaders** (Shadertoy style) | GLSL `vec2 mainSound(int sample, float t)` returns a stereo sample; the GPU computes thousands at once into a texture. Demoscene 4k intros make picture and music from one file this way | Rendered offline in headless Chrome to WAV; the same functions can drive the image shader, so the visuals and audio share one equation |
| **Wave-terrain synthesis** | Treat a 2D shader (plasma, Paper Shaders' `warp`, `voronoi`, `metaballs`) as a landscape and trace an orbit through it at audio rate; the heights along the path are the waveform. Moving or morphing the orbit changes the timbre. The picture *is* the instrument | Render as WAV, or as a wavetable (next row) |
| **Shader → wavetable bank** | Each row of a shader frame becomes one waveform cycle; successive frames morph. Export as a wavetable `.wav` | Load into **Surge XT** or **Vital** in Ableton: play with MPE, tuned by MTS-ESP to your `.scl`. Your demoscene visuals become a playable instrument |
| **Image as spectrogram** | Read a frame with y = frequency and x = time, and resynthesize (inverse STFT). Animated shaders become evolving drones; halftone and dither patterns become rhythmic textures | Stems for the films; also the reverse (audio → texture) for audio-reactive shaders |
| **Raster scan** | Read pixels left to right like a TV signal → audio, and back (audio → raster image: "seeing" a sound) | A glitch-aesthetic bridge (§8) |

### 12b. An audio-processing language (proposed skill: token-light, compute-heavy)
**Idea:** a *recipe* file describes the sound; a local engine executes it. I write or adjust recipes (a few lines); the
heavy DSP runs without me. It's reproducible because a recipe plus a seed plus an input always gives the same bytes.
```yaml
# recipe: haunted-music-box.yaml
input: music_box.wav
seed: 7
chain:
  - pitch: {semitones: -12}
  - tape_warble: {preset: worn}
  - granular: {grain_ms: 80, density: 12, jitter: 0.3}
  - reverb: {size: 0.9, wet: 0.4}
loop: {times: 4, feedback: 0.6, mutate: {reverb.size: [0.6, 1.0]}}   # re-process the output N times, drifting params
target: {lufs: -18, max_centroid_hz: 2500}                            # optional: search params until targets are met
```
- **Engine:** Python with Spotify's **pedalboard** (fast C++ effects, and it can **host your installed AU/VST3
  plugins**), our tape-warble, granular / spectral-freeze / convolution in NumPy, and SuperCollider NRT for synthesis
  stages.
- **Commands:** `loom run recipe.yaml`; `loom explore recipe.yaml --vary reverb.size --n 8` renders 8 variants onto an
  audition page so you choose by ear (zero tokens); `loom target …` searches parameters until the metrics are met.
- **Free expression:** any parameter can be an LFO, an envelope, a random walk or an expression in `t`; recipes can
  include other recipes; every run writes recipe + seed + hash next to the output.
- Say the word and I'll build v0 as a skill.

### 12c. Depth maps: sources and generators
| Source | Notes |
|---|---|
| **From one photo (on your Mac)** | **Apple Depth Pro** (open source, sharp metric depth, runs on Apple Silicon via PyTorch), **Depth Anything V2** (fast; in Hugging Face transformers, which we have), Marigold (diffusion-based, very crisp edges, slower) |
| **From video** | **Video Depth Anything** / DepthCrafter: temporally stable depth for animated stereograms of real footage |
| **From our 3D worlds** | Blender depth or mist pass (clay sets, origami, voxel imports); Brush splats rendered to depth |
| **COLMAP (your build)** | Version 4.2.1 **without GPU**: camera solving and sparse point clouds work, but its dense depth step needs an NVIDIA GPU. Mac route: COLMAP sparse → **Brush** (in `~/yougonelearn/brush`; reads COLMAP datasets) trains a splat → render depth and views. **OpenMVS** is a CPU alternative for dense depth and meshes |
| **Ready-made** | Free stereogram depth-map collections; 3D-print STL libraries (Thingiverse, Printables): relief STLs make excellent depth maps through Blender; Poly Haven (CC0 models); research sets with true depth (Middlebury stereo, MPI Sintel, which has animated depth, NYU Depth V2) |
| **Hand-made** | Paint white = near with a soft brush; type a word and blur it; or inflate any silhouette (the distance-transform trick from the clay height maps) |
The point-cloud and reconstruction look you liked from COLMAP (and Benjamin Bardou's latent, glitchy cityscapes) also
works as an *aesthetic*: sparse clouds, splat dissolves and reconstruction errors rendered deliberately (§6, §8).

### 12d. MagicaVoxel ↔ AI bridges
- **The MCP that exists:** `Mahinika/magicavoxel-mcp` (small, community-built). It edits `.vox` *files* through tool calls
  (place voxel, fill box, sphere…); it doesn't control the app. It works, but voxel-by-voxel tool calls are token-expensive.
- **Better bridges for your token goals:**
  1. **`.vox` read/write in Python:** I generate whole models in one script run (from NumPy arrays, heightmaps,
     voxelized meshes or the clay forms) and read yours into Blender. One command, any size.
  2. **MagicaVoxel's own shader scripts:** the app runs GLSL "shader" scripts from its `shader/` folder to generate or
     modify voxels in place. I write the shader files; you run and tweak them inside the app with sliders. Native and
     zero-token per use.
  3. **Blender:** import `.vox` (add-on) or OBJ exports for lighting and animation.

### 12e. Clay-forge pre-load tool: built
`~/.claude/skills/clay-forge/`: `init_kit.py` (scaffold), `check_kit.py` (readiness + kit.json), `clay.blend` (ClayLook
sliders), `export_look.py` (records your tuning), `guides/BLENDER_FIRST_STEPS.md` (for total beginners).
