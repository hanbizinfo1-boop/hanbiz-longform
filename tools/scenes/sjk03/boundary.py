# -*- coding: utf-8 -*-
"""성제관03 자막 경계 — 강제 정렬과 따로, 줄 사이 «소리 골»(−40dB 아래 30ms 이상)에서 목소리 시작·끝을 잰다.

10-30 실측: refine_onsets.py 는 앞 줄 끝이 일찍 잡힌(정렬기 끝 당김) 곳을 «틈»으로 보고, 앞 줄 꼬리 소리를
다음 줄 시작으로 당겨 28줄을 0.2~0.4초 이르게 만들었다(«심지어» 8.78 ← 실제 9.20, ㅅ 마찰음). 그래서 3편은 이 방식으로 잰다.
- 시작: [앞 줄 끝 −0.1, t0 +0.15] 안 가장 깊은 골 → 골 다음에 골+10dB 를 처음 넘는 곳
- 끝:   [t1 −0.15, 다음 줄 시작 +0.1] 안 가장 깊은 골 → 골 앞에서 골+10dB 를 마지막으로 넘는 곳
골이 없으면(쉼 없이 이어 말함) «이어짐» — 에너지로 경계를 못 잰다.
    py -3.11 tools/scenes/sjk03/boundary.py [lines.json] [--fix]   (--fix: 잰 값으로 t0·t1 을 바꾸고 원본은 lines_pre_boundary.json)
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[3]
WAV = ROOT / "_tmp/sjk03/audio/voice16k.wav"
DIP_DB, DIP_LEN, RISE = -40.0, 3, 10.0      # 10ms 프레임


def db_track():
    x, sr = sf.read(str(WAV), dtype="float32")
    hop = sr // 100
    n = len(x) // hop
    return 20 * np.log10(np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1)) + 1e-9)


def deepest_dip(db, lo, hi):
    a, b = max(0, int(lo * 100)), min(len(db), int(hi * 100))
    if b - a < DIP_LEN:
        return None
    q = db[a:b] < DIP_DB
    best, k = None, 0
    while k < len(q):
        if q[k]:
            j = k
            while j < len(q) and q[j]:
                j += 1
            if j - k >= DIP_LEN:
                m = a + k + int(np.argmin(db[a + k:a + j]))
                if best is None or db[m] < db[best[0]]:
                    best = (m, a + k, a + j)
            k = j
        else:
            k += 1
    return best


def measure(L, db):
    out = []
    for k, r in enumerate(L):
        prev_t1 = L[k - 1]["t1"] if k else 0.0
        nxt_t0 = L[k + 1]["t0"] if k + 1 < len(L) else len(db) / 100
        s = e = None
        d = deepest_dip(db, max(prev_t1 - 0.1, r["t0"] - 0.6), r["t0"] + 0.15)
        if d:
            m, _, j = d
            i = m
            while i < len(db) and db[i] < db[m] + RISE:
                i += 1
            s = i / 100
        d = deepest_dip(db, r["t1"] - 0.15, min(nxt_t0 + 0.1, r["t1"] + 0.6))
        if d:
            m, a0, _ = d
            i = m
            while i > 0 and db[i] < db[m] + RISE:
                i -= 1
            e = (i + 1) / 100
        out.append((s, e))
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    lp = Path(args[0]) if args else ROOT / "_tmp/sjk03/audio/lines.json"
    L = json.load(open(lp, encoding="utf-8"))
    db = db_track()
    M = measure(L, db)
    ns = sum(1 for s, _ in M if s is not None)
    ne = sum(1 for _, e in M if e is not None)
    oks = sum(1 for (s, _), r in zip(M, L) if s is not None and abs(s - r["t0"]) <= 0.1)
    oke = sum(1 for (_, e), r in zip(M, L) if e is not None and abs(e - r["t1"]) <= 0.1)
    print(f"줄 {len(L)} · 시작 잴 수 있음 {ns}(±0.1 안 {oks}) · 끝 잴 수 있음 {ne}(±0.1 안 {oke}) · 나머지 이어짐")
    for k, ((s, e), r) in enumerate(zip(M, L)):
        if s is not None and abs(s - r["t0"]) > 0.1:
            print(f"  {k:3d} 시작 {r['t0']:.2f} → {s:.2f}  {r['text']}")
        if e is not None and abs(e - r["t1"]) > 0.1:
            print(f"  {k:3d} 끝   {r['t1']:.2f} → {e:.2f}  {r['text']}")
    if "--fix" in sys.argv:
        shutil.copy(lp, lp.with_name("lines_pre_boundary.json"))
        for (s, e), r in zip(M, L):
            if s is not None:
                r["t0"] = s
                if r.get("words"):
                    r["words"][0]["t0"] = s
            if e is not None and e > r["t0"]:
                r["t1"] = e
                if r.get("words"):
                    r["words"][-1]["t1"] = e
            r["bound"] = ["잼" if s is not None else "이어짐", "잼" if e is not None else "이어짐"]
        json.dump(L, open(lp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("고침 →", lp)


if __name__ == "__main__":
    main()
