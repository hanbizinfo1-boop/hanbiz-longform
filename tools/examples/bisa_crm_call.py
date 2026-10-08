# -*- coding: utf-8 -*-
r"""빡이사DB 본편 21 «DB 수집됐을 때 세월아 네월아 ~ 4차 콜까지는 전화를 하셔야 합니다» (시퀀스 2218.917~2235.80, 양 끝 컷 경계)
사장님 10-08 «직원 입장에서 2D 애니메이션 느낌 · 주인공이 회사에서 업무하는 느낌 · DB 관련 CRM 화면을 보고 있는 구도 ·
모니터 속 화면은 따로 왼쪽 상단에 띄워서».
사장님이 이 구간 사람(V2)을 전체 화면 50%로 두심 → 시작에 사람이 왼쪽 아래 30%(본편 PIP 자리)로 줄며 2D 사무실이 열리고, 끝에 다시 전체 화면.
  사무실(Codex 2D, 19·20 같은 인물 5동작 — 소재/21) + 왼쪽 위 «모니터 속 CRM» 확대 창(모니터에서 끌어낸 연결선):
  새 DB 줄 상태가 말에 맞춰 바뀜 — 방금 도착 → 미연락 +1일·+2일(빨강, 딴청) → ✕ 늦으면 놓침 → 다시 방금 도착(놀람) → 즉시 · 알림톡 발송 →
  1차 콜(헤드셋) → 부재 → 2차·3차·4차 칩(다시 누름) → «4차 콜까지» 막대 꽉. 화면 글은 개념어(말 따라 쓰지 않기).

  python bisa_crm_call.py [--조각만] [--소리만]
    → 빡이사DB\납품\21_4차콜_2218.92~.mp4 (V1 만 — 사람은 사장님 V2 PIP 가 위에 얹힘, 10-08) · _효과음.xml · _미리보기.mp4
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

M.T0, M.T1 = 2218.917, 2235.80
M.DUR = M.T1 - M.T0
M.SEGS = [(2218.917, 2220.218, 3594.307, 3596.827), (2220.218, 2221.836, 3595.792, 3598.311), (2221.836, 2224.122, 3597.761, 3600.28),
          (2224.122, 2225.39, 3600.18, 3602.699), (2225.39, 2228.676, 3601.665, 3604.184), (2228.676, 2229.577, 3605.485, 3608.004),
          (2229.577, 2232.363, 3606.503, 3609.022), (2232.363, 2235.8, 3609.439, 3611.958)]
M.NAME = "21_4차콜"
M.SFX_DIR = (config.WORK / "효과음21")
M.WORK = (config.WORK / "빡이사" / "ae21")
W, H, FPS = M.W, M.H, M.FPS
T0, T1 = M.T0, M.T1
WORK = M.WORK
SRC = (config.ORIG_ROOT / "빡이사DB" / "소재" / "21")
PRET = str(config.FONTS["pretendard_bold"])
NOTO = str(config.FONTS["noto_sans_kr"])
INK, GREY, LINE, BLUE, RED, GREEN = (28, 30, 33), (101, 103, 107), (222, 225, 230), (0, 100, 224), (220, 38, 38), (36, 150, 72)
YELLOW = (254, 229, 0)

# ── 시각(_tmp/w21/words.txt) ──
T_IN, T_OUT = 2218.93, 2235.36
T_POP = 2219.22                         # 수집됐을 때 → CRM 창 + 새 DB
T_LAZY = 2220.18                        # 세월아 네월아
T_D1, T_D2 = 2222.28, 2222.46           # 하루 · 이틀
T_NO = 2223.62                          # 안 돼요
T_ALERT = 2224.48                       # 수집됐을 때
T_NOW = 2225.44                         # 바로바로
T_TALK = 2226.12                        # 알림톡
T_CALL = 2228.80                        # 콜하시고
T_MISS = 2229.84                        # 전화 안 받는다고
T_RECALL = 2230.68                      # 한 번 전화하고 마는 게
T_C = [2232.34, 2232.84, 2233.16]       # 두 번 · 세 번 · 네 번
T_FULL = 2233.72                        # 4차 콜까지는

PERSON_FULL, PERSON_PIP = ((960, 540), 50), ((0.0927083 * W, 0.837037 * H), 30)   # 사장님 V2: 50% 가운데 / 본편 PIP
PIP, CAPTION = (0, 580, 720, 1080), (480, 900, 1440, 1080)
CH_X, CH_FOOT, CH_H = 1330, 900, 720    # 인물+책상 그림 가운데 x · 바닥 y · 높이(화면)
BOX = {}
MON = {}                                # 모니터 화면 칸(화면 좌표) — 그림에서 잼


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


def shadowed(w, h, r, fill=(255, 255, 255), m=22, alpha=70, outline=None, ow=3):
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


def pill_img(t, size, fg, bg, padx=16, h=None, wght=700):
    f = font(size, wght)
    w = int(tl(t, f)) + 2 * padx
    h = h or int(size * 1.9)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), h // 2, fill=bg + (255,))
    ImageDraw.Draw(im).text((w / 2, h / 2), t, font=f, fill=fg, anchor="mm")
    return im


def pill(t, size, fg, bg, padx=24, h=None):
    f = font(size)
    w = int(tl(t, f)) + 2 * padx
    h = h or int(size * 1.8)
    im, m = shadowed(w, h, h // 2, bg, m=16, alpha=70)
    ImageDraw.Draw(im).text((m + w / 2, m + h / 2), t, font=f, fill=fg, anchor="mm")
    return im, m


def find_monitor(im):
    """연한 파랑 모니터 화면 칸 — 그림 안 좌표."""
    a = np.asarray(im).astype(int)
    r, g, b, al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    m = (al > 200) & (b > 200) & (b - r > 25) & (g > 170) & (r > 150)
    ys, xs = np.where(m)
    if len(xs) < 50:
        return None
    # 가장 큰 덩어리 대신 사분위로 바깥 점 걸러 냄
    x0, x1 = np.percentile(xs, [3, 97])
    y0, y1 = np.percentile(ys, [3, 97])
    return int(x0), int(y0), int(x1), int(y1)


def pieces():
    WORK.mkdir(parents=True, exist_ok=True)
    BOX.clear()
    bg = Image.open(SRC / "office_bg.png").convert("RGBA")
    s = max(W / bg.width, H / bg.height)
    bg = bg.resize((int(bg.width * s + 1), int(bg.height * s + 1)), Image.LANCZOS)
    save("bg", bg.crop((0, bg.height - H, W, bg.height)), (0, 0))
    # 인물 5동작 — 같은 크기·같은 자리(책상 바닥 기준)
    for nm in ("work", "lazy", "alert", "call", "recall"):
        im = Image.open(SRC / f"w_{nm}.png").convert("RGBA")
        k = CH_H / im.height
        im = im.resize((int(im.width * k), CH_H), Image.LANCZOS)
        save(f"w_{nm}", im, (CH_X - im.width / 2, CH_FOOT - CH_H))
        if nm == "work":                                       # 모니터 뒷판 자리(그림 안 비율, 10-08 다시 그린 5동작 실측) — 색으로 찾으면 셔츠를 잡음
            x, y, w_, h_ = BOX["w_work"]
            MON["box"] = (x + 0.48 * w_, y + 0.19 * h_, x + 0.87 * w_, y + 0.42 * h_)
    mx0, my0, mx1, my1 = MON.get("box", (1500, 420, 1700, 560))
    # 모니터 테두리 반짝(«화면을 띄운다» 시작점)
    rg = Image.new("RGBA", (int(mx1 - mx0) + 24, int(my1 - my0) + 24), (0, 0, 0, 0))
    ImageDraw.Draw(rg).rounded_rectangle((4, 4, rg.width - 5, rg.height - 5), 10, outline=BLUE + (255,), width=6)
    save("mon_ring", rg, (mx0 - 12, my0 - 12))
    # CRM 창(왼쪽 위)
    cx0, cy0, cw, ch = 50, 46, 760, 470
    im, m = shadowed(cw, ch, 18, outline=(200, 210, 226))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((m, m, m + cw, m + 54), 18, fill=(30, 42, 82, 255))
    d.rectangle((m, m + 30, m + cw, m + 54), fill=(30, 42, 82, 255))
    for k, c in enumerate(((255, 96, 92), (255, 190, 46), (40, 200, 64))):
        d.ellipse((m + 20 + k * 26, m + 19, m + 36 + k * 26, m + 35), fill=c + (255,))
    d.text((m + 110, m + 27), "고객 DB 관리", font=font(24), fill=(255, 255, 255), anchor="lm")
    d.text((m + cw - 24, m + 27), "CRM", font=font(20, 600), fill=(170, 186, 220), anchor="rm")
    hy = m + 96
    for x, t in ((m + 30, "이름"), (m + 170, "연락처"), (m + 380, "유입"), (m + 530, "상태")):
        d.text((x, hy), t, font=font(20, 600), fill=GREY, anchor="lm")
    d.line((m + 20, hy + 24, m + cw - 20, hy + 24), fill=LINE + (255,), width=2)
    for k, (nm, ph) in enumerate((("이○○", "010-0000-0000"), ("박○○", "010-0000-0000"))):   # 지난 줄(흐림, 이미 처리)
        y = hy + 120 + k * 46
        d.text((m + 30, y), nm, font=font(21, 500), fill=(150, 154, 160), anchor="lm")
        d.text((m + 170, y), ph, font=font(21, 500), fill=(150, 154, 160), anchor="lm")
        d.text((m + 380, y), "메타 광고", font=font(21, 500), fill=(150, 154, 160), anchor="lm")
        d.text((m + 530, y), "상담 완료", font=font(21, 500), fill=(150, 154, 160), anchor="lm")
    d.text((m + 30, m + ch - 120), "연락 기록", font=font(22), fill=INK, anchor="lm")
    d.rounded_rectangle((m + 30, m + ch - 34, m + cw - 30, m + ch - 18), 8, fill=(232, 236, 242, 255))
    save("crm", im, (cx0 - m, cy0 - m))
    # 새 DB 줄(강조 바탕)
    row_y = cy0 + 96 + 66
    rw = Image.new("RGBA", (cw - 30, 58), (0, 0, 0, 0))
    d = ImageDraw.Draw(rw)
    d.rounded_rectangle((0, 0, cw - 31, 57), 12, fill=(236, 243, 255, 255), outline=(170, 196, 240, 255), width=2)
    d.text((16, 29), "김○○", font=font(22, 700), fill=INK, anchor="lm")
    d.text((156, 29), "010-0000-0000", font=font(22, 600), fill=INK, anchor="lm")
    d.text((366, 29), "메타 광고", font=font(22, 600), fill=INK, anchor="lm")
    save("row", rw, (cx0 + 15, row_y - 29))
    # 상태 칩(바뀜)
    chips = [("st_new", "방금 도착", (255, 255, 255), BLUE), ("st_d1", "미연락 +1일", (255, 255, 255), RED), ("st_d2", "미연락 +2일", (255, 255, 255), RED),
             ("st_new2", "방금 도착", (255, 255, 255), BLUE), ("st_talk", "알림톡 발송", INK, YELLOW), ("st_call", "1차 콜 중", (255, 255, 255), GREEN),
             ("st_miss", "부재중", (255, 255, 255), (130, 136, 146)), ("st_retry", "다시 콜", (255, 255, 255), GREEN)]
    for nm, t, fg, bgc in chips:
        im = pill_img(t, 20, fg, bgc, padx=14, h=36)
        save(nm, im, (cx0 + 15 + 530 - 16, row_y - 18))
    # 새 DB 알림 점
    dot = Image.new("RGBA", (26, 26), (0, 0, 0, 0))
    ImageDraw.Draw(dot).ellipse((2, 2, 23, 23), fill=RED + (255,), outline=(255, 255, 255, 255), width=3)
    save("newdot", dot, (cx0 + 15 - 10, row_y - 38))
    # 연락 기록 칩 1~4차(꺼짐/켜짐) + 막대
    ly = cy0 + ch - 120
    for k in range(4):
        x = cx0 + 160 + k * 150
        for st, (fg, bgc) in (("off", (GREY, (236, 239, 244))), ("on", ((255, 255, 255), GREEN)), ("miss", ((255, 255, 255), (150, 156, 166)))):
            t = f"{k + 1}차 콜" + (" 부재" if st == "miss" else "")
            im = pill_img(t, 19, fg, bgc, padx=12, h=34)
            save(f"c{k}_{st}", im, (x, ly - 17))
    bw = cw - 60
    bar = Image.new("RGBA", (bw, 16), (0, 0, 0, 0))
    ImageDraw.Draw(bar).rounded_rectangle((0, 0, bw - 1, 15), 8, fill=BLUE + (255,))
    save("bar", bar, (cx0 + 30, cy0 + ch - 34))
    # 연결선: CRM 창 오른쪽 아래 → 모니터
    x0, y0 = cx0 + cw, cy0 + ch * 0.55
    x1, y1 = mx0, (my0 + my1) / 2
    ln = Image.new("RGBA", (int(abs(x1 - x0)) + 20, int(abs(y1 - y0)) + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(ln)
    ax, ay = 10, 10 if y1 >= y0 else ln.height - 10
    bx, by = ln.width - 10, ln.height - 10 if y1 >= y0 else 10
    n = 18
    for i in range(n):                                           # 점선
        if i % 2 == 0:
            u0, u1 = i / n, (i + 1) / n
            d.line((ax + (bx - ax) * u0, ay + (by - ay) * u0, ax + (bx - ax) * u1, ay + (by - ay) * u1), fill=BLUE + (220,), width=5)
    d.ellipse((bx - 8, by - 8, bx + 8, by + 8), fill=BLUE + (255,))
    save("link", ln, (min(x0, x1) - 10, min(y0, y1) - 10))
    # 개념 알약(오른쪽 위, 인물 머리 위 공간)
    for nm, t, bgc in (("p_late", "늦으면 놓친다", RED), ("p_now", "수집 즉시 연락", BLUE), ("p_4", "4차 콜까지", BLUE)):
        im, m = pill(t, 40, (255, 255, 255), bgc, padx=30, h=74)
        save(nm, im, (1340 - im.width / 2 + m - m, 70 - m))
    xb = Image.new("RGBA", (96, 96), (0, 0, 0, 0))
    d = ImageDraw.Draw(xb)
    d.ellipse((4, 4, 92, 92), fill=RED + (255,), outline=(255, 255, 255, 255), width=6)
    d.line((31, 31, 65, 65), fill=(255, 255, 255, 255), width=10)
    d.line((65, 31, 31, 65), fill=(255, 255, 255, 255), width=10)
    save("xbadge", xb, (cx0 + cw - 70, row_y - 70))
    # 말풍선 아이콘(알림톡 — 노란 말풍선, 로고·글자 없음)
    tb = Image.new("RGBA", (120, 104), (0, 0, 0, 0))
    d = ImageDraw.Draw(tb)
    d.ellipse((4, 4, 116, 80), fill=YELLOW + (255,), outline=(60, 50, 0, 255), width=3)
    d.polygon([(30, 70), (24, 100), (54, 76)], fill=YELLOW + (255,))
    for k in range(3):
        d.ellipse((34 + k * 22, 36, 46 + k * 22, 48), fill=(60, 50, 0, 255))
    save("talk", tb, (mx0 + (mx1 - mx0) * 0.45, my0 - tb.height - 14))   # 모니터 윗변 위 — 머리(그림 x 0.45 까지)와 안 겹치게(10-08)
    # 전화 울림 물결(머리 옆)
    rw_ = Image.new("RGBA", (200, 140), (0, 0, 0, 0))
    d = ImageDraw.Draw(rw_)
    for r in (34, 60):
        d.arc((100 - r, 70 - r, 100 + r, 70 + r), 130, 230, fill=GREEN + (255,), width=8)   # 왼쪽으로 퍼짐
    x, y, w, h = BOX["w_call"]
    save("ring", rw_, (x + w * 0.10 - 20, y + h * 0.10 - 70))         # 머리 왼쪽(헤드셋 쪽) — 모니터와 안 겹치게(10-08)
    check_layout()


def check_layout():
    bad = []
    for n, (x, y, w, h) in BOX.items():
        if n in ("bg",) or n.startswith("w_"):
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
         f"(function(){{ var comp=app.project.items.addComp('bisa21',{W},{H},1,{M.DUR:.3f},{FPS}); comp.motionBlur=true;"]
    a = L.append
    nv = [0]
    slide = "thisComp.layer('RIG').transform.position[0]"

    def lay(name, anchor=None, extra=""):
        nv[0] += 1
        v = f"L{nv[0]}"
        x, y, w, h = BOX[name]
        ax, ay = anchor if anchor else (w / 2, h / 2)
        a(f"var {v}=comp.layers.add(imp({js(str(WORK / f'{name}.png'))})); {v}.motionBlur=true; {v}.transform.anchorPoint.setValue([{ax},{ay}]); {v}.transform.position.setValue([{x + ax:.1f},{y + ay:.1f}]);")
        a(f"{v}.transform.position.expression=\"value+[{slide},0]{extra}\";")
        return v

    def opa(v, k, hold_=False):
        a(f"keys({v}.transform.opacity,{k});")
        if hold_:
            a(f"hold({v}.transform.opacity);")

    def life(t_in, t_out=T1, fi=0.12, fo=0.2):
        return [[max(0, s(t_in) - 0.001), 0], [s(t_in) + fi, 100], [s(t_out), 100], [s(t_out) + fo, 0]]

    def swap(t_in, t_out):
        """그 시각에 딱 바뀜(앞뒤 0.001)."""
        k = [[max(0, s(t_in) - 0.001), 0], [s(t_in), 100]]
        if t_out < T1:
            k += [[s(t_out) - 0.001, 100], [s(t_out), 0]]
        return k

    def pop(v, t, frm=72, dur=0.22):
        a(f"keys({v}.transform.scale,[[{s(t)},[{frm},{frm}]],[{s(t) + dur:.3f},[100,100]]]); eo({v}.transform.scale);")

    # 무대(뒤) — 사람보다 아래
    a("var RIG=comp.layers.addNull(); RIG.name='RIG'; RIG.enabled=false; RIG.transform.position.setValue([0,0]);")
    # 무대는 밀어 넣지 않는다 — 전체 화면 사람이 줄어들며 뒤의 사무실이 드러남(밀면 왼쪽에 까만 틈, 10-08 확인)
    WITH_PERSON = False                                  # 10-08 사장님 «V2 로 위에서 덮어씌우면 되는데 왜 굳이 마스크까지 렌더» — 사람은 굽지 않음(V1 만)
    if WITH_PERSON:
        a(f"var cv=imp({js(str(M.CAM))});")
    # 사람(사장님 컷 조각): 전체 50% → PIP 30% → 끝에 전체
    cams = []
    for i, (ta, tb, _, cs) in enumerate(M.SEGS if WITH_PERSON else []):
        v = f"C{i}"
        a(f"var {v}=comp.layers.add(cv); {v}.startTime={s(ta) - cs:.4f}; {v}.inPoint={s(ta):.4f}; {v}.outPoint={s(tb):.4f}; {v}.audioEnabled=false;")
        (fx, fy), fs = PERSON_FULL
        (px, py), ps = PERSON_PIP
        a(f"keys({v}.transform.position,[[{s(T_IN)},[{fx},{fy}]],[{s(T_IN) + 0.45:.3f},[{px:.1f},{py:.1f}]],[{s(T_OUT)},[{px:.1f},{py:.1f}]],[{s(T_OUT) + 0.4:.3f},[{fx},{fy}]]]); ez({v}.transform.position);")
        a(f"keys({v}.transform.scale,[[{s(T_IN)},[{fs},{fs}]],[{s(T_IN) + 0.45:.3f},[{ps},{ps}]],[{s(T_OUT)},[{ps},{ps}]],[{s(T_OUT) + 0.4:.3f},[{fs},{fs}]]]); ez({v}.transform.scale);")
        # 사장님 PIP 타원 마스크(10-08 prproj 실측: 소스 4K 기준 가운데 1842,1172 · 반지름 529×512 · 페더 0) — 줄어들며 닫히고 끝에 다시 열림
        k_ = 0.5523
        cxm, cym, rx, ry = 1842, 1172, 529, 512
        a(f"var mk{v}={v}.property('ADBE Mask Parade').addProperty('ADBE Mask Atom'); var sh{v}=new Shape();"
          f" sh{v}.vertices=[[{cxm},{cym - ry}],[{cxm + rx},{cym}],[{cxm},{cym + ry}],[{cxm - rx},{cym}]];"
          f" sh{v}.inTangents=[[{-rx * k_:.1f},0],[0,{-ry * k_:.1f}],[{rx * k_:.1f},0],[0,{ry * k_:.1f}]];"
          f" sh{v}.outTangents=[[{rx * k_:.1f},0],[0,{ry * k_:.1f}],[{-rx * k_:.1f},0],[0,{-ry * k_:.1f}]]; sh{v}.closed=true;"
          f" mk{v}.property('ADBE Mask Shape').setValue(sh{v});")
        a(f"keys(mk{v}.property('ADBE Mask Offset'),[[{s(T_IN)},2600],[{s(T_IN) + 0.45:.3f},0],[{s(T_OUT)},0],[{s(T_OUT) + 0.4:.3f},2600]]); ez(mk{v}.property('ADBE Mask Offset'));")
        cams.append(v)
    lay("bg")
    # 인물 5동작(들썩임, 바뀔 때 눌림)
    poses = [("w_work", T_IN, T_LAZY), ("w_lazy", T_LAZY, T_ALERT), ("w_alert", T_ALERT, T_CALL), ("w_call", T_CALL, T_RECALL), ("w_recall", T_RECALL, T1)]
    for nm, ta, tb in poses:
        x, y, w, h = BOX[nm]
        v = lay(nm, anchor=(w / 2, h), extra=f"+[0,3*Math.sin(time*{3.0 if nm != 'w_lazy' else 1.6})]")
        opa(v, swap(ta, tb), hold_=True)
        if ta > T_IN:
            a(f"keys({v}.transform.scale,[[{s(ta)},[104,96]],[{s(ta) + 0.12:.3f},[98,103]],[{s(ta) + 0.26:.3f},[100,100]]]);")
        if nm == "w_recall":
            for t in T_C:                                          # 다시 누를 때마다 살짝 눌림
                a(f"keys({v}.transform.scale,[[{s(t)},[100,100]],[{s(t) + 0.08:.3f},[103,97]],[{s(t) + 0.2:.3f},[100,100]]]);")
    # 모니터 → CRM 창
    # 모니터 반짝·점선 연결선 없음 — 사장님 10-08 «굳이 이어 주지 않아도 사람들 다 저 안의 내용인 거 알아»
    mx = (MON.get("box", (1500, 420, 1700, 560))[0] + MON.get("box", (1500, 420, 1700, 560))[2]) / 2
    my = (MON.get("box", (1500, 420, 1700, 560))[1] + MON.get("box", (1500, 420, 1700, 560))[3]) / 2
    cx, cy, cw_, ch_ = BOX["crm"]
    v = lay("crm"); opa(v, life(T_POP + 0.25, T_OUT, fi=0.1))
    a(f"keys({v}.transform.position,[[{s(T_POP) + 0.25:.3f},[{mx:.1f},{my:.1f}]],[{s(T_POP) + 0.7:.3f},[{cx + cw_ / 2:.1f},{cy + ch_ / 2:.1f}]]]); eo({v}.transform.position);")
    a(f"keys({v}.transform.scale,[[{s(T_POP) + 0.25:.3f},[18,18]],[{s(T_POP) + 0.7:.3f},[100,100]]]); eo({v}.transform.scale);")
    crm = v
    td = T_POP + 0.75
    v = lay("row"); opa(v, life(td, T_OUT, fi=0.15)); pop(v, td, 90, 0.2)
    v = lay("newdot"); opa(v, [[s(td) - 0.001, 0], [s(td), 100], [s(T_LAZY), 100], [s(T_LAZY) + 0.2, 0], [s(T_ALERT) - 0.001, 0], [s(T_ALERT), 100], [s(T_TALK), 100], [s(T_TALK) + 0.2, 0]])
    a(f"{v}.transform.scale.expression=\"var u=(time*2.4)%1; [100+18*Math.sin(u*Math.PI),100+18*Math.sin(u*Math.PI)]\";")
    states = [("st_new", td, T_LAZY + 0.6), ("st_d1", T_D1, T_D2), ("st_d2", T_D2, T_ALERT), ("st_new2", T_ALERT, T_TALK),
              ("st_talk", T_TALK, T_CALL), ("st_call", T_CALL, T_MISS), ("st_miss", T_MISS, T_C[0]), ("st_retry", T_C[0], T1)]
    for nm, ta, tb in states:
        v = lay(nm); opa(v, swap(ta, tb), hold_=True); pop(v, ta, 80, 0.18)
    v = lay("xbadge"); opa(v, life(T_NO, T_ALERT - 0.05, fi=0.06, fo=0.15)); pop(v, T_NO, 40)
    # 연락 기록 칩
    for k in range(4):
        v = lay(f"c{k}_off"); opa(v, life(T_POP + 0.8, T_OUT, fi=0.15))
    v = lay("c0_on"); opa(v, swap(T_CALL, T_MISS), hold_=True); pop(v, T_CALL, 80, 0.18)
    v = lay("c0_miss"); opa(v, swap(T_MISS, T1), hold_=True); pop(v, T_MISS, 80, 0.18)
    for k, t in enumerate(T_C):
        v = lay(f"c{k + 1}_on"); opa(v, swap(t, T1), hold_=True); pop(v, t, 70, 0.2)
    x, y, w, h = BOX["bar"]
    v = lay("bar", anchor=(0, h / 2))
    steps = [(T_CALL, 0.25), (T_C[0], 0.5), (T_C[1], 0.75), (T_C[2], 1.0)]
    k_ = [[s(T_CALL) - 0.01, [0, 100]]]
    for t, p in steps:
        k_ += [[s(t), [k_[-1][1][0], 100]], [s(t) + 0.25, [p * 100, 100]]]
    a(f"keys({v}.transform.scale,{k_}); eo({v}.transform.scale);")
    opa(v, life(T_CALL, T_OUT, fi=0.05))
    # 알림톡 말풍선 · 전화 물결
    v = lay("talk"); opa(v, life(T_TALK, T_CALL, fi=0.1, fo=0.2)); pop(v, T_TALK, 50, 0.26)
    a(f"keys({v}.transform.position,[[{s(T_TALK)},[{BOX['talk'][0] + 60},{BOX['talk'][1] + 52 + 40}]],[{s(T_TALK) + 0.5:.3f},[{BOX['talk'][0] + 60},{BOX['talk'][1] + 52}]]]); eo({v}.transform.position);")
    v = lay("ring"); opa(v, [[s(T_CALL) - 0.001, 0], [s(T_CALL) + 0.05, 100], [s(T_MISS), 100], [s(T_MISS) + 0.1, 0], [s(T_C[0]) - 0.001, 0], [s(T_C[0]) + 0.05, 100], [s(T_OUT), 100], [s(T_OUT) + 0.2, 0]])
    a(f"{v}.transform.opacity.expression=\"var u=(time*2.5)%1; value*(0.35+0.65*(1-u))\";")
    # 개념 알약(머리 위)
    v = lay("p_late"); opa(v, life(T_NO + 0.1, T_ALERT - 0.05, fi=0.1, fo=0.15)); pop(v, T_NO + 0.1)
    v = lay("p_now"); opa(v, life(T_NOW, T_FULL - 0.05, fi=0.1, fo=0.15)); pop(v, T_NOW)
    v = lay("p_4"); opa(v, life(T_FULL, T_OUT, fi=0.1)); pop(v, T_FULL, 60, 0.26)
    # 사람은 맨 위(PIP)
    for v in cams:
        a(f"{v}.moveToBeginning();")
    a(f"var rq=app.project.renderQueue.items.add(comp); var om=rq.outputModule(1); om.applyTemplate({js('고품질')}); om.file=new File({js(str(out_mov))});")
    a("log('ok bisa21'); })();")
    assert T_OUT + 0.4 < T1 + 0.01
    return "\n".join(L)


SND_FIX = {
    "in":    ("휙２.mp3", 0.6, 4, "peak"),
    "new":   ("ML_Bell notification.wav", 0.8, 5, "onset"),          # 새 DB 도착(알림)
    "st1":   ("KN_pepSound1.wav", 0.4, 8, "onset"),
    "st2":   ("KN_pepSound2.wav", 0.4, 8, "onset"),
    "no":    ("KN_error_003.wav", 0.5, 5, "onset"),
    "talk":  ("채팅 효과음.mp3", 0.6, 5, "onset"),                     # 알림톡 발송
    "ring":  ("SEL_携帯電話の着信音1.mp3", 1.2, 5, "onset"),           # 콜
    "miss":  ("KN_lowDown.wav", 0.8, 5, "onset"),                      # 부재
    "click1": ("마우스 클릭.mp3", 0.25, 5, "onset"),                   # 다시 누름
    "click2": ("15. 마우스클릭.mp3", 0.25, 5, "onset"),
    "full":  ("SEL_レベルアップ.mp3", 0.9, 5, "onset"),                # 4차 콜까지
    "back":  ("휙1.mp3", 0.7, 8, "peak"),
}
EVENTS = [(T_IN + 0.25, "in"), (T_POP + 0.75, "new"), (T_LAZY, "st1"), (T_D1, "st2"), (T_NO, "no"), (T_ALERT, "new"), (T_NOW, "st1"),
          (T_TALK, "talk"), (T_CALL, "ring"), (T_MISS, "miss"), (T_RECALL, "st2"), (T_C[0], "click1"), (T_C[1], "click2"), (T_C[2], "click1"),
          (T_FULL, "full"), (T_OUT + 0.2, "back")]
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
    lec_xml.V_TRACK, lec_xml.A_TRACK = 1, 2                 # 사람 포함 → V3
    print(lec_xml.write(M.OUT / f"{M.NAME}_효과음.xml", f"빡이사DB_{M.NAME}", scene, M.DUR, T0,
                        [(t, f) for t, f, _ in placed], 59.94, tag="bs21"))
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
