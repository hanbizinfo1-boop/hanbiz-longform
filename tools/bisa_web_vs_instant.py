# -*- coding: utf-8 -*-
r"""[레거시 — 10-13 부터 AE 안 씀. 새 장면은 html_motion(references/ae-replacement.md)]
빡이사DB 본편 06 «웹사이트는 아무래도 문의를 넣기 전에 ~ 허수 DB가 어느 정도는 섞여 있다라고 이해를 하면 되는데»
(시퀀스 440.29~471.90) — 광고 관리자 «단일 전환 위치» 드롭다운의 웹사이트·인스턴트 양식 줄을 짚고, 오른쪽 비교 판에
«가는 길(단계)»과 «DB 수집·계약 전환·허수» 게이지가 말에 맞춰 쌓이는 연출.

  python bisa_web_vs_instant.py [--조각만] [--소리만]
    → 빡이사DB\납품\06_웹사이트vs인스턴트_440.29~.mp4 (녹화본 화면 포함 — V1 그 자리에 바꿔 끼움, 사람 PIP 는 사장님 V2 그대로)
       · 06_…_효과음.xml(V1 장면 + A2~ 효과음) · 06_…_미리보기.mp4(장면 + 사람 PIP + 목소리 + 효과음)
앞뒤 맥락(기록.md 06)
  앞 420.6~437.49 단일 전환 위치 → 인스턴트 양식으로, «웹사이트 있으면 웹사이트, 없으면 인스턴트» · 437.49 «두 가지의 차이점을 간단하게만»
  뒤 471.9~ «스스로 DB 안 뽑아 봤으면 랜딩 말고 무조건 인스턴트로 먼저» (07 은 클로드 디자인 B 경로로 예약)
  → 화면에 떠 있는 드롭다운의 두 줄을 그대로 짚고(뒤에서 «인스턴트로 하세요»로 이어짐), 비교는 오른쪽 판 한 장에.
     웹사이트는 단계가 길고(4칸) 인스턴트는 짧다(3칸) — 길이 차이가 곧 «수집 쉬움/어려움»이 보이게.
흐름(시퀀스 초, faster-whisper 단어 시각)
  440.29 확대(2.1배, 0.5초) · 440.85 웹사이트 줄 파란 테두리 + 오른쪽 판 «웹사이트»
  443.15 «클릭» 웹사이트 클릭 → 445.59 «살펴보고» 콘텐츠 살펴보기 → 446.21 «인지» 인지 → 447.15 «문의를» 문의
  448.41 «DB» DB 수집 줄 → 450.55 «어려울» 게이지 2칸 + «조금 더 어려움»
  453.00 «계약» 계약 전환 줄 → 455.45 «조금 더» 게이지 4칸 → 457.17 «잘» «잘 됨»
  458.73 «인스턴트» 테두리가 인스턴트 양식 줄로, 웹사이트 칸 흐려짐 → 459.25 판 «인스턴트 양식»
  461.57 «누르면» 딱 누르면 폼 → 463.47 «빠르게» 빠르게 입력 → 464.53 «넘어갈» 넘어감
  465.57 «DB» DB 수집 줄 → 466.31 게이지 4칸 → 466.83 «쉽거든요» «쉬움»
  468.19 «허수» 허수 DB 줄(빨강 게이지 2칸) → 469.97 «섞여있다고» «어느 정도 섞임»
  471.30 빠지고 확대 풀림 → 471.90 다음 조각(100%)
영상미(후킹애펙-워크플로우 2-1장): 1 흰·검정·메타 파랑(+ 허수만 빨강) · 3 튕김 없음(eo) · 4 단어마다 한 칸 · 9 단계 = 왼→오 계단
겹침: 판 안 요소끼리 · 판 밖 · 드롭다운 줄 · 사람 PIP · 자막 · 화면 밖을 렌더 전에 검사한다.
"""

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[0]))   # tools/ (config.py)
import config  # noqa: E402
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(config.TOOLS))
import rf3_ae as AE  # noqa: E402
import rule_check  # noqa: E402
import lec_xml  # noqa: E402
import bisa_meta_sfx as SFX  # noqa: E402
from bisa_toc_cards import by_name  # noqa: E402

