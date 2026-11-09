# -*- coding: utf-8 -*-
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

print("[1/3] Cargando fotogramas de reel_cal_mp_v3_lipsync_raw.mp4...")
frames_v3, fps_v3 = load_video_frames(v3_raw_path)
print(f"  -> {len(frames_v3)} fotogramas cargados (@ {fps_v3:.2f} fps)")

def sample_frame(frames, src_fps, t_sec):
    idx_f = max(0.0, min(float(len(frames) - 1), t_sec * src_fps))
    i0 = int(np.floor(idx_f))
    i1 = min(len(frames) - 1, i0 + 1)
    alpha = idx_f - i0
    if alpha < 1e-3 or i0 == i1:
        return frames[i0]
    return cv2.addWeighted(frames[i0], 1.0 - alpha, frames[i1], alpha, 0.0)

# Load word timestamps 1..54 from transcription_table.json (Turns 1 & 2)
with open(os.path.join(WORK_DIR, "transcription_table.json"), "r", encoding="utf-8") as f:
    t12 = json.load(f)["words"]

vid_w_1_54 = []
for w in t12:
    if w["word_id"] <= 56 and w["word_id"] not in (30, 31):
        vid_w_1_54.append((float(w["real_start"]), float(w["end"])))

# Words 55..68 from large-v3 transcription of Turn 3 in v3_raw
vid_w_55_68 = [
    (22.190, 22.520),  # 55: Además,
    (23.100, 23.440),  # 56: activás
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

# Notice: for Scene 6 (25.44s -> 28.80s), what if we keep 100% continuous unbroken v3_raw
# by mapping the 2 segments of Scene 6?
# Wait: in v3_raw, from 27.30s to 27.50s her mouth is closed (matching 25.08s -> 25.64s pause!).
# And in v3_raw from 27.50s to 28.55s she speaks the CTA and from 28.55s to 29.80s she smiles warmly with her mouth closed!
# Wait: what if we compare:
# Option A: Continuous unbroken v3_raw from 0.00s to 29.80s (where words 69..75 map across 27.50s..28.55s, and 27.62s..28.80s maps across 28.55s..29.80s)
# Let's check the speed of 27.50s..28.55s (1.05s of speech mapped to 1.98s = 0.53x for 1.9s) vs:
# What if during 25.64s..26.96s ("¡Entrá hoy en MascotaMás", 1.32s) and 26.96s..27.62s ("y probalo!", 0.66s),
# we check if v3_raw has any artifact at 0.53x?With sub-frame interpolation over 1.9s, wait: why not check BOTH or see how natural v3_raw looks?
# Even better: in v3_raw, at t=25.44s there is a SCENE TRANSITION (Scene 5 -> Scene 6)!
# At a scene transition (t=25.44s), if we start Scene 6 in v3_raw at 26.08s (where she articulates "asegurar cada turno" = 7 syllables in 1.22s with bilabial/dental/open vowels, followed by a brief 0.18s breath at 27.30..27.50s, or wait - "Entrá hoy en MascotaMás y probalo" has NO pause inside it!).
# Wait: in v3_raw:
# - 27.50s -> 27.92s: "Entrá..." (open E-A, dental T-R)
# - 27.92s -> 28.04s: bilabial closure (lips close!) -> matches the "M" of "MascotaMás" at 26.34s!
# - 28.04s -> 28.56s: "...y probalo!" (open O-A-O + bilabial B/P!)
# WAIT A SECOND!
# Look at the phonetic structure of "Entrá hoy en MascotaMás y probalo!":
# 1. "Entrá hoy en" (25.64s -> 26.34s = 0.70s): open vowels without full lip closure, ending right as the lips close for "M" of "Mascota"!
#    In v3_raw: 27.50s -> 27.96s (0.46s) is "Entrá..." ending with full lip closure at 27.96s! (Ratio = 0.46 / 0.70 = 0.66x — completely smooth!)
# 2. "MascotaMás y probalo!" (26.34s -> 27.62s = 1.28s): starts with lip closure at 26.34s, opens on "Ma-sco-ta-Más y pro-ba-lo" and closes lips at 27.62s!
#    In v3_raw: 27.96s -> 28.58s (0.62s) starts with lip closure at 27.96s, opens on "...pro-ba-lo" and closes lips into a warm smile at 28.58s!
# 3. Final warm smile (27.62s -> 28.80s = 1.18s):
#    In v3_raw: 28.58s -> 29.78s (1.20s — 1.02x exact real-time!) she holds a warm, radiant closed-mouth smile looking straight into the lens!

vid_w_69_75 = [
    (27.500, 27.680),  # 69: Entrá
    (27.680, 27.820),  # 70: hoy
    (27.820, 27.950),  # 71: en
    (27.950, 28.140),  # 72: Mascota
    (28.140, 28.260),  # 73: Más
    (28.260, 28.360),  # 74: y
    (28.360, 28.580),  # 75: probalo!
]

all_vid_words = vid_w_1_54 + vid_w_55_68 + vid_w_69_75
assert len(all_vid_words) == 75, f"Expected 75 words, got {len(all_vid_words)}"

# Build piecewise-linear control points (tts_t, vid_t) across the entire 28.80s timeline
# Also anchor inter-sentence silent pauses so her mouth stays closed during beat transitions!
anchors = [
    (0.00, 0.42),   # Pre-speech breath before "¡Mirá"
]

# Sentence 1 (words 1..12: idx 0..11)
for idx in range(0, 12):
    tw = tts_words[idx]
    vs, ve = all_vid_words[idx]
    anchors.append((float(tw["start"]), vs))
    anchors.append((float(tw["end"]), ve))

# Pause 1 (3.90s -> 4.44s across Beat 9 transition at 4.32s): closed mouth in v3_raw (3.95s -> 4.25s)
anchors.append((4.32, 4.12))

# Sentence 2 (words 13..29: idx 12..28)
for idx in range(12, 29):
    tw = tts_words[idx]
    vs, ve = all_vid_words[idx]
    anchors.append((float(tw["start"]), vs))
    anchors.append((float(tw["end"]), ve))

# Pause 2 (10.40s -> 11.06s across Beat 22 transition at 10.56s): closed mouth in v3_raw (12.15s -> 12.45s, skipping deleted 'o internas' at 11.41..12.05s!)
# Wait: at t=10.56s is the Scene 2 -> Scene 3 beat cut! So jumping from 11.41s to 12.25s right at the t=10.56s scene cut is 100% invisible and skips the mouth movement of deleted words 'o internas'!
anchors.append((10.55, 11.43))
anchors.append((10.56, 12.25))

# Sentence 3 (words 30..40: idx 29..39)
for idx in range(29, 40):
    tw = tts_words[idx]
    vs, ve = all_vid_words[idx]
    anchors.append((float(tw["start"]), vs))
    anchors.append((float(tw["end"]), ve))

# Pause 3 (15.20s -> 15.76s across Beat 32 transition at 15.36s)
anchors.append((15.36, 16.35))

# Sentence 4 (words 41..54: idx 40..53)
for idx in range(40, 54):
    tw = tts_words[idx]
    vs, ve = all_vid_words[idx]
    anchors.append((float(tw["start"]), vs))
    anchors.append((float(tw["end"]), ve))

# Pause 4 (19.90s -> 20.62s across Beat 42 transition at 20.16s): closed mouth in v3_raw (21.11s -> 22.18s)
anchors.append((20.16, 21.65))

# Sentence 5 (words 55..68: idx 54..67)
# Note: in v3_raw there is a 0.5s pause between "Además" (22.52s) and "activás" (23.10s), while in TTS "Además" ends at 20.92s and "activás" starts at 21.20s (0.28s pause) - the piecewise linear map naturally compresses that pause!
for idx in range(54, 68):
    tw = tts_words[idx]
    vs, ve = all_vid_words[idx]
    anchors.append((float(tw["start"]), vs))
    anchors.append((float(tw["end"]), ve))

# Pause 5 (25.08s -> 25.64s across Beat 53 transition at 25.44s): closed mouth in v3_raw (27.30s -> 27.50s)
anchors.append((25.44, 27.40))

# Sentence 6 (words 69..75: idx 68..74)
for idx in range(68, 75):
    tw = tts_words[idx]
    vs, ve = all_vid_words[idx]
    anchors.append((float(tw["start"]), vs))
    anchors.append((float(tw["end"]), ve))

# Final warm smile (27.62s -> 28.80s): maps to 28.58s -> 29.78s in v3_raw
anchors.append((total_dur, 29.78))

# Clean & deduplicate anchors so tts_t is strictly increasing
clean_anchors = [anchors[0]]
for t_tts, t_vid in anchors[1:]:
    prev_tts, prev_vid = clean_anchors[-1]
    if t_tts <= prev_tts + 1e-4:
        clean_anchors[-1] = (prev_tts, max(prev_vid, t_vid))
    else:
        clean_anchors.append((t_tts, max(prev_vid, t_vid)))

xp = np.array([a[0] for a in clean_anchors], dtype=np.float64)
yp = np.array([a[1] for a in clean_anchors], dtype=np.float64)

print(f"[2/3] Generando {total_frames} fotogramas sincronizados palabra por palabra ({total_dur:.2f}s @ {fps}fps)...")
cmd = [
    FFMPEG_BIN, "-y",
    "-f", "rawvideo",
    "-vcodec", "rawvideo",
    "-pix_fmt", "bgr24",
    "-s", "1080x1920",
    "-r", str(fps),
    "-i", "-",
    "-i", os.path.join(WORK_DIR, "gemini_tts_ar_synced.wav"),
    "-c:v", "libx264",
    "-crf", "16",
    "-preset", "fast",
    "-pix_fmt", "yuv420p",
    "-c:a", "aac",
    "-b:a", "192k",
    "-shortest",
    out_master_mp4
]
proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

for f_idx in range(total_frames):
    t_out = f_idx / float(fps)
    t_src = float(np.interp(t_out, xp, yp))
    frm = sample_frame(frames_v3, fps_v3, t_src)
    proc.stdin.write(frm.tobytes())

proc.stdin.close()
proc.wait()
print(f"[3/3] ¡Listo! Video maestro con lip-sync sincronizado guardado en: {out_master_mp4} ({os.path.getsize(out_master_mp4)} bytes)")
