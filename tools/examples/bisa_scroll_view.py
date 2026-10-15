# -*- coding: utf-8 -*-
r"""[레거시 — 10-13 부터 AE 안 씀. 새 장면은 html_motion(references/ae-replacement.md)]
빡이사DB 본편 17 «유튜브라든가 쇼츠라든가 릴스라든가 ~ 구조를 짜는 게 엄청 중요하다라는 거죠» (시퀀스 1478.293~1500.549)
사장님 10-08 «"이렇게"라는 표현을 쓰면서 손가락으로 방향을 알려 주거든, 그런 거 정합성 맞춰서 핸드폰으로 보는 화면 연출 ·
올리고 내리고 하는 연출이 대충 봐도 알 수 있을 정도의 시각화 · 시각화 표현 도구가 디자인이 너무 없어 보이지 않게».

구도: 사장님이 이 구간 사람(V2)을 전체 화면 50% 로 키워 두심 → 사람이 왼쪽 절반으로(크기 그대로), 오른쪽 판(12 반반 결).
  판 = 손에 든 휴대폰(보는 사람 화면, 소재/15/phone_cut.png) + 왼쪽 칸(로고 → 방향 카드).
  휴대폰 화면 안(SCR 프리컴프, 화면 흰 칸을 매트로): 광고 피드가 손짓 «세로»마다 위로 넘어감(손가락 터치 + 꼬리) ·
  손짓 «가로»에선 옆으로 밀렸다 튕겨 돌아오고(빨강), 글줄 지그재그(빨강) → 책 → 끝은 앞 맥락의 인사말 카드가 위에서 아래로 한 줄씩(파랑).
  색: 세로(익숙) = 파랑 · 가로(지루) = 빨강 — 비교는 쪽마다 색 하나(06 통과 때 말씀).

  python bisa_scroll_view.py [--조각만] [--소리만]
    → 빡이사DB\납품\17_위에서아래로_1478.29~.mp4 (사람 포함 → **V3**, 시작 1478.293 은 클립 가운데 — 끝 1500.549 컷 경계) · _효과음.xml · _미리보기.mp4
손짓(촬영본 0.25초 프레임, 기록.md 17): 세로 1483.18 · 1484.28 · 1487.18 / 가로 1485.14 · 1490.50
"""

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))   # tools/ (config.py)
import config  # noqa: E402
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(config.TOOLS))
import rf3_ae as AE  # noqa: E402
import rule_check  # noqa: E402
import lec_xml  # noqa: E402
import bisa_meta_sfx as SFX  # noqa: E402
import bisa_web_vs_instant as M  # noqa: E402
from bisa_toc_cards import by_name  # noqa: E402

M.T0, M.T1 = 1478.293, 1500.549
M.DUR = M.T1 - M.T0
# (시퀀스 시작, 끝, 녹화 소스 시각@시작, 사람 소스 시각@시작) — 사장님 컷 조각(10-08 10:23 자동저장본)
M.SEGS = [(1478.293, 1482.982, 2379.41 + 0.533, 2381.145 + 0.533), (1482.982, 1484.066, 2385.083, 2386.818),
          (1484.066, 1500.549, 2386.901, 2388.636)]
M.NAME = "17_위에서아래로"
M.SFX_DIR = (config.WORK / "효과음17")
M.WORK = (config.WORK / "빡이사" / "ae17")
W, H, FPS = M.W, M.H, M.FPS
T0, T1 = M.T0, M.T1
WORK = M.WORK
SRC = (config.ORIG_ROOT / "빡이사DB" / "소재")
PRET = str(config.FONTS["pretendard_bold"])
NOTO = str(config.FONTS["noto_sans_kr"])
SERIF = str(config.FONTS["noto_serif_kr"])
INK, GREY, BLUE, RED = (24, 27, 31), (110, 116, 124), (0, 100, 224), (214, 48, 40)
BLUE_BG, RED_BG = (228, 238, 253), (253, 232, 230)

# ── 시각(단어 시각, _tmp/w17/words.txt) ──
T_SPLIT, T_BACK = 1478.30, 1500.12
T_LOGO = [1478.62, 1479.32, 1480.12, 1481.30]                     # 유튜브 · 쇼츠 · 릴스 · 여러 가지 광고
T_Q = 1482.40                                                     # 어떻게 봐요?
T_SWIPE = [1483.18, 1484.28, 1487.18]                             # 세로 손짓(이렇게 보잖아요 · 이해되세요 · 이렇게 본단)
T_SIDE = 1485.14                                                  # 가로 손짓 «이렇게 보는 광고 없단»
T_NO = 1485.88                                                    # 없단
T_EYE = 1488.40                                                   # 눈은 익숙해요
T_PAGE = 1490.50                                                  # 가로 «이렇게 가면» → 글줄 페이지(옆에서 들어옴)
T_BORING = 1491.50                                                # 지루하다
T_BOOK = 1492.32                                                  # 책 보는 것 같다
T_PSY = 1495.06                                                   # 심리학적으로 그래요
T_FORM = 1496.84                                                  # 위에서 아래로
T_LINES = [1497.06, 1497.28, 1497.66, 1497.96]                    # 제목 · 1. · 2. · 버튼(아래로 한 줄씩)
T_STRUCT = 1498.16                                                # 구조를
T_KEY = 1499.10                                                   # 엄청 중요

# ── 판·휴대폰 배치 ──
PX = 900                                                          # 판 기준점(그림자 60 포함 왼쪽 끝) 화면 x — 종이는 960부터
PERSON_FULL, PERSON_HALF = (960, 540), (480, 540)                 # 사장님 V2: 4K 50% 가운데 → 왼쪽 절반
SP = 0.70                                                         # 휴대폰 사진 배율
SCR_IMG = (222, 166, 776, 1302)                                   # phone_cut.png 안 흰 화면 칸
SX0, SY0 = 1290, 80                                               # 화면 왼쪽 위(화면 좌표)
SW, SH = int(round((SCR_IMG[2] - SCR_IMG[0]) * SP)), int(round((SCR_IMG[3] - SCR_IMG[1]) * SP))
PHONE_XY = (SX0 - SCR_IMG[0] * SP, SY0 - SCR_IMG[1] * SP)
COL = (978, 1264)                                                 # 왼쪽 칸 x 범위(화면 좌표)
PIP, CAPTION = (0, 580, 720, 1080), (480, 900, 1440, 1080)
BOX = {}
LP = 50                                                           # 화면 왼쪽 여백 — 사진 속 손가락이 화면 왼쪽 아래(사진 x 222→250)를 덮음


