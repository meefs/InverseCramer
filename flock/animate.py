"""M2/M3: the flight. Swifts (the SVG prototile) flutter in, land in their warped slots, and the
finished frame is the QA-passed stereogram. Later the hidden gull beats its wings.

    python -m flock.animate <builddir> <shard> <nshards>     -> <builddir>/segments/seg_XX.mp4
    python -m flock.animate <builddir> sheet                 -> sprite + frame review sheet
"""
import math
import subprocess
import sys
import time
from pathlib import Path

import cairocffi as cairo
import numpy as np

from common import tess
from flock import depth as D
from flock import pattern, stereo, still
from flock import timeline as TL

W, H = 1920, 1080
FLAP_POSES = (1.0, 0.45, -0.45, 0.45)   # wings up, level, down, level - held on twos at 12 fps


def background():
    """Two-tone wash behind the empty slots: lavender to mint, top to bottom."""
    top = np.array(tess.shade(tess.hex_rgb("#9974de"), 0.72, -0.1))
    bot = np.array(tess.shade(tess.hex_rgb("#6aec7c"), 0.70, -0.1))
    t = np.linspace(0, 1, H)[:, None, None]
    return ((1 - t) * top + t * bot) * np.ones((1, W, 1))


class Film:
    def __init__(self, build):
        self.build = Path(build)
        core = np.load(self.build / "core.npz")
        self.final = core["img"]
        self.cell = core["cell"].astype(np.float32)
        self.ids = core["ids"]
        self.sched = TL.landing_schedule(core["inst"])
        TL.write_audio_cues(self.sched, self.build / "cues.json")
        self.bg = (background() * 255).astype(np.uint8)
        self.lins = pattern.class_linear(still.P)
        self.ramps = pattern.ramps()
        self.n_frames = int(round(TL.DURATION * TL.FPS))
        self._flap_cache = {}

    # ---- sprites -------------------------------------------------------------------------------
    SPR_RES = 110  # px per prototile unit in the cached sprite

    def _build_sprites(self):
        """Per colour class: a raster swift in prototile units. The twisted outline leaves an empty
        middle (winding number 0), so that hole is filled with a pale belly tint and gets the eye."""
        from scipy.ndimage import binary_fill_holes, center_of_mass
        pts = tess.bezier_points()
        lo = pts.min(0) - 0.12
        hi = pts.max(0) + 0.12
        r = self.SPR_RES
        w, h = (np.ceil((hi - lo) * r)).astype(int)
        self.spr_origin = lo
        self.sprites, self.shadows = [], []
        for c in range(4):
            surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
            ctx = cairo.Context(surf)
            m = cairo.Matrix(r, 0, 0, r, -lo[0] * r, -lo[1] * r)
            ctx.save(); ctx.transform(m); tess.cairo_path(ctx); ctx.restore()
            ctx.set_source_rgb(1, 1, 1)
            ctx.fill_preserve()
            ctx.set_line_width(0.05 * r)  # the outline seals the twisted middle so it counts as a hole
            ctx.stroke()
            surf.flush()
            a = np.frombuffer(surf.get_data(), np.uint8).reshape(h, surf.get_stride() // 4, 4)[:, :w, 3] > 127
            hole = binary_fill_holes(a) & ~a
            dark, base, light = self.ramps[c]
            belly = tess.shade(base, 0.40, 0.1)
            buf = np.zeros((h, w, 4), np.uint8)
            buf[hole] = [int(belly[2] * 255), int(belly[1] * 255), int(belly[0] * 255), 255]
            spr = cairo.ImageSurface.create_for_data(memoryview(buf.reshape(-1)), cairo.FORMAT_ARGB32, w, h, w * 4)
            ctx = cairo.Context(spr)
            ctx.save(); ctx.transform(m); tess.cairo_path(ctx); ctx.restore()
            g = cairo.LinearGradient(-1.4, 0.45, 2.4, 0.55)
            g.add_color_stop_rgb(0, *dark)
            g.add_color_stop_rgb(0.45, *base)
            g.add_color_stop_rgb(1, *light)
            mi = cairo.Matrix(*m.as_tuple()); mi.invert(); g.set_matrix(mi)
            ctx.set_source(g)
            ctx.fill_preserve()
            ctx.set_source_rgb(0.06, 0.02, 0.09)
            ctx.set_line_width(0.028 * r)
            ctx.set_line_join(cairo.LINE_JOIN_ROUND)
            ctx.stroke()
            # eye on the belly, nudged toward the leading side
            cy, cx = center_of_mass(hole)
            ex, ey = cx, cy - 0.16 * r
            er = 0.15 * r
            ctx.arc(ex, ey, er, 0, 2 * math.pi)
            ctx.set_source_rgb(1, 0.98, 0.94); ctx.fill_preserve()
            ctx.set_source_rgb(0.06, 0.02, 0.09); ctx.set_line_width(0.02 * r); ctx.stroke()
            ctx.arc(ex + 0.3 * er, ey - 0.1 * er, 0.52 * er, 0, 2 * math.pi); ctx.fill()
            ctx.arc(ex + 0.45 * er, ey - 0.3 * er, 0.16 * er, 0, 2 * math.pi)
            ctx.set_source_rgb(1, 1, 1); ctx.fill()
            spr.flush()
            self._keep = getattr(self, "_keep", []) + [buf]
            self.sprites.append(spr)
            self.belly_centre = (np.array([cx, cy]) / r + lo)

    def _sprite_matrix(self, c, pos, rot, scale, f):
        L = self.lins[c]
        cr, sr = math.cos(rot), math.sin(rot)
        Rm = np.array([[cr, -sr], [sr, cr]])
        A = Rm @ (scale * L) @ np.diag([1.0, f])
        off = np.array(pos) - A @ self.belly_centre
        # local prototile units -> sprite pixels: (p - origin) * res ; compose device <- local <- sprite px
        S = A / self.SPR_RES
        o = off + A @ self.spr_origin
        return cairo.Matrix(S[0, 0], S[1, 0], S[0, 1], S[1, 1], o[0], o[1])

    def draw_swift(self, ctx, c, pos, rot, scale, f):
        if not hasattr(self, "sprites"):
            self._build_sprites()
        m = self._sprite_matrix(c, pos, rot, scale, f)
        inv = cairo.Matrix(*m.as_tuple()); inv.invert()
        sp = cairo.SurfacePattern(self.sprites[c])
        sp.set_filter(cairo.FILTER_GOOD)
        # soft shadow, then the swift
        shadow = cairo.Matrix(1, 0, 0, 1, -(10 + 14 * scale), -(16 + 20 * scale)).multiply(inv)
        sp.set_matrix(shadow)
        ctx.set_source_rgba(0.22, 0.05, 0.30, 0.16)
        ctx.mask(sp)
        sp.set_matrix(inv)
        ctx.set_source(sp)
        ctx.paint()

    # ---- frames --------------------------------------------------------------------------------
    def flying_state(self, i, t, k):
        s = self.sched
        p = (t - s["t_start"][i]) / (s["t_land"][i] - s["t_start"][i])
        e = 1 - (1 - p) ** 1.8
        P0 = s["entry"][i]
        P2 = np.array([s["cx"][i], s["cy"][i]])
        d = P2 - P0
        P1 = (P0 + P2) / 2 + s["bend"][i] * np.array([-d[1], d[0]])
        pos = (1 - e) ** 2 * P0 + 2 * (1 - e) * e * P1 + e * e * P2
        vel = 2 * (1 - e) * (P1 - P0) + 2 * e * (P2 - P1)
        c = int(s["cls"][i])
        a_c = math.atan2(self.lins[c][1, 0], self.lins[c][0, 0])
        th = math.atan2(vel[1], vel[0])
        cands = [((th + sgn * math.pi / 2 - a_c + math.pi) % (2 * math.pi)) - math.pi for sgn in (1, -1)]
        target = min(cands, key=abs)
        settle = np.clip((p - 0.72) / 0.28, 0, 1)
        settle = settle * settle * (3 - 2 * settle)
        rot = target * (1 - settle)
        scale = 0.42 + 0.2 * p ** 3
        f = 0.75 if p > 0.85 else FLAP_POSES[(k + int(s["flap_phase"][i])) % 4]
        return c, pos, rot, scale, f

    def gull_frame(self, t):
        fl = TL.flap_at(t)
        if fl == 0.0:
            return self.final
        key = round(fl, 4)
        if key not in self._flap_cache:
            z = D.gull_depth(fl, scale=still.GULL_SCALE)
            img, _, _ = stereo.stereogram(z, None, self.ids, still.P, still.SS, cell_blur=self.cell)
            self._flap_cache = {key: still.u8(img)}
        return self._flap_cache[key]

    def frame(self, k):
        t = k / TL.FPS
        s = self.sched
        if t >= TL.LAST_LAND + 1 / TL.FPS:
            out = self.gull_frame(t).copy()
        else:
            landed = s["t_land"] <= t + 1e-9
            mask = landed[s["labels"]]
            out = np.where(mask[..., None], self.final, self.bg)
            # stop-motion settle: swifts that landed this frame flash a touch brighter
            fresh = landed & (s["t_land"] > t - 1 / TL.FPS + 1e-9)
            if fresh.any():
                fm = fresh[s["labels"]]
                out[fm] = np.clip(out[fm].astype(np.int16) + 28, 0, 255).astype(np.uint8)
            flying = np.where((s["t_start"] <= t) & (s["t_land"] > t + 1e-9))[0]
            if len(flying):
                out = self._draw_flyers(out, flying, t, k)
        if t >= TL.GUIDE_DOTS_AT:
            out = self._guide_dots(out, min(1.0, (t - TL.GUIDE_DOTS_AT) * 2))
        return out

    def _draw_flyers(self, rgb, flying, t, k):
        buf = np.empty((H, W, 4), np.uint8)
        buf[..., 0] = rgb[..., 2]
        buf[..., 1] = rgb[..., 1]
        buf[..., 2] = rgb[..., 0]
        buf[..., 3] = 255
        surf = cairo.ImageSurface.create_for_data(memoryview(buf.reshape(-1)), cairo.FORMAT_ARGB32, W, H, W * 4)
        ctx = cairo.Context(surf)
        states = [self.flying_state(i, t, k) for i in flying]
        for st in sorted(states, key=lambda q: q[3]):  # nearer (bigger) swifts on top
            self.draw_swift(ctx, *st)
        surf.flush()
        return np.ascontiguousarray(buf[..., [2, 1, 0]])

    def _guide_dots(self, rgb, alpha):
        out = rgb.copy()
        yy, xx = np.mgrid[0:60, 0:W]
        for x0 in (W / 2 - still.P / 2, W / 2 + still.P / 2):
            d = np.hypot(xx - x0, yy - 34)
            ring = np.clip(13 - d, 0, 1) * alpha
            core = np.clip(9 - d, 0, 1) * alpha
            seg = out[:60].astype(np.float32)
            seg = seg * (1 - ring[..., None]) + 255 * ring[..., None]
            seg = seg * (1 - core[..., None]) + 20 * core[..., None]
            out[:60] = seg.astype(np.uint8)
        return out


def encode(film, shard, nshards):
    seg = film.build / "segments"
    seg.mkdir(exist_ok=True)
    per = math.ceil(film.n_frames / nshards)
    ks = range(shard * per, min(film.n_frames, (shard + 1) * per))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(TL.FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "18",
           "-pix_fmt", "yuv420p", "-g", str(2 * TL.FPS), str(seg / f"seg_{shard:02d}.mp4")]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    for k in ks:
        proc.stdin.write(film.frame(k).tobytes())
    proc.stdin.close()
    proc.wait()
    print(f"shard {shard}/{nshards}: frames {ks.start}-{ks.stop - 1} in {time.time() - t0:.1f}s")


def sheet(film):
    from PIL import Image
    times = [1.0, 4.0, 8.0, 12.0, 14.5, 30.4]
    ims = [Image.fromarray(film.frame(int(t * TL.FPS))).resize((640, 360)) for t in times]
    out = Image.new("RGB", (1280, 360 * 3), "white")
    for i, im in enumerate(ims):
        out.paste(im, ((i % 2) * 640, (i // 2) * 360))
    out.save(film.build / "anim_sheet.png")


if __name__ == "__main__":
    film = Film(sys.argv[1])
    if sys.argv[2] == "sheet":
        sheet(film)
    else:
        encode(film, int(sys.argv[2]), int(sys.argv[3]))
