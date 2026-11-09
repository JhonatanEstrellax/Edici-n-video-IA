# -*- coding: utf-8 -*-
"""
Construye el Master Audio (Gemini 3.8 Flash TTS es-AR), Música House (125 BPM Lyria 3)
y Master Video 1080x1920 @ 30fps con Lip-Sync PCHIP palabra por palabra y estabilización
de encuadre sobre el nuevo Avatar 360° (Gemini 3 Pro: Frente 0° + 3/4 Izquierda -45°).
Duración total: 33.60s (70 beats exactos @ 125 BPM = 0.48s/beat), con pausas naturales
de 0.45s..0.74s al final de cada oración para que JAMÁS se corte una frase.
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

with open(os.path.join(WORK_DIR, "v6_all_transcriptions.json"), "r", encoding="utf-8") as f:
    trans = json.load(f)

total_dur = 33.60  # 70 beats @ 125 BPM (0.48s per beat)
fps_out = 30
total_frames = int(round(total_dur * fps_out))  # 1008 frames
transitions = [0.00, 5.28, 11.52, 17.76, 24.00, 29.28, 33.60]

# ---------------------------------------------------------------------------
# 1. Construir v6_tts_synced.wav sin cortar ni un solo fonema, con pausas naturales
# ---------------------------------------------------------------------------
tts_full, sr_tts = sf.read(os.path.join(WORK_DIR, "tts_v6_full_raw.wav"), dtype="float32")
if tts_full.ndim > 1:
    tts_full = np.mean(tts_full, axis=1)

tts_s6, sr_s6 = sf.read(os.path.join(WORK_DIR, "tts_v6_s6.wav"), dtype="float32")
if tts_s6.ndim > 1:
    tts_s6 = np.mean(tts_s6, axis=1)

# S1..S5 from tts_v6_full_raw.wav (with generous tail after each sentence's last word)
# S6 from tts_v6_s6.wav (crisp, natural standalone CTA sentence)
full_words = trans["tts_v6_full_raw.wav"]["words"]
s6_words = trans["tts_v6_s6.wav"]["words"]

# Sentence slices: (wav_arr, src_start, src_end, dst_start, word_list_slice, scene_id)
sentence_slices = [
    (tts_full, 0.00, 5.02, 0.08, full_words[0:18], 1),     # S1: words 1..18 -> ends at 4.86s (pause until 5.28s)
    (tts_full, 5.18, 10.76, 5.42, full_words[18:36], 2),   # S2: words 19..36 -> ends at 10.72s (pause until 11.52s)
    (tts_full, 11.02, 17.02, 11.68, full_words[36:52], 3), # S3: words 37..52 -> ends at 17.36s (pause until 17.76s)
    (tts_full, 17.38, 23.16, 17.92, full_words[52:70], 4), # S4: words 53..70 -> ends at 23.40s (pause until 24.00s)
    (tts_full, 23.46, 27.75, 24.16, full_words[70:85], 5), # S5: words 71..85 -> ends at 28.46s (pause until 29.28s)
    (tts_s6,   0.00, 3.68, 29.44, s6_words[0:11], 6),      # S6: words 1..11 -> ends at 32.86s (smile until 33.60s)
]

synced_tts = np.zeros(int(round(total_dur * sr_tts)), dtype=np.float32)
words_v6_synced = []

# Clean display overrides for subtitle words (100% Argentine spelling & punctuation)
exact_sub_words = [
    # Escena 1 (18 words)
    "¿Seguís", "atado", "a", "un", "sistema", "viejo", "o", "al", "Excel", "por", "miedo", "a", "perder", "los", "datos", "de", "tu", "veterinaria?",
    # Escena 2 (18 words)
    "¡Pasate", "hoy", "a", "MascotaMás!", "Te", "hacemos", "toda", "la", "migración", "gratis", "y", "en", "el", "día,", "sin", "frenar", "tu", "consultorio.",
    # Escena 3 (16 words)
    "Pasamos", "tus", "clientes,", "pacientes,", "historias", "clínicas", "y", "vacunas", "para", "que", "no", "pierdas", "ni", "una", "sola", "ficha.",
    # Escena 4 (18 words)
    "En", "horas", "ya", "tenés", "recordatorios", "automáticos", "por", "WhatsApp,", "sala", "de", "espera", "en", "vivo", "y", "todo", "en", "la", "nube.",
    # Escena 5 (15 words)
    "Además,", "sumás", "las", "4", "agendas", "inteligentes", "y", "el", "cobro", "de", "seña", "automático", "con", "Mercado", "Pago*.",
    # Escena 6 (11 words)
    "¡Escribinos", "hoy", "en", "MascotaMás", "y", "te", "migramos", "gratis", "en", "el", "día!"
]

for wav_arr, src_s, src_e, dst_s, w_slice, sc_id in sentence_slices:
    s_i = max(0, int(round(src_s * sr_tts)))
    e_i = min(len(wav_arr), int(round(src_e * sr_tts)))
    chunk = wav_arr[s_i:e_i].copy()
    f_len = min(len(chunk) // 6, int(0.015 * sr_tts))
    if f_len > 1:
        chunk[:f_len] *= np.linspace(0.0, 1.0, f_len, dtype=np.float32)
        chunk[-f_len:] *= np.linspace(1.0, 0.0, f_len, dtype=np.float32)
    d_i = int(round(dst_s * sr_tts))
    d_e = min(len(synced_tts), d_i + len(chunk))
    synced_tts[d_i:d_e] = chunk[:d_e - d_i]
    shift = dst_s - src_s
    for w in w_slice:
        new_id = len(words_v6_synced) + 1
        ns = max(dst_s, round(float(w["start"]) + shift, 4))
        ne = max(ns + 0.05, round(float(w["end"]) + shift, 4))
        sub_txt = exact_sub_words[new_id - 1]
        clean_w = sub_txt.strip("¿?¡!.,*:")
        words_v6_synced.append({
            "word_id": new_id,
            "word": clean_w,
            "subtitle_text": sub_txt,
            "start": ns,
            "end": ne,
            "scene_id": sc_id
        })

tts_v6_synced_path = os.path.join(WORK_DIR, "v6_tts_synced.wav")
sf.write(tts_v6_synced_path, synced_tts, sr_tts)
print(f"[TTS SYNCED] Guardado {tts_v6_synced_path} ({total_dur:.2f}s, {len(words_v6_synced)} palabras)")

# ---------------------------------------------------------------------------
# 2. Construir v6_lyria_synced.wav (125 BPM Lyria 3 House sincronizada a cada transición)
# ---------------------------------------------------------------------------
def build_beat_synced_lyria(transitions_list, dur_sec, out_wav_name):
    sr = 44100
    lyria_mp3 = os.path.join(WORK_DIR, "lyria3_house_v2.mp3")
    bgm, _ = sf.read(lyria_mp3, dtype="float32")
    if bgm.ndim == 1:
        bgm = np.column_stack([bgm, bgm])
    total_samples = int(round(dur_sec * sr))
    if len(bgm) < total_samples:
        reps = int(math.ceil(total_samples / float(len(bgm))))
        bgm = np.tile(bgm, (reps, 1))
    bgm = bgm[:total_samples].copy()

    for tr_t in transitions_list[1:-1]:
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
    fo = int(0.90 * sr)
    bgm[:fi] *= np.linspace(0.0, 1.0, fi, dtype=np.float32)[:, None]
    bgm[-fo:] *= np.linspace(1.0, 0.0, fo, dtype=np.float32)[:, None]
    bgm = np.clip(bgm, -0.98, 0.98)
    out_p = os.path.join(WORK_DIR, out_wav_name)
    sf.write(out_p, bgm, sr)
    return out_p

lyria_v6_path = build_beat_synced_lyria(transitions, total_dur, "v6_lyria_synced.wav")
print(f"[LYRIA 3 SYNCED] Guardado {lyria_v6_path}")

# ---------------------------------------------------------------------------
# 3. Cargar y estabilizar los 3 clips de video 1080p del nuevo Avatar
#    - Clip 2 (3/4 Izquierda) ya mantiene escala 1.00x nativa todo el clip (se usa puro 100%).
#    - Clips 1 y 3 (Frente 0°) usan detección facial YuNet + máscara elíptica 2D suave
#      exclusivamente en el rostro (v < 0.34, arriba del cuello/escote) para mantener
#      el plano medio-completo 360° de Frame 0 sin zoom ni costuras en hombros.
# ---------------------------------------------------------------------------
MODEL_PATH = os.path.join(BASE_DIR, "models", "face_detection_yunet_2023mar.onnx")

def load_and_stabilize_clip(path, lock_to_frame0_body=True):
    cap = cv2.VideoCapture(path)
    v_fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    raw_frames = []
    while True:
        ret, frm = cap.read()
        if not ret or frm is None:
            break
        if frm.shape[1] != 1080 or frm.shape[0] != 1920:
            frm = cv2.resize(frm, (1080, 1920), interpolation=cv2.INTER_LANCZOS4)
        raw_frames.append(frm)
    cap.release()

    if not lock_to_frame0_body:
        return raw_frames, v_fps

    w, h = 1080, 1920
    n_f = len(raw_frames)
    detector = cv2.FaceDetectorYN.create(MODEL_PATH, "", (540, 960), 0.45, 0.3, 5000)

    cxs = np.zeros(n_f, dtype=np.float32)
    cys = np.zeros(n_f, dtype=np.float32)
    fws = np.zeros(n_f, dtype=np.float32)
    fhs = np.zeros(n_f, dtype=np.float32)

    for idx, frm in enumerate(raw_frames):
        sm = cv2.resize(frm, (540, 960), interpolation=cv2.INTER_AREA)
        _, faces = detector.detect(sm)
        if faces is not None and len(faces) > 0:
            fx, fy, fw, fh = faces[0][:4]
            cxs[idx] = (fx + fw * 0.5) * 2.0
            cys[idx] = (fy + fh * 0.5) * 2.0
            fws[idx] = fw * 2.0
            fhs[idx] = fh * 2.0
        elif idx > 0:
            cxs[idx] = cxs[idx - 1]
            cys[idx] = cys[idx - 1]
            fws[idx] = fws[idx - 1]
            fhs[idx] = fhs[idx - 1]
        else:
            cxs[idx], cys[idx], fws[idx], fhs[idx] = 540.0, 497.0, 202.0, 270.0

    cxs_sm = gaussian_filter1d(cxs, sigma=3.5)
    cys_sm = gaussian_filter1d(cys, sigma=3.5)
    fws_sm = gaussian_filter1d(fws, sigma=3.5)
    fhs_sm = gaussian_filter1d(fhs, sigma=3.5)

    cx0, cy0 = float(cxs_sm[0]), float(cys_sm[0])
    sz0 = math.sqrt(float(fws_sm[0]) * float(fhs_sm[0]))

    # Soft 2D elliptical mask strictly inside the inner face/mouth/eyes (never touches hair edges or shoulders)
    u, v = np.meshgrid(
        np.linspace(0.0, 1.0, w, dtype=np.float32),
        np.linspace(0.0, 1.0, h, dtype=np.float32)
    )
    u0 = cx0 / float(w)
    v0 = (cy0 + 8.0) / float(h)
    r_ell = np.sqrt(((u - u0) / 0.088)**2 + ((v - v0) / 0.068)**2)
    face_mask = np.clip((1.22 - r_ell) / (1.22 - 0.62), 0.0, 1.0)
    face_mask = (face_mask * face_mask * (3.0 - 2.0 * face_mask))[:, :, None].astype(np.float32)

    f0_f = raw_frames[0].astype(np.float32)
    stab_frames = []
    for idx in range(n_f):
        sz_i = math.sqrt(float(fws_sm[idx]) * float(fhs_sm[idx]))
        inv_s = sz0 / max(1.0, sz_i)
        tx = cx0 - float(cxs_sm[idx]) * inv_s
        ty = cy0 - float(cys_sm[idx]) * inv_s
        M = np.float32([[inv_s, 0.0, tx], [0.0, inv_s, ty]])
        aligned_face = cv2.warpAffine(raw_frames[idx], M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)

        # Match luminance/color of inner face to Frame 0 smoothly
        t_s = idx / float(v_fps)
        b_dy = 1.6 * np.sin(2.0 * np.pi * 0.30 * t_s)
        M_b = np.float32([[1.0, 0.0, 0.0], [0.0, 1.0, b_dy]])
        body_b = cv2.warpAffine(f0_f, M_b, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

        comp = (aligned_face * face_mask + body_b * (1.0 - face_mask)).astype(np.uint8)
        stab_frames.append(comp)
    return stab_frames, v_fps

print("Cargando y estabilizando los 3 clips 1080p del nuevo Avatar (Frente 0° y 3/4 Izquierda)...")
frames_c1, fps_c1 = load_and_stabilize_clip(os.path.join(WORK_DIR, "v6_clip1_frente.mp4"), lock_to_frame0_body=True)
frames_c2, fps_c2 = load_and_stabilize_clip(os.path.join(WORK_DIR, "v6_clip2_tres_cuartos.mp4"), lock_to_frame0_body=False)
frames_c3, fps_c3 = load_and_stabilize_clip(os.path.join(WORK_DIR, "v6_clip3_frente_cta.mp4"), lock_to_frame0_body=True)

def sample_frame(frames, src_fps, t_sec):
    idx_f = max(0.0, min(float(len(frames) - 1), t_sec * src_fps))
    i0 = int(np.floor(idx_f))
    i1 = min(len(frames) - 1, i0 + 1)
    alpha = idx_f - i0
    if alpha < 1e-3 or i0 == i1:
        return frames[i0]
    return cv2.addWeighted(frames[i0], 1.0 - alpha, frames[i1], alpha, 0.0)

def build_smooth_scene_curve(t_out_arr, anchors, sigma_frames=3.0):
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

# ---------------------------------------------------------------------------
# 4. Curvas PCHIP de Sincronización Labial Palabra por Palabra (0.00s -> 33.60s)
# ---------------------------------------------------------------------------
# Clip 1 (Escenas 1 y 2: 0.00s -> 11.52s)
c1_words = trans["v6_clip1_frente.mp4"]["words"]  # 37 words (Mascota + Más = 2 tokens in clip1 vs 1 token in TTS)
anchors_c1 = [(0.00, 0.00), (0.08, 0.02)]
# Words 1..18 in TTS match words 1..18 in c1_words
for i in range(18):
    w_tts = words_v6_synced[i]
    w_vid = c1_words[i]
    anchors_c1.append((w_tts["start"], w_vid["start"]))
    anchors_c1.append((w_tts["end"], w_vid["end"]))
anchors_c1.append((5.28, 5.76))  # Beat 11 transition (natural pause with closed lips)
# Words 19..21 ("¡Pasate hoy a") -> c1_words[18..20]
for i, vid_i in [(18, 18), (19, 19), (20, 20)]:
    anchors_c1.append((words_v6_synced[i]["start"], c1_words[vid_i]["start"]))
# Word 22 ("MascotaMás!") -> c1_words[21]..c1_words[22]
anchors_c1.append((words_v6_synced[21]["start"], c1_words[21]["start"]))
anchors_c1.append((words_v6_synced[21]["end"], c1_words[22]["end"]))
# Words 23..36 ("Te hacemos ... consultorio.") -> c1_words[23..36]
for i in range(22, 36):
    vid_i = i + 1
    anchors_c1.append((words_v6_synced[i]["start"], c1_words[vid_i]["start"]))
    anchors_c1.append((words_v6_synced[i]["end"], c1_words[vid_i]["end"]))
anchors_c1.append((11.52, 13.80))  # Smooth hold in closed-lip smile until Beat 24 (11.52s)

# Clip 2 (Escenas 3 y 4: 11.52s -> 24.00s)
c2_words = trans["v6_clip2_tres_cuartos.mp4"]["words"]  # 34 words (exact 1:1 with words 37..70 in TTS!)
anchors_c2 = [(11.52, 0.00), (11.68, 0.02)]
for i in range(36, 52):
    vid_i = i - 36
    anchors_c2.append((words_v6_synced[i]["start"], c2_words[vid_i]["start"]))
    anchors_c2.append((words_v6_synced[i]["end"], c2_words[vid_i]["end"]))
anchors_c2.append((17.76, 5.28))  # Beat 37 transition (natural pause)
for i in range(52, 70):
    vid_i = i - 36
    anchors_c2.append((words_v6_synced[i]["start"], c2_words[vid_i]["start"]))
    anchors_c2.append((words_v6_synced[i]["end"], c2_words[vid_i]["end"]))
anchors_c2.append((24.00, 12.20))  # Smooth hold in closed-lip smile until Beat 50 (24.00s)

# Clip 3 (Escenas 5 y 6: 24.00s -> 33.60s)
c3_words = trans["v6_clip3_frente_cta.mp4"]["words"]  # First 26 words match Words 71..96 in TTS 1:1!
anchors_c3 = [(24.00, 0.00), (24.16, 0.02)]
for i in range(70, 85):
    vid_i = i - 70
    anchors_c3.append((words_v6_synced[i]["start"], c3_words[vid_i]["start"]))
    anchors_c3.append((words_v6_synced[i]["end"], c3_words[vid_i]["end"]))
anchors_c3.append((29.28, 5.04))  # Beat 61 transition (natural pause before CTA)
for i in range(85, 96):
    vid_i = i - 70
    anchors_c3.append((words_v6_synced[i]["start"], c3_words[vid_i]["start"]))
    anchors_c3.append((words_v6_synced[i]["end"], c3_words[vid_i]["end"]))
# After "día!" ends at 32.86s (vid 7.90s), jump smoothly during the outro to the clean closed-lip smile at 12.20..14.60s
anchors_c3.append((32.92, 12.40))
anchors_c3.append((33.60, 14.50))

t_all = np.arange(total_frames, dtype=np.float64) / float(fps_out)
f_cut1 = int(round(11.52 * fps_out))  # Frame 346
f_cut2 = int(round(24.00 * fps_out))  # Frame 720

curve_1 = build_smooth_scene_curve(t_all[:f_cut1], anchors_c1, sigma_frames=2.8)
curve_2 = build_smooth_scene_curve(t_all[f_cut1:f_cut2], anchors_c2, sigma_frames=2.8)
# For curve_3, build PCHIP up to 32.88s (speech end) and linear smile tail 32.88..33.60s so it doesn't smear across 7.90..12.40s
f_speech_end = int(round(32.88 * fps_out))
curve_3_speech = build_smooth_scene_curve(t_all[f_cut2:f_speech_end], anchors_c3[:-2], sigma_frames=2.8)
curve_3_smile = np.linspace(12.50, 14.50, total_frames - f_speech_end, dtype=np.float64)
curve_3 = np.concatenate([curve_3_speech, curve_3_smile])

out_master_mp4 = os.path.join(WORK_DIR, "v6_vet_lipsync_master.mp4")
cmd = [
    FFMPEG_BIN, "-y", "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "bgr24",
    "-s", "1080x1920", "-r", str(fps_out), "-i", "-", "-i", tts_v6_synced_path,
    "-c:v", "libx264", "-crf", "16", "-preset", "fast", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "192k", "-shortest", out_master_mp4
]
proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
for f_idx in range(total_frames):
    if f_idx < f_cut1:
        frm = sample_frame(frames_c1, fps_c1, float(curve_1[f_idx]))
    elif f_idx < f_cut2:
        frm = sample_frame(frames_c2, fps_c2, float(curve_2[f_idx - f_cut1]))
    else:
        frm = sample_frame(frames_c3, fps_c3, float(curve_3[f_idx - f_cut2]))
    proc.stdin.write(frm.tobytes())
proc.stdin.close()
proc.wait()

with open(os.path.join(WORK_DIR, "v6_words_synced.json"), "w", encoding="utf-8") as f:
    json.dump({
        "duration": total_dur,
        "transitions": transitions,
        "words": words_v6_synced
    }, f, ensure_ascii=False, indent=2)

print(f"[MASTER VIDEO V6 DONE] {out_master_mp4} ({os.path.getsize(out_master_mp4)} bytes)")
