# -*- coding: utf-8 -*-
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
TTS_ROOT = os.path.join(WORK_DIR, "tts_storytelling")
sys.path.insert(0, WORK_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "scripts"))

from storytelling_data import (
    V1_SCENES,
    V2_SCENES,
    V2_WORD_OVERRIDES,
    V3_SCENES,
    V3_WORD_OVERRIDES,
    SPOTS_30S,
)
from edit_instructivo_desktop import (
    FFMPEG_BIN,
    TEMPLATE_HTML,
    NODE_RENDER_SCRIPT,
    HIGHLIGHT_KEYWORDS,
    normalize_clean,
    build_desktop_subtitle_blocks,
    blend_roi_bgra,
    build_verification_grid,
)

# Expand highlight keywords for Videos 2 & 3
EXTRA_HIGHLIGHTS = {
    "tablero", "columnas", "bloques", "bloque", "ficha", "fichas", "historia",
    "clínica", "manualmente", "color", "mediodía", "deslanado", "corte", "baño",
    "ingreso", "egreso", "check-in", "check-out", "365", "año", "90.000", "$90.000",
    "noventa", "cuarenta", "trescientos", "sesenta", "cinco", "doce", "cuatro"
}
ALL_HIGHLIGHT_KEYWORDS = set(HIGHLIGHT_KEYWORDS) | EXTRA_HIGHLIGHTS

SHORT_CONNECTORS = {
    "el", "la", "los", "las", "un", "una", "de", "del", "al", "a", "en",
    "y", "o", "que", "se", "si", "es", "por", "su", "lo", "no", "va"
}

SOURCE_CONFIGS = {
    "v1": {
        "video": os.path.join(WORK_DIR, "MascotaMas - VeteBosco - Google Chrome 2026-11-08 10-28-13.mp4"),
        "wav_44k": os.path.join(WORK_DIR, "audio_44k.wav"),
        "raw_transcript": os.path.join(WORK_DIR, "raw_transcript.json"),
        "av_clock_ratio": 383.550533 / 406.548375,
        "noise_windows": [(5.2, 7.8), (133.2, 135.8)],
    },
    "v2": {
        "video": os.path.join(WORK_DIR, "CALENDARIO Y TURNOS POR SERVICIO.mp4"),
        "wav_44k": os.path.join(WORK_DIR, "audio_servicios_44k.wav"),
        "raw_transcript": os.path.join(WORK_DIR, "raw_transcript_servicios.json"),
        "av_clock_ratio": 327.180000 / 347.285333,
        "noise_windows": [(0.2, 3.5), (298.0, 301.0)],
    },
    "v3": {
        "video": os.path.join(WORK_DIR, "CALENDARIO Y TURNOS GUARDERIA.mp4"),
        "wav_44k": os.path.join(WORK_DIR, "audio_guarderia_44k.wav"),
        "raw_transcript": os.path.join(WORK_DIR, "raw_transcript_guarderia.json"),
        "av_clock_ratio": 141.283733 / 143.360000,
        "noise_windows": [(0.1, 2.1), (107.8, 109.8)],
    },
}


def mark_highlights_and_bounces(edited_words: list):
    last_bounce_t = -999.0
    for w in edited_words:
        sub_t = w.get("subtitle_text", w["word"])
        tokens = [normalize_clean(tok) for tok in sub_t.split() if normalize_clean(tok)]
        is_hl = any(tok in ALL_HIGHLIGHT_KEYWORDS or any(ch.isdigit() for ch in tok) for tok in tokens)
        w["is_yellow"] = is_hl
        if is_hl and (w["edited_start"] - last_bounce_t >= 4.5):
            w["trigger_bounce"] = True
            last_bounce_t = w["edited_start"]
        else:
            w["trigger_bounce"] = False


