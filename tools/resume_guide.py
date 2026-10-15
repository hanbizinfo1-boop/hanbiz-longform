# -*- coding: utf-8 -*-
"""SessionStart 훅(compact·resume) — 자동 압축·세션 재개 뒤에도 규칙을 빠뜨리지 않게, 상시 규칙과 지금 진행 상황을 대화에 넣는다.

[이식본 — 원본 D:/영상제작/도구/점검/resume_guide.py 를 롱폼 폴더 구조에 맞게 다시 씀. 사장님 10-07 «오토컴팩트 진행되더라도 길라잡이 누락되지 않게끔 장치 만들어서 적용»]
.claude/settings.json → hooks.SessionStart(matcher compact|resume) → python tools/resume_guide.py
출력(표준 출력)이 그대로 대화 맥락에 들어간다. **출력은 6000자 이하**(훅 출력이 길면 맥락을 잡아먹는다). 발췌만 믿지 말고 파일을 다시 연다.

넣는 것(우선순위 순):
  1. CLAUDE.md «하드 규칙» — 항목별 첫 줄
  2. 기록/작업기록.md «다음 작업 예정» — 장면별 바깥 줄(첫 줄)  ← 지금 몇 번째 장면인지
  3. references/checklist.md — A표(말하는 사람 위 애펙 장면) 점검표 줄
  4. SKILL.md «사장님 상시 규칙» — 굵은 머리말만
  5. 읽을 순서 안내(꼬리말)
숏폼 세션(핸드오프/역할.local.json «숏폼», 10-15)이면 롱폼 상시 규칙·점검표 대신: shorts/SKILL.md 1~4장 머리줄 · 절대금지 전부 ·
  handoff.py 상태(숏폼 줄) · «롱폼 규격·모드 표는 쓰지 않는다» 한 줄.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".claude" / "skills" / "longform"
LIMIT = 9000


def read(p):
    return p.read_text(encoding="utf-8") if p.exists() else ""


def section(text, heading_keyword, level="##"):
    """'## ... 키워드 ...' 로 시작하는 절을 다음 같은 수준 제목 직전까지 잘라 온다."""
    m = re.search(rf"^{level} [^\n]*{re.escape(heading_keyword)}[^\n]*\n[\s\S]*?(?=\n{level} |\Z)", text, re.M)
    return m.group(0) if m else ""


def clip(s, n):
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def claude_rules():
    """CLAUDE.md 하드 규칙 — '### N. 제목' 아래 첫 문장/불릿 한 줄씩."""
    sec = section(read(ROOT / "CLAUDE.md"), "하드 규칙")
    out = ["## CLAUDE.md 하드 규칙 (항목별 첫 줄)"]
    for m in re.finditer(r"^### ([^\n]+)\n([\s\S]*?)(?=\n### |\n---|\Z)", sec, re.M):
        title, body = m.group(1), m.group(2)
        first = next((ln.strip().lstrip("- ").strip() for ln in body.splitlines() if ln.strip()), "")
        first = re.sub(r"[`*]", "", first)
        out.append(f"- {title} — {clip(first, 78)}")
    return "\n".join(out)


def next_tasks():
    """기록/작업기록.md «다음 작업 예정» — 바깥 줄(들여쓰기 없는 '- ')만, 장면별 첫 줄."""
    rec = re.sub(r"<!--[\s\S]*?-->", "", read(ROOT / "기록" / "작업기록.md"))   # 예시 주석은 뺀다
    sec = section(rec, "다음 작업 예정")
    status = section(rec, "지금 상태")
    out = ["## 기록/작업기록.md — 지금 몇 번째 장면인지"]
    for ln in status.splitlines()[1:]:
        if ln.startswith("- "):
            out.append(clip(ln, 110))
    out.append("### 다음 작업 예정 (장면별 첫 줄)")
    lines = [clip(ln, 140) for ln in sec.splitlines()[1:] if ln.startswith("- ")]
    out += lines[:14] or ["- (비어 있음)"]
    return "\n".join(out)


def checklist():
    """checklist.md A표 — 코드 블록 안의 '[ ] N' 줄."""
    sec = section(read(SKILL / "references" / "checklist.md"), "A.")
    out = ["## 납품 전 점검표 A (전문 references/checklist.md — A~F)"]
    for ln in sec.splitlines():
        if ln.startswith("[ ]"):
            out.append(clip(ln, 96))
    return "\n".join(out)


def skill_rules():
    """SKILL.md 사장님 상시 규칙 — 굵은 머리말만."""
    sec = section(read(SKILL / "SKILL.md"), "상시 규칙")
    out = ["## SKILL.md 사장님 상시 규칙 (머리말만)"]
    heads = []
    for ln in sec.splitlines():
        m = re.match(r"- \*\*(.+?)\*\*", ln)
        if m:
            heads.append(clip(m.group(1), 36))
    out.append(" · ".join(heads))
    return "\n".join(out)


def forbidden():
    """피드백/절대금지.md — 영구 금지(10-13 규칙 4). 줄마다 원문 인용 앞까지만."""
    t = read(ROOT / "피드백" / "절대금지.md")
    lines = []
    for ln in t.splitlines():
        if ln.startswith("- "):
            core = ln.split(" — «")[0].split(" — ")[0]
            lines.append(clip(core, 150))
    return "## 피드백/절대금지.md (영구 — 전문을 다시 열 것)\n" + "\n".join(lines)


def handoff():
    """두 컴퓨터 분업 — 이 컴퓨터 역할과 내 차례 건(받기 없이)."""
    import subprocess
    try:
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "handoff.py"), "상태", "--받기없이"], capture_output=True,
                           text=True, encoding="utf-8", timeout=20, env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
        return "## 두 컴퓨터 분업 (핸드오프/README.md — 시작 때 `python tools/handoff.py 상태` 로 최신 받기)\n" + r.stdout.strip()
    except Exception as e:
        return f"## 두 컴퓨터 분업\n(상태 확인 실패: {e})"


def is_shorts():
    import json
    p = ROOT / "핸드오프" / "역할.local.json"
    try:
        return json.load(open(p, encoding="utf-8-sig")).get("역할") == "숏폼"
    except Exception:
        return False


def shorts_skill():
    """shorts/SKILL.md 1~4장 — 절 제목 + 단계·불릿 줄."""
    t = read(ROOT / ".claude" / "skills" / "shorts" / "SKILL.md")
    out = ["## .claude/skills/shorts/SKILL.md 1~4장 (머리줄 — 전문을 다시 열 것)"]
    for m in re.finditer(r"^## ([1-4]\.[^\n]*)\n([\s\S]*?)(?=\n## |\Z)", t, re.M):
        out.append(f"### {m.group(1).strip()}")
        body = [ln for ln in m.group(2).splitlines() if re.match(r"(\d+\. |- )", ln)]
        body = body or [ln for ln in m.group(2).splitlines() if ln.strip()][:2]   # 불릿 없는 장은 첫 줄들
        out += [clip(re.sub(r"[`*]", "", ln), 150) for ln in body]
    return "\n".join(out)


def main_shorts():
    head = ("# 한비즈 숏폼 전용 세션 — 세션 재개 자동 안내 (D:\숏폼전용 · 역할 «숏폼»)\n"
            "숏폼 세션 — 롱폼 규격·모드 A/B/C 표·longform/SKILL.md 는 쓰지 않는다. CLAUDE.md 는 최상위 규칙·하드 규칙 1~14·절대금지만, "
            "길라잡이는 .claude/skills/shorts/SKILL.md. 쓰는 파일은 건 폴더 40_* · tools_shorts/ · 핸드오프/숏폼로그.md 뿐(롱폼 저장소는 읽기만).\n")
    foot = ("\n---\n읽을 순서: 피드백/절대금지.md 전문([10-12 쇼츠] 줄 전부) → 피드백/원하는영상.md → 그 건의 20_쇼츠기획.md 전부 → "
            "20_대본·20_고정댓글·20_재현자료 → 롱폼 30_결과.md → study/sjk-ref-1014.md 8장 → shorts/SKILL.md 2~4장. 발췌만 믿지 말고 파일을 다시 연다.")
    body = "\n\n".join([handoff(), forbidden(), shorts_skill()])
    keep = LIMIT - len(head) - len(foot) - 4
    print(head + (body if len(body) <= keep else body[:keep].rstrip() + " …") + foot)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if is_shorts():
        return main_shorts()
    head = ("# 한비즈 롱폼 자동화 — 세션 재개 자동 안내 (장면을 만들기 전에 아래를 다시 읽는다)\n"
            "최상위 규칙(10-13): 작업 시작 때 길라잡이(CLAUDE.md·SKILL.md·references·피드백/)를 전문 정독하고, "
            "바뀐 규칙은 매 작업 길라잡이에 반영 — 충돌·병목은 최신으로 정리(폐기는 취소선+날짜, 보존, 갱신). 절대금지는 폐기 없음.\n")
    foot = ("\n---\n읽을 순서: CLAUDE.md → .claude/skills/longform/SKILL.md(3장 상시 규칙·4장 범위·7장 점검표) → 일에 맞는 references/"
            "(장면=motion-graphics.md, 효과음=sfx.md, 무음편집=silence-cut.md, 강의 자료=lecture-graphics.md) → 기록/작업기록.md. "
            "위 파일들을 Read 로 다시 열어 전문을 확인한 뒤 작업을 이어 간다(발췌만 믿지 않는다). "
            "모드 먼저 확인: A. 얹을 것만(구간 지정 — 자료 자리는 사장님) / B. 자동 연출(원문 통째로 — auto-pipeline.md 13장이 A 와 다른 점). "
            "두 모드 모두 컷은 사장님 몫(B 모드 자막은 맞춤법·타이밍만 고치고 검수표에 적음). 피드백/작업목록.json 맨 아래 작업 기록을 먼저 읽는다.")
    parts = [handoff(), forbidden(), claude_rules(), next_tasks(), checklist(), skill_rules()]
    caps = [700, 2600, 1900, 1300, 1700, 900]
    body = []
    for p, c in zip(parts, caps):
        body.append(p if len(p) <= c else p[: c - 2].rstrip() + " …")
    txt = head + "\n\n".join(body) + foot
    if len(txt) > LIMIT:                       # 마지막 안전판: 꼬리말은 남기고 본문을 자른다
        keep = LIMIT - len(foot) - len(head) - 4
        txt = head + "\n\n".join(body)[:keep].rstrip() + " …" + foot
    print(txt)


if __name__ == "__main__":
    main()
