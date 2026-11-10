# -*- coding: utf-8 -*-
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

BASE_DIR = pathlib.Path(r"c:\IA\Edicion de videos")
OUT_DIR = BASE_DIR / "assets" / "avatar_veterinario_hombre_vip" / "spot_migracion_gratis"
AVATAR_DIR = BASE_DIR / "assets" / "avatar_veterinario_hombre_vip"
MANUAL_DIR = BASE_DIR / "assets" / "manual_vete_y_marca"
ARTIFACTS_DIR = pathlib.Path(r"C:\Users\Demiante\.gemini\antigravity\brain\56e5cec9-1285-4884-b2c6-a38ac91ed5ae")

ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip().strip("\"'")

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

AVATAR_FRONT = (AVATAR_DIR / "avatar_vete_hombre_vip_1_frente.png").read_bytes()
AVATAR_HERO = (AVATAR_DIR / "avatar_vete_hombre_vip_hero_brazos_cruzados.png").read_bytes()
UI_ESCRITORIO_MAC = (
    MANUAL_DIR / "00_Secuencias_Paso_a_Paso__01_Recorrido_Completo_App_10_Pantallas__01_Paso_1_Escritorio_y_Resumen_Operativo_del_Dia__01_MacBook_Pro_Real.png"
).read_bytes()
RAW_CAL_PATH = str(
    MANUAL_DIR / "00_Secuencias_Paso_a_Paso__02_Flujo_Calendarios_y_Sena_MercadoPago__02_Paso_2_Modal_Crear_Calendario_Selector_de_4_Modalidades__04_Raw_Desktop.png"
)
RAW_HC_PATH = str(
    MANUAL_DIR / "06_Historias_Clinicas_y_Fichas__03_Legajo_Clinico_Digital_y_PDF__01_Modal_Historial_Completo_y_Descarga_PDF__04_Raw_Desktop.png"
)
UI_HC_PDF_RAW = pathlib.Path(RAW_HC_PATH).read_bytes()


def warp_exact_quad(kf_path, ui_path, quad_pts, keep_hand=False):
    img = cv2.imread(str(kf_path))
    ui = cv2.imread(str(ui_path))
    h, w = img.shape[:2]
    uh, uw = ui.shape[:2]
    quad = np.array(quad_pts, dtype=np.float32)
    src_pts = np.array([[0, 0], [uw - 1, 0], [uw - 1, uh - 1], [0, uh - 1]], dtype=np.float32)
    M = cv2.getPerspectiveTransform(src_pts, quad)
    warped = cv2.warpPerspective(ui, M, (w, h), flags=cv2.INTER_LANCZOS4)
    poly = np.zeros((h, w), dtype=np.uint8)
    cv2.fillConvexPoly(poly, quad.astype(np.int32), 255)
    if keep_hand:
        ycrcb = cv2.cvtColor(img, cv2.cvtColor_BGR2YCrCb if hasattr(cv2, "cvtColor_BGR2YCrCb") else cv2.COLOR_BGR2YCrCb)
        Y, Cr, Cb = cv2.split(ycrcb)
        hand = ((Cr > 138) & (Cb < 130) & (Y < 225) & (Y > 40)).astype(np.uint8) * 255
        hand = cv2.dilate(hand, np.ones((5, 5), np.uint8), iterations=2)
        poly = cv2.bitwise_and(poly, cv2.bitwise_not(hand))
    alpha = cv2.GaussianBlur(poly.astype(np.float32) / 255.0, (3, 3), 0)[..., None]
    out = (warped.astype(np.float32) * alpha + img.astype(np.float32) * (1.0 - alpha)).astype(np.uint8)
    cv2.imwrite(str(kf_path), out)
    shutil.copy2(kf_path, ARTIFACTS_DIR / kf_path.name)
    print(f"  -> [WARPED] {kf_path.name}")


def main():
    # 1. En kf3 el quad de la pantalla completa es exactamente [[506.0, 732.0], [749.0, 757.0], [718.0, 936.0], [475.0, 887.0]]
    warp_exact_quad(
        OUT_DIR / "kf3_espalda_caracteristicas_4_calendarios_y_hc.png",
        RAW_CAL_PATH,
        [[506.0, 732.0], [749.0, 757.0], [718.0, 936.0], [475.0, 887.0]],
        keep_hand=True,
    )

    # 2. Regenerar kf4 limpio
    p4 = (
        "Hyper-realistic vertical 9:16 medium-full commercial shot on Sony A7R V 35mm f/1.4 GM lens. "
        "The exact strong, muscular Argentine VIP male veterinarian/founder from the first and second reference images "
        "wearing a tailored dark-navy executive clinical polo shirt with subtle purple collar trim, dark tailored trousers, and a stainless-steel luxury watch, "
        "standing facing the camera in the modern Buenos Aires veterinary clinic reception. "
        "He leans confidently beside the wooden reception desk where the open 16-inch Space Black MacBook Pro sits on the right side facing the camera, "
        "clearly displaying the MascotaMás 'Historia Clínica de tango · Descargar Historia' web interface from the third reference image, "
        "while holding a Titanium iPhone 16 Pro Max in his left hand and gesturing warmly toward the viewer with a charismatic Argentine smile."
    )
    resp = client.models.generate_content(
        model="gemini-3-pro-image",
        contents=[
            types.Part.from_bytes(data=AVATAR_FRONT, mime_type="image/png"),
            types.Part.from_bytes(data=AVATAR_HERO, mime_type="image/png"),
            types.Part.from_bytes(data=UI_HC_PDF_RAW, mime_type="image/png"),
            types.Part.from_bytes(data=UI_ESCRITORIO_MAC, mime_type="image/png"),
            p4,
        ],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio="9:16"),
        ),
    )
    kf4_path = OUT_DIR / "kf4_frente_vip_cta_migracion_gratis.png"
    for part in resp.candidates[0].content.parts:
        if part.inline_data:
            kf4_path.write_bytes(part.inline_data.data)
            shutil.copy2(kf4_path, ARTIFACTS_DIR / kf4_path.name)
            print("  -> [SAVED CLEAN] kf4_frente_vip_cta_migracion_gratis.png")
            break


if __name__ == "__main__":
    main()
