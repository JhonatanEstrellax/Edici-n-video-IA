import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK_DIR = os.path.join(BASE_DIR, "reels_work")

with open(os.path.join(WORK_DIR, "transcription_table.json"), "r", encoding="utf-8") as f:
    trans = json.load(f)

words = trans["words"]

subtitle_overrides = {
    2: "pasó",
    3: "alguna",
    24: "tenés",
    28: "aumentás",
    34: "recaudás",
    47: "Dejá",
    52: "suscribite",
    54: "Mascota",
    55: "Más."
}

words_cleaned = []
for w in words:
    wc = dict(w)
    wid = wc["word_id"]
    wc["keep"] = True
    wc["delete_reason"] = ""
    wc["subtitle_text"] = subtitle_overrides.get(wid, wc["word"])
    words_cleaned.append(wc)

hook_title = {
    "line1": "¿FALTAN A TUS",
    "line2": "TURNOS? 😱",
    "keyword": "TURNOS",
    "emoji": "😱"
}

scenes = [
    {
        "scene_id": 1,
        "sentence_id": 1,
        "word_ids": list(range(1, 16)),
        "text": "¿Te pasó alguna vez de ir a trabajar y que falten casi todos tus turnos?",
        "layout_mode": "full_face",
        "is_hook": True,
        "is_cta": False,
        "top_title": hook_title,
        "graphic_config": {
            "template": "none",
            "pill": "MASCOTAMÁS · WEB & APP",
            "mascot_expression": "surprised"
        }
    },
    {
        "scene_id": 2,
        "sentence_id": 2,
        "word_ids": list(range(16, 28)),
        "text": "Con nuestro sistema de autogestión y recordatorios automáticos tenés menos tiempo muerto,",
        "layout_mode": "split_graphic",
        "is_hook": False,
        "is_cta": False,
        "top_title": None,
        "graphic_config": {
            "template": "app_connection",
            "pill": "AUTOGESTIÓN 24/7",
            "title": "Recordatorios Automáticos por WhatsApp",
            "showcase_icon": "💬",
            "laptop_screenshot": "../assets/mascotamas/reminders_laptop.png",
            "phone_screenshot": "../assets/mascotamas/reminders_phone.jpg",
            "showcase_caption": "Envío automático de recordatorios de turnos y vacunas",
            "showcase_tag": "WHATSAPP ACTIVO",
            "app_a_name": "Autogestión",
            "sub_a": "Turnos Online 24/7",
            "app_a_icon": "📅",
            "app_b_name": "WhatsApp",
            "sub_b": "Recordatorios",
            "app_b_icon": "💬",
            "status": "✓ Menos tiempo muerto",
            "mascot_expression": "happy"
        }
    },
    {
        "scene_id": 3,
        "sentence_id": 3,
        "word_ids": list(range(28, 37)),
        "text": "aumentás los turnos efectivos y obvio recaudás más plata.",
        "layout_mode": "split_graphic",
        "is_hook": False,
        "is_cta": False,
        "top_title": None,
        "graphic_config": {
            "template": "checklist",
            "pill": "MÁS RENTABILIDAD",
            "title": "Panel de Estadísticas e Ingresos",
            "showcase_icon": "📈",
            "laptop_screenshot": "../assets/mascotamas/stats_laptop.png",
            "phone_screenshot": "../assets/mascotamas/stats_phone.jpg",
            "showcase_caption": "Métricas reales: +271.4% en turnos efectivos",
            "showcase_tag": "+INGRESOS",
            "items": [
                {"text": "Turnos 100% efectivos", "tag": "TURNOS"},
                {"text": "Sin huecos libres", "tag": "AGENDA"},
                {"text": "Recaudás más plata", "tag": "+INGRESOS"}
            ],
            "mascot_expression": "surprised"
        }
    },
    {
        "scene_id": 4,
        "sentence_id": 4,
        "word_ids": list(range(37, 47)),
        "text": "Los huecos en tu agenda son cada vez más caros.",
        "layout_mode": "split_graphic",
        "is_hook": False,
        "is_cta": False,
        "top_title": None,
        "graphic_config": {
            "template": "before_after",
            "pill": "CUIDÁ TU TIEMPO",
            "title": "Gestión y Automatización de Turnos",
            "showcase_icon": "📅",
            "laptop_screenshot": "../assets/mascotamas/turnos_laptop.png",
            "phone_screenshot": "../assets/mascotamas/turnos_phone.jpg",
            "showcase_caption": "Control total de horarios y turnos confirmados",
            "showcase_tag": "AGENDA 100%",
            "before_label": "SIN SISTEMA",
            "before_val": "Huecos en Agenda",
            "before_sub": "Turnos perdidos y tiempo muerto",
            "after_label": "MASCOTAMÁS",
            "after_val": "Agenda 100% Llena",
            "after_sub": "Turnos efectivos confirmados",
            "mascot_expression": "dizzy"
        }
    },
    {
        "scene_id": 5,
        "sentence_id": 5,
        "word_ids": list(range(47, 56)),
        "text": "Dejá de perder plata y suscribite a MascotaMás.",
        "layout_mode": "split_graphic",
        "is_hook": False,
        "is_cta": True,
        "top_title": None,
        "graphic_config": {
            "template": "chat_input",
            "pill": "EMPEZÁ HOY MISMO",
            "title": "Suscribite hoy a MascotaMás",
            "showcase_icon": "🐾",
            "laptop_screenshot": "../assets/mascotamas/escritorio_laptop.png",
            "phone_screenshot": "../assets/mascotamas/screenshot_1.png",
            "use_dual_phone_img": True,
            "showcase_caption": "Para veterinarias, peluquerías caninas y profesionales pet",
            "showcase_tag": "mascotamas.com",
            "prompt_text": "DEJÁ DE PERDER PLATA POR INASISTENCIAS",
            "reply_text": "Suscribite hoy a MascotaMás",
            "badge": "DEJÁ DE PERDER PLATA · ACTIVÁ TU CUENTA",
            "mascot_expression": "happy"
        }
    }
]

out_json = {
    "total_original_words": len(words),
    "kept_word_ids": [w["word_id"] for w in words_cleaned],
    "deleted_word_ids": [],
    "deleted_details": [],
    "cta_keyword": "MASCOTAMAS",
    "hook_title": hook_title,
    "cta_title": {
        "line1": "Sigue y comenta",
        "line2": "'MASCOTAMAS' 🐾",
        "keyword": "MASCOTAMAS",
        "emoji": "🐾"
    },
    "words_cleaned": words_cleaned,
    "scenes": scenes
}

with open(os.path.join(WORK_DIR, "guion_corregido.json"), "w", encoding="utf-8") as f:
    json.dump(out_json, f, ensure_ascii=False, indent=2)

print("[STEP 2 DONE] Guion corregido MascotaMás v2 (con capturas reales Laptop + iPhone) generado.")
