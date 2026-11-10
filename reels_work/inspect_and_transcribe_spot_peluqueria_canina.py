# -*- coding: utf-8 -*-
r"""
Transcribe con `faster_whisper` (word_timestamps=True) los 3 clips de 1080p generados con
`gemini-omni-1.2-flash` para el Spot de Turnos (Peluquerías Caninas), verificando que ninguna
frase se corte, extrayendo los tiempos palabra por palabra y generando la grilla visual de los 3 clips.
"""
import os
import sys
import json
import subprocess
import pathlib
import shutil
import cv2
import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

BASE_DIR = pathlib.Path(r"c:\IA\Edicion de videos")
SPOT_DIR = BASE_DIR / "assets" / "avatar_veterinario_hombre_vip" / "spot_peluqueria_canina"
WORK_DIR = BASE_DIR / "reels_work"
FFMPEG_EXE = str(BASE_DIR / "bin" / "ffmpeg" / "ffmpeg.exe")
ARTIFACTS_DIR = pathlib.Path(r"C:\Users\Demiante\.gemini\antigravity\brain\56e5cec9-1285-4884-b2c6-a38ac91ed5ae")

CLIPS = [
    ("clip1", SPOT_DIR / "spot_peluqueria_clip1_espalda_a_giro_10s.mp4"),
    ("clip2", SPOT_DIR / "spot_peluqueria_clip2_espalda_agenda_y_sena_10s.mp4"),
    ("clip3", SPOT_DIR / "spot_peluqueria_clip3_frente_groomer_vip_cta_10s.mp4"),
]


def main():
    model = WhisperModel("small", device="cpu", compute_type="int8")
    results = {}

    grid_rows = []
    for tag, mp4_path in CLIPS:
        wav_path = WORK_DIR / f"tmp_pc_{tag}_16k.wav"
        subprocess.run(
            [
                FFMPEG_EXE, "-y",
                "-i", str(mp4_path),
                "-vn", "-ac", "1", "-ar", "16000",
                str(wav_path),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        audio_np, sr = sf.read(str(wav_path), dtype="float32")
        segments, info = model.transcribe(audio_np, language="es", word_timestamps=True, vad_filter=False)
        words = []
        full_text = []
        for seg in segments:
            full_text.append(seg.text.strip())
            if seg.words:
                for w in seg.words:
                    words.append({
                        "word": w.word.strip(),
                        "start": round(float(w.start), 3),
                        "end": round(float(w.end), 3),
                        "prob": round(float(w.probability), 3),
                    })
        cap = cv2.VideoCapture(str(mp4_path))
        fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
        n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        dur = n_frames / fps
        w_px = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h_px = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        thumbs = []
        for t_sec in [0.5, 2.2, 4.0, 6.0, 8.0, 9.4]:
            f_idx = min(n_frames - 1, max(0, int(t_sec * fps)))
            cap.set(cv2.CAP_PROP_POS_FRAMES, f_idx)
            ok, frm = cap.read()
            if ok:
                th = cv2.resize(frm, (270, 480), interpolation=cv2.INTER_AREA)
                cv2.rectangle(th, (0, 0), (270, 38), (15, 23, 42), -1)
                cv2.putText(th, f"{tag} t={t_sec:.1f}s", (10, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (92, 199, 242), 2)
                thumbs.append(th)
        cap.release()
        if thumbs:
            grid_rows.append(np.hstack(thumbs))

        last_word_end = words[-1]["end"] if words else 0.0
        results[tag] = {
            "path": str(mp4_path),
            "width": w_px,
            "height": h_px,
            "fps": round(fps, 3),
            "duration": round(dur, 3),
            "last_word_end": last_word_end,
            "tail_margin_sec": round(dur - last_word_end, 3),
            "text": " ".join(full_text),
            "words": words,
        }
        print(f"\n[{tag}] {w_px}x{h_px} @ {fps:.2f}fps | dur={dur:.2f}s | last_word_end={last_word_end:.2f}s (margin={dur - last_word_end:.2f}s)")
        print(f"  Texto: {results[tag]['text']}")
        for w in words:
            print(f"    {w['start']:5.2f}s - {w['end']:5.2f}s : {w['word']}")

    out_json = WORK_DIR / "spot_peluqueria_canina_clips_transcription.json"
    out_json.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    if grid_rows:
        grid = np.vstack(grid_rows)
        grid_path = WORK_DIR / "spot_peluqueria_canina_raw_clips_grid.jpg"
        cv2.imwrite(str(grid_path), grid, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
        shutil.copy2(grid_path, ARTIFACTS_DIR / grid_path.name)
        print(f"\n[SAVED GRID] {grid_path}")


if __name__ == "__main__":
    main()
