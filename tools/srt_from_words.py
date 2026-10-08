# -*- coding: utf-8 -*-
r"""확정 타임라인 어절(map.json words) → 자막 SRT (간이판).

    python srt_from_words.py <map.json> <출력.srt>

규격 = 사장님 실측(ADR 0007 OUR_SHORTFORM): 1줄 · 최대 24자 · 자막 사이 간격 0.
  · 끊는 곳: 24자를 넘기 전 / 0.35초 넘는 쉼 / 문장부호(. ? !)
  · 자막 끝 = 다음 자막 시작 (간격 0). 마지막은 마지막 어절 끝 + 0.25초
  · 시각은 Whisper 어절 시각(실제보다 0.1~0.5초 이르다) — 정밀판은 자막 파이프라인(WhisperX 정렬)
UTF-8 BOM + CRLF (사장님 자막 파일 형식)
"""

import json
import sys
from pathlib import Path

MAXC, GAP = 24, 0.35


def ts(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main():
    words = json.load(open(sys.argv[1], encoding="utf-8"))["words"]
    out = Path(sys.argv[2])
    subs, cur = [], []
    for i, w in enumerate(words):
        text = " ".join(x["w"] for x in cur + [w]).strip()
        if cur and (len(text) > MAXC or w["t"] - cur[-1]["t1"] > GAP):
            subs.append(cur)
            cur = []
        cur.append(w)
        if w["w"].rstrip().endswith((".", "?", "!")) and len(" ".join(x["w"] for x in cur)) >= 6:
            subs.append(cur)
            cur = []
    if cur:
        subs.append(cur)
    lines = []
    for k, s in enumerate(subs):
        a = s[0]["t"]
        b = subs[k + 1][0]["t"] if k + 1 < len(subs) and subs[k + 1][0]["t"] - s[-1]["t1"] < 1.0 else s[-1]["t1"] + 0.25
        txt = " ".join(x["w"] for x in s).strip().rstrip(",.")
        lines.append(f"{k + 1}\r\n{ts(a)} --> {ts(b)}\r\n{txt}\r\n")
    out.write_text("\r\n".join(lines), encoding="utf-8-sig", newline="")
    print(f"자막 {len(subs)}장 · 저장: {out}")


if __name__ == "__main__":
    sys.exit(main())
