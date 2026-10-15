# -*- coding: utf-8 -*-
r"""[레거시 — 10-13 부터 AE 안 씀. 새 장면은 html_motion(references/ae-replacement.md)]
빡이사DB 본편 19 «아~ 이 광고 진짜 누가 봐도 ~ 우리가 빌려오면 되겠죠?» (시퀀스 1964.012~1984.216, 양 끝 컷 경계)
사장님 10-08 «광고 관리자 실제 화면을 참고해서 임의로 만들어서 자막에 맞게 연출».
녹화 화면 = 메타 광고 라이브러리(실제 업체 광고) → 같은 결의 가짜 화면(업체 ○○)을 PIL 로 다시 그림.
  카드 셋(예쁜 광고 둘 «8. 21.» / 투박한 광고 «5. 29.») → 투박한 카드에 초점 · 왼쪽 «내 눈 기준»(빨강) →
  날짜 형광펜 → «내 눈 기준» 지움 → «데이터 기준 · 게재 기간» 막대(파랑) → 오래된 순 정렬로 투박한 카드가 맨 앞 «오래 게재 = 검증된 광고» →
  카드가 «내 레퍼런스» 폴더로 복사. 화면 글은 말 따라 쓰지 않고 개념어(10-08 피드백).

  python bisa_ad_library.py [--조각만] [--소리만]
    → 빡이사DB\납품\19_광고라이브러리_1964.01~.mp4 (V1 그 자리, 사람 PIP 는 사장님 V2 그대로) · _효과음.xml · _미리보기.mp4
"""

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))   # tools/ (config.py)
import config  # noqa: E402
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
import rf3_ae as AE  # noqa: E402
import bisa_web_vs_instant as M  # noqa: E402

M.T0, M.T1 = 1964.012, 1984.216
M.DUR = M.T1 - M.T0
M.SEGS = [(1964.012, 1968.517, 3145.609, 3147.711), (1968.517, 1969.267, 3150.297, 3152.399), (1969.267, 1975.04, 3151.398, 3153.5),
          (1975.04, 1979.511, 3157.521, 3159.623), (1979.511, 1980.095, 3162.126, 3164.244), (1980.095, 1981.513, 3162.86, 3164.978),
          (1981.513, 1984.216, 3164.461, 3166.58)]
M.NAME = "19_광고라이브러리"
M.SFX_DIR = (config.WORK / "효과음19")
M.WORK = (config.WORK / "빡이사" / "ae19")
W, H = M.W, M.H
T0, T1 = M.T0, M.T1
WORK = M.WORK
SRC = (config.ORIG_ROOT / "빡이사DB" / "소재")
PRET = str(config.FONTS["pretendard_bold"])
NOTO = str(config.FONTS["noto_sans_kr"])
INK, GREY, LINE, BLUE, RED, GREEN = (28, 30, 33), (101, 103, 107), (222, 225, 230), (0, 100, 224), (214, 48, 40), (36, 150, 72)
PAGE = (240, 242, 245)

# ── 시각(_tmp/w19/words.txt) ──
T_IN, T_OUT = 1964.02, 1983.82
T_FOCUS = 1964.67                      # 광고
T_EYE = 1965.79                        # 너무 안 좋은
T_DATE = 1967.45                       # 이렇게 돌린다고?
T_EYE2 = 1970.13                       # 눈에 → «내 눈 기준» 다시 짚음
T_STRIKE = 1971.85                     # 올바른 게 아니라
T_DATA = 1972.27                       # 데이터가
T_BARS = 1973.43                       # 밀어주는
T_SORT = 1975.29                       # 오래 전부터
T_PROVEN = 1977.87                     # 잘 되는
T_FOLDER = 1981.65                     # 그래서
T_FLY = 1982.45                        # 레퍼런스로
T_LAND = 1983.13                       # 빌려오면

CW, CH = 360, 700
SLOT_X = [760, 1140, 1520]
CY = 186
PIP, CAPTION = (0, 580, 720, 1080), (480, 900, 1440, 1080)
BOX = {}
AXIS = [0, 0]


def font(n, wght=None):
    if wght:
        f = ImageFont.truetype(NOTO, n)
        f.set_variation_by_axes([wght])
        return f
    return ImageFont.truetype(PRET, n)


def tl(t, f):
    return ImageDraw.Draw(Image.new("RGBA", (1, 1))).textlength(t, font=f)


