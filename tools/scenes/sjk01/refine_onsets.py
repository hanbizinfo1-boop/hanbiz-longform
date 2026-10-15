# -*- coding: utf-8 -*-
"""자막 시작 보정 — 강제 정렬(MMS_FA)은 모음으로 시작하는 줄(«이…» «왜…» «오…»)의 첫 음절을 0.2~0.35초 늦게 잡는다(10-14 실측).
앞에 무음 틈(0.25초 이상)이 있는 줄만, 소리 에너지로 잰 «목소리 시작»으로 줄 시작을 당긴다.
숨소리(고역 비중 큼)는 목소리로 치지 않는다. 결과는 lines.json 의 t0(첫 어절 t0 도 같이) — 원본은 lines_pre_refine.json 으로 남김.
    py -3.11 tools/scenes/sjk01/refine_onsets.py [--check]   (--check: 고치지 않고 재기만)
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[3]
LP = ROOT / "_tmp/sjk01/audio/lines.json"
WAV = ROOT / "_tmp/sjk01/audio/voice16k.wav"


def onsets(L, x, sr):
    hop = int(sr * 0.01); n = len(x) // hop
    fr = x[:n * hop].reshape(n, hop)
    db = 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9)
    sp = np.abs(np.fft.rfft(fr * np.hanning(hop), axis=1)); f = np.fft.rfftfreq(hop, 1 / sr)
    hi = (sp[:, f > 3000] ** 2).sum(1) / ((sp ** 2).sum(1) + 1e-12)
    floor = np.percentile(db, 10); thr = floor + 12
    out = {}
    for k, r in enumerate(L):
        t = r["t0"]; pe = L[k - 1]["t1"] if k else 0.0
        if t - pe < 0.25:
            continue
        a = int(max(pe + 0.05, t - 0.6) * 100); b = int((t + 0.4) * 100)
        seg = db[a:b]
        voiced = (seg > thr) & (hi[a:b] < 0.25)
        if not voiced.any():
            continue
        on = (a + int(np.argmax(voiced))) / 100
        out[k] = on
    return out


def main():
    check = "--check" in sys.argv
    x, sr = sf.read(str(WAV), dtype="float32")
    L = json.load(open(LP, encoding="utf-8"))
    ons = onsets(L, x, sr)
    d = np.array([L[k]["t0"] - o for k, o in ons.items()])
    print(f"틈 있는 줄 {len(d)} · 정렬 시작 − 목소리 시작: 중앙 {np.median(d):+.3f} · |차|≤0.1 {np.mean(abs(d) <= 0.1) * 100:.1f}% · 최대 {d.max():+.3f}")
    if check:
        return
    shutil.copy(LP, LP.with_name("lines_pre_refine.json"))
    n = 0
    for k, o in ons.items():
        dd = L[k]["t0"] - o
        if 0.06 < dd < 0.5:                      # 늦게 잡힌 것만 당김(일찍 잡힌 쪽은 손대지 않음)
            new = round(o - 0.01, 3)
            L[k]["t0_aligned"] = L[k]["t0"]
            L[k]["t0"] = new
            if L[k]["words"]:
                L[k]["words"][0]["t0"] = new
            n += 1
    json.dump(L, open(LP, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("당긴 줄", n)


if __name__ == "__main__":
    main()
