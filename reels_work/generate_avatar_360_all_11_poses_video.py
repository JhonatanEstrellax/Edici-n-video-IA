# -*- coding: utf-8 -*-
r"""
Genera el Video Completo del Giro 360° + LAS 11 POSES REALES del Avatar con movimiento lento, fluido y 100% natural
usando gemini-omni-1.2-flash (1080p, 9:16) sin omitir ninguna de las 11 imágenes generadas:

Las 11 imágenes incluidas en orden lento y natural:
  1. avatar_360_1_frente.png            (0° De Frente)
  2. avatar_360_2_tres_cuartos_izq.png  (-45° 3/4 Izquierda)
  3. avatar_360_3_lateral_izq.png       (-90° Lateral Izquierdo)
  4. avatar_360_6_espalda.png           (180° De Espalda)
  5. avatar_360_5_lateral_der.png       (+90° Lateral Derecho)
  6. avatar_360_4_tres_cuartos_der.png  (+45° 3/4 Derecha)
  --- (Ya generados en Avatar_Veterinaria_360_IA_Omni_Giro_Continuo_15s_1080p.mp4, id=v1_ChdKMGJ5YXFuMUJJV0d6N0lQbHJUNzhBdxIXSjBieWFxbjFCSVdHejdJUGxyVDc4QXc) ---
  7. avatar_360_7_espalda_puntitas.png  (De Espalda en Puntitas de Pie)
  8. avatar_360_8_espalda_agachada.png  (De Espalda Agachada / Inclinada mirando sobre el hombro)
  9. avatar_360_9_frente_agachada.png   (De Frente Agachada / Inclinada mirando a cámara)
 10. avatar_360_10_cuclillas_frente.png (En Cuclillas de Frente mirando a cámara)
 11. avatar_360_11_cuclillas_espalda.png(En Cuclillas de Espalda mirando sobre el hombro)
"""
import os
import sys
import shutil
import pathlib
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

SKILL_SCRIPTS_DIR = r"C:\Users\Demiante\.gemini\config\plugins\gemini-api\skills\gemini-omni-flash-api\scripts"
sys.path.insert(0, SKILL_SCRIPTS_DIR)
sys.path.insert(0, os.path.join(SKILL_SCRIPTS_DIR, "video"))
from generate_video import generate_video, resolve_or_upload_asset, DEFAULT_MODEL

BASE_DIR = pathlib.Path(r"c:\IA\Edicion de videos")
AVATAR_DIR = BASE_DIR / "assets" / "avatar_veterinaria_360"
EDITADOS_DIR = BASE_DIR / "editados"
WORK_DIR = BASE_DIR / "reels_work"
FFMPEG_BIN = str(BASE_DIR / "bin" / "ffmpeg" / "ffmpeg.exe")
ENV_FILE = BASE_DIR / ".env"

if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip().strip("\"'")

PART1_INTERACTION_ID = "v1_ChdKMGJ5YXFuMUJJV0d6N0lQbHJUNzhBdxIXSjBieWFxbjFCSVdHejdJUGxyVDc4QXc"
PART1_MP4 = str(AVATAR_DIR / "Avatar_Veterinaria_360_IA_Omni_Giro_Continuo_15s_1080p.mp4")