def save(name, im, xy):
    im.save(WORK / f"{name}.png")
    BOX[name] = (int(round(xy[0])), int(round(xy[1])), im.width, im.height)


def cover(src, w, h):
    im = Image.open(src).convert("RGB")
    s = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * s + 1), int(im.height * s + 1)), Image.LANCZOS)
    x, y = (im.width - w) // 2, int((im.height - h) * 0.3)
    return im.crop((x, y, x + w, y + h)).convert("RGBA")


def shadowed(w, h, r, fill=(255, 255, 255), m=22, alpha=55, outline=None):
    im = Image.new("RGBA", (w + 2 * m, h + 2 * m), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((m, m + 8, m + w, m + h + 8), r, fill=(10, 25, 60, alpha))
    sh = sh.filter(ImageFilter.GaussianBlur(12))
    al = np.asarray(sh.split()[3]).copy()
    al[al < 8] = 0                                                  # 흐림 꼬리가 사각 테두리로 비치지 않게(10-08)
    sh.putalpha(Image.fromarray(al))
    im.alpha_composite(sh)
    ImageDraw.Draw(im).rounded_rectangle((m, m, m + w, m + h), r, fill=fill + (255,), outline=(outline + (255,)) if outline else None, width=3)
    return im, m


def pill(t, size, fg, bg, padx=22, h=None):
    f = font(size)
    w = int(tl(t, f)) + 2 * padx
    h = h or int(size * 1.8)
    im, m = shadowed(w, h, h // 2, bg, m=16, alpha=60)
    ImageDraw.Draw(im).text((m + w / 2, m + h / 2), t, font=f, fill=fg, anchor="mm")
    return im, m


# ── 투박한 광고 소재(일부러 촌스럽게 — «누가 봐도 별로»인데 오래 돈 광고) ──
def ugly_creative(w, h):
    im = Image.new("RGBA", (w, h), (255, 226, 0, 255))
    d = ImageDraw.Draw(im)
    for i in range(0, w + h, 26):                                  # 사선 줄무늬
        d.line((i, 0, i - h, h), fill=(255, 208, 0, 255), width=10)
    burst = []
    import math
    for k in range(24):
        r = 54 if k % 2 == 0 else 38
        a = math.radians(k * 15)
        burst.append((w - 62 + r * math.cos(a), 62 + r * math.sin(a)))
    d.polygon(burst, fill=(230, 20, 30, 255))
    d.text((w - 62, 62), "특가", font=font(28), fill=(255, 255, 0, 255), anchor="mm")
    for txt, y, sz, col in (("살 안 빠지세요?", 120, 38, (220, 20, 30)), ("첫 상담 무료!!", 178, 44, (20, 20, 160))):
        f = font(sz)
        for dx in (-3, 0, 3):
            for dy in (-3, 0, 3):
                d.text((w / 2 + dx, y + dy), txt, font=f, fill=(0, 0, 0, 255), anchor="mm")
        d.text((w / 2, y), txt, font=f, fill=col + (255,), anchor="mm")
    d.rectangle((24, h - 74, w - 24, h - 24), fill=(0, 70, 220, 255), outline=(0, 0, 0, 255), width=3)
    d.text((w / 2 - 14, h - 49), "지금 바로 신청", font=font(28), fill=(255, 255, 255, 255), anchor="mm")
    d.polygon([(w - 70, h - 62), (w - 70, h - 36), (w - 48, h - 49)], fill=(255, 255, 0, 255))
    return im


CARDS = {"A": ("○○한의원", "2026. 5. 29.에 게재 시작함", ["살 안 빠져서 고민이시죠?", "1:1 맞춤 상담 받아 보세요"], None, "OOHANI.COM", "다이어트 상담 신청"),
         "B": ("○○피부과", "2026. 8. 21.에 게재 시작함", ["맑은 피부, 상담부터", "받아 보세요"], "17/feed_skin.png", "OOSKIN.COM", "피부 상담 예약"),
         "C": ("○○필라테스", "2026. 8. 21.에 게재 시작함", ["1:1 체형 교정", "체험 수업 신청하세요"], "17/feed_pilates.png", "OOPILATES.COM", "체험 수업 신청")}
ORDER0 = {"B": 0, "A": 1, "C": 2}                                   # 처음
ORDER1 = {"A": 0, "B": 1, "C": 2}                                   # 오래된 순 정렬 뒤


def card_img(key):
    name, date, txt, img, dom, cta = CARDS[key]
    im, m = shadowed(CW, CH, 14, outline=LINE)
    d = ImageDraw.Draw(im)
    x0, y0 = m + 20, m
    d.ellipse((x0, y0 + 20, x0 + 18, y0 + 38), fill=GREEN + (255,))
    d.line(((x0 + 4, y0 + 29), (x0 + 8, y0 + 33), (x0 + 14, y0 + 25)), fill=(255, 255, 255, 255), width=3)
    d.text((x0 + 26, y0 + 29), "활성", font=font(18, 700), fill=INK, anchor="lm")
    d.text((m + CW - 26, y0 + 27), "···", font=font(22, 700), fill=GREY, anchor="mm")
    d.text((x0, y0 + 62), "라이브러리 ID: ○○○○○○○○○○", font=font(16, 500), fill=GREY, anchor="lm")
    d.text((x0, y0 + 90), date, font=font(17, 500), fill=INK, anchor="lm")
    d.text((x0, y0 + 118), "플랫폼  Facebook · Instagram", font=font(16, 500), fill=GREY, anchor="lm")
    d.rounded_rectangle((x0, y0 + 140, m + CW - 20, y0 + 180), 8, fill=(234, 236, 240, 255))
    d.text((m + CW / 2, y0 + 160), "광고 상세 정보 보기", font=font(17, 600), fill=INK, anchor="mm")
    d.line((x0, y0 + 198, m + CW - 20, y0 + 198), fill=LINE + (255,), width=2)
    d.ellipse((x0, y0 + 212, x0 + 40, y0 + 252), fill=((230, 200, 60) if key == "A" else (200, 214, 236)) + (255,))
    d.text((x0 + 52, y0 + 222), name, font=font(19, 700), fill=INK, anchor="lm")
    d.text((x0 + 52, y0 + 244), "광고", font=font(14, 500), fill=GREY, anchor="lm")
    for k, t in enumerate(txt):
        d.text((x0, y0 + 280 + k * 26), t, font=font(17, 500), fill=INK, anchor="lm")
    cr = ugly_creative(CW - 40, 290) if img is None else cover(SRC / img, CW - 40, 290)
    im.alpha_composite(cr, (x0, y0 + 330))
    d.rectangle((x0, y0 + 620, m + CW - 20, y0 + 684), fill=(244, 245, 247, 255))
    d.text((x0 + 10, y0 + 638), dom, font=font(12, 500), fill=GREY, anchor="lm")
    d.text((x0 + 10, y0 + 662), cta, font=font(15, 600), fill=INK, anchor="lm")
    d.rounded_rectangle((m + CW - 130, y0 + 632, m + CW - 30, y0 + 672), 6, fill=(226, 229, 234, 255))
    d.text((m + CW - 80, y0 + 652), "더 알아보기", font=font(14, 600), fill=INK, anchor="mm")
    return im, m


def pieces():
    WORK.mkdir(parents=True, exist_ok=True)
    BOX.clear()
    # 판(머리줄 + 검색줄)
    bg = Image.new("RGBA", (W, H), PAGE + (255,))
    d = ImageDraw.Draw(bg)
    d.rectangle((0, 0, W, 84), fill=(255, 255, 255, 255))
    d.line((0, 84, W, 84), fill=LINE + (255,), width=2)
    lg = Image.open(SRC / "10" / "logo_meta.png").convert("RGBA")
    lg.thumbnail((150, 44), Image.LANCZOS)
    bg.alpha_composite(lg, (52, 42 - lg.height // 2))
    for k, t in enumerate(("광고 라이브러리", "광고 라이브러리 보고서", "브랜디드 콘텐츠")):
        x = 1080 + k * 270
        d.text((x, 42), t, font=font(20, 600 if k == 0 else 500), fill=INK if k == 0 else GREY, anchor="lm")
    d.line((1080, 70, 1080 + tl("광고 라이브러리", font(20, 600)), 70), fill=BLUE + (255,), width=3)
    for x0, x1, t in ((760, 890, "대한민국"), (902, 1050, "모든 광고")):          # «▾» 는 글꼴에 없어 삼각형으로 그림
        d.rounded_rectangle((x0, 104, x1, 158), 10, fill=(255, 255, 255, 255), outline=LINE + (255,), width=2)
        d.text(((x0 + x1) / 2 - 12, 131), t, font=font(18, 600), fill=INK, anchor="mm")
        d.polygon([(x1 - 30, 126), (x1 - 16, 126), (x1 - 23, 136)], fill=INK + (255,))
    d.rounded_rectangle((1062, 104, 1880, 158), 10, fill=(255, 255, 255, 255), outline=LINE + (255,), width=2)
    d.ellipse((1082, 120, 1102, 140), outline=GREY + (255,), width=3)
    d.line((1099, 137, 1108, 146), fill=GREY + (255,), width=3)
    d.text((1122, 131), "상담", font=font(20, 500), fill=INK, anchor="lm")
    save("board", bg, (0, 0))
    # 카드
    for key in "ABC":
        im, m = card_img(key)
        save(f"card{key}", im, (SLOT_X[ORDER0[key]] - m, CY - m))
        dim = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(dim).rounded_rectangle((m, m, m + CW, m + CH), 14, fill=PAGE + (150,))
        save(f"dim{key}", dim, (SLOT_X[ORDER0[key]] - m, CY - m))
    # 카드 A 위 요소(카드에 묶음 — 좌표는 카드 이미지 안)
    m = 22
    hl = Image.new("RGBA", (int(tl("2026. 5. 29.에 게재 시작함", font(17, 500))) + 16, 30), (255, 214, 0, 150))
    save("hlA", hl, (m + 12, m + 75))
    ring = Image.new("RGBA", (CW + 24, CH + 24), (0, 0, 0, 0))
    ImageDraw.Draw(ring).rounded_rectangle((3, 3, CW + 20, CH + 20), 18, outline=INK + (255,), width=5)
    save("focusA", ring, (m - 12, m - 12))
    im, mm = pill("오래 게재 = 검증된 광고", 24, (255, 255, 255), BLUE, padx=20, h=46)
    save("proven", im, (m + CW / 2 - im.width / 2, m - 34 - mm))
    # 왼쪽 칸 2판(10-08 «카드 너무 없어 보여, 캐릭터 눈으로 귀엽게 · «» 대본 넣는 거 별로») — 2D 캐릭터 + 말풍선
    bx, bw = 60, 640
    for nm, src, y0, tint in (("sk", "eye_skeptic.png", 86, (253, 226, 222)), ("dt", "data_confident.png", 330, (222, 234, 252))):
        ch = Image.open(SRC / "19" / src).convert("RGBA")
        a_ = np.asarray(ch)[..., 3] > 40
        ys, xs = np.where(a_)
        ch = ch.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
        k = 214 / ch.height
        ch = ch.resize((int(ch.width * k), 214), Image.LANCZOS)
        blob = Image.new("RGBA", (222, 222), (0, 0, 0, 0))
        ImageDraw.Draw(blob).ellipse((0, 0, 221, 221), fill=tint + (255,))
        save(f"blob_{nm}", blob, (bx + 4, y0 + 6))
        save(f"ch_{nm}", ch, (bx + 115 - ch.width / 2, y0 + 228 - 214))
    # 내 눈 기준: 빨간 이름표 + 말풍선(따옴표 없이)
    im, mm = pill("내 눈 기준", 24, (255, 255, 255), RED, padx=18, h=44)
    save("tag_sk", im, (bx + 262 - mm, 104 - mm))
    f = font(30)
    bw_ = int(tl("디자인이 별로인데…?", f)) + 60
    im, mm = shadowed(bw_, 84, 42, outline=(240, 200, 196))
    d = ImageDraw.Draw(im)
    d.text((mm + bw_ / 2, mm + 42), "디자인이 별로인데…?", font=f, fill=INK, anchor="mm")
    tail = [(mm + 2, mm + 30), (mm + 2, mm + 56), (mm - 26, mm + 58)]   # 왼쪽(캐릭터 쪽)으로 짧은 꼬리 — 끝은 캐릭터와 떨어짐
    d.polygon(tail, fill=(255, 255, 255, 255))
    d.line((tail[0], tail[2]), fill=(240, 200, 196, 255), width=3)
    d.line((tail[1], tail[2]), fill=(240, 200, 196, 255), width=3)
    save("bub_sk", im, (bx + 292 - mm, 160 - mm))
    st = Image.new("RGBA", (bw_ - 20, 12), (0, 0, 0, 0))
    ImageDraw.Draw(st).rounded_rectangle((0, 0, bw_ - 21, 11), 6, fill=RED + (230,))
    save("strike", st, (bx + 292 + 10, 160 + 42 - 6))
    xb = Image.new("RGBA", (84, 84), (0, 0, 0, 0))
    d = ImageDraw.Draw(xb)
    d.ellipse((4, 4, 80, 80), fill=RED + (255,), outline=(255, 255, 255, 255), width=5)
    d.line((27, 27, 57, 57), fill=(255, 255, 255, 255), width=9)
    d.line((57, 27, 27, 57), fill=(255, 255, 255, 255), width=9)
    save("xbadge", xb, (bx + 292 + bw_ - 50, 160 - 34))
    # 데이터 기준: 파란 이름표 + 게재 기간 막대 카드
    im, mm = pill("데이터 기준 · 게재 기간", 24, (255, 255, 255), BLUE, padx=18, h=44)
    save("tag_dt", im, (bx + 262 - mm, 334 - mm))
    cw_, chh = 410, 168
    im, mm = shadowed(cw_, chh, 18, outline=(196, 214, 244))
    d = ImageDraw.Draw(im)
    MX0, MX1 = mm + 128, mm + cw_ - 18                                # 5월 1일 ~ 9월 30일
    for k, t in enumerate(["5월", "6월", "7월", "8월", "9월"]):
        x = MX0 + (MX1 - MX0) * k / 5
        d.line((x, mm + 14, x, mm + chh - 12), fill=(232, 234, 238, 255), width=2)
        d.text((x + 6, mm + 24), t, font=font(14, 500), fill=GREY, anchor="lm")
    for k, nm in enumerate(("○○한의원", "○○피부과", "○○필라테스")):
        d.text((mm + 16, mm + 66 + k * 36), nm, font=font(16, 700 if k == 0 else 500), fill=INK, anchor="lm")
    cx0, cy0 = bx + 292, 386
    save("data", im, (cx0 - mm, cy0 - mm))
    AXIS[:] = [cx0 - mm + MX0, cx0 - mm + MX1]
    d0 = 28 / 31 / 5                                                  # 5월 29일 = 5월 칸의 28/31
    for k, (start, key) in enumerate(((d0, "A"), (3 / 5 + 20 / 31 / 5, "B"), (3 / 5 + 20 / 31 / 5, "C"))):
        ax0, ax1 = AXIS
        x0 = ax0 + (ax1 - ax0) * start
        wbar = int(ax1 - x0)
        b = Image.new("RGBA", (wbar, 20), (0, 0, 0, 0))
        ImageDraw.Draw(b).rounded_rectangle((0, 0, wbar - 1, 19), 10, fill=(BLUE if key == "A" else (170, 178, 190)) + (255,))
        save(f"bar{key}", b, (x0, cy0 + 66 + k * 36 - 10))
    # 내 레퍼런스 폴더
    im, mm = shadowed(bw, 420, 22, outline=(196, 214, 244))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((mm + 30, mm + 30, mm + 92, mm + 74), 8, fill=(255, 196, 60, 255))
    d.rounded_rectangle((mm + 30, mm + 22, mm + 62, mm + 36), 5, fill=(255, 196, 60, 255))
    d.text((mm + 110, mm + 52), "내 레퍼런스", font=font(36), fill=INK, anchor="lm")
    d.rounded_rectangle((mm + 30, mm + 100, mm + 230, mm + 400), 14, outline=(196, 214, 244, 255), width=3)
    d.text((mm + 270, mm + 150), "잘 되는 광고의", font=font(28, 600), fill=INK, anchor="lm")
    d.text((mm + 270, mm + 192), "구조를 빌려오기", font=font(28, 700), fill=BLUE, anchor="lm")
    d.text((mm + 270, mm + 250), "문구 · 사진 · 버튼 배치", font=font(22, 500), fill=GREY, anchor="lm")
    save("folder", im, (bx - mm, 120 - mm))
    BOX["slot"] = (bx + 30, 120 + 100, 200, 300)                     # 폴더 안 카드 자리(화면 좌표)
    im, mm = pill("+1", 30, (255, 255, 255), BLUE, padx=18, h=52)
    save("plus", im, (bx + 30 + 200 - 10 - mm, 120 + 96 - mm))
    check_layout()


def check_layout():
    bad = []
    for n, (x, y, w, h) in BOX.items():
        if n in ("board", "data_axis", "slot") or n.startswith(("dim", "hl", "focus", "proven")):
            continue
        a = np.asarray(Image.open(WORK / f"{n}.png"))[..., 3] > 60
        ys, xs = np.where(a)
        b = (x + xs.min(), y + ys.min(), x + xs.max(), y + ys.max())
        for z, zn in ((PIP, "사람 PIP"), (CAPTION, "자막")):
            if b[0] < z[2] and z[0] < b[2] and b[1] < z[3] and z[1] < b[3]:
                bad.append(f"{n} {b} ↔ {zn}")
    if bad:
        raise SystemExit("레이아웃 겹침:\n  " + "\n  ".join(bad))
    print("겹침 없음")


# ── 애펙 ───────────────────────────────────────────────────────
def jsx(out_mov):
    js = AE.js
    s = lambda t: round(t - T0, 4)                         # noqa: E731
    L = ["function eo(p){ for(var k=1;k<=p.numKeys;k++){ var n=p.isSpatial?1:(p.value.length||1), o=[], i=[]; for(var j=0;j<n;j++){ o.push(new KeyframeEase(0,0.1)); i.push(new KeyframeEase(0,85)); } p.setTemporalEaseAtKey(k,i,o); } }",
         "function hold(p){ for(var q=1;q<=p.numKeys;q++){ p.setInterpolationTypeAtKey(q,KeyframeInterpolationType.HOLD); } }",
         f"(function(){{ var comp=app.project.items.addComp('bisa19',{W},{H},1,{M.DUR:.3f},{M.FPS}); comp.motionBlur=true;"]
    a = L.append
    nv = [0]
    slide = "thisComp.layer('RIG').transform.position[0]"

    def lay(name, parent=None, anchor=None):
        nv[0] += 1
        v = f"L{nv[0]}"
        x, y, w, h = BOX[name]
        ax, ay = anchor if anchor else (w / 2, h / 2)
        a(f"var {v}=comp.layers.add(imp({js(str(WORK / f'{name}.png'))})); {v}.motionBlur=true; {v}.transform.anchorPoint.setValue([{ax},{ay}]);")
        if parent:                                                 # 카드에 묶음: 좌표 = 카드 이미지 안
            a(f"{v}.parent={parent}; {v}.transform.scale.setValue([100,100]); {v}.transform.position.setValue([{x + ax:.1f},{y + ay:.1f}]);")
        else:
            a(f"{v}.transform.position.setValue([{x + ax:.1f},{y + ay:.1f}]); {v}.transform.position.expression=\"value+[{slide},0]\";")
        return v

    def opa(v, k, hold_=False):
        a(f"keys({v}.transform.opacity,{k});")
        if hold_:
            a(f"hold({v}.transform.opacity);")

    def life(t_in, t_out=T_OUT + 0.4, fi=0.14, fo=0.25):
        return [[max(0, s(t_in) - 0.001), 0], [s(t_in) + fi, 100], [s(t_out), 100], [s(t_out) + fo, 0]]

    def pop(v, t, frm=72, dur=0.22):
        a(f"keys({v}.transform.scale,[[{s(t)},[{frm},{frm}]],[{s(t) + dur:.3f},[100,100]]]); eo({v}.transform.scale);")

    def rise(v, name, t, dx=0, dy=24, dur=0.3):
        x, y, w, h = BOX[name]
        a(f"keys({v}.transform.position,[[{s(t)},[{x + w / 2 + dx:.1f},{y + h / 2 + dy:.1f}]],[{s(t) + dur:.3f},[{x + w / 2:.1f},{y + h / 2:.1f}]]]); eo({v}.transform.position);")

    a(f"var iv=imp({js(str(M.REC))});")
    for i, (ta, tb, rs, _) in enumerate(M.SEGS):
        a(f"var R{i}=comp.layers.add(iv); R{i}.startTime={s(ta) - rs:.4f}; R{i}.inPoint={s(ta):.4f}; R{i}.outPoint={s(tb):.4f};")
    a("var RIG=comp.layers.addNull(); RIG.name='RIG'; RIG.enabled=false; RIG.transform.position.setValue([0,0]);")
    a(f"keys(RIG.transform.position,[[{s(T_IN)},[{W},0]],[{s(T_IN) + 0.45:.3f},[0,0]],[{s(T_OUT)},[0,0]],[{s(T_OUT) + 0.36:.3f},[{-W},0]]]); eo(RIG.transform.position);")
    lay("board")
    # 카드: 처음 자리 → 정렬 뒤 자리(위치 키), A 는 초점 동안 살짝 들림
    cv = {}
    for key in "ABC":
        v = lay(f"card{key}")
        x, y, w, h = BOX[f"card{key}"]
        x1 = SLOT_X[ORDER1[key]] - 22
        if x1 != x:
            a(f"keys({v}.transform.position,[[{s(T_SORT)},[{x + w / 2:.1f},{y + h / 2:.1f}]],[{s(T_SORT) + 0.6:.3f},[{x1 + w / 2:.1f},{y + h / 2:.1f}]]]); eo({v}.transform.position);")
        if key == "A":
            a(f"keys({v}.transform.scale,[[{s(T_FOCUS)},[100,100]],[{s(T_FOCUS) + 0.3:.3f},[103,103]],[{s(T_SORT)},[103,103]],[{s(T_SORT) + 0.6:.3f},[100,100]]]); eo({v}.transform.scale);")
        cv[key] = v
    for key in "BC":                                               # 초점 동안 다른 카드 흐리게
        v = lay(f"dim{key}", parent=cv[key], anchor=(0, 0))
        a(f"{v}.transform.position.setValue([0,0]);")
        opa(v, [[s(T_FOCUS), 0], [s(T_FOCUS) + 0.3, 100], [s(T_SORT), 100], [s(T_SORT) + 0.4, 0]])
    a(f"{cv['A']}.moveToBeginning();")
    v = lay("focusA", parent=cv["A"], anchor=(0, 0)); a(f"{v}.transform.position.setValue([{BOX['focusA'][0]},{BOX['focusA'][1]}]);")
    opa(v, [[s(T_FOCUS), 0], [s(T_FOCUS) + 0.2, 100], [s(T_SORT), 100], [s(T_SORT) + 0.3, 0]])
    v = lay("hlA", parent=cv["A"], anchor=(0, 0)); a(f"{v}.transform.position.setValue([{BOX['hlA'][0]},{BOX['hlA'][1]}]); {v}.blendingMode=BlendingMode.MULTIPLY;")
    a(f"var e{v}={v}.Effects.addProperty('ADBE Linear Wipe'); e{v}.property(2).setValue(270); e{v}.property(3).setValue(6); keys(e{v}.property(1),[[{s(T_DATE)},100],[{s(T_DATE) + 0.4:.3f},0]]);")
    opa(v, [[s(T_DATE) - 0.01, 0], [s(T_DATE), 100], [s(T_FLY), 100], [s(T_FLY) + 0.2, 0]])
    v = lay("proven", parent=cv["A"]); opa(v, life(T_PROVEN, T_FLY)); pop(v, T_PROVEN)
    # 왼쪽 칸: 캐릭터(들썩) + 말풍선
    def char(nm, t, t_out):
        b = lay(f"blob_{nm}"); opa(b, life(t, t_out, fo=0.3)); pop(b, t, 60, 0.28)
        x, y, w, h = BOX[f"ch_{nm}"]
        c = lay(f"ch_{nm}", anchor=(w / 2, h))
        opa(c, life(t + 0.05, t_out, fo=0.3)); pop(c, t + 0.05, 80, 0.26)
        a(f"{c}.transform.position.expression=\"value+[{slide},3*Math.sin(time*3.2)]\";")
        return b, c
    b, c = char("sk", T_EYE - 0.1, T_FOLDER - 0.3)
    a(f"keys({c}.transform.scale,[[{s(T_EYE2)},[100,100]],[{s(T_EYE2) + 0.12:.3f},[106,95]],[{s(T_EYE2) + 0.3:.3f},[100,100]]]);")
    for v_ in (b, c):
        a(f"keys({v_}.transform.opacity,[[{s(T_STRIKE) + 0.2:.3f},100],[{s(T_STRIKE) + 0.5:.3f},50]]);")
    v = lay("tag_sk"); opa(v, life(T_EYE + 0.1, T_FOLDER - 0.3, fo=0.3)); pop(v, T_EYE + 0.1)
    x, y, w, h = BOX["bub_sk"]
    v = lay("bub_sk", anchor=(0, h / 2)); opa(v, life(T_EYE + 0.15, T_FOLDER - 0.3, fo=0.3)); pop(v, T_EYE + 0.15, 60, 0.24)
    a(f"keys({v}.transform.opacity,[[{s(T_STRIKE) + 0.2:.3f},100],[{s(T_STRIKE) + 0.5:.3f},55]]);")
    v = lay("strike", anchor=(0, BOX["strike"][3] / 2))
    a(f"keys({v}.transform.scale,[[{s(T_STRIKE)},[0,100]],[{s(T_STRIKE) + 0.3:.3f},[100,100]]]); eo({v}.transform.scale);")
    opa(v, life(T_STRIKE, T_FOLDER - 0.3, fi=0.04, fo=0.3))
    v = lay("xbadge"); opa(v, life(T_STRIKE + 0.2, T_FOLDER - 0.3, fi=0.06, fo=0.3)); pop(v, T_STRIKE + 0.2, 40)
    char("dt", T_DATA, T_FOLDER - 0.3)
    v = lay("tag_dt"); opa(v, life(T_DATA + 0.1, T_FOLDER - 0.3, fo=0.3)); pop(v, T_DATA + 0.1)
    v = lay("data"); opa(v, life(T_DATA + 0.2, T_FOLDER - 0.3, fo=0.3)); rise(v, "data", T_DATA + 0.2, dx=-24, dy=0)
    for k, key in enumerate("ABC"):
        v = lay(f"bar{key}", anchor=(0, 10))
        t = T_BARS + k * 0.12
        a(f"keys({v}.transform.scale,[[{s(t)},[0,100]],[{s(t) + 0.6:.3f},[100,100]]]); eo({v}.transform.scale);")
        opa(v, life(t, T_FOLDER - 0.3, fi=0.05, fo=0.3))
    # 내 레퍼런스: 폴더 → 카드 A 사본이 날아와 들어감 → +1
    v = lay("folder"); opa(v, life(T_FOLDER, fi=0.2)); rise(v, "folder", T_FOLDER, dx=-30, dy=0)
    x, y, w, h = BOX["cardA"]
    sx, sy, sw, sh = BOX["slot"]
    k_ = min(sw / (CW + 44), sh / (CH + 44)) * 100
    fx, fy = SLOT_X[0] - 22 + w / 2, y + h / 2
    tx, ty = sx + sw / 2, sy + sh / 2 + 2
    v = lay("cardA")
    a(f"keys({v}.transform.position,[[{s(T_FLY)},[{fx:.1f},{fy:.1f}]],[{s(T_LAND)},[{tx:.1f},{ty:.1f}]]]); eo({v}.transform.position);")
    a(f"keys({v}.transform.scale,[[{s(T_FLY)},[100,100]],[{s(T_LAND)},[{k_:.1f},{k_:.1f}]]]); eo({v}.transform.scale);")
    opa(v, [[s(T_FLY) - 0.001, 0], [s(T_FLY) + 0.06, 100], [s(T_OUT + 0.4), 100], [s(T_OUT + 0.6), 0]])
    v = lay("plus"); opa(v, life(T_LAND, fi=0.08)); pop(v, T_LAND, 40)
    a(f"var rq=app.project.renderQueue.items.add(comp); var om=rq.outputModule(1); om.applyTemplate({js('고품질')}); om.file=new File({js(str(out_mov))});")
    a("log('ok bisa19'); })();")
    assert T_OUT + 0.36 < T1
    return "\n".join(L)


M.SND_FIX = {
    "in":    ("휙２.mp3", 0.6, 4, "peak"),
    "st1":   ("KN_pepSound1.wav", 0.4, 8, "onset"),
    "st2":   ("KN_pepSound2.wav", 0.4, 8, "onset"),
    "pop":   ("ML_Cartoon bubbles popping.wav", 0.5, 5, "onset"),
    "hl":    ("SEL_ゲージ回復1.mp3", 0.6, 12, "onset"),               # 날짜 형광펜 · 막대
    "no":    ("KN_error_003.wav", 0.5, 5, "onset"),                   # 내 눈 기준 ✕
    "sort":  ("ML_Fast small sweep transition.wav", 0.6, 5, "onset"),  # 오래된 순 정렬
    "ok":    ("맑은소리.mp3", 0.8, 7, "onset"),                        # 검증된 광고
    "fly":   ("ML_Fast air sweep transition.wav", 0.6, 5, "onset"),    # 폴더로 복사
    "land":  ("SEL_キラッ1.mp3", 0.7, -1, "onset"),
    "back":  ("휙1.mp3", 0.7, 8, "peak"),
}
M.EVENTS = [(T_IN + 0.25, "in"), (T_FOCUS, "st1"), (T_EYE, "pop"), (T_DATE, "hl"), (T_EYE2, "st2"), (T_STRIKE, "no"), (T_DATA, "st2"), (T_BARS, "hl"),
            (T_SORT, "sort"), (T_PROVEN, "ok"), (T_FOLDER, "pop"), (T_FLY, "fly"), (T_LAND, "land"), (T_OUT + 0.2, "back")]

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
    print(M.sfx(scene))
