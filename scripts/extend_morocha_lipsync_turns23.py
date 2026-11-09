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

interaction_id_path = WORK_DIR / "vet_lipsync_interaction_id.txt"
part2_video_path = WORK_DIR / "vet_video_morocha_lipsync_part2.mp4"
full_video_path = WORK_DIR / "vet_video_morocha_lipsync_full.mp4"

res1_id = interaction_id_path.read_text(encoding="utf-8").strip()
print(f"Usando Turno 1 existente: {res1_id}")

print("[Turno 2/3] Extendiendo +6s (Mercado Pago y Plan Premium) con lip-sync argentino...")
res2 = client.interactions.create(
    model="gemini-omni-1.2-flash",
    previous_interaction_id=res1_id,
    input=(
        "Extend this video. In the same continuous unbroken shot, she continues speaking directly to the camera "
        "in the exact same Argentine Rioplatense Spanish voice and porteño accent from Buenos Aires, with accurate "
        "lip-sync and warm commercial enthusiasm, saying the exact words in Spanish: "
        "\"Tus clientes reservan abonando seña por Mercado Pago, con cero comisión en el Plan Premium.\" "
        "No background music. Clear studio voice audio. Keep everything else the same."
    ),
    response_format={
        "type": "video",
        "aspect_ratio": "9:16",
        "resolution": "1080p",
        "duration": "6s",
    },
)

if not (res2.output_video and res2.output_video.data):
    raise RuntimeError("No se recibio output_video en Turno 2")

part2_video_path.write_bytes(base64.b64decode(res2.output_video.data))
print(f"  -> Turno 2 guardado en {part2_video_path} ({part2_video_path.stat().st_size} bytes), id={res2.id}")

print("[Turno 3/3] Extendiendo +8s (Historias Clínicas PDF, Pacientes Vistos y ¡Probá hoy MascotaMás!) con lip-sync argentino...")
res3 = client.interactions.create(
    model="gemini-omni-1.2-flash",
    previous_interaction_id=res2.id,
    input=(
        "Extend this video. In the same continuous unbroken shot, she continues speaking directly to the camera "
        "in the exact same Argentine Rioplatense Spanish voice and porteño accent from Buenos Aires, with accurate "
        "lip-sync and warm commercial enthusiasm, saying the exact words in Spanish: "
        "\"Además, descargás Historias Clínicas en PDF con foto del paciente y medís tus pacientes vistos. "
        "¡Probá hoy MascotaMás!\" "
        "She finishes with a warm, confident smile to the camera. No background music. Clear studio voice audio. Keep everything else the same."
    ),
    response_format={
        "type": "video",
        "aspect_ratio": "9:16",
        "resolution": "1080p",
        "duration": "8s",
    },
)

if not (res3.output_video and res3.output_video.data):
    raise RuntimeError("No se recibio output_video en Turno 3")

full_video_path.write_bytes(base64.b64decode(res3.output_video.data))
print(f"  -> Turno 3 (video completo con lip-sync) guardado en {full_video_path} ({full_video_path.stat().st_size} bytes), id={res3.id}")
print("¡Extensión completa finalizada!")
