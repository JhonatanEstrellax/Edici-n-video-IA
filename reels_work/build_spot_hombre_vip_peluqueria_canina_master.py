# -*- coding: utf-8 -*-
r"""
Ensambla y masteriza el Spot Publicitario Profesional de MascotaMás
(Sección: Turnos para Peluquerías Caninas)
protagonizado por el Avatar Hombre VIP Argentino con ropa de Groomer Canino profesional,
usando su MacBook Pro 16" y su iPhone 16 Pro Max, con acento argentino (es-AR),
lip-sync natural, música House (125 BPM) sincronizada a los cortes y transiciones,
capturas reales de `Manual De Usuario Vete y Marca` (Turnos · Peluquería Canina) y subtítulos Poppins.

Genera dos versiones en `1080x1920 @ 30fps`:
1. `Spot Publicitario - MascotaMas Turnos Peluqueria Canina (Avatar Groomer VIP + MacBook Pro e iPhone Reales + Musica House).mp4`
   (Producción completa con HUD interactivo de Turnos Peluquería Canina, cursor animado, subtítulos Poppins ExtraBold y SFX).
2. `Spot Publicitario - MascotaMas Turnos Peluqueria Canina (Avatar Groomer VIP - Version Clean Cinema 1080p).mp4`
   (Edición cinematográfica pura 1080p con voz argentina y música House sincronizada al beat).
"""
import os
import sys
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
SPOT_DIR = BASE_DIR / "assets" / "avatar_veterinario_hombre_vip" / "spot_peluqueria_canina"
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
# Clip 1: 0.00s -> 9.60s (20 beats, dur=9.60s) | src: 0.00s -> 9.60s (speech ends 9.12s)
# Clip 2: 9.60s -> 18.24s (18 beats, dur=8.64s) | src: 0.00s -> 8.64s (speech ends 7.66s)
# Clip 3: 18.24s -> 27.36s (19 beats, dur=9.12s) | src: 0.00s -> 9.12s (speech ends 8.38s)
TOTAL_DUR = 27.36
TOTAL_FRAMES = int(round(TOTAL_DUR * FPS))

SEGMENTS_SPEC = [
    {
        "name": "clip1",
        "path": str(SPOT_DIR / "spot_peluqueria_clip1_espalda_a_giro_10s.mp4"),
        "src_start": 0.00,
        "src_end": 9.60,
        "dst_start": 0.00,
        "dst_end": 9.60,
    },
    {
        "name": "clip2",
        "path": str(SPOT_DIR / "spot_peluqueria_clip2_espalda_agenda_y_sena_10s.mp4"),
        "src_start": 0.00,
        "src_end": 8.64,
        "dst_start": 9.60,
        "dst_end": 18.24,
    },
    {
        "name": "clip3",
        "path": str(SPOT_DIR / "spot_peluqueria_clip3_frente_groomer_vip_cta_10s.mp4"),
        "src_start": 0.00,
        "src_end": 9.12,
        "dst_start": 18.24,
        "dst_end": 27.36,
    },
]

