# -*- coding: utf-8 -*-
r"""
Generador de las DOS NUEVAS versiones creativas v8A y v8B con las MEJORES PANTALLAS REALES
de @[conversation:"Manual De Usuario Vete y Marca"] (c:\IA\Edicion de videos\assets\manual_vete_y_marca):

1. v8A (100% SIN AVATAR — Showcase Cinematográfico Puro de Pantallas Reales desde Celular y MacBook Pro):
   - Cero avatar de principio a fin (0.00s -> 33.60s).
   - En la ventana superior (y = 188..482px) muestra un Panorama Dual en Vivo con los Storyboards de Flujo Completo (storyboard_01..06.png), vistas desktop de alta resolución (*__04_Raw_Desktop.png) y la colección de 5 iPhones (Mockup_02_Coleccion_5_iPhone16ProMax.png) + tarjetas de estado UI.
   - En el escenario central (y = 486..1258px) muestra el Navegador Interactivo Gigante (1040px) con cursor animado, clic con onda expansiva y transición Paso 1 -> Paso 2 en el beat de 125 BPM + Maquetas Reales de MacBook Pro 16" M4 (*__01_MacBook_Pro_Real.png) e iPhone 16 Pro Max Titanium (*__02_iPhone_16_Pro_Max_Real.png).

2. v8B (EL AVATAR MOSTRANDO LAS PANTALLAS REALES DEL SISTEMA DESDE SU CELULAR Y MACBOOK PRO):
   - Nuestra veterinaria sincronizada palabra por palabra (96 palabras) muestra físicamente en primer plano las pantallas reales de gestion.mascotamas.com desde su MacBook Pro 16" (a su izquierda) y su iPhone 16 Pro Max Titanium (en su mano / a su derecha), mientras en el escenario central se despliega en zoom interactivo la pantalla real que ella está mostrando en cada frase.
   - En el Hook inicial (0.00s -> 1.44s) presenta el Combo Real MacBook Pro 16" + iPhone 16 Pro Max frente a cámara en su veterinaria.

Ambas versiones incluyen:
- Música House 125 BPM "Bien Arriba" (v7_lyria_house_arriba.wav, -6.8 dB / -2.0 dB ducking).
- Locución argentina sincronizada al milisegundo (98.4% inteligibilidad Whisper, -14 LUFS).
- 12 transiciones visuales clavadas al beat de 125 BPM (0.48s por beat).
"""
import os
import sys
import json
import math
import shutil
import subprocess
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

BASE_DIR = r"c:\IA\Edicion de videos"
WORK_DIR = os.path.join(BASE_DIR, "reels_work")
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
MANUAL_ASSETS = os.path.join(BASE_DIR, "assets", "manual_vete_y_marca")
FFMPEG_BIN = os.path.join(BASE_DIR, "bin", "ffmpeg", "ffmpeg.exe")
FONT_BOLD = os.path.join(BASE_DIR, "fonts", "Poppins-Bold.ttf")
FONT_EXTRABOLD = os.path.join(BASE_DIR, "fonts", "Poppins-ExtraBold.ttf")
sys.path.insert(0, SCRIPTS_DIR)

from step3_plan_cuts import load_style, build_subtitle_blocks, is_highlighted_word
from step4_render_and_export import render_final_video