def prepare_clean_studio_voice(video_key: str) -> tuple[np.ndarray, int]:
    cfg = SOURCE_CONFIGS[video_key]
    clean_eq_wav = os.path.join(WORK_DIR, f"audio_{video_key}_studio_clean.wav")
    if os.path.exists(clean_eq_wav):
        y, sr = sf.read(clean_eq_wav, dtype="float32")
        if y.ndim > 1:
            y = np.mean(y, axis=1)
        return y, sr

    print(f"[{video_key.upper()} DSP] Spectral noise cancellation + echo suppression on {cfg['wav_44k']}...")
    audio, sr = sf.read(cfg["wav_44k"], dtype="float32")
    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)

    b_hp, a_hp = butter(3, 95.0 / (sr / 2), btype="high")
    audio_hp = filtfilt(b_hp, a_hp, audio).astype(np.float32)

    noise_pieces = []
    for ns, ne in cfg["noise_windows"]:
        s_i = max(0, int(ns * sr))
        e_i = min(len(audio_hp), int(ne * sr))
        if e_i > s_i:
            noise_pieces.append(audio_hp[s_i:e_i])
    noise_clip = np.concatenate(noise_pieces) if noise_pieces else audio_hp[:int(2.0 * sr)]

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

    pre_eq_wav = os.path.join(WORK_DIR, f"audio_{video_key}_pre_eq.wav")
    sf.write(pre_eq_wav, (audio_dn * sample_gain).astype(np.float32), sr)

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


def refine_and_trim_word_generic(audio: np.ndarray, sr: int, word_str: str, raw_s: float, raw_e: float) -> tuple[float, float]:
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
        gap = 0
        for k in range(len(act)):
            if not act[k]:
                gap += 1
            else:
                if 0 < gap <= 5:
                    act[k - gap:k] = True
                gap = 0
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
            best_isl = max(islands, key=lambda x: (x[1] - x[0]) + (2 if x[0] > 2 else 0))
            s_t = raw_s + best_isl[0] * 0.01
            e_t = min(raw_e, raw_s + (best_isl[1] + 1) * 0.01)

    clean_w = normalize_clean(word_str)
    dur = e_t - s_t
    if clean_w in SHORT_CONNECTORS:
        max_conn_dur = 0.23 if clean_w in {"por", "los", "las", "del", "una"} else 0.19
        if dur > max_conn_dur:
            e_t = s_t + max_conn_dur
    else:
        max_word_dur = max(0.38, min(0.88, 0.095 * len(clean_w) + 0.12))
        if dur > max_word_dur:
            e_t = s_t + max_word_dur

    if e_t - s_t < 0.055:
        e_t = s_t + 0.065
    return round(s_t, 4), round(e_t, 4)


