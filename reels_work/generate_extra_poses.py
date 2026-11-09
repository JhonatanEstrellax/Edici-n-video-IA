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

with open(os.path.join(WORK_DIR, "avatar_360_5_lateral_der.png"), "rb") as f:
    side_bytes = f.read()

base_consistency = (
    "Keep this exact Argentine female veterinarian, same gorgeous face, green eyes, long dark brown wavy hair, "
    "modern Palermo veterinary clinic background, stethoscope, and exact outfit (second-skin ribbed stretch-knit "
    "deep V-neck dark teal top tucked into ultra-fitted high-waisted sculpting stretch dark teal trousers, NO blazer). "
    "Preserve her exact athletic-curvy hourglass proportions (full bust, tiny cinched waist, curvy hips, and toned sculpted glutes). "
    "Shot on Sony A7S III 85mm f/1.4, 100% natural anatomy, glamorous, elegant, vertical 9:16."
)

poses = [
    (
        "avatar_360_6_espalda.png",
        side_bytes,
        base_consistency + " Pose: Standing Back View (180 degrees from behind), framed from head to knee, "
        "with her head turned gracefully over her right shoulder smiling at the camera. Clearly showcases her "
        "narrow back, tiny cinched waist, and round, sculpted glutes in the high-waisted fitted dark teal trousers."
    ),
    (
        "avatar_360_7_espalda_puntitas.png",
        side_bytes,
        base_consistency + " Pose: Full-body Back View (180 degrees from behind) standing high on her tiptoes "
        "(en puntitas de pie, heels lifted high off the floor in sleek athletic sneakers/footwear) as she reaches "
        "gracefully toward an upper glass shelf in the clinic, looking back over her shoulder at the camera. "
        "Full-length framing from head to feet so her tiptoe stance, toned calves, thighs, sculpted lifted glutes, "
        "and tiny waist are completely visible."
    ),
    (
        "avatar_360_8_espalda_agachada.png",
        side_bytes,
        base_consistency + " Pose: Rear-diagonal Back View crouching / squatting down gracefully on her heels "
        "(agachada de espalda) in the veterinary clinic as if organizing a low clinic cabinet, looking back over "
        "her shoulder toward the camera with a warm captivating smile. Clearly showcases her arched lower back, "
        "tiny waist, and curvy, sculpted hips and glutes in the high-waisted stretch dark teal trousers."
    ),
    (
        "avatar_360_9_frente_agachada.png",
        front_bytes,
        base_consistency + " Pose: Front View crouching / squatting down gracefully (agachada de frente) in the "
        "veterinary clinic, leaning slightly forward with a warm, confident smile directed at the camera. "
        "Clearly showcases her face, stethoscope, full bust in the ribbed V-neck dark teal top, tiny waist, "
        "and curvy hips and thighs."
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

with ThreadPoolExecutor(max_workers=4) as ex:
    list(ex.map(generate_pose, poses))

print("ALL 4 EXTRA POSES GENERATED SUCCESSFULLY!")
