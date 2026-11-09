import os
import subprocess
import cv2
import numpy as np
from scipy.ndimage import gaussian_filter1d

BASE_DIR = r"c:\IA\Edicion de videos"
WORK_DIR = os.path.join(BASE_DIR, "reels_work")
FFMPEG_BIN = os.path.join(BASE_DIR, "bin", "ffmpeg", "ffmpeg.exe")


def build_silhouette_maps(w: int, h: int):
    u, v = np.meshgrid(
        np.linspace(0.0, 1.0, w, dtype=np.float32),
        np.linspace(0.0, 1.0, h, dtype=np.float32)
    )
    du = u - 0.50
    abs_du = np.abs(du)

    fg_plateau = np.clip((0.47 - abs_du) / (0.47 - 0.33), 0.0, 1.0)
    fg_plateau = fg_plateau * fg_plateau * (3.0 - 2.0 * fg_plateau)

    # 1. Collar contour adjustment
    collar_u = np.exp(-(du / 0.065)**2)
    collar_v = np.exp(-((v - 0.622) / 0.042)**2) * np.clip((v - 0.565) / 0.025, 0.0, 1.0)
    dv_collar = -0.046 * collar_u * collar_v
    du_collar = np.sign(du) * 0.015 * np.exp(-((abs_du - 0.042) / 0.035)**2) * collar_v

    # 2. Upper torso contour expansion
    r2_l = ((u - 0.380) / 0.122)**2 + ((v - 0.662) / 0.084)**2
    r2_r = ((u - 0.620) / 0.122)**2 + ((v - 0.662) / 0.084)**2
    spheres = np.exp(-r2_l) + np.exp(-r2_r)

    upper_v_band = np.exp(-((v - 0.662) / 0.080)**2)
    torso_gate = np.clip((0.275 - abs_du) / (0.275 - 0.215), 0.0, 1.0)
    torso_gate = torso_gate * torso_gate * (3.0 - 2.0 * torso_gate)
    du_upper = -du * 0.36 * upper_v_band * torso_gate
    dv_upper = 0.028 * spheres * ((v - 0.652) / 0.080)

    # 3. Mid-torso silhouette contour
    mid_v_band = np.exp(-((v - 0.822) / 0.080)**2)
    mid_v_band *= np.clip((v - 0.705) / 0.045, 0.0, 1.0) * np.clip((0.945 - v) / 0.045, 0.0, 1.0)
    inner_only = np.clip((0.218 - abs_du) / (0.218 - 0.170), 0.0, 1.0)
    inner_only = inner_only * inner_only * (3.0 - 2.0 * inner_only)
    du_mid = du * mid_v_band * (0.135 * fg_plateau + 0.095 * inner_only)

    # 4. Lower torso flare
    low_v_band = np.exp(-((v - 0.975) / 0.055)**2)
    du_low = -du * 0.11 * low_v_band * fg_plateau

    src_u = u + du_collar + du_upper + du_mid + du_low
    src_v = v + dv_collar + dv_upper

    map_x = (src_u * w).astype(np.float32)
    map_y = (src_v * h).astype(np.float32)

    # 5. Precompute 3D shading multipliers
    v_gate = np.clip((v - 0.584) / 0.016, 0.0, 1.0) * np.clip((0.648 - v) / 0.014, 0.0, 1.0)
    center_line = np.exp(-((u - 0.50) / 0.0052)**2) * np.exp(-((v - 0.620) / 0.024)**2) * v_gate
    l_curve = np.exp(-((u - (0.50 - (0.628 - v)*0.52)) / 0.0072)**2) * np.exp(-((v - 0.604) / 0.014)**2) * v_gate
    r_curve = np.exp(-((u - (0.50 + (0.628 - v)*0.52)) / 0.0072)**2) * np.exp(-((v - 0.604) / 0.014)**2) * v_gate
    c_shade = np.clip(center_line * 0.42 + (l_curve + r_curve) * 0.25, 0.0, 0.45)

    inner_hl = (
        np.exp(-((u - 0.474) / 0.016)**2 - ((v - 0.610) / 0.020)**2) +
        np.exp(-((u - 0.526) / 0.016)**2 - ((v - 0.610) / 0.020)**2)
    ) * 0.18 * v_gate

    dome_hl = (
        np.exp(-((u - 0.372) / 0.088)**2 - ((v - 0.630) / 0.044)**2) +
        np.exp(-((u - 0.628) / 0.088)**2 - ((v - 0.630) / 0.044)**2)
    ) * 0.32

    v_arc_l = 0.742 - 2.3 * (u - 0.380)**2
    low_l = np.exp(-((v - v_arc_l) / 0.019)**2) * np.exp(-((u - 0.380) / 0.094)**2)
    v_arc_r = 0.742 - 2.3 * (u - 0.620)**2
    low_r = np.exp(-((v - v_arc_r) / 0.019)**2) * np.exp(-((u - 0.620) / 0.094)**2)

    center_dip = np.exp(-((u - 0.50) / 0.022)**2 - ((v - 0.698) / 0.032)**2) * 0.36
    side_shade = (
        np.exp(-((u - 0.410) / 0.042)**2 - ((v - 0.815) / 0.065)**2) +
        np.exp(-((u - 0.590) / 0.042)**2 - ((v - 0.815) / 0.065)**2)
    ) * 0.26

    base_mult = 1.0 + inner_hl + dome_hl - (low_l + low_r) * 0.55 - center_dip - side_shade
    mult_bgr = np.stack([
        base_mult - c_shade * 1.15,
        base_mult - c_shade * 1.05,
        base_mult - c_shade * 0.75
    ], axis=-1).astype(np.float32)

    # Head blend mask
    r_head = np.sqrt(((u - 0.50) / 0.215)**2 + ((v - 0.355) / 0.148)**2)
    head_mask = np.clip((1.18 - r_head) / (1.18 - 0.72), 0.0, 1.0)
    head_mask = head_mask * head_mask * (3.0 - 2.0 * head_mask)
    v_cut = np.clip((0.512 - v) / (0.512 - 0.478), 0.0, 1.0)
    v_cut = v_cut * v_cut * (3.0 - 2.0 * v_cut)
    head_mask = (head_mask * v_cut)[:, :, None].astype(np.float32)

    return map_x, map_y, mult_bgr, head_mask


