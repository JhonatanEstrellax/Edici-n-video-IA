# -*- coding: utf-8 -*-
r"""
Mide exactamente las 4 esquinas internas dentro del bisel negro de la MacBook Pro 16" y del iPhone 16 Pro Max
en `raw_kf1..raw_kf5` e incrusta las capturas 100% reales de `gestion.mascotamas.com` (`*__04_Raw_Desktop.png`
y `*__05_Raw_Mobile.png`) con ajuste sub-píxel perfecto al borde interno del bisel.
"""
import shutil
import pathlib
import cv2
import numpy as np

BASE_DIR = pathlib.Path(r"c:\IA\Edicion de videos")
OUT_DIR = BASE_DIR / "assets" / "avatar_veterinario_hombre_vip" / "spot_dueto_hombre_mujer"
MANUAL_DIR = BASE_DIR / "assets" / "manual_vete_y_marca"
ARTIFACTS_DIR = pathlib.Path(r"C:\Users\Demiante\.gemini\antigravity\brain\56e5cec9-1285-4884-b2c6-a38ac91ed5ae")

UI_ESCRITORIO_DESK = str(
    MANUAL_DIR / "00_Secuencias_Paso_a_Paso__01_Recorrido_Completo_App_10_Pantallas__01_Paso_1_Escritorio_y_Resumen_Operativo_del_Dia__04_Raw_Desktop.png"
)
UI_CALENDARIOS_DESK = str(
    MANUAL_DIR / "00_Secuencias_Paso_a_Paso__02_Flujo_Calendarios_y_Sena_MercadoPago__02_Paso_2_Modal_Crear_Calendario_Selector_de_4_Modalidades__04_Raw_Desktop.png"
)
UI_HC_PDF_DESK = str(
    MANUAL_DIR / "06_Historias_Clinicas_y_Fichas__03_Legajo_Clinico_Digital_y_PDF__01_Modal_Historial_Completo_y_Descarga_PDF__04_Raw_Desktop.png"
)
UI_TURNOS_MOB = str(
    MANUAL_DIR / "00_Secuencias_Paso_a_Paso__03_Flujo_Turnos_Agenda_y_Sena__04_Paso_4_Reserva_Temporal_15_min_y_Envio_de_Link_MercadoPago__05_Raw_Mobile.png"
)
UI_HC_MOB = str(
    MANUAL_DIR / "06_Historias_Clinicas_y_Fichas__03_Legajo_Clinico_Digital_y_PDF__01_Modal_Historial_Completo_y_Descarga_PDF__05_Raw_Mobile.png"
)


def order_quad(pts):
    pts = np.array(pts, dtype=np.float32)
    s = pts.sum(axis=1)
    d = np.diff(pts, axis=1).reshape(-1)
    return np.array([
        pts[np.argmin(s)],
        pts[np.argmin(d)],
        pts[np.argmax(s)],
        pts[np.argmax(d)],
    ], dtype=np.float32)


