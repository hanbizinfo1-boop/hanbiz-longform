# -*- coding: utf-8 -*-
"""파트너센터 자동 — 모자이크 칸 만들기(규칙 1). 실명 목록은 기록/비공개/ 에 있고 여기엔 시각·칸만.

1) 텔레그램 창 구간: OCR 로 대략 찾고(0.5초 간격) → 경계 ±1초를 프레임마다 «텔레그램 대화 초록 바탕 비율»로 정확히 → 창 전체(작업표시줄 위) 모자이크
2) 텔레그램 알림 팝업·작업표시줄 미리보기: 칸 단위 모자이크(앞뒤 0.4초 여유)
출력 _tmp/pc/mosaic_boxes.json (시퀀스 시각 · 녹화 좌표)
"""
import json, re, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ROOT))
from tools.auto.layers import TrackReader, SEQ_FPS
TMP = ROOT / "_tmp" / "pc"
d = json.load(open(TMP / "ocr.json", encoding="utf-8"))
it = json.load(open(TMP / "edit.json", encoding="utf-8"))["items"]
v1 = [i for i in it if i["track"] == "V1" and "화면" in i["name"]]
FPS = float(SEQ_FPS)
def seq(s): return [i["t0"] + s - i["s0"] for i in v1 if i["s0"] <= s < i["s1"]]
TG = re.compile(r"유월비|members|memnbers|mnembers|shared links|Write a mess|광고일림|광고알림록 .*members")
pts = sorted(t for smp in d["samples"] if TG.search(" ".join(b[4] for b in smp["boxes"])) for t in seq(smp["s"]))
groups = []
for t in pts:
    if groups and t - groups[-1][1] <= 1.5: groups[-1][1] = t
    else: groups.append([t, t])
R = TrackReader([i for i in it if i["track"] == "V1"], [r"D:\26년 10월\261012"])
def is_tg(k):
    f, _ = R.frame(k)
    if f is None: return False
    roi = f[150:900, 500:1400].astype(np.int16)      # 대화 영역
    b, g, r = roi[..., 0], roi[..., 1], roi[..., 2]
    green = (g > r + 4) & (g > b + 12) & (g > 150) & (g < 235)
    return green.mean() > 0.25
out = []
for a, b in groups:
    ka = next((k for k in range(int((a - 1.2) * FPS), int((a + 1.2) * FPS)) if is_tg(k)), None)
    if ka is None:                                    # 창이 아니라 알림 팝업 등 → 2) 에서 칸 단위로
        print(f"  {a:.2f}~{b:.2f} 텔레그램 창 아님(팝업) — 건너뜀", flush=True); continue
    kb = ka                                           # 뒤로 가면 매번 seek 라 느리다 → 앞으로 훑으며 마지막 텔레그램 프레임
    for k in range(max(ka, int((b - 0.3) * FPS)), int((b + 1.2) * FPS)):
        if is_tg(k): kb = k
    t0, t1 = ka / FPS - 0.5 / FPS, (kb + 1) / FPS
    out.append(dict(t0=round(t0, 3), t1=round(t1, 3), box=[0, 0, 1920, 1040], block=22, why="텔레그램 창 전체"))
    print(f"텔레그램 {a:.2f}~{b:.2f} → 프레임 {t0:.3f}~{t1:.3f}")
# 알림 팝업 · 미리보기 (OCR 로 시각, 칸은 화면에서 잰 값)
POP = [(re.compile(r"한마 광고"), (1500, 1000), [1508, 905, 1915, 1015], "텔레그램 알림 팝업"),
       (re.compile(r"한마 광고"), (1200, 838), [1088, 800, 1378, 1038], "작업표시줄 텔레그램 미리보기")]
for rx, near, box, why in POP:
    ts = []
    for smp in d["samples"]:
        for bb in smp["boxes"]:
            cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
            if rx.search(bb[4]) and abs(cx - near[0]) < 260 and abs(cy - near[1]) < 90:
                ts += seq(smp["s"])
    ts = sorted(t for t in ts if not any(o["t0"] - 1 <= t <= o["t1"] + 1 for o in out if o["box"][2] == 1920))
    gs = []
    for t in ts:
        if gs and t - gs[-1][1] <= 1.5: gs[-1][1] = t
        else: gs.append([t, t])
    for a, b in gs:
        out.append(dict(t0=round(a - 0.6, 3), t1=round(b + 0.6, 3), box=box, block=14, why=why))
        print(f"{why} {a - 0.6:.2f}~{b + 0.6:.2f}")
json.dump(sorted(out, key=lambda m: m["t0"]), open(TMP / "mosaic_boxes.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
