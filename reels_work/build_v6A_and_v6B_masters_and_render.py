# -*- coding: utf-8 -*-
"""
Une sin costuras los 4 turnos Multi-Turn (0-10s, 10-20s, 20-30s, 30-36s = 864 fotogramas / 36.00s @ 24fps),
construye los masters Lip-Sync 100% orgánicos (SIN face_mask ni Frame 0 congelado) para v6A y v6B,
y renderiza y verifica las 2 versiones finales editadas + los 2 brutos sincronizados.
"""
import os
import sys
import json
import copy
import shutil
import subprocess
import unicodedata
import cv2
import numpy as np
import soundfile as sf
from scipy.interpolate import PchipInterpolator
from faster_whisper import WhisperModel

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

BASE_DIR = r"c:\IA\Edicion de videos"
WORK_DIR = os.path.join(BASE_DIR, "reels_work")
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
sys.path.insert(0, SCRIPTS_DIR)

from step3_plan_cuts import load_style, build_subtitle_blocks, is_highlighted_word
from step4_render_and_export import render_final_video, FFMPEG_BIN


def get_ffmpeg_exe():
    return FFMPEG_BIN


def norm_word(w: str) -> str:
    s = "".join(
        c for c in unicodedata.normalize("NFD", w.lower().strip())
        if unicodedata.category(c) != "Mn"
    )
    return "".join(c for c in s if c.isalnum())


def load_video_frames_1080p(path: str):
    cap = cv2.VideoCapture(path)
    frames = []
    while True:
        ret, f = cap.read()
        if not ret:
            break
        if f.shape[1] != 1080 or f.shape[0] != 1920:
            f = cv2.resize(f, (1080, 1920), interpolation=cv2.INTER_LANCZOS4)
        frames.append(f)
    cap.release()
    return frames


