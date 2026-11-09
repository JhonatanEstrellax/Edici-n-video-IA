import os
import re
import sys
import glob
import json
import math
import shutil
import subprocess
import numpy as np
import soundfile as sf
import cv2
from PIL import Image, ImageDraw, ImageFont

def _build_url_prefix_delta():
    base_bg_rgb = (224, 234, 224)
    base_bg_bgr = np.array([224, 234, 224], dtype=np.int16)
    font = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 21)
    pil_strip = Image.new("RGB", (400, 30), base_bg_rgb)
    draw = ImageDraw.Draw(pil_strip)
    x_cur = 8
    y_txt = 0
    draw.text((x_cur, y_txt), "https://", font=font, fill=(95, 99, 104))
    x_cur = draw.textbbox((x_cur, y_txt), "https://", font=font)[2]
    draw.text((x_cur, y_txt), "gestion.mascotamas.com", font=font, fill=(31, 31, 31))
    end_x = draw.textbbox((x_cur, y_txt), "gestion.mascotamas.com", font=font)[2] + 1
    strip_bgr = cv2.cvtColor(np.array(pil_strip)[:, :end_x], cv2.COLOR_RGB2BGR)
    return strip_bgr.astype(np.int16) - base_bg_bgr

URL_PREFIX_DELTA = _build_url_prefix_delta()
URL_PREFIX_W = URL_PREFIX_DELTA.shape[1]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK_DIR = os.path.join(BASE_DIR, "instructivos_work")
FFMPEG_BIN = os.path.join(BASE_DIR, "bin", "ffmpeg", "ffmpeg.exe")
TEMPLATE_HTML = os.path.join(BASE_DIR, "templates", "tutorial_desktop_mg.html")
NODE_RENDER_SCRIPT = os.path.join(BASE_DIR, "scripts", "render_tutorial_desktop.js")

SOURCE_VIDEO = os.path.join(WORK_DIR, "MascotaMas - VeteBosco - Google Chrome 2026-11-08 10-28-13.mp4")
RAW_TRANSCRIPT = os.path.join(WORK_DIR, "raw_transcript.json")
WAV_44K = os.path.join(WORK_DIR, "audio_44k.wav")

# Exact clock ratio between video stream (383.550533s) and audio stream (406.548375s)
VIDEO_DURATION_SEC = 383.550533
AUDIO_DURATION_SEC = 406.548375
AV_CLOCK_RATIO = VIDEO_DURATION_SEC / AUDIO_DURATION_SEC  # 0.9434315

# Word-level transcription corrections by word_id (1-indexed across all 841 words)
WORD_OVERRIDES = {
    29: "",               # "los" -> merged into MascotaMás
    30: "",               # "costos" -> merged into MascotaMás
    31: "MascotaMás.",    # "más." -> "MascotaMás."
    56: "el",             # "la" -> "el"
    57: "link",           # "ley" -> "link"
    105: "seña",          # "escena" -> "seña"
    107: "Mercado",       # "mercado" -> "Mercado"
    108: "Pago,",         # "pago," -> "Pago,"
    147: "Cupos",         # "tipos" -> "Cupos"
    149: "Horario.",      # "horario." -> "Horario."
    317: "grilla de",     # "grillo" -> "grilla de"
    387: "público o",     # "público" -> "público o"
    398: "por",           # "de" -> "por"
    399: "Mercado",       # "forma" -> "Mercado"
    400: "Pago",          # "acabado" -> "Pago"
    444: "y",             # "de" -> "y" (baño y corte)
    560: "veterinaria o", # "veterinario," -> "veterinaria o"
    720: "turnos",        # "turno" -> "turnos"
    749: "cobro",         # "cobrado" -> "cobro"
}

HIGHLIGHT_KEYWORDS = {
    "cuatro", "4", "12", "15", "30", "45", "90", "uno", "simples", "clásico",
    "mascotamás", "mascotamas", "tarifa", "precio", "visible", "título", "descripción",
    "público", "interno", "privado", "link", "turnos", "seña", "señas", "mercado", "pago",
    "duración", "horas", "horarios", "días", "cupos", "cupo", "horario", "mascota",
    "mascotas", "simultáneamente", "guarderías", "guardería", "diurnas", "paseadores",
    "internaciones", "descontando", "servicios", "servicio", "profesionales", "profesional",
    "grilla", "automático", "automáticamente", "huecos", "muertos", "peluquería",
    "veterinaria", "vacunación", "consulta", "control", "minutos", "categoría",
    "bloquear", "licencias", "francos", "editar", "estadía", "mínimo", "máximo",
    "anticipación", "exterior", "interior", "sector", "navidad", "nuevo"
}


def refine_word_boundaries(audio: np.ndarray, sr: int, raw_start: float, raw_end: float, threshold_db: float = -38.0):
    s_idx = max(0, int(raw_start * sr))
    e_idx = min(len(audio), int(raw_end * sr))
    if e_idx <= s_idx + int(0.02 * sr):
        return raw_start, raw_end, -45.0

    seg = audio[s_idx:e_idx]
    rms_total = float(np.sqrt(np.mean(seg ** 2) + 1e-12))
    rms_db = 20.0 * math.log10(max(rms_total, 1e-6))

    win = max(1, int(0.005 * sr))
    n_wins = len(seg) // win
    if n_wins < 3:
        return raw_start, raw_end, round(rms_db, 2)

    frames = seg[: n_wins * win].reshape(n_wins, win)
    win_rms = np.sqrt(np.mean(frames ** 2, axis=1) + 1e-12)
    win_db = 20.0 * np.log10(np.maximum(win_rms, 1e-6))

    peak_db = float(np.max(win_db))
    active_thresh = max(threshold_db, peak_db - 18.0)
    active_indices = np.where(win_db >= active_thresh)[0]

    if len(active_indices) > 0:
        first_win = int(active_indices[0])
        last_win = int(active_indices[-1])
        real_start = raw_start + (first_win * win) / sr
        real_end = min(raw_end, raw_start + ((last_win + 2) * win) / sr)
        if real_end - real_start < 0.04:
            real_end = min(raw_end, real_start + 0.06)
    else:
        real_start, real_end = raw_start, raw_end

    rs_idx = max(0, int(real_start * sr))
    re_idx = min(len(audio), int(real_end * sr))
    if re_idx > rs_idx:
        active_seg = audio[rs_idx:re_idx]
        active_rms = float(np.sqrt(np.mean(active_seg ** 2) + 1e-12))
        rms_db = 20.0 * math.log10(max(active_rms, 1e-6))

    return round(real_start, 4), round(real_end, 4), round(rms_db, 2)


