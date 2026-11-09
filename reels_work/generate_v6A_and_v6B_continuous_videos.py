# -*- coding: utf-8 -*-
"""
Genera en paralelo las 2 cadenas continuas Multi-Turn (10s -> +10s -> +10s -> +6s = 36s continuos sin cortes)
usando gemini-omni-1.1-flash (1080p 9:16) via Interactions API y Files API:
- Cadena v6A (v6A_continuous_full.mp4): Avatar 360° en consultorio con movimiento 100% natural y continuo
  de cuerpo, pelo, hombros y manos de principio a fin (sin congelar cuerpo ni rostro).
- Cadena v6B (v6B_palermo_walk_full.mp4): Avatar trabajando en su Veterinaria de Palermo, empezando en el
  consultorio junto a la camilla acariciando al perro, caminando en plano secuencia Steadicam por la clínica
  y llegando hasta el mostrador / escritorio de entrada con su MacBook Pro.
"""
import os
import sys
import pathlib
from concurrent.futures import ThreadPoolExecutor
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
AVATAR_DIR = BASE_DIR / "assets" / "avatar_veterinaria_360"
ENV_FILE = BASE_DIR / ".env"

for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.strip().startswith("#"):
        k, v = line.split("=", 1)
        os.environ[k.strip()] = v.strip().strip("\"'")


def run_turn(client, prompt_text, duration_s, out_path: pathlib.Path, prev_id=None, first_frame_uri=None, ref_img_uri=None):
    input_parts = []
    if first_frame_uri:
        uri, mime = first_frame_uri
        input_parts.append({"type": "image", "uri": uri, "mime_type": mime})
        if "<FIRST_FRAME>" not in prompt_text:
            prompt_text = f"<FIRST_FRAME> {prompt_text}"
    if ref_img_uri:
        uri, mime = ref_img_uri
        input_parts.append({"type": "image", "uri": uri, "mime_type": mime})

    input_parts.append({"type": "text", "text": prompt_text})

    video_config = {
        "type": "video",
        "delivery": "uri",
        "aspect_ratio": "9:16",
        "duration": f"{duration_s}s",
        "resolution": "1080p",
    }
    kwargs = {
        "model": DEFAULT_MODEL,
        "input": input_parts,
        "response_format": video_config,
    }
    if prev_id:
        kwargs["previous_interaction_id"] = prev_id

    interaction = client.interactions.create(**kwargs)
    download_video_file(interaction.output_video, str(out_path), client=client)
    print(f"  -> Guardado {out_path.name} ({out_path.stat().st_size} bytes) | id={interaction.id}")
    return interaction.id


