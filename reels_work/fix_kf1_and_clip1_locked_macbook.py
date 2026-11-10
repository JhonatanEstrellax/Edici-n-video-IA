# -*- coding: utf-8 -*-
r"""
1. Genera `kf1_dueto_espalda_macbook_escritorio.png` usando `raw_kf2_dueto_giro_hablando_camara.png`
   como ancla geométrica para que el mostrador y la MacBook Pro 16" estén exactamente en las mismas
   coordenadas (`[[285, 634], [500, 636], [496, 761], [285, 750]]`) que en `kf2` y `kf3`.
2. Incrusta con precisión sub-píxel la pantalla real `Escritorio Principal` de MascotaMás en `kf1`.
3. Regenera `spot_dueto_clip1_espalda_a_giro_10s.mp4` con voz limpia sin música de fondo y con la
   MacBook Pro 100% despejada de principio a fin.
"""
import os
import sys
import shutil
import pathlib
import cv2
import numpy as np
from google import genai
from google.genai import types

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

SKILL_SCRIPTS_DIR = r"C:\Users\Demiante\.gemini\config\plugins\gemini-api\skills\gemini-omni-flash-api\scripts"
sys.path.insert(0, SKILL_SCRIPTS_DIR)
sys.path.insert(0, os.path.join(SKILL_SCRIPTS_DIR, "video"))
from generate_video import generate_video, resolve_or_upload_asset, DEFAULT_MODEL
from apply_exact_real_screens_to_kfs import find_inner_screen_inside_bezel, warp_into_quad, UI_ESCRITORIO_DESK

BASE_DIR = pathlib.Path(r"c:\IA\Edicion de videos")
OUT_DIR = BASE_DIR / "assets" / "avatar_veterinario_hombre_vip" / "spot_dueto_hombre_mujer"
HOMBRE_DIR = BASE_DIR / "assets" / "avatar_veterinario_hombre_vip" / "modo_veterinario_palermo"
MUJER_DIR = BASE_DIR / "assets" / "avatar_veterinaria_360"
ARTIFACTS_DIR = pathlib.Path(r"C:\Users\Demiante\.gemini\antigravity\brain\56e5cec9-1285-4884-b2c6-a38ac91ed5ae")

ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip().strip("\"'")

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


def main():
    raw_kf2_bytes = (OUT_DIR / "raw_kf2_dueto_giro_hablando_camara.png").read_bytes()
    hombre_espalda = (HOMBRE_DIR / "modo_veterinario_palermo_06_espalda_180.png").read_bytes()
    mujer_espalda = (MUJER_DIR / "avatar_360_6_espalda.png").read_bytes()

    print("1. Generando raw_kf1 anclado a la geometría exacta de kf2...")
    resp = client.models.generate_content(
        model="gemini-3-pro-image",
        contents=[
            types.Part.from_bytes(data=raw_kf2_bytes, mime_type="image/png"),
            types.Part.from_bytes(data=hombre_espalda, mime_type="image/png"),
            types.Part.from_bytes(data=mujer_espalda, mime_type="image/png"),
            (
                "Keep the EXACT same camera framing, background, wooden reception counter height, and exact same open 16-inch MacBook Pro position in the center from the first reference image. "
                "Make ONE change: both the male veterinarian on the left and the female veterinarian on the right have their heads turned away from the camera, looking directly at the open MacBook Pro screen between them (seen from behind over their shoulders, as in the second and third reference images), "
                "with their hands resting on the wooden desk / keyboard so the entire rectangular MacBook Pro screen is 100% unobstructed."
            ),
        ],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio="9:16"),
        ),
    )
    raw_kf1_path = OUT_DIR / "raw_kf1_dueto_espalda_macbook_escritorio.png"
    for part in resp.candidates[0].content.parts:
        if part.inline_data:
            raw_kf1_path.write_bytes(part.inline_data.data)
            break

    im1 = cv2.imread(str(raw_kf1_path))
    q1_mac = find_inner_screen_inside_bezel(im1, 275, 620, 515, 775)
    if q1_mac is None:
        q1_mac = np.array([[285.0, 634.0], [500.0, 636.0], [496.0, 761.0], [285.0, 750.0]], dtype=np.float32)
    print("kf1 anchored mac quad:", q1_mac.astype(int).tolist())
    im1 = warp_into_quad(im1, UI_ESCRITORIO_DESK, q1_mac, is_iphone=False, keep_skin=True)
    kf1_path = OUT_DIR / "kf1_dueto_espalda_macbook_escritorio.png"
    cv2.imwrite(str(kf1_path), im1)
    shutil.copy2(kf1_path, ARTIFACTS_DIR / kf1_path.name)

    print("2. Subiendo kf1 y kf2 y regenerando Clip 1 (1080p, voz limpia sin música, MacBook Pro fija)...")
    uri_kf1, _ = resolve_or_upload_asset(str(kf1_path), "image/png")
    uri_kf2, _ = resolve_or_upload_asset(str(OUT_DIR / "kf2_dueto_giro_hablando_camara.png"), "image/png")

    out_clip1 = str(OUT_DIR / "spot_dueto_clip1_espalda_a_giro_10s.mp4")
    generate_video(
        prompt=(
            "Use the first image as the starting frame and the second image as the final frame. "
            "In a single continuous tripod-steady 9:16 commercial shot in the modern Buenos Aires veterinary clinic reception 'Veterinaria Palermo', "
            "[0-1.5s] seen from behind over their shoulders ('enfocado desde espaldas'), the strong muscular 38-year-old Argentine male veterinarian on the left "
            "and the charismatic Argentine female veterinarian with a brunette ponytail on the right (both in matching dark petrol-teal 'VETERINARIA PALERMO' scrubs with Littmann stethoscopes) "
            "are looking at the open 16-inch Space Black MacBook Pro between them on the wooden desk (keeping the entire laptop screen 100% unobstructed, no phone in their hands). "
            "[1.5-5.3s] The male veterinarian turns his head over his right shoulder toward the camera and speaks with clear, natural male Rioplatense Argentine Spanish (es-AR) lip-sync: "
            "\"¿Seguís manejando tu veterinaria con cuadernos y mensajes sueltos?\" "
            "[5.3-8.8s] The female veterinarian turns her head over her left shoulder toward the camera with a bright smile and speaks with clear, natural female Rioplatense Argentine Spanish (es-AR) lip-sync: "
            "\"Mirá cómo organizamos todo nuestro equipo en MascotaMás.\" "
            "[8.8-10.0s] Both hold warm, confident smiles looking directly at the camera as shown in the final frame, keeping their hands below the laptop screen so the MacBook Pro screen stays 100% clear. "
            "AUDIO: Clean studio dialogue recording in a quiet room, voice only, NO background music, NO drums, NO beats."
        ),
        model=DEFAULT_MODEL,
        aspect_ratio="9:16",
        duration="10s",
        resolution="1080p",
        first_frame=uri_kf1,
        last_frame=uri_kf2,
        output_path=out_clip1,
        timeout=900,
    )
    print("  -> [DONE] Clip 1 regenerado con éxito.")


if __name__ == "__main__":
    main()
