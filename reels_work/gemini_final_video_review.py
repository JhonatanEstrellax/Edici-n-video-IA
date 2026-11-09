# -*- coding: utf-8 -*-
import os
import sys
import time
import pathlib
from google import genai
from google.genai import types

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

video_path = WORK_DIR / "final_output.mp4"
print(f"[GEMINI V3 REVIEW] Subiendo {video_path} ({video_path.stat().st_size} bytes) a Files API...")
uploaded = client.files.upload(file=str(video_path))
while uploaded.state.name == "PROCESSING":
    time.sleep(2)
    uploaded = client.files.get(name=uploaded.name)

prompt = """Analizá este Reel publicitario vertical (v3) de MascotaMás y evaluá los siguientes 6 puntos:
1. Presencia de la Veterinaria y Lip-Sync: ¿Se ve a la veterinaria presentando el sistema con sus labios sincronizados con la locución argentina y su rostro/boca despejados por encima de los mockups de MacBook Pro e iPhone?
2. Locución Argentina 10/10 (Gemini TTS): ¿La voz suena 100% natural, cálida, con voseo rioplatense argentino y ritmo pausado (sin mencionar en voz alta la comisión de Mercado Pago)?
3. Nota Legal con Asterisco (*) en Cursiva: ¿Aparece abajo en cursiva la aclaración '* Aplican posibles comisiones de Mercado Pago según las condiciones y plazos de acreditación de tu cuenta.'?
4. Música House (Lyria 3 - 125 BPM) y Transiciones de Pantalla: ¿La música House acompaña con energía comercial y cada cambio de escena/muestra de pantalla (0.00s, 4.32s, 10.56s, 15.36s, 20.16s, 25.44s) cae sincronizado con el pulso musical?
5. Muestras del Sistema (MacBook Pro e iPhone): ¿Se aprecian claramente los 4 tipos de calendario (Turnos 1 a 1, Cupos por Horario, Servicios y Profesionales, Guardería por Fechas) y el cobro de Seña Automática con Mercado Pago?
6. Veredicto general para publicación en Instagram Reels y TikTok.
Respondé en español en formato Markdown claro y conciso."""

res = client.models.generate_content(
    model="gemini-3.8-flash",
    contents=[uploaded, prompt],
    config=types.GenerateContentConfig(temperature=0.2)
)

review_md = WORK_DIR / "gemini_v3_video_review.md"
review_md.write_text(res.text, encoding="utf-8")
print(res.text)
