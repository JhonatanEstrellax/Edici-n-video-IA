import os
import re

conv_dir = r"C:\Users\Demiante\.gemini\antigravity\brain\88556d39-9f52-4d70-8b46-4262f87f0cd8"
print("=== Files in brain/88556d39-9f52-4d70-8b46-4262f87f0cd8 ===")
for root, dirs, files in os.walk(conv_dir):
    if ".system_generated" in root:
        continue
    for f in files:
        print(os.path.join(root, f))

print("\n=== Extracting file paths from transcript.jsonl ===")
tr_path = os.path.join(conv_dir, ".system_generated", "logs", "transcript.jsonl")
if os.path.exists(tr_path):
    with open(tr_path, encoding="utf-8", errors="ignore") as fp:
        txt = fp.read()
    # Find all Windows/Unix paths ending in .png, .jpg, .webp, .html, .md
    matches = set(re.findall(r"[A-Za-z]:[\\/][^\"'\n\r<>|*?]+\.(?:png|jpg|jpeg|webp|html)", txt))
    for m in sorted(matches):
        norm = m.replace("\\\\", "\\")
        exists = os.path.exists(norm)
        if exists:
            print(f"[EXISTS] {norm}")
    print("\n=== Top directories mentioned in transcript ===")
    dirs_found = set()
    for m in matches:
        norm = m.replace("\\\\", "\\")
        dirs_found.add(os.path.dirname(norm))
    for d in sorted(dirs_found):
        if os.path.exists(d):
            print(f"[DIR EXISTS] {d} ({len(os.listdir(d))} items)")
