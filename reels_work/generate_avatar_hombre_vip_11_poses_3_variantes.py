# -*- coding: utf-8 -*-
r"""
Genera el Pack Completo de 11 Poses + Hero (12 vistas por variante = 36 imágenes 9:16 en alta resolución)
del Avatar Hombre VIP Argentino con `gemini-3-pro-image` en las 3 variantes solicitadas:
1. Modo Veterinario (`VETERINARIA PALERMO`)
2. Modo Groomer Canino (`GROOMING VIP - PELUQUERÍA CANINA`)
3. Modo Casual Urbano (`CASUAL URBANO VIP`)

Y ensambla los 3 Grids Maestros 4x3 etiquetados (idénticos en estructura al grid de 11 poses de la veterinaria)
más un Mega-Grid comparativo de las 3 variantes.
"""
import os
import sys
import shutil
import pathlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image, ImageDraw, ImageFont
from google import genai
from google.genai import types

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

BASE_DIR = pathlib.Path(r"c:\IA\Edicion de videos")
AVATAR_HOMBRE_DIR = BASE_DIR / "assets" / "avatar_veterinario_hombre_vip"
AVATAR_MUJER_DIR = BASE_DIR / "assets" / "avatar_veterinaria_360"
ARTIFACTS_DIR = pathlib.Path(r"C:\Users\Demiante\.gemini\antigravity\brain\56e5cec9-1285-4884-b2c6-a38ac91ed5ae")
EDITADOS_DIR = BASE_DIR / "editados"
EDITADOS_DIR.mkdir(parents=True, exist_ok=True)

FONT_EXTRABOLD = str(BASE_DIR / "fonts" / "Poppins-ExtraBold.ttf")
FONT_BOLD = str(BASE_DIR / "fonts" / "Poppins-Bold.ttf")

ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip().strip("\"'")

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Referencias de identidad del Avatar Hombre VIP
REF_HOMBRE_HERO = (AVATAR_HOMBRE_DIR / "avatar_vete_hombre_vip_hero_brazos_cruzados.png").read_bytes()
REF_HOMBRE_FRENTE = (AVATAR_HOMBRE_DIR / "avatar_vete_hombre_vip_1_frente.png").read_bytes()
REF_HOMBRE_ESPALDA = (AVATAR_HOMBRE_DIR / "avatar_vete_hombre_vip_6_espalda.png").read_bytes()
REF_HOMBRE_LAT_IZQ = (AVATAR_HOMBRE_DIR / "avatar_vete_hombre_vip_3_lateral_izq.png").read_bytes()
REF_HOMBRE_LAT_DER = (AVATAR_HOMBRE_DIR / "avatar_vete_hombre_vip_5_lateral_der.png").read_bytes()

# Referencias de postura de las poses 7..11 del pack 360 para clavar el encuadre exacto de cada pose
REF_POSE_7 = (AVATAR_MUJER_DIR / "avatar_360_7_espalda_puntitas.png").read_bytes()
REF_POSE_8 = (AVATAR_MUJER_DIR / "avatar_360_8_espalda_agachada.png").read_bytes()
REF_POSE_9 = (AVATAR_MUJER_DIR / "avatar_360_9_frente_agachada.png").read_bytes()
REF_POSE_10 = (AVATAR_MUJER_DIR / "avatar_360_10_cuclillas_frente.png").read_bytes()
REF_POSE_11 = (AVATAR_MUJER_DIR / "avatar_360_11_cuclillas_espalda.png").read_bytes()

IDENTITY_DESC = (
    "The EXACT same strong, muscular, handsome 38-year-old Argentine VIP man from the first two reference images: "
    "chiseled masculine jawline, groomed short dark-brown beard/stubble, expressive warmhazel-brown eyes, "
    "thick short wavy dark-brown hair, broad athletic shoulders, V-taper torso, thick muscular biceps and vascular forearms, "
    "wearing a luxury stainless-steel chronograph watch on his left wrist."
)

