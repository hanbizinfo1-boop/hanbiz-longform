# -*- coding: utf-8 -*-
r"""자막 검수 — 사장님 자막(prproj C1)을 받아쓰기 단어 시각과 대조한다 (10-13 규칙 3: 맞춤법 · SRT↔목소리 타이밍).

    python tools/auto/sub_check.py <edit.json> <words.json> <출력.json>

줄마다: 자막 글 · 겹치는 받아쓰기 글 · 글 일치율 · 시작/끝 어긋남(첫 단어 시작 − 자막 시작, 자막 끝 − 마지막 단어 끝).
판정은 설계자가 한다(받아쓰기도 틀린다 — whisper 는 더듬은 소리를 매끄럽게 지우고 고유명사를 틀린다).
"""
import difflib
import json
import re
import sys


def norm(s):
    return re.sub(r"[\s.,!?~·…\"'“”‘’()\-]", "", s)


def main():
    edit, words, out = sys.argv[1:4]
    caps = sorted((i for i in json.load(open(edit, encoding="utf-8"))["items"] if i["track"] == "C1"), key=lambda i: i["t0"])
    segs = json.load(open(words, encoding="utf-8"))
    ws = [w for s in segs for w in s["words"]]
    rows = []
    for c in caps:
        a, b = c["t0"], c["t1"]
        inside = [w for w in ws if (min(b, w["t1"]) - max(a, w["t0"])) > 0.5 * max(0.01, w["t1"] - w["t0"])]
        heard = " ".join(w["w"] for w in inside)
        r = difflib.SequenceMatcher(None, norm(c.get("text", "")), norm(heard)).ratio() if inside else 0.0
        rows.append({
            "t0": round(a, 3), "t1": round(b, 3), "text": c.get("text", ""), "heard": heard, "ratio": round(r, 3),
            "start_off": round(inside[0]["t0"] - a, 3) if inside else None,
            "end_off": round(b - inside[-1]["t1"], 3) if inside else None,
            "minp": round(min(w["p"] for w in inside), 3) if inside else None,
        })
    json.dump(rows, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    low = [r for r in rows if r["ratio"] < 0.9]
    print(f"자막 {len(rows)}줄 · 일치율 0.9 미만 {len(low)}줄 · 받아쓰기 없음 {sum(1 for r in rows if not r['heard'])}줄")


if __name__ == "__main__":
    main()
