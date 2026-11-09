# -*- coding: utf-8 -*-
import os
import sys
import pathlib
from google import genai
from google.genai import types

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

SKILL_SCRIPTS_DIR = r"C:\Users\Demiante\.gemini\config\plugins\gemini-api\skills\gemini-omni-flash-api\scripts"
sys.path.insert(0, SKILL_SCRIPTS_DIR)
sys.path.insert(0, os.path.join(SKILL_SCRIPTS_DIR, "video"))
from generate_video import resolve_or_upload_asset, download_video_file, DEFAULT_MODEL

BASE_DIR = pathlib.Path(r"c:\IA\Edicion de videos")
WORK_DIR = BASE_DIR / "reels_work"
ENV_FILE = BASE_DIR / ".env"

for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.strip().startswith("#"):
        k, v = line.split("=", 1)
        os.environ[k.strip()] = v.strip().strip("\"'")

def main():
    client = genai.Client(http_options=types.HttpOptions(timeout=600_000))
    mostrador_uri, mostrador_mime = resolve_or_upload_asset(
        str(WORK_DIR / "avatar_v6B_mostrador_entrada_ref.png"), "image/png"
    )
    prompt = (
        "<FIRST_FRAME> Use this image as the starting frame. In a single continuous unbroken 9:16 vertical shot "
        "at the front reception counter and entrance desk of her modern veterinary clinic in Palermo, Buenos Aires, "
        "this young Argentine female veterinarian with long wavy dark brown hair and a dark-teal scrub top with a "
        "stethoscope stands beside the open laptop on the marble reception counter. With energetic, natural body "
        "movement, her hair swaying softly, and her hands gesturing invitingly toward the viewer, she speaks directly "
        "to the camera in Spanish with a natural Argentine Rioplatense accent: "
        "\"¡Escribinos hoy en MascotaMás y te migramos gratis en el día!\" "
        "After finishing the last word, she keeps moving naturally with a warm closed-lip smile. "
        "Keep a constant medium-full camera distance. No background music. Clear studio voice audio."
    )
    interaction = client.interactions.create(
        model=DEFAULT_MODEL,
        input=[
            {"type": "image", "uri": mostrador_uri, "mime_type": mostrador_mime},
            {"type": "text", "text": prompt},
        ],
        response_format={
            "type": "video",
            "delivery": "uri",
            "aspect_ratio": "9:16",
            "duration": "6s",
            "resolution": "1080p",
        },
    )
    out_p = WORK_DIR / "v6B_mostrador_cta_6s.mp4"
    download_video_file(interaction.output_video, str(out_p), client=client)
    print(f"Guardado {out_p} ({out_p.stat().st_size} bytes)")

if __name__ == "__main__":
    main()