VARIANTS = {
    "modo_veterinario_palermo": {
        "title": "MODO VETERINARIO · VETERINARIA PALERMO",
        "subtitle": "11 Poses 360° + Hero VIP · Ambos Clínicos Petrol-Teal 'VETERINARIA PALERMO' + Estetoscopio Littmann",
        "accent_rgb": (56, 189, 248),
        "outfit": (
            "wearing an ultra-fitted dark petrol-teal athletic-luxury short-sleeve veterinary scrub top and matching tailored scrub trousers "
            "that hug his muscular chest, shoulders, back, and arms, with 'VETERINARIA PALERMO' embroidered in clean white letters on the left chest "
            "(and on the upper back when seen from behind), a professional black/silver Littmann stethoscope around his neck, and clean off-white leather clinical sneakers"
        ),
        "env": (
            "inside the bright, modern luxury 'Veterinaria Palermo' clinic in Buenos Aires with warm oak wood door frames, "
            "floor-to-ceiling glass partitions with subtle 'VETERINARIA PALERMO' frosted lettering, lush indoor green plants in ceramic pots, and warm wood flooring"
        ),
        "out_Grid_name": "grid_11_poses_hombre_vip_modo_veterinario_palermo.png",
    },
    "modo_groomer": {
        "title": "MODO GROOMER CANINO · PELUQUERÍA CANINA VIP",
        "subtitle": "11 Poses 360° + Hero VIP · Chaqueta Impermeable Negra 'GROOMING VIP' con Vivo Violeta + Tijeras Profesionales",
        "accent_rgb": (168, 85, 247),
        "outfit": (
            "wearing a sleek, ultra-fitted matte-black water-resistant short-sleeve professional dog groomer zip-smock / technical groomer vest "
            "with subtle purple collar/shoulder piping, 'GROOMING VIP' embroidered on the chest, stainless-steel professional grooming shears and comb tucked into his pocket, "
            "dark tailored work trousers, and sleek black athletic work sneakers (NO stethoscope)"
        ),
        "env": (
            "inside a luxury modern Buenos Aires Dog Grooming Salon ('Peluquería Canina') with warm wood shelving, "
            "neatly arranged professional grooming shears, combs, and premium dog shampoo bottles, glass partitions, and warm wood flooring"
        ),
        "out_Grid_name": "grid_11_poses_hombre_vip_modo_groomer.png",
    },
    "modo_casual_urbano": {
        "title": "MODO CASUAL URBANO · ESTILO BUENOS AIRES VIP",
        "subtitle": "11 Poses 360° + Hero VIP · Remera Entallada Charcoal-Navy Premium + Chinos Oscuros + Sneakers Cuero",
        "accent_rgb": (242, 199, 92),
        "outfit": (
            "wearing a premium ultra-fitted charcoal-navy crew-neck cotton t-shirt that highlights his muscular chest, broad shoulders, V-taper back, and thick vascular arms, "
            "tailored dark slate-grey urban chino trousers, a dark leather belt, and clean white/black luxury leather urban sneakers (NO stethoscope, NO uniform badges)"
        ),
        "env": (
            "inside a stylish modern Palermo Soho architectural loft & pet-friendly executive space in Buenos Aires with warm vertical wood slats, "
            "glass partitions, indoor tropical plants, and warm natural daylight"
        ),
        "out_Grid_name": "grid_11_poses_hombre_vip_modo_casual_urbano.png",
    },
}

