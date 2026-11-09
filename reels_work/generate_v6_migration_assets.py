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
AVATAR_DIR = BASE_DIR / "assets" / "avatar_veterinaria_360"
ENV_FILE = BASE_DIR / ".env"

for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.strip().startswith("#"):
        k, v = line.split("=", 1)
        os.environ[k.strip()] = v.strip().strip("\"'")

API_KEY = os.environ["GEMINI_API_KEY"]

def load_b64(path: pathlib.Path):
    raw = path.read_bytes()
    mime = "image/png" if raw.startswith(b"\x89PNG") else "image/jpeg"
    return base64.b64encode(raw).decode("utf-8"), mime

frente_b64, frente_mime = load_b64(AVATAR_DIR / "avatar_360_1_frente.png")
tres_cuartos_b64, tres_cuartos_mime = load_b64(AVATAR_DIR / "avatar_360_2_tres_cuartos_izq.png")

# ---------------------------------------------------------------------------
# 1. Guion Argentino de Storytelling: "Migración GRATIS en el Día a MascotaMás"
# ---------------------------------------------------------------------------
sentences_v6 = [
    "¿Seguís atado a un sistema viejo o al Excel por miedo a perder los datos de tu veterinaria?",
    "¡Pasate hoy a MascotaMás! Te hacemos toda la migración gratis y en el día, sin frenar tu consultorio.",
    "Pasamos tus clientes, pacientes, historias clínicas y vacunas para que no pierdas ni una sola ficha.",
    "En horas ya tenés recordatorios automáticos por WhatsApp, sala de espera en vivo y todo en la nube.",
    "Además, sumás las cuatro agendas inteligentes y el cobro de seña automático con Mercado Pago.",
    "¡Escribinos hoy en MascotaMás y te migramos gratis en el día!"
]

tts_full_text_v6 = " <short pause> ".join(sentences_v6)

# ---------------------------------------------------------------------------
# 2. Prompts de Video (3 clips de 15s en 1080p, solo 2 oraciones por clip = ~9s de habla)
#    Esto garantiza que JAMÁS se corte una frase y que el ritmo sea pausado, natural y energético.
# ---------------------------------------------------------------------------
base_prompt_frente = (
    "Use this image as the exact starting frame. In a single continuous unbroken vertical 9:16 commercial shot "
    "in a bright modern veterinary clinic, this glamorous young Argentine female veterinarian with long glossy "
    "dark brunette wavy hair, bright emerald-green eyes, and a fitted dark-teal V-neck scrub top with a stethoscope "
    "speaks directly into the camera lens in Spanish with a natural, warm, energetic Argentine Rioplatense accent "
    "from Buenos Aires (porteño voseo and yeísmo). "
    "CRITICAL LIP-SYNC & MOUTH INSTRUCTION: Articulate every word at a natural, unhurried, confident pace with crisp, "
    "anatomically natural mouth and lip movements, clear bilabial closures on M, P, and B sounds, natural teeth "
    "visibility, and warm eye contact. Keep her framing steady. No background music. Clear studio voice audio. "
)

base_prompt_tres_cuartos = (
    "Use this image as the exact starting frame. In a single continuous unbroken vertical 9:16 commercial shot "
    "in a bright modern veterinary clinic, this glamorous young Argentine female veterinarian in a three-quarter "
    "angle looking directly at the camera lens speaks in Spanish with a natural, warm, energetic Argentine "
    "Rioplatense accent from Buenos Aires (porteño voseo and yeísmo). "
    "CRITICAL LIP-SYNC & MOUTH INSTRUCTION: Articulate every word at a natural, unhurried, confident pace with crisp, "
    "anatomically natural mouth and lip movements, clear bilabial closures on M, P, and B sounds, natural teeth "
    "visibility, and warm eye contact. Keep her framing steady. No background music. Clear studio voice audio. "
)

video_jobs = [
    (
        "v6_clip1_frente",
        frente_b64,
        frente_mime,
        base_prompt_frente + (
            "She speaks at a natural, empathetic, and energetic commercial pace saying the exact words in Spanish: "
            "\"¿Seguís atado a un sistema viejo o al Excel por miedo a perder los datos de tu veterinaria? "
            "¡Pasate hoy a MascotaMás! Te hacemos toda la migración gratis y en el día, sin frenar tu consultorio.\" "
            "She finishes every word clearly with time to spare before the end of the 15-second clip and holds a warm closed-lip smile."
        )
    ),
    (
        "v6_clip2_tres_cuartos",
        tres_cuartos_b64,
        tres_cuartos_mime,
        base_prompt_tres_cuartos + (
            "She speaks at a natural, confident, and reassuring commercial pace saying the exact words in Spanish: "
            "\"Pasamos tus clientes, pacientes, historias clínicas y vacunas para que no pierdas ni una sola ficha. "
            "En horas ya tenés recordatorios automáticos por WhatsApp, sala de espera en vivo y todo en la nube.\" "
            "She finishes every word clearly with time to spare before the end of the 15-second clip and holds a warm closed-lip smile."
        )
    ),
    (
        "v6_clip3_frente_cta",
        frente_b64,
        frente_mime,
        base_prompt_frente + (
            "She speaks at a natural, enthusiastic commercial pace saying the exact words in Spanish: "
            "\"Además, sumás las cuatro agendas inteligentes y el cobro de seña automático con Mercado Pago. "
            "¡Escribinos hoy en MascotaMás y te migramos gratis en el día!\" "
            "She finishes every word clearly with time to spare before the end of the 15-second clip and holds a radiant closed-lip smile at the camera."
        )
    ),
]

def generate_tts_wav(name: str, text: str):
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
                    "style": "natural, unhurried, warm, confident and energetic Argentine Rioplatense commercial storytelling delivery",
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

def generate_video_clip(name: str, img_b64: str, img_mime: str, prompt_text: str):
    c = genai.Client(api_key=API_KEY)
    out_mp4 = WORK_DIR / f"{name}.mp4"
    print(f"[VIDEO] Generando {name}.mp4 (15s 1080p) con gemini-omni-1.2-flash...")
    res = c.interactions.create(
        model="gemini-omni-1.2-flash",
        input=[
            {"type": "image", "data": img_b64, "mime_type": img_mime},
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
        # Full TTS take + individual sentence takes so we have 100% unclipped audio
        futs.append(ex.submit(generate_tts_wav, "tts_v6_full_raw", tts_full_text_v6))
        for idx, s_txt in enumerate(sentences_v6, start=1):
            futs.append(ex.submit(generate_tts_wav, f"tts_v6_s{idx}", s_txt))
        for v_name, v_b64, v_mime, v_prompt in video_jobs:
            futs.append(ex.submit(generate_video_clip, v_name, v_b64, v_mime, v_prompt))
        for f in as_completed(futs):
            print("Completado:", f.result())