def generate_chain_v6A():
    client = genai.Client(http_options=types.HttpOptions(timeout=900_000))
    frente_uri = resolve_or_upload_asset(str(AVATAR_DIR / "avatar_360_1_frente.png"), "image/png")
    tres_cuartos_uri = resolve_or_upload_asset(str(AVATAR_DIR / "avatar_360_2_tres_cuartos_izq.png"), "image/png")

    print("[v6A - Turno 1/4] Generando 0-10s (movimiento natural continuo de cuerpo, pelo, respiración y manos)...")
    id1 = run_turn(
        client,
        prompt_text=(
            "Use this image as the starting frame. In a single continuous unbroken 9:16 vertical shot "
            "in a bright luxury veterinary clinic in Palermo, this glamorous young Argentine female veterinarian "
            "with long glossy dark brunette wavy hair, emerald-green eyes, and a fitted dark-teal V-neck scrub top "
            "with a stethoscope speaks directly to the camera in Spanish with a natural Argentine Rioplatense accent "
            "from Buenos Aires (porteño voseo and yeísmo). "
            "CRITICAL CAMERA & BODY MOTION: Keep a constant medium-full camera distance framed from head to mid-thigh "
            "(do NOT zoom in close to her face). Her entire body, shoulders, breathing, expressive hands, hips, and "
            "long wavy brunette hair move naturally, fluidly, and continuously throughout the entire shot as she shifts "
            "her weight and gestures organically while speaking in Spanish: "
            "\"¿Seguís atado a un sistema viejo o al Excel por miedo a perder los datos de tu veterinaria? "
            "¡Pasate hoy a MascotaMás! Te hacemos toda la migración gratis y en el día, sin frenar tu consultorio.\" "
            "No background music. Clear studio voice audio."
        ),
        duration_s=10,
        out_path=WORK_DIR / "v6A_turn1.mp4",
        first_frame_uri=frente_uri,
    )

    print("[v6A - Turno 2/4] Extendiendo +10s (10-20s continuos sin corte, giro natural 3/4 y movimiento de pelo/manos)...")
    id2 = run_turn(
        client,
        prompt_text=(
            "Extend this video in the exact same continuous unbroken shot with no scene cuts. "
            "Keep the camera at the same medium-full distance (do NOT zoom in). She shifts her posture smoothly "
            "into a natural three-quarter angle like <IMAGE_REF_0> while her long wavy dark brunette hair sways "
            "naturally and she gestures with her hands, moving her torso and shoulders fluidly while speaking directly "
            "to the camera in the exact same Argentine Rioplatense Spanish voice: "
            "\"Pasamos tus clientes, pacientes, historias clínicas y vacunas para que no pierdas ni una sola ficha. "
            "En horas ya tenés recordatorios automáticos por WhatsApp, sala de espera en vivo y todo en la nube.\" "
            "Use the given image as a pose reference; keep continuous natural body and hair motion. "
            "No background music. Clear studio voice audio."
        ),
        duration_s=10,
        out_path=WORK_DIR / "v6A_turn2.mp4",
        prev_id=id1,
        ref_img_uri=tres_cuartos_uri,
    )

    print("[v6A - Turno 3/4] Extendiendo +10s (20-30s continuos sin corte, movimiento fluido de cuerpo y pelo)...")
    id3 = run_turn(
        client,
        prompt_text=(
            "Extend this video in the exact same continuous unbroken shot with no scene cuts. "
            "Keep the medium-full framing so her head, flowing wavy brunette hair, shoulders, and sculpted waist remain "
            "visible. She turns smoothly back toward the front, shifting her weight, moving her hair and shoulders "
            "naturally, and counting on her fingers expressively while speaking directly to the camera in the exact same "
            "Argentine Rioplatense Spanish voice: "
            "\"Además, sumás las cuatro agendas inteligentes y el cobro de seña automático con Mercado Pago.\" "
            "After speaking, she continues gesturing and breathing naturally with a warm smile. "
            "No background music. Clear studio voice audio."
        ),
        duration_s=10,
        out_path=WORK_DIR / "v6A_turn3.mp4",
        prev_id=id2,
    )

    print("[v6A - Turno 4/4] Extendiendo +6s (30-36s continuos sin corte hasta el cierre CTA)...")
    out_v6a = WORK_DIR / "v6A_continuous_full.mp4"
    run_turn(
        client,
        prompt_text=(
            "Extend this video in the exact same continuous unbroken shot with no scene cuts. "
            "Keep the medium-full framing. With warm, energetic body language, her long wavy brunette hair swaying "
            "softly and her hands gesturing invitingly, she speaks directly to the camera in the exact same Argentine "
            "Rioplatense Spanish voice: "
            "\"¡Escribinos hoy en MascotaMás y te migramos gratis en el día!\" "
            "After finishing the last word, she keeps moving naturally, breathing softly with her hair swaying and holding "
            "a radiant closed-lip smile at the camera. No background music. Clear studio voice audio."
        ),
        duration_s=6,
        out_path=out_v6a,
        prev_id=id3,
    )
    return str(out_v6a)