# Bloques de Subtítulos sincronizados a los timestamps reales de Whisper
SUBTITLE_BLOCKS = [
    # Clip 1 (offset 0.00s, habla 2.64s -> 9.12s)
    {
        "start": 2.60,
        "end": 4.30,
        "words": [
            {"text": "¿TENÉS", "start": 2.64, "end": 3.24, "hl": False},
            {"text": "UNA", "start": 3.24, "end": 3.38, "hl": False},
            {"text": "PELUQUERÍA", "start": 3.38, "end": 3.86, "hl": True},
            {"text": "CANINA", "start": 3.86, "end": 4.30, "hl": True},
        ],
    },
    {
        "start": 4.30,
        "end": 5.95,
        "words": [
            {"text": "Y", "start": 4.30, "end": 4.50, "hl": False},
            {"text": "SEGUÍS", "start": 4.50, "end": 4.76, "hl": False},
            {"text": "DANDO", "start": 4.76, "end": 4.94, "hl": False},
            {"text": "TURNOS", "start": 4.94, "end": 5.32, "hl": True},
            {"text": "POR", "start": 5.32, "end": 5.48, "hl": False},
            {"text": "WHATSAPP?", "start": 5.48, "end": 5.95, "hl": True},
        ],
    },
    {
        "start": 6.30,
        "end": 9.25,
        "words": [
            {"text": "MIRÁ", "start": 6.34, "end": 6.58, "hl": False},
            {"text": "CÓMO", "start": 6.58, "end": 6.74, "hl": False},
            {"text": "ORGANIZO", "start": 6.74, "end": 7.22, "hl": False},
            {"text": "CADA", "start": 7.22, "end": 7.46, "hl": False},
            {"text": "BAÑO", "start": 7.46, "end": 7.82, "hl": True},
            {"text": "Y", "start": 7.82, "end": 7.90, "hl": False},
            {"text": "CORTE", "start": 7.90, "end": 8.42, "hl": True},
            {"text": "EN", "start": 8.42, "end": 8.56, "hl": False},
            {"text": "MASCOTAMÁS.", "start": 8.56, "end": 9.25, "hl": True},
        ],
    },
    # Clip 2 (offset +9.60s, habla 9.60s -> 17.26s)
    {
        "start": 9.60,
        "end": 13.30,
        "words": [
            {"text": "ASIGNÁS", "start": 9.60, "end": 10.30, "hl": True},
            {"text": "CADA", "start": 10.30, "end": 10.50, "hl": False},
            {"text": "TURNO", "start": 10.50, "end": 10.94, "hl": True},
            {"text": "POR", "start": 10.94, "end": 11.10, "hl": False},
            {"text": "PELUQUERO,", "start": 11.10, "end": 11.75, "hl": True},
            {"text": "DURACIÓN", "start": 12.02, "end": 12.48, "hl": True},
            {"text": "DEL", "start": 12.48, "end": 12.64, "hl": False},
            {"text": "SERVICIO,", "start": 12.64, "end": 13.30, "hl": True},
        ],
    },
    {
        "start": 13.55,
        "end": 15.25,
        "words": [
            {"text": "COBRÁS", "start": 13.64, "end": 13.90, "hl": True},
            {"text": "SEÑA", "start": 13.90, "end": 14.18, "hl": True},
            {"text": "CON", "start": 14.18, "end": 14.34, "hl": False},
            {"text": "MERCADO", "start": 14.34, "end": 14.64, "hl": True},
            {"text": "PAGO", "start": 14.64, "end": 15.25, "hl": True},
        ],
    },
    {
        "start": 15.25,
        "end": 17.50,
        "words": [
            {"text": "Y", "start": 15.25, "end": 15.44, "hl": False},
            {"text": "CONFIRMÁS", "start": 15.44, "end": 15.92, "hl": True},
            {"text": "POR", "start": 15.92, "end": 16.08, "hl": False},
            {"text": "WHATSAPP", "start": 16.08, "end": 16.48, "hl": True},
            {"text": "EN", "start": 16.48, "end": 16.96, "hl": False},
            {"text": "UN", "start": 16.96, "end": 17.08, "hl": False},
            {"text": "CLIC.", "start": 17.08, "end": 17.50, "hl": True},
        ],
    },
    # Clip 3 (offset +18.24s, habla 18.24s -> 26.62s)
    {
        "start": 18.24,
        "end": 20.50,
        "words": [
            {"text": "¡PASATE", "start": 18.24, "end": 19.12, "hl": True},
            {"text": "HOY", "start": 19.12, "end": 19.54, "hl": False},
            {"text": "A", "start": 19.54, "end": 19.66, "hl": False},
            {"text": "MASCOTAMÁS!", "start": 19.66, "end": 20.50, "hl": True},
        ],
    },
    {
        "start": 20.50,
        "end": 23.45,
        "words": [
            {"text": "MIGRAMOS", "start": 20.50, "end": 21.18, "hl": True},
            {"text": "TODA", "start": 21.18, "end": 21.46, "hl": False},
            {"text": "TU", "start": 21.46, "end": 21.68, "hl": False},
            {"text": "PELUQUERÍA", "start": 21.68, "end": 22.16, "hl": True},
            {"text": "CANINA", "start": 22.16, "end": 22.58, "hl": True},
            {"text": "EN", "start": 22.58, "end": 22.88, "hl": False},
            {"text": "EL", "start": 22.88, "end": 23.04, "hl": False},
            {"text": "DÍA", "start": 23.04, "end": 23.45, "hl": True},
        ],
    },
    {
        "start": 23.45,
        "end": 26.85,
        "words": [
            {"text": "Y", "start": 23.45, "end": 23.66, "hl": False},
            {"text": "100%", "start": 23.66, "end": 24.48, "hl": True},
            {"text": "GRATIS.", "start": 24.48, "end": 25.62, "hl": True},
            {"text": "¡ESCRIBINOS", "start": 25.62, "end": 26.28, "hl": True},
            {"text": "AHORA!", "start": 26.28, "end": 26.85, "hl": True},
        ],
    },
]

