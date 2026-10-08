# -*- coding: utf-8 -*-
r"""광고영상 규칙 점검기 — 길라잡이/제작규칙-길라잡이.md 의 «납품 전 점검표»를 기계로 확인한다.

사장님 2026-09-28: «규칙 누락 현상 심함 → 길라잡이 만들 것», «점검기 만들어서 체크 루틴 넣어».
렌더 도구(rf3_render 등)가 렌더 전에 check_plan(), 소리 섞은 뒤 check_sfx() 를 부르고 report() 로 남긴다.
ERROR 가 하나라도 있으면 렌더 도구는 멈춘다(`--무시` 로만 통과).

화면 목록(shots) 한 칸 = dict(
    t0, t1,            초
    seg,               대본 구간 번호
    src,               소스 파일 경로(문자열) — 같은 파일이면 같은 소스
    kind,              "video" | "image" | "doc"(PDF 장표) | "black" | "grad" | "speed"
    tr,                들어올 때 전환 종류 — "cut" | "slide" | "fly" | "punch" | "move" | "push" …
    label=None,        화면에 보이는 타입명(예 "84A") — 타입을 말하는 줄이면 필수
    props=[],          얹은 소품 종류(prop/confetti/coins/x/stamp/big …)
)
직접 실행: python rule_check.py <work 폴더의 점검용 plan.json>
"""
import json
import re
import sys
from pathlib import Path

GUIDE = ".claude/skills/longform/references/checklist.md"
IMG_MIN, ANY_MIN, SCENE_MAX = 2.0, 1.0, 3.0
SFX_GAP = 2.5
SFX_REPEAT_MIN = 3.0   # 5-2b 같은 파일이 이 초 안에 다시 나오면 «짧은 주기»로 친다
SFX_ALT_MAX = 3        # 번갈아 쓰기는 짧은 주기 사슬에서 같은 파일 3번까지 허용 (사장님 10-02 «최대 3번까지는 번갈아사용가능»)
BANNED_BG = {"black": "까만 화면", "grad": "그라데이션 카드", "speed": "집중선 검정 화면"}
BANNED_OV = {"prop": "이모티콘 소품", "confetti": "꽃가루", "coins": "금화", "x": "X 표시", "stamp": "도장", "site": "SITE·체크 표시",
             "big": "중복 자막(위에 큰 글자)", "title": "제목 띠 글자"}
TYPE_RE = re.compile(r"(\d{2,3}\s*타입|\b\d{2,3}[A-F]\b|평면|대형\s*평수|국평)")

# 모형(미니어처) 소스 — 사장님이 지정하지 않으면 쓰지 않는다 (규칙 1-2)
MODEL_DRONE = set(range(0, 7)) | set(range(232, 250))
MODEL_FILES = {"1-4.mp4", "1-5.mp4", "1-7.mp4", "1-11.mp4", "1-12.mp4"}


def is_model(src):
    p = Path(str(src))
    if p.name in MODEL_FILES:
        return True
    m = re.match(r"DJI_\d+_(\d{4})_D", p.stem)
    return bool(m) and int(m.group(1)) in _DJI_MODEL


_DJI_MODEL = set()   # DJI 파일 번호 → 드론 번호 매핑은 도구가 register_drone() 으로 넣는다


def register_drone(meta):
    """v5_render.META {드론 번호: 파일명} 를 받아 모형 드론 파일을 표시한다."""
    for i, f in meta.items():
        if i in MODEL_DRONE:
            m = re.match(r"DJI_\d+_(\d{4})_D", Path(f).stem)
            if m:
                _DJI_MODEL.add(int(m.group(1)))


