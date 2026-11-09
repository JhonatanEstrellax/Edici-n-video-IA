# -*- coding: utf-8 -*-
import os
import json
import subprocess
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfiltfilt, resample_poly
from faster_whisper import WhisperModel

BASE_DIR = r"c:\IA\Edicion de videos"
WORK_DIR = os.path.join(BASE_DIR, "reels_work")

tts_in = os.path.join(WORK_DIR, "gemini_tts_ar_v2.wav")
lyria_mp3 = os.path.join(WORK_DIR, "lyria3_house_v2.mp3")
lyria_wav = os.path.join(WORK_DIR, "lyria3_house_raw.wav")

# 1. Read Lyria 3 MP3 directly via soundfile
bgm_raw, bgm_sr_raw = sf.read(lyria_mp3, dtype="float32")
if bgm_raw.ndim == 1:
    bgm_raw = np.column_stack([bgm_raw, bgm_raw])
sf.write(lyria_wav, bgm_raw, bgm_sr_raw)

# 2. Load TTS WAV (24kHz mono) and find exact silent split points between the 6 sentences
tts_data, tts_sr = sf.read(tts_in, dtype="float32")
if tts_data.ndim > 1:
    tts_data = tts_data.mean(axis=1)

# Approximate silent windows between the 6 sentences from Whisper:
# S1: 0.00 - 3.98 | gap1: 3.98 - 4.44
# S2: 4.44 - 10.42 | gap2: 10.42 - 11.12
# S3: 11.12 - 15.30 | gap3: 15.30 - 15.64
# S4: 15.64 - 19.94 | gap4: 19.94 - 20.68
# S5: 20.68 - 25.14 | gap5: 25.14 - 25.60
# S6: 25.60 - 27.58