def font(n, f=PRET, wght=None):
    ft = ImageFont.truetype(f, n)
    if wght:
        ft.set_variation_by_axes([wght])
    return ft


def tl(t, f):
    return ImageDraw.Draw(Image.new("RGBA", (1, 1))).textlength(t, font=f)


def save(name, im, xy=(0, 0)):
    im.save(WORK / f"{name}.png")
    BOX[name] = (int(round(xy[0])), int(round(xy[1])), im.width, im.height)


def shadowed(w, h, r, fill=(255, 255, 255), m=24, alpha=70, dy=10, blur=14):
    im = Image.new("RGBA", (w + 2 * m, h + 2 * m), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((m, m + dy, m + w, m + h + dy), r, fill=(10, 25, 60, alpha))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))
    ImageDraw.Draw(im).rounded_rectangle((m, m, m + w, m + h), r, fill=fill + (255,))
    return im, m


def pill(t, size, fg, bg, padx=22, h=None, f=None):
    f = f or font(size)
    w = int(tl(t, f)) + 2 * padx
    h = h or int(size * 1.8)
    im, m = shadowed(w, h, h // 2, bg, m=16, alpha=60, dy=6, blur=8)
    ImageDraw.Draw(im).text((m + w / 2, m + h / 2), t, font=f, fill=fg, anchor="mm")
    return im, m


def cover(src, w, h):
    im = Image.open(src).convert("RGB")
    s = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * s + 1), int(im.height * s + 1)), Image.LANCZOS)
    x, y = (im.width - w) // 2, int((im.height - h) * 0.35)
    return im.crop((x, y, x + w, y + h)).convert("RGBA")


# ── 판 ──
def panel_png():
    pn = Image.new("RGBA", (960 + 60, H), (0, 0, 0, 0))
    s3 = Image.new("RGBA", pn.size, (0, 0, 0, 0))
    ImageDraw.Draw(s3).rectangle((60, 0, 60 + 960, H), fill=(0, 0, 0, 110))
    pn.alpha_composite(s3.filter(ImageFilter.GaussianBlur(22)))
    g = np.linspace(0, 1, H)[:, None]
    top, bot = np.array([246, 248, 252]), np.array([226, 233, 244])
    body = (top * (1 - g) + bot * g)[:, None, :].repeat(960, 1)
    body = Image.fromarray(body.astype(np.uint8).reshape(H, 960, 3)).convert("RGBA")
    d = ImageDraw.Draw(body)
    for y in range(36, H, 36):                                    # 아주 연한 점 격자(HUD 결, 2-1 원칙 10)
        for x in range(36, 960, 36):
            d.point((x, y), fill=(200, 208, 222, 255))
    d.text((COL[0] - 960 + 4, 44), "보는 사람 화면", font=font(20, NOTO, 500), fill=(140, 148, 160), anchor="lm")
    d.line((COL[0] - 960 + 4, 62, COL[0] - 960 + 130, 62), fill=(190, 198, 212), width=2)
    pn.alpha_composite(body, (60, 0))
    save("panel", pn, (PX, 0))
    ph = Image.open(SRC / "15" / "phone_cut.png").convert("RGBA")
    ph = ph.resize((int(ph.width * SP), int(ph.height * SP)), Image.LANCZOS)
    save("phone", ph, PHONE_XY)
    # 화면 매트: 사진의 흰 화면 칸(둥근 모서리·노치 그대로)
    a = np.asarray(Image.open(SRC / "15" / "phone_cut.png").convert("RGBA")).astype(int)
    wmask = ((a[..., 0] > 236) & (a[..., 1] > 236) & (a[..., 2] > 236) & (a[..., 3] > 250)).astype(np.uint8) * 255
    mk = Image.fromarray(wmask[SCR_IMG[1]:SCR_IMG[3] + 1, SCR_IMG[0]:SCR_IMG[2] + 1]).resize((SW, SH), Image.LANCZOS)
    mk = mk.filter(ImageFilter.MinFilter(3))                      # 테두리 흰 띠 안쪽으로
    m = Image.new("RGBA", (SW, SH), (255, 255, 255, 0))
    m.putalpha(mk)
    save("matte", m, (SX0, SY0))


# ── 화면 안(SCR 좌표 0..SW × 0..SH) ──
FEEDS = [("feed_skin.png", "○○피부과", "맑은 피부, 상담부터 받아 보세요"),
         ("feed_interior.png", "○○인테리어", "30평 아파트 전체 리모델링"),
         ("feed_pilates.png", "○○필라테스", "1:1 체형 교정 체험 수업"),
         ("feed_bakery.png", "○○베이커리", "오늘 아침 구운 크루아상")]


def icon_heart(d, cx, cy, r, col):
    d.ellipse((cx - r, cy - r * 0.9, cx, cy + r * 0.1), outline=col, width=4)
    d.ellipse((cx, cy - r * 0.9, cx + r, cy + r * 0.1), outline=col, width=4)
    d.line(((cx - r * 0.93, cy - r * 0.2), (cx, cy + r)), fill=col, width=4)
    d.line(((cx + r * 0.93, cy - r * 0.2), (cx, cy + r)), fill=col, width=4)


def icon_bubble(d, cx, cy, r, col):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=col, width=4)
    d.line(((cx - r * 0.75, cy + r * 0.6), (cx - r * 1.05, cy + r * 1.1), (cx - r * 0.2, cy + r * 0.95)), fill=col, width=4)


def icon_send(d, cx, cy, r, col):
    pts = [(cx - r, cy - r * 0.2), (cx + r, cy - r), (cx + r * 0.1, cy + r), (cx - r * 0.15, cy + r * 0.05)]
    d.line(pts + [pts[0]], fill=col, width=4, joint="curve")


