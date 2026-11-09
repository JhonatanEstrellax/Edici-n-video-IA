import os
import sys
import json
import math
import glob
import subprocess
import numpy as np
import soundfile as sf
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FFMPEG_BIN = os.path.join(BASE_DIR, "bin", "ffmpeg", "ffmpeg.exe")
WORK_DIR = os.path.join(BASE_DIR, "reels_work")
STYLE_PATH = os.path.join(BASE_DIR, "style.json")
TEMPLATE_HTML = os.path.join(BASE_DIR, "templates", "motion_graphics.html")
FONT_EXTRABOLD = os.path.join(BASE_DIR, "fonts", "Poppins-ExtraBold.ttf")
FONT_BOLD = os.path.join(BASE_DIR, "fonts", "Poppins-Bold.ttf")


def load_style():
    with open(STYLE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def hex_to_rgba(hex_str: str, alpha: int = 255):
    h = hex_str.lstrip("#")
    if len(h) == 6:
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), alpha)
    return (255, 255, 255, alpha)


def render_motion_graphics_scenes(scenes: list, fps: int = 30, width: int = 1080, graphic_h: int = 1920, subtitle_blocks: list = None, top_title: dict = None, reuse_mg_frames: bool = False):
    """
    Renders every scene + subtitle blocks + hook title using HTML + GSAP + Google Fonts Poppins in headless Playwright Chromium
    on a 1080x1920 transparent RGBA canvas (omitBackground: true):
    - Top-left: 100% original MascotaMás logo.png in a clean white pill
    - Bottom-left: Animated .peeking-creature SVG taken directly from mascotamas.com
    - Safe lower zone (y=1175..1435): Compact floating glassmorphic cards on graphic scenes
    Returns a dict: { scene_id: [ list of BGRA numpy frames (1920 x 1080 x 4) ] }
    """
    if not scenes:
        return {}

    mg_root = os.path.join(WORK_DIR, "mg_frames")
    subs_out_dir = os.path.join(mg_root, "subs_gf_poppins")
    os.makedirs(mg_root, exist_ok=True)
    os.makedirs(subs_out_dir, exist_ok=True)
    html_uri = "file:///" + os.path.abspath(TEMPLATE_HTML).replace("\\", "/")

    if not reuse_mg_frames:
        jobs_payload = {
            "width": width,
            "height": graphic_h,
            "fps": fps,
            "html_url": html_uri,
            "scenes": [],
            "subtitle_blocks": subtitle_blocks or [],
            "top_title": top_title,
            "subs_out_dir": subs_out_dir
        }

        for sc in scenes:
            sid = sc["scene_id"]
            sc_dir = os.path.join(mg_root, f"scene_{sid}")
            if os.path.exists(sc_dir):
                for old_f in glob.glob(os.path.join(sc_dir, "frame_*.png")):
                    try:
                        os.remove(old_f)
                    except OSError:
                        pass
            g_cfg = dict(sc.get("graphic_config", {}) or {})
            if sc.get("layout_mode") == "full_face" and not g_cfg.get("template"):
                g_cfg["template"] = "none"
            jobs_payload["scenes"].append({
                "scene_id": sid,
                "edited_duration": sc.get("edited_duration", 2.0),
                "graphic_config": g_cfg,
                "out_dir": sc_dir
            })

        jobs_json = os.path.join(mg_root, "mg_jobs.json")
        with open(jobs_json, "w", encoding="utf-8") as f:
            json.dump(jobs_payload, f, ensure_ascii=False, indent=2)

        print(f"[MOTION GRAPHICS] Rendering {len(scenes)} full-screen transparent RGBA overlay scenes via Playwright + GSAP...")
        node_script = os.path.join(BASE_DIR, "scripts", "render_mg.js")
        subprocess.run(["node", node_script, jobs_json], check=True, cwd=BASE_DIR)
    else:
        print(f"[MOTION GRAPHICS] Reusing pre-rendered transparent RGBA overlay scenes from {mg_root}...")

    rendered = {}
    for sc in scenes:
        sid = sc["scene_id"]
        dur = max(0.3, float(sc.get("edited_duration", 2.0)))
        total_frames = max(1, int(round(dur * fps)))
        sc_dir = os.path.join(mg_root, f"scene_{sid}")
        png_files = sorted(glob.glob(os.path.join(sc_dir, "frame_*.png")))
        loaded = []
        for p in png_files:
            bgra = cv2.imread(p, cv2.IMREAD_UNCHANGED)
            if bgra is not None:
                if bgra.ndim == 2:
                    bgra = cv2.cvtColor(bgra, cv2.COLOR_GRAY2BGRA)
                elif bgra.shape[2] == 3:
                    bgra = cv2.cvtColor(bgra, cv2.COLOR_BGR2BGRA)
                if bgra.shape[0] != graphic_h or bgra.shape[1] != width:
                    bgra = cv2.resize(bgra, (width, graphic_h), interpolation=cv2.INTER_AREA)
                loaded.append(bgra)

        if not loaded:
            loaded = [np.zeros((graphic_h, width, 4), dtype=np.uint8)]

        while len(loaded) < total_frames:
            loaded.append(loaded[-1])

        rendered[sid] = loaded[:total_frames]
        tpl_name = (sc.get("graphic_config") or {}).get("template", "none")
        print(f"  -> Scene {sid} ({tpl_name}): {total_frames} transparent RGBA frames ({dur:.2f}s)")

    return rendered


