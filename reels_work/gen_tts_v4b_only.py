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

tts_text_v4B_clean = (
    "¿Perdés turnos por WhatsApp en tu veterinaria, peluquería o guardería? ¡Mirá lo nuevo de MascotaMás! <short pause> "
    "Elegí entre cuatro agendas inteligentes: Turnos Simples uno a uno, o Cupos por Horario. <short pause> "
    "También agendas por Servicios y Profesionales, con grilla automática sin huecos, <short pause> "
    "y Calendario de Guardería por rango de fechas, con sectores de ingreso y egreso. <short pause> "
    "¿Lo mejor? Cobrás seña automática con Mercado Pago y te olvidás de los faltazos. <short pause> "
    "¡Entrá hoy en MascotaMás y probalo!"
)

print("[TTS v4B] Generando tts_v4B_raw.wav con gemini-3.8-flash-tts (voice_7j8i5jtcagb0)...")
res = client.interactions.create(
    model="gemini-3.8-flash-tts",
    input=[{
        "type": "user_input",
        "content": [{
            "type": "text",
            "text": tts_text_v4B_clean,
            "annotations": [{
                "type": "speech_metadata",
                "style": "natural, warm, confident, alluring Argentine Rioplatense commercial delivery",
            }],
        }],
    }],
    response_format={"type": "audio"},
    generation_config={"speech_config": [{"voice": "voice_7j8i5jtcagb0"}]},
)

out_wav = WORK_DIR / "tts_v4B_raw.wav"
out_wav.write_bytes(base64.b64decode(res.output_audio.data))
print(f"  -> Guardado {out_wav} ({out_wav.stat().st_size} bytes)")
