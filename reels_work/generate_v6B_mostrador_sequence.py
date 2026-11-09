# -*- coding: utf-8 -*-
"""
Genera la secuencia continua Multi-Turn (10s -> +10s -> +5s = 25s continuos)
para los segundos 11.52s a 33.60s de v6B: la veterinaria caminando desde el pasillo del consultorio
hasta el mostrador / escritorio de entrada de su veterinaria en Palermo con la MacBook Pro sobre el mostrador.
"""
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


def run_turn(client, prompt_text, duration_s, out_path: pathlib.Path, prev_id=None, first_frame_uri=None):
    input_parts = []
    if first_frame_uri:
        uri, mime = first_frame_uri
        input_parts.append({"type": "image", "uri": uri, "mime_type": mime})
        if "<FIRST_FRAME>" not in prompt_text:
            prompt_text = f"<FIRST_FRAME> {prompt_text}"

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


def main():
    client = genai.Client(http_options=types.HttpOptions(timeout=900_000))
    mostrador_uri = resolve_or_upload_asset(str(WORK_DIR / "avatar_v6B_mostrador_entrada_ref.png"), "image/png")

    print("[v6B Mostrador - Turno 1/3] Generando 10s (llegando caminando al mostrador de entrada en Palermo con MacBook Pro)...")
    id1 = run_turn(
        client,
        prompt_text=(
            "Use this image as the starting frame. In a single continuous unbroken 9:16 vertical Steadicam shot "
            "inside a bright modern veterinary clinic in Palermo, Buenos Aires, this young Argentine female veterinarian "
            "with long wavy dark brown hair and a dark-teal scrub top with a stethoscope walks smoothly a couple of steps "
            "along the sleek wood-and-marble front reception counter and entrance desk beside the open laptop, gesturing "
            "naturally with her hands while her hair and shoulders move fluidly as she speaks directly to the camera in "
            "Spanish with a natural Argentine Rioplatense accent: "
            "\"Pasamos tus clientes, pacientes, historias clínicas y vacunas para que no pierdas ni una sola ficha. "
            "En horas ya tenés recordatorios automáticos por WhatsApp, sala de espera en vivo y todo en la nube.\" "
            "Keep a constant medium-full camera distance. No background music. Clear studio voice audio."
        ),
        duration_s=10,
        out_path=WORK_DIR / "v6B_mostrador_t1.mp4",
        first_frame_uri=mostrador_uri,
    )

    print("[v6B Mostrador - Turno 2/3] Extendiendo +10s (en el mostrador de entrada trabajando con su laptop)...")
    id2 = run_turn(
        client,
        prompt_text=(
            "Extend this video in the exact same continuous unbroken shot at the front reception counter and entrance desk "
            "of her Palermo veterinary clinic. Keep the same medium-full framing. She shifts her posture naturally beside "
            "the open laptop on the marble reception counter, gesturing with her hands and moving her long wavy brown hair "
            "and shoulders fluidly while speaking directly to the camera in the exact same Argentine Rioplatense Spanish voice: "
            "\"Además, sumás las cuatro agendas inteligentes y el cobro de seña automático con Mercado Pago.\" "
            "After speaking, she glances briefly at the laptop on the counter and back at the camera with a warm smile. "
            "No background music. Clear studio voice audio."
        ),
        duration_s=10,
        out_path=WORK_DIR / "v6B_mostrador_t2.mp4",
        prev_id=id1,
    )

    print("[v6B Mostrador - Turno 3/3] Extendiendo +5s (cierre CTA desde el mostrador de entrada en Palermo)...")
    run_turn(
        client,
        prompt_text=(
            "Extend this video in the exact same continuous unbroken shot at the front reception counter and entrance desk "
            "of her Palermo veterinary clinic. With warm, energetic body language beside the laptop on the reception counter, "
            "her long wavy brown hair swaying softly and her hands gesturing invitingly, she speaks directly to the camera "
            "in the exact same Argentine Rioplatense Spanish voice: "
            "\"¡Escribinos hoy en MascotaMás y te migramos gratis en el día!\" "
            "After finishing the last word, she continues moving naturally at the reception desk with a warm closed-lip smile "
            "at the camera. No background music. Clear studio voice audio."
        ),
        duration_s=5,
        out_path=WORK_DIR / "v6B_mostrador_t3.mp4",
        prev_id=id2,
    )
    print("Secuencia v6B mostrador completada con éxito.")


if __name__ == "__main__":
    main()
