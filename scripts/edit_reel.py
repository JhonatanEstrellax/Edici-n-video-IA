import os
import sys
import glob

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK_DIR = os.path.join(BASE_DIR, "reels_work")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from step1_transcribe import transcribe_video
from step2_build_script import generate_corrected_script
from step3_plan_cuts import plan_cuts
from step4_render_and_export import render_final_video
from step5_verify import verify_final_video

IGNORED_NAMES = {
    "reel_editado.mp4",
    "final_output.mp4",
    "source_input.mp4",
    "reference_reel.mp4"
}


def find_input_video(explicit_path: str = None) -> str:
    if explicit_path and os.path.exists(explicit_path):
        return os.path.abspath(explicit_path)

    exts = ("*.mp4", "*.mov", "*.mkv", "*.webm", "*.m4v")
    candidates = []
    for folder in [BASE_DIR, WORK_DIR]:
        if not os.path.exists(folder):
            continue
        for ext in exts:
            for p in glob.glob(os.path.join(folder, ext)):
                if os.path.basename(p).lower() not in IGNORED_NAMES:
                    candidates.append(p)

    if not candidates:
        return None

    # Pick most recently modified video
    candidates.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return os.path.abspath(candidates[0])


def run_full_pipeline(video_path: str = None, output_path: str = None):
    target_video = find_input_video(video_path)
    if not target_video:
        print("NO_VIDEO_FOUND")
        return None

    if output_path is None:
        stem = os.path.splitext(os.path.basename(target_video))[0]
        output_path = os.path.join(BASE_DIR, f"{stem}_editado.mp4")

    print(f"=== INICIANDO EDICIÓN AUTOMÁTICA DE REEL: {target_video} ===")
    # ① Transcribe audio with word-level timestamps & voice onset refinement
    transcribe_video(target_video, model_name="large-v3-turbo")

    # ② Build corrected script & visual scene composition
    generate_corrected_script()

    # ③ Plan cuts, subtitle blocks, yellow highlights, bounce emphasis & SFX
    plan_cuts()

    # ④ & ⑤ Render HTML+GSAP motion graphics, master -14 LUFS audio, and export final MP4
    render_final_video(output_path)

    # [4. Autoverificación] Re-transcribe, check audio/video anomalies, and generate frame grid
    report = verify_final_video(output_path)
    print(f"=== EDICIÓN COMPLETADA: {output_path} ===")
    return report


if __name__ == "__main__":
    in_vid = sys.argv[1] if len(sys.argv) > 1 else None
    out_vid = sys.argv[2] if len(sys.argv) > 2 else None
    run_full_pipeline(in_vid, out_vid)
