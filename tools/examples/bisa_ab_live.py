# -*- coding: utf-8 -*-
r"""빡이사DB 본편 13 2판 «그러면 상세 타겟팅 건 광고 하나 ~ 실력 많이 좋아지실 거예요» (시퀀스 1044.56~1075.958)
1판(bisa_ab_setup.py) 반려 10-08 «글자가 생길 때 나오는 포인트들도 없고 · 왼쪽 상단엔 글자도 깨지고 · 연출도 없고 해서 몰입이 안 됨».
→ 2판: 실제 광고 세트 편집 화면에서
  · 커서가 칸·줄·스위치를 실제로 누르고(클릭 고리) 이름은 타자(캐럿)로 바뀜
  · 글자·알약이 뜰 때마다 강조 포인트(반짝 선 + 테두리 번짐, 튕김 없이 감속)
  · 카메라(CAM 널, 식으로 따라감)가 말하는 칸으로 밀고 당김 — 칸 → 트리 → 지표 카드(뒤 어둡게) → 스위치 → 순환 카드
  · 녹화 글자를 덮은 판은 투명도를 낮추지 않는다(꺼짐 = 불투명 회색판 교체) — 1판 «글자 깨짐» 원인

  python bisa_ab_live.py [--조각만] [--소리만]
    → 빡이사DB\납품\13_AB세팅_1044.56~.mp4 (1판과 같은 이름 덮어쓰기) · _효과음.xml · _미리보기.mp4
단어 시각(faster-whisper, _tmp/w13/words.txt): 그러면 1044.56 · 상세 1045.14 · 타겟팅 1045.58 · 광고 1046.58 · 똑같은 1047.94 · 영상 1050.56 ·
  상세 1051.58 · 논 1054.06 · 타겟을 1055.10 · 총 1056.72 · 6만원 1059.46 · 6만원 1059.92 · 12만원 1060.74 · 며칠 1062.52 · 3일 1063.12 ·
  지켜보시고 1063.62 · 지표를 1064.34 · 여기가 1065.84 · 더 잘 1066.48 · 들어오네 1066.80 · 이어가시고 1068.04 · 꺼버리고 1069.32 ·
  계속 1071.58 · 데이터 1071.80 · 개선 1072.78 · 실력 1074.46 · 좋아지실 1075.02
"""

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))   # tools/ (config.py)
import config  # noqa: E402
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
import rf3_ae as AE  # noqa: E402
import bisa_web_vs_instant as M  # noqa: E402
import bisa_ab_setup as V1  # noqa: E402  (컷 조각·녹화 프레임·트리 줄 좌표 재사용)

M.T0, M.T1 = V1.M.T0, V1.M.T1
M.DUR = M.T1 - M.T0
M.SEGS = V1.M.SEGS
M.NAME = "13_AB세팅"
M.SFX_DIR = (config.WORK / "효과음13")
M.WORK = (config.WORK / "빡이사" / "ae13b")
W, H = M.W, M.H
T0, T1 = M.T0, M.T1
WORK = M.WORK
FRAME = V1.FRAME
PRET = V1.PRET
PRET_X = PRET                                              # ExtraBold 없음
MALG = V1.MALG
NOTO = str(config.FONTS["noto_sans_kr"])             # 줄 이름 — 맑은 고딕 25px 은 «같» 받침이 뭉개짐(10-08 «또 깨졌어»)


def ui_font(n=25, wght=500):
    f = ImageFont.truetype(NOTO, n)
    f.set_variation_by_axes([wght])
    return f
INK, GREY, BLUE, RED, OFF = (28, 30, 33), (95, 99, 104), (0, 100, 224), (214, 48, 40), (196, 199, 204)
DIM_INK = (160, 164, 170)
S, A = V1.S, V1.A                                          # 녹화 점 p → S·(p − A) (기본 틀)
ROW_SET, ROW_AD, FIELD = V1.ROW_SET, V1.ROW_AD, V1.FIELD
PIP, CAPTION = V1.PIP, V1.CAPTION

# ── 시각 ──
T_ZOOM, T_OUT = 1044.56, 1075.45
T_FCLICK, T_CHIPS = 1045.40, [1045.58, 1045.78, 1045.98]
T_ACLICK, T_ATYPE = 1046.50, (1046.58, 1047.20)
T_DCLICK, T_DTYPE = 1047.80, (1047.94, 1048.62)
T_VIDEO, T_APULSE = 1050.56, 1051.94
T_GRAB, T_DUP, T_BTYPE = 1053.70, 1054.06, (1054.86, 1055.50)
T_TWO = 1056.72
T_B60A, T_B60B, T_SUM = 1059.46, 1059.92, 1060.74
T_CARD, T_3DAY, T_DAYS = 1062.52, 1063.12, [1063.62, 1064.06, 1064.50]
T_WIN, T_WINTXT, T_CARDOUT = 1065.84, 1066.48, 1067.62
T_KEEP, T_OFFCLICK = 1068.04, 1069.32
T_LOOP, T_AN, T_IMP, T_SKILL = 1071.00, 1071.80, 1072.78, 1074.46

# ── 카메라(CAM: 화면 = P + k·(p − 가운데)) ──
C = (W / 2, H / 2)


def cam_at(k, f, g):
    """기본 틀의 점 f 를 화면 g 에 놓는 CAM 위치 — 기본 틀(0~1920×0~1080) 밖이 보이지 않게 묶는다
    (밖 = 녹화본 주소창·북마크·탭, 10-08 정지 화면 확인)."""
    px, py = g[0] - k * (f[0] - C[0]), g[1] - k * (f[1] - C[1])
    px = min(max(px, W - k * C[0]), k * C[0])
    py = min(max(py, H - k * C[1]), k * C[1])
    return (px, py, k)


SH_ID = (C[0], C[1], 1.0)
SH_FIELD = cam_at(1.08, (1366, 815), (1330, 760))
SH_TREE = cam_at(1.14, (368, 200), (470, 300))
SH_TREE2 = cam_at(1.18, (368, 200), (474, 306))
SH_TOG = cam_at(1.25, (560, 200), (700, 330))
CAM_KEYS = [(T_ZOOM + 0.5, SH_ID), (T_ZOOM + 0.62, SH_ID), (T_FCLICK + 0.2, SH_FIELD), (1046.02, SH_FIELD), (1046.42, SH_TREE),
            (1058.9, SH_TREE2), (T_CARD - 0.05, SH_TREE2), (T_CARD + 0.55, SH_ID), (T_CARDOUT - 0.05, SH_ID), (T_CARDOUT + 0.5, SH_TOG),
            (1070.30, SH_TOG), (1070.85, SH_ID)]


def cam_val(t):
    ks = [(T_ZOOM, SH_ID)] + CAM_KEYS + [(T1, SH_ID)]
    for (ta, a), (tb, b) in zip(ks, ks[1:]):
        if ta <= t <= tb:
            u = 0 if tb == ta else (t - ta) / (tb - ta)
            return tuple(a[i] + (b[i] - a[i]) * u for i in range(3))
    return SH_ID


