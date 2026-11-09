# -*- coding: utf-8 -*-
import os
import shutil
import json
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK_DIR = os.path.join(BASE_DIR, "reels_work")
sys.path.insert(0, os.path.join(BASE_DIR, "scripts"))

from step3_plan_cuts import load_style, build_subtitle_blocks, is_highlighted_word

# 1. Copy v3_vet_lipsync_master.mp4 -> source_input.mp4 and gemini_tts_ar_synced.wav -> source_audio.wav
shutil.copy2(os.path.join(WORK_DIR, "v3_vet_lipsync_master.mp4"), os.path.join(WORK_DIR, "source_input.mp4"))
shutil.copy2(os.path.join(WORK_DIR, "gemini_tts_ar_synced.wav"), os.path.join(WORK_DIR, "source_audio.wav"))

with open(os.path.join(WORK_DIR, "tts_v2_words.json"), "r", encoding="utf-8") as f:
    tts_data = json.load(f)

raw_words = tts_data["words"]
transitions = tts_data["transitions"]  # [0.0, 4.32, 10.56, 15.36, 20.16, 25.44, 28.8]
total_dur = float(tts_data["duration"])

# Exact Argentine commercial text & punctuation overrides for the 75 word tokens
subtitle_overrides = {
    1: "¡Mirá",
    5: "Mascota",
    6: "Más",
    9: "veterinaria,",
    10: "peluquería",
    12: "guardería!",
    13: "Ahora",
    14: "tenés",
    15: "4",
    18: "calendario:",
    19: "Turnos",
    20: "Simples",
    21: "1",
    23: "1,",
    25: "Cupos",
    27: "Horario",
    29: "paseos.",
    30: "También",
    33: "Servicios",
    35: "Profesionales,",
    37: "grilla",
    38: "automática",
    40: "huecos,",
    42: "Calendario",
    44: "Guardería",
    48: "fechas,",
    50: "sectores",
    52: "ingreso",
    54: "egreso.",
    55: "Además,",
    56: "activás",
    60: "seña",
    61: "automático",
    63: "Mercado",
    64: "Pago*",
    68: "turno.",
    69: "¡Entrá",
    72: "Mascota",
    73: "Más",
    75: "probalo!",
}

hook_title = {
    "line1": "LO NUEVO DE",
    "line2": "MASCOTAMÁS 🚀",
    "keyword": "MASCOTAMÁS",
    "emoji": "🚀"
}

legal_tyc = "* Aplican posibles comisiones de Mercado Pago según las condiciones y plazos de acreditación de tu cuenta."

