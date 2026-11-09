import cv2
import numpy as np

# Load reference frame 0 (1080x1920)
cap = cv2.VideoCapture(r"c:\IA\Edicion de videos\reels_work\v4A_vet_lipsync_master.mp4")
ret, frame0 = cap.read()
h, w, _ = frame0.shape

# Build background mask for rigid camera zoom estimation (exclude the person: u in [0.18..0.82], v in [0.18..1.0])
bg_mask = np.ones((h, w), dtype=np.uint8) * 255
bg_mask[int(0.18*h):, int(0.16*w):int(0.84*w)] = 0

gray0 = cv2.cvtColor(frame0, cv2.COLOR_BGR2GRAY)
pts0 = cv2.goodFeaturesToTrack(gray0, maxCorners=600, qualityLevel=0.01, minDistance=12, mask=bg_mask)

# Template for torso tracking on unzoomed frame: the "VETERINARIA PALERMO" embroidery + V-neck collar (v=0.52..0.70, u=0.36..0.72)
t_y0, t_y1 = int(0.54 * h), int(0.70 * h)
t_x0, t_x1 = int(0.38 * w), int(0.72 * w)
torso_tmpl = gray0[t_y0:t_y1, t_x0:t_x1].copy()

# Precompute base normalized grids (1080x1920)
u_base, v_base = np.meshgrid(
    np.linspace(0.0, 1.0, w, dtype=np.float32),
    np.linspace(0.0, 1.0, h, dtype=np.float32)
)

