# -*- coding: utf-8 -*-
"""
Sincronización labial y gestual palabra por palabra (PCHIP exacto por fonema/palabra, CERO deriva)
para las 6 escenas completas (0.00s -> 33.60s, 96 palabras) de v6A y v6B:
- Sin face_mask ni Frame 0 congelado (100% fotograma completo con movimiento natural de cuerpo, pelo y manos).
- En v6A:
  * Escenas 1 a 4 (0.00s -> 24.00s): v6A_turn2.mp4 [0.00s -> 20.00s] (Frente -> giro 3/4 continuo)
  * Escena 5 (24.00s -> 29.28s): v6A_turn3.mp4 [10.15s -> 16.85s] (Contando las 4 agendas con los dedos y gestos de cobro)
  * Escena 6 CTA (29.28s -> 33.60s): v6A_continuous_full.mp4 [10.15s -> 14.85s] (Hablando y gesticulando el CTA completo "¡Escribinos hoy en MascotaMás y te migramos gratis en el día!")
- En v6B (Veterinaria de Palermo: de la Camilla con el Perro al Mostrador de Entrada):
  * Escenas 1 y 2 (0.00s -> 11.52s): v6B_turn1.mp4 [0.00s -> 10.02s] (36 palabras 1:1 en camilla con el Golden Retriever y caminando por la clínica)
  * Escenas 3, 4 y 5 (11.52s -> 29.28s): v6B_mostrador_t2.mp4 [0.00s -> 16.95s] (49 palabras 1:1 llegando y hablando en el mostrador de entrada con su MacBook Pro)
  * Escena 6 CTA (29.28s -> 33.60s): v6B_mostrador_cta_6s.mp4 [0.00s -> 4.95s] (11 palabras 1:1 en el mostrador de entrada diciendo "¡Escribinos hoy en MascotaMás y te migramos gratis en el día!")
"""
import os
import sys
import json
import copy
import shutil
import subprocess
import cv2
import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import gaussian_filter1d

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

BASE_DIR = r"c:\IA\Edicion de videos"
WORK_DIR = os.path.join(BASE_DIR, "reels_work")
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
sys.path.insert(0, SCRIPTS_DIR)

from step3_plan_cuts import load_style, build_subtitle_blocks, is_highlighted_word
from step4_render_and_export import render_final_video, FFMPEG_BIN


def load_video_frames_1080p(path: str):
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    frames = []
    while True:
        ret, f = cap.read()
        if not ret:
            break
        if f.shape[1] != 1080 or f.shape[0] != 1920:
            f = cv2.resize(f, (1080, 1920), interpolation=cv2.INTER_LANCZOS4)
        frames.append(f)
    cap.release()
    return frames, fps


def sample_subframe(frames: list, src_fps: float, t_sec: float):
    idx_f = float(np.clip(t_sec * src_fps, 0.0, len(frames) - 1.001))
    i0 = int(np.floor(idx_f))
    i1 = min(len(frames) - 1, i0 + 1)
    alpha = idx_f - i0
    if alpha < 1e-3 or i0 == i1:
        return frames[i0]
    return cv2.addWeighted(frames[i0], 1.0 - alpha, frames[i1], alpha, 0.0)


def eval_pchip_segment(t_out_arr: np.ndarray, anchors: list, sigma_frames: float = 2.0) -> np.ndarray:
    """
    Construye una curva PCHIP estrictamente monotónica a partir de pares (t_tts, t_vid)
    exactos palabra por palabra, sin acumular deriva.
    """
    xs = []
    ys = []
    for x, y in anchors:
        x = float(x)
        y = float(y)
        if not xs:
            xs.append(x)
            ys.append(y)
        else:
            if x > xs[-1] + 0.015:
                xs.append(x)
                ys.append(max(ys[-1] + 0.004, y))
    pchip = PchipInterpolator(np.array(xs, dtype=np.float64), np.array(ys, dtype=np.float64))
    raw_y = pchip(t_out_arr)
    if len(raw_y) > 8 and sigma_frames > 0:
        sm_y = gaussian_filter1d(raw_y, sigma=sigma_frames, mode="nearest")
        sm_y[0] = raw_y[0]
        sm_y[-1] = raw_y[-1]
        return np.maximum.accumulate(sm_y)
    return raw_y


