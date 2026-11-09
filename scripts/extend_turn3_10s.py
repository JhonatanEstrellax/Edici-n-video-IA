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

res2_id = "v1_ChdhNlR2YXRhZEw0dXJ1TVlQaFpQZHlBRRIXUktidmFvT0pITkNpdU1ZUDlJQ0w0QXc"
full_video_path = WORK_DIR / "vet_video_morocha_lipsync_full.mp4"

print("[Turno 3 - 10s] Extendiendo +10s desde Turno 2 (18s -> 28s) a ritmo ágil sin pausas...")
res3 = client.interactions.create(
    model="gemini-omni-1.2-flash",
    previous_interaction_id=res2_id,
    input=(
        "Extend this video. In the same continuous unbroken shot, she immediately continues speaking directly to the camera "
        "at a brisk, fluid commercial pace without pauses between sentences, in the exact same Argentine Rioplatense Spanish "
        "voice and porteño accent from Buenos Aires, with accurate lip-sync, saying the exact words in Spanish: "
        "\"Además, descargás Historias Clínicas en PDF con foto del paciente y medís tus pacientes vistos. ¡Probá hoy MascotaMás!\" "
        "She finishes speaking before the end of the clip and smiles warmly at the camera. No background music. Clear studio voice audio. Keep everything else the same."
    ),
    response_format={
        "type": "video",
        "aspect_ratio": "9:16",
        "resolution": "1080p",
        "duration": "10s",
    },
)

if not (res3.output_video and res3.output_video.data):
    raise RuntimeError("No se recibio output_video en Turno 3 (10s)")

full_video_path.write_bytes(base64.b64decode(res3.output_video.data))
print(f"  -> Video completo (28s) guardado en {full_video_path} ({full_video_path.stat().st_size} bytes), id={res3.id}")
