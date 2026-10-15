# -*- coding: utf-8 -*-
r"""[레거시 — 10-13 부터 AE 안 씀. 새 장면은 html_motion(references/ae-replacement.md)]
빡이사DB 본편 20 «아, 뒷배경 이렇게 했구나 ~ 그래서 이거는 정말 노력 많이 하셔야 하는 부분이다» (시퀀스 2131.56~2162.627)
사장님 10-08 «보여지는 화면에서 마우스 포인트랑 대본 정합성 맞춰서 확대 및 강조 표현(빨간 테두리·애펙·클로드 디자인 자유) ·
강조할 게 없거나 애매한 부분은 내용에 맞는 이미지를 만들어서 연출».
앞(~2142.3): 녹화 화면을 어둡게 하고 마우스가 있던 카드 부분만 2.2배 «돋보기»로 띄움(사람 PIP 자리 피함) + 빨간 테두리·연결선·이름표
  2131.94 뒷배경 · 2133.36 디자인 · 2133.94 글 배치(테슬라 이미지 카드, 스크롤 전) → 2136.6 스크롤 → 왼쪽 영상 카드(재생 중) 2.2배
  «초반 3초» · «팀장님으로 시작» 자막 동그라미 · 2140.14 «영상 구조» 구조 띠(그림)
뒤(2142.5~): 화면 전체 판 + 19 캐릭터(Codex 2D, 소재/20) — 분석 노트(앞에서 짚은 것 체크) → 세팅 = 정답 있음(파랑) / 콘텐츠 = 정답 없음(빨강) →
  시도 카드 쌓임 → «노력» 강조. 따옴표 대사 없음(10-08 19 피드백).

  python bisa_ref_analyze.py [--조각만] [--소리만]
    → 빡이사DB\납품\20_레퍼런스분석_2131.56~.mp4 (V1 2131.56 은 클립 가운데 — 잘라서, 끝 2162.627 컷 경계) · _효과음.xml · _미리보기.mp4
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

M.T0, M.T1 = 2131.56, 2162.627
M.DUR = M.T1 - M.T0
_V1 = [(2129.394, 2133.164, 3473.086, 3475.555), (2133.164, 2133.765, 3477.19, 3479.676), (2133.765, 2135.667, 3477.908, 3480.394),
       (2135.667, 2136.618, 3480.127, 3482.612), (2136.618, 2137.686, 3481.161, 3483.647), (2137.686, 2139.771, 3482.346, 3484.831),
       (2139.771, 2142.49, 3484.614, 3487.1), (2142.49, 2145.577, 3487.434, 3489.92), (2145.577, 2146.678, 3490.654, 3493.156),
       (2146.678, 2151.166, 3491.905, 3494.408), (2151.166, 2152.751, 3496.727, 3499.229), (2152.751, 2155.37, 3498.495, 3500.997),
       (2155.37, 2159.491, 3501.264, 3503.767), (2159.491, 2162.627, 3506.253, 3508.772)]
M.SEGS = [(max(a, M.T0), b, r + max(0, M.T0 - a), c + max(0, M.T0 - a)) for a, b, r, c in _V1]
M.NAME = "20_레퍼런스분석"
M.SFX_DIR = (config.WORK / "효과음20")
M.WORK = (config.WORK / "빡이사" / "ae20")
W, H = M.W, M.H
T0, T1 = M.T0, M.T1
WORK = M.WORK
SRC = (config.ORIG_ROOT / "빡이사DB" / "소재")
PRET = str(config.FONTS["pretendard_bold"])
NOTO = str(config.FONTS["noto_sans_kr"])
HAND = str(config.FONTS["gaegu_bold"])
INK, GREY, LINE, BLUE, RED = (28, 30, 33), (101, 103, 107), (222, 225, 230), (0, 100, 224), (220, 38, 38)
PAGE = (240, 242, 245)

# ── 시각(_tmp/w20/words.txt) ──
T_DIM = 2131.62
T_BG, T_DESIGN, T_LAYOUT = 2131.94, 2133.36, 2133.94
T_TOUT = 2135.62                        # 영상이면 → 테슬라 돋보기 빠짐
T_SCROLL = 2136.60                      # 녹화 화면 스크롤(−125px)
T_VID, T_3S, T_BOSS = 2136.72, 2137.08, 2137.78
T_STRUCT = 2140.14
T_IN = 2142.30                          # 판 들어옴
T_NOTE = [2143.18, 2143.62, 2144.12, 2144.74]   # 뜯어보시면서 · · 적어보셔야
T_WHY = 2145.58                         # 이건 왜 잘 됐지?
T_WRITE = 2148.30                       # 적으면서 분석
T_GOOD = 2150.42                        # 좋은 광고 → «빌려올 점» 밑줄
T_SET, T_CONT = 2153.46, 2154.34        # 세팅법처럼 · 정답이 없어요
T_NOTEOUT = 2152.78                     # 이거는 → 노트 걷힘
T_TRY = [2155.30, 2155.82, 2156.44, 2156.98, 2157.34]
T_FIRE, T_EFFORT = 2159.38, 2160.88     # 그래서 · 노력
T_OUT = 2162.18

# 돋보기(녹화 좌표 → 화면): 가운데·배율
MAG = 2.2
POP_C = (1150, 440)
TESLA = (614, 632, 833, 851)            # 스크롤 전
VIDEO = (208, 507, 331, 726)            # 스크롤 뒤
PIP, CAPTION = (0, 580, 720, 1080), (480, 900, 1440, 1080)
BOX = {}


def font(n, wght=None, f=None):
    if f:
        return ImageFont.truetype(f, n)
    if wght:
        ft = ImageFont.truetype(NOTO, n)
        ft.set_variation_by_axes([wght])
        return ft
    return ImageFont.truetype(PRET, n)


def tl(t, f):
    return ImageDraw.Draw(Image.new("RGBA", (1, 1))).textlength(t, font=f)


def save(name, im, xy):
    im.save(WORK / f"{name}.png")
    BOX[name] = (int(round(xy[0])), int(round(xy[1])), im.width, im.height)


def shadowed(w, h, r, fill=(255, 255, 255), m=22, alpha=60, outline=None, ow=3):
    im = Image.new("RGBA", (w + 2 * m, h + 2 * m), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((m, m + 8, m + w, m + h + 8), r, fill=(10, 25, 60, alpha))
    sh = sh.filter(ImageFilter.GaussianBlur(12))
    al = np.asarray(sh.split()[3]).copy()
    al[al < 8] = 0
    sh.putalpha(Image.fromarray(al))
    im.alpha_composite(sh)
    ImageDraw.Draw(im).rounded_rectangle((m, m, m + w, m + h), r, fill=fill + (255,), outline=(outline + (255,)) if outline else None, width=ow)
    return im, m


def pill(t, size, fg, bg, padx=22, h=None):
    f = font(size)
    w = int(tl(t, f)) + 2 * padx
    h = h or int(size * 1.8)
    im, m = shadowed(w, h, h // 2, bg, m=16, alpha=70)
    ImageDraw.Draw(im).text((m + w / 2, m + h / 2), t, font=f, fill=fg, anchor="mm")
    return im, m


def pop_xy(box, p):
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    return POP_C[0] + MAG * (p[0] - cx), POP_C[1] + MAG * (p[1] - cy)


def outline(name, box, rec, pad=8, r=14, width=6, ellipse=False):
    x0, y0 = pop_xy(box, (rec[0], rec[1]))
    x1, y1 = pop_xy(box, (rec[2], rec[3]))
    x0, y0, x1, y1 = x0 - pad, y0 - pad, x1 + pad, y1 + pad
    im = Image.new("RGBA", (int(x1 - x0) + 12, int(y1 - y0) + 12), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if ellipse:
        d.ellipse((6, 6, im.width - 7, im.height - 7), outline=RED + (255,), width=width)
    else:
        d.rounded_rectangle((6, 6, im.width - 7, im.height - 7), r, outline=RED + (255,), width=width)
    save(name, im, (x0 - 6, y0 - 6))
    return x1, (y0 + y1) / 2


def connector(name, x0, y0, x1, y1):
    w, h = int(abs(x1 - x0)) + 10, int(abs(y1 - y0)) + 10
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ax, ay = (5, 5) if y1 >= y0 else (5, h - 5)
    bx, by = (w - 5, h - 5) if y1 >= y0 else (w - 5, 5)
    d = ImageDraw.Draw(im)
    d.line(((ax, ay), (bx, by)), fill=RED + (255,), width=4)
    d.ellipse((ax - 5, ay - 5, ax + 5, ay + 5), fill=RED + (255,))
    save(name, im, (min(x0, x1) - 5, min(y0, y1) - 5))


def char_img(fn, hgt):
    ch = Image.open(SRC / "20" / fn).convert("RGBA")
    a = np.asarray(ch)[..., 3] > 40
    ys, xs = np.where(a)
    ch = ch.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    return ch.resize((int(ch.width * hgt / ch.height), hgt), Image.LANCZOS)


def pieces():
    WORK.mkdir(parents=True, exist_ok=True)
    BOX.clear()
    save("dim", Image.new("RGBA", (W, H), (10, 14, 24, 150)), (0, 0))
    # 돋보기 틀(흰 테두리 + 그림자) — 두 크기
    for nm, box in (("frameT", TESLA), ("frameV", VIDEO)):
        w, h = int((box[2] - box[0]) * MAG), int((box[3] - box[1]) * MAG)
        fr = Image.new("RGBA", (w + 60, h + 60), (0, 0, 0, 0))
        sh = Image.new("RGBA", fr.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((30 - 6, 30 + 4, 30 + w + 6, 30 + h + 16), 18, fill=(0, 0, 0, 150))
        fr.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
        ImageDraw.Draw(fr).rounded_rectangle((30 - 8, 30 - 8, 30 + w + 8, 30 + h + 8), 18, outline=(255, 255, 255, 255), width=8)
        save(nm, fr, (POP_C[0] - w / 2 - 30, POP_C[1] - h / 2 - 30))
    # 테슬라 카드: 뒷배경 · 디자인 · 글 배치
    LX = 1440
    for nm, rec, lab, ly in (("o_bg", TESLA, "뒷배경", 230), ("o_design", (618, 638, 762, 708), "디자인", 390), ("o_layout", (664, 788, 832, 849), "글 배치", 600)):
        x1, ym = outline(nm, TESLA, rec, pad=4 if nm == "o_bg" else 8)
        im, m = pill(lab, 34, (255, 255, 255), RED, padx=24, h=62)
        save(f"l_{nm}", im, (LX - m, ly - 31 - m))
        connector(f"c_{nm}", x1 + 2, ym, LX - 2, ly)
    # 영상 카드: 초반 3초 · 팀장님(자막 동그라미) · 구조 띠
    x1, ym = outline("o_vid", VIDEO, VIDEO, pad=4)
    im, m = pill("초반 3초", 34, (255, 255, 255), RED, padx=24, h=62)
    save("l_3s", im, (1330 - m, 230 - 31 - m))
    connector("c_3s", x1 + 2, 330, 1328, 230)
    tb = Image.new("RGBA", (int((VIDEO[2] - VIDEO[0]) * MAG), 26), (0, 0, 0, 0))
    d = ImageDraw.Draw(tb)
    d.rounded_rectangle((0, 6, tb.width - 1, 20), 7, fill=(255, 255, 255, 200))
    d.rounded_rectangle((0, 6, int(tb.width * 0.2), 20), 7, fill=RED + (255,))
    vx0, vy0 = pop_xy(VIDEO, (VIDEO[0], VIDEO[3]))
    save("tbar", tb, (vx0, vy0 + 22))
    f = font(20, 600)
    im = Image.new("RGBA", (200, 30), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((0, 15), "0:00 ~ 0:03", font=f, fill=(255, 255, 255, 255), anchor="lm")
    save("tbar_t", im, (vx0, vy0 + 52))
    x1b, ymb = outline("o_boss", VIDEO, (248, 640, 302, 664), pad=10, ellipse=True)
    im, m = pill("첫 장면 = 팀장님 등장", 30, (255, 255, 255), RED, padx=22, h=56)
    save("l_boss", im, (1330 - m, 470 - 28 - m))
    connector("c_boss", x1b + 2, ymb, 1328, 470)
    # 영상 구조 띠(그림)
    sw_, sh_ = 520, 210
    im, m = shadowed(sw_, sh_, 20)
    d = ImageDraw.Draw(im)
    d.text((m + 26, m + 36), "영상 구조", font=font(30), fill=INK, anchor="lm")
    segs = [("0~3초", "첫 장면", RED), ("본론", "설명", (120, 130, 145)), ("끝", "행동 유도", (120, 130, 145))]
    x = m + 26
    for k, (a_, b_, col) in enumerate(segs):
        w_ = 150
        if k == 0:
            d.rounded_rectangle((x, m + 80, x + w_, m + 180), 14, fill=col + (255,))
            fc = (255, 255, 255)
        else:
            d.rounded_rectangle((x, m + 80, x + w_, m + 180), 14, outline=col + (255,), width=3, fill=(246, 247, 249, 255))
            fc = INK
        d.text((x + w_ / 2, m + 112), a_, font=font(26), fill=fc, anchor="mm")
        d.text((x + w_ / 2, m + 150), b_, font=font(20, 600), fill=fc, anchor="mm")
        if k < 2:
            d.polygon([(x + w_ + 6, m + 120), (x + w_ + 6, m + 140), (x + w_ + 16, m + 130)], fill=GREY + (255,))
        x += w_ + 22
    save("struct", im, (1330 - m, 600 - m))

    # ── 뒤: 판 ──
    bg = Image.new("RGBA", (W, H), PAGE + (255,))
    d = ImageDraw.Draw(bg)
    for y in range(40, H, 40):
        for x in range(40, W, 40):
            d.point((x, y), fill=(208, 214, 224, 255))
    save("board", bg, (0, 0))
    for nm, fn, hgt in (("ch_note", "char_note.png", 430), ("ch_practice", "char_practice.png", 430), ("ch_fire", "char_fire.png", 440)):
        ch = char_img(fn, hgt)
        save(nm, ch, (330 - ch.width / 2, 570 - hgt))
    # 분석 노트(줄 노트 + 손글씨 줄)
    nx0, ny0, nw, nh = 800, 110, 1040, 760
    im, m = shadowed(nw, nh, 22)
    d = ImageDraw.Draw(im)
    for y in range(m + 150, m + nh - 30, 86):
        d.line((m + 40, y, m + nw - 40, y), fill=(214, 226, 242, 255), width=2)
    d.line((m + 120, m + 20, m + 120, m + nh - 20), fill=(244, 196, 196, 255), width=2)
    d.text((m + 150, m + 80), "레퍼런스 분석 노트", font=font(44), fill=INK, anchor="lm")
    save("note", im, (nx0 - m, ny0 - m))
    hf = font(52, f=HAND)
    rows = ["뒷배경", "디자인, 글 배치", "초반 3초 = 팀장님 등장", "영상 구조"]   # 개구 글꼴엔 «·»«→» 없음
    for k, t in enumerate(rows):
        y = ny0 + 150 + 86 * k + 86 - 16                            # 노트 줄 위에 앉게
        box = Image.new("RGBA", (44, 44), (0, 0, 0, 0))
        ImageDraw.Draw(box).rounded_rectangle((2, 2, 41, 41), 8, outline=INK + (255,), width=4)
        save(f"cb{k}", box, (nx0 + 150, y - 46))
        ck = Image.new("RGBA", (60, 54), (0, 0, 0, 0))
        ImageDraw.Draw(ck).line(((8, 28), (24, 44), (54, 6)), fill=BLUE + (255,), width=8, joint="curve")
        save(f"ck{k}", ck, (nx0 + 146, y - 58))
        w = int(tl(t, hf)) + 20
        im = Image.new("RGBA", (w, 70), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((4, 46), t, font=hf, fill=INK + (255,), anchor="ls")
        save(f"row{k}", im, (nx0 + 215, y - 60))
    y = ny0 + 150 + 86 * 4 + 86 - 16
    t = "잘 된 이유:"
    w = int(tl(t, hf)) + 20
    im = Image.new("RGBA", (w, 70), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((4, 46), t, font=hf, fill=RED + (255,), anchor="ls")
    save("why", im, (nx0 + 150, y - 60))
    hl = Image.new("RGBA", (w + 10, 34), (255, 214, 0, 140))
    save("why_hl", hl, (nx0 + 145, y - 34))
    t = "내 광고에 빌려올 점"
    w2 = int(tl(t, hf)) + 20
    im = Image.new("RGBA", (w2, 70), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((4, 46), t, font=hf, fill=BLUE + (255,), anchor="ls")
    save("borrow", im, (nx0 + 160 + w, y - 60))
    ul = Image.new("RGBA", (w2, 16), (0, 0, 0, 0))
    ImageDraw.Draw(ul).line((4, 10, w2 * 0.5, 6, w2 - 6, 11), fill=BLUE + (255,), width=6, joint="curve")
    save("borrow_ul", ul, (nx0 + 160 + w, y + 2))
    # 세팅(파랑) vs 콘텐츠(빨강)
    for nm, x0, col, tint, title, sub, items in (("cmpA", 800, BLUE, (226, 236, 252), "세팅", "정답이 있다", ["예산 · 타겟", "언어 · 노출 위치", "따라 하면 끝"]),
                                                 ("cmpB", 1340, RED, (253, 230, 228), "콘텐츠", "정답이 없다", ["업종마다 다름", "보는 사람마다 다름", "해 봐야 안다"])):
        im, m = shadowed(500, 560, 24)
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((m, m, m + 500, m + 150), 24, fill=tint + (255,))
        d.rectangle((m, m + 120, m + 500, m + 150), fill=tint + (255,))
        d.text((m + 250, m + 62), title, font=font(54), fill=col, anchor="mm")
        d.text((m + 250, m + 118), sub, font=font(30, 700), fill=INK, anchor="mm")
        for k, it in enumerate(items):
            yy = m + 220 + k * 100
            d.ellipse((m + 50, yy - 18, m + 86, yy + 18), fill=col + (255,))
            if nm == "cmpA":
                d.line(((m + 59, yy), (m + 66, yy + 8), (m + 79, yy - 8)), fill=(255, 255, 255, 255), width=5)
            else:
                d.text((m + 68, yy), "?", font=font(26), fill=(255, 255, 255), anchor="mm")
            d.text((m + 110, yy), it, font=font(32, 600), fill=INK, anchor="lm")
        save(nm, im, (x0 - m, 150 - m))
    # 시도 카드(반복)
    for k in range(5):
        im, m = shadowed(300, 380, 20, outline=(214, 220, 230))
        d = ImageDraw.Draw(im)
        d.text((m + 26, m + 40), f"시도 {k + 1}", font=font(34), fill=INK if k < 4 else BLUE, anchor="lm")
        for j in range(5):
            d.rounded_rectangle((m + 26, m + 90 + j * 52, m + 274 - (j % 3) * 50, m + 112 + j * 52), 8, fill=(226, 230, 236, 255))
        if k == 4:
            d.rounded_rectangle((m + 4, m + 4, m + 296, m + 376), 18, outline=BLUE + (255,), width=6)
        save(f"try{k}", im, (840 + k * 180 - m, 180 + (k % 2) * 30 - m))
    im, m = pill("반복할수록 좋아진다", 34, (255, 255, 255), BLUE, padx=26, h=64)
    save("try_lab", im, (1340 - im.width / 2 + m - m, 660 - m))
    # 노력
    f = font(170)
    w = int(tl("노력", f)) + 40
    im = Image.new("RGBA", (w, 230), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((20, 115), "노력", font=f, fill=INK + (255,), anchor="lm")
    save("effort", im, (1080, 260))
    ul = Image.new("RGBA", (w - 20, 60), (0, 0, 0, 0))
    ImageDraw.Draw(ul).rounded_rectangle((0, 0, w - 21, 59), 16, fill=(255, 92, 92, 150))
    save("effort_hl", ul, (1090, 400))
    im, m = pill("정답 대신 반복", 40, (255, 255, 255), RED, padx=30, h=74)
    save("effort_sub", im, (1080 + w / 2 - im.width / 2, 540 - m))
    sp = Image.new("RGBA", (130, 130), (0, 0, 0, 0))
    d = ImageDraw.Draw(sp)
    import math
    for ang in (-90, -45, 0):
        r0, r1 = 36, 86 if ang == -45 else 72
        c_, s_ = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        p0, p1 = (10 + r0 * c_, 120 + r0 * s_), (10 + r1 * c_, 120 + r1 * s_)
        d.line((p0, p1), fill=RED + (255,), width=11)
        for q in (p0, p1):
            d.ellipse((q[0] - 5, q[1] - 5, q[0] + 5, q[1] + 5), fill=RED + (255,))
    save("spark", sp, (1080 + w - 30, 230))
    check_layout()


def check_layout():
    bad = []
    skip = ("dim", "board")
    for n, (x, y, w, h) in BOX.items():
        if n in skip or n.startswith("frame"):
            continue
        a = np.asarray(Image.open(WORK / f"{n}.png"))[..., 3] > 60
        ys, xs = np.where(a)
        b = (x + xs.min(), y + ys.min(), x + xs.max(), y + ys.max())
        for z, zn in ((PIP, "사람 PIP"), (CAPTION, "자막")):
            if b[0] < z[2] and z[0] < b[2] and b[1] < z[3] and z[1] < b[3]:
                bad.append(f"{n} {b} ↔ {zn}")
        if b[0] < 10 or b[1] < 10 or b[2] > W - 10 or b[3] > H - 10:
            bad.append(f"{n} {b} 화면 밖")
    if bad:
        raise SystemExit("레이아웃 겹침:\n  " + "\n  ".join(bad))
    print("겹침 없음")


# ── 애펙 ───────────────────────────────────────────────────────
def jsx(out_mov):
    js = AE.js
    s = lambda t: round(t - T0, 4)                         # noqa: E731
    L = ["function eo(p){ for(var k=1;k<=p.numKeys;k++){ var n=p.isSpatial?1:(p.value.length||1), o=[], i=[]; for(var j=0;j<n;j++){ o.push(new KeyframeEase(0,0.1)); i.push(new KeyframeEase(0,85)); } p.setTemporalEaseAtKey(k,i,o); } }",
         "function hold(p){ for(var q=1;q<=p.numKeys;q++){ p.setInterpolationTypeAtKey(q,KeyframeInterpolationType.HOLD); } }",
         f"(function(){{ var comp=app.project.items.addComp('bisa20',{W},{H},1,{M.DUR:.3f},{M.FPS}); comp.motionBlur=true;"]
    a = L.append
    nv = [0]
    slide = "thisComp.layer('RIG').transform.position[0]"

    def lay(name, anchor=None, rig=False):
        nv[0] += 1
        v = f"L{nv[0]}"
        x, y, w, h = BOX[name]
        ax, ay = anchor if anchor else (w / 2, h / 2)
        a(f"var {v}=comp.layers.add(imp({js(str(WORK / f'{name}.png'))})); {v}.motionBlur=true; {v}.transform.anchorPoint.setValue([{ax},{ay}]); {v}.transform.position.setValue([{x + ax:.1f},{y + ay:.1f}]);")
        if rig:
            a(f"{v}.transform.position.expression=\"value+[{slide},0]\";")
        return v

    def opa(v, k, hold_=False):
        a(f"keys({v}.transform.opacity,{k});")
        if hold_:
            a(f"hold({v}.transform.opacity);")

    def life(t_in, t_out, fi=0.14, fo=0.22):
        return [[max(0, s(t_in) - 0.001), 0], [s(t_in) + fi, 100], [s(t_out), 100], [s(t_out) + fo, 0]]

    def pop(v, t, frm=72, dur=0.22):
        a(f"keys({v}.transform.scale,[[{s(t)},[{frm},{frm}]],[{s(t) + dur:.3f},[100,100]]]); eo({v}.transform.scale);")

    def wipe(v, t0, t1, ang=270):
        a(f"var e{v}={v}.Effects.addProperty('ADBE Linear Wipe'); e{v}.property(2).setValue({ang}); e{v}.property(3).setValue(8); keys(e{v}.property(1),[[{s(t0)},100],[{s(t1)},0]]);")

    def grow(v, t, dur=0.32):
        a(f"keys({v}.transform.scale,[[{s(t)},[0,100]],[{s(t) + dur:.3f},[100,100]]]); eo({v}.transform.scale);")

    # 녹화(바탕)
    a(f"var iv=imp({js(str(M.REC))});")
    for i, (ta, tb, rs, _) in enumerate(M.SEGS):
        a(f"var R{i}=comp.layers.add(iv); R{i}.startTime={s(ta) - rs:.4f}; R{i}.inPoint={s(ta):.4f}; R{i}.outPoint={s(tb):.4f};")
    v = lay("dim"); opa(v, [[s(T_DIM), 0], [s(T_DIM) + 0.3, 100], [s(T_IN), 100], [s(T_IN) + 0.3, 0]])

    # 돋보기: 녹화 사본에 마스크(카드 부분) → 제자리에서 2.2배로 떠오름
    def magnify(box, t_in, t_out, tag):
        cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        for i, (ta, tb, rs, _) in enumerate(M.SEGS):
            if tb <= t_in or ta >= t_out + 0.35:
                continue
            g = f"G{tag}{i}"
            a(f"var {g}=comp.layers.add(iv); {g}.startTime={s(ta) - rs:.4f}; {g}.inPoint={s(ta):.4f}; {g}.outPoint={s(tb):.4f}; {g}.motionBlur=true;")
            a(f"var mk{g}={g}.property('ADBE Mask Parade').addProperty('ADBE Mask Atom'); var sh{g}=new Shape(); sh{g}.vertices=[[{box[0]},{box[1]}],[{box[2]},{box[1]}],[{box[2]},{box[3]}],[{box[0]},{box[3]}]]; sh{g}.closed=true; mk{g}.property('ADBE Mask Shape').setValue(sh{g});")
            a(f"{g}.transform.anchorPoint.setValue([{cx},{cy}]);")
            a(f"keys({g}.transform.position,[[{s(t_in)},[{cx},{cy}]],[{s(t_in) + 0.45:.3f},[{POP_C[0]},{POP_C[1]}]],[{s(t_out)},[{POP_C[0]},{POP_C[1]}]],[{s(t_out) + 0.35:.3f},[{cx},{cy}]]]); eo({g}.transform.position);")
            a(f"keys({g}.transform.scale,[[{s(t_in)},[100,100]],[{s(t_in) + 0.45:.3f},[{MAG * 100},{MAG * 100}]],[{s(t_out)},[{MAG * 100},{MAG * 100}]],[{s(t_out) + 0.35:.3f},[100,100]]]); eo({g}.transform.scale);")
            a(f"keys({g}.transform.opacity,[[{s(t_in) - 0.001:.3f},0],[{s(t_in)},100],[{s(t_out) + 0.3:.3f},100],[{s(t_out) + 0.35:.3f},0]]);")

    fr = lay("frameT"); opa(fr, life(T_DIM + 0.25, T_TOUT, fi=0.2, fo=0.2))
    magnify(TESLA, T_DIM, T_TOUT, "T")
    for nm, t in (("o_bg", T_BG), ("o_design", T_DESIGN), ("o_layout", T_LAYOUT)):
        v = lay(nm); opa(v, life(t, T_TOUT - 0.05, fi=0.1, fo=0.15)); pop(v, t, 108, 0.24)
        x, y, w, h = BOX[f"c_{nm}"]
        v = lay(f"c_{nm}", anchor=(0, h / 2)); opa(v, life(t + 0.1, T_TOUT - 0.05, fi=0.05, fo=0.15)); grow(v, t + 0.1, 0.25)
        v = lay(f"l_{nm}"); opa(v, life(t + 0.25, T_TOUT - 0.05, fi=0.1, fo=0.15)); pop(v, t + 0.25)
    fr = lay("frameV"); opa(fr, life(T_VID + 0.25, T_IN, fi=0.2, fo=0.2))
    magnify(VIDEO, T_VID, T_IN, "V")
    v = lay("o_vid"); opa(v, life(T_3S, T_IN - 0.05, fi=0.1, fo=0.15)); pop(v, T_3S, 106, 0.24)
    x, y, w, h = BOX["c_3s"]
    v = lay("c_3s", anchor=(0, h)); opa(v, life(T_3S + 0.1, T_IN - 0.05, fi=0.05, fo=0.15)); grow(v, T_3S + 0.1, 0.25)
    v = lay("l_3s"); opa(v, life(T_3S + 0.25, T_IN - 0.05, fi=0.1, fo=0.15)); pop(v, T_3S + 0.25)
    v = lay("tbar"); opa(v, life(T_3S + 0.2, T_IN - 0.05, fi=0.1, fo=0.15))
    v = lay("tbar_t"); opa(v, life(T_3S + 0.3, T_IN - 0.05, fi=0.1, fo=0.15))
    v = lay("o_boss"); opa(v, life(T_BOSS, T_STRUCT - 0.1, fi=0.1, fo=0.2)); pop(v, T_BOSS, 130, 0.24)
    x, y, w, h = BOX["c_boss"]
    v = lay("c_boss", anchor=(0, h / 2)); opa(v, life(T_BOSS + 0.1, T_STRUCT - 0.1, fi=0.05, fo=0.2)); grow(v, T_BOSS + 0.1, 0.25)
    v = lay("l_boss"); opa(v, life(T_BOSS + 0.25, T_STRUCT - 0.1, fi=0.1, fo=0.2)); pop(v, T_BOSS + 0.25)
    v = lay("struct"); opa(v, life(T_STRUCT, T_IN - 0.05, fi=0.15, fo=0.15)); pop(v, T_STRUCT, 85, 0.26)

    # ── 판 ──
    a("var RIG=comp.layers.addNull(); RIG.name='RIG'; RIG.enabled=false; RIG.transform.position.setValue([0,0]);")
    a(f"keys(RIG.transform.position,[[{s(T_IN)},[{W},0]],[{s(T_IN) + 0.45:.3f},[0,0]],[{s(T_OUT)},[0,0]],[{s(T_OUT) + 0.36:.3f},[{-W},0]]]); eo(RIG.transform.position);")
    lay("board", rig=True)
    # 캐릭터(동작 바꿀 때 딱, 들썩임)
    for nm, ta, tb in (("ch_note", T_IN, T_TRY[0]), ("ch_practice", T_TRY[0], T_FIRE), ("ch_fire", T_FIRE, T1)):
        x, y, w, h = BOX[nm]
        v = lay(nm, anchor=(w / 2, h))
        a(f"{v}.transform.position.expression=\"value+[{slide},3*Math.sin(time*3.4)]\";")
        if tb < T1:
            opa(v, [[max(0, s(ta) - 0.001), 0], [s(ta), 100], [s(tb), 0]], hold_=True)
        else:
            opa(v, [[s(ta) - 0.001, 0], [s(ta), 100]], hold_=True)
        if ta > T_IN:
            a(f"keys({v}.transform.scale,[[{s(ta)},[108,92]],[{s(ta) + 0.12:.3f},[96,105]],[{s(ta) + 0.26:.3f},[100,100]]]);")
    # 노트
    v = lay("note", rig=True); opa(v, life(T_IN + 0.3, T_NOTEOUT, fi=0.2, fo=0.3))
    for k, t in enumerate(T_NOTE):
        v = lay(f"cb{k}", rig=True); opa(v, life(t, T_NOTEOUT, fi=0.08, fo=0.3))
        v = lay(f"row{k}", rig=True); opa(v, life(t, T_NOTEOUT, fi=0.02, fo=0.3)); wipe(v, t, t + 0.45)
        v = lay(f"ck{k}", rig=True); opa(v, life(t + 0.4, T_NOTEOUT, fi=0.02, fo=0.3)); wipe(v, t + 0.4, t + 0.6)
    v = lay("why_hl", rig=True); a(f"{v}.blendingMode=BlendingMode.MULTIPLY;"); opa(v, life(T_WHY + 0.5, T_NOTEOUT, fi=0.02, fo=0.3)); wipe(v, T_WHY + 0.5, T_WHY + 0.9)
    v = lay("why", rig=True); opa(v, life(T_WHY, T_NOTEOUT, fi=0.02, fo=0.3)); wipe(v, T_WHY, T_WHY + 0.45)
    v = lay("borrow", rig=True); opa(v, life(T_WRITE, T_NOTEOUT, fi=0.02, fo=0.3)); wipe(v, T_WRITE, T_WRITE + 0.8)
    v = lay("borrow_ul", rig=True); opa(v, life(T_GOOD, T_NOTEOUT, fi=0.02, fo=0.3)); wipe(v, T_GOOD, T_GOOD + 0.45)
    # 세팅 vs 콘텐츠
    for nm, t in (("cmpA", T_SET), ("cmpB", T_CONT)):
        v = lay(nm, rig=True); opa(v, life(t, T_TRY[0] - 0.1, fi=0.15, fo=0.25)); pop(v, t, 85, 0.26)
    # 시도 카드 쌓임
    for k, t in enumerate(T_TRY):
        v = lay(f"try{k}", rig=True); opa(v, life(t, T_FIRE - 0.1, fi=0.12, fo=0.25)); pop(v, t, 80, 0.24)
        x, y, w, h = BOX[f"try{k}"]
        a(f"keys({v}.transform.position,[[{s(t)},[{x + w / 2:.1f},{y + h / 2 + 40:.1f}]],[{s(t) + 0.26:.3f},[{x + w / 2:.1f},{y + h / 2:.1f}]]]); eo({v}.transform.position);")
    v = lay("try_lab", rig=True); opa(v, life(T_TRY[4] + 0.3, T_FIRE - 0.1, fi=0.12, fo=0.25)); pop(v, T_TRY[4] + 0.3)
    # 노력
    v = lay("effort", rig=True); opa(v, life(T_FIRE + 0.1, T1, fi=0.12)); pop(v, T_FIRE + 0.1, 80, 0.26)
    v = lay("effort_hl", rig=True); a(f"{v}.blendingMode=BlendingMode.MULTIPLY;"); opa(v, life(T_EFFORT, T1, fi=0.02)); wipe(v, T_EFFORT, T_EFFORT + 0.35)
    v = lay("effort_sub", rig=True); opa(v, life(T_EFFORT + 0.45, T1, fi=0.12)); pop(v, T_EFFORT + 0.45)
    v = lay("spark", anchor=(10, 120), rig=True)
    a(f"keys({v}.transform.opacity,[[{s(T_EFFORT) - 0.001:.3f},0],[{s(T_EFFORT) + 0.03:.3f},100],[{s(T_EFFORT) + 0.35:.3f},100],[{s(T_EFFORT) + 0.55:.3f},0]]);")
    a(f"keys({v}.transform.scale,[[{s(T_EFFORT)},[35,35]],[{s(T_EFFORT) + 0.16:.3f},[100,100]],[{s(T_EFFORT) + 0.55:.3f},[115,115]]]); eo({v}.transform.scale);")
    a(f"var rq=app.project.renderQueue.items.add(comp); var om=rq.outputModule(1); om.applyTemplate({js('고품질')}); om.file=new File({js(str(out_mov))});")
    a("log('ok bisa20'); })();")
    assert T_OUT + 0.36 < T1
    return "\n".join(L)


M.SND_FIX = {
    "dim":   ("휙２.mp3", 0.6, -6, "peak"),                          # 돋보기 떠오름(화면 확대 결)
    "mark1": ("KN_pepSound1.wav", 0.4, 8, "onset"),
    "mark2": ("KN_pepSound2.wav", 0.4, 8, "onset"),
    "pop":   ("ML_Cartoon bubbles popping.wav", 0.5, 5, "onset"),
    "in":    ("휙２.mp3", 0.6, 4, "peak"),
    "pen1":  ("SEL_シャーペンで字を書く.mp3", -0.45, 4, "onset"),        # 노트 손글씨(쓰는 동안만)
    "pen2":  ("24. 연필.mp3", -0.45, 3, "onset"),
    "hl":    ("SEL_ゲージ回復1.mp3", 0.6, 12, "onset"),
    "ok":    ("맑은소리.mp3", 0.8, 7, "onset"),
    "no":    ("KN_error_003.wav", 0.5, 5, "onset"),
    "key":   ("SEL_キラッ1.mp3", 0.7, -1, "onset"),
    "back":  ("휙1.mp3", 0.7, 8, "peak"),
    "zout":  ("휙1.mp3", 0.7, -6, "peak"),                          # 돋보기 제자리로
    "ul":    ("SEL_油性マーカーで字を書く.mp3", -0.45, 3, "onset"),   # 밑줄 = 마커
}
M.EVENTS = [(T_DIM + 0.2, "dim"), (T_BG, "mark1"), (T_DESIGN, "mark2"), (T_LAYOUT, "mark1"), (T_TOUT + 0.15, "zout"), (T_VID + 0.2, "dim"), (T_3S, "mark2"),
            (T_BOSS, "pop"), (T_STRUCT, "mark1"), (T_IN + 0.25, "in"), (T_NOTE[0], "pen1"), (T_NOTE[1], "pen2"), (T_NOTE[2], "pen1"),
            (T_NOTE[3], "pen2"), (T_WHY, "pen1"), (T_WHY + 0.5, "hl"), (T_WRITE, "pen2"), (T_GOOD, "ul"), (T_NOTEOUT + 0.1, "zout"), (T_SET, "ok"), (T_CONT, "no"),
            (T_TRY[0], "mark1"), (T_TRY[2], "mark2"), (T_TRY[4], "pop"), (T_FIRE + 0.1, "mark1"), (T_EFFORT, "key"), (T_OUT + 0.2, "back")]
M.EVENTS.sort()

_role = M.SFX.role


def _role_zoom(r, mx, rel, align):
    t = _role(r, mx, rel, align)
    return t[:4] + (-6,) + t[5:] if (Path(r["파일"]).name in ("휙２.mp3", "휙1.mp3") and rel == -6) else t


M.SFX.role = _role_zoom

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