def feed_item(k):
    fn, name, cap = FEEDS[k]
    p = SRC / "17" / fn
    im = cover(p, SW, SH) if p.exists() else Image.new("RGBA", (SW, SH), (180, 190, 205, 255))
    g = np.zeros((SH, SW, 4), np.uint8)                            # 아래 어둡게(글 읽히게)
    ramp = np.clip((np.arange(SH) - SH * 0.55) / (SH * 0.45), 0, 1) ** 1.3 * 190
    g[..., 3] = ramp[:, None].astype(np.uint8)
    im.alpha_composite(Image.fromarray(g))
    top = np.zeros((SH, SW, 4), np.uint8)
    top[..., 3] = (np.clip(1 - np.arange(SH) / 150, 0, 1) * 90)[:, None].astype(np.uint8)
    im.alpha_composite(Image.fromarray(top))
    d = ImageDraw.Draw(im)
    wht = (255, 255, 255, 255)
    d.text((30, 58), "릴스" if k % 2 == 0 else "쇼츠", font=font(24), fill=wht, anchor="lm")
    for j, fn_ in enumerate((icon_heart, icon_bubble, icon_send)):   # 오른쪽 버튼(숫자 없음)
        fn_(d, SW - 34, SH - 330 + j * 74, 15, wht)
    av = cover(p, 44, 44) if p.exists() else Image.new("RGBA", (44, 44), (200, 200, 200, 255))
    mk = Image.new("L", (44, 44), 0)
    ImageDraw.Draw(mk).ellipse((0, 0, 43, 43), fill=255)
    im.paste(av, (LP, SH - 186), mk)
    d.ellipse((LP - 1, SH - 187, LP + 45, SH - 141), outline=wht, width=2)
    d.text((LP + 56, SH - 172), name, font=font(21), fill=wht, anchor="lm")
    d.text((LP + 56, SH - 150), "광고", font=font(16, NOTO, 500), fill=(230, 230, 230, 255), anchor="lm")
    d.text((LP, SH - 116), cap, font=font(18, NOTO, 500), fill=wht, anchor="lm")
    d.rounded_rectangle((LP, SH - 88, SW - 70, SH - 46), 10, outline=wht, width=2)
    d.text(((LP + SW - 70) / 2, SH - 67), "더 알아보기", font=font(18), fill=wht, anchor="mm")
    return im


PAGE_TXT = ("피부 고민 있으신 분들 많으시죠. 저희 병원은 여드름 흉터와 모공, 색소 고민을 오랫동안 연구해 왔고 "
            "많은 분들이 상담 후에 만족하셨습니다. 이번 달에는 신청만 하셔도 백화점 상품권을 드리고 첫 방문 고객님께는 "
            "이벤트 할인도 함께 진행하고 있으니 관심 있으신 분은 아래 버튼을 눌러 신청서를 작성해 주시면 담당 실장이 "
            "순서대로 연락을 드리고 피부 상태에 맞는 관리 방법을 자세히 안내해 드리겠습니다. 상담은 무료이며 부담 없이 "
            "문의 주셔도 됩니다. 자세한 일정과 가격은 상담 때 안내드립니다.")
PAGE_ROWS = []                                                     # 글줄 y(지그재그 맞춤)


def wrap(t, f, w):
    out, cur = [], ""
    for ch in t:
        if tl(cur + ch, f) > w:
            out.append(cur)
            cur = ch.lstrip()
        else:
            cur += ch
    return out + [cur] if cur else out


def page_img(book=False):
    bg = (246, 238, 222) if book else (255, 255, 255)
    im = Image.new("RGBA", (SW, SH), bg + (255,))
    d = ImageDraw.Draw(im)
    f = font(19, SERIF, 500) if book else font(19, NOTO, 500)
    if not book:
        d.text((LP, 62), "광고", font=font(16, NOTO, 600), fill=GREY, anchor="lm")
        d.text((LP, 98), "○○피부과 안내", font=font(24), fill=INK, anchor="lm")
    else:
        d.text((SW / 2, 74), "— 12 —", font=font(16, SERIF, 500), fill=(150, 130, 100), anchor="mm")
        for x in range(0, 14):                                    # 왼쪽 접힘 그늘
            d.line((x, 0, x, SH), fill=(int(bg[0] - (14 - x) * 3), int(bg[1] - (14 - x) * 3), int(bg[2] - (14 - x) * 3), 255))
    rows = wrap(PAGE_TXT, f, SW - LP - 22)
    PAGE_ROWS.clear()
    y = 142
    for r in rows:
        d.text((LP, y), r, font=f, fill=(60, 52, 40, 255) if book else (55, 60, 66, 255), anchor="lm")
        PAGE_ROWS.append(y)
        y += 36
    return im


