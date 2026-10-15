# -*- coding: utf-8 -*-
"""성제관01 — 연출표 53장면을 녹음 줄(뜻 자리)에 맞춘 시각표.

SCENES[n] = (장면 번호, 시작 줄 index(lines.json), 엔진, 들어오는 전환)
장면 시작 = 시작 줄 말 시작 − LEAD, 끝 = 다음 장면 시작. 출력 _tmp/sjk01/timeline.json
각 장면에 그 구간 줄·어절 시각(장면 안 상대 시각 rel)을 같이 담아 장면 HTML 이 그대로 읽는다.
    py -3.11 tools/scenes/sjk01/timeline.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LINES = ROOT / "_tmp/sjk01/audio/lines.json"
OUT = ROOT / "_tmp/sjk01/timeline.json"
LEAD = 0.25
TOTAL = 711.93

# (장면, 시작 줄, 엔진, 들어오는 전환)  전환: cut · dissolve · push(종이 밀어내기) · zoom(자료 속으로) · split(반으로 갈라짐) · wipe(지우개) · cont(원테이크 이어짐)
SCENES = [
    (1, 0, "blender", "cut"), (2, 3, "blender", "cont"), (3, 7, "html", "dissolve"),
    (4, 9, "html", "push"), (5, 15, "html", "cut"), (6, 25, "html", "cut"),
    (7, 30, "blender", "cut"), (8, 37, "html", "cut"), (9, 46, "html", "zoom"),
    (10, 57, "html", "dissolve"), (11, 72, "photo", "cut"), (12, 74, "photo", "cut"),
    (13, 78, "photo", "cut"), (14, 87, "html", "cut"), (15, 93, "html", "cut"),
    (16, 107, "html", "cut"), (17, 111, "html", "cut"), (18, 122, "html", "split"),
    (19, 127, "html", "cut"), (20, 146, "html", "push"), (21, 160, "html", "cut"),
    (22, 167, "html", "cut"), (23, 176, "html", "cut"), (24, 184, "html", "cut"),
    (25, 193, "html", "zoom"), (26, 204, "html", "push"), (27, 209, "photo", "dissolve"),
    (28, 212, "photo", "cut"), (29, 225, "html", "cut"), (30, 243, "html", "cut"),
    (31, 249, "photo", "cut"), (32, 257, "html", "cut"), (33, 270, "html", "wipe"),
    (34, 277, "blender", "cut"), (35, 287, "html", "cut"), (36, 299, "html", "zoom"),
    (37, 304, "html", "split"), (38, 314, "photo", "cut"), (39, 322, "blender", "cut"),
    (40, 335, "html", "cut"), (41, 343, "html", "cut"), (42, 355, "html", "cut"),
    (43, 365, "photo", "dissolve"), (44, 372, "html", "cut"), (45, 388, "blender", "cut"),
    (46, 392, "blender", "cont"), (47, 397, "html", "push"), (48, 402, "photo", "cut"),
    (49, 405, "html", "cut"), (50, 406, "html", "cut"), (51, 411, "photo", "dissolve"),
    (52, 413, "blender", "cut"), (53, 418, "html", "cut"),
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
    D = 0.6                                    # 전환 길이(경계 가운데 걸침)
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
