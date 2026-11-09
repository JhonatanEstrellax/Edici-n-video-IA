# -*- coding: utf-8 -*-
import os
import sys
import base64
import pathlib
from google import genai

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

BASE_DIR = pathlib.Path(r"c:\IA\Edicion de videos")
WORK_DIR = BASE_DIR / "reels_work"
ENV_FILE = BASE_DIR / ".env"

for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.strip().startswith("#"):
        k, v = line.split("=", 1)
        os.environ[k.strip()] = v.strip()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

out_path = WORK_DIR / "vet_avatar_sexy_v4.png"

prompt = (
    "Vertical 9:16 photorealistic commercial portrait of a bombshell-gorgeous, sexy, charismatic 25-year-old Argentine "
    "female veterinarian in a bright luxury veterinary clinic in Palermo, Buenos Aires. She has a supermodel-level "
    "sculpted face, radiant warm sun-kissed skin, mesmerizing bright emerald-green almond eyes with thick lashes, "
    "and voluminous glossy dark espresso-brown waves cascading over her shoulders. "
    "CRITICAL MOUTH & LIPS DETAIL: Her mouth and lips are anatomically flawless, full, symmetrical, and luscious with "
    "a sharp Cupid's bow, hydrated rose-nude satin lip gloss, and a natural, relaxed closed-lip smile (lips gently touching "
    "with crisp lip edges, no teeth distortion, ready to speak clearly). "
    "She wears a stylish, form-fitting, tailored deep-teal V-neck veterinary scrub top that accentuates her feminine silhouette "
    "and neckline tastefully, with a sleek silver Littmann stethoscope draped over her shoulders. "
    "Her head is framed in the upper-center of the 9:16 image (eyes at 30% from top, mouth at 38% from top) with waist-up framing. "
    "Shot on Sony A1 85mm f/1.4 GM lens, soft studio beauty lighting, ultra-detailed skin texture."
)

print("[AVATAR V4] Generando retrato de veterinaria sexy con boca perfecta via gemini-nano-banana-2.1...")
res = client.interactions.create(
    model="gemini-nano-banana-2.1",
    input=[{"type": "text", "text": prompt}],
    response_format={
        "type": "image",
        "mime_type": "image/jpeg",
        "aspect_ratio": "9:16",
    },
)

if res.output_image and res.output_image.data:
    img_bytes = base64.b64decode(res.output_image.data)
    out_path.write_bytes(img_bytes)
    print(f"  -> Retrato guardado en {out_path} ({len(img_bytes)} bytes)")
else:
    raise RuntimeError("No se recibio output_image de gemini-nano-banana-2.1")
