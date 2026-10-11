# Animation tooling: inventory, verified examples, and build blueprint

**Verified:** 2026-10-11 in a cloud sandbox: Ubuntu, Python 3.13.16, Node 22.22.0, ffmpeg and ffprobe 6.1.1, uv 0.11.32, headless Chromium at `/opt/pw-browsers/chromium`.

This document is written so an agent with no prior context can rebuild the work. Paths in commands are relative to `docs/animation-tooling/`.

**Status keys**
- **Verified:** run in the sandbox, with output checked by ffprobe or by viewing the frame.
- **Partial:** installed or inspected, but the full path was not run.
- **Not run:** documented only (licensed GUI apps, accounts, or too heavy for the sandbox).

**Link note:** the sandbox egress policy blocked `cdn.jsdelivr.net` and most official project websites. Links marked † come from known official domains and were not reachable from the sandbox. npm, PyPI, `git clone` from GitHub, `storage.googleapis.com`, and `claude.com` were reachable.

## 1. Summary

- Blender does not ship an MCP server. The community project's README calls itself "a third-party integration and not made by Blender". Its PyPI package is now `mcp-for-blender`, formerly `blender-mcp`.
- The Python route is the strongest for reproducible 3D here. `bpy 5.2.2` installs on the sandbox's Python 3.13, and a spec-driven pipeline (§5.1) produced identical per-frame pixel hashes across two runs.
- Browser and JavaScript tools also render end to end: HyperFrames (HTML and GSAP), Motion Canvas (TypeScript generators), and Remotion (React). Lottie plays hand-written JSON in Chromium.
- Manim renders math and diagrams on Python 3.12, once Pango and Cairo headers are installed.
- No skill named `animated-short` exists on this account or in this repo. Send its path or SKILL.md so it can be compared with the design in §8.

## 2. Skills, plugins, and MCP entries

