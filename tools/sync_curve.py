# -*- coding: utf-8 -*-
"""두 소리(촬영본 vs 화면녹화)의 어긋남을 구간마다 잰다 — 녹화가 가변 프레임이라 어긋남이 시간에 따라 변할 때.

    python sync_curve.py <녹화.wav> <촬영본.wav> <출력.json> [간격초=120]
wav 는 8kHz 모노(ffmpeg -ac 1 -ar 8000). 결과 = [(녹화 시각, 촬영본−녹화 초, 점수)].
소리 크기 포락선(5ms)의 정규화 상관으로 맞춘다 — 마이크가 달라도 말의 리듬은 같다.
"""
import json
import sys
import wave

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

SR, HOP = 8000, 40
FS = SR / HOP


def load_env(p):
    w = wave.open(p)
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float)
    n = len(x) // HOP
    return np.log1p(np.sqrt((x[:n * HOP].reshape(n, HOP) ** 2).mean(1)))


def main():
    r, c = load_env(sys.argv[1]), load_env(sys.argv[2])
    step = int(sys.argv[4]) if len(sys.argv) > 4 else 120
    print("녹화", round(len(r) / FS, 1), "촬영본", round(len(c) / FS, 1))
    prev, res = 1.5, []
    for t in range(30, int(len(r) / FS) - 40, step):
        a = r[int(t * FS):int((t + 20) * FS)]
        a = (a - a.mean()) / (a.std() + 1e-9)
        lo = max(0, int((t + prev - 6) * FS))
        b = c[lo:lo + int(32 * FS)]
        if len(b) <= len(a):
            break
        W = sliding_window_view(b, len(a))
        Wn = (W - W.mean(1, keepdims=True)) / (W.std(1, keepdims=True) + 1e-9)
        sc = Wn @ a / len(a)
        k = int(np.argmax(sc))
        off = (lo + k) / FS - t
        res.append((t, round(off, 4), round(float(sc[k]), 3)))
        if sc[k] > 0.5:
            prev = off
        print(f"{t:5d}  어긋남 {off:7.3f}  점수 {sc[k]:.2f}")
    json.dump(res, open(sys.argv[3], "w"))


if __name__ == "__main__":
    main()
