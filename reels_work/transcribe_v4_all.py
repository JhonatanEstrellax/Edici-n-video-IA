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

items = [
    ("tts_v4A_raw.wav", "Mirá lo nuevo de MascotaMás para tu veterinaria, peluquería o guardería. Ahora tenés cuatro tipos de calendario: Turnos Simples uno a uno, y Cupos por Horario. También agendas por Servicios y Profesionales, con grilla automática sin huecos, y Calendario de Guardería por rango de fechas, con sectores de ingreso y egreso. Además, activás el cobro de seña automático con Mercado Pago para asegurar cada turno. ¡Entrá hoy en MascotaMás y probalo!"),
    ("tts_v4B_raw.wav", "¿Perdés turnos por WhatsApp en tu veterinaria, peluquería o guardería? ¡Mirá lo nuevo de MascotaMás! Elegí entre cuatro agendas inteligentes: Turnos Simples uno a uno, o Cupos por Horario. Agenda por Servicios y Profesionales, que calcula duraciones sola y elimina los huecos, y Calendario de Guardería por fechas, controlando sectores, ingreso y egreso. ¿Lo mejor? Cobrás seña automática con Mercado Pago y te olvidás de los faltazos. ¡Entrá hoy en mascotamas punto com y probalo!"),
    ("v4A_part1.mp4", "Mirá lo nuevo de MascotaMás para tu veterinaria, peluquería o guardería. Ahora tenés cuatro tipos de calendario: Turnos Simples uno a uno, y Cupos por Horario. También agendas por Servicios y Profesionales, con grilla automática sin huecos."),
    ("v4A_part2.mp4", "Y Calendario de Guardería por rango de fechas, con sectores de ingreso y egreso. Además, activás el cobro de seña automático con Mercado Pago para asegurar cada turno. ¡Entrá hoy en MascotaMás y probalo!"),
    ("v4B_part1.mp4", "¿Perdés turnos por WhatsApp en tu veterinaria, peluquería o guardería? ¡Mirá lo nuevo de MascotaMás! Elegí entre cuatro agendas inteligentes: Turnos Simples uno a uno, o Cupos por Horario. Agenda por Servicios y Profesionales, que calcula duraciones sola y elimina los huecos."),
    ("v4B_part2.mp4", "Y Calendario de Guardería por fechas, controlando sectores, ingreso y egreso. ¿Lo mejor? Cobrás seña automática con Mercado Pago y te olvidás de los faltazos. ¡Entrá hoy en MascotaMás y probalo!"),
]

results = {}
for fname, prompt in items:
    in_path = os.path.join(WORK_DIR, fname)
    tmp_16k = os.path.join(WORK_DIR, f"tmp_16k_{fname}.wav")
    subprocess.run([
        FFMPEG_BIN, "-y", "-i", in_path, "-vn", "-ac", "1", "-ar", "16000", tmp_16k
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    audio, sr = sf.read(tmp_16k, dtype="float32")
    dur = len(audio) / float(sr)
    segs, _ = model.transcribe(audio, language="es", word_timestamps=True, vad_filter=False, initial_prompt=prompt)
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
