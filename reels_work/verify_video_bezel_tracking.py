# -*- coding: utf-8 -*-
r"""
Perfecciona el ajuste sub-píxel de las pantallas reales de `gestion.mascotamas.com`
sobre la MacBook Pro 16" y el iPhone 16 Pro Max en `clip1`, `clip2` y `clip3`,
incluyendo el bisel negro Titanium + esquinas redondeadas + Dynamic Island en el iPhone
y preservando manos/dedos en primer plano.
"""
import sys
import pathlib
import shutil
import cv2
import numpy as np

sys.path.insert(0, r"c:\IA\Edicion de videos\reels_work")
from apply_exact_real_screens_to_kfs import (
    UI_ESCRITORIO_DESK,
    UI_CALENDARIOS_DESK,
    UI_HC_PDF_DESK,
    UI_TURNOS_MOB,
    UI_HC_MOB,
)

BASE_DIR = pathlib.Path(r"c:\IA\Edicion de videos")
SPOT_DIR = BASE_DIR / "assets" / "avatar_veterinario_hombre_vip" / "spot_dueto_hombre_mujer"
WORK_DIR = BASE_DIR / "reels_work"
ARTIFACTS_DIR = pathlib.Path(r"C:\Users\Demiante\.gemini\antigravity\brain\56e5cec9-1285-4884-b2c6-a38ac91ed5ae")

SX = 1080.0 / 768.0
SY = 1920.0 / 1376.0


def scale_quad(q_768):
    q = np.array(q_768, dtype=np.float32)
    q[:, 0] *= SX
    q[:, 1] *= SY
    return q


Q_KF1_MAC = scale_quad([[307.0, 639.0], [494.0, 620.0], [514.0, 774.0], [329.0, 758.0]])
Q_KF2_MAC = scale_quad([[292.0, 636.0], [496.0, 638.0], [492.0, 755.0], [293.0, 752.0]])
Q_KF3_MAC = scale_quad([[292.0, 636.0], [496.0, 638.0], [492.0, 755.0], [293.0, 752.0]])
Q_KF3_IPH = scale_quad([[437.0, 736.0], [473.0, 730.0], [531.0, 809.0], [495.0, 816.0]])
Q_KF4_MAC = scale_quad([[358.0, 916.0], [728.0, 954.0], [708.0, 1170.0], [338.0, 1118.0]])
Q_KF4_IPH = scale_quad([[376.0, 606.0], [425.0, 607.0], [423.0, 710.0], [374.0, 709.0]])

_UI_CACHE = {}


def get_ui_img(path_str):
    if path_str not in _UI_CACHE:
        _UI_CACHE[path_str] = cv2.imread(path_str)
    return _UI_CACHE[path_str].copy()


def sample_border_points(quad, n_per_edge=12):
    pts = []
    for i in range(4):
        p0 = quad[i]
        p1 = quad[(i + 1) % 4]
        for t in np.linspace(0.05, 0.95, n_per_edge):
            pts.append(p0 * (1.0 - t) + p1 * t)
    return np.array(pts, dtype=np.float32).reshape(-1, 1, 2)


def track_quad_sequence(frames_gray, q_start, q_end=None):
    n = len(frames_gray)
    lk_params = dict(winSize=(25, 25), maxLevel=3, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01))

    fwd_quads = [q_start.copy()]
    cur_q = q_start.copy()
    for i in range(1, n):
        p0 = sample_border_points(cur_q)
        p1, st, _ = cv2.calcOpticalFlowPyrLK(frames_gray[i - 1], frames_gray[i], p0, None, **lk_params)
        good0 = p0[st == 1].reshape(-1, 2)
        good1 = p1[st == 1].reshape(-1, 2)
        if len(good0) >= 6:
            M, _ = cv2.estimateAffinePartial2D(good0, good1, method=cv2.RANSAC, ransacReprojThreshold=3.0)
            if M is not None:
                ones = np.ones((4, 1), dtype=np.float32)
                cur_q = (M @ np.hstack([cur_q, ones]).T).T.astype(np.float32)
        fwd_quads.append(cur_q.copy())

    if q_end is None:
        return fwd_quads

    bwd_quads = [None] * n
    bwd_quads[-1] = q_end.copy()
    cur_q = q_end.copy()
    for i in range(n - 2, -1, -1):
        p0 = sample_border_points(cur_q)
        p1, st, _ = cv2.calcOpticalFlowPyrLK(frames_gray[i + 1], frames_gray[i], p0, None, **lk_params)
        good0 = p0[st == 1].reshape(-1, 2)
        good1 = p1[st == 1].reshape(-1, 2)
        if len(good0) >= 6:
            M, _ = cv2.estimateAffinePartial2D(good0, good1, method=cv2.RANSAC, ransacReprojThreshold=3.0)
            if M is not None:
                ones = np.ones((4, 1), dtype=np.float32)
                cur_q = (M @ np.hstack([cur_q, ones]).T).T.astype(np.float32)
        bwd_quads[i] = cur_q.copy()

    blended = []
    for i in range(n):
        u = i / float(max(1, n - 1))
        w = 0.5 - 0.5 * np.cos(u * np.pi)
        q = fwd_quads[i] * (1.0 - w) + bwd_quads[i] * w
        blended.append(q.astype(np.float32))
    return blended


