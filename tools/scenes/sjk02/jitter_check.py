# -*- coding: utf-8 -*-
"""렌더 떨림 검사 — 이웃 프레임 위상 상관으로 화면 이동량을 재서 «앞뒤로 번갈아 튀는» 프레임을 센다.
html_motion 은 브라우저 여러 개가 프레임을 나눠 찍으므로, 페이지가 뜰 때 잰 값(글꼴 로드 전후 getBoundingClientRect 등)이
브라우저마다 다르면 프레임이 번갈아 어긋나 화면이 떨린다(10-16 장면 33 «성장할 수 있는 기회» 7:36 사장님 지적).
    py -3.11 tools/scenes/sjk02/jitter_check.py [s33 s41 …]   (없으면 render/sNN.mp4 전부)
"""
import glob
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
W, H = 480, 270


def check(mp4):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp4), "-vf", f"scale={W}:{H},format=gray", "-f", "rawvideo", "-"],
                         capture_output=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.float32)
    mv = [cv2.phaseCorrelate(fr[i - 1], fr[i])[0] for i in range(1, len(fr))]
    flips = 0
    for a, b in zip(mv, mv[1:]):
        for k in (0, 1):
            if abs(a[k]) > 1.0 and abs(b[k]) > 1.0 and np.sign(a[k]) != np.sign(b[k]) and abs(abs(a[k]) - abs(b[k])) < 0.35 * max(abs(a[k]), abs(b[k])):
                flips += 1
                break
    return len(fr), flips


def main():
    names = sys.argv[1:] or sorted(Path(p).stem for p in glob.glob(str(ROOT / "_tmp/sjk02/render/s[0-9][0-9].mp4")))
    bad = []
    for n in names:
        nf, fl = check(ROOT / f"_tmp/sjk02/render/{n}.mp4")
        mark = "  ← 떨림" if fl >= 3 else ""
        print(f"{n}: 프레임 {nf} · 번갈아 튐 {fl}{mark}")
        if fl >= 3:
            bad.append(n)
    print("떨림 장면:", " ".join(bad) or "없음")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
