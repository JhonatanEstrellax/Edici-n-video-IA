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
    "line1": "MIGRACIÓN GRATIS",
    "line2": "EN EL DÍA 🚀",
    "keyword": "GRATIS",
    "emoji": "🚀"
}

def build_and_render_v6():
    shutil.copy2(os.path.join(WORK_DIR, "v6_vet_lipsync_master.mp4"), os.path.join(WORK_DIR, "source_input.mp4"))
    shutil.copy2(os.path.join(WORK_DIR, "v6_tts_synced.wav"), os.path.join(WORK_DIR, "source_audio.wav"))

    with open(os.path.join(WORK_DIR, "v6_words_synced.json"), "r", encoding="utf-8") as f:
        wdata = json.load(f)

    raw_words = wdata["words"]
    transitions = wdata["transitions"]
    total_dur = float(wdata["duration"])

    scene_texts = [
        "¿Seguís atado a un sistema viejo o al Excel por miedo a perder los datos de tu veterinaria?",
        "¡Pasate hoy a MascotaMás! Te hacemos toda la migración gratis y en el día, sin frenar tu consultorio.",
        "Pasamos tus clientes, pacientes, historias clínicas y vacunas para que no pierdas ni una sola ficha.",
        "En horas ya tenés recordatorios automáticos por WhatsApp, sala de espera en vivo y todo en la nube.",
        "Además, sumás las 4 agendas inteligentes y el cobro de seña automático con Mercado Pago*.",
        "¡Escribinos hoy en MascotaMás y te migramos gratis en el día!"
    ]

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
                "pill": "MASCOTAMÁS · MIGRACIÓN GRATIS",
                "headline_kicker": "✨ PASATE SIN MIEDO · GESTIÓN INTEGRAL PET",
                "headline_main": "🚀 MIGRACIÓN 100% GRATIS Y EN EL DÍA",
                "mascot_expression": "surprised"
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
                "template": "before_after",
                "device_mode": "combo",
                "real_photo_mockups": True,
                "pill": "MIGRACIÓN EN EL DÍA · $0",
                "headline_kicker": "⚡ SIN FRENAR TU CONSULTORIO · MACBOOK PRO & IPHONE",
                "headline_main": "🐾 TE MIGRAMOS GRATIS Y EN EL DÍA",
                "laptop_screenshot": "../assets/mascotamas_real_mockups/mac_dashboard_tutores_pacientes.png",
                "phone_screenshot": "../assets/mascotamas_real_mockups/iphone_dashboard_tutores_pacientes.png",
                "before_label": "SISTEMA VIEJO / EXCEL",
                "before_value": "Miedo a Perder Datos",
                "before_desc": "Planillas sueltas y tiempo perdido",
                "after_label": "CON MASCOTAMÁS",
                "after_value": "Migración en el Día",
                "after_desc": "100% Gratis y sin frenar tu clínica",
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
                "real_photo_mockups": True,
                "pill": "HISTORIAS CLÍNICAS Y VACUNAS",
                "headline_kicker": "📋 CERO PÉRDIDA DE INFORMACIÓN · LEGAJO DIGITAL",
                "headline_main": "🩺 CLIENTES, PACIENTES, HISTORIAS Y VACUNAS",
                "laptop_screenshot": "../assets/mascotamas_real_mockups/mac_historias_clinicas_legajo_pdf.png",
                "phone_screenshot": "../assets/mascotamas_real_mockups/iphone_evolucion_y_vacunas.png",
                "items": [
                    {"text": "Clientes y Pacientes", "tag": "100% MIGRADO"},
                    {"text": "Historias Clínicas PDF", "tag": "SIN PERDER FICHAS"},
                    {"text": "Historial de Vacunas", "tag": "COMPLETO"}
                ],
                "mascot_expression": "happy"
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
                "template": "app_connection",
                "device_mode": "combo",
                "real_photo_mockups": True,
                "pill": "WHATSAPP + SALA DE ESPERA",
                "headline_kicker": "💬 AUTOMATIZACIÓN EN HORAS · WEB & APP",
                "headline_main": "📲 RECORDATORIOS WHATSAPP Y SALA EN VIVO",
                "laptop_screenshot": "../assets/mascotamas_real_mockups/mac_directorio_tutores_whatsapp.png",
                "phone_screenshot": "../assets/mascotamas_real_mockups/real_iphone_05_sala_espera.png",
                "icon_a": "🏥",
                "app_a": "Sala en Vivo",
                "sub_a": "Fichas en la Nube 24/7",
                "status": "✓ EN EL DÍA",
                "app_b": "WhatsApp",
                "sub_b": "Recordatorios Automáticos",
                "mascot_expression": "surprised"
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
                "real_photo_mockups": True,
                "pill": "4 AGENDAS + MERCADO PAGO*",
                "headline_kicker": "💳 4 CALENDARIOS + COBRO AUTOMATIZADO ONLINE*",
                "headline_main": "⚡ 4 AGENDAS Y SEÑA CON MERCADO PAGO*",
                "laptop_screenshot": "../assets/mascotamas_real_mockups/real_macbook_cobro_sena_mp.png",
                "phone_screenshot": "../assets/mascotamas_real_mockups/iphone_4_tipos_agenda.png",
                "items": [
                    {"text": "4 Agendas Inteligentes", "tag": "SIN HUECOS"},
                    {"text": "Seña Mercado Pago*", "tag": "TURNOS SEGUROS"},
                    {"text": "Cero Inasistencias", "tag": "24/7 ONLINE"}
                ],
                "legal_disclaimer": legal_tyc,
                "mascot_expression": "happy"
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
                "device_mode": "none",
                "pill": "MASCOTAMAS.COM · MIGRÁ HOY",
                "headline_kicker": "🐾 CAMBIATE HOY SIN FRENAR TU VETERINARIA",
                "headline_main": "💻 ESCRIBINOS HOY EN MASCOTAMAS.COM",
                "prompt_text": "MIGRACIÓN 100% GRATIS Y EN EL DÍA",
                "reply_text": "Entrá en mascotamas.com o comentá MIGRAR",
                "badge": "MASCOTAMAS.COM · MIGRACIÓN GRATIS",
                "legal_disclaimer": legal_tyc,
                "mascot_expression": "happy"
            }
        }
    ]

    style = load_style()
    cta_kw = "MIGRAR"
    cooldown_min = 4.0
    last_bounce_time = -999.0

    words_cleaned = []
    edited_words = []
    hl_terms = [
        "excel", "miedo", "veterinaria", "mascotamás", "migración", "gratis", "día",
        "clientes", "pacientes", "historias", "clínicas", "vacunas", "ficha",
        "recordatorios", "automáticos", "whatsapp", "vivo", "nube",
        "4", "agendas", "inteligentes", "seña", "mercado", "pago", "migramos"
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
            "face_center": [0.5, 0.22]
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
        "cta_title": {
            "line1": "Te migramos gratis en",
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
        "face_center": [0.5, 0.36],
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
        "bgm_override_path": os.path.join(WORK_DIR, "v6_lyria_synced.wav"),
        "bgm_relative_db": -13.5,
        "bgm_ducking_db": -6.5,
        "original_duration_sec": total_dur,
        "edited_duration_sec": total_dur,
        "motion_graphics_coverage_ratio": mg_ratio,
        "cta_keyword": cta_kw,
        "hook_title": hook_title,
        "cta_title": guion_json["cta_title"],
        "face_metadata": {
            "default_face_center": [0.5, 0.22],
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
    with open(os.path.join(WORK_DIR, "edit_plan_v6_migracion.json"), "w", encoding="utf-8") as f:
        json.dump(edit_plan, f, ensure_ascii=False, indent=2)

    print(f"[V6 MIGRACION PLAN READY] Dur={total_dur:.2f}s, MG={mg_ratio*100:.1f}%, Blocks={len(subtitle_blocks)}")

    out_v6 = os.path.join(
        BASE_DIR, "editados",
        "Reel Publicitario - Migracion Gratis en el Dia a MascotaMas (v6 - Storytelling Argentino + Nuevo Avatar 360 Gemini 3 Pro + Maquetas Reales MacBook y iPhone + Lyria 3).mp4"
    )
    bruto_v6 = os.path.join(
        BASE_DIR, "brutos",
        "Reel Publicitario - Migracion Gratis en el Dia a MascotaMas (v6 - Bruto Nuevo Avatar 360 LipSync).mp4"
    )
    render_final_video(out_v6)
    shutil.copy2(os.path.join(WORK_DIR, "v6_vet_lipsync_master.mp4"), bruto_v6)
    subprocess.run([sys.executable, os.path.join(SCRIPTS_DIR, "step5_verify.py"), out_v6], check=True)
    shutil.copy2(os.path.join(BASE_DIR, "verification_grid.jpg"), os.path.join(WORK_DIR, "verification_grid_v6_migracion.jpg"))
    print(f"\n¡VIDEO V6 RENDERIZADO Y VERIFICADO CON ÉXITO!\n -> {out_v6}")

if __name__ == "__main__":
    build_and_render_v6()
