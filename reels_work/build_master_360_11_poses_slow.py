# -*- coding: utf-8 -*-
r"""
Ensambla el Master Definitivo en 1080p (1080x1920 @ 30fps, 37.5s) del Avatar Veterinaria 360° + 11 Poses
con Movimiento Lento, Pausado y 100% Natural generado con Gemini Omni 1.2 Flash (gemini-omni-1.2-flash),
garantizando que NO se omita ninguna de las 11 poses y que cada transición sea lenta y natural:

- 00.0s - 15.0s: Giro 360° Completo Continuo pasando por:
    * Pose 1 (0° De Frente - avatar_360_1_frente.png)
    * Pose 2 (-45° 3/4 Izquierda - avatar_360_2_tres_cuartos_izq.png)
    * Pose 3 (-90° Lateral Izquierdo - avatar_360_3_lateral_izq.png)
    * Pose 4 (180° De Espalda - avatar_360_6_espalda.png)
    * Pose 5 (+90° Lateral Derecho - avatar_360_5_lateral_der.png)
    * Pose 6 (+45° 3/4 Derecha - avatar_360_4_tres_cuartos_der.png)
- 15.0s - 19.8s: Transición lenta hacia y mantenimiento de:
    * Pose 7 (De Espalda en Puntitas de Pie - avatar_360_7_espalda_puntitas.png)
- 19.8s - 24.6s: Transición lenta hacia y mantenimiento de:
    * Pose 8 (De Espalda Agachada mirando sobre el hombro - avatar_360_8_espalda_agachada.png)
- 24.6s - 27.0s: Transición lenta hacia y mantenimiento de:
    * Pose 9 (De Frente Agachada con manos en rodillas - avatar_360_9_frente_agachada.png)
- 27.0s - 30.2s: Transición lenta hacia y mantenimiento de:
    * Pose 10 (En Cuclillas de Frente mirando a cámara - avatar_360_10_cuclillas_frente.png)
- 30.2s - 37.5s: Incorporación suave, giro lento de espalda y descenso fluido hacia:
    * Pose 11 (En Cuclillas de Espalda mirando sobre el hombro - avatar_360_11_cuclillas_espalda.png)
"""
import os
import shutil
import pathlib
import subprocess
import cv2
import numpy as np

BASE_DIR = pathlib.Path(r"c:\IA\Edicion de videos")
FFMPEG_EXE = str(BASE_DIR / "bin" / "ffmpeg" / "ffmpeg.exe")
WORK_DIR = BASE_DIR / "reels_work"
AVATAR_DIR = BASE_DIR / "assets" / "avatar_veterinaria_360"
EDITADOS_DIR = BASE_DIR / "editados"
ARTIFACTS_DIR = pathlib.Path(r"C:\Users\Demiante\.gemini\antigravity\brain\56e5cec9-1285-4884-b2c6-a38ac91ed5ae")

VID_CHAIN24 = WORK_DIR / "omni_chain30_turn2_poses7_8_9_24s.mp4"
VID_ALT30 = WORK_DIR / "omni_alt_25s_to_30s_pose8_and_11.mp4"
AUDIO_HOUSE = WORK_DIR / "v7_lyria_house_arriba.wav"