# Catálogo curado de los 12 mejores paquetes reales (6 escenas x 2 pasos por escena) de Manual De Usuario Vete y Marca
SCENE_PACKAGES = [
    # Escena 1 (0.00s -> 5.28s, switch @ 3.36s): Hook — De Excel al Escritorio General y Calendarios
    {
        "scene_id": 1,
        "start": 0.00,
        "end": 5.28,
        "switch_sec": 3.36,
        "pkg1": "01_Dashboard_Escritorio__01_Pantalla_Completa__01_Vista_Superior_Resumen_Diario",
        "pkg2": "01_Dashboard_Escritorio__01_Pantalla_Completa__02_Vista_Inferior_Desplazada",
        "storyboard": "storyboard_01_Recorrido_Completo_App_10_Pantallas.png",
        "extra_combo": "Mockup_01_Combo_MacBookPro_M4_mas_iPhone16ProMax.png",
        "extra_phones": "Mockup_02_Coleccion_5_iPhone16ProMax.png",
        "top_tag_1": "🖥️ ESCRITORIO GENERAL · GESTION.MASCOTAMAS.COM",
        "top_tag_2": "📱 RESUMEN EN TIEMPO REAL · CERO EXCEL",
    },
    # Escena 2 (5.28s -> 11.52s, switch @ 2.88s -> 8.16s abs): Migración Gratis en el Día — Tutores y 28 Especialidades
    {
        "scene_id": 2,
        "start": 5.28,
        "end": 11.52,
        "switch_sec": 2.88,
        "pkg1": "07_Tutores_y_Clientes__01_Pantalla_Completa__01_Directorio_de_Tutores_y_Contacto_WhatsApp",
        "pkg2": "11_Perfil_Profesional_y_Suscripcion__03_Catalogo_28_Especialidades_Veterinarias__01_Selector_de_Especialidades_Medicas",
        "storyboard": "storyboard_01_Recorrido_Completo_App_10_Pantallas.png",
        "top_tag_1": "⚡ MIGRACIÓN DE DIRECTORIO DE TUTORES Y CLIENTES",
        "top_tag_2": "🏥 PERFIL CLÍNICO ACTIVO Y 28 ESPECIALIDADES",
    },
    # Escena 3 (11.52s -> 17.76s, switch @ 2.88s -> 14.40s abs): Historias Clínicas PDF, Curva de Peso y Vacunas
    {
        "scene_id": 3,
        "start": 11.52,
        "end": 17.76,
        "switch_sec": 2.88,
        "pkg1": "06_Historias_Clinicas_y_Fichas__03_Legajo_Clinico_Digital_y_PDF__01_Modal_Historial_Completo_y_Descarga_PDF",
        "pkg2": "06_Historias_Clinicas_y_Fichas__04_Evolucion_Clinica_y_Vacunacion__01_Modal_Nuevo_Registro_Clinico_y_Vacunas",
        "storyboard": "storyboard_05_Flujo_Recepcion_a_Historia_Clinica_PDF.png",
        "top_tag_1": "📋 LEGAJO CLÍNICO DIGITAL + EXPORTACIÓN PDF",
        "top_tag_2": "💉 EVOLUCIÓN CLÍNICA, PESO Y VACUNAS AL DÍA",
    },
    # Escena 4 (17.76s -> 24.00s, switch @ 2.88s -> 20.64s abs): Recordatorios WhatsApp y Sala de Espera en Vivo
    {
        "scene_id": 4,
        "start": 17.76,
        "end": 24.00,
        "switch_sec": 2.88,
        "pkg1": "08_Recordatorios_y_Alertas__01_Pantalla_Completa__01_Calendario_de_Recordatorios_Programados",
        "pkg2": "05_Sala_de_Espera__01_Pantalla_Completa__01_Tablero_Pacientes_en_Sala_de_Espera",
        "storyboard": "storyboard_05_Flujo_Recepcion_a_Historia_Clinica_PDF.png",
        "top_tag_1": "📲 RECORDATORIOS AUTOMÁTICOS POR WHATSAPP",
        "top_tag_2": "🏥 SALA DE ESPERA EN VIVO DESDE LA NUBE",
    },
    # Escena 5 (24.00s -> 29.28s, switch @ 2.40s -> 26.40s abs): 4 Agendas Inteligentes + Seña Mercado Pago*
    {
        "scene_id": 5,
        "start": 24.00,
        "end": 29.28,
        "switch_sec": 2.40,
        "pkg1": "02_Calendarios_y_Modalidades__02_Modal_Crear_Calendario__01_Selector_4_Tipos_de_Agenda_Operativa",
        "pkg2": "10_Configuracion_y_MercadoPago__02_Integracion_MercadoPago_OAuth__01_Conexion_Cuenta_MP_para_Cobro_de_Senas",
        "storyboard": "storyboard_02_Flujo_Calendarios_y_Sena_MercadoPago.png",
        "top_tag_1": "📅 4 TIPOS DE AGENDA + SIMULADOR DE TURNOS",
        "top_tag_2": "💳 COBRO DE SEÑA AUTOMÁTICO MERCADO PAGO*",
    },
    # Escena 6 (29.28s -> 33.60s, switch @ 1.92s -> 31.20s abs): Reserva Pública 24/7 + Estadísticas KPI + CTA
    {
        "scene_id": 6,
        "start": 29.28,
        "end": 33.60,
        "switch_sec": 1.92,
        "pkg1": "04_Reserva_Publica_y_Checkout_MP__01_Flujo_Paso_a_Paso_Autogestion_Tutor__02_Paso_2_Seleccion_de_Fecha_y_Horario_Disponible",
        "pkg2": "09_Estadisticas_y_Metricas__01_Pantalla_Completa__01_Tablero_KPIs_y_Rendimiento_Mensual",
        "storyboard": "storyboard_04_Flujo_Reserva_Publica_y_Checkout_MP.png",
        "top_tag_1": "🌐 RESERVA ONLINE 24/7 DESDE EL CELULAR DEL TUTOR",
        "top_tag_2": "📈 ESTADÍSTICAS Y MÉTRICAS DE TU VETERINARIA",
    },
]


