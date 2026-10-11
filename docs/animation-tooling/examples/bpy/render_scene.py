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
