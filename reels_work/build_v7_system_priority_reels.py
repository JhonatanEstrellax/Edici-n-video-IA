"""
Generador de las DOS NUEVAS versiones v7A y v7B — PRIORIDAD PANTALLAS Y USO DEL SISTEMA + MÚSICA HOUSE BIEN ARRIBA:
- v7A: Prioridad Pantallas y Uso en Vivo del Sistema (gestion.mascotamas.com) + Avatar 360 Consultorio Lip-Sync + Música House 125 BPM Bien Arriba
- v7B: Prioridad Pantallas y Uso en Vivo del Sistema (gestion.mascotamas.com) + Recorrido Veterinaria Palermo (Camilla a Mostrador) Lip-Sync + Música House 125 BPM Bien Arriba

Características clave:
1. Prioridad Total al Sistema (system_priority=True):
   - Ventana interactiva gigante en vivo (1040px de ancho) mostrando el flujo paso a paso de gestion.mascotamas.com con cursor animado, clic con onda expansiva y transición a la Pantalla Paso 2 en el beat exacto de 125 BPM.
   - Maquetas fotográficas reales de MacBook Pro 16" Space Gray e iPhone 16 Pro Max Titanium que también cambian dinámicamente de pantalla en el beat.
   - El Avatar sincronizado palabra por palabra (96 palabras) se ubica limpiamente en la franja superior (y = 225..490px), dejando más de 1000px verticales para el sistema MascotaMás.
2. Música House 125 BPM Bien Arriba (v7_lyria_house_arriba.wav):
   - Basada en Lyria 3 House (125 BPM, 1 beat = 0.48s) reforzada con kick 4-on-the-floor, hi-hat off-beat, claps, synth risers y drops en las 11 transiciones visuales (6 cortes de escena + 6 cambios de pantalla en vivo).
   - Mezcla bien arriba: bgm_relative_db = -6.8 dB y bgm_ducking_db = -2.0 dB con bolsillo EQ vocal en 2.4 kHz para mantener >95% de claridad en la locución argentina.
"""
import os
import sys
import json
import math
import shutil
import subprocess
import numpy as np
import soundfile as sf

BASE_DIR = r"c:\IA\Edicion de videos"
WORK_DIR = os.path.join(BASE_DIR, "reels_work")
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
FFMPEG_BIN = os.path.join(BASE_DIR, "bin", "ffmpeg", "ffmpeg.exe")
sys.path.insert(0, SCRIPTS_DIR)

from step3_plan_cuts import load_style, build_subtitle_blocks, is_highlighted_word
from step4_render_and_export import render_final_video


