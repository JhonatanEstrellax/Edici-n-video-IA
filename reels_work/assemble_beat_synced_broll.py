# -*- coding: utf-8 -*-
import os
import cv2
import subprocess
import numpy as np

BASE_DIR = r"c:\IA\Edicion de videos"
WORK_DIR = os.path.join(BASE_DIR, "reels_work")
FFMPEG_BIN = os.path.join(BASE_DIR, "bin", "ffmpeg", "ffmpeg.exe")

p1 = os.path.join(WORK_DIR, "v2_cinema_broll_part1.mp4")
p2 = os.path.join(WORK_DIR, "v2_cinema_broll_part2.mp4")

def load_all_frames(path):
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    frames = []
    while True:
        ret, fr = cap.read()
        if not ret or fr is None:
            break
        if fr.shape[1] != 1080 or fr.shape[0] != 1920:
            fr = cv2.resize(fr, (1080, 1920), interpolation=cv2.INTER_AREA)
        frames.append(fr)
    cap.release()
    return frames, fps

def find_scene_cuts(frames, fps):
    diffs = []
    for i in range(1, len(frames)):
        g0 = cv2.cvtColor(cv2.resize(frames[i-1], (180, 320)), cv2.COLOR_BGR2GRAY).astype(np.float32)
        g1 = cv2.cvtColor(cv2.resize(frames[i], (180, 320)), cv2.COLOR_BGR2GRAY).astype(np.float32)
        diffs.append((i, float(np.mean(np.abs(g1 - g0)))))
    # Sort by largest frame difference to find the 2 internal shot cuts (around ~5s and ~10s)
    cut1_candidates = [d for d in diffs if 3.2 * fps <= d[0] <= 6.8 * fps]
    cut2_candidates = [d for d in diffs if 8.2 * fps <= d[0] <= 11.8 * fps]
    c1 = max(cut1_candidates, key=lambda x: x[1])[0] if cut1_candidates else int(5.0 * fps)
    c2 = max(cut2_candidates, key=lambda x: x[1])[0] if cut2_candidates else int(10.0 * fps)
    print(f"  Detected internal shot cuts at frame {c1} ({c1/fps:.2f}s) and frame {c2} ({c2/fps:.2f}s)")
    return c1, c2

print("Analyzing v2_cinema_broll_part1.mp4...")
f1, fps1 = load_all_frames(p1)
c1_a, c1_b = find_scene_cuts(f1, fps1)

print("Analyzing v2_cinema_broll_part2.mp4...")
f2, fps2 = load_all_frames(p2)
c2_a, c2_b = find_scene_cuts(f2, fps2)

# Trim 2 frames on either side of internal cuts to avoid any transition blend frame
shots = [
    f1[0 : max(10, c1_a - 2)],                    # Shot 1: Vet + Golden Retriever (Hook)
    f1[c1_a + 2 : max(c1_a + 12, c1_b - 2)],      # Shot 2: French Bulldog Walk in Park (Turnos 1a1 & Paseos)
    f1[c1_b + 2 : len(f1)],                       # Shot 3: White Poodle Grooming (Servicios y Profesionales)
    f2[0 : max(10, c2_a - 2)],                    # Shot 4: Puppies in Dog Daycare (Guardería)
    f2[c2_a + 2 : max(c2_a + 12, c2_b - 2)],      # Shot 5: Vet Hands on MacBook Pro + iPhone + Cat (Mercado Pago Seña)
    f2[c2_b + 2 : len(f2)],                       # Shot 6: Golden Puppy + Kitten Snuggling (CTA)
]

for idx, s in enumerate(shots, 1):
    print(f"  Pure Shot {idx}: {len(s)} frames ({len(s)/24.0:.2f}s @ 24fps)")

# Target 125 BPM Beat-Synced Transitions @ 30.0 fps:
# [0.00, 4.32, 10.56, 15.36, 20.16, 25.44, 28.80]
out_fps = 30.0
transitions = [0.00, 4.32, 10.56, 15.36, 20.16, 25.44, 28.80]
total_out_frames = int(round(transitions[-1] * out_fps))

out_mp4 = os.path.join(WORK_DIR, "v2_broll_master.mp4")
cmd = [
    FFMPEG_BIN, "-y",
    "-f", "rawvideo", "-vcodec", "rawvideo",
    "-pix_fmt", "bgr24", "-s", "1080x1920", "-r", "30",
    "-i", "-",
    "-i", os.path.join(WORK_DIR, "gemini_tts_ar_synced.wav"),
    "-c:v", "libx264", "-crf", "16", "-preset", "fast", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "192k", "-shortest",
    out_mp4
]
proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

for f_idx in range(total_out_frames):
    t = f_idx / out_fps
    sc_idx = 5
    for i in range(6):
        if transitions[i] <= t < transitions[i+1]:
            sc_idx = i
            break
    sc_t0 = transitions[sc_idx]
    sc_t1 = transitions[sc_idx + 1]
    u = (t - sc_t0) / max(0.001, sc_t1 - sc_t0)
    u = max(0.0, min(1.0, u))

    shot_frames = shots[sc_idx]
    # Smoothly map progress u -> frame index in shot_frames
    pos = u * (len(shot_frames) - 1)
    idx0 = int(pos)
    idx1 = min(len(shot_frames) - 1, idx0 + 1)
    frac = pos - idx0
    if frac < 0.01 or idx0 == idx1:
        frame = shot_frames[idx0]
    else:
        frame = cv2.addWeighted(shot_frames[idx0], 1.0 - frac, shot_frames[idx1], frac, 0.0)

    proc.stdin.write(frame.tobytes())

proc.stdin.close()
proc.wait()
print(f"Assembled beat-synced master B-roll video -> {out_mp4} ({total_out_frames} frames @ 30fps)")
