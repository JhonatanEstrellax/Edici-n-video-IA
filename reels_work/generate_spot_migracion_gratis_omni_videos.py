# -*- coding: utf-8 -*-
r"""
Genera los 3 clips de video profesionales (1080p, 9:16, 10s cada uno = 30s totales)
con `gemini-omni-1.2-flash` para el Spot Publicitario de MascotaMás:
"Migración Gratis en el Día + Características Más Importantes":
- Clip 1 (10s, 1080p): Enfocado desde espaldas usando la MacBook Pro 16" (mostrando el Escritorio Principal migrado)
  y el iPhone 16 Pro Max, girando naturalmente sobre su hombro hacia cámara con lip-sync argentino (es-AR).
- Clip 2 (10s, 1080p): Enfocado desde espaldas mostrando las características clave en la MacBook Pro 16"
  (4 modalidades de calendarios, seña Mercado Pago, historias clínicas PDF, sala de espera y recordatorios WhatsApp)
  y el celular, hablando a cámara con lip-sync argentino (es-AR).
- Clip 3 (10s, 1080p): Plano medio-frente VIP junto a la MacBook Pro 16" abierta y el iPhone en mano,
  dando el cierre de Migración Gratis en el Día y llamada a la acción (CTA) con lip-sync argentino (es-AR).
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
SPOT_DIR = BASE_DIR / "assets" / "avatar_veterinario_hombre_vip" / "spot_migracion_gratis"
AVATAR_DIR = BASE_DIR / "assets" / "avatar_veterinario_hombre_vip"
MANUAL_DIR = BASE_DIR / "assets" / "manual_vete_y_marca"
ENV_FILE = BASE_DIR / ".env"

if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip().strip("\"'")


def main():
    print(f"=== GENERANDO 3 CLIPS 1080p (9:16) CON {DEFAULT_MODEL} PARA SPOT MASCOTAMÁS MIGRACIÓN GRATIS EN EL DÍA ===")

    assets = {
        "kf1": str(SPOT_DIR / "kf1_espalda_migracion_escritorio_macbook.png"),
        "kf2": str(SPOT_DIR / "kf2_espalda_giro_migracion_gratis_hablando.png"),
        "kf3": str(SPOT_DIR / "kf3_espalda_caracteristicas_4_calendarios_y_hc.png"),
        "kf4": str(SPOT_DIR / "kf4_frente_vip_cta_migracion_gratis.png"),
        "hero": str(AVATAR_DIR / "avatar_vete_hombre_vip_hero_brazos_cruzados.png"),
        "ui_escritorio": str(
            MANUAL_DIR
            / "00_Secuencias_Paso_a_Paso__01_Recorrido_Completo_App_10_Pantallas__01_Paso_1_Escritorio_y_Resumen_Operativo_del_Dia__04_Raw_Desktop.png"
        ),
        "ui_calendarios": str(
            MANUAL_DIR
            / "00_Secuencias_Paso_a_Paso__02_Flujo_Calendarios_y_Sena_MercadoPago__02_Paso_2_Modal_Crear_Calendario_Selector_de_4_Modalidades__04_Raw_Desktop.png"
        ),
    }

    uris = {}
    for k, path_str in assets.items():
        uri, _ = resolve_or_upload_asset(path_str, "image/png")
        uris[k] = uri
        print(f"  -> [Uploaded {k}] {uri}")

    out_clip1 = str(SPOT_DIR / "spot_migracion_clip1_espalda_a_giro_10s.mp4")
    out_clip2 = str(SPOT_DIR / "spot_migracion_clip2_espalda_caracteristicas_10s.mp4")
    out_clip3 = str(SPOT_DIR / "spot_migracion_clip3_frente_vip_cta_10s.mp4")

    jobs = [
        {
            "name": "Clip1_Espalda_Migracion_Escritorio_Giro_Hablando_10s",
            "kwargs": {
                "prompt": (
                    "Use the first image as the starting frame and the second image as the final frame. "
                    "In a single continuous 9:16 commercial shot in a modern luxury Buenos Aires veterinary center & pet clinic reception, "
                    "[0-2.0s] seen from behind over his shoulder ('enfocado desde espaldas'), the strong muscular Argentine VIP man "
                    "dressed in his tailored dark-navy executive clinical polo shirt and luxury steel watch is typing on his 16-inch MacBook Pro "
                    "(which clearly displays the 'MascotaMás - Escritorio Principal · Turnos del Día · Vacunas · Recordatorios' web system on screen) while holding his iPhone 16 Pro Max. "
                    "[2.0-9.0s] He smoothly turns his head and upper torso over his right shoulder to look directly at the camera with a charismatic smile, "
                    "points naturally toward the MacBook Pro screen, and speaks with clear, natural male Rioplatense Argentine Spanish (es-AR) lip-sync: "
                    "\"¿Querés digitalizar tu veterinaria hoy mismo sin perder ni un dato? En MascotaMás te hacemos la migración gratis en el día.\" "
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
            "name": "Clip2_Espalda_Caracteristicas_Claves_MacBook_10s",
            "kwargs": {
                "prompt": (
                    "Use the first image as the starting frame and the second image as the final frame. "
                    "In this exact same continuous 9:16 over-the-shoulder commercial shot from behind ('enfocado desde espaldas'), "
                    "[0-8.6s] the strong muscular Argentine VIP man in his tailored dark-navy executive clinical polo shirt and luxury steel watch "
                    "speaks over his right shoulder directly to the camera with clear, natural male Rioplatense Argentine Spanish (es-AR) lip-sync "
                    "while gesturing to the 16-inch MacBook Pro screen and clicking on the keyboard to showcase the 4 calendar modalities, Mercado Pago deposit, digital clinical history PDF, and checking his iPhone 16 Pro Max: "
                    "\"Tenés cuatro tipos de agenda con seña por Mercado Pago, historias clínicas en PDF, sala de espera en vivo y recordatorios por WhatsApp.\" "
                    "[8.6-10.0s] He finishes clicking on the MacBook Pro keyboard while looking confidently over his shoulder at the camera as shown in the final frame. "
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
            "name": "Clip3_Frente_VIP_CTA_Migracion_Gratis_10s",
            "kwargs": {
                "prompt": (
                    "Use the first image as the starting frame. "
                    "In a continuous 9:16 medium-full commercial shot in the modern Buenos Aires veterinary clinic reception, "
                    "the strong muscular Argentine VIP man in his tailored dark-navy executive clinical polo shirt, dark trousers, and luxury steel watch "
                    "leans confidently beside the wooden counter next to the open 16-inch MacBook Pro (displaying 'MascotaMás - Historia Clínica Digital' on screen) "
                    "while holding his iPhone 16 Pro Max in his left hand. "
                    "[0.4-8.8s] Looking directly at the camera with natural, charismatic body movement and expressive hand gestures, "
                    "he speaks with clear, energetic male Rioplatense Argentine Spanish (es-AR) lip-sync: "
                    "\"¡Pasate hoy a MascotaMás! Nosotros migramos tus pacientes, clientes y turnos en el día y cien por ciento gratis. ¡Escribinos ahora!\" "
                    "[8.8-10.0s] He finishes with a warm, self-assured Argentine smile looking directly into the lens. Upbeat house music softly in background."
                ),
                "model": DEFAULT_MODEL,
                "aspect_ratio": "9:16",
                "duration": "10s",
                "resolution": "1080p",
                "first_frame": uris["kf4"],
                "image_path": [uris["hero"], uris["ui_escritorio"]],
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
