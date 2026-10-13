# -*- coding: utf-8 -*-
import json, sys
import numpy as np, cv2, av
sys.path.insert(0, ".")
from tools.auto.layers import TrackReader, SEQ_FPS
from PIL import ImageFont
DIRS = [r"D:\26년 10월\261012"]
it = json.load(open("_tmp/pc/edit.json", encoding="utf-8"))["items"]
V1 = TrackReader([i for i in it if i["track"] == "V1"], DIRS)
caps = [i for i in it if i["track"] == "C1"]
mp4 = av.open(r"D:\26년 10월\261006\자동화 MP4\파트너센터 자동.mp4"); s = mp4.streams.video[0]
def mp4_frame(k):
    t = float(k / SEQ_FPS); mp4.seek(int((t - 1) / s.time_base), stream=s)
    for f in mp4.decode(s):
        if f.pts * s.time_base >= t - 0.5 / 59.94: return f.to_ndarray(format="bgr24")
font = ImageFont.truetype(r"C:\Users\user\AppData\Local\Microsoft\Windows\Fonts\GmarketSansMedium.otf", 100)
for c in caps[100:800:60]:
    k = int(round((c["t0"] + c["t1"]) / 2 * 59.94))
    rec, _ = V1.frame(k); ref = mp4_frame(k)
    R = rec[900:1080, 330:1650].astype(float).mean(2); M = ref[900:1080, 330:1650].astype(float).mean(2)
    ratio = (M + 1) / (R + 1)
    box = (ratio > 0.28) & (ratio < 0.5) & (R > 60)
    ys, xs = np.where(box)
    if len(xs) < 500: continue
    # 행/열 히스토그램으로 상자 경계
    col = box.sum(0); row = box.sum(1)
    cx = np.where(col > 3)[0]; ry = np.where(row > 20)[0]
    x0, x1 = cx.min() + 330, cx.max() + 330; y0, y1 = ry.min() + 900, ry.max() + 900
    a = 1 - np.median(ratio[box])
    # 흰 글자 픽셀
    W = (ref[900:1080, 330:1650].min(2) > 225) & (R < 200)
    wy, wx = np.where(W)
    bb = font.getbbox(c["text"])
    print(f'{c["text"][:18]:20s} box x{x0}-{x1} (w{x1-x0}) y{y0}-{y1} (h{y1-y0}) a={a:.3f} | white x{wx.min()+330}-{wx.max()+330} y{wy.min()+900}-{wy.max()+900} | font100 w={bb[2]-bb[0]} h={bb[3]-bb[1]}')
