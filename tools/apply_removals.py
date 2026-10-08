"""무음 컷 계획에서 버벅임·중복 구간을 더 빼 «새» 컷 계획을 만든다. 원래 계획은 건드리지 않는다.

    python apply_removals.py <cut_plan.json> <버벅임_후보.json> <출력 plan.json> [번호,번호,...]

번호를 안 주면 후보 전부를 뺀다.
  · 뺀 자리마다 타임라인 마커(`markers`)를 남긴다 — XML 마커·미리보기 자막에 쓴다
  · 빼고 남은 조각이 0.1초 미만이면 버린다 (ADR 0007: 0.1초 미만 컷은 효과 없이 컷만 늘린다)
후보의 a·b 는 `disfluency_preview.py` 가 저음량 지점으로 스냅해 둔 값이다.
"""

import json
import sys
from pathlib import Path

MIN_PIECE = 0.1


def subtract(keep, cuts):
    out = []
    for s, e in keep:
        pieces = [(s, e)]
        for a, b in cuts:
            nxt = []
            for ps, pe in pieces:
                if b <= ps or a >= pe:
                    nxt.append((ps, pe))
                    continue
                if a > ps:
                    nxt.append((ps, a))
                if b < pe:
                    nxt.append((b, pe))
            pieces = nxt
        out += [(ps, pe) for ps, pe in pieces if pe - ps >= MIN_PIECE]
    return out


def to_timeline(t, keep):
    acc = 0.0
    for s, e in keep:
        if t < s:
            return acc
        if t <= e:
            return acc + (t - s)
        acc += e - s
    return acc


def main():
    plan_p, cand_p, out_p = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    plan = json.loads(plan_p.read_text(encoding="utf-8"))
    cands = json.loads(cand_p.read_text(encoding="utf-8"))
    if len(sys.argv) > 4:
        pick = {int(x) for x in sys.argv[4].split(",")}
        cands = [c for c in cands if c["no"] in pick]

    cuts = [(c["a"], c["b"]) for c in cands]
    keep = subtract(plan["keep"], cuts)
    markers = []
    for c in cands:
        t = to_timeline(c["b"], keep)
        markers.append({"t": round(t, 3), "no": c["no"], "label": c["label"], "text": c["text"]})

    new = dict(plan)
    new["keep"] = [[s, e] for s, e in keep]
    new["markers"] = markers
    new["removed_disfluency"] = [{"no": c["no"], "a": c["a"], "b": c["b"],
                                  "label": c["label"], "text": c["text"]} for c in cands]
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out_p.write_text(json.dumps(new, ensure_ascii=False, indent=1), encoding="utf-8")

    before = sum(e - s for s, e in plan["keep"])
    after = sum(e - s for s, e in keep)
    print(f"무음 컷만 {before:.2f}초 → 버벅임 제거 {after:.2f}초 (−{before - after:.2f}초, {len(cands)}곳)")
    for m in markers:
        mm, ss = divmod(m["t"], 60)
        print(f"  {m['no']:2d}  {int(mm)}:{ss:05.2f}  {m['label']}  {m['text']}")
    print(f"저장: {out_p}")


if __name__ == "__main__":
    sys.exit(main())
