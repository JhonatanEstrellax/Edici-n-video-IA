# -*- coding: utf-8 -*-
r"""
Completa la cadena continua de 30.0 segundos (1080x1920 @ 24fps, un solo plano secuencia sin cortes)
en gemini-omni-1.2-flash garantizando que NO se omita ninguna de las 11 imágenes y que cada transición
sea lenta, pausada y 100% natural:

- Turno 1 (0.0s - 15.0s, ya generado: v1_ChdKMGJ5YXFuMUJJV0d6N0lQbHJUNzhBdxIXSjBieWFxbjFCSVdHejdJUGxyVDc4QXc):
    Pose 1 (0° Frente) -> Pose 2 (-45° 3/4 Izq) -> Pose 3 (-90° Lateral Izq) ->
    Pose 4 (180° De Espalda) -> Pose 5 (+90° Lateral Der) -> Pose 6 (+45° 3/4 Der) -> Frente
- Turno 2 (15.0s - 24.0s, +9s de extensión lenta dedicada SOLO a las Poses 7, 8 y 9 — 3.0s por pose):
    Pose 7 (De Espalda en Puntitas de Pie) ->
    Pose 8 (De Espalda Agachada / Inclinada hacia adelante con manos en rodillas mirando sobre el hombro) ->
    Pose 9 (De Frente Agachada / Inclinada hacia adelante con manos en rodillas mirando a cámara)
- Turno 3 (24.0s - 30.0s, +6s de extensión lenta dedicada SOLO a las Poses 10 y 11 — 3.0s por pose):
    Pose 10 (En Cuclillas Completas de Frente mirando a cámara) ->
    Pose 11 (En Cuclillas Completas de Espalda mirando sobre el hombro a cámara)
"""
import os
import sys
import pathlib
from concurrent.futures import ThreadPoolExecutor

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

SKILL_SCRIPTS_DIR = r"C:\Users\Demiante\.gemini\config\plugins\gemini-api\skills\gemini-omni-flash-api\scripts"
sys.path.insert(0, SKILL_SCRIPTS_DIR)
sys.path.insert(0, os.path.join(SKILL_SCRIPTS_DIR, "video"))
from generate_video import DEFAULT_MODEL
from google import genai
from google.genai import types

BASE_DIR = pathlib.Path(r"c:\IA\Edicion de videos")
WORK_DIR = BASE_DIR / "reels_work"
AVATAR_DIR = BASE_DIR / "assets" / "avatar_veterinaria_360"
ENV_FILE = BASE_DIR / ".env"

if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip().strip("\"'")

TURN1_ID = "v1_ChdKMGJ5YXFuMUJJV0d6N0lQbHJUNzhBdxIXSjBieWFxbjFCSVdHejdJUGxyVDc4QXc"
PREV_25S_ID = "v1_ChdKMGJ5YXFuMUJJV0d6N0lQbHJUNzhBdxIXMlVqeWF1ZlJKNzJGejdJUHhkckgyQUk"

# Active File URIs already uploaded
URI_P7_PUNTITAS = "https://generativelanguage.googleapis.com/files/s3ygzztm1lrq"
URI_P8_ESP_AGACHADA = "https://generativelanguage.googleapis.com/files/d4ifim1k6dqn"
URI_P9_FRE_AGACHADA = "https://generativelanguage.googleapis.com/files/b7qrxcsb67tq"
URI_P10_CUC_FRENTE = "https://generativelanguage.googleapis.com/files/cooshu7kqdkb"
URI_P11_CUC_ESPALDA = "https://generativelanguage.googleapis.com/files/3mx1hc3if7no"


def run_interaction_and_get_id(prompt, duration_s, prev_id, ref_uris, out_mp4):
    client = genai.Client(http_options=types.HttpOptions(timeout=900_000))
    input_parts = [{"type": "image", "uri": u, "mime_type": "image/png"} for u in ref_uris]
    input_parts.append({"type": "text", "text": prompt})
    video_config = {
        "type": "video",
        "delivery": "uri",
        "aspect_ratio": "9:16",
        "duration": f"{duration_s}s",
        "resolution": "1080p",
    }
    interaction = client.interactions.create(
        model=DEFAULT_MODEL,
        previous_interaction_id=prev_id,
        input=input_parts,
        response_format=video_config,
    )
    output_video = getattr(interaction, "output_video", None)
    if not output_video or not getattr(output_video, "uri", None):
        raise RuntimeError(f"No output_video in response (id={getattr(interaction, 'id', None)})")
    target = getattr(output_video, "uri", output_video)
    video_bytes = client.files.download(file=target)
    with open(out_mp4, "wb") as f:
        f.write(video_bytes)
    print(f"  -> [SAVED] {out_mp4} ({len(video_bytes)} bytes) | id={interaction.id}")
    return interaction.id


