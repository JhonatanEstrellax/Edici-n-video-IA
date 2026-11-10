# -*- coding: utf-8 -*-
r"""
Ensambla y masteriza el Spot Publicitario Profesional de MascotaMás (Sección: Turnos -> Guardería)
protagonizado por el Avatar Veterinario Hombre VIP Argentino con ropa urbana/casual,
enfocado desde espaldas usando su MacBook Pro 16" y su iPhone 16 Pro Max, con acento argentino (es-AR),
lip-sync natural, música House (125 BPM) sincronizada a los cortes y transiciones,
capturas reales de `Manual De Usuario Vete y Marca` (Turnos -> Guardería) y subtítulos Poppins.

Genera dos versiones en `1080x1920 @ 30fps`:
1. `Spot Publicitario - MascotaMas Turnos Guarderia (Avatar Hombre VIP Casual + MacBook Pro e iPhone Reales + Musica House).mp4`
   (Producción completa con HUD interactivo de Turnos Guardería, cursor animado, subtítulos Poppins ExtraBold y SFX).
2. `Spot Publicitario - MascotaMas Turnos Guarderia (Avatar Hombre VIP Casual - Version Clean Cinema 1080p).mp4`
   (Edición cinematográfica pura 1080p con voz argentina y música House sincronizada al beat).
"""
import os
import sys
import json
import math
import shutil
import subprocess
import pathlib
import cv2
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

BASE_DIR = pathlib.Path(r"c:\IA\Edicion de videos")
WORK_DIR = BASE_DIR / "reels_work"
SPOT_DIR = BASE_DIR / "assets" / "avatar_veterinario_hombre_vip" / "spot_guarderia"
MANUAL_DIR = BASE_DIR / "assets" / "manual_vete_y_marca"
EDITADOS_DIR = BASE_DIR / "editados"
EDITADOS_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACTS_DIR = pathlib.Path(r"C:\Users\Demiante\.gemini\antigravity\brain\56e5cec9-1285-4884-b2c6-a38ac91ed5ae")

FFMPEG_EXE = str(BASE_DIR / "bin" / "ffmpeg" / "ffmpeg.exe")
FONT_EXTRABOLD = str(BASE_DIR / "fonts" / "Poppins-ExtraBold.ttf")
FONT_BOLD = str(BASE_DIR / "fonts" / "Poppins-Bold.ttf")
HOUSE_BGM_WAV = str(WORK_DIR / "v7_lyria_house_arriba.wav")

W, H, FPS = 1080, 1920, 30
BEAT_SEC = 0.48  # 125 BPM exacto (60 / 125 = 0.48s)

# Duraciones clavadas al grid de 125 BPM (0.48s por beat):
# Clip 1: 0.00s -> 9.60s (20 beats = 5 compases) | src: 0.00s -> 9.60s
# Clip 2: 9.60s -> 18.24s (18 beats = 4.5 compases, dur=8.64s) | src: 0.00s -> 8.64s
# Clip 3: 18.24s -> 27.84s (20 beats = 5 compases, dur=9.60s) | src: 0.20s -> 9.80s
TOTAL_DUR = 27.84
TOTAL_FRAMES = int(round(TOTAL_DUR * FPS))

SEGMENTS_SPEC = [
    {
        "name": "clip1",
        "path": str(SPOT_DIR / "spot_guarderia_clip1_espalda_a_giro_10s.mp4"),
        "src_start": 0.00,
        "src_end": 9.60,
        "dst_start": 0.00,
        "dst_end": 9.60,
    },
    {
        "name": "clip2",
        "path": str(SPOT_DIR / "spot_guarderia_clip2_espalda_cupos_y_celular_10s.mp4"),
        "src_start": 0.00,
        "src_end": 8.64,
        "dst_start": 9.60,
        "dst_end": 18.24,
    },
    {
        "name": "clip3",
        "path": str(SPOT_DIR / "spot_guarderia_clip3_frente_vip_cta_10s.mp4"),
        "src_start": 0.20,
        "src_end": 9.80,
        "dst_start": 18.24,
        "dst_end": 27.84,
    },
]

