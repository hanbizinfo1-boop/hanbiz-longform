# -*- coding: utf-8 -*-
r"""원문 층 재구성 — prproj 트랙(read_lecture_edit.py 결과)을 시퀀스 프레임 단위로 다시 읽는다.

자동 연출(B 모드) R0: 사장님 mp4 는 한 장으로 붙어 있어 모자이크·자막 수정·«자막 아래» 연출이 안 된다.
그래서 V1(녹화)·V2(사람)를 원본 파일에서 다시 뽑고, 자막은 다시 그린다. 결과는 mp4 와 SSIM 으로 대조한다.

    from tools.auto.layers import TrackReader
    r = TrackReader(items_of_V1, media_dirs, fps=60000/1001)
    frame = r.frame(k)          # 시퀀스 k 번째 프레임(BGR uint8) 또는 None(빈 곳)

시각 규칙: 시퀀스 프레임 k 의 시각 t = k / fps. 그 시각을 덮는 클립(t0 <= t < t1)의 원본 시각 s = s0 + (t - t0).
원본 프레임은 s 이하에서 가장 가까운 것(floor). 앞으로만 가면 이어서 디코드하고, 뒤로 가거나 2초 넘게 건너뛰면 seek.
"""

import bisect
from fractions import Fraction
from pathlib import Path

import av
import numpy as np

SEQ_FPS = Fraction(60000, 1001)


def find_media(name, dirs):
    for d in dirs:
        p = Path(d) / name
        if p.exists():
            return p
    raise FileNotFoundError(f"원본 «{name}» 을 {dirs} 에서 못 찾음")


class _Src:
    """원본 파일 하나를 앞으로 읽어 나가는 디코더."""

    def __init__(self, path):
        self.c = av.open(str(path))
        self.vs = self.c.streams.video[0]
        self.vs.thread_type = "AUTO"
        self.tb = self.vs.time_base
        self.gen = None
        self.cur = None      # (pts_sec, frame ndarray)
        self.nxt = None
        self.w, self.h = self.vs.codec_context.width, self.vs.codec_context.height

    def _restart(self, s):
        self.c.seek(max(0, int((s - 1.0) / self.tb)), stream=self.vs, backward=True, any_frame=False)
        self.gen = self.c.decode(self.vs)
        self.cur = None
        self.nxt = self._pull()

    def _pull(self):
        try:
            f = next(self.gen)
        except StopIteration:
            return None
        return (float(f.pts * self.tb), f)

    def at(self, s):
        """원본 시각 s 이하에서 가장 가까운 프레임(av.VideoFrame)."""
        eps = float(__import__("os").environ.get("SRC_EPS", "1e-4"))
        if self.gen is None or self.cur is None and self.nxt is None or \
                (self.cur is not None and s < self.cur[0] - eps) or \
                (self.nxt is not None and s > self.nxt[0] + 2.0):
            self._restart(s)
        while self.nxt is not None and self.nxt[0] <= s + eps:
            self.cur, self.nxt = self.nxt, self._pull()
        if self.cur is None:          # s 가 첫 프레임보다 앞 → 첫 프레임
            self.cur, self.nxt = self.nxt, self._pull()
        return self.cur[1]


class TrackReader:
    def __init__(self, items, media_dirs, fps=SEQ_FPS):
        self.items = sorted(items, key=lambda i: i["t0"])
        self.t0s = [i["t0"] for i in self.items]
        self.fps = fps
        self.dirs = media_dirs
        self.srcs = {}

    def item_at(self, t):
        j = bisect.bisect_right(self.t0s, t + 1e-6) - 1
        if j < 0:
            return None
        it = self.items[j]
        return it if t < it["t1"] - 1e-6 else None

    def src(self, name):
        if name not in self.srcs:
            self.srcs[name] = _Src(find_media(name, self.dirs))
        return self.srcs[name]

    def frame(self, k, fmt="bgr24", size=None):
        t = float(k / self.fps)
        it = self.item_at(t)
        if it is None:
            return None, None
        s = it["s0"] + (t - it["t0"])
        vf = self.src(it["name"]).at(s)
        if size:
            vf = vf.reformat(width=size[0], height=size[1], format=fmt)
        return vf.to_ndarray(format=fmt) if not size else vf.to_ndarray(), it


def motion_of(item):
    """모션 이펙트 → (위치 x,y 정규화, 비율 %). 없으면 기본(가운데·100)."""
    for f in item.get("fx", []):
        if f.get("name") == "모션":
            p = f["params"]
            x, y = (float(v) for v in p.get("위치", "0.5:0.5").split(":"))
            return (x, y), float(p.get("비율 조정", "100"))
    return (0.5, 0.5), 100.0


def place(canvas, img, pos_norm, scale_pct, alpha=None):
    """img 를 비율 scale_pct 로 줄여 중심을 pos_norm(캔버스 비율)에 놓는다. alpha(0~1, img 크기 기준) 있으면 섞는다."""
    import cv2
    H, W = canvas.shape[:2]
    s = scale_pct / 100.0
    h, w = img.shape[:2]
    nw, nh = int(round(w * s)), int(round(h * s))
    im = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR)
    a = None
    if alpha is not None:
        a = cv2.resize(alpha, (nw, nh), interpolation=cv2.INTER_LINEAR) if alpha.shape[:2] != (nh, nw) else alpha
    cx, cy = pos_norm[0] * W, pos_norm[1] * H
    x0, y0 = int(round(cx - nw / 2)), int(round(cy - nh / 2))
    ax0, ay0, ax1, ay1 = max(0, x0), max(0, y0), min(W, x0 + nw), min(H, y0 + nh)
    if ax0 >= ax1 or ay0 >= ay1:
        return
    sub = im[ay0 - y0:ay1 - y0, ax0 - x0:ax1 - x0]
    if a is None:
        canvas[ay0:ay1, ax0:ax1] = sub
    else:
        aa = a[ay0 - y0:ay1 - y0, ax0 - x0:ax1 - x0][..., None]
        dst = canvas[ay0:ay1, ax0:ax1].astype(np.float32)
        canvas[ay0:ay1, ax0:ax1] = (sub.astype(np.float32) * aa + dst * (1 - aa)).astype(np.uint8)