def enhance_and_denoise_source_audio(raw_wav_path: str, sr: int = 44100, skip_denoise: bool = False) -> str:
    """
    Removes background room noise and enhances vocal clarity/presence using FFmpeg DSP filters.
    When skip_denoise=True (e.g. studio Gemini TTS), skips FFT spectral denoiser to preserve 100% natural vocal warmth.
    """
    enhanced_wav = os.path.join(WORK_DIR, "source_audio_enhanced.wav")
    if skip_denoise:
        af_chain = (
            "highpass=f=75:poles=2,"
            "equalizer=f=185:t=q:w=1.1:g=1.5,"
            "equalizer=f=3400:t=q:w=1.2:g=2.0,"
            "acompressor=threshold=-20dB:ratio=2.2:attack=12:release=130:makeup=3dB"
        )
    else:
        af_chain = (
            "highpass=f=90:poles=2,"
            "afftdn=nr=20:nf=-28:tn=1,"
            "equalizer=f=240:t=q:w=1.2:g=-2.5,"
            "equalizer=f=3200:t=q:w=1.0:g=5.0,"
            "equalizer=f=6800:t=q:w=1.2:g=3.5,"
            "acompressor=threshold=-22dB:ratio=3.2:attack=6:release=110:makeup=5dB"
        )
    cmd = [
        FFMPEG_BIN, "-y",
        "-i", raw_wav_path,
        "-af", af_chain,
        "-ar", str(sr),
        "-ac", "1",
        enhanced_wav
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"[AUDIO DSP] Voice processed (skip_denoise={skip_denoise}) -> {enhanced_wav}")
    return enhanced_wav


