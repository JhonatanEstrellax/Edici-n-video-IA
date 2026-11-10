# -*- coding: utf-8 -*-
r"""
Genera los 3 clips de video profesionales (1080p, 9:16, 10s cada uno = 30s totales)
con `gemini-omni-1.2-flash` para el Spot Publicitario de MascotaMás en DUETO
(Avatar Hombre VIP + Avatar Mujer Veterinaria 360°):
- SIN música de fondo en el prompt IA (voz limpia de estudio en silencio para evitar superposición/"zapateo" con el House de 125 BPM).
- Con `first_frame` y `last_frame` en los 3 clips (`kf1->kf2`, `kf2->kf3`, `kf4->kf5`) para garantizar que el iPhone 16 Pro Max
  muestre SIEMPRE el frente de su pantalla hacia cámara y jamás se gire del lado de las cámaras traseras.
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
SPOT_DIR = BASE_DIR / "assets" / "avatar_veterinario_hombre_vip" / "spot_dueto_hombre_mujer"
ENV_FILE = BASE_DIR / ".env"

if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip().strip("\"'")


def main():
    print(f"=== GENERANDO 3 CLIPS 1080p (9:16) VOZ LIMPIA + PANTALLAS FRONTALES CON {DEFAULT_MODEL} ===")

    assets = {
        "kf1": str(SPOT_DIR / "kf1_dueto_espalda_macbook_escritorio.png"),
        "kf2": str(SPOT_DIR / "kf2_dueto_giro_hablando_camara.png"),
        "kf3": str(SPOT_DIR / "kf3_dueto_operando_turnos_y_hc_macbook.png"),
        "kf4": str(SPOT_DIR / "kf4_dueto_frente_hero_cta_mascotamas.png"),
        "kf5": str(SPOT_DIR / "kf5_dueto_frente_hero_cierre.png"),
    }

    uris = {}
    for k, path_str in assets.items():
        uri, _ = resolve_or_upload_asset(path_str, "image/png")
        uris[k] = uri
        print(f"  -> [Uploaded {k}] {uri}")

    out_clip1 = str(SPOT_DIR / "spot_dueto_clip1_espalda_a_giro_10s.mp4")
    out_clip2 = str(SPOT_DIR / "spot_dueto_clip2_dueto_funciones_macbook_10s.mp4")
    out_clip3 = str(SPOT_DIR / "spot_dueto_clip3_frente_dueto_cta_10s.mp4")

    jobs = [
        {
            "name": "Clip1_Dueto_Espalda_a_Giro_Hablando_10s",
            "kwargs": {
                "prompt": (
                    "Use the first image as the starting frame and the second image as the final frame. "
                    "In a single continuous 9:16 commercial shot in the modern Buenos Aires veterinary clinic reception 'Veterinaria Palermo', "
                    "[0-1.5s] seen from behind over their shoulders ('enfocado desde espaldas'), the strong muscular 38-year-old Argentine male veterinarian on the left "
                    "and the charismatic Argentine female veterinarian with a brunette ponytail on the right (both in matching dark petrol-teal 'VETERINARIA PALERMO' scrubs with Littmann stethoscopes) "
                    "are working together on the open 16-inch Space Black MacBook Pro displaying the MascotaMás dashboard while she holds the iPhone 16 Pro Max with its illuminated front white screen facing the camera (never showing the back camera lenses). "
                    "[1.5-5.3s] The male veterinarian turns his head and upper torso over his right shoulder toward the camera and speaks with clear, natural male Rioplatense Argentine Spanish (es-AR) lip-sync: "
                    "\"¿Seguís manejando tu veterinaria con cuadernos y mensajes sueltos?\" "
                    "[5.3-8.8s] The female veterinarian turns over her left shoulder toward the camera with a bright smile, keeping the iPhone front screen facing the camera, and speaks with clear, natural female Rioplatense Argentine Spanish (es-AR) lip-sync: "
                    "\"Mirá cómo organizamos todo nuestro equipo en MascotaMás.\" "
                    "[8.8-10.0s] Both hold warm, confident smiles looking directly at the camera as shown in the final frame. "
                    "AUDIO: Clean studio dialogue recording in a quiet room, voice only, NO background music, NO drums, NO beats."
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
            "name": "Clip2_Dueto_Funciones_MacBook_e_iPhone_10s",
            "kwargs": {
                "prompt": (
                    "Use the first image as the starting frame and the second image as the final frame. "
                    "In this continuous 9:16 over-the-shoulder commercial shot at the wooden reception desk of 'Veterinaria Palermo', "
                    "[0-4.6s] the strong muscular Argentine male veterinarian on the left gestures beside the open 16-inch Space Black MacBook Pro screen (keeping the laptop screen completely unobstructed) "
                    "and speaks over his shoulder to the camera with clear, natural male Rioplatense Argentine Spanish (es-AR) lip-sync: "
                    "\"Tenés agendas para clínica, peluquería y guardería con seña por Mercado Pago.\" "
                    "[4.6-8.6s] The charismatic Argentine female veterinarian on the right holds the iPhone 16 Pro Max steady with its illuminated front white screen facing directly toward the camera (NEVER turning the phone to show the back cameras), "
                    "speaking to the camera with clear, natural female Rioplatense Argentine Spanish (es-AR) lip-sync: "
                    "\"Historias clínicas en PDF, sala de espera en vivo y recordatorios por WhatsApp.\" "
                    "[8.6-10.0s] Both smile confidently at the camera as shown in the final frame. "
                    "AUDIO: Clean studio dialogue recording in a quiet room, voice only, NO background music, NO drums, NO beats."
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
            "name": "Clip3_Dueto_Frente_CTA_MascotaMas_10s",
            "kwargs": {
                "prompt": (
                    "Use the first image as the starting frame and the second image as the final frame. "
                    "In a continuous 9:16 medium-full front commercial shot in the sunlit 'Veterinaria Palermo' clinic reception, "
                    "the strong muscular Argentine male veterinarian on the left and the charismatic Argentine female veterinarian on the right "
                    "(both wearing matching dark petrol-teal 'VETERINARIA PALERMO' clinical scrubs and Littmann stethoscopes) "
                    "stand side by side behind the wooden counter where the open 16-inch Space Black MacBook Pro faces the viewer. "
                    "CRITICAL: Throughout the entire 10 seconds, the male veterinarian holds the iPhone 16 Pro Max in his left hand with its flat illuminated FRONT white screen facing 100% straight toward the camera lens (NEVER rotating his wrist and NEVER showing the back camera lenses of the iPhone). "
                    "[0.3-3.5s] The female veterinarian gestures warmly toward the viewer with a radiant smile and speaks with clear, energetic female Rioplatense Argentine Spanish (es-AR) lip-sync: "
                    "\"¡Pasate hoy mismo a MascotaMás!\" "
                    "[3.5-8.6s] Keeping the iPhone front screen facing straight at the camera with his left hand, the male veterinarian gestures with his right hand toward the MacBook Pro screen and speaks with clear, confident male Rioplatense Argentine Spanish (es-AR) lip-sync: "
                    "\"Te hacemos la migración en el día y cien por ciento gratis. ¡Escribinos ahora!\" "
                    "[8.6-10.0s] Both hold a warm, charismatic smile looking directly into the camera lens as in the final frame. "
                    "AUDIO: Clean studio dialogue recording in a quiet room, voice only, NO background music, NO drums, NO beats."
                ),
                "model": DEFAULT_MODEL,
                "aspect_ratio": "9:16",
                "duration": "10s",
                "resolution": "1080p",
                "first_frame": uris["kf4"],
                "last_frame": uris["kf5"],
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

    print("=== 3 CLIPS 1080p DUETO (VOZ LIMPIA + PANTALLAS FRONTALES) GENERADOS CON ÉXITO ===")


if __name__ == "__main__":
    main()