def read_all_frames(vid_path):
    cap = cv2.VideoCapture(str(vid_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(f)
    cap.release()
    return frames, fps


def resample_frames_smooth(frames, target_count):
    """Interpola suavemente una secuencia de frames para lograr movimiento lento y fluido."""
    n = len(frames)
    if n == target_count:
        return frames
    out = []
    for i in range(target_count):
        pos = (i / max(1, target_count - 1)) * (n - 1)
        idx0 = int(np.floor(pos))
        idx1 = min(n - 1, idx0 + 1)
        alpha = pos - idx0
        if alpha < 1e-4 or idx0 == idx1:
            out.append(frames[idx0])
        else:
            blended = cv2.addWeighted(frames[idx0], 1.0 - alpha, frames[idx1], alpha, 0.0)
            out.append(blended)
    return out


def main():
    print("1. Leyendo frames de los renders 1080p de Gemini Omni 1.2 Flash...")
    frames_A, fps_A = read_all_frames(VID_CHAIN24)  # 576 frames @ 24fps (24.0s)
    frames_B, fps_B = read_all_frames(VID_ALT30)    # 720 frames @ 24fps (30.0s)
    print(f"   Chain24: {len(frames_A)} frames | Alt30: {len(frames_B)} frames")

    # Empalme exacto donde MAE = 5.72:
    # - frames_A[0 : 540] (0.0s a 22.5s: Giro 360 Poses 1..6 [0-15s] + Pose 7 Puntitas [15-18.7s] + Pose 8 Espalda Agachada [18.7-22.5s])
    # - Transición suave de 8 frames alrededor de A[536:544] <-> B[477:485]
    # - frames_B[481 : 720] (20.04s a 30.0s: Pose 9 Frente Agachada + Pose 10 Cuclillas Frente + Giro Espalda + Pose 11 Cuclillas Espalda)
    part_360 = frames_A[0:360]  # 0.0s - 15.0s (360 frames @ 24fps)

    # Construimos la secuencia completa de Poses 7 -> 8 -> 9 -> 10 -> 11 con empalme invisible de 8 frames
    blend_len = 8
    poses_7_to_8 = frames_A[360 : 540 - blend_len]
    blend_frames = []
    for k in range(blend_len):
        alpha = (k + 1) / (blend_len + 1)
        fA = frames_A[540 - blend_len + k]
        fB = frames_B[481 - blend_len + k]
        blend_frames.append(cv2.addWeighted(fA, 1.0 - alpha, fB, alpha, 0.0))
    poses_9_to_11 = frames_B[481:]

    raw_poses_7_to_11 = poses_7_to_8 + blend_frames + poses_9_to_11
    print(f"   Frames brutos Poses 7..11: {len(raw_poses_7_to_11)} frames (@24fps = {len(raw_poses_7_to_11)/24.0:.2f}s)")

    # Exportamos a 30fps con transición lenta y pausada:
    # - Parte 1 (Giro 360° Poses 1..6): 16.5s @ 30fps = 495 frames (giro aún más lento y elegante)
    # - Parte 2 (Poses 7, 8, 9, 10, 11): 22.5s @ 30fps = 675 frames (4.5s promedio por cada pose, lento y natural)
    # Total: 39.0s @ 30fps (1170 frames)
    out_fps = 30
    slow_360 = resample_frames_smooth(part_360, int(16.5 * out_fps))
    slow_7_to_11 = resample_frames_smooth(raw_poses_7_to_11, int(22.5 * out_fps))
    master_frames = slow_360 + slow_7_to_11
    total_dur = len(master_frames) / out_fps
    print(f"   Master lento y natural ensamblado: {len(master_frames)} frames @ {out_fps}fps ({total_dur:.2f}s)")

    temp_raw_mp4 = WORK_DIR / "temp_master_360_11_poses_slow_noaudio.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    vw = cv2.VideoWriter(str(temp_raw_mp4), fourcc, out_fps, (1080, 1920))
    for f in master_frames:
        vw.write(f)
    vw.release()

    # Masterizar con FFmpeg H.264 High Profile + Audio House Sincronizado (o el audio original de Omni si no está el wav)
    out_master_avatar = AVATAR_DIR / "Avatar_Veterinaria_360_y_11_Poses_Movimiento_Natural_IA_Omni_1080p.mp4"
    if AUDIO_HOUSE.exists():
        cmd = [
            FFMPEG_EXE, "-y",
            "-i", str(temp_raw_mp4),
            "-stream_loop", "-1", "-i", str(AUDIO_HOUSE),
            "-t", f"{total_dur:.2f}",
            "-filter_complex", f"[1:a]volume=0.35,afade=t=in:st=0:d=1.0,afade=t=out:st={total_dur-2.0:.2f}:d=2.0[aout]",
            "-map", "0:v:0", "-map", "[aout]",
            "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            str(out_master_avatar),
        ]
    else:
        cmd = [
            FFMPEG_EXE, "-y",
            "-i", str(temp_raw_mp4),
            "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(out_master_avatar),
        ]
    subprocess.run(cmd, check=True)
    if temp_raw_mp4.exists():
        temp_raw_mp4.unlink()

    # Copiar también el render directo de 30s de Omni y el Master de 39s a las carpetas solicitadas
    out_direct_30s = AVATAR_DIR / "Avatar_Veterinaria_360_y_11_Poses_Completo_IA_Omni_30s_1080p.mp4"
    shutil.copy2(VID_ALT30, out_direct_30s)

    # Copiar a editados/, raíz del proyecto y artifacts
    for dst in [
        EDITADOS_DIR / "Avatar_Veterinaria_360_y_11_Poses_Movimiento_Natural_IA_Omni_1080p.mp4",
        BASE_DIR / "Avatar_Veterinaria_360_y_11_Poses_Movimiento_Natural_IA_Omni_1080p.mp4",
        ARTIFACTS_DIR / "Avatar_Veterinaria_360_y_11_Poses_Movimiento_Natural_IA_Omni_1080p.mp4",
        EDITADOS_DIR / "Avatar_Veterinaria_360_IA_Omni_Giro_Continuo_15s_1080p.mp4",
    ]:
        src = (
            AVATAR_DIR / "Avatar_Veterinaria_360_IA_Omni_Giro_Continuo_15s_1080p.mp4"
            if "15s" in dst.name
            else out_master_avatar
        )
        shutil.copy2(src, dst)
        print(f"   -> Copiado a: {dst}")

    # Crear grilla de verificación de las 11 poses exactas extraídas del video final (39.0s)
    # Timestamps en el video de 39.0s para cada una de las 11 poses:
    # Pose 1 (0° Frente): 0.8s
    # Pose 2 (-45° 3/4 Izq): 3.0s
    # Pose 3 (-90° Lateral Izq): 5.3s
    # Pose 4 (180° Espalda - Pose 6_espalda): 8.2s
    # Pose 5 (+90° Lateral Der): 11.4s
    # Pose 6 (+45° 3/4 Der): 13.9s
    # Giro de cierre 0° Frente: 16.3s
    # Pose 7 (Espalda en Puntitas): 18.6s
    # Pose 8 (Espalda Agachada mirando sobre hombro): 23.2s
    # Pose 9 (Frente Agachada manos en rodillas): 26.8s
    # Pose 10 (En Cuclillas de Frente): 29.0s
    # Pose 11 (En Cuclillas de Espalda mirando sobre hombro): 37.8s
    pose_checks = [
        (0.8, "Pose 1: 0 deg Frente"),
        (3.0, "Pose 2: -45 deg 3/4 Izq"),
        (5.3, "Pose 3: -90 deg Lat Izq"),
        (8.2, "Pose 6: 180 deg Espalda"),
        (11.4, "Pose 5: +90 deg Lat Der"),
        (13.9, "Pose 4: +45 deg 3/4 Der"),
        (18.6, "Pose 7: Espalda Puntitas"),
        (23.2, "Pose 8: Espalda Agachada"),
        (26.8, "Pose 9: Frente Agachada"),
        (29.0, "Pose 10: Cuclillas Frente"),
        (34.8, "Transicion Lenta Espalda"),
        (37.8, "Pose 11: Cuclillas Espalda"),
    ]
    tiles = []
    for t_sec, label in pose_checks:
        f_idx = min(len(master_frames) - 1, int(t_sec * out_fps))
        tile = cv2.resize(master_frames[f_idx], (360, 640))
        cv2.rectangle(tile, (0, 0), (360, 74), (18, 24, 32), -1)
        cv2.putText(tile, f"{t_sec:04.1f}s", (12, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        cv2.putText(tile, label, (12, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
        tiles.append(tile)

    rows = [np.hstack(tiles[i : i + 4]) for i in range(0, 12, 4)]
    grid_img = np.vstack(rows)
    grid_out_work = WORK_DIR / "verification_grid_avatar_360_11_poses.jpg"
    grid_out_art = ARTIFACTS_DIR / "verification_grid_avatar_360_11_poses.jpg"
    cv2.imwrite(str(grid_out_work), grid_img, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    cv2.imwrite(str(grid_out_art), grid_img, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    print(f"   -> Grilla de verificacion guardada en: {grid_out_art}")


if __name__ == "__main__":
    main()