scenes_def = [
    {
        "scene_id": 1,
        "sentence_id": 1,
        "word_ids": list(range(1, 13)),
        "text": "¡Mirá lo nuevo de MascotaMás para tu veterinaria, peluquería o guardería!",
        "layout_mode": "full_face",
        "is_hook": True,
        "is_cta": False,
        "top_title": hook_title,
        "edited_start": transitions[0],
        "edited_end": transitions[1],
        "edited_duration": round(transitions[1] - transitions[0], 4),
        "graphic_config": {
            "template": "none",
            "device_mode": "none",
            "pill": "MASCOTAMÁS · LO NUEVO",
            "headline_kicker": "✨ NUEVO LANZAMIENTO · GESTIÓN INTEGRAL PET",
            "headline_main": "🚀 4 CALENDARIOS + SEÑA MERCADO PAGO",
            "mascot_expression": "happy"
        }
    },
    {
        "scene_id": 2,
        "sentence_id": 2,
        "word_ids": list(range(13, 30)),
        "text": "Ahora tenés 4 tipos de calendario: Turnos Simples 1 a 1, y Cupos por Horario para paseos.",
        "layout_mode": "split_graphic",
        "is_hook": False,
        "is_cta": False,
        "top_title": None,
        "edited_start": transitions[1],
        "edited_end": transitions[2],
        "edited_duration": round(transitions[2] - transitions[1], 4),
        "graphic_config": {
            "template": "checklist",
            "device_mode": "combo",
            "pill": "4 TIPOS DE CALENDARIO",
            "headline_kicker": "📅 MACBOOK PRO & IPHONE · 4 AGENDAS A MEDIDA",
            "headline_main": "🐾 TURNOS 1 A 1 Y CUPOS POR HORARIO",
            "laptop_screenshot": "../assets/mascotamas_v11/reel_mac_01_4_calendarios.png",
            "phone_screenshot": "../assets/mascotamas_v11/reel_iphone_02_servicios.png",
            "items": [
                {"text": "Turnos Simples 1 a 1", "tag": "CONSULTORIO"},
                {"text": "Cupos por Horario", "tag": "GRUPAL / PASEOS"},
                {"text": "Múltiples Mascotas", "tag": "SIMULTÁNEO"}
            ],
            "mascot_expression": "happy"
        }
    },
    {
        "scene_id": 3,
        "sentence_id": 3,
        "word_ids": list(range(30, 41)),
        "text": "También agendas por Servicios y Profesionales, con grilla automática sin huecos,",
        "layout_mode": "split_graphic",
        "is_hook": False,
        "is_cta": False,
        "top_title": None,
        "edited_start": transitions[2],
        "edited_end": transitions[3],
        "edited_duration": round(transitions[3] - transitions[2], 4),
        "graphic_config": {
            "template": "checklist",
            "device_mode": "combo_left_phone",
            "pill": "SERVICIOS Y PROFESIONALES",
            "headline_kicker": "✂️ PELUQUERÍA, CLÍNICA Y ESPECIALIDADES",
            "headline_main": "⚡ SERVICIOS Y PROFESIONALES SIN HUECOS",
            "laptop_screenshot": "../assets/mascotamas_v11/reel_mac_02_tablero_servicios.png",
            "phone_screenshot": "../assets/mascotamas_v11/reel_iphone_01_sena_turnos.png",
            "items": [
                {"text": "Grilla Sin Huecos", "tag": "AUTOMÁTICA"},
                {"text": "Tablero por Staff", "tag": "AGENDA COLOR"},
                {"text": "Duración y Precio", "tag": "POR SERVICIO"}
            ],
            "mascot_expression": "surprised"
        }
    },
    {
        "scene_id": 4,
        "sentence_id": 4,
        "word_ids": list(range(41, 55)),
        "text": "y Calendario de Guardería por rango de fechas, con sectores de ingreso y egreso.",
        "layout_mode": "split_graphic",
        "is_hook": False,
        "is_cta": False,
        "top_title": None,
        "edited_start": transitions[3],
        "edited_end": transitions[4],
        "edited_duration": round(transitions[4] - transitions[3], 4),
        "graphic_config": {
            "template": "checklist",
            "device_mode": "combo",
            "pill": "CALENDARIO DE GUARDERÍA",
            "headline_kicker": "🏨 HOTEL, PENSIONADO Y GUARDERÍA",
            "headline_main": "🛏️ GUARDERÍA POR FECHAS: CHECK-IN Y OUT",
            "laptop_screenshot": "../assets/mascotamas_v11/reel_mac_03_guarderia_estadias.png",
            "phone_screenshot": "../assets/mascotamas_v11/reel_iphone_03_guarderia.png",
            "items": [
                {"text": "Rango de Fechas", "tag": "CHECK-IN / OUT"},
                {"text": "Sectores y Cupos", "tag": "CATEGORÍAS"},
                {"text": "Bloqueo de Feriados", "tag": "365 DÍAS"}
            ],
            "mascot_expression": "happy"
        }
    },
    {
        "scene_id": 5,
        "sentence_id": 5,
        "word_ids": list(range(55, 69)),
        "text": "Además, activás el cobro de seña automático con Mercado Pago para asegurar cada turno.",
        "layout_mode": "split_graphic",
        "is_hook": False,
        "is_cta": False,
        "top_title": None,
        "edited_start": transitions[4],
        "edited_end": transitions[5],
        "edited_duration": round(transitions[5] - transitions[4], 4),
        "graphic_config": {
            "template": "checklist",
            "device_mode": "combo_left_phone",
            "pill": "SEÑA AUTOMÁTICA · MERCADO PAGO*",
            "headline_kicker": "💳 COBRO AUTOMATIZADO ONLINE 24/7*",
            "headline_main": "⚡ SEÑA AUTOMÁTICA CON MERCADO PAGO*",
            "laptop_screenshot": "../assets/mascotamas_v11/reel_mac_04_sena_mercadopago.png",
            "phone_screenshot": "../assets/mascotamas_v11/reel_iphone_01_sena_turnos.png",
            "items": [
                {"text": "Cobro de Seña Online*", "tag": "MERCADO PAGO"},
                {"text": "Turno Confirmado 24/7", "tag": "AL INSTANTE"},
                {"text": "Cero Inasistencias", "tag": "100% SEGURO"}
            ],
            "legal_disclaimer": legal_tyc,
            "mascot_expression": "surprised"
        }
    },
    {
        "scene_id": 6,
        "sentence_id": 6,
        "word_ids": list(range(69, 76)),
        "text": "¡Entrá hoy en MascotaMás y probalo!",
        "layout_mode": "split_graphic",
        "is_hook": False,
        "is_cta": True,
        "top_title": None,
        "edited_start": transitions[5],
        "edited_end": transitions[6],
        "edited_duration": round(transitions[6] - transitions[5], 4),
        "graphic_config": {
            "template": "chat_input",
            "device_mode": "combo",
            "pill": "MASCOTAMAS.COM · ACTIVÁ HOY",
            "headline_kicker": "🐾 SUMATE A LA GESTIÓN INTELIGENTE",
            "headline_main": "💻 ENTRÁ HOY EN MASCOTAMAS.COM",
            "laptop_screenshot": "../assets/mascotamas_v11/01-dashboard.png",
            "phone_screenshot": "../assets/mascotamas_v11/reel_iphone_02_servicios.png",
            "prompt_text": "AUTOMATIZÁ TUS AGENDAS Y SEÑAS HOY",
            "reply_text": "Entrá en mascotamas.com o comentá TURNOS",
            "badge": "MASCOTAMAS.COM · ACTIVÁ TU CUENTA",
            "legal_disclaimer": legal_tyc,
            "mascot_expression": "happy"
        }
    }
]

