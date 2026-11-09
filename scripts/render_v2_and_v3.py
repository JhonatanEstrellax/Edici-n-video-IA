import os
import re
import sys
import glob
import json
import math
import subprocess
import numpy as np
import soundfile as sf
import noisereduce as nr
import cv2
from scipy.signal import butter, filtfilt
from PIL import Image, ImageDraw, ImageFont

def _build_url_prefix_delta():
    base_bg_rgb = (224, 234, 224)
    base_bg_bgr = np.array([224, 234, 224], dtype=np.int16)
    font = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 21)
    pil_strip = Image.new("RGB", (400, 30), base_bg_rgb)
    draw = ImageDraw.Draw(pil_strip)
    x_cur = 8
    y_txt = 0
    draw.text((x_cur, y_txt), "https://", font=font, fill=(95, 99, 104))
    x_cur = draw.textbbox((x_cur, y_txt), "https://", font=font)[2]
    draw.text((x_cur, y_txt), "gestion.mascotamas.com", font=font, fill=(31, 31, 31))
    end_x = draw.textbbox((x_cur, y_txt), "gestion.mascotamas.com", font=font)[2] + 1
    strip_bgr = cv2.cvtColor(np.array(pil_strip)[:, :end_x], cv2.COLOR_RGB2BGR)
    return strip_bgr.astype(np.int16) - base_bg_bgr

URL_PREFIX_DELTA = _build_url_prefix_delta()
URL_PREFIX_W = URL_PREFIX_DELTA.shape[1]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK_DIR = os.path.join(BASE_DIR, "instructivos_work")
sys.path.insert(0, WORK_DIR)

from prepare_v2_v3_plans import WORD_OVERRIDES, MANUAL_WORD_SPANS
from edit_instructivo_desktop import (
    FFMPEG_BIN, TEMPLATE_HTML, NODE_RENDER_SCRIPT, SOURCE_VIDEO, RAW_TRANSCRIPT, WAV_44K,
    AV_CLOCK_RATIO, HIGHLIGHT_KEYWORDS, get_scene_definitions, normalize_clean,
    build_desktop_subtitle_blocks, blend_roi_bgra, build_verification_grid
)

SHORT_CONNECTORS = {
    "el", "la", "los", "las", "un", "una", "de", "del", "al", "a", "en",
    "y", "o", "que", "se", "si", "es", "por", "su", "lo", "no", "va"
}


