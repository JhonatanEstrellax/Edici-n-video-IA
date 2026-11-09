# -*- coding: utf-8 -*-
import os
import cv2
import numpy as np

BASE_DIR = r"c:\IA\Edicion de videos"
WORK_DIR = os.path.join(BASE_DIR, "reels_work")
MODEL_PATH = os.path.join(BASE_DIR, "models", "face_detection_yunet_2023mar.onnx")

detector = cv2.FaceDetectorYN.create(MODEL_PATH, "", (540, 960), 0.5, 0.3, 5000)

for cname in ["v6_clip1_frente.mp4", "v6_clip2_tres_cuartos.mp4", "v6_clip3_frente_cta.mp4"]:
    cap = cv2.VideoCapture(os.path.join(WORK_DIR, cname))
    n_f = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"=== {cname} ({n_f} frames) ===")
    for f_i in [0, 60, 120, 180, 240, 300]:
        cap.set(cv2.CAP_PROP_POS_FRAMES, f_i)
        ret, frm = cap.read()
        if not ret:
            continue
        sm = cv2.resize(frm, (540, 960))
        _, faces = detector.detect(sm)
        if faces is not None and len(faces) > 0:
            x, y, w, h = faces[0][:4]
            cx, cy = (x + w/2)/540.0, (y + h/2)/960.0
            wn, hn = w/540.0, h/960.0
            print(f"  f={f_i:03d}: center=({cx:.3f}, {cy:.3f}), size=({wn:.3f}, {hn:.3f})")
    cap.release()
