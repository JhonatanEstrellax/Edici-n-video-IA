import os
import math
import urllib.request
import numpy as np
import soundfile as sf

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS_DIR = os.path.join(BASE_DIR, "fonts")
MODELS_DIR = os.path.join(BASE_DIR, "models")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
SFX_DIR = os.path.join(BASE_DIR, "sfx")
BGM_DIR = os.path.join(BASE_DIR, "bgm")

for d in [FONTS_DIR, MODELS_DIR, TEMPLATES_DIR, SFX_DIR, BGM_DIR]:
    os.makedirs(d, exist_ok=True)


def download_file(url: str, dest: str, description: str):
    if os.path.exists(dest) and os.path.getsize(dest) > 1024:
        print(f"[OK] {description} already exists at {dest}")
        return True
    print(f"[DOWNLOAD] Fetching {description} from {url} ...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp, open(dest, "wb") as out:
        out.write(resp.read())
    print(f"[OK] Saved {description} ({os.path.getsize(dest)} bytes)")
    return True


def generate_whoosh(filepath: str, sr: int = 44100):
    """Synthesize a clean cinematic air whoosh/swoosh (0.30s)."""
    dur = 0.30
    n = int(sr * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    rng = np.random.default_rng(42)
    noise = rng.standard_normal(n)

    # Time-varying bandpass / swept sine + shaped air noise
    env = np.sin(np.pi * (t / dur)) ** 1.8
    # Low-to-mid air sweep
    f_start, f_end = 140.0, 950.0
    phase = 2 * np.pi * (f_start * t + 0.5 * (f_end - f_start) * (t ** 2) / dur)
    tonal_air = np.sin(phase) * 0.35

    # Simple moving-average smoothing on noise to make it warm swoosh
    kernel_size = 18
    kernel = np.ones(kernel_size) / kernel_size
    smooth_noise = np.convolve(noise, kernel, mode="same")
    smooth_noise = smooth_noise / (np.max(np.abs(smooth_noise)) + 1e-8)

    sig = (0.72 * smooth_noise + 0.28 * tonal_air) * env
    sig = sig / (np.max(np.abs(sig)) + 1e-8) * 0.85
    stereo = np.column_stack([sig, sig]).astype(np.float32)
    sf.write(filepath, stereo, sr)
    print(f"[OK] Generated SFX: {filepath}")


def generate_pop(filepath: str, sr: int = 44100):
    """Synthesize a crisp bubble/lip pop sound effect (0.11s) for keyword bounce."""
    dur = 0.11
    n = int(sr * dur)
    t = np.linspace(0, dur, n, endpoint=False)

    # Pitch rapidly rises then drops like a classic pop
    freq = 180.0 + 520.0 * np.exp(-t * 32.0)
    phase = 2 * np.pi * np.cumsum(freq) / sr
    env = np.exp(-t * 38.0) * (1.0 - np.exp(-t * 450.0))

    click = np.exp(-t * 260.0) * np.sin(2 * np.pi * 1200.0 * t) * 0.25
    sig = (np.sin(phase) * env + click)
    sig = sig / (np.max(np.abs(sig)) + 1e-8) * 0.90
    stereo = np.column_stack([sig, sig]).astype(np.float32)
    sf.write(filepath, stereo, sr)
    print(f"[OK] Generated SFX: {filepath}")


def generate_ding(filepath: str, sr: int = 44100):
    """Synthesize a bright, pleasant notification bell ding (0.65s) for CTA title."""
    dur = 0.65
    n = int(sr * dur)
    t = np.linspace(0, dur, n, endpoint=False)

    attack = 1.0 - np.exp(-t * 350.0)
    f1 = 1046.50  # C6
    f2 = 1567.98  # G6
    f3 = 2093.00  # C7
    f4 = 3135.96  # G7

    sig = (
        0.55 * np.sin(2 * np.pi * f1 * t) * np.exp(-t * 5.5)
        + 0.25 * np.sin(2 * np.pi * f2 * t) * np.exp(-t * 8.0)
        + 0.14 * np.sin(2 * np.pi * f3 * t) * np.exp(-t * 11.0)
        + 0.06 * np.sin(2 * np.pi * f4 * t) * np.exp(-t * 16.0)
    ) * attack

    sig = sig / (np.max(np.abs(sig)) + 1e-8) * 0.88
    stereo = np.column_stack([sig, sig]).astype(np.float32)
    sf.write(filepath, stereo, sr)
    print(f"[OK] Generated SFX: {filepath}")


def generate_default_bgm(filepath: str, sr: int = 44100):
    """Synthesize a warm, subtle 64-second copyright-free chill lo-fi background rhythm."""
    dur = 64.0
    n = int(sr * dur)
    t = np.linspace(0, dur, n, endpoint=False)

    # 4-chord warm progression (Am9 -> Fmaj7 -> Cmaj7 -> G6), 2 seconds per bar (120 BPM)
    chords = [
        [220.00, 261.63, 329.63, 392.00],  # Am7
        [174.61, 220.00, 261.63, 329.63],  # Fmaj7
        [130.81, 196.00, 246.94, 329.63],  # Cmaj7
        [196.00, 246.94, 293.66, 392.00],  # G6
    ]
    bar_len = 2.0
    pad_l = np.zeros(n, dtype=np.float32)
    pad_r = np.zeros(n, dtype=np.float32)

    total_bars = int(dur / bar_len)
    samples_per_bar = int(sr * bar_len)

    for b in range(total_bars):
        c = chords[b % len(chords)]
        start = b * samples_per_bar
        end = min(n, start + samples_per_bar)
        tb = np.linspace(0, bar_len, end - start, endpoint=False)
        env = np.sin(np.pi * (tb / bar_len)) ** 0.45 * np.exp(-tb * 0.35)
        chord_sig_l = np.zeros_like(tb)
        chord_sig_r = np.zeros_like(tb)
        for idx, freq in enumerate(c):
            detune = 1.0015 if idx % 2 == 0 else 0.9985
            chord_sig_l += np.sin(2 * np.pi * freq * tb) * 0.25
            chord_sig_r += np.sin(2 * np.pi * (freq * detune) * tb) * 0.25
        pad_l[start:end] += (chord_sig_l * env).astype(np.float32)
        pad_r[start:end] += (chord_sig_r * env).astype(np.float32)

    # Add a soft rhythmic pulse (120 BPM = 0.5s beat)
    beat_period = 0.5
    beat_phase = np.mod(t, beat_period)
    kick_freq = 55.0 + 75.0 * np.exp(-beat_phase * 28.0)
    kick_env = np.exp(-beat_phase * 14.0) * (1.0 - np.exp(-beat_phase * 200.0))
    kick = np.sin(2 * np.pi * kick_freq * beat_phase) * kick_env * 0.22

    # Soft hi-hat tick on off-beats
    hat_phase = np.mod(t + 0.25, beat_period)
    rng = np.random.default_rng(7)
    hat_noise = rng.standard_normal(n).astype(np.float32)
    hat_env = np.exp(-hat_phase * 60.0)
    hat = hat_noise * hat_env * 0.03

    left = pad_l * 0.65 + kick + hat
    right = pad_r * 0.65 + kick + hat
    peak = max(np.max(np.abs(left)), np.max(np.abs(right)), 1e-8)
    stereo = np.column_stack([left / peak * 0.75, right / peak * 0.75]).astype(np.float32)
    sf.write(filepath, stereo, sr)
    print(f"[OK] Generated default BGM: {filepath}")


def main():
    # 1. Pretendard ExtraBold Font (OTF + WOFF2)
    download_file(
        "https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/packages/pretendard/dist/public/static/Pretendard-ExtraBold.otf",
        os.path.join(FONTS_DIR, "Pretendard-ExtraBold.otf"),
        "Pretendard ExtraBold OTF",
    )
    download_file(
        "https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/packages/pretendard/dist/public/static/Pretendard-Bold.otf",
        os.path.join(FONTS_DIR, "Pretendard-Bold.otf"),
        "Pretendard Bold OTF",
    )
    download_file(
        "https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/packages/pretendard/dist/web/static/woff2/Pretendard-ExtraBold.woff2",
        os.path.join(FONTS_DIR, "Pretendard-ExtraBold.woff2"),
        "Pretendard ExtraBold WOFF2",
    )

    # 2. GSAP local bundle for Playwright motion graphics
    download_file(
        "https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js",
        os.path.join(TEMPLATES_DIR, "gsap.min.js"),
        "GSAP 3.12.5",
    )

    # 3. OpenCV YuNet Face & Landmark Detection model
    download_file(
        "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
        os.path.join(MODELS_DIR, "face_detection_yunet_2023mar.onnx"),
        "OpenCV YuNet Face Detector ONNX",
    )

    # 4. Generate SFX & Default BGM
    generate_whoosh(os.path.join(SFX_DIR, "whoosh.wav"))
    generate_pop(os.path.join(SFX_DIR, "pop.wav"))
    generate_ding(os.path.join(SFX_DIR, "ding.wav"))
    generate_default_bgm(os.path.join(BGM_DIR, "default_bgm.wav"))
    print("[DONE] All assets initialized successfully.")


if __name__ == "__main__":
    main()