W, H, FPS = 1920, 1080, 59.94
T0, T1 = 440.29, 471.90
DUR = T1 - T0
REC = (config.ORIG_ROOT / "빡이사DB" / "소재" / "녹화본_30fps고정.mp4")
CAM = (config.RAW_ROOT / "싱크1시간.mp4")
# 사장님 컷(10-07 15:31 저장본): (시퀀스 시작, 끝, V1 녹화 원본 시작, V2·A1 사람 원본 시작)
SEGS = [(440.29, 444.01, 831.814, 833.783), (444.01, 446.262, 835.818, 837.787), (446.262, 448.415, 838.187, 840.156),
        (448.415, 453.019, 840.406, 842.375), (453.019, 456.222, 845.128, 847.096), (456.222, 458.692, 848.915, 850.867),
        (458.692, 464.497, 851.651, 853.603), (464.497, 465.715, 857.623, 859.575), (465.715, 467.517, 859.092, 861.044),
        (467.517, 468.218, 861.277, 863.229), (468.218, 471.9, 863.696, 865.648)]
WORK = (config.WORK / "빡이사" / "ae06")
OUT = config.OUT
NAME = "06_웹사이트vs인스턴트"
SFX_DIR = (config.WORK / "효과음06")
PRET = str(config.FONTS["pretendard_bold"])
META_BLUE, INK, GREY, RED = (0, 100, 224), (28, 43, 51), (101, 103, 107), (225, 50, 50)
PILL_BG, EMPTY = (240, 242, 245), (222, 226, 232)

# 시각
T_ZOOM, T_OUT = 440.29, 471.30
T_WCARD, T_SWITCH, T_ICARD = 440.85, 458.73, 459.25
W_STEPS = [("웹사이트 클릭", 443.15), ("콘텐츠 살펴보기", 445.59), ("인지", 446.21), ("문의", 447.15)]
I_STEPS = [("딱 누르면 폼", 461.57), ("빠르게 입력", 463.47), ("넘어감", 464.53)]
# (이름, 줄 등장, 게이지 채움, 칸 수, 색, 꼬리말, 꼬리말 시각)
W_ROWS = [("w_db", "DB 수집", 448.41, 450.55, 2, META_BLUE, "조금 더 어려움", 450.75),
          ("w_ct", "계약 전환", 453.00, 455.45, 4, META_BLUE, "잘 됨", 457.17)]
I_ROWS = [("i_db", "DB 수집", 465.57, 466.31, 4, META_BLUE, "쉬움", 466.83),
          ("i_fk", "허수 DB", 468.19, 468.40, 2, RED, "어느 정도 섞임", 469.97)]

# 확대: 녹화 점 p → P + S·(p − A). 드롭다운 왼쪽 끝·두 줄 사이 = (686, 729).
# 아래 끝이 녹화 작업 표시줄(y ≥ 1029) 위에 오게 P_y ≥ 1080 − S·(1025 − 729).
S, A, P = 2.1, (686, 729), (40, 460)


def sc(x, y):
    return P[0] + S * (x - A[0]), P[1] + S * (y - A[1])


