# -*- coding: utf-8 -*-
r"""12강 포토카드 시안 2차 (사장님 09-29 피드백 반영).

피드백: «회전시키지 말고 똑바로», «판이 어두우면 글자가 잘 안 보인다 → 밝은 배경»,
        «글자는 너무 많은 색 쓰지 말고 강조할 때만 노란색 혹은 초록색, 나머지는 다 하얀색»,
        «글자 안 보이는 거 방지를 위해 글자 테두리 살짝 까맣게»
  python photocard_drafts2.py  → _tmp\out\12강\포토카드_시안4\A~D_*.png · A~D_화면.png · 모아보기.png
글자는 강사 말(자막 006~009)에서만. 시안은 글자가 다 나온 마지막 상태.
"""

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))   # tools/ (config.py)
import config  # noqa: E402
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = (config.WORK / "out" / "12강" / "포토카드_시안4")
BG = (config.WORK / "out" / "12강" / "frame_13.0.png")
AS = (config.WORK / "out" / "자료카드" / "assets")
FD = config.USER_FONTS
GB, GM = str(FD / "GmarketSansBold.otf"), str(FD / "GmarketSansMedium.otf")
W_, Y_, G_ = (255, 255, 255), (255, 222, 40), (70, 230, 120)     # 흰 · 노랑(강조) · 초록(구분이 필요할 때만 — 사장님 09-29)
K = (0, 0, 0)
NAVY, BLUE = (11, 42, 122), (47, 91, 208)
CW, CH = 600, 700
POS = (1270, 170)


def F(p, s):
    return ImageFont.truetype(p, s)


def logo(which="full", h=60):
    im = Image.open(AS / {"full": "logo_full.png", "sym": "logo_symbol.png"}[which]).convert("RGBA")
    return im.resize((round(im.width * h / im.height), h), Image.LANCZOS)


def say(d, xy, parts, font, sw):
    """[(글, 색)] 한 줄 — 흰 글자 + 얇은 검은 테두리, 강조만 노랑/초록."""
    x0, y = xy
    for layer in ("stroke", "fill"):          # 테두리를 줄 전체에 먼저 → 글자색을 위에 (테두리가 옆 글자를 먹지 않게)
        x = x0
        for t, c in parts:
            if layer == "stroke":
                d.text((x, y), t, font=font, fill=K, stroke_width=sw, stroke_fill=K)
            else:
                d.text((x, y), t, font=font, fill=c)
            x += d.textlength(t, font=font) + 1
    return x


def rounded(size, r, fill):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], r, fill=255)
    im = Image.new("RGBA", size, fill)
    im.putalpha(m)
    return im, m


def shadow(card, blur=20, off=(0, 14), a=0.35):
    w, h = card.size
    pad = blur * 3
    sh = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    sh.paste((0, 0, 0, 255), (pad + off[0], pad + off[1]), card.getchannel("A").point(lambda v: int(v * a)))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    sh.alpha_composite(card, (pad, pad))
    return sh, pad


def body(d, x0, y0):
    """제목 + 두 줄 + = 중진공 (자막 007·008·009 가 하나씩 생길 자리)."""
    say(d, (x0, y0), [("기관명 풀어보기", W_)], F(GM, 28), 2)
    y = y0 + 50
    say(d, (x0, y), [("중소벤처기업진흥공단", W_)], F(GB, 46), 3)
    y += 92
    say(d, (x0, y), [("1. ", W_), ("중소기업 · 벤처기업", W_)], F(GB, 40), 3)
    y += 56
    say(d, (x0 + 44, y), [("지원", W_)], F(GB, 34), 2)
    y += 70
    say(d, (x0, y), [("2. ", W_), ("기술성", Y_), (" 있는 기업", W_)], F(GB, 40), 3)
    y += 56
    say(d, (x0 + 44, y), [("우대 지원", W_)], F(GB, 34), 2)
    y += 78
    say(d, (x0, y), [("= ", W_), ("중진공", Y_)], F(GB, 64), 4)
    return y


def grad(w, h, c0, c1, vertical=False):
    g = np.linspace(0, 1, h if vertical else w)
    g = g[:, None, None] if vertical else g[None, :, None]
    arr = np.array(c0) * (1 - g) + np.array(c1) * g
    arr = np.broadcast_to(arr, (h, w, 3))
    return Image.fromarray(np.dstack([arr, np.full((h, w, 1), 255)]).astype(np.uint8), "RGBA")


