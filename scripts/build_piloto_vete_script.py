import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK_DIR = os.path.join(BASE_DIR, "reels_work")

with open(os.path.join(WORK_DIR, "transcription_table.json"), "r", encoding="utf-8") as f:
    trans = json.load(f)

words = trans["words"]

deleted_ids = {22, 23}

subtitle_overrides = {
    2: "tenés",
    4: "veterinaria,",
    5: "mirá",
    12: "MascotaMás.",
    14: "configurás",
    20: "guardería,",
    28: "Sala",
    30: "Espera.",
    35: "seña",
    37: "Mercado",
    38: "Pago,",
    41: "comisión",
    44: "Plan",
    45: "Premium.",
    46: "Además,",
    47: "descargás",
    48: "Historias",
    49: "Clínicas",
    51: "PDF",
    57: "medís",
    61: "¡Probá",
    63: "MascotaMás!"
}

words_cleaned = []
deleted_details = []
for w in words:
    wc = dict(w)
    wid = wc["word_id"]
    if wid in deleted_ids:
        wc["keep"] = False
        wc["delete_reason"] = "Repetición / titubeo ('en vivos')"
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
    "line1": "+100 MEJORAS",
    "line2": "VETERINARIAS 🐾",
    "keyword": "VETERINARIAS",
    "emoji": "🐾"
}

scenes = [
    {
        "scene_id": 1,
        "sentence_id": 1,
        "word_ids": list(range(1, 13)),
        "text": "Si tenés una veterinaria, mirá las nuevas funciones que sumamos en MascotaMás.",
        "layout_mode": "full_face",
        "is_hook": True,
        "is_cta": False,
        "top_title": hook_title,
        "graphic_config": {
            "template": "none",
            "device_mode": "none",
            "pill": "MASCOTAMÁS · VETERINARIAS",
            "headline_kicker": "✨ NUEVA VERSIÓN · GESTIÓN VETERINARIA",
            "headline_main": "🚀 +100 MEJORAS PARA TU VETERINARIA",
            "mascot_expression": "happy"
        }
    },
    {
        "scene_id": 2,
        "sentence_id": 2,
        "word_ids": [13, 14, 15, 16, 17, 18, 19, 20, 21, 24, 25, 26, 27, 28, 29, 30],
        "text": "Ahora configurás agendas por servicio, profesional o guardería, conectadas en vivo con tu Sala de Espera.",
        "layout_mode": "split_graphic",
        "is_hook": False,
        "is_cta": False,
        "top_title": None,
        "graphic_config": {
            "template": "checklist",
            "device_mode": "combo",
            "pill": "AGENDAS & SALA EN VIVO",
            "headline_kicker": "📅 4 MOTORES DE AGENDA + SALA DE ESPERA",
            "headline_main": "🏥 SERVICIOS, GUARDERÍA Y SALA EN VIVO",
            "laptop_screenshot": "../assets/mascotamas_v11/12b-hotel-tablero-estadias.png",
            "phone_screenshot": "../assets/mascotamas_v11/05-sala-de-espera.png",
            "items": [
                {"text": "Servicios y Profesionales", "tag": "AGENDAS"},
                {"text": "Guardería y Estadías", "tag": "HOTEL"},
                {"text": "Sala de Espera en Vivo", "tag": "EN VIVO"}
            ],
            "mascot_expression": "happy"
        }
    },
    {
        "scene_id": 3,
        "sentence_id": 3,
        "word_ids": list(range(31, 46)),
        "text": "Tus clientes reservan abonando seña por Mercado Pago, con cero comisión en el Plan Premium.",
        "layout_mode": "split_graphic",
        "is_hook": False,
        "is_cta": False,
        "top_title": None,
        "graphic_config": {
            "template": "before_after",
            "device_mode": "combo_left_phone",
            "pill": "MERCADO PAGO · $0 COMISIÓN",
            "headline_kicker": "💳 VINCULACIÓN EN 3 PASOS · CERO AUSENTISMO",
            "headline_main": "⚡ SEÑAS MERCADO PAGO · $0 COMISIÓN",
            "laptop_screenshot": "../assets/mascotamas_v11/10b-settings-mercadopago-split.png",
            "phone_screenshot": "../assets/mascotamas_v11/04-link-publico-sena.png",
            "before_label": "SIN SEÑA",
            "before_val": "Huecos y Faltazos",
            "before_sub": "Turnos perdidos en consultorio",
            "after_label": "PLAN PREMIUM",
            "after_val": "$0 Comisión en Señas",
            "after_sub": "100% acreditado en tu Mercado Pago",
            "mascot_expression": "surprised"
        }
    },
    {
        "scene_id": 4,
        "sentence_id": 4,
        "word_ids": list(range(46, 61)),
        "text": "Además, descargás Historias Clínicas en PDF con foto del paciente y medís tus pacientes vistos.",
        "layout_mode": "split_graphic",
        "is_hook": False,
        "is_cta": False,
        "top_title": None,
        "graphic_config": {
            "template": "checklist",
            "device_mode": "combo",
            "pill": "HISTORIAS CLÍNICAS & KPIS",
            "headline_kicker": "📋 CONSULTORIO DIGITAL & ESTADÍSTICAS",
            "headline_main": "🩺 HISTORIA CLÍNICA PDF + PACIENTES VISTOS",
            "laptop_screenshot": "../assets/mascotamas_v11/06c-hc-ver-legajo-y-pdf.png",
            "phone_screenshot": "../assets/mascotamas_v11/06d-hc-nuevo-registro-vacunas.png",
            "items": [
                {"text": "Legajo PDF con Foto", "tag": "HISTORIA CLÍNICA"},
                {"text": "Vacunas y WhatsApp", "tag": "RECORDATORIOS"},
                {"text": "KPI Pacientes Vistos", "tag": "ESTADÍSTICAS"}
            ],
            "mascot_expression": "happy"
        }
    },
    {
        "scene_id": 5,
        "sentence_id": 5,
        "word_ids": [61, 62, 63],
        "text": "¡Probá hoy MascotaMás!",
        "layout_mode": "split_graphic",
        "is_hook": False,
        "is_cta": True,
        "top_title": None,
        "graphic_config": {
            "template": "chat_input",
            "device_mode": "combo",
            "pill": "MASCOTAMAS.COM · SUMATE HOY",
            "headline_kicker": "🐾 28 ESPECIALIDADES MÉDICAS VETERINARIAS",
            "headline_main": "💻 PROBÁ HOY MASCOTAMÁS EN TU CLÍNICA",
            "laptop_screenshot": "../assets/mascotamas_v11/01-dashboard.png",
            "phone_screenshot": "../assets/mascotamas_v11/11c-perfil-medico-28-especialidades.png",
            "prompt_text": "LLEVÁ TU VETERINARIA AL SIGUIENTE NIVEL",
            "reply_text": "Probá hoy MascotaMás en tu clínica",
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
    "cta_keyword": "MASCOTAMAS",
    "hook_title": hook_title,
    "cta_title": {
        "line1": "Probá hoy",
        "line2": "MASCOTAMÁS 🐾",
        "keyword": "MASCOTAMÁS",
        "emoji": "🐾"
    },
    "words_cleaned": words_cleaned,
    "scenes": scenes
}

with open(os.path.join(WORK_DIR, "guion_corregido.json"), "w", encoding="utf-8") as f:
    json.dump(out_json, f, ensure_ascii=False, indent=2)

print("[STEP 2 DONE] Guion corregido con lip-sync nativo generado.")