def warp_device_screen(img, ui_path, quad, is_iphone=False, keep_skin=True, exclude_poly=None, opacity=1.0):
    if opacity <= 0.01:
        return img
    h, w = img.shape[:2]
    ui = get_ui_img(ui_path)
    uh, uw = ui.shape[:2]

    src_mask = np.zeros((uh, uw), dtype=np.uint8)
    if is_iphone:
        # Chasis/bisel Titanium + pantalla redondeada con Dynamic Island integrada
        canvas = np.full((uh, uw, 3), (24, 26, 30), dtype=np.uint8)
        outer_rad = int(min(uw, uh) * 0.13)
        cv2.rectangle(src_mask, (outer_rad, 0), (uw - outer_rad, uh), 255, -1)
        cv2.rectangle(src_mask, (0, outer_rad), (uw, uh - outer_rad), 255, -1)
        for cx, cy in [(outer_rad, outer_rad), (uw - outer_rad, outer_rad), (uw - outer_rad, uh - outer_rad), (outer_rad, uh - outer_rad)]:
            cv2.circle(src_mask, (cx, cy), outer_rad, 255, -1)

        pad_x = int(uw * 0.045)
        pad_y = int(uh * 0.024)
        in_w = uw - 2 * pad_x
        in_h = uh - 2 * pad_y
        ui_resized = cv2.resize(ui, (in_w, in_h), interpolation=cv2.INTER_AREA)

        inner_mask = np.zeros((uh, uw), dtype=np.uint8)
        in_rad = int(min(in_w, in_h) * 0.10)
        cv2.rectangle(inner_mask, (pad_x + in_rad, pad_y), (pad_x + in_w - in_rad, pad_y + in_h), 255, -1)
        cv2.rectangle(inner_mask, (pad_x, pad_y + in_rad), (pad_x + in_w, pad_y + in_h - in_rad), 255, -1)
        for cx, cy in [
            (pad_x + in_rad, pad_y + in_rad),
            (pad_x + in_w - in_rad, pad_y + in_rad),
            (pad_x + in_w - in_rad, pad_y + in_h - in_rad),
            (pad_x + in_rad, pad_y + in_h - in_rad),
        ]:
            cv2.circle(inner_mask, (cx, cy), in_rad, 255, -1)

        canvas_roi = canvas[pad_y : pad_y + in_h, pad_x : pad_x + in_w]
        im_roi = inner_mask[pad_y : pad_y + in_h, pad_x : pad_x + in_w]
        canvas_roi[im_roi > 0] = ui_resized[im_roi > 0]

        # Dynamic Island pill
        pill_w = int(uw * 0.27)
        pill_h = int(uh * 0.032)
        px1 = (uw - pill_w) // 2
        py1 = pad_y + int(uh * 0.014)
        cv2.rectangle(canvas, (px1 + pill_h // 2, py1), (px1 + pill_w - pill_h // 2, py1 + pill_h), (14, 15, 18), -1)
        cv2.circle(canvas, (px1 + pill_h // 2, py1 + pill_h // 2), pill_h // 2, (14, 15, 18), -1)
        cv2.circle(canvas, (px1 + pill_w - pill_h // 2, py1 + pill_h // 2), pill_h // 2, (14, 15, 18), -1)
        ui_to_warp = canvas
    else:
        src_mask[:, :] = 255
        ui_to_warp = ui

    src_pts = np.array([[0, 0], [uw - 1, 0], [uw - 1, uh - 1], [0, uh - 1]], dtype=np.float32)
    M = cv2.getPerspectiveTransform(src_pts, quad)
    warped = cv2.warpPerspective(ui_to_warp, M, (w, h), flags=cv2.INTER_LANCZOS4)
    poly = cv2.warpPerspective(src_mask, M, (w, h), flags=cv2.INTER_LINEAR)

    if exclude_poly is not None:
        cv2.fillConvexPoly(poly, exclude_poly.astype(np.int32), 0)

    if keep_skin:
        ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
        Y, Cr, Cb = cv2.split(ycrcb)
        skin = ((Cr > 140) & (Cb < 128) & (Y < 220) & (Y > 45)).astype(np.uint8) * 255
        skin = cv2.dilate(skin, np.ones((3, 3), np.uint8), iterations=1)
        poly = cv2.bitwise_and(poly, cv2.bitwise_not(skin))

    alpha = (cv2.GaussianBlur(poly.astype(np.float32) / 255.0, (3, 3), 0) * float(opacity))[..., None]
    return (warped.astype(np.float32) * alpha + img.astype(np.float32) * (1.0 - alpha)).astype(np.uint8)


def process_clip_with_real_screens(mp4_path, mode):
    cap = cv2.VideoCapture(str(mp4_path))
    frames = []
    grays = []
    while True:
        ok, frm = cap.read()
        if not ok:
            break
        frames.append(frm)
        grays.append(cv2.cvtColor(frm, cv2.COLOR_BGR2GRAY))
    cap.release()

    if mode == "clip1":
        mac_quads = track_quad_sequence(grays, Q_KF1_MAC, Q_KF2_MAC)
        for i in range(len(frames)):
            frames[i] = warp_device_screen(frames[i], UI_ESCRITORIO_DESK, mac_quads[i], is_iphone=False, keep_skin=True)
    elif mode == "clip2":
        mac_quads = track_quad_sequence(grays, Q_KF2_MAC, Q_KF3_MAC)
        iph_quads = track_quad_sequence(grays[::-1], Q_KF3_IPH, None)[::-1]
        for i in range(len(frames)):
            # En clip2 la veterinaria levanta el iPhone entre el cuadro 16 y el 28
            iph_op = min(1.0, max(0.0, (i - 16) / 10.0))
            qi = iph_quads[i]
            center = qi.mean(axis=0)
            excl = (center + (qi - center) * 1.08) if iph_op > 0.1 else None
            desk_ui = UI_ESCRITORIO_DESK if i < 18 else UI_CALENDARIOS_DESK
            frames[i] = warp_device_screen(frames[i], desk_ui, mac_quads[i], is_iphone=False, keep_skin=True, exclude_poly=excl)
            if iph_op > 0.01:
                frames[i] = warp_device_screen(frames[i], UI_TURNOS_MOB, qi, is_iphone=True, keep_skin=True, opacity=iph_op)
    elif mode == "clip3":
        mac_quads = track_quad_sequence(grays, Q_KF4_MAC, Q_KF4_MAC)
        iph_quads = track_quad_sequence(grays, Q_KF4_IPH, Q_KF4_IPH)
        for i in range(len(frames)):
            frames[i] = warp_device_screen(frames[i], UI_HC_PDF_DESK, mac_quads[i], is_iphone=False, keep_skin=False)
            frames[i] = warp_device_screen(frames[i], UI_HC_MOB, iph_quads[i], is_iphone=True, keep_skin=True)

    return frames


def main():
    rows = []
    for mode, fn in [
        ("clip1", "spot_dueto_clip1_espalda_a_giro_10s.mp4"),
        ("clip2", "spot_dueto_clip2_dueto_funciones_macbook_10s.mp4"),
        ("clip3", "spot_dueto_clip3_frente_dueto_cta_10s.mp4"),
    ]:
        frms = process_clip_with_real_screens(SPOT_DIR / fn, mode)
        thumbs = []
        for idx in [0, 48, 96, 144, 192, 235]:
            th = cv2.resize(frms[min(len(frms) - 1, idx)], (270, 480), interpolation=cv2.INTER_AREA)
            cv2.rectangle(th, (0, 0), (270, 36), (15, 23, 42), -1)
            cv2.putText(th, f"{mode} f={idx}", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (52, 211, 153), 2)
            thumbs.append(th)
        rows.append(np.hstack(thumbs))

    grid = np.vstack(rows)
    out_g = WORK_DIR / "verify_tracked_real_screens_grid.jpg"
    cv2.imwrite(str(out_g), grid, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    shutil.copy2(out_g, ARTIFACTS_DIR / out_g.name)
    print("Saved:", out_g)


if __name__ == "__main__":
    main()
