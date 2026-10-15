# -*- coding: utf-8 -*-
r"""[레거시 — 10-13 부터 AE 안 씀. 새 장면은 html_motion(references/ae-replacement.md)]
빡이사DB 후킹 «저는 한 달간 메타에서 정책자금, 보험 … 여러가지 업종에 대행을 하고 있습니다»(1.28~9.80) — 애펙 (사장님 10-01).

  python bisa_meta_cards.py → 빡이사DB\납품\01_메타로고·업종카드_2.00~.mp4 · 01_…_배치.xml (V2, 시퀀스 1920×1080 59.94)
흐름(시퀀스 초 = 원본 «디비광고세팅법 후킹부분.mp4» 초, 0초부터 통째로 깔려 있음)
  2.14 «메타에서»  사람 오른쪽 빈 벽에 메타 로고 톡
  2.40~2.85        로고에서 파란 물결이 퍼지며 오른쪽 절반이 홈페이지 같은 판으로 열림 + 사람은 왼쪽 절반으로 밀림, 로고는 판 머리로
  2.90~7.18        업종 카드 8장이 말하는 순간마다 작게 톡 → 자리 잡음(4×2): 정책자금·보험·피부과·부동산 분양·장기렌트·휴대폰·정수기·프랜차이즈
  8.06 «여러가지»  카드 전부 차례로 반짝 + 살짝 커졌다 작아짐 두 번
  8.84 «대행을»    카드 빠지고 판이 오른쪽으로 빠지며 사람이 다시 꽉 찬 화면으로 → 9.40 끝
카드 사진: 8장 모두 Codex 연출 사진(글자·로고 없음). 홈페이지 실제 썸네일은 업체명·대표번호가 찍혀 있어 사장님 판단으로 뺌(10-01).
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
import rf3_ae as AE  # noqa: E402

W, H, FPS = 1920, 1080, 59.94
T0, T1 = 2.00, 9.40
DUR = T1 - T0
SRC = (config.RAW_ROOT / "디비광고세팅법 후킹부분.mp4")
CARDS = (config.WORK / "빡이사" / "cards")
WORK = (config.WORK / "빡이사" / "ae01")
OUT = config.OUT
FONT = str(config.FONTS["pretendard_bold"])
META_BLUE, META_CYAN, INK = (0, 100, 224), (0, 170, 255), (28, 43, 51)
PANEL = (246, 248, 252)

# (시퀀스 초, 카드 이름, 파일)
ITEMS = [(2.90, "정책자금", "01_정책자금.png"), (3.68, "보험", "02_보험.png"), (4.14, "피부과", "03_피부과.png"),
         (4.64, "부동산 분양", "04_부동산.png"), (5.50, "장기렌트", "05_장기렌트.png"), (6.04, "휴대폰", "06_휴대폰.png"),
         (6.68, "정수기", "07_정수기.png"), (7.18, "프랜차이즈", "08_프랜차이즈.png")]
LOGO_AT = (1530, 560)          # 사람 오른쪽 빈 벽
T_LOGO, T_SPREAD, T_OPEN = 2.14, 2.40, 2.85
T_SHINE = (8.06, 8.45)
T_BACK = 8.84
HEAD_Y = 92
CW, IH, LH, GAP = 196, 348, 58, 22          # 카드 폭 · 사진 높이 · 이름 칸 · 간격
CH = IH + LH
GX0 = 960 + (960 - (4 * CW + 3 * GAP)) / 2
GY0 = 170


def slot(i):
    r, c = divmod(i, 4)
    return GX0 + c * (CW + GAP) + CW / 2, GY0 + r * (CH + 28) + CH / 2


def rounded(im, r):
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), r, fill=255)
    im.putalpha(m)
    return im


def grad(size, c0, c1):
    w, h = size
    t = (np.add.outer(np.arange(h) / h, np.arange(w) / w) / 2)[..., None]
    a = np.array(c0, float) * (1 - t) + np.array(c1, float) * t
    return Image.fromarray(a.astype(np.uint8), "RGB").convert("RGBA")


def card_png(name, fn, k):
    pad, b = 26, 5
    im = Image.new("RGBA", (CW + 2 * pad, CH + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((pad, pad + 8, pad + CW, pad + CH + 8), 20, fill=(10, 30, 70, 110))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    border = rounded(grad((CW, CH), META_BLUE, META_CYAN), 20)
    im.alpha_composite(border, (pad, pad))
    inner = rounded(Image.new("RGBA", (CW - 2 * b, CH - 2 * b), (255, 255, 255, 255)), 16)
    im.alpha_composite(inner, (pad + b, pad + b))
    ph = Image.open(CARDS / fn).convert("RGB")
    pw, phh = CW - 2 * b - 8, IH - b - 4
    s = max(pw / ph.width, phh / ph.height)
    ph = ph.resize((round(ph.width * s), round(ph.height * s)), Image.LANCZOS)
    ph = ph.crop(((ph.width - pw) // 2, 0, (ph.width - pw) // 2 + pw, phh))
    im.alpha_composite(rounded(ph.convert("RGBA"), 12), (pad + b + 4, pad + b + 4))
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT, 26 if len(name) <= 4 else 23)
    cy = pad + IH + LH / 2
    tw = d.textlength(name, font=f) + 34
    d.rounded_rectangle((pad + CW / 2 - tw / 2, cy - 19, pad + CW / 2 + tw / 2, cy + 19), 19, fill=META_BLUE + (255,))
    d.text((pad + CW / 2, cy), name, font=f, fill=(255, 255, 255), anchor="mm")
    p = WORK / f"card{k}.png"
    im.save(p)
    hl = Image.new("RGBA", im.size, (0, 0, 0, 0))                      # 반짝일 때 테두리 빛
    ImageDraw.Draw(hl).rounded_rectangle((pad - 2, pad - 2, pad + CW + 2, pad + CH + 2), 22, outline=(140, 220, 255, 255), width=9)
    hl.filter(ImageFilter.GaussianBlur(7)).save(WORK / f"cardhl{k}.png")
    return p


def star_png():
    im = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = 60
    d.polygon([(c, 4), (c + 9, c - 9), (116, c), (c + 9, c + 9), (c, 116), (c - 9, c + 9), (4, c), (c - 9, c - 9)], fill=(255, 255, 255, 255))
    g = im.filter(ImageFilter.GaussianBlur(6))
    g.alpha_composite(im)
    g.save(WORK / "star.png")


def pieces():
    WORK.mkdir(parents=True, exist_ok=True)
    for k, (_, name, fn) in enumerate(ITEMS):
        card_png(name, fn, k)
    star_png()
    # 오른쪽 절반 판: 연한 바탕 + 점 무늬 + 왼쪽 가장자리 그림자
    pn = Image.new("RGBA", (960 + 60, H), (0, 0, 0, 0))
    sh = Image.new("RGBA", pn.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle((60, 0, 60 + 960, H), fill=(0, 0, 0, 120))
    pn.alpha_composite(sh.filter(ImageFilter.GaussianBlur(22)))
    body = Image.new("RGBA", (960, H), PANEL + (255,))
    d = ImageDraw.Draw(body)
    for y in range(20, H, 34):
        for x in range(20, 960, 34):
            d.ellipse((x - 2, y - 2, x + 2, y + 2), fill=(214, 224, 240, 255))
    d.rectangle((0, 0, 6, H), fill=META_BLUE + (255,))
    pn.alpha_composite(body, (60, 0))
    pn.save(WORK / "panel.png")
    # 머리글(로고 오른쪽 글)
    f = ImageFont.truetype(FONT, 46)
    t = Image.new("RGBA", (700, 80), (0, 0, 0, 0))
    td = ImageDraw.Draw(t)
    td.text((0, 40), "DB 업종별 ", font=f, fill=INK, anchor="lm")
    x = td.textlength("DB 업종별 ", font=f)
    td.text((x, 40), "광고 레퍼런스", font=f, fill=META_BLUE, anchor="lm")
    t.save(WORK / "head.png")
    # 메타 로고(심볼+글자) — 벽 위에서 잘 보이게 흰 반투명 받침
    logo = Image.open(CARDS / "meta_logo.png").convert("RGBA")
    lw = 520
    logo = logo.resize((lw, round(logo.height * lw / logo.width)), Image.LANCZOS)
    lg = Image.new("RGBA", (lw + 80, logo.height + 80), (0, 0, 0, 0))
    lg.alpha_composite(logo, (40, 40))
    lg.save(WORK / "logo.png")
    disc = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
    ImageDraw.Draw(disc).ellipse((0, 0, 199, 199), fill=(255, 255, 255, 255))
    disc.save(WORK / "disc.png")
    ring = Image.new("RGBA", (220, 220), (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse((10, 10, 209, 209), outline=META_CYAN + (255,), width=8)
    ring.filter(ImageFilter.GaussianBlur(2)).save(WORK / "ring.png")


def jsx(out_mov):
    js = AE.js
    s = lambda t: round(t - T0, 4)                         # noqa: E731  시퀀스 초 → 컴프 초
    L = [f"(function(){{ var comp=app.project.items.addComp('bisa01',{W},{H},1,{DUR:.3f},{FPS});"]
    a = L.append
    # 사람(원본 4K 를 50%)
    a(f"var iv=imp({js(str(SRC))}); var Lp=comp.layers.add(iv); Lp.startTime={-T0}; Lp.transform.scale.setValue([50,50]);")
    a(f"keys(Lp.transform.position,[[{s(T_SPREAD)},[960,540]],[{s(T_OPEN)},[480,540]],[{s(T_BACK + 0.10)},[480,540]],[{s(T_BACK + 0.46)},[960,540]]]); ez(Lp.transform.position);")
    # 판(원 모양으로 퍼지며 열림 → 끝에 오른쪽으로 빠짐)
    a(f"var ipn=imp({js(str(WORK / 'panel.png'))}); var Lpn=comp.layers.add(ipn); Lpn.transform.anchorPoint.setValue([0,540]);")
    a(f"keys(Lpn.transform.position,[[{s(T_BACK + 0.10)},[900,540]],[{s(T_BACK + 0.46)},[1960,540]]]); ez(Lpn.transform.position);")
    a(f"var idc=imp({js(str(WORK / 'disc.png'))}); var Ld=comp.layers.add(idc); Ld.transform.position.setValue([{LOGO_AT[0]},{LOGO_AT[1]}]);")
    a(f"keys(Ld.transform.scale,[[{s(T_SPREAD)},[0,0]],[{s(T_OPEN)},[1000,1000]]]); ez(Ld.transform.scale);")
    a("try{ Lpn.setTrackMatte(Ld, TrackMatteType.ALPHA); Ld.enabled=false; }catch(e){ Ld.moveBefore(Lpn); Lpn.trackMatteType=TrackMatteType.ALPHA; }")
    # 퍼지는 파란 고리 두 겹
    for k, d0 in enumerate((0.0, 0.08)):
        a(f"var ir{k}=imp({js(str(WORK / 'ring.png'))}); var R{k}=comp.layers.add(ir{k}); R{k}.transform.position.setValue([{LOGO_AT[0]},{LOGO_AT[1]}]);")
        t0 = s(T_SPREAD + d0)
        a(f"keys(R{k}.transform.scale,[[{t0},[40,40]],[{t0 + 0.5:.3f},[900,900]]]); keys(R{k}.transform.opacity,[[{t0 - 0.01:.3f},0],[{t0},100],[{t0 + 0.5:.3f},0]]); glow(R{k},30,1.2);")
    # 머리글
    hx = 960 + 48 + 150
    a(f"var ih=imp({js(str(WORK / 'head.png'))}); var Lh=comp.layers.add(ih); Lh.transform.anchorPoint.setValue([0,40]);")
    a(f"keys(Lh.transform.position,[[{s(T_OPEN - 0.15)},[{hx + 40},{HEAD_Y}]],[{s(T_OPEN + 0.15)},[{hx},{HEAD_Y}]],[{s(T_BACK + 0.10)},[{hx},{HEAD_Y}]],[{s(T_BACK + 0.46)},[{hx + 1060},{HEAD_Y}]]]); ez(Lh.transform.position);")
    a(f"keys(Lh.transform.opacity,[[{s(T_OPEN - 0.15)},0],[{s(T_OPEN + 0.1)},100]]);")
    # 카드
    for k, (t, _, _) in enumerate(ITEMS):
        x, y = slot(k)
        a(f"var ic{k}=imp({js(str(WORK / f'card{k}.png'))}); var C{k}=comp.layers.add(ic{k});")
        a(f"var ih{k}=imp({js(str(WORK / f'cardhl{k}.png'))}); var G{k}=comp.layers.add(ih{k}); G{k}.blendingMode=BlendingMode.ADD;")
        for v in (f"C{k}", f"G{k}"):
            a(f"{v}.transform.position.setValue([{x:.1f},{y:.1f}]);")
        t = s(t)
        sk = [[t, [55, 55]], [t + 0.16, [106, 106]], [t + 0.26, [100, 100]]]
        for j, ts in enumerate(T_SHINE):
            u = s(ts) + k * 0.035
            sk += [[u, [100, 100]], [u + 0.11, [107, 107]], [u + 0.24, [100, 100]]]
        u = s(T_BACK) + k * 0.025
        sk += [[u, [100, 100]], [u + 0.18, [0, 0]]]
        a(f"keys(C{k}.transform.scale,{sk}); ez(C{k}.transform.scale); keys(G{k}.transform.scale,{sk}); ez(G{k}.transform.scale);")
        a(f"keys(C{k}.transform.opacity,[[{t - 0.01:.3f},0],[{t + 0.06:.3f},100]]);")
        a(f"keys(C{k}.transform.position,[[{t},[{x:.1f},{y + 24:.1f}]],[{t + 0.22:.3f},[{x:.1f},{y:.1f}]]]); ez(C{k}.transform.position);")
        a(f"keys(G{k}.transform.position,[[{t},[{x:.1f},{y + 24:.1f}]],[{t + 0.22:.3f},[{x:.1f},{y:.1f}]]]); ez(G{k}.transform.position);")
        gk = [[t - 0.01, 0], [t + 0.05, 90], [t + 0.35, 0]]
        for ts in T_SHINE:
            u = s(ts) + k * 0.035
            gk += [[u, 0], [u + 0.1, 100], [u + 0.3, 0]]
        a(f"keys(G{k}.transform.opacity,{[[round(p, 3), v] for p, v in gk]});")
        # 반짝 별(카드 모서리, 두 번)
        for j, ts in enumerate(T_SHINE):
            u = s(ts) + k * 0.035 + 0.04
            sx = x + (CW / 2 - 14) * (1 if (k + j) % 2 else -1)
            sy = y - CH / 2 + 18 if j == 0 else y + CH / 2 - LH - 10
            a(f"var is{k}{j}=imp({js(str(WORK / 'star.png'))}); var S{k}{j}=comp.layers.add(is{k}{j}); S{k}{j}.transform.position.setValue([{sx:.1f},{sy:.1f}]); S{k}{j}.blendingMode=BlendingMode.ADD;")
            a(f"keys(S{k}{j}.transform.scale,[[{u:.3f},[0,0]],[{u + 0.12:.3f},[70,70]],[{u + 0.3:.3f},[0,0]]]); keys(S{k}{j}.transform.rotation,[[{u:.3f},0],[{u + 0.3:.3f},90]]);")
    # 메타 로고: 빈 벽에 톡 → 판 머리로
    a(f"var il=imp({js(str(WORK / 'logo.png'))}); var Ll=comp.layers.add(il);")
    lx, ly = 960 + 48 + 64, HEAD_Y
    a(f"keys(Ll.transform.position,[[{s(T_SPREAD + 0.05)},[{LOGO_AT[0]},{LOGO_AT[1]}]],[{s(T_OPEN + 0.05)},[{lx},{ly}]],[{s(T_BACK + 0.10)},[{lx},{ly}]],[{s(T_BACK + 0.46)},[{lx + 1060},{ly}]]]); ez(Ll.transform.position);")
    a(f"keys(Ll.transform.scale,[[{s(T_LOGO)},[0,0]],[{s(T_LOGO + 0.14)},[112,112]],[{s(T_LOGO + 0.24)},[100,100]],[{s(T_SPREAD + 0.05)},[100,100]],[{s(T_OPEN + 0.05)},[24,24]]]); ez(Ll.transform.scale);")
    a(f"keys(Ll.transform.opacity,[[{s(T_LOGO) - 0.01:.3f},0],[{s(T_LOGO + 0.06)},100]]); glow(Ll,20,0.5);")
    a(f"var rq=app.project.renderQueue.items.add(comp); var om=rq.outputModule(1); om.applyTemplate({js('고품질')}); om.file=new File({js(str(out_mov))});")
    a("log('ok bisa01'); })();")
    return "\n".join(L)


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
    OUT.mkdir(parents=True, exist_ok=True)
    dst = OUT / "01_메타로고·업종카드_2.00~.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mov), "-c:v", "libx264", "-crf", "14", "-preset", "slow", "-pix_fmt", "yuv420p", "-an", str(dst)], check=True)
    return dst


if __name__ == "__main__":
    dst = build()
    print(dst)
    sys.path.insert(0, str(config.TOOLS))
    import lec_xml
    lec_xml.V_TRACK = 2
    print(lec_xml.write(OUT / "01_메타로고·업종카드_배치.xml", "빡이사DB_01_메타카드", dst, DUR, T0, [], 59.94, tag="bs01"))