def chain_30s_slow_all_11():
    out_t2 = str(WORK_DIR / "omni_chain30_turn2_poses7_8_9_24s.mp4")
    out_t3 = str(AVATAR_DIR / "Avatar_Veterinaria_360_y_11_Poses_Completo_IA_Omni_30s_1080p.mp4")

    print("  -> [Chain 30s - Turno 2 (15s->24s, +9s)] Poses 7 (Espalda Puntitas) -> 8 (Espalda Agachada) -> 9 (Frente Agachada)...")
    t2_id = run_interaction_and_get_id(
        prompt=(
            "Extend this video in the exact same unbroken full-body studio shot with slow, unhurried, "
            "fluid, and completely natural movement transitioning clearly through all three reference images: "
            "[0-3.0s] She slowly turns her back to the camera and rises up onto her tiptoes while reaching her right hand upward, holding the tiptoe pose shown in the first reference image. "
            "[3.0-6.0s] Remaining with her back to the camera, she slowly lowers her heels to the floor, rests both hands on the back of her thighs/knees, and leans her upper body forward at the waist while turning her head over her right shoulder to smile at the camera, clearly holding the back-leaning pose shown in the second reference image. "
            "[6.0-9.0s] Keeping her torso leaned slightly forward with both hands resting on her knees, she slowly pivots around to face the camera with a warm smile, holding the front-leaning pose shown in the third reference image. "
            "Every transition is slow, smooth, and natural. Upbeat studio house music. No dialogue."
        ),
        duration_s=9,
        prev_id=TURN1_ID,
        ref_uris=[URI_P7_PUNTITAS, URI_P8_ESP_AGACHADA, URI_P9_FRE_AGACHADA],
        out_mp4=out_t2,
    )

    print("  -> [Chain 30s - Turno 3 (24s->30s, +6s)] Poses 10 (Cuclillas Frente) -> 11 (Cuclillas Espalda)...")
    t3_id = run_interaction_and_get_id(
        prompt=(
            "Extend this video in the exact same unbroken full-body studio shot with slow, unhurried, "
            "fluid, and completely natural movement transitioning clearly through both reference images: "
            "[0-3.0s] From her front-leaning pose, she slowly and smoothly bends her knees all the way down into a full deep front crouch (cuclillas de frente) facing the camera with her arms resting on her knees and a warm smile, holding the exact pose shown in the first reference image. "
            "[3.0-6.0s] Staying low, she slowly pivots 180 degrees and lowers into a full deep back crouch (cuclillas de espalda) facing away from the camera with her hands on her knees while turning her head over her right shoulder to smile warmly at the camera, holding the exact pose shown in the second reference image. "
            "Every transition is slow, smooth, and natural. Upbeat studio house music. No dialogue."
        ),
        duration_s=6,
        prev_id=t2_id,
        ref_uris=[URI_P10_CUC_FRENTE, URI_P11_CUC_ESPALDA],
        out_mp4=out_t3,
    )
    return out_t3


def extend_existing_25s_to_30s():
    out_alt_30s = str(WORK_DIR / "omni_alt_25s_to_30s_pose8_and_11.mp4")
    print("  -> [Alt 25s->30s (+5s)] Añadiendo Pose 8 (Espalda Agachada) y Pose 11 (Cuclillas Espalda) al video de 25s...")
    run_interaction_and_get_id(
        prompt=(
            "Extend this video in the exact same unbroken full-body studio shot with slow, smooth, and natural movement: "
            "[0-2.5s] Standing with her back to the camera, she slowly rests her hands on her thighs/knees and leans her torso forward while looking back over her right shoulder with a warm smile, holding the exact back-leaning pose shown in the first reference image. "
            "[2.5-5.0s] Staying facing away from the camera, she slowly bends her knees all the way down into a full deep back crouch (cuclillas de espalda) while turning her head over her right shoulder to smile at the camera, holding the exact pose shown in the second reference image. "
            "Every movement is slow, unhurried, and natural. Upbeat studio house music. No dialogue."
        ),
        duration_s=5,
        prev_id=PREV_25S_ID,
        ref_uris=[URI_P8_ESP_AGACHADA, URI_P11_CUC_ESPALDA],
        out_mp4=out_alt_30s,
    )
    return out_alt_30s


def main():
    with ThreadPoolExecutor(max_workers=2) as ex:
        f1 = ex.submit(chain_30s_slow_all_11)
        f2 = ex.submit(extend_existing_25s_to_30s)
        for name, fut in [("Chain_30s_15_9_6", f1), ("Alt_30s_25_5", f2)]:
            try:
                res = fut.result()
                print(f"[DONE {name}] -> {res}")
            except Exception as e:
                print(f"[WARN {name}] -> {e}")


if __name__ == "__main__":
    main()
