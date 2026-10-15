# -*- coding: utf-8 -*-
r"""[레거시 — 10-13 부터 AE 안 씀. 새 장면은 html_motion(references/ae-replacement.md)]
빡이사DB 후킹 «그래서 오늘 공통적으로 DB 잘 뽑는 법 / 그리고 여러 업종에서 공용으로 잘 쓸 수 있는
메타 DB 광고 세팅법 공유해드릴 겁니다»(20.08~28.32) — 오늘의 목차, 노트 필기 (사장님 10-02 시안 A → 3판).

  python bisa_toc_cards.py [--소리만]
    → 빡이사DB\납품\02_목차카드_20.00~.mp4 (사람 포함 — 프리미어 원본 컷이 바뀌면 다시 렌더)
    → 02_목차카드_효과음.xml (V2 장면 + A2~ 효과음) · 02_목차카드_미리보기.mp4 (장면 + 목소리 + 효과음)
판 이력
  1판 벽 카드 → 2판 반반(사람 왼쪽·카드 판) «사람이 왼쪽으로 가고 화면이 오른쪽으로 나오면서 반반, 겹침 없게»
  3판 «이미지가 마음에 안 들어, 노트에 글씨 쓰면서 적는 느낌으로» + «게이지는 왜 뺐어, 1번 올라갈 때 그런 거 넣고»
흐름(시퀀스 초)
  20.30 «그래서»          사람이 왼쪽 절반으로, 오른쪽에서 스프링 노트가 들어옴(머리글 «오늘 알려드릴 2가지»는 이미 적혀 있음)
  20.72 «공통적으로»      펜이 «1. 공통» 적음
  21.40 «디비 잘 뽑는 법» 펜이 «DB 잘 뽑는 법» 크게 적음 → 22.05 형광펜 게이지가 차오름(게이지 소리)
  23.10 «그리고 여러»     «2. 여러 업종 공용» → 23.60 «업종에서 공용으로» 연필로 «정책자금, 보험, 피부과, 분양 등»(개구 글꼴에 · … 이 없다)
  25.70 «메타»            «메타 DB 광고 세팅법» 크게 적음
  27.40 «공유해»          형광펜이 메타 줄에 그어지고, «2가지»에 빨간 동그라미
  28.30 끝                노트가 오른쪽으로 빠지고 사람 꽉 찬 화면 → 28.75
손글씨 글꼴: 개구 굵게(Gaegu Bold, OFL) — `_tmp\fonts\` (없으면 google/fonts 저장소 ofl/gaegu 에서 받는다).
겹침: 줄마다 실제 픽셀 상자를 재서 서로 겹치거나 종이 밖이면 렌더 전에 멈춘다.
"""

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[0]))   # tools/ (config.py)
import config  # noqa: E402
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(config.TOOLS))
import rf3_ae as AE  # noqa: E402
import rule_check  # noqa: E402
import lec_xml  # noqa: E402
import bisa_meta_sfx as SFX  # noqa: E402  (load·prep·write_wav·role 재사용)

W, H, FPS = 1920, 1080, 59.94
T0, T1 = 20.00, 28.75
DUR = T1 - T0
SRC = (config.RAW_ROOT / "디비광고세팅법 후킹부분.mp4")
WORK = (config.WORK / "빡이사" / "ae02")
OUT = config.OUT
SFX_DIR = (config.WORK / "효과음02")
HAND = Path(config.FONTS["gaegu_bold"])
HAND_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/gaegu/Gaegu-Bold.ttf"
PAPER, RULE, MARGIN = (253, 251, 245), (196, 214, 236), (232, 120, 120)
NAVY, BLUE, PENCIL, RED = (25, 35, 60), (30, 90, 210), (110, 115, 128), (225, 50, 50)
YELLOW = (255, 222, 70)

PX = 900                             # 판 기준점(그림자 포함 왼쪽 끝)이 놓이는 화면 x. 종이는 960부터
RULE_Y0, RULE_GAP = 280, 90
X_TEXT = 1130
T_SPLIT, T_BACK = 20.30, 28.30
# (이름, 글, 크기, 색, 화면 x, 기준선 y, 쓰기 시작, 쓰기 끝)
ROWS = [("r1", "1. 공통", 52, BLUE, X_TEXT, 370, 20.72, 21.10),
        ("r2", "DB 잘 뽑는 법", 92, NAVY, X_TEXT, 460, 21.40, 22.00),
        ("r3", "2. 여러 업종 공용", 52, BLUE, X_TEXT, 640, 23.10, 23.55),
        ("r4", "정책자금, 보험, 피부과, 분양 등", 40, PENCIL, X_TEXT + 30, 715, 23.60, 24.60),
        ("r5", "메타 DB 광고 세팅법", 84, NAVY, X_TEXT, 820, 25.70, 26.70)]
