"""Mide en el video original lo necesario para integrar al personaje:

  - wipes.json   : frente del barrido diagonal de cada transicion (recta x = a*y + b por cuadro),
                   para que el personaje quede tapado igual que el resto de la escena.
  - circles.json : centro y radio del marco circular de las fotos, cuadro a cuadro
                   (el personaje se asoma por detras y flota junto con la foto).
  - card.json    : borde superior de la tarjeta de direccion (flota lentamente; el personaje baila encima).

Indices de cuadro en base 0. Uso: python analizar_video.py <video.mp4> <dir_salida>
"""
import json
import os
import subprocess
import sys

import numpy as np

W, H, FPS = 1080, 1920, 30
YEL, PUR, TEA = np.array([255, 211, 73]), np.array([127, 62, 223]), np.array([108, 224, 204])
# primer cuadro (base 0) de la fase "tapar" de cada transicion
WIPE_STARTS = {'T1': 104, 'T2': 248, 'T3': 313, 'T4': 393, 'T5': 538, 'T6': 682}


def grab(video, n0, count=1):
    cmd = ['ffmpeg', '-v', 'error', '-ss', f'{n0 / FPS:.5f}', '-i', video, '-frames:v', str(count),
           '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)


def near(fr, col, tol=26):
    return np.abs(fr - col).max(-1) <= tol


def detect_wipes(video):
    f = grab(video, 105)[0].astype(np.int16)
    cand = (f[..., 0] > 225) & (f[..., 1] < 95) & (f[..., 2] > 110) & (f[..., 2] < 200)
    pink_col = np.median(f[cand].reshape(-1, 3), 0)
    res = {}
    for n0 in WIPE_STARTS.values():
        for k, fr in enumerate(grab(video, n0 - 1, 10).astype(np.int16)):
            pink, yel = near(fr, pink_col), near(fr, YEL)
            wipe = pink | yel | near(fr, PUR) | near(fr, TEA)
            pts = []
            for y in range(4, H, 6):
                row = pink[y]
                if not row.any():
                    continue
                d = np.diff(np.concatenate([[0], row.view(np.int8), [0]]))
                for a, b in zip(np.where(d == 1)[0], np.where(d == -1)[0]):       # tramos rosa [a, b)
                    if b - a < 24:
                        continue
                    left_ok = (a <= 3) or yel[y, max(a - 10, 0)]                   # a su izquierda: amarillo o borde
                    right_scene = (b >= W - 1) or (not wipe[y, min(b + 10, W - 1)])  # a su derecha: la escena
                    if left_ok and right_scene and b < W - 1:
                        pts.append((y, b))
            res[n0 - 1 + k] = {'pts': np.array(pts), 'wipe': float(wipe.mean())}
    slopes = []
    for r in res.values():
        p = r['pts']
        if len(p) >= 40:
            a_mat = np.stack([p[:, 0], np.ones(len(p))], 1)
            for _ in range(3):
                co, *_ = np.linalg.lstsq(a_mat, p[:, 1], rcond=None)
                resid = np.abs(a_mat @ co - p[:, 1])
                keep = resid <= max(3.0, np.median(resid) * 3)
                a_mat, p = a_mat[keep], p[keep]
            slopes.append(co[0])
    slope = float(np.median(slopes))
    frames = {}
    for n, r in sorted(res.items()):
        p = r['pts']
        if len(p) >= 6:
            frames[n] = {'a': slope, 'b': float(np.median(p[:, 1] - slope * p[:, 0]))}
        else:
            frames[n] = {'full': r['wipe'] > 0.97, 'none': r['wipe'] < 0.5}
    print(f'  barridos: pendiente dx/dy = {slope:.4f}, {sum("a" in v for v in frames.values())} cuadros con frente')
    return {'slope': slope, 'frames': frames}


def fit_circle(fr, c0, rmin=230, rmax=410):
    cx, cy = c0
    pts = []
    for ang in np.deg2rad(np.arange(0, 360, 2.0)):
        rs = np.arange(rmin, rmax, 0.5)
        xs = np.clip((cx + rs * np.cos(ang)).round().astype(int), 0, W - 1)
        ys = np.clip((cy + rs * np.sin(ang)).round().astype(int), 0, H - 1)
        white = fr[ys, xs].min(-1) >= 243                                         # anillo blanco del marco
        if white.sum() < 6:
            continue
        idx = np.where(white)[0]
        run = max(np.split(idx, np.where(np.diff(idx) > 2)[0] + 1), key=len)
        if 6 <= len(run) <= 60:
            pts.append((ang, rs[run[-1]]))
    pts = np.array(pts)
    x = cx + pts[:, 1] * np.cos(pts[:, 0])
    y = cy + pts[:, 1] * np.sin(pts[:, 0])
    for _ in range(4):
        a_mat = np.stack([2 * x, 2 * y, np.ones_like(x)], 1)
        co, *_ = np.linalg.lstsq(a_mat, x * x + y * y, rcond=None)
        ccx, ccy = co[0], co[1]
        rad = np.sqrt(co[2] + ccx ** 2 + ccy ** 2)
        resid = np.abs(np.hypot(x - ccx, y - ccy) - rad)
        keep = resid < max(1.5, 2.5 * np.median(resid))
        x, y = x[keep], y[keep]
    return float(ccx), float(ccy), float(rad), float(np.median(resid)), int(len(x))


def track_circles(video):
    out = {}
    for name, c0, n0, n1 in (('S2', (540, 518), 126, 256), ('S6', (540, 560), 703, 824)):
        rows, c = [], c0
        for k, fr in enumerate(grab(video, n0, n1 - n0 + 1)):
            try:
                cx, cy, rad, med, npts = fit_circle(fr.astype(np.float32), c)
                ok = med < 1.2 and npts >= 35
            except Exception:
                ok = False
            if ok:
                rows.append([n0 + k, cx, cy, rad])
                c = (cx, cy)
            else:
                rows.append([n0 + k, None, None, None])
        print(f'  marco {name}: {sum(r[1] is not None for r in rows)}/{len(rows)} cuadros')
        out[name] = rows
    return out


def track_card(video, n0=560, n1=690):
    rows = []
    for k, fr in enumerate(grab(video, n0, n1 - n0 + 1)):
        ys = []
        for x in (110, 150, 190, 230, 270, 310, 350):
            lum = fr[560:630, x - 3:x + 4].astype(np.float32).mean((1, 2))
            i = int(np.argmax(lum))
            if i < 3 or i > 66:
                continue
            base = np.median(lum)
            peak = lum[i] - base
            if peak < 35:                                                           # no hay linea de borde clara
                continue
            wgt = np.clip(lum[i - 3:i + 4] - base - 0.25 * peak, 0, None)
            ys.append(560 + (np.arange(i - 3, i + 4) * wgt).sum() / wgt.sum())
        rows.append([n0 + k, float(np.median(ys)) if len(ys) >= 4 else None])
    print(f'  tarjeta: {sum(r[1] is not None for r in rows)}/{len(rows)} cuadros')
    return rows


if __name__ == '__main__':
    video, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    print('Analizando video...')
    json.dump(detect_wipes(video), open(os.path.join(out_dir, 'wipes.json'), 'w'), indent=1)
    json.dump(track_circles(video), open(os.path.join(out_dir, 'circles.json'), 'w'))
    json.dump(track_card(video), open(os.path.join(out_dir, 'card.json'), 'w'))