def apply_38d_sculpt(img_bgr: np.ndarray, du_shift: float = 0.0, dv_shift: float = 0.0) -> np.ndarray:
    u = u_base - du_shift
    v = v_base - dv_shift
    du = u - 0.50
    abs_du = np.abs(du)

    fg_plateau = np.clip((0.47 - abs_du) / (0.47 - 0.33), 0.0, 1.0)
    fg_plateau = fg_plateau * fg_plateau * (3.0 - 2.0 * fg_plateau)

    # 1. Plunge lower V-neck apex
    vneck_u_mask = np.exp(-(du / 0.065)**2)
    vneck_v_mask = np.exp(-((v - 0.622) / 0.042)**2) * np.clip((v - 0.565) / 0.025, 0.0, 1.0)
    delta_v_vneck = -0.046 * vneck_u_mask * vneck_v_mask
    delta_u_vneck = np.sign(du) * 0.015 * np.exp(-((abs_du - 0.042) / 0.035)**2) * vneck_v_mask

    # 2. Expand 38D Bust Spheres outward & upward
    r2_left = ((u - 0.380) / 0.122)**2 + ((v - 0.662) / 0.084)**2
    r2_right = ((u - 0.620) / 0.122)**2 + ((v - 0.662) / 0.084)**2
    bust_spheres = np.exp(-r2_left) + np.exp(-r2_right)

    bust_v_band = np.exp(-((v - 0.662) / 0.080)**2)
    bust_torso_gate = np.clip((0.275 - abs_du) / (0.275 - 0.215), 0.0, 1.0)
    bust_torso_gate = bust_torso_gate * bust_torso_gate * (3.0 - 2.0 * bust_torso_gate)
    delta_u_bust = -du * 0.36 * bust_v_band * bust_torso_gate
    delta_v_bust = 0.028 * bust_spheres * ((v - 0.652) / 0.080)

    # 3. Smooth Hourglass Waist Cinch
    waist_v_band = np.exp(-((v - 0.822) / 0.080)**2)
    waist_v_band *= np.clip((v - 0.705) / 0.045, 0.0, 1.0) * np.clip((0.945 - v) / 0.045, 0.0, 1.0)
    inner_scrub_only = np.clip((0.218 - abs_du) / (0.218 - 0.170), 0.0, 1.0)
    inner_scrub_only = inner_scrub_only * inner_scrub_only * (3.0 - 2.0 * inner_scrub_only)
    delta_u_waist = du * waist_v_band * (0.135 * fg_plateau + 0.095 * inner_scrub_only)

    # 4. Subtle hip flare
    hips_v_band = np.exp(-((v - 0.975) / 0.055)**2)
    delta_u_hips = -du * 0.11 * hips_v_band * fg_plateau

    src_u = u_base + delta_u_vneck + delta_u_bust + delta_u_waist + delta_u_hips
    src_v = v_base + delta_v_vneck + delta_v_bust

    map_x = (src_u * w).astype(np.float32)
    map_y = (src_v * h).astype(np.float32)
    warped = cv2.remap(img_bgr, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

    # 5. 3D Relighting
    out = warped.astype(np.float32)
    skin_v_gate = np.clip((v - 0.584) / 0.016, 0.0, 1.0) * np.clip((0.648 - v) / 0.014, 0.0, 1.0)
    cleavage_line = np.exp(-((u - 0.50) / 0.0052)**2) * np.exp(-((v - 0.620) / 0.024)**2) * skin_v_gate
    left_inner_curve = np.exp(-((u - (0.50 - (0.628 - v)*0.52)) / 0.0072)**2) * np.exp(-((v - 0.604) / 0.014)**2) * skin_v_gate
    right_inner_curve = np.exp(-((u - (0.50 + (0.628 - v)*0.52)) / 0.0072)**2) * np.exp(-((v - 0.604) / 0.014)**2) * skin_v_gate
    cleavage_shadow = np.clip(cleavage_line * 0.42 + (left_inner_curve + right_inner_curve) * 0.25, 0.0, 0.45)

    cleavage_hl = (
        np.exp(-((u - 0.474) / 0.016)**2 - ((v - 0.610) / 0.020)**2) +
        np.exp(-((u - 0.526) / 0.016)**2 - ((v - 0.610) / 0.020)**2)
    ) * 0.18 * skin_v_gate

    dome_hl = (
        np.exp(-((u - 0.372) / 0.088)**2 - ((v - 0.630) / 0.044)**2) +
        np.exp(-((u - 0.628) / 0.088)**2 - ((v - 0.630) / 0.044)**2)
    ) * 0.32

    v_arc_l = 0.742 - 2.3 * (u - 0.380)**2
    ub_left = np.exp(-((v - v_arc_l) / 0.019)**2) * np.exp(-((u - 0.380) / 0.094)**2)
    v_arc_r = 0.742 - 2.3 * (u - 0.620)**2
    ub_right = np.exp(-((v - v_arc_r) / 0.019)**2) * np.exp(-((u - 0.620) / 0.094)**2)

    center_dip = np.exp(-((u - 0.50) / 0.022)**2 - ((v - 0.698) / 0.032)**2) * 0.36
    waist_shade = (
        np.exp(-((u - 0.410) / 0.042)**2 - ((v - 0.815) / 0.065)**2) +
        np.exp(-((u - 0.590) / 0.042)**2 - ((v - 0.815) / 0.065)**2)
    ) * 0.26

    fabric_mult = 1.0 + cleavage_hl + dome_hl - (ub_left + ub_right) * 0.55 - center_dip - waist_shade
    out[:, :, 0] = out[:, :, 0] * (fabric_mult - cleavage_shadow * 1.15)
    out[:, :, 1] = out[:, :, 1] * (fabric_mult - cleavage_shadow * 1.05)
    out[:, :, 2] = out[:, :, 2] * (fabric_mult - cleavage_shadow * 0.75)

    return np.clip(out, 0, 255).astype(np.uint8)

white_mask = np.ones((h, w), dtype=np.float32)
# Feather the outer 65px border of the unzoomed frame so it blends invisibly into frame0
margin = 75
for i in range(margin):
    val = 0.5 * (1.0 - np.cos(np.pi * i / float(margin)))
    white_mask[i, :] = np.minimum(white_mask[i, :], val)
    white_mask[h - 1 - i, :] = np.minimum(white_mask[h - 1 - i, :], val)
    white_mask[:, i] = np.minimum(white_mask[:, i], val)
    white_mask[:, w - 1 - i] = np.minimum(white_mask[:, w - 1 - i], val)

for sec in [0, 2, 5, 10, 15, 20, 25]:
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(sec * 30))
    ret, frm = cap.read()
    if not ret:
        continue
    gray = cv2.cvtColor(frm, cv2.COLOR_BGR2GRAY)
    pts1, st, _ = cv2.calcOpticalFlowPyrLK(gray0, gray, pts0, None, winSize=(31, 31), maxLevel=4)
    good0 = pts0[st.flatten() == 1]
    good1 = pts1[st.flatten() == 1]
    # Estimate pure similarity (scale + translation, no rotation) from frame0 -> frm
    # Fit x1 = s * x0 + tx, y1 = s * y0 + ty via RANSAC / median
    M, inliers = cv2.estimateAffinePartial2D(good1, good0, method=cv2.RANSAC, ransacReprojThreshold=3.0)
    scale_inv = np.sqrt(M[0, 0]**2 + M[0, 1]**2)
    print(f"sec={sec}s: unzoom scale_inv={scale_inv:.4f} (camera zoom={1.0/scale_inv:.3f}x)")

    unzoomed = cv2.warpAffine(frm, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    alpha = cv2.warpAffine(white_mask, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0.0)

    # Track torso subtle offset in unzoomed frame
    unzoomed_gray = cv2.cvtColor(unzoomed, cv2.COLOR_BGR2GRAY)
    search_margin = 40
    s_y0 = max(0, t_y0 - search_margin)
    s_y1 = min(h, t_y1 + search_margin)
    s_x0 = max(0, t_x0 - search_margin)
    s_x1 = min(w, t_x1 + search_margin)
    res = cv2.matchTemplate(unzoomed_gray[s_y0:s_y1, s_x0:s_x1], torso_tmpl, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)
    dx_px = (s_x0 + max_loc[0]) - t_x0
    dy_px = (s_y0 + max_loc[1]) - t_y0
    print(f"  torso match={max_val:.3f}, dx={dx_px}px, dy={dy_px}px")

    # Shift frame0 slightly at the bottom (v > 0.72) by (dx_px, dy_px) so lower pockets align with unzoomed torso!
    M_torso = np.float32([[1, 0, dx_px], [0, 1, dy_px]])
    frame0_torso = cv2.warpAffine(frame0, M_torso, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    # Use frame0_torso in the lower center (u in [0.18..0.82], v > 0.65) and static frame0 in the outer background
    lower_fg_mask = np.clip((u_base - 0.18)/0.05, 0, 1) * np.clip((0.82 - u_base)/0.05, 0, 1) * np.clip((v_base - 0.65)/0.08, 0, 1)
    base_canvas = frame0.astype(np.float32) * (1.0 - lower_fg_mask[:, :, None]) + frame0_torso.astype(np.float32) * lower_fg_mask[:, :, None]

    composited = (unzoomed.astype(np.float32) * alpha[:, :, None] + base_canvas * (1.0 - alpha[:, :, None])).astype(np.uint8)
    sculpted = apply_38d_sculpt(composited, du_shift=dx_px / float(w), dv_shift=dy_px / float(h))
    cv2.imwrite(rf"c:\IA\Edicion de videos\reels_work\test_v5_frame_{sec}s.jpg", sculpted)
