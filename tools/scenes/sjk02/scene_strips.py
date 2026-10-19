r"""완성본에서 장면마다 4프레임(15·40·65·90%)을 뽑아 장면 8개씩 한 장(가로 4칸 × 세로 8줄)으로 묶는다 — 장면 전수 눈 검수용.
  py -3.11 tools/scenes/sjk02/scene_strips.py <완성본.mp4> <출력 폴더>
"""
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
TL = json.loads((ROOT / "_tmp/sjk02/timeline.json").read_text(encoding="utf-8"))
FONT = ImageFont.truetype(str(ROOT / "소재/fonts/Pretendard-Bold.otf"), 22)


def grab(src, t, w=480):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", src, "-frames:v", "1", "-vf", f"scale={w}:-2", "-f", "image2pipe", "-vcodec", "png", "-"],
                       capture_output=True, check=True)
    from io import BytesIO
    return Image.open(BytesIO(r.stdout)).convert("RGB")


def main():
    src, out = sys.argv[1], Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    W, H, LAB = 480, 270, 30
    for page in range(0, len(TL), 8):
        chunk = TL[page:page + 8]
        sheet = Image.new("RGB", (W * 4, (H + LAB) * len(chunk)), (20, 23, 27))
        d = ImageDraw.Draw(sheet)
        for r, s in enumerate(chunk):
            y = r * (H + LAB)
            d.text((8, y + 4), f"s{s['scene']:02d}  {s['t0']:.1f}–{s['t1']:.1f}s  " + " / ".join(l["text"] for l in s["lines"])[:110], font=FONT, fill=(235, 235, 235))
            for c, k in enumerate((0.15, 0.4, 0.65, 0.9)):
                sheet.paste(grab(src, s["t0"] + (s["t1"] - s["t0"]) * k), (c * W, y + LAB))
        p = out / f"strip_{page // 8 + 1:02d}.jpg"
        sheet.save(p, quality=86)
        print(p, flush=True)


if __name__ == "__main__":
    main()
