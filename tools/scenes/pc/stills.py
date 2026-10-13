# -*- coding: utf-8 -*-
"""검수용 정지 프레임: still_times.txt 의 시각마다 compose 로 1프레임 렌더 → _tmp/pc/stills/<초>.png"""
import subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
ts = [float(x) for x in open(ROOT / "_tmp/pc/still_times.txt").read().split()]
if len(sys.argv) > 1:
    ts = [float(x) for x in sys.argv[1:]]
for t in ts:
    mp4 = ROOT / f"_tmp/pc/stills/{t:.2f}.mp4"
    subprocess.run([sys.executable, str(ROOT / "tools/auto/compose.py"), str(ROOT / "_tmp/pc/plan.json"), "--from", f"{t}", "--to", f"{t + 0.04}", "--out", str(mp4)],
                   capture_output=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mp4), "-frames:v", "1", str(mp4.with_suffix(".png"))])
    mp4.unlink(missing_ok=True)
    print(t, flush=True)
