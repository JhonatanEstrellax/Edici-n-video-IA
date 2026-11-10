# -*- coding: utf-8 -*-
r"""
Genera los 4 Keyframes maestros (9:16 vertical) con `gemini-3-pro-image` para el
Spot Publicitario de MascotaMás protagonizado en DUETO por el Avatar Hombre VIP
(`modo_veterinario_palermo`) y el Avatar Mujer Veterinaria 360° (`avatar_veterinaria_360`),
ambos con ambo clínico verde petróleo oscuro "VETERINARIA PALERMO" y estetoscopio Littmann,
usando la MacBook Pro 16" Space Black y el iPhone 16 Pro Max Titanium con pantallas reales de MascotaMás.
"""
import os
import sys
import shutil
import pathlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from google import genai
from google.genai import types

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

BASE_DIR = pathlib.Path(r"c:\IA\Edicion de videos")
OUT_DIR = BASE_DIR / "assets" / "avatar_veterinario_hombre_vip" / "spot_dueto_hombre_mujer"
OUT_DIR.mkdir(parents=True, exist_ok=True)

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

# Referencias exactas del Avatar Hombre VIP (Modo Veterinario Palermo)
HOMBRE_FRENTE = (HOMBRE_DIR / "modo_veterinario_palermo_03_frente_0.png").read_bytes()
HOMBRE_ESPALDA = (HOMBRE_DIR / "modo_veterinario_palermo_06_espalda_180.png").read_bytes()
HOMBRE_HERO = (HOMBRE_DIR / "modo_veterinario_palermo_12_hero_brazos_cruzados.png").read_bytes()

# Referencias exactas del Avatar Mujer Veterinaria 360°
MUJER_FRENTE = (MUJER_DIR / "avatar_360_1_frente.png").read_bytes()
MUJER_TRES_CUARTOS = (MUJER_DIR / "avatar_360_2_tres_cuartos_izq.png").read_bytes()
MUJER_ESPALDA = (MUJER_DIR / "avatar_360_6_espalda.png").read_bytes()

# Pantallas reales del sistema MascotaMás (gestion.mascotamas.com)
UI_ESCRITORIO_MAC = (
    MANUAL_DIR / "00_Secuencias_Paso_a_Paso__01_Recorrido_Completo_App_10_Pantallas__01_Paso_1_Escritorio_y_Resumen_Operativo_del_Dia__01_MacBook_Pro_Real.png"
).read_bytes()
UI_ESCRITORIO_RAW = (
    MANUAL_DIR / "00_Secuencias_Paso_a_Paso__01_Recorrido_Completo_App_10_Pantallas__01_Paso_1_Escritorio_y_Resumen_Operativo_del_Dia__04_Raw_Desktop.png"
).read_bytes()
UI_CALENDARIOS_RAW = (
    MANUAL_DIR / "00_Secuencias_Paso_a_Paso__02_Flujo_Calendarios_y_Sena_MercadoPago__02_Paso_2_Modal_Crear_Calendario_Selector_de_4_Modalidades__04_Raw_Desktop.png"
).read_bytes()
UI_HC_PDF_RAW = (
    MANUAL_DIR / "06_Historias_Clinicas_y_Fichas__03_Legajo_Clinico_Digital_y_PDF__01_Modal_Historial_Completo_y_Descarga_PDF__04_Raw_Desktop.png"
).read_bytes()


def generate_keyframe(filename: str, parts_list: list):
    out_path = OUT_DIR / filename
    print(f"  -> [START] Generando {filename}...")
    resp = client.models.generate_content(
        model="gemini-3-pro-image",
        contents=parts_list,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio="9:16"),
        ),
    )
    for part in resp.candidates[0].content.parts:
        if part.inline_data:
            out_path.write_bytes(part.inline_data.data)
            shutil.copy2(out_path, ARTIFACTS_DIR / filename)
            print(f"  -> [SAVED] {out_path}")
            return filename
    raise RuntimeError(f"No se recibió imagen para {filename}")


