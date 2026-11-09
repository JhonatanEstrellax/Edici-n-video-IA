# -*- coding: utf-8 -*-
"""
Construye los masters de audio, música House (125 BPM Lyria 3) y video con Lip-Sync
suavizado por spline cúbico PCHIP + filtro Gaussiano de velocidad para AMBAS versiones:
- Versión A (v4A): Guion Directo sin "para paseos" (28.80s = 60 beats @ 125 BPM)
- Versión B (v4B): Guion Storytelling Comercial «Problema -> Solución -> Beneficio» sin "para paseos" (28.80s = 60 beats @ 125 BPM)
"""
import os
import sys
import json
import math
import subprocess
import numpy as np
import soundfile as sf
import cv2
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import gaussian_filter1d

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

BASE_DIR = r"c:\IA\Edicion de videos"
WORK_DIR = os.path.join(BASE_DIR, "reels_work")
FFMPEG_BIN = os.path.join(BASE_DIR, "bin", "ffmpeg", "ffmpeg.exe")
sys.path.insert(0, os.path.join(BASE_DIR, "scripts"))

from step3_plan_cuts import load_style, build_subtitle_blocks, is_highlighted_word

with open(os.path.join(WORK_DIR, "v4_transcriptions.json"), "r", encoding="utf-8") as f:
    trans = json.load(f)

def load_video_frames(path):
    cap = cv2.VideoCapture(path)
    v_fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    frames = []
    while True:
        ret, frm = cap.read()
        if not ret or frm is None:
            break
        if frm.shape[1] != 1080 or frm.shape[0] != 1920:
            frm = cv2.resize(frm, (1080, 1920), interpolation=cv2.INTER_LANCZOS4)
        frames.append(frm)
    cap.release()
    return frames, v_fps

def sample_frame(frames, src_fps, t_sec):
    idx_f = max(0.0, min(float(len(frames) - 1), t_sec * src_fps))
    i0 = int(np.floor(idx_f))
    i1 = min(len(frames) - 1, i0 + 1)
    alpha = idx_f - i0
    if alpha < 1e-3 or i0 == i1:
        return frames[i0]
    return cv2.addWeighted(frames[i0], 1.0 - alpha, frames[i1], alpha, 0.0)

def build_smooth_scene_curve(t_out_arr, anchors, sigma_frames=3.5):
    xs = np.array([a[0] for a in anchors], dtype=np.float64)
    ys = np.array([a[1] for a in anchors], dtype=np.float64)
    clean_x = [xs[0]]
    clean_y = [ys[0]]
    for x, y in zip(xs[1:], ys[1:]):
        if x > clean_x[-1] + 0.01:
            clean_x.append(x)
            clean_y.append(max(clean_y[-1] + 0.002, y))
    pchip = PchipInterpolator(clean_x, clean_y)
    raw_y = pchip(t_out_arr)
    if len(raw_y) > 8 and sigma_frames > 0:
        sm_y = gaussian_filter1d(raw_y, sigma=sigma_frames, mode="nearest")
        sm_y[0] = raw_y[0]
        sm_y[-1] = raw_y[-1]
        return np.maximum.accumulate(sm_y)
    return raw_y

