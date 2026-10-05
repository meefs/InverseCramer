"""Painter's Order: the picture. A four-beam oscilloscope drawing in light on the tessellation's lattice.

Every lit tile is a voice sounding at a lattice site (its pitch); brightness is the very envelope the
audio uses, and the bright comet head is where that voice's beam is at the frame's instant (it strobes
against the 24 fps frame rate, so each pitch crawls at its own apparent speed). Released tiles keep a
phosphor afterglow, so the screen accumulates the chorale's walk. At the end the camera pulls back and
the walk is filled in: unvisited tiles in muted shades underneath, visited tiles stacked in the order
the music first reached them. The music chooses the painter's order of the overlapping tiles.

    python -m painters_order.film <builddir> <shard> <nshards>
    python -m painters_order.film <builddir> sheet
"""
import json
import math
import subprocess
import sys
import time
from pathlib import Path

import cairocffi as cairo
import numpy as np
from scipy.ndimage import gaussian_filter, zoom

from common import tess
from painters_order import music as M

W, H, FPS = 1920, 1080, 24
FOLLOW_SCALE = 1.75
AFTERGLOW_FLOOR, AFTERGLOW_TAU = 0.11, 2.2
INK = (0.031, 0.020, 0.047)


def palette():
    out = []
    for col, _ in tess.CLASSES:
        base = tess.hex_rgb(col)
        out.append(dict(base=base, core=tuple(0.45 * b + 0.55 for b in base),
                        dark=tess.shade(base, -0.45, 0.25), light=tess.shade(base, 0.4, 0.2),
                        mute_dark=tess.shade(base, -0.72, -0.35), mute_light=tess.shade(base, -0.38, -0.45)))
    return out


