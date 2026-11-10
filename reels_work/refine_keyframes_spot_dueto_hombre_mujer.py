# -*- coding: utf-8 -*-
r"""
Regenera `kf3_dueto_operando_turnos_y_hc_macbook.png` asegurando que SOLO aparezcan
los dos avatares protagonistas (Avatar Hombre VIP a la izquierda + Avatar Mujer Veterinaria a la derecha)
sin ninguna tercera persona en primer plano, e inspecciona/perfecciona las pantallas de la MacBook Pro.
"""
import os
import sys
import shutil
import pathlib
from google import genai
from google.genai import types

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

BASE_DIR = pathlib.Path(r"c:\IA\Edicion de videos")
OUT_DIR = BASE_DIR / "assets" / "avatar_veterinario_hombre_vip" / "spot_dueto_hombre_mujer"
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

HOMBRE_FRENTE = (HOMBRE_DIR / "modo_veterinario_palermo_03_frente_0.png").read_bytes()
HOMBRE_TRES_CUARTOS = (HOMBRE_DIR / "modo_veterinario_palermo_04_tres_cuartos_der_45.png").read_bytes()
MUJER_FRENTE = (MUJER_DIR / "avatar_360_1_frente.png").read_bytes()
MUJER_TRES_CUARTOS = (MUJER_DIR / "avatar_360_2_tres_cuartos_izq.png").read_bytes()
KF2_REF = (OUT_DIR / "kf2_dueto_giro_hablando_camara.png").read_bytes()
UI_CALENDARIOS_RAW = (
    MANUAL_DIR / "00_Secuencias_Paso_a_Paso__02_Flujo_Calendarios_y_Sena_MercadoPago__02_Paso_2_Modal_Crear_Calendario_Selector_de_4_Modalidades__04_Raw_Desktop.png"
).read_bytes()


def main():
    print("Regenerando kf3_dueto_operando_turnos_y_hc_macbook.png (SOLO los 2 protagonistas)...")
    prompt_kf3 = (
        "Hyper-realistic vertical 9:16 commercial photography shot on Sony A7R V 35mm f/1.4 GM lens. "
        "Keep the exact same two protagonists and camera angle from the first reference image (over-the-shoulder view from behind at the wooden reception desk of 'Veterinaria Palermo', with ONLY these two people in the scene and nobody else): "
        "on the left is the strong, muscular 38-year-old Argentine male veterinarian, and on the right is the charismatic Argentine female veterinarian with a brunette ponytail, "
        "both wearing matching dark petrol-teal 'VETERINARIA PALERMO' clinical scrubs and Littmann stethoscopes. "
        "In this frame, the male veterinarian has his left hand typing on the open 16-inch Space Black MacBook Pro keyboard while looking over his shoulder at the camera with an expressive smile, "
        "and the female veterinarian turns toward the camera holding up the Titanium iPhone 16 Pro Max and pointing to the MacBook Pro screen. "
        "The MacBook Pro screen between them clearly displays the 'MascotaMás — Nuevo Calendario · 4 Modalidades (Veterinaria, Peluquería, Guardería) + Seña Mercado Pago' web interface from the last reference image."
    )
    resp = client.models.generate_content(
        model="gemini-3-pro-image",
        contents=[
            types.Part.from_bytes(data=KF2_REF, mime_type="image/png"),
            types.Part.from_bytes(data=HOMBRE_FRENTE, mime_type="image/png"),
            types.Part.from_bytes(data=MUJER_FRENTE, mime_type="image/png"),
            types.Part.from_bytes(data=UI_CALENDARIOS_RAW, mime_type="image/png"),
            prompt_kf3,
        ],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio="9:16"),
        ),
    )
    kf3_path = OUT_DIR / "kf3_dueto_operando_turnos_y_hc_macbook.png"
    for part in resp.candidates[0].content.parts:
        if part.inline_data:
            kf3_path.write_bytes(part.inline_data.data)
            shutil.copy2(kf3_path, ARTIFACTS_DIR / kf3_path.name)
            print(f"  -> [SAVED] {kf3_path}")
            break


if __name__ == "__main__":
    main()
