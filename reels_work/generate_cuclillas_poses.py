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

with open(os.path.join(WORK_DIR, "avatar_360_1_frente.png"), "rb") as f:
    front_bytes = f.read()

with open(os.path.join(WORK_DIR, "avatar_360_7_espalda_puntitas.png"), "rb") as f:
    back_bytes = f.read()

base_consistency = (
    "Keep this exact Argentine female veterinarian, same gorgeous face, green eyes, long dark brown wavy hair, "
    "modern Palermo veterinary clinic background, stethoscope, and exact outfit (second-skin ribbed stretch-knit "
    "deep V-neck dark teal top with 'VETERINARIA PALERMO' embroidery tucked into ultra-fitted high-waisted sculpting "
    "stretch dark teal trousers and sleek dark teal athletic sneakers, NO blazer). "
    "Preserve her exact athletic-curvy hourglass proportions (full bust, tiny cinched waist, curvy hips, and toned sculpted glutes). "
    "Full-length framing from head to feet, shot on Sony A7S III 85mm f/1.4, 100% natural anatomy, glamorous, elegant, vertical 9:16."
)

poses = [
    (
        "avatar_360_10_cuclillas_frente.png",
        front_bytes,
        base_consistency + " Pose: Full-body Front View (0 degrees straight-on from the front) in a deep full squat "
        "(en cuclillas de frente — squatting all the way down balanced on the balls of her feet with knees deeply bent "
        "and hips lowered close to her heels), torso upright and slightly angled forward, arms resting gracefully "
        "across her knees, smiling directly at the camera. Clearly showcases her face, full bust in the V-neck ribbed top, "
        "tiny waist, and curvy hips and thighs."
    ),
    (
        "avatar_360_11_cuclillas_espalda.png",
        back_bytes,
        base_consistency + " Pose: Full-body Back View (180 degrees from directly behind her back) in a deep full squat "
        "(en cuclillas de espalda — squatting all the way down balanced on the balls of her feet with heels lifted, "
        "knees deeply bent, and hips lowered near her heels), with her back arched gracefully and her head turned "
        "over her right shoulder smiling at the camera. Clearly showcases her narrow back, tiny waist, and round, "
        "sculpted glutes and thighs in the high-waisted fitted stretch dark teal trousers."
    ),
]

def generate_pose(item):
    fname, ref_b, prompt = item
    out_p = os.path.join(WORK_DIR, fname)
    print(f"Generating {fname}...")
    r = client.models.generate_content(
        model="gemini-3-pro-image",
        contents=[
            types.Part.from_bytes(data=ref_b, mime_type="image/png"),
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

with ThreadPoolExecutor(max_workers=2) as ex:
    list(ex.map(generate_pose, poses))

print("BOTH CUCLILLAS POSES GENERATED SUCCESSFULLY!")