def card_A():
    """화이트 포토카드 — 흰 판, 위 연하늘 사진칸에 원색 로고."""
    c, m = rounded((CW, CH), 22, (255, 255, 255, 255))
    ph = grad(CW - 40, 150, (226, 238, 255), (246, 250, 255))
    c.alpha_composite(ph, (20, 20))
    lg = logo("full", 64)
    c.alpha_composite(lg, ((CW - lg.width) // 2, 20 + (150 - 64) // 2))
    body(ImageDraw.Draw(c), 48, 196)
    return c


def card_B():
    """사원증 — 흰 카드, 똑바로 내려온 목걸이 줄, 위 연한 브랜드 띠."""
    c, m = rounded((CW, CH), 26, (255, 255, 255, 255))
    band = grad(CW, 170, (214, 228, 255), (255, 236, 214))
    c.paste(band, (0, 0), m.crop((0, 0, CW, 170)))
    d = ImageDraw.Draw(c)
    d.rounded_rectangle([CW // 2 - 50, 20, CW // 2 + 50, 38], 9, fill=(240, 242, 246), outline=(200, 205, 215))
    lg = logo("full", 56)
    c.alpha_composite(lg, ((CW - lg.width) // 2, 78))
    d.rectangle([0, 170, CW, 174], fill=(47, 91, 208))
    body(d, 48, 204)
    full = Image.new("RGBA", (CW, CH + 130), (0, 0, 0, 0))
    fd = ImageDraw.Draw(full)
    for sgn in (-1, 1):
        fd.line([(CW // 2 + sgn * 34, 0), (CW // 2 + sgn * 34, 134)], fill=BLUE, width=20)
    fd.rounded_rectangle([CW // 2 - 50, 118, CW // 2 + 50, 160], 8, fill=(200, 205, 215))
    full.alpha_composite(c, (0, 130))
    return full


def card_C(bg):
    """밝은 유리 카드 — 뒤 화면을 흐리게 비추되 흰빛을 많이 섞어 밝게, 얇은 흰 테두리."""
    x, y = POS
    cr = bg.crop((x, y, x + CW, y + CH)).convert("RGBA").filter(ImageFilter.GaussianBlur(28))
    cr.alpha_composite(Image.new("RGBA", (CW, CH), (245, 248, 255, 190)))
    _, m = rounded((CW, CH), 30, (0, 0, 0, 0))
    cr.putalpha(m)
    d = ImageDraw.Draw(cr)
    d.rounded_rectangle([1, 1, CW - 2, CH - 2], 30, outline=(255, 255, 255, 255), width=3)
    lg = logo("full", 56)
    cr.alpha_composite(lg, ((CW - lg.width) // 2, 50))
    d.line([(48, 140), (CW - 48, 140)], fill=(200, 210, 230), width=2)
    body(d, 48, 172)
    return cr


def card_D():
    """미색 종이 + 마스킹테이프(똑바로) — 따뜻한 밝은 종이, 원색 로고."""
    c, m = rounded((CW, CH), 8, (252, 248, 238, 255))
    arr = np.asarray(c).astype(np.float32)
    arr[..., :3] += np.random.default_rng(3).normal(0, 4, (CH, CW, 1)).clip(-10, 10)
    c = Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(c)
    lg = logo("full", 56)
    c.alpha_composite(lg, ((CW - lg.width) // 2, 58))
    d.line([(48, 140), (CW - 48, 140)], fill=(222, 212, 190), width=2)
    body(d, 48, 172)
    full = Image.new("RGBA", (CW, CH + 24), (0, 0, 0, 0))
    full.alpha_composite(c, (0, 24))
    ImageDraw.Draw(full).rectangle([CW // 2 - 95, 0, CW // 2 + 95, 50], fill=(246, 222, 160, 215))
    return full


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    bg = Image.open(BG).convert("RGBA")
    cards = [("A_화이트포토카드", card_A()), ("B_사원증", card_B()), ("C_밝은유리", card_C(bg)), ("D_미색종이테이프", card_D())]
    shots = []
    for name, cd in cards:
        cd.save(OUT / f"{name}.png")
        sh, pad = shadow(cd, a=0.25 if name.startswith("C") else 0.35)
        fr = bg.copy()
        fr.alpha_composite(sh, (POS[0] - pad, POS[1] - pad - (cd.height - CH)))
        fr.convert("RGB").save(OUT / f"{name}_화면.png")
        shots.append((name, fr))
    sheet = Image.new("RGB", (1920, 1140), (20, 20, 24))
    for k, (name, fr) in enumerate(shots):
        x, y = (k % 2) * 960, (k // 2) * 570
        sheet.paste(fr.convert("RGB").resize((960, 540)), (x, y + 30))
        ImageDraw.Draw(sheet).text((x + 16, y + 2), name.replace("_", " "), font=F(GB, 24), fill=W_)
    sheet.save(OUT / "모아보기.png")
    print("→", OUT)


if __name__ == "__main__":
    main()
