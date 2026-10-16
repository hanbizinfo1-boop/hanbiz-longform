# -*- coding: utf-8 -*-
"""세로 쇼츠 검토 — 고르게 8장. py -3.11 tools/scenes/sjk02/review_v.py S4 S5"""
import subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parents[3]
F = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", 20)
for n in sys.argv[1:]:
    p = ROOT / f"_tmp/sjk02/render/sh_{n}.mp4"
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout)
    S = Image.new("RGB", (8 * 270, 480))
    for k in range(8):
        t = dur * (k + 0.5) / 8
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(p), "-frames:v", "1", "-s", "270x480", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        if len(raw) < 270 * 480 * 3: continue
        im = Image.frombytes("RGB", (270, 480), raw[:270 * 480 * 3]); ImageDraw.Draw(im).text((4, 450), f"{t:.1f}s", fill=(255, 0, 255), font=F)
        S.paste(im, (k * 270, 0))
    S.save(ROOT / f"_tmp/sjk02/review/sh_{n}.jpg", quality=85); print(n, dur)
