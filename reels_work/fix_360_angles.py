import os
import shutil
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

# Keep avatar_360_3_lateral_izq.png as avatar_360_5_lateral_der.png (since she is facing the right edge of the frame)
shutil.copy2(
    os.path.join(WORK_DIR, "avatar_360_3_lateral_izq.png"),
    os.path.join(WORK_DIR, "avatar_360_5_lateral_der.png")
)

with open(os.path.join(WORK_DIR, "avatar_360_1_frente.png"), "rb") as f:
    front_bytes = f.read()

with open(os.path.join(WORK_DIR, "avatar_360_5_lateral_der.png"), "rb") as f:
    side_right_bytes = f.read()

tasks = [
    (
        "avatar_360_2_tres_cuartos_izq.png",
        front_bytes,
        "Keep this exact woman, face, hair, clinic background, stethoscope, and outfit (second-skin ribbed stretch-knit "
        "deep V-neck dark teal top with 'VETERINARIA PALERMO' embroidery tucked into high-waisted sculpting stretch dark teal trousers). "
        "Change the pose to a FRONT-DIAGONAL 3/4 LEFT VIEW (torso turned 45 degrees toward the LEFT edge of the image, "
        "so her V-neck cleavage and both breasts are visible in a 45-degree 3/4 front view facing left, while her right hip "
        "and glute curve out toward the right side of the image). Framed from head to mid-thigh, looking at the camera."
    ),
    (
        "avatar_360_4_tres_cuartos_der.png",
        front_bytes,
        "Keep this exact woman, face, hair, clinic background, stethoscope, and outfit (second-skin ribbed stretch-knit "
        "deep V-neck dark teal top with 'VETERINARIA PALERMO' embroidery tucked into high-waisted sculpting stretch dark teal trousers). "
        "Change the pose to a FRONT-DIAGONAL 3/4 RIGHT VIEW (torso turned 45 degrees toward the RIGHT edge of the image, "
        "so her V-neck cleavage and both breasts are visible in a 45-degree 3/4 front view facing right, while her left hip "
        "and glute curve out toward the left side of the image). Framed from head to mid-thigh, looking at the camera."
    ),
    (
        "avatar_360_3_lateral_izq.png",
        side_right_bytes,
        "Keep this exact woman, face, hair, stethoscope, and outfit (second-skin ribbed stretch-knit dark teal top tucked "
        "into high-waisted sculpting stretch dark teal trousers). "
        "Change the pose to the opposite FULL LEFT SIDE PROFILE VIEW: her body is in 90-degree side profile facing toward "
        "the LEFT edge of the image (so her prominent full bust points toward the LEFT side of the image, her waist is tiny, "
        "and her round sculpted glutes curve out toward the RIGHT side of the image), with her head turned slightly toward the camera."
    ),
]

def run_one(item):
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

with ThreadPoolExecutor(max_workers=3) as ex:
    list(ex.map(run_one, tasks))

print("Completed 3 distinct angles!")
