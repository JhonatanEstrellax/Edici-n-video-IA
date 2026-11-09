import os
import cv2
import numpy as np
from google import genai
from google.genai import types

WORK_DIR = r"c:\IA\Edicion de videos\reels_work"
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    with open(r"c:\IA\Edicion de videos\.env", encoding="utf-8") as f:
        for line in f:
            if line.startswith("GEMINI_API_KEY="):
                api_key = line.strip().split("=", 1)[1].strip("\"'")

client = genai.Client(api_key=api_key)

# Flip avatar_360_5_lateral_der.png horizontally as structural pose guide and refine with gemini-3-pro-image
# so the background and embroidery are 100% right-reading while she faces 90 degrees to the LEFT!
img_r = cv2.imread(os.path.join(WORK_DIR, "avatar_360_5_lateral_der.png"))
img_l_guide = cv2.flip(img_r, 1)
guide_p = os.path.join(WORK_DIR, "temp_left_profile_guide.png")
cv2.imwrite(guide_p, img_l_guide)

with open(guide_p, "rb") as f:
    guide_bytes = f.read()

prompt = (
    "Keep this exact woman, pose (90-degree side profile facing the LEFT side of the image, showing her full bust "
    "on the left, tiny waist, and round sculpted glutes on the right, looking slightly toward the camera), "
    "and refine the image so it is 100% crisp and photorealistic with 'VETERINARIA PALERMO' correctly oriented."
)

print("Generating true Left Profile (-90 deg) with gemini-3-pro-image...")
resp = client.models.generate_content(
    model="gemini-3-pro-image",
    contents=[
        types.Part.from_bytes(data=guide_bytes, mime_type="image/png"),
        prompt,
    ],
    config=types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(aspect_ratio="9:16"),
    ),
)

out_p = os.path.join(WORK_DIR, "avatar_360_3_lateral_izq.png")
for p in resp.candidates[0].content.parts:
    if p.inline_data:
        with open(out_p, "wb") as f:
            f.write(p.inline_data.data)
        print("Saved:", out_p)
