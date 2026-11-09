import os
import glob
import shutil
import urllib.request
import numpy as np
from PIL import Image

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS_DIR = os.path.join(BASE_DIR, "fonts")
ASSETS_DIR = os.path.join(BASE_DIR, "assets", "mascotamas")
WEB_PUBLIC_DIR = r"C:\IA\MascotaMas-WEB\public"

os.makedirs(FONTS_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)

GOOGLE_FONTS = [
    (
        "Poppins-ExtraBold.ttf",
        "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-ExtraBold.ttf",
    ),
    (
        "Poppins-Bold.ttf",
        "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf",
    ),
    (
        "Poppins-SemiBold.ttf",
        "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-SemiBold.ttf",
    ),
    (
        "OpenSans-Bold.ttf",
        "https://github.com/google/fonts/raw/main/ofl/opensans/OpenSans%5Bwdth%2Cwght%5D.ttf",
    ),
]


def download_fonts():
    for fname, url in GOOGLE_FONTS:
        dest = os.path.join(FONTS_DIR, fname)
        if os.path.exists(dest) and os.path.getsize(dest) > 10000:
            print(f"[OK] Font already exists: {fname}")
            continue
        print(f"[DOWNLOAD] Downloading {fname} from {url} ...")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as resp, open(dest, "wb") as out:
            out.write(resp.read())
        print(f"[OK] Saved {fname} ({os.path.getsize(dest)} bytes)")


def copy_mascotamas_assets():
    if not os.path.exists(WEB_PUBLIC_DIR):
        print(f"[WARN] {WEB_PUBLIC_DIR} not found.")
        return

    exts = ("*.png", "*.webp", "*.jpg", "*.svg")
    copied = 0
    for ext in exts:
        for src in glob.glob(os.path.join(WEB_PUBLIC_DIR, ext)):
            dst = os.path.join(ASSETS_DIR, os.path.basename(src))
            shutil.copy2(src, dst)
            copied += 1
    print(f"[OK] Copied {copied} MascotaMás brand assets to {ASSETS_DIR}")

    # Generate white and purple-accent versions of logo.png for dark and light surfaces
    logo_src = os.path.join(ASSETS_DIR, "logo.png")
    if os.path.exists(logo_src):
        im = Image.open(logo_src).convert("RGBA")
        arr = np.array(im)
        alpha = arr[:, :, 3]

        # 1. Pure white logo with "MÁS" in MascotaMás Lavender/Purple (#BE97FF)
        white_arr = np.zeros_like(arr)
        h, w = alpha.shape
        # In logo.png, "mascota" is roughly x < 46% width, "MÁS" is x >= 46% width
        split_x = int(w * 0.465)
        white_arr[:, :split_x, 0] = 255
        white_arr[:, :split_x, 1] = 255
        white_arr[:, :split_x, 2] = 255
        # Tint "MÁS" in vibrant MascotaMás lavender-purple (#C084FC / #BE97FF)
        white_arr[:, split_x:, 0] = 190
        white_arr[:, split_x:, 1] = 151
        white_arr[:, split_x:, 2] = 255
        white_arr[:, :, 3] = alpha
        Image.fromarray(white_arr).save(os.path.join(ASSETS_DIR, "logo_dark_bg.png"))

        # 2. All-white logo
        all_white = np.zeros_like(arr)
        all_white[:, :, :3] = 255
        all_white[:, :, 3] = alpha
        Image.fromarray(all_white).save(os.path.join(ASSETS_DIR, "logo_white.png"))
        print("[OK] Generated logo_dark_bg.png and logo_white.png")


if __name__ == "__main__":
    download_fonts()
    copy_mascotamas_assets()
