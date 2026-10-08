# -*- coding: utf-8 -*-
r"""보조 패널 PNG 를 사장님 확정 타임라인에 놓는다 — 인물 전체화면 구간에만.

    python side_panel_place.py <map.json> <보조패널.json> <패널 png폴더> <출력 panels_place.json>

  · 카드의 원본 시각(from/until/build) → 확정 타임라인 (map.json pieces). 잘려 나간 시각은 다음 조각 시작으로
  · 사장님이 «자료»(녹화+원형 PIP)로 두신 구간에는 놓지 않는다 — 슬라이드를 가린다
  · 패널은 첫 항목을 말할 때 뜬다(build[0]) · 항목이 쌓일 때마다 다음 단계 PNG 로 바뀐다
  · 1.5초 미만으로 잠깐 떴다 사라지는 조각은 버린다(깜빡임)
효과음: 패널 첫 등장 = 종이소리 · 항목 추가 = 띠딩2 (자료 구간을 지나 다시 뜰 때는 소리 없음)
"""

import json
import sys
from pathlib import Path

MIN_PART = 1.5


def to_tl(pieces, s):
    for t0, t1, s0, s1 in pieces:
        if s0 <= s < s1:
            return t0 + (s - s0)
        if s < s0:
            return t0            # 잘려 나간 곳 → 다음 조각 시작
    return pieces[-1][1]


def main():
    m = json.load(open(sys.argv[1], encoding="utf-8"))
    spec = json.load(open(sys.argv[2], encoding="utf-8"))
    pdir, out = Path(sys.argv[3]), Path(sys.argv[4])
    pieces = m["pieces"]
    person = [(a, b) for a, b, k in m["modes"] if k == "인물"]
    clips, dropped = [], []
    for c in spec["cards"]:
        stem = f'{c["no"]:02d}_{c["name"]}'
        builds = [to_tl(pieces, t) for t in c["build"]]
        a, b = builds[0], to_tl(pieces, c["until"])
        parts = [(max(a, x), min(b, y)) for x, y in person if min(b, y) - max(a, x) >= MIN_PART]
        if not parts:
            dropped.append(f"{stem} (인물 구간 없음)")
            continue
        for pi, (x, y) in enumerate(parts):
            for k in range(len(builds)):
                s0 = max(x, builds[k])
                s1 = min(y, builds[k + 1]) if k + 1 < len(builds) else y
                if s1 - s0 < 0.05:
                    continue
                first_shown = not any(cl["card"] == c["no"] for cl in clips)   # 이 카드가 처음 뜨는 순간
                step_sfx = s0 == builds[k] and k > 0
                clips.append({"file": f"{stem}_{k + 1}.png", "card": c["no"], "step": k + 1,
                              "t0": round(s0, 3), "t1": round(s1, 3),
                              "fade": s0 == x,                   # 패널이 새로 뜨는 클립만 페이드인
                              "sfx": "종이소리" if first_shown else "띠딩2" if step_sfx else None})
    for cl in clips:
        assert (pdir / cl["file"]).exists(), cl["file"]
    out.write_text(json.dumps(clips, ensure_ascii=False, indent=1), encoding="utf-8")
    cards = sorted({c["card"] for c in clips})
    print(f"패널 {len(cards)}장 · 클립 {len(clips)} · 화면에 떠 있는 시간 {sum(c['t1'] - c['t0'] for c in clips):.0f}초")
    if dropped:
        print("못 놓은 카드: " + ", ".join(dropped))
    print(f"저장: {out}")


if __name__ == "__main__":
    sys.exit(main())
