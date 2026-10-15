# -*- coding: utf-8 -*-
"""성제관01 — lines.json(강제 정렬) → 녹음원고.md · 바뀐 곳 표 · 자막 srt.

    py -3.11 tools/scenes/sjk01/make_docs.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.scenes.sjk01.assemble import cap_text  # noqa: E402
CASE = ROOT / "핸드오프/2026-10-14_성제관01_AI10가지"
LINES = ROOT / "_tmp/sjk01/audio/lines_cut.json"   # 10-15 같은 말 다시 한 줄 뺀 판
SRT_OUT = ROOT / "_tmp/sjk01/sub/성제관01.srt"


def ts(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def mmss(t):
    return f"{int(t // 60)}:{t % 60:05.2f}"


def fixed_times(rows):
    """겹침 정리 — 시작은 앞 줄 끝(말 끝) 뒤로, 끝 = 말 끝 +0.15 (다음 시작 −0.02 넘지 않게)."""
    out = []
    for k, r in enumerate(rows):
        t0 = r["t0"]
        if k and t0 < rows[k - 1]["t1"]:
            t0 = rows[k - 1]["t1"] + 0.01
        out.append([t0, r["t1"]])
    for k in range(len(out)):
        nxt = out[k + 1][0] if k + 1 < len(out) else out[k][1] + 1
        out[k].append(min(out[k][1] + 0.15, nxt - 0.02))
    return out


def main():
    rows = json.load(open(LINES, encoding="utf-8"))
    script = (CASE / "20_대본.md").read_text(encoding="utf-8").splitlines()
    tt = fixed_times(rows)
    for r, (t0, t1, end) in zip(rows, tt):
        r["sub_t0"], r["sub_t1"] = round(t0, 3), round(end, 3)
    json.dump(rows, open(LINES, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # srt
    SRT_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(SRT_OUT, "w", encoding="utf-8", newline="\n") as f:
        for k, r in enumerate(rows):
            f.write(f"{k + 1}\n{ts(r['sub_t0'])} --> {ts(r['sub_t1'])}\n{cap_text(r['text'])}\n\n")

    # 녹음원고.md
    md = ["# 성제관01 — 녹음 원고 (녹음 정본에서 실제로 한 말 · 한 줄 = 자막 한 줄)", "",
          "> 녹음: `D:\\성제관 1편\\성제관 1편.wav`(711.9초 · 24bit 48kHz 모노 — 지시서의 «성제관 1편 수정완료.wav» 자리에 이 이름으로 있었다. 길이·형식이 지시서와 같아 정본으로 씀)",
          "> 만든 법: faster-whisper large-v3 받아쓰기 → 대본과 대조 → 애매한 22곳은 그 조각만 다시 받아쓰기 + 후보 글 강제 정렬 점수로 확정(`tools/scenes/sjk01/check_ambig.py`) → MMS_FA 강제 정렬(`align_lines.py`)",
          "> 시각 = 강제 정렬 첫 어절 시작 · 마지막 어절 끝. 줄 앞 표시: (대본 줄) · «~» 녹음대로 고친 줄 · «+» 녹음에서 더한 줄", "",
          "| # | 대본 줄 | 시작 | 끝 | 녹음 원고 | 정렬 점수 |", "|---|---|---|---|---|---|"]
    for k, r in enumerate(rows):
        md.append(f"| {k + 1} | {r['src']} | {mmss(r['t0'])} | {mmss(r['t1'])} | {r['text']} | {r.get('score', '')} |")
    (CASE / "10_분석/녹음원고.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    # 바뀐 곳 표
    ch = ["# 성제관01 — 녹음과 대본이 바뀐 곳", "",
          "> 종류: 추가(녹음에서 더한 말) · 어미/말 바뀜 · 삭제(대본에 있는데 녹음에 없음) · 반복(같은 말을 두 번 — 편집본에 남아 있음, 사장님 확인 권장)",
          "> 맞춤법만 고친 곳(«예를들어»→«예를 들어», «칠판같은거에요»→«칠판 같은 거예요», «다섯 번 째»→«다섯 번째», «거도»→«근거도», «깔끔하죠.?»→«깔끔하죠?»)은 따로 적지 않았다.", "",
          "| 종류 | 대본 줄 | 대본 글 | 녹음 글 | 시각 |", "|---|---|---|---|---|"]
    seen_src = set()
    for r in rows:
        s = r["src"]
        n = int(s.lstrip("~+"))
        stext = script[n - 1].strip() if n - 1 < len(script) else ""
        if s.startswith("+"):
            kind = "반복" if r["text"].strip(". ") in " ".join(x["text"] for x in rows if x["src"] == str(n)) else "추가"
            ch.append(f"| {kind} | {n} | {stext} | {r['text']} | {mmss(r['t0'])} |")
        elif s.startswith("~") and s not in seen_src:
            seen_src.add(s)
            rec = " / ".join(x["text"] for x in rows if x["src"] == s)
            ch.append(f"| 어미/말 바뀜 | {n} | {stext} | {rec} | {mmss(r['t0'])} |")
    # 삭제: 대본 줄 중 원고에 없는 줄(빈 줄 제외)
    used = {int(r["src"].lstrip("~+")) for r in rows}
    for i, line in enumerate(script, 1):
        if line.strip() and i not in used:
            ch.append(f"| 삭제 | {i} | {line.strip()} | (녹음에 없음) | — |")
    ch += ["", "### 확인이 필요한 곳(사장님)",
           "- **10:47 «원가가 60%라서 빼라고 했어요»** — 대본은 70%(앞 9:16 «원가율이 무려 70%예요»와 화면 원가표도 70%). 녹음은 두 번 따로 들어도 «60%». 자막은 녹음대로 60% — 말실수면 자막만 70%로 고치거나 이 구간 재녹음.",
           "- **11:20 «그 시간 아껴서»** — 받아쓰기는 두 번 다 «앞에서»로 들었다. 뜻이 «아껴서»라 그렇게 적었다(발음이 뭉개진 것으로 판단).",
           "- **5:07 «자, 바로 다섯 번째 갈게요»** — 다시 받아쓰기는 «갈 거예요», 강제 정렬 점수는 «갈게요»(0.80 대 0.73). 점수 쪽을 따랐다.",
           "- 같은 말 두 번(편집본에 남아 있음): 2:42 «우리 가게는 ○○동 국밥집이야» · 3:35 «그냥 챗GPT 켜셔서 / 켜시고» · 6:39 «위험한 건 맨 위에 넣어 주고» · 9:41 «그냥 사인하시는 분들 진짜 많아요». 자막은 들리는 대로 두 번 넣었다."]
    (CASE / "10_분석/바뀐곳.md").write_text("\n".join(ch) + "\n", encoding="utf-8")
    print("줄", len(rows), "· srt", SRT_OUT)


if __name__ == "__main__":
    main()