HL = [("hl1", "r2", 22.05, 22.45), ("hl2", "r5", 27.40, 27.75)]      # 형광펜 게이지(줄, 시작, 끝)
T_CIRCLE = (27.55, 27.95)
POS = {}                              # 이름 → 화면 상자 (x0, y0, x1, y1)
SHOW_PEN = False                      # 펜 그림(사장님 10-02 «흔들려서 집중 분산» → 끔)


def hand(n):
    if not HAND.exists():
        HAND.parent.mkdir(parents=True, exist_ok=True)
        HAND.write_bytes(urllib.request.urlopen(HAND_URL, timeout=60).read())
    return ImageFont.truetype(str(HAND), n)


def text_png(name, text, size, color, x, base):
    """글 한 줄을 딱 맞는 PNG 로. POS 에 화면 상자를 적는다."""
    sys.path.insert(0, str(config.TOOLS))
    import glyph_check                                     # 개구에 없는 «·»«→» 등은 렌더 전에 멈춤(10-08)
    glyph_check.check(text, str(HAND))
    f = hand(size)
    l, t, r, b = f.getbbox(text, anchor="ls")
    pad = 8
    im = Image.new("RGBA", (r - l + 2 * pad, b - t + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((pad - l, pad - t), text, font=f, fill=color + (255,), anchor="ls")
    im.save(WORK / f"{name}.png")
    POS[name] = (x + l - pad, base + t - pad, x + r + pad, base + b + pad)


def marker_png(name, box):
    """형광펜 한 획 — 글 아래 절반쯤, 가장자리를 살짝 거칠게."""
    x0, y0, x1, y1 = box
    hgt = int((y1 - y0) * 0.42)
    w = int(x1 - x0 + 20)
    im = Image.new("RGBA", (w, hgt + 10), (0, 0, 0, 0))
    rng = np.random.default_rng(7)
    top = [(i, 5 + rng.integers(-2, 3)) for i in range(0, w, 24)] + [(w - 1, 5)]
    bot = [(i, hgt + 4 + rng.integers(-2, 3)) for i in range(w - 1, -1, -24)] + [(0, hgt + 4)]
    ImageDraw.Draw(im).polygon(top + bot, fill=YELLOW + (175,))
    im = im.filter(ImageFilter.GaussianBlur(1.2))
    im.save(WORK / f"{name}.png")
    POS[name] = (x0 - 10, y1 - hgt - 18, x0 - 10 + w, y1 - 8)


def pen_png():
    """볼펜 — 끝이 왼쪽 아래를 향하게. 기준점 = 펜촉."""
    im = Image.new("RGBA", (420, 70), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(4, 35), (46, 22), (46, 48)], fill=(170, 175, 185, 255))          # 펜촉 금속
    d.rectangle((46, 20, 120, 50), fill=(40, 45, 58, 255))                       # 손잡이
    d.rounded_rectangle((116, 16, 400, 54), 14, fill=BLUE + (255,))              # 몸통
    d.rectangle((300, 8, 380, 16), fill=(200, 205, 215, 255))                    # 클립
    d.ellipse((0, 31, 9, 40), fill=(20, 20, 30, 255))
    sh = Image.new("RGBA", (440, 90), (0, 0, 0, 0))
    sh.alpha_composite(im, (10, 14))
    shadow = Image.new("RGBA", sh.size, (0, 0, 0, 0))
    shadow.paste((0, 0, 0, 70), mask=sh.split()[3])
    out = Image.new("RGBA", (460, 110), (0, 0, 0, 0))
    out.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(5)), (14, 14))
    out.alpha_composite(sh, (0, 0))
    out = out.rotate(38, resample=Image.BICUBIC, expand=True)
    a = np.array(out)[..., 3] > 200
    ys, xs = np.where(a)
    i = np.argmin(xs)
    out.save(WORK / "pen.png")
    return int(xs[i]), int(ys[i])


