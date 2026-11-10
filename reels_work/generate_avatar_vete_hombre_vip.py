# -*- coding: utf-8 -*-
r"""
Genera el Pack Avatar Veterinario Hombre VIP Argentino en alta resolución (9:16)
utilizando `gemini-3-pro-image` (Nano Banana Pro):
- Extrae recortes de alta precisión de la cabeza/rostro en cada ángulo (frente, perfil derecho, perfil izquierdo, nuca/espalda)
  para preservar al 100% la identidad facial real del usuario sin que la remera suelta de la foto casera limite la estructura corporal.
- Esculpe un físico bien macho argentino, fuerte, atlético y estilizado VIP PERSON:
  hombros anchos y potentes, pectorales marcados en 3D, bíceps gruesos que llenan las mangas, antebrazos musculosos y venosos,
  torso en V con cintura atlética estrecha, piernas fuertes y postura alfa dominante.
"""
import os
import sys
import shutil
import pathlib
import io
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont
from google import genai
from google.genai import types

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

BASE_DIR = pathlib.Path(r"c:\IA\Edicion de videos")
WORK_DIR = BASE_DIR / "reels_work"
OUT_DIR = BASE_DIR / "assets" / "avatar_veterinario_hombre_vip"
OUT_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACTS_DIR = pathlib.Path(r"C:\Users\Demiante\.gemini\antigravity\brain\56e5cec9-1285-4884-b2c6-a38ac91ed5ae")
UPLOAD_DIR = ARTIFACTS_DIR / ".user_uploaded"

ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip().strip("\"'")

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

REF_FRONT_1 = UPLOAD_DIR / "media_1794273940385_7332d4ff.jpg"
REF_RIGHT = UPLOAD_DIR / "media_1794273940389_dcd44b88.jpg"
REF_FRONT_2 = UPLOAD_DIR / "media_1794273940394_c1ede90a.jpg"
REF_BACK = UPLOAD_DIR / "media_1794273940399_5f22a7bf.jpg"
REF_LEFT = UPLOAD_DIR / "media_1794273940402_a8c21393.jpg"


def crop_head_bytes(img_path, box_rel):
    """Recorta únicamente la cabeza y cuello (sin la remera suelta) para fijar 100% identidad facial."""
    im = Image.open(img_path).convert("RGB")
    w, h = im.size
    x1, y1, x2, y2 = [int( box_rel[0]*w ), int( box_rel[1]*h ), int( box_rel[2]*w ), int( box_rel[3]*h )]
    crop = im.crop((x1, y1, x2, y2))
    buf = io.BytesIO()
    crop.save(buf, format="PNG")
    return buf.getvalue()


# Recortes de cabeza/rostro reales en cada ángulo
head_front1_bytes = crop_head_bytes(REF_FRONT_1, (0.36, 0.16, 0.64, 0.37))
head_front2_bytes = crop_head_bytes(REF_FRONT_2, (0.36, 0.16, 0.64, 0.37))
head_right_bytes = crop_head_bytes(REF_RIGHT, (0.36, 0.15, 0.68, 0.36))
head_left_bytes = crop_head_bytes(REF_LEFT, (0.34, 0.16, 0.66, 0.36))
head_back_bytes = crop_head_bytes(REF_BACK, (0.36, 0.16, 0.66, 0.36))