def build_original_voice_plan_and_audio(video_key: str, scene_defs: list, word_overrides: dict, job_tag: str):
    plan_path = os.path.join(WORK_DIR, f"plan_{job_tag}.json")
    final_wav = os.path.join(WORK_DIR, f"{job_tag}_final_14lufs.wav")
    if os.path.exists(plan_path) and os.path.exists(final_wav):
        with open(plan_path, "r", encoding="utf-8") as f:
            return json.load(f), final_wav
    print(f"\n========================================================")
    print(f"BUILDING ORIGINAL VOICE ENHANCED ({job_tag})")
    print(f"========================================================")
    cfg = SOURCE_CONFIGS[video_key]
    clean_audio, sr = prepare_clean_studio_voice(video_key)
    orig_dur = round(len(clean_audio) / sr, 3)

    with open(cfg["raw_transcript"], "r", encoding="utf-8") as f:
        raw = json.load(f)

    seg_to_scene = {}
    for sc in scene_defs:
        s1, s2 = sc["seg_range"]
        for s_id in range(s1, s2 + 1):
            seg_to_scene[s_id] = sc["scene_id"]

    words = []
    wid = 1
    max_sc_id = scene_defs[-1]["scene_id"]
    for s in raw["segments"]:
        s_id = s["id"]
        sc_id = seg_to_scene.get(s_id, max_sc_id)
        for w in s["words"]:
            sub_txt = word_overrides.get(wid, w["word"])
            rs, re_t = refine_and_trim_word_generic(clean_audio, sr, w["word"], w["start"], w["end"])
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

    for i in range(1, len(words)):
        if words[i]["real_start"] < words[i - 1]["end"]:
            mid = round(0.5 * (words[i]["real_start"] + words[i - 1]["end"]), 4)
            words[i - 1]["end"] = max(words[i - 1]["real_start"] + 0.05, mid)
            words[i]["real_start"] = mid
            if words[i]["end"] < words[i]["real_start"] + 0.05:
                words[i]["end"] = round(words[i]["real_start"] + 0.06, 4)

    pad_before = 0.028
    pad_after = 0.038
    max_contig_gap = 0.13

    phrase_groups = []
    for w in words:
        if w["subtitle_text"] == "":
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

    edited_cursor = 0.0
    edited_segments = []
    edited_words = []
    audio_pieces = []

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
        gain_db = max(-2.5, min(4.5, target_db - db))
        chunk *= float(10.0 ** (gain_db / 20.0))

        fi = min(len(chunk) // 3, int(0.016 * sr))
        fo = min(len(chunk) // 3, int(0.020 * sr))
        if fi > 1:
            chunk[:fi] *= 0.5 * (1.0 - np.cos(np.linspace(0, math.pi, fi, dtype=np.float32)))
        if fo > 1:
            chunk[-fo:] *= 0.5 * (1.0 + np.cos(np.linspace(0, math.pi, fo, dtype=np.float32)))

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

    pre_norm = os.path.join(WORK_DIR, f"{job_tag}_pre_loudnorm.wav")
    peak = max(float(np.max(np.abs(voice_track))), 1e-6)
    if peak > 0.96:
        voice_track = voice_track / peak * 0.94
    sf.write(pre_norm, np.column_stack([voice_track, voice_track]).astype(np.float32), sr)

    final_wav = os.path.join(WORK_DIR, f"{job_tag}_final_14lufs.wav")
    subprocess.run(
        [FFMPEG_BIN, "-y", "-i", pre_norm, "-af", "loudnorm=I=-14.0:TP=-1.0:LRA=9", "-ar", str(sr), "-ac", "2", final_wav],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    mark_highlights_and_bounces(edited_words)
    subtitle_blocks = build_desktop_subtitle_blocks(edited_words)

    edited_scenes = []
    for idx, sc in enumerate(scene_defs):
        sc_words = [w for w in edited_words if w["scene_id"] == sc["scene_id"]]
        s_start = 0.0 if idx == 0 else edited_scenes[-1]["edited_end"]
        s_end = total_edited_duration if (idx == len(scene_defs) - 1 or not sc_words) else round(sc_words[-1]["edited_end"], 4)
        sc_copy = dict(sc)
        sc_copy["edited_start"] = round(s_start, 4)
        sc_copy["edited_end"] = round(s_end, 4)
        sc_copy["edited_duration"] = round(s_end - s_start, 4)
        edited_scenes.append(sc_copy)

    plan = {
        "job_tag": job_tag,
        "mode": "original_voice",
        "video_key": video_key,
        "source_video": cfg["video"],
        "av_clock_ratio": cfg["av_clock_ratio"],
        "original_duration_sec": orig_dur,
        "edited_duration_sec": total_edited_duration,
        "segments": edited_segments,
        "words": edited_words,
        "subtitle_blocks": subtitle_blocks,
        "scenes": edited_scenes,
    }
    plan_path = os.path.join(WORK_DIR, f"plan_{job_tag}.json")
    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)

    print(f"[{job_tag}] {orig_dur:.2f}s -> {total_edited_duration:.2f}s ({len(edited_words)} words, {len(subtitle_blocks)} sub blocks)")
    return plan, final_wav


def build_tts_storytelling_plan_and_audio(
    tts_collection_name: str,
    video_key: str,
    scene_defs: list,
    job_tag: str,
    is_spot_30s: bool = False
):
    plan_path = os.path.join(WORK_DIR, f"plan_{job_tag}.json")
    final_wav = os.path.join(WORK_DIR, f"{job_tag}_final_14lufs.wav")
    if os.path.exists(plan_path) and os.path.exists(final_wav):
        with open(plan_path, "r", encoding="utf-8") as f:
            return json.load(f), final_wav
    print(f"\n========================================================")
    print(f"BUILDING STORYTELLING + VOZ ARGENTINA PREMIUM ({job_tag})")
    print(f"========================================================")
    sr = 44100
    cfg = SOURCE_CONFIGS[video_key]
    tts_json = os.path.join(TTS_ROOT, tts_collection_name, "all_segments.json")
    with open(tts_json, "r", encoding="utf-8") as f:
        tts_segs = json.load(f)

    # Calculate pauses: for 30s spots, calibrate pause padding so total duration lands right around 30.0s
    speech_sum = sum(tseg["tts_duration"] for tseg in tts_segs)
    n_segs = len(tts_segs)

    if is_spot_30s:
        target_total = 30.0
        rem = max(0.75, target_total - speech_sum)
        intro_pad = min(0.25, rem * 0.12)
        outro_pad = min(0.45, rem * 0.22)
        inter_pause = (rem - intro_pad - outro_pad) / max(1, n_segs - 1)
        inter_pause = max(0.10, min(0.55, inter_pause))
    else:
        intro_pad = 0.08
        outro_pad = 0.28
        inter_pause = 0.14

    edited_cursor = round(intro_pad, 4)
    edited_segments = []
    edited_words = []
    audio_pieces = [np.zeros(int(round(intro_pad * sr)), dtype=np.float32)]
    wid = 1

    for idx, tseg in enumerate(tts_segs):
        sid = tseg["seg_id"]
        sc_id = tseg["scene_id"]
        y_seg, _ = sf.read(tseg["wav_path"], dtype="float32")
        if y_seg.ndim > 1:
            y_seg = np.mean(y_seg, axis=1)

        next_sc_id = tts_segs[idx + 1]["scene_id"] if idx + 1 < n_segs else sc_id
        if idx == n_segs - 1:
            pause_after = outro_pad
        elif next_sc_id != sc_id and not is_spot_30s:
            pause_after = 0.22
        else:
            pause_after = inter_pause

        pause_samples = int(round(pause_after * sr))
        full_piece = np.concatenate([y_seg, np.zeros(pause_samples, dtype=np.float32)])
        piece_dur = round(len(full_piece) / sr, 4)

        ed_s = round(edited_cursor, 4)
        ed_e = round(ed_s + piece_dur, 4)
        src_s = tseg["src_start"]
        src_e = tseg["src_end"]

        seg_word_ids = []
        for w in tseg["words"]:
            w_ed_s = round(ed_s + w["rel_start"], 4)
            w_ed_e = round(max(w_ed_s + 0.06, ed_s + w["rel_end"]), 4)
            w_item = {
                "word_id": wid,
                "segment_id": sid,
                "scene_id": sc_id,
                "word": w["word"],
                "subtitle_text": w["subtitle_text"],
                "edited_start": w_ed_s,
                "edited_end": w_ed_e,
                "src_start": w["src_start"],
                "src_end": w["src_end"],
            }
            edited_words.append(w_item)
            seg_word_ids.append(wid)
            wid += 1

        edited_segments.append({
            "segment_id": sid,
            "scene_id": sc_id,
            "source_start": src_s,
            "source_end": src_e,
            "duration": piece_dur,
            "edited_start": ed_s,
            "edited_end": ed_e,
            "word_ids": seg_word_ids,
        })

        audio_pieces.append(full_piece)
        edited_cursor = ed_e

    voice_track = np.concatenate(audio_pieces).astype(np.float32)
    total_edited_duration = round(len(voice_track) / sr, 4)

    pre_norm = os.path.join(WORK_DIR, f"{job_tag}_pre_loudnorm.wav")
    sf.write(pre_norm, np.column_stack([voice_track, voice_track]).astype(np.float32), sr)

    final_wav = os.path.join(WORK_DIR, f"{job_tag}_final_14lufs.wav")
    af_tts = (
        "highpass=f=85:poles=2,"
        "equalizer=f=160:t=q:w=1.2:g=1.5,"
        "equalizer=f=3200:t=q:w=1.1:g=1.8,"
        "loudnorm=I=-14.0:TP=-1.0:LRA=9"
    )
    subprocess.run(
        [FFMPEG_BIN, "-y", "-i", pre_norm, "-af", af_tts, "-ar", str(sr), "-ac", "2", final_wav],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    mark_highlights_and_bounces(edited_words)
    subtitle_blocks = build_desktop_subtitle_blocks(edited_words)

    edited_scenes = []
    for idx, sc in enumerate(scene_defs):
        sc_words = [w for w in edited_words if w["scene_id"] == sc["scene_id"]]
        s_start = 0.0 if idx == 0 else edited_scenes[-1]["edited_end"]
        s_end = total_edited_duration if (idx == len(scene_defs) - 1 or not sc_words) else round(sc_words[-1]["edited_end"], 4)
        sc_copy = dict(sc)
        sc_copy["edited_start"] = round(s_start, 4)
        sc_copy["edited_end"] = round(s_end, 4)
        sc_copy["edited_duration"] = round(s_end - s_start, 4)
        edited_scenes.append(sc_copy)

    plan = {
        "job_tag": job_tag,
        "mode": "tts_storytelling",
        "video_key": video_key,
        "source_video": cfg["video"],
        "av_clock_ratio": cfg["av_clock_ratio"],
        "edited_duration_sec": total_edited_duration,
        "segments": edited_segments,
        "words": edited_words,
        "subtitle_blocks": subtitle_blocks,
        "scenes": edited_scenes,
    }
    plan_path = os.path.join(WORK_DIR, f"plan_{job_tag}.json")
    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)

    print(
        f"[{job_tag}] Total Duration: {total_edited_duration:.2f}s "
        f"({len(edited_segments)} segs, {len(edited_words)} words synced word-by-word, {len(subtitle_blocks)} sub blocks)"
    )
    return plan, final_wav


def render_mg_for_plan(plan: dict, out_w: int = 1920, out_h: int = 1080, fps: int = 30):
    job_tag = plan["job_tag"]
    mg_root = os.path.join(WORK_DIR, "mg_jobs", job_tag)
    subs_dir = os.path.join(mg_root, "subs")
    os.makedirs(subs_dir, exist_ok=True)

    html_uri = "file:///" + os.path.abspath(TEMPLATE_HTML).replace("\\", "/")
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
            "docks_out_dir": None
        }
        jobs_json = os.path.join(mg_root, "jobs.json")
        with open(jobs_json, "w", encoding="utf-8") as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)

        print(f"[PLAYWRIGHT {job_tag}] Rendering {len(scenes_needed)} scenes & {len(plan['subtitle_blocks'])} subtitle blocks...")
        subprocess.run(["node", NODE_RENDER_SCRIPT, jobs_json], check=True, cwd=BASE_DIR)

    scene_overlays = {}
    for sc in plan["scenes"]:
        sid = sc["scene_id"]
        sc_dir = os.path.join(mg_root, f"scene_{sid}")
        pngs = sorted(glob.glob(os.path.join(sc_dir, "frame_*.png")))
        scene_overlays[sid] = [cv2.imread(p, cv2.IMREAD_UNCHANGED) for p in pngs]

    return scene_overlays, subs_dir