# Bloques de Subtítulos sincronizados a los timestamps reales de Whisper (con ortografía comercial perfecta)
SUBTITLE_BLOCKS = [
    # Clip 1 (offset 0.00s, habla 2.98s -> 9.06s)
    {
        "start": 2.94,
        "end": 4.92,
        "words": [
            {"text": "¿SEGUÍS", "start": 2.94, "end": 3.32, "hl": False},
            {"text": "ANOTANDO", "start": 3.32, "end": 3.70, "hl": False},
            {"text": "TU", "start": 3.70, "end": 3.86, "hl": False},
            {"text": "GUARDERÍA", "start": 3.86, "end": 4.30, "hl": True},
            {"text": "POR", "start": 4.30, "end": 4.48, "hl": False},
            {"text": "WHATSAPP?", "start": 4.48, "end": 4.92, "hl": True},
        ],
    },
    {
        "start": 5.36,
        "end": 7.24,
        "words": [
            {"text": "MIRÁ", "start": 5.36, "end": 5.66, "hl": False},
            {"text": "CÓMO", "start": 5.66, "end": 5.80, "hl": False},
            {"text": "MANEJO", "start": 5.80, "end": 6.16, "hl": False},
            {"text": "LAS", "start": 6.16, "end": 6.28, "hl": False},
            {"text": "ESTADÍAS", "start": 6.28, "end": 6.84, "hl": True},
            {"text": "DESDE", "start": 6.84, "end": 7.24, "hl": False},
        ],
    },
    {
        "start": 7.24,
        "end": 9.25,
        "words": [
            {"text": "TURNOS", "start": 7.24, "end": 7.70, "hl": True},
            {"text": "DE", "start": 7.70, "end": 7.80, "hl": False},
            {"text": "GUARDERÍA", "start": 7.80, "end": 8.30, "hl": True},
            {"text": "EN", "start": 8.30, "end": 8.48, "hl": False},
            {"text": "MASCOTAMÁS.", "start": 8.48, "end": 9.25, "hl": True},
        ],
    },
    # Clip 2 (offset +9.60s, habla 9.60s -> 17.36s)
    {
        "start": 9.60,
        "end": 11.96,
        "words": [
            {"text": "CONTROLÁS", "start": 9.60, "end": 10.60, "hl": False},
            {"text": "EL", "start": 10.60, "end": 10.74, "hl": False},
            {"text": "CHECK-IN,", "start": 10.74, "end": 11.16, "hl": True},
            {"text": "EL", "start": 11.46, "end": 11.50, "hl": False},
            {"text": "CHECK-OUT,", "start": 11.50, "end": 11.96, "hl": True},
        ],
    },
    {
        "start": 12.60,
        "end": 15.28,
        "words": [
            {"text": "LOS", "start": 12.60, "end": 12.76, "hl": False},
            {"text": "CUPOS", "start": 12.76, "end": 13.10, "hl": True},
            {"text": "POR", "start": 13.10, "end": 13.30, "hl": False},
            {"text": "DÍA", "start": 13.30, "end": 13.56, "hl": True},
            {"text": "Y", "start": 13.56, "end": 14.60, "hl": False},
            {"text": "VINCULÁS", "start": 14.60, "end": 15.06, "hl": True},
            {"text": "CADA", "start": 15.06, "end": 15.28, "hl": False},
        ],
    },
    {
        "start": 15.28,
        "end": 17.56,
        "words": [
            {"text": "MASCOTA", "start": 15.28, "end": 15.80, "hl": False},
            {"text": "A", "start": 15.80, "end": 15.90, "hl": False},
            {"text": "SU", "start": 15.90, "end": 16.00, "hl": False},
            {"text": "HISTORIA", "start": 16.00, "end": 16.26, "hl": True},
            {"text": "CLÍNICA", "start": 16.26, "end": 16.80, "hl": True},
            {"text": "EN", "start": 16.80, "end": 17.08, "hl": False},
            {"text": "UN", "start": 17.08, "end": 17.18, "hl": False},
            {"text": "CLIC.", "start": 17.18, "end": 17.56, "hl": True},
        ],
    },
    # Clip 3 (src_start=0.20s -> offset = +18.04s sobre timestamps de clip3)
    {
        "start": 18.68,
        "end": 20.64,
        "words": [
            {"text": "¡PASATE", "start": 18.68, "end": 19.34, "hl": True},
            {"text": "HOY", "start": 19.34, "end": 19.68, "hl": False},
            {"text": "A", "start": 19.68, "end": 19.92, "hl": False},
            {"text": "MASCOTAMÁS!", "start": 19.92, "end": 20.64, "hl": True},
        ],
    },
    {
        "start": 20.64,
        "end": 23.40,
        "words": [
            {"text": "MIGRAMOS", "start": 20.64, "end": 21.52, "hl": True},
            {"text": "TODA", "start": 21.52, "end": 21.82, "hl": False},
            {"text": "TU", "start": 21.82, "end": 22.04, "hl": False},
            {"text": "VETERINARIA", "start": 22.04, "end": 22.70, "hl": True},
            {"text": "EN", "start": 22.70, "end": 22.90, "hl": False},
            {"text": "EL", "start": 22.90, "end": 23.02, "hl": False},
            {"text": "DÍA", "start": 23.02, "end": 23.40, "hl": True},
        ],
    },
    {
        "start": 23.40,
        "end": 27.10,
        "words": [
            {"text": "Y", "start": 23.40, "end": 24.14, "hl": False},
            {"text": "100%", "start": 24.14, "end": 24.66, "hl": True},
            {"text": "GRATIS.", "start": 24.66, "end": 25.64, "hl": True},
            {"text": "¡ESCRIBINOS", "start": 25.64, "end": 26.30, "hl": True},
            {"text": "AHORA!", "start": 26.30, "end": 27.10, "hl": True},
        ],
    },
]