def generate_chain_v6B():
    client = genai.Client(http_options=types.HttpOptions(timeout=900_000))
    camilla_uri = resolve_or_upload_asset(str(WORK_DIR / "avatar_v6B_camilla_perro_start.png"), "image/png")
    mostrador_uri = resolve_or_upload_asset(str(WORK_DIR / "avatar_v6B_mostrador_entrada_ref.png"), "image/png")

    print("[v6B - Turno 1/4] Generando 0-10s (Consultorio en Palermo: en la camilla con el perro arriba y empezando a caminar)...")
    id1 = run_turn(
        client,
        prompt_text=(
            "Use this image as the starting frame. In a single continuous unbroken 9:16 Steadicam shot "
            "in her luxury veterinary clinic in Palermo, Buenos Aires, this glamorous young Argentine female veterinarian "
            "(dark teal V-neck scrub top with 'VETERINARIA PALERMO', stethoscope, long wavy dark brown hair, curvy hourglass figure) "
            "is working in her consultation room next to the stainless-steel examination table where the friendly Golden Retriever dog "
            "sits calmly on top of the table. "
            "[0-5s] She affectionately strokes and examines the dog on the stainless-steel examination table while looking directly into "
            "the camera lens with natural body and hair movement, speaking in Spanish with a natural Argentine Rioplatense accent: "
            "\"¿Seguís atado a un sistema viejo o al Excel por miedo a perder los datos de tu veterinaria?\" "
            "[5-10s] She gives the happy dog on the examination table a warm pat, steps forward away from the examination table, and "
            "walks smoothly out of the consultation room into the bright glass-walled Palermo clinic hallway as the Steadicam tracks "
            "backward in front of her at a constant medium-full distance while she speaks to the camera: "
            "\"¡Pasate hoy a MascotaMás! Te hacemos toda la migración gratis y en el día, sin frenar tu consultorio.\" "
            "Her hair, arms, hips, and body move naturally and continuously as she walks. No background music. Clear studio voice audio."
        ),
        duration_s=10,
        out_path=WORK_DIR / "v6B_turn1.mp4",
        first_frame_uri=camilla_uri,
    )

    print("[v6B - Turno 2/4] Extendiendo +10s (10-20s: caminando del consultorio hasta el mostrador/escritorio de entrada)...")
    id2 = run_turn(
        client,
        prompt_text=(
            "Extend this video in the exact same continuous unbroken Steadicam tracking shot with no scene cuts. "
            "She continues walking gracefully from the consultation room corridor into the bright front reception area of her "
            "Palermo veterinary clinic and arrives at the sleek wood-and-marble front reception counter / entrance desk "
            "shown in <IMAGE_REF_0> (with a MacBook Pro on the counter and glass street entrance behind her). Throughout her walk "
            "and arrival at the reception desk, her long wavy brunette hair sways naturally and she gestures expressively while "
            "looking directly at the camera and speaking in the exact same Argentine Rioplatense Spanish voice: "
            "\"Pasamos tus clientes, pacientes, historias clínicas y vacunas para que no pierdas ni una sola ficha. "
            "En horas ya tenés recordatorios automáticos por WhatsApp, sala de espera en vivo y todo en la nube.\" "
            "Use the given image as a reference for the front reception counter. No background music. Clear studio voice audio."
        ),
        duration_s=10,
        out_path=WORK_DIR / "v6B_turn2.mp4",
        prev_id=id1,
        ref_img_uri=mostrador_uri,
    )

    print("[v6B - Turno 3/4] Extendiendo +10s (20-30s: en el mostrador/escritorio de entrada de la veterinaria con su MacBook Pro)...")
    id3 = run_turn(
        client,
        prompt_text=(
            "Extend this video in the exact same continuous unbroken shot at the front reception counter / entrance desk "
            "of her Palermo veterinary clinic. She stands at the reception desk beside the open MacBook Pro, glancing briefly "
            "at the laptop screen and gesturing naturally with her hands while shifting her weight organically, her long wavy "
            "dark brown hair moving softly as she speaks directly to the camera in the exact same Argentine Rioplatense Spanish voice: "
            "\"Además, sumás las cuatro agendas inteligentes y el cobro de seña automático con Mercado Pago.\" "
            "After speaking, she continues moving naturally at the reception counter with a warm smile. "
            "No background music. Clear studio voice audio."
        ),
        duration_s=10,
        out_path=WORK_DIR / "v6B_turn3.mp4",
        prev_id=id2,
    )

    print("[v6B - Turno 4/4] Extendiendo +6s (30-36s: cierre CTA desde el mostrador de entrada en Palermo)...")
    out_v6b = WORK_DIR / "v6B_palermo_walk_full.mp4"
    run_turn(
        client,
        prompt_text=(
            "Extend this video in the exact same continuous unbroken shot at the front reception counter / entrance desk "
            "of her Palermo veterinary clinic. With warm, energetic body language beside the MacBook Pro on the reception counter, "
            "her long wavy brunette hair swaying softly and her hands gesturing invitingly, she speaks directly to the camera "
            "in the exact same Argentine Rioplatense Spanish voice: "
            "\"¡Escribinos hoy en MascotaMás y te migramos gratis en el día!\" "
            "After finishing the last word, she continues moving naturally at the reception desk with a radiant closed-lip smile "
            "at the camera. No background music. Clear studio voice audio."
        ),
        duration_s=6,
        out_path=out_v6b,
        prev_id=id3,
    )
    return str(out_v6b)


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=2) as ex:
        fa = ex.submit(generate_chain_v6A)
        fb = ex.submit(generate_chain_v6B)
        print("Cadenas completadas:", fa.result(), fb.result())