def panel_png():
    pn = Image.new("RGBA", (960 + 60, H), (0, 0, 0, 0))
    s3 = Image.new("RGBA", pn.size, (0, 0, 0, 0))
    ImageDraw.Draw(s3).rectangle((60, 0, 60 + 960, H), fill=(0, 0, 0, 110))
    pn.alpha_composite(s3.filter(ImageFilter.GaussianBlur(22)))
    body = Image.new("RGBA", (960, H), PAPER + (255,))
    d = ImageDraw.Draw(body)
    for y in range(RULE_Y0, H - 20, RULE_GAP):
        d.line((70, y, 940, y), fill=RULE + (255,), width=2)
    d.line((X_TEXT - 960 - 20, 0, X_TEXT - 960 - 20, H), fill=MARGIN + (255,), width=2)
    for y in range(50, H - 20, 64):                                              # 스프링
        d.ellipse((24, y - 9, 42, y + 9), fill=(205, 205, 210, 255))
        d.rounded_rectangle((-6, y - 13, 36, y + 13), 12, outline=(140, 146, 158, 255), width=5)
    f = hand(66)
    t1, t2 = "오늘 알려드릴 ", "2가지"
    x0, base = X_TEXT - 960, 190
    d.text((x0, base), t1, font=f, fill=NAVY + (255,), anchor="ls")
    w1 = d.textlength(t1, font=f)
    d.text((x0 + w1, base), t2, font=f, fill=BLUE + (255,), anchor="ls")
    l, t, r, b = f.getbbox(t2, anchor="ls")
    POS["head"] = (960 + x0 + f.getbbox(t1, anchor="ls")[0], base + min(t, f.getbbox(t1, anchor="ls")[1]), 960 + x0 + w1 + r, base + b)
    POS["head2"] = (960 + x0 + w1 + l, base + t, 960 + x0 + w1 + r, base + b)
    pn.alpha_composite(body, (60, 0))
    pn.save(WORK / "panel.png")


def circle_png():
    x0, y0, x1, y1 = POS["head2"]
    m = 22
    w, h = int(x1 - x0 + 2 * m), int(y1 - y0 + 2 * m)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.arc((4, 6, w - 4, h - 4), 200, 560, fill=RED + (255,), width=6)             # 한 바퀴 조금 넘게 — 손으로 그린 느낌
    d.arc((8, 2, w - 2, h - 8), 190, 250, fill=RED + (255,), width=5)
    im.save(WORK / "circle.png")
    POS["circle"] = (x0 - m, y0 - m, x0 - m + w, y0 - m + h)


def check_layout():
    names = [r[0] for r in ROWS] + ["head"]
    bad = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            A, B = POS[a], POS[b]
            if A[0] < B[2] and B[0] < A[2] and A[1] < B[3] and B[1] < A[3]:
                bad.append(f"{a} {A} ↔ {b} {B}")
    for n in names + ["hl1", "hl2", "circle"]:
        x0, y0, x1, y1 = POS[n]
        if x0 < 1000 or x1 > W - 20 or y0 < 20 or y1 > H - 20:
            bad.append(f"{n} {POS[n]} 종이 밖")
    if bad:
        raise SystemExit("레이아웃 겹침:\n  " + "\n  ".join(bad))
    print("겹침 없음")


def pieces():
    WORK.mkdir(parents=True, exist_ok=True)
    panel_png()
    for name, text, size, color, x, base, *_ in ROWS:
        text_png(name, text, size, color, x, base)
    for name, row, *_ in HL:
        marker_png(name, POS[row])
    circle_png()
    check_layout()
    return pen_png()