# Tarjetas Reales de Turnos -> Guardería (de Manual De Usuario Vete y Marca) sincronizadas al beat de 125 BPM (0.48s)
HUD_CARDS_SPEC = [
    {
        "start": 0.48,
        "end": 4.80,
        "badge": "TURNOS -> GUARDERÍA · ESTADÍAS Y OCUPACIÓN EN VIVO",
        "sub": "MacBook Pro 16\" + iPhone 16 Pro Max · gestion.mascotamas.com",
        "main_img": "12_Hotel_y_Guarderia_por_Estadia__02_Tablero_de_Estadias_y_Ocupacion__01_Grilla_Reservas_MultiDia_CheckIn_CheckOut__01_MacBook_Pro_Real.png",
        "side_img": "12_Hotel_y_Guarderia_por_Estadia__02_Tablero_de_Estadias_y_Ocupacion__01_Grilla_Reservas_MultiDia_CheckIn_CheckOut__02_iPhone_16_Pro_Max_Real.png",
        "click_t": 2.40,
        "click_rel": (0.68, 0.46),
        "beam_target": (245, 945),  # Conecta visualmente con la MacBook Pro física en el escritorio
    },
    {
        "start": 4.80,
        "end": 9.60,
        "badge": "GRILLA MULTI-DÍA · CHECK-IN Y CHECK-OUT DE GUARDERÍA",
        "sub": "Thor (Martín López) · Suite Canina · Ingreso 09/11 -> Egreso 11/11",
        "main_img": "12_Hotel_y_Guarderia_por_Estadia__02_Tablero_de_Estadias_y_Ocupacion__01_Grilla_Reservas_MultiDia_CheckIn_CheckOut__04_Raw_Desktop.png",
        "side_img": "12_Hotel_y_Guarderia_por_Estadia__02_Tablero_de_Estadias_y_Ocupacion__01_Grilla_Reservas_MultiDia_CheckIn_CheckOut__02_iPhone_16_Pro_Max_Real.png",
        "click_t": 6.72,
        "click_rel": (0.76, 0.45),
        "beam_target": (250, 935),
    },
    {
        "start": 9.60,
        "end": 14.40,
        "badge": "CATEGORÍAS, CUPOS DISPONIBLES Y TARIFAS POR DÍA",
        "sub": "Bloqueo de Fechas · Cupo 5 Lugares · Tarifa Automática por Estadía",
        "main_img": "12_Hotel_y_Guarderia_por_Estadia__01_Configuracion_de_Alojamiento__01_Modal_Categorias_Cupos_y_Tarifas_por_Noche__04_Raw_Desktop.png",
        "side_img": "12_Hotel_y_Guarderia_por_Estadia__01_Configuracion_de_Alojamiento__01_Modal_Categorias_Cupos_y_Tarifas_por_Noche__02_iPhone_16_Pro_Max_Real.png",
        "click_t": 11.52,
        "click_rel": (0.64, 0.62),
        "beam_target": (250, 935),
    },
    {
        "start": 14.40,
        "end": 18.24,
        "badge": "VINCULACIÓN DIRECTA A HISTORIA CLÍNICA EN 1 CLIC",
        "sub": "Botón 'Vincular HC' y 'Ver / Check-in ->' desde Turnos Guardería",
        "main_img": "00_Secuencias_Paso_a_Paso__01_Recorrido_Completo_App_10_Pantallas__10_Paso_10_Hotel_y_Guarderia_por_Estadia_Check-In_Check-Out__01_MacBook_Pro_Real.png",
        "side_img": "12_Hotel_y_Guarderia_por_Estadia__02_Tablero_de_Estadias_y_Ocupacion__01_Grilla_Reservas_MultiDia_CheckIn_CheckOut__02_iPhone_16_Pro_Max_Real.png",
        "click_t": 16.32,
        "click_rel": (0.66, 0.50),
        "beam_target": (250, 935),
    },
    {
        "start": 18.24,
        "end": 27.84,
        "badge": "MIGRACIÓN 100% GRATIS EN EL DÍA · PASATE A MASCOTAMÁS",
        "sub": "Escribinos ahora · Todo tu sistema y Turnos de Guardería listos hoy",
        "main_img": "12_Hotel_y_Guarderia_por_Estadia__02_Tablero_de_Estadias_y_Ocupacion__01_Grilla_Reservas_MultiDia_CheckIn_CheckOut__03_Combo_MacBook_e_iPhone.png",
        "side_img": "12_Hotel_y_Guarderia_por_Estadia__01_Configuracion_de_Alojamiento__01_Modal_Categorias_Cupos_y_Tarifas_por_Noche__01_MacBook_Pro_Real.png",
        "click_t": 22.08,
        "click_rel": (0.52, 0.54),
        "beam_target": (825, 960),  # En clip3 la MacBook Pro está a la derecha del escritorio
    },
]


def load_Segment_frames(spec):
    """Carga los frames del segmento a 30fps exactos en resolución 1080x1920."""
    cap = cv2.VideoCapture(spec["path"])
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    n_src = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    raw_frames = []
    while True:
        ok, frm = cap.read()
        if not ok:
            break
        if frm.shape[1] != W or frm.shape[0] != H:
            frm = cv2.resize(frm, (W, H), interpolation=cv2.INTER_LANCZOS4)
        raw_frames.append(frm)
    cap.release()

    dur = spec["dst_end"] - spec["dst_start"]
    n_out = int(round(dur * FPS))
    out_frames = []
    for i in range(n_out):
        t_rel = i / float(FPS)
        t_src = spec["src_start"] + t_rel
        f_float = min(len(raw_frames) - 1.001, max(0.0, t_src * src_fps))
        idx0 = int(math.floor(f_float))
        idx1 = min(len(raw_frames) - 1, idx0 + 1)
        frac = f_float - idx0
        if frac < 0.01 or idx0 == idx1:
            out_frames.append(raw_frames[idx0].copy())
        else:
            blended = cv2.addWeighted(raw_frames[idx0], 1.0 - frac, raw_frames[idx1], frac, 0.0)
            out_frames.append(blended)
    return out_frames


