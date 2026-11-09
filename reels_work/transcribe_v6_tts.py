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

model = WhisperModel("small", device="cpu", compute_type="int8")

files = (
    ["tts_v6_full_raw.wav"]
    + [f"tts_v6_s{i}.wav" for i in range(1, 7)]
    + ["v6_clip1_frente.mp4", "v6_clip2_tres_cuartos.mp4", "v6_clip3_frente_cta.mp4"]
)
out = {}

for fname in files:
    in_path = os.path.join(WORK_DIR, fname)
    tmp_16k = os.path.join(WORK_DIR, f"tmp_16k_{fname}.wav")
    subprocess.run([
        FFMPEG_BIN, "-y", "-i", in_path, "-vn", "-ac", "1", "-ar", "16000", tmp_16k
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    audio, sr = sf.read(tmp_16k, dtype="float32")
    dur = len(audio) / float(sr)
    segs, _ = model.transcribe(audio, language="es", word_timestamps=True, vad_filter=False)
    words = []
    for s in segs:
        for w in (s.words or []):
            tok = w.word.strip()
            if not tok:
                continue
            words.append({
                "word_id": len(words) + 1,
                "word": tok,
                "start": round(float(w.start), 4),
                "end": round(float(w.end), 4),
            })
    out[fname] = {"duration": round(dur, 4), "words": words}
    print(f"=== {fname} (dur={dur:.2f}s, {len(words)} words) ===")
    print("  " + " ".join(f"{w['word']}[{w['start']:.2f}-{w['end']:.2f}]" for w in words))

with open(os.path.join(WORK_DIR, "v6_all_transcriptions.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