def get_scene_definitions():
    return [
        {
            "scene_id": 1,
            "seg_range": (1, 3),
            "chapter_index": 1,
            "is_new_chapter": True,
            "graphic_config": {
                "chapter_index": 1,
                "badge": "NUEVA VERSIÓN · 4 MODALIDADES",
                "title": "4 Tipos de Calendarios en MascotaMás",
                "subtitle": "Elegí el modelo operativo ideal para cada área de tu negocio pet.",
                "items": [
                    {"icon": "1", "title": "Turnos Simples (1 a 1)", "tag": "CLÁSICO", "desc": "Un turno por horario con duración fija para consultorio."},
                    {"icon": "2", "title": "Cupos por Horario", "tag": "GRUPAL", "desc": "Múltiples mascotas en simultáneo por franja."},
                    {"icon": "3", "title": "Servicios y Profesionales", "tag": "EQUIPO", "desc": "Prestaciones de distinta duración asignadas a tu staff."},
                    {"icon": "4", "title": "Guardería por Estadía", "tag": "DÍAS", "desc": "Reservas por rango de fechas (Ingreso → Egreso)."}
                ]
            }
        },
        {
            "scene_id": 2,
            "seg_range": (4, 6),
            "chapter_index": 1,
            "is_new_chapter": False,
            "graphic_config": {
                "chapter_index": 1,
                "template": "before_after",
                "badge": "TIPO 1 · TURNOS SIMPLES 1 A 1",
                "title": "Tarifa de Referencia del Turno",
                "subtitle": "Vos decidís si mostrar o no el valor de la consulta en el link público.",
                "before_badge": "SI SE DEJA VACÍO ($0)",
                "before_title": "Tarifa Oculta en el Link",
                "before_desc": "El tutor reserva su turno sin ver un monto de referencia.",
                "after_badge": "SI SE COLOCA UN VALOR",
                "after_title": "Precio Visible al Reservar",
                "after_desc": "El valor configurado se informa claramente en el link de turnos.",
                "tip_text": "La tarifa de referencia es 100% optativa."
            }
        },
        {
            "scene_id": 3,
            "seg_range": (7, 11),
            "chapter_index": 1,
            "is_new_chapter": False,
            "graphic_config": {
                "chapter_index": 1,
                "badge": "TIPO 1 · REGLAS Y DISPONIBILIDAD",
                "title": "Visibilidad, Seña y Duración",
                "subtitle": "Personalizá los datos y horarios de atención del consultorio.",
                "metric_value": "Máx. 4h",
                "metric_label": "Duración máxima permitida por turno en modalidad 1 a 1",
                "items": [
                    {"icon": "🌐", "title": "Público o Uso Interno", "tag": "ACCESO", "desc": "Visible en el link de turnos o privado solo para recepción."},
                    {"icon": "💳", "title": "Seña con Mercado Pago", "tag": "COBROS", "desc": "Habilitá el cobro automático de seña para confirmar."},
                    {"icon": "🕒", "title": "Días y Franjas Horarias", "tag": "AGENDA", "desc": "Definí qué días y en qué horarios se ofrecen turnos."}
                ]
            }
        },
        {
            "scene_id": 4,
            "seg_range": (12, 15),
            "chapter_index": 2,
            "is_new_chapter": True,
            "graphic_config": {
                "chapter_index": 2,
                "badge": "TIPO 2 · CUPOS POR HORARIO",
                "title": "Múltiples Mascotas en Simultáneo",
                "subtitle": "Turnos de duración fija que admiten varias mascotas en el mismo horario.",
                "items": [
                    {"icon": "☀️", "title": "Guarderías Diurnas", "tag": "DIURNO", "desc": "Controlá cuántos ingresos simultáneos recibís por franja."},
                    {"icon": "🦮", "title": "Paseadores Caninos", "tag": "GRUPOS", "desc": "Organizá salidas grupales con límite máximo de perros."},
                    {"icon": "🏥", "title": "Internaciones en Clínica", "tag": "CLÍNICA", "desc": "Administrá la disponibilidad de jaulas o plazas por turno."}
                ],
                "tip_text": "Ideal cuando recibís más de una mascota al mismo tiempo."
            }
        },
        {
            "scene_id": 5,
            "seg_range": (16, 19),
            "chapter_index": 2,
            "is_new_chapter": False,
            "graphic_config": {
                "chapter_index": 2,
                "badge": "TIPO 2 · CONTROL AUTOMÁTICO",
                "title": "Cupo Total y Descuento en Vivo",
                "subtitle": "El sistema controla automáticamente la capacidad de cada franja.",
                "items": [
                    {"icon": "1", "title": "Cupo Total por Horario", "tag": "LÍMITE", "desc": "Cantidad máxima de mascotas permitidas en simultáneo."},
                    {"icon": "2", "title": "Precio por Mascota", "tag": "OPCIONAL", "desc": "Si no colocás un valor, no se mostrará en el link."},
                    {"icon": "3", "title": "Descuento Automático", "tag": "TIEMPO REAL", "desc": "Cada turno tomado descuenta 1 cupo hasta completar el límite."}
                ]
            }
        },
        {
            "scene_id": 6,
            "seg_range": (20, 22),
            "chapter_index": 2,
            "is_new_chapter": False,
            "graphic_config": {
                "chapter_index": 2,
                "badge": "TIPO 2 · DURACIÓN EXTENDIDA",
                "title": "Datos, Señas y Hasta 12 Horas",
                "subtitle": "Configuración general para agendas grupales o de jornada completa.",
                "metric_value": "Hasta 12h",
                "metric_label": "Permite turnos de hasta 12 horas para cubrir jornadas diurnas",
                "items": [
                    {"icon": "📝", "title": "Título y Descripción", "tag": "INFO", "desc": "Indicaciones y requisitos visibles para el tutor."},
                    {"icon": "🔒", "title": "Público o Privado + Señas", "tag": "RESERVA", "desc": "Elegí visibilidad en el link y cobro de seña opcional."},
                    {"icon": "📅", "title": "Días y Horarios Activos", "tag": "GRILLA", "desc": "Seleccioná los días de atención de la agenda."}
                ]
            }
        },
        {
            "scene_id": 7,
            "seg_range": (23, 28),
            "chapter_index": 3,
            "is_new_chapter": True,
            "graphic_config": {
                "chapter_index": 3,
                "template": "before_after",
                "badge": "TIPO 3 · SERVICIOS Y PROFESIONALES",
                "title": "Grilla Automática Sin Huecos",
                "subtitle": "Combiná servicios de distinta duración con uno o varios profesionales.",
                "before_badge": "ELECCIÓN DE PROFESIONAL",
                "before_title": "Específico o Automático",
                "before_desc": "El cliente elige profesional o el sistema asigna según disponibilidad.",
                "after_badge": "INTERVALO RECOMENDADO",
                "after_title": "Grilla Automática Sin Huecos",
                "after_desc": "Ofrece bloques consecutivos exactos para evitar tiempos muertos.",
                "tip_text": "Recomendado: Intervalo Automático para optimizar tu agenda."
            }
        },
        {
            "scene_id": 8,
            "seg_range": (29, 32),
            "chapter_index": 3,
            "is_new_chapter": False,
            "graphic_config": {
                "chapter_index": 3,
                "badge": "TIPO 3 · PASO 1: CREAR AGENDA",
                "title": "Peluquería o Especialidades",
                "subtitle": "Configurá los datos base del calendario antes de cargar el catálogo.",
                "items": [
                    {"icon": "✂️", "title": "Título del Calendario", "tag": "EJEMPLO", "desc": "Ej: «Servicios de Peluquería» o «Servicios de Veterinaria»."},
                    {"icon": "💳", "title": "Visibilidad y Mercado Pago", "tag": "SEÑAS", "desc": "Definí si es público o interno y si requiere seña."},
                    {"icon": "⚙️", "title": "Configurar Servicios y Staff", "tag": "PASO 2", "desc": "Una vez creado, abrí el catálogo desde la tarjeta."}
                ]
            }
        },
        {
            "scene_id": 9,
            "seg_range": (33, 40),
            "chapter_index": 3,
            "is_new_chapter": False,
            "graphic_config": {
                "chapter_index": 3,
                "badge": "TIPO 3 · PASO 2: CATÁLOGO DE SERVICIOS",
                "title": "Alta de Servicios a Medida",
                "subtitle": "Cada prestación tiene su propia duración, precio y profesionales.",
                "items": [
                    {"icon": "⏱️", "title": "Duración Personalizada", "tag": "15 / 30 / 45m", "desc": "Ej: Baño razas pequeñas, Corte, Vacunación o Consulta."},
                    {"icon": "🏷️", "title": "Categoría y Precio Base", "tag": "CATÁLOGO", "desc": "Agrupación organizativa interna y tarifa opcional."},
                    {"icon": "👩‍⚕️", "title": "Profesional y Bloqueos", "tag": "ASIGNACIÓN", "desc": "Asigná a un profesional o a cualquiera disponible y bloqueá fechas."}
                ]
            }
        },
        {
            "scene_id": 10,
            "seg_range": (41, 47),
            "chapter_index": 3,
            "is_new_chapter": False,
            "graphic_config": {
                "chapter_index": 3,
                "badge": "TIPO 3 · PASO 3: EQUIPO Y EDICIÓN",
                "title": "Gestión de Profesionales y Francos",
                "subtitle": "Administrá la disponibilidad individual de cada integrante de tu equipo.",
                "items": [
                    {"icon": "👤", "title": "Alta de Nuevo Profesional", "tag": "EQUIPO", "desc": "Cargá nombre, especialidad y color identificador."},
                    {"icon": "🗓️", "title": "Horario General o Propio", "tag": "JORNADA", "desc": "Toda la franja del local o días y horarios particulares."},
                    {"icon": "🏖️", "title": "Licencias y Edición Rápida", "tag": "GESTIÓN", "desc": "Bloqueá francos puntuales y editá servicios en 1 clic."}
                ]
            }
        },
        {
            "scene_id": 11,
            "seg_range": (48, 55),
            "chapter_index": 4,
            "is_new_chapter": True,
            "graphic_config": {
                "chapter_index": 4,
                "badge": "TIPO 4 · CALENDARIO DE GUARDERÍA",
                "title": "Reservas por Rango de Fechas",
                "subtitle": "El tutor selecciona la fecha de ingreso y egreso para la estadía.",
                "metric_value": "90 Días",
                "metric_label": "Ejemplo de anticipación máxima hacia adelante para reservar",
                "items": [
                    {"icon": "📆", "title": "Mínimo y Máximo de Días", "tag": "ESTADÍA", "desc": "Definí la duración mínima y máxima permitida."},
                    {"icon": "⏩", "title": "Anticipación Máxima", "tag": "FUTURO", "desc": "Hasta cuántos días hacia adelante se puede reservar."},
                    {"icon": "💳", "title": "Visibilidad y Señas", "tag": "RESERVA", "desc": "Público o interno con cobro de seña opcional."}
                ]
            }
        },
        {
            "scene_id": 12,
            "seg_range": (56, 62),
            "chapter_index": 4,
            "is_new_chapter": False,
            "graphic_config": {
                "chapter_index": 4,
                "badge": "TIPO 4 · SECTORES Y FERIADOS",
                "title": "Categorías de Alojamiento y Bloqueos",
                "subtitle": "Configurá tus sectores disponibles y bloqueá fechas sin atención.",
                "items": [
                    {"icon": "🏡", "title": "Sectores (Interior / Exterior)", "tag": "CATEGORÍAS", "desc": "Creá cada sector de hospedaje por separado."},
                    {"icon": "🐾", "title": "Cupo Máximo y Tarifa Diaria", "tag": "PLAZAS", "desc": "Definí cuántas mascotas entran por sector y el valor por día."},
                    {"icon": "🔒", "title": "Bloqueo de Feriados", "tag": "NAVIDAD / AÑO NUEVO", "desc": "Bloqueá fechas o rangos para que no reciban reservas."}
                ],
                "tip_text": "Los días bloqueados quedan deshabilitados en el link."
            }
        }
    ]