def main():
    print("=== PREPARANDO REFERENCIAS DE LAS 11 IMÁGENES + CLIP DE REFERENCIA DE CÁMARA ===")

    # Extraer los últimos 3 segundos de PART1_MP4 como video_reference para mantener exactamente el mismo estudio, luz y encuadre
    ref_3s_mp4 = str(WORK_DIR / "omni_360_part1_last3s_ref.mp4")
    subprocess.run(
        [
            FFMPEG_BIN, "-y",
            "-ss", "12.0", "-t", "3.0",
            "-i", PART1_MP4,
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-an",
            ref_3s_mp4,
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    vid_ref_uri, _ = resolve_or_upload_asset(ref_3s_mp4, "video/mp4")
    print(f"  -> [Uploaded Video Ref 3s] {vid_ref_uri}")

    pose_files = {
        "p1_frente": str(AVATAR_DIR / "avatar_360_1_frente.png"),
        "p6_espalda": str(AVATAR_DIR / "avatar_360_6_espalda.png"),
        "p7_puntitas": str(AVATAR_DIR / "avatar_360_7_espalda_puntitas.png"),
        "p8_esp_agachada": str(AVATAR_DIR / "avatar_360_8_espalda_agachada.png"),
        "p9_fre_agachada": str(AVATAR_DIR / "avatar_360_9_frente_agachada.png"),
        "p10_cuc_frente": str(AVATAR_DIR / "avatar_360_10_cuclillas_frente.png"),
        "p11_cuc_espalda": str(AVATAR_DIR / "avatar_360_11_cuclillas_espalda.png"),
    }

    uris = {}
    for k, fpath in pose_files.items():
        uri, _ = resolve_or_upload_asset(fpath, "image/png")
        uris[k] = uri
        print(f"  -> [Uploaded {k}] {uri}")

    out_ext_turn2 = str(WORK_DIR / "omni_11poses_ext_turn2_10s.mp4")
    out_r2v_all5_15s = str(WORK_DIR / "omni_11poses_r2v_7_to_11_15s.mp4")
    out_r2v_part2a_12s = str(WORK_DIR / "omni_11poses_part2a_7_8_9_12s.mp4")
    out_r2v_part2b_12s = str(WORK_DIR / "omni_11poses_part2b_9_10_11_12s.mp4")

    jobs = [
        # Job A: Extensión directa de la interacción v1_... (+10s) con las poses 7, 8, 9, 10, 11
        {
            "name": "Extend_Turn2_Poses_7_to_11_10s",
            "kwargs": {
                "prompt": (
                    "Extend this video in the exact same unbroken full-body studio shot with slow, fluid, unhurried, "
                    "and completely natural body movement transitioning through all five reference images in sequence: "
                    "[0-2s] She slowly turns her back and gently rises up onto her tiptoes as shown in the first reference image. "
                    "[2-4s] She slowly lowers her heels and leans her torso slightly forward from behind while looking back over her shoulder at the camera as shown in the second reference image. "
                    "[4-6s] She slowly pivots to face the camera while leaning slightly forward with her hands on her knees and a warm smile as shown in the third reference image. "
                    "[6-8s] She slowly bends her knees to lower into a natural front crouching pose facing the camera as shown in the fourth reference image. "
                    "[8-10s] She slowly pivots in her crouch to show her back view while turning her head over her shoulder to smile at the camera as shown in the fifth reference image. "
                    "Keep movement slow, graceful, and natural. Upbeat studio house music. No dialogue."
                ),
                "model": DEFAULT_MODEL,
                "aspect_ratio": "9:16",
                "duration": "10s",
                "resolution": "1080p",
                "previous_interaction_id": PART1_INTERACTION_ID,
                "image_path": [
                    uris["p7_puntitas"],
                    uris["p8_esp_agachada"],
                    uris["p9_fre_agachada"],
                    uris["p10_cuc_frente"],
                    uris["p11_cuc_espalda"],
                ],
                "output_path": out_ext_turn2,
                "timeout": 900,
            },
        },
        # Job B: 15s R2V dedicado a las Poses 7, 8, 9, 10, 11 (3 segundos lentos por cada pose) con video_reference del estudio
        {
            "name": "R2V_Poses_7_to_11_Slow_15s",
            "kwargs": {
                "prompt": (
                    "In a single continuous unbroken 9:16 full-body shot in the exact same studio room, lighting, and camera framing "
                    "as the reference video, the young Argentine female veterinarian in her teal veterinary scrub uniform and stethoscope "
                    "transitions slowly, smoothly, and naturally through every single one of the five pose reference images without rushing: "
                    "[0-3s] Starting from standing, she slowly turns away and rises onto her tiptoes from behind as shown in the first reference image. "
                    "[3-6s] She slowly lowers her heels and leans gently forward from behind while glancing over her shoulder at the camera as shown in the second reference image. "
                    "[6-9s] She slowly turns toward the camera and leans gently forward resting her hands near her knees with a warm smile as shown in the third reference image. "
                    "[9-12s] She slowly bends her knees to lower smoothly into a front crouch facing the camera as shown in the fourth reference image. "
                    "[12-15s] She slowly rotates in her crouch to a back view while looking back over her right shoulder at the camera with a warm smile as shown in the fifth reference image. "
                    "All transitions between movements are slow, fluid, and natural. Upbeat studio house music. No dialogue."
                ),
                "model": DEFAULT_MODEL,
                "aspect_ratio": "9:16",
                "duration": "15s",
                "resolution": "1080p",
                "video_reference": [vid_ref_uri],
                "image_path": [
                    uris["p7_puntitas"],
                    uris["p8_esp_agachada"],
                    uris["p9_fre_agachada"],
                    uris["p10_cuc_frente"],
                    uris["p11_cuc_espalda"],
                ],
                "output_path": out_r2v_all5_15s,
                "timeout": 900,
            },
        },
        # Job C1: 12s Ultra-Lento para Poses 7 (Espalda Puntitas), 8 (Espalda Agachada) y 9 (Frente Agachada) — 4s por pose
        {
            "name": "R2V_Part2A_Poses_7_8_9_UltraSlow_12s",
            "kwargs": {
                "prompt": (
                    "In a single continuous unbroken 9:16 full-body shot in the exact same studio room and camera framing as the reference video, "
                    "the female veterinarian in her teal scrub uniform performs a slow, graceful, natural sequence through the reference images: "
                    "[0-4s] She turns smoothly to face away from the camera and rises slowly onto her tiptoes as shown in thesecond reference image. "
                    "[4-8s] She slowly lowers her heels to the floor and leans gently forward from behind while turning her head over her shoulder toward the camera as shown in the third reference image. "
                    "[8-12s] She slowly turns around to face the camera and leans gently forward with a warm natural smile as shown in the fourth reference image. "
                    "Every movement is slow, unhurried, and natural. Upbeat studio house music. No dialogue."
                ),
                "model": DEFAULT_MODEL,
                "aspect_ratio": "9:16",
                "duration": "12s",
                "resolution": "1080p",
                "video_reference": [vid_ref_uri],
                "image_path": [
                    uris["p6_espalda"],
                    uris["p7_puntitas"],
                    uris["p8_esp_agachada"],
                    uris["p9_fre_agachada"],
                ],
                "output_path": out_r2v_part2a_12s,
                "timeout": 900,
            },
        },
        # Job C2: 12s Ultra-Lento para Poses 9 (Frente Agachada), 10 (Cuclillas Frente), 11 (Cuclillas Espalda) y vuelta a 1 (Frente) — 4s por pose
        {
            "name": "R2V_Part2B_Poses_9_10_11_UltraSlow_12s",
            "kwargs": {
                "prompt": (
                    "In a single continuous unbroken 9:16 full-body shot in the exact same studio room and camera framing as the reference video, "
                    "the female veterinarian in her teal scrub uniform performs a slow, graceful, natural sequence through the reference images: "
                    "[0-3s] She begins leaning gently forward facing the camera with a warm smile as shown in the first reference image. "
                    "[3-7s] She slowly and smoothly bends her knees to lower into a natural front crouching pose facing the camera as shown in the second reference image. "
                    "[7-10s] She slowly pivots in her crouching pose to face away from the camera while looking back over her shoulder with a warm smile as shown in the third reference image. "
                    "[10-12s] She slowly rises back up to a standing front pose facing the camera as shown in the fourth reference image. "
                    "Every movement is slow, unhurried, and natural. Upbeat studio house music. No dialogue."
                ),
                "model": DEFAULT_MODEL,
                "aspect_ratio": "9:16",
                "duration": "12s",
                "resolution": "1080p",
                "video_reference": [vid_ref_uri],
                "image_path": [
                    uris["p9_fre_agachada"],
                    uris["p10_cuc_frente"],
                    uris["p11_cuc_espalda"],
                    uris["p1_frente"],
                ],
                "output_path": out_r2v_part2b_12s,
                "timeout": 900,
            },
        },
    ]

    def run_safe(job):
        name = job["name"]
        print(f"  -> [START] {name}...")
        try:
            generate_video(**job["kwargs"])
            print(f"  -> [SUCCESS] {name} -> {job['kwargs']['output_path']}")
            return name, True, job["kwargs"]["output_path"]
        except Exception as e:
            print(f"  -> [WARN] {name} failed: {e}")
            return name, False, str(e)

    results = {}
    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = [ex.submit(run_safe, j) for j in jobs]
        for fut in as_completed(futures):
            name, ok, info = fut.result()
            results[name] = (ok, info)

    print("\n=== RESUMEN DE GENERACIONES ===")
    for k, (ok, info) in results.items():
        print(f"  - {k}: {'OK' if ok else 'FAILED'} ({info})")


if __name__ == "__main__":
    main()
