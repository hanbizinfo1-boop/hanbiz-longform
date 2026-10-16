# -*- coding: utf-8 -*-
"""성제관02 — 사장님 편집본에서 편집 이음매(컷 지점)를 찾는다(지시서 3장 3번).

편집 컷은 ① 소리가 들리는 도중 뚝 끊기거나(샘플 불연속 · 앞뒤 스펙트럼이 갑자기 다름)
② 쉼 안에서 방 소리(바닥 소음)가 갑자기 바뀌거나 디지털 무음(−90dB 아래)이 끼는 자리로 남는다.
- 1) 샘플 불연속: |x[n]−x[n−1]| 가 주변 5ms 차분 표준편차의 12배 넘음(클릭)
- 2) 바닥 소음 계단: 쉼(−45dB 아래) 안에서 이웃 50ms 평균이 6dB 넘게 바뀜
- 3) 디지털 무음: 20ms 이상 −90dB 아래
출력: _tmp/sjk02/audio/seams.json [{t, kind, db_before, db_after}] — 강제 정렬 묶음은 이 점을 넘지 않는다.
    py -3.11 tools/scenes/sjk02/seams.py
"""
import json
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[3]
WAV = ROOT / "_tmp/sjk02/audio/voice.wav"
OUT = ROOT / "_tmp/sjk02/audio/seams.json"


def main():
    x, sr = sf.read(str(WAV), dtype="float64")
    if x.ndim > 1:
        x = x.mean(1)
    hop = int(sr * 0.01)
    n = len(x) // hop
    fr = x[:n * hop].reshape(n, hop)
    db = 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-12)
    out = []
    # 3) 디지털 무음
    dz = db < -90
    k = 0
    while k < n:
        if dz[k]:
            j = k
            while j < n and dz[j]:
                j += 1
            if j - k >= 2:
                out.append({"t": round(k / 100, 3), "kind": "digital_silence", "len": round((j - k) / 100, 3)})
            k = j
        else:
            k += 1
    # 1) 샘플 불연속(클릭) — 2차 차분이 주변 대비 튐
    d = np.abs(np.diff(x, 2))
    w = int(sr * 0.005)
    ker = np.ones(w) / w
    loc = np.sqrt(np.convolve(d ** 2, ker, mode="same")) + 1e-6
    ratio = d / loc
    idx = np.where((ratio > 9) & (d > 0.004))[0]
    last = -1
    for i in idx:
        if i - last < sr * 0.05:
            continue
        last = i
        f = i // hop
        out.append({"t": round(i / sr, 4), "kind": "click", "ratio": round(float(ratio[i]), 1),
                    "db": round(float(db[min(f, n - 1)]), 1)})
    # 2) 바닥 소음 계단(쉼 안)
    m5 = np.convolve(db, np.ones(5) / 5, mode="same")
    for f in range(10, n - 10):
        a, b = m5[f - 5], m5[f + 5]
        if max(db[f - 8:f + 8]) < -36 and abs(a - b) > 5:
            if out and out[-1]["kind"] == "floor_step" and f / 100 - out[-1]["t"] < 0.3:
                continue
            out.append({"t": round(f / 100, 3), "kind": "floor_step", "db_before": round(float(a), 1), "db_after": round(float(b), 1)})
    out.sort(key=lambda r: r["t"])
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    from collections import Counter
    print("이음매 후보", len(out), Counter(r["kind"] for r in out))
    print("바닥 소음(10퍼센타일) dB", round(float(np.percentile(db, 10)), 1))
    for r in out[:400]:
        print(r)


if __name__ == "__main__":
    main()
