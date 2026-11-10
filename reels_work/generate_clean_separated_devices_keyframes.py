# -*- coding: utf-8 -*-
r"""
Genera los 5 keyframes (`kf1..kf5`) donde la MacBook Pro 16" y el iPhone 16 Pro Max están
100% separados (el iPhone delante del ambo verde petróleo oscuro, sin tapar la MacBook Pro)
y con el iPhone mostrando SIEMPRE su pantalla frontal hacia cámara.
Luego detecta el interior exacto del bisel negro de ambos dispositivos e incrusta con
esquinas redondeadas y máscara sub-píxel las capturas 100% reales de `gestion.mascotamas.com`.
"""
import os
import sys
import shutil
import pathlib
from concurrent.futures import ThreadPoolExecutor, as_completed
import cv2
import numpy as np
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
HOMBRE_ESPALDA = (HOMBRE_DIR / "modo_veterinario_palermo_06_espalda_180.png").read_bytes()
HOMBRE_HERO = (HOMBRE_DIR / "modo_veterinario_palermo_12_hero_brazos_cruzados.png").read_bytes()
MUJER_FRENTE = (MUJER_DIR / "avatar_360_1_frente.png").read_bytes()
MUJER_TRES_CUARTOS = (MUJER_DIR / "avatar_360_2_tres_cuartos_izq.png").read_bytes()
MUJER_ESPALDA = (MUJER_DIR / "avatar_360_6_espalda.png").read_bytes()

UI_ESCRITORIO_DESK_PATH = str(
    MANUAL_DIR / "00_Secuencias_Paso_a_Paso__01_Recorrido_Completo_App_10_Pantallas__01_Paso_1_Escritorio_y_Resumen_Operativo_del_Dia__04_Raw_Desktop.png"
)
UI_CALENDARIOS_DESK_PATH = str(
    MANUAL_DIR / "00_Secuencias_Paso_a_Paso__02_Flujo_Calendarios_y_Sena_MercadoPago__02_Paso_2_Modal_Crear_Calendario_Selector_de_4_Modalidades__04_Raw_Desktop.png"
)
UI_HC_PDF_DESK_PATH = str(
    MANUAL_DIR / "06_Historias_Clinicas_y_Fichas__03_Legajo_Clinico_Digital_y_PDF__01_Modal_Historial_Completo_y_Descarga_PDF__04_Raw_Desktop.png"
)
UI_ESCRITORIO_MOB_PATH = str(
    MANUAL_DIR / "00_Secuencias_Paso_a_Paso__01_Recorrido_Completo_App_10_Pantallas__01_Paso_1_Escritorio_y_Resumen_Operativo_del_Dia__05_Raw_Mobile.png"
)
UI_TURNOS_MOB_PATH = str(
    MANUAL_DIR / "00_Secuencias_Paso_a_Paso__03_Flujo_Turnos_Agenda_y_Sena__04_Paso_4_Reserva_Temporal_15_min_y_Envio_de_Link_MercadoPago__05_Raw_Mobile.png"
)
UI_HC_MOB_PATH = str(
    MANUAL_DIR / "06_Historias_Clinicas_y_Fichas__03_Legajo_Clinico_Digital_y_PDF__01_Modal_Historial_Completo_y_Descarga_PDF__05_Raw_Mobile.png"
)

UI_ESCRITORIO_DESK_BYTES = pathlib.Path(UI_ESCRITORIO_DESK_PATH).read_bytes()
UI_CALENDARIOS_DESK_BYTES = pathlib.Path(UI_CALENDARIOS_DESK_PATH).read_bytes()
UI_HC_PDF_DESK_BYTES = pathlib.Path(UI_HC_PDF_DESK_PATH).read_bytes()
UI_ESCRITORIO_MOB_BYTES = pathlib.Path(UI_ESCRITORIO_MOB_PATH).read_bytes()


def generate_raw_kf(filename: str, contents_list: list):
    raw_path = OUT_DIR / f"raw_{filename}"
    print(f"  -> [START] Generando raw_{filename}...")
    resp = client.models.generate_content(
        model="gemini-3-pro-image",
        contents=contents_list,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio="9:16"),
        ),
    )
    for part in resp.candidates[0].content.parts:
        if part.inline_data:
            raw_path.write_bytes(part.inline_data.data)
            print(f"  -> [SAVED] {raw_path.name}")
            return filename
    raise RuntimeError(f"Error generando {filename}")