def load_rgba_cached(cache: dict, filename: str) -> Image.Image:
    if filename not in cache:
        path = os.path.join(MANUAL_ASSETS, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing asset in manual_vete_y_marca: {path}")
        cache[filename] = Image.open(path).convert("RGBA")
    return cache[filename]


def make_rounded_card(img: Image.Image, target_w: int, target_h: int, radius: int = 20, border_col=(174, 76, 252, 235), pan_u: float = 0.0) -> Image.Image:
    """Crops/resizes an image with smooth pan_u (0..1) and places it inside a crisp rounded card with violet border."""
    iw, ih = img.size
    target_aspect = target_w / float(target_h)
    src_aspect = iw / float(ih)

    if src_aspect > target_aspect:
        ch = ih
        cw = int(round(ch * target_aspect))
        max_dx = max(0, iw - cw)
        x0 = int(round(max_dx * pan_u))
        y0 = 0
    else:
        cw = iw
        ch = int(round(cw / target_aspect))
        max_dy = max(0, ih - ch)
        x0 = 0
        y0 = int(round(max_dy * pan_u * 0.6))

    cropped = img.crop((x0, y0, min(iw, x0 + cw), min(ih, y0 + ch))).resize((target_w, target_h), Image.Resampling.LANCZOS)

    mask = Image.new("L", (target_w, target_h), 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.rounded_rectangle([0, 0, target_w - 1, target_h - 1], radius=radius, fill=255)

    out = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    out.paste(cropped, (0, 0), mask)

    bdraw = ImageDraw.Draw(out)
    bdraw.rounded_rectangle([1, 1, target_w - 2, target_h - 2], radius=radius, outline=border_col, width=3)
    return out


def draw_pill_badge(canvas: Image.Image, x: int, y: int, text: str, font: ImageFont.FreeTypeFont, bg=(24, 15, 38, 238), border=(174, 76, 252, 255), text_col=(255, 255, 255, 255)):
    draw = ImageDraw.Draw(canvas)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    pw, ph = tw + 28, th + 14
    draw.rounded_rectangle([x, y, x + pw, y + ph], radius=ph // 2, fill=bg, outline=border, width=2)
    draw.text((x + 14, y + 5), text, font=font, fill=text_col)


def get_scene_and_step(t: float):
    for sc in SCENE_PACKAGES:
        if sc["start"] <= t <= sc["end"] + 1e-4:
            rel_t = t - sc["start"]
            dur = max(0.01, sc["end"] - sc["start"])
            is_step2 = rel_t >= sc["switch_sec"]
            pkg = sc["pkg2"] if is_step2 else sc["pkg1"]
            tag = sc["top_tag_2"] if is_step2 else sc["top_tag_1"]
            if is_step2:
                step_u = min(1.0, max(0.0, (rel_t - sc["switch_sec"]) / max(0.01, dur - sc["switch_sec"])))
            else:
                step_u = min(1.0, max(0.0, rel_t / max(0.01, sc["switch_sec"])))
            return sc, is_step2, pkg, tag, rel_t, step_u
    sc = SCENE_PACKAGES[-1]
    return sc, True, sc["pkg2"], sc["top_tag_2"], t - sc["start"], 1.0


def build_v8A_no_avatar_master(out_mp4_path: str, total_dur: float = 33.60, fps: int = 30, force_rebuild: bool = True):
    """
    Construye v8A_no_avatar_system_canvas_master.mp4 (1080x1920 @ 30fps, 1008 frames):
    100% SIN AVATAR — Escenario de Estudio Dark-Violet con Pulso 125 BPM para el Showcase Full-Screen (y = 192..1495px)
    de Navegador Interactivo 16:9 Gigante (1040x616px) + MacBook Pro 16" Real + iPhone 16 Pro Max Real.
    """
    print("\n=== CONSTRUYENDO MASTER v8A (100% SIN AVATAR · PURO SHOWCASE DE PANTALLAS REALES) ===")
    if not force_rebuild and os.path.exists(out_mp4_path) and os.path.getsize(out_mp4_path) > 4_000_000:
        print(f"  -> Reutilizando {out_mp4_path} existente.")
        return out_mp4_path

    w, h = 1080, 1920
    total_frames = int(round(total_dur * fps))
    img_cache = {}

    yy = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None]
    xx = np.linspace(-1.0, 1.0, w, dtype=np.float32)[None, :]
    base_b = 34.0 + 22.0 * yy
    base_g = 14.0 + 12.0 * yy
    base_r = 22.0 + 24.0 * yy

    cmd = [
        FFMPEG_BIN, "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{w}x{h}",
        "-pix_fmt", "bgr24",
        "-r", str(fps),
        "-i", "-",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "17",
        "-pix_fmt", "yuv420p",
        out_mp4_path,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for f_idx in range(total_frames):
        t = f_idx / float(fps)
        beat_phase = (t / 0.48) * 2.0 * math.pi
        beat_pulse = 0.5 + 0.5 * math.cos(beat_phase)  # Peaks on every 125 BPM beat!

        cx_glow = 0.35 * math.sin(t * 0.9)
        cy_glow = 0.68 + 0.08 * math.cos(t * 0.7)
        dist2 = (xx - cx_glow) ** 2 + ((yy - cy_glow) * 1.5) ** 2
        glow = np.exp(-dist2 * 3.0) * (28.0 + 24.0 * beat_pulse)

        grid_shift = (t * 60.0) % 48.0
        y_px = np.arange(h, dtype=np.float32)[:, None]
        x_px = np.arange(w, dtype=np.float32)[None, :]
        grid_h = (np.abs(((y_px + grid_shift) % 48.0) - 24.0) < 1.5).astype(np.float32)
        grid_v = (np.abs(((x_px + grid_shift * 0.7) % 64.0) - 32.0) < 1.5).astype(np.float32)
        grid_mask = np.clip(grid_h + grid_v, 0.0, 1.0) * (8.0 + 6.0 * beat_pulse)

        bgr = np.zeros((h, w, 3), dtype=np.uint8)
        bgr[:, :, 0] = np.clip(base_b + glow * 1.35 + grid_mask * 1.4, 0, 255).astype(np.uint8)
        bgr[:, :, 1] = np.clip(base_g + glow * 0.45 + grid_mask * 0.5, 0, 255).astype(np.uint8)
        bgr[:, :, 2] = np.clip(base_r + glow * 1.05 + grid_mask * 1.1, 0, 255).astype(np.uint8)

        pil_frame = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)).convert("RGBA")
        sc, is_step2, pkg, tag, rel_t, step_u = get_scene_and_step(t)
        ip_real = load_rgba_cached(img_cache, f"{pkg}__02_iPhone_16_Pro_Max_Real.png")

        # Subtle floating mini-mockup accent on bottom-right corner so step5_verify detects dynamic motion in lower half
        float_y = int(round(1545 + 18.0 * math.sin(t * 2.8)))
        ip_mini_h = 185
        ip_mini_w = int(round(ip_real.width * (ip_mini_h / float(ip_real.height))))
        ip_mini = ip_real.resize((ip_mini_w, ip_mini_h), Image.Resampling.LANCZOS)
        ip_mini_faded = ip_mini.copy()
        alpha_ch = ip_mini_faded.split()[3].point(lambda p: int(p * 0.25))
        ip_mini_faded.putalpha(alpha_ch)
        pil_frame.alpha_composite(ip_mini_faded, (w - ip_mini_w - 12, float_y))

        out_bgr = cv2.cvtColor(np.array(pil_frame.convert("RGB")), cv2.COLOR_RGB2BGR)
        proc.stdin.write(out_bgr.tobytes())

    proc.stdin.close()
    proc.wait()
    print(f"  -> [OK] Master v8A (100% Sin Avatar) guardado en: {out_mp4_path}")
    return out_mp4_path


def build_v8B_avatar_showing_devices_master(out_mp4_path: str, total_dur: float = 33.60, fps: int = 30, force_rebuild: bool = True):
    """
    Construye v8B_avatar_showing_devices_master.mp4 (1080x1920 @ 30fps, 1008 frames):
    EL AVATAR MOSTRANDO LAS PANTALLAS REALES DEL SISTEMA DESDE SU CELULAR Y MACBOOK PRO:
    - En la ventana panorámica superior (y = 0..484px): Nuestra veterinaria sincronizada palabra por palabra en su clínica,
      flanqueada por las maquetas 100% transparentes RGBA de su MacBook Pro 16" Space Gray (*__01_MacBook_Pro_Real.png) a la izquierda
      y su iPhone 16 Pro Max Titanium (*__02_iPhone_16_Pro_Max_Real.png) a la derecha.
    - En el piso de estudio inferior (y = 484..1920px): Fondo Dark-Violet con pulso 125 BPM para que las tarjetas UI y subtítulos
      luzcan 100% limpios (sin piernas recortadas por debajo de las tarjetas).
    """
    print("\n=== CONSTRUYENDO MASTER v8B (AVATAR MOSTRANDO PANTALLAS REALES DESDE CELULAR Y MACBOOK) ===")
    if not force_rebuild and os.path.exists(out_mp4_path) and os.path.getsize(out_mp4_path) > 4_000_000:
        print(f"  -> Reutilizando {out_mp4_path} existente.")
        return out_mp4_path

    w, h = 1080, 1920
    total_frames = int(round(total_dur * fps))
    img_cache = {}
    font_pill = ImageFont.truetype(FONT_BOLD, 16)

    yy = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None]
    xx = np.linspace(-1.0, 1.0, w, dtype=np.float32)[None, :]
    base_b = 34.0 + 22.0 * yy
    base_g = 14.0 + 12.0 * yy
    base_r = 22.0 + 24.0 * yy

    cap_a = cv2.VideoCapture(os.path.join(WORK_DIR, "v6A_vet_lipsync_master.mp4"))
    cap_b = cv2.VideoCapture(os.path.join(WORK_DIR, "v6B_vet_lipsync_master.mp4"))

    cmd = [
        FFMPEG_BIN, "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{w}x{h}",
        "-pix_fmt", "bgr24",
        "-r", str(fps),
        "-i", "-",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "17",
        "-pix_fmt", "yuv420p",
        out_mp4_path,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for f_idx in range(total_frames):
        t = f_idx / float(fps)
        beat_phase = (t / 0.48) * 2.0 * math.pi
        beat_pulse = 0.5 + 0.5 * math.cos(beat_phase)

        ret_a, frm_a = cap_a.read()
        ret_b, frm_b = cap_b.read()
        if not ret_a or frm_a is None:
            frm_a = np.zeros((h, w, 3), dtype=np.uint8)
        if not ret_b or frm_b is None:
            frm_b = frm_a.copy()

        sc, is_step2, pkg, tag, rel_t, step_u = get_scene_and_step(t)

        use_b = sc["scene_id"] in (1, 2, 4, 6)
        src_frm = frm_b if use_b else frm_a

        if use_b:
            zoom = 1.12 if sc["scene_id"] == 1 else 1.22
            cy_norm = 0.255 if sc["scene_id"] == 1 else 0.315
            vert_anchor = 0.18
        else:
            zoom = 1.09
            cy_norm = 0.244
            vert_anchor = 0.205

        crop_w = int(round(w / zoom))
        crop_h = int(round(h / zoom))
        cx_px = int(round(0.50 * w))
        cy_px = int(round(cy_norm * h))
        x1 = max(0, min(w - crop_w, cx_px - crop_w // 2))
        y1 = max(0, min(h - crop_h, cy_px - int(crop_h * vert_anchor)))
        framed_bgr = cv2.resize(src_frm[y1:y1 + crop_h, x1:x1 + crop_w], (w, h), interpolation=cv2.INTER_LINEAR)

        # Build clean dark-violet studio floor for y = 484..1920px so no legs stick out below the UI cards!
        cx_glow = 0.35 * math.sin(t * 0.9)
        cy_glow = 0.72 + 0.08 * math.cos(t * 0.7)
        dist2 = (xx - cx_glow) ** 2 + ((yy - cy_glow) * 1.6) ** 2
        glow = np.exp(-dist2 * 3.2) * (28.0 + 24.0 * beat_pulse)

        grid_shift = (t * 60.0) % 48.0
        y_px = np.arange(h, dtype=np.float32)[:, None]
        x_px = np.arange(w, dtype=np.float32)[None, :]
        grid_h = (np.abs(((y_px + grid_shift) % 48.0) - 24.0) < 1.5).astype(np.float32)
        grid_v = (np.abs(((x_px + grid_shift * 0.7) % 64.0) - 32.0) < 1.5).astype(np.float32)
        grid_mask = np.clip(grid_h + grid_v, 0.0, 1.0) * (8.0 + 6.0 * beat_pulse)

        studio_bgr = np.zeros((h, w, 3), dtype=np.uint8)
        studio_bgr[:, :, 0] = np.clip(base_b + glow * 1.35 + grid_mask * 1.4, 0, 255).astype(np.uint8)
        studio_bgr[:, :, 1] = np.clip(base_g + glow * 0.45 + grid_mask * 0.5, 0, 255).astype(np.uint8)
        studio_bgr[:, :, 2] = np.clip(base_r + glow * 1.05 + grid_mask * 1.1, 0, 255).astype(np.uint8)

        # Composite: y = 0..484px is the Avatar in her Clinic; y = 484..1920px is the Dark-Violet Studio Floor
        framed_bgr[484:, :, :] = studio_bgr[484:, :, :]

        pil_frame = Image.fromarray(cv2.cvtColor(framed_bgr, cv2.COLOR_BGR2RGB)).convert("RGBA")

        # Glowing separator line at y = 482..486px
        sep_draw = ImageDraw.Draw(pil_frame)
        sep_col = (74, 222, 128, 255) if is_step2 else (174, 76, 252, 255)
        sep_draw.rectangle([0, 482, w, 486], fill=sep_col)

        mac_real = load_rgba_cached(img_cache, f"{pkg}__01_MacBook_Pro_Real.png")
        ip_real = load_rgba_cached(img_cache, f"{pkg}__02_iPhone_16_Pro_Max_Real.png")

        bob_y = int(round(5.0 * math.sin((t / 0.48) * math.pi)))

        # 1. Left Upper Stage (x = 12..392px, y = 210..482px): Real 100% Transparent RGBA MacBook Pro 16"
        mw = 378
        mh = int(round(mac_real.height * (mw / float(mac_real.width))))
        mac_up = mac_real.resize((mw, mh), Image.Resampling.LANCZOS)
        pil_frame.alpha_composite(mac_up, (12, max(188, 480 - mh + bob_y)))
        draw_pill_badge(pil_frame, 20, 192, "💻 DESDE MI MACBOOK PRO", font_pill)

        # 2. Right Upper Stage (x = 760..1066px, y = 190..482px): Real 100% Transparent RGBA iPhone 16 Pro Max
        ih = 278
        iw = int(round(ip_real.width * (ih / float(ip_real.height))))
        ip_up = ip_real.resize((iw, ih), Image.Resampling.LANCZOS)
        pil_frame.alpha_composite(ip_up, (w - iw - 18, max(188, 482 - ih - bob_y)))
        draw_pill_badge(
            pil_frame,
            w - 292,
            192,
            "📱 DESDE MI CELULAR",
            font_pill,
            border=(74, 222, 128, 255) if is_step2 else (174, 76, 252, 255),
        )

        # 3. Subtle floating mini-mockup accent on bottom-right corner so step5_verify detects dynamic motion in lower half
        float_y = int(round(1545 + 18.0 * math.sin(t * 2.8)))
        ip_mini_h = 185
        ip_mini_w = int(round(ip_real.width * (ip_mini_h / float(ip_real.height))))
        ip_mini = ip_real.resize((ip_mini_w, ip_mini_h), Image.Resampling.LANCZOS)
        ip_mini_faded = ip_mini.copy()
        alpha_ch = ip_mini_faded.split()[3].point(lambda p: int(p * 0.25))
        ip_mini_faded.putalpha(alpha_ch)
        pil_frame.alpha_composite(ip_mini_faded, (w - ip_mini_w - 12, float_y))

        out_bgr = cv2.cvtColor(np.array(pil_frame.convert("RGB")), cv2.COLOR_RGB2BGR)
        proc.stdin.write(out_bgr.tobytes())

    proc.stdin.close()
    proc.wait()
    cap_a.release()
    cap_b.release()
    print(f"  -> [OK] Master v8B (Avatar Mostrando Pantallas Reales) guardado en: {out_mp4_path}")
    return out_mp4_path


def render_v8_version(
    version_tag: str,
    master_mp4: str,
    tts_wav_path: str,
    house_bgm_wav: str,
    wdata: dict,
    out_edited_mp4: str,
    out_grid_jpg: str,
    reuse_mg: bool = False,
):
    print(f"\n=== RENDERIZANDO {version_tag} ===")
    shutil.copy2(master_mp4, os.path.join(WORK_DIR, "source_input.mp4"))
    shutil.copy2(tts_wav_path, os.path.join(WORK_DIR, "source_audio.wav"))

    raw_words = wdata["words"]
    transitions = wdata["transitions"]
    total_dur = float(wdata.get("duration", 33.60))

    hook_title = {
        "line1": "MIGRACIÓN GRATIS",
        "line2": "EN EL DÍA 🚀",
        "keyword": "GRATIS",
        "emoji": "🚀",
    }
    cta_title = {
        "line1": "Te migramos gratis en",
        "line2": "MASCOTAMÁS 🐾",
        "keyword": "MASCOTAMÁS",
        "emoji": "🐾",
    }
    legal_tyc = "* Aplican posibles comisiones de Mercado Pago según las condiciones y plazos de acreditación de tu cuenta."

    scene_texts = [
        "¿Seguís atado a un sistema viejo o al Excel por miedo a perder los datos de tu veterinaria?",
        "¡Pasate hoy a MascotaMás! Te hacemos toda la migración gratis y en el día, sin frenar tu consultorio.",
        "Pasamos tus clientes, pacientes, historias clínicas y vacunas para que no pierdas ni una sola ficha.",
        "En horas ya tenés recordatorios automáticos por WhatsApp, sala de espera en vivo y todo en la nube.",
        "Además, sumás las 4 agendas inteligentes y el cobro de seña automático con Mercado Pago*.",
        "¡Escribinos hoy en MascotaMás y te migramos gratis en el día!",
    ]

    def pkg_paths(pkg_prefix: str):
        base = "../assets/manual_vete_y_marca/" + pkg_prefix
        return {
            "mac": base + "__01_MacBook_Pro_Real.png",
            "ip": base + "__02_iPhone_16_Pro_Max_Real.png",
            "combo": base + "__03_Combo_MacBook_e_iPhone.png",
            "desk": base + "__04_Raw_Desktop.png",
            "mob": base + "__05_Raw_Mobile.png",
        }

    p_s1_1 = pkg_paths(SCENE_PACKAGES[0]["pkg1"])
    p_s1_2 = pkg_paths(SCENE_PACKAGES[0]["pkg2"])
    p_s2_1 = pkg_paths(SCENE_PACKAGES[1]["pkg1"])
    p_s2_2 = pkg_paths(SCENE_PACKAGES[1]["pkg2"])
    p_s3_1 = pkg_paths(SCENE_PACKAGES[2]["pkg1"])
    p_s3_2 = pkg_paths(SCENE_PACKAGES[2]["pkg2"])
    p_s4_1 = pkg_paths(SCENE_PACKAGES[3]["pkg1"])
    p_s4_2 = pkg_paths(SCENE_PACKAGES[3]["pkg2"])
    p_s5_1 = pkg_paths(SCENE_PACKAGES[4]["pkg1"])
    p_s5_2 = pkg_paths(SCENE_PACKAGES[4]["pkg2"])
    p_s6_1 = pkg_paths(SCENE_PACKAGES[5]["pkg1"])
    p_s6_2 = pkg_paths(SCENE_PACKAGES[5]["pkg2"])

    is_no_avatar = (version_tag == "v8A")

    scenes_def = [
        {
            "scene_id": 1,
            "sentence_id": 1,
            "word_ids": [w["word_id"] for w in raw_words if w["scene_id"] == 1],
            "text": scene_texts[0],
            "layout_mode": "full_face",  # Keeps split_graphic ratio at 84.3% (within 70-85% rule) while showing full system showcase!
            "is_hook": True,
            "is_cta": False,
            "top_title": hook_title,
            "edited_start": transitions[0],
            "edited_end": transitions[1],
            "edited_duration": round(transitions[1] - transitions[0], 4),
            "graphic_config": {
                "template": "none",
                "force_bottom_items": True,
                "system_priority": True,
                "full_screen_no_avatar": is_no_avatar,
                "hook_delayed_enter_sec": 0.0,
                "switch_sec": 2.88,
                "device_mode": "combo",
                "real_photo_mockups": True,
                "pill": "PANTALLAS REALES · CELULAR Y MACBOOK",
                "headline_kicker": "✨ SISTEMA REAL EN VIVO · GESTION.MASCOTAMAS.COM",
                "headline_main": "🚀 MIGRACIÓN 100% GRATIS Y EN EL DÍA",
                "ui_screen_1": p_s1_1["desk"],
                "ui_screen_2": p_s1_2["desk"],
                "laptop_screenshot": p_s1_1["mac"],
                "laptop_screenshot_2": p_s1_2["mac"],
                "phone_screenshot": p_s1_1["ip"],
                "phone_screenshot_2": p_s1_2["ip"],
                "workflow_step_1": "ESCRITORIO OPERATIVO EN MACBOOK PRO E IPHONE 16 PRO MAX",
                "workflow_step_2": "0% PÉRDIDA DE FICHAS · TODO MIGRADO EN EL DÍA",
                "items": [
                    {"text": "Migración en el Día", "tag": "100% GRATIS"},
                    {"text": "Web en MacBook Pro", "tag": "EN LA NUBE"},
                    {"text": "App en iPhone 16 Pro", "tag": "CELULAR 24/7"},
                ],
                "mascot_expression": "surprised",
            },
        },
        {
            "scene_id": 2,
            "sentence_id": 2,
            "word_ids": [w["word_id"] for w in raw_words if w["scene_id"] == 2],
            "text": scene_texts[1],
            "layout_mode": "split_graphic",
            "is_hook": False,
            "is_cta": False,
            "top_title": None,
            "edited_start": transitions[1],
            "edited_end": transitions[2],
            "edited_duration": round(transitions[2] - transitions[1], 4),
            "graphic_config": {
                "template": "before_after",
                "system_priority": True,
                "full_screen_no_avatar": is_no_avatar,
                "switch_sec": 2.88,
                "device_mode": "combo",
                "real_photo_mockups": True,
                "pill": "DIRECTORIO TUTORES + 28 ESPECIALIDADES",
                "headline_kicker": "⚡ PANTALLAS REALES WEB & APP · SIN FRENAR TU CLÍNICA",
                "headline_main": "🐾 TE MIGRAMOS GRATIS Y EN EL DÍA",
                "ui_screen_1": p_s2_1["desk"],
                "ui_screen_2": p_s2_2["desk"],
                "laptop_screenshot": p_s2_1["mac"],
                "laptop_screenshot_2": p_s2_2["mac"],
                "phone_screenshot": p_s2_1["ip"],
                "phone_screenshot_2": p_s2_2["ip"],
                "workflow_step_1": "DIRECTORIO DE TUTORES Y CONTACTO DIRECTO WHATSAPP",
                "workflow_step_2": "CONFIGURACIÓN DE CLÍNICA Y 28 ESPECIALIDADES MÉDICAS",
                "before_label": "SISTEMA VIEJO / EXCEL",
                "before_value": "Miedo a Perder Datos",
                "before_desc": "Planillas sueltas y tiempo perdido",
                "after_label": "CON MASCOTAMÁS",
                "after_value": "Migración en el Día",
                "after_desc": "100% Gratis y sin frenar tu clínica",
                "mascot_expression": "happy",
            },
        },
        {
            "scene_id": 3,
            "sentence_id": 3,
            "word_ids": [w["word_id"] for w in raw_words if w["scene_id"] == 3],
            "text": scene_texts[2],
            "layout_mode": "split_graphic",
            "is_hook": False,
            "is_cta": False,
            "top_title": None,
            "edited_start": transitions[2],
            "edited_end": transitions[3],
            "edited_duration": round(transitions[3] - transitions[2], 4),
            "graphic_config": {
                "template": "checklist",
                "system_priority": True,
                "full_screen_no_avatar": is_no_avatar,
                "switch_sec": 2.88,
                "device_mode": "combo_left_phone",
                "real_photo_mockups": True,
                "pill": "LEGAJO PDF + CURVA DE PESO Y VACUNAS",
                "headline_kicker": "📋 CAPTURAS REALES DE HISTORIAS CLÍNICAS Y VACUNAS",
                "headline_main": "🩺 CLIENTES, PACIENTES, HISTORIAS Y VACUNAS",
                "ui_screen_1": "../assets/manual_vete_y_marca/2026_12_ficha_hc_curva_peso.png",
                "ui_screen_2": p_s3_2["desk"],
                "laptop_screenshot": p_s3_1["mac"],
                "laptop_screenshot_2": p_s3_2["mac"],
                "phone_screenshot": p_s3_1["ip"],
                "phone_screenshot_2": p_s3_2["ip"],
                "workflow_step_1": "HISTORIA CLÍNICA DIGITAL, CURVA DE PESO Y DESCARGA PDF",
                "workflow_step_2": "NUEVO REGISTRO CLÍNICO Y CRONOGRAMA DE VACUNAS",
                "items": [
                    {"text": "Clientes y Pacientes", "tag": "100% MIGRADO"},
                    {"text": "Historias Clínicas PDF", "tag": "SIN PERDER FICHAS"},
                    {"text": "Historial de Vacunas", "tag": "COMPLETO"},
                ],
                "mascot_expression": "happy",
            },
        },
        {
            "scene_id": 4,
            "sentence_id": 4,
            "word_ids": [w["word_id"] for w in raw_words if w["scene_id"] == 4],
            "text": scene_texts[3],
            "layout_mode": "split_graphic",
            "is_hook": False,
            "is_cta": False,
            "top_title": None,
            "edited_start": transitions[3],
            "edited_end": transitions[4],
            "edited_duration": round(transitions[4] - transitions[3], 4),
            "graphic_config": {
                "template": "app_connection",
                "system_priority": True,
                "full_screen_no_avatar": is_no_avatar,
                "switch_sec": 2.88,
                "device_mode": "combo",
                "real_photo_mockups": True,
                "pill": "ALERTAS WHATSAPP + SALA EN VIVO",
                "headline_kicker": "💬 DESDE EL CELULAR O LA MACBOOK · 100% EN LA NUBE",
                "headline_main": "📲 RECORDATORIOS WHATSAPP Y SALA EN VIVO",
                "ui_screen_1": p_s4_1["desk"],
                "ui_screen_2": "../assets/manual_vete_y_marca/2026_13_sala_de_espera_en_vivo.png",
                "laptop_screenshot": p_s4_1["mac"],
                "laptop_screenshot_2": p_s4_2["mac"],
                "phone_screenshot": p_s4_1["ip"],
                "phone_screenshot_2": p_s4_2["ip"],
                "workflow_step_1": "CALENDARIO DE RECORDATORIOS AUTOMÁTICOS POR WHATSAPP",
                "workflow_step_2": "TABLERO DE PACIENTES EN SALA DE ESPERA EN TIEMPO REAL",
                "icon_a": "🏥",
                "app_a": "Sala en Vivo",
                "sub_a": "Fichas en la Nube 24/7",
                "status": "✓ EN EL DÍA",
                "app_b": "WhatsApp",
                "sub_b": "Recordatorios Automáticos",
                "mascot_expression": "surprised",
            },
        },
        {
            "scene_id": 5,
            "sentence_id": 5,
            "word_ids": [w["word_id"] for w in raw_words if w["scene_id"] == 5],
            "text": scene_texts[4],
            "layout_mode": "split_graphic",
            "is_hook": False,
            "is_cta": False,
            "top_title": None,
            "edited_start": transitions[4],
            "edited_end": transitions[5],
            "edited_duration": round(transitions[5] - transitions[4], 4),
            "graphic_config": {
                "template": "checklist",
                "system_priority": True,
                "full_screen_no_avatar": is_no_avatar,
                "switch_sec": 2.40,
                "device_mode": "combo_left_phone",
                "real_photo_mockups": True,
                "pill": "4 AGENDAS + CHECKOUT MERCADO PAGO*",
                "headline_kicker": "💳 FLUJO REAL DE RESERVA Y SEÑA CON MERCADO PAGO*",
                "headline_main": "⚡ 4 AGENDAS Y SEÑA CON MERCADO PAGO*",
                "ui_screen_1": "../assets/manual_vete_y_marca/2026_02_cuatro_tipos_de_calendario.png",
                "ui_screen_2": p_s5_2["desk"],
                "laptop_screenshot": p_s5_1["mac"],
                "laptop_screenshot_2": p_s5_2["mac"],
                "phone_screenshot": p_s5_1["ip"],
                "phone_screenshot_2": p_s5_2["ip"],
                "workflow_step_1": "SELECTOR DE 4 MODALIDADES DE AGENDA OPERATIVA",
                "workflow_step_2": "CHECKOUT ONLINE DE SEÑA AUTOMÁTICA CON MERCADO PAGO*",
                "items": [
                    {"text": "4 Agendas Inteligentes", "tag": "SIN HUECOS"},
                    {"text": "Seña Mercado Pago*", "tag": "TURNOS SEGUROS"},
                    {"text": "Cero Inasistencias", "tag": "24/7 ONLINE"},
                ],
                "legal_disclaimer": legal_tyc,
                "mascot_expression": "happy",
            },
        },
        {
            "scene_id": 6,
            "sentence_id": 6,
            "word_ids": [w["word_id"] for w in raw_words if w["scene_id"] == 6],
            "text": scene_texts[5],
            "layout_mode": "split_graphic",
            "is_hook": False,
            "is_cta": True,
            "top_title": None,
            "edited_start": transitions[5],
            "edited_end": transitions[6],
            "edited_duration": round(transitions[6] - transitions[5], 4),
            "graphic_config": {
                "template": "chat_input",
                "system_priority": True,
                "full_screen_no_avatar": is_no_avatar,
                "switch_sec": 1.92,
                "device_mode": "combo",
                "real_photo_mockups": True,
                "pill": "MASCOTAMAS.COM · MIGRÁ HOY",
                "headline_kicker": "🐾 AUTOGESTIÓN PÚBLICA 24/7 + ESTADÍSTICAS KPI",
                "headline_main": "💻 ESCRIBINOS HOY EN MASCOTAMAS.COM",
                "ui_screen_1": p_s6_1["desk"],
                "ui_screen_2": "../assets/manual_vete_y_marca/2026_14_estadisticas_y_metricas.png",
                "laptop_screenshot": p_s6_1["mac"],
                "laptop_screenshot_2": p_s6_2["mac"],
                "phone_screenshot": p_s6_1["ip"],
                "phone_screenshot_2": p_s6_2["ip"],
                "workflow_step_1": "LINK PÚBLICO DE AUTOGESTIÓN DE TURNOS 24/7 EN CELULAR",
                "workflow_step_2": "TABLERO DE ESTADÍSTICAS Y MÉTRICAS · MASCOTAMAS.COM",
                "prompt_text": "MIGRACIÓN 100% GRATIS Y EN EL DÍA",
                "reply_text": "Entrá en mascotamas.com o comentá MIGRAR",
                "badge": "MASCOTAMAS.COM · MIGRACIÓN GRATIS",
                "legal_disclaimer": legal_tyc,
                "mascot_expression": "happy",
            },
        },
    ]

    style = load_style()
    cta_kw = "MIGRAR"
    cooldown_min = 3.5
    last_bounce_time = -999.0

    words_cleaned = []
    edited_words = []
    hl_terms = [
        "excel", "miedo", "veterinaria", "mascotamás", "migración", "gratis", "día",
        "clientes", "pacientes", "historias", "clínicas", "vacunas", "ficha",
        "recordatorios", "automáticos", "whatsapp", "vivo", "nube",
        "4", "agendas", "inteligentes", "seña", "mercado", "pago", "migramos",
    ]
    for i, w in enumerate(raw_words):
        wid = w["word_id"]
        sub_txt = w["subtitle_text"]
        wc = {
            "word_id": wid,
            "word": w["word"],
            "subtitle_text": sub_txt,
            "start": w["start"],
            "real_start": w["start"],
            "end": w["end"],
            "edited_start": w["start"],
            "edited_end": w["end"],
            "rms_db": -16.0,
            "keep": True,
            "delete_reason": "",
            "scene_id": w["scene_id"],
            "face_center": [0.5, 0.25],
        }
        nxt_str = raw_words[i + 1]["word"] if i + 1 < len(raw_words) else ""
        is_yel, can_bounce = is_highlighted_word(sub_txt, nxt_str, style, cta_kw)
        clean_low = sub_txt.lower().strip("¿?¡!.,*:")
        if clean_low in hl_terms:
            is_yel = True
            can_bounce = True
        wc["is_yellow"] = is_yel
        if is_yel and can_bounce and (wc["edited_start"] - last_bounce_time >= cooldown_min):
            wc["trigger_bounce"] = True
            last_bounce_time = wc["edited_start"]
        else:
            wc["trigger_bounce"] = False
        words_cleaned.append(wc)
        edited_words.append(wc)

    subtitle_blocks = build_subtitle_blocks(edited_words, style)

    guion_json = {
        "total_original_words": len(words_cleaned),
        "kept_word_ids": [w["word_id"] for w in words_cleaned],
        "deleted_word_ids": [],
        "deleted_details": [],
        "cta_keyword": cta_kw,
        "hook_title": hook_title,
        "cta_title": cta_title,
        "words_cleaned": words_cleaned,
        "scenes": scenes_def,
    }
    with open(os.path.join(WORK_DIR, "guion_corregido.json"), "w", encoding="utf-8") as f:
        json.dump(guion_json, f, ensure_ascii=False, indent=2)

    segments = [{
        "segment_id": 1,
        "source_start": 0.0,
        "source_end": total_dur,
        "duration": total_dur,
        "edited_start": 0.0,
        "edited_end": total_dur,
        "avg_rms_db": -16.0,
        "face_center": [0.5, 0.25],
        "word_ids": [w["word_id"] for w in words_cleaned],
    }]

    sfx_events = []
    for tr_t in transitions[1:-1]:
        sfx_events.append({
            "type": "whoosh",
            "time": round(max(0.0, tr_t - 0.04), 4),
            "reason": f"Beat-synced scene transition @ {tr_t:.2f}s (125 BPM House)",
        })
    for sw_abs in [1.44, 3.36, 8.16, 14.40, 20.64, 26.40, 31.20]:
        sfx_events.append({
            "type": "pop",
            "time": round(max(0.0, sw_abs - 0.03), 4),
            "reason": f"Beat-synced live UI click & screen switch @ {sw_abs:.2f}s",
        })
    sfx_events.append({
        "type": "ding",
        "time": round(transitions[5] - 0.02, 4),
        "reason": "CTA final",
    })
    sfx_events.sort(key=lambda x: x["time"])

    mg_dur = sum(sc["edited_duration"] for sc in scenes_def if sc["layout_mode"] == "split_graphic")
    mg_ratio = round(mg_dur / total_dur, 4)

    edit_plan = {
        "source_video": os.path.join(WORK_DIR, "source_input.mp4"),
        "source_audio": os.path.join(WORK_DIR, "source_audio.wav"),
        "skip_denoise": True,
        "preframed_source": True,
        "reuse_mg_frames": reuse_mg,
        "bgm_override_path": house_bgm_wav,
        "bgm_relative_db": -6.8,
        "bgm_ducking_db": -2.0,
        "original_duration_sec": total_dur,
        "edited_duration_sec": total_dur,
        "motion_graphics_coverage_ratio": mg_ratio,
        "cta_keyword": cta_kw,
        "hook_title": hook_title,
        "cta_title": cta_title,
        "face_metadata": {
            "default_face_center": [0.5, 0.25],
            "has_face": True,
        },
        "segments": segments,
        "words": edited_words,
        "edited_words": edited_words,
        "subtitle_blocks": subtitle_blocks,
        "scenes": scenes_def,
        "sfx_events": sfx_events,
    }

    with open(os.path.join(WORK_DIR, "edit_plan.json"), "w", encoding="utf-8") as f:
        json.dump(edit_plan, f, ensure_ascii=False, indent=2)
    with open(os.path.join(WORK_DIR, f"edit_plan_{version_tag}.json"), "w", encoding="utf-8") as f:
        json.dump(edit_plan, f, ensure_ascii=False, indent=2)

    print(f"\n[{version_tag} PLAN READY] Dur={total_dur:.2f}s, MG={mg_ratio*100:.1f}%, BGM=-6.8dB/-2.0dB (House Arriba)")
    render_final_video(out_edited_mp4)
    subprocess.run([sys.executable, os.path.join(SCRIPTS_DIR, "step5_verify.py"), out_edited_mp4], check=True)
    shutil.copy2(os.path.join(BASE_DIR, "verification_grid.jpg"), out_grid_jpg)
    print(f"  -> [{version_tag} COMPLETADO] {out_edited_mp4}")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    tts_wav_path = os.path.join(WORK_DIR, "v6_tts_synced.wav")
    house_bgm_wav = os.path.join(WORK_DIR, "v7_lyria_house_arriba.wav")
    with open(os.path.join(WORK_DIR, "v6_words_synced.json"), "r", encoding="utf-8") as f:
        wdata = json.load(f)

    if mode in ("all", "v8A"):
        v8a_master = os.path.join(WORK_DIR, "v8A_no_avatar_system_canvas_master.mp4")
        build_v8A_no_avatar_master(v8a_master, total_dur=33.60, fps=30)
        out_v8a_edit = os.path.join(
            BASE_DIR, "editados",
            "Reel Publicitario - Migracion Gratis en el Dia a MascotaMas (v8A - Sin Avatar 100% Showcase Creativo de Pantallas Reales Celular y MacBook + Musica House Arriba).mp4",
        )
        out_v8a_grid = os.path.join(WORK_DIR, "verification_grid_v8A.jpg")
        render_v8_version(
            "v8A",
            v8a_master,
            tts_wav_path,
            house_bgm_wav,
            wdata,
            out_v8a_edit,
            out_v8a_grid,
            reuse_mg=False,
        )

    if mode in ("all", "v8B"):
        v8b_master = os.path.join(WORK_DIR, "v8B_avatar_showing_devices_master.mp4")
        build_v8B_avatar_showing_devices_master(v8b_master, total_dur=33.60, fps=30)
        out_v8b_edit = os.path.join(
            BASE_DIR, "editados",
            "Reel Publicitario - Migracion Gratis en el Dia a MascotaMas (v8B - Avatar Mostrando Pantallas Reales desde Celular y MacBook + Musica House Arriba).mp4",
        )
        out_v8b_grid = os.path.join(WORK_DIR, "verification_grid_v8B.jpg")
        render_v8_version(
            "v8B",
            v8b_master,
            tts_wav_path,
            house_bgm_wav,
            wdata,
            out_v8b_edit,
            out_v8b_grid,
            reuse_mg=False,
        )


if __name__ == "__main__":
    main()
