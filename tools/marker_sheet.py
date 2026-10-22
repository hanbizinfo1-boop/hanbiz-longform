# -*- coding: utf-8 -*-
"""표시(동그라미·밑줄·박스) 맞춤 검수판 — 10-22 사장님 «이런거 좀 검수할떄 잘좀 잡아줘» · «이것도 안맞잖아».

장면 렌더의 sNN_events.json 에서 role 이 marker 인 신호마다, 그려지기를 마친 뒤(t + 0.8초) 한 장을 뽑아
한 판에 모은다. 표시가 대상(글자·사람·물건)을 제대로 감싸는지 눈으로 보는 판이다 — 8장 장면 판 사이에 빠지지 않게.

    py -3.11 tools/marker_sheet.py <render 폴더> <출력 폴더> [sNN ...]
"""
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 960, 540


def grab(src, t):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(src), "-frames:v", "1",
                          "-vf", f"scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return Image.frombytes("RGB", (W, H), raw) if len(raw) == W * H * 3 else None


def main():
    rd, out = Path(sys.argv[1]), Path(sys.argv[2])
    only = set(sys.argv[3:])
    out.mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", 26)
    shots = []
    for ev in sorted(rd.glob("s[0-9]*_events.json")):
        name = ev.name.split("_")[0]
        if only and name not in only:
            continue
        src = rd / f"{name}.mp4"
        d = json.loads(ev.read_text(encoding="utf-8"))
        for e in d.get("events", []):
            if e.get("role") != "marker":
                continue
            t = min(e["t"] + 0.8, d.get("duration", e["t"] + 1) - 0.05)
            im = grab(src, t)
            if im is None:
                continue
            ImageDraw.Draw(im).rectangle([0, 0, 330, 36], fill=(0, 0, 0))
            ImageDraw.Draw(im).text((6, 3), f"{name} {e.get('id', '')} {t:.1f}s", font=font, fill=(255, 230, 0))
            shots.append(im)
    for i in range(0, len(shots), 6):
        sh = Image.new("RGB", (W * 2, H * 3), (30, 30, 30))
        for j, im in enumerate(shots[i:i + 6]):
            sh.paste(im, ((j % 2) * W, (j // 2) * H))
        sh.save(out / f"mk_{i // 6:02d}.jpg", quality=82)
    print(len(shots), "markers")


if __name__ == "__main__":
    main()
