# -*- coding: utf-8 -*-
"""파트너센터 자동 — 아침 검수표(납품/파트너센터_자동/검수표.md). 실명은 넣지 않는다."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TMP = ROOT / "_tmp" / "pc"
OUT = ROOT / "납품" / "파트너센터_자동" / "검수표.md"
cap = json.load(open(TMP / "captions_v1.json", encoding="utf-8"))
mos = json.load(open(TMP / "mosaic_boxes.json", encoding="utf-8"))
plan = json.load(open(TMP / "plan.json", encoding="utf-8"))
sfx = json.load(open(TMP / "sfx_report.json", encoding="utf-8"))
ver = json.load(open(TMP / "verify.json", encoding="utf-8")) if (TMP / "verify.json").exists() else None
tm = json.load(open(TMP / "subtiming_v1.json", encoding="utf-8"))


def mmss(t):
    return f"{int(t // 60):02d}:{t % 60:05.2f}"


L = ["# 파트너센터 본편 — 자동 연출 검수표 (2026-10-13)", "",
     "> 완성본: `파트너센터_자동.mp4`(1920×1080 59.94, 23분 21초). 사장님 컷·자막 시각은 그대로, 아래 «바꾼 곳»만 다르다.",
     "> 시각은 완성본 기준(분:초). 소리는 제가 귀로 듣지 못했습니다 — 수치 점검만 했습니다.", ""]
L += ["## 1. 모자이크 (규칙 1)", "", "| 구간 | 무엇 | 방법 |", "|---|---|---|"]
for m in mos:
    L.append(f"| {mmss(m['t0'])} ~ {mmss(m['t1'])} | {m['why']} | {'창 전체 + 체험병원 예시로 다시 그린 카드' if m['box'][2] == 1920 else '칸 단위'} |")
L += ["", "- 가리지 않은 것: 체험병원 예시 데이터(010-0000·010-0010 번호, 데모 이름), 담당자 카드(사장님 예외: 담당자 이름·대표 번호), 직원별 응답 속도 표의 직원 이름(체험 계정 직원 — **확인 부탁**).", ""]
L += ["## 2. 자막 (규칙 3)", "", "강제 정렬로 798줄 전수 검사. 사장님 자막은 말보다 0~0.1초 먼저 뜨는 결이라 그 결은 그대로 두었습니다.", "",
      "| 시각 | 전 | 후 | 근거 |", "|---|---|---|---|"]
for c in cap["changes"]:
    if c["kind"] == "글":
        L.append(f"| {mmss(c['t0'])} | {c['before']} | **{c['after']}** | {c['why']} |")
    else:
        L.append(f"| {mmss(c['t0'])} | {c.get('text', '')} 시작 {c['before']} | {c['after']} | {c['why']} |")
for h in cap.get("hold", []):
    L.append(f"| {mmss(h['t0'])} | {h['text']} | (그대로) | **확인 필요** — {h['why']} |")
from collections import Counter
cnt = Counter(v for r in tm for v in r.get("verdict", ["판단불가"]))
L += ["", f"- 타이밍 판정(바꾼 뒤): {dict(cnt)} — «늦음/먼저 꺼짐» 남은 줄은 «어·은» 같은 군말이 자막에 없어 정렬이 흔들린 자리로 보고 그대로 두었습니다.", ""]
L += ["## 3. 연출 (장면 18곳)", "", "| 시각 | 연출 | 근거 |", "|---|---|---|"]
rows = []
for c in plan["cams"]:
    rows.append(f"| {mmss(c['t0'])} ~ {mmss(c['t1'])} | 실화면 확대(최대 {c['zmax']}배) | 말하는 화면 칸 — 외부 호평 1위 구도(실제 관리 화면에서 보여 주기) |")
for f in plan["fx"]:
    if f["kind"] in ("brush_rect", "underline"):
        rows.append(f"| {mmss(f['t0'])} ~ {mmss(f['t1'])} | {'붓 획 테두리' if f['kind'] == 'brush_rect' else '밑줄'} | 그 순간 말하는 칸 |")
    elif f["kind"] == "image":
        rows.append(f"| {mmss(f['t0'])} ~ {mmss(f['t1'])} | 이미지 {Path(f['src']).stem} | 매체 로고(위키미디어) · 체험병원 예시 카드 |")
    elif f["kind"] == "chip":
        rows.append(f"| {mmss(f['t0'])} ~ {mmss(f['t1'])} | 조작 키 칩 «{f['text']}» | 키 조작 표시 |")
L += sorted(rows)
L += ["", "## 4. 효과음", "", f"- 큐 {sfx['cues']} → 배치 {sfx['placed']} · ERROR {len(sfx['errors'])} · 경고 {len(sfx['warnings'])} · 크기 폭 {sfx['rel_spread_db']:.1f}dB(확대 휙은 사장님 값대로 작게)",
      "- 규칙: 그래픽에만(장면 밖 강의엔 없음) · 들리는 어택 정렬 · 겹침 0 · 마림바/실로폰 0 · 같은 소리 3초 안 연속 0", ""]
if ver:
    s = ver["ssim_outside_fx"]
    L += ["## 5. 전체 검수 (끝나고 1번)", "",
          f"- 원문 대조(연출 밖 {s['n']}표본): SSIM 평균 {s['mean']} · 최저 {s['min']} · 0.93 미만 {len(s['low'])}곳 {s['low'][:12]}",
          f"- 완성본 OCR 재검사(1초마다): 금지어·IP·실제 번호 걸린 곳 **{len(ver['privacy_hits'])}곳** {ver['privacy_hits'][:10]}",
          f"- 음량: 통합 {ver['loudness']['integrated_lufs']} LUFS · 트루피크 {ver['loudness']['true_peak_dbtp']} dBTP", ""]
L += ["## 6. 사장님께 여쭐 것", "", "1. 988초 «이건 무조건 끄고» — «그거»로 들리기도 합니다. 그대로 둘까요?",
      "2. 직원별 응답 속도 표의 직원 이름 — 가려야 하나요?", "3. 연출 밀도(23분에 18곳)·카드 디자인 방향 — 피드백 주시면 `피드백/` 에 기록하고 다음 편에 반영합니다.", ""]
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(L), encoding="utf-8")
print(OUT)