BASE_VIP_STYLE = (
    "Hyper-realistic vertical 9:16 commercial full-body portrait shot on Sony A7R V 85mm f/1.4 GM lens, "
    "100% real human skin texture with natural pores, masculine facial lines, and cinematic lighting. "
    "Identity: Keep the EXACT face identity, eyes, nose, cheekbones, masculine jawline, short dark brown wavy hair, "
    "and thick masculine stubble beard from the reference face photos. "
    "Physique ('bien macho argentino, REAL, fuerte, estilizado VIP PERSON'): "
    "He has a powerful, muscular, sculpted, athletic male fitness-model V-taper physique — wide, capped muscular shoulders (deltoids), "
    "a thick, broad, sculpted muscular chest (3D pectorals clearly defined under the fitted fabric), thick muscular biceps that tightly fill "
    "the short sleeves, thick vascular muscular forearms, a narrow flat athletic waist (pronounced V-taper from wide shoulders to trim waist), "
    "and strong, athletic legs with tall, commanding alpha posture. "
    "Outfit: He wears an ultra-fitted, stretch-tailored luxury dark teal V-neck medical scrub top (ambo quirúrgico VIP entallado de tela elástica premium) "
    "that hugs and contours his broad muscular pectorals, wide shoulders, V-taper torso, and biceps (with subtle white/gold 'MASCOTAMÁS VIP' embroidery on the left chest), "
    "paired with tailored athletic-fit dark teal scrub trousers, clean white luxury leather sneakers, a high-end stainless-steel luxury chronograph watch "
    "on his left wrist, and a sleek black & silver Littmann Cardiology stethoscope draped around his neck. "
    "Background: Bright, high-end luxury veterinary clinic in Palermo, Buenos Aires (warm architectural wood, glass partitions, soft natural daylight bokeh)."
)


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
    print("[1/7] Generando Pose 1 Maestra: De Frente Cuerpo Entero (0°) — Físico Fuerte, Muscular y Estilizado VIP...")
    prompt_frente = (
        BASE_VIP_STYLE
        + " Angle: Full-body Front View (0 degrees, head to white sneakers visible). Standing tall and powerful facing the camera "
        "with a confident, charismatic Argentine alpha expression, showcasing his wide muscular shoulders, sculpted chest under the fitted "
        "stretch scrub top, narrow V-taper waist, thick muscular biceps and vascular forearms, and luxury steel watch."
    )
    hero_front_path = OUT_DIR / "avatar_vete_hombre_vip_1_frente.png"
    hero_front_bytes = generate_image(
        [
            types.Part.from_bytes(data=head_front1_bytes, mime_type="image/png"),
            types.Part.from_bytes(data=head_front2_bytes, mime_type="image/png"),
            prompt_frente,
        ],
        hero_front_path,
    )

    tasks = [
        (
            "avatar_vete_hombre_vip_hero_brazos_cruzados.png",
            [
                types.Part.from_bytes(data=hero_front_bytes, mime_type="image/png"),
                types.Part.from_bytes(data=head_front1_bytes, mime_type="image/png"),
            ],
            "Keep this exact man, exact facial identity, beard, hair, powerful muscular V-taper physique, ultra-fitted dark teal VIP scrubs, "
            "stethoscope, luxury steel watch, and Palermo VIP clinic background from the first reference image. "
            "Framing: Medium-full VIP Hero Portrait (from head to mid-thigh). Pose: He stands with his thick muscular arms confidently crossed "
            "over his broad sculpted chest, flexing his biceps and vascular forearms with the luxury chronograph watch clearly visible, "
            "looking directly at the camera with an intense, warm, self-assured Argentine VIP expression.",
        ),
        (
            "avatar_vete_hombre_vip_2_tres_cuartos_izq.png",
            [
                types.Part.from_bytes(data=hero_front_bytes, mime_type="image/png"),
                types.Part.from_bytes(data=head_left_bytes, mime_type="image/png"),
            ],
            "Keep this exact man, exact facial identity, beard, hair, powerful muscular V-taper physique (wide shoulders, sculpted 3D pectorals, "
            "thick biceps, vascular forearms, trim waist), ultra-fitted dark teal VIP scrubs, stethoscope, luxury steel watch, white sneakers, "
            "and Palermo VIP clinic background from the first reference image. "
            "Change the pose to a FULL-BODY FRONT-DIAGONAL 3/4 LEFT VIEW (-45 degrees: body turned 45 degrees toward the left edge of the frame, "
            "head to shoes visible, looking confidently at the camera), highlighting the 3D thickness of his muscular chest, deltoids, and left arm.",
        ),
        (
            "avatar_vete_hombre_vip_3_lateral_izq.png",
            [
                types.Part.from_bytes(data=hero_front_bytes, mime_type="image/png"),
                types.Part.from_bytes(data=head_left_bytes, mime_type="image/png"),
            ],
            "Keep this exact man, exact facial profile (from the second reference image), beard, hair, powerful muscular physique, "
            "ultra-fitted dark teal VIP scrubs, stethoscope, luxury steel watch, white sneakers, and Palermo VIP clinic background from the first reference image. "
            "Change the pose to a FULL-BODY 90-DEGREE LEFT SIDE PROFILE VIEW (facing toward the left edge of the frame, head to shoes visible), "
            "clearly showcasing his strong masculine jaw, thick 3D chest projection, large capped left shoulder and muscular bicep/forearm with the steel watch, "
            "flat waist, and athletic legs.",
        ),
        (
            "avatar_vete_hombre_vip_4_tres_cuartos_der.png",
            [
                types.Part.from_bytes(data=hero_front_bytes, mime_type="image/png"),
                types.Part.from_bytes(data=head_right_bytes, mime_type="image/png"),
            ],
            "Keep this exact man, exact facial identity, beard, hair, powerful muscular V-taper physique (wide shoulders, sculpted 3D pectorals, "
            "thick biceps, vascular forearms, trim waist), ultra-fitted dark teal VIP scrubs, stethoscope, luxury steel watch, white sneakers, "
            "and Palermo VIP clinic background from the first reference image. "
            "Change the pose to a FULL-BODY FRONT-DIAGONAL 3/4 RIGHT VIEW (+45 degrees: body turned 45 degrees toward the right edge of the frame, "
            "head to shoes visible, looking confidently toward the camera), highlighting his broad muscular chest, shoulders, and strong arms.",
        ),
        (
            "avatar_vete_hombre_vip_5_lateral_der.png",
            [
                types.Part.from_bytes(data=hero_front_bytes, mime_type="image/png"),
                types.Part.from_bytes(data=head_right_bytes, mime_type="image/png"),
            ],
            "Keep this exact man, exact right facial profile (from the second reference image), beard, hair, powerful muscular physique, "
            "ultra-fitted dark teal VIP scrubs, stethoscope, white sneakers, and Palermo VIP clinic background from the first reference image. "
            "Change the pose to a FULL-BODY 90-DEGREE RIGHT SIDE PROFILE VIEW (facing toward the right edge of the frame, head to shoes visible), "
            "clearly showcasing his strong masculine right profile, thick 3D chest projection, capped right deltoid, thick muscular right bicep and vascular forearm, "
            "flat waist, and upright athletic posture.",
        ),
        (
            "avatar_vete_hombre_vip_6_espalda.png",
            [
                types.Part.from_bytes(data=hero_front_bytes, mime_type="image/png"),
                types.Part.from_bytes(data=head_back_bytes, mime_type="image/png"),
            ],
            "Keep this exact man, back of head and hair (from the second reference image), powerful muscular V-taper physique, "
            "ultra-fitted dark teal VIP scrubs, white sneakers, and Palermo VIP clinic background from the first reference image. "
            "Change the pose to a FULL-BODY 180-DEGREE BACK VIEW (standing facing directly away from the camera, head to shoes visible), "
            "clearly showcasing his wide muscular shoulders, broad V-taper upper back (lats and traps), narrow waist, and thick muscular arms.",
        ),
    ]

    def run_task(item):
        fname, parts, prompt = item
        out_p = OUT_DIR / fname
        print(f"  -> Generando {fname}...")
        return generate_image(parts + [prompt], out_p)

    with ThreadPoolExecutor(max_workers=3) as ex:
        list(ex.map(run_task, tasks))

    print("7. Creando láminas comparativas (Antes vs Después y Turnaround 360° Completo)...")
    font_path = str(BASE_DIR / "fonts" / "Poppins-ExtraBold.ttf")
    font = ImageFont.truetype(font_path, 32) if os.path.exists(font_path) else ImageFont.load_default()

    tw, th = 480, 854
    comp_sheet = Image.new("RGB", (tw * 4, th * 2), (15, 23, 42))
    all_8 = [
        (REF_FRONT_1, "ANTES: Foto Real Frente"),
        (OUT_DIR / "avatar_vete_hombre_vip_1_frente.png", "VIP 1: Frente (0°)"),
        (OUT_DIR / "avatar_vete_hombre_vip_hero_brazos_cruzados.png", "VIP Hero: Brazos Cruzados"),
        (OUT_DIR / "avatar_vete_hombre_vip_2_tres_cuartos_izq.png", "VIP 2: 3/4 Izq (-45°)"),
        (REF_RIGHT, "ANTES: Foto Real Perfil"),
        (OUT_DIR / "avatar_vete_hombre_vip_5_lateral_der.png", "VIP 5: Lateral Der (+90°)"),
        (OUT_DIR / "avatar_vete_hombre_vip_3_lateral_izq.png", "VIP 3: Lateral Izq (-90°)"),
        (OUT_DIR / "avatar_vete_hombre_vip_6_espalda.png", "VIP 6: Espalda (180°)"),
    ]
    for idx, (img_p, label) in enumerate(all_8):
        im = Image.open(img_p).convert("RGB").resize((tw, th), Image.LANCZOS)
        dr = ImageDraw.Draw(im)
        dr.rectangle([0, 0, tw, 62], fill=(15, 23, 42))
        col = (242, 199, 92) if "VIP" in label else (180, 200, 220)
        dr.text((16, 12), label, font=font, fill=col)
        r_idx = idx // 4
        c_idx = idx % 4
        comp_sheet.paste(im, (c_idx * tw, r_idx * th))

    sheet_path = OUT_DIR / "avatar_vete_hombre_vip_master_sheet.png"
    comp_sheet.save(sheet_path)
    shutil.copy2(sheet_path, ARTIFACTS_DIR / sheet_path.name)
    print(f"  -> [SAVED MASTER SHEET] {sheet_path}")


if __name__ == "__main__":
    main()