ROWS = {"web": (684, 729), "inst": (729, 775)}            # 드롭다운 줄 띠(녹화 y, 실측)
ROW_TEXT_END = 829                                        # «인스턴트 양식» 글자 끝(녹화 x)
PANEL = (1100, 96, 1890, 836)                             # 오른쪽 판(화면)
SEC_Y = [PANEL[1], (PANEL[1] + PANEL[3]) // 2]            # 웹사이트 칸 · 인스턴트 칸 위쪽
PIP = (0, 580, 720, 1080)
CAPTION = (480, 900, 1440, 1080)
BOX = {}


def font(n, f=PRET):
    return ImageFont.truetype(f, n)


def save(name, im, xy):
    xy = (int(round(xy[0])), int(round(xy[1])))
    im.save(WORK / f"{name}.png")
    a = np.array(im)[..., 3] > 60
    ys, xs = np.where(a)
    BOX[name] = (int(xy[0] + xs.min()), int(xy[1] + ys.min()), int(xy[0] + xs.max()), int(xy[1] + ys.max()))
    BOX[name + "@"] = (int(xy[0]), int(xy[1]), im.width, im.height)


def shadowed(w, h, r, fill, pad=24, alpha=70):
    im = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((pad, pad + 6, pad + w, pad + h + 6), r, fill=(10, 30, 70, alpha))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    ImageDraw.Draw(im).rounded_rectangle((pad, pad, pad + w, pad + h), r, fill=fill)
    return im


def tlen(t, f):
    return ImageDraw.Draw(Image.new("RGBA", (1, 1))).textlength(t, font=f)


def overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def inside(a, b, m=0):
    return a[0] >= b[0] + m and a[1] >= b[1] + m and a[2] <= b[2] - m and a[3] <= b[3] - m


def check_layout():
    bad = []
    content = [n for n in BOX if not n.endswith("@") and n not in ("panel_w", "panel_i", "hl", "dim") and not n.endswith("_fill")]
    for i, a in enumerate(content):
        for b in content[i + 1:]:
            if overlap(BOX[a], BOX[b]):
                bad.append(f"{a} {BOX[a]} ↔ {b} {BOX[b]}")
    for n in content + [n for n in BOX if n.endswith("_fill")]:
        if not inside(BOX[n], PANEL, 20):
            bad.append(f"{n} {BOX[n]} 판 밖")
    for n in [n for n in BOX if not n.endswith("@")]:
        for z, zn in ((PIP, "사람 PIP"), (CAPTION, "자막")):
            if overlap(BOX[n], z):
                bad.append(f"{n} {BOX[n]} ↔ {zn}")
        x0, y0, x1, y1 = BOX[n]
        if x0 < 15 or y0 < 15 or x1 > W - 15 or y1 > H - 15:
            bad.append(f"{n} {BOX[n]} 화면 밖")
    # 줄 테두리는 두 줄 글자를 다 감싸고, 판 밖 왼쪽 드롭다운 위에 있어야 한다
    for k in ROWS:
        y0, y1 = sc(0, ROWS[k][0])[1], sc(0, ROWS[k][1])[1]
        if not (BOX["hl"][1] <= y0 + 6 and BOX["hl"][3] >= y1 - 6 and BOX["hl"][2] >= sc(ROW_TEXT_END, 0)[0] + 20):
            bad.append(f"줄 테두리 {BOX['hl']} 가 {k} 줄({y0:.0f}~{y1:.0f})을 못 감쌈")
    if bad:
        raise SystemExit("레이아웃 겹침:\n  " + "\n  ".join(bad))
    print("겹침 없음")


# ── 조각 ──────────────────────────────────────────────────────
def pieces():
    WORK.mkdir(parents=True, exist_ok=True)
    BOX.clear()
    x0, y0, x1, y1 = PANEL
    pad = 24
    # 카드 두 장 — 인스턴트 카드는 그 차례에만(빈 흰 판이 오래 떠 있지 않게)
    mid = SEC_Y[1]
    save("panel_w", shadowed(x1 - x0, mid - 10 - y0, 28, (255, 255, 255, 255), pad), (x0 - pad, y0 - pad))
    save("panel_i", shadowed(x1 - x0, y1 - mid - 10, 28, (255, 255, 255, 255), pad), (x0 - pad, mid + 10 - pad))
    # 판 안 웹사이트 칸을 흐리는 흰 막(인스턴트 차례)
    dim = Image.new("RGBA", (x1 - x0 - 8, SEC_Y[1] - 10 - y0 - 8), (255, 255, 255, 150))
    save("dim", dim, (x0 + 4, y0 + 4))
    # 드롭다운 줄 테두리(웹사이트 줄 자리, 인스턴트 때 아래로 옮김) — 오른쪽 끝은 판 밑으로 들어간다
    ya, yb = sc(0, ROWS["web"][0])[1], sc(0, ROWS["web"][1])[1]
    hw, hh = int(x0 + 20 - 26), int(yb - ya + 12)
    hl = Image.new("RGBA", (hw, hh), (0, 0, 0, 0))
    ImageDraw.Draw(hl).rounded_rectangle((3, 3, hw - 3, hh - 3), 16, fill=META_BLUE + (26,), outline=META_BLUE + (255,), width=6)
    save("hl", hl, (26, ya - 6))
    BOX["hl"] = (26, int(ya - 6), 26 + hw, int(sc(0, ROWS["inst"][1])[1] + 6))   # 두 자리를 다 덮는 상자(검사용)

    def section(tag, sy, title, steps, rows):
        cx = x0 + 44
        # 제목: 파란 점 + 굵은 글
        f = font(42)
        t = Image.new("RGBA", (int(tlen(title, f)) + 60, 64), (0, 0, 0, 0))
        d = ImageDraw.Draw(t)
        d.ellipse((4, 20, 28, 44), outline=META_BLUE + (255,), width=5)
        d.ellipse((11, 27, 21, 37), fill=META_BLUE + (255,))
        d.text((44, 32), title, font=f, fill=INK, anchor="lm")
        save(f"{tag}_title", t, (cx, sy + 30))
        # 단계 알약 + 화살표(왼→오)
        f = font(29)
        x = cx
        for k, (s, _) in enumerate(steps):
            w = int(tlen(s, f)) + 44
            p = Image.new("RGBA", (w, 56), (0, 0, 0, 0))
            ImageDraw.Draw(p).rounded_rectangle((0, 0, w - 1, 55), 28, fill=PILL_BG + (255,))
            ImageDraw.Draw(p).text((w / 2, 28), s, font=f, fill=INK, anchor="mm")
            save(f"{tag}_s{k}", p, (x, sy + 116))
            x += w
            if k < len(steps) - 1:
                a = Image.new("RGBA", (34, 56), (0, 0, 0, 0))
                ImageDraw.Draw(a).polygon([(10, 18), (24, 28), (10, 38)], fill=GREY + (255,))
                save(f"{tag}_a{k}", a, (x, sy + 116))
                x += 34
        # 결과 줄: 이름 · 게이지 5칸 · 꼬리말
        for j, (nm, label, _, _, n, col, tail, _) in enumerate(rows):
            ry = sy + 210 + j * 72
            f = font(30)
            lb = Image.new("RGBA", (190, 52), (0, 0, 0, 0))
            ImageDraw.Draw(lb).text((0, 26), label, font=f, fill=INK, anchor="lm")
            save(f"{nm}_label", lb, (cx, ry))
            for kind, cols in (("empty", [EMPTY] * 5), ("fill", [col if i < n else (0, 0, 0, 0)[:3] for i in range(5)])):
                g = Image.new("RGBA", (5 * 46, 52), (0, 0, 0, 0))
                d = ImageDraw.Draw(g)
                for i in range(5):
                    if kind == "fill" and i >= n:
                        continue
                    d.rounded_rectangle((i * 46, 16, i * 46 + 38, 36), 8, fill=cols[i] + (255,))
                save(f"{nm}_{kind}", g, (cx + 196, ry))
            f = font(30)
            tc = RED if col == RED else (META_BLUE if n >= 4 else GREY)
            tl = Image.new("RGBA", (int(tlen(tail, f)) + 8, 52), (0, 0, 0, 0))
            ImageDraw.Draw(tl).text((0, 26), tail, font=f, fill=tc, anchor="lm")
            save(f"{nm}_tail", tl, (cx + 196 + 5 * 46 + 24, ry))
        BOX.pop(f"{rows[0][0]}_empty", None)          # 빈 게이지는 채움과 같은 자리(검사에서 뺌)
        BOX.pop(f"{rows[1][0]}_empty", None)

    section("w", SEC_Y[0], "웹사이트", W_STEPS, W_ROWS)
    section("i", SEC_Y[1], "인스턴트 양식", I_STEPS, I_ROWS)
    check_layout()


# ── 애펙 ───────────────────────────────────────────────────────
def jsx(out_mov):
    js = AE.js
    s = lambda t: round(t - T0, 4)                         # noqa: E731
    L = ["function eo(p){ for(var k=1;k<=p.numKeys;k++){ var n=p.isSpatial?1:(p.value.length||1), o=[], i=[]; for(var j=0;j<n;j++){ o.push(new KeyframeEase(0,0.1)); i.push(new KeyframeEase(0,85)); } p.setTemporalEaseAtKey(k,i,o); } }",
         f"(function(){{ var comp=app.project.items.addComp('bisa06',{W},{H},1,{DUR:.3f},{FPS});"]
    a = L.append
    nv = [0]

    def lay(name):
        nv[0] += 1
        var = f"L{nv[0]}"
        x, y, w, h = BOX[name + "@"]
        a(f"var {var}=comp.layers.add(imp({js(str(WORK / f'{name}.png'))})); {var}.transform.position.setValue([{x + w / 2:.1f},{y + h / 2:.1f}]);")
        return var

    def show(var, t_in, t_out=T_OUT, fade_in=0.08):
        a(f"keys({var}.transform.opacity,[[{max(0, s(t_in) - 0.001)},0],[{s(t_in) + fade_in:.3f},100],[{s(t_out)},100],[{s(t_out) + 0.15:.3f},0]]);")

    def pop(var, name, t_in, frm=72, left=True):
        x, y, w, h = BOX[name + "@"]
        ax, ay = (0, h / 2) if left else (w / 2, h / 2)
        a(f"{var}.transform.anchorPoint.setValue([{ax},{ay}]); {var}.transform.position.setValue([{x + ax:.1f},{y + ay:.1f}]);")
        a(f"keys({var}.transform.scale,[[{s(t_in)},[{frm},{frm}]],[{s(t_in) + 0.22:.3f},[100,100]]]); eo({var}.transform.scale);")

    # 녹화 화면(사장님 컷 조각대로) + 확대
    a(f"var iv=imp({js(str(REC))});")
    for i, (ta, tb, rs, _) in enumerate(SEGS):
        a(f"var R{i}=comp.layers.add(iv); R{i}.startTime={s(ta) - rs:.4f}; R{i}.inPoint={s(ta):.4f}; R{i}.outPoint={s(tb):.4f};")
        a(f"R{i}.transform.anchorPoint.setValue([{A[0]},{A[1]}]);")
        a(f"keys(R{i}.transform.position,[[{s(T_ZOOM)},[{A[0]},{A[1]}]],[{s(T_ZOOM) + 0.5:.3f},[{P[0]},{P[1]}]],[{s(T_OUT)},[{P[0]},{P[1]}]],[{s(T_OUT) + 0.45:.3f},[{A[0]},{A[1]}]]]);")
        a(f"keys(R{i}.transform.scale,[[{s(T_ZOOM)},[100,100]],[{s(T_ZOOM) + 0.5:.3f},[{S * 100},{S * 100}]],[{s(T_OUT)},[{S * 100},{S * 100}]],[{s(T_OUT) + 0.45:.3f},[100,100]]]);")
        a(f"ez(R{i}.transform.position); ez(R{i}.transform.scale); flat(R{i}.transform.position);")
    # 줄 테두리: 웹사이트 → 인스턴트
    v = lay("hl")
    x, y, w, h = BOX["hl@"]
    dy = sc(0, ROWS["inst"][0])[1] - sc(0, ROWS["web"][0])[1]
    a(f"keys({v}.transform.position,[[{s(T_SWITCH)},[{x + w / 2:.1f},{y + h / 2:.1f}]],[{s(T_SWITCH) + 0.3:.3f},[{x + w / 2:.1f},{y + h / 2 + dy:.1f}]]]); eo({v}.transform.position);")
    show(v, T_WCARD, fade_in=0.15)
    # 카드
    for nm, t in (("panel_w", T_WCARD), ("panel_i", T_ICARD)):
        v = lay(nm)
        pop(v, nm, t, 92, left=False)
        show(v, t)

    def section(tag, t_card, steps, rows):
        v = lay(f"{tag}_title")
        pop(v, f"{tag}_title", t_card)
        show(v, t_card)
        for k, (_, t) in enumerate(steps):
            v = lay(f"{tag}_s{k}")
            pop(v, f"{tag}_s{k}", t)
            show(v, t)
            if k:
                v = lay(f"{tag}_a{k - 1}")
                show(v, t - 0.06, fade_in=0.1)
        for nm, _, t_row, t_fill, _, _, _, t_tail in rows:
            v = lay(f"{nm}_label")
            pop(v, f"{nm}_label", t_row)
            show(v, t_row)
            v = lay(f"{nm}_empty")
            show(v, t_row, fade_in=0.15)
            v = lay(f"{nm}_fill")                                   # 게이지가 왼쪽부터 차오름
            a(f"var e{v}={v}.Effects.addProperty('ADBE Linear Wipe'); e{v}.property(2).setValue(270); e{v}.property(3).setValue(6); keys(e{v}.property(1),[[{s(t_fill)},100],[{s(t_fill) + 0.45:.3f},0]]);")
            show(v, t_fill, fade_in=0.01)
            v = lay(f"{nm}_tail")
            pop(v, f"{nm}_tail", t_tail)
            show(v, t_tail)

    section("w", T_WCARD, W_STEPS, W_ROWS)
    v = lay("dim")                                                   # 인스턴트 차례엔 웹사이트 칸을 흐리게
    show(v, T_SWITCH, fade_in=0.3)
    section("i", T_ICARD, I_STEPS, I_ROWS)
    a(f"var rq=app.project.renderQueue.items.add(comp); var om=rq.outputModule(1); om.applyTemplate({js('고품질')}); om.file=new File({js(str(out_mov))});")
    a("log('ok bisa06'); })();")
    assert T_OUT + 0.45 < T1
    return "\n".join(L)



def run_ae_guarded(jf, logf, aep):
    """AfterFX -r 를 띄우고 지켜본다(10-07 밤 14·15 에서 두 번 멈춤).
    ① 20초 넘게 로그가 안 생기면 «충돌 복구 옵션» 창 → 애펙 창에 Enter(«계속»)
    ② 로그가 ok/ERR 이고 프로젝트가 저장됐는데 20초 넘게 안 닫히면 → 강제 종료(렌더는 aerender 로 따로 하므로 손실 없음)"""
    proc = subprocess.Popen([str(AE.AE_DIR / "AfterFX.exe"), "-r", str(jf)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t0, done_at, pressed = time.time(), None, 0
    while proc.poll() is None and time.time() - t0 < 900:
        time.sleep(3)
        txt = logf.read_text(errors="ignore") if logf.exists() else ""
        if not txt and time.time() - t0 > 20 + pressed * 25 and pressed < 20:      # 창이 늦게 뜰 수 있어 25초마다 계속(10-07 밤 16: 3번으론 부족)
            subprocess.run(["powershell", "-NoProfile", "-Command",
                            "$ws=New-Object -ComObject WScript.Shell; foreach($p in (Get-Process AfterFX -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 })){ if($ws.AppActivate($p.Id)){ Start-Sleep -Milliseconds 700; $ws.SendKeys('{ENTER}') } }"],
                           capture_output=True)
            pressed += 1
            print("애펙 응답 없음 → 충돌 복구 창으로 보고 Enter(계속)")
        if ("ok" in txt or "ERR" in txt) and aep.exists():
            done_at = done_at or time.time()
            if time.time() - done_at > 20:
                subprocess.run(["taskkill", "/F", "/IM", "AfterFX.exe"], capture_output=True)
                subprocess.run(["taskkill", "/F", "/IM", "AfterFX.com"], capture_output=True)
                print("애펙이 스크립트 끝난 뒤 안 닫힘 → 강제 종료(다음 실행 때 충돌 복구 창은 ①이 넘김)")
                break
    if proc.poll() is None:
        proc.kill()


def build():
    pieces()
    aep, jf, logf, mov = WORK / "a.aep", WORK / "a.jsx", WORK / "log.txt", WORK / "a.mov"
    for f in (logf, aep, mov):
        if f.exists():
            f.unlink()
    body = [AE.HEAD.replace("%LOG%", AE.js(str(logf))), "app.newProject();",
            "try{" + jsx(mov) + "}catch(e){ log('ERR '+e.toString()+' line '+e.line); }",
            f"app.project.save(new File({AE.js(str(aep))})); LOG.close(); app.quit();"]
    jf.write_text("\n".join(body), encoding="ascii")
    t0 = time.time()
    run_ae_guarded(jf, logf, aep)
    while time.time() - t0 < 900:
        txt = logf.read_text(errors="ignore") if logf.exists() else ""
        if aep.exists() and ("ok" in txt or "ERR" in txt) and not AE._ae_running():
            break
        time.sleep(3)
    txt = logf.read_text(errors="ignore") if logf.exists() else "(로그 없음)"
    print("AE:", txt.strip())
    if "ERR" in txt:
        raise SystemExit(txt)
    subprocess.run([str(AE.AE_DIR / "aerender.exe"), "-project", str(aep)], capture_output=True, timeout=1800)
    dst = OUT / f"{NAME}_{T0:.2f}~.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mov), "-c:v", "libx264", "-crf", "14", "-preset", "slow",
                    "-pix_fmt", "yuv420p", "-an", str(dst)], check=True)
    return dst


# ── 효과음 ── 이름 고정. 크기 = 목소리 원음 대비 구울 값. bisa_meta_sfx.FILE_DB(사장님 10-07 실측)가 우선,
# 표에 없는 파일은 효과음 길라잡이 0-2 «파일별 크기» 읽는 법대로 일반 +2 · 게이지 +5.
SND_FIX = {
    "zoom":  ("휙２.mp3", 0.6, 1, "peak"),
    "card":  ("ML_Cartoon bubbles popping.wav", 0.5, 2, "onset"),   # 판·칸 등장
    "st1":   ("KN_pepSound1.wav", 0.4, 2, "onset"),                 # 단계 알약
    "st2":   ("KN_pepSound2.wav", 0.4, 2, "onset"),
    "msg":   ("채팅 효과음.mp3", 0.6, 2, "onset"),                   # «문의» · «넘어감» = 메시지가 넘어감
    "g1":    ("SEL_ゲージ回復1.mp3", 0.6, 9, "onset"),              # 게이지 차오름(02·04 통과)
    "g2":    ("SEL_ゲージ回復2.mp3", 0.6, 5, "onset"),
    "g3":    ("SEL_ゲージ回復3.mp3", 0.6, 5, "onset"),
    "ok":    ("맑은소리.mp3", 0.8, 4, "onset"),                      # «잘 됨»
    "fake":  ("KN_error_003.wav", 0.5, 2, "onset"),                 # 허수 DB(빨강)
    "back":  ("휙1.mp3", 0.7, 5, "peak"),
}
EVENTS = [(T_ZOOM + 0.25, "zoom"), (T_WCARD, "card"),
          (W_STEPS[0][1], "st1"), (W_STEPS[1][1], "st2"), (W_STEPS[3][1], "msg"),
          (W_ROWS[0][2], "st1"), (W_ROWS[0][3], "g2"), (W_ROWS[1][2], "st2"), (W_ROWS[1][3], "g1"), (W_ROWS[1][7], "ok"),
          (T_ICARD, "card"), (I_STEPS[0][1], "st1"), (I_STEPS[1][1], "st2"), (I_STEPS[2][1], "msg"),
          (I_ROWS[0][3], "g3"), (I_ROWS[1][2], "fake"), (I_ROWS[1][7], "st1"), (T_OUT + 0.2, "back")]


def voice():
    parts = []
    for ta, tb, _, cs in SEGS:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{cs}", "-t", f"{tb - ta}", "-i", str(CAM), "-vn",
                              "-af", "aresample=48000,aformat=sample_fmts=flt:channel_layouts=stereo", "-f", "f32le", "-"],
                             capture_output=True, check=True).stdout
        x = np.frombuffer(raw, np.float32).reshape(-1, 2)
        n = int(round((tb - ta) * SFX.SR))
        x = np.pad(x, ((0, max(0, n - len(x))), (0, 0)))[:n]
        parts.append(x)
    return np.concatenate(parts).copy()


