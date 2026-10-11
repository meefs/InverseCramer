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
