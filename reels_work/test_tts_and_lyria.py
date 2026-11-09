# -*- coding: utf-8 -*-
import os
import json
import base64
import pathlib
from google import genai

BASE_DIR = pathlib.Path(r"c:\IA\Edicion de videos")
WORK_DIR = BASE_DIR / "reels_work"
ENV_FILE = BASE_DIR / ".env"

for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.strip().startswith("#"):
        k, v = line.split("=", 1)
        os.environ[k.strip()] = v.strip().strip("\"'")

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# 1. Test Gemini 3.8 Flash TTS with our es-AR designed voice (voice_7j8i5jtcagb0)
script_text = (
    "¡Mirá lo nuevo de MascotaMás para tu veterinaria, peluquería o guardería! <short pause> "
    "Ahora tenés cuatro tipos de calendario: Turnos Simples uno a uno, y Cupos por Horario para paseos. <short pause> "
    "También agendas por Servicios y Profesionales, con grilla automática sin huecos, <short pause> "
    "y Calendario de Guardería por rango de fechas, con sectores de ingreso y egreso. <short pause> "
    "Además, activás el cobro de seña automático con Mercado Pago para asegurar cada turno. <short pause> "
    "¡Entrá hoy en MascotaMás y probalo!"
)

print("[1/2] Generando locución con gemini-3.8-flash-tts (acento argentino es-AR)...")
tts_res = client.interactions.create(
    model="gemini-3.8-flash-tts",
    input=[{
        "type": "user_input",
        "content": [{
            "type": "text",
            "text": script_text,
            "annotations": [{
                "type": "speech_metadata",
                "style": "natural, warm, relaxed conversational pace, authentic Argentine Rioplatense commercial delivery",
            }],
        }],
    }],
    response_format={"type": "audio"},
    generation_config={
        "speech_config": [
            {"voice": "voice_7j8i5jtcagb0"},
        ]
    },
)

tts_path = WORK_DIR / "gemini_tts_ar_v2.wav"
tts_path.write_bytes(base64.b64decode(tts_res.output_audio.data))
print(f"  -> Guardado {tts_path} ({tts_path.stat().st_size} bytes)")

# 2. Test Lyria 3 (lyria-3-clip-preview) for modern commercial House music (30s instrumental)
print("[2/2] Generando música House con Lyria 3 (lyria-3-clip-preview)...")
lyria_prompt = (
    "Modern, upbeat, sophisticated commercial House music at 124 BPM in A Minor. "
    "Punchy four-on-the-floor kick drum, crisp house hi-hats, groovy warm deep bassline, "
    "bright pluck synth chords, and subtle filter-sweep transitions every 5 seconds "
    "([0:00-0:04] punchy house intro groove, [0:04-0:10] warm house bass drop, "
    "[0:10-0:15] melodic synth progression with crisp clap transition, "
    "[0:15-0:20] uplifting house groove with subtle riser, "
    "[0:20-0:25] energetic deep house drop, [0:25-0:30] clean uplifting commercial outro). "
    "Instrumental only, no vocals, studio master quality."
)
lyria_res = client.interactions.create(
    model="lyria-3-clip-preview",
    input=lyria_prompt,
)

lyria_path = WORK_DIR / "lyria3_house_v2.mp3"
if lyria_res.output_audio and lyria_res.output_audio.data:
    lyria_path.write_bytes(base64.b64decode(lyria_res.output_audio.data))
    print(f"  -> Guardado {lyria_path} ({lyria_path.stat().st_size} bytes)")
else:
    for step in lyria_res.steps:
        if step.type == "model_output":
            for cb in step.content:
                if cb.type == "audio":
                    lyria_path.write_bytes(base64.b64decode(cb.data))
                    print(f"  -> Guardado (from steps) {lyria_path} ({lyria_path.stat().st_size} bytes)")
