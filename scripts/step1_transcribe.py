import os
import sys
import json
import math
import shutil
import subprocess
import numpy as np
import soundfile as sf
import cv2
from faster_whisper import WhisperModel

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FFMPEG_BIN = os.path.join(BASE_DIR, "bin", "ffmpeg", "ffmpeg.exe")
FFPROBE_BIN = os.path.join(BASE_DIR, "bin", "ffmpeg", "ffprobe.exe")
YUNET_MODEL = os.path.join(BASE_DIR, "models", "face_detection_yunet_2023mar.onnx")
WORK_DIR = os.path.join(BASE_DIR, "reels_work")
STYLE_PATH = os.path.join(BASE_DIR, "style.json")


def load_style():
    with open(STYLE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_audio_wav(video_path: str, wav_path: str, sr: int = 44100):
    cmd = [
        FFMPEG_BIN, "-y",
        "-i", video_path,
        "-vn", "-ac", "1",
        "-ar", str(sr),
        "-acodec", "pcm_s16le",
        wav_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def refine_word_boundaries(audio: np.ndarray, sr: int, raw_start: float, raw_end: float, threshold_db: float = -38.0):
    """
    Whisper often includes pre-word silence in `word.start`.
    Measures actual voice energy in 5ms windows and trims leading silence to true voice onset.
    """
    s_idx = max(0, int(raw_start * sr))
    e_idx = min(len(audio), int(raw_end * sr))
    if e_idx <= s_idx + int(0.02 * sr):
        return raw_start, raw_end, -45.0

    seg = audio[s_idx:e_idx]
    rms_total = float(np.sqrt(np.mean(seg ** 2) + 1e-12))
    rms_db = 20.0 * math.log10(max(rms_total, 1e-6))

    win = max(1, int(0.005 * sr))  # 5ms window
    n_wins = len(seg) // win
    if n_wins < 3:
        return raw_start, raw_end, round(rms_db, 2)

    frames = seg[: n_wins * win].reshape(n_wins, win)
    win_rms = np.sqrt(np.mean(frames ** 2, axis=1) + 1e-12)
    win_db = 20.0 * np.log10(np.maximum(win_rms, 1e-6))

    peak_db = float(np.max(win_db))
    # Dynamic onset threshold: whichever is higher between absolute threshold_db and (peak_db - 18 dB)
    active_thresh = max(threshold_db, peak_db - 18.0)
    active_indices = np.where(win_db >= active_thresh)[0]

    if len(active_indices) > 0:
        first_win = int(active_indices[0])
        last_win = int(active_indices[-1])
        real_start = raw_start + (first_win * win) / sr
        real_end = min(raw_end, raw_start + ((last_win + 2) * win) / sr)
        if real_end - real_start < 0.04:
            real_end = min(raw_end, real_start + 0.06)
    else:
        real_start, real_end = raw_start, raw_end

    # Recompute RMS on active voice part
    rs_idx = max(0, int(real_start * sr))
    re_idx = min(len(audio), int(real_end * sr))
    if re_idx > rs_idx:
        active_seg = audio[rs_idx:re_idx]
        active_rms = float(np.sqrt(np.mean(active_seg ** 2) + 1e-12))
        rms_db = 20.0 * math.log10(max(active_rms, 1e-6))

    return round(real_start, 4), round(real_end, 4), round(rms_db, 2)


def analyze_video_faces(video_path: str, sample_fps: float = 4.0):
    """
    Samples the video at `sample_fps` using OpenCV YuNet to find:
    1. Face center (cx, cy, w, h) normalized [0..1]
    2. Whether the speaker is looking at the camera vs looking down/away at script
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {"default_face_center": [0.5, 0.38, 0.3, 0.3], "timeline": []}

    vid_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1080)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 1920)
    step = max(1, int(round(vid_fps / sample_fps)))

    detector = None
    if os.path.exists(YUNET_MODEL):
        try:
            detector = cv2.FaceDetectorYN.create(YUNET_MODEL, "", (320, 320), 0.6, 0.3, 5000)
        except Exception:
            detector = None

    timeline = []
    cx_list, cy_list = [], []
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % step == 0:
            t = frame_idx / vid_fps
            looking = True
            face_norm = None
            if detector is not None:
                small = cv2.resize(frame, (320, 320))
                _, faces = detector.detect(small)
                if faces is not None and len(faces) > 0:
                    # Pick largest face
                    best = max(faces, key=lambda f: f[2] * f[3])
                    fx, fy, fw, fh = best[0] / 320.0, best[1] / 320.0, best[2] / 320.0, best[3] / 320.0
                    cx = fx + fw * 0.5
                    cy = fy + fh * 0.5
                    face_norm = [round(float(cx), 4), round(float(cy), 4), round(float(fw), 4), round(float(fh), 4)]
                    cx_list.append(float(cx))
                    cy_list.append(float(cy))

                    # Landmarks: right eye (4,5), left eye (6,7), nose (8,9), right mouth (10,11), left mouth (12,13)
                    re_x, re_y = best[4] / 320.0, best[5] / 320.0
                    le_x, le_y = best[6] / 320.0, best[7] / 320.0
                    nose_x, nose_y = best[8] / 320.0, best[9] / 320.0
                    rm_x, rm_y = best[10] / 320.0, best[11] / 320.0
                    lm_x, lm_y = best[12] / 320.0, best[13] / 320.0

                    eye_mid_y = 0.5 * (re_y + le_y)
                    mouth_mid_y = 0.5 * (rm_y + lm_y)
                    face_vert = max(mouth_mid_y - eye_mid_y, 1e-4)
                    nose_ratio_y = (nose_y - eye_mid_y) / face_vert

                    eye_dist = abs(le_x - re_x)
                    eye_mid_x = 0.5 * (re_x + le_x)
                    yaw_offset = abs(nose_x - eye_mid_x) / max(eye_dist, 1e-4)

                    # Looking down at script pushes nose_ratio_y > 0.68; turning head away pushes yaw_offset > 0.38
                    if nose_ratio_y > 0.69 or yaw_offset > 0.40:
                        looking = False
            timeline.append({
                "time": round(t, 3),
                "face": face_norm,
                "looking_at_camera": bool(looking)
            })
        frame_idx += 1

    cap.release()
    med_cx = float(np.median(cx_list)) if cx_list else 0.5
    med_cy = float(np.median(cy_list)) if cy_list else 0.38
    return {
        "source_width": width,
        "source_height": height,
        "source_fps": round(vid_fps, 3),
        "default_face_center": [round(med_cx, 4), round(med_cy, 4)],
        "timeline": timeline
    }


def lookup_face_at_time(face_data: dict, t: float):
    tl = face_data.get("timeline", [])
    if not tl:
        return True, face_data.get("default_face_center", [0.5, 0.38])
    best = min(tl, key=lambda item: abs(item["time"] - t))
    center = best["face"][:2] if best.get("face") else face_data.get("default_face_center", [0.5, 0.38])
    return best.get("looking_at_camera", True), center


def run_whisper_transcribe(audio_16k: np.ndarray, model_name: str = "large-v3-turbo", vad: bool = True):
    for device, compute_type in [("cuda", "float16"), ("cpu", "int8")]:
        try:
            print(f"[WHISPER] Running {model_name} on {device} ({compute_type})...")
            model = WhisperModel(model_name, device=device, compute_type=compute_type)
            kwargs = {"word_timestamps": True}
            if vad:
                kwargs["vad_filter"] = True
                kwargs["vad_parameters"] = dict(min_silence_duration_ms=250)
            segs_gen, info = model.transcribe(audio_16k, **kwargs)
            segs_list = list(segs_gen)
            return segs_list, info
        except Exception as e:
            print(f"[WHISPER] Fallback from {device}: {e}")
    raise RuntimeError("Could not run faster-whisper transcription.")


def transcribe_video(input_video_path: str, model_name: str = "large-v3-turbo"):
    os.makedirs(WORK_DIR, exist_ok=True)
    style = load_style()
    onset_thresh = style["cuts"].get("voice_onset_trim_threshold_db", -38.0)

    # Copy to safe English path in reels_work
    safe_video = os.path.join(WORK_DIR, "source_input.mp4")
    if os.path.abspath(input_video_path) != os.path.abspath(safe_video):
        shutil.copy2(input_video_path, safe_video)

    wav_path = os.path.join(WORK_DIR, "source_audio.wav")
    extract_audio_wav(safe_video, wav_path, sr=44100)
    audio, sr = sf.read(wav_path, dtype="float32")
    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)
    total_duration = round(len(audio) / sr, 3)

    wav_16k_path = os.path.join(WORK_DIR, "source_audio_16k.wav")
    extract_audio_wav(safe_video, wav_16k_path, sr=16000)
    audio_16k, _ = sf.read(wav_16k_path, dtype="float32")
    if audio_16k.ndim > 1:
        audio_16k = np.mean(audio_16k, axis=1)

    print("[FACE] Analyzing speaker face position and gaze...")
    face_data = analyze_video_faces(safe_video)

    segments_gen, info = run_whisper_transcribe(audio_16k, model_name=model_name, vad=True)

    words = []
    sentences = []
    word_id = 1

    for seg_idx, seg in enumerate(segments_gen):
        seg_words = []
        if not seg.words:
            continue
        for w in seg.words:
            w_text = w.word.strip()
            if not w_text:
                continue
            real_s, real_e, rms_db = refine_word_boundaries(
                audio, sr, float(w.start), float(w.end), threshold_db=onset_thresh
            )
            mid_t = 0.5 * (real_s + real_e)
            looking, face_center = lookup_face_at_time(face_data, mid_t)
            w_entry = {
                "word_id": word_id,
                "sentence_id": seg_idx + 1,
                "word": w_text,
                "raw_start": round(float(w.start), 4),
                "real_start": real_s,
                "end": real_e,
                "duration": round(real_e - real_s, 4),
                "rms_db": rms_db,
                "probability": round(float(w.probability), 3),
                "looking_at_camera": looking,
                "face_center": face_center
            }
            words.append(w_entry)
            seg_words.append(w_entry)
            word_id += 1

        if seg_words:
            s_rms = float(np.mean([x["rms_db"] for x in seg_words]))
            s_look = sum(1 for x in seg_words if x["looking_at_camera"]) / len(seg_words) >= 0.5
            sentences.append({
                "sentence_id": seg_idx + 1,
                "text": " ".join(x["word"] for x in seg_words),
                "start": seg_words[0]["real_start"],
                "end": seg_words[-1]["end"],
                "word_ids": [x["word_id"] for x in seg_words],
                "avg_rms_db": round(s_rms, 2),
                "looking_at_camera": s_look
            })

    # Compute median voice RMS to flag whispered words
    if words:
        med_rms = float(np.median([w["rms_db"] for w in words]))
        for w in words:
            w["is_whispering"] = bool(w["rms_db"] < (med_rms - 9.5))
        for s in sentences:
            s["is_whispering"] = bool(s["avg_rms_db"] < (med_rms - 8.5))
    else:
        med_rms = -24.0

    result = {
        "source_video": input_video_path,
        "safe_video": safe_video,
        "safe_audio": wav_path,
        "language": info.language,
        "original_duration_sec": total_duration,
        "median_rms_db": round(med_rms, 2),
        "face_metadata": {
            "source_width": face_data["source_width"],
            "source_height": face_data["source_height"],
            "source_fps": face_data["source_fps"],
            "default_face_center": face_data["default_face_center"]
        },
        "sentences": sentences,
        "words": words
    }

    json_out = os.path.join(WORK_DIR, "transcription_table.json")
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # Also save human-readable markdown table
    md_out = os.path.join(WORK_DIR, "transcription_table.md")
    lines = [
        "# Tabla de Transcripción por Palabra",
        f"- **Duración original:** `{total_duration}s`",
        f"- **Idioma detectado:** `{info.language}`",
        f"- **Volumen mediano de voz:** `{round(med_rms, 2)} dB`",
        "",
        "| # | Palabra | Inicio Real (s) | Fin (s) | Volumen (dB) | Mira a Cámara | Susurro | Oración |",
        "|---:|:---|---:|---:|---:|:---:|:---:|---:|"
    ]
    for w in words:
        lines.append(
            f"| {w['word_id']} | {w['word']} | {w['real_start']:.3f} | {w['end']:.3f} | "
            f"{w['rms_db']:.1f} | {'Sí' if w['looking_at_camera'] else 'No'} | "
            f"{'Sí' if w.get('is_whispering') else 'No'} | {w['sentence_id']} |"
        )
    with open(md_out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"[STEP 1 DONE] Transcribed {len(words)} words across {len(sentences)} sentences -> {json_out}")
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python step1_transcribe.py <video_path>")
        sys.exit(1)
    transcribe_video(sys.argv[1])
