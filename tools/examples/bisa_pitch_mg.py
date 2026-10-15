# -*- coding: utf-8 -*-
r"""[레거시 — 10-13 부터 AE 안 씀. 새 장면은 html_motion(references/ae-replacement.md)]
빡이사DB 본편 22 «말 그대로 저는 그냥 광고 세팅법이라고 해서 ~ 라고 제가 권장드리고» (시퀀스 2290.555~2319.617)
사장님 10-08 «모션그래픽처럼 좀 화려하고 연출 좋게 시도 · 여러 자료 화면 띄워서 각각 날아다니면서 자막에 맞춰서 맞는 자료가 나오게».
사장님이 이 구간 사람(V2)을 전체 화면 50%로 두심 → 사람이 왼쪽 절반으로(크기 그대로), 오른쪽 어두운 모션그래픽 무대(17 반반 결).
자료 = 이 영상에서 만든 장면들의 정지 화면(_tmp/w22/cards — 05 캠페인 · 08 예산 · 09 언어 · 13 세트 / 21 CRM · 18 니즈 · 19 라이브러리 · 16 학습 /
  07 · 14 · 15 실수 장면) → 말에 맞춰 날아들고 날아감 + 큰 글(개념어, 말 따라 쓰지 않기).

  python bisa_pitch_mg.py [--조각만] [--소리만]
    → 빡이사DB\납품\22_실무강조_2290.56~.mp4 (사람 포함 → **V3**, 시작·끝 클립 가운데) · _효과음.xml · _미리보기.mp4
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

M.T0, M.T1 = 2290.555, 2319.617
M.DUR = M.T1 - M.T0
_V = [(2280.895, 2291.489, 3697.244, 3695.992 + (2280.895 - 2277.175)), (2291.489, 2294.409, 3708.004, 3710.473), (2294.409, 2295.944, 3711.074, 3713.543),
      (2295.944, 2303.401, 3712.792, 3715.262), (2303.401, 2305.136, 3720.684, 3723.136), (2305.136, 2306.771, 3722.736, 3725.188),
      (2306.771, 2312.026, 3724.521, 3726.973), (2312.026, 2316.965, 3729.96, 3732.412), (2316.965, 2322.003, 3735.015, 3737.467)]
M.SEGS = [(max(a, M.T0), min(b, M.T1), r + max(0, M.T0 - a), c + max(0, M.T0 - a)) for a, b, r, c in _V if b > M.T0 and a < M.T1]
M.NAME = "22_실무강조"
M.SFX_DIR = (config.WORK / "효과음22")
M.WORK = (config.WORK / "빡이사" / "ae22")
W, H, FPS = M.W, M.H, M.FPS
T0, T1 = M.T0, M.T1
WORK = M.WORK
CARDS = (config.WORK / "w22" / "cards")
PRET = str(config.FONTS["pretendard_bold"])
NOTO = str(config.FONTS["noto_sans_kr"])
WHITE, GOLD, BLUE, RED, NAVY = (255, 255, 255), (255, 200, 61), (61, 139, 255), (255, 77, 77), (13, 22, 48)

# ── 시각(_tmp/w22/words.txt) ──
T_SPLIT, T_BACK = 2290.56, 2319.20
T_SET = 2291.86                         # 광고 세팅법이라고
T_SETOUT = 2293.13                      # 세팅만 하는 게 아니라
T_MONEY = 2294.45                       # 돈 버는 방법
T_MIS = 2297.91                         # 시행착오
T_X = 2298.95                           # 겪지 말라고
T_CHECK, T_UNCHECK = 2300.27, 2300.57   # 체크 푸세요
T_ALL = 2301.39                         # 이런 것들도 다
T_SAME = 2303.69                        # 수강을 듣게 되시면
T_THEORY, T_PRACT, T_MONEY2 = 2306.05, 2308.51, 2309.23
T_SWEEP = 2310.51                       # 제가 알려드리고
T_NUM = 2312.61                         # 순수익 1000만 원 미만
T_AGENCY, T_LEARN, T_REC = 2314.88, 2316.47, 2318.73

PX = 900
PERSON_FULL, PERSON_HALF = (960, 540), (480, 540)
CAPTION = (480, 900, 1440, 1080)
CX = 1440                               # 무대 가운데 x
BOX = {}

GROUPS = {"set": ["05", "08", "09", "13"], "money": ["21", "18", "19", "16"], "mis": ["07", "14", "15"]}
GRID = [(1222, 360, -4), (1660, 350, 3), (1230, 620, 2), (1668, 630, -3)]
FAN = [(1125, 480, 0), (1440, 480, 0), (1755, 480, 0)]          # 겹치지 않게 나란히(10-08 «레이아웃 겹치는 거»)
REAL = [("an", 292), ("bud", 516), ("form", 756)]                 # 실제 녹화 화면: 오디언스 네트워크 · 예산 공유 · 유연한 양식 표시 (10-08)
CARDS2 = (config.WORK / "w22" / "cards2")


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


def glow_text(t, size, col, glow=None, pad=40):
    f = font(size)
    w, h = int(tl(t, f)) + 2 * pad, int(size * 1.5) + 2 * pad
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if glow:
        g = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(g).text((w / 2, h / 2), t, font=f, fill=glow + (200,), anchor="mm")
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(14)))
    ImageDraw.Draw(im).text((w / 2, h / 2), t, font=f, fill=col + (255,), anchor="mm")
    return im


def chip(t, size, fg, bg, padx=26, h=None, outline=None):
    f = font(size)
    w = int(tl(t, f)) + 2 * padx
    h = h or int(size * 1.8)
    m = 20
    im = Image.new("RGBA", (w + 2 * m, h + 2 * m), (0, 0, 0, 0))
    g = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(g).rounded_rectangle((m, m, m + w, m + h), h // 2, fill=bg + (150,))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(12)))
    ImageDraw.Draw(im).rounded_rectangle((m, m, m + w, m + h), h // 2, fill=bg + (255,), outline=(outline + (255,)) if outline else None, width=3)
    ImageDraw.Draw(im).text((m + w / 2, m + h / 2), t, font=f, fill=fg, anchor="mm")
    return im


def card(src, w=400):
    im = Image.open(src).convert("RGBA")
    h = int(w * im.height / im.width)
    im = im.resize((w, h), Image.LANCZOS)
    m = 26
    c = Image.new("RGBA", (w + 2 * m, h + 2 * m), (0, 0, 0, 0))
    g = Image.new("RGBA", c.size, (0, 0, 0, 0))
    ImageDraw.Draw(g).rounded_rectangle((m - 4, m - 4, m + w + 4, m + h + 4), 16, fill=(110, 170, 255, 170))
    c.alpha_composite(g.filter(ImageFilter.GaussianBlur(14)))
    mk = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mk).rounded_rectangle((0, 0, w - 1, h - 1), 12, fill=255)
    c.paste(im, (m, m), mk)
    ImageDraw.Draw(c).rounded_rectangle((m - 3, m - 3, m + w + 2, m + h + 2), 14, outline=(255, 255, 255, 235), width=4)
    return c


def stamp(ok, col, r=46):
    im = Image.new("RGBA", (2 * r + 8, 2 * r + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((4, 4, 2 * r + 4, 2 * r + 4), fill=col + (255,), outline=(255, 255, 255, 255), width=5)
    c = r + 4
    if ok:
        d.line(((c - 22, c + 2), (c - 6, c + 18), (c + 24, c - 16)), fill=(255, 255, 255, 255), width=10, joint="curve")
    else:
        d.line((c - 18, c - 18, c + 18, c + 18), fill=(255, 255, 255, 255), width=10)
        d.line((c + 18, c - 18, c - 18, c + 18), fill=(255, 255, 255, 255), width=10)
    return im


def pieces():
    WORK.mkdir(parents=True, exist_ok=True)
    BOX.clear()
    # 무대 판(어두운 남색 + 모눈 + 빛 번짐)
    pn = Image.new("RGBA", (960 + 60, H), (0, 0, 0, 0))
    s3 = Image.new("RGBA", pn.size, (0, 0, 0, 0))
    ImageDraw.Draw(s3).rectangle((60, 0, 1020, H), fill=(0, 0, 0, 140))
    pn.alpha_composite(s3.filter(ImageFilter.GaussianBlur(22)))
    g = np.linspace(0, 1, H)[:, None]
    top, bot = np.array([16, 28, 62]), np.array([9, 14, 32])
    body = (top * (1 - g) + bot * g)[:, None, :].repeat(960, 1).astype(np.uint8)
    body = Image.fromarray(body).convert("RGBA")
    d = ImageDraw.Draw(body)
    for x in range(0, 960, 60):
        d.line((x, 0, x, H), fill=(40, 60, 110, 255), width=1)
    for y in range(0, H, 60):
        d.line((0, y, 960, y), fill=(40, 60, 110, 255), width=1)
    gl = Image.new("RGBA", (960, H), (0, 0, 0, 0))
    ImageDraw.Draw(gl).ellipse((180, 180, 780, 780), fill=(60, 110, 230, 90))
    body.alpha_composite(gl.filter(ImageFilter.GaussianBlur(120)))
    pn.alpha_composite(body, (60, 0))
    save("panel", pn, (PX, 0))
    # 자료 카드
    for k, n in enumerate(GROUPS["set"] + GROUPS["money"]):
        im = card(CARDS / f"{n}.png", 400)
        x, y, _ = GRID[k % 4]
        save(f"k{n}", im, (x - im.width / 2, y - im.height / 2))
    for k, n in enumerate(GROUPS["mis"]):
        im = card(CARDS / f"{n}.png", 258)
        x, y, _ = FAN[k]
        save(f"m{n}", im, (x - im.width / 2, y - im.height / 2))
        st = stamp(False, RED, 34)
        save(f"x{n}", st, (x + im.width / 2 - 26 - 30 - st.width / 2, y - im.height / 2 + 26 - 6))
    # 큰 글 · 칩
    for nm, t, size, col, glow, y in (("t_set", "광고 세팅법", 64, WHITE, BLUE, 140), ("t_money", "돈 버는 방법", 96, GOLD, GOLD, 140),
                                      ("t_mis", "시행착오 줄이기", 70, WHITE, RED, 140), ("t_same", "수강도 똑같이", 88, WHITE, BLUE, 300),
                                      ("t_pract", "실무", 150, BLUE, BLUE, 420), ("t_money2", "= 돈 버는 법", 72, GOLD, GOLD, 600),
                                      ("t_num_a", "순수익", 54, WHITE, None, 260), ("t_num_b", "월 1,000만 원", 128, GOLD, GOLD, 420),
                                      ("t_num_c", "미만이라면", 54, WHITE, None, 580), ("t_all", "실전 팁까지 전부", 64, WHITE, BLUE, 140)):
        im = glow_text(t, size, col, glow)
        save(nm, im, (CX - im.width / 2, y - im.height / 2))
    # 이론 칩(지워짐)
    for k, t in enumerate(("ABO", "CBO", "복잡한 이론")):
        im = chip(t, 44, WHITE, (70, 80, 110), padx=30, h=80)
        x = CX + (k - 1) * 280
        save(f"th{k}", im, (x - im.width / 2, 420 - im.height / 2))
        st = Image.new("RGBA", (im.width - 30, 14), (0, 0, 0, 0))
        ImageDraw.Draw(st).rounded_rectangle((0, 0, im.width - 31, 13), 7, fill=RED + (255,))
        save(f"ths{k}", st, (x - im.width / 2 + 15, 420 - 7))
    # 실제 화면 카드(켜짐/꺼짐)
    for nm, y in REAL:
        for st_ in ("on", "off"):
            im = card(CARDS2 / f"{nm}_{st_}.png", 420)
            save(f"r_{nm}_{st_}", im, (CX - im.width / 2, y - im.height / 2))
    # 체크 해제 카드(1판 — 지금은 안 씀)
    cw, chh = 560, 220
    im = Image.new("RGBA", (cw + 40, chh + 40), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((20, 20, 20 + cw, 20 + chh), 22, fill=(255, 255, 255, 255))
    d = ImageDraw.Draw(im)
    for j in range(3):
        d.rounded_rectangle((170, 70 + j * 46, 170 + (330 - j * 70), 90 + j * 46), 10, fill=(222, 228, 238, 255))
    save("chk_card", im, (CX - im.width / 2, 470 - im.height / 2))
    for nm, on in (("chk_on", True), ("chk_off", False)):
        b = Image.new("RGBA", (96, 96), (0, 0, 0, 0))
        d = ImageDraw.Draw(b)
        if on:
            d.rounded_rectangle((6, 6, 89, 89), 16, fill=(24, 119, 242, 255))
            d.line(((24, 50), (42, 68), (74, 30)), fill=(255, 255, 255, 255), width=11, joint="curve")
        else:
            d.rounded_rectangle((6, 6, 89, 89), 16, fill=(255, 255, 255, 255), outline=(150, 156, 166, 255), width=6)
        save(nm, b, (CX - 280 + 40, 470 - 48))
    cur = Image.new("RGBA", (64, 84), (0, 0, 0, 0))
    pts = [(4, 4), (4, 60), (18, 47), (29, 72), (40, 67), (29, 43), (48, 43)]
    ImageDraw.Draw(cur).polygon(pts, fill=(255, 255, 255, 255), outline=(20, 20, 20, 255))
    ImageDraw.Draw(cur).line(pts + [pts[0]], fill=(20, 20, 20, 255), width=3)
    save("cursor", cur, (CX - 200, 500))
    im = chip("체크 해제", 40, WHITE, BLUE, padx=28, h=70)
    save("chk_lab", im, (CX - im.width / 2, 140 - im.height / 2))
    # 대행 ✕ / 직접 배우기 ✓ / 추천
    for nm, t, col, x in (("c_agency", "대행 맡기기", RED, 1215), ("c_learn", "직접 배우기", BLUE, 1665)):
        im = Image.new("RGBA", (400, 300), (0, 0, 0, 0))
        g = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(g).rounded_rectangle((20, 20, 380, 280), 26, fill=col + (140,))
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(16)))
        ImageDraw.Draw(im).rounded_rectangle((20, 20, 380, 280), 26, fill=(18, 30, 64, 255), outline=col + (255,), width=6)
        ImageDraw.Draw(im).text((200, 190), t, font=font(46), fill=WHITE, anchor="mm")
        save(nm, im, (x - 200, 470 - 150))
        st = stamp(nm == "c_learn", col, 40)
        save(f"s_{nm}", st, (x - st.width / 2, 470 - 150 + 40))
    rc = Image.new("RGBA", (210, 210), (0, 0, 0, 0))
    d = ImageDraw.Draw(rc)
    d.ellipse((8, 8, 202, 202), outline=GOLD + (255,), width=10)
    d.ellipse((26, 26, 184, 184), outline=GOLD + (255,), width=4)
    d.text((105, 92), "빡이사", font=font(34), fill=GOLD, anchor="mm")
    d.text((105, 136), "추천", font=font(44), fill=GOLD, anchor="mm")
    save("rec", rc, (1665 + 30, 470 - 250))
    # 빛 훑기(가로 빛줄)
    sw = Image.new("RGBA", (900, 16), (0, 0, 0, 0))
    a = np.zeros((16, 900), np.uint8)
    xx = np.arange(900)
    a[:] = (np.clip(1 - np.abs(xx - 450) / 450, 0, 1) ** 1.5 * 255).astype(np.uint8)
    sw = Image.new("RGBA", (900, 16), GOLD + (0,))
    sw.putalpha(Image.fromarray(a))
    save("sweep", sw.filter(ImageFilter.GaussianBlur(3)), (CX - 450, 690))
    check_layout()


def check_layout():
    bad = []
    for n, (x, y, w, h) in BOX.items():
        if n in ("panel", "sweep"):
            continue
        al = np.asarray(Image.open(WORK / f"{n}.png"))[..., 3] > 60
        ys, xs = np.where(al)
        b = (x + xs.min(), y + ys.min(), x + xs.max(), y + ys.max())
        if b[0] < 960 or b[2] > W - 8 or b[1] < 8:
            bad.append(f"{n} {b} 판 밖")
        if b[0] < CAPTION[2] and b[3] > CAPTION[1]:
            bad.append(f"{n} {b} ↔ 자막")
    if bad:
        raise SystemExit("레이아웃 겹침:\n  " + "\n  ".join(bad))
    print("겹침 없음")


# ── 애펙 ───────────────────────────────────────────────────────
def jsx(out_mov):
    js = AE.js
    s = lambda t: round(t - T0, 4)                         # noqa: E731
    L = ["function eo(p){ for(var k=1;k<=p.numKeys;k++){ var n=p.isSpatial?1:(p.value.length||1), o=[], i=[]; for(var j=0;j<n;j++){ o.push(new KeyframeEase(0,0.1)); i.push(new KeyframeEase(0,85)); } p.setTemporalEaseAtKey(k,i,o); } }",
         "function hold(p){ for(var q=1;q<=p.numKeys;q++){ p.setInterpolationTypeAtKey(q,KeyframeInterpolationType.HOLD); } }",
         f"(function(){{ var comp=app.project.items.addComp('bisa22',{W},{H},1,{M.DUR:.3f},{FPS}); comp.motionBlur=true; comp.shutterAngle=220;"]
    a = L.append
    nv = [0]

    def lay(name, anchor=None, parent="PN"):
        nv[0] += 1
        v = f"L{nv[0]}"
        x, y, w, h = BOX[name]
        ax, ay = anchor if anchor else (w / 2, h / 2)
        a(f"var {v}=comp.layers.add(imp({js(str(WORK / f'{name}.png'))})); {v}.motionBlur=true; {v}.parent={parent}; {v}.transform.scale.setValue([100,100]); {v}.transform.anchorPoint.setValue([{ax},{ay}]); {v}.transform.position.setValue([{x + ax - PX:.1f},{y + ay:.1f}]);")
        return v

    def pos_of(name):
        x, y, w, h = BOX[name]
        return x + w / 2 - PX, y + h / 2

    def opa(v, k):
        a(f"keys({v}.transform.opacity,{k});")

    def fly_in(v, name, t, dx=420, rot=24, frm=30, dur=0.5, dy=0):
        x, y = pos_of(name)
        a(f"keys({v}.transform.position,[[{s(t)},[{x + dx:.1f},{y + dy:.1f}]],[{s(t) + dur:.3f},[{x:.1f},{y:.1f}]]]); eo({v}.transform.position);")
        a(f"keys({v}.transform.scale,[[{s(t)},[{frm},{frm}]],[{s(t) + dur:.3f},[100,100]]]); eo({v}.transform.scale);")
        a(f"keys({v}.transform.rotation,[[{s(t)},{rot}],[{s(t) + dur:.3f},0]]); eo({v}.transform.rotation);")

    def fly_out(v, name, t, dx=-520, rot=-18, to=60, dur=0.38, dy=0):
        x, y = pos_of(name)
        a(f"keys({v}.transform.position,[[{s(t)},[{x:.1f},{y:.1f}]],[{s(t) + dur:.3f},[{x + dx:.1f},{y + dy:.1f}]]]);")
        a(f"keys({v}.transform.scale,[[{s(t)},[100,100]],[{s(t) + dur:.3f},[{to},{to}]]]);")
        a(f"keys({v}.transform.rotation,[[{s(t)},0],[{s(t) + dur:.3f},{rot}]]);")

    def life(t_in, t_out, fi=0.12, fo=0.3):
        return [[max(0, s(t_in) - 0.001), 0], [s(t_in) + fi, 100], [s(t_out), 100], [s(t_out) + fo, 0]]

    def slam(v, t, frm=170, dur=0.24):
        a(f"keys({v}.transform.scale,[[{s(t)},[{frm},{frm}]],[{s(t) + dur:.3f},[100,100]]]); eo({v}.transform.scale);")

    def tilt(v, rot):
        a(f"{v}.transform.rotation.expression=\"value+{rot}\";")

    # 사람(사장님 컷 조각): 50% 가운데 → 왼쪽 절반 → 끝에 가운데
    a(f"var cv=imp({js(str(M.CAM))});")
    for i, (ta, tb, _, cs) in enumerate(M.SEGS):
        v = f"C{i}"
        a(f"var {v}=comp.layers.add(cv); {v}.startTime={s(ta) - cs:.4f}; {v}.inPoint={s(ta):.4f}; {v}.outPoint={s(tb):.4f}; {v}.audioEnabled=false; {v}.transform.scale.setValue([50,50]);")
        a(f"keys({v}.transform.position,[[{s(T_SPLIT)},[{PERSON_FULL[0]},{PERSON_FULL[1]}]],[{s(T_SPLIT) + 0.45:.3f},[{PERSON_HALF[0]},{PERSON_HALF[1]}]],[{s(T_BACK)},[{PERSON_HALF[0]},{PERSON_HALF[1]}]],[{s(T_BACK) + 0.36:.3f},[{PERSON_FULL[0]},{PERSON_FULL[1]}]]]); ez({v}.transform.position);")
    a(f"var PN=comp.layers.add(imp({js(str(WORK / 'panel.png'))})); PN.transform.anchorPoint.setValue([0,540]);")
    a(f"keys(PN.transform.position,[[{s(T_SPLIT)},[{W},540]],[{s(T_SPLIT) + 0.45:.3f},[{PX},540]],[{s(T_BACK)},[{PX},540]],[{s(T_BACK) + 0.36:.3f},[{W + 40},540]]]); ez(PN.transform.position);")
    a("PN.moveToBeginning();")

    # ① 광고 세팅법 — 카드 넷이 깊이에서 날아들어 격자 → 왼쪽으로 쓸려 나감
    v = lay("t_set"); opa(v, life(T_SET - 0.1, T_SETOUT + 0.2, fo=0.2)); slam(v, T_SET - 0.1, 140)
    for k, n in enumerate(GROUPS["set"]):
        t = T_SET + k * 0.13
        v = lay(f"k{n}"); tilt(v, GRID[k][2])
        opa(v, life(t, T_SETOUT + k * 0.06, fi=0.1, fo=0.3)); fly_in(v, f"k{n}", t, dx=380 + k * 40, rot=28 - k * 6)
        fly_out(v, f"k{n}", T_SETOUT + k * 0.06, dx=-560, rot=-22, to=55)
    # ② 돈 버는 방법 — 큰 글 쾅 + 카드 넷이 아래에서 휘어 올라옴
    v = lay("t_money"); opa(v, life(T_MONEY, T_MIS - 0.1, fi=0.06, fo=0.25)); slam(v, T_MONEY, 190, 0.26)
    for k, n in enumerate(GROUPS["money"]):
        t = T_MONEY + 0.35 + k * 0.16
        v = lay(f"k{n}"); tilt(v, GRID[k][2])
        opa(v, life(t, T_MIS - 0.1 + k * 0.04, fi=0.1, fo=0.3)); fly_in(v, f"k{n}", t, dx=(-1) ** k * 160, dy=520, rot=(-1) ** k * 30, frm=40)
        fly_out(v, f"k{n}", T_MIS - 0.1 + k * 0.04, dx=0, dy=-620, rot=(-1) ** k * 25, to=70, dur=0.36)
    # ③ 시행착오 — 실수 장면 셋 부채꼴 + ✕ 도장 → 체크 해제 → «실전 팁까지 전부»
    v = lay("t_mis"); opa(v, life(T_MIS, T_CHECK - 0.15, fi=0.08, fo=0.2)); slam(v, T_MIS, 150)
    for k, n in enumerate(GROUPS["mis"]):
        t = T_MIS + 0.2 + k * 0.14
        v = lay(f"m{n}"); tilt(v, FAN[k][2])
        opa(v, life(t, T_CHECK - 0.1, fi=0.1, fo=0.25)); fly_in(v, f"m{n}", t, dx=0, dy=-480, rot=(k - 1) * 30, frm=50)
        v = lay(f"x{n}"); opa(v, life(T_X + k * 0.15, T_CHECK - 0.1, fi=0.04, fo=0.25)); slam(v, T_X + k * 0.15, 220, 0.2)
    v = lay("chk_lab"); opa(v, life(T_CHECK, T_ALL - 0.05, fi=0.08, fo=0.2)); slam(v, T_CHECK, 140)
    # 실제 화면 셋(오디언스 네트워크 · 예산 공유 · 유연한 양식 표시)이 날아들고 «푸세요»에 차례로 꺼짐 → «이런 것들도 다»
    for k, (nm, y) in enumerate(REAL):
        t = T_CHECK + k * 0.1
        tsw = T_UNCHECK + 0.06 + k * 0.16
        v = lay(f"r_{nm}_on"); opa(v, [[s(t) - 0.001, 0], [s(t) + 0.1, 100], [s(tsw) - 0.001, 100], [s(tsw), 0]]); fly_in(v, f"r_{nm}_on", t, dx=420, rot=14, frm=50, dur=0.4)
        v = lay(f"r_{nm}_off"); opa(v, [[s(tsw) - 0.001, 0], [s(tsw), 100], [s(T_SAME - 0.1), 100], [s(T_SAME - 0.1) + 0.3, 0]]); slam(v, tsw, 106, 0.16)
        fly_out(v, f"r_{nm}_off", T_SAME - 0.1, dx=-480, rot=-14, to=60, dur=0.36)
    v = lay("cursor", anchor=(4, 4))
    ax, ay = pos_of("r_an_on")
    tx, ty = ax + 83, ay + 3                                       # 오디언스 네트워크 체크박스(카드 420폭 기준)
    a(f"keys({v}.transform.position,[[{s(T_CHECK) + 0.2:.3f},[{tx + 200:.1f},{ty + 180:.1f}]],[{s(T_UNCHECK):.3f},[{tx:.1f},{ty:.1f}]]]); eo({v}.transform.position);")
    a(f"keys({v}.transform.scale,[[{s(T_UNCHECK)},[100,100]],[{s(T_UNCHECK) + 0.06:.3f},[84,84]],[{s(T_UNCHECK) + 0.18:.3f},[100,100]]]);")
    opa(v, life(T_CHECK + 0.2, T_ALL - 0.05, fi=0.1, fo=0.2))
    v = lay("t_all"); opa(v, life(T_ALL, T_SAME - 0.1, fi=0.08, fo=0.2)); slam(v, T_ALL, 150)
    # ④ 수강도 똑같이 → 이론 칩 지움 → 실무 = 돈 버는 법
    v = lay("t_same"); opa(v, life(T_SAME, T_THEORY - 0.05, fi=0.08, fo=0.2)); slam(v, T_SAME, 150)
    for k in range(3):
        t = T_THEORY + k * 0.12
        v = lay(f"th{k}"); opa(v, life(t, T_PRACT - 0.15, fi=0.08, fo=0.2)); fly_in(v, f"th{k}", t, dx=0, dy=-200, rot=0, frm=60, dur=0.3)
        fly_out(v, f"th{k}", T_PRACT - 0.15, dx=(k - 1) * 380, dy=260, rot=(k - 1) * 40, to=50, dur=0.4)
        x, y, w, h = BOX[f"ths{k}"]
        sv = lay(f"ths{k}", anchor=(0, h / 2)); opa(sv, life(T_THEORY + 0.6 + k * 0.12, T_PRACT - 0.15, fi=0.03, fo=0.2))
        a(f"keys({sv}.transform.scale,[[{s(T_THEORY + 0.6 + k * 0.12):.3f},[0,100]],[{s(T_THEORY + 0.85 + k * 0.12):.3f},[100,100]]]);")
    v = lay("t_pract"); opa(v, life(T_PRACT, T_NUM - 0.1, fi=0.06, fo=0.25)); slam(v, T_PRACT, 200, 0.26)
    v = lay("t_money2"); opa(v, life(T_MONEY2, T_NUM - 0.1, fi=0.08, fo=0.25)); fly_in(v, "t_money2", T_MONEY2, dx=300, rot=0, frm=80, dur=0.35)
    x, y, w, h = BOX["sweep"]
    v = lay("sweep"); opa(v, [[s(T_SWEEP) - 0.001, 0], [s(T_SWEEP) + 0.05, 100], [s(T_SWEEP) + 0.6, 100], [s(T_SWEEP) + 0.8, 0]])
    a(f"keys({v}.transform.position,[[{s(T_SWEEP)},[{x + w / 2 - PX - 500:.1f},{y + h / 2:.1f}]],[{s(T_SWEEP) + 0.7:.3f},[{x + w / 2 - PX + 500:.1f},{y + h / 2:.1f}]]]);")
    # ⑤ 순수익 월 1,000만 원 미만
    for nm, t, frm in (("t_num_a", T_NUM - 0.05, 130), ("t_num_b", T_NUM + 0.4, 220), ("t_num_c", T_NUM + 0.95, 130)):
        v = lay(nm); opa(v, life(t, T_AGENCY - 0.1, fi=0.06, fo=0.25)); slam(v, t, frm, 0.24)
    # ⑥ 대행 ✕ / 직접 배우기 ✓ → 추천 도장
    for nm, t in (("c_agency", T_AGENCY), ("c_learn", T_LEARN)):
        v = lay(nm); opa(v, life(t, T_BACK, fi=0.1, fo=0.2)); fly_in(v, nm, t, dx=0, dy=-300, rot=0, frm=60, dur=0.35)
        v = lay(f"s_{nm}"); opa(v, life(t + 0.35, T_BACK, fi=0.04, fo=0.2)); slam(v, t + 0.35, 220, 0.2)
    v = lay("rec"); opa(v, life(T_REC, T_BACK, fi=0.05, fo=0.2)); slam(v, T_REC, 260, 0.26)
    a(f"keys({v}.transform.rotation,[[{s(T_REC)},-30],[{s(T_REC) + 0.26:.3f},-12]]); eo({v}.transform.rotation);")
    a(f"var rq=app.project.renderQueue.items.add(comp); var om=rq.outputModule(1); om.applyTemplate({js('고품질')}); om.file=new File({js(str(out_mov))});")
    a("log('ok bisa22'); })();")
    assert T_BACK + 0.36 < T1
    return "\n".join(L)


SND_FIX = {                             # 10-08 사장님 «천만 원 미만인데 왜 축하 효과음 · 도장엔 왜 도장 효과음 안 써» → 뜻·그림에 맞춰 다시
    "split": ("휙２.mp3", 0.6, 4, "peak"),
    "sw1":   ("ML_Fast sweep transition.wav", 0.6, 5, "onset"),       # 카드 날아듦
    "sw2":   ("ML_Fast air sweep transition.wav", 0.6, 5, "onset"),
    "sw3":   ("ML_Fast small sweep transition.wav", 0.6, 5, "onset"),
    "big1":  ("SEL_文字表示の衝撃音1.mp3", 0.8, 5, "onset"),          # 큰 글 등장(강조 자막 쿵 — 중립)
    "big2":  ("SEL_文字表示の衝撃音2.mp3", 0.8, 5, "onset"),
    "big3":  ("SEL_文字表示の衝撃音3.mp3", 0.8, 5, "onset"),          # 월 1,000만 원 미만 = 조건(축하 아님)
    "st1":   ("KN_pepSound1.wav", 0.4, 8, "onset"),
    "st2":   ("KN_pepSound2.wav", 0.4, 8, "onset"),
    "stamp": ("도장.mp3", 0.6, 5, "onset"),                           # 도장 그림엔 도장 소리(사장님 라이브러리 A★)
    "no":    ("KN_error_003.wav", 0.5, 5, "onset"),                   # 부정(지움·대행 ✕)
    "click": ("마우스 클릭.mp3", 0.25, 5, "onset"),
    "ok":    ("맑은소리.mp3", 0.8, 7, "onset"),                        # 긍정(직접 배우기 ✓)
    "shine": ("SEL_キラッ1.mp3", 0.7, -1, "onset"),                   # 빛줄 훑기
    "back":  ("휙1.mp3", 0.7, 8, "peak"),
}
EVENTS = [(T_SPLIT + 0.25, "split"), (T_SET, "sw1"), (T_SETOUT, "sw2"), (T_MONEY, "big1"), (T_MIS, "st1"), (T_MIS + 0.2, "sw3"),
          (T_X, "stamp"), (T_CHECK, "st2"), (T_UNCHECK, "click"), (T_ALL, "sw1"), (T_SAME, "st1"), (T_THEORY, "st2"), (T_THEORY + 0.6, "no"),
          (T_PRACT, "big2"), (T_MONEY2, "st1"), (T_SWEEP, "shine"), (T_NUM + 0.4, "big3"), (T_AGENCY, "sw3"), (T_AGENCY + 0.35, "no"),
          (T_LEARN, "sw2"), (T_LEARN + 0.35, "ok"), (T_REC, "stamp"), (T_BACK + 0.2, "back")]
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
    lec_xml.V_TRACK, lec_xml.A_TRACK = 3, 2
    print(lec_xml.write(M.OUT / f"{M.NAME}_효과음.xml", f"빡이사DB_{M.NAME}", scene, M.DUR, T0,
                        [(t, f) for t, f, _ in placed], 59.94, tag="bs22"))
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
