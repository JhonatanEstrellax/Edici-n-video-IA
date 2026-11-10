# -*- coding: utf-8 -*-
r"""
Detecta el rectángulo/cuadrilátero blanco brillante de la pantalla de la MacBook Pro 16" en
`kf1`, `kf2`, `kf3` y `kf4` y proyecta con perspectiva (`cv2.warpPerspective`, LANCZOS4)
las capturas reales 100% legibles de `gestion.mascotamas.com` preservando manos/dedos en primer plano.
"""
import shutil
import pathlib
import cv2
import numpy as np

BASE_DIR = pathlib.Path(r"c:\IA\Edicion de videos")
OUT_DIR = BASE_DIR / "assets" / "avatar_veterinario_hombre_vip" / "spot_dueto_hombre_mujer"
MANUAL_DIR = BASE_DIR / "assets" / "manual_vete_y_marca"
ARTIFACTS_DIR = pathlib.Path(r"C:\Users\Demiante\.gemini\antigravity\brain\56e5cec9-1285-4884-b2c6-a38ac91ed5ae")

UI_ESCRITORIO = str(
    MANUAL_DIR / "00_Secuencias_Paso_a_Paso__01_Recorrido_Completo_App_10_Pantallas__01_Paso_1_Escritorio_y_Resumen_Operativo_del_Dia__04_Raw_Desktop.png"
)
UI_CALENDARIOS = str(
    MANUAL_DIR / "00_Secuencias_Paso_a_Paso__02_Flujo_Calendarios_y_Sena_MercadoPago__02_Paso_2_Modal_Crear_Calendario_Selector_de_4_Modalidades__04_Raw_Desktop.png"
)
UI_HC_PDF = str(
    MANUAL_DIR / "06_Historias_Clinicas_y_Fichas__03_Legajo_Clinico_Digital_y_PDF__01_Modal_Historial_Completo_y_Descarga_PDF__04_Raw_Desktop.png"
)


def find_screen_quad(img, y_min_frac=0.38, y_max_frac=0.90):
    h, w = img.shape[:2]
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    # La pantalla web de MascotaMás es blanca/clara (alta V, baja S) dentro de un bisel negro
    mask = ((hsv[:, :, 2] > 200) & (hsv[:, :, 1] < 45)).astype(np.uint8) * 255
    mask[: int(h * y_min_frac), :] = 0
    mask[int(h * y_max_frac) :, :] = 0
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
    for c in cnts:
        area = cv2.contourArea(c)
        if area < (h * w * 0.015):
            continue
        hull = cv2.convexHull(c)
        peri = cv2.arcLength(hull, True)
        for eps in np.linspace(0.01, 0.08, 25):
            approx = cv2.approxPolyDP(hull, eps * peri, True)
            if len(approx) == 4:
                pts = approx.reshape(4, 2).astype(np.float32)
                s = pts.sum(axis=1)
                d = np.diff(pts, axis=1).reshape(-1)
                ordered = np.array([
                    pts[np.argmin(s)],
                    pts[np.argmin(d)],
                    pts[np.argmax(s)],
                    pts[np.argmax(d)],
                ], dtype=np.float32)
                return ordered
        rect = cv2.minAreaRect(hull)
        box = cv2.boxPoints(rect).astype(np.float32)
        s = box.sum(axis=1)
        d = np.diff(box, axis=1).reshape(-1)
        return np.array([
            box[np.argmin(s)],
            box[np.argmin(d)],
            box[np.argmax(s)],
            box[np.argmax(d)],
        ], dtype=np.float32)
    return None


def warp_ui_onto_screen(kf_path, ui_path, y_min_frac=0.38, y_max_frac=0.90):
    img = cv2.imread(str(kf_path))
    ui = cv2.imread(str(ui_path))
    h, w = img.shape[:2]
    uh, uw = ui.shape[:2]
    quad = find_screen_quad(img, y_min_frac, y_max_frac)
    if quad is None:
        print(f"  [WARN] No se detectó pantalla en {kf_path.name}")
        return
    print(f"  -> {kf_path.name} quad={quad.tolist()}")
    src_pts = np.array([[0, 0], [uw - 1, 0], [uw - 1, uh - 1], [0, uh - 1]], dtype=np.float32)
    M = cv2.getPerspectiveTransform(src_pts, quad)
    warped = cv2.warpPerspective(ui, M, (w, h), flags=cv2.INTER_LANCZOS4)
    poly = np.zeros((h, w), dtype=np.uint8)
    cv2.fillConvexPoly(poly, quad.astype(np.int32), 255)

    # Preservar piel/dedos y teléfono oscuro si cruzan el borde de la pantalla
    ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    Y, Cr, Cb = cv2.split(ycrcb)
    skin = ((Cr > 138) & (Cb < 130) & (Y < 225) & (Y > 40)).astype(np.uint8) * 255
    skin = cv2.dilate(skin, np.ones((5, 5), np.uint8), iterations=2)
    dark_obj = (Y < 90).astype(np.uint8) * 255
    fg_mask = cv2.bitwise_or(skin, dark_obj)
    poly = cv2.bitwise_and(poly, cv2.bitwise_not(fg_mask))

    alpha = cv2.GaussianBlur(poly.astype(np.float32) / 255.0, (3, 3), 0)[..., None]
    out = (warped.astype(np.float32) * alpha + img.astype(np.float32) * (1.0 - alpha)).astype(np.uint8)
    cv2.imwrite(str(kf_path), out)
    shutil.copy2(kf_path, ARTIFACTS_DIR / kf_path.name)


def main():
    warp_ui_onto_screen(OUT_DIR / "kf1_dueto_espalda_macbook_escritorio.png", UI_ESCRITORIO, 0.40, 0.62)
    warp_ui_onto_screen(OUT_DIR / "kf2_dueto_giro_hablando_camara.png", UI_ESCRITORIO, 0.42, 0.62)
    warp_ui_onto_screen(OUT_DIR / "kf3_dueto_operando_turnos_y_hc_macbook.png", UI_CALENDARIOS, 0.42, 0.62)
    warp_ui_onto_screen(OUT_DIR / "kf4_dueto_frente_hero_cta_mascotamas.png", UI_HC_PDF, 0.62, 0.90)


if __name__ == "__main__":
    main()
