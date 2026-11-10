# -*- coding: utf-8 -*-
r"""
Genera los 4 Keyframes en alta resolución (9:16) con `gemini-3-pro-image` (Nano Banana Pro)
para el Spot Publicitario de MascotaMás (Sección: Turnos -> Guardería) protagonizado por el
Avatar Veterinario Hombre VIP Argentino con ropa urbana/casual, enfocado desde espaldas
usando su MacBook Pro 16" y su iPhone 16 Pro Max.
"""
import os
import sys
import shutil
import pathlib
import io
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
from google import genai
from google.genai import types

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

BASE_DIR = pathlib.Path(r"c:\IA\Edicion de videos")
OUT_DIR = BASE_DIR / "assets" / "avatar_veterinario_hombre_vip" / "spot_guarderia"
OUT_DIR.mkdir(parents=True, exist_ok=True)
AVATAR_DIR = BASE_DIR / "assets" / "avatar_veterinario_hombre_vip"
MANUAL_DIR = BASE_DIR / "assets" / "manual_vete_y_marca"
ARTIFACTS_DIR = pathlib.Path(r"C:\Users\Demiante\.gemini\antigravity\brain\56e5cec9-1285-4884-b2c6-a38ac91ed5ae")
UPLOAD_DIR = ARTIFACTS_DIR / ".user_uploaded"

ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip().strip("\"'")

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Referencias del Avatar VIP ya generado y recortes faciales originales
AVATAR_FRONT = (AVATAR_DIR / "avatar_vete_hombre_vip_1_frente.png").read_bytes()
AVATAR_HERO = (AVATAR_DIR / "avatar_vete_hombre_vip_hero_brazos_cruzados.png").read_bytes()
AVATAR_BACK = (AVATAR_DIR / "avatar_vete_hombre_vip_6_espalda.png").read_bytes()
AVATAR_Q_DER = (AVATAR_DIR / "avatar_vete_hombre_vip_4_tres_cuartos_der.png").read_bytes()

# Capturas reales de MascotaMás -> Turnos Guardería desde Manual De Usuario Vete y Marca
UI_GUARDERIA_ESTADIAS_RAW = (
    MANUAL_DIR / "12_Hotel_y_Guarderia_por_Estadia__02_Tablero_de_Estadias_y_Ocupacion__01_Grilla_Reservas_MultiDia_CheckIn_CheckOut__04_Raw_Desktop.png"
).read_bytes()
UI_GUARDERIA_ESTADIAS_MAC = (
    MANUAL_DIR / "12_Hotel_y_Guarderia_por_Estadia__02_Tablero_de_Estadias_y_Ocupacion__01_Grilla_Reservas_MultiDia_CheckIn_CheckOut__01_MacBook_Pro_Real.png"
).read_bytes()
UI_GUARDERIA_CUPOS_RAW = (
    MANUAL_DIR / "12_Hotel_y_Guarderia_por_Estadia__01_Configuracion_de_Alojamiento__01_Modal_Categorias_Cupos_y_Tarifas_por_Noche__04_Raw_Desktop.png"
).read_bytes()
UI_GUARDERIA_IPHONE = (
    MANUAL_DIR / "12_Hotel_y_Guarderia_por_Estadia__02_Tablero_de_Estadias_y_Ocupacion__01_Grilla_Reservas_MultiDia_CheckIn_CheckOut__02_iPhone_16_Pro_Max_Real.png"
).read_bytes()


def generate_image(contents, out_path):
    resp = client.models.generate_content(
        model="gemini-3-pro-image",
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio="9:16"),
        ),
    )
    for part in resp.candidates[0].content.parts:
        if part.inline_data:
            data = part.inline_data.data
            pathlib.Path(out_path).write_bytes(data)
            shutil.copy2(out_path, ARTIFACTS_DIR / pathlib.Path(out_path).name)
            print(f"  -> [SAVED] {out_path} ({len(data)} bytes)")
            return data
    raise RuntimeError(f"No image returned for {out_path}")


