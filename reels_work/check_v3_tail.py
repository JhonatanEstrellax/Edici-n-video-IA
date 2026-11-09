# -*- coding: utf-8 -*-
"""
Construye el video maestro `v3_vet_lipsync_master.mp4` (28.80s @ 30fps, 1080x1920):
- Sincroniza palabra por palabra (75 palabras exactas) los labios de la veterinaria
  (`reel_cal_mp_v3_lipsync_raw.mp4` + cierre CTA de `reel_cal_mp_lipsync_full.mp4`)
  con la locución argentina 10/10 (`gemini_tts_ar_synced.wav`) y las transiciones
  al compás de 125 BPM de Lyria 3 House (`[0.00, 4.32, 10.56, 15.36, 20.16, 25.44, 28.80]`).
"""
import os
import sys
import json
import cv2
import numpy as np
import subprocess

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

BASE_DIR = r"c:\IA\Edicion de videos"
WORK_DIR = os.path.join(BASE_DIR, "reels_work")
FFMPEG_BIN = os.path.join(BASE_DIR, "bin", "ffmpeg", "ffmpeg.exe")

v3_raw_path = os.path.join(WORK_DIR, "reel_cal_mp_v3_lipsync_raw.mp4")
v1_raw_path = os.path.join(WORK_DIR, "reel_cal_mp_lipsync_full.mp4")
tts_words_path = os.path.join(WORK_DIR, "tts_v2_words.json")
out_master_mp4 = os.path.join(WORK_DIR, "v3_vet_lipsync_master.mp4")

with open(tts_words_path, "r", encoding="utf-8") as f:
    tts_data = json.load(f)

tts_words = tts_data["words"]  # 75 words (word_id 1..75)
total_dur = float(tts_data["duration"])  # 28.80s
fps = 30
total_frames = int(round(total_dur * fps))  # 864 frames

# Load all frames from v3_raw_path and v1_raw_path into memory for sub-frame accurate interpolation
def load_video_frames(path):
    cap = cv2.VideoCapture(path)
    v_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
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

print("[1/3] Cargando fotogramas de la veterinaria en memoria...")
frames_v3, fps_v3 = load_video_frames(v3_raw_path)
frames_v1, fps_v1 = load_video_frames(v1_raw_path)
print(f"  -> v3_raw: {len(frames_v3)} frames @ {fps_v3:.2f}fps | v1_raw: {len(frames_v1)} frames @ {fps_v1:.2f}fps")

# Word timestamps in v3_raw (words 1..68 and 74..75) and v1_raw (words 69..73)
with open(os.path.join(WORK_DIR, "transcription_table.json"), "r", encoding="utf-8") as f:
    t12 = json.load(f)["words"]

vid_w_1_54 = []
for w in t12:
    if w["word_id"] <= 56 and w["word_id"] not in (30, 31):
        vid_w_1_54.append((float(w["real_start"]), float(w["end"])))

# Words 55..68 from large-v3 transcription of Turn 3 in v3_raw
vid_w_55_68 = [
    (22.190, 22.520),  # 55: Además,
    (22.740, 23.440),  # 56: activás
    (23.440, 23.560),  # 57: el
    (23.560, 23.880),  # 58: cobro
    (23.880, 23.940),  # 59: de
    (23.940, 24.280),  # 60: seña
    (24.280, 24.920),  # 61: automático
    (24.920, 25.100),  # 62: con
    (25.100, 25.520),  # 63: Mercado
    (25.520, 25.860),  # 64: Pago
    (25.860, 26.080),  # 65: para
    (26.080, 26.580),  # 66: asegurar
    (26.580, 26.800),  # 67: cada
    (26.800, 27.300),  # 68: turno.
]

# Words 69..73 ("¡Entrá hoy en Mascota Más") from v1_raw + Words 74..75 ("y probalo!") from v3_raw
# Wait: let's check if we can make Scene 6 (25.44s -> 28.80s) a single continuous unbroken shot from v3_raw
# OR blend seamlessly at word 74.
# Wait: in v3_raw, from 27.320 to 28.520 she says "¡Entrá... y probalo!" and smiles from 28.520 to 29.950!
# Let's check how many syllables she articulates in v3_raw between 27.30 and 28.55 vs v1_raw + v3_raw!
# In v1_raw (28.424 -> 29.680), she says "Entrá hoy en Mascota Más" (5 words = 1.25s, exact match to TTS 25.64 -> 26.96 = 1.32s!).
# And in v3_raw (27.840 -> 28.520), she says "y probalo!" (2 words = 0.68s, exact match to TTS 26.96 -> 27.62 = 0.66s!) and then smiles (28.52 -> 29.95 = 1.43s, exact match to TTS 27.62 -> 28.80 = 1.18s!).

# Let's build the piecewise-linear control points (tts_t, source_id, vid_t) for Scenes 1..5 (0.00s -> 25.44s) using v3_raw
anchors_s1_s5 = [(0.0, 0.35)]  # At t=0.00s, start just before word 1 in v3_raw (0.35s -> 0.594s pre-speech breath)

all_vid_1_68 = vid_w_1_54 + vid_w_55_68
assert len(all_vid_1_68) == 68, f"Expected 68 words, got {len(all_vid_1_68)}"

for idx in range(68):
    tw = tts_words[idx]
    vs, ve = all_vid_1_68[idx]
    ts, te = float(tw["start"]), float(tw["end"])
    # Ensure strictly non-decreasing anchors
    if ts > anchors_s1_s5[-1][0] + 0.005:
        if vs > anchors_s1_s5[-1][1] + 0.005:
            anchors_s1_s5.append((ts, vs))
        else:
            anchors_s1_s5.append((ts, anchors_s1_s5[-1][1] + 0.005))
    if te > anchors_s1_s5[-1][0] + 0.005:
        ve_safe = max(ve, anchors_s1_s5[-1][1] + 0.01)
        anchors_s1_s5.append((te, ve_safe))

# End of Scene 5 (25.08s -> 25.44s): closed-mouth pause at 27.30s -> 27.32s in v3_raw
anchors_s1_s5.append((25.44, 27.31))

# Scene 6 (25.44s -> 28.80s):
# Wait: what if we compare how v3_raw looks at 27.31s vs v1_raw at 28.35s?
# Both v1_raw and v3_raw are extensions of the EXACT SAME Turn 2 (`res2_id`), but at t=27s they are 5 seconds into Turn 3,
# so her head position at v1_raw(28.35s) vs v3_raw(27.84s) might differ by a few pixels if we cut mid-Scene 6!
# Whereas at t=25.44s (the Scene 5 -> Scene 6 beat transition!), there is ALREADY a scene transition with whip-zoom + glow!
# AND what if in Scene 6 (25.44s -> 28.80s) we check whether using v3_raw continuously or v1_raw -> v3_raw is smoother?
# Wait: why did Whisper transcribe v3_raw (27.32 -> 28.52) as "Entrás y próbalo"? Let's check the audio duration of v3_raw from 27.30 to 29.95!
