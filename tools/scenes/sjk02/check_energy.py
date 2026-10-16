# -*- coding: utf-8 -*-
"""성제관02 자막 시각 검수(지시서 3장 5번 «다른 방법으로») — 강제 정렬과 따로, 목소리 에너지(10ms RMS)로 쉼을 찾아
쉼 바로 뒤에서 시작하는 줄의 시작 · 쉼 바로 앞에서 끝나는 줄의 끝을 대조한다.

쉼 = −38dB 아래가 0.12초 이상(편집본 바닥 소음 −45~−53dB, 말 꼬리 −40dB 안팎).
- 시작 대조: 줄 t0 가 어떤 쉼 끝(=목소리 시작) ±0.35초 안이면 그 쉼 끝과 비교
- 끝 대조:  줄 t1(마지막 어절 끝)이 어떤 쉼 시작 ±0.35초 안이면 비교
이어지는 줄(쉼 없이 붙은 줄)은 에너지로 경계를 못 재므로 정렬 점수·받아쓰기 대조로만 본다(보고에 «이어짐»).
    py -3.11 tools/scenes/sjk02/check_energy.py [lines.json] [wav16k] [--fix]
--fix: 쉼 뒤 줄의 t0 를 목소리 시작으로, 쉼 앞 줄의 t1 을 목소리 끝으로 맞춘다(차이 0.04초 넘는 것만, 첫·끝 어절도) → 원본은 lines_pre_energy.json
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[3]


def pauses(x, sr, thr=-38.0, min_len=0.12):
    hop = int(sr * 0.01)
    n = len(x) // hop
    db = 20 * np.log10(np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1)) + 1e-9)
    q = db < thr
    out, k = [], 0
    while k < n:
        if q[k]:
            j = k
            while j < n and q[j]:
                j += 1
            if (j - k) / 100 >= min_len:
                out.append((k / 100, j / 100))
            k = j
        else:
            k += 1
    return out, db


def main():
    a = [s for s in sys.argv[1:] if not s.startswith("--")]
    lp = Path(a[0]) if a else ROOT / "_tmp/sjk02/audio/lines.json"
    wp = a[1] if len(a) > 1 else str(ROOT / "_tmp/sjk02/audio/voice16k.wav")
    fix = "--fix" in sys.argv
    L = json.load(open(lp, encoding="utf-8"))
    x, sr = sf.read(wp, dtype="float32")
    if x.ndim > 1:
        x = x.mean(1)
    P, db = pauses(x, sr)
    starts = np.array([b for _, b in P])   # 쉼 끝 = 목소리 시작
    ends = np.array([a_ for a_, _ in P])   # 쉼 시작 = 목소리 끝
    rows, ds, de = [], [], []
    for k, r in enumerate(L):
        s = e = None
        if len(starts):
            j = int(np.argmin(abs(starts - r["t0"])))
            if abs(starts[j] - r["t0"]) <= 0.35:
                s = round(float(starts[j]), 2)
                ds.append(r["t0"] - s)
            j = int(np.argmin(abs(ends - r["t1"])))
            if abs(ends[j] - r["t1"]) <= 0.35:
                e = round(float(ends[j]), 2)
                de.append(r["t1"] - e)
        rows.append({"i": k, "t0": r["t0"], "t1": r["t1"], "on": s, "off": e, "text": r["text"]})
    ds, de = np.array(ds), np.array(de)
    print(f"쉼 {len(P)} · 시작 대조 {len(ds)}줄: ±0.1 안 {(abs(ds) <= 0.1).mean():.3f} 중앙 {np.median(ds):+.3f} · "
          f"끝 대조 {len(de)}줄: ±0.1 안 {(abs(de) <= 0.1).mean():.3f} 중앙 {np.median(de):+.3f}")
    for r in rows:
        flag = []
        if r["on"] is not None and abs(r["t0"] - r["on"]) > 0.1:
            flag.append(f"시작 {r['t0'] - r['on']:+.2f}")
        if r["off"] is not None and abs(r["t1"] - r["off"]) > 0.1:
            flag.append(f"끝 {r['t1'] - r['off']:+.2f}")
        if flag:
            print(f"  {r['i']:3d} {r['t0']:7.2f} {' · '.join(flag)}  {r['text']}")
    (ROOT / "_tmp/sjk02/audio/energy_check.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    if fix:
        bak = lp.with_name("lines_pre_energy.json")
        if not bak.exists():
            shutil.copy(lp, bak)
        n = 0
        for r, ln in zip(rows, L):
            if r["on"] is not None and abs(ln["t0"] - r["on"]) > 0.04:
                ln["t0"] = r["on"]
                if ln.get("words"):
                    ln["words"][0]["t0"] = min(r["on"], ln["words"][0]["t1"] - 0.03)
                n += 1
            # 끝: 강제 정렬은 마지막 음절 꼬리를 짧게 잡는다(중앙 −0.09초) → 쉼 앞 줄은 목소리 끝으로
            if r["off"] is not None and abs(ln["t1"] - r["off"]) > 0.04 and r["off"] > ln["t0"] + 0.2:
                ln["t1"] = r["off"]
                if ln.get("words"):
                    ln["words"][-1]["t1"] = max(r["off"], ln["words"][-1]["t0"] + 0.03)
                n += 1
        for k, ln in enumerate(L):
            nxt = L[k + 1]["t0"] if k + 1 < len(L) else ln["t1"] + 1
            ln["end"] = round(min(ln["t1"] + 0.15, nxt - 0.02), 3)
        lp.write_text(json.dumps(L, ensure_ascii=False, indent=1), encoding="utf-8")
        print("고친 줄", n)


if __name__ == "__main__":
    main()
