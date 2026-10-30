# -*- coding: utf-8 -*-
"""성제관03 — lines.json(강제 정렬 → boundary.py --fix) → 녹음원고.md · 바뀐곳.md · 자막 srt.

순서(10-30): transcribe.py → check_ambig.py(애매한 곳) → 녹음원고.txt → align_lines.py → check_energy.py --fix
→ boundary.py --fix → make_docs.py. (refine_onsets.py 는 3편에서 쓰지 않는다 — boundary.py 머리말)
    py -3.11 tools/scenes/sjk03/make_docs.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CASE = ROOT / "핸드오프/2026-10-23_성제관03_배달앱수수료"
LINES = ROOT / "_tmp/sjk03/audio/lines.json"
CHECK = ROOT / "_tmp/sjk03/audio/lines_check.json"     # 묶음 3줄로 다시 돌린 정렬(검수용)
SRT_OUT = ROOT / "_tmp/sjk03/sub/성제관03.srt"
WAV_INFO = "`D:\\성제관 3편\\사장의파트너 3편.wav`(547.21초 · 24bit 48kHz 모노 — 지시서 경로·길이·형식 그대로)"

# 손으로 정한 경계(줄 번호 0부터, 값, 근거) — 정렬 두 번 · 받아쓰기 · 에너지를 하나씩 대 보고 정함(10-30)
MANUAL = [   # (줄 글, 대략 시각, 키, 값, 근거)
    ("같은 가게에서", 120.0, "t1", 120.14, "«세 그릇» 시작에 맞춰 앞 줄 끝"),
    ("세 그릇 묶어서", 120.2, "t0", 120.16, "다시 정렬 120.14 · 받아쓰기 120.12 · 에너지 골 120.13~120.15 뒤 오름 — 첫 정렬 120.29 는 «세 | 그릇» 사이 ㄱ 막힘을 잡음"),
    ("나쁜 기억도", 313.0, "t1", 313.50, "«기억도» 끝 = 골(313.49~313.51)"),
    ("더 빨리 퍼지는 거죠", 313.7, "t0", 313.53, "«더» 시작(받아쓰기 313.52 · 골 뒤 오름 313.53). boundary 는 «더 | 빨리» 사이 ㅃ 막힘(−47dB)을 줄 사이로 잘못 봄 — «더»가 잘림. 조각 점수도 «더» 있음 0.820 대 0.779"),
    ("우리 가게 리뷰부터", 330.6, "t1", 331.49, "«리뷰부터» 끝 = 골 시작(331.49)"),
    ("읽어 보시면 돼요", 331.6, "t0", 331.57, "«읽어» 모음 시작 = 골(−34dB 331.49~331.55) 뒤 오름. 다시 정렬 331.37 은 앞 줄 «터» 꼬리"),
    ("광고는", 384.8, "t1", 384.99, "다음 줄 시작에 맞춤"),
    ("좋은 가게를 더 빨리 알리는 거지", 384.9, "t0", 385.00, "boundary 가 «광고는» 앞 골을 이 줄 시작으로 잘못 씀(같은 골 두 번) — «광고는» 끝 = «좋은» 시작(받아쓰기 385.06)"),
    ("좋게 만들어 주는 게 아닙니다", 388.0, "t1", 389.24, "«꼭» 앞 ㄲ 막힘 시작"),
    ("꼭 기억하세요", 389.4, "t0", 389.26, "«꼭»(받아쓰기 세 번 — 389.2초부터 자른 조각에서도 들림 · 에너지 터짐 389.28). 정렬기는 짧은 막힘소리 «꼭»을 못 잡아 389.48(«기억») 로 둠"),
    ("대신 주변에", 543.5, "t1", 544.05, "다음 줄 «배달하시는» 시작 544.07(정렬 두 번 · 에너지 오름 544.08) 앞에서 끝"),
]


def cap_text(t):
    """자막 글 — 끝 마침표 하나만 뺀다(10-15 «자막에 마지막 마침표 다 제거해줘», 물음표는 그대로)."""
    return re.sub(r"(?<!\.)\.\s*$", "", t.strip())


def ts(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def mmss(t):
    return f"{int(t // 60)}:{t % 60:05.2f}"


def sub_times(rows):
    """자막 시각 — 시작 = 목소리 시작, 끝 = 말 끝 +0.15(다음 줄 시작 −0.02 넘지 않게). 겹침 0."""
    out = []
    for k, r in enumerate(rows):
        nxt = rows[k + 1]["t0"] if k + 1 < len(rows) else r["t1"] + 1
        out.append((r["t0"], min(r["t1"] + 0.15, nxt - 0.02)))
    return out


def main():
    rows = json.load(open(LINES, encoding="utf-8"))
    for text, near, key, v, _ in MANUAL:
        hit = [r for r in rows if r["text"] == text and abs(r["t0"] - near) < 1.0]
        assert len(hit) == 1, (text, near, len(hit))
        hit[0][key] = v
        hit[0].setdefault("manual", []).append(key)
    for k in range(len(rows) - 1):
        assert rows[k + 1]["t0"] > rows[k]["t0"], (k, rows[k]["text"])
        assert rows[k]["t1"] <= rows[k + 1]["t0"] + 1e-6, ("겹침", k, rows[k]["text"], rows[k]["t1"], rows[k + 1]["t0"])
    st = sub_times(rows)
    for r, (a, b) in zip(rows, st):
        r["sub_t0"], r["sub_t1"] = round(a, 3), round(b, 3)
    json.dump(rows, open(LINES, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    SRT_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(SRT_OUT, "w", encoding="utf-8", newline="\n") as f:
        for k, r in enumerate(rows):
            f.write(f"{k + 1}\n{ts(r['sub_t0'])} --> {ts(r['sub_t1'])}\n{cap_text(r['text'])}\n\n")

    # 검수 숫자 — 다시 돌린 정렬(묶음 3줄)과 대조
    chk = json.load(open(CHECK, encoding="utf-8"))
    assert [c["text"] for c in chk] == [r["text"] for r in rows]
    s_ok = sum(abs(r["t0"] - c["t0"]) <= 0.1 for r, c in zip(rows, chk))
    meas = [r for r in rows if r.get("bound", ["", ""])[0] == "잼"]
    gaps = sum(1 for k in range(len(rows) - 1) if rows[k]["sub_t1"] < rows[k + 1]["sub_t0"] - 0.0201)
    stat = dict(n=len(rows), s_ok=s_ok, meas=len(meas), gaps=gaps)

    md = ["# 성제관03 — 녹음 원고 (녹음 정본에서 실제로 한 말 · 한 줄 = 자막 한 줄)", "",
          f"> 녹음: {WAV_INFO}",
          "> 만든 법: faster-whisper large-v3 받아쓰기(`tools/scenes/sjk03/transcribe.py`) → 대본과 대조 → 애매한 31곳은 그 조각만 다시 받아쓰기 + 후보 글 강제 정렬 점수, 점수 차가 작은 6곳은 더 짧은 조각으로 한 번 더, 경계 검수 중 나온 2곳(«꼭» «더»)도 같은 방법(`check_ambig.py`) → MMS_FA 강제 정렬(`align_lines.py`) → 쉼 에너지로 시작·끝(`check_energy.py --fix`) → 줄 사이 소리 골로 시작·끝(`boundary.py --fix`) → 손으로 정한 " + str(len(MANUAL)) + "곳(`make_docs.py` MANUAL — 근거는 코드에)",
          "> 시작·끝 = 목소리 시작 · 말 끝. 자막(srt) 끝 = 말 끝 +0.15초(다음 줄 시작 −0.02초 넘지 않게). 줄 앞 «~» = 녹음대로 고친 줄", "",
          "| # | 대본 줄 | 시작 | 끝 | 녹음 원고 | 정렬 점수 |", "|---|---|---|---|---|---|"]
    for k, r in enumerate(rows):
        md.append(f"| {k + 1} | {r['src']} | {mmss(r['t0'])} | {mmss(r['t1'])} | {r['text']} | {r.get('score', '')} |")
    (CASE / "10_분석/녹음원고.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps(stat, ensure_ascii=False), "· srt", SRT_OUT)


if __name__ == "__main__":
    main()