def prepare_clean_source_audio() -> tuple[np.ndarray, int]:
    """
    Produces a studio-cleaned 44.1kHz mono array from WAV_44K:
    - 95Hz highpass
    - Stationary STFT spectral gating (noisereduce) trained on pure room tone (5.2s..7.8s)
    - Soft dereverb expander gate to suppress room reverb tails
    - FFmpeg broadcast vocal EQ (mud cut @ 220Hz, presence @ 3.1kHz, de-esser @ 7.2kHz, soft compressor)
    """
    clean_eq_wav = os.path.join(WORK_DIR, "audio_v2_studio_source.wav")
    if os.path.exists(clean_eq_wav):
        y, sr = sf.read(clean_eq_wav, dtype="float32")
        if y.ndim > 1:
            y = np.mean(y, axis=1)
        return y, sr

    print("[V2 DSP] Running spectral noise cancellation + room echo suppression...")
    audio, sr = sf.read(WAV_44K, dtype="float32")
    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)

    b_hp, a_hp = butter(3, 95.0 / (sr / 2), btype="high")
    audio_hp = filtfilt(b_hp, a_hp, audio).astype(np.float32)

    # Pure room noise sample from 5.2s..7.8s + 133.2s..135.8s (zero clicks, pure room tone/hum)
    noise_clip = np.concatenate([
        audio_hp[int(5.2 * sr):int(7.8 * sr)],
        audio_hp[int(133.2 * sr):int(135.8 * sr)]
    ])

    audio_dn = nr.reduce_noise(
        y=audio_hp,
        sr=sr,
        y_noise=noise_clip,
        stationary=True,
        prop_decrease=0.90,
        n_fft=2048,
        hop_length=512,
        freq_mask_smooth_hz=300,
        time_mask_smooth_ms=45
    ).astype(np.float32)

    # Soft dereverb expander to damp room echo tails below -34 dB
    win_len = int(0.01 * sr)
    n_w = len(audio_dn) // win_len
    frames = audio_dn[:n_w * win_len].reshape(n_w, win_len)
    env_rms = np.sqrt(np.mean(frames ** 2, axis=1) + 1e-12)
    env_db = 20.0 * np.log10(np.maximum(env_rms, 1e-6))

    gain_env = np.ones(n_w, dtype=np.float32)
    gate_thresh = -33.5
    gate_floor = 0.05
    for i in range(n_w):
        if env_db[i] < gate_thresh:
            diff = gate_thresh - env_db[i]
            gain_env[i] = max(gate_floor, 10.0 ** (-diff * 1.4 / 20.0))

    kernel = np.hanning(9)
    kernel /= np.sum(kernel)
    gain_smooth = np.convolve(gain_env, kernel, mode="same")
    sample_gain = np.interp(
        np.arange(len(audio_dn)),
        np.arange(n_w) * win_len + win_len // 2,
        gain_smooth
    ).astype(np.float32)

    pre_eq_wav = os.path.join(WORK_DIR, "audio_v2_pre_eq.wav")
    sf.write(pre_eq_wav, (audio_dn * sample_gain).astype(np.float32), sr)

    # Broadcast vocal EQ: cut 220Hz boxy room echo, warm 145Hz body, +3.2dB 3.1kHz clarity, soft de-ess 7.2kHz
    af_chain = (
        "highpass=f=100:poles=2,"
        "equalizer=f=145:t=q:w=1.2:g=1.4,"
        "equalizer=f=225:t=q:w=1.3:g=-3.8,"
        "equalizer=f=480:t=q:w=1.5:g=-1.5,"
        "equalizer=f=3100:t=q:w=1.0:g=3.2,"
        "equalizer=f=7200:t=q:w=1.6:g=-2.5,"
        "acompressor=threshold=-20dB:ratio=2.6:attack=8:release=120:makeup=3dB"
    )
    subprocess.run(
        [FFMPEG_BIN, "-y", "-i", pre_eq_wav, "-af", af_chain, "-ar", str(sr), "-ac", "1", clean_eq_wav],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    y, sr = sf.read(clean_eq_wav, dtype="float32")
    return y, sr


def refine_and_trim_word_v2(audio: np.ndarray, sr: int, wid: int, word_str: str, raw_s: float, raw_e: float) -> tuple[float, float]:
    """
    Uses MANUAL_WORD_SPANS first if present; otherwise finds the main speech island inside [raw_s, raw_e]
    and trims stretched vowels at the end so drawled words sound crisp and natural.
    """
    if wid in MANUAL_WORD_SPANS:
        s_t, e_t = MANUAL_WORD_SPANS[wid]
    else:
        s_i = max(0, int(raw_s * sr))
        e_i = min(len(audio), int(raw_e * sr))
        seg = audio[s_i:e_i]
        win = max(1, int(0.01 * sr))
        n_w = len(seg) // win
        if n_w < 3:
            s_t, e_t = raw_s, raw_e
        else:
            frames = seg[:n_w * win].reshape(n_w, win)
            rms = np.sqrt(np.mean(frames ** 2, axis=1) + 1e-12)
            db = 20.0 * np.log10(np.maximum(rms, 1e-6))
            peak_db = float(np.max(db))
            thresh = max(-33.0, peak_db - 16.0)
            act = db >= thresh
            # Bridge micro gaps <= 50ms
            gap = 0
            for k in range(len(act)):
                if not act[k]:
                    gap += 1
                else:
                    if 0 < gap <= 5:
                        act[k - gap:k] = True
                    gap = 0
            # Find islands
            islands = []
            in_isl = False
            is_s = 0
            for k, val in enumerate(act):
                if val and not in_isl:
                    in_isl = True
                    is_s = k
                elif not val and in_isl:
                    in_isl = False
                    islands.append((is_s, k))
            if in_isl:
                islands.append((is_s, len(act)))

            if not islands:
                s_t, e_t = raw_s, raw_e
            elif len(islands) == 1:
                s_t = raw_s + islands[0][0] * 0.01
                e_t = min(raw_e, raw_s + (islands[0][1] + 1) * 0.01)
            else:
                # If multiple islands separated by > 120ms, pick the island with highest energy/duration
                # (avoiding tiny leading click/tail from previous word)
                best_isl = max(islands, key=lambda x: (x[1] - x[0]) + (2 if x[0] > 2 else 0))
                s_t = raw_s + best_isl[0] * 0.01
                e_t = min(raw_e, raw_s + (best_isl[1] + 1) * 0.01)

    # Trim stretched vowels ("cuando se alarga una palabra")
    clean_w = normalize_clean(word_str)
    dur = e_t - s_t
    if clean_w in SHORT_CONNECTORS:
        max_conn_dur = 0.23 if clean_w in {"por", "los", "las", "del", "una"} else 0.19
        if dur > max_conn_dur:
            e_t = s_t + max_conn_dur
    else:
        # Cap excessive vowel drawl on content words based on character length
        max_word_dur = max(0.38, min(0.88, 0.095 * len(clean_w) + 0.12))
        if dur > max_word_dur and wid not in MANUAL_WORD_SPANS:
            e_t = s_t + max_word_dur

    if e_t - s_t < 0.055:
        e_t = s_t + 0.065

    return round(s_t, 4), round(e_t, 4)


def build_v2_plan_and_audio():
    plan_path = os.path.join(WORK_DIR, "desktop_edit_plan_v2.json")
    final_wav = os.path.join(WORK_DIR, "voice_v2_final_14lufs.wav")
    if os.path.exists(plan_path) and os.path.exists(final_wav):
        with open(plan_path, "r", encoding="utf-8") as f:
            return json.load(f), final_wav
    print("\n========================================================")
    print("BUILDING VERSION 2: VOZ ORIGINAL MEJORADA SIN ECO NI ESPACIOS")
    print("========================================================")
    clean_audio, sr = prepare_clean_source_audio()
    orig_dur = round(len(clean_audio) / sr, 3)

    with open(RAW_TRANSCRIPT, "r", encoding="utf-8") as f:
        raw = json.load(f)

    scene_defs = get_scene_definitions()
    seg_to_scene = {}
    for sc in scene_defs:
        s1, s2 = sc["seg_range"]
        for s_id in range(s1, s2 + 1):
            seg_to_scene[s_id] = sc["scene_id"]

    words = []
    wid = 1
    for s in raw["segments"]:
        s_id = s["id"]
        sc_id = seg_to_scene.get(s_id, 12)
        for w in s["words"]:
            sub_txt = WORD_OVERRIDES.get(wid, w["word"])
            rs, re_t = refine_and_trim_word_v2(clean_audio, sr, wid, w["word"], w["start"], w["end"])
            words.append({
                "word_id": wid,
                "segment_id": s_id,
                "scene_id": sc_id,
                "word": w["word"],
                "subtitle_text": sub_txt,
                "raw_start": w["start"],
                "real_start": rs,
                "end": re_t,
                "duration": round(re_t - rs, 4)
            })
            wid += 1

    # Ensure strictly non-overlapping monotonic word spans
    for i in range(1, len(words)):
        if words[i]["real_start"] < words[i - 1]["end"]:
            mid = round(0.5 * (words[i]["real_start"] + words[i - 1]["end"]), 4)
            words[i - 1]["end"] = max(words[i - 1]["real_start"] + 0.05, mid)
            words[i]["real_start"] = mid
            if words[i]["end"] < words[i]["real_start"] + 0.05:
                words[i]["end"] = round(words[i]["real_start"] + 0.06, 4)

    # Group contiguous words where gap <= 0.13s within the same segment/scene;
    # cut all gaps > 0.13s and insert a clean zero-noise micro-pause (0.055s intra-sentence, 0.14s inter-sentence)
    pad_before = 0.028
    pad_after = 0.038
    max_contig_gap = 0.13

    phrase_groups = []
    for w in words:
        if w["subtitle_text"] == "" and w["word_id"] in {29, 30}:
            # Merged into #31 MascotaMás
            continue
        if not phrase_groups:
            phrase_groups.append({
                "scene_id": w["scene_id"],
                "segment_id": w["segment_id"],
                "words": [w]
            })
            continue
        prev_grp = phrase_groups[-1]
        prev_w = prev_grp["words"][-1]
        gap = w["real_start"] - prev_w["end"]
        has_punct = any(p in prev_w["subtitle_text"] for p in ".,;:")
        if gap <= max_contig_gap and w["scene_id"] == prev_grp["scene_id"] and not has_punct:
            prev_grp["words"].append(w)
        else:
            phrase_groups.append({
                "scene_id": w["scene_id"],
                "segment_id": w["segment_id"],
                "words": [w]
            })

    # Assemble voice_track and edited segments/words with pure zero-noise micro-pauses
    edited_cursor = 0.0
    edited_segments = []
    edited_words = []
    audio_pieces = []

    # Measure RMS of phrase chunks for gentle leveling
    chunk_rms_dbs = []
    raw_chunks = []
    for grp in phrase_groups:
        src_s = max(0.0, round(grp["words"][0]["real_start"] - pad_before, 4))
        src_e = min(orig_dur, round(grp["words"][-1]["end"] + pad_after, 4))
        if src_e <= src_s + 0.06:
            src_e = min(orig_dur, round(src_s + 0.08, 4))
        s_i = int(round(src_s * sr))
        e_i = int(round(src_e * sr))
        chunk = clean_audio[s_i:e_i].copy()
        rms = float(np.sqrt(np.mean(chunk ** 2) + 1e-12))
        db = 20.0 * math.log10(max(rms, 1e-5))
        raw_chunks.append((src_s, src_e, chunk, db))
        chunk_rms_dbs.append(db)

    target_db = float(np.median(chunk_rms_dbs))

    for g_idx, grp in enumerate(phrase_groups):
        src_s, src_e, chunk, db = raw_chunks[g_idx]
        # Gentle syllable-group leveling (-2.5dB to +4.5dB)
        gain_db = max(-2.5, min(4.5, target_db - db))
        chunk *= float(10.0 ** (gain_db / 20.0))

        # Smooth 16ms cosine fade-in and 20ms cosine fade-out on every phrase island
        # so room reverb tail and breath onset are 100% damped
        fi = min(len(chunk) // 3, int(0.016 * sr))
        fo = min(len(chunk) // 3, int(0.020 * sr))
        if fi > 1:
            chunk[:fi] *= 0.5 * (1.0 - np.cos(np.linspace(0, math.pi, fi, dtype=np.float32)))
        if fo > 1:
            chunk[-fo:] *= 0.5 * (1.0 + np.cos(np.linspace(0, math.pi, fo, dtype=np.float32)))

        # Determine clean digital pause after this phrase group
        last_w_txt = grp["words"][-1]["subtitle_text"]
        if g_idx == len(phrase_groups) - 1:
            pause_after = 0.25
        elif any(ch in last_w_txt for ch in ".?!"):
            pause_after = 0.14
        elif "," in last_w_txt or grp["segment_id"] != phrase_groups[g_idx + 1]["segment_id"]:
            pause_after = 0.09
        else:
            pause_after = 0.045

        pause_samples = int(round(pause_after * sr))
        full_piece = np.concatenate([chunk, np.zeros(pause_samples, dtype=np.float32)])
        piece_dur = round(len(full_piece) / sr, 4)
        ed_s = round(edited_cursor, 4)
        ed_e = round(ed_s + piece_dur, 4)

        edited_segments.append({
            "segment_id": g_idx + 1,
            "scene_id": grp["scene_id"],
            "source_start": src_s,
            "source_end": src_e,
            "duration": piece_dur,
            "edited_start": ed_s,
            "edited_end": ed_e,
            "word_ids": [w["word_id"] for w in grp["words"]]
        })

        spoken_dur = len(chunk) / sr
        for w in grp["words"]:
            w_rel_s = max(0.0, w["real_start"] - src_s)
            w_rel_e = min(spoken_dur, w["end"] - src_s)
            w_ed_s = round(ed_s + w_rel_s, 4)
            w_ed_e = round(max(w_ed_s + 0.06, ed_s + w_rel_e), 4)
            w_item = dict(w)
            w_item["edited_start"] = w_ed_s
            w_item["edited_end"] = w_ed_e
            w_item["src_start"] = w["real_start"]
            w_item["src_end"] = w["end"]
            edited_words.append(w_item)

        audio_pieces.append(full_piece)
        edited_cursor = ed_e

    voice_track = np.concatenate(audio_pieces).astype(np.float32)
    total_edited_duration = round(len(voice_track) / sr, 4)

    # Save pre-loudnorm stereo WAV (100% pure studio voice, ZERO annoying BGM or SFX!)
    pre_norm = os.path.join(WORK_DIR, "v2_pre_loudnorm.wav")
    peak = max(float(np.max(np.abs(voice_track))), 1e-6)
    if peak > 0.96:
        voice_track = voice_track / peak * 0.94
    sf.write(pre_norm, np.column_stack([voice_track, voice_track]).astype(np.float32), sr)

    final_wav = os.path.join(WORK_DIR, "v2_final_audio_14lufs.wav")
    subprocess.run(
        [FFMPEG_BIN, "-y", "-i", pre_norm, "-af", "loudnorm=I=-14.0:TP=-1.0:LRA=9", "-ar", str(sr), "-ac", "2", final_wav],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    # Highlight & Bounce scheduling
    last_bounce_t = -999.0
    for w in edited_words:
        sub_t = w.get("subtitle_text", w["word"])
        tokens = [normalize_clean(tok) for tok in sub_t.split() if normalize_clean(tok)]
        is_hl = any(tok in HIGHLIGHT_KEYWORDS or any(ch.isdigit() for ch in tok) for tok in tokens)
        w["is_yellow"] = is_hl
        if is_hl and (w["edited_start"] - last_bounce_t >= 5.0):
            w["trigger_bounce"] = True
            last_bounce_t = w["edited_start"]
        else:
            w["trigger_bounce"] = False

    subtitle_blocks = build_desktop_subtitle_blocks(edited_words)

    edited_scenes = []
    for idx, sc in enumerate(scene_defs):
        sc_words = [w for w in edited_words if w["scene_id"] == sc["scene_id"]]
        s_start = 0.0 if idx == 0 else edited_scenes[-1]["edited_end"]
        s_end = total_edited_duration if idx == len(scene_defs) - 1 else round(sc_words[-1]["edited_end"], 4)
        sc_copy = dict(sc)
        sc_copy["edited_start"] = round(s_start, 4)
        sc_copy["edited_end"] = round(s_end, 4)
        sc_copy["edited_duration"] = round(s_end - s_start, 4)
        edited_scenes.append(sc_copy)

    plan = {
        "version": "v2",
        "source_video": SOURCE_VIDEO,
        "original_duration_sec": orig_dur,
        "edited_duration_sec": total_edited_duration,
        "segments": edited_segments,
        "words": edited_words,
        "subtitle_blocks": subtitle_blocks,
        "scenes": edited_scenes
    }
    plan_path = os.path.join(WORK_DIR, "desktop_edit_plan_v2.json")
    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)

    print(
        f"[V2 PLAN READY] {orig_dur:.2f}s -> {total_edited_duration:.2f}s "
        f"({len(edited_segments)} clean islands, {len(edited_words)} words, {len(subtitle_blocks)} subtitle blocks)."
    )
    return plan, final_wav


def build_v3_plan_and_audio():
    plan_path = os.path.join(WORK_DIR, "desktop_edit_plan_v3.json")
    final_wav = os.path.join(WORK_DIR, "voice_v3_final_14lufs.wav")
    if os.path.exists(plan_path) and os.path.exists(final_wav):
        with open(plan_path, "r", encoding="utf-8") as f:
            return json.load(f), final_wav
    print("\n========================================================")
    print("BUILDING VERSION 3: VOZ ARGENTINA PREMIUM (es-AR-ElenaNeural)")
    print("========================================================")
    sr = 44100
    tts_json = os.path.join(WORK_DIR, "tts_v3_segments", "all_tts_segments.json")
    with open(tts_json, "r", encoding="utf-8") as f:
        tts_segs = json.load(f)

    scene_defs = get_scene_definitions()
    seg_to_scene = {}
    for sc in scene_defs:
        s1, s2 = sc["seg_range"]
        for s_id in range(s1, s2 + 1):
            seg_to_scene[s_id] = sc["scene_id"]

    edited_cursor = 0.0
    edited_segments = []
    edited_words = []
    audio_pieces = []

    for idx, tseg in enumerate(tts_segs):
        sid = tseg["seg_id"]
        sc_id = seg_to_scene.get(sid, 12)
        y_seg, _ = sf.read(tseg["wav_path"], dtype="float32")
        if y_seg.ndim > 1:
            y_seg = np.mean(y_seg, axis=1)

        # Natural breath pause between TTS segments (0.14s normal, 0.22s on scene change)
        next_sc_id = seg_to_scene.get(tts_segs[idx + 1]["seg_id"], 12) if idx + 1 < len(tts_segs) else sc_id
        if idx == len(tts_segs) - 1:
            pause_after = 0.28
        elif next_sc_id != sc_id:
            pause_after = 0.20
        else:
            pause_after = 0.12

        pause_samples = int(round(pause_after * sr))
        full_piece = np.concatenate([y_seg, np.zeros(pause_samples, dtype=np.float32)])
        piece_dur = round(len(full_piece) / sr, 4)

        ed_s = round(edited_cursor, 4)
        ed_e = round(ed_s + piece_dur, 4)

        orig_words = tseg["words"]
        bounds = tseg["boundaries"]
        src_s = orig_words[0]["src_start"]
        src_e = orig_words[-1]["src_end"]

        edited_segments.append({
            "segment_id": sid,
            "scene_id": sc_id,
            "source_start": src_s,
            "source_end": src_e,
            "duration": piece_dur,
            "edited_start": ed_s,
            "edited_end": ed_e,
            "word_ids": [w["word_id"] for w in orig_words]
        })

        # Map each word in orig_words to its exact WordBoundary in `bounds`
        # Note: some orig_words have 2 tokens in subtitle_text (e.g. "grilla de", "público o", "Mascota Más.")
        b_cursor = 0
        n_bounds = len(bounds)
        n_orig = len(orig_words)
        spoken_dur = len(y_seg) / sr

        for w_i, w in enumerate(orig_words):
            n_toks = max(1, len(w["spoken_text"].split()))
            if b_cursor < n_bounds:
                b_start = bounds[b_cursor]["start"]
                b_end_idx = min(n_bounds - 1, b_cursor + n_toks - 1)
                b_end = bounds[b_end_idx]["end"]
                b_cursor = b_end_idx + 1
            else:
                frac0 = w_i / max(1, n_orig)
                frac1 = (w_i + 1) / max(1, n_orig)
                b_start = round(frac0 * spoken_dur, 4)
                b_end = round(frac1 * spoken_dur, 4)

            w_ed_s = round(ed_s + b_start, 4)
            w_ed_e = round(max(w_ed_s + 0.06, ed_s + b_end), 4)
            w_item = dict(w)
            w_item["segment_id"] = sid
            w_item["scene_id"] = sc_id
            w_item["edited_start"] = w_ed_s
            w_item["edited_end"] = w_ed_e
            edited_words.append(w_item)

        audio_pieces.append(full_piece)
        edited_cursor = ed_e

    voice_track = np.concatenate(audio_pieces).astype(np.float32)
    total_edited_duration = round(len(voice_track) / sr, 4)

    # Studio mastering on es-AR-ElenaNeural (warm broadcast EQ + -14 LUFS)
    pre_norm = os.path.join(WORK_DIR, "v3_pre_loudnorm.wav")
    sf.write(pre_norm, np.column_stack([voice_track, voice_track]).astype(np.float32), sr)

    final_wav = os.path.join(WORK_DIR, "v3_final_audio_14lufs.wav")
    af_v3 = (
        "highpass=f=85:poles=2,"
        "equalizer=f=160:t=q:w=1.2:g=1.5,"
        "equalizer=f=3200:t=q:w=1.1:g=1.8,"
        "loudnorm=I=-14.0:TP=-1.0:LRA=9"
    )
    subprocess.run(
        [FFMPEG_BIN, "-y", "-i", pre_norm, "-af", af_v3, "-ar", str(sr), "-ac", "2", final_wav],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    # Highlight & Bounce scheduling
    last_bounce_t = -999.0
    for w in edited_words:
        sub_t = w.get("subtitle_text", w["word"])
        tokens = [normalize_clean(tok) for tok in sub_t.split() if normalize_clean(tok)]
        is_hl = any(tok in HIGHLIGHT_KEYWORDS or any(ch.isdigit() for ch in tok) for tok in tokens)
        w["is_yellow"] = is_hl
        if is_hl and (w["edited_start"] - last_bounce_t >= 5.0):
            w["trigger_bounce"] = True
            last_bounce_t = w["edited_start"]
        else:
            w["trigger_bounce"] = False

    subtitle_blocks = build_desktop_subtitle_blocks(edited_words)

    edited_scenes = []
    for idx, sc in enumerate(scene_defs):
        sc_words = [w for w in edited_words if w["scene_id"] == sc["scene_id"]]
        s_start = 0.0 if idx == 0 else edited_scenes[-1]["edited_end"]
        s_end = total_edited_duration if idx == len(scene_defs) - 1 else round(sc_words[-1]["edited_end"], 4)
        sc_copy = dict(sc)
        sc_copy["edited_start"] = round(s_start, 4)
        sc_copy["edited_end"] = round(s_end, 4)
        sc_copy["edited_duration"] = round(s_end - s_start, 4)
        edited_scenes.append(sc_copy)

    plan = {
        "version": "v3",
        "source_video": SOURCE_VIDEO,
        "original_duration_sec": 406.548,
        "edited_duration_sec": total_edited_duration,
        "segments": edited_segments,
        "words": edited_words,
        "subtitle_blocks": subtitle_blocks,
        "scenes": edited_scenes
    }
    plan_path = os.path.join(WORK_DIR, "desktop_edit_plan_v3.json")
    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)

    print(
        f"[V3 PLAN READY] 406.55s -> {total_edited_duration:.2f}s "
        f"({len(edited_segments)} segments, {len(edited_words)} words synced word-by-word, {len(subtitle_blocks)} subtitle blocks)."
    )
    return plan, final_wav


def render_subtitles_only(plan: dict, subs_dir: str, out_w: int = 1920, out_h: int = 1080, fps: int = 30):
    os.makedirs(subs_dir, exist_ok=True)
    mg_root = os.path.join(WORK_DIR, "mg_desktop")
    docks_dir = os.path.join(mg_root, "docks")
    html_uri = "file:///" + os.path.abspath(TEMPLATE_HTML).replace("\\", "/")

    # Reuse already-rendered scenes & docks if present!
    scenes_needed = []
    for sc in plan["scenes"]:
        sid = sc["scene_id"]
        sc_dir = os.path.join(mg_root, f"scene_{sid}")
        if len(glob.glob(os.path.join(sc_dir, "frame_*.png"))) < 21:
            scenes_needed.append({
                "scene_id": sid,
                "graphic_config": sc["graphic_config"],
                "out_dir": sc_dir
            })

    subs_existing = len(glob.glob(os.path.join(subs_dir, "sub_*.png")))
    if scenes_needed or subs_existing < len(plan["subtitle_blocks"]):
        jobs = {
            "width": out_w,
            "height": out_h,
            "fps": fps,
            "html_url": html_uri,
            "scenes": scenes_needed,
            "subtitle_blocks": plan["subtitle_blocks"],
            "subs_out_dir": subs_dir,
            "docks_out_dir": docks_dir
        }
        jobs_json = os.path.join(subs_dir, "jobs_subs.json")
        with open(jobs_json, "w", encoding="utf-8") as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)

        print(f"[PLAYWRIGHT] Rendering {len(plan['subtitle_blocks'])} subtitle blocks -> {subs_dir}...")
        subprocess.run(["node", NODE_RENDER_SCRIPT, jobs_json], check=True, cwd=BASE_DIR)

    dock_overlays = {}
    for ch in range(1, 5):
        p = os.path.join(docks_dir, f"dock_ch_{ch}.png")
        dock_overlays[ch] = cv2.imread(p, cv2.IMREAD_UNCHANGED)

    scene_overlays = {}
    for sc in plan["scenes"]:
        sid = sc["scene_id"]
        sc_dir = os.path.join(mg_root, f"scene_{sid}")
        pngs = sorted(glob.glob(os.path.join(sc_dir, "frame_*.png")))
        scene_overlays[sid] = [cv2.imread(p, cv2.IMREAD_UNCHANGED) for p in pngs]

    return scene_overlays, dock_overlays


def build_word_synced_time_lookup(plan: dict, out_fps: int = 30) -> np.ndarray:
    """
    Builds a per-frame lookup array mapping edited frame index f_idx -> source audio time src_audio_t,
    anchored word-by-word within each segment so that every spoken word coincides with the exact UI frame!
    """
    total_dur = plan["edited_duration_sec"]
    total_frames = max(1, int(round(total_dur * out_fps)))
    t_grid = np.arange(total_frames, dtype=np.float64) / float(out_fps)

    if plan.get("version") == "v3":
        # Word-by-word monotonic anchor curve within each segment
        ed_anchors = [0.0]
        src_anchors = [plan["words"][0]["src_start"]]
        for seg in plan["segments"]:
            seg_words = [w for w in plan["words"] if w["segment_id"] == seg["segment_id"]]
            for w in seg_words:
                t_ed = w["edited_start"]
                t_src = max(src_anchors[-1], w["src_start"])
                if t_ed > ed_anchors[-1] + 0.01:
                    ed_anchors.append(t_ed)
                    src_anchors.append(t_src)
                t_ed_end = w["edited_end"]
                t_src_end = max(src_anchors[-1], w["src_end"])
                if t_ed_end > ed_anchors[-1] + 0.01:
                    ed_anchors.append(t_ed_end)
                    src_anchors.append(t_src_end)
        if total_dur > ed_anchors[-1]:
            ed_anchors.append(total_dur)
            src_anchors.append(src_anchors[-1])

        raw_lookup = np.interp(t_grid, ed_anchors, src_anchors)
        # Smooth with a 9-frame (0.3s) Savitzky/moving window inside segments to keep mouse cursor velocity smooth
        kernel = np.ones(9, dtype=np.float64) / 9.0
        smooth_lookup = np.convolve(raw_lookup, kernel, mode="same")
        smooth_lookup[:4] = raw_lookup[:4]
        smooth_lookup[-4:] = raw_lookup[-4:]
        return np.maximum.accumulate(smooth_lookup)
    else:
        # Segment-level exact mapping for v2
        lookup = np.zeros(total_frames, dtype=np.float64)
        segments = plan["segments"]
        s_idx = 0
        n_segs = len(segments)
        for f_i, t in enumerate(t_grid):
            while s_idx < n_segs - 1 and t > segments[s_idx]["edited_end"]:
                s_idx += 1
            seg = segments[s_idx]
            prog = max(0.0, min(1.0, (t - seg["edited_start"]) / max(0.005, seg["edited_end"] - seg["edited_start"])))
            lookup[f_i] = seg["source_start"] + prog * (seg["source_end"] - seg["source_start"])
        return lookup


def composite_version_video(plan: dict, scene_overlays: dict, subs_dir: str, final_wav: str, out_mp4: str):
    out_w, out_h, out_fps = 1920, 1080, 30
    total_dur = plan["edited_duration_sec"]
    total_frames = max(1, int(round(total_dur * out_fps)))
    src_time_lookup = build_word_synced_time_lookup(plan, out_fps=out_fps)

    cap = cv2.VideoCapture(plan["source_video"])
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 29.604962
    src_total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 11355)

    ffmpeg_cmd = [
        FFMPEG_BIN, "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-pix_fmt", "bgr24",
        "-s", f"{out_w}x{out_h}",
        "-r", str(out_fps),
        "-i", "-",
        "-i", final_wav,
        "-c:v", "libx264",
        "-crf", "17",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        out_mp4
    ]

    print(f"[RENDER {plan.get('version', '').upper()}] Compositing {total_frames} frames (1920x1080 @ {out_fps}fps) -> {out_mp4}...")
    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

    scenes = plan["scenes"]
    sub_blocks = plan["subtitle_blocks"]

    sub_cache = {}
    def get_sub_bgra(block_id: int, scale: float = 1.0):
        key = (block_id, round(scale, 3))
        if key in sub_cache:
            return sub_cache[key]
        p = os.path.join(subs_dir, f"sub_{block_id}.png")
        bgra = cv2.imread(p, cv2.IMREAD_UNCHANGED)
        if bgra is None:
            return None
        if abs(scale - 1.0) > 0.005:
            sh, sw = bgra.shape[:2]
            nw, nh = max(1, int(round(sw * scale))), max(1, int(round(sh * scale)))
            resized = cv2.resize(bgra, (nw, nh), interpolation=cv2.INTER_LINEAR)
            out = np.zeros_like(bgra)
            ox = (sw - nw) // 2
            oy = (sh - nh) // 2
            if ox >= 0 and oy >= 0:
                out[oy:oy+nh, ox:ox+nw] = resized
            else:
                sx = max(0, -ox)
                sy = max(0, -oy)
                out[:, :] = resized[sy:sy+sh, sx:sx+sw]
            bgra = out
        sub_cache[key] = bgra
        return bgra

    cur_src_idx = -1
    cur_src_frame = None
    side_card_alpha = 0.0
    sc_idx = 0
    sub_idx = 0

    for f_idx in range(total_frames):
        t = f_idx / float(out_fps)

        while sc_idx < len(scenes) - 1 and t > scenes[sc_idx]["edited_end"]:
            sc_idx += 1
        scene = scenes[sc_idx]

        while sub_idx < len(sub_blocks) and t > sub_blocks[sub_idx]["end"]:
            sub_idx += 1
        sub_block = sub_blocks[sub_idx] if (sub_idx < len(sub_blocks) and sub_blocks[sub_idx]["start"] <= t <= sub_blocks[sub_idx]["end"]) else None

        src_audio_t = float(src_time_lookup[f_idx])
        src_video_t = src_audio_t * AV_CLOCK_RATIO
        target_src_idx = max(0, min(src_total_frames - 1, int(round(src_video_t * src_fps))))

        if cur_src_frame is None or target_src_idx != cur_src_idx:
            if target_src_idx < cur_src_idx or (target_src_idx - cur_src_idx) > 60 or cur_src_idx < 0:
                cap.set(cv2.CAP_PROP_POS_FRAMES, target_src_idx)
                ret, frm = cap.read()
                if ret and frm is not None:
                    cur_src_frame = frm
                    cur_src_idx = target_src_idx
            else:
                while cur_src_idx < target_src_idx:
                    ret, frm = cap.read()
                    cur_src_idx += 1
                    if ret and frm is not None:
                        cur_src_frame = frm

        if cur_src_frame is None:
            cur_src_frame = np.zeros((1008, 1920, 3), dtype=np.uint8)

        canvas = np.zeros((out_h, out_w, 3), dtype=np.uint8)
        canvas[:1008, :1920] = cur_src_frame

        backdrop_luma = float(np.mean(canvas[500, 400]))
        modal_is_open = backdrop_luma < 175.0

        bg_bgr = canvas[78, 850]
        path_slice = canvas[80:110, 518:830].copy()
        canvas[80:110, 230:860] = bg_bgr
        canvas[80:110, 230:230 + URL_PREFIX_W] = np.clip(
            bg_bgr.astype(np.int16) + URL_PREFIX_DELTA, 0, 255
        ).astype(np.uint8)
        canvas[80:110, 230 + URL_PREFIX_W:230 + URL_PREFIX_W + path_slice.shape[1]] = path_slice
        canvas[4:52, 1430:1712] = canvas[25:26, 1420:1421]

        if not modal_is_open:
            canvas[926:962, 310:1900] = canvas[930:931, 320:321]
            side_card_alpha = max(0.0, side_card_alpha - 0.16)
        else:
            side_card_alpha = min(1.0, side_card_alpha + 0.16)

        sc_frames = scene_overlays[scene["scene_id"]]
        sc_rel_f = max(0, min(len(sc_frames) - 1, int(round((t - scene["edited_start"]) * out_fps))))
        ov_bgra = sc_frames[sc_rel_f]

        blend_roi_bgra(canvas, ov_bgra, 0, 62, 1380, 1920, 1.0)
        blend_roi_bgra(canvas, ov_bgra, 915, 1080, 0, 1920, 1.0)

        if side_card_alpha > 0.01:
            blend_roi_bgra(canvas, ov_bgra, 165, 955, 1420, 1915, side_card_alpha)

        if sub_block:
            sub_scale = 1.0
            if sub_block.get("has_bounce"):
                bt = sub_block.get("bounce_start", sub_block["start"])
                if bt <= t <= bt + 0.26:
                    u = (t - bt) / 0.26
                    sub_scale = 1.0 + 0.14 * math.sin(math.pi * u)
            sub_bgra = get_sub_bgra(sub_block["block_id"], scale=sub_scale)
            if sub_bgra is not None:
                sh, sw = sub_bgra.shape[:2]
                sy1, sx1 = 966, 295
                roi = canvas[sy1:sy1+sh, sx1:sx1+sw].astype(np.float32)
                sa = sub_bgra[:, :, 3:4].astype(np.float32) / 255.0
                sbgr = sub_bgra[:, :, :3].astype(np.float32)
                canvas[sy1:sy1+sh, sx1:sx1+sw] = (roi * (1.0 - sa) + sbgr * sa).astype(np.uint8)

        proc.stdin.write(canvas.tobytes())
        if f_idx % 1200 == 0 and f_idx > 0:
            print(f"  -> [{plan.get('version', '').upper()}] {f_idx}/{total_frames} frames ({f_idx/total_frames*100:.1f}%)")

    proc.stdin.close()
    proc.wait()
    cap.release()
    print(f"[DONE {plan.get('version', '').upper()}] Exported -> {out_mp4}")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "both"

    if target in ("v2", "both"):
        plan_v2, wav_v2 = build_v2_plan_and_audio()
        subs_v2_dir = os.path.join(WORK_DIR, "mg_desktop", "subs_v2")
        scene_ovs, _ = render_subtitles_only(plan_v2, subs_v2_dir)
        out_v2 = os.path.join(WORK_DIR, "MascotaMas - Instructivo Calendarios (v2 - Voz Original Mejorada).mp4")
        composite_version_video(plan_v2, scene_ovs, subs_v2_dir, wav_v2, out_v2)
        build_verification_grid(out_v2, os.path.join(BASE_DIR, "verification_grid_v2.jpg"))

    if target in ("v3", "both"):
        plan_v3, wav_v3 = build_v3_plan_and_audio()
        subs_v3_dir = os.path.join(WORK_DIR, "mg_desktop", "subs_v3")
        scene_ovs, _ = render_subtitles_only(plan_v3, subs_v3_dir)
        out_v3 = os.path.join(WORK_DIR, "MascotaMas - Instructivo Calendarios (v3 - Voz Argentina Premium).mp4")
        composite_version_video(plan_v3, scene_ovs, subs_v3_dir, wav_v3, out_v3)
        build_verification_grid(out_v3, os.path.join(BASE_DIR, "verification_grid_v3.jpg"))
        build_verification_grid(out_v3, os.path.join(BASE_DIR, "verification_grid.jpg"))