def extract_16k_audio(video_path: str, ffmpeg_exe: str) -> np.ndarray:
    tmp_wav = video_path + ".16k.wav"
    subprocess.run(
        [ffmpeg_exe, "-y", "-i", video_path, "-vn", "-ac", "1", "-ar", "16000", "-f", "wav", tmp_wav],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    audio_np, _ = sf.read(tmp_wav, dtype="float32")
    if os.path.exists(tmp_wav):
        os.remove(tmp_wav)
    return audio_np


def stitch_multiturn_36s(
    t2_path: str,
    t3_path: str,
    t4_path: str,
    ffmpeg_exe: str,
):
    """
    En gemini-omni-1.1-flash:
    - t2_path (20s, 480 frames @ 24fps) contiene [Turno 1 (0..10s) + Turno 2 (10..20s)] con la transición 1->2 nativa en frame 240.
    - t3_path (20s, 480 frames @ 24fps) contiene [Turno 2 (10..20s) + Turno 3 (20..30s)] con la transición 2->3 nativa en frame 240.
    - t4_path (16s, 384 frames @ 24fps) contiene [Turno 3 (20..30s) + Turno 4 (30..36s)] con la transición 3->4 nativa en frame 240.
    Fundimos en las zonas de solapamiento idéntico (t=15s alrededor de t2[360]/t3[120] y t=25s alrededor de t3[360]/t4[120])
    para obtener los 864 fotogramas (36.00s @ 24fps) 100% continuos sin ningún corte ni salto.
    """
    f2 = load_video_frames_1080p(t2_path)
    f3 = load_video_frames_1080p(t3_path)
    f4 = load_video_frames_1080p(t4_path)

    # Asegurar longitudes esperadas
    assert len(f2) >= 480 and len(f3) >= 480 and len(f4) >= 360, f"Longitudes inesperadas: {len(f2)}, {len(f3)}, {len(f4)}"

    stitched = []
    # 0 .. 348 (0s .. 14.5s) desde t2
    for i in range(348):
        stitched.append(f2[i])
    # 348 .. 372 (14.5s .. 15.5s): cross-blend suave entre f2[348..372] y f3[108..132] (mismo contenido)
    for k in range(24):
        alpha = (k + 1) / 25.0
        blended = cv2.addWeighted(f2[348 + k], 1.0 - alpha, f3[108 + k], alpha, 0.0)
        stitched.append(blended)
    # 372 .. 588 (15.5s .. 24.5s) desde f3[132..348] (incluye transición nativa 2->3 en f3[240])
    for i in range(132, 348):
        stitched.append(f3[i])
    # 588 .. 612 (24.5s .. 25.5s): cross-blend suave entre f3[348..372] y f4[108..132] (mismo contenido)
    for k in range(24):
        alpha = (k + 1) / 25.0
        blended = cv2.addWeighted(f3[348 + k], 1.0 - alpha, f4[108 + k], alpha, 0.0)
        stitched.append(blended)
    # 612 .. fin (25.5s .. 36.0s) desde f4[132:] (incluye transición nativa 3->4 en f4[240])
    for i in range(132, len(f4)):
        stitched.append(f4[i])

    # Audio 16kHz completo (0..20s desde t2 + 20..36s desde t4[10s:])
    a2 = extract_16k_audio(t2_path, ffmpeg_exe)
    a4 = extract_16k_audio(t4_path, ffmpeg_exe)
    sr = 16000
    a2_20s = a2[: 20 * sr]
    a4_after_10s = a4[10 * sr :]
    full_audio_16k = np.concatenate([a2_20s, a4_after_10s], axis=0)

    return stitched, 24.0, full_audio_16k


def transcribe_audio_array(audio_np: np.ndarray, model: WhisperModel):
    segments, _ = model.transcribe(audio_np, language="es", word_timestamps=True, vad_filter=False)
    words = []
    for seg in segments:
        for w in (seg.words or []):
            nw = norm_word(w.word)
            if nw:
                words.append({
                    "word": w.word.strip(),
                    "norm": nw,
                    "start": float(w.start),
                    "end": float(w.end),
                })
    return words


def build_monotonic_pchip_time_map(tts_words, vid_words, target_dur: float, vid_dur: float):
    """
    Empareja palabras ancla entre el TTS maestro (33.60s) y el video continuo (36.00s)
    garantizando una pendiente mínima y máxima estricta en cada tramo (0.55 <= slope <= 1.55)
    para que el cuerpo, el pelo, los hombros y las manos se muevan de forma 100% continua y NUNCA se congelen.
    """
    anchors = [(0.0, 0.0)]
    v_idx = 0
    last_t_tts = 0.0
    last_t_vid = 0.0

    min_slope = 0.55
    max_slope = 1.55

    for tw in tts_words:
        tn = norm_word(tw["word"])
        if len(tn) < 3:
            continue
        t_mid = 0.5 * (float(tw["start"]) + float(tw["end"]))
        if t_mid - last_t_tts < 0.50:
            continue

        best_j = None
        for j in range(v_idx, min(len(vid_words), v_idx + 14)):
            vn = vid_words[j]["norm"]
            if vn == tn or (len(tn) >= 4 and (tn[:4] == vn[:4] or tn in vn or vn in tn)):
                v_mid = 0.5 * (vid_words[j]["start"] + vid_words[j]["end"])
                dt_tts = t_mid - last_t_tts
                dt_vid = v_mid - last_t_vid
                if dt_tts > 0.25 and (min_slope * dt_tts <= dt_vid <= max_slope * dt_tts):
                    best_j = j
                    break

        if best_j is not None:
            v_mid = 0.5 * (vid_words[best_j]["start"] + vid_words[best_j]["end"])
            anchors.append((t_mid, v_mid))
            last_t_tts = t_mid
            last_t_vid = v_mid
            v_idx = best_j + 1

    rem_tts = target_dur - last_t_tts
    if rem_tts > 0.25:
        target_end_vid = min(vid_dur - 0.08, last_t_vid + np.clip(rem_tts * 1.0, rem_tts * min_slope, rem_tts * max_slope))
        if target_end_vid <= last_t_vid + 0.15:
            target_end_vid = min(vid_dur - 0.05, last_t_vid + rem_tts * 0.6)
        anchors.append((target_dur, target_end_vid))
    else:
        anchors[-1] = (target_dur, min(vid_dur - 0.05, max(last_t_vid + 0.1, anchors[-1][1])))

    clean_tts = [anchors[0][0]]
    clean_vid = [anchors[0][1]]
    for t_val, v_val in anchors[1:]:
        dt = t_val - clean_tts[-1]
        if dt <= 0.15:
            continue
        dv = v_val - clean_vid[-1]
        dv_clamped = float(np.clip(dv, dt * min_slope, dt * max_slope))
        next_v = min(vid_dur - 0.04, clean_vid[-1] + dv_clamped)
        if next_v <= clean_vid[-1] + 0.02:
            continue
        clean_tts.append(t_val)
        clean_vid.append(next_v)

    if clean_tts[-1] < target_dur:
        dt = target_dur - clean_tts[-1]
        clean_tts.append(target_dur)
        clean_vid.append(min(vid_dur - 0.04, clean_vid[-1] + dt * 0.80))

    print(f"  -> PCHIP nodos ancla: {len(clean_tts)} | fin video={clean_vid[-1]:.2f}s / {vid_dur:.2f}s")
    return PchipInterpolator(np.array(clean_tts), np.array(clean_vid))


def build_pure_unmasked_master_from_turns(
    tag: str,
    t2_path: str,
    t3_path: str,
    t4_path: str,
    tts_wav_path: str,
    tts_words: list,
    target_dur: float,
    out_master_path: str,
    whisper_model: WhisperModel,
    ffmpeg_exe: str,
):
    print(f"\n[{tag}] Uniendo los 4 turnos Multi-Turn (36.00s continuos @ 24fps) y transcribiendo...")
    frames, src_fps, full_audio_16k = stitch_multiturn_36s(t2_path, t3_path, t4_path, ffmpeg_exe)
    vid_words = transcribe_audio_array(full_audio_16k, whisper_model)
    num_src = len(frames)
    vid_dur = num_src / src_fps
    print(f"  -> Fotogramas continuos: {num_src} ({vid_dur:.2f}s @ {src_fps:.1f}fps) | Palabras detectadas: {len(vid_words)}")

    pchip = build_monotonic_pchip_time_map(tts_words, vid_words, target_dur, vid_dur)

    out_fps = 30.0
    total_out_frames = int(round(target_dur * out_fps))
    tmp_silent_mp4 = out_master_path + ".silent.mp4"

    proc = subprocess.Popen(
        [
            ffmpeg_exe,
            "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", "1080x1920",
            "-pix_fmt", "bgr24",
            "-r", "30",
            "-i", "-",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "16",
            "-pix_fmt", "yuv420p",
            tmp_silent_mp4,
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    for out_idx in range(total_out_frames):
        t_out = out_idx / out_fps
        t_vid = float(np.clip(pchip(t_out), 0.0, vid_dur - 0.001))
        f_pos = t_vid * src_fps
        i0 = int(np.floor(f_pos))
        i1 = min(num_src - 1, i0 + 1)
        i0 = min(num_src - 1, max(0, i0))
        alpha = float(f_pos - i0)

        if alpha <= 0.01 or i0 == i1:
            out_frame = frames[i0]
        else:
            out_frame = cv2.addWeighted(frames[i0], 1.0 - alpha, frames[i1], alpha, 0.0)

        proc.stdin.write(out_frame.tobytes())

    proc.stdin.close()
    proc.wait()

    subprocess.run(
        [
            ffmpeg_exe,
            "-y",
            "-i", tmp_silent_mp4,
            "-i", tts_wav_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            out_master_path,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    if os.path.exists(tmp_silent_mp4):
        os.remove(tmp_silent_mp4)
    print(f"  -> Master 100% continuo listo: {out_master_path}")


def render_reel_version(
    version_tag: str,
    master_mp4_path: str,
    tts_wav_path: str,
    wdata: dict,
    out_edited_mp4: str,
    out_bruto_mp4: str,
    out_grid_jpg: str,
    scene6_full_face: bool = False,
    face_center_y: float = 0.22,
):
    shutil.copy2(master_mp4_path, os.path.join(WORK_DIR, "source_input.mp4"))
    shutil.copy2(tts_wav_path, os.path.join(WORK_DIR, "source_audio.wav"))
    shutil.copy2(master_mp4_path, out_bruto_mp4)

    raw_words = copy.deepcopy(wdata["words"])
    transitions = wdata["transitions"]
    total_dur = float(wdata["duration"])

    legal_tyc = "* Aplican posibles comisiones de Mercado Pago según las condiciones y plazos de acreditación de tu cuenta."
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

    scene_texts = [
        "¿Seguís atado a un sistema viejo o al Excel por miedo a perder los datos de tu veterinaria?",
        "¡Pasate hoy a MascotaMás! Te hacemos toda la migración gratis y en el día, sin frenar tu consultorio.",
        "Pasamos tus clientes, pacientes, historias clínicas y vacunas para que no pierdas ni una sola ficha.",
        "En horas ya tenés recordatorios automáticos por WhatsApp, sala de espera en vivo y todo en la nube.",
        "Además, sumás las 4 agendas inteligentes y el cobro de seña automático con Mercado Pago*.",
        "¡Escribinos hoy en MascotaMás y te migramos gratis en el día!",
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
            "layout_mode": "full_face" if scene6_full_face else "split_graphic",
            "is_hook": False,
            "is_cta": True,
            "top_title": cta_title if scene6_full_face else None,
            "edited_start": transitions[5],
            "edited_end": transitions[6],
            "edited_duration": round(transitions[6] - transitions[5], 4),
            "graphic_config": {
                "template": "none" if scene6_full_face else "chat_input",
                "device_mode": "none",
                "pill": "MASCOTAMAS.COM · MIGRÁ HOY",
                "headline_kicker": "🐾 CAMBIATE HOY SIN FRENAR TU VETERINARIA",
                "headline_main": "💻 ESCRIBINOS HOY EN MASCOTAMAS.COM",
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
    cooldown_min = 4.0
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
            "face_center": [0.5, face_center_y],
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
        "face_center": [0.5, face_center_y],
        "word_ids": [w["word_id"] for w in words_cleaned],
    }]

    sfx_events = []
    for tr_t in transitions[1:-1]:
        sfx_events.append({
            "type": "whoosh",
            "time": round(max(0.0, tr_t - 0.04), 4),
            "reason": f"Beat-synced transition @ {tr_t:.2f}s (125 BPM Lyria 3 House)",
        })
    sfx_events.append({
        "type": "ding",
        "time": round(transitions[5] - 0.02, 4),
        "reason": "CTA final",
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
        "cta_title": cta_title,
        "face_metadata": {
            "default_face_center": [0.5, face_center_y],
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

    print(f"\n[{version_tag} PLAN READY] Dur={total_dur:.2f}s, MG={mg_ratio*100:.1f}%, Blocks={len(subtitle_blocks)}")
    render_final_video(out_edited_mp4)
    subprocess.run([sys.executable, os.path.join(SCRIPTS_DIR, "step5_verify.py"), out_edited_mp4], check=True)
    shutil.copy2(os.path.join(BASE_DIR, "verification_grid.jpg"), out_grid_jpg)
    print(f"  -> [{version_tag} COMPLETADO] {out_edited_mp4}")


def build_v6B_palermo_master(
    t1_camilla_path: str,
    t2_mostrador_20s_path: str,
    tts_wav_path: str,
    tts_words: list,
    transitions: list,
    target_dur: float,
    out_master_path: str,
    whisper_model: WhisperModel,
    ffmpeg_exe: str,
):
    """
    Construye el master 100% orgánico de v6B (Recorrido Veterinaria de Palermo):
    - Parte A (0.00s -> 11.52s, Escenas 1 y 2): v6B_turn1.mp4 (10.00s, 240 fotogramas @ 24fps)
      Atendiendo y acariciando al Golden Retriever sobre la camilla de acero inoxidable del consultorio
      y empezando a caminar por la clínica.
    - Parte B (11.52s -> 33.60s, Escenas 3, 4, 5 y 6): v6B_mostrador_t2.mp4 (20.00s, 480 fotogramas @ 24fps)
      Llegando caminando al mostrador / escritorio de entrada en Palermo junto a su MacBook Pro y hablando
      de forma continua sin cortes.
    """
    print("\n[v6B] Cargando y transcribiendo Parte A (Camilla con perro + caminata) y Parte B (Mostrador de entrada)...")
    f_part_a = load_video_frames_1080p(t1_camilla_path)
    f_part_b = load_video_frames_1080p(t2_mostrador_20s_path)
    src_fps = 24.0
    dur_a = len(f_part_a) / src_fps
    dur_b = len(f_part_b) / src_fps

    aud_a = extract_16k_audio(t1_camilla_path, ffmpeg_exe)
    aud_b = extract_16k_audio(t2_mostrador_20s_path, ffmpeg_exe)
    words_a = transcribe_audio_array(aud_a, whisper_model)
    words_b = transcribe_audio_array(aud_b, whisper_model)
    print(f"  -> Parte A: {len(f_part_a)} frames ({dur_a:.2f}s), {len(words_a)} palabras | Parte B: {len(f_part_b)} frames ({dur_b:.2f}s), {len(words_b)} palabras")

    t_split = float(transitions[2])  # 11.52s (transición exacta Escena 2 -> Escena 3)
    tts_words_a = [w for w in tts_words if float(w["end"]) <= t_split + 0.05]
    tts_words_b = []
    for w in tts_words:
        if float(w["start"]) >= t_split - 0.05:
            wc = dict(w)
            wc["start"] = max(0.0, float(w["start"]) - t_split)
            wc["end"] = max(0.05, float(w["end"]) - t_split)
            tts_words_b.append(wc)

    pchip_a = build_monotonic_pchip_time_map(tts_words_a, words_a, t_split, dur_a)
    pchip_b = build_monotonic_pchip_time_map(tts_words_b, words_b, target_dur - t_split, dur_b)

    out_fps = 30.0
    total_out_frames = int(round(target_dur * out_fps))
    split_frame = int(round(t_split * out_fps))
    tmp_silent_mp4 = out_master_path + ".silent.mp4"

    proc = subprocess.Popen(
        [
            ffmpeg_exe,
            "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", "1080x1920",
            "-pix_fmt", "bgr24",
            "-r", "30",
            "-i", "-",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "16",
            "-pix_fmt", "yuv420p",
            tmp_silent_mp4,
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    def sample_subframe(flist, dur_s, t_val):
        t_c = float(np.clip(t_val, 0.0, dur_s - 0.001))
        f_pos = t_c * src_fps
        i0 = int(np.floor(f_pos))
        i1 = min(len(flist) - 1, i0 + 1)
        i0 = min(len(flist) - 1, max(0, i0))
        alpha = float(f_pos - i0)
        if alpha <= 0.01 or i0 == i1:
            return flist[i0]
        return cv2.addWeighted(flist[i0], 1.0 - alpha, flist[i1], alpha, 0.0)

    for out_idx in range(total_out_frames):
        t_out = out_idx / out_fps
        if out_idx < split_frame - 3:
            out_frame = sample_subframe(f_part_a, dur_a, float(pchip_a(t_out)))
        elif out_idx > split_frame + 3:
            out_frame = sample_subframe(f_part_b, dur_b, float(pchip_b(t_out - t_split)))
        else:
            # Crossfade suave de 6 fotogramas justo en la transición de escena (11.52s)
            blend_w = (out_idx - (split_frame - 3)) / 6.0
            fa = sample_subframe(f_part_a, dur_a, float(pchip_a(min(t_split, t_out))))
            fb = sample_subframe(f_part_b, dur_b, float(pchip_b(max(0.0, t_out - t_split))))
            out_frame = cv2.addWeighted(fa, 1.0 - blend_w, fb, blend_w, 0.0)

        proc.stdin.write(out_frame.tobytes())

    proc.stdin.close()
    proc.wait()

    subprocess.run(
        [
            ffmpeg_exe,
            "-y",
            "-i", tmp_silent_mp4,
            "-i", tts_wav_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            out_master_path,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    if os.path.exists(tmp_silent_mp4):
        os.remove(tmp_silent_mp4)
    print(f"  -> Master v6B 100% continuo listo: {out_master_path}")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    ffmpeg_exe = get_ffmpeg_exe()
    tts_wav_path = os.path.join(WORK_DIR, "v6_tts_synced.wav")
    with open(os.path.join(WORK_DIR, "v6_words_synced.json"), "r", encoding="utf-8") as f:
        wdata = json.load(f)

    tts_words = wdata["words"]
    target_dur = float(wdata["duration"])

    print("Cargando modelo faster-whisper (small)...")
    whisper_model = WhisperModel("small", device="cpu", compute_type="int8")

    if mode in ("all", "v6A"):
        v6a_master = os.path.join(WORK_DIR, "v6A_vet_lipsync_master.mp4")
        build_pure_unmasked_master_from_turns(
            "v6A",
            os.path.join(WORK_DIR, "v6A_turn2.mp4"),
            os.path.join(WORK_DIR, "v6A_turn3.mp4"),
            os.path.join(WORK_DIR, "v6A_continuous_full.mp4"),
            tts_wav_path,
            tts_words,
            target_dur,
            v6a_master,
            whisper_model,
            ffmpeg_exe,
        )
        out_v6a_edit = os.path.join(
            BASE_DIR, "editados",
            "Reel Publicitario - Migracion Gratis en el Dia a MascotaMas (v6A - Avatar 360 Movimiento Continuo Natural + Maquetas Reales MacBook y iPhone + Lyria 3).mp4",
        )
        out_v6a_bruto = os.path.join(
            BASE_DIR, "brutos",
            "Reel Publicitario - Migracion Gratis en el Dia a MascotaMas (v6A - Bruto Avatar 360 Movimiento Continuo Natural LipSync).mp4",
        )
        out_v6a_grid = os.path.join(WORK_DIR, "verification_grid_v6A.jpg")
        render_reel_version(
            "v6A",
            v6a_master,
            tts_wav_path,
            wdata,
            out_v6a_edit,
            out_v6a_bruto,
            out_v6a_grid,
            scene6_full_face=False,
            face_center_y=0.22,
        )

    if mode in ("all", "v6B"):
        v6b_master = os.path.join(WORK_DIR, "v6B_vet_lipsync_master.mp4")
        build_v6B_palermo_master(
            os.path.join(WORK_DIR, "v6B_turn1.mp4"),
            os.path.join(WORK_DIR, "v6B_mostrador_t2.mp4"),
            tts_wav_path,
            tts_words,
            wdata["transitions"],
            target_dur,
            v6b_master,
            whisper_model,
            ffmpeg_exe,
        )
        out_v6b_edit = os.path.join(
            BASE_DIR, "editados",
            "Reel Publicitario - Migracion Gratis en el Dia a MascotaMas (v6B - Recorrido Veterinaria Palermo Camilla con Perro a Mostrador + Maquetas Reales + Lyria 3).mp4",
        )
        out_v6b_bruto = os.path.join(
            BASE_DIR, "brutos",
            "Reel Publicitario - Migracion Gratis en el Dia a MascotaMas (v6B - Bruto Recorrido Veterinaria Palermo Camilla con Perro a Mostrador LipSync).mp4",
        )
        out_v6b_grid = os.path.join(WORK_DIR, "verification_grid_v6B.jpg")
        render_reel_version(
            "v6B",
            v6b_master,
            tts_wav_path,
            wdata,
            out_v6b_edit,
            out_v6b_bruto,
            out_v6b_grid,
            scene6_full_face=True,
            face_center_y=0.25,
        )


if __name__ == "__main__":
    main()
