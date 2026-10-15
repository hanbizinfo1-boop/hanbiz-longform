# -*- coding: utf-8 -*-
"""완성본 소리에서 «목소리 대비 BGM dB» 재기 — 목소리 단독 wav 로 말/쉼을 나누고, 완성본의 말 구간 중앙 − 쉼 구간 중앙(50ms RMS).
레퍼런스 9채널 실측(10-15, _tmp/bgm_ref/측정.md)과 같은 정의. 효과음이 쉼에 섞이면 BGM 이 크게 잡히므로 효과음 버스도 받아 그 자리를 뺀다.
    py -3.11 tools/scenes/sjk01/bgm_gap.py <목소리.wav> <완성본.wav> [효과음버스.wav]
"""
import sys

import numpy as np
import soundfile as sf


def rms_db(x, sr, w=0.05):
    n = int(w * sr); k = len(x) // n
    return 20 * np.log10(np.sqrt((x[:k * n].reshape(k, n) ** 2).mean(1)) + 1e-9)


def mono(p):
    x, sr = sf.read(p, dtype="float32")
    return (x.mean(1) if x.ndim > 1 else x), sr


def main():
    v, sr = mono(sys.argv[1]); m, sr2 = mono(sys.argv[2])
    assert sr == sr2
    dv, dm = rms_db(v, sr), rms_db(m, sr)
    n = min(len(dv), len(dm)); dv, dm = dv[:n], dm[:n]
    top = np.percentile(dv, 90)
    speech = dv > top - 20
    quiet = dv < top - 23                                   # 목소리 단독이 말 꼭대기보다 23dB 아래 = 쉼(이 녹음 바닥 소음 −45 근처)
    if len(sys.argv) > 3:
        s, _ = mono(sys.argv[3]); ds = rms_db(s, sr)[:n]
        quiet &= ds < -70                                    # 효과음 나오는 곳 뺌
    sp, qu = float(np.median(dm[speech])), float(np.median(dm[quiet]))
    vq = float(np.median(dv[quiet]))
    print(f"말 중앙 {sp:.1f} · 쉼(BGM) 중앙 {qu:.1f} dBFS · 목소리 대비 BGM {sp - qu:.1f} dB · 쉼 표본 {quiet.sum() * 0.05:.0f}초 · (쉼에서 목소리 단독 {vq:.1f})")


if __name__ == "__main__":
    main()
