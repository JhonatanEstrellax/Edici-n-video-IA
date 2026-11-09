# -*- coding: utf-8 -*-
import os
import sys
import base64
import pathlib
from concurrent.futures import ThreadPoolExecutor, as_completed
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

API_KEY = os.environ["GEMINI_API_KEY"]

avatar_path = WORK_DIR / "vet_avatar_sexy_v4.png"
raw_bytes = avatar_path.read_bytes()
mime_type = "image/png" if raw_bytes.startswith(b"\x89PNG") else "image/jpeg"
avatar_b64 = base64.b64encode(raw_bytes).decode("utf-8")

# ---------------------------------------------------------------------------
# 1. Textos de locución (sin "para paseos" y sin mencionar comisión en voz alta)
# ---------------------------------------------------------------------------
tts_text_v4A = (
    "¡Mirá lo nuevo de MascotaMás para tu veterinaria, peluquería o guardería! <short pause> "
    "Ahora tenés cuatro tipos de calendario: Turnos Simples uno a uno, y Cupos por Horario. <short pause> "
    "También agendas por Servicios y Profesionales, con grilla automática sin huecos, <short pause> "
    "y Calendario de Guardería por rango de fechas, con sectores de ingreso y egreso. <short pause> "
    "Además, activás el cobro de seña automático con Mercado Pago para asegurar cada turno. <short pause> "
    "¡Entrá hoy en MascotaMás y probalo!"
)

tts_text_v4B = (
    "¿Perdés turnos por WhatsApp en tu veterinaria, peluquería o guardería? ¡Mirá lo nuevo de MascotaMás! <short pause> "
    "Elegí entre cuatro agendas inteligentes: Turnos Simples uno a uno, o Cupos por Horario. <short pause> "
    "Agenda por Servicios y Profesionales, que calcula duraciones sola y elimina los huecos, <short pause> "
    "y Calendario de Guardería por fechas, controlando sectores, ingreso y egreso. <short pause> "
    "¿Lo mejor? Cobrás seña automática con Mercado Pago y te olvidás de los faltazos. <short pause> "
    "¡Entrá hoy en mascotamas punto com y probalo!"
)

# ---------------------------------------------------------------------------
# 2. Prompts de video Turno-1 (15s 1080p desde vet_avatar_sexy_v4.png)
#    Nota: v4A_part2 se comparte o cada versión tiene sus clips exactos.
# ---------------------------------------------------------------------------
base_visual_dir = (
    "Use this image as the exact starting frame. In a single continuous unbroken vertical 9:16 commercial shot "
    "in a bright modern veterinary clinic, this stunning, glamorous young Argentine female veterinarian with "
    "dark espresso-brown wavy hair, bright emerald-green eyes, and a tailored teal V-neck scrub top speaks "
    "directly into the camera lens in Spanish with a natural Argentine Rioplatense accent from Buenos Aires "
    "(porteño voseo and yeísmo). "
    "CRITICAL LIP-SYNC & MOUTH INSTRUCTION: Articulate every syllable with crisp, natural, anatomically flawless "
    "mouth and lip movements, clear bilabial closures on M, P, and B sounds, natural teeth visibility, and warm, "
    "confident, alluring eye contact. Keep her head centered in the upper-middle frame (minimal head bobbing). "
    "No background music. Clear studio voice audio. "
)

