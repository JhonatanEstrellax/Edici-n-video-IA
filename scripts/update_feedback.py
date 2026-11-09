import os
import sys
import json
import datetime
import argparse
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STYLE_PATH = os.path.join(BASE_DIR, "style.json")
MANUAL_PATH = os.path.join(BASE_DIR, "Manual_de_edicion.md")
WORK_DIR = os.path.join(BASE_DIR, "reels_work")


def set_nested_key(data: dict, dotted_key: str, val):
    keys = dotted_key.split(".")
    cur = data
    for k in keys[:-1]:
        if k not in cur or not isinstance(cur[k], dict):
            cur[k] = {}
        cur = cur[k]
    cur[keys[-1]] = val


def record_feedback(user_request: str, key_path: str, new_value_str: str):
    with open(STYLE_PATH, "r", encoding="utf-8") as f:
        style = json.load(f)

    # Parse value into int/float/bool/json/str
    try:
        parsed_val = json.loads(new_value_str)
    except Exception:
        parsed_val = new_value_str

    if key_path:
        set_nested_key(style, key_path, parsed_val)

    today = datetime.date.today().isoformat()
    entry = {
        "date": today,
        "request": user_request,
        "parameter": f"{key_path} = {json.dumps(parsed_val, ensure_ascii=False)}" if key_path else "Ajuste de regla",
        "status": "Activo"
    }
    style.setdefault("feedback_history", []).append(entry)

    with open(STYLE_PATH, "w", encoding="utf-8") as f:
        json.dump(style, f, ensure_ascii=False, indent=2)

    # Append row to Manual_de_edicion.md
    if os.path.exists(MANUAL_PATH):
        with open(MANUAL_PATH, "r", encoding="utf-8") as f:
            md = f.read().rstrip()
        row = f"| {today} | {user_request} | `{entry['parameter']}` | Activo |"
        md = md + "\n" + row + "\n"
        with open(MANUAL_PATH, "w", encoding="utf-8") as f:
            f.write(md)

    print(f"[FEEDBACK REGISTERED] {entry}")


def analyze_reference_reel(url: str):
    """
    Downloads a reference Reel using yt-dlp, transcribes it with faster-whisper,
    measures its pacing (max pause, speech rate) and adapts style.json.
    """
    os.makedirs(WORK_DIR, exist_ok=True)
    ref_mp4 = os.path.join(WORK_DIR, "reference_reel.mp4")
    ytdlp_exe = os.path.join(BASE_DIR, ".venv", "Scripts", "yt-dlp.exe")

    subprocess.run(
        [ytdlp_exe, "-f", "mp4/best", "-o", ref_mp4, "--force-overwrites", url],
        check=True
    )

    from step1_transcribe import transcribe_video
    res = transcribe_video(ref_mp4, model_name="large-v3-turbo")
    words = res.get("words", [])
    gaps = []
    for i in range(1, len(words)):
        g = words[i]["real_start"] - words[i - 1]["end"]
        if 0.02 <= g <= 0.6:
            gaps.append(g)

    adapted_pause = round(float(sum(gaps) / len(gaps)), 2) if gaps else 0.14
    adapted_pause = max(0.08, min(0.25, adapted_pause))
    record_feedback(
        f"Adaptar estilo a Reel de referencia ({url})",
        "cuts.max_sentence_pause_sec",
        str(adapted_pause)
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=str, help="User feedback description")
    parser.add_argument("--key", type=str, default="", help="Dotted key in style.json")
    parser.add_argument("--value", type=str, default="", help="New value for key")
    parser.add_argument("--analyze-url", type=str, default="", help="Reel URL to analyze and adapt style")
    args = parser.parse_args()

    if args.analyze_url:
        analyze_reference_reel(args.analyze_url)
    elif args.request:
        record_feedback(args.request, args.key, args.value)
