# -*- coding: utf-8 -*-
"""자막만 다시 굽기 — 자막 없는 완성본 + lines.json(sub_t0/sub_t1) → 자막 구운 완성본(소리 같이 묶음).
전체 조립(assemble.py)을 다시 돌리지 않고 자막 시각만 고쳤을 때 쓴다. 자막 모양은 assemble.CAP_STYLE 그대로.
    py -3.11 tools/scenes/sjk02/burn_subs.py <자막없음.mp4> <소리.wav> <출력.mp4>
"""
import bisect
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.auto.compose import Captions  # noqa: E402
from tools.scenes.sjk02.assemble import CAP_STYLE, W, H, FN, FD, cap_text  # noqa: E402


def main():
    src, wav, out = sys.argv[1:4]
    lines = json.load(open(ROOT / "_tmp/sjk02/audio/lines.json", encoding="utf-8"))
    capf = ROOT / "_tmp/sjk02/sub/captions.json"
    json.dump([{"t0": r["sub_t0"], "t1": r["sub_t1"], "text": cap_text(r["text"])} for r in lines], open(capf, "w", encoding="utf-8"), ensure_ascii=False)
    caps = Captions(str(capf), CAP_STYLE)
    t0s = [c["t0"] for c in caps.caps]
    rd = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE, bufsize=W * H * 3 * 4)
    en = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", f"{FN}/{FD}", "-i", "-",
                           "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "h264_nvenc", "-preset", "p6", "-rc", "vbr", "-cq", "17", "-b:v", "0",
                           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    n = 0
    while True:
        buf = rd.stdout.read(W * H * 3)
        if len(buf) < W * H * 3:
            break
        fr = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        t = n * FD / FN
        i = bisect.bisect_right(t0s, t) - 1
        if i >= 0 and t < caps.caps[i]["t1"]:
            fr = fr.copy()
            rgb, al, y0 = caps.rgba(i)
            h = al.shape[0]
            fr[y0:y0 + h] = (rgb * al + fr[y0:y0 + h].astype(np.float32) * (1 - al)).astype(np.uint8)
        en.stdin.write(fr.tobytes())
        n += 1
        if n % 6000 == 0:
            print(f"  {t:.0f}s", flush=True)
    en.stdin.close(); en.wait()
    print("완료", n, "프레임 →", out)


if __name__ == "__main__":
    main()
