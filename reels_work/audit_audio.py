# -*- coding: utf-8 -*-
import os, sys, base64, pathlib
from google import genai

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

BASE_DIR = pathlib.Path(r"c:\IA\Edicion de videos")
WORK_DIR = BASE_DIR / "reels_work"
for line in (BASE_DIR / ".env").read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.strip().startswith("#"):
        k, v = line.split("=", 1)
        os.environ[k.strip()] = v.strip().strip("\"'")

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

tts_b64 = base64.b64encode((WORK_DIR / "gemini_tts_ar_v2.wav").read_bytes()).decode("utf-8")
lyria_b64 = base64.b64encode((WORK_DIR / "lyria3_house_v2.mp3").read_bytes()).decode("utf-8")

res = client.interactions.create(
    model="gemini-3.8-flash",
    input=[
        {"type": "audio", "mime_type": "audio/wav", "data": tts_b64},
        {"type": "audio", "mime_type": "audio/mp3", "data": lyria_b64},
        {"type": "text", "text": (
            "Analizá estos dos audios:\n"
            "Audio 1 (Locución TTS): 1) ¿Cómo suena el acento argentino rioplatense (yeísmo/sh, voseo) y la naturalidad del ritmo (¿suena 100% humano y relajado, o robótico)? "
            "2) ¿Cómo pronuncia específicamente: Mirá, tenés, activás, seña, Mercado Pago, Entrá, probalo? ¿Alguna palabra tiene acentuación incorrecta (ej. 'activas' grave en vez de 'activás' aguda, o 'probalo' esdrújula en vez de 'probalo' grave)?\n"
            "Audio 2 (Música Lyria 3): ¿Es música House instrumental limpia (sin voces), qué BPM aproximado tiene y en qué segundos exactos se sienten los cambios de compás/transiciones?"
        )}
    ]
)
print(res.output_text)