def form_parts():
    """앞 맥락(1456~1472) 녹화 화면 인사말 카드 — 위에서 아래로 한 줄씩."""
    bg = Image.new("RGBA", (SW, SH), (238, 241, 246, 255))
    card_w, card_h = SW - LP - 14, 470
    c, m = shadowed(card_w, card_h, 18, m=18, alpha=50, dy=6, blur=10)
    cy0 = 170
    bg.alpha_composite(c, (LP - 4 - m, cy0 - m))
    CX = LP - 4 + card_w / 2                                       # 카드 가운데 x
    d = ImageDraw.Draw(bg)
    save("s_formbg", bg)
    parts = []
    p = SRC / "17" / "feed_skin.png"
    av = cover(p, 76, 76) if p.exists() else Image.new("RGBA", (76, 76), (220, 200, 200, 255))
    mk = Image.new("L", (76, 76), 0)
    ImageDraw.Draw(mk).ellipse((0, 0, 75, 75), fill=255)
    a = Image.new("RGBA", (80, 80), (0, 0, 0, 0))
    a.paste(av, (2, 2), mk)
    parts.append(("s_f0", a, (CX - 40, cy0 + 24)))
    for nm, t, f, col, y in (("s_f1", "피부 여신이 되는 방법", font(23), INK, cy0 + 150),
                             ("s_f2", "1. 신청만 하셔도 백화점 상품권 지급!", font(16, NOTO, 600), (50, 55, 62), cy0 + 222),
                             ("s_f3", "2. 첫 방문 이벤트 10만원 할인", font(16, NOTO, 600), (50, 55, 62), cy0 + 270)):
        w = int(tl(t, f)) + 8
        im = Image.new("RGBA", (w, 44), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((4, 22), t, font=f, fill=col + (255,), anchor="lm")
        parts.append((nm, im, (LP + 40, y - 22)))                 # 줄 머리 맞춤(왼쪽 화살표 옆)
    b = Image.new("RGBA", (card_w - 60, 52), (0, 0, 0, 0))
    ImageDraw.Draw(b).rounded_rectangle((0, 0, card_w - 61, 51), 12, fill=BLUE + (255,))
    ImageDraw.Draw(b).text(((card_w - 60) / 2, 26), "다음", font=font(20), fill=(255, 255, 255, 255), anchor="mm")
    parts.append(("s_f4", b, (CX - (card_w - 60) / 2, cy0 + 360)))
    for nm, im, xy in parts:
        save(nm, im, xy)
    # 왼쪽 여백의 파란 «아래로» 화살표(카드 줄을 따라)
    hgt = 190
    ar = Image.new("RGBA", (40, hgt), (0, 0, 0, 0))
    d = ImageDraw.Draw(ar)
    d.line((20, 4, 20, hgt - 26), fill=BLUE + (255,), width=6)
    d.polygon([(4, hgt - 30), (36, hgt - 30), (20, hgt - 2)], fill=BLUE + (255,))
    save("s_fdown", ar, (LP + 4, cy0 + 128))
    # 강조(구조): 세 줄을 감싸는 파란 테두리
    im = Image.new("RGBA", (card_w - 12, 200), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((3, 3, card_w - 16, 196), 14, outline=BLUE + (255,), width=4)
    save("s_fbox", im, (LP - 4 + 6, cy0 + 112))


def zig_parts():
    """글줄 따라 왼쪽→오른쪽으로 훑는 빨간 눈길(줄마다 한 장) + 다음 줄로 꺾는 사선."""
    for k, y in enumerate(PAGE_ROWS[:8]):
        im = Image.new("RGBA", (SW - 30, 16), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.line((4, 8, SW - 52, 8), fill=RED + (175,), width=3)
        d.polygon([(SW - 54, 1), (SW - 54, 15), (SW - 36, 8)], fill=RED + (220,))
        save(f"s_z{k}", im, (LP - 8, y + 9))
        if k < 7:
            r = Image.new("RGBA", (SW - 40, 40), (0, 0, 0, 0))
            ImageDraw.Draw(r).line((SW - 50, 4, 10, 34), fill=RED + (110,), width=3)
            save(f"s_zr{k}", r, (LP - 4, y + 16))


def touch_parts():
    im = Image.new("RGBA", (90, 90), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((12, 12, 78, 78), fill=(255, 255, 255, 120), outline=(255, 255, 255, 235), width=4)
    save("s_touch", im)
    tr = Image.new("RGBA", (40, 260), (0, 0, 0, 0))
    a = np.zeros((260, 40), np.uint8)
    yy, xx = np.mgrid[0:260, 0:40]
    a[((xx - 20) ** 2 < (14 * (yy / 260)) ** 2 + 1)] = 1
    al = (a * (yy / 260) * 150).astype(np.uint8)
    tr.putalpha(Image.fromarray(al))
    save("s_trail", tr)
    tint = Image.new("RGBA", (SW, SH), RED + (70,))
    save("s_redtint", tint)
    # 눈길(세로, 파랑) — 화면 가운데 위→아래
    ey = Image.new("RGBA", (60, SH - 220), (0, 0, 0, 0))
    d = ImageDraw.Draw(ey)
    for y in range(6, SH - 270, 26):
        d.rounded_rectangle((26, y, 34, y + 14), 4, fill=BLUE + (230,))
    d.polygon([(8, SH - 262), (52, SH - 262), (30, SH - 226)], fill=BLUE + (240,))
    save("s_eye", ey, (SW / 2 - 30, 120))


def screen_parts():
    strip = Image.new("RGBA", (SW, SH * 4), (0, 0, 0, 255))
    for k in range(4):
        strip.alpha_composite(feed_item(k), (0, k * SH))
    save("s_strip", strip)
    save("s_page", page_img(False))
    save("s_book", page_img(True))
    zig_parts()
    touch_parts()
    form_parts()


# ── 왼쪽 칸(화면 좌표) ──
def column_parts():
    cw = COL[1] - COL[0]
    logos = [("10/logo_youtube.png", "유튜브"), ("17/logo_shorts.png", "쇼츠"), ("17/logo_instagram.png", "릴스"), (None, "여러 가지 광고")]
    for k, (lp, t) in enumerate(logos):
        im, m = shadowed(cw, 92, 20)
        d = ImageDraw.Draw(im)
        if lp:
            lg = Image.open(SRC / lp).convert("RGBA")
            lg.thumbnail((60, 50), Image.LANCZOS)
            im.alpha_composite(lg, (m + 26 + (60 - lg.width) // 2, m + 46 - lg.height // 2))
            d.text((m + 108, m + 46), t, font=font(32), fill=INK, anchor="lm")
        else:
            d.text((m + cw / 2, m + 46), t, font=font(30), fill=INK, anchor="mm")
        save(f"logo{k}", im, (COL[0] - m, 150 + k * 112 - m))
    im, m = pill("어떻게 봐요?", 34, (255, 255, 255), INK, padx=28, h=66)
    save("q", im, ((COL[0] + COL[1]) / 2 - im.width / 2, 150 + 4 * 112 + 4 - m))
    # 방향 카드: 세로(파랑) / 가로(빨강)
    for nm, col, bgc, title, sub in (("dirV", BLUE, BLUE_BG, "위아래로", "스크롤해서 봐요"), ("dirH", RED, RED_BG, "옆으로", "왼쪽 → 오른쪽")):
        im, m = shadowed(cw, 400, 26)
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((m + 18, m + 18, m + cw - 18, m + 262), 20, fill=bgc + (255,))
        d.text((m + cw / 2, m + 312), title, font=font(42), fill=col, anchor="mm")
        d.text((m + cw / 2, m + 360), sub, font=font(22, NOTO, 500), fill=GREY, anchor="mm")
        save(nm, im, (COL[0] - m, 230 - m))
    # 카드 안 큰 화살표(따로 — 그 방향으로 계속 흐름)
    for nm, col, vert in (("arrV", BLUE, True), ("arrH", RED, False)):
        L, Wd = 170, 26
        im = Image.new("RGBA", (L + 20, L + 20), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        c = (L + 20) / 2
        if vert:
            d.line((c, 14, c, L - 36), fill=col + (255,), width=Wd)
            d.polygon([(c - 46, L - 56), (c + 46, L - 56), (c, L + 6)], fill=col + (255,))
            d.ellipse((c - Wd / 2, 14 - Wd / 2, c + Wd / 2, 14 + Wd / 2), fill=col + (255,))
        else:
            d.line((14, c, L - 36, c), fill=col + (255,), width=Wd)
            d.polygon([(L - 56, c - 46), (L - 56, c + 46), (L + 6, c)], fill=col + (255,))
            d.ellipse((14 - Wd / 2, c - Wd / 2, 14 + Wd / 2, c + Wd / 2), fill=col + (255,))
        save(nm, im, ((COL[0] + COL[1]) / 2 - im.width / 2, 230 + 140 - im.height / 2))
    # ✕ / ✓ 배지(글꼴 대신 선으로)
    for nm, col, ok in (("badgeX", RED, False), ("badgeV", BLUE, True)):
        im = Image.new("RGBA", (84, 84), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.ellipse((4, 4, 80, 80), fill=col + (255,), outline=(255, 255, 255, 255), width=5)
        if ok:
            d.line(((24, 44), (37, 57), (61, 30)), fill=(255, 255, 255, 255), width=9, joint="curve")
        else:
            d.line((27, 27, 57, 57), fill=(255, 255, 255, 255), width=9)
            d.line((57, 27, 27, 57), fill=(255, 255, 255, 255), width=9)
        save(nm, im, (COL[1] - 66, 230 - 18))
    # 아래 알약(말 그대로·짧게)
    for nm, t, fg, bg in (("p_no", "이런 광고 없어요", (255, 255, 255), RED), ("p_eye", "눈은 이게 익숙해요", (255, 255, 255), BLUE),
                          ("p_boring", "지루하다", (255, 255, 255), RED), ("p_book", "책 보는 것 같다", (255, 255, 255), RED),
                          ("p_psy", "심리학적으로 그래요", INK, (255, 255, 255)), ("p_key", "구조가 엄청 중요!", (255, 255, 255), BLUE)):
        im, m = pill(t, 26, fg, bg, padx=22, h=54)
        save(nm, im, ((COL[0] + COL[1]) / 2 - im.width / 2, 662 - m))
    im, m = pill("위에서 아래로", 26, BLUE, (255, 255, 255), padx=22, h=54)
    save("p_down", im, ((COL[0] + COL[1]) / 2 - im.width / 2, 662 - m))
    # 반짝 선(13 2판 강조 포인트)
    n = 104
    sp = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(sp)
    for ang in (-90, -45, 0):
        r0, r1 = 30, 70 if ang == -45 else 58
        c_, s_ = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        p0, p1 = (8 + r0 * c_, n - 8 + r0 * s_), (8 + r1 * c_, n - 8 + r1 * s_)
        d.line((p0, p1), fill=BLUE + (255,), width=9)
        for q in (p0, p1):
            d.ellipse((q[0] - 4, q[1] - 4, q[0] + 4, q[1] + 4), fill=BLUE + (255,))
    save("spark", sp)


def check_layout():
    bad = []
    for n, (x, y, w, h) in BOX.items():
        if n.startswith("s_") or n in ("panel", "phone", "matte", "spark"):
            continue
        im = np.asarray(Image.open(WORK / f"{n}.png"))[..., 3] > 60
        ys, xs = np.where(im)
        b = (x + xs.min(), y + ys.min(), x + xs.max(), y + ys.max())
        if b[0] < 960 or b[2] > W - 10 or b[1] < 10:
            bad.append(f"{n} {b} 판 밖")
        if b[0] < CAPTION[2] and b[3] > CAPTION[1]:
            bad.append(f"{n} {b} ↔ 자막")
        if b[2] > SX0 - 8 and b[0] < SX0 + SW:
            bad.append(f"{n} {b} ↔ 휴대폰 화면")
    if bad:
        raise SystemExit("레이아웃 겹침:\n  " + "\n  ".join(bad))
    print("겹침 없음")


def pieces():
    WORK.mkdir(parents=True, exist_ok=True)
    BOX.clear()
    panel_png()
    screen_parts()
    column_parts()
    check_layout()


# ── 애펙 ───────────────────────────────────────────────────────
def jsx(out_mov):
    js = AE.js
    s = lambda t: round(t - T0, 4)                         # noqa: E731
    L = ["function eo(p){ for(var k=1;k<=p.numKeys;k++){ var n=p.isSpatial?1:(p.value.length||1), o=[], i=[]; for(var j=0;j<n;j++){ o.push(new KeyframeEase(0,0.1)); i.push(new KeyframeEase(0,85)); } p.setTemporalEaseAtKey(k,i,o); } }",
         "function hold(p){ for(var q=1;q<=p.numKeys;q++){ p.setInterpolationTypeAtKey(q,KeyframeInterpolationType.HOLD); } }",
         f"(function(){{ var comp=app.project.items.addComp('bisa17',{W},{H},1,{M.DUR:.3f},{FPS}); comp.motionBlur=true;",
         f"var scr=app.project.items.addComp('bisa17_screen',{SW},{SH},1,{M.DUR:.3f},{FPS}); scr.motionBlur=true;"]
    a = L.append
    nv = [0]

    def lay(name, cmp="comp", parent=None, anchor=None):
        nv[0] += 1
        v = f"L{nv[0]}"
        x, y, w, h = BOX[name]
        a(f"var {v}={cmp}.layers.add(imp({js(str(WORK / f'{name}.png'))})); {v}.motionBlur=true;")
        if parent:
            a(f"{v}.parent={parent}; {v}.transform.scale.setValue([100,100]);")
            x -= PX
        if anchor:
            a(f"{v}.transform.anchorPoint.setValue([{anchor[0]},{anchor[1]}]); {v}.transform.position.setValue([{x + anchor[0]:.1f},{y + anchor[1]:.1f}]);")
        else:
            a(f"{v}.transform.position.setValue([{x + w / 2:.1f},{y + h / 2:.1f}]);")
        return v

    def center(name, parent=False):
        x, y, w, h = BOX[name]
        return (x + w / 2 - (PX if parent else 0), y + h / 2)

    def opa(v, k, hold_=False):
        a(f"keys({v}.transform.opacity,{k});")
        if hold_:
            a(f"hold({v}.transform.opacity);")

    def life(t_in, t_out, fi=0.14, fo=0.2):
        return [[max(0, s(t_in) - 0.001), 0], [s(t_in) + fi, 100], [s(t_out), 100], [s(t_out) + fo, 0]]

    def pop(v, t, frm=72, dur=0.22):
        a(f"keys({v}.transform.scale,[[{s(t)},[{frm},{frm}]],[{s(t) + dur:.3f},[100,100]]]); eo({v}.transform.scale);")

    def slide(v, name, t, dx=0, dy=24, dur=0.28, parent=True):
        cx, cy = center(name, parent)
        a(f"keys({v}.transform.position,[[{s(t)},[{cx + dx:.1f},{cy + dy:.1f}]],[{s(t) + dur:.3f},[{cx:.1f},{cy:.1f}]]]); eo({v}.transform.position);")

    def spark_at(name, t, parent="PN"):
        x, y, w, h = BOX[name]
        v = lay("spark", parent=parent, anchor=(8, 96))
        a(f"{v}.transform.position.setValue([{x + w - 30 - PX:.1f},{y + 22:.1f}]);")
        a(f"keys({v}.transform.opacity,[[{s(t) - 0.001:.3f},0],[{s(t) + 0.03:.3f},100],[{s(t) + 0.3:.3f},100],[{s(t) + 0.48:.3f},0]]);")
        a(f"keys({v}.transform.scale,[[{s(t)},[35,35]],[{s(t) + 0.16:.3f},[100,100]],[{s(t) + 0.48:.3f},[115,115]]]); eo({v}.transform.scale);")

    # ── 화면 안(scr) ── 아래부터 쌓음
    v = lay("s_strip", "scr")
    ys = [SH * 2 - k * SH for k in range(4)]                      # 띠 가운데 y(0번 피드가 보일 때 = 2·SH)
    k_ = [[0, [SW / 2, ys[0]]]]
    cur = 0
    for t in T_SWIPE:
        k_ += [[s(t), [SW / 2, ys[cur]]], [s(t) + 0.45, [SW / 2, ys[cur + 1]]]]
        cur += 1
        if t == T_SWIPE[1]:                                        # 가로 손짓: 옆으로 밀렸다 돌아옴(넘어가지 않음)
            k_ += [[s(T_SIDE), [SW / 2, ys[cur]]], [s(T_SIDE) + 0.35, [SW / 2 - 120, ys[cur]]], [s(T_SIDE) + 0.75, [SW / 2, ys[cur]]]]
    k_.sort(key=lambda r: r[0])
    a(f"keys({v}.transform.position,{k_}); eo({v}.transform.position);")
    strip = v
    v = lay("s_redtint", "scr"); opa(v, [[s(T_SIDE), 0], [s(T_SIDE) + 0.3, 100], [s(T_NO) + 0.5, 100], [s(T_NO) + 0.9, 0]])
    # 손가락 터치(세로 스와이프마다: 아래에서 위로 끌어올림)
    for t in T_SWIPE:
        tv = lay("s_trail", "scr", anchor=(20, 0))
        a(f"keys({tv}.transform.position,[[{s(t) - 0.08:.3f},[{SW * 0.62:.1f},{SH * 0.74:.1f}]],[{s(t) + 0.36:.3f},[{SW * 0.62:.1f},{SH * 0.30:.1f}]]]); eo({tv}.transform.position);")
        opa(tv, [[s(t) - 0.08, 0], [s(t) + 0.02, 100], [s(t) + 0.36, 100], [s(t) + 0.56, 0]])
        dv = lay("s_touch", "scr")
        a(f"keys({dv}.transform.position,[[{s(t) - 0.08:.3f},[{SW * 0.62:.1f},{SH * 0.74:.1f}]],[{s(t) + 0.36:.3f},[{SW * 0.62:.1f},{SH * 0.30:.1f}]]]); eo({dv}.transform.position);")
        opa(dv, [[s(t) - 0.12, 0], [s(t) - 0.04, 100], [s(t) + 0.38, 100], [s(t) + 0.56, 0]])
        a(f"keys({dv}.transform.scale,[[{s(t) - 0.12:.3f},[130,130]],[{s(t) - 0.02:.3f},[100,100]]]);")
    # 가로 손짓: 터치가 옆으로 밀고 돌아옴
    tv = lay("s_touch", "scr")
    a(f"keys({tv}.transform.position,[[{s(T_SIDE) - 0.05:.3f},[{SW * 0.72:.1f},{SH * 0.55:.1f}]],[{s(T_SIDE) + 0.35:.3f},[{SW * 0.30:.1f},{SH * 0.55:.1f}]]]); eo({tv}.transform.position);")
    opa(tv, [[s(T_SIDE) - 0.1, 0], [s(T_SIDE) - 0.02, 100], [s(T_SIDE) + 0.36, 100], [s(T_SIDE) + 0.55, 0]])
    # 눈길(세로) «눈은 이게 익숙해요»
    v = lay("s_eye", "scr", anchor=(30, 0))
    a(f"keys({v}.transform.scale,[[{s(T_EYE)},[100,0]],[{s(T_EYE) + 0.7:.3f},[100,100]]]); eo({v}.transform.scale);")
    opa(v, life(T_EYE, T_PAGE - 0.3, fi=0.1, fo=0.25))
    # 글줄 페이지: 옆에서 들어옴(가로 손짓) → 지그재그 → 책
    v = lay("s_page", "scr")
    a(f"keys({v}.transform.position,[[{s(T_PAGE)},[{SW * 1.5:.1f},{SH / 2:.1f}]],[{s(T_PAGE) + 0.42:.3f},[{SW / 2:.1f},{SH / 2:.1f}]]]); eo({v}.transform.position);")
    opa(v, [[s(T_PAGE) - 0.01, 0], [s(T_PAGE), 100], [s(T_FORM) + 0.5, 100], [s(T_FORM) + 0.51, 0]], hold_=True)
    v = lay("s_book", "scr"); opa(v, [[s(T_BOOK), 0], [s(T_BOOK) + 0.35, 100], [s(T_FORM) + 0.5, 100], [s(T_FORM) + 0.51, 0]])
    a(f"keys({v}.transform.scale,[[{s(T_BOOK)},[104,104]],[{s(T_BOOK) + 0.35:.3f},[100,100]]]); eo({v}.transform.scale);")
    nz = len([n for n in BOX if n.startswith("s_z") and not n.startswith("s_zr")])
    t = T_PAGE + 0.55
    step = (T_PSY + 0.6 - t) / nz                                  # 줄마다 왼쪽→오른쪽으로 훑고 다음 줄로
    for k in range(nz):
        v = lay(f"s_z{k}", "scr")
        a(f"var e{v}={v}.Effects.addProperty('ADBE Linear Wipe'); e{v}.property(2).setValue(270); e{v}.property(3).setValue(10); keys(e{v}.property(1),[[{s(t)},100],[{s(t) + step * 0.8:.3f},0]]);")
        opa(v, [[s(t) - 0.01, 0], [s(t), 100], [s(T_FORM) + 0.1, 100], [s(T_FORM) + 0.3, 0]])
        if f"s_zr{k}" in BOX and k < nz - 1:
            r = lay(f"s_zr{k}", "scr"); opa(r, [[s(t + step * 0.8), 0], [s(t + step * 0.95), 100], [s(T_FORM) + 0.1, 100], [s(T_FORM) + 0.3, 0]])
        t += step
    # 인사말 카드: 아래에서 위로 올라옴 → 위에서 아래로 한 줄씩
    v = lay("s_formbg", "scr")
    a(f"keys({v}.transform.position,[[{s(T_FORM)},[{SW / 2:.1f},{SH * 1.5:.1f}]],[{s(T_FORM) + 0.45:.3f},[{SW / 2:.1f},{SH / 2:.1f}]]]); eo({v}.transform.position);")
    opa(v, [[s(T_FORM) - 0.01, 0], [s(T_FORM), 100]], hold_=True)
    for nm, tt in zip(("s_f0", "s_f1", "s_f2", "s_f3", "s_f4"), [T_FORM + 0.3] + T_LINES):
        v = lay(nm, "scr"); opa(v, life(tt, T1, fi=0.12)); slide(v, nm, tt, dy=-16, parent=False)
    v = lay("s_fdown", "scr", anchor=(20, 0))
    a(f"keys({v}.transform.scale,[[{s(T_LINES[0])},[100,0]],[{s(T_LINES[3]) + 0.3:.3f},[100,100]]]);")
    opa(v, life(T_LINES[0], T1, fi=0.05))
    v = lay("s_fbox", "scr"); opa(v, life(T_STRUCT, T1, fi=0.1)); pop(v, T_STRUCT, 94, 0.25)

    # ── 본 화면 ── 녹화(사람 밑, 안 보임) · 사람 · 판
    a(f"var cv=imp({js(str(M.CAM))});")
    for i, (ta, tb, _, cs) in enumerate(M.SEGS):
        v = f"C{i}"
        a(f"var {v}=comp.layers.add(cv); {v}.startTime={s(ta) - cs:.4f}; {v}.inPoint={s(ta):.4f}; {v}.outPoint={s(tb):.4f}; {v}.audioEnabled=false; {v}.transform.scale.setValue([50,50]);")
        a(f"keys({v}.transform.position,[[{s(T_SPLIT)},[{PERSON_FULL[0]},{PERSON_FULL[1]}]],[{s(T_SPLIT) + 0.45:.3f},[{PERSON_HALF[0]},{PERSON_HALF[1]}]],[{s(T_BACK)},[{PERSON_HALF[0]},{PERSON_HALF[1]}]],[{s(T_BACK) + 0.36:.3f},[{PERSON_FULL[0]},{PERSON_FULL[1]}]]]); ez({v}.transform.position);")
    a(f"var PN=comp.layers.add(imp({js(str(WORK / 'panel.png'))})); PN.transform.anchorPoint.setValue([0,540]);")
    a(f"keys(PN.transform.position,[[{s(T_SPLIT)},[{W},540]],[{s(T_SPLIT) + 0.45:.3f},[{PX},540]],[{s(T_BACK)},[{PX},540]],[{s(T_BACK) + 0.36:.3f},[{W + 40},540]]]); ez(PN.transform.position);")
    a("PN.moveToBeginning();")
    lay("phone", parent="PN")
    x, y, w, h = BOX["matte"]
    a(f"var SL=comp.layers.add(scr); SL.parent=PN; SL.transform.scale.setValue([100,100]); SL.transform.position.setValue([{x + w / 2 - PX:.1f},{y + h / 2:.1f}]);")
    v = lay("matte", parent="PN")
    a(f"try{{ SL.setTrackMatte({v}, TrackMatteType.ALPHA); {v}.enabled=false; }}catch(e){{ {v}.moveBefore(SL); SL.trackMatteType=TrackMatteType.ALPHA; }}")

    # 왼쪽 칸: 로고 넷 → «어떻게 봐요?» → 방향 카드
    for k, t in enumerate(T_LOGO):
        v = lay(f"logo{k}", parent="PN"); opa(v, life(t, T_SWIPE[0] - 0.25, fo=0.25)); slide(v, f"logo{k}", t, dx=-30, dy=0)
        a(f"keys({v}.transform.position,[[{s(T_SWIPE[0] - 0.25):.3f},[{center(f'logo{k}', True)[0]:.1f},{center(f'logo{k}', True)[1]:.1f}]],[{s(T_SWIPE[0] + 0.05):.3f},[{center(f'logo{k}', True)[0]:.1f},{center(f'logo{k}', True)[1] - 40:.1f}]]]);")
    v = lay("q", parent="PN"); opa(v, life(T_Q, T_SWIPE[0] - 0.25, fo=0.25)); pop(v, T_Q)
    # 방향 카드: 손짓마다 뒤집혀(가로 크기 100→0→100) 바뀜 — 같은 카드가 모양을 바꾸며(2-1 원칙 8)
    STATES = [(T_SWIPE[0], "V"), (T_SIDE, "H"), (T_SWIPE[2], "V"), (T_PAGE, "H"), (T_FORM, "V")]
    for j, (t, d_) in enumerate(STATES):
        t_end = STATES[j + 1][0] if j + 1 < len(STATES) else T_BACK
        for nm in (f"dir{d_}", f"arr{d_}"):
            v = lay(nm, parent="PN")
            first = j == 0
            k_ = [[s(t) - 0.001, 0], [s(t), 100], [s(t_end), 100], [s(t_end) + 0.001, 0]]
            opa(v, k_, hold_=True)
            sk = [[s(t), [0 if not first else 80, 100 if not first else 80]], [s(t) + 0.16, [100, 100]]]
            if j + 1 < len(STATES):
                sk += [[s(t_end) - 0.16, [100, 100]], [s(t_end), [0, 100]]]
            a(f"keys({v}.transform.scale,{sk}); eo({v}.transform.scale);")
            if nm.startswith("arr"):                               # 화살표가 그 방향으로 계속 흐름(조용히)
                axis = 1 if d_ == "V" else 0
                a(f"{v}.transform.position.expression={js(f'var u=(time*1.6)%1; var o=u*28-14; var p=value; p[{axis}]+=o; p')};")
                a(f"{v}.transform.opacity.expression={js('var u=(time*1.6)%1; value*(u<0.15?u/0.15:(u>0.85?(1-u)/0.15:1))*0.6+value*0.4')};")
    # 배지·알약
    for nm, t, t_end in (("badgeX", T_NO, T_SWIPE[2] - 0.16), ("badgeV", T_EYE, T_PAGE - 0.16), ("badgeX", T_BORING, T_FORM - 0.16), ("badgeV", T_KEY, T_BACK)):
        v = lay(nm, parent="PN"); opa(v, life(t, t_end, fi=0.08, fo=0.1)); pop(v, t, 40, 0.2)
    for nm, t, t_end in (("p_no", T_NO, T_SWIPE[2] - 0.2), ("p_eye", T_EYE, T_PAGE - 0.2), ("p_boring", T_BORING, T_BOOK),
                         ("p_book", T_BOOK, T_PSY), ("p_psy", T_PSY, T_FORM - 0.2), ("p_down", T_FORM + 0.2, T_KEY), ("p_key", T_KEY, T_BACK)):
        v = lay(nm, parent="PN")
        opa(v, life(t, t_end, fi=0.1, fo=0.12 if nm in ("p_boring", "p_book", "p_down") else 0.2))
        pop(v, t)
        slide(v, nm, t, dy=18)
    spark_at("p_key", T_KEY + 0.08)
    spark_at("p_eye", T_EYE + 0.08)
    a(f"var rq=app.project.renderQueue.items.add(comp); var om=rq.outputModule(1); om.applyTemplate({js('고품질')}); om.file=new File({js(str(out_mov))});")
    a("log('ok bisa17'); })();")
    assert T_BACK + 0.36 < T1
    return "\n".join(L)


# ── 효과음 ── 이름 고정(크기 = bisa_meta_sfx.FILE_DB 우선, 없는 파일 기본 +5)
SND_FIX = {
    "split": ("휙２.mp3", 0.6, 4, "peak"),
    "c1":    ("ML_Cartoon bubbles popping.wav", 0.5, 5, "onset"),
    "st1":   ("KN_pepSound1.wav", 0.4, 8, "onset"),
    "st2":   ("KN_pepSound2.wav", 0.4, 8, "onset"),
    "q":     ("채팅 효과음.mp3", 0.6, 5, "onset"),                     # 어떻게 봐요?
    "sw1":   ("ML_Fast small sweep transition.wav", 0.6, 5, "onset"),  # 세로 스와이프(새 파일)
    "sw2":   ("ML_Fast air sweep transition.wav", 0.6, 5, "onset"),
    "no":    ("KN_error_003.wav", 0.5, 5, "onset"),                    # 이런 광고 없어요
    "ok":    ("맑은소리.mp3", 0.8, 7, "onset"),                        # 눈은 익숙해요
    "side":  ("ML_Fast sweep transition.wav", 0.6, 5, "onset"),        # 글줄 페이지 옆에서
    "book":  ("ML_Page turn chime.wav", 1.0, 5, "onset"),              # 책
    "key":   ("SEL_キラッ1.mp3", 0.7, -1, "onset"),                    # 구조가 엄청 중요
    "back":  ("휙1.mp3", 0.7, 8, "peak"),
}
EVENTS = [(T_SPLIT + 0.25, "split"), (T_LOGO[0], "c1"), (T_LOGO[1], "st1"), (T_LOGO[2], "st2"), (T_LOGO[3], "c1"), (T_Q, "q"),
          (T_SWIPE[0], "sw1"), (T_SWIPE[1], "sw2"), (T_SIDE, "side"), (T_NO, "no"), (T_SWIPE[2], "sw1"), (T_EYE, "ok"),
          (T_PAGE, "side"), (T_BORING, "no"), (T_BOOK, "book"), (T_PSY, "st1"), (T_FORM, "sw2"), (T_LINES[1], "st2"),
          (T_LINES[2], "st1"), (T_KEY, "key"), (T_BACK + 0.2, "back")]
EVENTS.sort()


def sfx(scene):
    snd = {k: SFX.role(by_name(f), mx, rel, al) for k, (f, mx, rel, al) in SND_FIX.items()}
    SFX.SND.clear()
    SFX.SND.update(snd)
    v = M.voice()
    f = SFX.rms_frames(v)
    ref = float(np.median(f[f > f.max() - 25]))
    M.SFX_DIR.mkdir(parents=True, exist_ok=True)
    cache, placed, mix = {}, [], np.zeros_like(v)
    for k, (t, name) in enumerate(EVENTS):
        if name not in cache:
            cache[name] = SFX.prep(name, ref)
        x, peak_at = cache[name]
        start = t - (peak_at if snd[name][5] == "peak" else 0.0)
        fp = M.SFX_DIR / f"{k + 1:02d}_{name}.wav"
        SFX.write_wav(fp, x)
        placed.append((round(start, 3), fp, name))
        i = int((start - T0) * SFX.SR)
        seg = x[: len(mix) - i]
        mix[i: i + len(seg)] += seg
        print(f"  {start:7.2f}s  {name:6s} {snd[name][0].name}  {snd[name][4]:+d}dB  {len(x) / SFX.SR:.2f}s")
    bad = [it for it in rule_check.check_sfx([(t - T0, snd[n][0], len(cache[n][0]) / SFX.SR) for t, _, n in placed], T1 - T0) if it[0] == "ERROR"]
    for it in bad:
        print(*it)
    if bad:
        sys.exit(1)
    tmp = M.SFX_DIR / "_미리듣기소리.wav"
    both = v * 10 ** (7 / 20) + mix * 10 ** (7 / 20)
    both *= min(1.0, 0.8 / (np.abs(both).max() + 1e-9))
    SFX.write_wav(tmp, both)
    pre = M.OUT / f"{M.NAME}_미리보기.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(scene), "-i", str(tmp), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", "alimiter=limit=0.84:level=false", "-c:a", "aac", "-b:a", "256k", "-shortest", str(pre)], check=True)
    tmp.unlink()
    lec_xml.V_TRACK, lec_xml.A_TRACK = 3, 2                 # 장면 = 사람 포함 → V3(사장님 V2 사람을 덮음)
    print(lec_xml.write(M.OUT / f"{M.NAME}_효과음.xml", f"빡이사DB_{M.NAME}", scene, M.DUR, T0,
                        [(t, f) for t, f, _ in placed], 59.94, tag="bs17"))
    return pre


if __name__ == "__main__":
    M.pieces = pieces
    M.jsx = jsx
    WORK.mkdir(parents=True, exist_ok=True)
    scene = M.OUT / f"{M.NAME}_{T0:.2f}~.mp4"
    if "--조각만" in sys.argv:
        pieces()
        sys.exit()
    if "--소리만" not in sys.argv:
        scene = M.build()
    print(scene)
    print(sfx(scene))
