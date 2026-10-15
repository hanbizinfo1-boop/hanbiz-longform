# -*- coding: utf-8 -*-
"""성제관01 — 녹음 원고(한 줄 = 자막 한 줄)를 녹음에 강제 정렬해 줄·어절 시각을 얻는다.

1) whisper 단어(대략 시각)와 원고 글자를 difflib 로 맞춰 줄마다 «어디쯤»을 잡고
2) 줄 몇 개씩 묶어 그 구간 소리에 MMS_FA 강제 정렬(tools/auto/ko_align) → 어절 시각
3) 자막 시각 = 첫 어절 시작 ~ 마지막 어절 끝 +0.15초(다음 자막 시작을 넘지 않게)
출력: _tmp/sjk01/audio/lines.json  [{i, src, text, t0, t1, end, words:[{w,t0,t1,sc}], score}]
    py -3.11 tools/scenes/sjk01/align_lines.py [--wav 다른소리.wav --out 경로]   (검수 때는 완성본 소리로 다시)
"""
import argparse
import difflib
import json
import re
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.auto.ko_align import Aligner  # noqa: E402

CASE = ROOT / "핸드오프/2026-10-14_성제관01_AI10가지"
TXT = CASE / "10_분석/녹음원고.txt"
WORDS = ROOT / "_tmp/sjk01/audio/words.json"

SINO = ["", "일", "이", "삼", "사", "오", "육", "칠", "팔", "구"]
NATIVE_SPOKEN = {"12시": "열두시", "4개": "네개", "4개를": "네개를"}


def sino(n):
    n = int(n)
    if n == 0:
        return "영"
    out = ""
    for unit, name in ((10000, "만"), (1000, "천"), (100, "백"), (10, "십")):
        d = n // unit
        if d:
            out += ("" if d == 1 and unit != 10000 else SINO[d]) + name
            n %= unit
    return out + SINO[n]


def spoken(tok):
    t = tok
    for k, v in NATIVE_SPOKEN.items():
        if t.startswith(k):
            t = v + t[len(k):]
    t = t.replace("○○", "오오").replace("GPT", "지피티").replace("AI", "에이아이").replace("%", "퍼센트")
    t = re.sub(r"\d+", lambda m: sino(m.group()), t)
    t = re.sub(r"[^\w가-힣]", "", t)
    return t


def load_lines():
    rows = []
    for ln in TXT.read_text(encoding="utf-8").splitlines():
        if not ln.strip() or ln.startswith("#"):
            continue
        src, text = ln.split("\t", 1)
        rows.append({"src": src.strip(), "text": text.strip()})
    for i, r in enumerate(rows):
        r["i"] = i
    return rows


def rough_times(rows):
    """원고 글자열과 whisper 글자열을 맞춰 줄마다 대략 시작·끝."""
    segs = json.load(open(WORDS, encoding="utf-8"))
    wchars, wtimes = [], []
    for s in segs:
        for w in s["words"]:
            cs = re.sub(r"[^\w가-힣]", "", w["w"])
            for k, c in enumerate(cs):
                wchars.append(c)
                wtimes.append(w["t0"] + (w["t1"] - w["t0"]) * k / max(1, len(cs)))
    lchars, lidx = [], []
    for r in rows:
        for c in re.sub(r"[^\w가-힣]", "", r["text"]):
            lchars.append(c)
            lidx.append(r["i"])
    sm = difflib.SequenceMatcher(None, lchars, wchars, autojunk=False)
    m = [None] * len(lchars)
    for a, b, n in sm.get_matching_blocks():
        for k in range(n):
            m[a + k] = wtimes[b + k]
    for r in rows:
        ts = [m[k] for k in range(len(lchars)) if lidx[k] == r["i"] and m[k] is not None]
        r["rough"] = (min(ts), max(ts)) if ts else None
    # 비어 있으면 앞뒤로 메움
    for k, r in enumerate(rows):
        if r["rough"] is None:
            prev = next((rows[j]["rough"][1] for j in range(k - 1, -1, -1) if rows[j]["rough"]), 0.0)
            nxt = next((rows[j]["rough"][0] for j in range(k + 1, len(rows)) if rows[j]["rough"]), prev + 2)
            r["rough"] = (prev, nxt)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wav", default=str(ROOT / "_tmp/sjk01/audio/voice16k.wav"))
    ap.add_argument("--out", default=str(ROOT / "_tmp/sjk01/audio/lines.json"))
    ap.add_argument("--group", type=int, default=6)
    a = ap.parse_args()
    wav, sr = sf.read(a.wav, dtype="float32")
    if wav.ndim > 1:
        wav = wav.mean(1)
    assert sr == 16000, "16k 모노로 넣는다"
    rows = rough_times(load_lines())
    al = Aligner()
    G = a.group
    for g0 in range(0, len(rows), G):
        grp = rows[g0:g0 + G]
        w0 = max(0.0, grp[0]["rough"][0] - 1.2)
        if g0 > 0 and rows[g0 - 1].get("t1"):
            w0 = max(w0, rows[g0 - 1]["t1"] - 0.05)
        w1 = min(len(wav) / sr, grp[-1]["rough"][1] + 1.5)
        nxt = rows[g0 + G]["rough"][0] if g0 + G < len(rows) else None
        if nxt:
            w1 = min(w1, nxt + 0.3) if nxt + 0.3 > grp[-1]["rough"][1] else w1
        toks, owner = [], []
        for r in grp:
            for w in r["text"].split():
                sp = spoken(w)
                if sp:
                    toks.append(sp)
                    owner.append((r["i"], w))
        clip = wav[int(w0 * sr):int(w1 * sr)]
        spans = al.align(clip, toks)
        for r in grp:
            r["words"] = []
        for (li, w), sp in zip(owner, spans):
            if sp is None:
                continue
            rows[li]["words"].append({"w": w, "t0": round(w0 + sp[0], 3), "t1": round(w0 + sp[1], 3), "sc": round(sp[2], 3)})
        for r in grp:
            if r["words"]:
                r["t0"] = r["words"][0]["t0"]
                r["t1"] = r["words"][-1]["t1"]
                r["score"] = round(float(np.mean([w["sc"] for w in r["words"]])), 3)
        print(f"{g0:3d}~ {w0:7.2f}-{w1:7.2f} " + " | ".join(f"{r.get('t0', 0):.2f} {r['text'][:14]}" for r in grp), flush=True)
    for k, r in enumerate(rows):
        nxt = rows[k + 1]["t0"] if k + 1 < len(rows) else r["t1"] + 1
        r["end"] = round(min(r["t1"] + 0.15, nxt - 0.02), 3)
        r.pop("rough", None)
    Path(a.out).write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    low = [r for r in rows if r.get("score", 0) < 0.45]
    print(f"저장 {a.out} · 줄 {len(rows)} · 점수 0.45 미만 {len(low)}")
    for r in low:
        print(f"  낮음 {r['t0']:.2f} {r['score']} {r['text']}")


if __name__ == "__main__":
    main()
