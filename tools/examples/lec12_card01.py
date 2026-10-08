# -*- coding: utf-8 -*-
r"""12강 자료 01 — «기관명 풀어보기» 포토카드(시안5-1 왼쪽띠) 애펙 연출 + «얹을 것만» XML (사장님 09-29 «1번으로 해서 진행»).

  python lec12_card01.py        → _tmp\out\12강\자료01_기관명풀어보기\
       01_기관명풀어보기.mov (1920×1080 알파, 29.97fps) · 효과음 wav 4개 · 12강_자료01.xml · 확인용 프레임

시각(«강의12강» 시퀀스 초) — 사장님 요청: 자막 나오는 타이밍에 맞춰 강조하며 글자가 생김
  9.977  자막006 «기관명을 조금 더 딥하게 보면은»      카드 등장 + «기관명 풀어보기 / 중소벤처기업진흥공단»
  12.112 자막007 «중소기업이고 벤처기업을 지원해 준다»  «1. 중소기업 · 벤처기업»
  15.165 자막008 «즉, 기술성 있는 기업들을»            «2. 기술성 있는 기업»
  16.783 자막009 «우대해서 … 기관이 중진공입니다»       «우대 지원»
  18.20  그 자막 안 «중진공» 말하는 순간(받아쓰기)       «= 중진공» 쾅
  19.469 자막010 (다음 주제)                          카드 퇴장
색(09-29 사장님): 노랑 = «기관명 풀어보기»·«우대 지원»·«중진공», 나머지 전부 흰색. «일반 지원» 줄은 뺌(«잘못 넣었네»). 로고 76px
효과음(8강 문법, overlay_xml): 카드 등장 = 종이소리 −5dB · 항목 = 띠딩2 −4dB · 작은 항목 = 마우스클릭 0dB · 핵심 = 도장 0dB
"""

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))   # tools/ (config.py)
import config  # noqa: E402
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(config.TOOLS))
import photocard_drafts2 as P  # noqa: E402
import photocard_drafts3 as P3  # noqa: E402
import rf3_ae as AE  # noqa: E402

OUT = (config.WORK / "out" / "12강" / "자료01_기관명풀어보기")
WORK = (config.WORK / "out" / "12강" / "ae01")      # 애펙 작업 폴더(영문 경로가 안전하지만 기존 모듈도 한글 경로로 돌았다)
FPS = 29.97
T0, T_END = 9.977, 19.469
EV = dict(card=0.0, l1=12.112 - T0, l2=15.165 - T0, l2b=16.783 - T0, fin=18.20 - T0, out=T_END - T0)
DUR = EV["out"] + 0.35
SFX_DIR = (config.SFX_LIB_OWNER / "효과음")
SFX = [(EV["card"], "종이소리 화면전환.mp3", -5), (EV["l1"], "2. 띠딩2.mp3", -4), (EV["l2"], "2. 띠딩2.mp3", -4),
       (EV["l2b"], "마우스 클릭.mp3", 0), (EV["fin"], "도장.mp3", 0)]
X0, CW, CH = 48, P.CW, P.CH