def draw_top_header(canvas_pil: Image.Image, t_sec: float, font_badge: ImageFont.FreeTypeFont, font_sub: ImageFont.FreeTypeFont):
    draw = ImageDraw.Draw(canvas_pil, "RGBA")
    # Pastilla superior glassmorphism en zona segura (y = 66..154)
    bx1, by1, bx2, by2 = 44, 66, W - 44, 154
    draw.rounded_rectangle([bx1, by1, bx2, by2], radius=26, fill=(12, 18, 34, 218), outline=(168, 85, 247, 230), width=3)

    # Indicador pulsante al ritmo de 125 BPM (0.48s)
    beat_phase = (t_sec / BEAT_SEC) % 1.0
    dot_r = int(8 + 3 * math.sin(beat_phase * math.pi * 2))
    draw.ellipse([bx1 + 26 - dot_r, by1 + 44 - dot_r, bx1 + 26 + dot_r, by1 + 44 + dot_r], fill=(52, 211, 153, 255))

    title_txt = "MASCOTAMÁS · TURNOS GUARDERÍA"
    draw.text((bx1 + 50, by1 + 14), title_txt, font=font_badge, fill=(255, 255, 255, 255))
    sub_txt = "SISTEMA DE GESTIÓN VETERINARIA · ESTADÍAS, CUPOS Y CHECK-IN"
    draw.text((bx1 + 50, by1 + 52), sub_txt, font=font_sub, fill=(242, 199, 92, 245))


def draw_hud_callout_deck(
    canvas_pil: Image.Image,
    t_sec: float,
    img_cache: dict,
    font_title: ImageFont.FreeTypeFont,
    font_sub: ImageFont.FreeTypeFont,
):
    """
    Dibuja el panel HUD interactivo en y = 1095..1505 (debajo de la línea del escritorio y la MacBook Pro física,
    y arriba de la zona segura de subtítulos y=1525..1730), conectado con un haz luminoso a la pantalla de la MacBook Pro.
    """
    active_card = None
    for c in HUD_CARDS_SPEC:
        if c["start"] <= t_sec < c["end"]:
            active_card = c
            break
    if active_card is None:
        return

    local_t = t_sec - active_card["start"]
    card_dur = active_card["end"] - active_card["start"]

    # Animación suave de entrada en los primeros 0.28s
    enter_u = min(1.0, local_t / 0.28)
    ease_u = 1.0 - pow(1.0 - enter_u, 3)
    y_offset = int((1.0 - ease_u) * 35)

    cx1, cy1, cx2, cy2 = 38, 1096 + y_offset, W - 38, 1502 + y_offset
    cw = cx2 - cx1
    ch = cy2 - cy1

    draw = ImageDraw.Draw(canvas_pil, "RGBA")

    # Haz de proyección sutil desde la MacBook Pro física del escritorio hasta el borde superior de la tarjeta HUD
    tx, ty = active_card["beam_target"]
    beam_pts = [(tx - 28, ty), (tx + 28, ty), (cx1 + int(cw * 0.62), cy1), (cx1 + int(cw * 0.18), cy1)]
    draw.polygon(beam_pts, fill=(168, 85, 247, int(42 * ease_u)))
    draw.line([(tx, ty), (cx1 + int(cw * 0.35), cy1)], fill=(242, 199, 92, int(185 * ease_u)), width=3)
    draw.ellipse([tx - 7, ty - 7, tx + 7, ty + 7], fill=(242, 199, 92, int(240 * ease_u)))

    # Fondo glass oscuro con borde neón violeta/dorado pulsante al beat
    beat_pulse = 0.5 + 0.5 * math.cos((t_sec / BEAT_SEC) * 2.0 * math.pi)
    border_col = (
        int(168 + (242 - 168) * beat_pulse * 0.4),
        int(85 + (199 - 85) * beat_pulse * 0.4),
        int(247 + (92 - 247) * beat_pulse * 0.4),
        245,
    )
    draw.rounded_rectangle([cx1, cy1, cx2, cy2], radius=24, fill=(13, 19, 36, 238), outline=border_col, width=3)

    # Barra superior del HUD
    draw.rounded_rectangle([cx1 + 3, cy1 + 3, cx2 - 3, cy1 + 68], radius=21, fill=(28, 37, 65, 245))
    draw.text((cx1 + 22, cy1 + 10), active_card["badge"], font=font_title, fill=(242, 199, 92, 255))
    draw.text((cx1 + 22, cy1 + 39), active_card["sub"], font=font_sub, fill=(220, 232, 255, 240))

    # Área de contenido de las pantallas reales (cy1 + 74 .. cy2 - 10)
    inner_y1 = cy1 + 74
    inner_h = (cy2 - 10) - inner_y1
    main_w = int(cw * 0.69)
    side_w = cw - main_w - 28

    main_im = img_cache[active_card["main_img"]]
    side_im = img_cache[active_card["side_img"]]

    # Zoom suave progresivo en la captura principal
    pan_u = min(1.0, local_t / max(0.1, card_dur))
    mw_src, mh_src = main_im.size
    crop_scale = 1.0 - 0.08 * math.sin(pan_u * math.pi)
    c_w = int(mw_src * crop_scale)
    c_h = int(mh_src * crop_scale)
    x0 = int((mw_src - c_w) * 0.5 * pan_u)
    y0 = int((mh_src - c_h) * 0.35 * pan_u)
    main_crop = main_im.crop((x0, y0, x0 + c_w, y0 + c_h)).resize((main_w, inner_h), Image.Resampling.LANCZOS)

    # Máscara redondeada para imagen principal
    m_mask = Image.new("L", (main_w, inner_h), 0)
    ImageDraw.Draw(m_mask).rounded_rectangle([0, 0, main_w - 1, inner_h - 1], radius=14, fill=255)
    canvas_pil.paste(main_crop, (cx1 + 12, inner_y1), m_mask)
    draw.rounded_rectangle([cx1 + 12, inner_y1, cx1 + 12 + main_w, inner_y1 + inner_h], radius=14, outline=(255, 255, 255, 90), width=2)

    # Imagen lateral (iPhone 16 Pro Max Real / Secundaria)
    side_resized = side_im.resize((side_w, inner_h), Image.Resampling.LANCZOS)
    s_mask = Image.new("L", (side_w, inner_h), 0)
    ImageDraw.Draw(s_mask).rounded_rectangle([0, 0, side_w - 1, inner_h - 1], radius=14, fill=255)
    sx1 = cx1 + 18 + main_w
    canvas_pil.paste(side_resized, (sx1, inner_y1), s_mask)
    draw.rounded_rectangle([sx1, inner_y1, sx1 + side_w, inner_y1 + inner_h], radius=14, outline=(168, 85, 247, 150), width=2)

    # Cursor interactivo y onda de clic en la pantalla principal
    click_dt = t_sec - active_card["click_t"]
    rel_x, rel_y = active_card["click_rel"]
    cur_x = cx1 + 12 + int(main_w * rel_x)
    cur_y = inner_y1 + int(inner_h * rel_y)
    if -0.6 <= click_dt <= 1.2:
        move_u = min(1.0, max(0.0, (click_dt + 0.6) / 0.6))
        cx_now = int((cx1 + 60) * (1.0 - move_u) + cur_x * move_u)
        cy_now = int((inner_y1 + inner_h - 30) * (1.0 - move_u) + cur_y * move_u)
        if click_dt >= 0.0:
            ripple_u = min(1.0, click_dt / 0.55)
            r_rad = int(12 + 42 * ripple_u)
            r_alpha = int(235 * (1.0 - ripple_u))
            draw.ellipse([cur_x - r_rad, cur_y - r_rad, cur_x + r_rad, cur_y + r_rad], outline=(52, 211, 153, r_alpha), width=4)
        # Puntero blanco con borde oscuro
        arrow = [
            (cx_now, cy_now),
            (cx_now, cy_now + 26),
            (cx_now + 7, cy_now + 20),
            (cx_now + 13, cy_now + 31),
            (cx_now + 18, cy_now + 28),
            (cx_now + 12, cy_now + 17),
            (cx_now + 21, cy_now + 17),
        ]
        draw.polygon(arrow, fill=(255, 255, 255, 255), outline=(15, 23, 42, 255))


