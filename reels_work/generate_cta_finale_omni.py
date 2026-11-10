# -*- coding: utf-8 -*-
r"""
Genera en Gemini Omni 1.2 Flash (1080p, 9:16) el cierre con Llamada a la Acción (CTA) para MascotaMás
continuando inmediatamente después de la Pose 11 (En Cuclillas de Espalda mirando sobre el hombro):
la veterinaria se incorpora suavemente, gira hacia el frente mirando a cámara y pronuncia con lip-sync
natural en español argentino (es-AR) la llamada a la acción de MascotaMás.
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
from generate_video import generate_video, DEFAULT_MODEL

BASE_DIR = pathlib.Path(r"c:\IA\Edicion de videos")
WORK_DIR = BASE_DIR / "reels_work"
AVATAR_DIR = BASE_DIR / "assets" / "avatar_veterinaria_360"
ENV_FILE = BASE_DIR / ".env"

if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip().strip("\"'")

VID_PURE_30S = AVATAR_DIR / "Avatar_Veterinaria_360_y_11_Poses_Completo_IA_Omni_30s_1080p.mp4"
LAST_FRAME_PNG = WORK_DIR / "last_frame_pose11_30s.png"
URI_P1_FRENTE = "https://generativelanguage.googleapis.com/files/hp4f9ceu38fh"
URI_P11_CUC_ESPALDA = "https://generativelanguage.googleapis.com/files/3mx1hc3if7no"


def extract_last_frame():
    import subprocess
    ffmpeg_exe = str(BASE_DIR / "bin" / "ffmpeg" / "ffmpeg.exe")
    subprocess.run(
        [
            ffmpeg_exe, "-y",
            "-sseof", "-0.08",
            "-i", str(VID_PURE_30S),
            "-frames:v", "1",
            str(LAST_FRAME_PNG),
        ],
        check=True,
    )
    print(f"  -> Último frame extraído: {LAST_FRAME_PNG} ({LAST_FRAME_PNG.stat().st_size} bytes)")


def run_cta_job1():
    out_path = str(WORK_DIR / "omni_cta_finale_job1_firstframe_10s.mp4")
    prompt = (
        "Use the first image as the starting frame. In this exact same unbroken full-body studio shot, "
        "[0-2.5s] she smoothly and naturally stands up from her crouch and turns around to face the camera "
        "standing upright with a warm, radiant smile as shown in the reference image. "
        "[2.5-10.0s] Standing facing the camera, she gestures naturally with her hands and speaks directly to the camera "
        "with clear, accurate lip-sync in warm, energetic Buenos Aires Argentine Spanish (es-AR): "
        "\"¡Sumate hoy a MascotaMás! Pasamos toda tu veterinaria en el día y cien por ciento gratis. ¡Escribinos ahora!\" "
        "Upbeat studio house music softly in background."
    )
    generate_video(
        prompt=prompt,
        model=DEFAULT_MODEL,
        aspect_ratio="9:16",
        duration="10s",
        resolution="1080p",
        first_frame=str(LAST_FRAME_PNG),
        image_path=[URI_P1_FRENTE],
        output_path=out_path,
        timeout=900,
    )
    return out_path


def run_cta_job2():
    out_path = str(WORK_DIR / "omni_cta_finale_job2_r2v_10s.mp4")
    prompt = (
        "Full-body 9:16 studio shot of the exact same young female veterinarian in teal scrubs with a stethoscope around her neck "
        "standing in the bright studio with glass clinic partitions behind her, matching the reference images. "
        "[0-2.5s] Starting from a low crouch facing away while looking over her shoulder (first reference image), she smoothly and naturally stands up and turns around to face the camera standing upright (second reference image). "
        "[2.5-10.0s] Facing the camera with a warm, confident smile and natural hand gestures, she speaks directly to the camera "
        "with clear, accurate lip-sync in warm, energetic Buenos Aires Argentine Spanish (es-AR): "
        "\"¡Sumate hoy a MascotaMás! Pasamos toda tu veterinaria en el día y cien por ciento gratis. ¡Escribinos ahora!\" "
        "Upbeat studio house music softly in background."
    )
    generate_video(
        prompt=prompt,
        model=DEFAULT_MODEL,
        aspect_ratio="9:16",
        duration="10s",
        resolution="1080p",
        image_path=[URI_P11_CUC_ESPALDA, URI_P1_FRENTE],
        output_path=out_path,
        timeout=900,
    )
    return out_path


def main():
    extract_last_frame()
    with ThreadPoolExecutor(max_workers=2) as ex:
        f1 = ex.submit(run_cta_job1)
        f2 = ex.submit(run_cta_job2)
        for name, fut in [("CTA_Job1_FirstFrame", f1), ("CTA_Job2_R2V", f2)]:
            try:
                res = fut.result()
                print(f"[DONE {name}] -> {res}")
            except Exception as e:
                print(f"[WARN {name}] -> {e}")


if __name__ == "__main__":
    main()
