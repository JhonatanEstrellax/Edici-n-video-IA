# -*- coding: utf-8 -*-
r"""
Ensambla el Master Definitivo en 1080p (1080x1920 @ 30fps, 49.0s) a partir de:
1. La cadena pura de 30.0s generada en Gemini Omni 1.2 Flash (`Avatar_Veterinaria_360_y_11_Poses_Completo_IA_Omni_30s_1080p.mp4`),
   estirada suavemente a 39.0s @ 30fps para que el giro 360° y las 11 poses tengan transiciones lentas, pausadas y 100% naturales.
2. El cierre de 10.0s generado en Gemini Omni 1.2 Flash (`omni_cta_finale_job1_firstframe_10s.mp4`) que parte exactamente
   del último frame de la Pose 11 (En Cuclillas de Espalda), donde la veterinaria se incorpora suavemente, gira hacia cámara
   y pronuncia con lip-sync en español argentino la Llamada a la Acción para MascotaMás:
   "¡Sumate hoy a MascotaMás! Pasamos toda tu veterinaria en el día y 100% gratis. ¡Escribinos ahora!"
   acompañada de subtítulos Poppins ExtraBold y tarjeta CTA oficial de MascotaMás en zona segura inferior.
"""
import shutil
import pathlib
import subprocess
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = pathlib.Path(r"c:\IA\Edicion de videos")
FFMPEG_EXE = str(BASE_DIR / "bin" / "ffmpeg" / "ffmpeg.exe")
WORK_DIR = BASE_DIR / "reels_work"
AVATAR_DIR = BASE_DIR / "assets" / "avatar_veterinaria_360"
EDITADOS_DIR = BASE_DIR / "editados"
ARTIFACTS_DIR = pathlib.Path(r"C:\Users\Demiante\.gemini\antigravity\brain\56e5cec9-1285-4884-b2c6-a38ac91ed5ae")

VID_PURE_30S_RAW = WORK_DIR / "pure_30s_chain_backup.mp4"
VID_PURE_30S_DEST = AVATAR_DIR / "Avatar_Veterinaria_360_y_11_Poses_Completo_IA_Omni_30s_1080p.mp4"
VID_CTA_10S = WORK_DIR / "omni_cta_finale_job1_firstframe_10s.mp4"
AUDIO_HOUSE = WORK_DIR / "v7_lyria_house_arriba.wav"
LOGO_PATH = BASE_DIR / "assets" / "mascotamas" / "logo.png"
FONT_EXTRABOLD = str(BASE_DIR / "fonts" / "Poppins-ExtraBold.ttf")
FONT_BOLD = str(BASE_DIR / "fonts" / "Poppins-Bold.ttf")


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