def draw_subtitles_poppins(
    canvas_pil: Image.Image,
    t_sec: float,
    font_sub: ImageFont.FreeTypeFont,
):
    """
    Renderiza los subtítulos palabra por palabra con Poppins-ExtraBold en la zona segura inferior (y = 1528..1728),
    con resalte amarillo (#F2C75C) en palabras clave y efecto bounce en la palabra activa.
    """
    active_block = None
    for blk in SUBTITLE_BLOCKS:
        if blk["start"] <= t_sec <= blk["end"]:
            active_block = blk
            break
    if active_block is None:
        return

    draw = ImageDraw.Draw(canvas_pil, "RGBA")
    words = active_block["words"]

    # Dividir en hasta 2 líneas balanceadas
    mid = (len(words) + 1) // 2 if len(words) > 3 else len(words)
    lines = [words[:mid], words[mid:]] if len(words) > 3 else [words]

    # Caja contenedora semitransparente para máxima legibilidad
    box_y1 = 1526
    box_y2 = 1718 if len(lines) > 1 else 1642
    draw.rounded_rectangle([54, box_y1, W - 54, box_y2], radius=26, fill=(10, 15, 28, 212), outline=(255, 255, 255, 55), width=2)

    y_cursor = box_y1 + 18
    for line in lines:
        if not line:
            continue
        space_w = 18
        word_widths = []
        for w in line:
            bbox = draw.textbbox((0, 0), w["text"], font=font_sub)
            word_widths.append(bbox[2] - bbox[0])
        total_w = sum(word_widths) + space_w * (len(line) - 1)
        x_cursor = (W - total_w) // 2

        for w, ww in zip(line, word_widths):
            is_active = w["start"] <= t_sec < w["end"]
            is_spoken = t_sec >= w["start"]
            if is_active:
                color = (242, 199, 92, 255) if w["hl"] else (56, 189, 248, 255)
                y_lift = -6
                # Píldora activa detrás de la palabra pronunciada
                draw.rounded_rectangle(
                    [x_cursor - 10, y_cursor + y_lift - 4, x_cursor + ww + 10, y_cursor + y_lift + 68],
                    radius=14,
                    fill=(168, 85, 247, 175) if not w["hl"] else (242, 199, 92, 55),
                )
            elif is_spoken:
                color = (242, 199, 92, 255) if w["hl"] else (255, 255, 255, 255)
                y_lift = 0
            else:
                color = (205, 215, 230, 195)
                y_lift = 0

            # Contorno negro de 4px para contraste total
            for ox, oy in [(-3, -3), (3, -3), (-3, 3), (3, 3), (0, 4), (0, -4), (-4, 0), (4, 0)]:
                draw.text((x_cursor + ox, y_cursor + y_lift + oy), w["text"], font=font_sub, fill=(0, 0, 0, 245))
            draw.text((x_cursor, y_cursor + y_lift), w["text"], font=font_sub, fill=color)
            x_cursor += ww + space_w

        y_cursor += 82


