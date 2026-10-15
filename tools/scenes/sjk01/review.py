# -*- coding: utf-8 -*-
"""장면 클립 검토용 — 고르게 6장(또는 지정 초) 뽑아 한 장으로. py -3.11 tools/scenes/sjk01/review.py 5 6 8 ..."""
import subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parents[3]
F = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", 22)
for a in sys.argv[1:]:
    n = int(a); p = ROOT / f"_tmp/sjk01/render/s{n:02d}.mp4"
    if not p.exists():
        print("없음", n); continue
    try:
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout)
    except ValueError:
        print("읽기 실패(렌더 중?)", n); continue
    ts = [dur * (k + 0.5) / 6 for k in range(6)]
    S = Image.new("RGB", (3 * 640, 2 * 360))
    for k, t in enumerate(ts):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(p), "-frames:v", "1", "-s", "640x360", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        if len(raw) < 640 * 360 * 3:
            continue
        im = Image.frombytes("RGB", (640, 360), raw[:640 * 360 * 3])
        ImageDraw.Draw(im).text((8, 6), f"s{n:02d} {t:.1f}s", fill=(255, 0, 255), font=F)
        S.paste(im, ((k % 3) * 640, (k // 3) * 360))
    out = ROOT / f"_tmp/sjk01/review/s{n:02d}.jpg"; out.parent.mkdir(parents=True, exist_ok=True); S.save(out, quality=85)
    print(out, f"{dur:.2f}s")