def normalize_clean(w: str) -> str:
    return re.sub(r"[^\wáéíóúüñÁÉÍÓÚÜÑ0-9%]", "", w.lower()).strip()


def build_desktop_subtitle_blocks(edited_words: list):
    """
    Groups edited words into crisp desktop subtitle blocks (3 to 7 words, max 42 chars per line, 1-2 lines)
    for the dedicated 1110x110 bottom dock center stage.
    """
    max_chars = 42
    min_w = 3
    max_w = 6
    blocks = []
    curr = []

    for idx, w in enumerate(edited_words):
        disp = w.get("subtitle_text", w["word"]).replace(",", "").replace(".", "").strip()
        if not disp:
            continue
        w_copy = dict(w)
        w_copy["display"] = disp
        curr.append(w_copy)

        next_w = edited_words[idx + 1] if idx + 1 < len(edited_words) else None
        gap_to_next = (next_w["edited_start"] - w["edited_end"]) if next_w else 999.0
        total_chars = sum(len(x["display"]) for x in curr) + max(0, len(curr) - 1)
        raw_word_str = w.get("subtitle_text", w["word"])

        should_close = False
        if len(curr) >= max_w or total_chars >= max_chars:
            should_close = True
        elif (
            (next_w and next_w.get("scene_id") != w.get("scene_id"))
            or any(ch in raw_word_str for ch in ".?!")
            or gap_to_next > 0.22
        ):
            should_close = True
        elif len(curr) >= min_w and (gap_to_next > 0.14 or "," in raw_word_str):
            should_close = True
        elif next_w is None:
            should_close = True

        if should_close:
            lines = []
            current_line = []
            for item in curr:
                cand_str = " ".join([x["display"] for x in current_line] + [item["display"]])
                if current_line and len(cand_str) > max_chars:
                    lines.append(current_line)
                    current_line = [item]
                else:
                    current_line.append(item)
            if current_line:
                lines.append(current_line)
            if len(lines) > 2:
                mid = max(1, len(curr) // 2)
                lines = [curr[:mid], curr[mid:]]

            has_bounce = any(x.get("trigger_bounce", False) for x in curr)
            bounce_time = next(
                (x["edited_start"] for x in curr if x.get("trigger_bounce", False)),
                curr[0]["edited_start"]
            )

            blocks.append({
                "block_id": len(blocks) + 1,
                "scene_id": curr[0].get("scene_id", 1),
                "start": round(curr[0]["edited_start"], 4),
                "end": round(curr[-1]["edited_end"], 4),
                "lines": [
                    [
                        {
                            "word_id": x["word_id"],
                            "text": x["display"],
                            "is_yellow": x.get("is_yellow", False),
                            "trigger_bounce": x.get("trigger_bounce", False),
                            "start": x["edited_start"],
                            "end": x["edited_end"]
                        }
                        for x in ln
                    ]
                    for ln in lines
                ],
                "has_bounce": has_bounce,
                "bounce_start": round(bounce_time, 4)
            })
            curr = []

    return blocks


def build_edit_plan():
    plan_path = os.path.join(WORK_DIR, "desktop_edit_plan.json")
    if os.path.exists(plan_path):
        with open(plan_path, "r", encoding="utf-8") as f:
            return json.load(f)
    print("[STEP 1 & 2] Refining 841 word timestamps & building desktop tutorial plan...")
    audio, sr = sf.read(WAV_44K, dtype="float32")
    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)
    orig_dur = round(len(audio) / sr, 3)

    with open(RAW_TRANSCRIPT, "r", encoding="utf-8") as f:
        raw = json.load(f)

    scene_defs = get_scene_definitions()
    seg_to_scene = {}
    for sc in scene_defs:
        s1, s2 = sc["seg_range"]
        for s_id in range(s1, s2 + 1):
            seg_to_scene[s_id] = sc["scene_id"]

    words = []
    wid = 1
    for s in raw["segments"]:
        s_id = s["id"]
        sc_id = seg_to_scene.get(s_id, 12)
        for w in s["words"]:
            rs, re_t, r_db = refine_word_boundaries(audio, sr, w["start"], w["end"])
            sub_txt = WORD_OVERRIDES.get(wid, w["word"])
            words.append({
                "word_id": wid,
                "segment_id": s_id,
                "scene_id": sc_id,
                "word": w["word"],
                "subtitle_text": sub_txt,
                "raw_start": w["start"],
                "real_start": rs,
                "end": re_t,
                "duration": round(re_t - rs, 4),
                "rms_db": r_db
            })
            wid += 1

    # Cut pauses > 0.22s; keep natural micro-pauses <= 0.22s within the same scene
    pad_before = 0.06
    pad_after = 0.07
    max_pause = 0.22
    crossfade_sec = 0.012

    raw_intervals = []
    for i, w in enumerate(words):
        is_first = (i == 0)
        is_last = (i == len(words) - 1)
        s_t = max(0.0, w["real_start"] - (0.45 if is_first else pad_before))
        e_t = min(orig_dur, w["end"] + (0.35 if is_last else pad_after))
        if e_t - s_t < 0.12:
            e_t = min(orig_dur, s_t + 0.12)
        raw_intervals.append({
            "start": round(s_t, 4),
            "end": round(e_t, 4),
            "words": [w],
            "scene_id": w["scene_id"]
        })

    segments = []
    for iv in raw_intervals:
        if not segments:
            segments.append(iv)
            continue
        prev = segments[-1]
        gap = iv["start"] - prev["end"]
        if gap <= max_pause and iv["scene_id"] == prev["scene_id"]:
            prev["end"] = max(prev["end"], iv["end"])
            prev["words"].extend(iv["words"])
        else:
            segments.append(iv)

    edited_cursor = 0.0
    edited_segments = []
    edited_words = []

    for seg_idx, seg in enumerate(segments):
        src_s = seg["start"]
        src_e = seg["end"]
        dur = round(src_e - src_s, 4)
        if seg_idx > 0:
            edited_cursor = max(0.0, edited_cursor - crossfade_sec)
        ed_s = round(edited_cursor, 4)
        ed_e = round(ed_s + dur, 4)

        edited_segments.append({
            "segment_id": seg_idx + 1,
            "scene_id": seg["scene_id"],
            "source_start": src_s,
            "source_end": src_e,
            "duration": dur,
            "edited_start": ed_s,
            "edited_end": ed_e,
            "word_ids": [w["word_id"] for w in seg["words"]]
        })

        for w in seg["words"]:
            w_rel_s = max(0.0, w["real_start"] - src_s)
            w_rel_e = min(dur, w["end"] - src_s)
            w_ed_s = round(ed_s + w_rel_s, 4)
            w_ed_e = round(max(w_ed_s + 0.06, ed_s + w_rel_e), 4)
            w_item = dict(w)
            w_item["edited_start"] = w_ed_s
            w_item["edited_end"] = w_ed_e
            edited_words.append(w_item)

        edited_cursor = ed_e

    total_edited_duration = round(edited_cursor, 4)

    # Highlight & Bounce scheduling (every ~5.0s)
    last_bounce_t = -999.0
    for w in edited_words:
        sub_t = w.get("subtitle_text", w["word"])
        tokens = [normalize_clean(tok) for tok in sub_t.split() if normalize_clean(tok)]
        is_hl = any(tok in HIGHLIGHT_KEYWORDS or any(ch.isdigit() for ch in tok) for tok in tokens)
        w["is_yellow"] = is_hl
        if is_hl and (w["edited_start"] - last_bounce_t >= 5.0):
            w["trigger_bounce"] = True
            last_bounce_t = w["edited_start"]
        else:
            w["trigger_bounce"] = False

    subtitle_blocks = build_desktop_subtitle_blocks(edited_words)

    # Build Edited Timeline Scenes
    edited_scenes = []
    for idx, sc in enumerate(scene_defs):
        sc_words = [w for w in edited_words if w["scene_id"] == sc["scene_id"]]
        s_start = 0.0 if idx == 0 else edited_scenes[-1]["edited_end"]
        s_end = total_edited_duration if idx == len(scene_defs) - 1 else round(sc_words[-1]["edited_end"], 4)
        sc_copy = dict(sc)
        sc_copy["edited_start"] = round(s_start, 4)
        sc_copy["edited_end"] = round(s_end, 4)
        sc_copy["edited_duration"] = round(s_end - s_start, 4)
        edited_scenes.append(sc_copy)

    # Schedule SFX (ding on new chapter, whoosh on scene change, pop on bounce, min 1.8s apart)
    raw_sfx = []
    for sc in edited_scenes:
        if sc["edited_start"] > 0.1:
            raw_sfx.append({
                "time": max(0.0, round(sc["edited_start"] - 0.05, 4)),
                "type": "ding" if sc.get("is_new_chapter") else "whoosh",
                "priority": 3 if sc.get("is_new_chapter") else 2
            })
    for b in subtitle_blocks:
        if b.get("has_bounce"):
            raw_sfx.append({
                "time": max(0.0, round(b["bounce_start"] - 0.04, 4)),
                "type": "pop",
                "priority": 1
            })
    raw_sfx.sort(key=lambda x: (x["time"], -x["priority"]))
    sfx_events = []
    for ev in raw_sfx:
        if not sfx_events or (ev["time"] - sfx_events[-1]["time"] >= 1.8):
            sfx_events.append(ev)
        elif ev["priority"] > sfx_events[-1]["priority"]:
            sfx_events[-1] = ev

    plan = {
        "source_video": SOURCE_VIDEO,
        "source_audio": WAV_44K,
        "original_duration_sec": orig_dur,
        "edited_duration_sec": total_edited_duration,
        "segments": edited_segments,
        "words": edited_words,
        "subtitle_blocks": subtitle_blocks,
        "scenes": edited_scenes,
        "sfx_events": sfx_events
    }
    plan_path = os.path.join(WORK_DIR, "desktop_edit_plan.json")
    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)

    print(
        f"[STEP 3 DONE] {orig_dur:.2f}s -> {total_edited_duration:.2f}s "
        f"(saved {orig_dur - total_edited_duration:.2f}s of dead air across {len(edited_segments)} cuts), "
        f"{len(edited_scenes)} scenes, {len(subtitle_blocks)} subtitle blocks, {len(sfx_events)} SFX events."
    )
    return plan