def decorate_cta_frame(frame_bgr, t_cta_sec, logo_rgba, font_sub, font_title, font_badge, font_url):
    """
    Aplica en el cierre CTA (t_cta_sec de 0.0s a 10.0s):
    - De 2.0s a 10.0s (cuando ya se incorporó y mira de frente a cámara):
      * Pastilla superior izquierda con logo oficial de MascotaMás
      * Subtítulos Poppins ExtraBold sincronizados con su voz (y=1280)
      * Tarjeta CTA inferior de MascotaMás (y=1470..1760):
        "MIGRACIÓN 100% GRATIS EN EL DÍA" + "¡Escribinos ahora! · mascotamas.com"
    """
    if t_cta_sec < 1.8:
        return frame_bgr

    fade_alpha = min(1.0, (t_cta_sec - 1.8) / 0.5)
    img_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    base_pil = Image.fromarray(img_rgb).convert("RGBA")
    overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 1. Pastilla superior con el Logo Oficial de MascotaMás (y=70..166)
    a_pill = int(242 * fade_alpha)
    draw.rounded_rectangle([60, 70, 470, 168], radius=49, fill=(255, 255, 255, a_pill))
    if logo_rgba is not None:
        logo_copy = logo_rgba.copy()
        if fade_alpha < 0.99:
            r, g, b, a = logo_copy.split()
            a = a.point(lambda p: int(p * fade_alpha))
            logo_copy = Image.merge("RGBA", (r, g, b, a))
        overlay.paste(logo_copy, (88, 84), logo_copy)

    # 2. Subtítulos Poppins sincronizados con las palabras habladas (2.40s -> 9.20s)
    sub_lines = None
    highlight_color = (242, 199, 92, int(255 * fade_alpha))  # Dorado MascotaMás #F2C75C
    white_color = (255, 255, 255, int(255 * fade_alpha))

    if 2.30 <= t_cta_sec < 4.45:
        sub_lines = [("¡SUMATE HOY A", white_color), ("MASCOTAMÁS!", highlight_color)]
    elif 4.45 <= t_cta_sec < 6.35:
        sub_lines = [("PASAMOS TODA TU", white_color), ("VETERINARIA EN EL DÍA", highlight_color)]
    elif 6.35 <= t_cta_sec < 7.95:
        sub_lines = [("¡Y 100% GRATIS!", highlight_color)]
    elif 7.95 <= t_cta_sec <= 9.80:
        sub_lines = [("¡ESCRIBINOS AHORA!", highlight_color)]

    if sub_lines:
        y_sub = 1230 if len(sub_lines) == 2 else 1270
        for line_txt, col in sub_lines:
            bbox = draw.textbbox((0, 0), line_txt, font=font_sub)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            tx = (1080 - tw) // 2
            # Fondo pastilla oscura translúcida detrás del subtítulo
            draw.rounded_rectangle(
                [tx - 28, y_sub - 10, tx + tw + 28, y_sub + th + 18],
                radius=24,
                fill=(15, 23, 42, int(215 * fade_alpha)),
            )
            # Sombra + texto
            draw.text((tx + 3, y_sub + 3), line_txt, font=font_sub, fill=(0, 0, 0, int(220 * fade_alpha)))
            draw.text((tx, y_sub), line_txt, font=font_sub, fill=col)
            y_sub += th + 34

    # 3. Tarjeta CTA Inferior de Marca (y=1470..1775)
    card_x1, card_y1, card_x2, card_y2 = 64, 1475, 1016, 1775
    draw.rounded_rectangle(
        [card_x1, card_y1, card_x2, card_y2],
        radius=38,
        fill=(15, 36, 57, int(235 * fade_alpha)),
        outline=(242, 199, 92, int(245 * fade_alpha)),
        width=4,
    )
    # Etiqueta dorada superior dentro de la tarjeta
    badge_txt = "MIGRACIÓN 100% GRATIS EN EL DÍA"
    bb_b = draw.textbbox((0, 0), badge_txt, font=font_badge)
    bw = bb_b[2] - bb_b[0]
    bx = (1080 - bw) // 2
    draw.rounded_rectangle(
        [bx - 26, card_y1 + 24, bx + bw + 26, card_y1 + 82],
        radius=29,
        fill=(242, 199, 92, int(255 * fade_alpha)),
    )
    draw.text((bx, card_y1 + 32), badge_txt, font=font_badge, fill=(15, 23, 42, int(255 * fade_alpha)))

    # Título principal CTA
    cta_main = "¡Pedi tu Demo en MascotaMás!"
    bb_m = draw.textbbox((0, 0), cta_main, font=font_title)
    mw = bb_m[2] - bb_m[0]
    draw.text(((1080 - mw) // 2, card_y1 + 104), cta_main, font=font_title, fill=white_color)

    # Botón verde esmeralda / URL
    url_txt = "mascotamas.com  ·  WhatsApp Directo"
    bb_u = draw.textbbox((0, 0), url_txt, font=font_url)
    uw = bb_u[2] - bb_u[0]
    ux = (1080 - uw) // 2
    draw.rounded_rectangle(
        [ux - 34, card_y1 + 188, ux + uw + 34, card_y1 + 262],
        radius=37,
        fill=(16, 185, 129, int(255 * fade_alpha)),
    )
    draw.text((ux, card_y1 + 199), url_txt, font=font_url, fill=white_color)

    comp = Image.alpha_composite(base_pil, overlay).convert("RGB")
    return cv2.cvtColor(np.array(comp), cv2.COLOR_RGB2BGR)


def main():
    # Respaldamos los 30s puros si aún no están respaldados
    if not VID_PURE_30S_RAW.exists():
        shutil.copy2(VID_PURE_30S_DEST, VID_PURE_30S_RAW)

    print("1. Leyendo los 720 frames (30.0s @ 24fps) de las 11 poses y los 240 frames (10.0s @ 24fps) del cierre CTA...")
    frames_30s, _ = read_all_frames(VID_PURE_30S_RAW)
    frames_cta_24, _ = read_all_frames(VID_CTA_10S)
    print(f"   Poses (30s): {len(frames_30s)} frames | CTA (10s): {len(frames_cta_24)} frames")

    out_fps = 30
    # 1) Estiramiento lento y suave de las 11 poses: 30.0s -> 39.0s @ 30fps (1170 frames)
    slow_poses_39s = resample_frames_smooth(frames_30s, int(39.0 * out_fps))
    # 2) El cierre CTA con lip-sync mantiene su velocidad exacta de 10.0s (re-muestreado de 24fps a 30fps = 300 frames)
    #    para que la sincronización labial sea 100% exacta al milisegundo
    cta_frames_30fps = resample_frames_smooth(frames_cta_24, int(10.0 * out_fps))

    # Preparamos fuentes y logo para decorar el cierre CTA
    logo_rgba = None
    if LOGO_PATH.exists():
        raw_logo = Image.open(LOGO_PATH).convert("RGBA")
        lh = 70
        lw = int(raw_logo.width * (lh / raw_logo.height))
        logo_rgba = raw_logo.resize((lw, lh), Image.LANCZOS)

    font_sub = ImageFont.truetype(FONT_EXTRABOLD, 52)
    font_title = ImageFont.truetype(FONT_EXTRABOLD, 46)
    font_badge = ImageFont.truetype(FONT_EXTRABOLD, 31)
    font_url = ImageFont.truetype(FONT_BOLD, 36)

    decorated_cta_frames = []
    for idx, f in enumerate(cta_frames_30fps):
        t_cta = idx / out_fps
        decorated_cta_frames.append(
            decorate_cta_frame(f, t_cta, logo_rgba, font_sub, font_title, font_badge, font_url)
        )

    master_frames = slow_poses_39s + decorated_cta_frames
    total_dur = len(master_frames) / out_fps
    print(f"   Master completo (360° + 11 Poses Lentas + CTA MascotaMás): {len(master_frames)} frames @ {out_fps}fps ({total_dur:.2f}s)")

    temp_raw_mp4 = WORK_DIR / "temp_master_360_11_poses_cta_noaudio.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    vw = cv2.VideoWriter(str(temp_raw_mp4), fourcc, out_fps, (1080, 1920))
    for f in master_frames:
        vw.write(f)
    vw.release()

    # Mezcla de audio profesional:
    # - 0.0s a 39.0s: Música House sincronizada al 35%
    # - 39.0s a 49.0s: Ducking suave de la música House al 12% + Voz y Lip-Sync original del CTA (100% volumen con retraso de 39000ms)
    out_master_avatar = AVATAR_DIR / "Avatar_Veterinaria_360_y_11_Poses_Movimiento_Natural_IA_Omni_1080p.mp4"
    filter_complex = (
        f"[1:a]volume='if(lt(t,38.8),0.35,0.12)':eval=frame,"
        f"afade=t=in:st=0:d=1.0,afade=t=out:st={total_dur-1.5:.2f}:d=1.5[bg];"
        f"[2:a]volume=1.45,adelay=39000|39000[cta_v];"
        f"[bg][cta_v]amix=inputs=2:duration=first:dropout_transition=0,alimiter=limit=0.95[aout]"
    )
    cmd = [
        FFMPEG_EXE, "-y",
        "-i", str(temp_raw_mp4),
        "-stream_loop", "-1", "-i", str(AUDIO_HOUSE),
        "-i", str(VID_CTA_10S),
        "-t", f"{total_dur:.2f}",
        "-filter_complex", filter_complex,
        "-map", "0:v:0", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(out_master_avatar),
    ]
    subprocess.run(cmd, check=True)
    if temp_raw_mp4.exists():
        temp_raw_mp4.unlink()

    # También ensamblamos la versión limpia sin textos de 40.0s (30s 11 poses + 10s CTA hablado) en VID_PURE_30S_DEST
    cmd_clean_40s = [
        FFMPEG_EXE, "-y",
        "-i", str(VID_PURE_30S_RAW),
        "-i", str(VID_CTA_10S),
        "-filter_complex", "[0:v:0][0:a:0][1:v:0][1:a:0]concat=n=2:v=1:a=1[v][a]",
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(VID_PURE_30S_DEST),
    ]
    subprocess.run(cmd_clean_40s, check=True)

    for dst in [
        EDITADOS_DIR / "Avatar_Veterinaria_360_y_11_Poses_Movimiento_Natural_IA_Omni_1080p.mp4",
        BASE_DIR / "Avatar_Veterinaria_360_y_11_Poses_Movimiento_Natural_IA_Omni_1080p.mp4",
        ARTIFACTS_DIR / "Avatar_Veterinaria_360_y_11_Poses_Movimiento_Natural_IA_Omni_1080p.mp4",
        EDITADOS_DIR / "Avatar_Veterinaria_360_y_11_Poses_Completo_IA_Omni_30s_1080p.mp4",
    ]:
        src = VID_PURE_30S_DEST if "30s" in dst.name else out_master_avatar
        shutil.copy2(src, dst)
        print(f"   -> Copiado a: {dst}")

    # Grilla de verificación de 12 cuadros (Las 11 Poses + El Cierre CTA de MascotaMás)
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
        (38.5, "Pose 11: Cuclillas Espalda"),
        (44.2, "Cierre CTA: MascotaMas"),
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
    print("   -> Grilla de verificación de las 11 Poses + Cierre CTA actualizada.")


if __name__ == "__main__":
    main()
