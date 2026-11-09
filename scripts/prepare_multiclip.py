import os
import subprocess
import cv2

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK_DIR = os.path.join(BASE_DIR, "reels_work")
FFMPEG_BIN = os.path.join(BASE_DIR, "bin", "ffmpeg", "ffmpeg.exe")

CLIPS = ["1.mp4", "2.mp4", "3.mp4"]


def main():
    for i, c in enumerate(CLIPS, 1):
        p = os.path.join(WORK_DIR, c)
        cap = cv2.VideoCapture(p)
        n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 1)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        print(f"Clip {i} ({c}): {n} frames, {n/fps:.2f}s @ {fps}fps")
        for pos_name, frame_idx in [("start", 5), ("mid", n // 2), ("end", max(0, n - 10))]:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frm = cap.read()
            if ret:
                cv2.imwrite(os.path.join(WORK_DIR, f"thumb_clip{i}_{pos_name}.jpg"), frm)
        cap.release()

    # Concatenate using ffmpeg filter_complex so timestamps and audio sync are 100% seamless
    out_mp4 = os.path.join(WORK_DIR, "combined_source.mp4")
    cmd = [
        FFMPEG_BIN, "-y",
        "-i", os.path.join(WORK_DIR, CLIPS[0]),
        "-i", os.path.join(WORK_DIR, CLIPS[1]),
        "-i", os.path.join(WORK_DIR, CLIPS[2]),
        "-filter_complex", "[0:v][0:a][1:v][1:a][2:v][2:a]concat=n=3:v=1:a=1[v][a]",
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-crf", "14", "-preset", "fast",
        "-c:a", "aac", "-b:a", "192k",
        out_mp4
    ]
    subprocess.run(cmd, check=True)
    print(f"[OK] Created {out_mp4} ({os.path.getsize(out_mp4)} bytes)")


if __name__ == "__main__":
    main()
