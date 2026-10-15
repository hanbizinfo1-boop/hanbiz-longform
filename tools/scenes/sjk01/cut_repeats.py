# -*- coding: utf-8 -*-
"""성제관01 — 녹음에서 같은 말을 다시 한 줄을 빼고(10-15 사장님 «영상 채워놓은곳을 살리고 멈춘곳을 제거해 단 앞뒤로 말이잘리거나 잡음 섞여들어가지않게»)
목소리·줄 시각을 함께 당긴다.

- 자르는 자리: 뺄 줄 앞 쉼(앞 줄 끝 ~ 뺄 줄 시작)과 뒤 쉼(뺄 줄 끝 ~ 다음 줄 시작) 안에서 각각 «10ms RMS 가 가장 낮은 곳».
  쉼 양 끝 30ms 는 건드리지 않는다(말 꼬리·첫소리 보호). 이음매는 20ms 같은 힘 교차(딸깍 없음).
- 출력: _tmp/sjk01/audio/voice_cut.wav(24bit 48kHz 모노) · lines_cut.json(뺀 줄 없음 · 뒤 줄 시각 당김 · i 다시 매김) · cut_report.json
- 원래 lines.json·녹음 원본은 그대로(쇼츠가 쓴다).
- 장면 시각표: timeline.py 로 다시 뽑지 않는다(lines.json 은 렌더 뒤 첫소리를 다듬은 판이라 다시 뽑으면 컷과 상관없는 장면 20여 개 시각이 바뀜).
  컷 전 시각표(_tmp/sjk01/timeline_precut.json — 처음 실행 때 지금 timeline.json 을 떠 둠)에 컷만 적용 → timeline.json · data/sNN.js.
  컷 뒤 장면은 통째로 당기고, 컷이 든 장면만 그 줄을 빼고 안쪽 시각을 당긴다(그 장면만 다시 렌더).
    py -3.11 tools/scenes/sjk01/cut_repeats.py
"""
import json
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[3]
SRC = r"D:\성제관 1편\성제관 1편.wav"
A = ROOT / "_tmp/sjk01/audio"
# 뺄 줄(lines.json index, 0부터) — 연출이 안 붙은 «다시 말한» 쪽. 10_분석/바뀐곳.md «반복» · 검수표 «같은 말을 다시 한 곳»
REMOVE = [96, 239, 351, 352]
GUARD, WIN, XF = 0.03, 0.010, 0.020


def quietest(x, sr, t0, t1):
    """[t0, t1] 안에서 «앞뒤 20ms(교차 구간 + 여유)가 가장 조용한» 가운데(초) — 5ms 간격으로 훑는다.
    10ms 최소점만 보면 다음 말 첫소리가 막 오르는 자리에 붙을 수 있다(1번 컷 첫 시도 −32dB 오름 직전)."""
    a, b = t0 + GUARD, t1 - GUARD
    if b - a < 0.005:
        return (t0 + t1) / 2
    h = int(0.020 * sr)
    best, bt = 1e9, (a + b) / 2
    for t in np.arange(a, b + 1e-9, 0.005):
        i = int(t * sr)
        w = x[max(0, i - h): i + h]
        e = float((w ** 2).mean())
        if e < best:
            best, bt = e, float(t)
    return bt