def process_master_video(in_mp4: str, out_mp4: str):
    cap = cv2.VideoCapture(in_mp4)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    ret, frame0 = cap.read()
    if not ret:
        raise RuntimeError(f"Cannot read {in_mp4}")

    # Fast half-resolution tracking for head scale & translation
    hw, hh = w // 2, h // 2
    gray0_h = cv2.resize(cv2.cvtColor(frame0, cv2.COLOR_BGR2GRAY), (hw, hh), interpolation=cv2.INTER_AREA)
    hy0, hy1 = int(0.22 * hh), int(0.41 * hh)
    hx0, hx1 = int(0.31 * hw), int(0.69 * hw)
    tmpl0 = gray0_h[hy0:hy1, hx0:hx1].copy()
    th, tw = tmpl0.shape

    scales = np.ones(n_frames, dtype=np.float32)
    txs = np.zeros(n_frames, dtype=np.float32)
    tys = np.zeros(n_frames, dtype=np.float32)

    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    prev_s = 1.0
    print(f"[TRACKING] Estimating trajectory for {os.path.basename(in_mp4)} ({n_frames} frames)...")
    for idx in range(n_frames):
        ret, frm = cap.read()
        if not ret:
            scales[idx] = prev_s
            txs[idx] = txs[max(0, idx - 1)]
            tys[idx] = tys[max(0, idx - 1)]
            continue
        if idx == 0:
            continue
        g_h = cv2.resize(cv2.cvtColor(frm, cv2.COLOR_BGR2GRAY), (hw, hh), interpolation=cv2.INTER_AREA)
        # Search around prev_s (with wider search near clip boundary around t=14..16s)
        s_min = 0.96 if (400 <= idx <= 490) else max(0.96, prev_s - 0.04)
        s_max = 1.35 if (400 <= idx <= 490) else min(1.36, prev_s + 0.04)
        n_steps = 25 if (400 <= idx <= 490) else 11

        best_val = -1.0
        best_s = prev_s
        best_loc = (hx0, hy0)
        for s in np.linspace(s_min, s_max, n_steps):
            inv_s = 1.0 / s
            sh_i, sw_i = int(round(hh * inv_s)), int(round(hw * inv_s))
            if sh_i <= th + 4 or sw_i <= tw + 4:
                continue
            sm = cv2.resize(g_h, (sw_i, sh_i), interpolation=cv2.INTER_LINEAR)
            res = cv2.matchTemplate(sm, tmpl0, cv2.TM_CCOEFF_NORMED)
            _, mval, _, mloc = cv2.minMaxLoc(res)
            if mval > best_val:
                best_val = mval
                best_s = s
                best_loc = mloc

        prev_s = best_s
        scales[idx] = best_s
        txs[idx] = (hx0 - best_loc[0]) * 2.0
        tys[idx] = (hy0 - best_loc[1]) * 2.0

    # Smooth trajectories (preserving any reset at clip stitch boundary if present, or smooth continuously)
    scales_sm = gaussian_filter1d(scales, sigma=2.2)
    txs_sm = gaussian_filter1d(txs, sigma=2.2)
    tys_sm = gaussian_filter1d(tys, sigma=2.2)

    map_x, map_y, mult_bgr, head_mask = build_silhouette_maps(w, h)
    frame0_f = frame0.astype(np.float32)

    cmd = [
        FFMPEG_BIN, "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-pix_fmt", "bgr24", "-s", f"{w}x{h}", "-r", f"{fps}",
        "-i", "-",
        "-i", in_mp4,
        "-map", "0:v:0", "-map", "1:a:0?",
        "-c:v", "libx264", "-preset", "fast", "-crf", "16",
        "-pix_fmt", "yuv420p", "-c:a", "copy",
        out_mp4
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    print(f"[RENDERING] Writing sculpted master -> {os.path.basename(out_mp4)}...")
    for idx in range(n_frames):
        ret, frm = cap.read()
        if not ret:
            break
        inv_s = 1.0 / float(scales_sm[idx])
        tx = float(txs_sm[idx])
        ty = float(tys_sm[idx])

        M_head = np.float32([[inv_s, 0.0, tx], [0.0, inv_s, ty]])
        aligned_head = cv2.warpAffine(frm, M_head, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

        # Subtle natural breathing motion on the base torso so it moves organically with speech
        t_sec = idx / float(fps)
        breath_dy = 2.2 * np.sin(2.0 * np.pi * 0.32 * t_sec)
        M_breath = np.float32([[1.0, 0.0, 0.0], [0.0, 1.0, breath_dy]])
        torso_breath = cv2.warpAffine(frame0_f, M_breath, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

        comp = (aligned_head.astype(np.float32) * head_mask + torso_breath * (1.0 - head_mask)).astype(np.uint8)
        warped = cv2.remap(comp, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        out_frm = np.clip(warped.astype(np.float32) * mult_bgr, 0, 255).astype(np.uint8)
        proc.stdin.write(out_frm.tobytes())

    proc.stdin.close()
    proc.wait()
    cap.release()
    print(f"[DONE] Saved {out_mp4}")


if __name__ == "__main__":
    process_master_video(
        os.path.join(WORK_DIR, "v4A_vet_lipsync_master.mp4"),
        os.path.join(WORK_DIR, "v5A_vet_lipsync_master.mp4")
    )
    process_master_video(
        os.path.join(WORK_DIR, "v4B_vet_lipsync_master.mp4"),
        os.path.join(WORK_DIR, "v5B_vet_lipsync_master.mp4")
    )
