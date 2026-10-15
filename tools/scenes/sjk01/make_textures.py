# -*- coding: utf-8 -*-
"""성제관01 — 장면 바탕 질감 PNG(단색 판 금지 — 종이 결·먹 무대·남색 방·인쇄 종이).

    py -3.11 tools/scenes/sjk01/make_textures.py   → _tmp/sjk01/tex/*.png
"""
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "_tmp/sjk01/tex"
rng = np.random.default_rng(14)


def noise(h, w, scale):
    small = rng.standard_normal((max(2, h // scale), max(2, w // scale))).astype(np.float32)
    return cv2.resize(small, (w, h), interpolation=cv2.INTER_CUBIC)


def fibers(h, w, n, length, col):
    m = np.zeros((h, w), np.float32)
    for _ in range(n):
        x, y = rng.integers(0, w), rng.integers(0, h)
        a = rng.uniform(0, np.pi)
        L = rng.integers(length // 2, length)
        x2, y2 = int(x + np.cos(a) * L), int(y + np.sin(a) * L)
        cv2.line(m, (x, y), (x2, y2), float(rng.uniform(0.3, 1.0)), 1, cv2.LINE_AA)
    return m * col


def paper(base, w=1920, h=1080, grain=6.0, blotch=7.0, fib=0.0, vignette=0.10):
    b = np.array(base, np.float32)[None, None, :]
    g = noise(h, w, 1) * grain + noise(h, w, 3) * grain * 0.6 + noise(h, w, 90) * blotch + noise(h, w, 400) * blotch * 0.8
    img = b + g[..., None]
    if fib:
        img -= fibers(h, w, 2600, 40, fib)[..., None]
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    img *= (1 - vignette * np.clip(r - 0.35, 0, 1.2))[..., None]
    return np.clip(img, 0, 255).astype(np.uint8)


def save(name, rgb):
    OUT.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgb).save(OUT / name)
    print(name)


def main():
    save("paper_cream.png", paper((236, 232, 224), grain=5, blotch=2.2, fib=7))          # 종이 #ECE8E0
    save("paper_print.png", paper((246, 245, 240), grain=3, blotch=2.5, fib=4, vignette=0.02, w=1600, h=2200))  # 출력 종이
    save("ink_stage.png", paper((22, 24, 28), grain=3, blotch=1.6, vignette=0.55))       # 먹 무대
    save("navy_room.png", paper((15, 27, 46), grain=2.5, blotch=2.0, vignette=0.50))     # 숫자의 방
    save("chalk_black.png", paper((34, 38, 36), grain=5, blotch=4, vignette=0.30))
    save("map_paper.png", paper((228, 224, 210), grain=4, blotch=2.5, fib=6, vignette=0.15))
    save("night_desk.png", paper((24, 20, 16), grain=3, blotch=2.5, vignette=0.60))     # 어두운 책상


def wood(w=1920, h=1080):
    y = np.arange(h, dtype=np.float32)[:, None]
    x = np.arange(w, dtype=np.float32)[None, :]
    warp = noise(h, w, 60) * 18 + noise(h, w, 300) * 40
    rings = np.sin((y + warp) / 7.0 + noise(h, w, 25) * 0.8) * 0.5 + 0.5
    base = np.array([58, 40, 28], np.float32)
    img = base[None, None, :] * (0.75 + 0.35 * rings[..., None]) + noise(h, w, 1)[..., None] * 3
    img *= (0.9 + 0.1 * np.sin(x / 400.0))[..., None]
    return np.clip(img, 0, 255).astype(np.uint8)


if __name__ == "__main__":
    main()
