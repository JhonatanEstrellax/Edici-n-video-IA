# -*- coding: utf-8 -*-
import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK_DIR = os.path.join(BASE_DIR, "reels_work")

with open(os.path.join(WORK_DIR, "transcription_table.json"), "r", encoding="utf-8") as f:
    trans = json.load(f)

words = trans["words"]

# Remove clipped end of Turn 1 ("o internas") so sentence 2 ends cleanly on "para paseos."
deleted_ids = {30, 31}

subtitle_overrides = {
    1: "¡Mirá",
    5: "MascotaMás",
    6: "",
    9: "veterinaria,",
    12: "guardería!",
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
    32: "También",
    35: "Servicios",
    37: "Profesionales",
    39: "grilla",
    40: "automática",
    42: "huecos,",
    44: "Calendario",
    46: "Guardería",
    50: "fechas,",
    52: "sectores",
    54: "ingreso",
    56: "egreso.",
    58: "activás",
    59: "seña",
    60: "automática",
    62: "Mercado",
    63: "Pago,",
    66: "comisión",
    68: "Mercado",
    69: "Pago.",
    70: "¡Entrá",
    73: "MascotaMás!",
    74: "",
}

# Note: for compound brand words where Whisper split "Mascota" + "Más",
# if we keep both words in subtitle_overrides as "Mascota" and "Más!" (or merge),
# let's keep non-empty strings so every kept word_id has a valid token!
subtitle_overrides[5] = "Mascota"
subtitle_overrides[6] = "Más"
subtitle_overrides[73] = "Mascota"
subtitle_overrides[74] = "Más!"

words_cleaned = []
deleted_details = []
for w in words:
    wc = dict(w)
    wid = wc["word_id"]
    if wid in deleted_ids:
        wc["keep"] = False
        wc["delete_reason"] = "Corte limpio de cierre de toma ('o internas')"
        deleted_details.append({
            "word_id": wid,
            "word": wc["word"],
            "reason": wc["delete_reason"]
        })
    else:
        wc["keep"] = True
        wc["delete_reason"] = ""
    wc["subtitle_text"] = subtitle_overrides.get(wid, wc["word"])
    words_cleaned.append(wc)

hook_title = {
    "line1": "LO NUEVO DE",
    "line2": "MASCOTAMÁS 🚀",
    "keyword": "MASCOTAMÁS",
    "emoji": "🚀"
}

scenes = [
    {
        "scene_id": 1,
        "sentence_id": 1,
        "word_ids": list(range(1, 13)),
        "text": "¡Mirá lo nuevo de MascotaMás para tu veterinaria, peluquería o guardería!",
        "layout_mode": "full_face",
        "is_hook": True,
        "is_cta": False,
        "top_title": hook_title,
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
        "sentence_id": 5,
        "word_ids": list(range(32, 43)),
        "text": "También agendas por Servicios y Profesionales con grilla automática sin huecos,",
        "layout_mode": "split_graphic",
        "is_hook": False,
        "is_cta": False,
        "top_title": None,
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
        "sentence_id": 6,
        "word_ids": list(range(43, 57)),
        "text": "y Calendario de Guardería por rango de fechas, con sectores de ingreso y egreso.",
        "layout_mode": "split_graphic",
        "is_hook": False,
        "is_cta": False,
        "top_title": None,
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
        "sentence_id": 7,
        "word_ids": list(range(57, 70)),
        "text": "Y activás seña automática con Mercado Pago, contemplando posible comisión de Mercado Pago.",
        "layout_mode": "split_graphic",
        "is_hook": False,
        "is_cta": False,
        "top_title": None,
        "graphic_config": {
            "template": "before_after",
            "device_mode": "combo_left_phone",
            "pill": "SEÑA MERCADO PAGO · ACLARACIÓN",
            "headline_kicker": "💳 COBRO AUTOMATIZADO · POSIBLE COMISIÓN DE MERCADO PAGO",
            "headline_main": "⚡ SEÑA AUTOMÁTICA CON MERCADO PAGO",
            "laptop_screenshot": "../assets/mascotamas_v11/reel_mac_04_sena_mercadopago.png",
            "phone_screenshot": "../assets/mascotamas_v11/reel_iphone_01_sena_turnos.png",
            "before_label": "IMPORTANTE · COMISIÓN MP",
            "before_val": "Posible Comisión MP",
            "before_sub": "Mercado Pago puede aplicar comisión por cobro",
            "after_label": "RESERVA ASEGURADA",
            "after_val": "Seña Automática 24/7",
            "after_sub": "Cero faltazos y turno confirmado al instante",
            "mascot_expression": "surprised"
        }
    },
    {
        "scene_id": 6,
        "sentence_id": 9,
        "word_ids": list(range(70, 75)),
        "text": "¡Entrá hoy en MascotaMás!",
        "layout_mode": "split_graphic",
        "is_hook": False,
        "is_cta": True,
        "top_title": None,
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
            "mascot_expression": "happy"
        }
    }
]

out_json = {
    "total_original_words": len(words),
    "kept_word_ids": [w["word_id"] for w in words_cleaned if w["keep"]],
    "deleted_word_ids": sorted(list(deleted_ids)),
    "deleted_details": deleted_details,
    "cta_keyword": "TURNOS",
    "hook_title": hook_title,
    "cta_title": {
        "line1": "Entrá hoy en",
        "line2": "MASCOTAMÁS 🐾",
        "keyword": "MASCOTAMÁS",
        "emoji": "🐾"
    },
    "words_cleaned": words_cleaned,
    "scenes": scenes
}

with open(os.path.join(WORK_DIR, "guion_corregido.json"), "w", encoding="utf-8") as f:
    json.dump(out_json, f, ensure_ascii=False, indent=2)

print("[STEP 2 DONE] Guion corregido para Reel Publicitario (Calendarios + Seña Mercado Pago) generado.")
