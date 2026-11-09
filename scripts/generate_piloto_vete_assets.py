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

# ---------------------------------------------------------
# 1. GENERATE VETERINARIAN PORTRAIT (Nano Banana 2.1)
# ---------------------------------------------------------
vet_frame_path = WORK_DIR / "vet_avatar_frame.png"
ref_img_path = WORK_DIR / "thumb_clip1_start.jpg"

if not vet_frame_path.exists():
    print("[1/3] Generando retrato de la protagonista vestida de veterinaria con gemini-nano-banana-2.1...")
    ref_b64 = base64.b64encode(ref_img_path.read_bytes()).decode("utf-8")
    img_interaction = client.interactions.create(
        model="gemini-nano-banana-2.1",
        input=[
            {
                "type": "image",
                "data": ref_b64,
                "mime_type": "image/jpeg",
            },
            {
                "type": "text",
                "text": (
                    "Edit this vertical 9:16 portrait of this exact same blonde woman, keeping her exact facial features, "
                    "eyes, skin tone, and long blonde hair identical. Dress her as a friendly, professional veterinarian "
                    "wearing a clean modern teal-blue medical scrub uniform (ambo veterinario) with a stethoscope draped "
                    "around her neck. Change the background to a bright, modern, clean veterinary clinic consultation room "
                    "with soft natural lighting. Photorealistic smartphone vertical video frame (9:16), looking directly "
                    "at the camera with a warm, confident smile."
                ),
            },
        ],
    )
    if img_interaction.output_image and img_interaction.output_image.data:
        vet_frame_path.write_bytes(base64.b64decode(img_interaction.output_image.data))
        print(f"  -> Guardado en {vet_frame_path} ({vet_frame_path.stat().st_size} bytes)")
    else:
        raise RuntimeError("No se recibio output_image de gemini-nano-banana-2.1")
else:
    print(f"[1/3] Retrato ya existe: {vet_frame_path}")

# ---------------------------------------------------------
# 2. DESIGN ARGENTINE VOICE & SYNTHESIZE 22s SCRIPT (TTS 3.8)
# ---------------------------------------------------------
voiceover_path = WORK_DIR / "vet_voiceover_ar.wav"
voice_id_file = WORK_DIR / "vet_voice_id.txt"

SCRIPT_TEXT = (
    "Si tenés una veterinaria, mirá las nuevas funciones que sumamos en MascotaMás. "
    "Ahora configurás agendas por servicio, profesional o guardería, conectadas en vivo con tu Sala de Espera. "
    "Tus clientes reservan abonando seña por Mercado Pago, con cero comisión en el Plan Premium. "
    "Además, descargás Historias Clínicas en PDF con foto del paciente y medís tus pacientes vistos. "
    "¡Probá hoy MascotaMás!"
)

if not voiceover_path.exists():
    print("[2/3] Diseñando voz femenina argentina y generando locución de ~22s con gemini-3.8-flash-tts...")
    voice_id = None
    if voice_id_file.exists():
        voice_id = voice_id_file.read_text(encoding="utf-8").strip()

    if not voice_id:
        try:
            created_voice = client.voices.create(
                store=True,
                voice={
                    "model": "gemini-3.8-flash-tts",
                    "type": "prompted",
                    "display_name": "Veterinaria Argentina MascotaMas",
                    "gender": "female",
                    "language_code": "es-AR",
                    "prompted": {
                        "input": (
                            "A warm, friendly, and confident 32-year-old Argentine woman from Buenos Aires, "
                            "speaking Rioplatense Spanish with natural porteño intonation, clear commercial articulation, "
                            "bright medium-pitched feminine timbre, and engaging conversational energy."
                        )
                    },
                },
            )
            voice_id = created_voice.id
            voice_id_file.write_text(voice_id, encoding="utf-8")
            print(f"  -> Voz argentina diseñada con ID: {voice_id}")
        except Exception as e:
            print(f"  -> Aviso en voices.create ({e}), usando voz Kore con estilo rioplatense...")
            voice_id = "Kore"

    tts_interaction = client.interactions.create(
        model="gemini-3.8-flash-tts",
        input=[
            {
                "type": "user_input",
                "content": [
                    {
                        "type": "text",
                        "text": SCRIPT_TEXT,
                        "annotations": [
                            {
                                "type": "speech_metadata",
                                "style": (
                                    "Warm, enthusiastic, natural Argentine Rioplatense commercial presenter from Buenos Aires, "
                                    "clear and agile pace suitable for a 22-second Instagram Reel"
                                ),
                            }
                        ],
                    }
                ],
            }
        ],
        response_format={"type": "audio"},
        generation_config={
            "speech_config": [
                {"voice": voice_id},
            ]
        },
    )
    if tts_interaction.output_audio and tts_interaction.output_audio.data:
        voiceover_path.write_bytes(base64.b64decode(tts_interaction.output_audio.data))
        print(f"  -> Locución guardada en {voiceover_path} ({voiceover_path.stat().st_size} bytes)")
    else:
        raise RuntimeError("No se recibio output_audio de gemini-3.8-flash-tts")
else:
    print(f"[2/3] Locución ya existe: {voiceover_path}")

# ---------------------------------------------------------
# 3. GENERATE 9:16 VIDEO OF HER AS VETERINARIAN (Omni 1.2 Flash)
# ---------------------------------------------------------
vet_video_path = WORK_DIR / "vet_video_10s.mp4"
if not vet_video_path.exists():
    print("[3/3] Generando video 9:16 (10s) de la veterinaria con gemini-omni-1.2-flash...")
    vet_img_b64 = base64.b64encode(vet_frame_path.read_bytes()).decode("utf-8")
    vid_interaction = client.interactions.create(
        model="gemini-omni-1.2-flash",
        input=[
            {
                "type": "image",
                "data": vet_img_b64,
                "mime_type": "image/png",
            },
            {
                "type": "text",
                "text": (
                    "Use this image as the starting frame. In a single continuous unbroken vertical smartphone shot, "
                    "this blonde female veterinarian in a teal-blue scrub uniform with a stethoscope around her neck "
                    "speaks warmly and enthusiastically directly to the camera in a bright modern veterinary clinic. "
                    "She maintains natural eye contact with the camera lens, smiles naturally, and makes subtle, "
                    "friendly hand and head gestures while presenting. Keep her facial features, hair, and clinic background consistent."
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
        vet_video_path.write_bytes(base64.b64decode(vid_interaction.output_video.data))
        print(f"  -> Video guardado en {vet_video_path} ({vet_video_path.stat().st_size} bytes)")
    else:
        raise RuntimeError("No se recibio output_video de gemini-omni-1.2-flash")
else:
    print(f"[3/3] Video ya existe: {vet_video_path}")

print("¡Todos los assets generativos de Gemini están listos!")
