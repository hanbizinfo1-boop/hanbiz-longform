r"""종이 책상 장면(s07·s08·s32·s42) spec 만들기 — 시각은 data/sNN.js 의 낱말 시각에서 가져온다(장면 html 과 같은 시계).

    py -3.11 tools/scenes/sjk02/blender/desk_specs.py      → _tmp/sjk02/blender/spec_sNN.json
"""
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
DATA = HERE.parent / "data"
OUT = ROOT / "_tmp" / "sjk02" / "blender"


def sc(n):
    t = (DATA / f"s{n:02d}.js").read_text(encoding="utf-8")
    return json.loads(t[t.index("{"):t.rindex("}") + 1])


def at(d, word, nth=0, end=False, exact=False):
    k = 0
    for l in d["lines"]:
        for w in l["words"]:
            ww = w["w"].strip(".,?!'\"")
            if (ww == word) if exact else (word in w["w"]):
                if k == nth:
                    return w["t1"] if end else w["t0"]
                k += 1
    raise KeyError(word)


def base(d, out):
    return {"out": f"_tmp/sjk02/blender/{out}", "pre": d["pre"], "dur": d["dur"], "post": d["post"],
            "desk": "소재/sjk02/codex/t_dark_desk.png", "desk_size": [3.2, 2.13]}


# 열 장 자리(두 줄, 살짝 어긋나게) — s07·s08·s32 가 같은 배치를 쓴다(같은 책상으로 돌아옴)
R = random.Random(19)
LAYOUT = []
for i in range(10):
    row, col = divmod(i, 5)
    LAYOUT.append({"x": round(-0.56 + 0.28 * col + R.uniform(-0.025, 0.025) + (0.06 if row else 0), 3),
                   "y": round((0.175 if row == 0 else -0.165) + R.uniform(-0.02, 0.02), 3),
                   "rz": round(R.uniform(-6, 6), 1), "z": (i * 2) % 3})
DESC_Y = -0.0615          # 종이 가운데에서 «메뉴 설명» 줄까지(m)


def s07():
    d = sc(7); s = base(d, "s07")
    t_ten, t_read, t_same = at(d, "열"), at(d, "읽어"), at(d, "비슷비슷해요")
    order = sorted(range(10), key=lambda i: LAYOUT[i]["x"])
    sheets = []
    for k, i in enumerate(order):
        L = LAYOUT[i]
        dt = 0.10 + 0.205 * k                              # 첫 말부터 «군데» 끝까지 열 장이 차례로 내려앉음
        w = t_same + 0.06 * k
        sheets.append(dict(L, id=f"a{i}", tex=f"menuA{i}", drop=round(dt, 3), desat=[[w, 0], [w + 0.35, 1]]))
    s["sheets"] = sheets
    s["cam"] = [
        {"t": -d["pre"], "pos": [-0.95, -0.80, 0.55], "look": [-0.40, 0.02, 0.0], "lens": 38, "fstop": 3.2},
        {"t": t_read - 0.1, "pos": [0.05, -0.78, 0.50], "look": [0.20, 0.0, 0.0], "lens": 38, "fstop": 3.2},
        {"t": d["dur"] + d["post"], "pos": [0.42, -0.52, 0.30], "look": [0.58, -0.17 + DESC_Y, 0.0], "lens": 42, "fstop": 2.6},
    ]
    return s


def s08():
    d = sc(8); s = base(d, "s08")
    front = sorted([i for i in range(10) if i >= 5], key=lambda i: LAYOUT[i]["x"])
    s["sheets"] = [dict(L, id=f"a{i}", tex=f"menuA{i}") for i, L in enumerate(LAYOUT)]
    a, b = LAYOUT[front[1]], LAYOUT[front[3]]        # 세 장만 천천히(빠르면 흐려 안 읽힘)
    ya, yb = a["y"] + DESC_Y, b["y"] + DESC_Y
    s["cam"] = [
        {"t": -d["pre"], "pos": [a["x"] - 0.08, ya - 0.20, 0.16], "look": [a["x"] - 0.01, ya, 0.0], "lens": 50, "fstop": 4.0},
        {"t": d["dur"] + d["post"], "pos": [b["x"] - 0.04, yb - 0.20, 0.16], "look": [b["x"] + 0.03, yb, 0.0], "lens": 50, "fstop": 4.0},
    ]
    return s