def cam_preview(dst):
    """사람 PIP 미리보기용: 사장님 V2 컷대로 이어 붙인 사람 영상(소리 없음)."""
    fc, ins = [], []
    for i, (ta, tb, _, cs) in enumerate(SEGS):
        ins += ["-ss", f"{cs}", "-t", f"{tb - ta:.3f}", "-i", str(CAM)]
        fc.append(f"[{i}:v]scale=1152:648,fps=30,setpts=PTS-STARTPTS[v{i}]")
    fc.append("".join(f"[v{i}]" for i in range(len(SEGS))) + f"concat=n={len(SEGS)}:v=1:a=0[o]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", ";".join(fc), "-map", "[o]",
                    "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", str(dst)], check=True)


def sfx(scene):
    snd = {k: SFX.role(by_name(f), mx, rel, al) for k, (f, mx, rel, al) in SND_FIX.items()}
    SFX.SND.clear()
    SFX.SND.update(snd)
    v = voice()
    f = SFX.rms_frames(v)
    ref = float(np.median(f[f > f.max() - 25]))
    SFX_DIR.mkdir(parents=True, exist_ok=True)
    cache, placed, mix = {}, [], np.zeros_like(v)
    for k, (t, name) in enumerate(EVENTS):
        if name not in cache:
            cache[name] = SFX.prep(name, ref)
        x, peak_at = cache[name]
        start = t - (peak_at if snd[name][5] == "peak" else 0.0)
        fp = SFX_DIR / f"{k + 1:02d}_{name}.wav"
        SFX.write_wav(fp, x)
        placed.append((round(start, 3), fp, name))
        i = int((start - T0) * SFX.SR)
        seg = x[: len(mix) - i]
        mix[i: i + len(seg)] += seg
        print(f"  {start:6.2f}s  {name:5s} [{snd[name][6]}] {snd[name][0].name}  {snd[name][4]:+d}dB")
    bad = [it for it in rule_check.check_sfx([(t - T0, snd[n][0], len(cache[n][0]) / SFX.SR) for t, _, n in placed], T1 - T0) if it[0] == "ERROR"]
    for it in bad:
        print(*it)
    if bad:
        sys.exit(1)
    SFX.write_wav(SFX_DIR / f"00_효과음만_합본_{T0:.2f}~.wav", mix)
    tmp = SFX_DIR / "_미리듣기소리.wav"
    # 미리듣기는 사장님 타임라인처럼 목소리 +7dB(효과음 구울 값이 이 기준)
    both = v * 10 ** (7 / 20) + mix * 10 ** (7 / 20)
    both *= min(1.0, 0.8 / (np.abs(both).max() + 1e-9))
    SFX.write_wav(tmp, both)
    camv = WORK / "cam.mp4"
    cam_preview(camv)
    pre = OUT / f"{NAME}_미리보기.mp4"
    cx, cy = 0.0734 * W, 0.837 * H
    pw, ph = 1152, 648
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(scene), "-i", str(camv), "-i", str(tmp),
                    "-filter_complex", f"[0:v][1:v]overlay={cx - pw / 2:.0f}:{cy - ph / 2:.0f}[v]",
                    "-map", "[v]", "-map", "2:a", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
                    "-af", "alimiter=limit=0.84:level=false", "-c:a", "aac", "-b:a", "256k", "-shortest", str(pre)], check=True)
    tmp.unlink()
    lec_xml.V_TRACK, lec_xml.A_TRACK = 1, 2                 # 장면은 V1 녹화 조각 자리(사람 V2 아래)
    print(lec_xml.write(OUT / f"{NAME}_효과음.xml", f"빡이사DB_{NAME}", scene, DUR, T0,
                        [(t, f) for t, f, _ in placed], 59.94, tag="bs06"))
    return pre


if __name__ == "__main__":
    scene = OUT / f"{NAME}_{T0:.2f}~.mp4"
    if "--조각만" in sys.argv:
        pieces()
        sys.exit()
    if "--소리만" not in sys.argv:
        scene = build()
    print(scene)
    print(sfx(scene))
