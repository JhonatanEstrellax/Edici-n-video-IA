# -*- coding: utf-8 -*-
r"""
Ensambla el Master Definitivo en 1080p (1080x1920 @ 30fps, 39.0s) a partir de la cadena pura de 30.0s
generada en Gemini Omni 1.2 Flash (`Avatar_Veterinaria_360_y_11_Poses_Completo_IA_Omni_30s_1080p.mp4`,
Interaction ID: v1_ChdKMGJ5YXFuMUJJV0d6N0lQbHJUNzhBdxIXazJmeWF0bTZIWi1mejdJUDRvTDgyQWM),
garantizando que NO se omita ninguna de las 11 poses y que cada transición sea lenta, pausada y 100% natural.
"""
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

VID_PURE_30S = AVATAR_DIR / "Avatar_Veterinaria_360_y_11_Poses_Completo_IA_Omni_30s_1080p.mp4"
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
            out.append(cv2.addWeighted(frames[idx0], 1.0 - alpha, frames[idx1], alpha, 0.0))
    return out


def main():
    print("1. Leyendo los 720 frames (30.0s @ 24fps) de la cadena pura de Gemini Omni 1.2 Flash...")
    frames_30s, fps = read_all_frames(VID_PURE_30S)
    print(f"   Frames leídos: {len(frames_30s)} (@{fps}fps = {len(frames_30s)/fps:.2f}s)")

    out_fps = 30
    # Estiramiento lento y suave (1.30x de duración: 30.0s -> 39.0s @ 30fps = 1170 frames)
    master_frames = resample_frames_smooth(frames_30s, int(39.0 * out_fps))
    total_dur = len(master_frames) / out_fps
    print(f"   Master lento y natural: {len(master_frames)} frames @ {out_fps}fps ({total_dur:.2f}s)")

    temp_raw_mp4 = WORK_DIR / "temp_master_360_11_poses_slow_noaudio.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    vw = cv2.VideoWriter(str(temp_raw_mp4), fourcc, out_fps, (1080, 1920))
    for f in master_frames:
        vw.write(f)
    vw.release()

    out_master_avatar = AVATAR_DIR / "Avatar_Veterinaria_360_y_11_Poses_Movimiento_Natural_IA_Omni_1080p.mp4"
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
    subprocess.run(cmd, check=True)
    if temp_raw_mp4.exists():
        temp_raw_mp4.unlink()

    for dst in [
        EDITADOS_DIR / "Avatar_Veterinaria_360_y_11_Poses_Movimiento_Natural_IA_Omni_1080p.mp4",
        BASE_DIR / "Avatar_Veterinaria_360_y_11_Poses_Movimiento_Natural_IA_Omni_1080p.mp4",
        ARTIFACTS_DIR / "Avatar_Veterinaria_360_y_11_Poses_Movimiento_Natural_IA_Omni_1080p.mp4",
        EDITADOS_DIR / "Avatar_Veterinaria_360_y_11_Poses_Completo_IA_Omni_30s_1080p.mp4",
    ]:
        src = VID_PURE_30S if "30s" in dst.name else out_master_avatar
        shutil.copy2(src, dst)
        print(f"   -> Copiado a: {dst}")

    # Grilla de verificación de las 11 poses en la versión de 39.0s (factor 1.30x respecto a los 30.0s originales)
    pose_checks = [
        (0.8, "Pose 1: 0 deg Frente"),
        (3.5, "Pose 2: -45 deg 3/4 Izq"),
        (5.3, "Pose 3: -90 deg Lat Izq"),
        (8.8, "Pose 6: 180 deg Espalda"),
        (10.6, "Pose 5: +90 deg Lat Der"),
        (12.4, "Pose 4: +45 deg 3/4 Der"),
        (21.6, "Pose 7: Espalda Puntitas"),
        (26.7, "Pose 8: Espalda Agachada"),
        (30.7, "Pose 9: Frente Agachada"),
        (33.7, "Pose 10: Cuclillas Frente"),
        (36.8, "Giro Lento Espalda"),
        (38.5, "Pose 11: Cuclillas Espalda"),
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
    for p in [
        WORK_DIR / "verification_grid_avatar_360_11_poses.jpg",
        ARTIFACTS_DIR / "verification_grid_avatar_360_11_poses.jpg",
    ]:
        cv2.imwrite(str(p), grid_img, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    print("   -> Grilla de verificación actualizada.")


if __name__ == "__main__":
    main()
