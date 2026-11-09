import cv2
import numpy as np

img = cv2.imread(r"c:\IA\Edicion de videos\reels_work\vet_avatar_sexy_v4.png")
h, w, _ = img.shape

u, v = np.meshgrid(
    np.linspace(0.0, 1.0, w, dtype=np.float32),
    np.linspace(0.0, 1.0, h, dtype=np.float32)
)
du = u - 0.50
abs_du = np.abs(du)

# Plateau mask: 1.0 across torso AND arms (|du| < 0.33), smoothly tapering to 0.0 in the blurred bokeh background (|du| = 0.33..0.48)
fg_plateau = np.clip((0.47 - abs_du) / (0.47 - 0.33), 0.0, 1.0)
fg_plateau = fg_plateau * fg_plateau * (3.0 - 2.0 * fg_plateau)

# 1. Plunge ONLY the lower V-neck apex (v = 0.575..0.675) so the neck tendons (v < 0.565) are 100% untouched!
vneck_u_mask = np.exp(-(du / 0.065)**2)
vneck_v_mask = np.exp(-((v - 0.622) / 0.042)**2) * np.clip((v - 0.565) / 0.025, 0.0, 1.0)
delta_v_vneck = -0.046 * vneck_u_mask * vneck_v_mask
delta_u_vneck = np.sign(du) * 0.015 * np.exp(-((abs_du - 0.042) / 0.035)**2) * vneck_v_mask

# 2. Expand 38D Bust Spheres outward & upward (v = 0.57..0.76)
r2_left = ((u - 0.380) / 0.122)**2 + ((v - 0.662) / 0.084)**2
r2_right = ((u - 0.620) / 0.122)**2 + ((v - 0.662) / 0.084)**2
bust_spheres = np.exp(-r2_left) + np.exp(-r2_right)

bust_v_band = np.exp(-((v - 0.662) / 0.080)**2)
# Gate bust outward expansion inside the torso (|du| < 0.25) so arms don't widen at chest level
bust_torso_gate = np.clip((0.275 - abs_du) / (0.275 - 0.215), 0.0, 1.0)
bust_torso_gate = bust_torso_gate * bust_torso_gate * (3.0 - 2.0 * bust_torso_gate)
delta_u_bust = -du * 0.36 * bust_v_band * bust_torso_gate
delta_v_bust = 0.028 * bust_spheres * ((v - 0.652) / 0.080)

# 3. Smooth Hourglass Waist Cinch (v = 0.72..0.93) across fg_plateau so there is ZERO gap tearing!
# Plus extra inward pull on the inner scrub waist (|du| < 0.21) where it won't cross the gap
waist_v_band = np.exp(-((v - 0.822) / 0.080)**2)
waist_v_band *= np.clip((v - 0.705) / 0.045, 0.0, 1.0) * np.clip((0.945 - v) / 0.045, 0.0, 1.0)
inner_scrub_only = np.clip((0.218 - abs_du) / (0.218 - 0.170), 0.0, 1.0)
inner_scrub_only = inner_scrub_only * inner_scrub_only * (3.0 - 2.0 * inner_scrub_only)

delta_u_waist = du * waist_v_band * (0.135 * fg_plateau + 0.095 * inner_scrub_only)

# 4. Subtle hip flare at bottom (v = 0.93..1.00)
hips_v_band = np.exp(-((v - 0.975) / 0.055)**2)
delta_u_hips = -du * 0.11 * hips_v_band * fg_plateau

src_u = u + delta_u_vneck + delta_u_bust + delta_u_waist + delta_u_hips
src_v = v + delta_v_vneck + delta_v_bust

map_x = (src_u * w).astype(np.float32)
map_y = (src_v * h).astype(np.float32)

warped = cv2.remap(img, map_x, map_y, interpolation=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

# 5. Photorealistic 3D Relighting (Anatomical cleavage at bottom of V-neck + 3D 38D scrub volume)
out = warped.astype(np.float32)

# Cleavage starts strictly at the lower V-neck (v = 0.588..0.648) right where the two 38D breasts meet
skin_v_gate = np.clip((v - 0.584) / 0.016, 0.0, 1.0) * np.clip((0.648 - v) / 0.014, 0.0, 1.0)
cleavage_line = np.exp(-((u - 0.50) / 0.0052)**2) * np.exp(-((v - 0.620) / 0.024)**2) * skin_v_gate
left_inner_curve = np.exp(-((u - (0.50 - (0.628 - v)*0.52)) / 0.0072)**2) * np.exp(-((v - 0.604) / 0.014)**2) * skin_v_gate
right_inner_curve = np.exp(-((u - (0.50 + (0.628 - v)*0.52)) / 0.0072)**2) * np.exp(-((v - 0.604) / 0.014)**2) * skin_v_gate
cleavage_shadow = np.clip(cleavage_line * 0.42 + (left_inner_curve + right_inner_curve) * 0.25, 0.0, 0.45)

# Inner-breast skin highlight mounds (warm studio reflection on upper inner curves)
cleavage_hl = (
    np.exp(-((u - 0.474) / 0.016)**2 - ((v - 0.610) / 0.020)**2) +
    np.exp(-((u - 0.526) / 0.016)**2 - ((v - 0.610) / 0.020)**2)
) * 0.18 * skin_v_gate

# 3D Spherical Upper-Breast Highlights on the Scrub Fabric (v = 0.630)
dome_hl = (
    np.exp(-((u - 0.372) / 0.088)**2 - ((v - 0.630) / 0.044)**2) +
    np.exp(-((u - 0.628) / 0.088)**2 - ((v - 0.630) / 0.044)**2)
) * 0.32

# Deep 3D Under-Bust Crescent Shadows (curved arcs under left and right 38D domes)
v_arc_l = 0.742 - 2.3 * (u - 0.380)**2
ub_left = np.exp(-((v - v_arc_l) / 0.019)**2) * np.exp(-((u - 0.380) / 0.094)**2)

v_arc_r = 0.742 - 2.3 * (u - 0.620)**2
ub_right = np.exp(-((v - v_arc_r) / 0.019)**2) * np.exp(-((u - 0.620) / 0.094)**2)

# Center sternal tension shadow between the two breasts on the scrub (u = 0.50, v = 0.67..0.72)
center_dip = np.exp(-((u - 0.50) / 0.022)**2 - ((v - 0.698) / 0.032)**2) * 0.36

# Waist vertical contour shading under the bust
waist_shade = (
    np.exp(-((u - 0.410) / 0.042)**2 - ((v - 0.815) / 0.065)**2) +
    np.exp(-((u - 0.590) / 0.042)**2 - ((v - 0.815) / 0.065)**2)
) * 0.26

fabric_mult = 1.0 + cleavage_hl + dome_hl - (ub_left + ub_right) * 0.55 - center_dip - waist_shade
out[:, :, 0] = out[:, :, 0] * (fabric_mult - cleavage_shadow * 1.15)
out[:, :, 1] = out[:, :, 1] * (fabric_mult - cleavage_shadow * 1.05)
out[:, :, 2] = out[:, :, 2] * (fabric_mult - cleavage_shadow * 0.75)

out = np.clip(out, 0, 255).astype(np.uint8)

out_path = r"c:\IA\Edicion de videos\reels_work\vet_avatar_sexy_v5.png"
cv2.imwrite(out_path, out)
print("Saved seamless plateau-warped vet_avatar_sexy_v5.png:", out_path)
