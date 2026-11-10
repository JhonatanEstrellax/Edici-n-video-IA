# -*- coding: utf-8 -*-
import os
import sys
import shutil
import pathlib
from google import genai
from google.genai import types
from warp_screens_spot_dueto import OUT_DIR

BASE_DIR = pathlib.Path(r"c:\IA\Edicion de videos")
HOMBRE_DIR = BASE_DIR / "assets" / "avatar_veterinario_hombre_vip" / "modo_veterinario_palermo"
MUJER_DIR = BASE_DIR / "assets" / "avatar_veterinaria_360"
MANUAL_DIR = BASE_DIR / "assets" / "manual_vete_y_marca"
ARTIFACTS_DIR = pathlib.Path(r"C:\Users\Demiante\.gemini\antigravity\brain\56e5cec9-1285-4884-b2c6-a38ac91ed5ae")

ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip().strip("\"'")

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

HOMBRE_ESPALDA = (HOMBRE_DIR / "modo_veterinario_palermo_06_espalda_180.png").read_bytes()
HOMBRE_FRENTE = (HOMBRE_DIR / "modo_veterinario_palermo_03_frente_0.png").read_bytes()
MUJER_ESPALDA = (MUJER_DIR / "avatar_360_6_espalda.png").read_bytes()
MUJER_FRENTE = (MUJER_DIR / "avatar_360_1_frente.png").read_bytes()
UI_ESCRITORIO_MAC = (
    MANUAL_DIR / "00_Secuencias_Paso_a_Paso__01_Recorrido_Completo_App_10_Pantallas__01_Paso_1_Escritorio_y_Resumen_Operativo_del_Dia__01_MacBook_Pro_Real.png"
).read_bytes()
UI_ESCRITORIO_RAW = (
    MANUAL_DIR / "00_Secuencias_Paso_a_Paso__01_Recorrido_Completo_App_10_Pantallas__01_Paso_1_Escritorio_y_Resumen_Operativo_del_Dia__04_Raw_Desktop.png"
).read_bytes()


def main():
    resp = client.models.generate_content(
        model="gemini-3-pro-image",
        contents=[
            types.Part.from_bytes(data=HOMBRE_ESPALDA, mime_type="image/png"),
            types.Part.from_bytes(data=HOMBRE_FRENTE, mime_type="image/png"),
            types.Part.from_bytes(data=MUJER_ESPALDA, mime_type="image/png"),
            types.Part.from_bytes(data=MUJER_FRENTE, mime_type="image/png"),
            types.Part.from_bytes(data=UI_ESCRITORIO_MAC, mime_type="image/png"),
            types.Part.from_bytes(data=UI_ESCRITORIO_RAW, mime_type="image/png"),
            (
                "Hyper-realistic vertical 9:16 commercial photography shot on Sony A7R V 35mm f/1.4 GM lens. "
                "Over-the-shoulder view from behind ('enfocado desde espaldas') of BOTH Argentine veterinarians standing side by side "
                "at the warm wooden reception desk of their modern Buenos Aires clinic 'Veterinaria Palermo': "
                "on the left is the strong, muscular 38-year-old Argentine male veterinarian from the first two reference images, "
                "and on the right is the charismatic Argentine female veterinarian with a brunette ponytail from the third and fourth reference images. "
                "Both wear matching fitted dark petrol-teal clinical scrubs with 'VETERINARIA PALERMO' embroidered on the chest and Littmann stethoscopes around their necks. "
                "Directly in front of them on the desk sits an open 16-inch Space Black MacBook Pro whose screen is crisp, sharp, and 100% legible to the camera, "
                "displaying the exact 'MascotaMás — Escritorio Principal · Turnos del Día · Vacunas · Recordatorios' web dashboard from the fifth and sixth reference images. "
                "The male veterinarian has his right hand on the MacBook Pro keyboard while the female veterinarian holds a Titanium iPhone 16 Pro Max in her right hand."
            ),
        ],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio="9:16"),
        ),
    )
    kf1_path = OUT_DIR / "kf1_dueto_espalda_macbook_escritorio.png"
    for part in resp.candidates[0].content.parts:
        if part.inline_data:
            kf1_path.write_bytes(part.inline_data.data)
            shutil.copy2(kf1_path, ARTIFACTS_DIR / kf1_path.name)
            print("  -> [SAVED CLEAN] kf1_dueto_espalda_macbook_escritorio.png")
            break


if __name__ == "__main__":
    main()
