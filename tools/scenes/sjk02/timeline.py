# -*- coding: utf-8 -*-
"""성제관02 — 연출표 72장면을 녹음 줄(뜻 자리)에 맞춘 시각표.

SCENES[n] = (장면 번호, 시작 줄 index(lines.json), 엔진, 들어오는 전환)
장면 시작 = 시작 줄 말 시작 − LEAD, 끝 = 다음 장면 시작. 출력 _tmp/sjk02/timeline.json
각 장면에 그 구간 줄·어절 시각(장면 안 상대 시각 rel)을 같이 담아 장면 HTML 이 그대로 읽는다.
    py -3.11 tools/scenes/sjk02/timeline.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LINES = ROOT / "_tmp/sjk02/audio/lines.json"
OUT = ROOT / "_tmp/sjk02/timeline.json"
LEAD = 0.25
TOTAL = 635.535

# (장면, 시작 줄, 엔진, 들어오는 전환) — 장면 번호 = 20_연출표.md 행 번호(2·3 은 1 안의 숏, 71 은 편집본에서 지워진 말이라 없음)
# 전환(2편 — 1편 휙·확대·밀기 대신, 연출설계 3-3): cut · shut_dn(셔터 내림) · shut_up(셔터 올림) · desat(탈색 넘김) · slide(옆 흐름 이어짐)
#   · flip(카드 뒤집기) · into(모양 안으로) · match(모양 이어 붙이기 — 원이 다음 원으로) · dissolve(1편 것 — 20% 이하)
SCENES = [
    (1, 0, "html", "cut"), (4, 3, "html", "slide"), (5, 7, "html", "desat"), (6, 9, "html", "cut"),
    (7, 12, "html", "into"), (8, 16, "html", "cut"), (9, 17, "html", "flip"), (10, 20, "html", "desat"),
    (12, 25, "html", "slide"), (13, 28, "html", "desat"), (14, 30, "html", "shut_up"),
    (15, 33, "html", "cut"), (16, 37, "html", "desat"), (17, 41, "html", "cut"), (18, 43, "html", "slide"),
    (19, 46, "html", "cut"), (20, 48, "html", "into"), (21, 57, "html", "cut"), (22, 63, "html", "desat"),
    (23, 68, "html", "cut"), (24, 74, "html", "flip"), (25, 77, "html", "shut_up"), (26, 82, "html", "match"),
    (27, 85, "html", "cut"), (28, 94, "html", "into"), (29, 99, "html", "cut"), (30, 108, "html", "cut"),
    (31, 117, "html", "desat"), (32, 120, "html", "cut"), (33, 126, "html", "into"), (34, 132, "html", "dissolve"),
    (35, 140, "html", "cut"), (36, 151, "html", "flip"), (37, 169, "html", "slide"), (38, 173, "html", "cut"),
    (39, 187, "html", "shut_up"), (40, 203, "html", "cut"), (41, 215, "html", "desat"), (42, 223, "html", "slide"),
    (43, 237, "html", "cut"), (45, 244, "html", "cut"), (46, 254, "html", "cut"),
    (47, 259, "html", "flip"), (48, 263, "html", "slide"), (49, 269, "html", "cut"), (50, 281, "html", "match"),
    (51, 292, "html", "cut"), (52, 296, "html", "dissolve"), (53, 306, "html", "desat"), (54, 309, "html", "cut"),
    (55, 317, "html", "into"), (56, 326, "html", "shut_dn"), (57, 337, "html", "shut_up"), (58, 344, "html", "into"),
    (59, 353, "html", "cut"), (60, 361, "html", "slide"), (61, 371, "html", "dissolve"), (62, 376, "html", "cut"),
    (63, 380, "html", "flip"), (64, 382, "html", "slide"), (65, 393, "html", "match"), (66, 404, "html", "cut"),
    (67, 417, "html", "match"), (68, 430, "html", "desat"), (69, 443, "html", "cut"), (70, 453, "html", "desat"),
    (72, 460, "html", "shut_up"), (73, 463, "html", "cut"),
]


def main():
    rows = json.load(open(LINES, encoding="utf-8"))
    out = []
    for k, (n, li, eng, tr) in enumerate(SCENES):
        t0 = 0.0 if k == 0 else round(rows[li]["t0"] - LEAD, 3)
        nxt = SCENES[k + 1][1] if k + 1 < len(SCENES) else None
        t1 = round(rows[nxt]["t0"] - LEAD, 3) if nxt is not None else TOTAL
        lines = []
        for r in rows[li:(nxt if nxt is not None else len(rows))]:
            lines.append({"i": r["i"], "text": r["text"], "t0": round(r["t0"] - t0, 3), "t1": round(r["t1"] - t0, 3),
                          "words": [{"w": w["w"], "t0": round(w["t0"] - t0, 3), "t1": round(w["t1"] - t0, 3)} for w in r["words"]]})
        out.append({"scene": n, "t0": t0, "t1": t1, "dur": round(t1 - t0, 3), "engine": eng, "trans_in": tr, "lines": lines})
    D = 0.36                                   # 전환 길이(경계 가운데 걸침) — 2편 0.3~0.4초
    soft = lambda tr: tr not in ("cut", "cont")
    for k, s in enumerate(out):
        s["pre"] = D / 2 if soft(s["trans_in"]) else 0.0
        s["post"] = D / 2 if k + 1 < len(out) and soft(out[k + 1]["trans_in"]) else 0.0
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    dd = Path(__file__).resolve().parent / "data"
    dd.mkdir(exist_ok=True)
    for s in out:
        (dd / f"s{s['scene']:02d}.js").write_text("window.SC = " + json.dumps(
            {k: s[k] for k in ("scene", "t0", "t1", "dur", "pre", "post", "trans_in", "lines")}, ensure_ascii=False) + ";\n", encoding="utf-8")
    for s in out:
        print(f"{s['scene']:2d} {s['t0']:7.2f}-{s['t1']:7.2f} ({s['dur']:5.2f}s) {s['engine']:7s} {s['trans_in']:8s} {s['lines'][0]['text'][:24]}")


if __name__ == "__main__":
    main()
