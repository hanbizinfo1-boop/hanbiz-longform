# -*- coding: utf-8 -*-
r"""내용 컷(더듬기·다시 말함·편집자에게 하는 말·덜어낼 설명) 후보 — 빡이사DB 사장님 실제 컷으로 배우고 잰다 (10-12).

사장님 10-12 «내가 더듬거나 내용 이상하면 자르거나 했던 부분, 내 기록 학습 데이터 기반으로 너에게 시키면 할 수 있겠어?»
+ «강사님 시리즈는 빡이사가 아니야, 빡이사 것만 참고해서 진행» → 정답지는 빡이사DB 본편 한 편뿐이다.

    # 1) 줄 목록 — 무음컷이 살린 말을 짧은 줄로(쉼 0.25초·문장 끝에서 끊음). --답 이면 사장님이 자른 줄에 ✂
    python content_cut_study.py 줄 <words.json> <cut_plan.json> <시작초> <끝초> <출력.txt> [--답 <비교_전체.json>]
    # 2) 채점 — 후보(줄 번호 목록 json)를 사장님 컷과 시간으로 겹쳐 잰다
    python content_cut_study.py 채점 <줄.txt> <후보.json> <비교_전체.json>

줄 번호는 «줄» 출력의 [번호]. 후보 json = [번호, …] 또는 {"cut": [번호, …]}.
"""
import json
import re
import sys
from pathlib import Path

GAP = 0.25          # 이 이상 쉬면 줄을 끊는다(무음편집 안전판의 «쉼» 기준과 같다)
END = re.compile(r"[.?!]$")


def lines_from(words_json, plan_json, t_from, t_to):
    keep = json.loads(Path(plan_json).read_text(encoding="utf-8"))["keep"]
    W = [w for s in json.loads(Path(words_json).read_text(encoding="utf-8")) for w in s["words"]
         if t_from <= w["t0"] < t_to]

    def region(t):
        for i, (a, b) in enumerate(keep):
            if a - 0.02 <= t <= b + 0.02:
                return i
        return None
    out, cur, prev = [], [], None
    for w in W:
        r = region((w["t0"] + w["t1"]) / 2)
        if r is None:
            continue
        brk = cur and (w["t0"] - cur[-1]["t1"] > GAP or r != prev or END.search(cur[-1]["w"]))
        if brk:
            out.append(cur)
            cur = []
        cur.append(w)
        prev = r
    if cur:
        out.append(cur)
    return [(round(ws[0]["t0"], 2), round(ws[-1]["t1"], 2), " ".join(w["w"] for w in ws)) for ws in out]


def truth(cmp_json):
    return [(a, b) for a, b, _ in json.loads(Path(cmp_json).read_text(encoding="utf-8"))["cats"]["내용 컷"]]


def overlap(a, b, T):
    return sum(max(0.0, min(b, y) - max(a, x)) for x, y in T)


def read_lines(p):
    rows = []
    for ln in Path(p).read_text(encoding="utf-8").splitlines():
        m = re.match(r"\[(\d+)\] ([\d.]+)~([\d.]+) (✂ )?(.*)", ln)
        if m:
            rows.append((int(m[1]), float(m[2]), float(m[3]), m[5]))
    return rows


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    cmd = sys.argv[1]
    if cmd == "줄":
        wj, pj, t0, t1, out = sys.argv[2], sys.argv[3], float(sys.argv[4]), float(sys.argv[5]), Path(sys.argv[6])
        T = truth(sys.argv[sys.argv.index("--답") + 1]) if "--답" in sys.argv else None
        L = lines_from(wj, pj, t0, t1)
        txt, n_cut = [], 0
        for i, (a, b, s) in enumerate(L):
            mark = ""
            if T is not None and overlap(a, b, T) >= 0.5 * (b - a):
                mark, n_cut = "✂ ", n_cut + 1
            txt.append(f"[{i}] {a:.2f}~{b:.2f} {mark}{s}")
        out.write_text("\n".join(txt) + "\n", encoding="utf-8")
        print(f"{len(L)}줄" + (f" · ✂ {n_cut}줄" if T is not None else "") + f" → {out}")
    elif cmd == "채점":
        rows = {i: (a, b, s) for i, a, b, s in read_lines(sys.argv[2])}
        pred = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
        pred = pred["cut"] if isinstance(pred, dict) else pred
        lo, hi = min(a for a, b, s in rows.values()), max(b for a, b, s in rows.values())
        T = [(a, b) for a, b in truth(sys.argv[4]) if a < hi and b > lo]
        P = [rows[i][:2] for i in pred if i in rows]
        tp_s = sum(overlap(a, b, T) for a, b in P)
        pred_s = sum(b - a for a, b in P)
        true_s = sum(b - a for a, b in T)
        hit = sum(1 for a, b in T if overlap(a, b, P) >= 0.5 * (b - a))
        wrong = [(i, *rows[i]) for i in pred if i in rows and overlap(*rows[i][:2], T) < 0.5 * (rows[i][1] - rows[i][0])]
        print(f"사장님 내용 컷 {len(T)}곳 {true_s:.0f}초 · 후보 {len(P)}줄 {pred_s:.0f}초")
        print(f"잡은 비율(재현) 곳 {hit}/{len(T)} = {hit / max(len(T), 1):.0%} · 초 {tp_s / max(true_s, 1e-9):.0%}")
        print(f"맞은 비율(정밀) 초 {tp_s / max(pred_s, 1e-9):.0%} · 사장님은 살렸는데 후보로 찍은 줄 {len(wrong)}개")
        for i, a, b, s in wrong[:40]:
            print(f"  ✗ [{i}] {a:.1f} {s}")


if __name__ == "__main__":
    main()
