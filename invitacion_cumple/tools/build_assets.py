"""Genera las capas del personaje listas para animar (PNG RGBA al tamano final):
 - saludo: cuerpo + mano separada (para el saludo con la muneca como pivote)
 - fiesta: pose de baile
 - gato: sticker con contorno blanco
Uso: build_assets.py <cut_dir> <out_dir>"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageFilter, ImageDraw
import numpy as np
from matte import gblur
cut, out = sys.argv[1], sys.argv[2]
meta = {}

def resize_rgba(im, scale):
    w, h = max(1, round(im.width * scale)), max(1, round(im.height * scale))
    return im.convert('RGBa').resize((w, h), Image.LANCZOS).convert('RGBA')

def sharpen(im, radius, percent):
    r, g, b, a = im.split()
    rgb = Image.merge('RGB', (r, g, b)).filter(ImageFilter.UnsharpMask(radius=radius, percent=percent, threshold=1))
    return Image.merge('RGBA', (*rgb.split(), a))

# ---------- SALUDO: separar la mano ----------
sal = Image.open(f'{cut}/saludo.png').convert('RGBA')
sal = sharpen(sal, 2.4, 85)
arr = np.asarray(sal).astype(np.float32)
Hh, Ww = arr.shape[:2]
A = np.array([562.0, 422.0]); B = np.array([601.0, 445.0])           # linea del puno de la manga
mid = (A + B) / 2; d = (B - A) / np.linalg.norm(B - A)
n = np.array([d[1], -d[0]])                                           # normal hacia la mano (arriba-derecha)
yy, xx = np.mgrid[0:Hh, 0:Ww].astype(np.float32)
sd = (xx - mid[0]) * n[0] + (yy - mid[1]) * n[1]                      # distancia con signo a la linea (+ = mano)
along = (xx - mid[0]) * d[0] + (yy - mid[1]) * d[1]
half = np.linalg.norm(B - A) / 2
region = Image.new('L', (Ww, Hh), 0)
ImageDraw.Draw(region).polygon([(556, 300), (Ww, 300), (Ww, 470), (601, 445), (562, 422), (556, 418)], fill=255)
region = np.asarray(region) > 0
hand_w = np.clip(sd + 0.5, 0, 1) * region                             # 1 = mano
base = arr.copy(); base[..., 3] *= (1 - hand_w)
hand = arr.copy(); hand[..., 3] *= hand_w
# munon de muneca oculto bajo la manga (evita huecos al girar la mano)
stub = (sd <= 0.5) & (sd > -20) & (np.abs(along) < half - 2)
sx = mid[0] + along * d[0] + n[0] * 3.0; sy = mid[1] + along * d[1] + n[1] * 3.0
sxi = np.clip(np.round(sx).astype(int), 0, Ww - 1); syi = np.clip(np.round(sy).astype(int), 0, Hh - 1)
src = arr[syi, sxi]
fade = np.clip((20 + sd) / 6.0, 0, 1)
hand = np.where(stub[..., None], np.dstack([src[..., :3], src[..., 3] * fade]), hand)
pivot = mid - n * 5.0
base_im = Image.fromarray(base.round().astype(np.uint8), 'RGBA'); hand_im = Image.fromarray(hand.round().astype(np.uint8), 'RGBA')
meta['saludo'] = {'w': Ww, 'h': Hh, 'anchor': [330, 1316], 'head': [291, 300], 'pivot': [float(pivot[0]), float(pivot[1])]}
for tag, hpx in (('s1', 570), ('peek', 800)):
    s = hpx / Hh
    resize_rgba(base_im, s).save(f'{out}/saludo_base_{tag}.png'); resize_rgba(hand_im, s).save(f'{out}/saludo_hand_{tag}.png')
    meta[f'saludo_{tag}'] = {'scale': s, 'w': round(Ww * s), 'h': round(Hh * s)}

# ---------- FIESTA ----------
fie = Image.open(f'{cut}/fiesta.png').convert('RGBA')
meta['fiesta'] = {'w': fie.width, 'h': fie.height, 'anchor': [232, 1160], 'head': [274, 274]}
for tag, hpx in (('cake', 620), ('disco', 500)):
    s = hpx / fie.height
    resize_rgba(fie, s).save(f'{out}/fiesta_{tag}.png')
    meta[f'fiesta_{tag}'] = {'scale': s, 'w': round(fie.width * s), 'h': round(fie.height * s)}

# ---------- GATO (sticker con contorno blanco) ----------
gat = Image.open(f'{cut}/gato.png').convert('RGBA')
hpx = 405; s = hpx / gat.height
g = resize_rgba(gat, s)
pad = 16
canvas = Image.new('RGBA', (g.width + 2 * pad, g.height + 2 * pad), (0, 0, 0, 0)); canvas.alpha_composite(g, (pad, pad))
a = np.asarray(canvas)[..., 3].astype(np.float32) / 255
# contorno: dilatacion redonda de ~8 px con borde suave
ol = np.clip((gblur(a, 5.0) - 0.035) * 14, 0, 1)
ol = np.clip((gblur(ol, 1.2) - 0.5) * 3 + 0.5, 0, 1)
white = np.dstack([np.full_like(a, 255), np.full_like(a, 255), np.full_like(a, 255), ol * 255]).round().astype(np.uint8)
st = Image.fromarray(white, 'RGBA'); st.alpha_composite(canvas)
st.save(f'{out}/gato_sticker.png')
meta['gato_sticker'] = {'scale': s, 'w': st.width, 'h': st.height, 'pad': pad}
json.dump(meta, open(f'{out}/meta.json', 'w'), indent=1)
print(json.dumps(meta, indent=1))
