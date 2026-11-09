# -*- coding: utf-8 -*-
import os
import sys
import json
import soundfile as sf
from faster_whisper import WhisperModel

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

BASE_DIR = r"c:\IA\Edicion de videos"
WORK_DIR = os.path.join(BASE_DIR, "reels_work")

model = WhisperModel("large-v3", device="cpu", compute_type="int8")

with open(os.path.join(WORK_DIR, "v4_transcriptions.json"), "r", encoding="utf-8") as f:
    results = json.load(f)

for fname in ["v4A_part1.mp4", "v4A_part2.mp4", "v4B_part1.mp4", "v4B_part2.mp4"]:
    tmp_16k = os.path.join(WORK_DIR, f"tmp_16k_{fname}.wav")
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
    results[fname] = {"duration": round(dur, 4), "words": words}
    print(f"=== {fname} (dur={dur:.2f}s, {len(words)} words) ===")
    print("  " + " ".join(f"{w['word']}[{w['start']:.2f}-{w['end']:.2f}]" for w in words))

with open(os.path.join(WORK_DIR, "v4_transcriptions.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
