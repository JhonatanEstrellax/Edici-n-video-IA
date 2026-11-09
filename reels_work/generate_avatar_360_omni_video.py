# -*- coding: utf-8 -*-
r"""
Genera el Video 360° Real del Avatar de la Veterinaria de MascotaMás usando el mejor modelo de video aplicable:
gemini-omni-1.2-flash (1080p, 9:16) via Interactions API y Files API.

Ejecuta en paralelo 4 generaciones con gemini-omni-1.2-flash (1080p, 9:16):
1. Giro 360° Continuo en 1 sola toma de 15s guiado por las 6 imágenes de referencia del turnaround (R2V: 0°, -45°, -90°, 180°, +90°, +45°).
2. Interpolación Keyframe Exacta Parte 1 (8s, 1080p): Frente (0°) -> De Espalda (180°) pasando por perfil izquierdo.
3. Interpolación Keyframe Exacta Parte 2 (8s, 1080p): De Espalda (180°) -> Frente (360°) pasando por perfil derecho.
4. Interpolación Keyframe Exacta Parte 3 (8s, 1080p): Poses Dinámicas (Espalda en Puntitas -> Giro a Cuclillas de Frente).

Y exporta los videos finales en:
- c:\IA\Edicion de videos\assets\avatar_veterinaria_360\
- c:\IA\Edicion de videos\editados\
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


def main():
    print(f"=== GENERANDO VIDEO 360° DEL AVATAR CON {DEFAULT_MODEL} (1080p 9:16) ===")

    # 1. Subir los keyframes del 360° una sola vez a Files API para reutilizar sus URIs en paralelo
    pose_files = {
        "frente": str(AVATAR_DIR / "avatar_360_1_frente.png"),
        "q_izq": str(AVATAR_DIR / "avatar_360_2_tres_cuartos_izq.png"),
        "lat_izq": str(AVATAR_DIR / "avatar_360_3_lateral_izq.png"),
        "q_der": str(AVATAR_DIR / "avatar_360_4_tres_cuartos_der.png"),
        "lat_der": str(AVATAR_DIR / "avatar_360_5_lateral_der.png"),
        "espalda": str(AVATAR_DIR / "avatar_360_6_espalda.png"),
        "puntitas": str(AVATAR_DIR / "avatar_360_7_espalda_puntitas.png"),
        "cuclillas_frente": str(AVATAR_DIR / "avatar_360_10_cuclillas_frente.png"),
    }

    uris = {}
    for k, fpath in pose_files.items():
        uri, _ = resolve_or_upload_asset(fpath, "image/png")
        uris[k] = uri
        print(f"  -> [Uploaded {k}] {uri}")

    out_r2v_15s = str(AVATAR_DIR / "Avatar_Veterinaria_360_IA_Omni_Giro_Continuo_15s_1080p.mp4")
    out_seg1 = str(WORK_DIR / "omni_360_seg1_0_to_180.mp4")
    out_seg2 = str(WORK_DIR / "omni_360_seg2_180_to_360.mp4")
    out_seg3 = str(WORK_DIR / "omni_360_seg3_puntitas_a_cuclillas.mp4")

    jobs = [
        {
            "name": "Giro_360_Continuo_R2V_15s",
            "kwargs": {
                "prompt": (
                    "In a single continuous unbroken 9:16 full-body studio shot with no scene cuts, "
                    "the glamorous young Argentine female veterinarian shown in the six reference images "
                    "(which show her exact front 0-degree view, 3/4 left view, left profile view, full back 180-degree view, "
                    "right profile view, and 3/4 right view in her fitted dark-teal V-neck veterinary scrub suit with a stethoscope "
                    "around her neck and white sneakers) stands in the center of a clean bright studio cyclorama and slowly, "
                    "smoothly, and gracefully rotates a full 360 degrees in place so the camera captures her complete 360-degree "
                    "body turnaround from front, through her left profile, to her back view, through her right profile, and returning "
                    "to face the camera with a warm confident smile. Stylish upbeat studio house music. No dialogue."
                ),
                "model": DEFAULT_MODEL,
                "aspect_ratio": "9:16",
                "duration": "15s",
                "resolution": "1080p",
                "image_path": [
                    uris["frente"],
                    uris["q_izq"],
                    uris["lat_izq"],
                    uris["espalda"],
                    uris["lat_der"],
                    uris["q_der"],
                ],
                "output_path": out_r2v_15s,
                "timeout": 900,
            },
        },
        {
            "name": "Keyframe_Seg1_Frente_a_Espalda_8s",
            "kwargs": {
                "prompt": (
                    "Use the first image as the starting frame and the second image as the final frame. "
                    "In a single continuous unbroken full-body studio shot with no cuts, the glamorous female veterinarian "
                    "in her fitted dark-teal V-neck scrub suit and white sneakers smoothly and gracefully rotates 180 degrees "
                    "in place on the studio floor, turning from facing the camera in front view (first image) through her "
                    "3/4 left and left profile views to end facing away from the camera in full back view (second image). "
                    "Keep camera distance fixed showing her full body head to toe. Upbeat studio house music. No dialogue."
                ),
                "model": DEFAULT_MODEL,
                "aspect_ratio": "9:16",
                "duration": "8s",
                "resolution": "1080p",
                "first_frame": uris["frente"],
                "last_frame": uris["espalda"],
                "output_path": out_seg1,
                "timeout": 900,
            },
        },
        {
            "name": "Keyframe_Seg2_Espalda_a_Frente_8s",
            "kwargs": {
                "prompt": (
                    "Use the first image as the starting frame and the second image as the final frame. "
                    "In a single continuous unbroken full-body studio shot with no cuts, the glamorous female veterinarian "
                    "in her fitted dark-teal V-neck scrub suit and white sneakers smoothly and gracefully rotates 180 degrees "
                    "in place on the studio floor, turning from facing away from the camera in back view (first image) through "
                    "her right profile and 3/4 right views to end facing the camera in front view with a warm smile (second image). "
                    "Keep camera distance fixed showing her full body head to toe. Upbeat studio house music. No dialogue."
                ),
                "model": DEFAULT_MODEL,
                "aspect_ratio": "9:16",
                "duration": "8s",
                "resolution": "1080p",
                "first_frame": uris["espalda"],
                "last_frame": uris["frente"],
                "output_path": out_seg2,
                "timeout": 900,
            },
        },
        {
            "name": "Keyframe_Seg3_Poses_Dinamicas_8s",
            "kwargs": {
                "prompt": (
                    "Use the first image as the starting frame and the second image as the final frame. "
                    "In a single continuous unbroken full-body studio shot with no cuts, the glamorous female veterinarian "
                    "in her fitted dark-teal V-neck scrub suit starts on tiptoes from behind (first image), smoothly turns "
                    "around toward the camera, and gracefully lowers into a poised front squat pose looking at the camera "
                    "with a warm smile (second image). Keep camera distance fixed showing her full body. Upbeat studio house music. No dialogue."
                ),
                "model": DEFAULT_MODEL,
                "aspect_ratio": "9:16",
                "duration": "8s",
                "resolution": "1080p",
                "first_frame": uris["puntitas"],
                "last_frame": uris["cuclillas_frente"],
                "output_path": out_seg3,
                "timeout": 900,
            },
        },
    ]

    def run_job(job):
        print(f"  -> [START] {job['name']}...")
        generate_video(**job["kwargs"])
        print(f"  -> [DONE] {job['name']} -> {job['kwargs']['output_path']}")
        return job["name"]

    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = [ex.submit(run_job, j) for j in jobs]
        for fut in as_completed(futures):
            print(f"  [COMPLETED] {fut.result()}")

    # 2. Unir Seg1 (0°->180°) + Seg2 (180°->360°) en un Loop 360° Perfecto de 16s
    out_loop_16s = str(AVATAR_DIR / "Avatar_Veterinaria_360_IA_Omni_Loop_Exacto_16s_1080p.mp4")
    concat_16_txt = WORK_DIR / "concat_360_16s.txt"
    concat_16_txt.write_text(
        f"file '{out_seg1.replace(chr(92), '/')}'\nfile '{out_seg2.replace(chr(92), '/')}'\n",
        encoding="utf-8",
    )
    subprocess.run(
        [
            FFMPEG_BIN, "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_16_txt),
            "-c:v", "libx264", "-preset", "fast", "-crf", "16",
            "-c:a", "aac", "-b:a", "192k",
            out_loop_16s,
        ],
        check=True,
    )
    print(f"  -> [OK] Loop 360° Exacto (16s) guardado en: {out_loop_16s}")

    # 3. Unir Seg1 + Seg2 + Seg3 en el Master 360° + Poses Dinámicas (24s) con música House 125 BPM sincronizada
    out_master_24s = str(AVATAR_DIR / "Avatar_Veterinaria_360_IA_Omni_Master_Completo_24s_1080p.mp4")
    concat_24_txt = WORK_DIR / "concat_360_24s.txt"
    concat_24_txt.write_text(
        f"file '{out_seg1.replace(chr(92), '/')}'\n"
        f"file '{out_seg2.replace(chr(92), '/')}'\n"
        f"file '{out_seg3.replace(chr(92), '/')}'\n",
        encoding="utf-8",
    )
    house_wav = str(WORK_DIR / "v7_lyria_house_arriba.wav")
    if os.path.exists(house_wav):
        subprocess.run(
            [
                FFMPEG_BIN, "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(concat_24_txt),
                "-i", house_wav,
                "-map", "0:v:0", "-map", "1:a:0",
                "-shortest",
                "-c:v", "libx264", "-preset", "fast", "-crf", "16",
                "-c:a", "aac", "-b:a", "192k",
                out_master_24s,
            ],
            check=True,
        )
    else:
        subprocess.run(
            [
                FFMPEG_BIN, "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(concat_24_txt),
                "-c:v", "libx264", "-preset", "fast", "-crf", "16",
                "-c:a", "aac", "-b:a", "192k",
                out_master_24s,
            ],
            check=True,
        )
    print(f"  -> [OK] Master Completo 360° + Poses (24s) guardado en: {out_master_24s}")

    # 4. Copiar también a la carpeta editados/ del proyecto
    EDITADOS_DIR.mkdir(parents=True, exist_ok=True)
    for fpath in [out_r2v_15s, out_loop_16s, out_master_24s]:
        if os.path.exists(fpath):
            shutil.copy2(fpath, str(EDITADOS_DIR / os.path.basename(fpath)))
            print(f"  -> Copiado a editados/: {os.path.basename(fpath)}")


if __name__ == "__main__":
    main()
