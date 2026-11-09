import os
import cv2
import numpy as np
from google import genai
from google.genai import types

img = cv2.imread(r"c:\IA\Edicion de videos\reels_work\vet_avatar_sexy_v4.png")
h, w, _ = img.shape
print(f"Loaded vet_avatar_sexy_v4.png: {w}x{h}")

# Normalized coordinate grid u in [0, 1], v in [0, 1]
u_grid, v_grid = np.meshgrid(
    np.linspace(0.0, 1.0, w, dtype=np.float32),
    np.linspace(0.0, 1.0, h, dtype=np.float32)
)

# In vet_avatar_sexy_v4.png:
# Face center: u=0.50, v=0.35
# Neck/collarbone: u=0.50, v=0.49..0.55
# V-neck tip of original scrub: u=0.50, v=0.60
# Bust center: u=0.50, v=0.66
# Under-bust: v=0.74
# Waist center: v=0.83
# Hips: v=0.94

# 1. Strong 2D Radial Hourglass Warp in normalized coordinates
du = u_grid - 0.50

# Bust outward expansion + lift around v=0.665
bust_v_mask = np.exp(-((v_grid - 0.665) / 0.095)**2)
bust_u_mask = np.exp(-(du / 0.30)**2)
bust_mask = bust_v_mask * bust_u_mask
scale_u_bust = 1.0 - 0.36 * bust_mask
lift_v_bust = 0.018 * bust_mask * np.exp(-((v_grid - 0.70) / 0.06)**2)

# Waist inward cinch around v=0.835
waist_v_mask = np.exp(-((v_grid - 0.835) / 0.085)**2)
# Maximum cinch at the waist edges (|du| ~ 0.19)
waist_u_mask = np.exp(-((np.abs(du) - 0.19) / 0.11)**2)
scale_u_waist = 1.0 + 0.44 * waist_v_mask * waist_u_mask

# Hips outward flare around v=0.96
hips_v_mask = np.exp(-((v_grid - 0.96) / 0.07)**2)
hips_u_mask = np.exp(-((np.abs(du) - 0.23) / 0.12)**2)
scale_u_hips = 1.0 - 0.18 * hips_v_mask * hips_u_mask

total_scale_u = scale_u_bust * scale_u_waist * scale_u_hips
map_x = ((0.50 + du * total_scale_u) * w).astype(np.float32)
map_y = ((v_grid + lift_v_bust) * h).astype(np.float32)

