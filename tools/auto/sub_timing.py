# -*- coding: utf-8 -*-
r"""자막 타이밍 검수 — 자막 글을 소리에 강제 정렬(MMS_FA, ko_align.py)해 줄마다 말 시작·끝과 비교한다 (10-13 규칙 3).

    python tools/auto/sub_timing.py <captions.json|edit.json> <소리16k.wav> <출력.json>

captions.json = {"captions":[{t0,t1,text},…]} 또는 read_lecture_edit 결과(edit.json, C1 트랙).
whisper 단어 시각은 0.2초가량 이르게 찍혀(10-13 파트너센터 실측: 자막−whisper 중앙값 +0.215초, 강제 정렬 대비 −0.05초)
기준으로 쓰지 않는다.

판정(줄마다)
- 시작: lag = 자막 시작 − 말 시작. lag > +0.05초 → «늦음», lag < −0.6초 → «이름»
- 끝: 자막 끝 − 말 끝 < −0.05초 → «먼저 꺼짐»(말이 남았는데 자막이 사라짐)
- 점수: 정렬 점수 평균 < 0.3 → «글 확인»(자막 글과 들린 말이 다를 수 있다 — 맞춤법·빠진 말 후보)
"""
import json
import sys

import soundfile as sf

sys.path.insert(0, ".")
from tools.auto.ko_align import Aligner  # noqa: E402

CHUNK = 25.0


def load_caps(p):
    d = json.load(open(p, encoding="utf-8"))
    if "captions" in d:
        return d["captions"]
    return [dict(t0=i["t0"], t1=i["t1"], text=i.get("text", "")) for i in sorted(
        (i for i in d["items"] if i["track"] == "C1"), key=lambda i: i["t0"])]


def main():
    src, wav, out = sys.argv[1:4]
    caps = load_caps(src)
    x, sr = sf.read(wav, dtype="float32")
    al = Aligner()
    rows = [dict(i=i, t0=round(c["t0"], 3), t1=round(c["t1"], 3), text=c["text"]) for i, c in enumerate(caps)]
    i = 0
    while i < len(caps):
        j = i
        while j + 1 < len(caps) and caps[j + 1]["t1"] - caps[i]["t0"] < CHUNK:
            j += 1
        a = max(0.0, caps[i]["t0"] - 0.6); b = min(len(x) / sr, caps[j]["t1"] + 0.6)
        words, owner = [], []
        for k in range(i, j + 1):
            for w in caps[k]["text"].split():
                words.append(w); owner.append(k)
        try:
            res = al.align(x[int(a * sr):int(b * sr)], words)
        except Exception as e:                       # 글이 소리보다 길면 정렬 실패 → 줄마다 표시
            for k in range(i, j + 1):
                rows[k]["error"] = str(e)[:80]
            i = j + 1
            continue
        for k in range(i, j + 1):
            rs = [r for r, o in zip(res, owner) if o == k and r is not None]
            if not rs:
                continue
            on, off = a + rs[0][0], a + rs[-1][1]
            sc = sum(r[2] for r in rs) / len(rs)
            r = rows[k]
            r.update(onset=round(on, 3), offset=round(off, 3), score=round(sc, 3),
                     lag=round(caps[k]["t0"] - on, 3), tail=round(caps[k]["t1"] - off, 3))
            v = []
            if r["lag"] > 0.05:
                v.append("늦음")
            if r["lag"] < -0.6:
                v.append("이름")
            if r["tail"] < -0.05:
                v.append("먼저 꺼짐")
            if sc < 0.3:
                v.append("글 확인")
            r["verdict"] = v or ["맞음"]
        i = j + 1
    json.dump(rows, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    from collections import Counter
    c = Counter(v for r in rows for v in r.get("verdict", ["판단불가"]))
    print(dict(c))


if __name__ == "__main__":
    main()
