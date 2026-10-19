# -*- coding: utf-8 -*-
"""s18 용 — n18_crt_tv.png 의 초록 화면을 어두운 유리색으로 지운 사본(_tmp/sjk02/tex/n18_clean.png)과
초록 화면 모양 마스크(_tmp/sjk02/tex/n18_mask.png, 불투명 = 화면)를 만든다. 사진 좌표 1536x1024.
    py -3.11 tools/scenes/sjk02/make_n18_clean.py
"""
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "소재/sjk02/codex/n18_crt_tv.png"
OUT = ROOT / "_tmp/sjk02/tex"
OUT.mkdir(parents=True, exist_ok=True)

a = np.array(Image.open(SRC).convert("RGB")).astype(np.int16)
r, g, b = a[..., 0], a[..., 1], a[..., 2]
m = ((g > 150) & (g - r > 70) & (g - b > 70)).astype(np.uint8) * 255
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
mm = cv2.dilate(m, np.ones((5, 5), np.uint8)) > 0
c = a.astype(np.uint8).copy()
c[mm] = (18, 20, 24)
sp = (g - np.maximum(r, b) > 30) & ~mm
c[sp, 1] = np.maximum(c[sp, 0], c[sp, 2]).astype(np.uint8)
Image.fromarray(c).save(OUT / "n18_clean.png")
rgba = np.zeros((a.shape[0], a.shape[1], 4), np.uint8)
rgba[..., :3] = 255
rgba[..., 3] = cv2.dilate(m, np.ones((3, 3), np.uint8))
Image.fromarray(rgba).save(OUT / "n18_mask.png")
print("ok", OUT)