video_jobs = {
    "v4A_part1": (
        base_visual_dir +
        "She speaks at a natural commercial pace saying the exact words in Spanish: "
        "\"¡Mirá lo nuevo de MascotaMás para tu veterinaria, peluquería o guardería! "
        "Ahora tenés cuatro tipos de calendario: Turnos Simples uno a uno, y Cupos por Horario. "
        "También agendas por Servicios y Profesionales, con grilla automática sin huecos.\" "
        "She finishes speaking before the end of the 15-second clip and closes her lips into a warm smile."
    ),
    "v4A_part2": (
        base_visual_dir +
        "She speaks at a natural commercial pace saying the exact words in Spanish: "
        "\"Y Calendario de Guardería por rango de fechas, con sectores de ingreso y egreso. "
        "Además, activás el cobro de seña automático con Mercado Pago para asegurar cada turno. "
        "¡Entrá hoy en MascotaMás y probalo!\" "
        "She finishes speaking before the end of the 15-second clip and holds a warm, radiant closed-lip smile at the camera."
    ),
    "v4B_part1": (
        base_visual_dir +
        "She speaks at a natural, engaging commercial pace saying the exact words in Spanish: "
        "\"¿Perdés turnos por WhatsApp en tu veterinaria, peluquería o guardería? ¡Mirá lo nuevo de MascotaMás! "
        "Elegí entre cuatro agendas inteligentes: Turnos Simples uno a uno, o Cupos por Horario. "
        "Agenda por Servicios y Profesionales, que calcula duraciones sola y elimina los huecos.\" "
        "She finishes speaking before the end of the 15-second clip and closes her lips into a warm smile."
    ),
    "v4B_part2": (
        base_visual_dir +
        "She speaks at a natural, engaging commercial pace saying the exact words in Spanish: "
        "\"Y Calendario de Guardería por fechas, controlando sectores, ingreso y egreso. "
        "¿Lo mejor? Cobrás seña automática con Mercado Pago y te olvidás de los faltazos. "
        "¡Entrá hoy en MascotaMás y probalo!\" "
        "She finishes speaking before the end of the 15-second clip and holds a warm, radiant closed-lip smile at the camera."
    ),
}

def generate_tts(name: str, text: str):
    c = genai.Client(api_key=API_KEY)
    out_wav = WORK_DIR / f"{name}.wav"
    print(f"[TTS] Generando {name}.wav con gemini-3.8-flash-tts (voice_7j8i5jtcagb0)...")
    res = c.interactions.create(
        model="gemini-3.8-flash-tts",
        input=[{
            "type": "user_input",
            "content": [{
                "type": "text",
                "text": text,
                "annotations": [{
                    "type": "speech_metadata",
                    "style": "natural, warm, confident, alluring Argentine Rioplatense commercial delivery",
                }],
            }],
        }],
        response_format={"type": "audio"},
        generation_config={
            "speech_config": [{"voice": "voice_7j8i5jtcagb0"}]
        },
    )
    out_wav.write_bytes(base64.b64decode(res.output_audio.data))
    print(f"  -> [TTS DONE] {out_wav.name} ({out_wav.stat().st_size} bytes)")
    return str(out_wav)

def generate_video_clip(name: str, prompt_text: str):
    c = genai.Client(api_key=API_KEY)
    out_mp4 = WORK_DIR / f"{name}.mp4"
    print(f"[VIDEO] Generando {name}.mp4 (15s Turno-1 1080p) con gemini-omni-1.2-flash...")
    res = c.interactions.create(
        model="gemini-omni-1.2-flash",
        input=[
            {"type": "image", "data": avatar_b64, "mime_type": mime_type},
            {"type": "text", "text": prompt_text},
        ],
        response_format={
            "type": "video",
            "aspect_ratio": "9:16",
            "resolution": "1080p",
            "duration": "15s",
        },
    )
    if not (res.output_video and res.output_video.data):
        raise RuntimeError(f"No output_video for {name}")
    out_mp4.write_bytes(base64.b64decode(res.output_video.data))
    print(f"  -> [VIDEO DONE] {out_mp4.name} ({out_mp4.stat().st_size} bytes), id={res.id}")
    return str(out_mp4)

if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = []
        futs.append(ex.submit(generate_tts, "tts_v4A_raw", tts_text_v4A))
        futs.append(ex.submit(generate_tts, "tts_v4B_raw", tts_text_v4B))
        for k, p in video_jobs.items():
            futs.append(ex.submit(generate_video_clip, k, p))
        for f in as_completed(futs):
            print("Completado:", f.result())
