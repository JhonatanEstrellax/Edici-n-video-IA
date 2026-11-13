"""Recorta al personaje de las tres imagenes de referencia y genera PNG con transparencia.

Solo usa numpy + Pillow (sin modelos de IA):
  - saludo.jpg : fondo lila degradado  -> modelo polinomico del fondo + clave por color
  - gato.jpg   : ilustracion sobre blanco (captura con margenes grises) -> inundacion desde el borde
  - fiesta.jpg : fondo de fiesta desenfocado -> barrera de bordes nitidos + inundacion del fondo

Uso: python recortar_personaje.py <dir_originales> <dir_recortes>
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from matte import dilate, estimate_bg, gblur, open_mask, projection_matte, smooth_alpha


def _flood_outside(free):
    """Devuelve la zona de `free` (bool) conectada con el borde de la imagen."""
    h, w = free.shape
    pad = Image.new('L', (w + 2, h + 2), 255)
    pad.paste(Image.fromarray(free.astype(np.uint8) * 255), (1, 1))
    ImageDraw.floodfill(pad, (0, 0), 64)
    return np.asarray(pad)[1:-1, 1:-1] == 64


def _component(mask, seed):
    """Componente conexa de `mask` que contiene `seed` (x, y)."""
    im = Image.fromarray(mask.astype(np.uint8) * 255).copy()
    assert im.getpixel(seed) == 255, 'la semilla no cae sobre el personaje'
    ImageDraw.floodfill(im, seed, 128)
    return np.asarray(im) == 128


def _save_cropped(rgba, path, pad=6):
    ys, xs = np.where(rgba[..., 3] > 8)
    h, w = rgba.shape[:2]
    box = (max(xs.min() - pad, 0), max(ys.min() - pad, 0), min(xs.max() + pad + 1, w), min(ys.max() + pad + 1, h))
    im = Image.fromarray(rgba, 'RGBA').crop(box)
    im.save(path)
    print(f'  {os.path.basename(path)}: {im.size[0]}x{im.size[1]} (recorte {tuple(int(v) for v in box)})')


def recortar_saludo(src, out):
    rgb = np.asarray(Image.open(src).convert('RGB')).astype(np.float32)
    h, w, _ = rgb.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    xn, yn = xx / w - 0.5, yy / h - 0.5
    basis = np.stack([np.ones_like(xn), xn, yn, xn * xn, yn * yn, xn * yn, xn ** 3, yn ** 3, xn * xn * yn, xn * yn * yn,
                      xn ** 4, yn ** 4, xn * xn * yn * yn], -1)
    # fondo: polinomio ajustado iterativamente a los pixeles lilas
    mask_bg = np.linalg.norm(rgb - np.array([190, 152, 195], np.float32), axis=-1) < 38
    for _ in range(4):
        a = basis[mask_bg][::7]
        bg = np.zeros_like(rgb)
        for c in range(3):
            coef, *_ = np.linalg.lstsq(a, rgb[..., c][mask_bg][::7], rcond=None)
            bg[..., c] = basis @ coef
        dist = np.linalg.norm(rgb - bg, axis=-1)
        mask_bg = dist < 14
    hard = Image.fromarray(((dist > 20) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))
    comp = _component(np.asarray(hard) > 127, (int(w * 0.50), int(h * 0.45)))
    solid = ~_flood_outside(~comp)                       # rellena huecos interiores
    rgba = smooth_alpha(projection_matte(rgb, bg, solid), sigma=1.3, gain=2.0, choke=0.10)
    _save_cropped(rgba, out)


def recortar_gato(src, out):
    full = np.asarray(Image.open(src).convert('RGB')).astype(np.float32)
    # panel blanco de la captura: se descartan los margenes grises (244,245,247)
    gray = np.abs(full - np.array([244, 245, 247], np.float32)).max(-1) <= 2.5
    inner = np.where(gray[100:1250].mean(0) < 0.02)[0]
    x0, x1 = inner.min() + 2, inner.max() - 1
    rows = np.where(gray[:, :60].mean(1) > 0.9)[0]
    y0, y1 = rows.min() + 2, rows.max() - 1
    rgb = full[y0:y1, x0:x1]
    h, w, _ = rgb.shape
    bg = np.full_like(rgb, 255.0)
    notbg = Image.fromarray(((rgb.min(-1) < 243) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))
    outside = _flood_outside(np.asarray(notbg) == 0)
    solid = _component(~outside, (int(w * 0.45), int(h * 0.45)))
    rgba = projection_matte(rgb, bg, solid, core_erode=3, band=4, spread=3.0)
    rgba[:, :3, 3] = 0                                   # resto del margen de la captura
    rgba = smooth_alpha(rgba, sigma=0.8, gain=1.8, choke=0.05)
    _save_cropped(rgba, out)


def recortar_fiesta(src, out, thr=9.0):
    rgb = np.asarray(Image.open(src).convert('RGB')).astype(np.float32)
    h, w, _ = rgb.shape
    sm = np.stack([gblur(rgb[..., c], 0.8) for c in range(3)], -1)
    gx = np.zeros_like(sm)
    gy = np.zeros_like(sm)
    gx[:, 1:-1] = (sm[:, 2:] - sm[:, :-2]) / 2
    gy[1:-1, :] = (sm[2:, :] - sm[:-2, :]) / 2
    edge = np.sqrt((gx ** 2 + gy ** 2).sum(-1)) > thr    # el personaje es lo unico nitido
    reached = _flood_outside(~dilate(edge, 2))
    solid = _component(~dilate(reached, 2), (400, 700))
    solid = _component(open_mask(solid, 3), (400, 700))  # quita hilos finos pegados
    # residuos del fondo (arco iris junto a la oreja, sombra del piso junto al zapato)
    remove = [[(410, 175), (560, 175), (560, 200), (548, 204), (538, 209), (530, 215), (524, 222), (410, 222)],
              [(586, 205), (610, 205), (610, 228), (590, 228)],
              [(327, 192), (345, 192), (345, 207), (334, 207), (327, 200)],
              [(285, 1284), (309, 1284), (309, 1300), (285, 1300)],
              [(285, 1312), (312, 1312), (312, 1332), (285, 1332)]]
    rm = Image.new('L', (w, h), 0)
    for poly in remove:
        ImageDraw.Draw(rm).polygon(poly, fill=255)
    solid &= ~(np.asarray(rm) > 0)
    rgba = smooth_alpha(projection_matte(rgb, estimate_bg(rgb, solid), solid, core_erode=3, band=4, spread=3.0))
    _save_cropped(rgba, out)


if __name__ == '__main__':
    src_dir, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    print('Recortando personaje...')
    recortar_saludo(os.path.join(src_dir, 'saludo.jpg'), os.path.join(out_dir, 'saludo.png'))
    recortar_gato(os.path.join(src_dir, 'gato.jpg'), os.path.join(out_dir, 'gato.png'))
    recortar_fiesta(os.path.join(src_dir, 'fiesta.jpg'), os.path.join(out_dir, 'fiesta.png'))
