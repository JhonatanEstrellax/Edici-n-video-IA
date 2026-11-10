# -*- coding: utf-8 -*-
r"""
Genera los 3 clips de video profesionales (1080p, 9:16, 10s cada uno = 30s totales)
con `gemini-omni-1.2-flash` para el Spot Publicitario de MascotaMás
(Sección: Turnos para Peluquerías Caninas):
- Clip 1 (10s, 1080p): Con ropa de Groomer Canino, enfocado desde espaldas usando la MacBook Pro 16"
  (mostrando Turnos -> Peluquería Canina por Groomer y Servicios) y el iPhone 16 Pro Max,
  girando naturalmente sobre su hombro hacia cámara con lip-sync argentino (es-AR).
- Clip 2 (10s, 1080p): Enfocado desde espaldas operando los turnos por peluquero, duración y seña Mercado Pago
  en la MacBook Pro 16" y el celular, girando hacia cámara con lip-sync argentino (es-AR).
- Clip 3 (10s, 1080p): Plano medio-frente VIP con ropa de Groomer Canino junto a la MacBook Pro (Turnos Peluquería Canina)
  y el iPhone en mano, dando el cierre y llamada a la acción (CTA) con lip-sync argentino (es-AR).
"""
import os
import sys
import pathlib
from concurrent.futures import ThreadPoolExecutor, as_completed

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

SKILL_SCRIPTS_DIR = r"C:\Users\Demiante\.gemini\config\plugins\gemini-api\skills\gemini-omni-flash-api\scripts"
sys.path.insert(0, SKILL_SCRIPTS_DIR)
sys.path.insert(0, os.path.join(SKILL_SCRIPTS_DIR, "video"))
from generate_video import generate_video, resolve_or_upload_asset, DEFAULT_MODEL

BASE_DIR = pathlib.Path(r"c:\IA\Edicion de videos")
SPOT_DIR = BASE_DIR / "assets" / "avatar_veterinario_hombre_vip" / "spot_peluqueria_canina"
AVATAR_DIR = BASE_DIR / "assets" / "avatar_veterinario_hombre_vip"
MANUAL_DIR = BASE_DIR / "assets" / "manual_vete_y_marca"
ENV_FILE = BASE_DIR / ".env"

if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip().strip("\"'")


