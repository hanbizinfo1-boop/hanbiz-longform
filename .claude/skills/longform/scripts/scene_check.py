# -*- coding: utf-8 -*-
"""연출표 반복 검사 — «같은 배경·같은 분위기·비슷한 장면 반복 = AI 자동화 느낌»(사장님 10-14).

    python .claude/skills/longform/scripts/scene_check.py <20_연출표.md> [--prev <앞 편 20_연출표.md>]

연출표 = 마크다운 표, 머리줄에 «배경 · 매체 · 구도» 칸이 있어야 한다(카메라 칸은 있으면 같이 본다).
- ERROR: 연속 두 장면이 배경·매체·구도 중 둘 이상 같다
- ERROR: 같은 장면 틀(배경+매체+구도)이 한 편에 3번 이상
- ERROR: 매체 종류가 5가지 미만
- WARN : 같은 카메라가 3장면 연속
--prev(앞 편과 비교 — 10-16 «속도감·퀄리티는 1편처럼, 분위기·색감·도구·구도는 다르게»):
- ERROR: 배경이 앞 편 장면 배경과 글자 그대로 같다
- ERROR: 장면 틀(배경+매체+구도)이 앞 편에 있던 것과 같다
- ERROR: «1편과 다른 점» 칸이 있는데 비어 있다
- WARN : 매체+구도 짝이 앞 편에도 있던 장면이 전체의 30% 넘음
매체는 괄호·«+» 앞의 큰 갈래로 묶어 센다(«실제 자료(화면 녹화)» → «실제 자료»).
종료 코드: ERROR 있으면 1.
"""

import re
import sys
from collections import Counter


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def main_kind(m):
    return re.split(r"[(+]", m)[0].strip()


def read_rows(path):
    rows, head = [], None
    for line in open(path, encoding="utf-8"):
        if not line.lstrip().startswith("|"):
            continue
        c = cells(line)
        if head is None:
            head = c
            continue
        if set("".join(c)) <= set("-: "):
            continue
        rows.append(dict(zip(head, c)))
    return head, rows


def main():
    args = sys.argv[1:]
    prev = None
    if "--prev" in args:
        i = args.index("--prev")
        prev = args[i + 1]
        del args[i:i + 2]
    if not args:
        print(__doc__)
        sys.exit(2)
    head, rows = read_rows(args[0])
    need = ["배경", "매체", "구도"]
    if not head or any(k not in head for k in need):
        print("연출표 머리줄에 배경 · 매체 · 구도 칸이 없다")
        sys.exit(2)
    errs, warns = [], []
    for a, b in zip(rows, rows[1:]):
        same = [k for k in need if (main_kind(a[k]) if k == "매체" else a[k]) == (main_kind(b[k]) if k == "매체" else b[k])]
        if len(same) >= 2:
            errs.append(f"{a.get('#', '?')}→{b.get('#', '?')} 연속 장면이 {'·'.join(same)} 같음")
    combo = Counter((r["배경"], main_kind(r["매체"]), r["구도"]) for r in rows)
    for k, n in combo.items():
        if n >= 3:
            errs.append(f"같은 장면 틀 {n}번: {' / '.join(k)}")
    kinds = Counter(main_kind(r["매체"]) for r in rows)
    if len(kinds) < 5:
        errs.append(f"매체 {len(kinds)}종 — 5종 이상이어야")
    if "카메라" in head:
        for x, y, z in zip(rows, rows[1:], rows[2:]):
            if x["카메라"] == y["카메라"] == z["카메라"]:
                warns.append(f"{x.get('#')}~{z.get('#')} 카메라 «{x['카메라']}» 3연속")
    if prev:
        _, prows = read_rows(prev)
        pbg = {r.get("배경", "") for r in prows}
        ptri = {(r.get("배경", ""), main_kind(r.get("매체", "")), r.get("구도", "")) for r in prows}
        ppair = {(main_kind(r.get("매체", "")), r.get("구도", "")) for r in prows}
        for r in rows:
            n = r.get("#", "?")
            if r["배경"] in pbg:
                errs.append(f"{n} 배경 «{r['배경']}» — 앞 편과 같음")
            elif (r["배경"], main_kind(r["매체"]), r["구도"]) in ptri:
                errs.append(f"{n} 장면 틀 앞 편과 같음")
            if "1편과 다른 점" in head and not r.get("1편과 다른 점", "").strip():
                errs.append(f"{n} «1편과 다른 점» 칸 비어 있음")
        same = sum((main_kind(r["매체"]), r["구도"]) in ppair for r in rows)
        if rows and same / len(rows) > 0.3:
            warns.append(f"매체+구도 짝이 앞 편과 같은 장면 {same}/{len(rows)}({same * 100 // len(rows)}%) — 30% 아래로")
        print(f"앞 편 비교: {prev} (장면 {len(prows)}개) · 매체+구도 같은 짝 {same}/{len(rows)}")
    print(f"# 연출표 반복 검사 — 장면 {len(rows)}개")
    print("매체:", " · ".join(f"{k} {n}" for k, n in kinds.most_common()))
    print("배경 종류:", len(set(r["배경"] for r in rows)), "· 구도 종류:", len(set(r["구도"] for r in rows)))
    for w in warns:
        print("WARN", w)
    for e in errs:
        print("ERROR", e)
    if errs:
        sys.exit(1)
    print("ERROR 0 — 반복 없음")


if __name__ == "__main__":
    main()