def build_time_lookup(plan: dict, out_fps: int = 30) -> np.ndarray:
    """
    Maps each output frame f_idx -> source audio timestamp src_audio_t.
    Uses segment-level linear mapping with word-level monotonic anchors within each segment,
    while allowing clean cuts between non-contiguous segments (such as in 30s spots or cut pauses).
    """
    total_dur = plan["edited_duration_sec"]
    total_frames = max(1, int(round(total_dur * out_fps)))
    t_grid = np.arange(total_frames, dtype=np.float64) / float(out_fps)

    lookup = np.zeros(total_frames, dtype=np.float64)
    segments = plan["segments"]
    s_idx = 0
    n_segs = len(segments)

    for f_i, t in enumerate(t_grid):
        while s_idx < n_segs - 1 and t > segments[s_idx]["edited_end"]:
            s_idx += 1
        seg = segments[s_idx]
        ed_s = seg["edited_start"]
        ed_e = seg["edited_end"]
        prog = max(0.0, min(1.0, (t - ed_s) / max(0.005, ed_e - ed_s)))
        lookup[f_i] = seg["source_start"] + prog * (seg["source_end"] - seg["source_start"])

    return lookup


def composite_video_job(plan: dict, scene_overlays: dict, subs_dir: str, final_wav: str, out_mp4: str):
    out_w, out_h, out_fps = 1920, 1080, 30
    total_dur = plan["edited_duration_sec"]
    total_frames = max(1, int(round(total_dur * out_fps)))
    src_time_lookup = build_time_lookup(plan, out_fps=out_fps)
    av_ratio = plan["av_clock_ratio"]
    job_tag = plan["job_tag"]

    cap = cv2.VideoCapture(plan["source_video"])
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 29.5
    src_total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 9000)

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

    print(f"[RENDER {job_tag}] Compositing {total_frames} frames ({total_dur:.2f}s @ {out_fps}fps) -> {os.path.basename(out_mp4)}...")
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
        src_video_t = src_audio_t * av_ratio
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

        # Robust modal detection using top-left sidebar (160, 100) and bottom-left (942, 400)
        backdrop_luma = 0.5 * (float(np.mean(canvas[160, 100])) + float(np.mean(canvas[942, 400])))
        modal_is_open = backdrop_luma < 175.0

        # Pixel-perfect Chrome URL bar prefix replacement:
        # Replaces 'mmas-staging-1a3e2.web.app' (x=238..518) with 'https://gestion.mascotamas.com'
        # while keeping the circular site-settings icon (x=185..225) and shifting the native path suffix (x=518..830).
        bg_bgr = canvas[78, 850]
        path_slice = canvas[80:110, 518:830].copy()
        canvas[80:110, 230:860] = bg_bgr
        canvas[80:110, 230:230 + URL_PREFIX_W] = np.clip(
            bg_bgr.astype(np.int16) + URL_PREFIX_DELTA, 0, 255
        ).astype(np.uint8)
        canvas[80:110, 230 + URL_PREFIX_W:230 + URL_PREFIX_W + path_slice.shape[1]] = path_slice

        # Clean top-right Gemini button
        canvas[4:52, 1430:1712] = canvas[25:26, 1420:1421]

        # Clean pink 'Estás conectado como: vetebosco@gmail.com' banner ONLY when present (admin panel without modal)
        b_px, g_px, _ = [int(x) for x in canvas[942, 400]]
        has_pink_footer = (not modal_is_open) and ((b_px - g_px) >= 8)
        if has_pink_footer:
            canvas[926:962, 310:1900] = canvas[930:931, 320:321]

        if not modal_is_open:
            side_card_alpha = max(0.0, side_card_alpha - 0.18)
        else:
            side_card_alpha = min(1.0, side_card_alpha + 0.18)

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
        if f_idx % 1500 == 0 and f_idx > 0:
            print(f"  -> [{job_tag}] {f_idx}/{total_frames} frames ({f_idx/total_frames*100:.1f}%)")

    proc.stdin.close()
    proc.wait()
    cap.release()
    print(f"[DONE {job_tag}] Exported -> {out_mp4}")


