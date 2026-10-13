# -*- coding: utf-8 -*-
"""자막 스타일 맞추기 — 크기·테두리·상자 여백·세로 위치를 격자 탐색(파트너센터 자동 R0)."""
import json, sys, itertools
import numpy as np, cv2, av
sys.path.insert(0, ".")
from tools.auto.layers import TrackReader, SEQ_FPS
from PIL import Image, ImageDraw, ImageFont
FONT = r"C:\Users\user\AppData\Local\Microsoft\Windows\Fonts\GmarketSansMedium.otf"
DIRS = [r"D:\26년 10월\261012"]
it = json.load(open("_tmp/pc/edit.json", encoding="utf-8"))["items"]
V1 = TrackReader([i for i in it if i["track"] == "V1"], DIRS)
caps = [i for i in it if i["track"] == "C1"]
mp4 = av.open(r"D:\26년 10월\261006\자동화 MP4\파트너센터 자동.mp4"); s = mp4.streams.video[0]
def mp4_frame(k):
    t = float(k / SEQ_FPS); mp4.seek(int((t - 1) / s.time_base), stream=s)
    for f in mp4.decode(s):
        if f.pts * s.time_base >= t - 0.5 / 59.94: return f.to_ndarray(format="bgr24")
samples = []
for c in [caps[i] for i in (160, 280, 400, 520, 640)]:
    k = int(round((c["t0"] + c["t1"]) / 2 * 59.94))
    rec, _ = V1.frame(k); ref = mp4_frame(k); samples.append((c["text"], rec, ref))
def render(text, size, stroke, padx, pady, rad, cy, alpha=0.616, track=0):
    f = ImageFont.truetype(FONT, size)
    im = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    bb = d.textbbox((0, 0), text, font=f, anchor="ls", stroke_width=0)
    w = bb[2] - bb[0]
    asc, desc = f.getmetrics()
    x0 = 960 - w / 2 - padx; x1 = 960 + w / 2 + padx
    y0 = cy - pady; y1 = cy + pady
    d.rounded_rectangle((x0, y0, x1, y1), radius=rad, fill=(0, 0, 0, int(round(alpha * 255))))
    d.text((960, cy), text, font=f, anchor="mm", fill=(255, 255, 255, 255), stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
    return np.array(im)
def comp(rec, rgba):
    a = rgba[..., 3:4] / 255.0; c = rgba[..., [2, 1, 0]].astype(float)
    return rec * (1 - a) + c * a
best = None
for size, stroke, padx, pady, rad, cy in itertools.product([46, 47, 48, 49], [2, 3, 4], [12, 16, 20], [35], [8, 12], [1009, 1010, 1011]):
    err = 0
    for text, rec, ref in samples:
        out = comp(rec[960:1060].astype(float), render(text, size, stroke, padx, pady, rad, cy)[960:1060])
        err += np.abs(out - ref[960:1060]).mean()
    if best is None or err < best[0]:
        best = (err, size, stroke, padx, pady, rad, cy)
print("best", best)
_, size, stroke, padx, pady, rad, cy = best
text, rec, ref = samples[0]
out = comp(rec.astype(float), render(text, size, stroke, padx, pady, rad, cy)).astype(np.uint8)
cv2.imwrite("_tmp/pc/capcmp.png", np.vstack([ref[960:1060, 400:1520], out[960:1060, 400:1520]]))