def build_beat_synced_lyria(transitions, total_dur=28.80, out_wav_name="lyria3_house_synced.wav"):
    sr = 44100
    lyria_mp3 = os.path.join(WORK_DIR, "lyria3_house_v2.mp3")
    bgm, bgm_sr = sf.read(lyria_mp3, dtype="float32")
    if bgm.ndim == 1:
        bgm = np.column_stack([bgm, bgm])
    total_samples = int(round(total_dur * sr))
    if len(bgm) < total_samples:
        reps = int(math.ceil(total_samples / float(len(bgm))))
        bgm = np.tile(bgm, (reps, 1))
    bgm = bgm[:total_samples].copy()

    for tr_t in transitions[1:-1]:
        r_len = int(0.32 * sr)
        r_end = int(round(tr_t * sr))
        r_start = max(0, r_end - r_len)
        if r_end > r_start:
            t_r = np.linspace(0.0, 1.0, r_end - r_start, dtype=np.float32)
            freq = 220.0 + 660.0 * (t_r ** 2)
            riser = 0.06 * (t_r ** 2) * np.sin(2.0 * np.pi * np.cumsum(freq) / sr)
            bgm[r_start:r_end, 0] += riser
            bgm[r_start:r_end, 1] += riser
        k_len = int(0.20 * sr)
        k_start = r_end
        k_end = min(total_samples, k_start + k_len)
        if k_end > k_start:
            t_k = np.linspace(0.0, 1.0, k_end - k_start, dtype=np.float32)
            f_k = 115.0 * np.exp(-9.0 * t_k) + 42.0
            kick = 0.16 * np.exp(-6.5 * t_k) * np.sin(2.0 * np.pi * np.cumsum(f_k) / sr)
            bgm[k_start:k_end, 0] += kick
            bgm[k_start:k_end, 1] += kick

    fi = int(0.25 * sr)
    fo = int(0.85 * sr)
    bgm[:fi] *= np.linspace(0.0, 1.0, fi, dtype=np.float32)[:, None]
    bgm[-fo:] *= np.linspace(1.0, 0.0, fo, dtype=np.float32)[:, None]
    bgm = np.clip(bgm, -0.98, 0.98)
    out_p = os.path.join(WORK_DIR, out_wav_name)
    sf.write(out_p, bgm, sr)
    return out_p

print("Cargando fotogramas 1080p de v4A_part1, v4A_part2, v4B_part1, v4B_part2...")
frames_A1, fps_A1 = load_video_frames(os.path.join(WORK_DIR, "v4A_part1.mp4"))
frames_A2, fps_A2 = load_video_frames(os.path.join(WORK_DIR, "v4A_part2.mp4"))
frames_B1, fps_B1 = load_video_frames(os.path.join(WORK_DIR, "v4B_part1.mp4"))
frames_B2, fps_B2 = load_video_frames(os.path.join(WORK_DIR, "v4B_part2.mp4"))

total_dur = 28.80
fps_out = 30
total_frames = int(round(total_dur * fps_out))
legal_tyc = "* Aplican posibles comisiones de Mercado Pago según las condiciones y plazos de acreditación de tu cuenta."
hook_title = {
    "line1": "LO NUEVO DE",
    "line2": "MASCOTAMÁS 🚀",
    "keyword": "MASCOTAMÁS",
    "emoji": "🚀"
}

# ==============================================================================
# 1. VERSIÓN A (v4A): Guion Directo sin "para paseos"
# ==============================================================================
print("\n[VERSIÓN A - v4A] Armando audio sincronizado al beat y video con lip-sync...")
transitions_A = [0.00, 4.32, 10.08, 14.88, 19.68, 24.96, 28.80]

tts_A_wav, sr_tts_A = sf.read(os.path.join(WORK_DIR, "tts_v4A_raw.wav"), dtype="float32")
if tts_A_wav.ndim > 1:
    tts_A_wav = np.mean(tts_A_wav, axis=1)

# S5 starts on word 53 ("activás") at 19.64s so it matches v4A_part2 (4.04s -> 7.80s) 100% word-for-word!
slices_A = [
    (0.00, 4.16, 0.08, list(range(1, 12)), 1),
    (4.22, 9.52, 4.44, list(range(12, 27)), 2),
    (9.70, 14.20, 10.20, list(range(27, 38)), 3),
    (14.26, 18.52, 15.04, list(range(38, 52)), 4),
    (19.64, 23.74, 20.10, list(range(53, 66)), 5),
    (23.84, 26.30, 25.16, list(range(66, 72)), 6),
]

synced_tts_A = np.zeros(int(round(total_dur * sr_tts_A)), dtype=np.float32)
words_A_raw = trans["tts_v4A_raw.wav"]["words"]
words_A_synced = []

sub_overrides_A = {
    1: "¡Mirá", 5: "MascotaMás", 8: "veterinaria,", 9: "peluquería", 11: "guardería!",
    12: "Ahora", 13: "tenés", 14: "4", 17: "calendario:", 18: "Turnos", 19: "Simples", 20: "1", 22: "1,", 24: "Cupos", 26: "Horario.",
    27: "También", 30: "Servicios", 32: "Profesionales,", 34: "grilla", 35: "automática", 37: "huecos,",
    38: "y", 39: "Calendario", 41: "Guardería", 45: "fechas,", 47: "sectores", 49: "ingreso", 51: "egreso.",
    53: "Activás", 57: "seña", 58: "automático", 60: "Mercado", 61: "Pago*", 65: "turno.",
    66: "¡Entrá", 69: "MascotaMás", 71: "probalo!"
}

