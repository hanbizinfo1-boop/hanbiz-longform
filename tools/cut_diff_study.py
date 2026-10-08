# -*- coding: utf-8 -*-
r"""내 무음컷 vs 사장님 추가 컷 — 사장님이 무엇을 얼마나 더 잘랐는지 재서 «사장님 기준 여유값»을 만든다. 읽기 전용.

    python cut_diff_study.py <내 무음컷 시퀀스.json> <사장님 편집 시퀀스.json> <words.json> <16k.wav> <원본 끝초> <출력.md>
  시퀀스 json = 읽기/read_master.py 출력. 카메라 소리 클립(이름 SRC_NAME)의 원본 구간(s0~s1)만 본다.
  words.json = transcribe_words.py 출력(원본 시각).

재는 것
  1. 사장님이 더 지운 조각 = 내 살린 구간 − 사장님 살린 구간. 조각마다 말(단어)이 들어 있으면 «내용 컷»(중복·더듬기), 없으면 «무음 컷».
     무음 컷은 자리로 나눈다 — 앞 다듬기(말 시작 전) · 뒤 다듬기(말 끝 뒤) · 가운데(쉼 줄이기) · 통째(살렸던 조각 전체).
  2. 사장님 컷 경계마다 «말 끝 → 컷»(뒤 여유)·«컷 → 말 시작»(앞 여유). 말 끝·시작은 단어 시각을 소리 크기로 다듬은 값
     (단어 끝 뒤 0.3초 안에서 소리가 바닥+8dB 위로 남아 있는 마지막 지점 = 잔음 끝).
  3. 결과 화면에서의 쉼 = 앞 클립 뒤 여유 + 다음 클립 앞 여유. 문장 끝(…다/요/죠/까)과 문장 중간을 나눠 본다.
  4. 같은 자리에서 내 컷(여유 0.06)은 어땠는지 — 비교.
"""
import json
import re
import sys
from pathlib import Path

import numpy as np

SRC_NAME = "싱크1시간.mp4"
SR, HOP = 16000, 160                       # 10ms
END_RE = re.compile(r"(다|요|죠|까|네|니다|세요|어요|아요|거든요|잖아요)[.?!]?$")


def kept(seq_json, s_end):
    d = json.loads(Path(seq_json).read_text(encoding="utf-8"))
    iv = sorted((c["s0"], c["s1"]) for c in d["clips"] if c["kind"] == "audio" and c["name"] == SRC_NAME and c["s0"] < s_end)
    return [(a, min(b, s_end)) for a, b in iv]


def subtract(A, B):
    """A − B (구간 목록, 정렬)."""
    out = []
    for a0, a1 in A:
        cur = a0
        for b0, b1 in B:
            if b1 <= cur or b0 >= a1:
                continue
            if b0 > cur:
                out.append((cur, b0))
            cur = max(cur, b1)
        if cur < a1:
            out.append((cur, a1))
    return [(x, y) for x, y in out if y - x > 0.02]


def energy(wav):
    import soundfile as sf
    y, sr = sf.read(str(wav))
    assert sr == SR
    n = len(y) // HOP
    e = 20 * np.log10(np.sqrt((y[:n * HOP].reshape(n, HOP) ** 2).mean(1)) + 1e-9)
    return e


def floor_at(e, t, win=3.0):
    i0, i1 = max(0, int((t - win) * 100)), min(len(e), int((t + win) * 100))
    return float(np.percentile(e[i0:i1], 10)) if i1 > i0 else -60.0


def refine(words, e):
    """단어 끝을 잔음 끝까지, 시작을 소리 시작까지 소리 크기로 다듬는다."""
    out = []
    for w in words:
        fl = floor_at(e, w["t0"])
        thr = fl + 8
        j = int(w["t1"] * 100)
        k = min(len(e) - 1, j + 30)
        tail = j
        for i in range(j, k):
            if e[i] > thr:
                tail = i
        i = int(w["t0"] * 100)
        h = max(0, i - 15)
        head = i
        for q in range(i, h, -1):
            if e[q] > thr:
                head = q
        out.append(dict(w, e0=head / 100, e1=(tail + 1) / 100))
    return out


def words_in(W, a, b):
    return [w for w in W if min(w["t1"], b) - max(w["t0"], a) > 0.5 * (w["t1"] - w["t0"])]


def margins(U, W):
    """구간마다 (앞 여유, 뒤 여유, 끝 단어, 끝 단어가 문장 끝인가)."""
    rows = []
    for a, b in U:
        ws = [w for w in W if w["e0"] >= a - 0.05 and w["e1"] <= b + 0.05]
        if not ws:
            continue
        rows.append(dict(a=a, b=b, head=ws[0]["e0"] - a, tail=b - ws[-1]["e1"], last=ws[-1]["w"],
                         end=bool(END_RE.search(ws[-1]["w"]))))
    return rows


def q(v):
    v = np.array(v)
    return f"중앙 {np.median(v):.2f} · 25~75% {np.percentile(v, 25):.2f}~{np.percentile(v, 75):.2f} (n={len(v)})" if len(v) else "-"