def s32():
    """같은 책상으로 돌아옴 — A 열 장은 이미 회색, «B는»에 B 한 장이 가운데 내려앉아 색이 남고 «딱 한 줄»에 주홍 형광."""
    d = sc(32); s = base(d, "s32")
    tB, tAI, tOne = at(d, "B는"), at(d, "AI한테"), at(d, "한", 1, exact=True)
    s["sheets"] = [dict(L, id=f"a{i}", tex=f"menuA{i}", desat=[[-1, 1], [0, 1]]) for i, L in enumerate(LAYOUT)]
    s["sheets"].append({"id": "b", "tex": "menuB", "tex2": "menuB_mk", "x": 0.0, "y": 0.0, "rz": -2.5, "z": 6, "s": 1.04,
                        "drop": round(tB + 0.05, 3), "lift": [[tAI, 0], [tAI + 0.4, 0.012]],
                        "wipe": [[tOne, 0], [tOne + 0.55, 1]]})
    y = DESC_Y * 1.04 - 0.003
    s["cam"] = [
        {"t": -d["pre"], "pos": [-0.10, -0.62, 1.20], "look": [0.0, 0.0, 0.0], "lens": 32, "fstop": 6.0},
        {"t": tB - 0.1, "pos": [0.05, -0.58, 1.10], "look": [0.02, 0.0, 0.0], "lens": 32, "fstop": 6.0},
        {"t": tB + 1.9, "pos": [0.0, -0.36, 0.52], "look": [0.0, -0.02, 0.0], "lens": 38, "fstop": 3.5},
        {"t": tOne - 0.1, "pos": [-0.04, -0.26, 0.33], "look": [0.0, y + 0.01, 0.0], "lens": 40, "fstop": 2.8},
        {"t": d["dur"] + d["post"], "pos": [-0.02, -0.24, 0.31], "look": [0.01, y + 0.01, 0.0], "lens": 40, "fstop": 2.8},
    ]
    return s


def _w(sh, lx, ly, z=0.006):
    """종이 안 좌표(m, 가운데 기준) → 책상 좌표."""
    import math
    a = math.radians(sh["rz"]); k = sh.get("s", 1.0)
    return [round(sh["x"] + k * (lx * math.cos(a) - ly * math.sin(a)), 4), round(sh["y"] + k * (lx * math.sin(a) + ly * math.cos(a)), 4), z]