# Tarjetas Reales de Turnos -> Peluquería Canina sincronizadas al beat de 125 BPM (0.48s)
HUD_CARDS_SPEC = [
    {
        "start": 0.48,
        "end": 4.80,
        "badge": "TURNOS · PELUQUERÍA CANINA EN VIVO",
        "sub": "MacBook Pro 16\" + iPhone 16 Pro Max · gestion.mascotamas.com",
        "main_img": "03_Turnos_y_Agenda__08_Turnos_Peluqueria_Canina__01_Tablero_por_Groomer_y_Servicios__01_MacBook_Pro_Real.png",
        "side_img": "03_Turnos_y_Agenda__08_Turnos_Peluqueria_Canina__01_Tablero_por_Groomer_y_Servicios__02_iPhone_16_Pro_Max_Real.png",
        "click_t": 2.40,
        "click_rel": (0.64, 0.43),
        "beam_target": (765, 995),  # En clip1/clip2 la MacBook Pro física está a la derecha del mostrador
    },
    {
        "start": 4.80,
        "end": 9.60,
        "badge": "TABLERO POR PELUQUERO · BAÑO Y CORTE POR DURACIÓN",
        "sub": "Baño y Corte Razas Chicas (45m) · Razas Grandes (120m) · + Agendar",
        "main_img": "03_Turnos_y_Agenda__08_Turnos_Peluqueria_Canina__01_Tablero_por_Groomer_y_Servicios__04_Raw_Desktop.png",
        "side_img": "03_Turnos_y_Agenda__08_Turnos_Peluqueria_Canina__01_Tablero_por_Groomer_y_Servicios__02_iPhone_16_Pro_Max_Real.png",
        "click_t": 6.72,
        "click_rel": (0.66, 0.72),
        "beam_target": (765, 995),
    },
    {
        "start": 9.60,
        "end": 13.92,
        "badge": "CATÁLOGO DE SERVICIOS, DURACIÓN Y PRECIOS DE GROOMING",
        "sub": "Configurá Baño, Corte de Raza, Deslanado y Peluqueros Asignados",
        "main_img": "03_Turnos_y_Agenda__08_Turnos_Peluqueria_Canina__03_Catalogo_Servicios_Duracion_y_Precios_Grooming__04_Raw_Desktop.png",
        "side_img": "03_Turnos_y_Agenda__08_Turnos_Peluqueria_Canina__03_Catalogo_Servicios_Duracion_y_Precios_Grooming__02_iPhone_16_Pro_Max_Real.png",
        "click_t": 11.52,
        "click_rel": (0.71, 0.68),
        "beam_target": (765, 995),
    },
    {
        "start": 13.92,
        "end": 18.24,
        "badge": "AGENDA DIARIA · SEÑA MERCADO PAGO Y WHATSAPP 1 CLIC",
        "sub": "15:00 hs · Luna (Caniche) · En Peluquería · Seña MP ($15.000) · Ver Ficha",
        "main_img": "03_Turnos_y_Agenda__08_Turnos_Peluqueria_Canina__02_Agenda_Diaria_Turnos_Confirmados_y_Sena_MP__04_Raw_Desktop.png",
        "side_img": "03_Turnos_y_Agenda__08_Turnos_Peluqueria_Canina__04_Sena_Automatica_MercadoPago_Peluqueria__02_iPhone_16_Pro_Max_Real.png",
        "click_t": 15.84,
        "click_rel": (0.88, 0.87),
        "beam_target": (765, 995),
    },
    {
        "start": 18.24,
        "end": 27.36,
        "badge": "MIGRACIÓN 100% GRATIS EN EL DÍA · PASATE A MASCOTAMÁS",
        "sub": "Escribinos ahora · Toda tu Peluquería Canina y Turnos listos hoy",
        "main_img": "03_Turnos_y_Agenda__08_Turnos_Peluqueria_Canina__02_Agenda_Diaria_Turnos_Confirmados_y_Sena_MP__03_Combo_MacBook_e_iPhone.png",
        "side_img": "03_Turnos_y_Agenda__08_Turnos_Peluqueria_Canina__01_Tablero_por_Groomer_y_Servicios__01_MacBook_Pro_Real.png",
        "click_t": 22.08,
        "click_rel": (0.52, 0.54),
        "beam_target": (785, 980),
    },
]