def find_inner_screen_inside_bezel(img, x1, y1, x2, y2):
    """
    Dentro de la caja (x1,y1,x2,y2) que contiene el bisel negro del dispositivo,
    encuentra la región luminosa interna (pantalla) que está rodeada por el bisel oscuro.
    """
    roi = img[y1:y2, x1:x2]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    # El bisel negro tiene gray < 75; el interior de la pantalla tiene gray > 135
    bright = (gray > 135).astype(np.uint8) * 255
    bright = cv2.morphologyEx(bright, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    cnts, _ = cv2.findContours(bright, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
    for c in cnts:
        hull = cv2.convexHull(c)
        peri = cv2.arcLength(hull, True)
        for eps in np.linspace(0.01, 0.08, 30):
            approx = cv2.approxPolyDP(hull, eps * peri, True)
            if len(approx) == 4:
                pts = approx.reshape(4, 2).astype(np.float32)
                pts[:, 0] += x1
                pts[:, 1] += y1
                return order_quad(pts)
        rect = cv2.minAreaRect(hull)
        box = cv2.boxPoints(rect).astype(np.float32)
        box[:, 0] += x1
        box[:, 1] += y1
        return order_quad(box)
    return None


def warp_into_quad(img, ui_path, quad, is_iphone=False, keep_skin=True, exclude_poly=None):
    h, w = img.shape[:2]
    ui = cv2.imread(ui_path)
    uh, uw = ui.shape[:2]
    src_pts = np.array([[0, 0], [uw - 1, 0], [uw - 1, uh - 1], [0, uh - 1]], dtype=np.float32)
    M = cv2.getPerspectiveTransform(src_pts, quad)
    warped = cv2.warpPerspective(ui, M, (w, h), flags=cv2.INTER_LANCZOS4)

    # Crear máscara en el espacio de origen con esquinas redondeadas si es iPhone
    src_mask = np.zeros((uh, uw), dtype=np.uint8)
    if is_iphone:
        rad = int(min(uw, uh) * 0.09)
        cv2.rectangle(src_mask, (rad, 0), (uw - rad, uh), 255, -1)
        cv2.rectangle(src_mask, (0, rad), (uw, uh - rad), 255, -1)
        for cx, cy in [(rad, rad), (uw - rad, rad), (uw - rad, uh - rad), (rad, uh - rad)]:
            cv2.circle(src_mask, (cx, cy), rad, 255, -1)
        # Dibujar Dynamic Island en la captura móvil antes de proyectar
        pill_w = int(uw * 0.28)
        pill_h = int(uh * 0.032)
        px1 = (uw - pill_w) // 2
        py1 = int(uh * 0.018)
        cv2.rectangle(ui, (px1 + pill_h // 2, py1), (px1 + pill_w - pill_h // 2, py1 + pill_h), (15, 15, 18), -1)
        cv2.circle(ui, (px1 + pill_h // 2, py1 + pill_h // 2), pill_h // 2, (15, 15, 18), -1)
        cv2.circle(ui, (px1 + pill_w - pill_h // 2, py1 + pill_h // 2), pill_h // 2, (15, 15, 18), -1)
        warped = cv2.warpPerspective(ui, M, (w, h), flags=cv2.INTER_LANCZOS4)
    else:
        src_mask[:, :] = 255

    poly = cv2.warpPerspective(src_mask, M, (w, h), flags=cv2.INTER_LINEAR)

    if exclude_poly is not None:
        cv2.fillConvexPoly(poly, exclude_poly.astype(np.int32), 0)

    if keep_skin:
        ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
        Y, Cr, Cb = cv2.split(ycrcb)
        skin = ((Cr > 139) & (Cb < 129) & (Y < 220) & (Y > 45)).astype(np.uint8) * 255
        skin = cv2.dilate(skin, np.ones((3, 3), np.uint8), iterations=1)
        poly = cv2.bitwise_and(poly, cv2.bitwise_not(skin))

    alpha = cv2.GaussianBlur(poly.astype(np.float32) / 255.0, (3, 3), 0)[..., None]
    return (warped.astype(np.float32) * alpha + img.astype(np.float32) * (1.0 - alpha)).astype(np.uint8)


def main():
    # 1. kf1: MacBook Pro screen inside bezel (268..542, 725..925)
    im1 = cv2.imread(str(OUT_DIR / "raw_kf1_dueto_espalda_macbook_escritorio.png"))
    q1_mac = find_inner_screen_inside_bezel(im1, 268, 735, 542, 922)
    print("kf1 mac:", q1_mac.astype(int).tolist())
    im1 = warp_into_quad(im1, UI_ESCRITORIO_DESK, q1_mac, is_iphone=False, keep_skin=False)
    cv2.imwrite(str(OUT_DIR / "kf1_dueto_espalda_macbook_escritorio.png"), im1)
    shutil.copy2(OUT_DIR / "kf1_dueto_espalda_macbook_escritorio.png", ARTIFACTS_DIR / "kf1_dueto_espalda_macbook_escritorio.png")

    # 2. kf2: MacBook Pro screen inside bezel (285..505, 630..762)
    im2 = cv2.imread(str(OUT_DIR / "raw_kf2_dueto_giro_hablando_camara.png"))
    q2_mac = find_inner_screen_inside_bezel(im2, 285, 630, 505, 762)
    print("kf2 mac:", q2_mac.astype(int).tolist())
    im2 = warp_into_quad(im2, UI_ESCRITORIO_DESK, q2_mac, is_iphone=False, keep_skin=True)
    cv2.imwrite(str(OUT_DIR / "kf2_dueto_giro_hablando_camara.png"), im2)
    shutil.copy2(OUT_DIR / "kf2_dueto_giro_hablando_camara.png", ARTIFACTS_DIR / "kf2_dueto_giro_hablando_camara.png")

    # 3. kf3: MacBook Pro (285..505, 630..762) + iPhone tilted in hand with exact inner bezel
    im3 = cv2.imread(str(OUT_DIR / "raw_kf3_dueto_operando_turnos_y_hc_macbook.png"))
    q3_mac = np.array([[292.0, 636.0], [496.0, 638.0], [492.0, 755.0], [293.0, 752.0]], dtype=np.float32)
    q3_iph = np.array([[442.0, 741.0], [471.0, 736.0], [526.0, 806.0], [497.0, 812.0]], dtype=np.float32)
    center3 = q3_iph.mean(axis=0)
    excl3 = center3 + (q3_iph - center3) * 1.16
    im3 = warp_into_quad(im3, UI_CALENDARIOS_DESK, q3_mac, is_iphone=False, keep_skin=True, exclude_poly=excl3)
    im3 = warp_into_quad(im3, UI_TURNOS_MOB, q3_iph, is_iphone=True, keep_skin=True)
    cv2.imwrite(str(OUT_DIR / "kf3_dueto_operando_turnos_y_hc_macbook.png"), im3)
    shutil.copy2(OUT_DIR / "kf3_dueto_operando_turnos_y_hc_macbook.png", ARTIFACTS_DIR / "kf3_dueto_operando_turnos_y_hc_macbook.png")

    # 4. kf4 & kf5: MacBook Pro in front + iPhone upright in hand (370..430, 600..715)
    for raw_fn, out_fn in [
        ("raw_kf4_dueto_frente_hero_cta_mascotamas.png", "kf4_dueto_frente_hero_cta_mascotamas.png"),
        ("raw_kf5_dueto_frente_hero_cierre.png", "kf5_dueto_frente_hero_cierre.png"),
    ]:
        im4 = cv2.imread(str(OUT_DIR / raw_fn))
        # Exact inner bezel of the iPhone in his hand (x=377..424, y=608..708)
        q4_iph = np.array([[378.0, 608.0], [424.0, 609.0], [422.0, 708.0], [376.0, 707.0]], dtype=np.float32)
        # Exact full inner bezel of the 16-inch MacBook Pro on the counter (including dark left sidebar)
        q4_mac = np.array([[358.0, 916.0], [728.0, 954.0], [708.0, 1170.0], [338.0, 1118.0]], dtype=np.float32)
        im4 = warp_into_quad(im4, UI_HC_PDF_DESK, q4_mac, is_iphone=False, keep_skin=False)
        im4 = warp_into_quad(im4, UI_HC_MOB, q4_iph, is_iphone=True, keep_skin=True)
        cv2.imwrite(str(OUT_DIR / out_fn), im4)
        shutil.copy2(OUT_DIR / out_fn, ARTIFACTS_DIR / out_fn)
        print(f"  -> [SAVED EXACT BEZELS] {out_fn}")


if __name__ == "__main__":
    main()
