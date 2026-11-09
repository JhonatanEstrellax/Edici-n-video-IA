# -*- coding: utf-8 -*-
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from google import genai
from google.genai import types

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

BASE_DIR = r"c:\IA\Edicion de videos"
WORK_DIR = os.path.join(BASE_DIR, "reels_work")
AVATAR_DIR = os.path.join(BASE_DIR, "assets", "avatar_veterinaria_360")

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    with open(os.path.join(BASE_DIR, ".env"), encoding="utf-8") as f:
        for line in f:
            if line.startswith("GEMINI_API_KEY="):
                api_key = line.strip().split("=", 1)[1].strip("\"'")

client = genai.Client(api_key=api_key)

with open(os.path.join(AVATAR_DIR, "avatar_360_1_frente.png"), "rb") as f:
    frente_bytes = f.read()
with open(os.path.join(AVATAR_DIR, "avatar_360_2_tres_cuartos_izq.png"), "rb") as f:
    tres_cuartos_bytes = f.read()

prompt_camilla = (
    "Hyper-realistic vertical 9:16 commercial medium-full shot on Sony A7S III 35mm f/1.8 in a luxury modern "
    "veterinary clinic in Palermo, Buenos Aires. "
    "Preserve 100% the exact female veterinarian from the reference images: identical face, bright emerald-green eyes, "
    "full lips, long glossy dark brunette wavy hair, voluptuous hourglass fitness-model physique (full round D-cup chest, "
    "tiny cinched waist, curvy hips), wearing the exact same form-fitting ribbed deep V-neck dark teal scrub top with "
    "'VETERINARIA PALERMO' embroidered in white on the left chest, high-waisted fitted dark teal trousers, and a "
    "stethoscope around her neck. "
    "Scene composition: She is standing in her veterinary consultation room right next to a modern stainless-steel "
    "veterinary examination table (camilla de consultorio) where a friendly, cute Golden Retriever dog is sitting "
    "calmly on the table. She rests one hand affectionately on the dog's back while looking directly into the camera "
    "lens with a warm, confident smile, framed from head to mid-thigh with generous headroom above her hair."
)

prompt_mostrador = (
    "Hyper-realistic vertical 9:16 commercial medium-full shot on Sony A7S III 35mm f/1.8 in a luxury modern "
    "veterinary clinic in Palermo, Buenos Aires. "
    "Preserve 100% the exact female veterinarian from the reference images: identical face, bright emerald-green eyes, "
    "full lips, long glossy dark brunette wavy hair, voluptuous hourglass fitness-model physique (full round D-cup chest, "
    "tiny cinched waist, curvy hips), wearing the exact same form-fitting ribbed deep V-neck dark teal scrub top with "
    "'VETERINARIA PALERMO' embroidered in white on the left chest, high-waisted fitted dark teal trousers, and a "
    "stethoscope around her neck. "
    "Scene composition: She is standing at the sleek modern wood-and-white-marble front reception counter / entrance desk "
    "(mostrador de entrada) of her Palermo veterinary clinic, with a sleek Space Gray MacBook Pro open on the counter "
    "beside her and warm glass entrance doors showing green Palermo street trees in soft bokeh behind her. She looks "
    "directly into the camera lens with a warm, confident smile, framed from head to waist/hips with generous headroom."
)

def gen_img(name: str, prompt_txt: str):
    out_path = os.path.join(WORK_DIR, name)
    print(f"[IMAGE] Generando {name} con gemini-3-pro-image-preview...")
    res = client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=[
            types.Part.from_bytes(data=frente_bytes, mime_type="image/png"),
            types.Part.from_bytes(data=tres_cuartos_bytes, mime_type="image/png"),
            prompt_txt,
        ],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio="9:16"),
        ),
    )
    for part in res.candidates[0].content.parts:
        if part.inline_data and part.inline_data.data:
            with open(out_path, "wb") as f:
                f.write(part.inline_data.data)
            print(f"  -> Guardado {out_path} ({os.path.getsize(out_path)} bytes)")
            return out_path
    raise RuntimeError(f"No image returned for {name}")

if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=2) as ex:
        f1 = ex.submit(gen_img, "avatar_v6B_camilla_perro_start.png", prompt_camilla)
        f2 = ex.submit(gen_img, "avatar_v6B_mostrador_entrada_ref.png", prompt_mostrador)
        print("Completado:", f1.result(), f2.result())
