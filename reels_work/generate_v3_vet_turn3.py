# -*- coding: utf-8 -*-
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

res2_id = "v1_ChdkN2J3YXRxVkZNNkZ5dE1QbHZqYTRBSRIXQTdmd2FyZnBKYk9IaUxNUHZzRHU4UXc"
v3_raw_path = WORK_DIR / "reel_cal_mp_v3_lipsync_raw.mp4"

prompt_t3_v3 = (
    "Extend this video. In the same continuous unbroken shot, she immediately continues speaking directly to the camera "
    "at a natural, warm commercial pace in the exact same Argentine Rioplatense Spanish voice and porteño accent from Buenos Aires, "
    "with accurate lip-sync, saying the exact words in Spanish: "
    "\"Además, activás el cobro de seña automático con Mercado Pago para asegurar cada turno. ¡Entrá hoy en MascotaMás y probalo!\" "
    "She finishes speaking before the end of the clip and smiles warmly at the camera with her mouth closed. "
    "No background music. Clear studio voice audio. Keep everything else the same."
)

for dur in ("8s", "6s"):
    try:
        print(f"[V3 Turno 3/3] Extendiendo +{dur} desde Turno 2 ({res2_id})...")
        res3 = client.interactions.create(
            model="gemini-omni-1.2-flash",
            previous_interaction_id=res2_id,
            input=prompt_t3_v3,
            response_format={
                "type": "video",
                "aspect_ratio": "9:16",
                "resolution": "1080p",
                "duration": dur,
            },
        )
        if res3.output_video and res3.output_video.data:
            v3_raw_path.write_bytes(base64.b64decode(res3.output_video.data))
            print(f"  -> Turno 3 V3 (+{dur}) guardado en {v3_raw_path} ({v3_raw_path.stat().st_size} bytes), id={res3.id}")
            break
    except Exception as e:
        print(f"  -> Falló con {dur}: {e}")
else:
    raise RuntimeError("No se pudo extender Turno 3 para V3")
