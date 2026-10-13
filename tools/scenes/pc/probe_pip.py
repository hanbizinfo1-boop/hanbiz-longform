# -*- coding: utf-8 -*-
"""PIP 원형 마스크를 mp4 와 원본 대조로 추정한다(파트너센터 자동 R0)."""
import json, sys
import numpy as np, cv2, av
sys.path.insert(0, ".")
from tools.auto.layers import TrackReader, motion_of, SEQ_FPS
DIRS = [r"D:\26년 10월\261012"]
it = json.load(open("_tmp/pc/edit.json", encoding="utf-8"))["items"]
V1 = TrackReader([i for i in it if i["track"] == "V1"], DIRS)
V2 = TrackReader([i for i in it if i["track"] == "V2"], DIRS)
mp4 = av.open(r"D:\26년 10월\261006\자동화 MP4\파트너센터 자동.mp4")
def mp4_frame(k):
    s = mp4.streams.video[0]
    t = float(k / SEQ_FPS)
    mp4.seek(int((t - 1) / s.time_base), stream=s)
    for f in mp4.decode(s):
        if f.pts * s.time_base >= t - 0.5 / 59.94:
            return f.to_ndarray(format="bgr24")
acc = []
for T in [60, 100, 300, 400, 650, 800, 1000, 1200, 1350]:
    k = int(round(T * 59.94))
    rec, i1 = V1.frame(k); cam, i2 = V2.frame(k); ref = mp4_frame(k)
    pos, sc = motion_of(i2)
    W, H = 1920, 1080
    s = sc / 100; nw, nh = int(round(1920 * s)), int(round(1080 * s))
    camr = cv2.resize(cam, (nw, nh), interpolation=cv2.INTER_AREA)
    x0, y0 = int(round(pos[0] * W - nw / 2)), int(round(pos[1] * H - nh / 2))
    full = rec.copy()
    ax0, ay0, ax1, ay1 = max(0, x0), max(0, y0), min(W, x0 + nw), min(H, y0 + nh)
    full[ay0:ay1, ax0:ax1] = camr[ay0 - y0:ay1 - y0, ax0 - x0:ax1 - x0]
    R = rec[700:1080, 0:420].astype(np.float32); C = full[700:1080, 0:420].astype(np.float32); M = ref[700:1080, 0:420].astype(np.float32)
    d = (C - R); num = ((M - R) * d).sum(2); den = (d * d).sum(2)
    a = np.where(den > 300, num / np.maximum(den, 1), np.nan)
    acc.append(a)
    # 전체 차이(자막 줄 제외)
    diff = np.abs(ref.astype(int) - rec.astype(int)).mean(2)
    print(T, "rec vs mp4 mean diff (y<900, x>450):", round(float(diff[:900, 450:].mean()), 2), "pos", pos, sc, x0, y0)
A = np.nanmedian(np.stack(acc), 0)
A = np.clip(np.nan_to_num(A, nan=0), 0, 1)
np.save("_tmp/pc/pip_alpha_est.npy", A)
cv2.imwrite("_tmp/pc/pip_alpha_est.png", (A * 255).astype(np.uint8))
ys, xs = np.where(A > 0.5)
print("alpha>0.5 bbox x", xs.min(), xs.max(), "y", ys.min() + 700, ys.max() + 700, "n", len(xs))
