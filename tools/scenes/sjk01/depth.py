# -*- coding: utf-8 -*-
"""사진 → 깊이 지도(Depth Anything V2) — 2.5D 카메라 이동(블렌더 변위 메시)용.
    py -3.11 tools/scenes/sjk01/depth.py 소재/sjk01/codex/c00_night_street.png [...]
출력: _tmp/sjk01/depth/<이름>.npy (상대 깊이 0~1, 클수록 가까움) + _depth.png(확인용)
"""
import sys
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from transformers import pipeline

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "_tmp/sjk01/depth"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pipe = pipeline("depth-estimation", model="depth-anything/Depth-Anything-V2-Base-hf", device=0 if torch.cuda.is_available() else -1)
    for p in sys.argv[1:]:
        im = Image.open(p).convert("RGB")
        r = pipe(im)
        d = np.array(r["predicted_depth"].squeeze().cpu(), dtype=np.float32)
        d = np.array(Image.fromarray(d).resize(im.size, Image.BICUBIC))
        d = (d - d.min()) / (d.max() - d.min() + 1e-6)
        np.save(OUT / (Path(p).stem + ".npy"), d)
        Image.fromarray((d * 255).astype(np.uint8)).save(OUT / (Path(p).stem + "_depth.png"))
        print(Path(p).stem, d.shape)


if __name__ == "__main__":
    main()
