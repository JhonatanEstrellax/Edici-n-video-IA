# -*- coding: utf-8 -*-
import os
import sys
import json
import subprocess
import soundfile as sf
from faster_whisper import WhisperModel

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

BASE_DIR = r"c:\IA\Edicion de videos"
WORK_DIR = os.path.join(BASE_DIR, "reels_work")
FFMPEG_BIN = os.path.join(BASE_DIR, "bin", "ffmpeg", "ffmpeg.exe")

v3_raw_mp4 = os.path.join(WORK_DIR, "reel_cal_mp_v3_lipsync_raw.mp4")
v3_raw_wav = os.path.join(WORK_DIR, "reel_cal_mp_v3_lipsync_raw_16k.wav")

subprocess.run([
    FFMPEG_BIN, "-y", "-i", v3_raw_mp4,
    "-vn", "-ac", "1", "-ar", "16000", v3_raw_wav
], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

with open(os.path.join(WORK_DIR, "transcription_table.json"), "r", encoding="utf-8") as f:
    t12 = json.load(f)["words"]

# Keep words 1..56 from Turns 1 & 2 (excluding 30, 31 'o internas')
vid_words = []
for w in t12:
    if w["word_id"] <= 56 and w["word_id"] not in (30, 31):
        vid_words.append({
            "word_id": len(vid_words) + 1,
            "word": w["word"],
            "start": round(float(w["real_start"]), 4),
            "end": round(float(w["end"]), 4)
        })

audio_16k, sr = sf.read(v3_raw_wav, dtype="float32")
offset_sec = 21.60
tail_audio = audio_16k[int(offset_sec * sr):]

model = WhisperModel("small", device="cpu", compute_type="int8")
segments, _ = model.transcribe(
    tail_audio,
    language="es",
    word_timestamps=True,
    vad_filter=False,
    initial_prompt="Además, activás el cobro de seña automático con Mercado Pago para asegurar cada turno. ¡Entrá hoy en MascotaMás y probalo!"
)

for seg in segments:
    for w in (seg.words or []):
        tok = w.word.strip()
        if not tok:
            continue
        vid_words.append({
            "word_id": len(vid_words) + 1,
            "word": tok,
            "start": round(offset_sec + float(w.start), 4),
            "end": round(offset_sec + float(w.end), 4)
        })

out_path = os.path.join(WORK_DIR, "v3_raw_vid_words.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump({"words": vid_words}, f, ensure_ascii=False, indent=2)

print(f"Total words in V3 video: {len(vid_words)}")
for w in vid_words:
    print(f"  {w['word_id']:2d}: {w['word']:<16} [{w['start']:6.3f} -> {w['end']:6.3f}]")