class Film:
    def __init__(self, build):
        self.build = Path(build)
        self.s = json.loads((self.build / "score.json").read_text())
        self.n_frames = int(self.s["duration"] * FPS)
        self.pal = palette()
        self.lins = [lin for _, lin in tess.CLASSES]
        # every (voice, note) that ever sounds, including the ghost and the coda
        self.events = []
        for v, notes in enumerate(self.s["voices"]):
            for nt in notes:
                self.events.append(dict(nt, voice=v, kind="voice"))
        for kind in ("ghost", "coda"):
            for nt in self.s[kind]:
                self.events.append(dict(nt, kind=kind))
        for e in self.events:
            e["stream"] = [dict(t0=e["t0"], t1=e["t1"], freq=e["freq"])]
        self.first_visit = {}
        for e in sorted(self.events, key=lambda e: e["t0"]):
            self.first_visit.setdefault((e["voice"], tuple(e["site"])), e["t0"])
        self._camera_path()
        self._reveal = None

    # ---- camera ---------------------------------------------------------------------------------
    def _camera_path(self):
        ts = np.arange(self.n_frames) / FPS
        cx = np.zeros((self.n_frames, 2))
        pts = np.array([M.site_world(e["site"]) for e in self.events])
        lo, hi = pts.min(0) - 260, pts.max(0) + 260
        over_c = (lo + hi) / 2
        over_s = min(W / (hi - lo)[0], H / (hi - lo)[1])
        c = M.site_world([0, 0]) + 0.5 * (tess.LAT_A + tess.LAT_B)
        a = 1 - math.exp(-1 / (FPS * 0.9))
        out_c, out_s = [], []
        for k, t in enumerate(ts):
            w_sum, acc = 0.0, np.zeros(2)
            for v, notes in enumerate(self.s["voices"]):
                nt = M.note_at(notes, t)
                if nt is not None:
                    w = 1.0 + (v == 0)
                    acc += w * (M.site_world(nt["site"]) + 0.5 * (tess.LAT_A + tess.LAT_B))
                    w_sum += w
            target = acc / w_sum if w_sum else c
            c = c + a * (target - c)
            z = np.clip((t - self.s["final_start"]) / 2.6, 0, 1)
            z = z * z * (3 - 2 * z)
            out_c.append((1 - z) * c + z * over_c)
            out_s.append(math.exp((1 - z) * math.log(FOLLOW_SCALE) + z * math.log(over_s)))
        self.cam_c, self.cam_s = np.array(out_c), np.array(out_s)
        self.over = (over_c, over_s)

    def _matrix(self, k_or_cam, L, origin):
        c, s = k_or_cam
        A = s * L
        o = s * (origin - c) + np.array([W / 2, H / 2])
        return cairo.Matrix(A[0, 0], A[1, 0], A[0, 1], A[1, 1], o[0], o[1])

    # ---- brightness -----------------------------------------------------------------------------
    def glow(self, e, t):
        """Sounding: the audio envelope of this note. Released: phosphor afterglow down to a faint burn-in."""
        if t < e["t0"]:
            return 0.0
        a = float(M.envelope(e["stream"], np.array([t]))[0])
        if t > e["t1"]:
            after = AFTERGLOW_FLOOR + (0.5 - AFTERGLOW_FLOOR) * math.exp(-(t - e["t1"]) / AFTERGLOW_TAU)
            a = max(a, after)
        return a * (0.75 if e["kind"] == "ghost" else 1.0)

    def phase(self, notes, t):
        ph = 0.0
        for k, nt in enumerate(notes):
            end = notes[k + 1]["t0"] if k + 1 < len(notes) else 1e9
            if t > nt["t0"]:
                ph += nt["freq"] * (min(t, end) - nt["t0"])
        return ph

    # ---- layers ---------------------------------------------------------------------------------
    def _background(self, ctx, cam):
        g = cairo.LinearGradient(0, 0, 0, H)
        g.add_color_stop_rgb(0, 0.055, 0.027, 0.078)
        g.add_color_stop_rgb(1, 0.016, 0.039, 0.027)
        ctx.set_source(g)
        ctx.paint()
        # the lattice itself, as faint graticule dots (a scope's grid, laid on the Tonnetz)
        c, s = cam
        inv = np.linalg.inv(np.stack([tess.LAT_A, tess.LAT_B], 1))
        corners = np.array([[0, 0], [W, 0], [0, H], [W, H]], float)
        world = (corners - [W / 2, H / 2]) / s + c - tess.PIVOT
        ij = world @ inv.T
        ctx.set_source_rgba(0.75, 0.7, 0.85, 0.16)
        r = max(1.2, 1.6 * s / FOLLOW_SCALE)
        for i in range(int(ij[:, 0].min()) - 1, int(ij[:, 0].max()) + 2):
            for j in range(int(ij[:, 1].min()) - 1, int(ij[:, 1].max()) + 2):
                p = s * (M.site_world((i, j)) - c) + [W / 2, H / 2]
                if -10 < p[0] < W + 10 and -10 < p[1] < H + 10:
                    ctx.arc(p[0], p[1], r, 0, 2 * math.pi)
                    ctx.fill()

    def _tile_path(self, ctx, cam, voice, site):
        m = self._matrix(cam, self.lins[voice], M.site_world(site))
        ctx.save()
        ctx.transform(m)
        tess.cairo_path(ctx)
        ctx.restore()
        return m

    def _two_tone(self, m, c0, c1, c2):
        g = cairo.LinearGradient(-1.4, 0.45, 2.4, 0.55)
        g.add_color_stop_rgb(0, *c0)
        g.add_color_stop_rgb(0.45, *c1)
        g.add_color_stop_rgb(1, *c2)
        mi = cairo.Matrix(*m.as_tuple())
        mi.invert()
        g.set_matrix(mi)
        return g

    def reveal_layer(self):
        """The filled tessellation at the overview camera, in the music's painter's order (cached)."""
        if self._reveal is not None:
            return self._reveal
        cam = self.over
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        ctx = cairo.Context(surf)
        c, s = cam
        inv = np.linalg.inv(np.stack([tess.LAT_A, tess.LAT_B], 1))
        corners = np.array([[0, 0], [W, 0], [0, H], [W, H]], float)
        ij = ((corners - [W / 2, H / 2]) / s + c - tess.PIVOT) @ inv.T
        visited = self.first_visit
        unvisited = []
        for v in (3, 2, 1, 0):
            for i in range(int(ij[:, 0].min()) - 4, int(ij[:, 0].max()) + 5):
                for j in range(int(ij[:, 1].min()) - 4, int(ij[:, 1].max()) + 5):
                    if (v, (i, j)) not in visited:
                        unvisited.append((v, i * 1.0 + j * 0.37, (i, j)))
        unvisited.sort(key=lambda q: ((3, 2, 1, 0).index(q[0]), q[1]))
        lw = max(1.0, 1.4 * s / FOLLOW_SCALE)
        for v, _, site in unvisited:
            m = self._tile_path(ctx, cam, v, site)
            p = self.pal[v]
            ctx.set_source(self._two_tone(m, p["mute_dark"], p["mute_light"], p["mute_light"]))
            ctx.fill_preserve()
            ctx.set_source_rgb(*INK)
            ctx.set_line_width(lw)
            ctx.stroke()
        for (v, site), _ in sorted(visited.items(), key=lambda kv: kv[1]):
            m = self._tile_path(ctx, cam, v, site)
            p = self.pal[v]
            ctx.set_source(self._two_tone(m, p["dark"], p["base"], p["light"]))
            ctx.fill_preserve()
            ctx.set_source_rgb(*INK)
            ctx.set_line_width(lw)
            ctx.stroke()
        surf.flush()
        self._reveal = surf
        return surf

    def frame(self, k):
        t = k / FPS
        cam = (self.cam_c[k], self.cam_s[k])
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        ctx = cairo.Context(surf)
        self._background(ctx, cam)
        rv = np.clip((t - (self.s["reveal"] - 0.6)) / 2.8, 0, 1)
        if rv > 0:
            ctx.set_source_surface(self.reveal_layer(), 0, 0)
            ctx.paint_with_alpha(rv * rv * (3 - 2 * rv))
        sc = cam[1] / FOLLOW_SCALE
        ctx.set_operator(cairo.OPERATOR_ADD)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        lit = []
        best = {}
        for e in self.events:
            g = self.glow(e, t)
            key = (e["voice"], tuple(e["site"]))
            if g > best.get(key, (0, None))[0]:
                best[key] = (g, e)
        for (v, site), (g, e) in sorted(best.items(), key=lambda kv: kv[1][0]):
            if g < 0.01:
                continue
            p = self.pal[v]
            m = self._tile_path(ctx, cam, v, site)
            ctx.set_source(self._two_tone(m, p["dark"], p["base"], p["light"]))
            ctx.save()
            ctx.clip_preserve()
            ctx.paint_with_alpha(0.10 * g * (1 - 0.6 * rv))
            ctx.restore()
            for width, alpha, col in ((16 * sc, 0.045, p["base"]), (6 * sc, 0.2, p["base"]), (max(1.2, 2.0 * sc), 0.95, p["core"])):
                ctx.set_source_rgba(*col, alpha * g)
                ctx.set_line_width(width)
                ctx.stroke_preserve()
            ctx.new_path()
            if g > 0.3 and e["t0"] <= t <= e["t1"] + 0.05:
                lit.append((v, e, g))
        # comet heads: where each sounding beam is at this instant
        for v, e, g in lit:
            stream = self.s["voices"][v] if e["kind"] == "voice" else e["stream"]
            ph = self.phase(stream, t)
            trail = ph - np.linspace(0, 0.22, 28)
            pts = tess.trace(trail) @ (cam[1] * self.lins[v]).T + cam[1] * (M.site_world(e["site"]) - cam[0]) + [W / 2, H / 2]
            for q, (x, y) in enumerate(pts):
                a = (1 - q / len(pts)) ** 2 * g
                ctx.set_source_rgba(1, 1, 1, 0.55 * a)
                ctx.arc(x, y, (5.5 - 4 * q / len(pts)) * max(0.6, sc), 0, 2 * math.pi)
                ctx.fill()
        ctx.set_operator(cairo.OPERATOR_OVER)
        self._labels(ctx, cam, t, lit)
        self._cards(ctx, t)
        surf.flush()
        buf = np.frombuffer(surf.get_data(), np.uint8).reshape(H, W, 4)
        rgb = buf[..., [2, 1, 0]].astype(np.float32) / 255
        # bloom: the phosphor bleeds a little
        small = rgb[::4, ::4]
        bloom = zoom(gaussian_filter(small, (6, 6, 0)), (4, 4, 1), order=1)[:H, :W]
        out = 1 - (1 - rgb) * (1 - 0.85 * bloom)
        return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)

    def _labels(self, ctx, cam, t, lit):
        ctx.select_font_face("DejaVu Sans Mono", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        ctx.set_font_size(15)
        for v, e, g in lit:
            if e["kind"] == "coda":
                continue
            p = cam[1] * (M.site_world(e["site"]) - cam[0]) + [W / 2, H / 2]
            txt = f"{M.note_name(e['site'])}  {e['freq']:.1f} Hz"
            ctx.set_source_rgba(*self.pal[v]["core"], 0.85 * g)
            ctx.move_to(p[0] + 10, p[1] - 10 - 18 * v)
            ctx.show_text(txt)

    def _cards(self, ctx, t):
        def card(lines, t0, t1, y, sizes, backing=False):
            a = min(np.clip((t - t0) / 0.8, 0, 1), np.clip((t1 - t) / 0.8, 0, 1))
            if a <= 0:
                return
            if backing:
                h = sum(sizes) * 1.5 + 30
                ctx.rectangle(0, y - sizes[0] - 22, W, h)
                ctx.set_source_rgba(*INK, 0.72 * a)
                ctx.fill()
            yy = y
            for line, size in zip(lines, sizes):
                ctx.select_font_face("DejaVu Sans" if size < 40 else "DejaVu Serif", cairo.FONT_SLANT_NORMAL,
                                     cairo.FONT_WEIGHT_NORMAL if size < 40 else cairo.FONT_WEIGHT_BOLD)
                ctx.set_font_size(size)
                xb, _, tw, _, _, _ = ctx.text_extents(line)
                ctx.move_to(W / 2 - tw / 2 - xb, yy)
                ctx.set_source_rgba(0.95, 0.92, 1.0, 0.92 * a)
                ctx.show_text(line)
                yy += size * 1.5
        card(["Painter's Order", "a comma-pump chorale for four beams, traced from tessellation 15"], 0.4, 4.6, 140, [64, 24])
        d = self.s["drift_cents"]
        card([f"Six times round C, Am, Dm, G, in just intonation, every common tone held.",
              f"Home sank six syntonic commas ({d:.0f} cents) and walked {abs(self.s['home_final'][0])} fifths across the tiles.",
              "Every sound you heard was a tile, traced by a beam."],
             self.s["reveal"] + 1.2, self.s["duration"] - 0.2, H - 150, [26, 26, 26], backing=True)


def encode(film, shard, nshards):
    seg = film.build / "segments"
    seg.mkdir(exist_ok=True)
    per = math.ceil(film.n_frames / nshards)
    ks = range(shard * per, min(film.n_frames, (shard + 1) * per))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "18",
           "-pix_fmt", "yuv420p", "-g", str(2 * FPS), str(seg / f"seg_{shard:02d}.mp4")]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    for k in ks:
        proc.stdin.write(film.frame(k).tobytes())
    proc.stdin.close()
    proc.wait()
    print(f"shard {shard}/{nshards}: frames {ks.start}-{ks.stop - 1} in {time.time() - t0:.1f}s")


def sheet(film):
    from PIL import Image
    times = [2.5, 9.0, 24.0, 40.0, 46.0, 55.0]
    out = Image.new("RGB", (1280, 360 * 3))
    for i, t in enumerate(times):
        out.paste(Image.fromarray(film.frame(int(t * FPS))).resize((640, 360)), ((i % 2) * 640, (i // 2) * 360))
    out.save(film.build / "sheet.png")


if __name__ == "__main__":
    f = Film(sys.argv[1])
    if sys.argv[2] == "sheet":
        sheet(f)
    else:
        encode(f, int(sys.argv[2]), int(sys.argv[3]))
