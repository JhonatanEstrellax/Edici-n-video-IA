# -*- coding: utf-8 -*-
r"""
Genera los 4 Keyframes en alta resolución (9:16) con `gemini-3-pro-image` (Nano Banana Pro)
para el Spot Publicitario de MascotaMás (Sección: Turnos para Peluquerías Caninas)
protagonizado por el Avatar Hombre VIP Argentino con ropa de Groomer Canino profesional,
usando su MacBook Pro 16" y su iPhone 16 Pro Max.
"""
import os
import sys
import shutil
import pathlib
from concurrent.futures import ThreadPoolExecutor
from google import genai
from google.genai import types

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

BASE_DIR = pathlib.Path(r"c:\IA\Edicion de videos")
OUT_DIR = BASE_DIR / "assets" / "avatar_veterinario_hombre_vip" / "spot_peluqueria_canina"
OUT_DIR.mkdir(parents=True, exist_ok=True)
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

# Referencias del Avatar VIP ya generado
AVATAR_FRONT = (AVATAR_DIR / "avatar_vete_hombre_vip_1_frente.png").read_bytes()
AVATAR_HERO = (AVATAR_DIR / "avatar_vete_hombre_vip_hero_brazos_cruzados.png").read_bytes()
AVATAR_BACK = (AVATAR_DIR / "avatar_vete_hombre_vip_6_espalda.png").read_bytes()
AVATAR_Q_DER = (AVATAR_DIR / "avatar_vete_hombre_vip_4_tres_cuartos_der.png").read_bytes()

# Capturas reales de MascotaMás -> Turnos para Peluquerías Caninas
UI_TURNOS_TABLERO_RAW = (
    MANUAL_DIR / "03_Turnos_y_Agenda__08_Turnos_Peluqueria_Canina__01_Tablero_por_Groomer_y_Servicios__04_Raw_Desktop.png"
).read_bytes()
UI_TURNOS_TABLERO_MAC = (
    MANUAL_DIR / "03_Turnos_y_Agenda__08_Turnos_Peluqueria_Canina__01_Tablero_por_Groomer_y_Servicios__01_MacBook_Pro_Real.png"
).read_bytes()
UI_TURNOS_AGENDA_RAW = (
    MANUAL_DIR / "03_Turnos_y_Agenda__08_Turnos_Peluqueria_Canina__02_Agenda_Diaria_Turnos_Confirmados_y_Sena_MP__04_Raw_Desktop.png"
).read_bytes()
UI_TURNOS_AGENDA_IPHONE = (
    MANUAL_DIR / "03_Turnos_y_Agenda__08_Turnos_Peluqueria_Canina__02_Agenda_Diaria_Turnos_Confirmados_y_Sena_MP__02_iPhone_16_Pro_Max_Real.png"
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
    print("=== GENERANDO 4 KEYFRAMES DEL SPOT PUBLICITARIO MASCOTAMÁS (TURNOS - PELUQUERÍAS CANINAS) ===")

    # 1. Keyframe 1: Enfocado desde espaldas con ropa de Groomer Canino usando MacBook Pro (Turnos Peluquería Canina) e iPhone 16 Pro Max
    p1 = (
        "Hyper-realistic vertical 9:16 commercial shot on Sony A7R V 35mm f/1.4 GM lens. "
        "Character & Outfit ('con ropa de groomer canino'): The exact strong, muscular Argentine VIP male from the first two reference images "
        "(broad muscular shoulders, V-taper back, thick muscular biceps and vascular forearms, short dark wavy hair), "
        "dressed in sleek, tailored PROFESSIONAL DOG GROOMER ('groomer canino') attire: an ultra-fitted matte-black water-resistant short-sleeve groomer zip-smock / technical groomer vest-apron "
        "with subtle purple/silver piping and a small 'Grooming VIP' scissors/paw badge, that hugs his muscular shoulders, chest, and back, dark tailored trousers, "
        "and a stainless-steel luxury chronograph watch on his left wrist (NO stethoscope, NO hospital scrubs). "
        "Environment & Camera Angle: Over-the-shoulder view from behind him in a luxury modern Buenos Aires Dog Grooming Salon ('Peluquería Canina' with warm wood shelving, "
        "neatly arranged professional grooming shears, combs, and premium dog shampoo bottles in the softly blurred background). "
        "With his right hand he is using a real Space Black 16-inch MacBook Pro open on the sleek wood reception desk in front of him, and in his left hand he holds a Titanium iPhone 16 Pro Max. "
        "CRITICAL SCREEN DETAIL: On the large, sharp, brightly lit screen of the MacBook Pro 16-inch, reproduce with 100% fidelity the exact MascotaMás web interface "
        "from the third and fourth reference images ('mascotaMÁS · Peluquería Canina GroomingVIP · Turnos', showing the white left sidebar with purple 'Turnos' active, "
        "'SELECCIONAR CALENDARIO: PELUQUERÍA CANINA (SERVICIOS)', 'Agenda por Servicios y Bloques', 'Tablero por Profesional', 'Baño y corte Rzas CHICAS 45m', 'Baño y corte Rzas GDES 120m', "
        "and groomer columns 'maria gonzalez • peluquera' and 'juan perez • peluquero')."
    )
    kf1_path = OUT_DIR / "kf1_espalda_groomer_macbook_turnos_peluqueria.png"
    kf3_path = OUT_DIR / "kf3_espalda_groomer_agenda_y_sena_peluqueria.png"
    kf1_bytes = kf1_path.read_bytes()
    kf3_bytes = kf3_path.read_bytes()

    tasks = [
        (
            "kf2_espalda_giro_groomer_hablando_turnos_peluqueria.png",
            [
                types.Part.from_bytes(data=kf1_bytes, mime_type="image/png"),
                types.Part.from_bytes(data=kf3_bytes, mime_type="image/png"),
                types.Part.from_bytes(data=UI_TURNOS_TABLERO_RAW, mime_type="image/png"),
            ],
            "Keep the EXACT same camera angle, composition, and background as the first and second reference images: "
            "the muscular Argentine groomer in his black GROOMING VIP short-sleeve smock with purple piping is on the LEFT side of the frame seen from behind, "
            "and the 16-inch MacBook Pro is on the RIGHT side of the wood counter. "
            "He turns his head over his right shoulder to smile warmly at the camera (like in the second reference image), "
            "while pointing his hand toward the MacBook Pro screen which displays the third reference image "
            "('MascotaMás · Peluquería Canina GroomingVIP · Turnos · Tablero por Profesional').",
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
