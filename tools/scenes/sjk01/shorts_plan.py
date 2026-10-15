# -*- coding: utf-8 -*-
"""성제관01 쇼츠 S1~S6 — 녹음 줄(lines.json index)로 편집 목록 → 소리 조각 이어 붙이기 + 쇼츠용 줄 시각(data/sh_SN.js).

20_쇼츠기획.md 0장 규칙: 첫 1~3초 = 그 편에서 제일 센 줄을 앞으로(녹음 안에서 순서만) · 롱폼 문맥 말(«아까»«○번째»«이따가») 빼기 ·
자르는 점은 실제 무음(줄 시작 −0.12 / 끝 +0.18, 다음 줄과 겹치지 않게) · 마지막 말 끝나면 0.5초 안에 끝 · CTA 목소리는 편마다(3장).
줄 번호는 대본 줄이 아니라 녹음 원고 줄(lines_idx.txt) — 대본 줄 → 녹음 줄 대응은 10_분석/녹음원고.md.
    py -3.11 tools/scenes/sjk01/shorts_plan.py
"""
import json
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[3]
LINES = json.load(open(ROOT / "_tmp/sjk01/audio/lines.json", encoding="utf-8"))
SRC = r"D:\성제관 1편\성제관 1편.wav"
OUT = ROOT / "_tmp/sjk01/shorts"
DATA = Path(__file__).resolve().parent / "data"

# 편 → (제목 2줄, [녹음 줄 묶음 …]) — 묶음 = (첫 줄, 끝 줄) 포함, 순서대로 이어 붙임
SHORTS = {
    "S1": (("AI한테 메뉴 설명 시킬 때", "꼭 넣어야 할 한 줄"),
           [(141, 141), (113, 117), (122, 127), (129, 140), (142, 144), (418, 420)]),
    "S2": (("팔수록 손해 보는", "메뉴 찾는 법"),
           [(333, 334), (316, 321), (327, 332), (376, 389), (392, 398), (426, 426)]),
    "S3": (("알바한테 두 번 설명 안 하는", "마감 매뉴얼 비법"),
           [(218, 219), (213, 217), (220, 237), (238, 238), (240, 242), (246, 248), (422, 424)]),
    "S4": (("알바 지원자 몰리는", "공고 한 줄 비법"),
           [(253, 254), (250, 252), (255, 262), (263, 269), (270, 276), (422, 424)]),
    "S5": (("리뷰 답글 한 달 7시간 반", "30분으로 줄이는 법"),
           [(43, 45), (38, 42), (50, 53), (57, 64), (66, 69), (70, 73), (75, 77), (418, 420)]),
    "S6": (("계약서 도장 찍기 전에", "AI한테 물어볼 질문"),
           [(349, 350), (345, 348), (353, 364), (365, 369), (426, 426)]),
}
PRE, POST = 0.12, 0.18
SR = 48000


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    wav, sr = sf.read(SRC, dtype="float32")
    assert sr == SR
    summary = {}
    for name, (title, groups) in SHORTS.items():
        pieces, lines_out, t = [], [], 0.0
        for gi, (a, b) in enumerate(groups):
            # 처음 자른 점(정렬 시작 −0.12)을 유지하되, 목소리 시작 보정(refine_onsets)으로 당겨진 줄은 그 시작 −0.02 까지
            s0 = max(0.0, min(LINES[a].get("t0_aligned", LINES[a]["t0"]) - PRE, LINES[a]["t0"] - 0.02))
            if a > 0:
                s0 = max(s0, LINES[a - 1]["t1"] + 0.02)
            s1 = LINES[b]["t1"] + POST
            if b + 1 < len(LINES):
                s1 = min(s1, LINES[b + 1]["t0"] - 0.02)
            seg = wav[int(s0 * SR):int(s1 * SR)].copy()
            f = min(int(0.012 * SR), len(seg) // 4)          # 잇는 곳 아주 짧은 페이드(숨 남김)
            seg[:f] *= np.linspace(0, 1, f); seg[-f:] *= np.linspace(1, 0, f)
            for i in range(a, b + 1):
                L = LINES[i]
                lines_out.append({"i": i, "text": L["text"], "t0": round(t + L["t0"] - s0, 3), "t1": round(t + L["t1"] - s0, 3),
                                  "words": [{"w": w["w"], "t0": round(t + w["t0"] - s0, 3), "t1": round(t + w["t1"] - s0, 3)} for w in L["words"]],
                                  "group": gi})
            pieces.append({"group": gi, "src": [round(s0, 3), round(s1, 3)], "at": round(t, 3)})
            pieces_audio = seg
            t += len(seg) / SR
            if gi == 0:
                buf = [seg]
            else:
                buf.append(seg)
        tail = np.zeros(int(0.4 * SR), np.float32)
        audio = np.concatenate(buf + [tail])
        sf.write(OUT / f"{name}_목소리.wav", audio, SR, subtype="PCM_24")
        dur = round(len(audio) / SR, 3)
        # 자막 끝 = 말 끝 +0.15 (다음 시작 넘지 않게)
        for k, L in enumerate(lines_out):
            nxt = lines_out[k + 1]["t0"] if k + 1 < len(lines_out) else dur
            L["end"] = round(min(L["t1"] + 0.15, nxt - 0.02), 3)
        sc = {"short": name, "title": title, "dur": dur, "pre": 0.0, "post": 0.0, "t0": 0.0, "lines": lines_out, "pieces": pieces,
              "groups": [list(g) for g in groups]}
        (DATA / f"sh_{name}.js").write_text("window.SC = " + json.dumps(sc, ensure_ascii=False) + ";\n", encoding="utf-8")
        summary[name] = dur
        print(name, f"{dur:5.1f}초", " / ".join(L["text"][:10] for L in lines_out[:3]), "…", lines_out[-1]["text"][:16])
    json.dump(summary, open(OUT / "길이.json", "w", encoding="utf-8"), ensure_ascii=False)


if __name__ == "__main__":
    main()