def main():
    print("=== GENERANDO 4 KEYFRAMES DUETO (AVATAR HOMBRE VIP + AVATAR MUJER) CON GEMINI-3-PRO-IMAGE ===")

    jobs = [
        (
            "kf1_dueto_espalda_macbook_escritorio.png",
            [
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
        ),
        (
            "kf2_dueto_giro_hablando_camara.png",
            [
                types.Part.from_bytes(data=HOMBRE_FRENTE, mime_type="image/png"),
                types.Part.from_bytes(data=HOMBRE_ESPALDA, mime_type="image/png"),
                types.Part.from_bytes(data=MUJER_FRENTE, mime_type="image/png"),
                types.Part.from_bytes(data=MUJER_TRES_CUARTOS, mime_type="image/png"),
                types.Part.from_bytes(data=UI_ESCRITORIO_RAW, mime_type="image/png"),
                (
                    "Hyper-realistic vertical 9:16 commercial photography shot on Sony A7R V 35mm f/1.4 GM lens. "
                    "Over-the-shoulder view from behind ('enfocado desde espaldas') at the wooden reception desk of 'Veterinaria Palermo', "
                    "where BOTH the strong, muscular 38-year-old Argentine male veterinarian (on the left, from the first two reference images) "
                    "and the charismatic Argentine female veterinarian with a brunette ponytail (on the right, from the third and fourth reference images) "
                    "turn their heads and upper torsos over their shoulders toward the camera to make direct eye contact with warm, confident Argentine smiles as if speaking to the viewer. "
                    "Both wear their matching fitted dark petrol-teal 'VETERINARIA PALERMO' clinical scrubs with Littmann stethoscopes. "
                    "Between them on the desk, the open 16-inch Space Black MacBook Pro remains clearly visible to the camera, "
                    "displaying the exact 'MascotaMás — Escritorio Principal · Turnos del Día' interface from the fifth reference image, "
                    "while the male veterinarian points toward the laptop screen and the female veterinarian holds a Titanium iPhone 16 Pro Max."
                ),
            ],
        ),
        (
            "kf3_dueto_operando_turnos_y_hc_macbook.png",
            [
                types.Part.from_bytes(data=HOMBRE_FRENTE, mime_type="image/png"),
                types.Part.from_bytes(data=MUJER_FRENTE, mime_type="image/png"),
                types.Part.from_bytes(data=MUJER_TRES_CUARTOS, mime_type="image/png"),
                types.Part.from_bytes(data=UI_CALENDARIOS_RAW, mime_type="image/png"),
                types.Part.from_bytes(data=UI_ESCRITORIO_MAC, mime_type="image/png"),
                (
                    "Hyper-realistic vertical 9:16 commercial three-quarter over-the-shoulder shot on Sony A7R V 35mm f/1.4 GM lens. "
                    "In the modern 'Veterinaria Palermo' clinic reception, BOTH the strong muscular Argentine male veterinarian (left, first reference image) "
                    "and the charismatic Argentine female veterinarian (right, second and third reference images) in matching dark petrol-teal 'VETERINARIA PALERMO' scrubs and Littmann stethoscopes "
                    "collaborate dynamically at the wooden counter while looking toward the camera with expressive smiles. "
                    "In the foreground, the open 16-inch Space Black MacBook Pro screen clearly displays the exact 'MascotaMás — Crear Calendario · 4 Modalidades (Veterinaria, Peluquería, Guardería) + Seña Mercado Pago' web interface from the fourth reference image, "
                    "while the female veterinarian holds up a Titanium iPhone 16 Pro Max showing the MascotaMás mobile agenda."
                ),
            ],
        ),
        (
            "kf4_dueto_frente_hero_cta_mascotamas.png",
            [
                types.Part.from_bytes(data=HOMBRE_FRENTE, mime_type="image/png"),
                types.Part.from_bytes(data=HOMBRE_HERO, mime_type="image/png"),
                types.Part.from_bytes(data=MUJER_FRENTE, mime_type="image/png"),
                types.Part.from_bytes(data=UI_HC_PDF_RAW, mime_type="image/png"),
                types.Part.from_bytes(data=UI_ESCRITORIO_MAC, mime_type="image/png"),
                (
                    "Hyper-realistic vertical 9:16 medium-full front commercial hero shot on Sony A7R V 35mm f/1.4 GM lens. "
                    "Standing side by side facing the camera in the sunlit luxury Buenos Aires veterinary clinic reception 'Veterinaria Palermo' are BOTH official spokespersons: "
                    "on the left, the strong, muscular 38-year-old Argentine male veterinarian from the first and second reference images; "
                    "on the right, the charismatic Argentine female veterinarian with a brunette ponytail from the third reference image. "
                    "Both wear matching fitted dark petrol-teal clinical scrubs with 'VETERINARIA PALERMO' embroidered on the chest, Littmann stethoscopes around their necks, and the male vet wears his stainless-steel watch. "
                    "On the wooden reception counter in the lower-front foreground sits an open 16-inch Space Black MacBook Pro angled toward the viewer, "
                    "clearly displaying the 'MascotaMás — Historia Clínica Digital y Descarga PDF' web interface from the fourth reference image, "
                    "while the male veterinarian holds a Titanium iPhone 16 Pro Max in his hand and both smile warmly and gesture invitingly toward the camera."
                ),
            ],
        ),
    ]

    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = [ex.submit(generate_keyframe, fn, pts) for fn, pts in jobs]
        for f in as_completed(futs):
            print(f"  [DONE] {f.result()}")

    print("=== 4 KEYFRAMES DUETO GENERADOS CON ÉXITO ===")


if __name__ == "__main__":
    main()
