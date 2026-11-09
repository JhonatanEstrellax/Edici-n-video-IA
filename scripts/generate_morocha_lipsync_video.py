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
part1_video_path = WORK_DIR / "vet_video_morocha_lipsync_part1.mp4"
full_video_path = WORK_DIR / "vet_video_morocha_lipsync_full.mp4"
interaction_id_path = WORK_DIR / "vet_lipsync_interaction_id.txt"

raw_bytes = morocha_frame_path.read_bytes()
mime_type = "image/png" if raw_bytes.startswith(b"\x89PNG") else "image/jpeg"
morocha_b64 = base64.b64encode(raw_bytes).decode("utf-8")

print("[Turno 1/2] Generando primeros 12s con diálogo argentino y lip-sync nativo en gemini-omni-1.2-flash...")
res1 = client.interactions.create(
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
                "Use this image as the starting frame. In a single continuous unbroken vertical smartphone shot "
                "in a bright modern veterinary clinic, this glamorous young fair-skinned female veterinarian with "
                "long glossy dark brunette hair and piercing bright green eyes speaks directly to the camera in Spanish "
                "with a natural Argentine Rioplatense accent from Buenos Aires (porteño voseo and yeísmo pronunciation), "
                "with accurate lip-sync and warm commercial enthusiasm, saying the exact words in Spanish: "
                "\"Si tenés una veterinaria, mirá las nuevas funciones que sumamos en MascotaMás. "
                "Ahora configurás agendas por servicio, profesional o guardería, conectadas en vivo con tu Sala de Espera.\" "
                "No background music. Clear studio voice audio. Keep her sculpted facial features, dark brunette hair, "
                "green eyes, fair skin, and clinic background consistent."
            ),
        },
    ],
    response_format={
        "type": "video",
        "aspect_ratio": "9:16",
        "resolution": "1080p",
        "duration": "12s",
    },
)

if not (res1.output_video and res1.output_video.data):
    raise RuntimeError("No se recibio output_video en Turno 1 de gemini-omni-1.2-flash")

part1_video_path.write_bytes(base64.b64decode(res1.output_video.data))
interaction_id_path.write_text(res1.id, encoding="utf-8")
print(f"  -> Turno 1 guardado en {part1_video_path} ({part1_video_path.stat().st_size} bytes), id={res1.id}")

print("[Turno 2/2] Extendiendo video (+10s -> 22s totales) con la segunda mitad del diálogo argentino y lip-sync...")
res2 = client.interactions.create(
    model="gemini-omni-1.2-flash",
    previous_interaction_id=res1.id,
    input=(
        "Extend this video. In the same continuous unbroken shot, she continues speaking directly to the camera "
        "in the exact same Argentine Rioplatense Spanish voice and porteño accent from Buenos Aires, with accurate "
        "lip-sync and warm commercial enthusiasm, saying the exact words in Spanish: "
        "\"Tus clientes reservan abonando seña por Mercado Pago, con cero comisión en el Plan Premium. "
        "Además, descargás Historias Clínicas en PDF con foto del paciente y medís tus pacientes vistos. "
        "¡Probá hoy MascotaMás!\" "
        "No background music. Clear studio voice audio. Keep everything else the same."
    ),
    response_format={
        "type": "video",
        "aspect_ratio": "9:16",
        "resolution": "1080p",
        "duration": "10s",
    },
)

if not (res2.output_video and res2.output_video.data):
    raise RuntimeError("No se recibio output_video en Turno 2 de gemini-omni-1.2-flash")

full_video_path.write_bytes(base64.b64decode(res2.output_video.data))
print(f"  -> Turno 2 (video completo extendido) guardado en {full_video_path} ({full_video_path.stat().st_size} bytes)")
print("¡Generación con lip-sync nativo completada!")
