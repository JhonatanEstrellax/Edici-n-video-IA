import os
import sys
import base64
import pathlib
from google import genai

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

BASE_DIR = pathlib.Path(r"c:\IA\Edicion de videos")
WORK_DIR = BASE_DIR / "reels_work"
ENV_FILE = BASE_DIR / ".env"

for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.strip().startswith("#"):
        k, v = line.split("=", 1)
        os.environ[k.strip()] = v.strip()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

morocha_frame_path = WORK_DIR / "vet_avatar_morocha.png"
morocha_video_path = WORK_DIR / "vet_video_morocha_10s.mp4"

mode = sys.argv[1] if len(sys.argv) > 1 else "all"

if mode in ("image", "all"):
    print("[1/2] Generando retrato de veterinaria estilo Megan Fox (pelo morocho oscuro, ojos verdes intensos, piel blanca, rasgos esculpidos) con gemini-nano-banana-2.1...")
    img_interaction = client.interactions.create(
        model="gemini-nano-banana-2.1",
        input=[
            {
                "type": "text",
                "text": (
                    "Vertical 9:16 photorealistic smartphone portrait of a stunning, glamorous 28-year-old female veterinarian "
                    "with striking facial features: long glossy dark espresso-black brunette hair (pelo morocho oscuro brillante) "
                    "falling over her shoulders, piercing bright emerald-green almond-shaped eyes (ojos verdes intensos), "
                    "sculpted high cheekbones, a defined jawline, arched dark eyebrows, full natural lips with a warm confident smile, "
                    "and smooth porcelain fair white skin (piel blanca). "
                    "She is wearing a tailored teal-blue medical veterinary scrub V-neck uniform (ambo veterinario) with a professional "
                    "stethoscope draped around her neck. "
                    "Background is a bright, modern, clean veterinary clinic consultation room with soft natural daylight and shallow depth of field. "
                    "Medium close-up chest-up framing, looking directly into the camera lens, ultra-realistic 8k commercial photography."
                ),
            },
        ],
        response_format={
            "type": "image",
            "mime_type": "image/jpeg",
            "aspect_ratio": "9:16",
        },
    )
    if img_interaction.output_image and img_interaction.output_image.data:
        morocha_frame_path.write_bytes(base64.b64decode(img_interaction.output_image.data))
        print(f"  -> Retrato guardado en {morocha_frame_path} ({morocha_frame_path.stat().st_size} bytes)")
    else:
        raise RuntimeError("No se recibio output_image de gemini-nano-banana-2.1")

if mode in ("video", "all"):
    print("[2/2] Generando video 9:16 (10s, 1080p) con gemini-omni-1.2-flash...")
    raw_bytes = morocha_frame_path.read_bytes()
    mime_type = "image/png" if raw_bytes.startswith(b"\x89PNG") else "image/jpeg"
    morocha_b64 = base64.b64encode(raw_bytes).decode("utf-8")
    vid_interaction = client.interactions.create(
        model="gemini-omni-1.2-flash",
        input=[
            {
                "type": "image",
                "data": morocha_b64,
                "mime_type": mime_type,
            },
            {
                "type": "text",
                "text": (
                    "Use this image as the starting frame. In a single continuous unbroken vertical smartphone shot, "
                    "this glamorous young fair-skinned female veterinarian with long glossy dark brunette hair and piercing bright green eyes, "
                    "wearing a teal-blue scrub uniform with a stethoscope around her neck, speaks warmly and enthusiastically "
                    "directly to the camera in a bright modern veterinary clinic. She maintains natural eye contact with the "
                    "camera lens, smiles naturally, and makes subtle, friendly hand and head gestures while presenting. "
                    "Keep her sculpted facial features, dark brunette hair, green eyes, fair skin, and clinic background consistent."
                ),
            },
        ],
        response_format={
            "type": "video",
            "aspect_ratio": "9:16",
            "resolution": "1080p",
            "duration": "10s",
        },
    )
    if vid_interaction.output_video and vid_interaction.output_video.data:
        morocha_video_path.write_bytes(base64.b64decode(vid_interaction.output_video.data))
        print(f"  -> Video guardado en {morocha_video_path} ({morocha_video_path.stat().st_size} bytes)")
    else:
        raise RuntimeError("No se recibio output_video de gemini-omni-1.2-flash")

print("Proceso finalizado con éxito.")
