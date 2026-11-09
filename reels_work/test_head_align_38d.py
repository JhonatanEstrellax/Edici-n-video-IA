import cv2
import numpy as np

cap = cv2.VideoCapture(r"c:\IA\Edicion de videos\reels_work\v4A_vet_lipsync_master.mp4")
ret, frame0 = cap.read()
h, w, _ = frame0.shape
gray0 = cv2.cvtColor(frame0, cv2.COLOR_BGR2GRAY)

# Reference template on frame0: upper head, hair crown, forehead, eyes, and nose bridge
# (v = 0.22..0.40, u = 0.31..0.69) — rigid part of the head unaffected by mouth opening!
hy0, hy1 = int(0.22 * h), int(0.41 * h)
hx0, hx1 = int(0.31 * w), int(0.69 * w)
head_tmpl0 = gray0[hy0:hy1, hx0:hx1].copy()
th, tw = head_tmpl0.shape

# Also build the soft elliptical feather mask for the live head + face + upper neck + hair waves
# Covers u = 0.25..0.75, v = 0.18..0.505, with smooth cosine feather
u_grid, v_grid = np.meshgrid(
    np.linspace(0.0, 1.0, w, dtype=np.float32),
    np.linspace(0.0, 1.0, h, dtype=np.float32)
)

# Elliptical head+face mask centered at u=0.50, v=0.355 with radii ru=0.22, rv=0.145
r_head = np.sqrt(((u_grid - 0.50) / 0.215)**2 + ((v_grid - 0.355) / 0.148)**2)
head_mask = np.clip((1.18 - r_head) / (1.18 - 0.72), 0.0, 1.0)
head_mask = head_mask * head_mask * (3.0 - 2.0 * head_mask)
# Strictly zero out below v = 0.515 so it never touches the V-neck cleavage or stethoscope
v_cut = np.clip((0.512 - v_grid) / (0.512 - 0.478), 0.0, 1.0)
v_cut = v_cut * v_cut * (3.0 - 2.0 * v_cut)
head_mask = (head_mask * v_cut)[:, :, None]

from test_unzoom_and_sculpt import apply_38d_sculpt

def align_head_to_frame0(frm_bgr: np.ndarray):
    gray = cv2.cvtColor(frm_bgr, cv2.COLOR_BGR2GRAY)
    # Coarse-to-fine scale search: in frm_bgr, the head is scaled by s in [0.98 .. 1.32] relative to frame0
    best_score = -1.0
    best_s = 1.0
    best_loc = (hx0, hy0)

    # Coarse step
    for s in np.linspace(0.98, 1.32, 35):
        # If we downscale frm_bgr by 1/s, the head in frm_bgr becomes the same size as head_tmpl0
        inv_s = 1.0 / s
        sh, sw = int(round(h * inv_s)), int(round(w * inv_s))
        small = cv2.resize(gray, (sw, sh), interpolation=cv2.INTER_AREA)
        if sh < th + 10 or sw < tw + 10:
            continue
        res = cv2.matchTemplate(small, head_tmpl0, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        if max_val > best_score:
            best_score = max_val
            best_s = s
            best_loc = max_loc

    # Fine step around best_s
    for s in np.linspace(max(0.96, best_s - 0.025), min(1.36, best_s + 0.025), 25):
        inv_s = 1.0 / s
        sh, sw = int(round(h * inv_s)), int(round(w * inv_s))
        small = cv2.resize(gray, (sw, sh), interpolation=cv2.INTER_LINEAR)
        res = cv2.matchTemplate(small, head_tmpl0, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        if max_val > best_score:
            best_score = max_val
            best_s = s
            best_loc = max_loc

    # Sub-pixel / affine refinement: in the downscaled image (scale = 1/best_s),
    # top-left of template is at best_loc = (lx, ly), and we want it at (hx0, hy0) in frame0!
    inv_s = 1.0 / best_s
    tx = hx0 - best_loc[0]
    ty = hy0 - best_loc[1]
    # So mapping from frm_bgr (x, y) -> frame0 (x0, y0) is:
    # x0 = x * inv_s + tx
    # y0 = y * inv_s + ty
    M = np.float32([
        [inv_s, 0.0, tx],
        [0.0, inv_s, ty]
    ])
    aligned = cv2.warpAffine(frm_bgr, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return aligned, best_s, tx, ty, best_score

for sec in [0, 2, 5, 10, 15, 20, 25]:
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(sec * 30))
    ret, frm = cap.read()
    if not ret:
        continue
    aligned_head, s, tx, ty, score = align_head_to_frame0(frm)
    print(f"sec={sec}s: head_scale={s:.4f}, tx={tx:.1f}, ty={ty:.1f}, match={score:.4f}")

    # Color/exposure match on the neck/cheeks transition zone so skin brightness matches frame0 100%
    comp = (aligned_head.astype(np.float32) * head_mask + frame0.astype(np.float32) * (1.0 - head_mask)).astype(np.uint8)
    sculpted = apply_38d_sculpt(comp)
    cv2.imwrite(rf"c:\IA\Edicion de videos\reels_work\test_v5_frame_{sec}s.jpg", sculpted)