def build_master_audio(plan: dict, style: dict) -> str:
    """
    1. Denoises and enhances the vocal track via FFmpeg spectral denoise + EQ + compression.
    2. Cuts and joins kept segments from enhanced audio with 10ms raised-cosine crossfade.
    3. Levels voice volume across sections (+6dB max boost, -3dB max cut).
    4. Mixes BGM (-26dB below voice, extra ducking during speech, 0.3s fade in, 0.8s fade out).
    5. Mixes SFX (whoosh, pop, ding) 0.05s before events, min 1.2s apart.
    6. Normalizes final audio to -14 LUFS via ffmpeg loudnorm.
    """
    sr = 44100
    enhanced_path = enhance_and_denoise_source_audio(
        plan["source_audio"],
        sr=sr,
        skip_denoise=bool(plan.get("skip_denoise", False))
    )
    src_audio, file_sr = sf.read(enhanced_path, dtype="float32")
    if src_audio.ndim > 1:
        src_audio = np.mean(src_audio, axis=1)

    segments = plan["segments"]
    crossfade_ms = style["cuts"].get("audio_crossfade_ms", 10)
    cf_samples = max(1, int(round((crossfade_ms / 1000.0) * sr)))

    lvl_cfg = style["audio"]["voice_leveling"]
    max_boost = lvl_cfg.get("max_boost_db", 6.0)
    max_cut = lvl_cfg.get("max_cut_db", -3.0)

    # Measure RMS of each segment on the denoised/enhanced audio
    seg_chunks = []
    seg_dbs = []
    for seg in segments:
        s_i = max(0, int(round(seg["source_start"] * sr)))
        e_i = min(len(src_audio), int(round(seg["source_end"] * sr)))
        chunk = src_audio[s_i:e_i].copy()
        if len(chunk) == 0:
            continue
        rms = float(np.sqrt(np.mean(chunk ** 2) + 1e-12))
        db = 20.0 * math.log10(max(rms, 1e-5))
        seg_chunks.append(chunk)
        seg_dbs.append(db)

    target_rms_db = float(np.median(seg_dbs)) if seg_dbs else -18.0
    voice_track = np.zeros(0, dtype=np.float32)

    for idx, chunk in enumerate(seg_chunks):
        # Voice leveling per section (+6 dB max boost, -3 dB max attenuation)
        if lvl_cfg.get("enabled", True):
            seg_db = seg_dbs[idx]
            diff_db = target_rms_db - seg_db
            gain_db = max(max_cut, min(max_boost, diff_db))
            chunk *= float(10.0 ** (gain_db / 20.0))

        # Apply tiny 3ms de-click fade at extreme boundaries
        declick = min(len(chunk) // 4, int(0.003 * sr))
        if declick > 1:
            chunk[:declick] *= np.linspace(0.0, 1.0, declick, dtype=np.float32)
            chunk[-declick:] *= np.linspace(1.0, 0.0, declick, dtype=np.float32)

        if idx == 0 or len(voice_track) < cf_samples or len(chunk) < cf_samples:
            voice_track = np.concatenate([voice_track, chunk])
        else:
            # 10ms raised-cosine crossfade
            fade_out = 0.5 * (1.0 + np.cos(np.linspace(0, math.pi, cf_samples, dtype=np.float32)))
            fade_in = 1.0 - fade_out
            overlap = voice_track[-cf_samples:] * fade_out + chunk[:cf_samples] * fade_in
            voice_track = np.concatenate([voice_track[:-cf_samples], overlap, chunk[cf_samples:]])

    total_samples = max(int(round(plan["edited_duration_sec"] * sr)), len(voice_track))
    if len(voice_track) < total_samples:
        voice_track = np.pad(voice_track, (0, total_samples - len(voice_track)))
    else:
        voice_track = voice_track[:total_samples]

    # Measure active voice RMS
    voice_rms = float(np.sqrt(np.mean(voice_track ** 2) + 1e-12))
    voice_db = 20.0 * math.log10(max(voice_rms, 1e-5))

    # Stereo mix buffer
    mix_l = voice_track.copy()
    mix_r = voice_track.copy()

    # Mix BGM (subtle background rhythm, well below enhanced voice)
    bgm_cfg = style["audio"]["bgm"]
    if bgm_cfg.get("enabled", True):
        bgm_dir = os.path.join(BASE_DIR, bgm_cfg.get("folder", "bgm"))
        candidates = []
        for ext in ("*.mp3", "*.wav", "*.m4a", "*.ogg", "*.flac"):
            candidates.extend(glob.glob(os.path.join(bgm_dir, ext)))
        user_tracks = [c for c in candidates if os.path.basename(c).lower() != "default_bgm.wav"]
        chosen_bgm = plan.get("bgm_override_path") or (user_tracks[0] if user_tracks else os.path.join(bgm_dir, "default_bgm.wav"))

        if os.path.exists(chosen_bgm):
            bgm_wav = os.path.join(WORK_DIR, "bgm_converted.wav")
            subprocess.run(
                [FFMPEG_BIN, "-y", "-i", chosen_bgm, "-ac", "2", "-ar", str(sr), bgm_wav],
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            bgm_data, _ = sf.read(bgm_wav, dtype="float32")
            if bgm_data.ndim == 1:
                bgm_data = np.column_stack([bgm_data, bgm_data])
            if len(bgm_data) < total_samples:
                reps = int(math.ceil(total_samples / len(bgm_data)))
                bgm_data = np.tile(bgm_data, (reps, 1))
            bgm_data = bgm_data[:total_samples]

            bgm_rms = float(np.sqrt(np.mean(bgm_data ** 2) + 1e-12))
            bgm_cur_db = 20.0 * math.log10(max(bgm_rms, 1e-5))
            rel_db = float(plan.get("bgm_relative_db", bgm_cfg.get("relative_to_voice_db", -26.0)))
            duck_db = float(plan.get("bgm_ducking_db", bgm_cfg.get("ducking_extra_db", -6.0)))

            target_bgm_db = voice_db + rel_db
            base_gain = float(10.0 ** ((target_bgm_db - bgm_cur_db) / 20.0))

            # Smooth voice envelope for ducking while speaking
            win = int(0.08 * sr)
            abs_v = np.abs(voice_track)
            if win > 1:
                env_v = np.convolve(abs_v, np.ones(win, dtype=np.float32) / win, mode="same")
            else:
                env_v = abs_v
            speaking_mask = np.clip(env_v / (voice_rms * 0.8 + 1e-6), 0.0, 1.0)
            duck_linear = float(10.0 ** (duck_db / 20.0))
            duck_curve = 1.0 - speaking_mask * (1.0 - duck_linear)

            # Fade in (0.3s) and Fade out (0.8s)
            fade_env = np.ones(total_samples, dtype=np.float32)
            fi_len = min(total_samples // 2, int(round(bgm_cfg.get("fade_in_sec", 0.3) * sr)))
            fo_len = min(total_samples // 2, int(round(bgm_cfg.get("fade_out_sec", 0.8) * sr)))
            if fi_len > 1:
                fade_env[:fi_len] = np.linspace(0.0, 1.0, fi_len, dtype=np.float32)
            if fo_len > 1:
                fade_env[-fo_len:] = np.linspace(1.0, 0.0, fo_len, dtype=np.float32)

            total_bgm_scale = base_gain * duck_curve * fade_env
            mix_l += bgm_data[:, 0] * total_bgm_scale
            mix_r += bgm_data[:, 1] * total_bgm_scale

    # Mix Sound Effects (SFX)
    sfx_cfg = style["audio"]["sfx"]
    if sfx_cfg.get("enabled", True):
        sfx_dir = os.path.join(BASE_DIR, sfx_cfg.get("folder", "sfx"))
        sfx_vol_db = sfx_cfg.get("volume_db", -12.0)
        sfx_gain = float(10.0 ** ((voice_db + sfx_vol_db - (-12.0)) / 20.0))
        sfx_gain = max(0.10, min(0.45, sfx_gain))

        for ev in plan.get("sfx_events", []):
            fname = sfx_cfg["types"].get(
                "scene_change" if ev["type"] == "whoosh" else (
                    "emphasis_bounce" if ev["type"] == "pop" else "cta_title"
                ),
                f"{ev['type']}.wav"
            )
            fpath = os.path.join(sfx_dir, fname)
            if not os.path.exists(fpath):
                fpath = os.path.join(sfx_dir, f"{ev['type']}.wav")
            if os.path.exists(fpath):
                s_data, _ = sf.read(fpath, dtype="float32")
                if s_data.ndim == 1:
                    s_data = np.column_stack([s_data, s_data])
                start_i = max(0, int(round(ev["time"] * sr)))
                end_i = min(total_samples, start_i + len(s_data))
                seg_len = end_i - start_i
                if seg_len > 0:
                    mix_l[start_i:end_i] += s_data[:seg_len, 0] * sfx_gain
                    mix_r[start_i:end_i] += s_data[:seg_len, 1] * sfx_gain

    pre_norm_path = os.path.join(WORK_DIR, "master_pre_loudnorm.wav")
    peak = max(float(np.max(np.abs(mix_l))), float(np.max(np.abs(mix_r))), 1e-6)
    if peak > 0.98:
        mix_l = mix_l / peak * 0.95
        mix_r = mix_r / peak * 0.95
    sf.write(pre_norm_path, np.column_stack([mix_l, mix_r]).astype(np.float32), sr)

    # Normalize to -14 LUFS via ffmpeg loudnorm
    final_wav = os.path.join(WORK_DIR, "final_audio_14lufs.wav")
    target_lufs = style["audio"].get("target_lufs", -14.0)
    tp = style["audio"].get("true_peak_dbtp", -1.0)
    cmd = [
        FFMPEG_BIN, "-y",
        "-i", pre_norm_path,
        "-af", f"loudnorm=I={target_lufs}:TP={tp}:LRA=11",
        "-ar", str(sr),
        "-ac", "2",
        final_wav
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"[AUDIO] Mastered and normalized to {target_lufs} LUFS -> {final_wav}")
    return final_wav


class OverlayRenderer:
    """Renders crisp brand subtitles and hook titles in pure geometric Poppins (Bold & ExtraBold) with soft Gaussian shadow and subtle 2px contour."""

    def __init__(self, style: dict):
        self.style = style
        sub_size = style["subtitles"].get("font_size_px", 66)
        title_size = style["top_title"].get("font_size_px", 86)
        sub_font_rel = style["subtitles"].get("font_path", "fonts/Poppins-Bold.ttf")
        title_font_rel = style["top_title"].get("font_path", "fonts/Poppins-ExtraBold.ttf")
        sub_font_path = os.path.join(BASE_DIR, sub_font_rel)
        title_font_path = os.path.join(BASE_DIR, title_font_rel)
        if not os.path.exists(sub_font_path):
            sub_font_path = FONT_BOLD
        if not os.path.exists(title_font_path):
            title_font_path = FONT_EXTRABOLD
        self.sub_font = ImageFont.truetype(sub_font_path, sub_size)
        self.sub_font_bold_hl = ImageFont.truetype(FONT_EXTRABOLD if os.path.exists(FONT_EXTRABOLD) else sub_font_path, sub_size)
        self.title_font = ImageFont.truetype(title_font_path, title_size)
        emoji_font_path = r"C:\Windows\Fonts\seguiemj.ttf"
        self.emoji_title_font = ImageFont.truetype(emoji_font_path, title_size) if os.path.exists(emoji_font_path) else self.title_font
        self.sub_cache = {}
        self.title_cache = {}
        self.subs_gf_dir = os.path.join(WORK_DIR, "mg_frames", "subs_gf_poppins")

    def render_subtitle_block(self, block: dict, scale: float = 1.0) -> Image.Image:
        key = (block["block_id"], round(scale, 3))
        if key in self.sub_cache:
            return self.sub_cache[key]

        canvas_w, canvas_h = 1040, 260
        gf_png = os.path.join(self.subs_gf_dir, f"sub_{block['block_id']}.png")
        if os.path.exists(gf_png):
            img = Image.open(gf_png).convert("RGBA")
        else:
            sub_cfg = self.style["subtitles"]
            stroke_w = min(2, int(sub_cfg.get("stroke_width_px", 2)))
            col_white = hex_to_rgba(sub_cfg.get("color_default", "#FFFFFF"))
            col_violet = hex_to_rgba(sub_cfg.get("color_highlight", "#AE4CFC"))
            col_stroke = hex_to_rgba(sub_cfg.get("stroke_color", "#1B1329"))

            shadow_layer = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow_layer)
            text_layer = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(text_layer)

            lines = block["lines"]
            line_h = 84
            total_h = len(lines) * line_h
            start_y = (canvas_h - total_h) // 2

            for l_idx, ln in enumerate(lines):
                space_w = draw.textlength(" ", font=self.sub_font)
                word_fonts = [self.sub_font_bold_hl if w.get("is_yellow") else self.sub_font for w in ln]
                word_widths = [draw.textlength(w["text"], font=word_fonts[i]) for i, w in enumerate(ln)]
                total_w = sum(word_widths) + space_w * max(0, len(ln) - 1)
                cur_x = (canvas_w - total_w) / 2.0
                cur_y = start_y + l_idx * line_h

                for w_idx, w in enumerate(ln):
                    txt = w["text"]
                    fnt = word_fonts[w_idx]
                    is_hl = bool(w.get("is_yellow"))
                    fill_col = col_violet if is_hl else col_white
                    shadow_draw.text(
                        (cur_x, cur_y + 4),
                        txt,
                        font=fnt,
                        fill=(15, 10, 24, 240),
                        stroke_width=stroke_w + 4,
                        stroke_fill=(15, 10, 24, 220)
                    )
                    draw.text(
                        (cur_x, cur_y),
                        txt,
                        font=fnt,
                        fill=fill_col,
                        stroke_width=stroke_w,
                        stroke_fill=col_stroke
                    )
                    cur_x += word_widths[w_idx] + space_w

            shadow_blurred = shadow_layer.filter(ImageFilter.GaussianBlur(radius=6))
            img = Image.alpha_composite(shadow_blurred, text_layer)

        if abs(scale - 1.0) > 0.005:
            nw = max(1, int(round(canvas_w * scale)))
            nh = max(1, int(round(canvas_h * scale)))
            resized = img.resize((nw, nh), Image.Resampling.BICUBIC)
            out = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
            ox = (canvas_w - nw) // 2
            oy = (canvas_h - nh) // 2
            out.paste(resized, (ox, oy))
            img = out

        self.sub_cache[key] = img
        return img

    def render_top_title(self, title_cfg: dict) -> Image.Image:
        if not title_cfg:
            return None
        key = (title_cfg.get("line1", ""), title_cfg.get("line2", ""))
        if key in self.title_cache:
            return self.title_cache[key]

        gf_title_png = os.path.join(self.subs_gf_dir, "top_title.png")
        if os.path.exists(gf_title_png):
            img = Image.open(gf_title_png).convert("RGBA")
            self.title_cache[key] = img
            return img

        canvas_w, canvas_h = 1040, 290
        shadow_layer = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow_layer)
        text_layer = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(text_layer)

        col_white = (255, 255, 255, 255)
        col_violet = hex_to_rgba(self.style["top_title"].get("color_keyword", "#AE4CFC"))
        col_stroke = hex_to_rgba(self.style["subtitles"].get("stroke_color", "#1B1329"))
        stroke_w = 2
        kw = title_cfg.get("keyword", "").upper()

        for idx, line_str in enumerate([title_cfg.get("line1", ""), title_cfg.get("line2", "")]):
            if not line_str:
                continue
            tokens = line_str.split()
            space_w = draw.textlength(" ", font=self.title_font)
            tok_widths = []
            for t in tokens:
                is_emj = any(ord(ch) > 0x2000 for ch in t)
                fnt = self.emoji_title_font if is_emj else self.title_font
                tok_widths.append(draw.textlength(t, font=fnt))
            total_w = sum(tok_widths) + space_w * max(0, len(tokens) - 1)
            cur_x = (canvas_w - total_w) / 2.0
            cur_y = 20 + idx * 114

            for t_i, tok in enumerate(tokens):
                is_emj = any(ord(ch) > 0x2000 for ch in tok)
                if is_emj:
                    draw.text(
                        (cur_x, cur_y),
                        tok,
                        font=self.emoji_title_font,
                        embedded_color=True
                    )
                else:
                    clean_tok = "".join(ch for ch in tok.upper() if ch.isalnum())
                    is_kw = bool(kw and (clean_tok == kw or kw in clean_tok or "'" in tok))
                    fill_c = col_violet if is_kw else col_white
                    shadow_draw.text(
                        (cur_x, cur_y + 5),
                        tok,
                        font=self.title_font,
                        fill=(15, 10, 24, 245),
                        stroke_width=stroke_w + 5,
                        stroke_fill=(15, 10, 24, 225)
                    )
                    draw.text(
                        (cur_x, cur_y),
                        tok,
                        font=self.title_font,
                        fill=fill_c,
                        stroke_width=stroke_w,
                        stroke_fill=col_stroke
                    )
                cur_x += tok_widths[t_i] + space_w

        shadow_blurred = shadow_layer.filter(ImageFilter.GaussianBlur(radius=7))
        img = Image.alpha_composite(shadow_blurred, text_layer)
        self.title_cache[key] = img
        return img


def alpha_blend_bgra_full(bgr_canvas: np.ndarray, bgra_overlay: np.ndarray):
    """Fast in-place alpha blend of a full-screen 4-channel BGRA overlay onto a 3-channel BGR canvas."""
    alpha_u8 = bgra_overlay[:, :, 3]
    # Only blend bounding box where alpha > 0 for maximum speed
    ys, xs = np.where(alpha_u8 > 0)
    if len(ys) == 0:
        return
    y1, y2 = int(ys.min()), int(ys.max()) + 1
    x1, x2 = int(xs.min()), int(xs.max()) + 1

    roi_bgr = bgr_canvas[y1:y2, x1:x2].astype(np.float32)
    ov_crop = bgra_overlay[y1:y2, x1:x2]
    alpha = (ov_crop[:, :, 3:4].astype(np.float32)) / 255.0
    ov_bgr = ov_crop[:, :, :3].astype(np.float32)

    bgr_canvas[y1:y2, x1:x2] = (roi_bgr * (1.0 - alpha) + ov_bgr * alpha).astype(np.uint8)


def alpha_blend_rgba_onto_bgr(bgr_canvas: np.ndarray, rgba_overlay: Image.Image, center_x: int, center_y: int):
    ov = np.array(rgba_overlay)
    oh, ow = ov.shape[:2]
    ch, cw = bgr_canvas.shape[:2]

    x1 = center_x - ow // 2
    y1 = center_y - oh // 2
    x2 = x1 + ow
    y2 = y1 + oh

    cx1, cy1 = max(0, x1), max(0, y1)
    cx2, cy2 = min(cw, x2), min(ch, y2)
    if cx2 <= cx1 or cy2 <= cy1:
        return

    ox1, oy1 = cx1 - x1, cy1 - y1
    ox2, oy2 = ox1 + (cx2 - cx1), oy1 + (cy2 - cy1)

    roi = bgr_canvas[cy1:cy2, cx1:cx2]
    ov_crop = ov[oy1:oy2, ox1:ox2]
    alpha = (ov_crop[:, :, 3:4].astype(np.float32)) / 255.0
    ov_bgr = ov_crop[:, :, [2, 1, 0]].astype(np.float32)
    roi_f = roi.astype(np.float32)

    blended = roi_f * (1.0 - alpha) + ov_bgr * alpha
    bgr_canvas[cy1:cy2, cx1:cx2] = blended.astype(np.uint8)


def crop_face_region(
    frame: np.ndarray,
    target_w: int,
    target_h: int,
    face_center: list,
    zoom: float = 1.0,
    pan_x: float = 0.0,
    vert_anchor: float = 0.42,
    min_y1_ratio: float = 0.0
) -> np.ndarray:
    """
    Centers the speaker's face inside full-screen (1080x1920) and applies smooth dynamic multi-camera zoom & pan.
    Never splits top/bottom so the speaker's face is 100% visible at all times.
    """
    sh, sw = frame.shape[:2]
    cx_norm = max(0.15, min(0.85, face_center[0] + pan_x))
    cy_norm = face_center[1]

    if min_y1_ratio > 0.0:
        zoom = max(zoom, 1.0 / max(0.5, 1.0 - min_y1_ratio))

    target_aspect = target_w / float(target_h)
    src_aspect = sw / float(sh)

    if src_aspect > target_aspect:
        base_crop_h = float(sh)
        base_crop_w = base_crop_h * target_aspect
    else:
        base_crop_w = float(sw)
        base_crop_h = base_crop_w / target_aspect

    crop_w = max(64, int(round(base_crop_w / max(1.0, zoom))))
    crop_h = max(64, int(round(base_crop_h / max(1.0, zoom))))

    cx_px = int(round(cx_norm * sw))
    cy_px = int(round(cy_norm * sh))

    min_y1_px = int(round(sh * min_y1_ratio))
    x1 = max(0, min(sw - crop_w, cx_px - crop_w // 2))
    y1 = max(min_y1_px, min(sh - crop_h, cy_px - int(crop_h * vert_anchor)))

    cropped = frame[y1:y1 + crop_h, x1:x1 + crop_w]
    return cv2.resize(cropped, (target_w, target_h), interpolation=cv2.INTER_LINEAR)


def render_final_video(output_mp4_path: str = None):
    style = load_style()
    with open(os.path.join(WORK_DIR, "edit_plan.json"), "r", encoding="utf-8") as f:
        plan = json.load(f)

    out_w = style["video"].get("width", 1080)
    out_h = style["video"].get("height", 1920)
    out_fps = style["video"].get("fps", 30)

    # 1. Render Full-Screen Transparent RGBA Overlays + Google Fonts Poppins Subtitles/Titles via Playwright + HTML + GSAP
    mg_frames_by_scene = render_motion_graphics_scenes(
        plan["scenes"],
        fps=out_fps,
        width=out_w,
        graphic_h=out_h,
        subtitle_blocks=plan.get("subtitle_blocks", []),
        top_title=plan.get("hook_title"),
        reuse_mg_frames=bool(plan.get("reuse_mg_frames", False))
    )

    # 2. Denoise, Enhance Voice, Mix BGM/SFX & Normalize Master Audio (-14 LUFS)
    final_wav = build_master_audio(plan, style)

    # 3. Single-pass Video Compositor -> FFmpeg high-quality H.264 encoder
    if output_mp4_path is None:
        output_mp4_path = os.path.join(BASE_DIR, "Reel_Editado.mp4")

    safe_out_mp4 = os.path.join(WORK_DIR, "final_output.mp4")
    overlay_renderer = OverlayRenderer(style)

    cap = cv2.VideoCapture(plan["source_video"])
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

    total_edited_dur = plan["edited_duration_sec"]
    total_out_frames = max(1, int(round(total_edited_dur * out_fps)))

    ffmpeg_cmd = [
        FFMPEG_BIN, "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-pix_fmt", "bgr24",
        "-s", f"{out_w}x{out_h}",
        "-r", str(out_fps),
        "-i", "-",
        "-i", final_wav,
        "-c:v", style["video"].get("codec", "libx264"),
        "-crf", str(style["video"].get("crf", 18)),
        "-preset", style["video"].get("preset", "medium"),
        "-pix_fmt", style["video"].get("pixel_format", "yuv420p"),
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        safe_out_mp4
    ]

    print(f"[RENDER] Compositing {total_out_frames} full-screen frames ({total_edited_dur:.2f}s @ {out_fps}fps) to {safe_out_mp4}...")
    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

    segments = plan["segments"]
    scenes = plan["scenes"]
    sub_blocks = plan["subtitle_blocks"]

    zoom_start = style["camera"].get("cut_zoom_start", 1.00)
    zoom_end = style["camera"].get("cut_zoom_end", 1.04)
    zoom_emph = style["camera"].get("emphasis_zoom", 1.10)

    last_src_frame_idx = -999
    cached_src_frame = None

    for f_idx in range(total_out_frames):
        t = f_idx / float(out_fps)

        seg = next(
            (s for s in segments if s["edited_start"] <= t <= s["edited_end"]),
            segments[-1] if segments else None
        )
        scene = next(
            (sc for sc in scenes if sc["edited_start"] <= t <= sc["edited_end"]),
            scenes[-1] if scenes else None
        )
        sub_block = next(
            (b for b in sub_blocks if b["start"] <= t <= b["end"]),
            None
        )

        if seg:
            seg_progress = (t - seg["edited_start"]) / max(0.01, seg["edited_end"] - seg["edited_start"])
            seg_progress = max(0.0, min(1.0, seg_progress))
            src_t = seg["source_start"] + seg_progress * (seg["source_end"] - seg["source_start"])
            face_center = seg.get("face_center", plan["face_metadata"]["default_face_center"])
        else:
            seg_progress = 0.0
            src_t = t
            face_center = plan["face_metadata"]["default_face_center"]

        target_src_frame = int(round(src_t * src_fps))
        if cached_src_frame is None or target_src_frame != last_src_frame_idx:
            if abs(target_src_frame - last_src_frame_idx) > 4 or last_src_frame_idx < 0:
                cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, target_src_frame))
                ret, frm = cap.read()
            else:
                ret, frm = True, cached_src_frame
                while last_src_frame_idx < target_src_frame:
                    ret, frm = cap.read()
                    last_src_frame_idx += 1
            if ret and frm is not None:
                cached_src_frame = frm
                last_src_frame_idx = target_src_frame

        if cached_src_frame is None:
            cached_src_frame = np.zeros((out_h, out_w, 3), dtype=np.uint8)

        g_cfg = scene.get("graphic_config", {}) if scene else {}
        if g_cfg.get("face_center"):
            face_center = g_cfg["face_center"]
        sc_z_start = float(g_cfg.get("camera_zoom_start", zoom_start))
        sc_z_end = float(g_cfg.get("camera_zoom_end", zoom_end))
        sc_pan_start = float(g_cfg.get("camera_pan_start", 0.0))
        sc_pan_end = float(g_cfg.get("camera_pan_end", 0.0))
        sc_vert_anchor = float(g_cfg.get("camera_vert_anchor", 0.42))

        if scene:
            sc_progress = max(0.0, min(1.0, (t - scene["edited_start"]) / max(0.01, scene["edited_end"] - scene["edited_start"])))
        else:
            sc_progress = seg_progress

        cur_zoom = sc_z_start + (sc_z_end - sc_z_start) * sc_progress
        cur_pan_x = sc_pan_start + (sc_pan_end - sc_pan_start) * sc_progress
        sub_scale = 1.0

        # Smooth commercial whip-zoom + glow transition on scene cuts (0.18s) and mid-scene beat switches
        trans_alpha = 0.0
        if scene and scene["edited_start"] > 0.05:
            dt_sc = t - scene["edited_start"]
            if 0.0 <= dt_sc <= 0.18:
                tr_u = 1.0 - (dt_sc / 0.18)
                cur_zoom += 0.065 * (tr_u * tr_u)
                trans_alpha = 0.26 * (tr_u * tr_u)

        if scene and g_cfg.get("switch_sec"):
            sw_abs_t = float(scene["edited_start"]) + float(g_cfg["switch_sec"])
            dt_sw = t - sw_abs_t
            if 0.0 <= dt_sw <= 0.16:
                sw_u = 1.0 - (dt_sw / 0.16)
                cur_zoom += 0.042 * (sw_u * sw_u)
                trans_alpha = max(trans_alpha, 0.20 * (sw_u * sw_u))

        if sub_block and sub_block.get("has_bounce"):
            bt = sub_block.get("bounce_start", sub_block["start"])
            b_dur = style["subtitles"]["bounce_emphasis"].get("duration_sec", 0.28)
            if bt <= t <= sub_block["end"]:
                ramp = min(1.0, (t - bt) / 0.12) if t >= bt else 0.0
                cur_zoom = max(cur_zoom, 1.0 + (zoom_emph - 1.0) * ramp)
            if bt <= t <= bt + b_dur:
                u = (t - bt) / b_dur
                sub_scale = 1.0 + 0.18 * math.sin(math.pi * u)

        # Always Full-Screen 1080x1920 speaker frame (NO top/bottom division!)
        is_split_graphic = bool(scene and scene.get("layout_mode") == "split_graphic")
        is_sys_prio = bool(g_cfg.get("system_priority", False))
        has_devices = (is_split_graphic or is_sys_prio) and (g_cfg.get("device_mode", "none") != "none")
        if not has_devices:
            cur_zoom = min(cur_zoom, 1.02)
        if is_sys_prio:
            cur_zoom = max(cur_zoom, float(g_cfg.get("system_priority_zoom", 1.14)))
            vert_anchor_cfg = float(g_cfg.get("system_priority_vert_anchor", 0.19))
            min_y1_cfg = float(g_cfg.get("system_priority_min_y1_ratio", 0.05))
        else:
            min_y1_cfg = float(style["camera"].get("split_graphic_min_y1_ratio", 0.0)) if has_devices else 0.0
            vert_anchor_cfg = float(style["camera"].get("split_graphic_vert_anchor", 0.25)) if has_devices else 0.39
        if plan.get("preframed_source", False):
            canvas = cached_src_frame.copy()
        else:
            canvas = crop_face_region(
                cached_src_frame,
                out_w,
                out_h,
                face_center,
                zoom=cur_zoom,
                pan_x=cur_pan_x,
                vert_anchor=vert_anchor_cfg,
                min_y1_ratio=min_y1_cfg
            )

        # Soft commercial glow-flash transition at scene cut
        if trans_alpha > 0.005:
            glow_bgr = np.array([255.0, 220.0, 245.0], dtype=np.float32)
            canvas = (canvas.astype(np.float32) * (1.0 - trans_alpha) + glow_bgr * trans_alpha).astype(np.uint8)

        # Alpha-blend transparent RGBA Motion Graphics overlay (Top-left logo.png, Commercial Headline, Bottom-left peeking creature, and Floating Cards)
        if scene and scene["scene_id"] in mg_frames_by_scene:
            mg_list = mg_frames_by_scene[scene["scene_id"]]
            sc_rel_f = max(0, min(len(mg_list) - 1, int(round((t - scene["edited_start"]) * out_fps))))
            alpha_blend_bgra_full(canvas, mg_list[sc_rel_f])

        # Hook Title on Scene 1 (only if scene does not already render a Commercial Headline Banner)
        if scene and scene.get("top_title") and scene.get("layout_mode") == "full_face" and not g_cfg.get("headline_main"):
            title_img = overlay_renderer.render_top_title(scene["top_title"])
            if title_img is not None:
                alpha_blend_rgba_onto_bgr(canvas, title_img, out_w // 2, style["top_title"].get("position_y", 1260))

        # Subtitles in safe lower zone (y=1620)
        if sub_block:
            sub_img = overlay_renderer.render_subtitle_block(sub_block, scale=sub_scale)
            alpha_blend_rgba_onto_bgr(canvas, sub_img, out_w // 2, style["subtitles"].get("position_y_full_face", 1620))

        proc.stdin.write(canvas.tobytes())

    proc.stdin.close()
    proc.wait()
    cap.release()

    if os.path.abspath(safe_out_mp4) != os.path.abspath(output_mp4_path):
        import shutil
        shutil.copy2(safe_out_mp4, output_mp4_path)

    print(f"[STEP 4 & 5 DONE] Exported high-quality final Reel -> {output_mp4_path}")
    return output_mp4_path


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else None
    render_final_video(out)
