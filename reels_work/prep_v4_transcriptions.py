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

model = WhisperModel("large-v3", device="cpu", compute_type="int8")

with open(os.path.join(WORK_DIR, "v4_transcriptions.json"), "r", encoding="utf-8") as f:
    trans = json.load(f)

for fname in ["tts_v4A_raw.wav", "tts_v4B_raw.wav"]:
    in_wav = os.path.join(WORK_DIR, fname)
    tmp_16k = os.path.join(WORK_DIR, f"tmp_16k_{fname}.wav")
    subprocess.run([FFMPEG_BIN, "-y", "-i", in_wav, "-vn", "-ac", "1", "-ar", "16000", tmp_16k], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    audio, sr = sf.read(tmp_16k, dtype="float32")
    segs, _ = model.transcribe(audio, language="es", word_timestamps=True, vad_filter=False)
    words = []
    for s in segs:
        for w in (s.words or []):
            tok = w.word.strip()
            if tok:
                words.append({"word_id": len(words) + 1, "word": tok, "start": round(float(w.start), 4), "end": round(float(w.end), 4)})
    trans[fname] = {"duration": round(len(audio) / float(sr), 4), "words": words}
    print(f"=== {fname} (dur={len(audio)/float(sr):.2f}s, {len(words)} words) ===")
    print("  " + " ".join(f"{w['word_id']}:{w['word']}[{w['start']:.2f}-{w['end']:.2f}]" for w in words))

with open(os.path.join(WORK_DIR, "v4_transcriptions.json"), "w", encoding="utf-8") as f:
    json.dump(trans, f, ensure_ascii=False, indent=2)