sculpted = cv2.remap(img, map_x, map_y, interpolation=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

# 2. Paint 3D Bust Shading + Deep V-Neck Cleavage in Normalized Coordinates
guide = sculpted.copy().astype(np.float32)

# Sample skin tone from neck/chest (u=0.47..0.53, v=0.49..0.53)
y0, y1 = int(0.49 * h), int(0.53 * h)
x0, x1 = int(0.47 * w), int(0.53 * w)
skin_bgr = np.mean(sculpted[y0:y1, x0:x1].astype(np.float32), axis=(0, 1))
shadow_skin_bgr = skin_bgr * np.array([0.55, 0.58, 0.66], dtype=np.float32)
highlight_skin_bgr = np.clip(skin_bgr * 1.15, 0, 255)

# Deep V-neck skin opening from v=0.52 down to v=0.69
v_mask = np.zeros((h, w), dtype=np.float32)
pts_v = np.array([
    [int(0.41 * w), int(0.51 * h)],
    [int(0.59 * w), int(0.51 * h)],
    [int(0.54 * w), int(0.64 * h)],
    [int(0.50 * w), int(0.69 * h)],
    [int(0.46 * w), int(0.64 * h)],
], dtype=np.int32)
cv2.fillPoly(v_mask, [pts_v], 1.0)
v_mask = cv2.GaussianBlur(v_mask, (25, 25), 8)

for c in range(3):
    guide[:, :, c] = guide[:, :, c] * (1.0 - v_mask * 0.92) + skin_bgr[c] * (v_mask * 0.92)

# Central cleavage shadow crease + curved inner breast contours (u=0.50, v=0.56..0.69)
cleavage_mask = np.zeros((h, w), dtype=np.float32)
cv2.line(cleavage_mask, (int(0.50 * w), int(0.565 * h)), (int(0.50 * w), int(0.69 * h)), 1.0, thickness=max(6, int(0.012 * w)))
pts_left_c = np.array([
    [int(0.50 * w), int(0.63 * h)],
    [int(0.475 * w), int(0.585 * h)],
    [int(0.435 * w), int(0.565 * h)]
], dtype=np.int32)
pts_right_c = np.array([
    [int(0.50 * w), int(0.63 * h)],
    [int(0.525 * w), int(0.585 * h)],
    [int(0.565 * w), int(0.565 * h)]
], dtype=np.int32)
cv2.polylines(cleavage_mask, [pts_left_c, pts_right_c], False, 0.9, thickness=max(5, int(0.010 * w)))
cleavage_mask = cv2.GaussianBlur(cleavage_mask, (21, 21), 7)

for c in range(3):
    guide[:, :, c] = guide[:, :, c] * (1.0 - cleavage_mask * 0.72) + shadow_skin_bgr[c] * (cleavage_mask * 0.72)

# Inner cleavage skin highlights (rounded upper-inner breast mounds)
inner_hl = np.zeros((h, w), dtype=np.float32)
cv2.ellipse(inner_hl, (int(0.468 * w), int(0.615 * h)), (int(0.025 * w), int(0.035 * h)), -12, 0, 360, 1.0, -1)
cv2.ellipse(inner_hl, (int(0.532 * w), int(0.615 * h)), (int(0.025 * w), int(0.035 * h)), 12, 0, 360, 1.0, -1)
inner_hl = cv2.GaussianBlur(inner_hl, (21, 21), 7)
for c in range(3):
    guide[:, :, c] = np.clip(guide[:, :, c] * (1.0 - inner_hl * 0.35) + highlight_skin_bgr[c] * (inner_hl * 0.35), 0, 255)

# 3D upper-dome highlights on scrub over left & right breasts
hl_mask = np.zeros((h, w), dtype=np.float32)
cv2.ellipse(hl_mask, (int(0.365 * w), int(0.645 * h)), (int(0.095 * w), int(0.042 * h)), -15, 0, 360, 1.0, -1)
cv2.ellipse(hl_mask, (int(0.635 * w), int(0.645 * h)), (int(0.095 * w), int(0.042 * h)), 15, 0, 360, 1.0, -1)
hl_mask = cv2.GaussianBlur(hl_mask, (45, 45), 16)
guide = np.clip(guide * (1.0 + hl_mask[:, :, None] * 0.34), 0, 255)

# Deep 3D under-bust crescent shadows (v=0.70..0.76) + waist vertical contour shadows
ub_mask = np.zeros((h, w), dtype=np.float32)
pts_ub_l = np.array([
    [int(0.24 * w), int(0.68 * h)],
    [int(0.31 * w), int(0.735 * h)],
    [int(0.41 * w), int(0.745 * h)],
    [int(0.485 * w), int(0.71 * h)],
], dtype=np.int32)
pts_ub_r = np.array([
    [int(0.76 * w), int(0.68 * h)],
    [int(0.69 * w), int(0.735 * h)],
    [int(0.59 * w), int(0.745 * h)],
    [int(0.515 * w), int(0.71 * h)],
], dtype=np.int32)
cv2.polylines(ub_mask, [pts_ub_l, pts_ub_r], False, 1.0, thickness=max(14, int(0.026 * w)))
# Vertical waist cinch shadows under the bust
cv2.ellipse(ub_mask, (int(0.39 * w), int(0.82 * h)), (int(0.045 * w), int(0.065 * h)), 8, 0, 360, 0.65, -1)
cv2.ellipse(ub_mask, (int(0.61 * w), int(0.82 * h)), (int(0.045 * w), int(0.065 * h)), -8, 0, 360, 0.65, -1)
ub_mask = cv2.GaussianBlur(ub_mask, (41, 41), 15)

guide = np.clip(guide * (1.0 - ub_mask[:, :, None] * 0.58), 0, 255)

guide_u8 = guide.astype(np.uint8)
guide_path = r"c:\IA\Edicion de videos\reels_work\vet_avatar_sexy_v5_guide.png"
cv2.imwrite(guide_path, guide_u8)
print("Saved properly-scaled guide:", guide_path)

# Call gemini-nano-banana-2.1 to turn the sculpted guide into a 100% photorealistic 38D portrait
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    with open(r"c:\IA\Edicion de videos\.env") as f:
        for line in f:
            if line.startswith("GEMINI_API_KEY="):
                api_key = line.strip().split("=", 1)[1].strip('"\'')
client = genai.Client(api_key=api_key)

with open(guide_path, "rb") as f:
    guide_bytes = f.read()

prompt = (
    "Keep this exact woman's face, smile, hair, and clinic background identical. "
    "Refine her torso following the exact sculpted 38D bust, deep V-neck cleavage, and ultra-narrow cinched wasp waist "
    "in the image so the fabric tension, cleavage skin texture, stethoscope, and 3D breast volume look 100% photorealistic, "
    "voluptuous, and natural. Do not flatten the bust or widen the waist. Vertical 9:16."
)

resp = client.models.generate_content(
    model="gemini-nano-banana-2.1",
    contents=[
        types.Part.from_bytes(data=guide_bytes, mime_type="image/png"),
        prompt,
    ],
    config=types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(aspect_ratio="9:16"),
    ),
)

out_path = r"c:\IA\Edicion de videos\reels_work\vet_avatar_sexy_v5_refined.png"
for part in resp.candidates[0].content.parts:
    if part.inline_data:
        with open(out_path, "wb") as f:
            f.write(part.inline_data.data)
        print("Saved refined image:", out_path)