def text_layers(pad):
    """시안5-1 과 같은 자리·글꼴로 글자 조각을 따로 그린다(카드+그림자 캔버스 크기)."""
    Y, Wt = P.Y_, P.W_
    items = [
        ("label", (X0, 170), [("기관명 풀어보기", Y)], P.F(P.GM, 28), 2),
        ("title", (X0, 220), [("중소벤처기업진흥공단", Wt)], P.F(P.GB, 46), 3),
        ("l1a", (X0, 312), [("1. ", Wt), ("중소기업 · 벤처기업", Wt)], P.F(P.GB, 40), 3),
        ("l2a", (X0, 384), [("2. 기술성 있는 기업", Wt)], P.F(P.GB, 40), 3),
        ("l2b", (X0 + 44, 440), [("우대 지원", Y)], P.F(P.GB, 34), 2),
        ("fin", (X0, 518), [("= ", Wt), ("중진공", Y)], P.F(P.GB, 64), 4),
    ]
    out = {}
    for name, (x, y), parts, font, sw in items:
        im = Image.new("RGBA", (CW + 2 * pad, CH + 2 * pad), (0, 0, 0, 0))
        P.say(ImageDraw.Draw(im), (x + pad, y + pad), parts, font, sw)
        f = WORK / f"t_{name}.png"
        im.save(f)
        out[name] = (f, im.getbbox())
    # «기술성» 만 따로(톡 튀는 강조)
    im = Image.new("RGBA", (CW + 2 * pad, CH + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = X0 + pad + d.textlength("2. ", font=P.F(P.GB, 40)) + 1
    P.say(d, (x, 438 + pad), [("기술성", Y)], P.F(P.GB, 40), 3)
    f = WORK / "t_hi.png"
    im.save(f)
    out["hi"] = (f, im.getbbox())
    return out


def card_base():
    """카드(시안5-1, 글자 없이) + 그림자."""
    c, m = P3.base(24)
    bar = P.grad(10, CH, P3.BLUE, P3.ORANGE, vertical=True)
    c.paste(bar, (0, 0), m.crop((0, 0, 10, CH)))
    lg = P.logo("full", 76)            # 로고 크게 (09-29 «상단 한국중소기업 비즈니스센터 좀 더 크게») — 52 → 76px
    c.alpha_composite(lg, (40, 34))
    ImageDraw.Draw(c).line([(48, 136), (CW - 48, 136)], fill=(228, 232, 240), width=2)
    sh, pad = P.shadow(c, a=0.30)
    f = WORK / "card_base.png"
    sh.save(f)
    return f, pad, sh.size


def jsx(base, pad, size, tl, out_mov):
    js = AE.js
    L = []
    a = L.append
    bw, bh = size
    cx, cy = P.POS[0] - pad + bw / 2, P.POS[1] - pad + bh / 2          # 카드 캔버스 가운데(화면 좌표)
    a(f"(function(){{ var comp=app.project.items.addComp('card01',1920,1080,1,{DUR:.3f},{FPS}); comp.motionBlur=true;")
    # 카드: 아래에서 60px 올라오며 나타남(0.35초), 끝에 위로 30px 빠지며 사라짐
    a(f"var bi=imp({js(str(base))}); var cd=comp.layers.add(bi); cd.motionBlur=true;")
    a(f"keys(cd.transform.position,[[0,[{cx},{cy + 60}]],[0.35,[{cx},{cy}]],[{EV['out']:.3f},[{cx},{cy}]],[{EV['out'] + 0.3:.3f},[{cx},{cy - 30}]]]); ez(cd.transform.position);")
    a(f"keys(cd.transform.opacity,[[0,0],[0.25,100],[{EV['out']:.3f},100],[{EV['out'] + 0.3:.3f},0]]);")
    a(f"keys(cd.transform.scale,[[0,[96,96]],[0.35,[100,100]]]); ez(cd.transform.scale);")

    def reveal(name, t, dur=0.35, pop=None):
        f, bb = tl[name]
        acx, acy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
        a(f"var i_{name}=imp({js(str(f))}); var L_{name}=comp.layers.add(i_{name}); L_{name}.setParentWithJump(cd);"
          f"L_{name}.transform.anchorPoint.setValue([{acx},{acy}]); L_{name}.transform.position.setValue([{acx},{acy}]); L_{name}.inPoint={max(0, t - 0.02):.3f};")
        # 왼쪽 → 오른쪽 닦아 내며 글자가 생김
        a(f"var w_{name}=L_{name}.Effects.addProperty('ADBE Linear Wipe'); w_{name}.property('ADBE Linear Wipe-0002').setValue(270);"
          f"w_{name}.property('ADBE Linear Wipe-0003').setValue(40);"
          f"keys(w_{name}.property('ADBE Linear Wipe-0001'),[[{t:.3f},100],[{t + dur:.3f},0]]); ez(w_{name}.property('ADBE Linear Wipe-0001'));")
        a(f"keys(L_{name}.transform.opacity,[[{EV['out']:.3f},100],[{EV['out'] + 0.3:.3f},0]]);")   # v4: 부모 불투명도는 안 물려받는다 → 퇴장도 따로
        if pop:
            k0, t_ = pop
            a(f"keys(L_{name}.transform.scale,[[{t_:.3f},[100,100]],[{t_ + 0.12:.3f},[{k0},{k0}]],[{t_ + 0.3:.3f},[100,100]]]); ez(L_{name}.transform.scale);")

    reveal("label", 0.25, 0.3)
    reveal("title", 0.4, 0.45)
    reveal("l1a", EV["l1"])
    reveal("l2a", EV["l2"])
    reveal("l2b", EV["l2b"], 0.3)
    # «= 중진공» — 크게(170%) 떨어지며 쾅, 살짝 넘쳤다 제자리
    f, bb = tl["fin"]
    acx, acy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
    t = EV["fin"]
    a(f"var i_fin=imp({js(str(f))}); var L_fin=comp.layers.add(i_fin); L_fin.motionBlur=true; L_fin.setParentWithJump(cd);"
      f"L_fin.transform.anchorPoint.setValue([{acx},{acy}]); L_fin.transform.position.setValue([{acx},{acy}]); L_fin.inPoint={t:.3f};"
      f"keys(L_fin.transform.scale,[[{t:.3f},[170,170]],[{t + 0.14:.3f},[94,94]],[{t + 0.24:.3f},[103,103]],[{t + 0.34:.3f},[100,100]]]); ez(L_fin.transform.scale);"
      f"keys(L_fin.transform.opacity,[[{t:.3f},0],[{t + 0.08:.3f},100],[{EV['out']:.3f},100],[{EV['out'] + 0.3:.3f},0]]);")
    # 쾅 순간 카드 살짝 흔들림(2px, 0.15초)
    a(f"var sp=cd.transform.position; var n0=sp.nearestKeyIndex({EV['fin']:.3f});")
    a(f"cd.transform.position.setValueAtTime({t + 0.03:.3f},[{cx + 3},{cy}]); cd.transform.position.setValueAtTime({t + 0.07:.3f},[{cx - 3},{cy + 1}]);"
      f"cd.transform.position.setValueAtTime({t + 0.11:.3f},[{cx + 2},{cy}]); cd.transform.position.setValueAtTime({t + 0.16:.3f},[{cx},{cy}]);")
    a(f"var rq=app.project.renderQueue.items.add(comp); var om=rq.outputModule(1); om.applyTemplate({js('고품질(알파 포함)')}); om.file=new File({js(str(out_mov))});")
    a("log('ok card01'); })();")
    return "\n".join(L)


def build_ae():
    WORK.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    base, pad, size = card_base()
    tl = text_layers(pad)
    aep, jf, logf, mov = WORK / "card01.aep", WORK / "card01.jsx", WORK / "log.txt", WORK / "card01.mov"
    for f in (logf, mov, aep):
        if f.exists():
            f.unlink()
    body = [AE.HEAD.replace("%LOG%", AE.js(str(logf))), "app.newProject();",
            "try{" + jsx(base, pad, size, tl, mov) + "}catch(e){ log('ERR '+e.toString()+' line '+e.line); }",
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
    dst = OUT / "01_기관명풀어보기_v4.mov"          # v4(09-30): 퇴장 때 글자가 카드보다 늦게 남던 것 고침
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mov), "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", str(dst)], check=True)
    return dst