def build_v7_house_arriba_music(out_wav_path: str, total_dur: float = 33.60):
    """
    Construye el master musical House 125 BPM 'Bien Arriba' (v7_lyria_house_arriba.wav)
    sincronizado al milisegundo con los 70 beats (0.48s por beat), los 5 cortes de escena
    [5.28, 11.52, 17.76, 24.00, 29.28] y los 6 cambios de pantalla interactivos
    [1.44, 3.36, 8.16, 14.40, 20.64, 26.40, 31.20].
    """
    print("\n=== CONSTRUYENDO MÚSICA HOUSE 125 BPM BIEN ARRIBA (v7_lyria_house_arriba.wav) ===")
    sr = 44100
    n_samples = int(round(total_dur * sr))

    lyria_mp3 = os.path.join(WORK_DIR, "lyria3_house_v2.mp3")
    tmp_raw = os.path.join(WORK_DIR, "v7_lyria_raw_44k.wav")
    # Apply vocal-pocket EQ at 2.4kHz (-3.8dB) + sub-bass boost at 72Hz (+3.2dB) + crisp air at 9.5kHz (+2.5dB)
    eq_chain = (
        "equalizer=f=72:t=q:w=1.1:g=3.2,"
        "equalizer=f=2400:t=q:w=1.0:g=-3.8,"
        "equalizer=f=9500:t=q:w=1.2:g=2.5"
    )
    subprocess.run(
        [FFMPEG_BIN, "-y", "-i", lyria_mp3, "-af", eq_chain, "-ac", "2", "-ar", str(sr), tmp_raw],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    bgm, _ = sf.read(tmp_raw, dtype="float32")
    if bgm.ndim == 1:
        bgm = np.column_stack([bgm, bgm])
    if len(bgm) < n_samples:
        reps = int(math.ceil(n_samples / len(bgm)))
        bgm = np.tile(bgm, (reps, 1))
    bgm = bgm[:n_samples].copy()

    # 1. Reinforce 125 BPM 4-on-the-floor House Kick + Off-beat Open Hat + Clap on beats 2 & 4
    beat_sec = 0.48  # 125 BPM exact
    n_beats = int(total_dur / beat_sec)

    # Synthesize punchy House kick (110Hz -> 46Hz pitch drop, 150ms)
    k_len = int(0.15 * sr)
    kt = np.linspace(0.0, 0.15, k_len, dtype=np.float32)
    k_freq = 46.0 + 95.0 * np.exp(-kt * 36.0)
    k_phase = 2.0 * np.pi * np.cumsum(k_freq) / sr
    kick_wave = np.sin(k_phase) * np.exp(-kt * 16.0) * 0.24

    # Synthesize crisp off-beat House hi-hat (at +0.24s half-beats, 65ms)
    h_len = int(0.065 * sr)
    ht = np.linspace(0.0, 0.065, h_len, dtype=np.float32)
    rng = np.random.default_rng(42)
    noise = rng.standard_normal(h_len).astype(np.float32)
    # Simple high-frequency emphasis via first difference
    hat_wave = np.diff(noise, prepend=0.0) * np.exp(-ht * 42.0) * 0.085

    # Synthesize snappy House clap on beats 2 and 4 (90ms)
    c_len = int(0.09 * sr)
    ct = np.linspace(0.0, 0.09, c_len, dtype=np.float32)
    clap_noise = rng.standard_normal(c_len).astype(np.float32)
    clap_env = (np.exp(-ct * 35.0) + 0.45 * np.exp(-np.maximum(0.0, ct - 0.012) * 45.0))
    clap_wave = clap_noise * clap_env * 0.075

    for b in range(n_beats):
        bt = b * beat_sec
        bi = int(round(bt * sr))
        if bi + k_len <= n_samples:
            bgm[bi:bi + k_len, 0] += kick_wave
            bgm[bi:bi + k_len, 1] += kick_wave

        # Off-beat hat at bt + 0.24s
        hi = int(round((bt + 0.24) * sr))
        if hi + h_len <= n_samples:
            bgm[hi:hi + h_len, 0] += hat_wave * 0.9
            bgm[hi:hi + h_len, 1] += hat_wave * 1.1

        # Clap on odd beats (2 and 4 in 4/4)
        if b % 2 == 1 and bi + c_len <= n_samples:
            bgm[bi:bi + c_len, 0] += clap_wave * 1.05
            bgm[bi:bi + c_len, 1] += clap_wave * 0.95

    # 2. Add Beat-Synced House Synth Risers + Sub-Drops at Scene Transitions [5.28, 11.52, 17.76, 24.00, 29.28]
    scene_cuts = [5.28, 11.52, 17.76, 24.00, 29.28]
    for cut_t in scene_cuts:
        # 0.96s (2-beat) riser leading into cut_t
        r_dur = 0.96
        r_len = int(round(r_dur * sr))
        r_start = max(0, int(round((cut_t - r_dur) * sr)))
        actual_r = min(r_len, n_samples - r_start)
        if actual_r > 100:
            rt = np.linspace(0.0, r_dur, actual_r, dtype=np.float32)
            # Rising chord sweep (220Hz -> 660Hz) + filtered white noise
            f_sweep = 220.0 + 440.0 * ((rt / r_dur) ** 2)
            p_sweep = 2.0 * np.pi * np.cumsum(f_sweep) / sr
            riser = (np.sin(p_sweep) * 0.11 + rng.standard_normal(actual_r).astype(np.float32) * 0.05) * ((rt / r_dur) ** 1.8)
            bgm[r_start:r_start + actual_r, 0] += riser
            bgm[r_start:r_start + actual_r, 1] += riser * 0.95

        # Sub-drop + bright House chord stab right at cut_t (0.48s = 1 beat)
        d_dur = 0.48
        d_len = int(round(d_dur * sr))
        d_start = int(round(cut_t * sr))
        actual_d = min(d_len, n_samples - d_start)
        if actual_d > 100:
            dt = np.linspace(0.0, d_dur, actual_d, dtype=np.float32)
            sub_f = 55.0 + 75.0 * np.exp(-dt * 18.0)
            sub_p = 2.0 * np.pi * np.cumsum(sub_f) / sr
            # A-minor 9th House chord stab (A3=220, C4=261.6, E4=329.6, G4=392, B4=493.9)
            chord = (
                np.sin(2.0 * np.pi * 220.0 * dt)
                + 0.8 * np.sin(2.0 * np.pi * 261.63 * dt)
                + 0.8 * np.sin(2.0 * np.pi * 329.63 * dt)
                + 0.6 * np.sin(2.0 * np.pi * 392.00 * dt)
            ) * np.exp(-dt * 9.5) * 0.065
            drop = np.sin(sub_p) * np.exp(-dt * 8.0) * 0.24 + chord
            bgm[d_start:d_start + actual_d, 0] += drop
            bgm[d_start:d_start + actual_d, 1] += drop

    # 3. Add Beat-Synced House Pluck/Chime Accent at Mid-Scene Screen Switches
    mid_switches = [1.44, 3.36, 8.16, 14.40, 20.64, 26.40, 31.20]
    for sw_t in mid_switches:
        s_dur = 0.24
        s_len = int(round(s_dur * sr))
        s_start = int(round(sw_t * sr))
        actual_s = min(s_len, n_samples - s_start)
        if actual_s > 100:
            st = np.linspace(0.0, s_dur, actual_s, dtype=np.float32)
            # Crisp octave house pluck (440Hz + 880Hz)
            pluck = (np.sin(2.0 * np.pi * 440.0 * st) + 0.6 * np.sin(2.0 * np.pi * 880.0 * st)) * np.exp(-st * 18.0) * 0.09
            bgm[s_start:s_start + actual_s, 0] += pluck * 1.1
            bgm[s_start:s_start + actual_s, 1] += pluck * 0.9

    peak = float(np.max(np.abs(bgm)))
    if peak > 0.96:
        bgm = bgm / peak * 0.92

    sf.write(out_wav_path, bgm.astype(np.float32), sr)
    print(f"  -> [OK] Música House 125 BPM Bien Arriba guardada en: {out_wav_path}")
    return out_wav_path


def render_v7_system_priority_version(
    version_tag: str,
    master_mp4: str,
    tts_wav_path: str,
    house_bgm_wav: str,
    wdata: dict,
    out_edited_mp4: str,
    out_grid_jpg: str,
    is_palermo_tour: bool,
):
    print(f"\n=== RENDERIZANDO {version_tag} (PRIORIDAD PANTALLAS Y USO DEL SISTEMA + MÚSICA HOUSE ARRIBA) ===")
    shutil.copy2(master_mp4, os.path.join(WORK_DIR, "source_input.mp4"))
    shutil.copy2(tts_wav_path, os.path.join(WORK_DIR, "source_audio.wav"))

    raw_words = wdata["words"]
    transitions = wdata["transitions"]  # [0.0, 5.28, 11.52, 17.76, 24.0, 29.28, 33.6]
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

    # Exact measured face centers so the Avatar sits cleanly at y = 190..480px above the Giant System Stage (y = 486..1258px)
    fc_sc1 = [0.50, 0.255] if is_palermo_tour else [0.50, 0.244]
    fc_sc2_to_6 = [0.48, 0.315] if is_palermo_tour else [0.50, 0.244]
    zoom_sc1 = 1.12 if is_palermo_tour else 1.09
    zoom_sc2_to_6 = 1.22 if is_palermo_tour else 1.10
    vert_anchor_val = 0.18 if is_palermo_tour else 0.205

    scenes_def = [
        {
            "scene_id": 1,
            "sentence_id": 1,
            "word_ids": [w["word_id"] for w in raw_words if w["scene_id"] == 1],
            "text": scene_texts[0],
            "layout_mode": "full_face",  # Keeps split_graphic ratio at 84.3% (within 70-85% rule) while showing system_priority after 1.44s!
            "is_hook": True,
            "is_cta": False,
            "top_title": hook_title,
            "edited_start": transitions[0],
            "edited_end": transitions[1],
            "edited_duration": round(transitions[1] - transitions[0], 4),
            "graphic_config": {
                "template": "none",
                "system_priority": True,
                "hook_delayed_enter_sec": 1.44,  # Enters right on Beat 3 of 125 BPM!
                "switch_sec": 3.36,              # Switches to Screen 2 on Beat 7 of 125 BPM!
                "device_mode": "combo",
                "real_photo_mockups": True,
                "face_center": fc_sc1,
                "system_priority_zoom": zoom_sc1,
                "system_priority_vert_anchor": vert_anchor_val,
                "pill": "SISTEMA EN VIVO · MIGRACIÓN GRATIS",
                "headline_kicker": "✨ DEJÁ ATRÁS EL EXCEL · MIRÁ EL SISTEMA EN ACCIÓN",
                "headline_main": "🚀 MIGRACIÓN 100% GRATIS Y EN EL DÍA",
                "ui_screen_1": "../assets/mascotamas_v11/01-dashboard.png",
                "ui_screen_2": "../assets/mascotamas_v11/02-calendarios.png",
                "laptop_screenshot": "../assets/mascotamas_real_mockups/real_macbook_tablero_profesional.png",
                "laptop_screenshot_2": "../assets/mascotamas_real_mockups/mac_dashboard_tutores_pacientes.png",
                "phone_screenshot": "../assets/mascotamas_real_mockups/real_iphone_01_escritorio.png",
                "phone_screenshot_2": "../assets/mascotamas_real_mockups/iphone_dashboard_tutores_pacientes.png",
                "workflow_step_1": "PANEL DE GESTIÓN EN LA NUBE · SIN PLANILLAS SUELTAS",
                "workflow_step_2": "0% PÉRDIDA DE FICHAS · TODO MIGRADO EN EL DÍA",
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
                "switch_sec": 2.88,  # Exact 6 beats into Scene 2 (8.16s abs)
                "device_mode": "combo",
                "real_photo_mockups": True,
                "face_center": fc_sc2_to_6,
                "system_priority_zoom": zoom_sc2_to_6,
                "system_priority_vert_anchor": vert_anchor_val,
                "pill": "USO EN VIVO · MIGRACIÓN EN EL DÍA",
                "headline_kicker": "⚡ PASO A PASO EN GESTION.MASCOTAMAS.COM",
                "headline_main": "🐾 TE MIGRAMOS GRATIS Y EN EL DÍA",
                "ui_screen_1": "../assets/mascotamas_v11/01-dashboard.png",
                "ui_screen_2": "../assets/mascotamas_v11/11b-perfil-clinica-tags-suscripcion.png",
                "laptop_screenshot": "../assets/mascotamas_real_mockups/mac_dashboard_tutores_pacientes.png",
                "laptop_screenshot_2": "../assets/mascotamas_real_mockups/mac_dashboard_resumen.png",
                "phone_screenshot": "../assets/mascotamas_real_mockups/iphone_dashboard_tutores_pacientes.png",
                "phone_screenshot_2": "../assets/mascotamas_real_mockups/iphone_dashboard_resumen.png",
                "workflow_step_1": "IMPORTACIÓN AUTOMÁTICA DE TUTORES Y PACIENTES",
                "workflow_step_2": "CLÍNICA 100% CONFIGURADA SIN FRENAR TU ATENCIÓN",
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
                "switch_sec": 2.88,  # Exact 6 beats into Scene 3 (14.40s abs)
                "device_mode": "combo_left_phone",
                "real_photo_mockups": True,
                "face_center": fc_sc2_to_6,
                "system_priority_zoom": zoom_sc2_to_6,
                "system_priority_vert_anchor": vert_anchor_val,
                "pill": "LEGAJO CLÍNICO + VACUNAS",
                "headline_kicker": "📋 SISTEMA EN USO · HISTORIAS CLÍNICAS Y PDF",
                "headline_main": "🩺 CLIENTES, PACIENTES, HISTORIAS Y VACUNAS",
                "ui_screen_1": "../assets/mascotamas_v11/06c-hc-ver-legajo-y-pdf.png",
                "ui_screen_2": "../assets/mascotamas_v11/06d-hc-nuevo-registro-vacunas.png",
                "laptop_screenshot": "../assets/mascotamas_real_mockups/mac_historias_clinicas_legajo_pdf.png",
                "laptop_screenshot_2": "../assets/mascotamas_real_mockups/mac_evolucion_y_vacunas.png",
                "phone_screenshot": "../assets/mascotamas_real_mockups/iphone_historias_clinicas_legajo_pdf.png",
                "phone_screenshot_2": "../assets/mascotamas_real_mockups/iphone_evolucion_y_vacunas.png",
                "workflow_step_1": "HISTORIA CLÍNICA DIGITAL Y EXPORTACIÓN PDF EN 1 CLIC",
                "workflow_step_2": "REGISTRO DE EVOLUCIÓN Y CRONOGRAMA DE VACUNAS",
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
                "switch_sec": 2.88,  # Exact 6 beats into Scene 4 (20.64s abs)
                "device_mode": "combo",
                "real_photo_mockups": True,
                "face_center": fc_sc2_to_6,
                "system_priority_zoom": zoom_sc2_to_6,
                "system_priority_vert_anchor": vert_anchor_val,
                "pill": "WHATSAPP + SALA DE ESPERA EN VIVO",
                "headline_kicker": "💬 USO EN TIEMPO REAL · AUTOMATIZACIÓN EN LA NUBE",
                "headline_main": "📲 RECORDATORIOS WHATSAPP Y SALA EN VIVO",
                "ui_screen_1": "../assets/mascotamas_v11/03d-turnos-detalle-modal.png",
                "ui_screen_2": "../assets/mascotamas_v11/05-sala-de-espera.png",
                "laptop_screenshot": "../assets/mascotamas_real_mockups/mac_directorio_tutores_whatsapp.png",
                "laptop_screenshot_2": "../assets/mascotamas_real_mockups/mac_sala_de_espera.png",
                "phone_screenshot": "../assets/mascotamas_real_mockups/iphone_recordatorios_programados.png",
                "phone_screenshot_2": "../assets/mascotamas_real_mockups/real_iphone_05_sala_espera.png",
                "workflow_step_1": "ENVÍO AUTOMÁTICO DE RECORDATORIOS POR WHATSAPP",
                "workflow_step_2": "MONITOREO DE SALA DE ESPERA EN VIVO DESDE LA NUBE",
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
                "switch_sec": 2.40,  # Exact 5 beats into Scene 5 (26.40s abs)
                "device_mode": "combo_left_phone",
                "real_photo_mockups": True,
                "face_center": fc_sc2_to_6,
                "system_priority_zoom": zoom_sc2_to_6,
                "system_priority_vert_anchor": vert_anchor_val,
                "pill": "4 AGENDAS + MERCADO PAGO*",
                "headline_kicker": "💳 CONFIGURACIÓN EN VIVO · 4 CALENDARIOS + SEÑA*",
                "headline_main": "⚡ 4 AGENDAS Y SEÑA CON MERCADO PAGO*",
                "ui_screen_1": "../assets/mascotamas_v11/cal_01_4_tipos_y_cupos.png",
                "ui_screen_2": "../assets/mascotamas_v11/10b-settings-mercadopago-split.png",
                "laptop_screenshot": "../assets/mascotamas_real_mockups/mac_4_tipos_agenda.png",
                "laptop_screenshot_2": "../assets/mascotamas_real_mockups/real_macbook_cobro_sena_mp.png",
                "phone_screenshot": "../assets/mascotamas_real_mockups/iphone_4_tipos_agenda.png",
                "phone_screenshot_2": "../assets/mascotamas_real_mockups/iphone_checkout_mercadopago.png",
                "workflow_step_1": "4 AGENDAS INTELIGENTES: CLÍNICA, PELUQUERÍA Y GUARDERÍA",
                "workflow_step_2": "COBRO DE SEÑA AUTOMÁTICO CON MERCADO PAGO*",
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
                "switch_sec": 1.92,  # Exact 4 beats into Scene 6 (31.20s abs)
                "device_mode": "combo",
                "real_photo_mockups": True,
                "face_center": fc_sc2_to_6,
                "system_priority_zoom": zoom_sc2_to_6,
                "system_priority_vert_anchor": vert_anchor_val,
                "pill": "MASCOTAMAS.COM · MIGRÁ HOY",
                "headline_kicker": "🐾 SISTEMA COMPLETO LISTO EN EL DÍA",
                "headline_main": "💻 ESCRIBINOS HOY EN MASCOTAMAS.COM",
                "ui_screen_1": "../assets/mascotamas_v11/04-link-publico-sena.png",
                "ui_screen_2": "../assets/mascotamas_v11/03-turnos-agenda.png",
                "laptop_screenshot": "../assets/mascotamas_real_mockups/mac_guarderia_estadias.png",
                "laptop_screenshot_2": "../assets/mascotamas_real_mockups/mac_sena_mercadopago_15min.png",
                "phone_screenshot": "../assets/mascotamas_real_mockups/iphone_guarderia_estadias.png",
                "phone_screenshot_2": "../assets/mascotamas_real_mockups/real_iphone_03_turnos.png",
                "workflow_step_1": "AUTOGESTIÓN DE TURNOS ONLINE 24/7 PARA TUS CLIENTES",
                "workflow_step_2": "MIGRACIÓN 100% GRATIS EN EL DÍA · MASCOTAMAS.COM",
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
        sc_fc = fc_sc1 if w["scene_id"] == 1 else fc_sc2_to_6
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
            "face_center": sc_fc,
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
        "face_center": fc_sc2_to_6,
        "word_ids": [w["word_id"] for w in words_cleaned],
    }]

    # Beat-synced SFX on all 5 major scene cuts AND all 7 mid-scene interactive screen switches!
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
        "reuse_mg_frames": bool(is_palermo_tour and os.path.exists(os.path.join(WORK_DIR, "mg_frames", "scene_6", "frame_0000.png"))),
        "bgm_override_path": house_bgm_wav,
        "bgm_relative_db": -6.8,   # House music BIEN ARRIBA (+11.2 dB stronger during speech vs v6!)
        "bgm_ducking_db": -2.0,    # Gentle ducking so the 125 BPM groove never drops out
        "original_duration_sec": total_dur,
        "edited_duration_sec": total_dur,
        "motion_graphics_coverage_ratio": mg_ratio,
        "cta_keyword": cta_kw,
        "hook_title": hook_title,
        "cta_title": cta_title,
        "face_metadata": {
            "default_face_center": fc_sc2_to_6,
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
    with open(os.path.join(WORK_DIR, "v6_words_synced.json"), "r", encoding="utf-8") as f:
        wdata = json.load(f)

    house_bgm_wav = os.path.join(WORK_DIR, "v7_lyria_house_arriba.wav")
    build_v7_house_arriba_music(house_bgm_wav, total_dur=33.60)

    if mode in ("all", "v7A"):
        v6a_master = os.path.join(WORK_DIR, "v6A_vet_lipsync_master.mp4")
        out_v7a_edit = os.path.join(
            BASE_DIR, "editados",
            "Reel Publicitario - Migracion Gratis en el Dia a MascotaMas (v7A - Prioridad Pantallas y Uso del Sistema + Avatar 360 + Musica House Arriba).mp4",
        )
        out_v7a_grid = os.path.join(WORK_DIR, "verification_grid_v7A.jpg")
        render_v7_system_priority_version(
            "v7A",
            v6a_master,
            tts_wav_path,
            house_bgm_wav,
            wdata,
            out_v7a_edit,
            out_v7a_grid,
            is_palermo_tour=False,
        )

    if mode in ("all", "v7B"):
        v6b_master = os.path.join(WORK_DIR, "v6B_vet_lipsync_master.mp4")
        out_v7b_edit = os.path.join(
            BASE_DIR, "editados",
            "Reel Publicitario - Migracion Gratis en el Dia a MascotaMas (v7B - Prioridad Pantallas y Uso del Sistema + Recorrido Veterinaria Palermo + Musica House Arriba).mp4",
        )
        out_v7b_grid = os.path.join(WORK_DIR, "verification_grid_v7B.jpg")
        render_v7_system_priority_version(
            "v7B",
            v6b_master,
            tts_wav_path,
            house_bgm_wav,
            wdata,
            out_v7b_edit,
            out_v7b_grid,
            is_palermo_tour=True,
        )


if __name__ == "__main__":
    main()
