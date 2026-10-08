# -*- coding: utf-8 -*-
"""화면녹화 파일 안에서 «소리 시각 vs 화면 시각»이 어긋나는지 본다.
클릭 소리(짧고 날카로운 소리) 시각과 화면 전환(장면 변화) 시각을 구간별로 맞대어, 가장 잘 맞는 지연을 찾는다.

    python rec_av_check.py <녹화.mp4> <녹화_8k.wav> 시작초 길이초 [시작초 길이초 …]
"""
import re
import subprocess
import sys
import wave

import numpy as np


def scene_times(mp4, t0, dur):
    r = subprocess.run(["ffmpeg", "-v", "info", "-ss", str(t0), "-t", str(dur), "-i", mp4, "-vf",
                        "scale=480:-1,select='gt(scene,0.06)',showinfo", "-an", "-f", "null", "-"], capture_output=True, text=True, errors="ignore")
    return np.array([t0 + float(x) for x in re.findall(r"pts_time:([\d.]+)", r.stderr)])


def clicks(wav, t0, dur):
    w = wave.open(wav)
    sr = w.getframerate()
    w.setpos(int(t0 * sr))
    x = np.frombuffer(w.readframes(int(dur * sr)), np.int16).astype(float)
    hp = np.diff(x)                                   # 고역만(클릭은 날카롭다)
    hop = sr // 200
    n = len(hp) // hop
    e = np.sqrt((hp[:n * hop].reshape(n, hop) ** 2).mean(1))
    base = np.convolve(e, np.ones(60) / 60, "same") + 1e-6
    k = np.where((e / base > 5) & (e > np.percentile(e, 90)))[0]
    out, last = [], -9
    for i in k:
        if i - last > 40:
            out.append(t0 + i / 200)
        last = i
    return np.array(out)


def best_lag(cl, sc):
    best = (0, 0)
    for lag in np.arange(-8, 8.001, 0.02):
        hit = sum(np.any(np.abs(sc - (c + lag)) < 0.12) for c in cl)
        if hit > best[0]:
            best = (hit, lag)
    return best


def main():
    mp4, wav = sys.argv[1], sys.argv[2]
    a = list(map(float, sys.argv[3:]))
    for t0, dur in zip(a[::2], a[1::2]):
        sc, cl = scene_times(mp4, t0, dur), clicks(wav, t0, dur)
        hit, lag = best_lag(cl, sc)
        print(f"{t0:7.0f}~{t0 + dur:.0f}  클릭 {len(cl)} · 화면전환 {len(sc)} · 최다 일치 {hit}개 @ 화면 = 소리 {lag:+.2f}초")


if __name__ == "__main__":
    main()
