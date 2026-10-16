# -*- coding: utf-8 -*-
"""1편·2편 나란히 보기(지시서 4장 «같은 간격(10초)으로 뽑은 프레임 띠를 위아래로 붙여 1편대비.jpg»).
줄마다 같은 시각 10칸 — 위 1편(회색 이름표) · 아래 2편(주홍 이름표). 설계자가 보고 «같은 영상처럼 보이는 곳»을 고친다.
    py -3.11 tools/scenes/sjk02/compare_ep1.py [1편.mp4] [2편.mp4] [출력.jpg]
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
STEP, TW, TH, PER = 10.0, 320, 180, 10


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                capture_output=True, text=True).stdout.strip())


def frames(p, n, tmp, tag):
    out = []
    for k in range(n):
        f = Path(tmp) / f"{tag}_{k:03d}.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{k * STEP + 0.5:.2f}", "-i", str(p), "-frames:v", "1",
                        "-vf", f"scale={TW}:{TH}", str(f)], check=True)
        out.append(Image.open(f).convert("RGB") if f.exists() else Image.new("RGB", (TW, TH), (40, 40, 40)))
    return out


def main():
    a = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "납품/성제관01/성제관01_자막없음.mp4"
    b = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "납품/성제관02/성제관02_자막없음.mp4"
    o = Path(sys.argv[3]) if len(sys.argv) > 3 else ROOT / "납품/성제관02/1편대비.jpg"
    n = int(min(dur(a), dur(b)) // STEP) + 1
    with tempfile.TemporaryDirectory() as tmp:
        A, B = frames(a, n, tmp, "a"), frames(b, n, tmp, "b")
    rows = (n + PER - 1) // PER
    LW, GAP = 70, 14
    img = Image.new("RGB", (LW + PER * TW, rows * (2 * TH + GAP)), (245, 245, 243))
    d = ImageDraw.Draw(img)
    try:
        ft = ImageFont.truetype(str(ROOT / "소재/fonts/Pretendard-Bold.otf"), 22)
    except Exception:
        ft = ImageFont.load_default()
    for r in range(rows):
        y = r * (2 * TH + GAP)
        d.rectangle([0, y, LW - 6, y + TH], fill=(154, 160, 166)); d.text((10, y + 70), "1편", fill="white", font=ft)
        d.rectangle([0, y + TH, LW - 6, y + 2 * TH], fill=(240, 90, 40)); d.text((10, y + TH + 70), "2편", fill="white", font=ft)
        for c in range(PER):
            k = r * PER + c
            if k >= n:
                break
            img.paste(A[k], (LW + c * TW, y)); img.paste(B[k], (LW + c * TW, y + TH))
            d.text((LW + c * TW + 6, y + 4), f"{int(k * STEP // 60)}:{int(k * STEP % 60):02d}", fill="white", font=ft)
    o.parent.mkdir(parents=True, exist_ok=True)
    img.save(o, quality=82)
    print(o, img.size, "칸", n)


if __name__ == "__main__":
    main()