def build_synced_audio_track(out_mixed_wav: str, include_sfx: bool = True):
    """
    Extrae el audio original con voz argentina (es-AR) de los 3 segmentos en los tiempos exactos,
    lo normaliza y lo mezcla con la pista House de 125 BPM (`v7_lyria_house_arriba.wav`) con sidechain ducking
    automático cuando el avatar habla + efectos de sonido (whoosh/pop/ding) clavados al beat.
    """
    sr = 48000
    n_samples = int(round(TOTAL_DUR * sr))
    voice_track = np.zeros((n_samples, 2), dtype=np.float32)

    for seg in SEGMENTS_SPEC:
        tmp_seg_wav = WORK_DIR / f"tmp_seg_{seg['name']}_48k.wav"
        seg_dur = seg["src_end"] - seg["src_start"]
        subprocess.run(
            [
                FFMPEG_EXE, "-y",
                "-ss", f"{seg['src_start']:.3f}",
                "-t", f"{seg_dur:.3f}",
                "-i", seg["path"],
                "-vn", "-ac", "2", "-ar", str(sr),
                str(tmp_seg_wav),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        seg_audio, _ = sf.read(str(tmp_seg_wav), dtype="float32")
        if seg_audio.ndim == 1:
            seg_audio = np.column_stack([seg_audio, seg_audio])

        # Normalizar pico de voz de cada clip para volumen parejo y potente
        peak = np.max(np.abs(seg_audio))
        if peak > 0.01:
            seg_audio = seg_audio * (0.88 / peak)

        # Fade-in y fade-out de 35ms en cada corte para cero clics
        fade_len = int(0.035 * sr)
        if len(seg_audio) > 2 * fade_len:
            fade_in = np.linspace(0.0, 1.0, fade_len, dtype=np.float32)[:, None]
            fade_out = np.linspace(1.0, 0.0, fade_len, dtype=np.float32)[:, None]
            seg_audio[:fade_len] *= fade_in
            seg_audio[-fade_len:] *= fade_out

        dst_i0 = int(round(seg["dst_start"] * sr))
        dst_i1 = min(n_samples, dst_i0 + len(seg_audio))
        voice_track[dst_i0:dst_i1] = seg_audio[: dst_i1 - dst_i0]

    # Cargar música House 125 BPM (v7_lyria_house_arriba.wav)
    bgm_audio, bgm_sr = sf.read(HOUSE_BGM_WAV, dtype="float32")
    if bgm_sr != sr:
        tmp_bgm_48k = WORK_DIR / "tmp_house_48k.wav"
        subprocess.run(
            [FFMPEG_EXE, "-y", "-i", HOUSE_BGM_WAV, "-ac", "2", "-ar", str(sr), str(tmp_bgm_48k)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        bgm_audio, _ = sf.read(str(tmp_bgm_48k), dtype="float32")
    if bgm_audio.ndim == 1:
        bgm_audio = np.column_stack([bgm_audio, bgm_audio])
    if len(bgm_audio) < n_samples:
        reps = int(math.ceil(n_samples / float(len(bgm_audio))))
        bgm_audio = np.tile(bgm_audio, (reps, 1))
    bgm_audio = bgm_audio[:n_samples]

    # Normalizar BGM base
    bgm_peak = np.max(np.abs(bgm_audio))
    if bgm_peak > 0.01:
        bgm_audio = bgm_audio * (0.75 / bgm_peak)

    # Envolvente de sidechain ducking: cuando el avatar no habla (intro 0..2.8s, transiciones 9.1..9.7s, 17.5..18.6s, outro 27.0..27.84s)
    # la música House sube con fuerza (gain=0.44); cuando habla baja suavemente (gain=0.19) para que el acento argentino brille 100% claro
    def moving_avg_fast(arr_1d, w_len):
        pad_l = w_len // 2
        pad_r = w_len - 1 - pad_l
        padded = np.pad(arr_1d.astype(np.float64), (pad_l, pad_r), mode="edge")
        cs = np.cumsum(np.insert(padded, 0, 0.0))
        return ((cs[w_len:] - cs[:-w_len]) / float(w_len)).astype(np.float32)

    win = int(0.08 * sr)
    voice_env = np.sqrt(np.maximum(0.0, moving_avg_fast(np.mean(voice_track ** 2, axis=1), win)))
    speaking_mask = (voice_env > 0.025).astype(np.float32)
    smooth_win = int(0.28 * sr)
    speaking_smooth = moving_avg_fast(speaking_mask, smooth_win)
    bgm_gain = (0.44 * (1.0 - speaking_smooth) + 0.19 * speaking_smooth)[:, None]

    mixed = voice_track * 1.05 + bgm_audio * bgm_gain

    if include_sfx:
        # Generar SFX sintéticos limpios de estudio (whoosh en transiciones y pop en clics UI)
        for tr_t in [0.48, 4.80, 9.60, 14.40, 18.24]:
            i0 = max(0, int((tr_t - 0.08) * sr))
            dur_s = int(0.22 * sr)
            if i0 + dur_s < n_samples:
                t_arr = np.linspace(0.0, 1.0, dur_s, dtype=np.float32)
                env = np.maximum(0.0, np.sin(t_arr * math.pi)) ** 1.5
                sweep = np.sin(2.0 * math.pi * (160.0 + 420.0 * t_arr) * t_arr) * env * 0.14
                mixed[i0 : i0 + dur_s, 0] += sweep
                mixed[i0 : i0 + dur_s, 1] += sweep

        for clk_t in [2.40, 6.72, 11.52, 16.32, 22.08]:
            i0 = max(0, int(clk_t * sr))
            dur_s = int(0.045 * sr)
            if i0 + dur_s < n_samples:
                t_arr = np.linspace(0.0, 1.0, dur_s, dtype=np.float32)
                pop = np.sin(2.0 * math.pi * 1150.0 * t_arr) * np.exp(-t_arr * 8.0) * 0.18
                mixed[i0 : i0 + dur_s, 0] += pop
                mixed[i0 : i0 + dur_s, 1] += pop

    # Fade-out musical en los últimos 0.45s
    fout = int(0.45 * sr)
    mixed[-fout:] *= np.linspace(1.0, 0.0, fout, dtype=np.float32)[:, None]

    mixed = np.clip(mixed, -0.98, 0.98)
    raw_wav = WORK_DIR / "tmp_spot_guarderia_mix_raw.wav"
    sf.write(str(raw_wav), mixed, sr)

    # Normalización final broadcast a -14 LUFS con ffmpeg loudnorm
    subprocess.run(
        [
            FFMPEG_EXE, "-y",
            "-i", str(raw_wav),
            "-af", "loudnorm=I=-14:TP=-1.2:LRA=9",
            "-ar", "48000", "-ac", "2",
            out_mixed_wav,
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"  -> [AUDIO MASTERIZADO -14 LUFS + HOUSE 125 BPM] {out_mixed_wav}")


def main():
    print("=== ENSAMBLANDO SPOT PUBLICITARIO MASCOTAMÁS (TURNOS GUARDERÍA) 1080x1920 @ 30fps ===")

    # 1. Cargar frames de los 3 clips
    all_base_frames = []
    for seg in SEGMENTS_SPEC:
        frms = load_Segment_frames(seg)
        print(f"  -> Segmento {seg['name']} cargado: {len(frms)} frames ({seg['dst_start']:.2f}s -> {seg['dst_end']:.2f}s)")
        all_base_frames.extend(frms)

    while len(all_base_frames) < TOTAL_FRAMES:
        all_base_frames.append(all_base_frames[-1].copy())
    all_base_frames = all_base_frames[:TOTAL_FRAMES]

    # 2. Cargar imágenes reales de Turnos -> Guardería en caché
    img_cache = {}
    for c in HUD_CARDS_SPEC:
        for k in ("main_img", "side_img"):
            fn = c[k]
            if fn not in img_cache:
                img_cache[fn] = Image.open(MANUAL_DIR / fn).convert("RGBA")

    font_header_badge = ImageFont.truetype(FONT_EXTRABOLD, 30)
    font_header_sub = ImageFont.truetype(FONT_BOLD, 19)
    font_hud_title = ImageFont.truetype(FONT_EXTRABOLD, 23)
    font_hud_sub = ImageFont.truetype(FONT_BOLD, 18)
    font_sub_poppins = ImageFont.truetype(FONT_EXTRABOLD, 46)

    # 3. Preparar audio masterizado (con y sin SFX)
    wav_full = str(WORK_DIR / "spot_guarderia_master_audio_full.wav")
    wav_clean = str(WORK_DIR / "spot_guarderia_master_audio_clean.wav")
    build_synced_audio_track(wav_full, include_sfx=True)
    build_synced_audio_track(wav_clean, include_sfx=False)

    # 4. Renderizar video Clean Cinema (sin HUD ni subtítulos, con transiciones al beat) y Full Commercial Master
    tmp_clean_mp4 = str(WORK_DIR / "tmp_spot_guarderia_clean_vid.mp4")
    tmp_full_mp4 = str(WORK_DIR / "tmp_spot_guarderia_full_vid.mp4")

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    vw_clean = cv2.VideoWriter(tmp_clean_mp4, fourcc, FPS, (W, H))
    vw_full = cv2.VideoWriter(tmp_full_mp4, fourcc, FPS, (W, H))

    transition_times = [9.60, 18.24]

    for idx in range(TOTAL_FRAMES):
        t_sec = idx / float(FPS)
        base_bgr = all_base_frames[idx].copy()

        # Pulso de zoom cinematográfico sutil sincronizado al beat de 125 BPM (0.48s) en cortes principales
        for tr_t in transition_times:
            dt = abs(t_sec - tr_t)
            if dt < 0.18:
                u = 1.0 - (dt / 0.18)
                # Flash cálido de estudio y ligero punch-in en la transición
                zoom = 1.0 + 0.035 * u
                zw, zh = int(W * zoom), int(H * zoom)
                z_frm = cv2.resize(base_bgr, (zw, zh), interpolation=cv2.INTER_LINEAR)
                x0 = (zw - W) // 2
                y0 = (zh - H) // 2
                base_bgr = z_frm[y0 : y0 + H, x0 : x0 + W]
                glow = np.full_like(base_bgr, (245, 220, 255))
                base_bgr = cv2.addWeighted(base_bgr, 1.0 - 0.18 * u, glow, 0.18 * u, 0.0)

        vw_clean.write(base_bgr)

        # Composición Full Commercial Spot (Header + HUD Turnos Guardería + Subtítulos Poppins)
        rgb = cv2.cvtColor(base_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb).convert("RGBA")

        draw_top_header(pil_img, t_sec, font_header_badge, font_header_sub)
        draw_hud_callout_deck(pil_img, t_sec, img_cache, font_hud_title, font_hud_sub)
        draw_subtitles_poppins(pil_img, t_sec, font_sub_poppins)

        out_bgr = cv2.cvtColor(np.array(pil_img.convert("RGB")), cv2.COLOR_RGB2BGR)
        vw_full.write(out_bgr)

        if idx % 150 == 0 or idx == TOTAL_FRAMES - 1:
            print(f"  -> Renderizando frame {idx + 1}/{TOTAL_FRAMES} (t={t_sec:.2f}s)...")

    vw_clean.release()
    vw_full.release()

    # 5. Muxear H.264 de alta calidad (CRF 16) + AAC 192kbps
    out_full_name = "Spot Publicitario - MascotaMas Turnos Guarderia (Avatar Hombre VIP Casual + MacBook Pro e iPhone Reales + Musica House).mp4"
    out_clean_name = "Spot Publicitario - MascotaMas Turnos Guarderia (Avatar Hombre VIP Casual - Version Clean Cinema 1080p).mp4"

    final_full_editados = EDITADOS_DIR / out_full_name
    final_clean_editados = EDITADOS_DIR / out_clean_name
    final_full_spot = SPOT_DIR / "Spot_MascotaMas_Turnos_Guarderia_Avatar_Hombre_VIP_Master_1080p.mp4"
    final_clean_spot = SPOT_DIR / "Spot_MascotaMas_Turnos_Guarderia_Avatar_Hombre_VIP_Clean_1080p.mp4"

    for vid_in, aud_in, out_p1, out_p2 in [
        (tmp_full_mp4, wav_full, final_full_editados, final_full_spot),
        (tmp_clean_mp4, wav_clean, final_clean_editados, final_clean_spot),
    ]:
        subprocess.run(
            [
                FFMPEG_EXE, "-y",
                "-i", vid_in,
                "-i", aud_in,
                "-map", "0:v:0", "-map", "1:a:0",
                "-c:v", "libx264", "-preset", "fast", "-crf", "16",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart",
                str(out_p1),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        shutil.copy2(out_p1, out_p2)
        print(f"  -> [EXPORTADO] {out_p1} ({out_p1.stat().st_size // 1024} KB)")

    # Copiar el spot principal también a la raíz como reel_final.mp4 y ejecutar step5_verify.py
    shutil.copy2(final_full_editados, BASE_DIR / "reel_final.mp4")

    # 6. Generar grilla de verificación visual de 12 cuadros clave (verification_grid_spot_hombre_vip_guarderia.jpg)
    cap_v = cv2.VideoCapture(str(final_full_editados))
    sample_times = [0.8, 2.4, 3.8, 5.8, 7.8, 9.2, 10.8, 13.0, 15.6, 19.2, 22.4, 26.4]
    thumbs = []
    for st in sample_times:
        f_idx = min(TOTAL_FRAMES - 1, max(0, int(st * FPS)))
        cap_v.set(cv2.CAP_PROP_POS_FRAMES, f_idx)
        ok, frm = cap_v.read()
        if ok:
            th = cv2.resize(frm, (360, 640), interpolation=cv2.INTER_AREA)
            cv2.rectangle(th, (10, 595), (145, 632), (15, 23, 42), -1)
            cv2.putText(th, f"t={st:.1f}s", (18, 621), cv2.FONT_HERSHEY_SIMPLEX, 0.68, (92, 199, 242), 2)
            thumbs.append(th)
    cap_v.release()

    row1 = np.hstack(thumbs[:4])
    row2 = np.hstack(thumbs[4:8])
    row3 = np.hstack(thumbs[8:12])
    grid = np.vstack([row1, row2, row3])
    grid_path = WORK_DIR / "verification_grid_spot_hombre_vip_guarderia.jpg"
    cv2.imwrite(str(grid_path), grid, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    shutil.copy2(grid_path, BASE_DIR / "verification_grid.jpg")
    shutil.copy2(grid_path, ARTIFACTS_DIR / grid_path.name)
    print(f"  -> [VERIFICATION GRID GUARDADA] {grid_path}")


if __name__ == "__main__":
    main()