def to_screen(p, t):
    px, py, k = cam_val(t)
    return (px + k * (p[0] - C[0]), py + k * (p[1] - C[1]))


BOX = {}
CAMMED = set()                                              # CAM 을 따라가는 레이어(기본 틀 좌표)
LIFE = {}                                                   # 이름 → (들어옴, 나감) — 겹침 검사를 시각별로


def font(n, f=PRET):
    return ImageFont.truetype(f, n)


def tl(t, f):
    return ImageDraw.Draw(Image.new("RGBA", (1, 1))).textlength(t, font=f)


def save(name, im, xy, cam=True, life=None):
    xy = (int(round(xy[0])), int(round(xy[1])))
    im.save(WORK / f"{name}.png")
    a = np.array(im)[..., 3] > 60
    ys, xs = np.where(a)
    BOX[name] = (int(xy[0] + xs.min()), int(xy[1] + ys.min()), int(xy[0] + xs.max()), int(xy[1] + ys.max()))
    BOX[name + "@"] = (int(xy[0]), int(xy[1]), im.width, im.height)
    if cam:
        CAMMED.add(name)
    if life:
        LIFE[name] = life


def pill(t, size, fg, bg, padx=16, h=None, f=None, shadow=True):
    f = f or font(size)
    w = int(tl(t, f)) + 2 * padx
    h = h or int(size * 1.7)
    m = 14
    im = Image.new("RGBA", (w + 2 * m, h + 2 * m), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((m, m + 5, m + w, m + h + 5), h // 2, fill=(10, 30, 70, 70))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    ImageDraw.Draw(im).rounded_rectangle((m, m, m + w, m + h), h // 2, fill=bg + (255,))
    ImageDraw.Draw(im).text((m + w / 2, m + h / 2), t, font=f, fill=fg, anchor="mm")
    return im


def card_bg(w, h, r=24, m=30):
    im = Image.new("RGBA", (w + 2 * m, h + 2 * m), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((m, m + 10, m + w, m + h + 10), r, fill=(5, 20, 50, 90))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    ImageDraw.Draw(im).rounded_rectangle((m, m, m + w, m + h), r, fill=(255, 255, 255, 255))
    return im


# ── 트리 줄(녹화 실제 줄 그림 · 글자만 바꿈) ──
def row_base(box, grey=False):
    fr = Image.open(FRAME).convert("RGBA")
    x0, y0, x1, y1 = box
    im = fr.crop(box).resize((int((x1 - x0) * S), int((y1 - y0) * S)), Image.LANCZOS)
    a = np.asarray(im.convert("RGB")).astype(int)
    bg = tuple(int(v) for v in np.median(a[:, int(im.width * 0.8):int(im.width * 0.95)].reshape(-1, 3), 0))
    tx = int(((178 if box == ROW_SET else 186) - x0) * S)
    ImageDraw.Draw(im).rectangle((tx - 14, 4, im.width - 2, im.height - 4), fill=bg + (255,))
    if grey:                                                # 꺼짐: 아이콘까지 회색으로 바래게(불투명 그대로)
        g = np.asarray(im.convert("L")).astype(float)
        g = 255 - (255 - g) * 0.35
        im = Image.merge("RGBA", [Image.fromarray(g.astype(np.uint8))] * 3 + [Image.new("L", im.size, 255)])
        tint = Image.new("RGBA", im.size, (236, 238, 241, 255))
        im = Image.blend(im, tint, 0.35)
    return im, tx


def row_label(box, label, col=INK):
    _, tx = row_base(box)
    w, h = int((box[2] - box[0]) * S), int((box[3] - box[1]) * S)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((tx, h / 2), label, font=ui_font(), fill=col + (255,), anchor="lm")
    end = tx + tl(label, ui_font())
    return im, tx, end


def toggle(on):
    w, h = 56, 32
    im = Image.new("RGBA", (w + 8, h + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((4, 4, 4 + w, 4 + h), h // 2, fill=(BLUE if on else OFF) + (255,))
    cx = 4 + (w - h / 2 if on else h / 2)
    d.ellipse((cx - 12, 4 + 4, cx + 12, 4 + 28), fill=(255, 255, 255, 255))
    return im


# ── 강조 포인트(반짝 선 · 테두리 번짐) ──
def spark_img(col=BLUE):
    n = 104
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for ang in (-90, -45, 0):                               # 왼쪽 아래 모서리에서 위·대각·오른쪽으로 벌어지는 세 줄
        r0, r1 = 30, 70 if ang == -45 else 58
        c, s_ = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        p0, p1 = (8 + r0 * c, n - 8 + r0 * s_), (8 + r1 * c, n - 8 + r1 * s_)
        d.line((p0, p1), fill=col + (255,), width=9)
        for p in (p0, p1):
            d.ellipse((p[0] - 4, p[1] - 4, p[0] + 4, p[1] + 4), fill=col + (255,))
    return im


def ring_img(w, h, r, col=BLUE, width=5):
    m = 8
    im = Image.new("RGBA", (w + 2 * m, h + 2 * m), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((m, m, m + w, m + h), r, outline=col + (255,), width=width)
    return im


POINTS = []                                                 # (대상 이름, 시각, 색, 반짝 여부)


def point(name, t, col=BLUE, spark=True, r=None):
    POINTS.append((name, t, col, spark, r))


def make_points():
    for k, (name, t, col, spark, r) in enumerate(POINTS):
        x0, y0, x1, y1 = BOX[name]
        cam = name in CAMMED
        w, h = x1 - x0 + 12, y1 - y0 + 12
        save(f"ring{k}", ring_img(w, h, r if r is not None else min(h // 2, 18), col), (x0 - 6 - 8, y0 - 6 - 8), cam=cam)
        if spark:
            im = spark_img(col)
            save(f"spark{k}", im, (x1 - 6, y0 - im.height + 14), cam=cam)


def cursor_img():
    cur = Image.new("RGBA", (64, 84), (0, 0, 0, 0))
    pts = [(4, 4), (4, 60), (18, 47), (29, 72), (40, 67), (29, 43), (48, 43)]
    sh = Image.new("RGBA", cur.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).polygon([(x + 3, y + 4) for x, y in pts], fill=(0, 0, 0, 110))
    cur.alpha_composite(sh.filter(ImageFilter.GaussianBlur(3)))
    ImageDraw.Draw(cur).polygon(pts, fill=(255, 255, 255, 255))
    ImageDraw.Draw(cur).line(pts + [pts[0]], fill=(20, 20, 20, 255), width=3)
    return cur


# 기본 틀 좌표
def sc(x, y):
    return S * (x - A[0]), S * (y - A[1])


SX, SY = sc(ROW_SET[0], ROW_SET[1])
AX, AY = sc(ROW_AD[0], ROW_AD[1])
RH = (ROW_SET[3] - ROW_SET[1]) * S
RW = (ROW_SET[2] - ROW_SET[0]) * S
GAP = 2 * RH + 30


# ── 조각 ──────────────────────────────────────────────────────
def pieces():
    WORK.mkdir(parents=True, exist_ok=True)
    BOX.clear(), CAMMED.clear(), POINTS.clear(), LIFE.clear()
    # 세트 A·광고 A: 빈 판(불투명) + 타자 글자
    for nm, box, x, y, lab in (("A_set", ROW_SET, SX, SY, "세트 A · 상세 타겟팅"), ("A_ad", ROW_AD, AX, AY, "광고 · 같은 영상"),
                               ("B_set", ROW_SET, SX, SY + GAP, "세트 B · 논타겟팅"), ("B_ad", ROW_AD, AX, AY + GAP, "광고 · 같은 영상")):
        im, tx = row_base(box)
        save(f"base_{nm}", im, (x, y))
        lb, tx, end = row_label(box, lab)
        save(f"lab_{nm}", lb, (x, y))
        BOX[f"lab_{nm}#"] = (x + tx, x + end, y + RH / 2)   # 타자 시작·끝 x, 가운데 y
        g, _ = row_base(box, grey=True)
        lg, _, _ = row_label(box, lab, DIM_INK)
        g.alpha_composite(lg)
        save(f"off_{nm}", g, (x, y))
    # 복제 유령(세트 A + 광고 A 를 한 덩어리로, 그림자)
    ga, _ = row_base(ROW_SET)
    ga.alpha_composite(row_label(ROW_SET, "세트 A · 상세 타겟팅")[0])
    gb, _ = row_base(ROW_AD)
    gb.alpha_composite(row_label(ROW_AD, "광고 · 같은 영상")[0])
    m = 18
    gh = Image.new("RGBA", (int(RW) + 2 * m, int(AY + RH - SY) + 2 * m), (0, 0, 0, 0))
    sh = Image.new("RGBA", gh.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((m, m + 8, m + RW, m + AY + RH - SY + 8), 8, fill=(10, 30, 70, 110))
    gh.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    gh.alpha_composite(ga, (m, m))
    gh.alpha_composite(gb, (m, m + int(AY - SY)))
    ImageDraw.Draw(gh).rectangle((m, m, m + RW - 1, m + AY + RH - SY - 1), outline=BLUE + (255,), width=3)
    save("ghost", gh, (SX - m, SY - m))
    save("ghost_lab", row_label(ROW_SET, "세트 A · 상세 타겟팅")[0], (SX, SY + GAP))   # 복제 직후 세트 B 줄 글자(아직 A 이름)
    # 캐럿
    im = Image.new("RGBA", (4, 32), BLUE + (255,))
    save("caret", im, (0, 0))
    # 상세 타겟팅 칸: 포커스 테두리 + 칩 셋
    fx0, fy0 = sc(FIELD[0], FIELD[1])
    fx1, fy1 = sc(FIELD[2], FIELD[3])
    im = Image.new("RGBA", (int(fx1 - fx0) - 16, int(fy1 - fy0) - 8), (255, 255, 255, 255))
    save("field_patch", im, (fx0 + 8, fy0 + 4))
    im = ring_img(int(fx1 - fx0), int(fy1 - fy0), 10, BLUE, 4)
    save("field_focus", im, (fx0 - 8, fy0 - 8))
    x = fx0 + 22
    for k, t in enumerate(("피부 관리", "뷰티", "화장품")):
        c = pill(t, 25, BLUE, (225, 236, 252), padx=16, h=42, f=font(25), shadow=False)
        save(f"chip{k}", c, (x - 14, (fy0 + fy1) / 2 - c.height / 2))
        x += c.width - 28 + 10
    BOX["chips"] = (BOX["chip0"][0], BOX["chip0"][1], BOX["chip2"][2], BOX["chip2"][3])
    point("chips", T_CHIPS[2] + 0.06)
    # 줄 강조
    for nm in ("A_set", "A_ad", "B_set"):
        BOX[f"row_{nm}"] = BOX[f"base_{nm}"]
    point("row_A_set", T_ATYPE[1], r=8)
    point("row_A_ad", T_DTYPE[1], r=8)
    point("row_B_set", T_BTYPE[1], r=8)
    # «영상 1개» 배지(광고 A 줄 오른쪽)
    im = pill("     영상 1개", 24, (255, 255, 255), INK, padx=16, h=40)
    ImageDraw.Draw(im).polygon([(14 + 18, 14 + 11), (14 + 18, 14 + 29), (14 + 33, 14 + 20)], fill=(255, 255, 255, 255))   # 재생 표시(글꼴 대신 그림)
    save("video", im, (SX + RW + 14, AY + RH / 2 - im.height / 2))
    point("video", T_VIDEO + 0.1, spark=True)
    # A 줄 다시 짚기(«상세 타겟팅 건 광고 하나»)
    BOX["rowA_both"] = (int(SX), int(SY), int(SX + RW), int(AY + RH))
    point("rowA_both", T_APULSE, spark=False, r=8)
    # 광고 2개: 두 광고 줄 오른쪽 괄호 + 배지
    bx = SX + RW + 12
    y_a, y_b = AY + RH / 2, AY + GAP + RH / 2
    im = Image.new("RGBA", (40, int(y_b - y_a) + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.line(((4, 10), (20, 10), (20, im.height - 10), (4, im.height - 10)), fill=BLUE + (255,), width=5, joint="curve")
    d.line(((20, im.height / 2), (36, im.height / 2)), fill=BLUE + (255,), width=5)
    save("brace2", im, (bx, y_a - 10))
    im = pill("광고 2개", 28, (255, 255, 255), BLUE, padx=20, h=48)
    save("two", im, (bx + 40, (y_a + y_b) / 2 - im.height / 2))
    point("two", T_TWO + 0.12)
    # 예산: 세트 줄 안 오른쪽 알약 → 괄호 → 합계
    for nm, y in (("b60a", SY), ("b60b", SY + GAP)):
        im = pill("₩60,000/일", 23, (255, 255, 255), INK, padx=14, h=38)
        save(nm, im, (SX + RW - im.width + 6, y + RH / 2 - im.height / 2))
    point("b60a", T_B60A + 0.1)
    point("b60b", T_B60B + 0.1)
    y_a, y_b = SY + RH / 2, SY + GAP + RH / 2
    im = Image.new("RGBA", (40, int(y_b - y_a) + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.line(((4, 10), (20, 10), (20, im.height - 10), (4, im.height - 10)), fill=INK + (255,), width=5, joint="curve")
    d.line(((20, im.height / 2), (36, im.height / 2)), fill=INK + (255,), width=5)
    save("brace_sum", im, (bx, y_a - 10))
    im = pill("하루 ₩120,000", 34, (255, 255, 255), BLUE, padx=24, h=60)
    save("sum", im, (bx + 40, (y_a + y_b) / 2 - im.height / 2))
    point("sum", T_SUM + 0.12)
    # 스위치(광고 줄 오른쪽 끝) + 유지·끔 표
    for nm, y in (("A", AY), ("B", AY + GAP)):
        for st in ("on", "off"):
            im = toggle(st == "on")
            save(f"tog{nm}_{st}", im, (SX + RW - im.width - 10, y + RH / 2 - im.height / 2))
    im = pill("이어 가기", 26, (255, 255, 255), BLUE, padx=18, h=44)
    save("keep", im, (SX + RW + 16, AY + GAP + RH / 2 - im.height / 2))
    point("keep", T_KEEP + 0.12)
    im = pill("끄기", 26, (255, 255, 255), RED, padx=18, h=44)
    save("offtag", im, (SX + RW + 16, AY + RH / 2 - im.height / 2))
    point("offtag", T_OFFCLICK + 0.15, col=RED)
    BOX["togB_on_"] = BOX["togB_on"]
    point("togB_on_", T_KEEP, spark=False)
    save("cursor", cursor_img(), (0, 0))
    ring = Image.new("RGBA", (96, 96), (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse((6, 6, 89, 89), outline=BLUE + (230,), width=6)
    save("click_ring", ring, (0, 0))

    # ── 지표 카드(화면 좌표, 뒤 어둡게) ──
    save("dim", Image.new("RGBA", (W, H), (8, 14, 28, 150)), (0, 0), cam=False)
    cx0, cy0, cw, ch = 780, 150, 1060, 600
    c = card_bg(cw, ch)
    d = ImageDraw.Draw(c)
    p = 30
    d.text((p + 50, p + 62), "지표 보기", font=font(44, PRET_X), fill=INK, anchor="lm")
    d.text((p + 50, p + 112), "같은 영상 · 세트별 DB 수집", font=font(26), fill=GREY, anchor="lm")
    d.line((p + 50, p + 160, p + cw - 50, p + 160), fill=(232, 234, 238), width=2)
    for j, t in enumerate(("세트 A", "세트 B")):
        y = p + 250 + j * 150
        d.text((p + 50, y - 20), t, font=font(32, PRET_X), fill=INK, anchor="lm")
        d.text((p + 50, y + 22), ("상세 타겟팅", "논타겟팅")[j], font=font(24), fill=GREY, anchor="lm")
        d.rounded_rectangle((p + 290, y - 20, p + 290 + 620, y + 20), 20, fill=(236, 239, 244, 255))
    save("card", c, (cx0 - p, cy0 - p), cam=False)
    # 날짜 칩(카드 오른쪽 위)
    for k in range(3):
        for st in ("off", "on"):
            im = pill(f"{k + 1}일", 26, (255, 255, 255) if st == "on" else GREY, BLUE if st == "on" else (236, 239, 244), padx=18, h=44, shadow=False)
            save(f"day{k}_{st}", im, (cx0 + cw - 3 * 104 - 30 + k * 104 - 14, cy0 + 42 - 14), cam=False)
    BOX["days"] = (BOX["day0_off"][0], BOX["day0_off"][1], BOX["day2_off"][2], BOX["day2_off"][3])
    CAMMED.discard("days")
    point("days", T_3DAY)
    lens = {"A": [0.18, 0.30, 0.38], "B": [0.30, 0.62, 0.92]}  # 그림 비율(숫자 아님 — «B 가 더 잘 들어옴»만 보이게)
    for j, key in enumerate("AB"):
        im = Image.new("RGBA", (620, 40), (0, 0, 0, 0))
        ImageDraw.Draw(im).rounded_rectangle((0, 0, 619, 39), 20, fill=(BLUE if key == "B" else (126, 150, 190)) + (255,))
        save(f"bar{key}", im, (cx0 + 290, cy0 + 250 + j * 150 - 20), cam=False)
    BAR_LENS.update(lens)
    BOX["rowB_card"] = (cx0 + 30, cy0 + 250 + 150 - 62, cx0 + cw - 30, cy0 + 250 + 150 + 56)
    point("rowB_card", T_WIN, r=16)
    im = pill("여기가 DB 더 잘 들어오네!", 32, (255, 255, 255), BLUE, padx=26, h=58)
    save("wintxt", im, (cx0 + cw - im.width + 4, cy0 + ch - 92 - 14), cam=False)
    point("wintxt", T_WINTXT + 0.12)

    # ── 순환 카드(데이터 분석 ⇄ 개선 → 실력) ──
    lx0, ly0, lw, lh = 860, 170, 960, 600
    save("loopcard", card_bg(lw, lh), (lx0 - 30, ly0 - 30), cam=False)
    cxl, cyl, R = lx0 + 300, ly0 + 300, 190                # 순환 고리 가운데
    ring = Image.new("RGBA", (2 * R + 80, 2 * R + 80), (0, 0, 0, 0))
    d = ImageDraw.Draw(ring)
    o = 40
    for a0, a1 in ((200, 330), (20, 150)):                  # 두 반원 화살표(돌아감)
        d.arc((o, o, o + 2 * R, o + 2 * R), a0, a1, fill=BLUE + (255,), width=12)
        ang = math.radians(a1)
        tip = (o + R + R * math.cos(ang), o + R + R * math.sin(ang))
        tang = (-math.sin(ang), math.cos(ang))
        nrm = (math.cos(ang), math.sin(ang))
        pts = [(tip[0] + tang[0] * 26, tip[1] + tang[1] * 26), (tip[0] + nrm[0] * 22, tip[1] + nrm[1] * 22), (tip[0] - nrm[0] * 22, tip[1] - nrm[1] * 22)]
        d.polygon(pts, fill=BLUE + (255,))
    save("loopring", ring, (cxl - R - o, cyl - R - o), cam=False)
    for nm, t, y in (("an", "데이터 분석", cyl - R), ("imp", "개선", cyl + R)):
        im = pill(t, 34, INK if nm == "an" else (255, 255, 255), (255, 255, 255) if nm == "an" else BLUE, padx=26, h=60)
        if nm == "an":
            ImageDraw.Draw(im).rounded_rectangle((14, 14, im.width - 14, im.height - 14), 30, outline=INK + (255,), width=3)
        save(nm, im, (cxl - im.width / 2, y - im.height / 2), cam=False)
    point("an", T_AN + 0.12)
    point("imp", T_IMP + 0.12)
    im = Image.new("RGBA", (300, 60), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((150, 30), "계속", font=font(36, PRET_X), fill=BLUE + (255,), anchor="mm")
    save("keepgo", im, (cxl - 150, cyl - 30), cam=False)
    # 실력: 오른쪽 오르는 계단 막대 + 큰 글
    sx0, sy1 = lx0 + 610, ly0 + 470
    for k, hh in enumerate((70, 130, 200, 290)):
        im = Image.new("RGBA", (56, hh), (0, 0, 0, 0))
        ImageDraw.Draw(im).rounded_rectangle((0, 0, 55, hh - 1), 10, fill=(BLUE if k == 3 else (170, 196, 238)) + (255,))
        save(f"step{k}", im, (sx0 + k * 74, sy1 - hh), cam=False)
    im = pill("실력이 좋아져요", 38, (255, 255, 255), BLUE, padx=28, h=66)
    save("skill", im, (lx0 + lw - im.width + 4, ly0 + lh - 100 - 14), cam=False)
    point("skill", T_SKILL + 0.12)
    CAMMED.update({"chips", "row_A_set", "row_A_ad", "row_B_set", "rowA_both", "togB_on_"})
    make_points()
    LIFE.update({"video": (T_VIDEO, T_DUP - 0.3), "brace2": (T_TWO, T_B60A - 0.4), "two": (T_TWO, T_B60A - 0.4),
                 "b60a": (T_B60A, T_CARD), "b60b": (T_B60B, T_CARD), "brace_sum": (T_SUM, T_CARD), "sum": (T_SUM, T_CARD),
                 "keep": (T_KEEP, T_LOOP - 0.6), "offtag": (T_OFFCLICK, T_LOOP - 0.6), "togA_on": (T_KEEP, T_LOOP - 0.6),
                 "togB_on": (T_KEEP, T_LOOP - 0.6), "base_A_set": (T_ACLICK + 0.1, T_CARD), "base_B_ad": (T_DUP + 0.6, T_LOOP - 0.6),
                 "card": (T_CARD + 0.4, T_CARDOUT), "wintxt": (T_WINTXT, T_CARDOUT), "loopcard": (T_LOOP + 0.4, T_OUT), "skill": (T_SKILL, T_OUT)})
    check_layout()


BAR_LENS = {}


def overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def screen_box(n, t):
    x0, y0, x1, y1 = BOX[n]
    if n not in CAMMED:
        return BOX[n]
    p0, p1 = to_screen((x0, y0), t), to_screen((x1, y1), t)
    return (p0[0], p0[1], p1[0], p1[1])


def check_layout():
    """사람 PIP·자막 자리·화면 밖 — CAM 을 따라가는 것은 쓰는 동안의 카메라 위치로 잰다."""
    bad = []
    names = [k for k in BOX if not k.endswith("@") and not k.endswith("#") and k in LIFE]
    for n in names:
        t0, t1 = LIFE[n]
        for t in np.arange(t0, t1, 0.1):
            b = screen_box(n, t)
            for z, zn in ((PIP, "사람 PIP"), (CAPTION, "자막")):
                if overlap(b, z):
                    bad.append(f"{n} {tuple(int(v) for v in b)} ↔ {zn} @{t:.1f}")
                    break
            if b[0] < 10 or b[1] < 8 or b[2] > W - 10 or b[3] > H - 10:
                bad.append(f"{n} {tuple(int(v) for v in b)} 화면 밖 @{t:.1f}")
    if bad:
        raise SystemExit("레이아웃 겹침:\n  " + "\n  ".join(sorted(set(bad))[:40]))
    print("겹침 없음")


# ── 애펙 ───────────────────────────────────────────────────────
CAM_POS = "var c=thisComp.layer('CAM'); var k=c.transform.scale[0]/100; var P=c.transform.position; [P[0]+k*(value[0]-960), P[1]+k*(value[1]-540)]"
CAM_SCL = "var k=thisComp.layer('CAM').transform.scale[0]/100; [value[0]*k, value[1]*k]"


def jsx(out_mov):
    js = AE.js
    s = lambda t: round(t - T0, 4)                         # noqa: E731
    L = ["function eo(p){ for(var k=1;k<=p.numKeys;k++){ var n=p.isSpatial?1:(p.value.length||1), o=[], i=[]; for(var j=0;j<n;j++){ o.push(new KeyframeEase(0,0.1)); i.push(new KeyframeEase(0,85)); } p.setTemporalEaseAtKey(k,i,o); } }",
         "function hold(p){ for(var q=1;q<=p.numKeys;q++){ p.setInterpolationTypeAtKey(q,KeyframeInterpolationType.HOLD); } }",
         f"(function(){{ var comp=app.project.items.addComp('bisa13b',{W},{H},1,{M.DUR:.3f},{M.FPS}); comp.motionBlur=true; comp.shutterAngle=180;"]
    a = L.append
    nv = [0]

    def camify(v):
        a(f"{v}.transform.position.expression={js(CAM_POS)}; {v}.transform.scale.expression={js(CAM_SCL)};")

    def lay(name, anchor=None):
        nv[0] += 1
        v = f"L{nv[0]}"
        x, y, w, h = BOX[name + "@"]
        a(f"var {v}=comp.layers.add(imp({js(str(WORK / f'{name}.png'))})); {v}.motionBlur=true;")
        if anchor:                                          # 기준점(이미지 안 좌표)
            a(f"{v}.transform.anchorPoint.setValue([{anchor[0]},{anchor[1]}]); {v}.transform.position.setValue([{x + anchor[0]:.1f},{y + anchor[1]:.1f}]);")
        else:
            a(f"{v}.transform.position.setValue([{x + w / 2:.1f},{y + h / 2:.1f}]);")
        if name in CAMMED:
            camify(v)
        return v

    def opa(v, k, hold_=False):
        a(f"keys({v}.transform.opacity,{k});")
        if hold_:
            a(f"hold({v}.transform.opacity);")

    def life(t_in, t_out=T_OUT, fi=0.12, fo=0.2):
        return [[max(0, s(t_in) - 0.001), 0], [s(t_in) + fi, 100], [s(t_out), 100], [s(t_out) + fo, 0]]

    def pop(v, t, frm=72, dur=0.2):
        a(f"keys({v}.transform.scale,[[{s(t)},[{frm},{frm}]],[{s(t) + dur:.3f},[100,100]]]); eo({v}.transform.scale);")

    def rise(v, name, t, dy=26, dx=0, dur=0.24):
        x, y, w, h = BOX[name + "@"]
        a(f"keys({v}.transform.position,[[{s(t)},[{x + w / 2 + dx:.1f},{y + h / 2 + dy:.1f}]],[{s(t) + dur:.3f},[{x + w / 2:.1f},{y + h / 2:.1f}]]]); eo({v}.transform.position);")

    def typed(name, t0, t1, t_out=T_OUT):
        """글자를 왼쪽부터 타자(Linear Wipe, 직선) + 캐럿이 따라감."""
        v = lay(name)
        opa(v, [[max(0, s(t0) - 0.001), 0], [s(t0), 100], [s(t_out), 100], [s(t_out) + 0.01, 0]], hold_=True)
        xs, xe, yc = BOX[name + "#"]
        x, y, w, h = BOX[name + "@"]
        c0, c1 = (xs - x) / w * 100, (xe - x) / w * 100
        a(f"var e{v}={v}.Effects.addProperty('ADBE Linear Wipe'); e{v}.property(2).setValue(270); e{v}.property(3).setValue(2); keys(e{v}.property(1),[[{s(t0)},{100 - c0:.2f}],[{s(t1)},{100 - c1 - 1:.2f}]]);")
        cv = lay("caret")
        a(f"keys({cv}.transform.position,[[{s(t0)},[{xs:.1f},{yc:.1f}]],[{s(t1)},[{xe + 4:.1f},{yc:.1f}]]]);")
        k = [[0, 0], [s(t0), 100]]
        tt = t1 + 0.25
        for i in range(2):                                  # 다 쓰고 두 번 깜빡이고 사라짐
            k += [[s(tt), 0], [s(tt + 0.25), 100]]
            tt += 0.5
        k += [[s(tt), 0]]
        opa(cv, k, hold_=True)
        return v

    def do_points():
        for k, (name, t, col, spark, r) in enumerate(POINTS):
            v = lay(f"ring{k}")
            a(f"keys({v}.transform.opacity,[[{s(t) - 0.001:.3f},0],[{s(t) + 0.04:.3f},95],[{s(t) + 0.5:.3f},0]]);")
            a(f"keys({v}.transform.scale,[[{s(t)},[100,100]],[{s(t) + 0.5:.3f},[108,118]]]); eo({v}.transform.scale);")
            if spark:
                x, y, w, h = BOX[f"spark{k}@"]
                v = lay(f"spark{k}", anchor=(8, h - 8))
                a(f"keys({v}.transform.opacity,[[{s(t) - 0.001:.3f},0],[{s(t) + 0.03:.3f},100],[{s(t) + 0.3:.3f},100],[{s(t) + 0.48:.3f},0]]);")
                a(f"keys({v}.transform.scale,[[{s(t)},[35,35]],[{s(t) + 0.16:.3f},[100,100]],[{s(t) + 0.48:.3f},[115,115]]]); eo({v}.transform.scale);")

    # 카메라 널(맨 먼저 — 식이 이름으로 찾음)
    a("var CAM=comp.layers.addNull(); CAM.name='CAM'; CAM.enabled=false; CAM.transform.anchorPoint.setValue([0,0]);")
    a(f"keys(CAM.transform.position,[{','.join(f'[{s(t)},[{p[0]:.2f},{p[1]:.2f}]]' for t, p in CAM_KEYS)}]); eo(CAM.transform.position);")
    a(f"keys(CAM.transform.scale,[{','.join(f'[{s(t)},[{p[2] * 100:.2f},{p[2] * 100:.2f}]]' for t, p in CAM_KEYS)}]); eo(CAM.transform.scale);")
    # 녹화(기본 확대 1.45 — 컷 조각마다) + CAM
    a(f"var iv=imp({js(str(M.REC))});")
    for i, (ta, tb, rs, _) in enumerate(M.SEGS):
        a(f"var R{i}=comp.layers.add(iv); R{i}.startTime={s(ta) - rs:.4f}; R{i}.inPoint={s(ta):.4f}; R{i}.outPoint={s(tb):.4f}; R{i}.motionBlur=true;")
        a(f"R{i}.transform.anchorPoint.setValue([{A[0]},{A[1]}]);")
        a(f"keys(R{i}.transform.position,[[{s(T_ZOOM)},[{A[0]},{A[1]}]],[{s(T_ZOOM) + 0.5:.3f},[0,0]],[{s(T_OUT)},[0,0]],[{s(T_OUT) + 0.45:.3f},[{A[0]},{A[1]}]]]);")
        a(f"keys(R{i}.transform.scale,[[{s(T_ZOOM)},[100,100]],[{s(T_ZOOM) + 0.5:.3f},[{S * 100},{S * 100}]],[{s(T_OUT)},[{S * 100},{S * 100}]],[{s(T_OUT) + 0.45:.3f},[100,100]]]);")
        a(f"ez(R{i}.transform.position); ez(R{i}.transform.scale); flat(R{i}.transform.position);")
        camify(f"R{i}")

    # ① 상세 타겟팅 칸: 클릭 → 포커스 → 칩 셋
    v = lay("field_patch"); opa(v, life(T_FCLICK, fi=0.06))
    v = lay("field_focus"); opa(v, life(T_FCLICK, T_FCLICK + 1.6, fi=0.08, fo=0.3))
    for k, t in enumerate(T_CHIPS):
        v = lay(f"chip{k}"); opa(v, life(t, fi=0.08)); pop(v, t); rise(v, f"chip{k}", t, dy=0, dx=-18)
    # ② 세트 A·광고 A 줄 이름 타자(빈 판은 불투명 — 녹화 글자가 비치지 않음)
    for nm, tc, (ta, tb) in (("A_set", T_ACLICK, T_ATYPE), ("A_ad", T_DCLICK, T_DTYPE)):
        v = lay(f"base_{nm}"); opa(v, [[max(0, s(tc) - 0.001), 0], [s(tc) + 0.02, 100], [s(T_OUT), 100], [s(T_OUT) + 0.2, 0]])
        typed(f"lab_{nm}", ta, tb, T_OFFCLICK + 0.08)
    v = lay("video"); opa(v, life(T_VIDEO, T_DUP - 0.3, fo=0.25)); pop(v, T_VIDEO); rise(v, "video", T_VIDEO, dy=0, dx=-20)
    # ③ 복제: 유령이 들려서 아래로 → 세트 B 이름 타자
    v = lay("ghost")
    x, y, w, h = BOX["ghost@"]
    a(f"keys({v}.transform.position,[[{s(T_GRAB + 0.12)},[{x + w / 2:.1f},{y + h / 2:.1f}]],[{s(T_DUP)},[{x + w / 2 + 10:.1f},{y + h / 2 + 18:.1f}]],[{s(T_DUP) + 0.5:.3f},[{x + w / 2:.1f},{y + h / 2 + GAP:.1f}]]]); eo({v}.transform.position);")
    a(f"keys({v}.transform.scale,[[{s(T_GRAB + 0.12)},[100,100]],[{s(T_DUP)},[103,103]],[{s(T_DUP) + 0.5:.3f},[100,100]]]);")
    opa(v, [[s(T_GRAB + 0.1), 0], [s(T_GRAB + 0.2), 92], [s(T_DUP) + 0.5, 92], [s(T_DUP) + 0.56, 0]])
    for nm in ("B_set", "B_ad"):
        v = lay(f"base_{nm}"); opa(v, [[0, 0], [s(T_DUP) + 0.5, 100], [s(T_OUT), 100], [s(T_OUT) + 0.2, 0]], hold_=True)
    v = lay("lab_B_ad"); opa(v, [[0, 0], [s(T_DUP) + 0.5, 100], [s(T_OUT), 100], [s(T_OUT) + 0.2, 0]], hold_=True)
    v = lay("ghost_lab"); opa(v, [[0, 0], [s(T_DUP) + 0.5, 100], [s(T_BTYPE[0]) - 0.12, 0]], hold_=True)
    typed("lab_B_set", T_BTYPE[0], T_BTYPE[1])
    # ④ 광고 2개
    v = lay("brace2"); opa(v, life(T_TWO, T_B60A - 0.4, fo=0.25))
    a(f"keys({v}.transform.scale,[[{s(T_TWO)},[100,0]],[{s(T_TWO) + 0.22:.3f},[100,100]]]); eo({v}.transform.scale);")
    v = lay("two"); opa(v, life(T_TWO + 0.1, T_B60A - 0.4, fo=0.25)); pop(v, T_TWO + 0.1); rise(v, "two", T_TWO + 0.1, dy=0, dx=-20)
    # ⑤ 예산 6만 · 6만 → 합계 12만
    for nm, t in (("b60a", T_B60A), ("b60b", T_B60B)):
        v = lay(nm); opa(v, life(t, T_CARDOUT, fi=0.06)); pop(v, t, 130, 0.18)
    v = lay("brace_sum"); opa(v, life(T_SUM - 0.12, T_CARD, fo=0.25))
    a(f"keys({v}.transform.scale,[[{s(T_SUM - 0.12)},[100,0]],[{s(T_SUM) + 0.1:.3f},[100,100]]]); eo({v}.transform.scale);")
    v = lay("sum"); opa(v, life(T_SUM, T_CARD, fo=0.25)); pop(v, T_SUM); rise(v, "sum", T_SUM, dy=0, dx=-24)
    # ⑥ 스위치: B 켜짐 «이어 가기» → A 클릭해서 끔 → A 줄 회색판(불투명 교체)
    v = lay("togB_on"); opa(v, life(T_KEEP - 0.3, fi=0.15))
    a(f"keys({v}.transform.scale,[[{s(T_KEEP)},[100,100]],[{s(T_KEEP) + 0.12:.3f},[112,112]],[{s(T_KEEP) + 0.3:.3f},[100,100]]]);")
    v = lay("togA_on"); opa(v, [[s(T_KEEP - 0.3) - 0.001, 0], [s(T_KEEP - 0.15), 100], [s(T_OFFCLICK + 0.08), 100], [s(T_OFFCLICK + 0.09), 0]])
    v = lay("keep"); opa(v, life(T_KEEP, fi=0.1)); pop(v, T_KEEP); rise(v, "keep", T_KEEP, dy=0, dx=-20)
    for nm in ("A_set", "A_ad"):
        v = lay(f"off_{nm}"); opa(v, [[0, 0], [s(T_OFFCLICK + 0.08), 100], [s(T_OUT), 100], [s(T_OUT) + 0.2, 0]], hold_=True)
    v = lay("togA_off"); opa(v, [[0, 0], [s(T_OFFCLICK + 0.08), 100], [s(T_OUT), 100], [s(T_OUT) + 0.2, 0]], hold_=True)
    v = lay("offtag"); opa(v, life(T_OFFCLICK + 0.05, fi=0.1)); pop(v, T_OFFCLICK + 0.05); rise(v, "offtag", T_OFFCLICK + 0.05, dy=0, dx=-20)

    # ⑦ 커서(기본 틀 좌표 · CAM 따라감)
    v = lay("cursor", anchor=(4, 4))
    fxc, fyc = sc((FIELD[0] + FIELD[2]) / 2 - 120, (FIELD[1] + FIELD[3]) / 2)
    xa, ya = BOX["lab_A_set#"][0] + 120, SY + RH / 2
    xd, yd = BOX["lab_A_ad#"][0] + 110, AY + RH / 2
    gx, gy = SX + RW * 0.45, SY + RH / 2
    togA = BOX["togA_on"]
    tx_, ty_ = (togA[0] + togA[2]) / 2, (togA[1] + togA[3]) / 2
    path = [(T_FCLICK - 0.55, fxc + 260, fyc + 140), (T_FCLICK, fxc, fyc), (T_FCLICK + 0.5, fxc, fyc), (T_ACLICK, xa, ya), (T_DCLICK - 0.5, xa + 10, ya + 6),
            (T_DCLICK, xd, yd), (T_DTYPE[1] + 0.3, xd + 40, yd + 40),
            (T_GRAB - 0.4, gx + 80, gy + 60), (T_GRAB, gx, gy), (T_DUP, gx + 10, gy + 18), (T_DUP + 0.5, gx, gy + GAP), (T_DUP + 0.9, gx + 60, gy + GAP + 50),
            (T_OFFCLICK - 0.7, tx_ + 90, ty_ + 70), (T_OFFCLICK, tx_, ty_), (T_OFFCLICK + 0.5, tx_ + 30, ty_ + 40)]
    a(f"keys({v}.transform.position,[{','.join(f'[{s(t)},[{x:.1f},{y:.1f}]]' for t, x, y in path)}]); eo({v}.transform.position);")
    opa(v, [[s(T_FCLICK - 0.55) - 0.001, 0], [s(T_FCLICK - 0.4), 100], [s(T_DTYPE[1] + 0.3), 100], [s(T_DTYPE[1] + 0.55), 0],
            [s(T_GRAB - 0.4), 0], [s(T_GRAB - 0.25), 100], [s(T_DUP + 0.9), 100], [s(T_DUP + 1.1), 0],
            [s(T_OFFCLICK - 0.7), 0], [s(T_OFFCLICK - 0.55), 100], [s(T_OFFCLICK + 0.5), 100], [s(T_OFFCLICK + 0.7), 0]])
    sk = []
    for t in (T_FCLICK, T_ACLICK, T_DCLICK, T_GRAB, T_OFFCLICK):
        sk += [[s(t) - 0.06, [100, 100]], [s(t), [84, 84]], [s(t) + 0.14, [100, 100]]]
    a(f"keys({v}.transform.scale,{sk});")
    for t, (x, y) in ((T_FCLICK, (fxc, fyc)), (T_ACLICK, (xa, ya)), (T_DCLICK, (xd, yd)), (T_GRAB, (gx, gy)), (T_OFFCLICK, (tx_, ty_))):
        v = lay("click_ring")
        a(f"{v}.transform.position.setValue([{x:.1f},{y:.1f}]);")
        opa(v, [[s(t) - 0.001, 0], [s(t) + 0.04, 100], [s(t) + 0.42, 0]])
        a(f"{v}.transform.scale.expression={js('var k=thisComp.layer(' + chr(39) + 'CAM' + chr(39) + ').transform.scale[0]/100; var u=linear(time,' + f'{s(t)},{s(t) + 0.42:.3f},35,130' + '); [u*k,u*k]')};")

    # ⑧ 지표 카드: 뒤 어둡게 → 카드 → 3일 → 날마다 막대 → B 강조 → «여기가 DB 더 잘 들어오네!»
    v = lay("dim"); opa(v, [[s(T_CARD) - 0.001, 0], [s(T_CARD) + 0.35, 100], [s(T_CARDOUT), 100], [s(T_CARDOUT) + 0.35, 0],
                            [s(T_LOOP) - 0.6, 0], [s(T_LOOP) - 0.25, 100], [s(T_OUT), 100], [s(T_OUT) + 0.3, 0]])
    v = lay("card"); opa(v, life(T_CARD, T_CARDOUT, fi=0.2, fo=0.25)); rise(v, "card", T_CARD, dy=60, dur=0.4)
    a(f"keys({v}.transform.position,[[{s(T_CARDOUT)},[{BOX['card@'][0] + BOX['card@'][2] / 2:.1f},{BOX['card@'][1] + BOX['card@'][3] / 2:.1f}]],[{s(T_CARDOUT) + 0.3:.3f},[{BOX['card@'][0] + BOX['card@'][2] / 2:.1f},{BOX['card@'][1] + BOX['card@'][3] / 2 + 50:.1f}]]]);")
    card_v = v
    for k in range(3):
        v = lay(f"day{k}_off"); a(f"{v}.parent={card_v}; {v}.transform.scale.setValue([100,100]);")
        x, y, w, h = BOX[f"day{k}_off@"]
        cx_, cy_ = BOX["card@"][0] + BOX["card@"][2] / 2, BOX["card@"][1] + BOX["card@"][3] / 2
        a(f"{v}.transform.position.setValue([{x + w / 2 - cx_ + BOX['card@'][2] / 2:.1f},{y + h / 2 - cy_ + BOX['card@'][3] / 2:.1f}]);")
        opa(v, life(T_CARD + 0.15, T_CARDOUT, fi=0.2, fo=0.25))
        v = lay(f"day{k}_on"); a(f"{v}.parent={card_v}; {v}.transform.scale.setValue([100,100]);")
        a(f"{v}.transform.position.setValue([{x + w / 2 - cx_ + BOX['card@'][2] / 2:.1f},{y + h / 2 - cy_ + BOX['card@'][3] / 2:.1f}]);")
        opa(v, life(T_DAYS[k], T_CARDOUT, fi=0.08, fo=0.25)); pop(v, T_DAYS[k], 80, 0.18)
    for key in "AB":
        v = lay(f"bar{key}")
        x, y, w, h = BOX[f"bar{key}@"]
        a(f"{v}.parent={card_v}; {v}.transform.scale.setValue([100,100]); {v}.transform.anchorPoint.setValue([0,{h / 2}]);")
        cx_, cy_ = BOX["card@"][0], BOX["card@"][1]
        a(f"{v}.transform.position.setValue([{x - cx_:.1f},{y + h / 2 - cy_:.1f}]);")
        sk = [[s(T_DAYS[0]) - 0.01, [0, 100]]]
        for k, t in enumerate(T_DAYS):
            sk += [[s(t), [sk[-1][1][0], 100]], [s(t) + 0.38, [BAR_LENS[key][k] * 100, 100]]]
        a(f"keys({v}.transform.scale,{sk}); eo({v}.transform.scale);")
        opa(v, life(T_DAYS[0], T_CARDOUT, fi=0.05, fo=0.25))
    v = lay("wintxt"); opa(v, life(T_WINTXT, T_CARDOUT, fi=0.1, fo=0.25)); a(f"{v}.parent={card_v}; {v}.transform.scale.setValue([100,100]);")
    x, y, w, h = BOX["wintxt@"]
    a(f"{v}.transform.position.setValue([{x + w / 2 - BOX['card@'][0]:.1f},{y + h / 2 - BOX['card@'][1]:.1f}]);")
    a(f"keys({v}.transform.scale,[[{s(T_WINTXT)},[72,72]],[{s(T_WINTXT) + 0.2:.3f},[100,100]]]); eo({v}.transform.scale);")

    # ⑨ 순환 카드: 데이터 분석 ⇄ 개선(고리 계속 돎) → 실력 계단 + «실력이 좋아져요»
    v = lay("loopcard"); opa(v, life(T_LOOP, fi=0.2)); rise(v, "loopcard", T_LOOP, dy=60, dur=0.4)
    v = lay("loopring"); opa(v, life(T_AN - 0.05, fi=0.2)); pop(v, T_AN - 0.05, 80, 0.3)
    a(f"{v}.transform.rotation.expression={js(f'time<{s(T_AN):.3f}?0:(time-{s(T_AN):.3f})*120')};")
    v = lay("keepgo"); opa(v, life(T_AN + 0.3, fi=0.2))
    v = lay("an"); opa(v, life(T_AN, fi=0.08)); pop(v, T_AN)
    v = lay("imp"); opa(v, life(T_IMP, fi=0.08)); pop(v, T_IMP)
    for k in range(4):
        v = lay(f"step{k}")
        x, y, w, h = BOX[f"step{k}@"]
        a(f"{v}.transform.anchorPoint.setValue([{w / 2},{h}]); {v}.transform.position.setValue([{x + w / 2},{y + h}]);")
        t = T_SKILL - 0.3 + k * 0.1
        a(f"keys({v}.transform.scale,[[{s(t)},[100,0]],[{s(t) + 0.3:.3f},[100,100]]]); eo({v}.transform.scale);")
        opa(v, life(t, fi=0.05))
    v = lay("skill"); opa(v, life(T_SKILL, fi=0.08)); pop(v, T_SKILL)
    do_points()
    a(f"var rq=app.project.renderQueue.items.add(comp); var om=rq.outputModule(1); om.applyTemplate({js('고품질')}); om.file=new File({js(str(out_mov))});")
    a("log('ok bisa13b'); })();")
    assert T_OUT + 0.45 < T1
    return "\n".join(L)


M.SND_FIX = {
    "zoom":  ("휙２.mp3", 0.6, -6, "peak"),                         # 녹화 화면 확대(05 사장님 0dB = 원음 −6)
    "clk1":  ("마우스 클릭.mp3", 0.25, 5, "onset"),                  # 커서 클릭(03)
    "clk2":  ("15. 마우스클릭.mp3", 0.25, 5, "onset"),
    "chip":  ("ML_Cartoon bubbles popping.wav", 0.5, 5, "onset"),
    "type1": ("SEL_キーボード2.mp3", 0.45, 6, "onset"),               # 이름 타자
    "type2": ("키보드.mp3", 0.45, 8, "onset"),
    "st1":   ("KN_pepSound1.wav", 0.4, 8, "onset"),
    "st2":   ("KN_pepSound2.wav", 0.4, 8, "onset"),
    "dup":   ("SEL_決定ボタンを押す4.mp3", 0.4, 5, "onset"),         # 세트 복제
    "ok":    ("맑은소리.mp3", 0.8, 7, "onset"),
    "card":  ("휙２.mp3", 0.6, 4, "peak"),                          # 지표·순환 카드 들어옴
    "gauge": ("SEL_ゲージ回復1.mp3", 0.6, 12, "onset"),             # 날마다 막대 참
    "win":   ("SEL_キラッ1.mp3", 0.7, -1, "onset"),                 # 여기가 더 잘
    "off":   ("KN_error_003.wav", 0.5, 5, "onset"),                 # 스위치 끔
    "lvl":   ("SEL_レベルアップ.mp3", 0.9, 5, "onset"),              # 실력이 좋아져요
    "back":  ("휙1.mp3", 0.7, -6, "peak"),
}
M.EVENTS = [(T_ZOOM + 0.25, "zoom"), (T_FCLICK, "clk1"), (T_CHIPS[0], "chip"), (T_ACLICK, "clk2"), (T_ATYPE[0], "type1"),
            (T_DCLICK, "clk1"), (T_DTYPE[0], "type2"), (T_VIDEO, "st1"), (T_APULSE, "st2"), (T_GRAB, "clk2"), (T_DUP, "dup"),
            (T_BTYPE[0], "type1"), (T_TWO, "st1"), (T_B60A, "chip"), (T_B60B, "st2"), (T_SUM, "ok"), (T_CARD, "card"),
            (T_3DAY, "st1"), (T_DAYS[0], "gauge"), (T_WIN, "win"), (T_WINTXT, "st2"), (T_CARDOUT, "back"), (T_KEEP, "st1"),
            (T_OFFCLICK, "off"), (T_LOOP, "card"), (T_AN, "st2"), (T_IMP, "st1"), (T_SKILL, "lvl"), (T_OUT + 0.2, "back")]

_role = M.SFX.role


def _role_zoom(r, mx, rel, align):
    """녹화 화면 확대/풀림 휙은 크기표(판 전환 값)보다 작게 — 05 사장님 0dB(원음 −6)."""
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