def write_master_from_frames(out_frames: list, tts_wav_path: str, out_master_path: str):
    tmp_silent = out_master_path + ".silent.mp4"
    proc = subprocess.Popen(
        [
            FFMPEG_BIN,
            "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", "1080x1920",
            "-pix_fmt", "bgr24",
            "-r", "30",
            "-i", "-",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "16",
            "-pix_fmt", "yuv420p",
            tmp_silent,
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for frm in out_frames:
        proc.stdin.write(frm.tobytes())
    proc.stdin.close()
    proc.wait()

    subprocess.run(
        [
            FFMPEG_BIN,
            "-y",
            "-i", tmp_silent,
            "-i", tts_wav_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            out_master_path,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    if os.path.exists(tmp_silent):
        os.remove(tmp_silent)


def build_v6A_exact_master(tts_wav_path: str, out_master_path: str):
    """
    Construye el master de 1008 fotogramas (33.60s @ 30fps) para v6A con sincronización
    palabra por palabra exacta en las 6 escenas:
    - Segmento 1 (0.00s -> 24.00s, Escenas 1, 2, 3 y 4): v6A_turn2.mp4 (0.00s -> 20.00s)
    - Segmento 2 (24.00s -> 29.28s, Escena 5): v6A_turn3.mp4 (10.15s -> 16.85s, contando las 4 agendas con los dedos)
    - Segmento 3 (29.28s -> 33.60s, Escena 6 CTA): v6A_continuous_full.mp4 (10.15s -> 14.85s, diciendo y gesticulando el CTA completo)
    """
    print("\n[v6A] Cargando clips continuos 1080p (v6A_turn2, v6A_turn3, v6A_continuous_full)...")
    f_t2, fps_t2 = load_video_frames_1080p(os.path.join(WORK_DIR, "v6A_turn2.mp4"))
    f_t3, fps_t3 = load_video_frames_1080p(os.path.join(WORK_DIR, "v6A_turn3.mp4"))
    f_t4, fps_t4 = load_video_frames_1080p(os.path.join(WORK_DIR, "v6A_continuous_full.mp4"))

    fps_out = 30.0
    total_frames = 1008  # 33.60s @ 30fps
    t_all = np.arange(total_frames, dtype=np.float64) / fps_out
    f_cut_s5 = int(round(24.00 * fps_out))  # Frame 720 (24.00s)
    f_cut_s6 = int(round(29.28 * fps_out))  # Frame 878 (29.28s)

    # Anclas exactas palabra por palabra para Escenas 1, 2, 3 y 4 en v6A_turn2.mp4 (0.00s -> 24.00s)
    anchors_s1_s4 = [
        (0.00, 0.72),
        # Escena 1: "¿Seguís atado a un sistema viejo o al Excel por miedo a perder los datos de tu veterinaria?"
        (0.08, 1.00), (0.66, 1.44),   # ¿Seguís
        (0.66, 1.44), (1.08, 1.74),   # atado
        (1.28, 1.86), (1.58, 2.12),   # sistema
        (1.58, 2.12), (2.08, 2.52),   # viejo
        (2.36, 2.76), (2.68, 3.04),   # Excel
        (2.88, 3.18), (3.16, 3.32),   # miedo
        (3.28, 3.38), (3.68, 3.60),   # perder los
        (3.68, 3.60), (4.10, 3.80),   # datos de
        (4.22, 3.82), (4.86, 4.08),   # veterinaria? (boca articulando hasta 4.86s)
        # Pausa entre Escena 1 y Escena 2 (4.86s -> 5.50s -> 4.08s -> 4.50s)
        (5.28, 4.32),
        # Escena 2: "¡Pasate hoy a MascotaMás! Te hacemos toda la migración gratis y en el día, sin frenar tu consultorio."
        (5.50, 4.50), (5.94, 4.90),   # ¡Pasate
        (5.94, 4.90), (6.16, 5.08),   # hoy
        (6.28, 5.16), (6.80, 5.78),   # MascotaMás!
        (7.14, 6.04), (7.42, 6.34),   # Te hacemos
        (7.42, 6.34), (7.76, 6.60),   # toda
        (7.94, 6.74), (8.30, 7.14),   # migración
        (8.30, 7.14), (8.80, 7.66),   # gratis
        (8.96, 7.90), (9.44, 8.22),   # en el día,
        (9.60, 8.44), (10.00, 8.96),  # sin frenar
        (10.12, 9.08), (10.72, 9.72), # consultorio.
        # Pausa entre Escena 2 y Escena 3 (10.72s -> 11.78s -> 9.72s -> 10.28s)
        (11.52, 10.12),
        # Escena 3: "Pasamos tus clientes, pacientes, historias clínicas y vacunas para que no pierdas ni una sola ficha."
        (11.78, 10.28), (12.10, 10.64), # Pasamos
        (12.28, 10.82), (12.96, 11.30), # clientes,
        (13.26, 11.50), (13.74, 11.86), # pacientes,
        (13.92, 12.18), (14.22, 12.54), # historias
        (14.22, 12.54), (14.72, 12.98), # clínicas
        (14.90, 13.24), (15.32, 13.74), # vacunas
        (15.32, 13.74), (15.74, 14.20), # para que no
        (15.74, 14.20), (16.12, 14.52), # pierdas
        (16.12, 14.52), (17.02, 15.02), # ni una sola
        (17.02, 15.02), (17.36, 15.42), # ficha.
        # Pausa entre Escena 3 y Escena 4 (17.36s -> 18.00s -> 15.42s -> 15.92s)
        (17.76, 15.72),
        # Escena 4: "En horas ya tenés recordatorios automáticos por WhatsApp, sala de espera en vivo y todo en la nube."
        (18.00, 15.92), (18.40, 16.22), # En horas
        (18.74, 16.28), (19.20, 16.70), # ya tenés
        (19.20, 16.70), (19.86, 17.30), # recordatorios
        (19.86, 17.30), (20.42, 17.84), # automáticos
        (20.62, 18.02), (20.94, 18.32), # WhatsApp,
        (21.32, 18.64), (21.88, 19.14), # sala de espera
        (21.88, 19.14), (22.20, 19.50), # en vivo
        (22.58, 19.56), (23.40, 19.92), # y todo en la nube.
        (24.00, 20.01),
    ]

    # Anclas exactas palabra por palabra para Escena 5 en v6A_turn3.mp4 (24.00s -> 29.28s)
    # En v6A_turn3.mp4 [10.52s - 16.40s] cuenta con los dedos las 4 agendas inteligentes y explica el cobro con Mercado Pago
    anchors_s5 = [
        (24.00, 10.22),
        (24.24, 10.52), (24.50, 11.00), # Además,
        (24.72, 11.48), (24.94, 11.72), # sumás
        (25.08, 11.86), (25.30, 12.14), # 4 (empieza a contar con los dedos)
        (25.30, 12.14), (25.68, 12.58), # agendas
        (25.68, 12.58), (26.34, 13.40), # inteligentes
        (26.60, 13.80), (26.96, 14.20), # cobro de
        (26.96, 14.20), (27.14, 14.42), # seña
        (27.14, 14.42), (27.62, 14.96), # automático
        (27.82, 15.74), (28.14, 16.10), # Mercado
        (28.14, 16.10), (28.46, 16.40), # Pago*.
        (29.28, 16.85),                 # Cierre suave de frase antes del CTA
    ]

    # Anclas exactas palabra por palabra para Escena 6 (CTA) en v6A_continuous_full.mp4 (29.28s -> 33.60s)
    # En v6A_continuous_full.mp4 [10.42s - 14.08s] dice "¡Escribinos hoy en MascotaMás y te migramos gratis en el día!" abriendo las manos
    anchors_s6 = [
        (29.28, 10.18),
        (29.44, 10.42), (30.20, 10.86), # ¡Escribinos
        (30.20, 10.86), (30.46, 11.08), # hoy
        (30.56, 11.18), (31.24, 11.90), # MascotaMás
        (31.24, 11.90), (31.60, 12.66), # y te
        (31.60, 12.66), (31.98, 13.02), # migramos
        (31.98, 13.02), (32.46, 13.62), # gratis
        (32.46, 13.62), (32.70, 13.88), # en el
        (32.70, 13.88), (32.86, 14.08), # día!
        (33.60, 14.82),                 # Sonrisa cálida en movimiento al terminar la última palabra
    ]

    curve_14 = eval_pchip_segment(t_all[:f_cut_s5], anchors_s1_s4, sigma_frames=2.0)
    curve_5 = eval_pchip_segment(t_all[f_cut_s5:f_cut_s6], anchors_s5, sigma_frames=2.0)
    curve_6 = eval_pchip_segment(t_all[f_cut_s6:], anchors_s6, sigma_frames=2.0)

    out_frames = []
    for idx in range(total_frames):
        if idx < f_cut_s5:
            frm = sample_subframe(f_t2, fps_t2, float(curve_14[idx]))
        elif idx < f_cut_s6:
            frm = sample_subframe(f_t3, fps_t3, float(curve_5[idx - f_cut_s5]))
        else:
            frm = sample_subframe(f_t4, fps_t4, float(curve_6[idx - f_cut_s6]))

        # Crossfade suave de 4 cuadros en las 2 transiciones de segmento (24.00s y 29.28s) para continuidad visual absoluta
        if f_cut_s5 - 2 <= idx < f_cut_s5 + 2:
            w_b = (idx - (f_cut_s5 - 2)) / 4.0
            fa = sample_subframe(f_t2, fps_t2, float(curve_14[min(len(curve_14) - 1, idx)]))
            fb = sample_subframe(f_t3, fps_t3, float(curve_5[max(0, idx - f_cut_s5)]))
            frm = cv2.addWeighted(fa, 1.0 - w_b, fb, w_b, 0.0)
        elif f_cut_s6 - 2 <= idx < f_cut_s6 + 2:
            w_b = (idx - (f_cut_s6 - 2)) / 4.0
            fa = sample_subframe(f_t3, fps_t3, float(curve_5[min(len(curve_5) - 1, idx - f_cut_s5)]))
            fb = sample_subframe(f_t4, fps_t4, float(curve_6[max(0, idx - f_cut_s6)]))
            frm = cv2.addWeighted(fa, 1.0 - w_b, fb, w_b, 0.0)

        out_frames.append(frm)

    write_master_from_frames(out_frames, tts_wav_path, out_master_path)
    print(f"  -> [v6A Master Exacto 96 palabras] {out_master_path}")


def build_v6B_exact_master(tts_wav_path: str, out_master_path: str):
    """
    Construye el master de 1008 fotogramas (33.60s @ 30fps) para v6B (Veterinaria de Palermo)
    con sincronización 1:1 palabra por palabra en las 96 palabras (Escenas 1 a 6):
    - Segmento 1 (0.00s -> 11.52s, Escenas 1 y 2): v6B_turn1.mp4 (0.00s -> 10.00s)
      En la camilla de acero inoxidable con el Golden Retriever arriba y saliendo caminando del consultorio.
    - Segmento 2 (11.52s -> 29.28s, Escenas 3, 4 y 5): v6B_mostrador_t2.mp4 (0.00s -> 16.95s)
      Caminando y hablando en el mostrador de entrada en Palermo junto a su MacBook Pro.
    - Segmento 3 (29.28s -> 33.60s, Escena 6 CTA): v6B_mostrador_cta_6s.mp4 (0.00s -> 4.95s)
      En el mostrador de entrada diciendo y gesticulando "¡Escribinos hoy en MascotaMás y te migramos gratis en el día!".
    """
    print("\n[v6B] Cargando clips 1080p de Palermo (v6B_turn1, v6B_mostrador_t2, v6B_mostrador_cta_6s)...")
    f_b1, fps_b1 = load_video_frames_1080p(os.path.join(WORK_DIR, "v6B_turn1.mp4"))
    f_b2, fps_b2 = load_video_frames_1080p(os.path.join(WORK_DIR, "v6B_mostrador_t2.mp4"))
    f_b3, fps_b3 = load_video_frames_1080p(os.path.join(WORK_DIR, "v6B_mostrador_cta_6s.mp4"))

    fps_out = 30.0
    total_frames = 1008  # 33.60s @ 30fps
    t_all = np.arange(total_frames, dtype=np.float64) / fps_out
    f_cut_s3 = int(round(11.52 * fps_out))  # Frame 346 (11.52s)
    f_cut_s6 = int(round(29.28 * fps_out))  # Frame 878 (29.28s)

    # Anclas 1:1 palabra por palabra para Escenas 1 y 2 en v6B_turn1.mp4 (36 palabras exactas)
    anchors_b12 = [
        (0.00, 0.00),
        # Escena 1 (18 palabras 1:1): "¿Seguís atado a un sistema viejo o al Excel por miedo a perder los datos de tu veterinaria?"
        (0.08, 0.04), (0.66, 0.48),   # ¿Seguís
        (0.66, 0.48), (1.08, 0.82),   # atado
        (1.28, 1.00), (1.58, 1.30),   # sistema
        (1.58, 1.30), (2.08, 1.84),   # viejo
        (2.36, 2.12), (2.68, 2.48),   # Excel
        (2.88, 2.64), (3.16, 2.86),   # miedo
        (3.28, 3.00), (3.50, 3.24),   # perder
        (3.68, 3.40), (3.92, 3.64),   # datos
        (4.22, 3.90), (4.86, 4.56),   # veterinaria?
        # Pausa entre Escena 1 y Escena 2 (4.86s -> 5.50s -> 4.56s -> 4.80s)
        (5.28, 4.70),
        # Escena 2 (18 palabras 1:1): "¡Pasate hoy a MascotaMás! Te hacemos toda la migración gratis y en el día, sin frenar tu consultorio."
        (5.50, 4.80), (5.94, 5.18),   # ¡Pasate
        (5.94, 5.18), (6.16, 5.34),   # hoy
        (6.28, 5.42), (6.80, 6.06),   # MascotaMás!
        (7.14, 6.26), (7.42, 6.60),   # Te hacemos
        (7.42, 6.60), (7.76, 6.86),   # toda
        (7.94, 7.02), (8.30, 7.44),   # migración
        (8.30, 7.44), (8.80, 7.94),   # gratis
        (8.96, 8.02), (9.44, 8.44),   # y en el día,
        (9.60, 8.60), (10.00, 9.12),  # sin frenar
        (10.12, 9.20), (10.72, 9.82), # consultorio.
        (11.52, 10.01),
    ]

    # Anclas 1:1 palabra por palabra para Escenas 3, 4 y 5 en v6B_mostrador_t2.mp4 (49 palabras exactas)
    anchors_b345 = [
        (11.52, 0.00),
        # Escena 3 (16 palabras 1:1): "Pasamos tus clientes, pacientes, historias clínicas y vacunas para que no pierdas ni una sola ficha."
        (11.78, 0.12), (12.10, 0.98), # Pasamos
        (12.28, 1.14), (12.96, 1.62), # clientes,
        (13.26, 1.82), (13.74, 2.10), # pacientes,
        (13.92, 2.36), (14.22, 2.64), # historias
        (14.22, 2.64), (14.72, 3.04), # clínicas
        (14.90, 3.20), (15.32, 3.60), # vacunas
        (15.32, 3.60), (15.74, 3.98), # para que no
        (15.74, 3.98), (16.12, 4.28), # pierdas
        (16.12, 4.28), (17.02, 4.74), # ni una sola
        (17.02, 4.74), (17.36, 5.10), # ficha.
        # Pausa entre Escena 3 y Escena 4 (17.36s -> 18.00s -> 5.10s -> 5.44s)
        (17.76, 5.30),
        # Escena 4 (18 palabras 1:1): "En horas ya tenés recordatorios automáticos por WhatsApp, sala de espera en vivo y todo en la nube."
        (18.00, 5.44), (18.40, 5.74), # En horas
        (18.74, 5.78), (19.20, 6.18), # ya tenés
        (19.20, 6.18), (19.86, 6.72), # recordatorios
        (19.86, 6.72), (20.42, 7.22), # automáticos
        (20.62, 7.42), (20.94, 7.74), # WhatsApp,
        (21.32, 8.10), (21.88, 8.58), # sala de espera
        (21.88, 8.58), (22.20, 8.92), # en vivo
        (22.58, 9.20), (23.16, 9.58), # y todo en la
        (23.16, 9.58), (23.40, 9.80), # nube.
        # Pausa entre Escena 4 y Escena 5 (23.40s -> 24.24s -> 9.80s -> 10.62s)
        (24.00, 10.32),
        # Escena 5 (15 palabras 1:1): "Además, sumás las 4 agendas inteligentes y el cobro de seña automático con Mercado Pago*."
        (24.24, 10.62), (24.50, 11.14), # Además,
        (24.72, 11.52), (24.94, 11.78), # sumás
        (25.08, 11.94), (25.30, 12.20), # 4
        (25.30, 12.20), (25.68, 12.56), # agendas
        (25.68, 12.56), (26.34, 13.34), # inteligentes
        (26.60, 13.80), (26.96, 14.22), # cobro de
        (26.96, 14.22), (27.14, 14.78), # seña
        (27.14, 14.78), (27.62, 15.34), # automático
        (27.82, 15.62), (28.14, 15.92), # Mercado
        (28.14, 15.92), (28.46, 16.30), # Pago*.
        (29.28, 16.95),                 # Cierre suave de Escena 5
    ]

    # Anclas 1:1 palabra por palabra para Escena 6 (CTA) en v6B_mostrador_cta_6s.mp4 (11 palabras exactas)
    anchors_b6 = [
        (29.28, 0.00),
        (29.44, 0.12), (30.20, 1.14), # ¡Escribinos
        (30.20, 1.14), (30.46, 1.48), # hoy
        (30.46, 1.48), (30.56, 1.58), # en
        (30.56, 1.58), (31.24, 2.28), # MascotaMás
        (31.24, 2.28), (31.48, 2.52), # y
        (31.48, 2.52), (31.60, 2.66), # te
        (31.60, 2.66), (31.98, 3.04), # migramos
        (31.98, 3.04), (32.46, 3.66), # gratis
        (32.46, 3.66), (32.58, 3.80), # en
        (32.58, 3.80), (32.70, 3.94), # el
        (32.70, 3.94), (32.86, 4.14), # día!
        (33.60, 4.92),                # Sonrisa cálida en movimiento en el mostrador de entrada
    ]

    curve_b12 = eval_pchip_segment(t_all[:f_cut_s3], anchors_b12, sigma_frames=2.0)
    curve_b345 = eval_pchip_segment(t_all[f_cut_s3:f_cut_s6], anchors_b345, sigma_frames=2.0)
    curve_b6 = eval_pchip_segment(t_all[f_cut_s6:], anchors_b6, sigma_frames=2.0)

    out_frames = []
    for idx in range(total_frames):
        if idx < f_cut_s3:
            frm = sample_subframe(f_b1, fps_b1, float(curve_b12[idx]))
        elif idx < f_cut_s6:
            frm = sample_subframe(f_b2, fps_b2, float(curve_b345[idx - f_cut_s3]))
        else:
            frm = sample_subframe(f_b3, fps_b3, float(curve_b6[idx - f_cut_s6]))

        # Crossfade suave de 4 cuadros justo en las transiciones (11.52s y 29.28s)
        if f_cut_s3 - 2 <= idx < f_cut_s3 + 2:
            w_b = (idx - (f_cut_s3 - 2)) / 4.0
            fa = sample_subframe(f_b1, fps_b1, float(curve_b12[min(len(curve_b12) - 1, idx)]))
            fb = sample_subframe(f_b2, fps_b2, float(curve_b345[max(0, idx - f_cut_s3)]))
            frm = cv2.addWeighted(fa, 1.0 - w_b, fb, w_b, 0.0)
        elif f_cut_s6 - 2 <= idx < f_cut_s6 + 2:
            w_b = (idx - (f_cut_s6 - 2)) / 4.0
            fa = sample_subframe(f_b2, fps_b2, float(curve_b345[min(len(curve_b345) - 1, idx - f_cut_s3)]))
            fb = sample_subframe(f_b3, fps_b3, float(curve_b6[max(0, idx - f_cut_s6)]))
            frm = cv2.addWeighted(fa, 1.0 - w_b, fb, w_b, 0.0)

        out_frames.append(frm)

    write_master_from_frames(out_frames, tts_wav_path, out_master_path)
    print(f"  -> [v6B Master Exacto 96 palabras] {out_master_path}")


def render_reel_version(
    version_tag: str,
    master_mp4_path: str,
    tts_wav_path: str,
    wdata: dict,
    out_edited_mp4: str,
    out_bruto_mp4: str,
    out_grid_jpg: str,
    scene6_full_face: bool = False,
    face_center_y: float = 0.22,
):
    shutil.copy2(master_mp4_path, os.path.join(WORK_DIR, "source_input.mp4"))
    shutil.copy2(tts_wav_path, os.path.join(WORK_DIR, "source_audio.wav"))
    shutil.copy2(master_mp4_path, out_bruto_mp4)

    raw_words = copy.deepcopy(wdata["words"])
    transitions = wdata["transitions"]
    total_dur = float(wdata["duration"])

    legal_tyc = "* Aplican posibles comisiones de Mercado Pago según las condiciones y plazos de acreditación de tu cuenta."
    hook_title = {
        "line1": "MIGRACIÓN GRATIS",
        "line2": "EN EL DÍA 🚀",
        "keyword": "GRATIS",
        "emoji": "🚀",
    }
    cta_title = {
        "line1": "Te migramos gratis en",
        "line2": "MASCOTAMÁS 🐾",
        "keyword": "MASCOTAMÁS",
        "emoji": "🐾",
    }

    scene_texts = [
        "¿Seguís atado a un sistema viejo o al Excel por miedo a perder los datos de tu veterinaria?",
        "¡Pasate hoy a MascotaMás! Te hacemos toda la migración gratis y en el día, sin frenar tu consultorio.",
        "Pasamos tus clientes, pacientes, historias clínicas y vacunas para que no pierdas ni una sola ficha.",
        "En horas ya tenés recordatorios automáticos por WhatsApp, sala de espera en vivo y todo en la nube.",
        "Además, sumás las 4 agendas inteligentes y el cobro de seña automático con Mercado Pago*.",
        "¡Escribinos hoy en MascotaMás y te migramos gratis en el día!",
    ]

    scenes_def = [
        {
            "scene_id": 1,
            "sentence_id": 1,
            "word_ids": [w["word_id"] for w in raw_words if w["scene_id"] == 1],
            "text": scene_texts[0],
            "layout_mode": "full_face",
            "is_hook": True,
            "is_cta": False,
            "top_title": hook_title,
            "edited_start": transitions[0],
            "edited_end": transitions[1],
            "edited_duration": round(transitions[1] - transitions[0], 4),
            "graphic_config": {
                "template": "none",
                "device_mode": "none",
                "pill": "MASCOTAMÁS · MIGRACIÓN GRATIS",
                "headline_kicker": "✨ PASATE SIN MIEDO · GESTIÓN INTEGRAL PET",
                "headline_main": "🚀 MIGRACIÓN 100% GRATIS Y EN EL DÍA",
                "mascot_expression": "surprised",
            },
        },
        {
            "scene_id": 2,
            "sentence_id": 2,
            "word_ids": [w["word_id"] for w in raw_words if w["scene_id"] == 2],
            "text": scene_texts[1],
            "layout_mode": "split_graphic",
            "is_hook": False,
            "is_cta": False,
            "top_title": None,
            "edited_start": transitions[1],
            "edited_end": transitions[2],
            "edited_duration": round(transitions[2] - transitions[1], 4),
            "graphic_config": {
                "template": "before_after",
                "device_mode": "combo",
                "real_photo_mockups": True,
                "pill": "MIGRACIÓN EN EL DÍA · $0",
                "headline_kicker": "⚡ SIN FRENAR TU CONSULTORIO · MACBOOK PRO & IPHONE",
                "headline_main": "🐾 TE MIGRAMOS GRATIS Y EN EL DÍA",
                "laptop_screenshot": "../assets/mascotamas_real_mockups/mac_dashboard_tutores_pacientes.png",
                "phone_screenshot": "../assets/mascotamas_real_mockups/iphone_dashboard_tutores_pacientes.png",
                "before_label": "SISTEMA VIEJO / EXCEL",
                "before_value": "Miedo a Perder Datos",
                "before_desc": "Planillas sueltas y tiempo perdido",
                "after_label": "CON MASCOTAMÁS",
                "after_value": "Migración en el Día",
                "after_desc": "100% Gratis y sin frenar tu clínica",
                "mascot_expression": "happy",
            },
        },
        {
            "scene_id": 3,
            "sentence_id": 3,
            "word_ids": [w["word_id"] for w in raw_words if w["scene_id"] == 3],
            "text": scene_texts[2],
            "layout_mode": "split_graphic",
            "is_hook": False,
            "is_cta": False,
            "top_title": None,
            "edited_start": transitions[2],
            "edited_end": transitions[3],
            "edited_duration": round(transitions[3] - transitions[2], 4),
            "graphic_config": {
                "template": "checklist",
                "device_mode": "combo_left_phone",
                "real_photo_mockups": True,
                "pill": "HISTORIAS CLÍNICAS Y VACUNAS",
                "headline_kicker": "📋 CERO PÉRDIDA DE INFORMACIÓN · LEGAJO DIGITAL",
                "headline_main": "🩺 CLIENTES, PACIENTES, HISTORIAS Y VACUNAS",
                "laptop_screenshot": "../assets/mascotamas_real_mockups/mac_historias_clinicas_legajo_pdf.png",
                "phone_screenshot": "../assets/mascotamas_real_mockups/iphone_evolucion_y_vacunas.png",
                "items": [
                    {"text": "Clientes y Pacientes", "tag": "100% MIGRADO"},
                    {"text": "Historias Clínicas PDF", "tag": "SIN PERDER FICHAS"},
                    {"text": "Historial de Vacunas", "tag": "COMPLETO"},
                ],
                "mascot_expression": "happy",
            },
        },
        {
            "scene_id": 4,
            "sentence_id": 4,
            "word_ids": [w["word_id"] for w in raw_words if w["scene_id"] == 4],
            "text": scene_texts[3],
            "layout_mode": "split_graphic",
            "is_hook": False,
            "is_cta": False,
            "top_title": None,
            "edited_start": transitions[3],
            "edited_end": transitions[4],
            "edited_duration": round(transitions[4] - transitions[3], 4),
            "graphic_config": {
                "template": "app_connection",
                "device_mode": "combo",
                "real_photo_mockups": True,
                "pill": "WHATSAPP + SALA DE ESPERA",
                "headline_kicker": "💬 AUTOMATIZACIÓN EN HORAS · WEB & APP",
                "headline_main": "📲 RECORDATORIOS WHATSAPP Y SALA EN VIVO",
                "laptop_screenshot": "../assets/mascotamas_real_mockups/mac_directorio_tutores_whatsapp.png",
                "phone_screenshot": "../assets/mascotamas_real_mockups/real_iphone_05_sala_espera.png",
                "icon_a": "🏥",
                "app_a": "Sala en Vivo",
                "sub_a": "Fichas en la Nube 24/7",
                "status": "✓ EN EL DÍA",
                "app_b": "WhatsApp",
                "sub_b": "Recordatorios Automáticos",
                "mascot_expression": "surprised",
            },
        },
        {
            "scene_id": 5,
            "sentence_id": 5,
            "word_ids": [w["word_id"] for w in raw_words if w["scene_id"] == 5],
            "text": scene_texts[4],
            "layout_mode": "split_graphic",
            "is_hook": False,
            "is_cta": False,
            "top_title": None,
            "edited_start": transitions[4],
            "edited_end": transitions[5],
            "edited_duration": round(transitions[5] - transitions[4], 4),
            "graphic_config": {
                "template": "checklist",
                "device_mode": "combo_left_phone",
                "real_photo_mockups": True,
                "pill": "4 AGENDAS + MERCADO PAGO*",
                "headline_kicker": "💳 4 CALENDARIOS + COBRO AUTOMATIZADO ONLINE*",
                "headline_main": "⚡ 4 AGENDAS Y SEÑA CON MERCADO PAGO*",
                "laptop_screenshot": "../assets/mascotamas_real_mockups/real_macbook_cobro_sena_mp.png",
                "phone_screenshot": "../assets/mascotamas_real_mockups/iphone_4_tipos_agenda.png",
                "items": [
                    {"text": "4 Agendas Inteligentes", "tag": "SIN HUECOS"},
                    {"text": "Seña Mercado Pago*", "tag": "TURNOS SEGUROS"},
                    {"text": "Cero Inasistencias", "tag": "24/7 ONLINE"},
                ],
                "legal_disclaimer": legal_tyc,
                "mascot_expression": "happy",
            },
        },
        {
            "scene_id": 6,
            "sentence_id": 6,
            "word_ids": [w["word_id"] for w in raw_words if w["scene_id"] == 6],
            "text": scene_texts[5],
            "layout_mode": "full_face" if scene6_full_face else "split_graphic",
            "is_hook": False,
            "is_cta": True,
            "top_title": cta_title if scene6_full_face else None,
            "edited_start": transitions[5],
            "edited_end": transitions[6],
            "edited_duration": round(transitions[6] - transitions[5], 4),
            "graphic_config": {
                "template": "none" if scene6_full_face else "chat_input",
                "device_mode": "none",
                "pill": "MASCOTAMAS.COM · MIGRÁ HOY",
                "headline_kicker": "🐾 CAMBIATE HOY SIN FRENAR TU VETERINARIA",
                "headline_main": "💻 ESCRIBINOS HOY EN MASCOTAMAS.COM",
                "prompt_text": "MIGRACIÓN 100% GRATIS Y EN EL DÍA",
                "reply_text": "Entrá en mascotamas.com o comentá MIGRAR",
                "badge": "MASCOTAMAS.COM · MIGRACIÓN GRATIS",
                "legal_disclaimer": legal_tyc,
                "mascot_expression": "happy",
            },
        },
    ]

    style = load_style()
    cta_kw = "MIGRAR"
    cooldown_min = 4.0
    last_bounce_time = -999.0

    words_cleaned = []
    edited_words = []
    hl_terms = [
        "excel", "miedo", "veterinaria", "mascotamás", "migración", "gratis", "día",
        "clientes", "pacientes", "historias", "clínicas", "vacunas", "ficha",
        "recordatorios", "automáticos", "whatsapp", "vivo", "nube",
        "4", "agendas", "inteligentes", "seña", "mercado", "pago", "migramos",
    ]
    for i, w in enumerate(raw_words):
        wid = w["word_id"]
        sub_txt = w["subtitle_text"]
        wc = {
            "word_id": wid,
            "word": w["word"],
            "subtitle_text": sub_txt,
            "start": w["start"],
            "real_start": w["start"],
            "end": w["end"],
            "edited_start": w["start"],
            "edited_end": w["end"],
            "rms_db": -16.0,
            "keep": True,
            "delete_reason": "",
            "scene_id": w["scene_id"],
            "face_center": [0.5, face_center_y],
        }
        nxt_str = raw_words[i + 1]["word"] if i + 1 < len(raw_words) else ""
        is_yel, can_bounce = is_highlighted_word(sub_txt, nxt_str, style, cta_kw)
        clean_low = sub_txt.lower().strip("¿?¡!.,*:")
        if clean_low in hl_terms:
            is_yel = True
            can_bounce = True
        wc["is_yellow"] = is_yel
        if is_yel and can_bounce and (wc["edited_start"] - last_bounce_time >= cooldown_min):
            wc["trigger_bounce"] = True
            last_bounce_time = wc["edited_start"]
        else:
            wc["trigger_bounce"] = False
        words_cleaned.append(wc)
        edited_words.append(wc)

    subtitle_blocks = build_subtitle_blocks(edited_words, style)

    guion_json = {
        "total_original_words": len(words_cleaned),
        "kept_word_ids": [w["word_id"] for w in words_cleaned],
        "deleted_word_ids": [],
        "deleted_details": [],
        "cta_keyword": cta_kw,
        "hook_title": hook_title,
        "cta_title": cta_title,
        "words_cleaned": words_cleaned,
        "scenes": scenes_def,
    }
    with open(os.path.join(WORK_DIR, "guion_corregido.json"), "w", encoding="utf-8") as f:
        json.dump(guion_json, f, ensure_ascii=False, indent=2)

    segments = [{
        "segment_id": 1,
        "source_start": 0.0,
        "source_end": total_dur,
        "duration": total_dur,
        "edited_start": 0.0,
        "edited_end": total_dur,
        "avg_rms_db": -16.0,
        "face_center": [0.5, face_center_y],
        "word_ids": [w["word_id"] for w in words_cleaned],
    }]

    sfx_events = []
    for tr_t in transitions[1:-1]:
        sfx_events.append({
            "type": "whoosh",
            "time": round(max(0.0, tr_t - 0.04), 4),
            "reason": f"Beat-synced transition @ {tr_t:.2f}s (125 BPM Lyria 3 House)",
        })
    sfx_events.append({
        "type": "ding",
        "time": round(transitions[5] - 0.02, 4),
        "reason": "CTA final",
    })

    mg_dur = sum(sc["edited_duration"] for sc in scenes_def if sc["layout_mode"] == "split_graphic")
    mg_ratio = round(mg_dur / total_dur, 4)

    edit_plan = {
        "source_video": os.path.join(WORK_DIR, "source_input.mp4"),
        "source_audio": os.path.join(WORK_DIR, "source_audio.wav"),
        "skip_denoise": True,
        "bgm_override_path": os.path.join(WORK_DIR, "v6_lyria_synced.wav"),
        "bgm_relative_db": -13.5,
        "bgm_ducking_db": -6.5,
        "original_duration_sec": total_dur,
        "edited_duration_sec": total_dur,
        "motion_graphics_coverage_ratio": mg_ratio,
        "cta_keyword": cta_kw,
        "hook_title": hook_title,
        "cta_title": cta_title,
        "face_metadata": {
            "default_face_center": [0.5, face_center_y],
            "has_face": True,
        },
        "segments": segments,
        "words": edited_words,
        "edited_words": edited_words,
        "subtitle_blocks": subtitle_blocks,
        "scenes": scenes_def,
        "sfx_events": sfx_events,
    }

    with open(os.path.join(WORK_DIR, "edit_plan.json"), "w", encoding="utf-8") as f:
        json.dump(edit_plan, f, ensure_ascii=False, indent=2)
    with open(os.path.join(WORK_DIR, f"edit_plan_{version_tag}.json"), "w", encoding="utf-8") as f:
        json.dump(edit_plan, f, ensure_ascii=False, indent=2)

    print(f"\n[{version_tag} PLAN READY] Dur={total_dur:.2f}s, MG={mg_ratio*100:.1f}%, Blocks={len(subtitle_blocks)}")
    render_final_video(out_edited_mp4)
    subprocess.run([sys.executable, os.path.join(SCRIPTS_DIR, "step5_verify.py"), out_edited_mp4], check=True)
    shutil.copy2(os.path.join(BASE_DIR, "verification_grid.jpg"), out_grid_jpg)
    print(f"  -> [{version_tag} COMPLETADO] {out_edited_mp4}")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    tts_wav_path = os.path.join(WORK_DIR, "v6_tts_synced.wav")
    with open(os.path.join(WORK_DIR, "v6_words_synced.json"), "r", encoding="utf-8") as f:
        wdata = json.load(f)

    if mode in ("all", "v6A"):
        v6a_master = os.path.join(WORK_DIR, "v6A_vet_lipsync_master.mp4")
        build_v6A_exact_master(tts_wav_path, v6a_master)
        out_v6a_edit = os.path.join(
            BASE_DIR, "editados",
            "Reel Publicitario - Migracion Gratis en el Dia a MascotaMas (v6A - Avatar 360 Movimiento Continuo Natural + Maquetas Reales MacBook y iPhone + Lyria 3).mp4",
        )
        out_v6a_bruto = os.path.join(
            BASE_DIR, "brutos",
            "Reel Publicitario - Migracion Gratis en el Dia a MascotaMas (v6A - Bruto Avatar 360 Movimiento Continuo Natural LipSync).mp4",
        )
        out_v6a_grid = os.path.join(WORK_DIR, "verification_grid_v6A.jpg")
        render_reel_version(
            "v6A",
            v6a_master,
            tts_wav_path,
            wdata,
            out_v6a_edit,
            out_v6a_bruto,
            out_v6a_grid,
            scene6_full_face=False,
            face_center_y=0.22,
        )

    if mode in ("all", "v6B"):
        v6b_master = os.path.join(WORK_DIR, "v6B_vet_lipsync_master.mp4")
        build_v6B_exact_master(tts_wav_path, v6b_master)
        out_v6b_edit = os.path.join(
            BASE_DIR, "editados",
            "Reel Publicitario - Migracion Gratis en el Dia a MascotaMas (v6B - Recorrido Veterinaria Palermo Camilla con Perro a Mostrador + Maquetas Reales + Lyria 3).mp4",
        )
        out_v6b_bruto = os.path.join(
            BASE_DIR, "brutos",
            "Reel Publicitario - Migracion Gratis en el Dia a MascotaMas (v6B - Bruto Recorrido Veterinaria Palermo Camilla con Perro a Mostrador LipSync).mp4",
        )
        out_v6b_grid = os.path.join(WORK_DIR, "verification_grid_v6B.jpg")
        render_reel_version(
            "v6B",
            v6b_master,
            tts_wav_path,
            wdata,
            out_v6b_edit,
            out_v6b_bruto,
            out_v6b_grid,
            scene6_full_face=True,
            face_center_y=0.25,
        )


if __name__ == "__main__":
    main()
