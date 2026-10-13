# -*- coding: utf-8 -*-
r"""Claude Code 세션 로그(jsonl)에서 사람 말·어시스턴트 글만 뽑아 읽을 수 있는 md 로 만든다. 읽기 전용.

도구 호출 결과(이미지 base64·파일 내용)는 빼고, 사장님 메시지(원문)·어시스턴트 답·압축 요약·
어시스턴트가 부른 도구 이름(한 줄)만 남긴다. 원본 세션의 학습(«무엇을 지시했고 무엇이 반려·통과됐나»)용.

    python tools/session_digest.py <세션.jsonl> <출력.md> [--from 2026-10-01] [--to 2026-10-13]

출력은 _tmp/ 아래에 둔다(사장님 말씀이 원문 그대로 들어가므로 커밋하지 않는다).
"""

import json
import sys
from pathlib import Path


def text_of(content):
    """message.content → (사람/어시스턴트 글, 도구 이름 목록). tool_result 는 버린다."""
    if isinstance(content, str):
        return content, []
    out, tools = [], []
    for part in content or []:
        if not isinstance(part, dict):
            continue
        t = part.get("type")
        if t == "text":
            out.append(part.get("text", ""))
        elif t == "tool_use":
            inp = part.get("input", {}) or {}
            hint = inp.get("description") or inp.get("file_path") or inp.get("command", "")[:80]
            tools.append(f"{part.get('name')}: {hint}")
    return "\n".join(out), tools


def main():
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    args = sys.argv[3:]
    lo = args[args.index("--from") + 1] if "--from" in args else ""
    hi = args[args.index("--to") + 1] if "--to" in args else "9999"
    lines = []
    n_user = n_asst = 0
    with src.open(encoding="utf-8", errors="replace") as f:
        for raw in f:
            try:
                ev = json.loads(raw)
            except json.JSONDecodeError:
                continue
            ts = (ev.get("timestamp") or "")[:19]
            if ts and not (lo <= ts[:10] <= hi):
                continue
            typ = ev.get("type")
            msg = ev.get("message") or {}
            if typ == "user":
                if ev.get("isMeta"):
                    continue
                txt, _ = text_of(msg.get("content"))
                txt = txt.strip()
                if not txt or txt.startswith("<local-command") or txt.startswith("<command-name>"):
                    continue
                tag = "압축요약" if ev.get("isCompactSummary") else "사장님"
                if txt.startswith("<system-reminder>") or txt.startswith("<task-notification>"):
                    continue
                lines.append(f"\n### [{ts}] {tag}\n{txt}\n")
                n_user += 1
            elif typ == "assistant":
                txt, tools = text_of(msg.get("content"))
                txt = txt.strip()
                if txt:
                    lines.append(f"\n#### [{ts}] 클로드\n{txt}\n")
                    n_asst += 1
                if tools:
                    lines.append("".join(f"- 🔧 {t}\n" for t in tools))
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(f"# 세션 요약본 — {src.name}\n\n사장님 {n_user} · 클로드 {n_asst}\n" + "".join(lines), encoding="utf-8")
    print(f"{dst} · 사장님 {n_user} · 클로드 {n_asst} · {dst.stat().st_size // 1024}KB")


if __name__ == "__main__":
    main()
