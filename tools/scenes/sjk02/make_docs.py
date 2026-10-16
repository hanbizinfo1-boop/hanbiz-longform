# -*- coding: utf-8 -*-
"""성제관02 — lines.json(강제 정렬) → 녹음원고.md · 바뀐 곳 표 · 자막 srt.

    py -3.11 tools/scenes/sjk02/make_docs.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.scenes.sjk02.assemble import cap_text  # noqa: E402
CASE = ROOT / "핸드오프/2026-10-14_성제관02_AI시대90퍼1퍼"
LINES = ROOT / "_tmp/sjk02/audio/lines.json"   # 편집본 정렬 → 에너지로 시작·끝 다듬은 판(check_energy --fix)
SRT_OUT = ROOT / "_tmp/sjk02/sub/성제관02.srt"


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
    md = ["# 성제관02 — 녹음 원고 (녹음 정본에서 실제로 한 말 · 한 줄 = 자막 한 줄)", "",
          "> 녹음: `D:\\성제관 1편\\성제관 1편.wav`(711.9초 · 24bit 48kHz 모노 — 지시서의 «성제관 1편 수정완료.wav» 자리에 이 이름으로 있었다. 길이·형식이 지시서와 같아 정본으로 씀)",
          "> 만든 법: faster-whisper large-v3 받아쓰기 → 대본과 대조 → 애매한 22곳은 그 조각만 다시 받아쓰기 + 후보 글 강제 정렬 점수로 확정(`tools/scenes/sjk02/check_ambig.py`) → MMS_FA 강제 정렬(`align_lines.py`)",
          "> 시각 = 강제 정렬 첫 어절 시작 · 마지막 어절 끝. 줄 앞 표시: (대본 줄) · «~» 녹음대로 고친 줄 · «+» 녹음에서 더한 줄", "",
          "| # | 대본 줄 | 시작 | 끝 | 녹음 원고 | 정렬 점수 |", "|---|---|---|---|---|---|"]
    for k, r in enumerate(rows):
        md.append(f"| {k + 1} | {r['src']} | {mmss(r['t0'])} | {mmss(r['t1'])} | {r['text']} | {r.get('score', '')} |")
    (CASE / "10_분석/녹음원고.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    # 바뀐 곳 표
    ch = ["# 성제관02 — 녹음과 대본이 바뀐 곳", "",
          "> 종류: 추가(녹음에서 더한 말) · 어미/말 바뀜 · 삭제(대본에 있는데 녹음에 없음) · 반복(같은 말을 두 번 — 편집본에 남아 있음, 사장님 확인 권장)",
          "> 맞춤법·띄어쓰기만 고친 곳(«첫번째»→«첫 번째», «시킨다음에»→«시킨 다음에», «검수한번 안해보고»→«검수 한번 안 해 보고», «떠오를거예요»→«떠오를 거예요», «말씀드리는거니까»→«말씀드리는 거니까», «확인하냐구요»→«확인하냐고요», «하던걸»→«하던 걸» 등)은 따로 적지 않았다.", "",
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
    def at(txt):
        r = next(x for x in rows if txt in x["text"])
        return mmss(r["t0"])
    ch += ["", "### 순서가 바뀐 곳(사장님 10-16 «9분 이후 딱 한 곳»)",
           f"- {at('몇 개나 있는지')} 대본 681~685 «오늘 밤에 가게 문 닫으시고 / 한번 확인해 보세요. / 우리 가게만 쓸 수 있는 특징이 / 몇 개나 있는지» → 편집본은 «오늘 밤에 가게 문 닫으시고 / 우리 가게만 쓸 수 있는 특징이 / 몇 개나 있는지 한번 확인해 보세요.»(«한번 확인해 보세요»가 뒤로). 자막은 들리는 순서.",
           "", "### 편집 이음매",
           "- 편집본은 쉼을 바짝 줄여 이어 붙여(쉼 0.1~0.3초) 이음매가 쉼 자리에 있다. 강제 정렬은 쉼(받아쓰기 시각 틈 0.12초 이상)에서 끊은 덩어리마다 따로, 창도 앞뒤 쉼 가운데까지만(이음매를 넘지 않음).",
           "- 말 도중에 뚝 끊긴 이음매는 받아쓰기에 끊긴 낱말로 나타나는데 한 곳도 없었다. 파형 후보(클릭·바닥 소음 계단)는 `_tmp/sjk02/audio/seams.json`.",
           "", "### 확인이 필요한 곳(사장님)",
           f"- **{at('99%랑')} «99%랑 1%를 진짜로 가르는 게»** — 대본·제목은 90%. 녹음은 받아쓰기 두 번 모두 «99%», 강제 정렬 점수도 99 쪽(0.775 대 0.759). 자막은 녹음대로 99% — 말실수면 자막만 90%로. 화면 연출(셔터 격자 등)은 90% / 1%.",
           f"- **{at('새벽 3시')} «아까 그 새벽 3시 국밥집처럼요»** — 대본·앞 장면은 «새벽 5시». 녹음은 받아쓰기 두 번 «3시», 점수도 3시(0.749 대 0.653). 자막은 녹음대로 3시 — 말실수면 자막만 5시로.",
           f"- **{at('이 첫 솥이에요')} «이 첫 솥이에요 / 오늘 첫 솥이에요»** — 같은 말 두 번(다시 말한 흔적). 지시서대로 자막도 들리는 대로 두 번.",
           "- **«남는 돈» 6곳 → 화면 자막은 «수익»** — 녹음에는 «근데 남는 돈은 한 달 지나서» · «이번 주에 실제로 남은 돈 계산해 주고» · «실제로 남은 돈 100만 원» · «근데 남는 돈을 매주 뽑아 보니까» · «통장에 남는 돈은» · «남는 돈을 따져 보니까»가 남아 있다(녹음이 10-16 «남는 돈 → 수익» 규칙보다 먼저). 절대금지(«남는 돈»이라고 쓰지 않는다)를 따라 자막은 «수익»(«실제 수익» · «통장 수익은»). 목소리와 글이 다른 곳이라 재녹음하거나, 자막도 말대로 두라고 하시면 `assemble.SHOW` 를 비우면 된다.",
           f"- {at('다른 거거든요')} «AI 말고 다른 거거든요» · {at('평균적인 글이거든요')} «평균적인 글이거든요» — 대본은 «~거예요»«~글이에요». 받아쓰기 두 번은 «거든요», 정렬 점수는 대본 쪽이 조금 높음 → 받아쓰기(서로 다른 두 번이 같음)를 따름.",
           f"- {at('이상한 생각')} «이상한 생각 드실 수도 있어요» — 받아쓰기는 «드릴»로 들었다. 뜻대로 «드실»(점수 차 0.016).",
           f"- {at('늘어난 가게도')} «늘어난» — 받아쓰기는 «드러난»으로 들었지만 소리가 같다([느러난]) → 대본 글.",
           ]
    (CASE / "10_분석/바뀐곳.md").write_text("\n".join(ch) + "\n", encoding="utf-8")
    print("줄", len(rows), "· srt", SRT_OUT)


if __name__ == "__main__":
    main()