def check_plan(shots, segs_text=(), model_ok=(), ref_lines=None):
    """화면 목록 점검 → [(수준, 규칙, 메시지)]."""
    out = []
    E = lambda r, m: out.append(("ERROR", r, m))   # noqa: E731
    Wn = lambda r, m: out.append(("WARN", r, m))   # noqa: E731
    at = lambda s: f"{s['t0']:5.2f}~{s['t1']:5.2f}s"  # noqa: E731
    # 1-1 같은 소스 두 번
    seen = {}
    for s in shots:
        if s["kind"] in ("video", "image", "doc"):
            seen.setdefault(str(s["src"]), []).append(s)
    for src, ss in seen.items():
        if len(ss) > 1:
            where = ", ".join(at(s) for s in ss)
            # 같은 장표 안에서 이어 옮겨 가는 샷(tr=move)은 한 번으로 본다
            real = [s for s in ss if not s.get("cont")]
            if len(real) > 1:
                E("1-1 같은 소스 중복", f"{Path(src).name} 가 {len(real)}번 — {where}")
    # 1-2 모형
    ok = {str(x) for x in model_ok}
    for s in shots:
        if s["kind"] in ("video", "image") and is_model(s["src"]) and str(s["src"]) not in ok and Path(str(s["src"])).name not in ok:
            E("1-2 모형 소재(지정 안 됨)", f"{at(s)} {Path(str(s['src'])).name}")
    # 1-4·1-5 금지 배경·소품, 4-2 중복 자막
    for s in shots:
        if s["kind"] in BANNED_BG:
            E("1-4 금지 화면", f"{at(s)} {BANNED_BG[s['kind']]}")
        for p in s.get("props", []):
            if p in BANNED_OV:
                E("1-5/4-2 금지 소품·글자", f"{at(s)} {BANNED_OV[p]}")
    # 1-8 타입명 표시
    for i, txt in enumerate(segs_text):
        if TYPE_RE.search(txt.replace("{", "").replace("}", "")):
            if not any(s.get("label") for s in shots if s["seg"] == i):
                E("1-8 타입명 표시 없음", f"구간 {i} «{txt.replace('|', ' ')}» — 화면에 84A 같은 타입명이 없다")
    # 1-9 첫 화면은 영상
    if shots and shots[0]["kind"] != "video":
        E("1-9 오프닝", f"첫 화면이 영상이 아니다 ({shots[0]['kind']})")
    # 2-1 시간 — 같은 자료 안에서 카메라만 옮겨 가는 이어진 샷(cont, 같은 src)은 한 번 보여 준 것으로 합쳐 잰다
    #   (2026-09-28 rf5: 84A·180A 한 장을 2.87초 보여 주며 84A → 180A 로 옮겨 가는 걸 1.3초 두 개로 잘못 셌다)
    runs = []
    for s in shots:
        if runs and s.get("cont") and str(s["src"]) == str(runs[-1]["src"]) and abs(s["t0"] - runs[-1]["t1"]) < 1e-3:
            runs[-1] = dict(runs[-1], t1=s["t1"])
        elif s.get("cont") and s.get("tr") is None:
            continue          # 위아래 분할의 소스별 칸(중복 검사용) — 길이는 본 칸에서 잰다
        else:
            runs.append(dict(s))
    for s in runs:
        d = s["t1"] - s["t0"]
        if s["kind"] in ("image", "doc") and d < IMG_MIN - 1e-6:
            E("2-1 자료 2초 미만", f"{at(s)} {d:.2f}초 {Path(str(s['src'])).name}")
        elif d < ANY_MIN - 1e-6:
            E("2-1 1초 미만 화면", f"{at(s)} {d:.2f}초 {Path(str(s['src'])).name}")
        elif s["kind"] == "video" and d > SCENE_MAX + 0.3:
            Wn("2-2 한 장면 3초 초과", f"{at(s)} {d:.2f}초 {Path(str(s['src'])).name}")
    # 3-1 같은 전환 연속
    for a, b in zip(shots, shots[1:]):
        if a.get("tr") and a.get("tr") == b.get("tr") and b["t0"] > 0:
            E("3-1 같은 전환 연속", f"{at(a)} → {at(b)} 둘 다 «{b['tr']}»")
    # 4-1 자막 원문 대조
    if ref_lines is not None:
        norm = lambda x: re.sub(r"[\s|{}.,!?~·…]", "", x)  # noqa: E731
        ref = norm("".join(ref_lines))
        got = norm("".join(segs_text))
        if ref != got:
            k = next((i for i, (x, y) in enumerate(zip(ref, got)) if x != y), min(len(ref), len(got)))
            E("4-1 자막 ≠ 원문", f"원문 «…{ref[max(0, k - 8):k + 8]}…» / 자막 «…{got[max(0, k - 8):k + 8]}…»")
    return out


def check_sfx(events, total):
    """events = [(초, 파일)] 또는 [(초, 파일, 길이초)] — 5-2 같은 효과음 연속, 5-2b 짧은 주기 반복, 5-3 빈 구간.
    길이가 있으면 5-3 은 «소리가 실제로 안 나는 시간»(앞 소리 끝 → 다음 소리 시작)으로 잰다(10-07 — 시작 간격만 세면
    빈칸 메우려 요소를 끼워 넣어 장면이 급해진다, 사장님 «연출이 전체적으로 급해서 정신없는 느낌»)."""
    out = []
    dur = {(e[0], str(e[1])): e[2] for e in events if len(e) > 2}
    ev = sorted((e[0], e[1]) for e in events)
    for (t1, f1), (t2, f2) in zip(ev, ev[1:]):
        if f1 == f2:
            out.append(("ERROR", "5-2 같은 효과음 연속", f"{t1:5.2f}s · {t2:5.2f}s {Path(str(f1)).name}"))
    last, chain = {}, {}
    for t, f in ev:                           # 5-2b 번갈아 쓰기는 같은 파일이 짧은 주기로 3번까지만 (사장님 10-02)
        chain[f] = chain.get(f, 0) + 1 if f in last and 0 < t - last[f] < SFX_REPEAT_MIN else 1
        if chain[f] > SFX_ALT_MAX:
            out.append(("ERROR", "5-2b 같은 효과음 짧은 주기 반복", f"{t:5.2f}s {Path(str(f)).name} — {SFX_REPEAT_MIN:.0f}초 간격 안에 {chain[f]}번째"))
        last[f] = t
    end = 0.0
    for t, f in ev + [(total, None)]:
        if t - end > SFX_GAP:
            out.append(("ERROR", "5-3 효과음 빈 구간", f"{end:5.2f}~{t:5.2f}s ({t - end:.1f}초)"))
        if f is not None:
            end = max(end, t + dur.get((t, str(f)), 0.0))
    return out


def report(items, path=None, title=""):
    err = [x for x in items if x[0] == "ERROR"]
    lines = [f"규칙 점검 {title} — ERROR {len(err)} · WARN {len(items) - len(err)}  (기준: {GUIDE})"]
    lines += [f"  [{lv}] {r}: {m}" for lv, r, m in items] or ["  통과"]
    txt = "\n".join(lines)
    print(txt, flush=True)
    if path:
        Path(path).write_text(txt + "\n", encoding="utf-8")
    return len(err)


if __name__ == "__main__":
    d = json.load(open(sys.argv[1], encoding="utf-8"))
    n = report(check_plan(d["shots"], d.get("segs_text", []), d.get("model_ok", []), d.get("ref_lines")))
    sys.exit(1 if n else 0)