def main():
    print("=== GENERANDO 4 KEYFRAMES DEL SPOT PUBLICITARIO MASCOTAMÁS (TURNOS GUARDERÍA) ===")

    # 1. Keyframe 1: Enfocado desde espaldas (Over-the-shoulder) usando MacBook Pro (Turnos Guardería) y Celular con ropa urbana/casual
    p1 = (
        "Hyper-realistic vertical 9:16 commercial shot on Sony A7R V 35mm f/1.4 GM lens. "
        "Character & Outfit: The exact strong, muscular Argentine VIP male from the first two reference images "
        "(broad muscular shoulders, V-taper back, thick muscular biceps and vascular forearms, short dark wavy hair), "
        "now dressed in stylish modern URBAN / SMART-CASUAL VIP clothing: an ultra-fitted charcoal-black premium cotton short-sleeve henley shirt "
        "that hugs his muscular back, wide shoulders, and thick biceps, dark tailored jeans, and a stainless-steel luxury chronograph watch on his left wrist (no medical scrubs, no stethoscope). "
        "Camera Angle ('enfocado desde espaldas usando una computadora y celular'): "
        "Over-the-shoulder view from behind him as he sits/leans at a sleek warm-wood modern executive desk in a stylish Buenos Aires loft/clinic office. "
        "With his right hand he is using a real Space Black 16-inch MacBook Pro open on the desk in front of him, and in his left hand he holds a Titanium iPhone 16 Pro Max. "
        "CRITICAL SCREEN DETAIL: On the large, sharp, brightly lit screen of the MacBook Pro 16-inch, reproduce with 100% fidelity the exact MascotaMás web interface "
        "from the third and fourth reference images ('Turnos -> Estadías y Ocupación de Guardería · GUARDERIA', showing the dark blue left sidebar with 'Turnos' selected, "
        "'SELECCIONAR CALENDARIO: GUARDERIA', green button '+ Cargar Estadía Manualmente', and patient row 'Thor (Martín López) · Suite Canina · En Guardería (Check-in) · 09/11/2026 -> 11/11/2026')."
    )
    kf1_path = OUT_DIR / "kf1_espalda_macbook_celular_guarderia.png"
    kf1_bytes = generate_image(
        [
            types.Part.from_bytes(data=AVATAR_BACK, mime_type="image/png"),
            types.Part.from_bytes(data=AVATAR_HERO, mime_type="image/png"),
            types.Part.from_bytes(data=UI_GUARDERIA_ESTADIAS_RAW, mime_type="image/png"),
            types.Part.from_bytes(data=UI_GUARDERIA_ESTADIAS_MAC, mime_type="image/png"),
            p1,
        ],
        kf1_path,
    )

    tasks = [
        (
            "kf2_espalda_giro_hablando_macbook_guarderia.png",
            [
                types.Part.from_bytes(data=kf1_bytes, mime_type="image/png"),
                types.Part.from_bytes(data=AVATAR_HERO, mime_type="image/png"),
                types.Part.from_bytes(data=UI_GUARDERIA_ESTADIAS_RAW, mime_type="image/png"),
            ],
            "Keep the exact same camera framing from behind / over-the-shoulder, the exact same muscular Argentine VIP man in his fitted charcoal-black urban short-sleeve henley shirt "
            "and luxury steel watch, the exact same modern wood desk, and the exact same 16-inch MacBook Pro displaying the crisp 'MascotaMás - Estadías y Ocupación de Guardería' interface on screen. "
            "Change his pose so that while still seen from behind at the desk with the MacBook Pro screen clearly visible in front of him and the iPhone in his left hand, "
            "he turns his head and upper torso over his right shoulder toward the camera (showing his exact face, masculine stubble beard, and charismatic smile from the second reference image) "
            "as he speaks to the viewer and points his right hand toward the 'Turnos Guardería' screen on the MacBook Pro.",
        ),
        (
            "kf3_espalda_zoom_macbook_cupos_guarderia.png",
            [
                types.Part.from_bytes(data=kf1_bytes, mime_type="image/png"),
                types.Part.from_bytes(data=AVATAR_Q_DER, mime_type="image/png"),
                types.Part.from_bytes(data=UI_GUARDERIA_CUPOS_RAW, mime_type="image/png"),
                types.Part.from_bytes(data=UI_GUARDERIA_IPHONE, mime_type="image/png"),
            ],
            "Closer over-the-shoulder commercial shot from behind the exact same muscular Argentine VIP man in his fitted charcoal-black urban short-sleeve henley shirt and luxury steel watch "
            "at the same wood desk. He is using the 16-inch MacBook Pro and holding his iPhone 16 Pro Max. "
            "On the large, crisp screen of the 16-inch MacBook Pro, display with 100% fidelity the third reference image: 'Categorías y Cupos de Guardería · GUARDERIA' "
            "('Bloqueo de Fechas y Rangos en Guardería', 'Nueva Categoría de Guardería', 'Cupo / Lugares Disponibles', 'Precio por Día ($ ARS)', 'guarderia: Cupo 5 lugar(es) · Tarifa: $45.000 ARS / día'). "
            "On the iPhone 16 Pro Max screen in his hand, show the mobile MascotaMás Guardería view from the fourth reference image. "
            "He glances slightly over his shoulder with a confident expression.",
        ),
        (
            "kf4_frente_casual_vip_macbook_cta.png",
            [
                types.Part.from_bytes(data=AVATAR_HERO, mime_type="image/png"),
                types.Part.from_bytes(data=kf1_bytes, mime_type="image/png"),
                types.Part.from_bytes(data=UI_GUARDERIA_ESTADIAS_RAW, mime_type="image/png"),
            ],
            "Hyper-realistic vertical 9:16 medium-full commercial shot in the exact same modern Buenos Aires loft/office. "
            "The exact same muscular Argentine VIP man (with his exact face, short dark wavy hair, masculine stubble beard, wide shoulders, sculpted 3D chest, thick muscular biceps and vascular forearms "
            "from the first reference image), dressed in the exact same fitted charcoal-black urban short-sleeve henley shirt, dark tailored jeans, and luxury stainless-steel chronograph watch (no scrubs, no stethoscope), "
            "has turned around to face the camera directly, leaning confidently against the front edge of the wood desk. "
            "He holds his Titanium iPhone 16 Pro Max in his left hand and gestures warmly toward the camera with his right hand as he speaks. "
            "Right beside him on the desk, the open 16-inch MacBook Pro screen is angled toward the camera clearly showing the 'MascotaMás - Estadías y Ocupación de Guardería' interface.",
        ),
    ]

    def run_task(item):
        fname, parts, prompt = item
        out_p = OUT_DIR / fname
        print(f"  -> Generando {fname}...")
        return generate_image(parts + [prompt], out_p)

    with ThreadPoolExecutor(max_workers=3) as ex:
        list(ex.map(run_task, tasks))

    print("=== 4 KEYFRAMES GENERADOS CON ÉXITO ===")


if __name__ == "__main__":
    main()
