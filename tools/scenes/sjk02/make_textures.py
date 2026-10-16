# -*- coding: utf-8 -*-
"""성제관02 — 감열지(영수증 종이) 질감 PNG. 콘크리트·벽·어두운 탁자는 Codex 질감 사진(소재/sjk02/codex/t_*.png).
    py -3.11 tools/scenes/sjk02/make_textures.py   → _tmp/sjk02/tex/thermal.png (600×1200, 세로로 이어 붙여 씀)
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "_tmp/sjk02/tex"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(7)
    w, h = 600, 1200
    base = np.full((h, w), 246.0)
    base += rng.normal(0, 2.2, (h, w))                        # 종이 결
    fib = Image.fromarray(np.clip(rng.normal(128, 40, (h // 4, w // 4)), 0, 255).astype(np.uint8)).resize((w, h), Image.BILINEAR)
    base += (np.asarray(fib, np.float32) - 128) * 0.035
    x = np.linspace(-1, 1, w)[None, :]
    base -= 7 * x ** 6                                         # 가장자리 살짝 말림 그림자
    img = np.stack([base, base - 1.5, base - 3.0], -1)        # 감열지 특유의 차가운 흰색
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.4)).save(OUT / "thermal.png")
    print(OUT / "thermal.png")


if __name__ == "__main__":
    main()
