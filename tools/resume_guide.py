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
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".claude" / "skills" / "longform"
LIMIT = 6000


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


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    head = "# 한비즈 롱폼 자동화 — 세션 재개 자동 안내 (장면을 만들기 전에 아래를 다시 읽는다)\n"
    foot = ("\n---\n읽을 순서: CLAUDE.md → .claude/skills/longform/SKILL.md(3장 상시 규칙·4장 범위·7장 점검표) → 일에 맞는 references/"
            "(장면=motion-graphics.md, 효과음=sfx.md, 무음편집=silence-cut.md, 강의 자료=lecture-graphics.md) → 기록/작업기록.md. "
            "위 파일들을 Read 로 다시 열어 전문을 확인한 뒤 작업을 이어 간다(발췌만 믿지 않는다). 컷·자막·자료 자리는 사장님이 정한다.")
    parts = [claude_rules(), next_tasks(), checklist(), skill_rules()]
    caps = [1500, 1300, 1700, 900]
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
