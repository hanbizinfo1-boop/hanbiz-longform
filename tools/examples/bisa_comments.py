# -*- coding: utf-8 -*-
r"""[레거시 — 10-13 부터 AE 안 씀. 새 장면은 html_motion(references/ae-replacement.md)]
빡이사DB 본편 23 «제 영상들 여러 가지 한번 살펴보시면 ~ 헤매지 마시고 댓글로 남겨주세요» (시퀀스 2346.177~2356.437, 양 끝 컷 경계)
사장님 10-08 «이런 곳에서(유튜브 댓글 캡처 3장) 아이디 같은 개인정보 블러 처리해서 저 화면 속에서 댓글이 쑥 나와서 확대되는 느낌으로 강조».
사장님이 이 구간 사람(V2)을 전체 화면 50%로 두심 → 21 처럼 사람이 왼쪽 아래 타원 PIP(사장님 마스크 실측)로 줄고, 뒤에 댓글 화면.
  댓글 페이지 셋이 넘겨짐(여러 영상) → 감사 댓글이 화면에서 쑥 나와 커짐 + 하트·«답글 4개» 동그라미 → 긴 질문 댓글이 쑥 + «답글 1개» →
  «댓글 추가» 칸이 쑥 + 깜빡이는 커서. 아이디·프로필 사진은 블러(빡이사 채널 자신의 것은 그대로).

  python bisa_comments.py [--조각만] [--소리만]
    → 빡이사DB\납품\23_댓글_2346.18~.mp4 (V1 만 — 사람은 사장님 V2 PIP 가 위에 얹힘, 10-08) · _효과음.xml · _미리보기.mp4
"""

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))   # tools/ (config.py)
import config  # noqa: E402
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

M.T0, M.T1 = 2346.177, 2356.437
M.DUR = M.T1 - M.T0
M.SEGS = [(2346.177, 2354.152, 3803.583, 3806.019), (2354.152, 2356.437, 3813.777, 3816.212)]
M.NAME = "23_댓글"
M.SFX_DIR = (config.WORK / "효과음23")
M.WORK = (config.WORK / "빡이사" / "ae23")
W, H, FPS = M.W, M.H, M.FPS
T0, T1 = M.T0, M.T1
WORK = M.WORK
SRC = (config.ORIG_ROOT / "빡이사DB" / "소재" / "23")
PRET = str(config.FONTS["pretendard_bold"])
BLUE, RED = (0, 100, 224), (220, 38, 38)

# ── 시각(_tmp/w23/words.txt) ──
T_IN, T_OUT = 2346.18, 2356.00
T_PAGES = [2346.62, 2346.98, 2347.40]       # 영상들 · 여러 가지 · 살펴보시면 → 페이지 셋 넘김
T_C1, T_C1R = 2348.36, 2349.58              # 댓글 → 감사 댓글 쑥 · 달아 드리거든요 → 하트·답글 동그라미
T_C2, T_C2R = 2351.54, 2353.12              # 상세하게 → 긴 질문 쑥 · 달아 → 답글
T_IN3, T_TYPE = 2354.10, 2355.10            # 헤매지 → 댓글 추가 칸 · 댓글로 → 커서

PERSON_FULL, PERSON_PIP = ((960, 540), 50), ((0.0927083 * W, 0.837037 * H), 30)
MASK = (1842, 1172, 529, 512)               # 사장님 PIP 타원(소스 4K)
WIN_S, WIN_C = 0.80, (1120, 470)            # 댓글 창 배율·가운데(화면)
CROP = (0, 168, 1352, 1032)                 # 캡처에서 댓글 칸만(주소창·탭·오른쪽 추천 영상 뺌)
# 블러(캡처 좌표): 다른 사람 프로필 사진 + 아이디 줄
BLUR = {49: [(665, 700), (855, 890)],
        50: [(245, 280), (347, 378), (481, 516), (579, 614), (697, 732), (847, 882)],
        51: [(179, 214), (349, 384), (499, 534), (649, 684), (819, 854), (968, 1004)]}
POPS = {"c1": (50, (0, 688, 1350, 832), [(140, 746, 176, 776, False), (60, 793, 190, 828, True)]),   # (캡처, 자를 칸, 동그라미[(x0,y0,x1,y1,알약?)])
        "c2": (51, (0, 172, 1350, 332), [(126, 249, 162, 279, False), (60, 296, 190, 330, True)]),
        "in": (49, (0, 430, 760, 478), [])}
