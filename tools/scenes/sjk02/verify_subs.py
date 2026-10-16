# -*- coding: utf-8 -*-
"""성제관02 자막 검수(지시서 «±0.1초 · 글 일치 100%») — 완성본 소리(목소리+BGM+효과음)에 자막 글을 다시 강제 정렬해
자막 srt 시각과 비교한다. 시작 차 = |srt 시작 − 다시 잰 첫 음절|, 끝 차 = |srt 끝 − (다시 잰 끝 +0.15, 다음 시작 −0.02 넘지 않게)|.
    py -3.11 tools/scenes/sjk02/verify_subs.py <완성본.mp4|wav> <자막.srt> <보고.md>
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


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
    wav16 = ROOT / "_tmp/sjk02/final/verify16k.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", media, "-vn", "-ac", "1", "-ar", "16000", str(wav16)], check=True)
    out = ROOT / "_tmp/sjk02/final/verify_lines.json"
    subprocess.run([sys.executable, str(ROOT / "tools/scenes/sjk02/align_lines.py"), "--wav", str(wav16), "--out", str(out)], check=True,
                   env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
    re_ = json.load(open(out, encoding="utf-8"))
    # 2편: 1편 refine_onsets(앞 줄 꼬리를 목소리 시작으로 잘못 잡음)를 쓰지 않고, 만들 때와 같은 «쉼 경계» 규칙(check_energy)을
    # 완성본 소리(BGM·효과음 섞임)에서 새로 잰다 — 쉼 뒤 줄 시작·쉼 앞 줄 끝은 완성본 목소리 에너지, 이어진 줄은 완성본에 다시 돌린 강제 정렬.
    sys.path.insert(0, str(ROOT / "tools/scenes/sjk02"))
    import numpy as np
    import soundfile as sf
    from check_energy import pauses
    from assemble import cap_text
    xx, sr = sf.read(str(wav16), dtype="float32")
    P, _ = pauses(xx, sr)
    st = np.array([b for _, b in P]); en = np.array([a for a, _ in P])
    for r in re_:
        j = int(np.argmin(abs(st - r["t0"])))
        if abs(st[j] - r["t0"]) <= 0.35:
            r["t0"] = float(st[j])
        j = int(np.argmin(abs(en - r["t1"])))
        if abs(en[j] - r["t1"]) <= 0.35 and en[j] > r["t0"] + 0.2:
            r["t1"] = float(en[j])
    sub = read_srt(srtp)
    assert len(re_) == len(sub), f"줄 수 다름 {len(re_)} vs {len(sub)}"
    rows, bad, text_bad = [], 0, 0
    for k, (r, s) in enumerate(zip(re_, sub)):
        nxt = re_[k + 1]["t0"] if k + 1 < len(re_) else r["t1"] + 1
        end = min(r["t1"] + 0.15, nxt - 0.02)
        ds, de = s["t0"] - r["t0"], s["t1"] - end
        norm = lambda t: "".join(ch for ch in t if ch.isalnum() or ch in "%○")
        tok = norm(cap_text(r["text"])) == norm(s["text"])
        ok = abs(ds) <= 0.1 + 1e-6 and abs(de) <= 0.1 + 1e-6 and tok
        bad += not ok; text_bad += not tok
        rows.append((k + 1, s["text"], round(ds, 3), round(de, 3), "OK" if ok else "넘음"))
    n = len(rows)
    lines = [f"# 성제관02 자막 검수 — 완성본 소리에 다시 강제 정렬", "",
             f"- 줄 {n} · ±0.1초 안 {n - bad}줄 ({(n - bad) / n * 100:.2f}%) · 글 일치 {n - text_bad}/{n}",
             f"- 시작 차 최대 {max(abs(r[2]) for r in rows):.3f}초 · 끝 차 최대 {max(abs(r[3]) for r in rows):.3f}초", "",
             "| # | 자막 | 시작 차(초) | 끝 차(초) | 판정 |", "|---|---|---|---|---|"]
    lines += [f"| {a} | {b} | {c:+.3f} | {d:+.3f} | {e} |" for a, b, c, d, e in rows]
    Path(rep).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(lines[2]); print(lines[3])


if __name__ == "__main__":
    main()
