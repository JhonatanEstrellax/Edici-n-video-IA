# -*- coding: utf-8 -*-
import os
import sys
import json
import shutil
import subprocess

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

BASE_DIR = r"c:\IA\Edicion de videos"
WORK_DIR = os.path.join(BASE_DIR, "reels_work")
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
sys.path.insert(0, SCRIPTS_DIR)

from step3_plan_cuts import load_style, build_subtitle_blocks, is_highlighted_word
from step4_render_and_export import render_final_video

legal_tyc = "* Aplican posibles comisiones de Mercado Pago según las condiciones y plazos de acreditación de tu cuenta."
hook_title = {
    "line1": "LO NUEVO DE",
    "line2": "MASCOTAMÁS 🚀",
    "keyword": "MASCOTAMÁS",
    "emoji": "🚀"
}

def build_plan_for_version(ver_code: str, words_json_name: str, video_master_name: str, tts_synced_name: str, lyria_synced_name: str, scene_texts: list):
    shutil.copy2(os.path.join(WORK_DIR, video_master_name), os.path.join(WORK_DIR, "source_input.mp4"))
    shutil.copy2(os.path.join(WORK_DIR, tts_synced_name), os.path.join(WORK_DIR, "source_audio.wav"))

    with open(os.path.join(WORK_DIR, words_json_name), "r", encoding="utf-8") as f:
        wdata = json.load(f)

    raw_words = wdata["words"]
    transitions = wdata["transitions"]
    total_dur = float(wdata["duration"])

    scenes_def = [
        {
            "scene_id": 1,
            "sentence_id": 1,
            "word_ids": [w["word_id"] for w in raw_words if w["scene_id"] == 1],
            "text": scene_texts[0],
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
                "template": "checklist",
                "device_mode": "combo",
                "pill": "4 TIPOS DE CALENDARIO",
                "headline_kicker": "📅 MACBOOK PRO & IPHONE · 4 AGENDAS A MEDIDA",
                "headline_main": "🐾 TURNOS 1 A 1 Y CUPOS POR HORARIO",
                "laptop_screenshot": "../assets/mascotamas_v11/reel_mac_01_4_calendarios.png",
                "phone_screenshot": "../assets/mascotamas_v11/reel_iphone_02_servicios.png",
                "items": [
                    {"text": "Turnos Simples 1 a 1", "tag": "CONSULTORIO"},
                    {"text": "Cupos por Horario", "tag": "MÚLTIPLES CUPOS"},
                    {"text": "Múltiples Mascotas", "tag": "SIMULTÁNEO"}
                ],
                "mascot_expression": "happy"
            }
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

    style = load_style()
    cta_kw = "TURNOS"
    cooldown_min = 4.0
    last_bounce_time = -999.0

    words_cleaned = []
    edited_words = []
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
            "face_center": [0.5, 0.39]
        }
        nxt_str = raw_words[i + 1]["word"] if i + 1 < len(raw_words) else ""
        is_yel, can_bounce = is_highlighted_word(sub_txt, nxt_str, style, cta_kw)
        if any(k in sub_txt.lower() for k in ["mascotamás", "whatsapp", "4", "1", "servicios", "guardería", "seña", "mercado", "pago", "faltazos", "probalo"]):
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

    segments = [{
        "segment_id": 1,
        "source_start": 0.0,
        "source_end": total_dur,
        "duration": total_dur,
        "edited_start": 0.0,
        "edited_end": total_dur,
        "avg_rms_db": -16.0,
        "face_center": [0.5, 0.39],
        "word_ids": [w["word_id"] for w in words_cleaned]
    }]

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
        "bgm_override_path": os.path.join(WORK_DIR, lyria_synced_name),
        "bgm_relative_db": -13.5,
        "bgm_ducking_db": -6.5,
        "original_duration_sec": total_dur,
        "edited_duration_sec": total_dur,
        "motion_graphics_coverage_ratio": mg_ratio,
        "cta_keyword": cta_kw,
        "hook_title": hook_title,
        "cta_title": guion_json["cta_title"],
        "face_metadata": {
            "default_face_center": [0.5, 0.39],
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
    with open(os.path.join(WORK_DIR, f"edit_plan_{ver_code}.json"), "w", encoding="utf-8") as f:
        json.dump(edit_plan, f, ensure_ascii=False, indent=2)

    print(f"[{ver_code} PLAN READY] MG={mg_ratio*100:.1f}%, Blocks={len(subtitle_blocks)}")


if __name__ == "__main__":
    # 1. Renderizar Versión A (v4A - Guion Directo sin "para paseos")
    out_v4A = os.path.join(
        BASE_DIR, "editados",
        "Reel Publicitario - Lo Nuevo de MascotaMas Calendarios y Mercado Pago (v4A - Guion Directo + Veterinaria Sexy LipSync + Lyria 3 House).mp4"
    )
    bruto_v4A = os.path.join(
        BASE_DIR, "brutos",
        "Reel Publicitario - Lo Nuevo de MascotaMas Calendarios y Mercado Pago (v4A - Bruto Veterinaria Sexy LipSync).mp4"
    )
    build_plan_for_version(
        "v4A",
        "v4A_words_synced.json",
        "v4A_vet_lipsync_master.mp4",
        "v4A_tts_synced.wav",
        "v4A_lyria_synced.wav",
        [
            "¡Mirá lo nuevo de MascotaMás para tu veterinaria, peluquería o guardería!",
            "Ahora tenés 4 tipos de calendario: Turnos Simples 1 a 1, y Cupos por Horario.",
            "También agendas por Servicios y Profesionales, con grilla automática sin huecos,",
            "y Calendario de Guardería por rango de fechas, con sectores de ingreso y egreso.",
            "Activás el cobro de seña automático con Mercado Pago para asegurar cada turno.",
            "¡Entrá hoy en MascotaMás y probalo!"
        ]
    )
    render_final_video(out_v4A)
    shutil.copy2(os.path.join(WORK_DIR, "v4A_vet_lipsync_master.mp4"), bruto_v4A)
    subprocess.run([sys.executable, os.path.join(SCRIPTS_DIR, "step5_verify.py")], check=True)
    shutil.copy2(os.path.join(WORK_DIR, "verification_grid.jpg"), os.path.join(WORK_DIR, "verification_grid_v4A.jpg"))

    # 2. Renderizar Versión B (v4B - Guion Storytelling Comercial sin "para paseos")
    out_v4B = os.path.join(
        BASE_DIR, "editados",
        "Reel Publicitario - Lo Nuevo de MascotaMas Calendarios y Mercado Pago (v4B - Guion Storytelling Comercial + Veterinaria Sexy LipSync + Lyria 3 House).mp4"
    )
    bruto_v4B = os.path.join(
        BASE_DIR, "brutos",
        "Reel Publicitario - Lo Nuevo de MascotaMas Calendarios y Mercado Pago (v4B - Bruto Veterinaria Sexy LipSync).mp4"
    )
    build_plan_for_version(
        "v4B",
        "v4B_words_synced.json",
        "v4B_vet_lipsync_master.mp4",
        "v4B_tts_synced.wav",
        "v4B_lyria_synced.wav",
        [
            "¿Perdés turnos por WhatsApp en tu veterinaria, peluquería o guardería? ¡Mirá lo nuevo de MascotaMás!",
            "Elegí entre 4 agendas inteligentes: Turnos Simples 1 a 1, o Cupos por Horario.",
            "También agendas por Servicios y Profesionales, con grilla automática sin huecos,",
            "y Calendario de Guardería por rango de fechas, con sectores de ingreso y egreso.",
            "¿Lo mejor? Cobrás seña automática con Mercado Pago y te olvidás de los faltazos.",
            "¡Entrá hoy en MascotaMás y probalo!"
        ]
    )
    render_final_video(out_v4B)
    shutil.copy2(os.path.join(WORK_DIR, "v4B_vet_lipsync_master.mp4"), bruto_v4B)
    subprocess.run([sys.executable, os.path.join(SCRIPTS_DIR, "step5_verify.py")], check=True)
    shutil.copy2(os.path.join(WORK_DIR, "verification_grid.jpg"), os.path.join(WORK_DIR, "verification_grid_v4B.jpg"))
    print("\n¡AMBOS VIDEOS (v4A y v4B) RENDERIZADOS Y VERIFICADOS CON ÉXITO!")