POP_S = {"c1": 1.25, "c2": 1.25, "in": 1.9}                 # 쑥 나와서 커지는 배율
BOX = {}


def font(n):
    return ImageFont.truetype(PRET, n)


def save(name, im, xy):
    im.save(WORK / f"{name}.png")
    BOX[name] = (int(round(xy[0])), int(round(xy[1])), im.width, im.height)


def blurred(n):
    im = Image.open(SRC / f"yt_comments_{n}.png").convert("RGB")
    for y0, y1 in BLUR[n]:
        for box in ((10, y0 - 6, 60, y1 + 6), (62, y0 - 4, 340, y0 + 26)):     # 사진 · 아이디+날짜 줄
            reg = im.crop(box).filter(ImageFilter.GaussianBlur(9))
            im.paste(reg, box[:2])
    return im


def window(im, n):
    c = im.crop(CROP)
    w, h = int(c.width * WIN_S), int(c.height * WIN_S)
    c = c.resize((w, h), Image.LANCZOS).convert("RGBA")
    m = 30
    out = Image.new("RGBA", (w + 2 * m, h + 2 * m + 44), (0, 0, 0, 0))
    sh = Image.new("RGBA", out.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((m, m + 10, m + w, m + h + 44 + 10), 16, fill=(0, 0, 0, 110))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
    d = ImageDraw.Draw(out)
    d.rounded_rectangle((m, m, m + w, m + h + 44), 16, fill=(255, 255, 255, 255))
    d.rectangle((m, m + 30, m + w, m + 44), fill=(242, 242, 242, 255))
    d.rounded_rectangle((m, m, m + w, m + 44), 16, fill=(242, 242, 242, 255))
    for k, col in enumerate(((255, 95, 87), (254, 188, 46), (40, 200, 64))):
        d.ellipse((m + 18 + k * 24, m + 15, m + 32 + k * 24, m + 29), fill=col + (255,))
    out.alpha_composite(c, (m, m + 44))
    return out


def pop_img(src, box, rings, s):
    c = src.crop(box)
    w, h = int(c.width * s), int(c.height * s)
    c = c.resize((w, h), Image.LANCZOS).convert("RGBA")
    m = 34
    out = Image.new("RGBA", (w + 2 * m, h + 2 * m), (0, 0, 0, 0))
    sh = Image.new("RGBA", out.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((m - 4, m + 12, m + w + 4, m + h + 16), 18, fill=(0, 30, 90, 120))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
    mk = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mk).rounded_rectangle((0, 0, w - 1, h - 1), 16, fill=255)
    out.paste(c, (m, m), mk)
    ImageDraw.Draw(out).rounded_rectangle((m - 3, m - 3, m + w + 2, m + h + 2), 18, outline=BLUE + (255,), width=5)
    return out, m


def pieces():
    WORK.mkdir(parents=True, exist_ok=True)
    BOX.clear()
    g = np.linspace(0, 1, H)[:, None]
    top, bot = np.array([238, 242, 250]), np.array([214, 223, 240])
    bg = Image.fromarray(((top * (1 - g) + bot * g)[:, None, :].repeat(W, 1)).astype(np.uint8)).convert("RGBA")
    save("bg", bg, (0, 0))
    srcs = {n: blurred(n) for n in (49, 50, 51)}
    for n in (49, 50, 51):
        srcs[n].save(WORK / f"src{n}.png")
        win = window(srcs[n], n)
        save(f"win{n}", win, (WIN_C[0] - win.width / 2, WIN_C[1] - win.height / 2))
    dim = Image.new("RGBA", (W, H), (10, 20, 45, 120))
    save("dim", dim, (0, 0))
    # 쑥 나오는 댓글(원본 크기 1.0 → 화면에서 커짐)
    for nm, (n, box, rings) in POPS.items():
        s = POP_S[nm]
        im, m = pop_img(srcs[n], box, rings, s)
        cy = 420 if nm != "in" else 380
        save(f"p_{nm}", im, (W / 2 + 60 - im.width / 2, cy - im.height / 2))
        px, py, _, _ = BOX[f"p_{nm}"]
        for k, (x0, y0, x1, y1, is_pill) in enumerate(rings):
            X0, Y0 = px + m + (x0 - box[0]) * s, py + m + (y0 - box[1]) * s
            X1, Y1 = px + m + (x1 - box[0]) * s, py + m + (y1 - box[1]) * s
            r = Image.new("RGBA", (int(X1 - X0) + 30, int(Y1 - Y0) + 30), (0, 0, 0, 0))
            d = ImageDraw.Draw(r)
            if is_pill:
                d.rounded_rectangle((5, 5, r.width - 6, r.height - 6), r.height // 2, outline=RED + (255,), width=6)
            else:
                d.ellipse((5, 5, r.width - 6, r.height - 6), outline=RED + (255,), width=6)
            save(f"r_{nm}{k}", r, (X0 - 15, Y0 - 15))
    # 개념 알약(위)
    for nm, t, col in (("l_c1", "직접 답글 달아요", BLUE), ("l_c2", "자세한 질문도 OK", BLUE), ("l_in", "막히면 댓글로 질문", RED)):
        f = font(40)
        w = int(ImageDraw.Draw(Image.new("RGBA", (1, 1))).textlength(t, font=f)) + 60
        im = Image.new("RGBA", (w + 30, 104), (0, 0, 0, 0))
        g2 = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(g2).rounded_rectangle((15, 20, 15 + w, 92), 36, fill=(0, 0, 0, 90))
        im.alpha_composite(g2.filter(ImageFilter.GaussianBlur(8)))
        ImageDraw.Draw(im).rounded_rectangle((15, 14, 15 + w, 86), 36, fill=col + (255,))
        ImageDraw.Draw(im).text((15 + w / 2, 50), t, font=f, fill=(255, 255, 255), anchor="mm")
        save(nm, im, (W / 2 + 60 - im.width / 2, 120))
    car = Image.new("RGBA", (6, 52), (20, 20, 20, 255))
    px, py, pw, ph = BOX["p_in"]
    save("caret", car, (px + 34 + 54 * POP_S["in"], py + ph / 2 - 20))


# ── 애펙 ───────────────────────────────────────────────────────
def jsx(out_mov):
    js = AE.js
    s = lambda t: round(t - T0, 4)                         # noqa: E731
    L = ["function eo(p){ for(var k=1;k<=p.numKeys;k++){ var n=p.isSpatial?1:(p.value.length||1), o=[], i=[]; for(var j=0;j<n;j++){ o.push(new KeyframeEase(0,0.1)); i.push(new KeyframeEase(0,85)); } p.setTemporalEaseAtKey(k,i,o); } }",
         "function hold(p){ for(var q=1;q<=p.numKeys;q++){ p.setInterpolationTypeAtKey(q,KeyframeInterpolationType.HOLD); } }",
         f"(function(){{ var comp=app.project.items.addComp('bisa23',{W},{H},1,{M.DUR:.3f},{FPS}); comp.motionBlur=true;"]
    a = L.append
    nv = [0]

    def lay(name, anchor=None):
        nv[0] += 1
        v = f"L{nv[0]}"
        x, y, w, h = BOX[name]
        ax, ay = anchor if anchor else (w / 2, h / 2)
        a(f"var {v}=comp.layers.add(imp({js(str(WORK / f'{name}.png'))})); {v}.motionBlur=true; {v}.transform.anchorPoint.setValue([{ax},{ay}]); {v}.transform.position.setValue([{x + ax:.1f},{y + ay:.1f}]);")
        return v

    def opa(v, k, hold_=False):
        a(f"keys({v}.transform.opacity,{k});")
        if hold_:
            a(f"hold({v}.transform.opacity);")

    def life(t_in, t_out, fi=0.12, fo=0.22):
        return [[max(0, s(t_in) - 0.001), 0], [s(t_in) + fi, 100], [s(t_out), 100], [s(t_out) + fo, 0]]

    def pop(v, t, frm=72, dur=0.22):
        a(f"keys({v}.transform.scale,[[{s(t)},[{frm},{frm}]],[{s(t) + dur:.3f},[100,100]]]); eo({v}.transform.scale);")

    lay("bg")
    # 댓글 창 셋: 아래에서 올라오며 차례로 겹쳐 넘어감 → 마지막 «49» 가 바탕(끝 «댓글 추가» 와 맞춤)
    order = [(49, T_IN + 0.1, T_PAGES[1]), (51, T_PAGES[0], T_PAGES[2]), (50, T_PAGES[1], T_C2 - 0.3), (51, T_C2 - 0.3, T_IN3 - 0.2), (49, T_IN3 - 0.2, T1)]
    for k, (n, ta, tb) in enumerate(order):
        x, y, w, h = BOX[f"win{n}"]
        v = lay(f"win{n}")
        cx, cy = x + w / 2, y + h / 2
        a(f"keys({v}.transform.position,[[{s(ta)},[{cx + 60:.1f},{cy + 260:.1f}]],[{s(ta) + 0.4:.3f},[{cx:.1f},{cy:.1f}]]]); eo({v}.transform.position);")
        a(f"keys({v}.transform.rotation,[[{s(ta)},{4 if k % 2 else -4}],[{s(ta) + 0.4:.3f},0]]); eo({v}.transform.rotation);")
        k_ = [[max(0, s(ta) - 0.001), 0], [s(ta) + 0.12, 100]]
        if tb < T1:
            k_ += [[s(tb) + 0.4, 100], [s(tb) + 0.41, 0]]
        opa(v, k_)
    # 어둡게 + 쑥 나오는 댓글
    v = lay("dim"); opa(v, [[s(T_C1) - 0.001, 0], [s(T_C1) + 0.3, 100], [s(T_C1R) + 1.0, 100], [s(T_C1R) + 1.3, 0],
                            [s(T_C2) - 0.001, 0], [s(T_C2) + 0.3, 100], [s(T_C2R) + 0.8, 100], [s(T_C2R) + 1.1, 0],
                            [s(T_IN3) - 0.001, 0], [s(T_IN3) + 0.3, 100], [s(T_OUT), 100], [s(T_OUT) + 0.3, 0]])
    for nm, t_in, t_out, (n, box, rings), from_y in (("c1", T_C1, T_C1R + 1.1, POPS["c1"], None), ("c2", T_C2, T_C2R + 0.9, POPS["c2"], None),
                                                     ("in", T_IN3, T_OUT, POPS["in"], None)):
        x, y, w, h = BOX[f"p_{nm}"]
        v = lay(f"p_{nm}")
        # 창 속 제자리(창 배율)에서 → 화면 가운데 위로 쑥(커짐)
        wx, wy, ww, wh = BOX[f"win{n}"]
        sx = wx + 30 + ((box[0] + box[2]) / 2 - CROP[0]) * WIN_S
        sy = wy + 30 + 44 + ((box[1] + box[3]) / 2 - CROP[1]) * WIN_S
        s0 = WIN_S / POP_S[nm] * 100
        a(f"keys({v}.transform.position,[[{s(t_in)},[{sx:.1f},{sy:.1f}]],[{s(t_in) + 0.45:.3f},[{x + w / 2:.1f},{y + h / 2:.1f}]],[{s(t_out)},[{x + w / 2:.1f},{y + h / 2:.1f}]],[{s(t_out) + 0.35:.3f},[{sx:.1f},{sy:.1f}]]]); eo({v}.transform.position);")
        a(f"keys({v}.transform.scale,[[{s(t_in)},[{s0:.1f},{s0:.1f}]],[{s(t_in) + 0.45:.3f},[100,100]],[{s(t_out)},[100,100]],[{s(t_out) + 0.35:.3f},[{s0:.1f},{s0:.1f}]]]); eo({v}.transform.scale);")
        opa(v, [[s(t_in) - 0.001, 0], [s(t_in) + 0.05, 100], [s(t_out) + 0.3, 100], [s(t_out) + 0.35, 0]])
    for nm, tr, tout in (("c1", T_C1R, T_C1R + 1.1), ("c2", T_C2R, T_C2R + 0.9)):
        for k in range(2):
            t = tr + k * 0.3
            v = lay(f"r_{nm}{k}"); opa(v, life(t, tout, fi=0.06, fo=0.15)); pop(v, t, 150, 0.22)
    for nm, t, tout in (("l_c1", T_C1 + 0.3, T_C1R + 1.1), ("l_c2", T_C2 + 0.3, T_C2R + 0.9), ("l_in", T_TYPE, T_OUT)):
        v = lay(nm); opa(v, life(t, tout, fi=0.1, fo=0.2)); pop(v, t)
    v = lay("caret"); opa(v, [[s(T_IN3 + 0.5) - 0.001, 0], [s(T_IN3 + 0.5), 100]] + [[s(T_IN3 + 0.5 + k * 0.45 + 0.25), 0 if k % 2 == 0 else 100] for k in range(4)] + [[s(T_OUT), 100], [s(T_OUT) + 0.01, 0]], hold_=True)
    # 사람(사장님 컷 조각) + 타원 PIP 마스크 — 맨 위
    WITH_PERSON = False                                  # 10-08 사장님 «V2 로 위에서 덮어씌우면 되는데 왜 굳이 마스크까지 렌더» — 사람은 굽지 않음(V1 만)
    if WITH_PERSON:
        a(f"var cv=imp({js(str(M.CAM))});")
    for i, (ta, tb, _, cs) in enumerate(M.SEGS if WITH_PERSON else []):
        v = f"C{i}"
        a(f"var {v}=comp.layers.add(cv); {v}.startTime={s(ta) - cs:.4f}; {v}.inPoint={s(ta):.4f}; {v}.outPoint={s(tb):.4f}; {v}.audioEnabled=false;")
        (fx, fy), fs = PERSON_FULL
        (px, py), ps = PERSON_PIP
        a(f"keys({v}.transform.position,[[{s(T_IN)},[{fx},{fy}]],[{s(T_IN) + 0.45:.3f},[{px:.1f},{py:.1f}]],[{s(T_OUT)},[{px:.1f},{py:.1f}]],[{s(T_OUT) + 0.4:.3f},[{fx},{fy}]]]); ez({v}.transform.position);")
        a(f"keys({v}.transform.scale,[[{s(T_IN)},[{fs},{fs}]],[{s(T_IN) + 0.45:.3f},[{ps},{ps}]],[{s(T_OUT)},[{ps},{ps}]],[{s(T_OUT) + 0.4:.3f},[{fs},{fs}]]]); ez({v}.transform.scale);")
        k_ = 0.5523
        cxm, cym, rx, ry = MASK
        a(f"var mk{v}={v}.property('ADBE Mask Parade').addProperty('ADBE Mask Atom'); var sh{v}=new Shape();"
          f" sh{v}.vertices=[[{cxm},{cym - ry}],[{cxm + rx},{cym}],[{cxm},{cym + ry}],[{cxm - rx},{cym}]];"
          f" sh{v}.inTangents=[[{-rx * k_:.1f},0],[0,{-ry * k_:.1f}],[{rx * k_:.1f},0],[0,{ry * k_:.1f}]];"
          f" sh{v}.outTangents=[[{rx * k_:.1f},0],[0,{ry * k_:.1f}],[{-rx * k_:.1f},0],[0,{-ry * k_:.1f}]]; sh{v}.closed=true;"
          f" mk{v}.property('ADBE Mask Shape').setValue(sh{v});")
        a(f"keys(mk{v}.property('ADBE Mask Offset'),[[{s(T_IN)},2600],[{s(T_IN) + 0.45:.3f},0],[{s(T_OUT)},0],[{s(T_OUT) + 0.4:.3f},2600]]); ez(mk{v}.property('ADBE Mask Offset'));")
        a(f"{v}.moveToBeginning();")
    a(f"var rq=app.project.renderQueue.items.add(comp); var om=rq.outputModule(1); om.applyTemplate({js('고품질')}); om.file=new File({js(str(out_mov))});")
    a("log('ok bisa23'); })();")
    assert T_OUT + 0.4 < T1 + 0.01
    return "\n".join(L)


SND_FIX = {
    "in":    ("휙２.mp3", 0.6, 4, "peak"),
    "pg1":   ("ML_Page turn chime.wav", 0.8, 5, "onset"),              # 페이지 넘김
    "pop1":  ("ML_Cartoon bubbles popping.wav", 0.5, 5, "onset"),      # 댓글 쑥
    "pop2":  ("KN_pepSound1.wav", 0.4, 8, "onset"),
    "ring":  ("SEL_油性マーカーで字を書く.mp3", -0.35, 3, "onset"),     # 동그라미 = 마커
    "ok":    ("맑은소리.mp3", 0.8, 7, "onset"),
    "click": ("마우스 클릭.mp3", 0.25, 5, "onset"),                     # 댓글 칸 누름
    "type":  ("SEL_キーボード2.mp3", 0.45, 6, "onset"),
    "back":  ("휙1.mp3", 0.7, 8, "peak"),
}
EVENTS = [(T_IN + 0.25, "in"), (T_PAGES[0], "pg1"), (T_C1, "pop1"), (T_C1R, "ring"), (T_C1R + 0.3, "ok"), (T_C2, "pop2"), (T_C2R, "ring"),
          (T_IN3, "click"), (T_TYPE, "type"), (T_OUT + 0.2, "back")]
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
    lec_xml.V_TRACK, lec_xml.A_TRACK = 1, 2
    print(lec_xml.write(M.OUT / f"{M.NAME}_효과음.xml", f"빡이사DB_{M.NAME}", scene, M.DUR, T0,
                        [(t, f) for t, f, _ in placed], 59.94, tag="bs23"))
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