POSES_SPEC = [
    (
        "01_lateral_izq_90",
        "1. LATERAL IZQ (-90°)",
        [REF_HOMBRE_HERO, REF_HOMBRE_LAT_IZQ],
        "Full-body profile shot facing 90 degrees to the LEFT ('Lateral Izquierdo -90°'), turning his head slightly toward the camera with a confident charismatic smile, showing his muscular left arm and athletic posture.",
    ),
    (
        "02_tres_cuartos_izq_45",
        "2. 3/4 IZQ (-45°)",
        [REF_HOMBRE_HERO, REF_HOMBRE_FRENTE],
        "Three-quarter full-body shot angled 45 degrees to the LEFT ('3/4 Izquierda -45°'), looking directly at the camera with a warm, self-assured Argentine smile.",
    ),
    (
        "03_frente_0",
        "3. FRENTE (0°)",
        [REF_HOMBRE_HERO, REF_HOMBRE_FRENTE],
        "Full-body front shot ('Frente 0°') standing straight and confident, looking directly into the camera lens with a warm charismatic smile.",
    ),
    (
        "04_tres_cuartos_der_45",
        "4. 3/4 DER (+45°)",
        [REF_HOMBRE_HERO, REF_HOMBRE_FRENTE],
        "Three-quarter full-body shot angled 45 degrees to the RIGHT ('3/4 Derecha +45°'), looking directly at the camera with a warm, confident smile.",
    ),
    (
        "05_lateral_der_90",
        "5. LATERAL DER (+90°)",
        [REF_HOMBRE_HERO, REF_HOMBRE_LAT_DER],
        "Full-body profile shot facing 90 degrees to the RIGHT ('Lateral Derecho +90°'), turning his head slightly toward the camera with a confident charismatic smile.",
    ),
    (
        "06_espalda_180",
        "6. DE ESPALDA (180°)",
        [REF_HOMBRE_ESPALDA, REF_HOMBRE_HERO],
        "Full-body shot from behind ('De Espalda 180°') showcasing his broad muscular V-taper back and shoulders, turning his head over his right shoulder to look back at the camera with a charismatic smile.",
    ),
    (
        "07_espalda_puntitas",
        "7. ESPALDA PUNTITAS",
        [REF_HOMBRE_ESPALDA, REF_HOMBRE_HERO, REF_POSE_7],
        "Match the exact body pose of the third reference image ('7. Espalda en Puntitas'): full-body shot from behind standing on his tiptoes ('en puntitas de pie'), reaching his right arm up toward a high glass/wood shelf while turning his head over his shoulder to smile at the camera.",
    ),
    (
        "08_espalda_agachado",
        "8. ESPALDA AGACHADO",
        [REF_HOMBRE_ESPALDA, REF_HOMBRE_HERO, REF_POSE_8],
        "Match the exact body pose of the third reference image ('8. Espalda Agachado'): full-body shot from behind/side crouching down low ('agachado de espalda/perfil') reaching into a low wooden cabinet with both hands while turning his head over his right shoulder to smile warmly at the camera.",
    ),
    (
        "09_frente_agachado",
        "9. FRENTE AGACHADO",
        [REF_HOMBRE_FRENTE, REF_HOMBRE_HERO, REF_POSE_9],
        "Match the exact body pose of the third reference image ('9. Frente Agachado'): three-quarter front crouching pose ('frente agachado') with knees bent low and forearms resting naturally near his knees as if greeting a pet at low table level, looking directly at the camera with a warm smile.",
    ),
    (
        "10_cuclillas_frente",
        "10. CUCLILLAS FRENTE",
        [REF_HOMBRE_FRENTE, REF_HOMBRE_HERO, REF_POSE_10],
        "Match the exact body pose of the third reference image ('10. Cuclillas Frente'): full deep squat facing the camera ('en cuclillas de frente') at floor level with elbows resting on his knees, smiling warmly directly into the lens.",
    ),
    (
        "11_cuclillas_espalda",
        "11. CUCLILLAS ESPALDA",
        [REF_HOMBRE_ESPALDA, REF_HOMBRE_HERO, REF_POSE_11],
        "Match the exact body pose of the third reference image ('11. Cuclillas Espalda'): full deep squat seen from behind ('en cuclillas de espalda') at floor level, turning his head over his right shoulder to smile charismatically at the camera.",
    ),
    (
        "12_hero_brazos_cruzados",
        "12. HERO VIP (BRAZOS CRUZADOS)",
        [REF_HOMBRE_HERO, REF_HOMBRE_FRENTE],
        "Medium-full Hero VIP portrait ('Hero Brazos Cruzados') with his thick muscular arms crossed confidently over his chest, looking directly into the lens with charismatic authority.",
    ),
]


def generate_single_pose(variant_key: str, pose_tuple: tuple) -> pathlib.Path:
    pose_id, pose_label, ref_bytes_list, pose_prompt = pose_tuple
    v_cfg = VARIANTS[variant_key]
    out_dir = AVATAR_HOMBRE_DIR / variant_key
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{variant_key}_{pose_id}.png"

    if out_path.exists() and out_path.stat().st_size > 100_000:
        print(f"  -> [SKIP EXISTING] {out_path.name}")
        return out_path

    full_prompt = (
        "Hyper-realistic vertical 9:16 commercial photography shot on Sony A7R V with 50mm f/1.2 GM lens, 8k photorealistic skin texture. "
        f"Subject Identity: {IDENTITY_DESC} "
        f"Outfit: {v_cfg['outfit']}. "
        f"Environment: {v_cfg['env']}. "
        f"Pose & Framing: {pose_prompt}"
    )

    contents = [types.Part.from_bytes(data=b, mime_type="image/png") for b in ref_bytes_list] + [full_prompt]

    for attempt in range(3):
        try:
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
                    out_path.write_bytes(part.inline_data.data)
                    print(f"  -> [SAVED] {variant_key}/{out_path.name} ({len(part.inline_data.data) // 1024} KB)")
                    return out_path
        except Exception as e:
            print(f"  [WARN] Retry {attempt + 1} for {variant_key}/{pose_id}: {e}")
    raise RuntimeError(f"Failed to generate {variant_key}/{pose_id}")