for src_s, src_e, dst_s, wids, sc_id in slices_A:
    s_i = max(0, int(round(src_s * sr_tts_A)))
    e_i = min(len(tts_A_wav), int(round(src_e * sr_tts_A)))
    chunk = tts_A_wav[s_i:e_i].copy()
    f_len = min(len(chunk) // 4, int(0.015 * sr_tts_A))
    if f_len > 1:
        chunk[:f_len] *= np.linspace(0.0, 1.0, f_len, dtype=np.float32)
        chunk[-f_len:] *= np.linspace(1.0, 0.0, f_len, dtype=np.float32)
    d_i = int(round(dst_s * sr_tts_A))
    d_e = min(len(synced_tts_A), d_i + len(chunk))
    synced_tts_A[d_i:d_e] = chunk[:d_e - d_i]
    shift = dst_s - src_s
    for wid in wids:
        w = dict(words_A_raw[wid - 1])
        ns = round(float(w["start"]) + shift, 4)
        ne = round(float(w["end"]) + shift, 4)
        new_id = len(words_A_synced) + 1
        words_A_synced.append({
            "word_id": new_id,
            "orig_id": wid,
            "word": w["word"],
            "subtitle_text": sub_overrides_A.get(wid, w["word"]),
            "start": ns,
            "end": ne,
            "scene_id": sc_id
        })

tts_v4A_synced_path = os.path.join(WORK_DIR, "v4A_tts_synced.wav")
sf.write(tts_v4A_synced_path, synced_tts_A, sr_tts_A)
lyria_v4A_path = build_beat_synced_lyria(transitions_A, total_dur, "v4A_lyria_synced.wav")

anchors_A_part1 = [
    (0.00, 0.35),
    (0.08, 0.50),   # "¡Mirá"
    (1.24, 1.46),   # "MascotaMás" (M closure)
    (1.80, 1.90),   # "para" (P closure)
    (2.18, 2.20),   # "veterinaria"
    (2.90, 2.82),   # "peluquería" (P closure)
    (4.20, 3.84),   # "guardería!" end
    (4.32, 3.86),   # Beat 9 cut (mouth closed)
    (4.44, 3.88),   # "Ahora"
    (5.50, 4.42),   # "cuatro"
    (6.80, 5.60),   # "calendario." end
    (6.86, 5.66),   # "Turnos"
    (7.46, 6.12),   # "Simples" (P closure)
    (8.46, 6.96),   # "uno," end
    (8.82, 7.12),   # "Cupos" (P closure)
    (9.68, 7.90),   # "Horario." end
    (10.08, 8.02),  # Beat 21 cut (mouth closed)
    (10.20, 8.08),  # "También" (M/B closure)
    (11.40, 9.26),  # "Servicios"
    (11.96, 9.90),  # "Profesionales," (P closure)
    (12.90, 10.82), # "grilla"
    (13.24, 11.16), # "automática" (M closure)
    (14.66, 12.38), # "huecos." end
    (14.88, 12.85), # Beat 31 cut (closed-lip smile)
]

anchors_A_part2 = [
    (14.88, 0.00),
    (15.04, 0.05),  # "y"
    (15.56, 0.78),  # "Calendario"
    (16.10, 1.40),  # "Guardería"
    (17.10, 2.36),  # "fechas,"
    (17.58, 2.80),  # "con"
    (17.82, 3.00),  # "sectores"
    (18.36, 3.54),  # "ingreso"
    (19.24, 3.92),  # "egreso." end
    (19.68, 3.98),  # Beat 41 cut (mouth closed)
    (20.10, 4.04),  # "Activás" start
    (20.68, 4.74),  # "cobro" (B closure)
    (21.06, 5.08),  # "seña"
    (21.34, 5.34),  # "automático" (M closure)
    (22.02, 5.96),  # "Mercado" (M closure)
    (22.36, 6.32),  # "Pago" (P closure)
    (22.72, 6.58),  # "para" (P closure)
    (22.88, 6.72),  # "asegurar"
    (23.60, 7.32),  # "turno."
    (24.14, 7.80),  # "turno." end
    (24.96, 8.05),  # Beat 52 cut (mouth closed)
    (25.16, 8.16),  # "¡Entrá" start
    (25.78, 8.66),  # "hoy"
    (26.32, 9.02),  # "Mascota" (M closure)
    (26.70, 9.38),  # "Más" (M closure)
    (27.10, 9.76),  # "probalo!" (P/B closure)
    (27.56, 10.12), # "probalo!" end
    (27.65, 13.10), # Transition to clean radiant closed-lip smile (13.10..14.50s)
    (28.80, 14.45),
]

t_all = np.arange(total_frames, dtype=np.float64) / float(fps_out)
cut_f_A = int(round(14.88 * fps_out))
curve_A1 = build_smooth_scene_curve(t_all[:cut_f_A], anchors_A_part1, sigma_frames=3.0)
curve_A2 = build_smooth_scene_curve(t_all[cut_f_A:], anchors_A_part2, sigma_frames=3.0)

out_mp4_A = os.path.join(WORK_DIR, "v4A_vet_lipsync_master.mp4")
cmd_A = [
    FFMPEG_BIN, "-y", "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "bgr24",
    "-s", "1080x1920", "-r", str(fps_out), "-i", "-", "-i", tts_v4A_synced_path,
    "-c:v", "libx264", "-crf", "16", "-preset", "fast", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "192k", "-shortest", out_mp4_A
]
proc_A = subprocess.Popen(cmd_A, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
for f_idx in range(total_frames):
    if f_idx < cut_f_A:
        frm = sample_frame(frames_A1, fps_A1, float(curve_A1[f_idx]))
    else:
        frm = sample_frame(frames_A2, fps_A2, float(curve_A2[f_idx - cut_f_A]))
    proc_A.stdin.write(frm.tobytes())
proc_A.stdin.close()
proc_A.wait()
print(f"  -> [v4A MASTER VIDEO] {out_mp4_A} ({os.path.getsize(out_mp4_A)} bytes)")

# ==============================================================================
# 2. VERSIÓN B (v4B): Guion Storytelling Comercial sin "para paseos"
# ==============================================================================
print("\n[VERSIÓN B - v4B] Armando audio sincronizado al beat y video con lip-sync...")
transitions_B = [0.00, 5.76, 11.52, 16.32, 20.64, 25.44, 28.80]

tts_B_wav, sr_tts_B = sf.read(os.path.join(WORK_DIR, "tts_v4B_raw.wav"), dtype="float32")
if tts_B_wav.ndim > 1:
    tts_B_wav = np.mean(tts_B_wav, axis=1)

# 6 intact sentence slices in tts_v4B_raw.wav:
# S1: 0.00 -> 5.74s  (placed at 0.00s -> 5.74s)
# S2: 6.06 -> 11.30s (placed at 5.92s -> 11.16s)
# S3: 11.54 -> 15.78s (placed at 11.72s -> 15.96s)
# S4: 15.84 -> 20.36s (placed at 16.36s -> 20.56s, trimming 0.3s pre-Y silence: 16.16..20.36 -> 16.36..20.56)
# S5: 20.80 -> 25.14s (placed at 20.82s -> 25.16s)
# S6: 25.24 -> 27.36s (placed at 25.60s -> 27.72s)
slices_B = [
    (0.00, 5.74, 0.00, list(range(1, 17)), 1),
    (6.06, 11.30, 5.92, list(range(17, 31)), 2),
    (11.54, 15.78, 11.72, list(range(31, 42)), 3),
    (16.10, 20.36, 16.34, list(range(42, 56)), 4),
    (20.80, 25.14, 20.82, list(range(56, 70)), 5),
    (25.24, 27.36, 25.60, list(range(70, 77)), 6),
]

synced_tts_B = np.zeros(int(round(total_dur * sr_tts_B)), dtype=np.float32)
words_B_raw = trans["tts_v4B_raw.wav"]["words"]
words_B_synced = []

sub_overrides_B = {
    1: "¿Perdés", 4: "WhatsApp", 7: "veterinaria,", 8: "peluquería", 10: "guardería?", 11: "¡Mirá", 15: "Mascota", 16: "Más!",
    17: "Elegí", 19: "4", 20: "agendas", 21: "inteligentes:", 22: "Turnos", 23: "Simples", 24: "1", 26: "1,", 28: "Cupos", 30: "Horario.",
    31: "También", 34: "Servicios", 36: "Profesionales,", 38: "grilla", 39: "automática", 41: "huecos,",
    42: "y", 43: "Calendario", 45: "Guardería", 49: "fechas,", 51: "sectores", 53: "ingreso", 55: "egreso.",
    56: "¿Lo", 57: "mejor?", 58: "Cobrás", 59: "seña", 60: "automática", 62: "Mercado", 63: "Pago*", 66: "olvidás", 69: "faltazos.",
    70: "¡Entrá", 73: "Mascota", 74: "Más", 76: "probalo!"
}

for src_s, src_e, dst_s, wids, sc_id in slices_B:
    s_i = max(0, int(round(src_s * sr_tts_B)))
    e_i = min(len(tts_B_wav), int(round(src_e * sr_tts_B)))
    chunk = tts_B_wav[s_i:e_i].copy()
    f_len = min(len(chunk) // 4, int(0.015 * sr_tts_B))
    if f_len > 1:
        chunk[:f_len] *= np.linspace(0.0, 1.0, f_len, dtype=np.float32)
        chunk[-f_len:] *= np.linspace(1.0, 0.0, f_len, dtype=np.float32)
    d_i = int(round(dst_s * sr_tts_B))
    d_e = min(len(synced_tts_B), d_i + len(chunk))
    synced_tts_B[d_i:d_e] = chunk[:d_e - d_i]
    shift = dst_s - src_s
    for wid in wids:
        w = dict(words_B_raw[wid - 1])
        ns = max(dst_s, round(float(w["start"]) + shift, 4))
        ne = max(ns + 0.04, round(float(w["end"]) + shift, 4))
        new_id = len(words_B_synced) + 1
        words_B_synced.append({
            "word_id": new_id,
            "orig_id": wid,
            "word": w["word"],
            "subtitle_text": sub_overrides_B.get(wid, w["word"]),
            "start": ns,
            "end": ne,
            "scene_id": sc_id
        })

tts_v4B_synced_path = os.path.join(WORK_DIR, "v4B_tts_synced.wav")
sf.write(tts_v4B_synced_path, synced_tts_B, sr_tts_B)
lyria_v4B_path = build_beat_synced_lyria(transitions_B, total_dur, "v4B_lyria_synced.wav")

# Video curves for v4B:
# Scenes 1..2 (0.00 -> 11.52s) from frames_B1
# Scene 3 (11.52 -> 16.32s) from frames_A1 (8.05 -> 12.85s)
# Scene 4 (16.32 -> 20.64s) from frames_A2 (0.00 -> 3.98s)
# Scenes 5..6 (20.64 -> 28.80s) from frames_B2 (2.55 -> 12.50s)
anchors_B_s12 = [
    (0.00, 0.00),
    (0.50, 0.96),   # "¿Perdés"
    (0.94, 1.40),   # "WhatsApp"
    (1.54, 1.98),   # "veterinaria,"
    (2.36, 2.66),   # "peluquería" (P closure)
    (3.58, 3.86),   # "guardería?" end
    (3.80, 4.04),   # "¡Mirá" (M closure)
    (5.10, 5.04),   # "MascotaMás" (M closure)
    (5.74, 5.64),   # "MascotaMás!" end
    (5.76, 5.68),   # Beat 12 cut (mouth closed)
    (5.92, 5.72),   # "Elegí" start
    (6.68, 6.40),   # "cuatro"
    (7.02, 6.66),   # "agendas"
    (8.08, 7.80),   # "inteligentes." end
    (8.26, 8.22),   # "Turnos" start
    (8.82, 8.78),   # "Simples" (P closure)
    (9.86, 9.80),   # "uno," end
    (10.26, 10.24), # "Cupos" (P closure)
    (11.12, 11.18), # "Horario." end
    (11.52, 11.35), # Beat 24 cut (mouth closed)
]

anchors_B_s3 = [
    (11.52, 8.04),
    (11.72, 8.08),  # "También" (M/B closure)
    (12.88, 9.26),  # "Servicios"
    (13.50, 9.90),  # "Profesionales," (P closure)
    (14.44, 10.82), # "grilla"
    (14.74, 11.16), # "automática" (M closure)
    (15.94, 12.38), # "huecos." end
    (16.32, 12.85), # Beat 34 cut (closed-lip smile)
]

anchors_B_s4 = [
    (16.32, 0.00),
    (16.36, 0.05),  # "y"
    (16.64, 0.78),  # "Calendario"
    (17.32, 1.40),  # "Guardería"
    (18.46, 2.36),  # "fechas,"
    (18.94, 2.80),  # "con"
    (19.18, 3.00),  # "sectores"
    (19.74, 3.54),  # "ingreso"
    (20.54, 3.92),  # "egreso." end
    (20.64, 3.98),  # Beat 43 cut (mouth closed)
]

anchors_B_s56 = [
    (20.64, 2.55),
    (20.84, 2.62),  # "¿Lo"
    (21.14, 3.02),  # "mejor?" (M closure)
    (21.46, 3.40),  # "mejor?" end
    (21.58, 3.52),  # "Cobrás" (B closure)
    (22.02, 4.30),  # "seña"
    (22.30, 4.64),  # "automática" (M closure)
    (22.90, 5.38),  # "Mercado" (M closure)
    (23.26, 5.80),  # "Pago" (P closure)
    (23.90, 6.46),  # "olvidás"
    (24.60, 7.10),  # "faltazos."
    (25.12, 7.70),  # "faltazos." end
    (25.44, 7.85),  # Beat 53 cut (mouth closed)
    (25.60, 7.94),  # "¡Entrá" start
    (26.16, 8.62),  # "hoy"
    (26.52, 9.10),  # "Mascota" (M closure)
    (27.14, 9.74),  # "y"
    (27.26, 10.08), # "probalo!" (P/B closure)
    (27.68, 10.74), # "probalo!" end
    (28.80, 12.10), # Radiant closed-lip smile (10.74..12.10s)
]

f_b1 = int(round(11.52 * fps_out))
f_b2 = int(round(16.32 * fps_out))
f_b3 = int(round(20.64 * fps_out))

c_B_s12 = build_smooth_scene_curve(t_all[:f_b1], anchors_B_s12, sigma_frames=3.0)
c_B_s3 = build_smooth_scene_curve(t_all[f_b1:f_b2], anchors_B_s3, sigma_frames=3.0)
c_B_s4 = build_smooth_scene_curve(t_all[f_b2:f_b3], anchors_B_s4, sigma_frames=3.0)
c_B_s56 = build_smooth_scene_curve(t_all[f_b3:], anchors_B_s56, sigma_frames=3.0)

out_mp4_B = os.path.join(WORK_DIR, "v4B_vet_lipsync_master.mp4")
cmd_B = [
    FFMPEG_BIN, "-y", "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "bgr24",
    "-s", "1080x1920", "-r", str(fps_out), "-i", "-", "-i", tts_v4B_synced_path,
    "-c:v", "libx264", "-crf", "16", "-preset", "fast", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "192k", "-shortest", out_mp4_B
]
proc_B = subprocess.Popen(cmd_B, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
for f_idx in range(total_frames):
    if f_idx < f_b1:
        frm = sample_frame(frames_B1, fps_B1, float(c_B_s12[f_idx]))
    elif f_idx < f_b2:
        frm = sample_frame(frames_A1, fps_A1, float(c_B_s3[f_idx - f_b1]))
    elif f_idx < f_b3:
        frm = sample_frame(frames_A2, fps_A2, float(c_B_s4[f_idx - f_b2]))
    else:
        frm = sample_frame(frames_B2, fps_B2, float(c_B_s56[f_idx - f_b3]))
    proc_B.stdin.write(frm.tobytes())
proc_B.stdin.close()
proc_B.wait()
print(f"  -> [v4B MASTER VIDEO] {out_mp4_B} ({os.path.getsize(out_mp4_B)} bytes)")

# Save word tables + transitions for both versions so we can render them cleanly
with open(os.path.join(WORK_DIR, "v4A_words_synced.json"), "w", encoding="utf-8") as f:
    json.dump({"duration": total_dur, "transitions": transitions_A, "words": words_A_synced}, f, ensure_ascii=False, indent=2)
with open(os.path.join(WORK_DIR, "v4B_words_synced.json"), "w", encoding="utf-8") as f:
    json.dump({"duration": total_dur, "transitions": transitions_B, "words": words_B_synced}, f, ensure_ascii=False, indent=2)

print("\n¡Ambos masters (v4A y v4B) generados con éxito!")
