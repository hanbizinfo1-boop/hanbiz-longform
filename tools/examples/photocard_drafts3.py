# -*- coding: utf-8 -*-
r"""12강 포토카드 시안 5차 — 카드 디자인만 새로 (사장님 09-29 «글자는 되었는데 카드가 마음에 안 들어,
위에 줄이나 테이프 같은 건 다 없애고 카드만 좀 깔끔한 디자인으로 4개»).

글자·색은 시안4 그대로(photocard_drafts2.body — 흰 글자+얇은 검은 테두리, 노랑은 «기술성»·«중진공»만).
  python photocard_drafts3.py → _tmp\out\12강\포토카드_시안5\
"""

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))   # tools/ (config.py)
import config  # noqa: E402
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).parent))
import photocard_drafts2 as P  # noqa: E402

OUT = (config.WORK / "out" / "12강" / "포토카드_시안5")
CW, CH, POS = P.CW, P.CH, P.POS
NAVY, BLUE, ORANGE = (11, 42, 122), (47, 91, 208), (242, 140, 28)


def base(r=28, fill=(255, 255, 255, 255)):
    c, m = P.rounded((CW, CH), r, fill)
    return c, m


def card_1():
    """왼쪽 브랜드색 세로 띠 — 흰 카드 왼쪽 가장자리에 파랑→주황 얇은 그라데이션, 로고 왼쪽 정렬."""
    c, m = base(24)
    bar = P.grad(10, CH, BLUE, ORANGE, vertical=True)
    c.paste(bar, (0, 0), m.crop((0, 0, 10, CH)))
    lg = P.logo("full", 52)
    c.alpha_composite(lg, (48, 48))
    ImageDraw.Draw(c).line([(48, 136), (CW - 48, 136)], fill=(228, 232, 240), width=2)
    P.body(ImageDraw.Draw(c), 48, 170)
    return c


def card_2():
    """위 얇은 그라데이션 선 + 오른쪽 아래 로고 심볼 워터마크 — 가장 담백한 흰 카드."""
    c, m = base(28)
    top = P.grad(CW, 8, BLUE, ORANGE)
    c.paste(top, (0, 0), m.crop((0, 0, CW, 8)))
    sym = P.logo("sym", 260).copy()
    sym.putalpha(sym.getchannel("A").point(lambda v: int(v * 0.07)))
    c.alpha_composite(sym, (CW - 230, CH - 240))
    lg = P.logo("full", 52)
    c.alpha_composite(lg, ((CW - lg.width) // 2, 50))
    ImageDraw.Draw(c).line([(48, 136), (CW - 48, 136)], fill=(228, 232, 240), width=2)
    P.body(ImageDraw.Draw(c), 48, 170)
    return c


def card_3():
    """아주 연한 하늘빛 그라데이션 판 — 위는 연하늘, 아래로 흰색. 모서리 크게 둥글게."""
    c, m = base(40)
    g = P.grad(CW, CH, (232, 242, 255), (255, 255, 255), vertical=True)
    c.paste(g, (0, 0), m)
    d = ImageDraw.Draw(c)
    d.rounded_rectangle([0, 0, CW - 1, CH - 1], 40, outline=(214, 226, 246), width=2)
    lg = P.logo("full", 52)
    c.alpha_composite(lg, ((CW - lg.width) // 2, 50))
    d.line([(CW // 2 - 60, 138), (CW // 2 + 60, 138)], fill=ORANGE, width=3)
    P.body(d, 48, 170)
    return c


def card_4():
    """안쪽 가는 테두리(액자) — 흰 판 안에 연회색 가는 선을 한 번 더, 네 모서리에 브랜드색 작은 꺾쇠."""
    c, m = base(20)
    d = ImageDraw.Draw(c)
    ins = 16
    d.rounded_rectangle([ins, ins, CW - 1 - ins, CH - 1 - ins], 12, outline=(222, 226, 234), width=2)
    L = 34
    for (x, y, sx, sy) in ((ins, ins, 1, 1), (CW - 1 - ins, ins, -1, 1), (ins, CH - 1 - ins, 1, -1), (CW - 1 - ins, CH - 1 - ins, -1, -1)):
        d.line([(x, y), (x + sx * L, y)], fill=BLUE, width=4)
        d.line([(x, y), (x, y + sy * L)], fill=BLUE, width=4)
    lg = P.logo("full", 50)
    c.alpha_composite(lg, ((CW - lg.width) // 2, 54))
    d.line([(56, 136), (CW - 56, 136)], fill=(228, 232, 240), width=2)
    P.body(d, 56, 170)
    return c


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    bg = Image.open(P.BG).convert("RGBA")
    cards = [("1_왼쪽띠", card_1()), ("2_윗선워터마크", card_2()), ("3_연하늘그라데이션", card_3()), ("4_액자테두리", card_4())]
    shots = []
    for name, cd in cards:
        cd.save(OUT / f"{name}.png")
        sh, pad = P.shadow(cd, a=0.30)
        fr = bg.copy()
        fr.alpha_composite(sh, (POS[0] - pad, POS[1] - pad))
        fr.convert("RGB").save(OUT / f"{name}_화면.png")
        shots.append((name, fr))
    sheet = Image.new("RGB", (1920, 1140), (20, 20, 24))
    for k, (name, fr) in enumerate(shots):
        x, y = (k % 2) * 960, (k // 2) * 570
        sheet.paste(fr.convert("RGB").resize((960, 540)), (x, y + 30))
        ImageDraw.Draw(sheet).text((x + 16, y + 2), name.replace("_", " "), font=P.F(P.GB, 24), fill=(255, 255, 255))
    sheet.save(OUT / "모아보기.png")
    print("→", OUT)


if __name__ == "__main__":
    main()