def build_variant_grid(variant_key: str) -> pathlib.Path:
    v_cfg = VARIANTS[variant_key]
    out_dir = AVATAR_HOMBRE_DIR / variant_key

    # Grid 4 columnas x 3 filas (idéntico en formato a avatar_360_11_poses_master_sheet.png)
    cell_w, cell_h = 540, 960
    label_h = 56
    pad = 8
    header_h = 128

    cols, rows = 4, 3
    grid_w = cols * cell_w + (cols + 1) * pad
    grid_h = header_h + rows * (cell_h + label_h) + (rows + 1) * pad

    accent = v_cfg["accent_rgb"]
    canvas = Image.new("RGB", (grid_w, grid_h), (15, 19, 32))
    draw = ImageDraw.Draw(canvas)

    font_header_title = ImageFont.truetype(FONT_EXTRABOLD, 42)
    font_header_sub = ImageFont.truetype(FONT_BOLD, 24)
    font_cell_label = ImageFont.truetype(FONT_EXTRABOLD, 24)

    # Top Banner Header
    draw.rectangle([0, 0, grid_w, header_h], fill=(20, 26, 46))
    draw.line([(0, header_h - 3), (grid_w, header_h - 3)], fill=accent, width=6)
    draw.text((28, 20), f"PACK AVATAR 360° (11 POSES + HERO) — {v_cfg['title']}", font=font_header_title, fill=(255, 255, 255))
    draw.text((28, 76), v_cfg["subtitle"], font=font_header_sub, fill=accent)

    for idx, (pose_id, pose_label, _, _) in enumerate(POSES_SPEC):
        r = idx // cols
        c = idx % cols
        x0 = pad + c * (cell_w + pad)
        y0 = header_h + pad + r * (cell_h + label_h + pad)

        # Barra superior de etiqueta de celda (estilo avatar_360_11_poses_master_sheet.png)
        draw.rectangle([x0, y0, x0 + cell_w, y0 + label_h], fill=(38, 16, 48), outline=accent, width=2)
        draw.text((x0 + 16, y0 + 12), pose_label, font=font_cell_label, fill=(255, 255, 255))

        img_path = out_dir / f"{variant_key}_{pose_id}.png"
        im = Image.open(img_path).convert("RGB").resize((cell_w, cell_h), Image.Resampling.LANCZOS)
        canvas.paste(im, (x0, y0 + label_h))
        draw.rectangle([x0, y0, x0 + cell_w, y0 + label_h + cell_h], outline=accent, width=3)

    grid_path = AVATAR_HOMBRE_DIR / v_cfg["out_Grid_name"]
    canvas.save(grid_path, format="PNG", optimize=True)
    shutil.copy2(grid_path, ARTIFACTS_DIR / grid_path.name)
    shutil.copy2(grid_path, EDITADOS_DIR / grid_path.name)

    # Guardar también versión JPG ligera para visualización rápida
    jpg_path = grid_path.with_suffix(".jpg")
    canvas.save(jpg_path, format="JPEG", quality=93)
    shutil.copy2(jpg_path, ARTIFACTS_DIR / jpg_path.name)
    print(f"  -> [GRID GUARDADO] {grid_path} ({grid_w}x{grid_h})")
    return grid_path


def main():
    print("=== GENERANDO LAS 11 POSES + HERO EN LAS 3 VARIANTES DEL AVATAR HOMBRE VIP (36 IMÁGENES) ===")
    jobs = []
    for v_key in ["modo_groomer", "modo_casual_urbano", "modo_veterinario_palermo"]:
        for pose_tuple in POSES_SPEC:
            jobs.append((v_key, pose_tuple))

    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(generate_single_pose, vk, pt): (vk, pt[0]) for vk, pt in jobs}
        for f in as_completed(futs):
            vk, pid = futs[f]
            f.result()

    print("=== ENSAMBLANDO LOS 3 GRIDS DE 11 POSES + HERO ===")
    grid_paths = []
    for v_key in ["modo_groomer", "modo_casual_urbano", "modo_veterinario_palermo"]:
        gp = build_variant_grid(v_key)
        grid_paths.append(gp)

    # Mega-Grid comparativo con las 3 variantes lado a lado
    imgs = [Image.open(p).convert("RGB") for p in grid_paths]
    target_w = 1080
    target_h = int(imgs[0].height * (target_w / float(imgs[0].width)))
    resized = [im.resize((target_w, target_h), Image.Resampling.LANCZOS) for im in imgs]
    mega = Image.new("RGB", (target_w * 3 + 32, target_h + 16), (12, 16, 28))
    for i, im in enumerate(resized):
        mega.paste(im, (8 + i * (target_w + 8), 8))
    mega_path = AVATAR_HOMBRE_DIR / "grid_comparativo_3_variantes_11_poses_hombre_vip.jpg"
    mega.save(mega_path, format="JPEG", quality=93)
    shutil.copy2(mega_path, ARTIFACTS_DIR / mega_path.name)
    shutil.copy2(mega_path, EDITADOS_DIR / mega_path.name)
    print(f"  -> [MEGA-GRID COMPARATIVO GUARDADO] {mega_path}")


if __name__ == "__main__":
    main()