def s42():
    """★2 그 한 줄이 따라다닌다 — B 메뉴의 주홍 한 줄에서 실이 나와 리뷰 답글 → 소식 → 차림표 → 손님 쪽지로 건너다님."""
    d = sc(42); s = base(d, "s42")
    t_doubt, t_once, t_each = at(d, "그거"), at(d, "한", 1, exact=True), at(d, "시킬")
    t_rev, t_news, t_board, t_month, t_cust, t_name, t_first = at(d, "리뷰"), at(d, "소식"), at(d, "메뉴판에도"), at(d, "쌓이면"), at(d, "손님이", 1), at(d, "이름보다"), at(d, "먼저")
    M = {"id": "b", "tex": "menuB", "tex2": "menuB_mk", "x": -0.46, "y": 0.02, "rz": -3, "z": 5,
         "wipe": [[-1, 1], [t_once, 1], [t_once + 0.45, 0], [t_each + 0.2, 0], [t_each + 0.9, 1]]}
    RV = {"id": "rv", "tex": "reviewB", "tex2": "reviewB_nm0", "x": -0.13, "y": 0.06, "rz": 5, "z": 5, "drop": round(t_rev - 0.15, 3), "mix": [[t_name, 0], [t_name + 0.5, 1]]}
    NW = {"id": "nw", "tex": "newsB", "tex2": "newsB_nm0", "x": 0.19, "y": -0.01, "rz": -4, "z": 5, "drop": round(t_news - 0.15, 3), "mix": [[t_name + 0.08, 0], [t_name + 0.58, 1]]}
    BD = {"id": "bd", "tex": "boardB", "tex2": "boardB_nm0", "x": 0.50, "y": 0.05, "rz": 3, "z": 5, "drop": round(t_board - 0.15, 3), "mix": [[t_name + 0.16, 0], [t_name + 0.66, 1]]}
    GS = {"id": "gs", "tex": "guest", "x": 0.16, "y": -0.33, "rz": -7, "z": 6, "s": 0.62, "drop": round(t_cust - 0.1, 3)}
    R2 = random.Random(42); pile = []
    spots = [(-0.78, 0.30), (-0.70, -0.30), (-0.30, 0.38), (0.02, 0.40), (0.36, 0.40), (0.78, 0.28), (0.80, -0.28), (-0.30, -0.36)]
    for j, (x, y) in enumerate(spots):
        pile.append({"id": f"p{j}", "tex": f"pile{j}", "x": x + R2.uniform(-0.03, 0.03), "y": y + R2.uniform(-0.03, 0.03), "rz": R2.uniform(-14, 14),
                     "z": j % 3, "drop": round(t_month + 0.05 + 0.12 * j, 3)})
    s["sheets"] = [M, RV, NW, BD, GS] + pile
    hl = [_w(M, -0.085, -0.064), _w(M, 0.075, -0.064), _w(RV, -0.01, -0.059), _w(NW, -0.06, -0.045), _w(BD, 0.0, -0.099), _w(GS, 0.035, -0.055)]   # 손님 쪽지는 글 아래 빈 자리에서 끝냄(글 위를 덮지 않게)
    pts = [hl[0], hl[1]]
    for a, b in zip(hl[1:], hl[2:]):
        pts.append([round((a[0] + b[0]) / 2, 4), round((a[1] + b[1]) / 2, 4), 0.055]); pts.append(b)
    nseg = len(pts) - 1
    s["thread"] = {"pts": pts, "width": 0.0028, "keys": [[t_each + 0.2, 0], [t_each + 0.9, 1 / nseg], [t_rev + 0.25, 3 / nseg], [t_news + 0.25, 5 / nseg],
                                                          [t_board + 0.25, 7 / nseg], [t_cust + 0.45, 9 / nseg]],
                   "glow": [[t_first, 1.2], [t_first + 0.5, 3.5]], "show": t_each + 0.2}
    cx = lambda sh: sh["x"]
    s["cam"] = [
        {"t": -d["pre"], "pos": [cx(M) - 0.13, -0.19, 0.13], "look": [cx(M) - 0.02, -0.045, 0.0], "lens": 50, "fstop": 2.2},
        {"t": t_doubt - 0.1, "pos": [cx(M) - 0.08, -0.19, 0.14], "look": [cx(M) + 0.02, -0.045, 0.0], "lens": 50, "fstop": 2.2},
        {"t": t_doubt + 1.8, "pos": [cx(M) + 0.25, -0.80, 1.05], "look": [cx(M) + 0.20, 0.0, 0.0], "lens": 35, "fstop": 5.0},
        {"t": t_each - 0.1, "pos": [cx(M) + 0.05, -0.50, 0.50], "look": [cx(M) + 0.08, -0.02, 0.0], "lens": 38, "fstop": 3.5},
        {"t": t_rev + 0.1, "pos": [cx(RV) - 0.10, -0.50, 0.48], "look": [cx(RV) - 0.06, -0.02, 0.0], "lens": 38, "fstop": 3.5},
        {"t": t_news + 0.1, "pos": [cx(NW) - 0.10, -0.50, 0.48], "look": [cx(NW) - 0.06, -0.02, 0.0], "lens": 38, "fstop": 3.5},
        {"t": t_board + 0.1, "pos": [cx(BD) - 0.12, -0.52, 0.50], "look": [cx(BD) - 0.08, -0.02, 0.0], "lens": 38, "fstop": 3.5},
        {"t": t_month + 0.9, "pos": [0.04, -0.95, 1.25], "look": [0.04, -0.02, 0.0], "lens": 32, "fstop": 6.0},
        {"t": t_cust + 0.9, "pos": [cx(GS) - 0.04, -0.70, 0.42], "look": [cx(GS), -0.30, 0.0], "lens": 42, "fstop": 3.2},
        {"t": t_name - 0.15, "pos": [cx(GS) - 0.01, -0.68, 0.43], "look": [cx(GS) + 0.01, -0.29, 0.0], "lens": 42, "fstop": 3.2},
        {"t": t_name + 1.2, "pos": [0.02, -0.72, 1.30], "look": [0.02, -0.06, 0.0], "lens": 32, "fstop": 6.0},
        {"t": d["dur"] + d["post"], "pos": [0.02, -0.62, 1.38], "look": [0.02, -0.05, 0.0], "lens": 32, "fstop": 6.0},
    ]
    return s


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in (("s07", s07), ("s08", s08), ("s32", s32), ("s42", s42)):
        p = OUT / f"spec_{name}.json"
        p.write_text(json.dumps(fn(), ensure_ascii=False, indent=1), encoding="utf-8")
        print("ok", p)


if __name__ == "__main__":
    main()