def render_overlays_and_subtitles(plan: dict, out_w: int = 1920, out_h: int = 1080, fps: int = 30):
    mg_root = os.path.join(WORK_DIR, "mg_desktop")
    subs_dir = os.path.join(mg_root, "subs")
    docks_dir = os.path.join(mg_root, "docks")
    os.makedirs(subs_dir, exist_ok=True)
    os.makedirs(docks_dir, exist_ok=True)

    html_uri = "file:///" + os.path.abspath(TEMPLATE_HTML).replace("\\", "/")
    jobs = {
        "width": out_w,
        "height": out_h,
        "fps": fps,
        "html_url": html_uri,
        "scenes": [],
        "subtitle_blocks": plan["subtitle_blocks"],
        "subs_out_dir": subs_dir,
        "docks_out_dir": docks_dir
    }
    for sc in plan["scenes"]:
        sid = sc["scene_id"]
        sc_dir = os.path.join(mg_root, f"scene_{sid}")
        jobs["scenes"].append({
            "scene_id": sid,
            "graphic_config": sc["graphic_config"],
            "out_dir": sc_dir
        })

    subs_existing = len(glob.glob(os.path.join(subs_dir, "sub_*.png")))
    if subs_existing < len(plan["subtitle_blocks"]):
        jobs_json = os.path.join(mg_root, "jobs.json")
        with open(jobs_json, "w", encoding="utf-8") as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)

        print("[PLAYWRIGHT] Rendering 1920x1080 RGBA scenes, docks & Google Fonts Poppins subtitles...")
        subprocess.run(["node", NODE_RENDER_SCRIPT, jobs_json], check=True, cwd=BASE_DIR)

    # Load dock-only overlays (for chapters 1..4 when modal is closed)
    dock_overlays = {}
    for ch in range(1, 5):
        p = os.path.join(docks_dir, f"dock_ch_{ch}.png")
        dock_overlays[ch] = cv2.imread(p, cv2.IMREAD_UNCHANGED)

    # Load scene keyframes (21 frames per scene)
    scene_overlays = {}
    for sc in plan["scenes"]:
        sid = sc["scene_id"]
        sc_dir = os.path.join(mg_root, f"scene_{sid}")
        pngs = sorted(glob.glob(os.path.join(sc_dir, "frame_*.png")))
        scene_overlays[sid] = [cv2.imread(p, cv2.IMREAD_UNCHANGED) for p in pngs]

    return scene_overlays, dock_overlays, subs_dir