def jsx(out_mov, tip):
    js = AE.js
    s = lambda t: round(t - T0, 4)                         # noqa: E731
    L = [f"(function(){{ var comp=app.project.items.addComp('bisa02',{W},{H},1,{DUR:.3f},{FPS});"]
    a = L.append
    a(f"var iv=imp({js(str(SRC))}); var Lp=comp.layers.add(iv); Lp.startTime={-T0}; Lp.transform.scale.setValue([50,50]);")
    a(f"keys(Lp.transform.position,[[{s(T_SPLIT)},[960,540]],[{s(T_SPLIT) + 0.45:.3f},[480,540]],[{s(T_BACK)},[480,540]],[{s(T_BACK) + 0.36:.3f},[960,540]]]); ez(Lp.transform.position);")
    a(f"var PN=comp.layers.add(imp({js(str(WORK / 'panel.png'))})); PN.transform.anchorPoint.setValue([0,540]);")
    a(f"keys(PN.transform.position,[[{s(T_SPLIT)},[{W},540]],[{s(T_SPLIT) + 0.45:.3f},[{PX},540]],[{s(T_BACK)},[{PX},540]],[{s(T_BACK) + 0.36:.3f},[{W + 40},540]]]); ez(PN.transform.position);")

    def wipe_layer(var, png, box, t0, t1, radial=False, blend=None):
        x0, y0, x1, y1 = box
        a(f"var {var}=comp.layers.add(imp({js(str(WORK / png))})); {var}.parent=PN; {var}.transform.position.setValue([{(x0 + x1) / 2 - PX:.1f},{(y0 + y1) / 2:.1f}]);")
        if blend:
            a(f"{var}.blendingMode=BlendingMode.{blend};")
        if radial:
            a(f"var e{var}={var}.Effects.addProperty('ADBE Radial Wipe'); e{var}.property(2).setValue(200);")
            a(f"keys(e{var}.property(1),[[{s(t0)},100],[{s(t1)},0]]);")
        else:                                              # 왼쪽부터 드러남(각도 270, 완료 100→0)
            a(f"var e{var}={var}.Effects.addProperty('ADBE Linear Wipe'); e{var}.property(2).setValue(270); e{var}.property(3).setValue(12);")
            a(f"keys(e{var}.property(1),[[{s(t0)},100],[{s(t1)},0]]);")

    for name, row, t0, t1 in HL:                           # 형광펜은 글 밑에 깔리게 먼저
        wipe_layer(name.upper(), f"{name}.png", POS[name], t0, t1, blend="MULTIPLY")
    for name, _, _, _, _, _, t0, t1 in ROWS:
        wipe_layer(name.upper(), f"{name}.png", POS[name], t0, t1)
    wipe_layer("CIR", "circle.png", POS["circle"], *T_CIRCLE, radial=True)

    # 펜 그림 — 10-02 «연필이 너무 흔들려서 집중이 분산돼» → 기본 끔(글씨는 왼쪽부터 써지는 것만)
    if not SHOW_PEN:
        a(f"var rq=app.project.renderQueue.items.add(comp); var om=rq.outputModule(1); om.applyTemplate({js('고품질')}); om.file=new File({js(str(out_mov))});")
        a("log('ok bisa02'); })();")
        return "\n".join(L)
    a(f"var PE=comp.layers.add(imp({js(str(WORK / 'pen.png'))})); PE.transform.anchorPoint.setValue([{tip[0]},{tip[1]}]);")
    pk, first = [], True
    for name, _, size, _, _, base, t0, t1 in ROWS:
        x0, _, x1, _ = POS[name]
        y = base - size * 0.3
        if first:
            pk.append([s(t0 - 0.25), [x0 + 120, y + 140]])
            first = False
        else:
            pk.append([s(t0 - 0.18), [x0, y]])
        pk += [[s(t0), [x0, y]], [s(t1), [x1, y]]]
    x_end, y_end = pk[-1][1]
    pk.append([s(ROWS[-1][7] + 0.4), [x_end + 160, y_end + 200]])
    a(f"keys(PE.transform.position,{[[round(t, 3), [round(v[0], 1), round(v[1], 1)]] for t, v in pk]});")
    a("PE.transform.position.expression='value + [Math.sin(time*31)*3, Math.sin(time*47)*5]';")
    a(f"keys(PE.transform.opacity,[[{s(ROWS[0][6] - 0.3):.3f},0],[{s(ROWS[0][6] - 0.15):.3f},100],[{s(ROWS[-1][7] + 0.2):.3f},100],[{s(ROWS[-1][7] + 0.45):.3f},0]]);")
    a(f"var rq=app.project.renderQueue.items.add(comp); var om=rq.outputModule(1); om.applyTemplate({js('고품질')}); om.file=new File({js(str(out_mov))});")
    a("log('ok bisa02'); })();")
    return "\n".join(L)


def build():
    tip = pieces()
    aep, jf, logf, mov = WORK / "a.aep", WORK / "a.jsx", WORK / "log.txt", WORK / "a.mov"
    for f in (logf, aep, mov):
        if f.exists():
            f.unlink()
    body = [AE.HEAD.replace("%LOG%", AE.js(str(logf))), "app.newProject();",
            "try{" + jsx(mov, tip) + "}catch(e){ log('ERR '+e.toString()+' line '+e.line); }",
            f"app.project.save(new File({AE.js(str(aep))})); LOG.close(); app.quit();"]
    jf.write_text("\n".join(body), encoding="ascii")
    t0 = time.time()
    subprocess.run([str(AE.AE_DIR / "AfterFX.exe"), "-r", str(jf)], capture_output=True, timeout=900)
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
    dst = OUT / "02_목차카드_20.00~.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mov), "-c:v", "libx264", "-crf", "14", "-preset", "slow",
                    "-pix_fmt", "yuv420p", "-an", str(dst)], check=True)
    return dst