def load_segment_frames(spec):
    cap = cv2.VideoCapture(spec["path"])
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
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
    bx1, by1, bx2, by2 = 44, 66, W - 44, 154
    draw.rounded_rectangle([bx1, by1, bx2, by2], radius=26, fill=(12, 18, 34, 218), outline=(168, 85, 247, 230), width=3)

    beat_phase = (t_sec / BEAT_SEC) % 1.0
    dot_r = int(8 + 3 * math.sin(beat_phase * math.pi * 2))
    draw.ellipse([bx1 + 26 - dot_r, by1 + 44 - dot_r, bx1 + 26 + dot_r, by1 + 44 + dot_r], fill=(52, 211, 153, 255))

    title_txt = "MASCOTAMÁS · TURNOS PELUQUERÍA"
    draw.text((bx1 + 50, by1 + 14), title_txt, font=font_badge, fill=(255, 255, 255, 255))
    sub_txt = "PELUQUERÍAS CANINAS · AGENDA POR GROOMER, SEÑA MP Y WHATSAPP"
    draw.text((bx1 + 50, by1 + 52), sub_txt, font=font_sub, fill=(242, 199, 92, 245))


def draw_hud_callout_deck(
    canvas_pil: Image.Image,
    t_sec: float,
    img_cache: dict,
    font_title: ImageFont.FreeTypeFont,
    font_sub: ImageFont.FreeTypeFont,
):
    active_card = None
    for c in HUD_CARDS_SPEC:
        if c["start"] <= t_sec < c["end"]:
            active_card = c
            break
    if active_card is None:
        return

    local_t = t_sec - active_card["start"]
    card_dur = active_card["end"] - active_card["start"]

    enter_u = min(1.0, local_t / 0.28)
    ease_u = 1.0 - pow(1.0 - enter_u, 3)
    y_offset = int((1.0 - ease_u) * 35)

    cx1, cy1, cx2, cy2 = 38, 1096 + y_offset, W - 38, 1502 + y_offset
    cw = cx2 - cx1

    draw = ImageDraw.Draw(canvas_pil, "RGBA")

    tx, ty = active_card["beam_target"]
    beam_pts = [(tx - 28, ty), (tx + 28, ty), (cx1 + int(cw * 0.78), cy1), (cx1 + int(cw * 0.34), cy1)]
    draw.polygon(beam_pts, fill=(168, 85, 247, int(42 * ease_u)))
    draw.line([(tx, ty), (cx1 + int(cw * 0.62), cy1)], fill=(242, 199, 92, int(185 * ease_u)), width=3)
    draw.ellipse([tx - 7, ty - 7, tx + 7, ty + 7], fill=(242, 199, 92, int(240 * ease_u)))

    beat_pulse = 0.5 + 0.5 * math.cos((t_sec / BEAT_SEC) * 2.0 * math.pi)
    border_col = (
        int(168 + (242 - 168) * beat_pulse * 0.4),
        int(85 + (199 - 85) * beat_pulse * 0.4),
        int(247 + (92 - 247) * beat_pulse * 0.4),
        245,
    )
    draw.rounded_rectangle([cx1, cy1, cx2, cy2], radius=24, fill=(13, 19, 36, 238), outline=border_col, width=3)

    draw.rounded_rectangle([cx1 + 3, cy1 + 3, cx2 - 3, cy1 + 68], radius=21, fill=(28, 37, 65, 245))
    draw.text((cx1 + 22, cy1 + 10), active_card["badge"], font=font_title, fill=(242, 199, 92, 255))
    draw.text((cx1 + 22, cy1 + 39), active_card["sub"], font=font_sub, fill=(220, 232, 255, 240))

    inner_y1 = cy1 + 74
    inner_h = (cy2 - 10) - inner_y1
    main_w = int(cw * 0.69)
    side_w = cw - main_w - 28

    main_im = img_cache[active_card["main_img"]]
    side_im = img_cache[active_card["side_img"]]

    pan_u = min(1.0, local_t / max(0.1, card_dur))
    mw_src, mh_src = main_im.size
    crop_scale = 1.0 - 0.08 * math.sin(pan_u * math.pi)
    c_w = int(mw_src * crop_scale)
    c_h = int(mh_src * crop_scale)
    x0 = int((mw_src - c_w) * 0.5 * pan_u)
    y0 = int((mh_src - c_h) * 0.35 * pan_u)
    main_crop = main_im.crop((x0, y0, x0 + c_w, y0 + c_h)).resize((main_w, inner_h), Image.Resampling.LANCZOS)

    m_mask = Image.new("L", (main_w, inner_h), 0)
    ImageDraw.Draw(m_mask).rounded_rectangle([0, 0, main_w - 1, inner_h - 1], radius=14, fill=255)
    canvas_pil.paste(main_crop, (cx1 + 12, inner_y1), m_mask)
    draw.rounded_rectangle([cx1 + 12, inner_y1, cx1 + 12 + main_w, inner_y1 + inner_h], radius=14, outline=(255, 255, 255, 90), width=2)

    side_resized = side_im.resize((side_w, inner_h), Image.Resampling.LANCZOS)
    s_mask = Image.new("L", (side_w, inner_h), 0)
    ImageDraw.Draw(s_mask).rounded_rectangle([0, 0, side_w - 1, inner_h - 1], radius=14, fill=255)
    sx1 = cx1 + 18 + main_w
    canvas_pil.paste(side_resized, (sx1, inner_y1), s_mask)
    draw.rounded_rectangle([sx1, inner_y1, sx1 + side_w, inner_y1 + inner_h], radius=14, outline=(168, 85, 247, 150), width=2)

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
    active_block = None
    for blk in SUBTITLE_BLOCKS:
        if blk["start"] <= t_sec <= blk["end"]:
            active_block = blk
            break
    if active_block is None:
        return

    draw = ImageDraw.Draw(canvas_pil, "RGBA")
    words = active_block["words"]

    mid = (len(words) + 1) // 2 if len(words) > 3 else len(words)
    lines = [words[:mid], words[mid:]] if len(words) > 3 else [words]

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

            for ox, oy in [(-3, -3), (3, -3), (-3, 3), (3, 3), (0, 4), (0, -4), (-4, 0), (4, 0)]:
                draw.text((x_cursor + ox, y_cursor + y_lift + oy), w["text"], font=font_sub, fill=(0, 0, 0, 245))
            draw.text((x_cursor, y_cursor + y_lift), w["text"], font=font_sub, fill=color)
            x_cursor += ww + space_w

        y_cursor += 82