def main():
    # Restaurar kf4 limpio desde git antes de usarlo como referencia
    os.system(f'git checkout HEAD -- "{OUT_DIR / "kf4_dueto_frente_hero_cta_mascotamas.png"}"')
    os.system(f'git checkout HEAD -- "{OUT_DIR / "kf2_dueto_giro_hablando_camara.png"}"')
    kf2_clean_bytes = (OUT_DIR / "kf2_dueto_giro_hablando_camara.png").read_bytes()
    kf4_clean_bytes = (OUT_DIR / "kf4_dueto_frente_hero_cta_mascotamas.png").read_bytes()

    jobs = [
        (
            "kf1_dueto_espalda_macbook_escritorio.png",
            [
                types.Part.from_bytes(data=HOMBRE_ESPALDA, mime_type="image/png"),
                types.Part.from_bytes(data=HOMBRE_FRENTE, mime_type="image/png"),
                types.Part.from_bytes(data=MUJER_ESPALDA, mime_type="image/png"),
                types.Part.from_bytes(data=MUJER_FRENTE, mime_type="image/png"),
                types.Part.from_bytes(data=UI_ESCRITORIO_DESK_BYTES, mime_type="image/png"),
                (
                    "Hyper-realistic vertical 9:16 commercial photography shot on Sony A7R V 35mm f/1.4 GM lens. "
                    "Over-the-shoulder view from behind ('enfocado desde espaldas') of BOTH Argentine veterinarians standing side by side "
                    "at the wooden reception desk of 'Veterinaria Palermo': on the left is the strong muscular 38-year-old Argentine male veterinarian, "
                    "and on the right is the charismatic Argentine female veterinarian with a brunette ponytail, both in matching dark petrol-teal 'VETERINARIA PALERMO' scrubs with Littmann stethoscopes. "
                    "Between them on the desk sits an open 16-inch Space Black MacBook Pro whose ENTIRE rectangular screen is 100% unobstructed (nothing in front of the laptop screen), "
                    "displaying the white 'MascotaMás — Escritorio Principal' web interface from the fifth reference image. "
                    "Both veterinarians have their hands resting on the wooden desk beside the laptop (no iPhone in this shot so the laptop screen is 100% clear)."
                ),
            ],
        ),
        (
            "kf2_dueto_giro_hablando_camara.png",
            [
                types.Part.from_bytes(data=kf2_clean_bytes, mime_type="image/png"),
                types.Part.from_bytes(data=UI_ESCRITORIO_DESK_BYTES, mime_type="image/png"),
                (
                    "Keep this exact vertical 9:16 photo of the two Argentine veterinarians turning over their shoulders smiling at the camera at the wooden desk of Veterinaria Palermo. "
                    "Make ONE clean modification: remove the phone and lower their hands slightly onto the wooden counter so that the ENTIRE rectangular screen of the open 16-inch Space Black MacBook Pro between them is 100% unobstructed from corner to corner, "
                    "clearly displaying the white 'MascotaMás — Escritorio Principal' web interface from the second reference image."
                ),
            ],
        ),
        (
            "kf3_dueto_operando_turnos_y_hc_macbook.png",
            [
                types.Part.from_bytes(data=kf2_clean_bytes, mime_type="image/png"),
                types.Part.from_bytes(data=UI_CALENDARIOS_DESK_BYTES, mime_type="image/png"),
                types.Part.from_bytes(data=UI_ESCRITORIO_MOB_BYTES, mime_type="image/png"),
                (
                    "Keep this exact vertical 9:16 photo of the two Argentine veterinarians at the wooden desk of Veterinaria Palermo. "
                    "1) Keep the open 16-inch Space Black MacBook Pro screen between them 100% unobstructed from corner to corner, displaying the 'MascotaMás — Nuevo Calendario' web interface from the second reference image. "
                    "2) The female veterinarian on the right holds an iPhone 16 Pro Max upright in front of her dark teal scrub shoulder/chest (to the right of the laptop, NOT overlapping the laptop screen at all) with its flat illuminated FRONT white screen (with Dynamic Island at the top) facing 100% straight toward the camera lens."
                ),
            ],
        ),
        (
            "kf4_dueto_frente_hero_cta_mascotamas.png",
            [
                types.Part.from_bytes(data=kf4_clean_bytes, mime_type="image/png"),
                types.Part.from_bytes(data=UI_HC_PDF_DESK_BYTES, mime_type="image/png"),
                types.Part.from_bytes(data=UI_ESCRITORIO_MOB_BYTES, mime_type="image/png"),
                (
                    "Keep this exact vertical 9:16 medium-full front shot of the two Argentine veterinarians standing side by side behind the open 16-inch Space Black MacBook Pro on the wooden reception counter. "
                    "The male veterinarian holds the iPhone 16 Pro Max upright in his left hand in front of his dark teal scrub chest with its flat illuminated FRONT white screen (with Dynamic Island at the top) facing 100% straight toward the camera lens (NEVER showing the back cameras), "
                    "and the open 16-inch MacBook Pro in front is 100% unobstructed."
                ),
            ],
        ),
        (
            "kf5_dueto_frente_hero_cierre.png",
            [
                types.Part.from_bytes(data=kf4_clean_bytes, mime_type="image/png"),
                types.Part.from_bytes(data=UI_HC_PDF_DESK_BYTES, mime_type="image/png"),
                types.Part.from_bytes(data=UI_ESCRITORIO_MOB_BYTES, mime_type="image/png"),
                (
                    "Keep this exact vertical 9:16 medium-full front shot of the two Argentine veterinarians standing side by side behind the open 16-inch Space Black MacBook Pro on the wooden reception counter, smiling warmly at the camera. "
                    "CRITICAL: The male veterinarian keeps holding the iPhone 16 Pro Max upright in his left hand in front of his dark teal scrub chest in the EXACT same position, with its flat illuminated FRONT white screen (with Dynamic Island at the top) facing 100% straight toward the camera lens (NEVER showing the back cameras)."
                ),
            ],
        ),
    ]

    with ThreadPoolExecutor(max_workers=5) as ex:
        futs = [ex.submit(generate_raw_kf, fn, c) for fn, c in jobs]
        for f in as_completed(futs):
            print(f"  [DONE RAW] {f.result()}")


if __name__ == "__main__":
    main()
