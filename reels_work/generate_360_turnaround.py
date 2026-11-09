import os
from concurrent.futures import ThreadPoolExecutor
from google import genai
from google.genai import types

WORK_DIR = r"c:\IA\Edicion de videos\reels_work"
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    with open(r"c:\IA\Edicion de videos\.env", encoding="utf-8") as f:
        for line in f:
            if line.startswith("GEMINI_API_KEY="):
                api_key = line.strip().split("=", 1)[1].strip("\"'")

client = genai.Client(api_key=api_key)

with open(os.path.join(WORK_DIR, "vet_face_identity_ref.png"), "rb") as f:
    face_bytes = f.read()

base_style = (
    "Hyper-realistic vertical 9:16 commercial portrait shot on Sony A7S III 85mm f/1.4 "
    "in a luxury modern veterinary clinic in Palermo, Buenos Aires (warm wood, glass partitions, plants, soft bokeh). "
    "Keep the exact face identity from the reference image (gorgeous Argentine woman, green eyes, full lips, "
    "long dark brown wavy hair). "
    "Physique: voluptuous, athletic-curvy Latin fitness-model hourglass figure with a prominent, full round D-cup chest, "
    "a tiny cinched wasp waist, wide curvy hips, and toned, round, sculpted glutes (dramatic S-curve silhouette). "
    "Outfit: NO jacket and NO blazer — she wears ONLY a second-skin, form-fitting, ribbed stretch-knit deep V-neck "
    "dark teal top (with 'VETERINARIA PALERMO' delicately embroidered in white on the left chest) tucked into "
    "ultra-fitted, high-waisted sculpting stretch dark teal trousers that hug her tiny waist, hips, and glutes, "
    "with a sleek medical stethoscope draped around her neck. 100% natural human anatomy, glamorous, sexy, and elegant."
)

prompt_front = (
    base_style + " Angle: Front View (0 degrees), framed from head to mid-thigh, standing with a confident, "
    "slight feminine hip contrapposto pose that highlights her full bust, tiny waist, and wide curvy hips."
)

print("[1/5] Generating Front View (0 deg) with gemini-3-pro-image...")
resp_front = client.models.generate_content(
    model="gemini-3-pro-image",
    contents=[
        types.Part.from_bytes(data=face_bytes, mime_type="image/png"),
        prompt_front,
    ],
    config=types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(aspect_ratio="9:16"),
    ),
)

front_path = os.path.join(WORK_DIR, "avatar_360_1_frente.png")
front_bytes = None
for part in resp_front.candidates[0].content.parts:
    if part.inline_data:
        front_bytes = part.inline_data.data
        with open(front_path, "wb") as f:
            f.write(front_bytes)
        print("Saved:", front_path)

angles = [
    (
        "avatar_360_2_tres_cuartos_izq.png",
        "Angle: 3/4 Left View (body turned 45 degrees to the left, looking toward the camera over her right shoulder). "
        "Framed from head to mid-thigh. Clearly showcases the 3D projection of her full D-cup bust in the V-neck top, "
        "her tiny cinched waist, and the curvy contour of her hips and sculpted glutes."
    ),
    (
        "avatar_360_3_lateral_izq.png",
        "Angle: Full Left Side Profile View (body turned 90 degrees to the left in profile, head turned slightly toward camera). "
        "Framed from head to mid-thigh. Clearly showcases her complete lateral S-curve silhouette: prominent full bust, "
        "tiny flat waist, and round, lifted, sculpted glutes in the high-waisted fitted stretch trousers."
    ),
    (
        "avatar_360_4_tres_cuartos_der.png",
        "Angle: 3/4 Right View (body turned 45 degrees to the right, looking toward the camera). "
        "Framed from head to mid-thigh. Clearly showcases her full D-cup bust, tiny cinched waist, "
        "and the curvy contour of her hips and sculpted glutes from the right 3/4 perspective."
    ),
    (
        "avatar_360_5_lateral_der.png",
        "Angle: Full Right Side Profile View (body turned 90 degrees to the right in profile, head turned slightly toward camera). "
        "Framed from head to mid-thigh. Clearly showcases her complete lateral S-curve silhouette from the right side: "
        "prominent full bust, tiny flat waist, and round, lifted, sculpted glutes in the high-waisted fitted stretch trousers."
    ),
]

def gen_angle(item):
    fname, angle_desc = item
    out_p = os.path.join(WORK_DIR, fname)
    prompt = (
        "Keep this exact character, face, hair, clinic background, stethoscope, and exact outfit "
        "(second-skin ribbed stretch-knit deep V-neck dark teal top tucked into high-waisted sculpting stretch dark teal trousers, NO blazer) "
        "from the reference image, and rotate her body to the requested camera angle while preserving her exact "
        "voluptuous hourglass proportions (full D-cup bust, tiny waist, round sculpted glutes). " + angle_desc
    )
    print(f"Generating {fname}...")
    r = client.models.generate_content(
        model="gemini-3-pro-image",
        contents=[
            types.Part.from_bytes(data=front_bytes, mime_type="image/png"),
            prompt,
        ],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio="9:16"),
        ),
    )
    for p in r.candidates[0].content.parts:
        if p.inline_data:
            with open(out_p, "wb") as f:
                f.write(p.inline_data.data)
            print("Saved:", out_p)
            return out_p
    return None

with ThreadPoolExecutor(max_workers=4) as ex:
    list(ex.map(gen_angle, angles))

print("ALL 5 TURNAROUND VIEWS GENERATED SUCCESSFULLY!")
