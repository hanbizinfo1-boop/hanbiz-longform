# -*- coding: utf-8 -*-
r"""빡이사DB 본편 18 «이제 상담 신청을 넣잖아요 ~ 이거 많이들 경험하고 계실 거잖아요» (시퀀스 1603.919~1617.232, 양 끝 컷 경계)
사장님 10-08 «애니메이션 연출(3인칭 관찰자 시점에서 장면 연출) · 3D 보다는 2D 체로, 그냥 움직이는 느낌만 모션만».
→ 화면 전체 거실 무대(2D 플랫, Codex 같은 캐릭터 4동작 — 소재/18/). 무대가 오른쪽에서 밀려 들어와 끝에 왼쪽으로 빠짐(06·07 B 결).
  고객이 소파에서 신청(휴대폰 위 «상담 신청 완료») → 들뜬 얼굴 + 왼쪽 위 «상담 니즈» 게이지 꽉 참 «신청 직후 = 니즈 최고» →
  달력 «+1일 · +2일» 넘어가며 창밖 밤낮 → 늘어진 자세 + 게이지 뚝(빨강) «1~2일 뒤 = 니즈 급락» → 탁자 위 상담 전화가 울려도 «됐어요» 손짓.
화면 글은 말 따라 쓰지 않고 말을 받치는 개념어(사장님 10-08 «심리학적으로 그래요 → 심리학적 요소처럼»).

  python bisa_need_drop.py [--조각만] [--소리만]
    → 빡이사DB\납품\18_니즈하락_1603.92~.mp4 (V1 그 자리, 사람 PIP 는 사장님 V2 그대로) · _효과음.xml · _미리보기.mp4
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

M.T0, M.T1 = 1603.919, 1617.232
M.DUR = M.T1 - M.T0
M.SEGS = [(1603.919, 1606.021, 2539.037, 2540.772), (1606.021, 1606.638, 2541.239, 2542.974), (1606.638, 1607.906, 2541.989, 2543.725),
          (1607.906, 1610.642, 2543.408, 2545.143), (1610.642, 1612.211, 2546.36, 2548.096), (1612.211, 1617.232, 2548.079, 2549.814)]
M.NAME = "18_니즈하락"
M.SFX_DIR = (config.WORK / "효과음18")
M.WORK = (config.WORK / "빡이사" / "ae18")
W, H = M.W, M.H
T0, T1 = M.T0, M.T1
WORK = M.WORK
SRC = (config.ORIG_ROOT / "빡이사DB" / "소재" / "18")
PRET = str(config.FONTS["pretendard_bold"])
INK, GREY, BLUE, RED, NAVY = (28, 36, 64), (110, 116, 124), (0, 100, 224), (214, 48, 40), (30, 42, 82)

# ── 시각(_tmp/w18/words.txt) ──
T_IN, T_OUT = 1603.92, 1616.80
T_APPLY = 1604.96                      # 신청을 → «상담 신청 완료»
T_FOCUS = 1606.62                      # 사람이 → 관찰자 시점으로 살짝 다가감
T_EAGER = 1608.18                      # 상담 신청을 넣었을
T_RISE = 1609.16                       # 넣었을 → 게이지 오름
T_NEED = 1610.74                       # 니즈가
T_HIGH = 1611.24                       # 굉장히 → «신청 직후 = 니즈 최고»
T_DAY = [1612.80, 1613.02]             # 하루 · 이틀
T_BORED = 1613.44                      # 지나도
T_DROP = 1614.14                       # 급격하게
T_LOW = 1614.66                        # 떨어지거든요 → «1~2일 뒤 = 니즈 급락»
T_RING = 1615.50                       # 이거 많이들 → 상담 전화가 울림
T_WAVE = 1615.96                       # 경험하고 → «됐어요» 손짓

BG_S, BG_DY = 1.25, -120               # 거실 1536×1024 → 1920 폭, 위 120 자름
CH_S, CH_FOOT, CH_X = 0.405, 852, 1135  # 캐릭터 배율 · 발 y · 가운데 x
PIP, CAPTION = (0, 580, 720, 1080), (480, 900, 1440, 1080)
BOX = {}


def font(n):
    return ImageFont.truetype(PRET, n)


def tl(t, f):
    return ImageDraw.Draw(Image.new("RGBA", (1, 1))).textlength(t, font=f)


def save(name, im, xy):
    im.save(WORK / f"{name}.png")
    BOX[name] = (int(round(xy[0])), int(round(xy[1])), im.width, im.height)


def bbox(im):
    a = np.asarray(im)[..., 3] > 40
    ys, xs = np.where(a)
    return xs.min(), ys.min(), xs.max(), ys.max()


def shadowed(w, h, r, fill=(255, 255, 255), m=20, alpha=60):
    im = Image.new("RGBA", (w + 2 * m, h + 2 * m), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((m, m + 8, m + w, m + h + 8), r, fill=(20, 30, 60, alpha))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    ImageDraw.Draw(im).rounded_rectangle((m, m, m + w, m + h), r, fill=fill + (255,), outline=NAVY + (255,), width=4)
    return im, m


def pill(t, size, fg, bg, padx=24, h=None):
    f = font(size)
    w = int(tl(t, f)) + 2 * padx
    h = h or int(size * 1.8)
    im, m = shadowed(w, h, h // 2, bg)
    ImageDraw.Draw(im).text((m + w / 2, m + h / 2), t, font=f, fill=fg, anchor="mm")
    return im, m


def pieces():
    WORK.mkdir(parents=True, exist_ok=True)
    BOX.clear()
    bg = Image.open(SRC / "bg_room.png").convert("RGBA")
    bg = bg.resize((int(bg.width * BG_S), int(bg.height * BG_S)), Image.LANCZOS)
    save("bg", bg.crop((0, -BG_DY, W, -BG_DY + H)), (0, 0))
    night = Image.new("RGBA", (W, H), (20, 30, 70, 120))          # 밤(시간이 흐름)
    save("night", night, (0, 0))
    # 캐릭터 4동작 — 발 y·가운데 x 를 맞춰 같은 자리
    for nm in ("apply", "eager", "bored", "ignore"):
        im = Image.open(SRC / f"char_{nm}.png").convert("RGBA")
        x0, y0, x1, y1 = bbox(im)
        im = im.crop((x0, y0, x1 + 1, y1 + 1))
        im = im.resize((int(im.width * CH_S), int(im.height * CH_S)), Image.LANCZOS)
        cx = CH_X + (40 if nm == "bored" else 0)
        save(f"c_{nm}", im, (cx - im.width / 2, CH_FOOT - im.height))
    # 탁자 위 전화(오른쪽 앞)
    im = Image.open(SRC / "phone_ring.png").convert("RGBA")
    x0, y0, x1, y1 = bbox(im)
    im = im.crop((x0, y0, x1 + 1, y1 + 1))
    im = im.resize((int(im.width * 0.36), int(im.height * 0.36)), Image.LANCZOS)
    save("phone", im, (1560, 880 - im.height))
    # 전화 울림 물결(양옆 호 두 개씩)
    rw = Image.new("RGBA", (360, 220), (0, 0, 0, 0))
    d = ImageDraw.Draw(rw)
    for r in (40, 70):
        d.arc((180 - 80 - r, 110 - r, 180 - 80 + r, 110 + r), 135, 225, fill=BLUE + (255,), width=8)
        d.arc((180 + 80 - r, 110 - r, 180 + 80 + r, 110 + r), -45, 45, fill=BLUE + (255,), width=8)
    px, py, pw, ph = BOX["phone"]
    save("ringw", rw, (px + pw * 0.42 - 180, py + ph * 0.22 - 110))
    im, m = pill("상담 전화", 26, (255, 255, 255), BLUE, padx=20, h=48)
    save("p_call", im, (px + pw / 2 - im.width / 2, py - 70 - m))
    # 휴대폰 위 «상담 신청 완료» 카드(머리 왼쪽 위)
    cx_, cy_ = BOX["c_apply"][0], BOX["c_apply"][1]
    f = font(30)
    w = int(tl("상담 신청 완료", f)) + 110
    im, m = shadowed(w, 76, 20)
    d = ImageDraw.Draw(im)
    d.ellipse((m + 18, m + 16, m + 62, m + 60), fill=BLUE + (255,))
    d.line(((m + 29, m + 39), (m + 37, m + 47), (m + 52, m + 29)), fill=(255, 255, 255, 255), width=6, joint="curve")
    d.text((m + 78, m + 38), "상담 신청 완료", font=f, fill=INK, anchor="lm")
    tail = [(m + w - 70, m + 74), (m + w - 40, m + 74), (m + w - 30, m + 104)]
    d.polygon(tail, fill=(255, 255, 255, 255))
    d.line(tail[1:] + [tail[0]][:0], fill=NAVY + (255,), width=4)
    d.line((tail[0], tail[2]), fill=NAVY + (255,), width=4)
    save("done", im, (cx_ - w + 150 - m, cy_ - 122 - m))            # 꼬리 끝이 머리 위 16px 에서 멈춤(10-08 «머리 위에 겹치지 않게»)
    # «됐어요» 말풍선(같은 자리)
    bw_ = int(tl("지금은 괜찮아요…", f)) + 56
    im, m = shadowed(bw_, 76, 38)
    d = ImageDraw.Draw(im)
    d.text((m + bw_ / 2, m + 38), "지금은 괜찮아요…", font=f, fill=INK, anchor="mm")
    tail = [(m + bw_ - 92, m + 72), (m + bw_ - 62, m + 72), (m + bw_ - 52, m + 102)]
    d.polygon(tail, fill=(255, 255, 255, 255))
    d.line((tail[1], tail[2]), fill=NAVY + (255,), width=4)
    d.line((tail[0], tail[2]), fill=NAVY + (255,), width=4)
    bx, by = BOX["c_ignore"][0], BOX["c_ignore"][1]
    save("bub_no", im, (bx + 122 - (bw_ - 52) - m, by - 118 - m))     # 꼬리 끝이 머리 위 16px
    # 들뜸 반짝 선(머리 둘레)
    sp = Image.new("RGBA", (420, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(sp)
    for ang in (-165, -128, -90, -52, -15):                     # 머리(반지름 약 95) 바깥으로만
        c, s_ = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        p0, p1 = (210 + 132 * c, 230 + 132 * s_), (210 + 178 * c, 230 + 178 * s_)
        d.line((p0, p1), fill=(255, 168, 60, 255), width=10)
        for q in (p0, p1):
            d.ellipse((q[0] - 5, q[1] - 5, q[0] + 5, q[1] + 5), fill=(255, 168, 60, 255))
    ex, ey, ew, eh = BOX["c_eager"]
    save("joy", sp, (ex + 100 - 210, ey + 75 - 230))                 # 머리 가운데(그림 안 100, 75) 기준
    # 게이지(왼쪽 위 — 사람 PIP·자막 자리 피함)
    gx, gy, gw, gh = 120, 130, 110, 340
    im, m = shadowed(gw, gh + 80, 30)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((m + 22, m + 22, m + gw - 22, m + gh), 33, fill=(232, 236, 244, 255))
    d.text((m + gw / 2, m + gh + 42), "니즈", font=font(30), fill=INK, anchor="mm")
    save("gauge", im, (gx - m, gy - m))
    fw, fh = gw - 44 - 8, gh - 22 - 8
    for nm, col in (("fill_b", BLUE), ("fill_r", RED)):
        im = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
        ImageDraw.Draw(im).rounded_rectangle((0, 0, fw - 1, fh - 1), 28, fill=col + (255,))
        save(nm, im, (gx + 26, gy + 26))
    im, m = pill("상담 니즈", 24, INK, (255, 255, 255), padx=18, h=44)
    save("g_title", im, (gx + gw / 2 - im.width / 2, gy - 70 - m))
    # 개념 알약(게이지 오른쪽)
    for nm, t, bgc in (("p_high", "신청 직후 = 니즈 최고", BLUE), ("p_low", "1~2일 뒤 = 니즈 급락", RED)):
        im, m = pill(t, 34, (255, 255, 255), bgc, padx=26, h=64)
        save(nm, im, (gx + gw + 40 - m, gy + 40 - m))                 # 둘은 시각이 갈려 같은 자리
    # 달력(+1일 · +2일)
    for k, t in enumerate(("오늘", "+1일", "+2일")):
        im, m = shadowed(200, 190, 22)
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((m, m, m + 200, m + 54), 22, fill=RED + (255,))
        d.rectangle((m, m + 30, m + 200, m + 54), fill=RED + (255,))
        d.line((m, m + 54, m + 200, m + 54), fill=NAVY + (255,), width=4)
        d.rounded_rectangle((m, m, m + 200, m + 190), 22, outline=NAVY + (255,), width=4)
        for x in (m + 55, m + 145):
            d.ellipse((x - 9, m - 12, x + 9, m + 6), fill=NAVY + (255,))
        d.text((m + 100, m + 124), t, font=font(58 if k else 50), fill=INK, anchor="mm")
        save(f"cal{k}", im, (gx + gw + 70 - m, gy + 150 - m))
    check_layout()


def check_layout():
    bad = []
    for n, (x, y, w, h) in BOX.items():
        if n in ("bg", "night"):
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
         f"(function(){{ var comp=app.project.items.addComp('bisa18',{W},{H},1,{M.DUR:.3f},{M.FPS}); comp.motionBlur=true;"]
    a = L.append
    nv = [0]
    rig = "thisComp.layer('RIG').transform"

    def lay(name, anchor=None, extra=""):
        """무대 레이어: RIG(밀려 들어옴·빠짐 + 관찰자 쪽으로 살짝 다가감)를 식으로 따름."""
        nv[0] += 1
        v = f"L{nv[0]}"
        x, y, w, h = BOX[name]
        ax, ay = anchor if anchor else (w / 2, h / 2)
        a(f"var {v}=comp.layers.add(imp({js(str(WORK / f'{name}.png'))})); {v}.motionBlur=true; {v}.transform.anchorPoint.setValue([{ax},{ay}]); {v}.transform.position.setValue([{x + ax:.1f},{y + ay:.1f}]);")
        a(f"{v}.transform.position.expression={js(f'var r={rig}; var k=r.scale[0]/100; var c=[1180,560]; var p=value{extra}; [c[0]+k*(p[0]-c[0])+r.position[0], c[1]+k*(p[1]-c[1])]')};")
        a(f"{v}.transform.scale.expression={js(f'var k={rig}.scale[0]/100; [value[0]*k, value[1]*k]')};")
        return v

    def opa(v, k, hold_=False):
        a(f"keys({v}.transform.opacity,{k});")
        if hold_:
            a(f"hold({v}.transform.opacity);")

    def life(t_in, t_out=T_OUT + 0.4, fi=0.14, fo=0.2):
        return [[max(0, s(t_in) - 0.001), 0], [s(t_in) + fi, 100], [s(t_out), 100], [s(t_out) + fo, 0]]

    def pop(v, t, frm=70, dur=0.22):
        a(f"keys({v}.transform.scale,[[{s(t)},[{frm},{frm}]],[{s(t) + dur:.3f},[100,100]]]); eo({v}.transform.scale);")

    def squash(v, t, k=1.0):
        a(f"keys({v}.transform.scale,[[{s(t)},[{100 + 8 * k:.0f},{100 - 8 * k:.0f}]],[{s(t) + 0.12:.3f},[{100 - 4 * k:.0f},{100 + 5 * k:.0f}]],[{s(t) + 0.26:.3f},[100,100]]]);")

    # 녹화(무대 밖으로 처음·끝에 보임)
    a(f"var iv=imp({js(str(M.REC))});")
    for i, (ta, tb, rs, _) in enumerate(M.SEGS):
        a(f"var R{i}=comp.layers.add(iv); R{i}.startTime={s(ta) - rs:.4f}; R{i}.inPoint={s(ta):.4f}; R{i}.outPoint={s(tb):.4f};")
    a("var RIG=comp.layers.addNull(); RIG.name='RIG'; RIG.enabled=false; RIG.transform.anchorPoint.setValue([0,0]); RIG.transform.position.setValue([0,0]);")
    a(f"keys(RIG.transform.position,[[{s(T_IN)},[{W},0]],[{s(T_IN) + 0.45:.3f},[0,0]],[{s(T_OUT)},[0,0]],[{s(T_OUT) + 0.4:.3f},[{-W},0]]]); eo(RIG.transform.position);")
    a(f"keys(RIG.transform.scale,[[{s(T_FOCUS)},[100,100]],[{s(T_FOCUS) + 1.4:.3f},[106,106]],[{s(T_DAY[0]) - 0.1:.3f},[106,106]],[{s(T_DAY[0]) + 0.5:.3f},[100,100]]]); eo(RIG.transform.scale);")
    lay("bg")
    v = lay("night")
    k_ = [[0, 0]]
    for t in T_DAY:                                          # 하루·이틀: 창밖이 밤으로 한 번씩
        k_ += [[s(t), 0], [s(t) + 0.1, 100], [s(t) + 0.2, 0]]
    opa(v, k_)
    # 캐릭터(동작 바꿈 = 그 시각에 딱, 들썩임·눌림)
    poses = [("c_apply", T_IN, T_EAGER, 3, 4.0), ("c_eager", T_EAGER, T_BORED, 5, 7.5), ("c_bored", T_BORED, T_WAVE, 2, 2.4), ("c_ignore", T_WAVE, T1, 2, 3.0)]
    for nm, ta, tb, amp, spd in poses:
        x, y, w, h = BOX[nm]
        v = lay(nm, anchor=(w / 2, h), extra=f"+[0,{amp}*Math.sin(time*{spd})]")
        opa(v, [[max(0, s(ta) - 0.001), 0], [s(ta), 100], [s(tb), 0]] if tb < T1 else [[s(ta) - 0.001, 0], [s(ta), 100]], hold_=True)
        if ta > T_IN:
            squash(v, ta)
        if nm == "c_ignore":                                  # 손 휘젓기 느낌: 몸 전체가 아주 살짝 좌우로
            a(f"{v}.transform.rotation.expression={js('2.2*Math.sin(time*9)')};")
    # «상담 신청 완료»
    v = lay("done"); opa(v, life(T_APPLY, T_EAGER - 0.1, fo=0.25)); pop(v, T_APPLY)
    v = lay("joy", anchor=(210, 230)); opa(v, life(T_HIGH - 0.2, T_BORED - 0.15, fo=0.2))
    a(f"keys({v}.transform.scale,[[{s(T_HIGH) - 0.2:.3f},[88,88]],[{s(T_HIGH) + 0.1:.3f},[100,100]]]); eo({v}.transform.scale);")
    a(f"{v}.transform.rotation.expression={js('3*Math.sin(time*6)')};")
    # 게이지
    v = lay("g_title"); opa(v, life(T_APPLY + 0.3)); pop(v, T_APPLY + 0.3)
    v = lay("gauge"); opa(v, life(T_APPLY + 0.3)); pop(v, T_APPLY + 0.3, 85)
    for nm, k_ in (("fill_b", [[T_APPLY + 0.4, 0.0], [T_APPLY + 0.9, 0.3], [T_RISE, 0.3], [T_RISE + 0.9, 0.6], [T_NEED, 0.6], [T_NEED + 0.5, 0.98]]),
                   ("fill_r", [[T_DROP, 0.98], [T_DROP + 0.55, 0.12]])):
        x, y, w, h = BOX[nm]
        v = lay(nm, anchor=(w / 2, h))
        a(f"keys({v}.transform.scale,[{','.join(f'[{s(t):.3f},[100,{p * 100:.1f}]]' for t, p in k_)}]); eo({v}.transform.scale);")
        if nm == "fill_b":
            opa(v, [[s(T_APPLY + 0.4) - 0.001, 0], [s(T_APPLY + 0.4), 100], [s(T_DROP), 0]], hold_=True)
        else:
            opa(v, [[s(T_DROP) - 0.001, 0], [s(T_DROP), 100], [s(T_OUT + 0.4), 100], [s(T_OUT + 0.6), 0]])
    v = lay("p_high"); opa(v, life(T_HIGH, T_DROP, fo=0.2)); pop(v, T_HIGH)
    v = lay("p_low"); opa(v, life(T_LOW)); pop(v, T_LOW)
    # 달력
    cal = [("cal0", T_DAY[0] - 0.45, T_DAY[0]), ("cal1", T_DAY[0], T_DAY[1]), ("cal2", T_DAY[1], T_DROP - 0.1)]
    for nm, ta, tb in cal:
        x, y, w, h = BOX[nm]
        v = lay(nm, anchor=(w / 2, 20))
        last = nm == "cal2"
        if last:
            opa(v, [[s(ta) - 0.001, 0], [s(ta), 100], [s(tb), 100], [s(tb) + 0.25, 0]])
        else:
            opa(v, [[s(ta) - 0.001, 0], [s(ta), 100], [s(tb), 0]], hold_=True)
        a(f"keys({v}.transform.scale,[[{s(ta)},[100,{60 if nm != 'cal0' else 80}]],[{s(ta) + 0.14:.3f},[100,100]]]); eo({v}.transform.scale);")
    # 상담 전화: 울림(흔들림) + 물결 + «상담 전화» → «됐어요»
    v = lay("phone", anchor=(BOX["phone"][2] / 2, BOX["phone"][3]))
    opa(v, life(T_RING - 0.35, fi=0.2)); pop(v, T_RING - 0.35, 85)
    a(f"{v}.transform.rotation.expression={js(f'time<{s(T_RING):.3f}?0:5*Math.sin(time*48)*(Math.sin(time*6)>-0.2?1:0)')};")
    v = lay("ringw"); opa(v, [[s(T_RING), 0], [s(T_RING) + 0.08, 100], [s(T_OUT + 0.4), 100], [s(T_OUT + 0.6), 0]])
    a(f"{v}.transform.scale.expression={js(f'var k={rig}.scale[0]/100; var u=(time*2.2)%1; [ (90+u*25)*k, (90+u*25)*k ]')};")
    a(f"{v}.transform.opacity.expression={js('var u=(time*2.2)%1; value*(1-u*0.8)')};")
    v = lay("p_call"); opa(v, life(T_RING + 0.15)); pop(v, T_RING + 0.15)
    v = lay("bub_no"); opa(v, life(T_WAVE + 0.15)); pop(v, T_WAVE + 0.15)
    a(f"var rq=app.project.renderQueue.items.add(comp); var om=rq.outputModule(1); om.applyTemplate({js('고품질')}); om.file=new File({js(str(out_mov))});")
    a("log('ok bisa18'); })();")
    assert T_OUT + 0.4 < T1
    return "\n".join(L)


M.SND_FIX = {
    "in":    ("휙２.mp3", 0.6, 4, "peak"),
    "msg":   ("채팅 효과음.mp3", 0.6, 5, "onset"),                     # 상담 신청 완료(보냄)
    "focus": ("ML_Fast small sweep transition.wav", 0.6, 5, "onset"),  # 관찰자 시점으로 다가감
    "st1":   ("KN_pepSound1.wav", 0.4, 8, "onset"),
    "st2":   ("KN_pepSound2.wav", 0.4, 8, "onset"),
    "gauge": ("SEL_ゲージ回復1.mp3", 0.6, 12, "onset"),
    "ok":    ("맑은소리.mp3", 0.8, 7, "onset"),                         # 신청 직후 = 니즈 최고
    "page":  ("ML_Page turn chime.wav", 1.0, 5, "onset"),              # 달력 넘김
    "drop":  ("KN_lowDown.wav", 0.8, 5, "onset"),                      # 니즈 급락(새 파일)
    "ring":  ("SEL_携帯電話の着信音1.mp3", 1.6, 5, "onset"),            # 상담 전화(새 파일)
    "back":  ("휙1.mp3", 0.7, 8, "peak"),
}
M.EVENTS = [(T_IN + 0.25, "in"), (T_APPLY, "msg"), (T_FOCUS, "focus"), (T_EAGER, "st1"), (T_RISE, "gauge"), (T_HIGH, "ok"),
            (T_DAY[0], "page"), (T_BORED, "st2"), (T_DROP, "drop"), (T_RING, "ring"), (T_OUT + 0.2, "back")]

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