# ── 효과음 ── 이름 고정. 역할 → (파일, 최대 길이, 목소리 대비 dB, 맞춤)
#   통과(10-02 2판): 2번 등장 거품 팝 · 메타 줄 맑은소리 — 같은 순간에 그대로 둔다.
#   «게이지는 왜 뺐어, 1번 올라갈 때 그런 거» → 1번 형광펜 게이지에 게이지 소리.
#   펜 소리는 줄 쓰는 동안만, 작게. 같은 파일이 연달아 붙지 않게 샤프·연필을 번갈아(같은 파일 3번 이하).
SND_FIX = {
    "split": ("휙２.mp3", 0.6, -2, "peak"),
    "pen1":  ("SEL_シャーペンで字を書く.mp3", 0.38, -7, "onset"),
    "gauge": ("SEL_ゲージ回復1.mp3", 0.6, -1, "onset"),
    "pop":   ("ML_Cartoon bubbles popping.wav", 0.45, -1, "onset"),   # 통과
    "pen2":  ("24. 연필.mp3", 0.6, -7, "onset"),
    "pen3":  ("SEL_シャーペンで字を書く.mp3", 0.45, -7, "onset"),
    "pen4":  ("24. 연필.mp3", 0.9, -8, "onset"),
    "title": ("맑은소리.mp3", 0.8, -1, "onset"),                       # 통과
    "pen5":  ("SEL_シャーペンで字を書く.mp3", 1.0, -7, "onset"),
    "shine": ("14. 짜잔.wav", 1.0, -1, "onset"),
    "back":  ("휙1.mp3", 0.7, -2, "peak"),
}
EVENTS = [(T_SPLIT + 0.22, "split"), (ROWS[0][6], "pen1"), (ROWS[1][6], "pen2"), (HL[0][2], "gauge"),
          (ROWS[2][6], "pop"), (ROWS[2][6] + 0.02, "pen3"), (ROWS[3][6], "pen4"),
          (ROWS[4][6], "title"), (ROWS[4][6] + 0.02, "pen5"), (HL[1][2], "shine"), (T_BACK + 0.18, "back")]


def by_name(n):
    rs = json.loads(SFX.GRADE.read_text(encoding="utf-8"))
    r = next((r for r in rs if Path(r["파일"]).name == n), None)
    if r is None:                                          # 등급표 다시 돌리기 전 새로 받은 파일
        p = next(p for root in config.SFX_ROOTS.values() if root.exists() for p in root.rglob(n))   # 폴더 지도 순서대로
        r = {"파일": str(p), "소재상태": "통과", "등급": "-"}
    return r


def sfx(scene):
    snd = {k: SFX.role(by_name(f), mx, rel, al) for k, (f, mx, rel, al) in SND_FIX.items()}
    SFX.SND.clear()
    SFX.SND.update(snd)
    v = SFX.load(SRC)[int(T0 * SFX.SR): int(T1 * SFX.SR)]
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
        print(f"  {start:5.2f}s  {name:6s} [{snd[name][6]}] {snd[name][0].name}")
    bad = [it for it in rule_check.check_sfx([(t - T0, snd[n][0]) for t, _, n in placed], T1 - T0) if it[0] == "ERROR"]
    for it in bad:
        print(*it)
    if bad:
        sys.exit(1)
    SFX.write_wav(SFX_DIR / "00_효과음만_합본_20.00~.wav", mix)
    tmp = SFX_DIR / "_미리듣기소리.wav"
    both = v + mix
    both *= min(1.0, 0.8 / (np.abs(both).max() + 1e-9))       # 1.0 넘으면 wav 에서 잘린 채로 리미터에 들어가 트루피크가 넘는다(10-02 03 +1.3dB)
    SFX.write_wav(tmp, both)
    pre = OUT / "02_목차카드_미리보기.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(scene), "-i", str(tmp), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", "alimiter=limit=0.84:level=false", "-c:a", "aac", "-b:a", "256k", "-shortest", str(pre)], check=True)
    tmp.unlink()
    lec_xml.V_TRACK, lec_xml.A_TRACK = 2, 2
    print(lec_xml.write(OUT / "02_목차카드_효과음.xml", "빡이사DB_02_목차카드", scene, DUR, T0,
                        [(t, f) for t, f, _ in placed], 59.94, tag="bs02"))
    return pre


if __name__ == "__main__":
    scene = OUT / "02_목차카드_20.00~.mp4"
    if "--소리만" not in sys.argv:
        scene = build()
    print(scene)
    print(sfx(scene))
