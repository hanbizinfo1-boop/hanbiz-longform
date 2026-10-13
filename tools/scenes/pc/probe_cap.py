# -*- coding: utf-8 -*-
"""자막 상자·글자 모양을 mp4 와 원본 대조로 잰다(파트너센터 자동 R0)."""
import json, sys
import numpy as np, cv2, av
sys.path.insert(0, ".")
from tools.auto.layers import TrackReader, SEQ_FPS
DIRS = [r"D:\26년 10월\261012"]
it = json.load(open("_tmp/pc/edit.json", encoding="utf-8"))["items"]
V1 = TrackReader([i for i in it if i["track"] == "V1"], DIRS)
caps = [i for i in it if i["track"] == "C1"]
mp4 = av.open(r"D:\26년 10월\261006\자동화 MP4\파트너센터 자동.mp4")
s = mp4.streams.video[0]
def mp4_frame(k):
    t = float(k / SEQ_FPS); mp4.seek(int((t - 1) / s.time_base), stream=s)
    for f in mp4.decode(s):
        if f.pts * s.time_base >= t - 0.5 / 59.94: return f.to_ndarray(format="bgr24")
out = []
for c in caps[100:800:70]:
    k = int(round((c["t0"] + c["t1"]) / 2 * 59.94))
    rec, _ = V1.frame(k); ref = mp4_frame(k)
    d = np.abs(ref.astype(int) - rec.astype(int)).sum(2)
    d[:, :330] = 0
    ys, xs = np.where(d[850:] > 40); ys = ys + 850
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    # 상자 안 글자 아닌 곳: 흰/검 아닌 픽셀 — 상자 색·불투명도 추정
    R = rec[y0:y1 + 1, x0:x1 + 1].astype(float); M = ref[y0:y1 + 1, x0:x1 + 1].astype(float)
    lum = M.mean(2)
    bg = (lum < 120) & (lum > 5) & (R.mean(2) > 150)   # 밝은 배경 위 어두워진 곳 = 상자만
    a_est = 1 - (M[bg].mean(1) / np.maximum(R[bg].mean(1), 1))
    out.append((c["text"], int(x0), int(x1), int(y0), int(y1), round(float(np.median(a_est)), 3) if bg.any() else None))
    cv2.imwrite(f"_tmp/pc/capfit_{k}.png", ref[y0 - 10:y1 + 10, x0 - 10:x1 + 10])
for o in out: print(o)
