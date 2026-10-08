# -*- coding: utf-8 -*-
r"""무음컷 2단계 — 살린 구간 «안»의 쉼을 사장님 기준으로 줄인다 (2026-10-02 빡이사DB 실측).

    python pause_compress.py <cut_plan.json> <16k.wav> <words.json> <출력 plan.json> [--검증 <내 컷 시퀀스.json> <사장님 시퀀스.json> <원본 끝초>]
  기본 = 안전판 compress_safe2(아래). 1차 compress 는 단어를 깎아 폐기 — 기록용으로만 남긴다.

왜: VAD 무음컷(여유 0.06)은 말 사이 0.25~0.6초 쉼을 «말 안»으로 보고 남긴다. 사장님은 그 쉼을 손으로 70~100% 줄이셨다
(빡이사DB 0~41분: 0.25~0.35초 쉼 70% · 0.35~0.5초 90% · 0.5초+ 100% 줄임, 남긴 쉼 0.12~0.17초). 경계 여유(말 끝 뒤 0.08 ·
말 시작 앞 0.12)는 이미 내 컷과 같았다 → 고칠 곳은 «안쪽 쉼»뿐.
쉼 찾기: 단어 시각이 아니라 소리 크기(10ms, 주변 10% 바닥 +8dB 아래가 0.25초 이상). 받아쓰기 단어 끝은 뒤 무음까지 늘어나 쉼을 못 잡는다.
줄이는 법: 쉼 길이 L → 남길 쉼 0.12(L<0.35) · 0.15(0.35~0.5) · 0.18(0.5+), 말 끝 쪽 45% · 다음 말 쪽 55%.
단어 없는 살린 조각(숨·입소리·추임새 추정)은 자르지 않고 «확인» 마커로 남긴다 — 사장님이 42%만 지우셨다.
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import cut_diff_study as C  # noqa: E402

OFF_DB, MIN_PAUSE = 8, 0.25


def target(L):
    return 0.12 if L < 0.35 else 0.15 if L < 0.5 else 0.18


def pauses(e, a, b):
    """살린 구간 [a,b] 안의 쉼 (앞뒤 0.05초 안쪽만)."""
    i0, i1 = int(a * 100), int(b * 100)
    fl = C.floor_at(e, (a + b) / 2, 5)
    low = e[i0:i1] < fl + OFF_DB
    out, j = [], 0
    while j < len(low):
        if low[j]:
            k = j
            while k < len(low) and low[k]:
                k += 1
            ta, tb = a + j / 100, a + k / 100
            if tb - ta >= MIN_PAUSE and ta > a + 0.05 and tb < b - 0.05:
                out.append((ta, tb))
            j = k
        else:
            j += 1
    return out


def compress(keep, e):
    new, n = [], 0
    for a, b in keep:
        cur = a
        for ta, tb in pauses(e, a, b):
            t = target(tb - ta)
            new.append((cur, ta + 0.45 * t))
            cur = tb - 0.55 * t
            n += 1
        new.append((cur, b))
    return [(x, y) for x, y in new if y - x > 0.02], n


def evaluate(K2, mine, boss, s_end, words_json, e):
    O, U = C.kept(mine, s_end), C.kept(boss, s_end)
    K2 = [(a, min(b, s_end)) for a, b in K2 if a < s_end]
    W = [w for s in json.loads(Path(words_json).read_text(encoding="utf-8")) for w in s["words"] if w["t0"] < s_end]
    R_boss = C.subtract(O, U)
    sil_boss = [(a, b) for a, b in R_boss if not C.words_in(W, a, b)]
    R2 = C.subtract(O, K2)

    def inter(A, B):
        return sum(max(0, min(b, y) - max(a, x)) for a, b in A for x, y in B)
    hit = inter(R2, sil_boss)
    over = sum(b - a for a, b in C.subtract(R2, R_boss))       # 내가 지웠는데 사장님은 살린 것
    print(f"사장님 무음 컷 {sum(b - a for a, b in sil_boss):.1f}초 중 새 컷이 같이 지운 것 {hit:.1f}초 ({hit / max(1e-9, sum(b - a for a, b in sil_boss)):.0%})")
    print(f"새 컷이 더 지운 것 {sum(b - a for a, b in R2):.1f}초 중 사장님은 살린 것(과하게 자른 것) {over:.1f}초")
    cut_words = [w for w in W if any(min(w["t1"], y) - max(w["t0"], x) > 0.3 * (w["t1"] - w["t0"]) for x, y in R2)]
    print(f"새 컷이 단어를 30% 넘게 깎은 곳 {len(cut_words)}개: " + " · ".join(f"{w['t0']:.1f}«{w['w']}»" for w in cut_words[:12]))


# ── 2차(안전판): 단어 금지 구역 + 단어 사이 틈에서만 ─────────────────────────
GUARD_TAIL, GUARD_HEAD = 0.06, 0.06       # 잔음 끝 뒤 · 소리 시작 앞 최소 남김(사장님 경계 여유 하위 25% = 0.04~0.05)


def word_edges(words, e):
    """받아쓰기 단어마다 실제 소리 시작·끝(잔음 포함)을 다시 잡는다. 단어 끝은 뒤 무음까지 늘어나 있어 «당겨»야 한다."""
    out = []
    for w in words:
        fl = C.floor_at(e, w["t0"])
        thr = fl + 8
        i0, i1 = max(0, int((w["t0"] - 0.15) * 100)), min(len(e), int((w["t1"] + 0.30) * 100))
        loud = np.where(e[i0:i1] > thr)[0]
        if len(loud):
            out.append((i0 + loud[0]) / 100), out.append((i0 + loud[-1] + 1) / 100)
        else:
            out.append(w["t0"]), out.append(w["t1"])
    return list(zip(out[0::2], out[1::2]))


def compress_safe(keep, e, words):
    """살린 구간 안에서, 이웃 단어 사이 틈(소리 끝 → 다음 소리 시작)이 0.25초 넘고 그 틈이 내내 조용할 때만 줄인다.
    단어 소리 구간 + 앞뒤 GUARD 는 절대 안 자른다."""
    E = sorted(word_edges(words, e))
    new, n = [], 0
    for a, b in keep:
        ws = [(x, y) for x, y in E if x >= a - 0.02 and y <= b + 0.02]
        cur = a
        for (x0, x1), (y0, y1) in zip(ws, ws[1:]):
            gap = y0 - x1
            if gap < MIN_PAUSE:
                continue
            fl = C.floor_at(e, (x1 + y0) / 2, 3)
            seg = e[int(x1 * 100):int(y0 * 100)]
            if len(seg) == 0 or np.mean(seg < fl + OFF_DB) < 0.9:      # 틈에 소리가 섞여 있으면(작은 말·숨) 손대지 않는다
                continue
            t = target(gap)
            cut0 = x1 + max(GUARD_TAIL, 0.45 * t)
            cut1 = y0 - max(GUARD_HEAD, 0.55 * t)
            if cut1 - cut0 < 0.05:
                continue
            new.append((cur, cut0))
            cur = cut1
            n += 1
        new.append((cur, b))
    return [(x, y) for x, y in new if y - x > 0.02], n


def evaluate_safe(K2, mine, boss, s_end, words, e):
    O, U = C.kept(mine, s_end), C.kept(boss, s_end)
    K2 = [(a, min(b, s_end)) for a, b in K2 if a < s_end]
    R_boss = C.subtract(O, U)
    E = word_edges([w for w in words if w["t0"] < s_end], e)
    sil_boss = [(a, b) for a, b in R_boss if not any(min(b, y) - max(a, x) > 0.5 * (y - x) for x, y in E)]
    R2 = C.subtract(O, K2)

    def inter(A, B):
        return sum(max(0, min(b, y) - max(a, x)) for a, b in A for x, y in B)
    hit = inter(R2, sil_boss)
    over = C.subtract(R2, R_boss)
    bite = [(x, y) for x, y in E if any(min(y, b) - max(x, a) > 0.01 for a, b in R2)]
    print(f"사장님 무음 컷 {sum(b - a for a, b in sil_boss):.1f}초 중 같이 지운 것 {hit:.1f}초 ({hit / max(1e-9, sum(b - a for a, b in sil_boss)):.0%})")
    print(f"새 컷이 지운 {sum(b - a for a, b in R2):.1f}초 중 사장님은 살린 것 {sum(b - a for a, b in over):.1f}초 ({len(over)}곳)")
    print(f"단어 소리 구간을 건드린 곳 {len(bite)}개")
    return hit, over, bite


# ── 2차-b(안전판 채택): 소리 쉼 + 거부 조건 ───────────────────────────────
SAFE_DB = 6                                  # 자르는 자리 안 소리는 바닥 +6dB 아래여야 한다(끝음 약하게 흐리는 «~요»·숨 보호)


def compress_safe2(keep, e, words):
    """쉼 찾기는 소리(바닥 +8dB 아래 0.25초+), 거부: ① 쉼 안에서 받아쓰기 단어가 «시작»하면(작게 말한 말) ② 실제 자를 자리에
    바닥 +6dB 넘는 프레임이 있으면 ③ 앞뒤 남김이 GUARD(0.06초)보다 작아지면. 받아쓰기 «끝» 시각은 무음까지 늘어나 믿지 않는다."""
    starts = np.array(sorted(w["t0"] for w in words))
    new, n, veto = [], 0, {"단어 시작": 0, "소리 섞임": 0}
    for a, b in keep:
        cur = a
        for ta, tb in pauses(e, a, b):
            if ((starts > ta + 0.03) & (starts < tb - 0.03)).any():
                veto["단어 시작"] += 1
                continue
            t = target(tb - ta)
            cut0, cut1 = ta + max(GUARD_TAIL, 0.45 * t), tb - max(GUARD_HEAD, 0.55 * t)
            if cut1 - cut0 < 0.05:
                continue
            fl = C.floor_at(e, (ta + tb) / 2, 5)
            if (e[int(cut0 * 100):int(cut1 * 100)] > fl + SAFE_DB).any():
                veto["소리 섞임"] += 1
                continue
            new.append((cur, cut0))
            cur = cut1
            n += 1
        new.append((cur, b))
    return [(x, y) for x, y in new if y - x > 0.02], n, veto


def damage(R2, e, words):
    """새로 지운 자리의 손상 검사 — 말소리 크기(바닥 +10dB) 프레임 · 받아쓰기 단어 시작이 들어 있으면 손상."""
    starts = [w["t0"] for w in words]
    bad = []
    for a, b in R2:
        fl = C.floor_at(e, (a + b) / 2, 5)
        loud = int((e[int(a * 100):int(b * 100)] > fl + 10).sum())
        st = [x for x in starts if a < x < b]
        if loud or st:
            bad.append((round(a, 2), round(b, 2), loud, len(st)))
    return bad


def main():
    """python pause_compress.py <cut_plan.json> <16k.wav> <words.json> <출력 plan.json> [--검증 <내 컷 시퀀스.json> <사장님 시퀀스.json> <원본 끝초>]
    기본 = 안전판(compress_safe2). 1차 compress 는 단어를 깎아 폐기(10-02)."""
    plan, wav, wj, out = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4])
    P = json.loads(plan.read_text(encoding="utf-8"))
    e = C.energy(wav)
    W = [w for s_ in json.loads(wj.read_text(encoding="utf-8")) for w in s_["words"]]
    O = [tuple(x) for x in P["keep"]]
    K2, n, veto = compress_safe2(O, e, W)
    bad = damage(C.subtract(O, K2), e, W)
    if bad:
        raise SystemExit(f"손상 후보 {len(bad)}곳 — 저장하지 않는다: {bad[:5]}")
    P2 = dict(P, keep=[list(x) for x in K2], pause_compress=dict(판="안전판", off_db=OFF_DB, safe_db=SAFE_DB, min_pause=MIN_PAUSE, n=n, 거부=veto))
    out.write_text(json.dumps(P2, ensure_ascii=False), encoding="utf-8")
    before, after = sum(b - a for a, b in O), sum(b - a for a, b in K2)
    print(f"쉼 줄임 {n}곳(거부 {veto}) · {before / 60:.1f}분 → {after / 60:.1f}분 (−{before - after:.0f}초) · 손상 0 → {out}")
    if "--검증" in sys.argv:
        i = sys.argv.index("--검증")
        evaluate_safe(K2, sys.argv[i + 1], sys.argv[i + 2], float(sys.argv[i + 3]), W, e)


if __name__ == "__main__":
    main()
