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
full_path = WORK_DIR / "reel_cal_mp_lipsync_full.mp4"

prompt_t3 = (
    "Extend this video. In the same continuous unbroken shot, she immediately continues speaking directly to the camera "
    "at a brisk, fluid commercial pace without pauses between sentences, in the exact same Argentine Rioplatense Spanish "
    "voice and porteño accent from Buenos Aires, with accurate lip-sync, saying the exact words in Spanish: "
    "\"Y activás seña automática con Mercado Pago, contemplando posible comisión de Mercado Pago. ¡Entrá hoy en MascotaMás!\" "
    "She finishes speaking before the end of the clip and smiles warmly at the camera. No background music. Clear studio voice audio. Keep everything else the same."
)

for dur in ("8s", "6s"):
    try:
        print(f"[Turno 3/3] Extendiendo +{dur} desde Turno 2 ({res2_id})...")
        res3 = client.interactions.create(
            model="gemini-omni-1.2-flash",
            previous_interaction_id=res2_id,
            input=prompt_t3,
            response_format={
                "type": "video",
                "aspect_ratio": "9:16",
                "resolution": "1080p",
                "duration": dur,
            },
        )
        if res3.output_video and res3.output_video.data:
            full_path.write_bytes(base64.b64decode(res3.output_video.data))
            print(f"  -> Turno 3 (+{dur}) guardado en {full_path} ({full_path.stat().st_size} bytes), id={res3.id}")
            break
    except Exception as e:
        print(f"  -> Falló con {dur}: {e}")
else:
    raise RuntimeError("No se pudo extender Turno 3")
