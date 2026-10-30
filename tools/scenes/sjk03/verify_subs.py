# -*- coding: utf-8 -*-
"""성제관03 자막 검수(하드 규칙 13 ②) — 완성본 소리(목소리+BGM+효과음)에 자막 글을 다시 강제 정렬(묶음 3줄)해 srt 시작과 비교하고,
srt 글이 녹음 원고(lines.json)와 같은지 본다. 3편 경계는 boundary.py(목소리 단독 소리 골)로 정했으므로, 섞인 소리에서는 강제 정렬 시작만 다시 잰다.
1단계에서 손으로 하나씩 확인한 줄(make_docs.py MANUAL · 30_결과 «7줄»)은 다시 정렬이 어긋나도 따로 표시한다.
    py -3.11 tools/scenes/sjk03/verify_subs.py <완성본.mp4|wav> <자막.srt> <보고.md>
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_docs import cap_text  # noqa: E402

CHECKED = {159, 198, 225, 238, 275, 310, 369}   # 1단계: 다시 정렬과 0.1초 넘게 달라 에너지·받아쓰기로 하나씩 확인한 줄(1부터 — 30_결과 «7줄» 번호는 0부터)


def read_srt(p):
    out = []
    for blk in re.split(r"\n\s*\n", Path(p).read_text(encoding="utf-8").strip()):
        ln = blk.strip().splitlines()
        if len(ln) < 3:
            continue
        a, b = ln[1].split(" --> ")
        f = lambda s: int(s[:2]) * 3600 + int(s[3:5]) * 60 + int(s[6:8]) + int(s[9:12]) / 1000
        out.append({"t0": f(a), "t1": f(b), "text": " ".join(ln[2:])})
    return out


def main():
    media, srtp, rep = sys.argv[1:4]
    wav16 = ROOT / "_tmp/sjk03/final/verify16k.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", media, "-vn", "-ac", "1", "-ar", "16000", str(wav16)], check=True)
    out = ROOT / "_tmp/sjk03/final/verify_lines.json"
    subprocess.run([sys.executable, str(ROOT / "tools/scenes/sjk03/align_lines.py"), "--wav", str(wav16), "--out", str(out), "--group", "3"],
                   check=True, env={**os.environ, "PYTHONIOENCODING": "utf-8"}, stdout=subprocess.DEVNULL)
    re_ = json.load(open(out, encoding="utf-8"))
    src = json.load(open(ROOT / "_tmp/sjk03/audio/lines.json", encoding="utf-8"))
    sub = read_srt(srtp)
    assert len(re_) == len(sub) == len(src), f"줄 수 다름 {len(re_)} {len(sub)} {len(src)}"
    norm = lambda t: "".join(ch for ch in t if ch.isalnum() or ch in "%○")
    rows, bad, text_bad, overlap = [], 0, 0, 0
    for k, (r, s, o) in enumerate(zip(re_, sub, src)):
        ds = s["t0"] - r["t0"]
        tok = norm(cap_text(o["text"])) == norm(s["text"])
        same_src = abs(s["t0"] - o["sub_t0"]) < 0.002 and abs(s["t1"] - o["sub_t1"]) < 0.002
        ok = abs(ds) <= 0.1 + 1e-6 and tok and same_src
        note = "OK" if ok else ("1단계 하나씩 확인한 줄" if (k + 1) in CHECKED and tok and same_src else "넘음")
        if k + 1 < len(sub) and s["t1"] > sub[k + 1]["t0"]:
            overlap += 1; note += " · 겹침"
        bad += note != "OK"; text_bad += not tok
        rows.append((k + 1, s["text"], round(ds, 3), note))
    n = len(rows)
    okn = sum(r[3] == "OK" for r in rows); chk = sum(r[3].startswith("1단계") for r in rows)
    lines = ["# 성제관03 자막 검수 — 완성본 소리에 다시 강제 정렬(묶음 3줄)", "",
             f"- 줄 {n} · 시작 ±0.1초 안 {okn}줄 ({okn / n * 100:.2f}%) + 1단계에서 하나씩 확인한 줄 {chk} · 그 밖 {n - okn - chk}",
             f"- 글 일치(녹음 원고 ↔ srt) {n - text_bad}/{n} · 겹침 {overlap} · srt 시각 = lines.json sub_t0/sub_t1 그대로",
             f"- 시작 차 최대 {max(abs(r[2]) for r in rows):.3f}초", "",
             "| # | 자막 | 시작 차(초) | 판정 |", "|---|---|---|---|"]
    lines += [f"| {a} | {b} | {c:+.3f} | {d} |" for a, b, c, d in rows]
    Path(rep).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(lines[2]); print(lines[3]); print(lines[4])


if __name__ == "__main__":
    main()
