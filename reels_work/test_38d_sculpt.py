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

img = cv2.imread(str(WORK_DIR / "vet_avatar_sexy_v4.png"))

# Let's ask gemini-nano-banana-2.1 with an explicit visual instruction that replaces the loose medical scrub with a
# form-fitting, low-cut black/teal evening-style fitted V-neck corset/bodysuit top + stethoscope so "medical scrub"
# doesn't force a loose hospital tunic!
_, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
in_b64 = base64.b64encode(buf.tobytes()).decode("utf-8")

prompt = (
    "Edit this photo: keep the woman's exact face, hair, and background, but change her body into a very busty, "
    "curvy voluptuous hourglass figure with huge 38D breasts and a tiny wasp waist. Replace her loose shirt with a "
    "tight, low-cut, form-fitting deep V-neck teal dressy top that shows pronounced cleavage and hugs her large 38D bust "
    "and narrow waist tightly, keeping the stethoscope around her neck."
)

res = client.interactions.create(
    model="gemini-nano-banana-2.1",
    input=[
        {"type": "image", "data": in_b64, "mime_type": "image/jpeg"},
        {"type": "text", "text": prompt},
    ],
    response_format={"type": "image", "mime_type": "image/jpeg", "aspect_ratio": "9:16"},
)

out_p = WORK_DIR / "vet_avatar_sexy_v5_test.png"
out_p.write_bytes(base64.b64decode(res.output_image.data))
print("Saved:", out_p, out_p.stat().st_size)