def build_sfx():
    out = []
    for t, fn, db in SFX:
        dst = OUT / f"효과_{t + T0:06.2f}s_{Path(fn).stem.replace(' ', '')}.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(SFX_DIR / fn), "-af", f"volume={db}dB", "-ar", "48000", "-ac", "2", str(dst)], check=True)
        out.append((t + T0, dst))
    return out


def fr(t):
    """시퀀스 29.97fps 프레임."""
    return int(round(t * 30000 / 1001))


def url(p):
    return "file://localhost/" + str(p).replace("\\", "/")


def build_xml(mov, sfx):
    RATE = "<rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>"
    n_mov = fr(DUR)
    s0 = fr(T0)
    vclip = (f'<clipitem id="v-card01v2"><name>{mov.name}</name><enabled>TRUE</enabled>{RATE}<start>{s0}</start><end>{s0 + n_mov}</end>'
             f'<in>0</in><out>{n_mov}</out><file id="f-card01v2"><name>{mov.name}</name><pathurl>{url(mov)}</pathurl>{RATE}<duration>{n_mov}</duration>'
             '<media><video><samplecharacteristics><width>1920</width><height>1080</height></samplecharacteristics></video></media></file></clipitem>')
    aitems = []
    for k, (t, f) in enumerate(sfx):
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)], capture_output=True, text=True).stdout)
        n = max(1, fr(dur))
        st = fr(t)
        aitems.append(f'<clipitem id="a-{k}"><name>{f.name}</name><enabled>TRUE</enabled>{RATE}<start>{st}</start><end>{st + n}</end><in>0</in><out>{n}</out>'
                      f'<file id="f-a{k}"><name>{f.name}</name><pathurl>{url(f)}</pathurl>{RATE}<duration>{n}</duration><media><audio><channelcount>2</channelcount></audio></media></file>'
                      '<sourcetrack><mediatype>audio</mediatype><trackindex>1</trackindex></sourcetrack></clipitem>')
    # 겹치는 효과음은 트랙을 나눈다
    tracks, ends = [], []
    for it, (t, f) in zip(aitems, sfx):
        for i, e in enumerate(ends):
            if e <= t:
                tracks[i].append(it)
                ends[i] = t + 1.5
                break
        else:
            tracks.append([it])
            ends.append(t + 1.5)
    end = s0 + n_mov + 60
    x = ('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n<xmeml version="4"><sequence id="seq-1"><name>12강_자료01_기관명풀어보기</name>'
         f"<duration>{end}</duration>{RATE}<media><video><format><samplecharacteristics>{RATE}<width>1920</width><height>1080</height>"
         f"<pixelaspectratio>square</pixelaspectratio></samplecharacteristics></format><track>{vclip}<enabled>TRUE</enabled></track></video>"
         "<audio>" + "".join(f"<track>{''.join(t)}<enabled>TRUE</enabled></track>" for t in tracks) + "</audio></media></sequence></xmeml>\n")
    p = OUT / "12강_자료01_기관명풀어보기_v3.xml"
    p.write_text(x, encoding="utf-8", newline="\n")
    return p


