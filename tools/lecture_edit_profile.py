# -*- coding: utf-8 -*-
r"""`read_lecture_edit.py` 가 뽑은 JSON 을 «편집 문법» 한 장으로 요약한다.

    python lecture_edit_profile.py <전수.json>

보는 것: 트랙 구성 · 화면 모드(풀샷/PIP) · 그래픽(종류·문구·글꼴) ·
효과음(종류·음량·그래픽 부착률) · 자막(글꼴·길이·글자수·간격).

음량: 프리미어는 레벨을 선형으로 저장하고 0.17783 을 0 dB 로 둔다 (+15 dB 여유).
"""

import json
import math
import sys
from collections import Counter

ZERO_DB = 0.177827941


def db(v):
    try:
        return round(20 * math.log10(float(v) / ZERO_DB), 1)
    except (ValueError, ZeroDivisionError):
        return None


def fxnames(r):
    return [c["name"] for c in r.get("fx", [])]


def level(r):
    for c in r.get("fx", []):
        if c["name"].startswith("Internal Volume") and "레벨" in c["params"]:
            return db(c["params"]["레벨"])
    return 0.0


def main():
    data = json.load(open(sys.argv[1], encoding="utf-8"))
    items = data["items"]
    dur = max(r["t1"] for r in items)
    print(f"«{data['sequence']}»  길이 {dur:.1f}초 ({dur/60:.1f}분)\n")

    # 1. 트랙 구성
    print("== 트랙 ==")
    for tr in sorted({r["track"] for r in items}):
        rows = [r for r in items if r["track"] == tr]
        src = Counter(r.get("name") or r["type"] for r in rows).most_common(4)
        print(f"  {tr:3s} {len(rows):4d}개  " + ", ".join(f"{n}×{c}" for n, c in src))

    # 2. 화면 모드 — 카메라 클립의 크기가 작으면 PIP
    vids = [r for r in items if r["type"] == "VideoClipTrackItem" and r["track"] in ("V1", "V2")]
    scales = Counter()
    for r in vids:
        for c in r.get("fx", []):
            if c["name"] == "모션":
                scales[(r["track"], r.get("name"), str(c["params"].get("비율 조정")),
                        str(c["params"].get("위치")))] += round(r["t1"] - r["t0"], 1)
    print("\n== 영상 크기·위치 (트랙, 소스, 비율, 위치 → 누적초) ==")
    for k, v in scales.most_common(6):
        print(f"  {v:7.1f}초  {k}")

    # 3. 그래픽
    gfx = [r for r in items if r["track"] not in ("V1", "V2") and r["track"].startswith("V")
           and r["type"] == "VideoClipTrackItem"]
    print(f"\n== 그래픽 {len(gfx)}개 · 분당 {len(gfx)/(dur/60):.1f}개 ==")
    kinds = Counter()
    for g in gfx:
        f = fxnames(g)
        k = "텍스트" if "텍스트" in f else "모양" if "모양" in f else (g.get("name") or "?")
        kinds[k] += 1
    print("  종류:", dict(kinds))
    pop = sum(1 for g in gfx for c in g.get("fx", [])
              if c["name"] == "변형" and isinstance(c["params"].get("높이 비율 조정"), dict))
    print(f"  «변형» 세로비율 키프레임(팝) {pop}개")
    fonts = Counter(f for g in gfx for f in g.get("fonts", []))
    print("  글꼴:", dict(fonts))
    ds = sorted(g["t1"] - g["t0"] for g in gfx)
    if ds:
        print(f"  길이 중앙 {ds[len(ds)//2]:.2f}초 (최소 {ds[0]:.2f} · 최대 {ds[-1]:.2f})")
    for g in gfx:
        if g.get("text"):
            print(f"    {g['t0']:7.2f} {g['track']}  {' / '.join(g['text'])}")

    # 4. 효과음 — 카메라·녹화 소리가 아닌 짧은 오디오
    main_src = Counter(r.get("name") for r in items if r["track"] == "A1").most_common(1)[0][0]
    sfx = [r for r in items if r["type"] == "AudioClipTrackItem" and r["track"] != "A1"
           and r.get("name") != main_src and (r["t1"] - r["t0"]) < 8]
    g0 = [g["t0"] for g in gfx]
    on = [s for s in sfx if g0 and min(abs(s["t0"] - t) for t in g0) <= 0.1]
    gs = [g for g in gfx if sfx and min(abs(s["t0"] - g["t0"]) for s in sfx) <= 0.1]
    print(f"\n== 효과음 {len(sfx)}개 · 분당 {len(sfx)/(dur/60):.1f}개 ==")
    print(f"  그래픽에 붙은 효과음 {len(on)}/{len(sfx)}  ·  효과음 달린 그래픽 {len(gs)}/{len(gfx)}")
    for n, c in Counter(s["name"] for s in sfx).most_common():
        lv = Counter(level(s) for s in sfx if s["name"] == n)
        print(f"    {c:3d}  {n:22s} 레벨(dB) {dict(lv)}")
    vo = Counter(level(r) for r in items if r["track"] == "A1")
    print(f"  A1(말소리) 클립 레벨(dB): {dict(vo.most_common(3))}")

    # 5. 자막
    cap = [r for r in items if r["type"] == "CaptionDataClipTrackItem"]
    if cap:
        cd = sorted(r["t1"] - r["t0"] for r in cap)
        cl = sorted(len(r.get("text", "")) for r in cap)
        gaps = Counter(round(b["t0"] - a["t1"], 2) for a, b in zip(cap, cap[1:]))
        cov = sum(cd) / dur * 100
        print(f"\n== 자막 {len(cap)}장 · 화면 덮는 비율 {cov:.1f}% ==")
        print("  글꼴:", dict(Counter(f for r in cap for f in r.get("fonts", []))))
        print(f"  길이 중앙 {cd[len(cd)//2]:.2f}초 (최소 {cd[0]:.2f} · 최대 {cd[-1]:.2f})")
        print(f"  글자수 중앙 {cl[len(cl)//2]} · 95% {cl[int(len(cl)*.95)]} · 최대 {cl[-1]}")
        print(f"  간격: {dict(gaps.most_common(3))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
