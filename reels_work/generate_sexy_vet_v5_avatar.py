# -*- coding: utf-8 -*-
import os
import sys
import base64
import pathlib
import cv2
import numpy as np
from google import genai

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

BASE_DIR = pathlib.Path(r"c:\IA\Edicion de videos")
WORK_DIR = BASE_DIR / "reels_work"
ENV_FILE = BASE_DIR / ".env"

for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.strip().startswith("#"):
        k, v = line.split("=", 1)
        os.environ[k.strip()] = v.strip().strip("\"'")

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

in_path = WORK_DIR / "vet_avatar_sexy_v4.png"
out_path = WORK_DIR / "vet_avatar_sexy_v5.png"

img = cv2.imread(str(in_path))

# Pre-warp the existing image in OpenCV first to create a genuine 38D bust expansion + narrow hourglass waist cinch,
# AND enhance 3D bust shading/cleavage contour, then pass to gemini-nano-banana-2.1 to refine photorealistic fabric & cleavage!
h, w = img.shape[:2]
map_x, map_y = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))

# 1. Bust expansion (38D volume) centered at left breast (395, 1340) and right breast (685, 1340) + outward chest curve
for bx, by, rx, ry, strength in [
    (400.0, 1330.0, 220.0, 240.0, 0.28),
    (680.0, 1330.0, 220.0, 240.0, 0.28),
    (540.0, 1320.0, 340.0, 250.0, 0.16),
]:
    dx = (map_x - bx) / rx
    dy = (map_y - by) / ry
    r2 = dx * dx + dy * dy
    mask = r2 < 1.0
    factor = 1.0 - strength * ((1.0 - r2[mask]) ** 2)
    map_x[mask] = bx + (map_x[mask] - bx) * factor
    map_y[mask] = by + (map_y[mask] - by) * factor

# 2. Hourglass waist cinch (pull inward toward x=540 around y=1660..1860)
waist_y = 1720.0
waist_ry = 240.0
dy_w = (map_y - waist_y) / waist_ry
w_mask = (np.abs(dy_w) < 1.0) & (np.abs(map_x - 540.0) < 380.0)
w_profile = (1.0 - dy_w[w_mask] ** 2) ** 2
# Pull waist inward by 22%
map_x[w_mask] = 540.0 + (map_x[w_mask] - 540.0) * (1.0 + 0.24 * w_profile)

warped = cv2.remap(img, map_x, map_y, interpolation=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT_101)
_, buf = cv2.imencode(".jpg", warped, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
warped_b64 = base64.b64encode(buf.tobytes()).decode("utf-8")

prompt = (
    "Enhance this portrait while keeping her exact face, emerald-green eyes, luscious lips, dark wavy hair, and clinic "
    "background 100% identical. Replace her loose top with a skin-tight, body-hugging deep V-neck stretch bodycon top "
    "in the same deep-teal color (with a stethoscope around her neck) that tightly contours her full, voluptuous 38D bust "
    "(with clear 3D breast volume, natural cleavage in the deeper V-neckline, and defined under-bust shadow) and her "
    "narrow, curvy hourglass waist. Do NOT make the top loose or boxy; make the fabric cling to her 38D bust and tiny waist."
)

print("[AVATAR V5] Aplicando geometría 38D + cintura reloj de arena y refinando con gemini-nano-banana-2.1...")
res = client.interactions.create(
    model="gemini-nano-banana-2.1",
    input=[
        {"type": "image", "data": warped_b64, "mime_type": "image/jpeg"},
        {"type": "text", "text": prompt},
    ],
    response_format={"type": "image", "mime_type": "image/jpeg", "aspect_ratio": "9:16"},
)

if res.output_image and res.output_image.data:
    img_bytes = base64.b64decode(res.output_image.data)
    out_path.write_bytes(img_bytes)
    print(f"  -> Retrato V5 guardado en {out_path} ({len(img_bytes)} bytes)")
else:
    raise RuntimeError("No se recibio output_image")
