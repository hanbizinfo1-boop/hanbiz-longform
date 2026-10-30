# -*- coding: utf-8 -*-
"""성제관03 — 연출표 71장면을 녹음 줄에 맞춘 시각표(2편 timeline.py 와 같은 계약).

장면 행·원고 줄 범위·전환은 `20_연출표.md` 2장 표에서 그대로 읽는다(손으로 옮기지 않음).
장면 시작 = 첫 원고 줄 말 시작 − LEAD, 끝 = 다음 장면 시작. 출력 _tmp/sjk03/timeline.json + data/sNN.js
    py -3.11 tools/scenes/sjk03/timeline.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CASE = ROOT / "핸드오프/2026-10-23_성제관03_배달앱수수료"
LINES = ROOT / "_tmp/sjk03/audio/lines.json"
OUT = ROOT / "_tmp/sjk03/timeline.json"
LEAD = 0.25
TOTAL = 547.213
D = 0.36                                   # 디졸브·칸 안으로 길이(경계 가운데 걸침)

# 연출표 «전환» 칸 → 조립기 전환 이름(3편은 거의 컷 — 층이 바뀔 때 몇 번만 디졸브, 장 시작은 칸 안으로)
TRANS = {"컷": "cut", "첫 장면": "cut", "컷 → 끝": "cut", "디졸브(층 바뀜)": "dissolve", "칸 안으로": "into"}


def table():
    rows = []
    for ln in (CASE / "20_연출표.md").read_text(encoding="utf-8").splitlines():
        c = [x.strip() for x in ln.strip().strip("|").split("|")]
        if len(c) < 12 or not c[0].isdigit():
            continue
        a, b = map(int, re.match(r"#(\d+)-(\d+)", c[2]).groups())
        rows.append({"scene": int(c[0]), "first": a - 1, "last": b - 1, "layer": c[4], "trans_in": TRANS[c[10]]})
    return rows


def main():
    L = json.load(open(LINES, encoding="utf-8"))
    T = table()
    assert [t["scene"] for t in T] == list(range(1, len(T) + 1))
    for k in range(len(T) - 1):
        assert T[k]["last"] + 1 == T[k + 1]["first"], ("원고 줄 빈틈", T[k]["scene"])
    assert T[-1]["last"] == len(L) - 1
    out = []
    for k, s in enumerate(T):
        t0 = 0.0 if k == 0 else round(L[s["first"]]["t0"] - LEAD, 3)
        t1 = round(L[T[k + 1]["first"]]["t0"] - LEAD, 3) if k + 1 < len(T) else TOTAL
        lines = [{"i": i, "text": r["text"], "t0": round(r["t0"] - t0, 3), "t1": round(r["t1"] - t0, 3),
                  "words": [{"w": w["w"], "t0": round(w["t0"] - t0, 3), "t1": round(w["t1"] - t0, 3)} for w in r["words"]]}
                 for i, r in enumerate(L[s["first"]:s["last"] + 1], s["first"])]
        out.append({"scene": s["scene"], "t0": t0, "t1": t1, "dur": round(t1 - t0, 3), "layer": s["layer"],
                    "engine": "html", "trans_in": s["trans_in"], "lines": lines})
    soft = lambda tr: tr != "cut"
    for k, s in enumerate(out):
        s["pre"] = D / 2 if soft(s["trans_in"]) else 0.0
        s["post"] = D / 2 if k + 1 < len(out) and soft(out[k + 1]["trans_in"]) else 0.0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    dd = Path(__file__).resolve().parent / "data"
    dd.mkdir(exist_ok=True)
    for s in out:
        (dd / f"s{s['scene']:02d}.js").write_text("window.SC = " + json.dumps(
            {k: s[k] for k in ("scene", "t0", "t1", "dur", "pre", "post", "layer", "trans_in", "lines")}, ensure_ascii=False) + ";\n", encoding="utf-8")
    for s in out:
        print(f"{s['scene']:2d} {s['t0']:7.2f}-{s['t1']:7.2f} ({s['dur']:5.2f}s) {s['layer']} {s['trans_in']:8s} {s['lines'][0]['text'][:24]}")


if __name__ == "__main__":
    main()