def main():
    rows = json.load(open(A / "lines.json", encoding="utf-8"))
    x, sr = sf.read(SRC, dtype="float32")
    if x.ndim > 1:
        x = x.mean(1)
    groups, cur = [], []
    for i in sorted(REMOVE):
        if cur and i == cur[-1] + 1:
            cur.append(i)
        else:
            if cur:
                groups.append(cur)
            cur = [i]
    groups.append(cur)
    cuts = []
    for g in groups:
        p, f, l, n = rows[g[0] - 1], rows[g[0]], rows[g[-1]], rows[g[-1] + 1]
        a = quietest(x, sr, p["t1"], f["t0"])
        b = quietest(x, sr, l["t1"], n["t0"])
        cuts.append(dict(a=round(a, 4), b=round(b, 4), dur=round(b - a, 4), lines=[rows[i]["text"] for i in g],
                         pause_before=round(f["t0"] - p["t1"], 3), pause_after=round(n["t0"] - l["t1"], 3),
                         new_pause=round((a - p["t1"]) + (n["t0"] - b), 3),
                         rms_a_db=None, rms_b_db=None))
    # 목소리 이어 붙이기 — 이음매 20ms 같은 힘 교차
    out, pos, xf = [], 0, int(XF * sr)
    for c in cuts:
        ia, ib = int(c["a"] * sr), int(c["b"] * sr)
        for key, t in (("rms_a_db", ia), ("rms_b_db", ib)):
            w = x[max(0, t - int(WIN * sr) // 2): t + int(WIN * sr) // 2]
            c[key] = round(float(20 * np.log10(np.sqrt((w ** 2).mean()) + 1e-12)), 1)
        out.append(x[pos:ia - xf // 2])
        h = np.linspace(0, np.pi / 2, xf)
        out.append(x[ia - xf // 2: ia - xf // 2 + xf] * np.cos(h) + x[ib - xf // 2: ib - xf // 2 + xf] * np.sin(h))
        pos = ib - xf // 2 + xf
    out.append(x[pos:])
    y = np.concatenate(out)
    sf.write(A / "voice_cut.wav", y, sr, subtype="PCM_24")
    # 줄 시각 당기기
    shift = lambda t: t - sum(c["dur"] for c in cuts if t >= c["b"] - 1e-6)
    new = []
    for i, r in enumerate(rows):
        if i in REMOVE:
            continue
        r = json.loads(json.dumps(r))
        for k in ("t0", "t1", "end", "sub_t0", "sub_t1"):
            if k in r and r[k] is not None:
                r[k] = round(shift(r[k]), 3)
        for w in r["words"]:
            w["t0"], w["t1"] = round(shift(w["t0"]), 3), round(shift(w["t1"]), 3)
        new.append(r)
    for k, r in enumerate(new):
        r["i"] = k
        if k and new[k - 1]["sub_t1"] > r["sub_t0"] - 0.02:          # 이음매 앞 줄 자막 끝이 다음 줄 시작을 넘지 않게
            new[k - 1]["sub_t1"] = round(r["sub_t0"] - 0.02, 3)
    json.dump(new, open(A / "lines_cut.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    rep = dict(src=SRC, total_in=round(len(x) / sr, 3), total_out=round(len(y) / sr, 3), cuts=cuts, removed=REMOVE)
    json.dump(rep, open(A / "cut_report.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    apply_timeline(cuts)
    for c in cuts:
        print(f"컷 {c['a']:.3f}~{c['b']:.3f} ({c['dur']:.3f}초) 쉼 앞 {c['pause_before']} 뒤 {c['pause_after']} → 남는 쉼 {c['new_pause']} · 자르는 곳 {c['rms_a_db']}/{c['rms_b_db']}dB · {' / '.join(c['lines'])}")
    print(f"길이 {rep['total_in']} → {rep['total_out']}초 · 줄 {len(rows)} → {len(new)}")


def apply_timeline(cuts):
    tlp, pre = ROOT / "_tmp/sjk01/timeline.json", ROOT / "_tmp/sjk01/timeline_precut.json"
    if not pre.exists():
        pre.write_text(tlp.read_text(encoding="utf-8"), encoding="utf-8")
    tl = json.load(open(pre, encoding="utf-8"))
    S = lambda t: t - sum(c["dur"] for c in cuts if t >= c["b"] - 1e-6)
    gone = lambda t: any(c["a"] - 1e-6 <= t < c["b"] - 1e-6 for c in cuts)
    dd = Path(__file__).resolve().parent / "data"
    for s in tl:
        t0, t1 = S(s["t0"]), S(s["t1"])
        lines = []
        for ln in s["lines"]:
            if gone(s["t0"] + ln["t0"]):
                print(f"  장면 {s['scene']} 줄 뺌: {ln['text']}")
                continue
            r = lambda x: round(S(s["t0"] + x) - t0, 3)
            lines.append(dict(ln, t0=r(ln["t0"]), t1=r(ln["t1"]), words=[dict(w, t0=r(w["t0"]), t1=r(w["t1"])) for w in ln["words"]]))
        s.update(t0=round(t0, 3), t1=round(t1, 3), dur=round(t1 - t0, 3), lines=lines)
        (dd / f"s{s['scene']:02d}.js").write_text("window.SC = " + json.dumps(
            {k: s[k] for k in ("scene", "t0", "t1", "dur", "pre", "post", "trans_in", "lines")}, ensure_ascii=False) + ";\n", encoding="utf-8")
    tlp.write_text(json.dumps(tl, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  시각표 끝 {tl[-1]['t1']}")


if __name__ == "__main__":
    main()