def main():
    mine, boss, wj, wav, s_end, out = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], float(sys.argv[5]), Path(sys.argv[6])
    O, U = kept(mine, s_end), kept(boss, s_end)
    e = energy(wav)
    W = refine([w for s in json.loads(Path(wj).read_text(encoding="utf-8")) for w in s["words"] if w["t0"] < s_end], e)
    R = subtract(O, U)
    ADD = subtract(U, O)
    cats = {"내용 컷": [], "무음·앞": [], "무음·뒤": [], "무음·가운데": [], "무음·통째": []}
    for r0, r1 in R:
        ws = words_in(W, r0, r1)
        if ws:
            cats["내용 컷"].append((r0, r1, " ".join(w["w"] for w in ws)))
            continue
        seg = next(((a, b) for a, b in O if a - 0.01 <= r0 and r1 <= b + 0.01), None)
        if seg is None:
            cats["무음·가운데"].append((r0, r1, ""))
        elif abs(seg[0] - r0) < 0.02 and abs(seg[1] - r1) < 0.02:
            cats["무음·통째"].append((r0, r1, ""))
        elif abs(seg[0] - r0) < 0.02:
            cats["무음·앞"].append((r0, r1, ""))
        elif abs(seg[1] - r1) < 0.02:
            cats["무음·뒤"].append((r0, r1, ""))
        else:
            cats["무음·가운데"].append((r0, r1, ""))
    # 내용 컷 종류 — 지운 말이 바로 뒤(15초 안) 살린 말에 다시 나오면 «반복(다시 말함)», 짧으면 «더듬기·군말», 길면 «긴 덜어냄»
    def norm(t):
        return re.sub(r"[^가-힣A-Za-z0-9]", "", t)
    kinds = {"반복(다시 말함)": [], "더듬기·군말(1.2초 미만)": [], "긴 덜어냄(4초 이상)": [], "기타": []}
    for r0, r1, txt in cats["내용 컷"]:
        rw = [norm(w["w"]) for w in words_in(W, r0, r1) if len(norm(w["w"])) >= 2]
        after = "".join(norm(w["w"]) for w in W if r1 <= w["t0"] < r1 + 15 and any(a <= w["t0"] < b for a, b in U))
        rep = rw and sum(w in after for w in rw) / len(rw) >= 0.6
        k = "반복(다시 말함)" if rep else "더듬기·군말(1.2초 미만)" if r1 - r0 < 1.2 else "긴 덜어냄(4초 이상)" if r1 - r0 >= 4 else "기타"
        kinds[k].append((r0, r1, txt))
    mU, mO = margins(U, W), margins(O, W)
    pauses_end, pauses_mid = [], []
    for x, y in zip(mU, mU[1:]):
        if y["a"] - x["b"] < 0.03:                     # 원본에서 이어진 자리는 쉼이 아니다
            continue
        (pauses_end if x["end"] else pauses_mid).append(x["tail"] + y["head"])
    tot = sum(b - a for a, b in O)
    L = [f"# 무음컷 비교 — 내 컷(여유 0.06) vs 사장님 편집 (원본 0~{s_end:.0f}초)", "",
         f"- 내 컷 살린 길이 {tot / 60:.1f}분 → 사장님 {sum(b - a for a, b in U) / 60:.1f}분 (더 지움 {sum(b - a for a, b in R):.0f}초, {len(R)}조각)",
         f"- 사장님이 내 컷보다 **더 살린** 조각(내가 지웠는데 되살림): {len(ADD)}개 {sum(b - a for a, b in ADD):.1f}초", "",
         "## 1. 더 지운 조각 — 종류별", "", "| 종류 | 조각 | 합계(초) | 길이 중앙(초) |", "|---|---|---|---|"]
    for k, v in cats.items():
        ln = [b - a for a, b, _ in v]
        L.append(f"| {k} | {len(v)} | {sum(ln):.1f} | {np.median(ln):.2f} |" if ln else f"| {k} | 0 | 0 | - |")
    L += ["", "### 내용 컷 종류", "", "| 종류 | 조각 | 합계(초) | 길이 중앙 | 예 |", "|---|---|---|---|---|"]
    for k, v in kinds.items():
        ln = [y - x for x, y, _ in v]
        ex = " / ".join(f"«{t[:22]}»" for _, _, t in v[:3])
        L.append(f"| {k} | {len(v)} | {sum(ln):.1f} | {np.median(ln):.2f} | {ex} |" if ln else f"| {k} | 0 | 0 | - | |")
    L += ["", "## 2. 경계 여유 (초) — 단어 끝은 잔음까지 다듬은 값", "",
          f"- 사장님 뒤 여유(말 끝 → 컷): {q([m['tail'] for m in mU])}",
          f"  - 문장 끝: {q([m['tail'] for m in mU if m['end']])}",
          f"  - 문장 중간: {q([m['tail'] for m in mU if not m['end']])}",
          f"- 사장님 앞 여유(컷 → 말 시작): {q([m['head'] for m in mU])}",
          f"- 내 컷 뒤 여유: {q([m['tail'] for m in mO])}",
          f"- 내 컷 앞 여유: {q([m['head'] for m in mO])}",
          f"- 음수(단어/잔음을 깎은 경계): 사장님 뒤 {sum(m['tail'] < -0.02 for m in mU)} · 앞 {sum(m['head'] < -0.02 for m in mU)} / 내 컷 뒤 {sum(m['tail'] < -0.02 for m in mO)} · 앞 {sum(m['head'] < -0.02 for m in mO)}",
          "", "## 3. 결과 화면의 쉼(앞 클립 뒤 여유 + 다음 클립 앞 여유)", "",
          f"- 문장 끝 다음: {q(pauses_end)}", f"- 문장 중간: {q(pauses_mid)}"]
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    Path(out).with_suffix(".json").write_text(json.dumps(dict(cats={k: v for k, v in cats.items()}, kinds=kinds, mU=mU, mO=mO,
                                                              pauses_end=pauses_end, pauses_mid=pauses_mid), ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
