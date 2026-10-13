# -*- coding: utf-8 -*-
r"""자막 전체 글 ↔ 받아쓰기 전체 글을 글자 단위로 맞춰 «다른 곳»만 뽑는다(맞춤법·오인식 후보).

    python tools/auto/sub_diff.py <edit.json> <words.json> <출력.md>

공백·문장부호는 빼고 비교한다. 다른 곳마다 자막 줄 시각·자막 글·들린 글(받아쓰기)·앞뒤 맥락을 적는다.
"""
import difflib
import json
import re
import sys

KEEP = re.compile(r"[0-9A-Za-z가-힣%]")


def main():
    edit, words, out = sys.argv[1:4]
    caps = sorted((i for i in json.load(open(edit, encoding="utf-8"))["items"] if i["track"] == "C1"), key=lambda i: i["t0"])
    segs = json.load(open(words, encoding="utf-8"))
    A, Aidx = [], []
    for ci, c in enumerate(caps):
        for ch in c.get("text", ""):
            if KEEP.match(ch):
                A.append(ch); Aidx.append(ci)
    B, Bt = [], []
    for s in segs:
        for w in s["words"]:
            for ch in w["w"]:
                if KEEP.match(ch):
                    B.append(ch); Bt.append(w["t0"])
    sm = difflib.SequenceMatcher(None, A, B, autojunk=False)
    lines = ["# 자막 ↔ 받아쓰기 다른 곳", "", "| # | 시각 | 자막 줄 | 자막 | 들린 글 |", "|---|---|---|---|---|"]
    n = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        ci = Aidx[min(i1, len(Aidx) - 1)]
        c = caps[ci]
        n += 1
        a = "".join(A[max(0, i1 - 6):i1]) + "[" + "".join(A[i1:i2]) + "]" + "".join(A[i2:i2 + 6])
        b = "".join(B[max(0, j1 - 6):j1]) + "[" + "".join(B[j1:j2]) + "]" + "".join(B[j2:j2 + 6])
        lines.append(f"| {n} | {c['t0']:.2f} | {c.get('text','')} | {a} | {b} |")
    open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("다른 곳", n, "· 일치율", round(sm.ratio(), 4))


if __name__ == "__main__":
    main()