def run_job_and_verify(plan: dict, final_wav: str, out_filename: str, grid_filename: str = None):
    import shutil
    scene_ovs, subs_dir = render_mg_for_plan(plan)
    out_mp4 = os.path.join(WORK_DIR, out_filename)
    composite_video_job(plan, scene_ovs, subs_dir, final_wav, out_mp4)
    editados_dir = os.path.join(BASE_DIR, "editados")
    brutos_dir = os.path.join(BASE_DIR, "brutos")
    os.makedirs(editados_dir, exist_ok=True)
    os.makedirs(brutos_dir, exist_ok=True)
    shutil.copy2(out_mp4, os.path.join(editados_dir, out_filename))
    src_vid = plan.get("source_video", "")
    if src_vid and os.path.exists(src_vid):
        dst_bruto = os.path.join(brutos_dir, os.path.basename(src_vid))
        if not os.path.exists(dst_bruto):
            shutil.copy2(src_vid, dst_bruto)
    if grid_filename:
        grid_path = os.path.join(BASE_DIR, grid_filename)
        build_verification_grid(out_mp4, grid_path)
    return out_mp4


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    if mode in ("full_v1", "all"):
        # 1. Video 1 v4 (Storytelling Ajustado + Voz Argentina Premium)
        plan, wav = build_tts_storytelling_plan_and_audio("v1_story_v4", "v1", V1_SCENES, "v1_story_v4", is_spot_30s=False)
        run_job_and_verify(
            plan, wav,
            "MascotaMas - Instructivo 1 - Tipos de Calendarios (v4 - Storytelling + Voz Argentina Premium).mp4",
            "verification_grid_v1_v4.jpg"
        )

    if mode in ("full_v2", "all"):
        # 2A. Video 2 v1 (Voz Original Mejorada)
        plan_o, wav_o = build_original_voice_plan_and_audio("v2", V2_SCENES, V2_WORD_OVERRIDES, "v2_orig_v1")
        run_job_and_verify(
            plan_o, wav_o,
            "MascotaMas - Instructivo 2 - Calendario y Turnos por Servicio (v1 - Voz Original Mejorada).mp4",
            "verification_grid_v2_v1.jpg"
        )
        # 2B. Video 2 v2 (Storytelling Ajustado + Voz Argentina Premium)
        plan_s, wav_s = build_tts_storytelling_plan_and_audio("v2_story_v2", "v2", V2_SCENES, "v2_story_v2", is_spot_30s=False)
        run_job_and_verify(
            plan_s, wav_s,
            "MascotaMas - Instructivo 2 - Calendario y Turnos por Servicio (v2 - Storytelling + Voz Argentina Premium).mp4",
            "verification_grid_v2_v2.jpg"
        )

    if mode in ("full_v3", "all"):
        # 3A. Video 3 v1 (Voz Original Mejorada)
        plan_o, wav_o = build_original_voice_plan_and_audio("v3", V3_SCENES, V3_WORD_OVERRIDES, "v3_orig_v1")
        run_job_and_verify(
            plan_o, wav_o,
            "MascotaMas - Instructivo 3 - Calendario y Turnos Guarderia (v1 - Voz Original Mejorada).mp4",
            "verification_grid_v3_v1.jpg"
        )
        # 3B. Video 3 v2 (Storytelling Ajustado + Voz Argentina Premium)
        plan_s, wav_s = build_tts_storytelling_plan_and_audio("v3_story_v2", "v3", V3_SCENES, "v3_story_v2", is_spot_30s=False)
        run_job_and_verify(
            plan_s, wav_s,
            "MascotaMas - Instructivo 3 - Calendario y Turnos Guarderia (v2 - Storytelling + Voz Argentina Premium).mp4",
            "verification_grid.jpg"
        )

    if mode in ("spots", "all"):
        # 4. All 9 x 30-second Spots
        for sp in SPOTS_30S:
            sid = sp["spot_id"]
            plan_sp, wav_sp = build_tts_storytelling_plan_and_audio(
                sid, sp["source_video_key"], sp["scenes"], sid, is_spot_30s=True
            )
            run_job_and_verify(
                plan_sp, wav_sp,
                sp["output_filename"],
                f"verification_grid_{sid}.jpg" if sid in ("v1_spot1", "v2_spot3", "v3_spot2") else None
            )