word_to_scene = {}
for sc in scenes_def:
    for wid in sc["word_ids"]:
        word_to_scene[wid] = sc["scene_id"]

style = load_style()
cta_kw = "TURNOS"
cooldown_min = 4.0
last_bounce_time = -999.0

words_cleaned = []
edited_words = []
for i, w in enumerate(raw_words):
    wid = w["word_id"]
    sub_txt = subtitle_overrides.get(wid, w["word"])
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
        "scene_id": word_to_scene.get(wid, 1),
        "face_center": [0.5, 0.36]
    }
    nxt_str = raw_words[i + 1]["word"] if i + 1 < len(raw_words) else ""
    is_yel, can_bounce = is_highlighted_word(sub_txt, nxt_str, style, cta_kw)
    # Also highlight key domain terms in violet (#AE4CFC)
    if any(k in sub_txt.lower() for k in ["mascotamás", "4", "1", "servicios", "guardería", "seña", "mercado", "pago", "probalo"]):
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
    "cta_title": {
        "line1": "Entrá hoy en",
        "line2": "MASCOTAMÁS 🐾",
        "keyword": "MASCOTAMÁS",
        "emoji": "🐾"
    },
    "words_cleaned": words_cleaned,
    "scenes": scenes_def
}
with open(os.path.join(WORK_DIR, "guion_corregido.json"), "w", encoding="utf-8") as f:
    json.dump(guion_json, f, ensure_ascii=False, indent=2)

# Single 1:1 continuous timeline segment (0.00 -> 28.80s) so every word and beat transition stays 100% locked
segments = [{
    "segment_id": 1,
    "source_start": 0.0,
    "source_end": total_dur,
    "duration": total_dur,
    "edited_start": 0.0,
    "edited_end": total_dur,
    "avg_rms_db": -16.0,
    "face_center": [0.5, 0.36],
    "word_ids": [w["word_id"] for w in words_cleaned]
}]

# SFX events locked to every 125 BPM transition + key bounces
sfx_events = []
for tr_t in transitions[1:-1]:
    sfx_events.append({
        "type": "whoosh",
        "time": round(max(0.0, tr_t - 0.04), 4),
        "reason": f"Beat-synced transition @ {tr_t:.2f}s (125 BPM Lyria 3 House)"
    })
sfx_events.append({
    "type": "ding",
    "time": round(transitions[5] - 0.02, 4),
    "reason": "CTA final"
})

mg_dur = sum(sc["edited_duration"] for sc in scenes_def if sc["layout_mode"] == "split_graphic")
mg_ratio = round(mg_dur / total_dur, 4)

edit_plan = {
    "source_video": os.path.join(WORK_DIR, "source_input.mp4"),
    "source_audio": os.path.join(WORK_DIR, "source_audio.wav"),
    "skip_denoise": True,
    "bgm_override_path": os.path.join(WORK_DIR, "lyria3_house_synced.wav"),
    "bgm_relative_db": -13.5,
    "bgm_ducking_db": -6.5,
    "original_duration_sec": total_dur,
    "edited_duration_sec": total_dur,
    "motion_graphics_coverage_ratio": mg_ratio,
    "cta_keyword": cta_kw,
    "hook_title": hook_title,
    "cta_title": guion_json["cta_title"],
    "face_metadata": {
        "default_face_center": [0.5, 0.36],
        "has_face": True
    },
    "segments": segments,
    "words": edited_words,
    "edited_words": edited_words,
    "subtitle_blocks": subtitle_blocks,
    "scenes": scenes_def,
    "sfx_events": sfx_events
}

with open(os.path.join(WORK_DIR, "edit_plan.json"), "w", encoding="utf-8") as f:
    json.dump(edit_plan, f, ensure_ascii=False, indent=2)

print(f"[V2 PLAN READY] Duration={total_dur:.2f}s (60 beats @ 125 BPM), MG coverage={mg_ratio*100:.1f}%, Sub blocks={len(subtitle_blocks)}")