def build_master_audio(plan: dict) -> str:
    final_wav = os.path.join(WORK_DIR, "final_audio_14lufs.wav")
    if os.path.exists(final_wav):
        return final_wav
    sr = 44100
    enhanced_wav = os.path.join(WORK_DIR, "audio_enhanced.wav")
    af_chain = (
        "highpass=f=90:poles=2,"
        "afftdn=nr=22:nf=-28:tn=1,"
        "equalizer=f=240:t=q:w=1.2:g=-2.5,"
        "equalizer=f=3200:t=q:w=1.0:g=4.5,"
        "equalizer=f=6800:t=q:w=1.2:g=3.0,"
        "acompressor=threshold=-22dB:ratio=3.2:attack=6:release=110:makeup=5dB"
    )
    subprocess.run(
        [FFMPEG_BIN, "-y", "-i", plan["source_audio"], "-af", af_chain, "-ar", str(sr), "-ac", "1", enhanced_wav],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    src_audio, _ = sf.read(enhanced_wav, dtype="float32")
    if src_audio.ndim > 1:
        src_audio = np.mean(src_audio, axis=1)

    cf_samples = max(1, int(round(0.012 * sr)))
    seg_chunks = []
    seg_dbs = []
    for seg in plan["segments"]:
        s_i = max(0, int(round(seg["source_start"] * sr)))
        e_i = min(len(src_audio), int(round(seg["source_end"] * sr)))
        chunk = src_audio[s_i:e_i].copy()
        if len(chunk) == 0:
            continue
        rms = float(np.sqrt(np.mean(chunk ** 2) + 1e-12))
        db = 20.0 * math.log10(max(rms, 1e-5))
        seg_chunks.append(chunk)
        seg_dbs.append(db)

    target_rms_db = float(np.median(seg_dbs)) if seg_dbs else -18.0
    voice_track = np.zeros(0, dtype=np.float32)

    for idx, chunk in enumerate(seg_chunks):
        gain_db = max(-3.0, min(6.0, target_rms_db - seg_dbs[idx]))
        chunk *= float(10.0 ** (gain_db / 20.0))
        declick = min(len(chunk) // 4, int(0.003 * sr))
        if declick > 1:
            chunk[:declick] *= np.linspace(0.0, 1.0, declick, dtype=np.float32)
            chunk[-declick:] *= np.linspace(1.0, 0.0, declick, dtype=np.float32)

        if idx == 0 or len(voice_track) < cf_samples or len(chunk) < cf_samples:
            voice_track = np.concatenate([voice_track, chunk])
        else:
            fade_out = 0.5 * (1.0 + np.cos(np.linspace(0, math.pi, cf_samples, dtype=np.float32)))
            fade_in = 1.0 - fade_out
            overlap = voice_track[-cf_samples:] * fade_out + chunk[:cf_samples] * fade_in
            voice_track = np.concatenate([voice_track[:-cf_samples], overlap, chunk[cf_samples:]])

    total_samples = max(int(round(plan["edited_duration_sec"] * sr)), len(voice_track))
    if len(voice_track) < total_samples:
        voice_track = np.pad(voice_track, (0, total_samples - len(voice_track)))
    else:
        voice_track = voice_track[:total_samples]

    voice_rms = float(np.sqrt(np.mean(voice_track ** 2) + 1e-12))
    voice_db = 20.0 * math.log10(max(voice_rms, 1e-5))

    mix_l = voice_track.copy()
    mix_r = voice_track.copy()

    # Mix subtle BGM (-28dB below voice + ducking)
    bgm_path = os.path.join(BASE_DIR, "bgm", "default_bgm.wav")
    if os.path.exists(bgm_path):
        bgm_data, _ = sf.read(bgm_path, dtype="float32")
        if bgm_data.ndim == 1:
            bgm_data = np.column_stack([bgm_data, bgm_data])
        if len(bgm_data) < total_samples:
            reps = int(math.ceil(total_samples / len(bgm_data)))
            bgm_data = np.tile(bgm_data, (reps, 1))
        bgm_data = bgm_data[:total_samples]
        bgm_rms = float(np.sqrt(np.mean(bgm_data ** 2) + 1e-12))
        bgm_cur_db = 20.0 * math.log10(max(bgm_rms, 1e-5))
        base_gain = float(10.0 ** (((voice_db - 28.0) - bgm_cur_db) / 20.0))

        fade_env = np.ones(total_samples, dtype=np.float32)
        fi_len = int(0.5 * sr)
        fo_len = int(1.2 * sr)
        fade_env[:fi_len] = np.linspace(0.0, 1.0, fi_len, dtype=np.float32)
        fade_env[-fo_len:] = np.linspace(1.0, 0.0, fo_len, dtype=np.float32)

        mix_l += bgm_data[:, 0] * base_gain * fade_env
        mix_r += bgm_data[:, 1] * base_gain * fade_env

    # Mix SFX (whoosh, pop, ding)
    sfx_dir = os.path.join(BASE_DIR, "sfx")
    sfx_gain = 0.20
    for ev in plan["sfx_events"]:
        fpath = os.path.join(sfx_dir, f"{ev['type']}.wav")
        if os.path.exists(fpath):
            s_data, _ = sf.read(fpath, dtype="float32")
            if s_data.ndim == 1:
                s_data = np.column_stack([s_data, s_data])
            start_i = max(0, int(round(ev["time"] * sr)))
            end_i = min(total_samples, start_i + len(s_data))
            seg_len = end_i - start_i
            if seg_len > 0:
                mix_l[start_i:end_i] += s_data[:seg_len, 0] * sfx_gain
                mix_r[start_i:end_i] += s_data[:seg_len, 1] * sfx_gain

    pre_norm = os.path.join(WORK_DIR, "master_pre_loudnorm.wav")
    peak = max(float(np.max(np.abs(mix_l))), float(np.max(np.abs(mix_r))), 1e-6)
    if peak > 0.98:
        mix_l = mix_l / peak * 0.95
        mix_r = mix_r / peak * 0.95
    sf.write(pre_norm, np.column_stack([mix_l, mix_r]).astype(np.float32), sr)

    final_wav = os.path.join(WORK_DIR, "final_audio_14lufs.wav")
    subprocess.run(
        [FFMPEG_BIN, "-y", "-i", pre_norm, "-af", "loudnorm=I=-14.0:TP=-1.0:LRA=11", "-ar", str(sr), "-ac", "2", final_wav],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    print(f"[AUDIO DSP] Mastered & normalized to -14.0 LUFS -> {final_wav}")
    return final_wav


def blend_roi_bgra(canvas: np.ndarray, bgra: np.ndarray, y1: int, y2: int, x1: int, x2: int, extra_opacity: float = 1.0):
    sub_ov = bgra[y1:y2, x1:x2]
    alpha_u8 = sub_ov[:, :, 3]
    if not np.any(alpha_u8):
        return
    roi = canvas[y1:y2, x1:x2].astype(np.float32)
    alpha = (sub_ov[:, :, 3:4].astype(np.float32) / 255.0) * extra_opacity
    ov_bgr = sub_ov[:, :, :3].astype(np.float32)
    canvas[y1:y2, x1:x2] = (roi * (1.0 - alpha) + ov_bgr * alpha).astype(np.uint8)


def composite_full_video(plan: dict, scene_overlays: dict, dock_overlays: dict, subs_dir: str, final_wav: str, out_mp4: str):
    out_w, out_h, out_fps = 1920, 1080, 30
    total_dur = plan["edited_duration_sec"]
    total_frames = max(1, int(round(total_dur * out_fps)))

    cap = cv2.VideoCapture(plan["source_video"])
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 29.604962
    src_total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 11355)

    ffmpeg_cmd = [
        FFMPEG_BIN, "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-pix_fmt", "bgr24",
        "-s", f"{out_w}x{out_h}",
        "-r", str(out_fps),
        "-i", "-",
        "-i", final_wav,
        "-c:v", "libx264",
        "-crf", "17",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        out_mp4
    ]

    print(f"[RENDER] Compositing {total_frames} frames (1920x1080 @ {out_fps}fps) -> {out_mp4}...")
    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

    segments = plan["segments"]
    scenes = plan["scenes"]
    sub_blocks = plan["subtitle_blocks"]

    sub_cache = {}
    def get_sub_bgra(block_id: int, scale: float = 1.0):
        key = (block_id, round(scale, 3))
        if key in sub_cache:
            return sub_cache[key]
        p = os.path.join(subs_dir, f"sub_{block_id}.png")
        bgra = cv2.imread(p, cv2.IMREAD_UNCHANGED)
        if bgra is None:
            return None
        if abs(scale - 1.0) > 0.005:
            sh, sw = bgra.shape[:2]
            nw, nh = max(1, int(round(sw * scale))), max(1, int(round(sh * scale)))
            resized = cv2.resize(bgra, (nw, nh), interpolation=cv2.INTER_LINEAR)
            out = np.zeros_like(bgra)
            ox = (sw - nw) // 2
            oy = (sh - nh) // 2
            if ox >= 0 and oy >= 0:
                out[oy:oy+nh, ox:ox+nw] = resized
            else:
                sx = max(0, -ox)
                sy = max(0, -oy)
                out[:, :] = resized[sy:sy+sh, sx:sx+sw]
            bgra = out
        sub_cache[key] = bgra
        return bgra

    cur_src_idx = -1
    cur_src_frame = None
    side_card_alpha = 0.0

    for f_idx in range(total_frames):
        t = f_idx / float(out_fps)

        seg = next((s for s in segments if s["edited_start"] <= t <= s["edited_end"]), segments[-1])
        scene = next((sc for sc in scenes if sc["edited_start"] <= t <= sc["edited_end"]), scenes[-1])
        sub_block = next((b for b in sub_blocks if b["start"] <= t <= b["end"]), None)

        seg_prog = max(0.0, min(1.0, (t - seg["edited_start"]) / max(0.005, seg["edited_end"] - seg["edited_start"])))
        src_audio_t = seg["source_start"] + seg_prog * (seg["source_end"] - seg["source_start"])
        # Exact A/V synchronization mapping: fixes the 23s Game DVR clock drift!
        src_video_t = src_audio_t * AV_CLOCK_RATIO
        target_src_idx = max(0, min(src_total_frames - 1, int(round(src_video_t * src_fps))))

        if cur_src_frame is None or target_src_idx != cur_src_idx:
            if target_src_idx < cur_src_idx or (target_src_idx - cur_src_idx) > 60 or cur_src_idx < 0:
                cap.set(cv2.CAP_PROP_POS_FRAMES, target_src_idx)
                ret, frm = cap.read()
                if ret and frm is not None:
                    cur_src_frame = frm
                    cur_src_idx = target_src_idx
            else:
                while cur_src_idx < target_src_idx:
                    ret, frm = cap.read()
                    cur_src_idx += 1
                    if ret and frm is not None:
                        cur_src_frame = frm

        if cur_src_frame is None:
            cur_src_frame = np.zeros((1008, 1920, 3), dtype=np.uint8)

        # Build 1920x1080 Full HD frame
        canvas = np.zeros((out_h, out_w, 3), dtype=np.uint8)
        canvas[:1008, :1920] = cur_src_frame

        # Detect whether a centered modal is currently open (backdrop dims x=400, y=500 to ~125)
        backdrop_luma = float(np.mean(canvas[500, 400]))
        modal_is_open = backdrop_luma < 175.0

        # Seamless pixel clean-up of Chrome URL bar and Gemini button
        bg_bgr = canvas[78, 850]
        path_slice = canvas[80:110, 518:830].copy()
        canvas[80:110, 230:860] = bg_bgr
        canvas[80:110, 230:230 + URL_PREFIX_W] = np.clip(
            bg_bgr.astype(np.int16) + URL_PREFIX_DELTA, 0, 255
        ).astype(np.uint8)
        canvas[80:110, 230 + URL_PREFIX_W:230 + URL_PREFIX_W + path_slice.shape[1]] = path_slice
        canvas[4:52, 1430:1712] = canvas[25:26, 1420:1421]

        # When modal is closed, clean the pink 'Estás conectado como: vetebosco@gmail.com' text at y=926..962
        if not modal_is_open:
            canvas[926:962, 310:1900] = canvas[930:931, 320:321]
            side_card_alpha = max(0.0, side_card_alpha - 0.16)
        else:
            side_card_alpha = min(1.0, side_card_alpha + 0.16)

        # Pick scene keyframe overlay
        sc_frames = scene_overlays[scene["scene_id"]]
        sc_rel_f = max(0, min(len(sc_frames) - 1, int(round((t - scene["edited_start"]) * out_fps))))
        ov_bgra = sc_frames[sc_rel_f]

        # 1. Blend Top Chrome patches (y=0..62, x=1380..1920) & Bottom Dock + Mascot (y=915..1080)
        blend_roi_bgra(canvas, ov_bgra, 0, 62, 1380, 1920, 1.0)
        blend_roi_bgra(canvas, ov_bgra, 915, 1080, 0, 1920, 1.0)

        # 2. Blend Right-Hand Tutorial Card (x=1420..1915, y=165..955) ONLY when modal is open!
        if side_card_alpha > 0.01:
            blend_roi_bgra(canvas, ov_bgra, 165, 955, 1420, 1915, side_card_alpha)

        # 3. Blend Subtitle Block in Bottom Dock (x=295..1405, y=966..1076)
        if sub_block:
            sub_scale = 1.0
            if sub_block.get("has_bounce"):
                bt = sub_block.get("bounce_start", sub_block["start"])
                if bt <= t <= bt + 0.26:
                    u = (t - bt) / 0.26
                    sub_scale = 1.0 + 0.14 * math.sin(math.pi * u)
            sub_bgra = get_sub_bgra(sub_block["block_id"], scale=sub_scale)
            if sub_bgra is not None:
                sh, sw = sub_bgra.shape[:2]
                sy1, sx1 = 966, 295
                roi = canvas[sy1:sy1+sh, sx1:sx1+sw].astype(np.float32)
                sa = sub_bgra[:, :, 3:4].astype(np.float32) / 255.0
                sbgr = sub_bgra[:, :, :3].astype(np.float32)
                canvas[sy1:sy1+sh, sx1:sx1+sw] = (roi * (1.0 - sa) + sbgr * sa).astype(np.uint8)

        proc.stdin.write(canvas.tobytes())
        if f_idx % 900 == 0 and f_idx > 0:
            print(f"  -> Progress: {f_idx}/{total_frames} frames ({f_idx/total_frames*100:.1f}%)")

    proc.stdin.close()
    proc.wait()
    cap.release()
    print(f"[STEP 4 & 5 DONE] Exported Full HD 1920x1080 Desktop Tutorial -> {out_mp4}")


def build_verification_grid(mp4_path: str, grid_out_path: str):
    cap = cv2.VideoCapture(mp4_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    nframes = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 1)
    dur = nframes / fps

    # 12 sample points (4x3 grid of 640x360 thumbnails -> 1920x1440 grid)
    cols, rows = 3, 4
    tw, th = 640, 360
    grid = np.zeros((rows * th, cols * tw, 3), dtype=np.uint8)

    for i in range(12):
        t = dur * (0.04 + 0.92 * (i / 11.0))
        f_idx = max(0, min(nframes - 1, int(round(t * fps))))
        cap.set(cv2.CAP_PROP_POS_FRAMES, f_idx)
        ret, frm = cap.read()
        if ret and frm is not None:
            thumb = cv2.resize(frm, (tw, th), interpolation=cv2.INTER_AREA)
            cv2.putText(thumb, f"t={t:.1f}s", (16, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 4, cv2.LINE_AA)
            cv2.putText(thumb, f"t={t:.1f}s", (16, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA)
            r = i // cols
            c = i % cols
            grid[r*th:(r+1)*th, c*tw:(c+1)*tw] = thumb

    cap.release()
    cv2.imwrite(grid_out_path, grid, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    print(f"[STEP 6 DONE] Verification grid saved -> {grid_out_path}")


if __name__ == "__main__":
    plan = build_edit_plan()
    scene_ovs, dock_ovs, subs_dir = render_overlays_and_subtitles(plan)
    final_wav = build_master_audio(plan)
    out_mp4 = os.path.join(WORK_DIR, "MascotaMas - Instructivo Calendarios (Editado).mp4")
    composite_full_video(plan, scene_ovs, dock_ovs, subs_dir, final_wav, out_mp4)
    grid_path = os.path.join(BASE_DIR, "verification_grid.jpg")
    build_verification_grid(out_mp4, grid_path)
