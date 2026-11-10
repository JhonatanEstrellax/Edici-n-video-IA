# -*- coding: utf-8 -*-
r"""
Completa el Turno 3 (24.0s -> 30.0s, +6s) partiendo directamente del Turno 2 ya generado
(id=v1_ChdKMGJ5YXFuMUJJV0d6N0lQbHJUNzhBdxIXM1V2eWF1YllPNjNVejdJUDF1YnVzUTA) en gemini-omni-1.2-flash (1080p, 9:16):
- [0.0s - 3.0s]: Pose 10 (En Cuclillas Completas de Frente mirando a cámara - avatar_360_10_cuclillas_frente.png)
- [3.0s - 6.0s]: Pose 11 (En Cuclillas Completas de Espalda mirando sobre el hombro - avatar_360_11_cuclillas_espalda.png)
"""
import os
import sys
import pathlib

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

T2_ID = "v1_ChdKMGJ5YXFuMUJJV0d6N0lQbHJUNzhBdxIXM1V2eWF1YllPNjNVejdJUDF1YnVzUTA"
URI_P10_CUC_FRENTE = "https://generativelanguage.googleapis.com/files/cooshu7kqdkb"
URI_P11_CUC_ESPALDA = "https://generativelanguage.googleapis.com/files/3mx1hc3if7no"


def main():
    out_t3 = str(AVATAR_DIR / "Avatar_Veterinaria_360_y_11_Poses_Completo_IA_Omni_30s_1080p.mp4")
    print("  -> [Chain 30s - Turno 3 (24s->30s, +6s)] Poses 10 (Cuclillas Frente) -> 11 (Cuclillas Espalda)...")
    client = genai.Client(http_options=types.HttpOptions(timeout=900_000))
    prompt = (
        "Extend this video in the exact same unbroken full-body studio shot with slow, unhurried, "
        "fluid, and completely natural movement transitioning clearly through both reference images: "
        "[0-3.0s] From her front-leaning pose, she slowly and smoothly bends her knees all the way down into a full deep front crouch (cuclillas de frente) facing the camera with her arms resting on her knees and a warm smile, holding the exact pose shown in the first reference image. "
        "[3.0-6.0s] Staying low, she slowly pivots 180 degrees and lowers into a full deep back crouch (cuclillas de espalda) facing away from the camera with her hands on her knees while turning her head over her right shoulder to smile warmly at the camera, holding the exact pose shown in the second reference image. "
        "Every transition is slow, smooth, and natural. Upbeat studio house music. No dialogue."
    )
    input_parts = [
        {"type": "image", "uri": URI_P10_CUC_FRENTE, "mime_type": "image/png"},
        {"type": "image", "uri": URI_P11_CUC_ESPALDA, "mime_type": "image/png"},
        {"type": "text", "text": prompt},
    ]
    video_config = {
        "type": "video",
        "delivery": "uri",
        "aspect_ratio": "9:16",
        "duration": "6s",
        "resolution": "1080p",
    }
    interaction = client.interactions.create(
        model=DEFAULT_MODEL,
        previous_interaction_id=T2_ID,
        input=input_parts,
        response_format=video_config,
    )
    output_video = getattr(interaction, "output_video", None)
    if not output_video or not getattr(output_video, "uri", None):
        raise RuntimeError(f"No output_video in response (id={getattr(interaction, 'id', None)})")
    target = getattr(output_video, "uri", output_video)
    video_bytes = client.files.download(file=target)
    with open(out_t3, "wb") as f:
        f.write(video_bytes)
    print(f"  -> [SAVED] {out_t3} ({len(video_bytes)} bytes) | id={interaction.id}")


if __name__ == "__main__":
    main()
