"""Utilidades de mate: desenfoque gaussiano separable, alfa por proyeccion y
descontaminacion de color. Solo numpy + Pillow."""
from PIL import Image, ImageFilter
import numpy as np

def gblur(a, sigma):
    r = max(1, int(round(sigma * 3)))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2).astype(np.float32)
    k /= k.sum()
    def pass1(x, axis):
        pad = [(0, 0)] * x.ndim
        pad[axis] = (r, r)
        xp = np.pad(x, pad, mode='edge')
        out = np.zeros_like(x)
        n = x.shape[axis]
        for i, w in enumerate(k):
            sl = [slice(None)] * x.ndim
            sl[axis] = slice(i, i + n)
            out += w * xp[tuple(sl)]
        return out
    return pass1(pass1(a.astype(np.float32), 0), 1)

def erode(mask, px):
    im = Image.fromarray(mask.astype(np.uint8) * 255)
    for _ in range(px):
        im = im.filter(ImageFilter.MinFilter(3))
    return np.asarray(im) > 127

def dilate(mask, px):
    im = Image.fromarray(mask.astype(np.uint8) * 255)
    for _ in range(px):
        im = im.filter(ImageFilter.MaxFilter(3))
    return np.asarray(im) > 127

def projection_matte(rgb, bg, solid, core_erode=4, band=5, spread=4.0):
    """rgb,bg: float32 HxWx3; solid: bool mascara dura. Devuelve RGBA uint8."""
    core = erode(solid, core_erode)                    # primer plano seguro
    reach = dilate(solid, band)                        # limite exterior del borde
    # color de primer plano extendido hacia fuera (desenfoque normalizado, 2 escalas)
    F = np.zeros_like(rgb); wsum = np.zeros(rgb.shape[:2], np.float32)
    for s, wgt in ((spread, 1.0), (spread * 3, 0.02)):
        m = gblur(core.astype(np.float32), s)
        c = np.stack([gblur(rgb[..., i] * core, s) for i in range(3)], -1)
        F += wgt * c; wsum += wgt * m
    F = F / np.maximum(wsum, 1e-5)[..., None]
    F = np.where(core[..., None], rgb, F)
    d = F - bg
    den = np.maximum((d * d).sum(-1), 30.0 ** 2)       # evita division inestable
    alpha = ((rgb - bg) * d).sum(-1) / den
    alpha = np.clip(alpha, 0, 1)
    alpha = np.where(core, 1.0, alpha)
    alpha = np.where(reach, alpha, 0.0)
    # contraste suave del borde para eliminar velo del fondo
    alpha = np.clip((alpha - 0.12) / (0.92 - 0.12), 0, 1)
    alpha = np.where(core, 1.0, alpha)
    a3 = alpha[..., None]
    decont = (rgb - (1 - a3) * bg) / np.maximum(a3, 0.25)
    decont = np.clip(decont, 0, 255)
    out_rgb = np.where(core[..., None], rgb, a3 * decont + (1 - a3) * F)
    out = np.dstack([np.clip(out_rgb, 0, 255), alpha * 255]).round().astype(np.uint8)
    return out

def estimate_bg(rgb, solid, gap=6, sigma=7.0):
    """Fondo local estimado propagando hacia dentro los colores exteriores."""
    outside = ~dilate(solid, gap)
    B = np.zeros_like(rgb); wsum = np.zeros(rgb.shape[:2], np.float32)
    for s, wgt in ((sigma, 1.0), (sigma * 3, 0.03), (sigma * 9, 0.001)):
        m = gblur(outside.astype(np.float32), s)
        c = np.stack([gblur(rgb[..., i] * outside, s) for i in range(3)], -1)
        B += wgt * c; wsum += wgt * m
    B = B / np.maximum(wsum, 1e-6)[..., None]
    return np.where(outside[..., None], rgb, B)

def open_mask(solid, px):
    return dilate(erode(solid, px), px) & solid

def smooth_alpha(rgba, sigma=1.0, gain=1.8, choke=0.06):
    """Suaviza el contorno (quita dientes de sierra) y lo contrae levemente."""
    a = rgba[..., 3].astype(np.float32) / 255
    b = gblur(a, sigma)
    b = np.clip((b - 0.5 - choke) * gain + 0.5, 0, 1)
    out = rgba.copy(); out[..., 3] = (b * 255).round().astype(np.uint8)
    return out