def main():
    print(f"=== GENERANDO 3 CLIPS 1080p (9:16) CON {DEFAULT_MODEL} PARA SPOT MASCOTAMÁS TURNOS PELUQUERÍA CANINA ===")

    assets = {
        "kf1": str(SPOT_DIR / "kf1_espalda_groomer_macbook_turnos_peluqueria.png"),
        "kf2": str(SPOT_DIR / "kf2_espalda_giro_groomer_hablando_turnos_peluqueria.png"),
        "kf3": str(SPOT_DIR / "kf3_espalda_groomer_agenda_y_sena_peluqueria.png"),
        "kf4": str(SPOT_DIR / "kf4_frente_groomer_vip_cta_peluqueria.png"),
        "hero": str(AVATAR_DIR / "avatar_vete_hombre_vip_hero_brazos_cruzados.png"),
        "ui_tablero": str(
            MANUAL_DIR
            / "03_Turnos_y_Agenda__08_Turnos_Peluqueria_Canina__01_Tablero_por_Groomer_y_Servicios__04_Raw_Desktop.png"
        ),
        "ui_agenda": str(
            MANUAL_DIR
            / "03_Turnos_y_Agenda__08_Turnos_Peluqueria_Canina__02_Agenda_Diaria_Turnos_Confirmados_y_Sena_MP__04_Raw_Desktop.png"
        ),
    }

    uris = {}
    for k, path_str in assets.items():
        uri, _ = resolve_or_upload_asset(path_str, "image/png")
        uris[k] = uri
        print(f"  -> [Uploaded {k}] {uri}")

    out_clip1 = str(SPOT_DIR / "spot_peluqueria_clip1_espalda_a_giro_10s.mp4")
    out_clip2 = str(SPOT_DIR / "spot_peluqueria_clip2_espalda_agenda_y_sena_10s.mp4")
    out_clip3 = str(SPOT_DIR / "spot_peluqueria_clip3_frente_groomer_vip_cta_10s.mp4")

    jobs = [
        {
            "name": "Clip1_Espalda_Groomer_MacBook_Giro_Hablando_10s",
            "kwargs": {
                "prompt": (
                    "Use the first image as the starting frame and the second image as the final frame. "
                    "In a single continuous 9:16 commercial shot in a modern Buenos Aires Dog Grooming Salon ('Peluquería Canina'), "
                    "[0-2.0s] seen from behind over his shoulder ('enfocado desde espaldas'), the strong muscular Argentine man "
                    "dressed in his fitted matte-black short-sleeve professional dog groomer zip-smock/apron and steel watch is typing on his 16-inch MacBook Pro "
                    "(which clearly displays the 'MascotaMás - Turnos · PELUQUERÍA CANINA (SERVICIOS)' web system on screen) while holding his iPhone 16 Pro Max. "
                    "[2.0-9.0s] He smoothly turns his head and upper torso over his shoulder to look directly at the camera with a charismatic smile, "
                    "points naturally toward the 'Turnos Peluquería Canina' screen on the MacBook Pro, and speaks with clear, natural male Rioplatense Argentine Spanish (es-AR) lip-sync: "
                    "\"¿Tenés una peluquería canina y seguís dando turnos por WhatsApp? Mirá cómo organizo cada baño y corte en MascotaMás.\" "
                    "[9.0-10.0s] He holds a confident, warm smile looking at the camera while pointing to the laptop screen. Upbeat house music softly in background."
                ),
                "model": DEFAULT_MODEL,
                "aspect_ratio": "9:16",
                "duration": "10s",
                "resolution": "1080p",
                "first_frame": uris["kf1"],
                "last_frame": uris["kf2"],
                "output_path": out_clip1,
                "timeout": 900,
            },
        },
        {
            "name": "Clip2_Espalda_Groomer_Agenda_Servicios_y_Sena_10s",
            "kwargs": {
                "prompt": (
                    "Use the first image as the starting frame and the second image as the final frame. "
                    "In this exact same continuous 9:16 over-the-shoulder commercial shot from behind ('enfocado desde espaldas'), "
                    "[0-8.2s] the strong muscular Argentine man in his fitted matte-black short-sleeve professional dog groomer zip-smock/apron and luxury steel watch "
                    "speaks over his shoulder directly to the camera with clear, natural male Rioplatense Argentine Spanish (es-AR) lip-sync "
                    "while gesturing to the 16-inch MacBook Pro screen and lowering his right hand to click on the keyboard to display the daily grooming appointments "
                    "('Luna · Caniche · En Peluquería · Seña MP $15.000 · Servicio: Baño y Corte Razas Chicas') and checking his iPhone 16 Pro Max in his left hand: "
                    "\"Asignás cada turno por peluquero, duración del servicio, cobrás seña con Mercado Pago y confirmás por WhatsApp en un clic.\" "
                    "[8.2-10.0s] He finishes clicking on the MacBook Pro keyboard while looking confidently over his shoulder at the camera as shown in the final frame. "
                    "Upbeat house music softly in background."
                ),
                "model": DEFAULT_MODEL,
                "aspect_ratio": "9:16",
                "duration": "10s",
                "resolution": "1080p",
                "first_frame": uris["kf2"],
                "last_frame": uris["kf3"],
                "output_path": out_clip2,
                "timeout": 900,
            },
        },
        {
            "name": "Clip3_Frente_Groomer_VIP_CTA_Peluqueria_10s",
            "kwargs": {
                "prompt": (
                    "Use the first image as the starting frame. "
                    "In a continuous 9:16 medium-full commercial shot in the modern Buenos Aires Dog Grooming Salon ('Peluquería Canina'), "
                    "the strong muscular Argentine VIP man in his fitted matte-black short-sleeve professional dog groomer zip-smock/apron, dark trousers, and luxury steel watch "
                    "leans confidently against the wooden counter next to the open 16-inch MacBook Pro (displaying 'MascotaMás - Turnos Peluquería Canina' on screen) "
                    "while holding his iPhone 16 Pro Max in his left hand. "
                    "[0.4-8.8s] Looking directly at the camera with natural, charismatic body movement and expressive hand gestures, "
                    "he speaks with clear, energetic male Rioplatense Argentine Spanish (es-AR) lip-sync: "
                    "\"¡Pasate hoy a MascotaMás! Migramos toda tu peluquería canina en el día y cien por ciento gratis. ¡Escribinos ahora!\" "
                    "[8.8-10.0s] He finishes with a warm, self-assured Argentine smile looking directly into the lens. Upbeat house music softly in background."
                ),
                "model": DEFAULT_MODEL,
                "aspect_ratio": "9:16",
                "duration": "10s",
                "resolution": "1080p",
                "first_frame": uris["kf4"],
                "image_path": [uris["hero"], uris["ui_tablero"]],
                "output_path": out_clip3,
                "timeout": 900,
            },
        },
    ]

    def run_job(job):
        print(f"  -> [START] {job['name']}...")
        generate_video(**job["kwargs"])
        print(f"  -> [DONE] {job['name']} -> {job['kwargs']['output_path']}")
        return job["name"]

    with ThreadPoolExecutor(max_workers=3) as ex:
        futs = [ex.submit(run_job, j) for j in jobs]
        for f in as_completed(futs):
            print(f"  [COMPLETED] {f.result()}")

    print("=== 3 CLIPS 1080p GENERADOS CON ÉXITO ===")


if __name__ == "__main__":
    main()