| Name | Kind | Status here | Where it lives or how to install | What it does and how relevant it is |
|---|---|---|---|---|
| `3d-animation-short-generator` | claude.ai skill (plugin-backed) | Enabled, not run | Skill `skill_01YB3cg9xwvuuLt6rbptj2qu`; backing plugin `plugin_019AW8pr1YoNX1qKv17YvJUu`. Lives in the claude.ai skill library, no public URL. | AI-video production: story outline, character and environment cards, shot planning, video-model generation, assembly, BGM, review. Generative, not procedural. |
| `animated-short` (yours) | Not found | n/a | Not in the claude.ai skill list or in this repo's `.claude/skills/` | Needs its path or SKILL.md before it can be compared. |
| `painters-order` | Repo skill | Present, not run | `.claude/skills/painters-order/SKILL.md` | Python procedural pipeline: a tessellation becomes a video with synthesized sound. Closest in-repo precedent for code-generated animation. |
| `animation-studio` | Anthropic Directory plugin (community) | Not installed | Plugin `plugin_01Twajzi6JWwx8f27E2mGShm`, marketplace `marketplace_01VNB7JgJyYTuJiDfXSABKm3`. [Marketplace page](https://claude.com/marketplace/plugins/animation-studio) | Every frame drawn in code, soundtrack synthesized in code from one score, 1080p MP4 in 16:9 or 9:16. No public source found; review before installing. |
| `Sticklore` | Anthropic Directory plugin (community) | Not installed | Plugin `plugin_015RLuPYF4LNAcADQTCP7sMK`. [Marketplace page](https://claude.com/marketplace/plugins/sticklore) | Stick-figure explainers from a topic. No public repo or docs found. |
| HyperFrames plugin | Claude plugin | Not installed | `claude plugin marketplace add heygen-com/hyperframes`, then `claude plugin install hyperframes@hyperframes`. [Plugin page](https://claude.com/plugins/hyperframes) | Skills for HTML video, with router `/hyperframes` and 21 skills. |
| HyperFrames MCP entry | MCP registry | Not connected | Registry UUID `275b944b-60a0-4f0d-9e55-0c0e5927a5c7`; tools `compose`, `render_video` | Hosted or registry route to the same HTML-to-MP4 idea. Not tested. |
| `web-animation-design` (in `audit-suite`) | Plugin skill | Not installed | Plugin `plugin_01X6swf4meJA8ZwrFryZ5MWK` | UI and web animation review. Not film animation. |
| Very Good AI Flutter Plugin (`animations`) | Plugin skill | Not installed | Plugin `plugin_01BDWRJ9EBgXM6tZk8fCSebx` | Flutter UI animation. Not relevant. |
| Three.js 3D Viewer | MCP registry demo | Not connected | UUID `471ca2be-244d-4d9a-955a-3cdbcf76a12b`; no tools listed | Demo viewer only. |
| Moda, Orshot | MCP registry | Not connected | UUIDs `ea86601d-514b-42e4-aefc-32c6c51baf7e` (Moda) and `68b8b4d0-aaec-416a-9bcf-4d2ff3bf7142` (Orshot) | Template-driven motion graphics and social video. Commercial products, not tested. |
| ClaudeAnimationBase | Third-party open-source kit (reported) | Not tested | Reported in [an AlphaSignal write-up](https://alphasignal.ai/news/claudeanimationbase-turns-a-single-prompt-into-hand-painted-mp4-cartoons). No repo found in search. | p5.js and p5.brush frames rendered to MP4 with ffmpeg; MIT per the write-up. Single source, so confirm the repo before use. |
| Higgsfield "Stickman cartoon explainer" | External connector skill | Not tested | [Skill page](https://higgsfield.ai/skills/stickman-cartoon) | Hosted generation that requires an account. May or may not be what Sticklore is. Unconfirmed. |
| `blender-mcp` / `mcp-for-blender` | Community MCP server and Blender add-on | Server verified via `uvx`; add-on not run | See §3 | Interactive Blender control from an AI client. |

Other registry results (vidIQ, Render, BioRender, Attention, Yardi Matrix, Notion) are not relevant to animation.

Considered and not pursued: Claude Design's "Animation" template (search results say it needs a paid plan), and an "Animator Traditional" SKILL.md on a third-party registry (guidance only, not a renderer).

## 3. Blender: what is verified

**MCP route.** The community project is [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp) (repository reachable; MIT). Its README says the PyPI package is now [`mcp-for-blender`](https://pypi.org/project/mcp-for-blender/) and that `uvx blender-mcp` still works. Verified: `uvx mcp-for-blender --help` installs the package and lists the subcommands `install-addon`, `addon-paths`, `setup`, and `update`.

Documented setup: install `uv`, run `uvx mcp-for-blender setup`, then open Blender. The add-on starts its server when Blender opens.

Tools exposed by the add-on, from its source: `execute_blender_code` (runs arbitrary Python inside Blender), `get_scene_info`, `get_object_info`, `get_viewport_screenshot`, and search and download tools for PolyHaven, Sketchfab, and Poly Pizza assets. The README also lists a Premium tier for AI 3D model generation.

**Security.** `execute_blender_code` runs arbitrary code inside the Blender process. Use it only on machines you control. Assets from third-party libraries carry their own licenses.

**bpy route (verified).**
- Package: [bpy on PyPI](https://pypi.org/project/bpy/). License: GPL-3.0.
- Wheel matrix, checked with `pip index versions bpy --python-version X`: 5.2.x and 5.1.x target CPython 3.13; 5.0.x targets CPython 3.11. Match the interpreter to the version.
- Install: `python3.13 -m venv .venv && .venv/bin/pip install bpy==5.2.2`.
- Check: `import bpy` then `bpy.app.version_string` returned `5.2.2 LTS` on Python 3.13.16.
- API change in Blender 5.x: `Action.fcurves` no longer exists. The first script failed with `AttributeError: 'Action' object has no attribute 'fcurves'`. The working path is `action.layers[0].strips[0].channelbag(action.slots[0]).fcurves`.
- Headless rendering: Cycles on CPU needs no GPU. 48 frames at 480×270 with 16 samples took about 30 seconds on this 4-core sandbox.
- Reproducibility: two runs of the same spec gave identical decoded-pixel hashes for all 48 frames and an identical MP4 SHA-256. Raw PNG bytes differ between runs because of metadata chunks, so the pipeline hashes decoded RGB pixels. Cross-machine determinism was not tested.

## 4. "What the experts use": linked table with working examples

| Need | Tool and source | Status here | Working example | Caveat |
|---|---|---|---|---|
| Scripted 3D: modeling, keyframes, renders | [Blender](https://www.blender.org)† via [bpy 5.2.2](https://pypi.org/project/bpy/). Python API: [docs.blender.org/api/current](https://docs.blender.org/api/current/)† | **Verified** | §5.1 and §8 | Pin the Blender version. The API changes between majors. GUI Blender is not installed here. |
| Node-based procedural VFX | [Houdini](https://www.sidefx.com)† (HOM Python) | **Not run** | None | Commercial desktop app, not installable in the sandbox. |
| Real-time 3D and cinematics | [Unreal Engine](https://www.unrealengine.com)† (Python editor scripting, Sequencer) | **Not run** | None | Large engine that needs a GPU. |
| Code-driven 2D motion and explainers | [Motion Canvas](https://motioncanvas.io)† 3.17.2, MIT. [Source](https://github.com/motion-canvas/motion-canvas) (reachable) | **Verified** | §5.4 | Use Vite 5, since the plugin's peer range is 4 to 5. The published CJS builds need `.default` unwrapped. Rendering goes through the editor's Render button, automated with playwright-core. |
| Code-driven video: HTML and GSAP | [HyperFrames](https://hyperframes.heygen.com)† 0.8.146, Apache-2.0. [Source](https://github.com/heygen-com/hyperframes) (reachable) | **Verified** | §5.2 | Set `HYPERFRAMES_CHROME_PATH`. Telemetry is on by default, so disable it. Vendor GSAP if the CDN is blocked. |
| Code-driven video: React | [Remotion](https://www.remotion.dev)† 4.0.534. [Source](https://github.com/remotion-dev/remotion) (reachable) | **Verified** | §5.5 | Free for individuals, non-profits, and for-profit organizations with up to 3 employees. Larger organizations need a company license. The license text says it changes in Remotion 5.0. Default headless mode fails on this Chromium build, so use `--chrome-mode=chrome-for-testing`. |
| Math and diagram animation | [Manim Community Edition](https://docs.manim.community)† 0.22.0, MIT. [Source](https://github.com/ManimCommunity/manim) (reachable) | **Verified** | §5.3 | Use Python 3.12, since manimpango has no cp313 wheel. On Linux, install Pango and Cairo headers. |
| Interactive vector characters | [Rive](https://rive.app)†, runtime [@rive-app/canvas](https://www.npmjs.com/package/@rive-app/canvas) 2.44.2, MIT | **Partial**: package checked on npm, no `.riv` file run | None | `.riv` files are authored in the Rive editor, a GUI. Not fully code-driven. |
| Vector JSON playback | [Lottie](https://airbnb.design/lottie/)†, runtime [lottie-web](https://github.com/airbnb/lottie-web) 5.13.0, MIT | **Verified** | §5.6 | Usually exported from After Effects with Bodymovin. Hand-written JSON is verbose. |
| Rigs and character libraries | [Mixamo](https://www.mixamo.com)† (auto-rig and motion library, Adobe account) | **Not run** | None | Web UI with Adobe sign-in. No API used here. |
| Pose and motion capture from video | [MediaPipe Pose Landmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker)†, [mediapipe](https://pypi.org/project/mediapipe/) 1.1.0, Apache-2.0 | **Verified** on one still image | §5.7 | Needs `libegl1`, `libgl1`, `libgles2`, and the 5.8 MB `.task` model. Video input was not tested. |
| Lip sync from dialogue | [Rhubarb Lip Sync](https://github.com/DanielSWolf/rhubarb-lip-sync) 1.14.0, MIT | **Verified** | §5.8 | Quality depends on the audio. The test used synthetic speech from espeak-ng. |
| Muxing and encoding | [FFmpeg](https://ffmpeg.org)† 6.1.1, installed | **Verified** in every pipeline above | §5.1, §5.2, §5.4 | Needs libx264. |
| Interactive AI control of Blender | [mcp-for-blender](https://pypi.org/project/mcp-for-blender/), MIT (see §3) | **Partial**: server runs via `uvx`, add-on not run | §3 | Executes arbitrary Python. Keep it local. |
| Character posing with physics | [Cascadeur](https://cascadeur.com)† | **Not run** | None | Not evaluated. Scripting interface not confirmed. |
| Code-driven 2D video, TypeScript | [Revideo](https://github.com/redotvideo/revideo) (official repo, reachable) | **Not run** | None | A Motion Canvas fork with server-side rendering, according to a [2026 comparison](https://www.pkgpulse.com/guides/remotion-vs-motion-canvas-vs-revideo-programmatic-video-2026). The npm package named `revideo` is a 0.0.0 placeholder that points at a fork, so use the official repo. |
| AI video generation on this account | `3d-animation-short-generator` skill | Enabled, not run | None | Generative path. Complements the procedural path rather than replacing it. |
| In-repo procedural art-to-video | `painters-order` | Present, not run | None | Procedural Python pipeline. |

† Not reachable from the sandbox. Listed from known official domains, so confirm before relying on them.

## 5. Verified examples

Source files are in [`examples/`](examples/) and reproduced exactly in Appendix A.

### 5.1 Blender bpy pipeline

Files: [`examples/bpy/render_scene.py`](examples/bpy/render_scene.py), [`examples/bpy/spec.example.json`](examples/bpy/spec.example.json)

```bash
python3.13 -m venv .venv
.venv/bin/pip install bpy==5.2.2
.venv/bin/python examples/bpy/render_scene.py examples/bpy/spec.example.json out/bounce
```

Result: `out/bounce/frame_0001.png` through `frame_0048.png`, `bounce.mp4` (H.264, 480×270, 24 fps, 48 frames, 2.0 s), and `manifest.json`. The frame at 12 shows the sphere touching the ground with a contact shadow.

### 5.2 HyperFrames

Files: [`examples/hyperframes/index.html`](examples/hyperframes/index.html)

```bash
export HYPERFRAMES_CHROME_PATH=/opt/pw-browsers/chromium   # any Chrome or Chromium binary
export HYPERFRAMES_SKIP_SKILLS=1
npx --yes hyperframes@0.8.146 telemetry disable
npx --yes hyperframes@0.8.146 init hf-demo --example blank --non-interactive --resolution=landscape --skip-transcribe
npm install --prefix /tmp/gsap-pkg gsap@3.14.2
mkdir -p hf-demo/vendor && cp /tmp/gsap-pkg/node_modules/gsap/dist/gsap.min.js hf-demo/vendor/
cp examples/hyperframes/index.html hf-demo/index.html
npx --yes hyperframes@0.8.146 lint hf-demo
npx --yes hyperframes@0.8.146 render hf-demo -o out/hf-demo.mp4 --quiet
```

Result: H.264, 1920×1080, 30 fps, 120 frames, 4.0 s. The frame at 2 s shows the title fully in place and the ball mid-travel. `lint` reported 0 errors and 0 warnings.

Gotchas:
- Without the vendored GSAP, the render failed with `sub_timeline_script_failure`, because the sandbox blocks `cdn.jsdelivr.net`. Replace the template's CDN script tag with a local file.
- HyperFrames requires Node 22 or newer and FFmpeg.

### 5.3 Manim

Files: [`examples/manim/sine_demo.py`](examples/manim/sine_demo.py)

```bash
uv python install 3.12
uv venv manim-venv --python 3.12
apt-get install -y libpango1.0-dev libcairo2-dev pkg-config   # manimpango builds from source on Linux
uv pip install --python manim-venv/bin/python manim==0.22.0
manim-venv/bin/manim -ql --format=mp4 -o sine_demo examples/manim/sine_demo.py SineDot
```

Result: `media/videos/sine_demo/480p15/sine_demo.mp4`, H.264, 854×480, 15 fps, 67 frames, 4.47 s.

Gotcha: the first attempt on Python 3.13 failed because `manimpango` had no cp313 wheel and needed Pango headers.

### 5.4 Motion Canvas

Files: [`examples/motion-canvas/`](examples/motion-canvas/): `package.json`, `vite.config.ts`, `render.mjs`, `src/project.ts`, `src/project.meta`, `src/scenes/example.tsx`, `src/motion-canvas.d.ts`, `tsconfig.json`

```bash
cp -r examples/motion-canvas mc-demo && cd mc-demo
npm install
CHROMIUM_PATH=/opt/pw-browsers/chromium node render.mjs   # starts Vite on :9000, clicks RENDER, waits for output/*.mp4
```

Result: `output/project.mp4`, H.264, 1280×720, 30 fps, 88 frames, 2.93 s. Vite stops when the script ends.

How it works: `project.meta` sets the exporter to `@motion-canvas/ffmpeg`, shown in the editor as "Video (FFmpeg)". The script opens the editor in headless Chromium and clicks Render.

Gotchas: A stray dev server from an earlier run holds port 9000 and silently serves the wrong project. Check with `ss -ltn | grep :9000` before rendering. The first version of `render.mjs` killed only the `npx` wrapper and left Vite running.

### 5.5 Remotion

No files to commit; the template is generated.

```bash
npx --yes create-video@4.0.534 --yes --blank remotion-demo
cd remotion-demo
npx remotion render src/index.ts MyComp out/remotion-demo.mp4 \
  --browser-executable=/opt/pw-browsers/chromium --chrome-mode=chrome-for-testing
```

Result: H.264, 1280×720, 30 fps, 60 frames, 2.0 s.

Gotcha: without `--chrome-mode=chrome-for-testing`, the render failed with "Old Headless mode has been removed from the Chrome binary".

### 5.6 Lottie

Files: [`examples/lottie/index.html`](examples/lottie/index.html), with hand-written Lottie JSON inline

```bash
mkdir -p lottie-demo/vendor && cd lottie-demo
npm install lottie-web@5.13.0
cp node_modules/lottie-web/build/player/lottie.min.js vendor/
cp ../examples/lottie/index.html .
/opt/pw-browsers/chromium --headless --no-sandbox --disable-gpu --allow-file-access-from-files \
  --window-size=400,400 --screenshot=frame30.png "file://$PWD/index.html"
```

Result: `frame30.png` shows the orange dot at the midpoint of its path. The page pauses at frame 30 of 60 for a deterministic still.

### 5.7 MediaPipe pose

Files: [`examples/mediapipe/pose_check.py`](examples/mediapipe/pose_check.py)

```bash
uv venv mp-venv --python 3.12
uv pip install --python mp-venv/bin/python mediapipe scikit-image pillow
apt-get install -y libegl1 libgl1 libgles2
curl -sSL -o pose_landmarker_lite.task \
  https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task
mp-venv/bin/python examples/mediapipe/pose_check.py
```

Result: `poses detected: 1`, with 33 landmarks on scikit-image's bundled sample photo. The script also writes `pose_overlay.png`.

### 5.8 Rhubarb lip sync

```bash
curl -sSL -o rhubarb.zip https://github.com/DanielSWolf/rhubarb-lip-sync/releases/download/v1.14.0/Rhubarb-Lip-Sync-1.14.0-Linux.zip
unzip -q rhubarb.zip -d rhubarb
chmod +x rhubarb/Rhubarb-Lip-Sync-1.14.0-Linux/rhubarb
apt-get install -y espeak-ng
espeak-ng -v en-us -w speech.wav "Hello from the lip sync test. Animation is timing."
rhubarb/Rhubarb-Lip-Sync-1.14.0-Linux/rhubarb -f json -o lipsync.json speech.wav
```

Result: 15 mouth cues from 0.00 s to 3.39 s, with letter-coded shapes (A to H and X).

Gotcha: the zip extracts into a versioned folder, so the binary path includes that folder.

## 6. Expert knowledge that transfers

These apply whichever tool you choose. Each maps to a spec field or a check in §8.

1. **Timing and spacing come before drawing.** The Disney principles (anticipation, follow-through, overlapping action, squash and stretch, arcs, slow in and slow out) are the working vocabulary; see Thomas and Johnston, *The Illusion of Life*. In code they become easing curves, frame offsets, and keyframe patterns. The examples use `BEZIER` in bpy, `power2.out` and `power1.inOut` in GSAP, and `easeInOutExpo` in Motion Canvas.
2. **Frame rate and holds are creative decisions.** Film runs at 24 fps. Limited animation holds each drawing for two frames ("on twos"), giving 12 drawings per second. Set `fps` and the hold pattern up front.
3. **Animatic first.** Make a rough, timed version to lock timing, then polish. The `3d-animation-short-generator` skill follows this order.
4. **Staging.** One focal point, readable silhouettes, contrast with the background, and the camera as an editor: cut or move with intent. In code, keep camera and focus targets in the spec.
5. **Audio drives timing.** Derive mouth shapes from dialogue with Rhubarb and beats from music. Convert every cue to frames before composing, and keep the spec in frames rather than seconds.
6. **Reproducibility is version discipline.** Pin the tools: `bpy==5.2.2` on Python 3.13, `hyperframes@0.8.146`, `@motion-canvas/*@3.17.2` with `vite@^5`, `gsap@3.14.2`, `manim==0.22.0`. Fix seeds. Hash decoded pixels, not files. Store the spec, not the `.blend`. §3 shows this working.
7. **One color pipeline, stated in the spec.** These examples use sRGB throughout.
8. **Licenses decide what you can ship.** bpy is GPL-3.0 per its PyPI metadata, so check obligations before distributing a bpy-based product. Motion Canvas, Manim, Rhubarb, lottie-web, and blender-mcp are MIT. HyperFrames and MediaPipe are Apache-2.0. Remotion has tiered terms (§4). Asset libraries such as Sketchfab carry per-asset licenses.
9. **Choose the tool by what must be reproducible and what must look hand-made.** Code-first tools (bpy, Motion Canvas, HyperFrames) are reproducible. A hand-drawn look comes from a deliberate style layer, such as p5.brush in ClaudeAnimationBase or the animation-studio plugin.

Failure modes seen in this work, so a future build avoids them:
- Stray dev servers hold ports and serve stale projects.
- CDN script tags fail silently in sandboxes. Vendor them.
- A Python minor-version mismatch breaks wheels: bpy 5.2 needs 3.13, and manimpango needs 3.12 here.
- Current Chromium builds dropped the old headless mode. Use the new headless or chrome-for-testing modes.
- Blender 5.x changed the action API. Check the version before copying snippets.

## 7. Recommendation and build plan

**Recommended architecture.** The spec is the source of truth. Compile it to renders:
- **3D shots:** bpy (§5.1), packaged as the `bpy-animation` skill in §8.
- **2D motion graphics:** choose one of HyperFrames (HTML, suited to agents and web-native looks), Motion Canvas (TypeScript generators, suited to precise explainers), or Remotion (React; check the license first).
- **Math and diagrams:** Manim.
- **Lip sync and audio timing:** Rhubarb, plus the audio tools in HyperFrames if needed.
- **Muxing:** FFmpeg.
- **Interactive exploration only:** the Blender MCP add-on. Keep production in scripts.

**Build order.**
1. Build `bpy-animation` (§8). It is the most reproducible route and needs no paid services.
2. Choose the 2D stack. This is your call: Motion Canvas if you want TypeScript and generator timelines, HyperFrames if you want HTML that agents can write and that renders in Chromium, or Remotion if your team works in React and the license fits.
3. Add audio: Rhubarb for mouth shapes, then beat detection with the HyperFrames `beats` command or your own analysis.
4. When you share `animated-short`, merge its conventions into the spec format.

## 8. Build blueprint: the `bpy-animation` skill

A future agent should be able to build this skill from this section and Appendix A. Create `skills/bpy-animation/SKILL.md`, `skills/bpy-animation/scripts/render_scene.py` (copied from `examples/bpy/render_scene.py`), and `skills/bpy-animation/examples/spec.example.json`. Where the skill lives, either `.claude/skills/` in this repo or a claude.ai upload, is your decision.

### 8.1 Spec format (JSON)

| Field | Type | Meaning |
|---|---|---|
| `fps` | int | Frames per second, written to the video |
| `frames` | int | Total frames, rendered as 1 through `frames` |
| `resolution` | [int, int] | Width and height in pixels |
| `samples` | int | Cycles samples per pixel on CPU |
| `seed` | int | Cycles seed, fixed for reproducibility |
| `output` | string | MP4 file name inside the output directory |
| `objects` | list | Each has `name`, `type` (`plane`, `cube`, or `sphere`), size or radius, `location`, `rotation_deg`, `color` (RGBA, 0 to 1), `interp` (`BEZIER`, `LINEAR`, or `CONSTANT`), and `keys` |
| `keys` | list | Each has `frame`, plus optional `location` and `rotation_deg` |
| `camera` | object | `location`, `rotation_deg` |
| `light` | object | `type` (for example `SUN`), `location`, `energy` |

To add a shape type, extend the `SHAPES` table in `render_scene.py`.

### 8.2 SKILL.md draft

```markdown
---
name: bpy-animation
description: Build reproducible 3D animation renders from a JSON scene spec using Blender's Python module (bpy 5.2.x). Use when the user wants keyframed 3D shots or a repeatable, code-driven animation pipeline instead of GUI editing. Produces PNG frames, an H.264 MP4, and a manifest with per-frame pixel hashes. Not for one-off GUI modeling or photoreal live action.
---

# bpy-animation

## Requirements
- Python 3.13 venv with `bpy==5.2.2` (`pip install bpy==5.2.2`). Other bpy versions need different Python versions and have different APIs.
- `ffmpeg` with libx264 on PATH.

## Workflow
1. Write `spec.json` with every value the shot needs. The schema is the spec format in the build blueprint. Do not hand-edit a `.blend` file.
2. Run `python scripts/render_scene.py spec.json out/<name>`.
3. Check the output. The `frame_NNNN.png` count equals `frames`. `ffprobe` reports the expected fps and size. `manifest.json` records `bpy_version` and `spec_sha256`.
4. Reproduce by running again into a second directory and comparing the per-frame hashes in both manifests.
5. Add audio with ffmpeg by muxing an AAC track into the MP4. For dialogue, derive mouth cues with Rhubarb first.
6. Review by building a contact sheet of frames and checking timing, silhouettes, and framing.

## Rules
- Use `BEZIER` for natural motion, `LINEAR` for mechanical motion, and `CONSTANT` for holds.
- Hash decoded pixels, not PNG bytes. Metadata chunks differ between runs.
- Keep the MCP add-on out of production. It executes arbitrary Python.

## Known gotchas
- Blender 5.x layered actions: reach keyframes with `action.layers[0].strips[0].channelbag(action.slots[0]).fcurves`.
- Cycles runs on CPU without a GPU. EEVEE needs an OpenGL context and is not used here.
- Reproducibility was verified on one machine only.
```

### 8.3 Test plan
1. `pip install bpy==5.2.2` succeeds on Python 3.13, and `import bpy` works.
2. The example spec renders 48 frames and an MP4 at 480×270, 24 fps, with 48 frames.
3. Two runs produce identical frame hashes and an identical MP4 SHA-256 on the same machine.
4. Bad inputs fail clearly. An unknown shape type or a keyframe without `frame` raises `KeyError`. This has not been tested yet.

### 8.4 Next steps
- Add a `contact_sheet.py` helper using ffmpeg's `tile` filter.
- Add an audio mux helper.
- Add a schema validator for the spec.

## 9. Not verified, and why

- Houdini, Unreal Engine, and Cascadeur: not installable or too heavy for the sandbox.
- Mixamo: needs an Adobe account and the browser UI.
- Rive authoring: the `.riv` editor is a GUI.
- The Blender GUI add-on and `execute_blender_code` against a live Blender session.
- The claude.ai plugins `animation-studio` and `Sticklore`: no public source was found, and neither was installed.
- The claude.ai skill `3d-animation-short-generator`: its registry description was checked, not its full contents.
- Cross-machine determinism for bpy renders.
- Official sites marked † in §4: their links come from known domains and were not fetched from the sandbox.

## 10. Sources

- [bpy on PyPI](https://pypi.org/project/bpy/) (checked)
- [mcp-for-blender on PyPI](https://pypi.org/project/mcp-for-blender/) (checked)
- [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp) (repository reachable; MIT)
- [HyperFrames repository](https://github.com/heygen-com/hyperframes) (reachable; Apache-2.0)
- [HyperFrames on Claude](https://claude.com/plugins/hyperframes) (checked)
- [Motion Canvas repository](https://github.com/motion-canvas/motion-canvas) (reachable; MIT)
- [Remotion repository](https://github.com/remotion-dev/remotion) (reachable; tiered license, see its LICENSE.md)
- [Manim Community repository](https://github.com/ManimCommunity/manim) (reachable; MIT)
- [lottie-web repository](https://github.com/airbnb/lottie-web) (reachable; MIT)
- [Rhubarb Lip Sync repository](https://github.com/DanielSWolf/rhubarb-lip-sync) (reachable; MIT)
- [Revideo repository](https://github.com/redotvideo/revideo) (reachable)
- [Anthropic Directory: animation-studio](https://claude.com/marketplace/plugins/animation-studio) (redirect target)
- [Anthropic Directory: Sticklore](https://claude.com/marketplace/plugins/sticklore) (redirect target)
- [ClaudeAnimationBase write-up](https://alphasignal.ai/news/claudeanimationbase-turns-a-single-prompt-into-hand-painted-mp4-cartoons)
- [Higgsfield stickman skill](https://higgsfield.ai/skills/stickman-cartoon)
- [Remotion vs Motion Canvas comparison](https://www.remotion.dev/docs/compare/motion-canvas) (not fetched; surfaced by search)
- [Remotion vs Motion Canvas vs Revideo, 2026](https://www.pkgpulse.com/guides/remotion-vs-motion-canvas-vs-revideo-programmatic-video-2026) (not fetched; surfaced by search)
- Official sites marked † in §4 (not reachable from the sandbox)

## Appendix A: Example source files

Each file below is an exact copy of the file in `examples/`.

### A.1 `examples/bpy/render_scene.py`

```python
"""Spec-driven bpy animation: JSON spec -> keyframed scene -> PNG frames -> H.264 MP4.

Run with a bpy-capable interpreter (pip install bpy==5.2.2 on CPython 3.13):
    python render_scene.py spec.json OUTDIR
Writes OUTDIR/frame_NNNN.png, OUTDIR/<output>.mp4 and OUTDIR/manifest.json.
"""
import hashlib
import json
import math
import os
import subprocess
import sys

import bpy

spec_path, outdir = sys.argv[1], sys.argv[2]
os.makedirs(outdir, exist_ok=True)
with open(spec_path, "rb") as fh:
    raw = fh.read()
spec = json.loads(raw)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# Render settings: fixed sampling and seed so identical specs give identical pixels
scene.render.fps = spec["fps"]
scene.frame_start, scene.frame_end = 1, spec["frames"]
scene.render.resolution_x, scene.render.resolution_y = spec["resolution"]
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = spec.get("samples", 32)
scene.cycles.seed = spec.get("seed", 1)
scene.cycles.use_denoising = False

SHAPES = {
    "plane": lambda s: bpy.ops.mesh.primitive_plane_add(size=s.get("size", 10)),
    "cube": lambda s: bpy.ops.mesh.primitive_cube_add(size=s.get("size", 1)),
    "sphere": lambda s: bpy.ops.mesh.primitive_uv_sphere_add(radius=s.get("radius", 0.5), segments=64, ring_count=32),
}

for od in spec["objects"]:
    SHAPES[od["type"]](od)
    obj = bpy.context.active_object
    obj.name = od["name"]
    obj.location = od.get("location", [0, 0, 0])
    obj.rotation_euler = [math.radians(a) for a in od.get("rotation_deg", [0, 0, 0])]
    mat = bpy.data.materials.new(name=od["name"] + "_mat")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = od.get("color", [0.8, 0.8, 0.8, 1])
    obj.data.materials.append(mat)
    for key in od.get("keys", []):
        obj.location = key.get("location", obj.location)
        if "rotation_deg" in key:
            obj.rotation_euler = [math.radians(a) for a in key["rotation_deg"]]
        obj.keyframe_insert(data_path="location", frame=key["frame"])
        obj.keyframe_insert(data_path="rotation_euler", frame=key["frame"])
    if od.get("keys"):
        action = obj.animation_data.action
        for fc in action.layers[0].strips[0].channelbag(action.slots[0]).fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = od.get("interp", "BEZIER")

cam = spec["camera"]
bpy.ops.object.camera_add(location=cam["location"], rotation=[math.radians(a) for a in cam["rotation_deg"]])
scene.camera = bpy.context.active_object
lt = spec["light"]
bpy.ops.object.light_add(type=lt["type"], location=lt["location"])
bpy.context.active_object.data.energy = lt.get("energy", 3.0)

def pixel_sha256(png_path):
    # Hash decoded RGB pixels, not file bytes: PNG metadata chunks differ between runs
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", png_path, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        check=True, capture_output=True,
    ).stdout
    return hashlib.sha256(raw).hexdigest()


frame_hashes = {}
for f in range(1, spec["frames"] + 1):
    scene.frame_set(f)
    png = os.path.join(outdir, f"frame_{f:04d}.png")
    scene.render.filepath = png
    bpy.ops.render.render(write_still=True)
    frame_hashes[f"frame_{f:04d}.png"] = pixel_sha256(png)

mp4 = os.path.join(outdir, spec["output"])
subprocess.run(
    ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(spec["fps"]),
     "-i", os.path.join(outdir, "frame_%04d.png"),
     "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", mp4],
    check=True,
)

manifest = {
    "spec_sha256": hashlib.sha256(raw).hexdigest(),
    "bpy_version": bpy.app.version_string,
    "frames": frame_hashes,
    "output": spec["output"],
}
with open(os.path.join(outdir, "manifest.json"), "w") as fh:
    json.dump(manifest, fh, indent=2, sort_keys=True)
print("wrote", mp4, "and", len(frame_hashes), "frames")
```

### A.2 `examples/bpy/spec.example.json`

```json
{
  "fps": 24,
  "frames": 48,
  "resolution": [480, 270],
  "samples": 16,
  "seed": 7,
  "output": "bounce.mp4",
  "objects": [
    {"name": "Ground", "type": "plane", "size": 10, "color": [0.75, 0.75, 0.75, 1]},
    {"name": "Ball", "type": "sphere", "radius": 0.6, "location": [0, 0, 3], "color": [0.9, 0.35, 0.18, 1],
     "interp": "BEZIER",
     "keys": [
       {"frame": 1,  "location": [-2.5, 0, 3.0], "rotation_deg": [0, 0, 0]},
       {"frame": 12, "location": [0, 0, 0.6],    "rotation_deg": [0, 90, 0]},
       {"frame": 24, "location": [2.5, 0, 3.0],  "rotation_deg": [0, 180, 0]},
       {"frame": 36, "location": [0, 0, 0.6],    "rotation_deg": [0, 270, 0]},
       {"frame": 48, "location": [-2.5, 0, 3.0], "rotation_deg": [0, 360, 0]}
     ]}
  ],
  "camera": {"location": [6, -8, 4], "rotation_deg": [65, 0, 37]},
  "light": {"type": "SUN", "location": [4, -4, 8], "energy": 3.0}
}
```

### A.3 `examples/manim/sine_demo.py`

```python
import numpy as np
from manim import *


class SineDot(Scene):
    def construct(self):
        axes = Axes(x_range=[0, 2 * PI, PI / 2], y_range=[-1.5, 1.5, 1],
                    x_length=10, y_length=4)
        curve = axes.plot(lambda x: np.sin(x), color=BLUE)
        dot = Dot(axes.c2p(0, 0), color=YELLOW)
        title = Text("Sine traced by a moving dot", font_size=36).to_edge(UP)
        self.play(Create(axes), Create(curve), FadeIn(title))
        self.play(MoveAlongPath(dot, curve), run_time=3, rate_func=smooth)
        self.wait(0.5)
```

### A.4 `examples/hyperframes/index.html`

```html
<!doctype html>
<html lang="en" data-resolution="landscape">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <script src="vendor/gsap.min.js"></script>
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1920px; height: 1080px; overflow: hidden; background: #0a0a0a; }
      #root { width: 100%; height: 100%; position: relative; font-family: Inter, ui-sans-serif, system-ui, sans-serif; }
      #title { position: absolute; left: 0; right: 0; top: 380px; text-align: center; color: #f4f4f5; font-size: 96px; font-weight: 600; letter-spacing: -0.03em; }
      #ball { position: absolute; left: 260px; top: 760px; width: 120px; height: 120px; border-radius: 50%; background: #e4572e; }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="4" data-width="1920" data-height="1080">
      <h1 id="title" class="clip" data-start="0" data-duration="4" data-track-index="0">Keyframed in code</h1>
      <div id="ball" class="clip" data-start="0" data-duration="4" data-track-index="1"></div>
    </div>
    <script>
      const tl = gsap.timeline({ paused: true });
      tl.fromTo("#title", { opacity: 0, y: 24 }, { opacity: 1, y: 0, duration: 0.8, ease: "power2.out" }, 0);
      tl.fromTo("#ball", { x: 0 }, { x: 1400, duration: 3.0, ease: "power1.inOut" }, 0.5);
      window.__timelines["main"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>
```

### A.5 `examples/lottie/index.html`

```html
<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;background:#0a0a0a}#anim{width:400px;height:400px}</style></head>
<body><div id="anim"></div>
<script src="vendor/lottie.min.js"></script>
<script>
  const anim = lottie.loadAnimation({ container: document.getElementById('anim'), renderer: 'svg',
    loop: false, autoplay: false, animationData: {"v":"5.7.4","fr":30,"ip":0,"op":60,"w":400,"h":400,"nm":"sliding-dot","ddd":0,"assets":[],"markers":[],
 "layers":[{"ddd":0,"ind":1,"ty":4,"nm":"dot","sr":1,"ao":0,"ip":0,"op":60,"st":0,"bm":0,
  "ks":{"o":{"a":0,"k":100,"ix":11},"r":{"a":0,"k":0,"ix":10},
        "p":{"a":1,"k":[{"i":{"x":[0.5],"y":[1]},"o":{"x":[0.5],"y":[0]},"t":0,"s":[60,200,0]},{"t":60,"s":[340,200,0]}],"ix":2},
        "a":{"a":0,"k":[0,0,0],"ix":1},"s":{"a":0,"k":[100,100,100],"ix":6}},
  "shapes":[{"ty":"gr","it":[
     {"ty":"el","p":{"a":0,"k":[0,0],"ix":2},"s":{"a":0,"k":[80,80],"ix":3},"nm":"Ellipse"},
     {"ty":"fl","c":{"a":0,"k":[0.894,0.341,0.18,1],"ix":4},"o":{"a":0,"k":100,"ix":5},"r":1,"nm":"Fill"},
     {"ty":"tr","p":{"a":0,"k":[0,0],"ix":2},"a":{"a":0,"k":[0,0],"ix":1},"s":{"a":0,"k":[100,100],"ix":3},"r":{"a":0,"k":0,"ix":6},"o":{"a":0,"k":100,"ix":7},"sk":{"a":0,"k":0,"ix":4},"sa":{"a":0,"k":0,"ix":5},"nm":"Transform"}],
   "nm":"Group","np":2,"cix":2,"bm":0,"ix":1,"mn":"ADBE Vector Group","hd":false}]}]}
 });
  anim.goToAndStop(30, true); // frame 30 of 60, deterministic still for verification
</script></body></html>
```

### A.6 `examples/motion-canvas/package.json`

```json
{
  "name": "mc-demo",
  "private": true,
  "type": "module",
  "scripts": { "dev": "vite --port 9000 --strictPort --host 127.0.0.1" },
  "dependencies": {
    "@motion-canvas/core": "3.17.2",
    "@motion-canvas/2d": "3.17.2"
  },
  "devDependencies": {
    "@motion-canvas/ui": "3.17.2",
    "@motion-canvas/vite-plugin": "3.17.2",
    "@motion-canvas/ffmpeg": "3.17.2",
    "vite": "^5.4.0",
    "typescript": "^5.6.0",
    "playwright-core": "^1.50.0"
  }
}
```

### A.7 `examples/motion-canvas/vite.config.ts`

```typescript
import motionCanvasModule from '@motion-canvas/vite-plugin';
import ffmpegModule from '@motion-canvas/ffmpeg';
import {defineConfig} from 'vite';

// The published CJS builds expose the plugin factory on `.default`
const motionCanvas = (motionCanvasModule as any).default ?? motionCanvasModule;
const ffmpeg = (ffmpegModule as any).default ?? ffmpegModule;

export default defineConfig({
  plugins: [motionCanvas(), ffmpeg()],
});
```

### A.8 `examples/motion-canvas/render.mjs`

```javascript
// Drives the Motion Canvas editor headlessly: start dev server, click Render, wait for the MP4.
import {spawn} from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import {chromium} from 'playwright-core';

const root = process.cwd();
// Launch the local vite binary directly so SIGTERM stops the dev server itself, not just a wrapper
const server = spawn(path.join(root, 'node_modules', '.bin', 'vite'), ['--port', '9000', '--strictPort', '--host', '127.0.0.1'], {cwd: root, stdio: ['ignore', fs.openSync('vite.log', 'w'), fs.openSync('vite.log', 'a')]});
const sleep = ms => new Promise(r => setTimeout(r, ms));
const findMp4 = dir => {
  if (!fs.existsSync(dir)) return null;
  for (const e of fs.readdirSync(dir, {withFileTypes: true})) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) { const f = findMp4(p); if (f) return f; }
    else if (e.name.endsWith('.mp4')) return p;
  }
  return null;
};
try {
  await sleep(6000);
  const browser = await chromium.launch({executablePath: process.env.CHROMIUM_PATH || undefined, args: ['--no-sandbox', '--disable-gpu']});
  const page = await browser.newPage({viewport: {width: 1600, height: 900}});
  await page.goto('http://127.0.0.1:9000');
  await page.waitForSelector('main', {timeout: 120000});
  await sleep(2000);
  const btn = page.getByRole('button', {name: 'Render'}).first();
  await btn.click({timeout: 60000});
  console.log('clicked Render');
  const deadline = Date.now() + 400000;
  let mp4 = null;
  while (!mp4 && Date.now() < deadline) { await sleep(3000); mp4 = findMp4(path.join(root, 'output')); }
  if (!mp4) { await page.screenshot({path: path.join(root, 'editor-debug.png')}); console.log('no mp4 produced; screenshot saved'); }
  else console.log('MP4:', mp4);
  await browser.close();
} finally {
  server.kill('SIGTERM');
}
```

### A.9 `examples/motion-canvas/src/project.ts`

```typescript
import {makeProject} from '@motion-canvas/core';

import example from './scenes/example?scene';

export default makeProject({
  scenes: [example],
});
```

### A.10 `examples/motion-canvas/src/project.meta`

```json
{
  "version": 1,
  "shared": {
    "background": "rgb(20,20,20)",
    "range": [
      0,
      null
    ],
    "size": {
      "x": 1280,
      "y": 720
    },
    "audioOffset": 0
  },
  "preview": {
    "fps": 30,
    "resolutionScale": 1
  },
  "rendering": {
    "fps": 30,
    "resolutionScale": 1,
    "colorSpace": "srgb",
    "exporter": {
      "name": "@motion-canvas/ffmpeg",
      "options": {
        "fastStart": true,
        "includeAudio": true,
        "format": "mp4",
        "forceEncoding": "h264"
      }
    }
  }
}
```

### A.11 `examples/motion-canvas/src/scenes/example.tsx`

Copied from the Motion Canvas monorepo template (MIT) without changes.

```tsx
import {Rect, makeScene2D} from '@motion-canvas/2d';
import {
  all,
  createRef,
  easeInExpo,
  easeInOutExpo,
  waitFor,
  waitUntil,
} from '@motion-canvas/core';

export default makeScene2D(function* (view) {
  const rect = createRef<Rect>();

  view.add(
    <Rect ref={rect} size={320} radius={80} smoothCorners fill={'#f3303f'} />,
  );

  yield* waitUntil('rect');
  yield* rect().scale(2, 1, easeInOutExpo).to(1, 0.6, easeInExpo);
  rect().fill('#ffa56d');
  yield* all(rect().ripple(1));
  yield* waitFor(0.3);
});
```

### A.12 `examples/motion-canvas/src/motion-canvas.d.ts`

```typescript
/// <reference types="@motion-canvas/core/project" />
```

### A.13 `examples/motion-canvas/tsconfig.json`

```json
{
  "extends": "@motion-canvas/2d/tsconfig.project.json",
  "compilerOptions": {
    "types": ["node"]
  },
  "include": ["src"]
}
```

### A.14 `examples/mediapipe/pose_check.py`

```python
import sys
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision
from skimage import data
from PIL import Image, ImageDraw

img = data.astronaut()  # bundled sample photo in scikit-image; RGB uint8
options = vision.PoseLandmarkerOptions(
    base_options=mp_python.BaseOptions(model_asset_path="pose_landmarker_lite.task"),
    running_mode=vision.RunningMode.IMAGE,
    num_poses=1,
)
with vision.PoseLandmarker.create_from_options(options) as landmarker:
    result = landmarker.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(img)))
n = len(result.pose_landmarks)
print("mediapipe", mp.__version__, "| poses detected:", n)
if n:
    pil = Image.fromarray(img).convert("RGB")
    d = ImageDraw.Draw(pil)
    h, w = img.shape[:2]
    pts = [(int(l.x * w), int(l.y * h)) for l in result.pose_landmarks[0]]
    for x, y in pts:
        d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(255, 80, 40))
    pil.save("pose_overlay.png")
    print("nose landmark (px):", pts[0], "| landmarks:", len(pts), "| overlay: pose_overlay.png")
```