def check(mov):
    """강의 화면 위에 얹어 시각마다 한 장씩."""
    import json
    it = [i for i in json.load(open(str(config.ORIG_ROOT / "창근님-강의편집" / "자료카드" / "12강_확정본" / "12강_확정.json"), encoding="utf-8"))["items"] if i["track"] == "V2"]
    src = str(config.LECTURE_SHOOT / "16강.MP4")
    shots = []
    for t in (10.2, 10.9, 12.6, 14.9, 15.6, 17.3, 18.3, 18.9, 19.6):
        c = next(i for i in it if i["t0"] <= t < i["t1"])
        s = c["s0"] + (t - c["t0"])
        bg = WORK / f"bg_{t}.png"
        ov = WORK / f"ov_{t}.png"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{s:.3f}", "-i", src, "-frames:v", "1", "-vf", "scale=1920:1080", str(bg)], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t - T0:.3f}", "-i", str(mov), "-frames:v", "1", "-pix_fmt", "rgba", str(ov)], check=True)
        b = Image.open(bg).convert("RGBA")
        b.alpha_composite(Image.open(ov).convert("RGBA"))
        shots.append((t, b.convert("RGB").resize((640, 360))))
    sheet = Image.new("RGB", (640 * 3, 380 * 3), (20, 20, 24))
    for k, (t, im) in enumerate(shots):
        x, y = (k % 3) * 640, (k // 3) * 380
        sheet.paste(im, (x, y + 20))
        ImageDraw.Draw(sheet).text((x + 8, y + 2), f"{t:.1f}s", font=P.F(P.GB, 18), fill=(255, 255, 255))
    sheet.save(OUT / "확인_시각별_v3.png")


def main():
    mov = build_ae()
    if "--mov-only" in sys.argv:          # v4: 효과음·XML은 v3 그대로(프리미어에 들어가 있음) — mov 만 갈아 끼운다
        print("→", mov)
        return
    sfx = build_sfx()
    xml = build_xml(mov, sfx)
    check(mov)
    print("→", mov, xml)


if __name__ == "__main__":
    main()
