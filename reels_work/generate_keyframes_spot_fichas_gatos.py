# -*- coding: utf-8 -*-
r"""
Genera los 4 Keyframes en alta resolución (9:16) con `gemini-3-pro-image` (Nano Banana Pro)
para el Spot Publicitario de MascotaMás (Sección: Fichas de Clientes para un Hotel de Gatos)
protagonizado por el Avatar Hombre VIP Argentino con ropa urbana/casual, enfocado desde espaldas
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
OUT_DIR = BASE_DIR / "assets" / "avatar_veterinario_hombre_vip" / "spot_fichas_gatos"
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

# Capturas reales de MascotaMás -> Fichas de Clientes (Hotel de Gatos)
UI_FICHAS_LISTADO_RAW = (
    MANUAL_DIR / "06_Historias_Clinicas_y_Fichas__05_Fichas_de_Clientes_Hotel_de_Gatos__01_Listado_y_Buscador_Felino__04_Raw_Desktop.png"
).read_bytes()
UI_FICHAS_LISTADO_MAC = (
    MANUAL_DIR / "06_Historias_Clinicas_y_Fichas__05_Fichas_de_Clientes_Hotel_de_Gatos__01_Listado_y_Buscador_Felino__01_MacBook_Pro_Real.png"
).read_bytes()
UI_FICHA_NANA_RAW = (
    MANUAL_DIR / "06_Historias_Clinicas_y_Fichas__05_Fichas_de_Clientes_Hotel_de_Gatos__02_Modal_Ficha_de_Cliente_Gato_NANA__04_Raw_Desktop.png"
).read_bytes()
UI_FICHA_NANA_IPHONE = (
    MANUAL_DIR / "06_Historias_Clinicas_y_Fichas__05_Fichas_de_Clientes_Hotel_de_Gatos__02_Modal_Ficha_de_Cliente_Gato_NANA__02_iPhone_16_Pro_Max_Real.png"
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
    print("=== GENERANDO 4 KEYFRAMES DEL SPOT PUBLICITARIO MASCOTAMÁS (FICHAS DE CLIENTES - HOTEL DE GATOS) ===")

    # 1. Keyframe 1: Enfocado desde espaldas (Over-the-shoulder) usando MacBook Pro (Fichas de Clientes - Hotel de Gatos) y Celular con ropa urbana/casual
    p1 = (
        "Hyper-realistic vertical 9:16 commercial shot on Sony A7R V 35mm f/1.4 GM lens. "
        "Character & Outfit: The exact strong, muscular Argentine VIP male from the first two reference images "
        "(broad muscular shoulders, V-taper back, thick muscular biceps and vascular forearms, short dark wavy hair), "
        "dressed in stylish modern URBAN / SMART-CASUAL VIP clothing: an ultra-fitted deep-navy / slate-charcoal premium cotton crew-neck t-shirt / henley "
        "that hugs his muscular back, wide shoulders, and thick biceps, dark tailored jeans, and a stainless-steel luxury chronograph watch on his left wrist (no medical scrubs, no stethoscope). "
        "Camera Angle ('enfocado desde espaldas usando una computadora y celular'): "
        "Over-the-shoulder view from behind him as he sits/leans at a sleek warm-wood modern reception/executive desk in a stylish boutique Buenos Aires Cat Hotel ('Hotel de Gatos' with warm wood shelving and subtle modern feline design touches in the softly blurred background). "
        "With his right hand he is using a real Space Black 16-inch MacBook Pro open on the desk in front of him, and in his left hand he holds a Titanium iPhone 16 Pro Max. "
        "CRITICAL SCREEN DETAIL: On the large, sharp, brightly lit screen of the MacBook Pro 16-inch, reproduce with 100% fidelity the exact MascotaMás web interface "
        "from the third and fourth reference images ('mascotaMÁS · Hotel de Gatos MichiVIP · Fichas de Clientes', showing the white left sidebar with purple 'Fichas de Clientes' active, "
        "purple button 'Agregar Ficha de Cliente', 'Buscador Avanzado' with 'Especie: Gato', and 'Todas las Fichas de Clientes' listing cats 'NANA · Gato · Común eur...', 'Milo · Gato · Siamés', 'Pupi · Gato · Mestizo')."
    )
    kf1_path = OUT_DIR / "kf1_espalda_macbook_fichas_gatos.png"
    kf1_bytes = generate_image(
        [
            types.Part.from_bytes(data=AVATAR_BACK, mime_type="image/png"),
            types.Part.from_bytes(data=AVATAR_HERO, mime_type="image/png"),
            types.Part.from_bytes(data=UI_FICHAS_LISTADO_RAW, mime_type="image/png"),
            types.Part.from_bytes(data=UI_FICHAS_LISTADO_MAC, mime_type="image/png"),
            p1,
        ],
        kf1_path,
    )

    tasks = [
        (
            "kf2_espalda_giro_hablando_fichas_gatos.png",
            [
                types.Part.from_bytes(data=kf1_bytes, mime_type="image/png"),
                types.Part.from_bytes(data=AVATAR_HERO, mime_type="image/png"),
                types.Part.from_bytes(data=UI_FICHAS_LISTADO_RAW, mime_type="image/png"),
            ],
            "Keep the exact same camera framing from behind / over-the-shoulder, the exact same muscular Argentine VIP man in his fitted deep-navy/charcoal urban short-sleeve shirt "
            "and luxury steel watch, the exact same modern wood desk in the boutique Cat Hotel, and the exact same 16-inch MacBook Pro displaying the crisp 'MascotaMás - Fichas de Clientes (NANA, Milo, Pupi - Gato)' interface on screen. "
            "Change his pose so that while still seen from behind at the desk with the MacBook Pro screen clearly visible in front of him and the iPhone in his left hand, "
            "he turns his head and upper torso over his right shoulder toward the camera (showing his exact face, masculine stubble beard, and charismatic smile from the second reference image) "
            "as he speaks to the viewer and points his right hand toward the 'Fichas de Clientes' screen on the MacBook Pro.",
        ),
        (
            "kf3_espalda_modal_ficha_nana_gato.png",
            [
                types.Part.from_bytes(data=kf1_bytes, mime_type="image/png"),
                types.Part.from_bytes(data=AVATAR_Q_DER, mime_type="image/png"),
                types.Part.from_bytes(data=UI_FICHA_NANA_RAW, mime_type="image/png"),
                types.Part.from_bytes(data=UI_FICHA_NANA_IPHONE, mime_type="image/png"),
            ],
            "Keep the exact same over-the-shoulder camera framing from behind the exact same muscular Argentine VIP man in his fitted deep-navy/charcoal urban short-sleeve shirt and luxury steel watch "
            "at the same wood desk in the boutique Cat Hotel. He is using the 16-inch MacBook Pro and holding his iPhone 16 Pro Max. "
            "On the large, crisp screen of the 16-inch MacBook Pro, display with 100% fidelity the third reference image: the open MascotaMás modal 'Ficha de Cliente de NANA' "
            "(showing button 'Descargar Ficha', 'INFORMACIÓN DEL TUTOR: cecilia rivas', purple square avatar 'N', 'NANA · Hembra · Gato · Común europeo · 2 años'). "
            "On the iPhone 16 Pro Max screen in his left hand, show the mobile MascotaMás 'Ficha de Cliente de NANA' view from the fourth reference image. "
            "He looks over his right shoulder toward the camera with a confident, warm expression.",
        ),
        (
            "kf4_frente_casual_vip_cta_fichas_gatos.png",
            [
                types.Part.from_bytes(data=AVATAR_HERO, mime_type="image/png"),
                types.Part.from_bytes(data=kf1_bytes, mime_type="image/png"),
                types.Part.from_bytes(data=UI_FICHAS_LISTADO_RAW, mime_type="image/png"),
            ],
            "Hyper-realistic vertical 9:16 medium-full commercial shot in the exact same modern Buenos Aires boutique Cat Hotel office. "
            "The exact same muscular Argentine VIP man (with his exact face, short dark wavy hair, masculine stubble beard, wide shoulders, sculpted 3D chest, thick muscular biceps and vascular forearms "
            "from the first reference image), dressed in the exact same fitted deep-navy/charcoal urban short-sleeve shirt, dark tailored jeans, and luxury stainless-steel chronograph watch (no scrubs, no stethoscope), "
            "has turned around to face the camera directly, leaning confidently against the front edge of the wood desk. "
            "He holds his Titanium iPhone 16 Pro Max in his left hand and gestures warmly toward the camera with his right hand as he speaks. "
            "Right beside him on the desk, the open 16-inch MacBook Pro screen is angled toward the camera clearly showing the 'MascotaMás - Fichas de Clientes (Hotel de Gatos)' interface.",
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
