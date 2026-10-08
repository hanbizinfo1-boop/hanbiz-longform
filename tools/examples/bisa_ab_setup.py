# -*- coding: utf-8 -*-
r"""빡이사DB 본편 13 «그러면 상세 타겟팅 건 광고 하나 ~ 실력 많이 좋아지실 거예요» (시퀀스 1044.56~1075.958)
— 실제 광고 관리자(광고 세트 편집) 화면에서 «같은 영상 · 세트 둘(상세 타겟팅 / 논타겟팅) · 6만+6만 · 3일 지표 · 잘 되는 쪽만 켜 두기»를 설정해 보는 연출.
사장님 10-07 «실제 광고 페이지에 설정하는 듯한 연출» → 08 2판 결(녹화 화면 확대 + 칸·트리·스위치가 실제처럼 바뀜).

  python bisa_ab_setup.py [--조각만] [--소리만]
    → 빡이사DB\납품\13_AB세팅_1044.56~.mp4 (V1 1044.56 은 클립 가운데 — 잘라서 바꿔 끼움, 끝 1075.958 컷 경계) · _효과음.xml · _미리보기.mp4
앞뒤 맥락(기록.md 13)
  앞 1040.02 «또 하나 더, 할 말이 되게 많은데 · 상세 타겟팅은 만약에 나는 꼭 넣어야겠어»(12 «3~5개, 관심사 안 해도 돼요» 다음)
  뒤 1075.96 «여기서 할 말이 많았죠 … 광고 투명성 패스 · 노출 위치»
흐름(시퀀스 초, faster-whisper 단어 시각)
  1044.56 «그러면» 트리+상세 타겟팅 칸이 보이게 1.45배 확대
  1045.58 «타겟팅» 상세 타겟팅 칸에 관심사 칩 셋(피부 관리 · 뷰티 · 화장품 — 12 «3~5개» 결) · 1046.58 «광고» 세트 줄 이름 «세트 A · 상세 타겟팅»
  1047.94 «똑같은 영상» 광고 줄 «광고 · 같은 영상»
  1054.06 «논 타겟팅» 트리에 세트 B 줄이 복제돼 내려옴 «세트 B · 논타겟팅» + 광고 줄 «광고 · 같은 영상»
  1056.72 «총 2개의» 광고 줄 둘에 파란 테두리
  1059.46 «6만원» 세트 A ₩60,000/일 · 1059.92 «6만원» 세트 B ₩60,000/일 · 1060.74 «12만원» «하루 ₩120,000»
  1062.52 «며칠» 지표 카드(세트 A · 세트 B, 1~3일 DB 막대 — 숫자 없음) → 1063.12~1064.76 날마다 막대가 참
  1065.80 «여기가» 세트 B 줄 강조 «DB 더 잘 들어옴»
  1067.78 «이어가시고» 세트 B 스위치 켜짐 유지 · 1068.66 «뒷광고는 꺼버리고» 세트 A 스위치 꺼짐(회색)·줄 흐려짐
  1070.36 «하면서 이제 계속 데이터 분석» → 1072.78 «개선» «데이터 분석 → 개선» · 1074.46 «실력» «실력이 좋아져요» · 1075.45 확대 풀림
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

M.T0, M.T1 = 1044.56, 1075.958
M.DUR = M.T1 - M.T0
M.SEGS = [(1044.56, 1045.127, 1784.332, 1786.101), (1045.127, 1046.195, 1785.1, 1786.868), (1046.195, 1047.43, 1786.351, 1788.12),
          (1047.43, 1047.914, 1787.703, 1789.471), (1047.914, 1050.316, 1790.739, 1792.507), (1050.316, 1051.5, 1793.258, 1795.027),
          (1051.5, 1058.708, 1794.526, 1796.294), (1058.708, 1069.819, 1801.817, 1803.585), (1069.819, 1070.553, 1813.061, 1814.83),
          (1070.553, 1073.906, 1813.929, 1815.697), (1073.906, 1075.958, 1817.733, 1819.484)]
M.NAME = "13_AB세팅"
M.SFX_DIR = (config.WORK / "효과음13")
M.WORK = (config.WORK / "빡이사" / "ae13")
W, H = M.W, M.H
T0, T1 = M.T0, M.T1
WORK = M.WORK
FRAME = (config.WORK / "bisa09" / "full13.png")          # 녹화 1795 초(트리·상세 타겟팅 칸, 줄 그림을 잘라 씀)
PRET = str(config.FONTS["pretendard_bold"])
MALG, MALGB = str(config.FONTS["malgun"]), str(config.FONTS["malgun_bold"])
INK, GREY, BLUE, RED, OFF = (28, 30, 33), (95, 99, 104), (0, 100, 224), (200, 40, 35), (190, 194, 200)

S, A = 1.45, (60, 150)                                     # 녹화 점 p → S·(p − A)


def sc(x, y):
    return S * (x - A[0]), S * (y - A[1])


ROW_SET, ROW_AD = (112, 202, 516, 254), (112, 255, 516, 306)  # 트리 줄(녹화)
FIELD = (697, 692, 1308, 732)                              # 상세 타겟팅 검색 칸(녹화)
T_ZOOM, T_OUT = 1044.56, 1075.45
T_CHIPS, T_SETA, T_ADA = 1045.58, 1046.58, 1047.94
T_SETB, T_TWO = 1054.06, 1056.72
T_B60A, T_B60B, T_B120 = 1059.46, 1059.92, 1060.74
T_CARD, T_DAYS = 1062.52, [1063.12, 1063.62, 1064.34]
T_WIN, T_KEEP, T_OFF = 1065.80, 1067.78, 1068.66
T_ANALYZE, T_IMPROVE, T_SKILL = 1070.36, 1072.78, 1074.46          # 1070.36 «하면서 이제 계속 데이터 분석하면서»
PIP = (0, 580, 720, 1080)
CAPTION = (480, 900, 1440, 1080)
BOX = {}


def font(n, f=PRET):
    return ImageFont.truetype(f, n)


def tl(t, f):
    return ImageDraw.Draw(Image.new("RGBA", (1, 1))).textlength(t, font=f)


def save(name, im, xy):
    xy = (int(round(xy[0])), int(round(xy[1])))
    im.save(WORK / f"{name}.png")
    a = np.array(im)[..., 3] > 60
    ys, xs = np.where(a)
    BOX[name] = (int(xy[0] + xs.min()), int(xy[1] + ys.min()), int(xy[0] + xs.max()), int(xy[1] + ys.max()))
    BOX[name + "@"] = (int(xy[0]), int(xy[1]), im.width, im.height)


def pill(t, size, fg, bg, padx=16, h=None, f=None):
    f = f or font(size)
    w = int(tl(t, f)) + 2 * padx
    h = h or int(size * 1.7)
    im = Image.new("RGBA", (w + 16, h + 16), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((8, 8, 8 + w, 8 + h), h // 2, fill=bg + (255,))
    ImageDraw.Draw(im).text((8 + w / 2, 8 + h / 2), t, font=f, fill=fg, anchor="mm")
    return im


def row_img(box, label, toggle=None):
    """녹화 화면의 실제 트리 줄을 잘라 확대 · 글자만 바꿔 쓴다(아이콘·바탕은 진짜). toggle: None/«on»/«off»."""
    fr = Image.open(FRAME).convert("RGBA")
    x0, y0, x1, y1 = box
    im = fr.crop(box).resize((int((x1 - x0) * S), int((y1 - y0) * S)), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    a = np.asarray(im.convert("RGB")).astype(int)
    bg = tuple(int(v) for v in np.median(a[:, int(im.width * 0.8):int(im.width * 0.95)].reshape(-1, 3), 0))
    tx = int(((178 if box == ROW_SET else 186) - x0) * S)
    d.rectangle((tx - 14, 6, im.width - 2, im.height - 6), fill=bg + (255,))
    d.text((tx, im.height / 2), label, font=font(24, MALG), fill=INK + (255,), anchor="lm")
    if toggle:
        w, h = 52, 30
        x, y = im.width - w - 14, im.height / 2 - h / 2
        on = toggle == "on"
        d.rounded_rectangle((x, y, x + w, y + h), h // 2, fill=(BLUE if on else OFF) + (255,))
        cx = x + w - h / 2 if on else x + h / 2
        d.ellipse((cx - 11, y + 4, cx + 11, y + 26), fill=(255, 255, 255, 255))
    return im


def overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def check_layout():
    bad = []
    for n in [k for k in BOX if not k.endswith("@")]:
        for z, zn in ((PIP, "사람 PIP"), (CAPTION, "자막")):
            if overlap(BOX[n], z):
                bad.append(f"{n} {BOX[n]} ↔ {zn}")
        x0, y0, x1, y1 = BOX[n]
        if x0 < 15 or y0 < 10 or x1 > W - 15 or y1 > H - 15:
            bad.append(f"{n} {BOX[n]} 화면 밖")
    for a_, b_ in (("b60a", "rowA_set"), ("b60b", "rowB_set")):
        pass
    if overlap(BOX["card"], BOX["chips"]):
        bad.append("지표 카드 ↔ 관심사 칩")
    if bad:
        raise SystemExit("레이아웃 겹침:\n  " + "\n  ".join(bad))
    print("겹침 없음")


# ── 조각 ──────────────────────────────────────────────────────
def pieces():
    WORK.mkdir(parents=True, exist_ok=True)
    BOX.clear()
    sx, sy = sc(ROW_SET[0], ROW_SET[1])
    ax, ay = sc(ROW_AD[0], ROW_AD[1])
    rh = (ROW_SET[3] - ROW_SET[1]) * S
    # 세트 A · 광고(제자리 덮기) — 이름 바꾼 줄 / 스위치 켜짐·꺼짐 두 벌
    save("rowA_set", row_img(ROW_SET, "세트 A · 상세 타겟팅"), (sx, sy))
    save("rowA_ad", row_img(ROW_AD, "광고 · 같은 영상"), (ax, ay))
    save("rowA_ad_on", row_img(ROW_AD, "광고 · 같은 영상", "on"), (ax, ay))
    save("rowA_ad_off", row_img(ROW_AD, "광고 · 같은 영상", "off"), (ax, ay))
    gap = 2 * rh + 30                                       # 세트 B 는 아래에 복제(빈 사이드바 자리)
    save("rowB_set", row_img(ROW_SET, "세트 B · 논타겟팅"), (sx, sy + gap))
    save("rowB_ad", row_img(ROW_AD, "광고 · 같은 영상"), (ax, ay + gap))
    save("rowB_ad_on", row_img(ROW_AD, "광고 · 같은 영상", "on"), (ax, ay + gap))
    # 광고 줄 테두리(둘)
    for nm, y in (("outA", ay), ("outB", ay + gap)):
        w = int((ROW_AD[2] - ROW_AD[0]) * S)
        im = Image.new("RGBA", (w + 8, int(rh) + 8), (0, 0, 0, 0))
        ImageDraw.Draw(im).rounded_rectangle((2, 2, w + 5, int(rh) + 5), 10, outline=BLUE + (255,), width=4)
        save(nm, im, (ax - 4, y - 4))
    im = pill("광고 2개", 24, (255, 255, 255), BLUE, padx=14, h=40)
    save("two", im, (sx + 10, ay + gap + rh + 14))
    # 예산 알약(세트 줄 오른쪽 위)
    for nm, y in (("b60a", sy), ("b60b", sy + gap)):
        im = pill("₩60,000/일", 22, (255, 255, 255), INK, padx=12, h=34)
        save(nm, im, (sc(ROW_SET[2], 0)[0] - im.width - 6, y + rh / 2 - im.height / 2))     # 세트 줄 안 오른쪽
    im = pill("하루 ₩120,000", 30, (255, 255, 255), BLUE, padx=20, h=52)
    save("b120", im, (sx + 10, ay + gap + rh + 70))
    # 관심사 칩(상세 타겟팅 칸 안)
    fx0, fy0 = sc(FIELD[0], FIELD[1])
    fx1, fy1 = sc(FIELD[2], FIELD[3])
    im = Image.new("RGBA", (int(fx1 - fx0) - 20, int(fy1 - fy0) - 10), (255, 255, 255, 255))
    save("field_patch", im, (fx0 + 10, fy0 + 5))
    x = fx0 + 24
    for k, t in enumerate(("피부 관리", "뷰티", "화장품")):
        c = pill(t, 24, BLUE, (225, 236, 252), padx=14, h=40, f=font(24, MALGB))
        save(f"chip{k}", c, (x, (fy0 + fy1) / 2 - c.height / 2))
        x += c.width - 4
    BOX["chips"] = (int(fx0), int(fy0), int(x), int(fy1))
    # 지표 카드(본문 위) — 세트 A·B 1~3일 DB 막대(숫자 없음)
    cx0, cy0, cw, ch = 830, 230, 990, 470
    c = Image.new("RGBA", (cw + 40, ch + 40), (0, 0, 0, 0))
    sh = Image.new("RGBA", c.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((20, 26, 20 + cw, 26 + ch), 18, fill=(10, 30, 70, 60))
    c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(c)
    d.rounded_rectangle((20, 20, 20 + cw, 20 + ch), 18, fill=(255, 255, 255, 255), outline=(220, 223, 228, 255), width=2)
    d.text((50, 62), "지표 · 3일", font=font(32), fill=INK, anchor="lm")
    d.text((50 + 330, 62), "DB 수집", font=font(24, MALG), fill=GREY, anchor="lm")
    for k, t in enumerate(("1일", "2일", "3일")):
        d.text((390 + k * 200, 120), t, font=font(24, MALG), fill=GREY, anchor="lm")
    for j, t in enumerate(("세트 A · 상세 타겟팅", "세트 B · 논타겟팅")):
        y = 190 + j * 120
        d.text((50, y), t, font=font(26, MALGB), fill=INK, anchor="lm")
        for k in range(3):
            d.rounded_rectangle((390 + k * 200, y - 16, 390 + k * 200 + 170, y + 16), 8, fill=(238, 240, 244, 255))
    save("card", c, (cx0 - 20, cy0 - 20))
    lens = {"A": [0.35, 0.45, 0.5], "B": [0.6, 0.8, 0.95]}       # 그림 비율(실측 아님 — «B 가 더 잘 들어옴»만 보이게)
    for j, key in enumerate("AB"):
        for k in range(3):
            w = int(170 * lens[key][k])
            im = Image.new("RGBA", (w, 32), (0, 0, 0, 0))
            ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, 31), 8, fill=(BLUE if key == "B" else (120, 150, 200)) + (255,))
            save(f"bar{key}{k}", im, (cx0 + 370 + k * 200, cy0 + 170 + j * 120 - 16))
    im = Image.new("RGBA", (cw - 40, 70), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, cw - 41, 69), 14, outline=BLUE + (255,), width=4, fill=BLUE + (22,))
    save("winrow", im, (cx0 + 10, cy0 + 170 + 120 - 35))
    im = pill("DB 더 잘 들어옴", 24, (255, 255, 255), BLUE, padx=14, h=40)
    save("win", im, (cx0 + cw - im.width - 20, cy0 + 170 + 120 + 38))
    ln = Image.new("RGBA", (cw - 60, 3), (230, 232, 236, 255))
    save("cardline", ln, (cx0 + 30, cy0 + 370))
    for nm, t, col, x in (("an", "데이터 분석", INK, cx0 + 30), ("imp", "→  개선", BLUE, cx0 + 270)):
        im = Image.new("RGBA", (300, 60), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((0, 30), t, font=font(38), fill=col + (255,), anchor="lm")
        save(nm, im, (x, cy0 + 385))
    im = pill("실력이 좋아져요", 30, (255, 255, 255), BLUE, padx=22, h=52)
    save("skill", im, (cx0 + 600, cy0 + 380))
    check_layout()


# ── 애펙 ───────────────────────────────────────────────────────
def jsx(out_mov):
    js = AE.js
    s = lambda t: round(t - T0, 4)                         # noqa: E731
    L = ["function eo(p){ for(var k=1;k<=p.numKeys;k++){ var n=p.isSpatial?1:(p.value.length||1), o=[], i=[]; for(var j=0;j<n;j++){ o.push(new KeyframeEase(0,0.1)); i.push(new KeyframeEase(0,85)); } p.setTemporalEaseAtKey(k,i,o); } }",
         f"(function(){{ var comp=app.project.items.addComp('bisa13',{W},{H},1,{M.DUR:.3f},{M.FPS});"]
    a = L.append
    nv = [0]

    def lay(name):
        nv[0] += 1
        v = f"L{nv[0]}"
        x, y, w, h = BOX[name + "@"]
        a(f"var {v}=comp.layers.add(imp({js(str(WORK / f'{name}.png'))})); {v}.transform.position.setValue([{x + w / 2:.1f},{y + h / 2:.1f}]);")
        return v

    def opa(v, k, hold=False):
        a(f"keys({v}.transform.opacity,{k});")
        if hold:
            a(f"for(var q=1;q<={v}.transform.opacity.numKeys;q++){{ {v}.transform.opacity.setInterpolationTypeAtKey(q,KeyframeInterpolationType.HOLD); }}")

    def life(t_in, t_out=T_OUT, fi=0.25, fo=0.2):
        return [[max(0, s(t_in) - 0.001), 0], [s(t_in) + fi, 100], [s(t_out), 100], [s(t_out) + fo, 0]]

    def drift(v, name, t, dx=0, dy=14, dur=0.35):
        x, y, w, h = BOX[name + "@"]
        a(f"keys({v}.transform.position,[[{s(t)},[{x + w / 2 + dx:.1f},{y + h / 2 + dy:.1f}]],[{s(t) + dur:.3f},[{x + w / 2:.1f},{y + h / 2:.1f}]]]); eo({v}.transform.position);")

    def grow(v, t, frm=85):
        a(f"keys({v}.transform.scale,[[{s(t)},[{frm},{frm}]],[{s(t) + 0.25:.3f},[100,100]]]); eo({v}.transform.scale);")

    a(f"var iv=imp({js(str(M.REC))});")
    for i, (ta, tb, rs, _) in enumerate(M.SEGS):
        a(f"var R{i}=comp.layers.add(iv); R{i}.startTime={s(ta) - rs:.4f}; R{i}.inPoint={s(ta):.4f}; R{i}.outPoint={s(tb):.4f};")
        a(f"R{i}.transform.anchorPoint.setValue([{A[0]},{A[1]}]);")
        a(f"keys(R{i}.transform.position,[[{s(T_ZOOM)},[{A[0]},{A[1]}]],[{s(T_ZOOM) + 0.5:.3f},[0,0]],[{s(T_OUT)},[0,0]],[{s(T_OUT) + 0.45:.3f},[{A[0]},{A[1]}]]]);")
        a(f"keys(R{i}.transform.scale,[[{s(T_ZOOM)},[100,100]],[{s(T_ZOOM) + 0.5:.3f},[{S * 100},{S * 100}]],[{s(T_OUT)},[{S * 100},{S * 100}]],[{s(T_OUT) + 0.45:.3f},[100,100]]]);")
        a(f"ez(R{i}.transform.position); ez(R{i}.transform.scale); flat(R{i}.transform.position);")
    # 트리: 세트 A·광고 줄 이름 바뀜 → 스위치(켜짐) → 꺼짐
    v = lay("rowA_set"); opa(v, life(T_SETA, fi=0.2))
    a(f"keys({v}.transform.opacity,[[{s(T_OFF) + 0.3:.3f},100],[{s(T_OFF) + 0.6:.3f},55]]);")
    v = lay("rowA_ad"); opa(v, [[max(0, s(T_ADA) - 0.001), 0], [s(T_ADA) + 0.2, 100], [s(T_KEEP) - 0.3, 100], [s(T_KEEP) - 0.29, 0]])
    v = lay("rowA_ad_on"); opa(v, [[0, 0], [s(T_KEEP) - 0.3, 100], [s(T_OFF), 0]], hold=True)
    v = lay("rowA_ad_off"); opa(v, [[0, 0], [s(T_OFF), 100], [s(T_OUT), 100], [s(T_OUT) + 0.2, 0]])
    a(f"for(var q=1;q<=3;q++){{ {v}.transform.opacity.setInterpolationTypeAtKey(q,KeyframeInterpolationType.HOLD); }} keys({v}.transform.opacity,[[{s(T_OFF) + 0.3:.3f},100],[{s(T_OFF) + 0.6:.3f},55]]);")
    # 세트 B 복제: 세트 A 자리에서 아래로 미끄러져 내려옴
    gap_y = BOX["rowB_set@"][1] - BOX["rowA_set@"][1]
    for nm, src in (("rowB_set", "rowA_set"), ("rowB_ad", "rowA_ad")):
        v = lay(nm)
        x, y, w, h = BOX[nm + "@"]
        a(f"keys({v}.transform.position,[[{s(T_SETB)},[{x + w / 2:.1f},{y + h / 2 - gap_y:.1f}]],[{s(T_SETB) + 0.5:.3f},[{x + w / 2:.1f},{y + h / 2:.1f}]]]); eo({v}.transform.position);")
        opa(v, life(T_SETB, T_KEEP - 0.3 if nm == "rowB_ad" else T_OUT, fi=0.2, fo=0.01))
    v = lay("rowB_ad_on"); opa(v, [[0, 0], [s(T_KEEP) - 0.31, 0], [s(T_KEEP) - 0.3, 100], [s(T_OUT), 100], [s(T_OUT) + 0.2, 0]])   # 그 시각에 딱(0초부터 서서히 비치지 않게)
    a(f"keys({v}.transform.scale,[[{s(T_KEEP)},[100,100]],[{s(T_KEEP) + 0.2:.3f},[103,103]],[{s(T_KEEP) + 0.45:.3f},[100,100]]]);")
    for nm in ("outA", "outB"):
        v = lay(nm); opa(v, life(T_TWO, T_B60A, fo=0.3))
    v = lay("two"); opa(v, life(T_TWO + 0.15, T_B60A, fo=0.3)); grow(v, T_TWO + 0.15)
    for nm, t in (("b60a", T_B60A), ("b60b", T_B60B)):
        v = lay(nm); opa(v, life(t)); grow(v, t, 80)
    v = lay("b120"); opa(v, life(T_B120)); drift(v, "b120", T_B120)
    # 관심사 칩
    v = lay("field_patch"); opa(v, life(T_CHIPS - 0.05, fi=0.05))
    for k in range(3):
        t = T_CHIPS + k * 0.33
        v = lay(f"chip{k}"); opa(v, life(t, fi=0.15)); grow(v, t, 70)
    # 지표 카드 + 막대(날마다) + 승자 + 분석·개선
    v = lay("card"); opa(v, life(T_CARD, fi=0.3)); drift(v, "card", T_CARD, dy=24, dur=0.4)
    for k, t in enumerate(T_DAYS):
        for key in "AB":
            v = lay(f"bar{key}{k}")
            x, y, w, h = BOX[f"bar{key}{k}@"]
            a(f"{v}.transform.anchorPoint.setValue([0,{h / 2}]); {v}.transform.position.setValue([{x},{y + h / 2}]);")
            a(f"keys({v}.transform.scale,[[{s(t)},[0,100]],[{s(t) + 0.45:.3f},[100,100]]]); eo({v}.transform.scale);")
            opa(v, life(t, fi=0.05))
    v = lay("winrow"); opa(v, life(T_WIN, fi=0.25))
    v = lay("win"); opa(v, life(T_WIN + 0.2)); grow(v, T_WIN + 0.2)
    v = lay("cardline"); opa(v, life(T_CARD, fi=0.3))
    v = lay("an"); opa(v, life(T_ANALYZE)); drift(v, "an", T_ANALYZE, dx=-16, dy=0)
    v = lay("imp"); opa(v, life(T_IMPROVE)); drift(v, "imp", T_IMPROVE, dx=-16, dy=0)
    v = lay("skill"); opa(v, life(T_SKILL)); grow(v, T_SKILL)
    a(f"var rq=app.project.renderQueue.items.add(comp); var om=rq.outputModule(1); om.applyTemplate({js('고품질')}); om.file=new File({js(str(out_mov))});")
    a("log('ok bisa13'); })();")
    assert T_OUT + 0.45 < T1
    return "\n".join(L)


M.SND_FIX = {
    "zoom":  ("휙２.mp3", 0.6, -6, "peak"),                         # 녹화 화면 확대(05 사장님 0dB = 원음 −6)
    "chip":  ("ML_Cartoon bubbles popping.wav", 0.5, 5, "onset"),
    "type":  ("SEL_キーボード2.mp3", 0.45, 6, "onset"),             # 줄 이름 바꿈
    "st1":   ("KN_pepSound1.wav", 0.4, 8, "onset"),
    "st2":   ("KN_pepSound2.wav", 0.4, 8, "onset"),
    "dup":   ("SEL_決定ボタンを押す4.mp3", 0.4, 5, "onset"),         # 세트 복제
    "ok":    ("맑은소리.mp3", 0.8, 7, "onset"),
    "gauge": ("SEL_ゲージ回復1.mp3", 0.6, 12, "onset"),             # 막대 차오름
    "off":   ("KN_error_003.wav", 0.5, 5, "onset"),                 # 스위치 끔
    "back":  ("휙1.mp3", 0.7, -6, "peak"),
}
M.EVENTS = [(T_ZOOM + 0.25, "zoom"), (T_CHIPS, "chip"), (T_SETA, "type"), (T_ADA, "st1"), (1050.54, "st2"), (1052.34, "st1"),
            (T_SETB, "dup"), (T_TWO, "st2"), (T_B60A, "st1"), (T_B120, "ok"), (T_CARD, "st2"), (T_DAYS[0], "gauge"),
            (T_WIN, "ok"), (T_KEEP, "st1"), (T_OFF, "off"), (T_ANALYZE, "st2"), (T_IMPROVE, "st1"), (T_SKILL, "ok"), (T_OUT + 0.2, "back")]

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