def build_synced_audio_track(out_mixed_wav: str, include_sfx: bool = True):
    sr = 48000
    n_samples = int(round(TOTAL_DUR * sr))
    voice_track = np.zeros((n_samples, 2), dtype=np.float32)

    for seg in SEGMENTS_SPEC:
        tmp_seg_wav = WORK_DIR / f"tmp_pc_seg_{seg['name']}_48k.wav"
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

        peak = np.max(np.abs(seg_audio))
        if peak > 0.01:
            seg_audio = seg_audio * (0.88 / peak)

        fade_len = int(0.035 * sr)
        if len(seg_audio) > 2 * fade_len:
            fade_in = np.linspace(0.0, 1.0, fade_len, dtype=np.float32)[:, None]
            fade_out = np.linspace(1.0, 0.0, fade_len, dtype=np.float32)[:, None]
            seg_audio[:fade_len] *= fade_in
            seg_audio[-fade_len:] *= fade_out

        dst_i0 = int(round(seg["dst_start"] * sr))
        dst_i1 = min(n_samples, dst_i0 + len(seg_audio))
        voice_track[dst_i0:dst_i1] = seg_audio[: dst_i1 - dst_i0]

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

    bgm_peak = np.max(np.abs(bgm_audio))
    if bgm_peak > 0.01:
        bgm_audio = bgm_audio * (0.75 / bgm_peak)

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
        for tr_t in [0.48, 4.80, 9.60, 13.92, 18.24]:
            i0 = max(0, int((tr_t - 0.08) * sr))
            dur_s = int(0.22 * sr)
            if i0 + dur_s < n_samples:
                t_arr = np.linspace(0.0, 1.0, dur_s, dtype=np.float32)
                env = np.maximum(0.0, np.sin(t_arr * math.pi)) ** 1.5
                sweep = np.sin(2.0 * math.pi * (160.0 + 420.0 * t_arr) * t_arr) * env * 0.14
                mixed[i0 : i0 + dur_s, 0] += sweep
                mixed[i0 : i0 + dur_s, 1] += sweep

        for clk_t in [2.40, 6.72, 11.52, 15.84, 22.08]:
            i0 = max(0, int(clk_t * sr))
            dur_s = int(0.045 * sr)
            if i0 + dur_s < n_samples:
                t_arr = np.linspace(0.0, 1.0, dur_s, dtype=np.float32)
                pop = np.sin(2.0 * math.pi * 1150.0 * t_arr) * np.exp(-t_arr * 8.0) * 0.18
                mixed[i0 : i0 + dur_s, 0] += pop
                mixed[i0 : i0 + dur_s, 1] += pop

    fout = int(0.45 * sr)
    mixed[-fout:] *= np.linspace(1.0, 0.0, fout, dtype=np.float32)[:, None]

    mixed = np.clip(mixed, -0.98, 0.98)
    raw_wav = WORK_DIR / "tmp_spot_peluqueria_canina_mix_raw.wav"
    sf.write(str(raw_wav), mixed, sr)

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
    print("=== ENSAMBLANDO SPOT PUBLICITARIO MASCOTAMÁS (TURNOS - PELUQUERÍA CANINA) 1080x1920 @ 30fps ===")

    all_base_frames = []
    for seg in SEGMENTS_SPEC:
        frms = load_segment_frames(seg)
        print(f"  -> Segmento {seg['name']} cargado: {len(frms)} frames ({seg['dst_start']:.2f}s -> {seg['dst_end']:.2f}s)")
        all_base_frames.extend(frms)

    while len(all_base_frames) < TOTAL_FRAMES:
        all_base_frames.append(all_base_frames[-1].copy())
    all_base_frames = all_base_frames[:TOTAL_FRAMES]

    img_cache = {}
    for c in HUD_CARDS_SPEC:
        for k in ("main_img", "side_img"):
            fn = c[k]
            if fn not in img_cache:
                img_cache[fn] = Image.open(MANUAL_DIR / fn).convert("RGBA")

    font_header_badge = ImageFont.truetype(FONT_EXTRABOLD, 29)
    font_header_sub = ImageFont.truetype(FONT_BOLD, 18)
    font_hud_title = ImageFont.truetype(FONT_EXTRABOLD, 23)
    font_hud_sub = ImageFont.truetype(FONT_BOLD, 18)
    font_sub_poppins = ImageFont.truetype(FONT_EXTRABOLD, 45)

    wav_full = str(WORK_DIR / "spot_peluqueria_canina_master_audio_full.wav")
    wav_clean = str(WORK_DIR / "spot_peluqueria_canina_master_audio_clean.wav")
    build_synced_audio_track(wav_full, include_sfx=True)
    build_synced_audio_track(wav_clean, include_sfx=False)

    tmp_clean_mp4 = str(WORK_DIR / "tmp_spot_peluqueria_canina_clean_vid.mp4")
    tmp_full_mp4 = str(WORK_DIR / "tmp_spot_peluqueria_canina_full_vid.mp4")

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    vw_clean = cv2.VideoWriter(tmp_clean_mp4, fourcc, FPS, (W, H))
    vw_full = cv2.VideoWriter(tmp_full_mp4, fourcc, FPS, (W, H))

    transition_times = [9.60, 18.24]

    for idx in range(TOTAL_FRAMES):
        t_sec = idx / float(FPS)
        base_bgr = all_base_frames[idx].copy()

        for tr_t in transition_times:
            dt = abs(t_sec - tr_t)
            if dt < 0.18:
                u = 1.0 - (dt / 0.18)
                zoom = 1.0 + 0.035 * u
                zw, zh = int(W * zoom), int(H * zoom)
                z_frm = cv2.resize(base_bgr, (zw, zh), interpolation=cv2.INTER_LINEAR)
                x0 = (zw - W) // 2
                y0 = (zh - H) // 2
                base_bgr = z_frm[y0 : y0 + H, x0 : x0 + W]
                glow = np.full_like(base_bgr, (245, 220, 255))
                base_bgr = cv2.addWeighted(base_bgr, 1.0 - 0.18 * u, glow, 0.18 * u, 0.0)

        vw_clean.write(base_bgr)

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

    out_full_name = "Spot Publicitario - MascotaMas Turnos Peluqueria Canina (Avatar Groomer VIP + MacBook Pro e iPhone Reales + Musica House).mp4"
    out_clean_name = "Spot Publicitario - MascotaMas Turnos Peluqueria Canina (Avatar Groomer VIP - Version Clean Cinema 1080p).mp4"

    final_full_editados = EDITADOS_DIR / out_full_name
    final_clean_editados = EDITADOS_DIR / out_clean_name
    final_full_spot = SPOT_DIR / "Spot_MascotaMas_Turnos_Peluqueria_Canina_Avatar_Groomer_VIP_Master_1080p.mp4"
    final_clean_spot = SPOT_DIR / "Spot_MascotaMas_Turnos_Peluqueria_Canina_Avatar_Groomer_VIP_Clean_1080p.mp4"

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

    shutil.copy2(final_full_editados, BASE_DIR / "reel_final.mp4")

    cap_v = cv2.VideoCapture(str(final_full_editados))
    sample_times = [0.8, 3.0, 4.8, 6.8, 8.6, 10.6, 12.4, 14.4, 16.4, 19.2, 22.2, 25.8]
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
    grid_path = WORK_DIR / "verification_grid_spot_hombre_vip_peluqueria_canina.jpg"
    cv2.imwrite(str(grid_path), grid, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    shutil.copy2(grid_path, BASE_DIR / "verification_grid.jpg")
    shutil.copy2(grid_path, ARTIFACTS_DIR / grid_path.name)
    print(f"  -> [VERIFICATION GRID GUARDADA] {grid_path}")


if __name__ == "__main__":
    main()
