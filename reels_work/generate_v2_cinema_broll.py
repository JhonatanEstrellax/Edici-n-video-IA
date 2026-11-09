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
        os.environ[k.strip()] = v.strip().strip("\"'")

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

part1_path = WORK_DIR / "v2_cinema_broll_part1.mp4"
part2_path = WORK_DIR / "v2_cinema_broll_part2.mp4"

prompt_1 = (
    "Ultra-realistic documentary commercial footage shot on ARRI Alexa Mini LF with 35mm f/1.4 prime lens, "
    "natural warm daylight, subtle handheld camera movement, realistic film grain, shallow depth of field. "
    "No dialogue, no speaking, no text overlays. "
    "[0-5s] Close-up cinematic shot in a bright modern veterinary clinic of a happy Golden Retriever dog sitting on a clean examination table, wagging its tail gently while a veterinarian's hands in teal medical scrubs gently pet its head with a stethoscope visible. "
    "[5-10s] Smooth cinematic tracking shot of a cute French Bulldog walking happily on a leash in a sunlit green park during a group dog walk. "
    "[10-15s] Cinematic medium close-up in a modern boutique dog grooming salon of a fluffy white toy poodle being gently brushed with a wooden brush under warm studio lighting."
)

prompt_2 = (
    "Ultra-realistic documentary commercial footage shot on ARRI Alexa Mini LF with 35mm f/1.4 prime lens, "
    "natural warm daylight, subtle handheld camera movement, realistic film grain, shallow depth of field. "
    "No dialogue, no speaking, no text overlays. "
    "[0-5s] Cinematic wide-to-medium shot of a bright, upscale indoor dog daycare and pet hotel playroom with two happy Golden Retriever and Beagle puppies relaxing and playing on cozy beds. "
    "[5-10s] Over-the-shoulder close-up shot at a modern veterinary clinic reception desk showing a veterinarian's hands typing on a sleek Space Black MacBook Pro laptop next to a Titanium iPhone on a wooden counter with a cute tabby cat resting nearby. "
    "[10-15s] Warm cinematic close-up of a happy Golden Retriever and a cute kitten sitting together on a veterinary clinic counter looking curiously at the camera lens with soft sunlit bokeh background."
)

print("[1/2] Generando B-Roll cinematográfico Parte 1 (15s, 1080p, 9:16) con gemini-omni-1.2-flash...")
res1 = client.interactions.create(
    model="gemini-omni-1.2-flash",
    input=prompt_1,
    response_format={
        "type": "video",
        "aspect_ratio": "9:16",
        "resolution": "1080p",
        "duration": "15s",
    },
)
if res1.output_video and res1.output_video.data:
    part1_path.write_bytes(base64.b64decode(res1.output_video.data))
    print(f"  -> Guardado {part1_path} ({part1_path.stat().st_size} bytes)")
else:
    raise RuntimeError("No se recibió output_video en Parte 1")

print("[2/2] Generando B-Roll cinematográfico Parte 2 (15s, 1080p, 9:16) con gemini-omni-1.2-flash...")
res2 = client.interactions.create(
    model="gemini-omni-1.2-flash",
    input=prompt_2,
    response_format={
        "type": "video",
        "aspect_ratio": "9:16",
        "resolution": "1080p",
        "duration": "15s",
    },
)
if res2.output_video and res2.output_video.data:
    part2_path.write_bytes(base64.b64decode(res2.output_video.data))
    print(f"  -> Guardado {part2_path} ({part2_path.stat().st_size} bytes)")
else:
    raise RuntimeError("No se recibió output_video en Parte 2")