def find_quietest_point(audio, sr, t_start, t_end):
    s0 = int(t_start * sr)
    s1 = int(t_end * sr)
    win = int(0.02 * sr)
    best_i = (s0 + s1) // 2
    best_e = 1e9
    for i in range(s0, max(s0 + 1, s1 - win), max(1, win // 4)):
        e = float(np.mean(audio[i:i+win] ** 2))
        if e < best_e:
            best_e = e
            best_i = i + win // 2
    return best_i / sr

cut1 = find_quietest_point(tts_data, tts_sr, 4.02, 4.40)
cut2 = find_quietest_point(tts_data, tts_sr, 10.48, 11.05)
cut3 = find_quietest_point(tts_data, tts_sr, 15.32, 15.60)
cut4 = find_quietest_point(tts_data, tts_sr, 20.00, 20.60)
cut5 = find_quietest_point(tts_data, tts_sr, 25.18, 25.55)

cuts = [0.0, cut1, cut2, cut3, cut4, cut5, len(tts_data) / tts_sr]
print("Split points in raw TTS (sec):", [round(c, 3) for c in cuts])

# Trim leading/trailing silence on each sentence chunk while keeping 40ms natural breath pad
sentences_audio = []
for idx in range(6):
    c0 = int(cuts[idx] * tts_sr)
    c1 = int(cuts[idx + 1] * tts_sr)
    chunk = tts_data[c0:c1].copy()
    # find active speech bounds (> 0.003 amplitude)
    abs_c = np.abs(chunk)
    active = np.where(abs_c > 0.004)[0]
    if len(active) > 0:
        a0 = max(0, int(active[0]) - int(0.035 * tts_sr))
        a1 = min(len(chunk), int(active[-1]) + int(0.055 * tts_sr))
        chunk = chunk[a0:a1]
    # smooth 12ms fade in/out to prevent clicks
    fade = min(int(0.012 * tts_sr), len(chunk) // 4)
    if fade > 0:
        chunk[:fade] *= np.linspace(0.0, 1.0, fade, dtype=np.float32)
        chunk[-fade:] *= np.linspace(1.0, 0.0, fade, dtype=np.float32)
    sentences_audio.append(chunk)
    print(f"  Sentence {idx+1} clean duration: {len(chunk)/tts_sr:.3f}s")

# 3. Exact 125 BPM Beat Grid (1 beat = 0.48s)
# Transitions at exact 125 BPM downbeats:
# Scene 1: 0.00s -> 4.32s (9 beats)
# Scene 2: 4.32s -> 10.56s (13 beats)
# Scene 3: 10.56s -> 15.36s (10 beats, lands on Bar 9 Main Drop at 15.36s!)
# Scene 4: 15.36s -> 20.16s (10 beats)
# Scene 5: 20.16s -> 25.44s (11 beats)
# Scene 6: 25.44s -> 28.80s (7 beats, total = 60 beats = 28.80s)
transitions = [0.00, 4.32, 10.56, 15.36, 20.16, 25.44, 28.80]
sentence_starts = [0.12, 4.46, 10.74, 15.52, 20.34, 25.62]

total_dur = 28.80
master_tts = np.zeros(int(total_dur * tts_sr), dtype=np.float32)

for idx in range(6):
    st_sec = sentence_starts[idx]
    st_idx = int(round(st_sec * tts_sr))
    chunk = sentences_audio[idx]
    end_idx = min(len(master_tts), st_idx + len(chunk))
    master_tts[st_idx:end_idx] = chunk[:end_idx - st_idx]
    print(f"  Placed Sentence {idx+1}: {st_sec:.2f}s -> {end_idx/tts_sr:.2f}s (next transition at {transitions[idx+1]:.2f}s)")

tts_synced_path = os.path.join(WORK_DIR, "gemini_tts_ar_synced.wav")
sf.write(tts_synced_path, master_tts, tts_sr)
print(f"Saved synced TTS to {tts_synced_path} ({total_dur:.2f}s)")

# 4. Align Lyria 3 House Music (125 BPM) and add subtle studio House transition risers/hits at the exact transition downbeats
bgm, bgm_sr = sf.read(lyria_wav, dtype="float32")
target_bgm_len = int(total_dur * bgm_sr)

# Detect first strong low-frequency kick transient in Lyria 3 so beat 0 is locked to t=0.00s
sos_lp = butter(4, 130.0, btype="low", fs=bgm_sr, output="sos")
low_band = sosfiltfilt(sos_lp, bgm[:, 0])
env = np.abs(low_band[:int(1.0 * bgm_sr)])
first_kick_idx = int(np.argmax(env > (0.45 * np.max(env))))
print(f"Lyria 3 first kick transient at {first_kick_idx / bgm_sr:.4f}s")

if first_kick_idx > 0 and len(bgm) - first_kick_idx >= target_bgm_len:
    bgm_aligned = bgm[first_kick_idx:first_kick_idx + target_bgm_len].copy()
else:
    bgm_aligned = bgm[:target_bgm_len].copy()

# Add subtle, authentic House transition accents (airy white-noise filter sweep + warm sub-kick reinforcement)
# at each scene transition [4.32, 10.56, 15.36, 20.16, 25.44] so every visual transition is felt musically
rng = np.random.default_rng(42)
for t_tr in transitions[1:-1]:
    center = int(t_tr * bgm_sr)
    # 0.36s pre-transition airy House riser (bandpass filtered noise sweeping up)
    riser_len = int(0.36 * bgm_sr)
    r0 = max(0, center - riser_len)
    noise = rng.normal(0, 1.0, center - r0).astype(np.float32)
    sos_bp = butter(2, [1200.0, 5500.0], btype="bandpass", fs=bgm_sr, output="sos")
    riser = sosfiltfilt(sos_bp, noise)
    env_r = np.linspace(0.0, 1.0, len(riser), dtype=np.float32) ** 2.2
    riser *= env_r * 0.08
    bgm_aligned[r0:center, 0] += riser
    bgm_aligned[r0:center, 1] += riser * 0.95

    # Crisp House downbeat sub-punch + shimmer at exact transition frame
    hit_len = int(0.28 * bgm_sr)
    h1 = min(len(bgm_aligned), center + hit_len)
    t_vec = np.arange(h1 - center, dtype=np.float32) / bgm_sr
    # Warm 90Hz->48Hz house kick reinforcement
    freq_env = 48.0 + 45.0 * np.exp(-t_vec * 28.0)
    phase = 2.0 * np.pi * np.cumsum(freq_env) / bgm_sr
    sub_hit = np.sin(phase) * np.exp(-t_vec * 11.0) * 0.18
    bgm_aligned[center:h1, 0] += sub_hit
    bgm_aligned[center:h1, 1] += sub_hit

# Smooth fade-out at the end (last 0.65s)
fade_len = int(0.65 * bgm_sr)
fade_curve = np.linspace(1.0, 0.0, fade_len, dtype=np.float32)[:, None]
bgm_aligned[-fade_len:] *= fade_curve

peak = float(np.max(np.abs(bgm_aligned)))
if peak > 0.98:
    bgm_aligned *= (0.95 / peak)

bgm_synced_path = os.path.join(WORK_DIR, "lyria3_house_synced.wav")
sf.write(bgm_synced_path, bgm_aligned, bgm_sr)
sf.write(os.path.join(BASE_DIR, "bgm_lyria3_house.wav"), bgm_aligned, bgm_sr)
print(f"Saved beat-synced Lyria 3 House music to {bgm_synced_path}")

# 5. Transcribe the beat-synced TTS audio to get exact word timestamps for Poppins subtitles
wav_16k = resample_poly(master_tts, 16000, tts_sr).astype(np.float32)
model = WhisperModel("small", device="cpu", compute_type="int8")
segments, info = model.transcribe(wav_16k, language="es", word_timestamps=True)

words_out = []
wid = 1
for seg in segments:
    for w in seg.words:
        txt = w.word.strip()
        if not txt:
            continue
        words_out.append({
            "word_id": wid,
            "word": txt,
            "start": round(float(w.start), 3),
            "end": round(float(w.end), 3),
            "probability": round(float(w.probability), 3)
        })
        print(f"  [{wid:02d}] {w.start:5.2f} - {w.end:5.2f}: {txt}")
        wid += 1

with open(os.path.join(WORK_DIR, "tts_v2_words.json"), "w", encoding="utf-8") as f:
    json.dump({"duration": total_dur, "transitions": transitions, "words": words_out}, f, ensure_ascii=False, indent=2)
