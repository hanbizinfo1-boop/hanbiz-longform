# -*- coding: utf-8 -*-
r"""강의 «자료 카드» — 자막 내용에 맞춘 정리 화면을 1920×1080 PNG 로 굽는다.

    python card_render.py <cards.json> <출력폴더>

  · 한국중소기업비즈니스센터 로고(좌상단) + 강 이름 태그(우상단) + 브랜드 색 띠
  · 좌하단 원형 PIP(카메라) 자리와 하단 자막 자리는 비운다 — 편집 문법-전체.md §0 C 장면 위에 얹는다
  · HTML → Chrome 헤드리스 캡처 (글자 품질 때문에 PIL 로 그리지 않는다)

cards.json:
  {"lecture": "10강 · 중진공", "cards": [ {"no":1, "type":"define", ...}, ... ]}
type: define · compare · steps · numbers · checklist · summary  (필드는 아래 렌더 함수 참고)
글꼴: 제목 G마켓 산스 Bold · 본문 Pretendard · 숫자 G마켓 산스
"""

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[0]))   # tools/ (config.py)
import config  # noqa: E402

import html
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image
import numpy as np

CHROME = str(config.CHROME)
LOGO_SRC = config.LOGO_SRC
FONTS = config.WIN_FONTS.as_posix()
LOCAL_FONTS = Path.home() / "AppData/Local/Microsoft/Windows/Fonts"

NAVY, BLUE, ORANGE, RED = "#0B2A7A", "#2F5BD0", "#F28C1C", "#E8452C"


def font_url(name):
    for d in (LOCAL_FONTS, Path(FONTS)):
        p = d / name
        if p.exists():
            return p.as_uri()
    return ""


def make_logo(assets: Path):
    """흰 배경 로고 → 투명 PNG. 원본은 건드리지 않는다."""
    out = assets / "logo_full.png"
    if out.exists():
        return out
    im = np.array(Image.open(LOGO_SRC).convert("RGBA")).astype(np.float32)
    mn = im[..., :3].min(axis=2)
    a = np.where(mn > 246, 0, np.clip((255 - mn) / 40, 0, 1))
    im[..., 3] = a * 255
    img = Image.fromarray(im.astype(np.uint8))
    img = img.crop(img.getbbox())
    img.save(out)
    h = img.size[1]
    sym = img.crop((0, 0, h, h))                    # 왼쪽 원형 심볼
    sym.crop(sym.getbbox()).save(assets / "logo_symbol.png")
    return out


def e(s):
    """줄바꿈 유지 + «강조» 는 주황으로."""
    s = html.escape(str(s)).replace("\n", "<br>")
    return s.replace("«", '<em>').replace("»", "</em>")


def cls(i, shown):
    return " hid" if shown is not None and i >= shown else ""


def r_define(c, shown=None):
    chips = "".join(f'<div class="chip{cls(i, shown)}">{e(k)}</div>' for i, k in enumerate(c.get("keywords", [])))
    return (f'<div class="kicker">{e(c.get("kicker", ""))}</div>'
            f'<div class="big">{e(c["term"])}</div>'
            f'<div class="lead">{e(c["body"])}</div><div class="chips">{chips}</div>')


def r_compare(c, shown=None):
    head = "".join(f"<th>{e(h)}</th>" for h in c["head"])
    rows = "".join(f'<tr class="{cls(i, shown).strip()}">' + "".join(f"<td>{e(x)}</td>" for x in r) + "</tr>"
                   for i, r in enumerate(c["rows"]))
    note = f'<div class="note">{e(c["note"])}</div>' if c.get("note") else ""
    return f'<table class="cmp"><tr>{head}</tr>{rows}</table>{note}'


def r_steps(c, shown=None):
    parts = []
    for i, s in enumerate(c["steps"]):
        if i:
            parts.append(f'<div class="arrow{cls(i, shown)}">›</div>')
        parts.append(f'<div class="step{cls(i, shown)}"><div class="sn">{i + 1:02d}</div>'
                     f'<div class="st">{e(s["t"])}</div><div class="sd">{e(s.get("d", ""))}</div></div>')
    note = f'<div class="note">{e(c["note"])}</div>' if c.get("note") else ""
    return f'<div class="steps">{"".join(parts)}</div>{note}'


def r_numbers(c, shown=None):
    boxes = "".join(f'<div class="num{cls(i, shown)}"><div class="nl">{e(n["label"])}</div>'
                    f'<div class="nv">{e(n["value"])}</div><div class="nd">{e(n.get("desc", ""))}</div></div>'
                    for i, n in enumerate(c["items"]))
    note = f'<div class="note">{e(c["note"])}</div>' if c.get("note") else ""
    return f'<div class="nums">{boxes}</div>{note}'


def r_checklist(c, shown=None):
    items = "".join(f'<div class="ck{cls(n, shown)}"><span class="ok{"" if i.get("ok", True) else " no"}">{"✓" if i.get("ok", True) else "✕"}</span>'
                    f'<div><div class="ct">{e(i["t"])}</div><div class="cd">{e(i.get("d", ""))}</div></div></div>'
                    for n, i in enumerate(c["items"]))
    return f'<div class="cks">{items}</div>'


def r_summary(c, shown=None):
    items = "".join(f'<div class="sm{cls(i, shown)}"><div class="smn">{i + 1}</div><div class="smt">{e(t)}</div></div>'
                    for i, t in enumerate(c["items"]))
    return f'<div class="sms">{items}</div>'


def r_versus(c, shown=None):
    def side(x, i):
        rows = "".join(f'<div class="vr"><span>{e(k)}</span><b>{e(v)}</b></div>' for k, v in x["rows"])
        return (f'<div class="vs-side{cls(i, shown)} {x.get("tone", "")}"><div class="vt">{e(x["label"])}</div>'
                f'{rows}<div class="vf">{e(x.get("foot", ""))}</div></div>')
    a, b = c["sides"]
    note = f'<div class="note{cls(2, shown)}">{e(c["note"])}</div>' if c.get("note") else ""
    return f'<div class="vs">{side(a, 0)}<div class="vsx{cls(1, shown)}">VS</div>{side(b, 1)}</div>{note}'


def r_statement(c, shown=None):
    lines = "".join(f'<div class="stl{cls(i, shown)} l{i}">{e(t)}</div>' for i, t in enumerate(c["lines"]))
    return f'<div class="stm">{lines}</div>'


RENDER = {"versus": r_versus, "statement": r_statement, "define": r_define, "compare": r_compare, "steps": r_steps,
          "numbers": r_numbers, "checklist": r_checklist, "summary": r_summary}

CSS = """
@font-face{font-family:G;src:url('%(gb)s');font-weight:700}
@font-face{font-family:G;src:url('%(gm)s');font-weight:500}
@font-face{font-family:P;src:url('%(pb)s');font-weight:700}
@font-face{font-family:N;src:url('%(noto)s');font-weight:100 900}
*{margin:0;padding:0;box-sizing:border-box}
.hid{visibility:hidden}
html,body{width:1920px;height:1080px;overflow:hidden}
body{background:#F6F7FB;font-family:N,sans-serif;color:#1B2340;position:relative}
body:before{content:"";position:absolute;inset:0;
 background:radial-gradient(1200px 600px at 100%% 0%%,#E6ECFB 0,transparent 60%%),
            radial-gradient(900px 500px at 0%% 100%%,#FDEBDD 0,transparent 55%%)}
.wm{position:absolute;right:-60px;bottom:-80px;width:520px;opacity:.06}
.hdr{position:absolute;left:84px;right:84px;top:48px;height:64px;display:flex;align-items:center;justify-content:space-between}
.hdr img{height:52px}
.tag{font-family:G;font-weight:500;font-size:26px;color:#fff;background:%(navy)s;padding:10px 26px;border-radius:40px}
.bar{position:absolute;left:84px;right:84px;top:132px;height:5px;border-radius:3px;
 background:linear-gradient(90deg,%(navy)s 0,%(blue)s 45%%,%(orange)s 80%%,%(red)s 100%%)}
.wrap{position:absolute;left:120px;right:120px;top:176px;bottom:150px;display:flex;flex-direction:column}
h1{font-family:G;font-weight:700;font-size:74px;color:%(navy)s;letter-spacing:-1px;line-height:1.15}
h1 em,.big em,.lead em,td em,.st em,.nv em,.ct em,.smt em,.note em{font-style:normal;color:%(orange)s}
.sub{font-weight:500;font-size:34px;color:#56607E;margin-top:14px}
.sub em{font-style:normal;color:%(orange)s;font-weight:700}
.body{flex:1;display:flex;flex-direction:column;justify-content:center;padding-bottom:40px}
.kicker{font-family:G;font-weight:500;font-size:30px;color:%(blue)s}
.big{font-family:G;font-weight:700;font-size:96px;color:%(navy)s;margin:10px 0 18px}
.lead{font-size:44px;font-weight:600;line-height:1.45}
.chips{display:flex;gap:18px;margin-top:40px;flex-wrap:wrap}
.chip{font-weight:700;font-size:32px;padding:14px 30px;border-radius:14px;background:#fff;border:3px solid %(blue)s;color:%(navy)s}
.chip:nth-child(2n){border-color:%(orange)s}
table.cmp{border-collapse:separate;border-spacing:0;width:100%%;background:#fff;border-radius:22px;overflow:hidden;
 box-shadow:0 10px 30px rgba(11,42,122,.10)}
.cmp th{background:%(navy)s;color:#fff;font-family:G;font-weight:500;font-size:34px;padding:24px 30px;text-align:left}
.cmp th:last-child,.cmp td:last-child{border-left:0}
.cmp td{font-size:38px;font-weight:600;padding:26px 30px;border-top:2px solid #E6E9F2}
.cmp tr:nth-child(odd) td{background:#FAFBFE}
.note{margin-top:26px;font-size:30px;color:#56607E;font-weight:500}
.steps{display:flex;align-items:stretch;gap:14px}
.step{flex:1;background:#fff;border-radius:22px;padding:30px 26px;box-shadow:0 10px 30px rgba(11,42,122,.10);border-top:8px solid %(blue)s}
.step:last-child{border-top-color:%(orange)s}
.sn{font-family:G;font-weight:700;font-size:30px;color:%(blue)s}
.step:last-child .sn{color:%(orange)s}
.st{font-family:G;font-weight:700;font-size:40px;color:%(navy)s;margin:12px 0;line-height:1.25}
.sd{font-size:28px;color:#56607E;line-height:1.45;font-weight:500}
.arrow{align-self:center;font-family:G;font-size:70px;color:#B7C0D8}
.nums{display:flex;gap:30px}
.num{flex:1;background:#fff;border-radius:24px;padding:38px 40px;box-shadow:0 10px 30px rgba(11,42,122,.10)}
.nl{font-family:G;font-weight:500;font-size:32px;color:%(blue)s}
.nv{font-family:G;font-weight:700;font-size:92px;color:%(navy)s;margin:14px 0 8px;letter-spacing:-2px}
.nd{font-size:30px;color:#56607E;font-weight:500;line-height:1.4}
.cks{display:flex;flex-direction:column;gap:22px}
.ck{display:flex;align-items:center;gap:28px;background:#fff;border-radius:20px;padding:26px 34px;box-shadow:0 8px 24px rgba(11,42,122,.08)}
.ok.no{background:%(red)s}
.ok{flex:none;width:64px;height:64px;border-radius:50%%;background:%(blue)s;color:#fff;font-size:38px;font-weight:800;
 display:flex;align-items:center;justify-content:center}
.ct{font-family:G;font-weight:700;font-size:40px;color:%(navy)s}
.cd{font-size:28px;color:#56607E;font-weight:500;margin-top:6px}
.sms{display:grid;grid-template-columns:1fr 1fr;gap:24px}
.sm{display:flex;gap:24px;align-items:center;background:#fff;border-radius:20px;padding:30px 32px;box-shadow:0 8px 24px rgba(11,42,122,.08)}
.smn{flex:none;width:62px;height:62px;border-radius:16px;background:linear-gradient(135deg,%(navy)s,%(blue)s);color:#fff;
 font-family:G;font-weight:700;font-size:34px;display:flex;align-items:center;justify-content:center}
.sm:nth-child(4n+2) .smn,.sm:nth-child(4n+3) .smn{background:linear-gradient(135deg,%(orange)s,%(red)s)}
.smt{font-size:36px;font-weight:700;line-height:1.35}
.vs{display:flex;align-items:stretch;gap:26px}
.vs-side{flex:1;background:#fff;border-radius:24px;padding:34px 40px;box-shadow:0 10px 30px rgba(11,42,122,.10);border-top:10px solid %(blue)s}
.vs-side.warm{border-top-color:%(orange)s}
.vt{font-family:G;font-weight:700;font-size:44px;color:%(navy)s;margin-bottom:18px}
.vr{display:flex;justify-content:space-between;font-size:34px;padding:14px 0;border-bottom:2px solid #EEF0F6}
.vr span{color:#56607E;font-weight:500}.vr b{font-weight:800;color:#1B2340}
.vr b em,.vf em{font-style:normal;color:%(orange)s}
.vf{margin-top:20px;font-family:G;font-weight:700;font-size:34px;color:%(red)s}
.vsx{align-self:center;font-family:G;font-weight:700;font-size:56px;color:%(orange)s}
.few .st{font-size:54px}.few .sd{font-size:36px}.few .sn{font-size:36px}.few .step{padding:44px 40px}
.few .ct{font-size:52px}.few .cd{font-size:34px}.few .ck{padding:36px 44px}.few .ok{width:80px;height:80px;font-size:46px}
.few .smt{font-size:46px}.few .sm{padding:40px 40px}.few .smn{width:76px;height:76px;font-size:40px}
.few .vt{font-size:54px}.few .vr{font-size:40px;padding:18px 0}.few .vf{font-size:40px}
.few .cmp td{font-size:44px;padding:32px 34px}.few .cmp th{font-size:38px}
.stm{display:flex;flex-direction:column;gap:30px}
.stl{font-family:G;font-weight:700;color:%(navy)s;line-height:1.25}
.stl.l0{font-size:84px}.stl.l1{font-size:60px;color:%(orange)s}.stl.l2{font-size:40px;color:#56607E;font-family:N;font-weight:600}
.stl em{font-style:normal;color:%(orange)s}
"""


def page(card, lecture, logo_uri, shown=None):
    css = CSS % dict(gb=font_url("GmarketSansBold.otf"), gm=font_url("GmarketSansMedium.otf"),
                     pb=font_url("Pretendard-Bold.otf"), noto=font_url("NotoSansKR-VF.ttf"),
                     navy=NAVY, blue=BLUE, orange=ORANGE, red=RED)
    sub = f'<div class="sub">{e(card["sub"])}</div>' if card.get("sub") else ""
    title = f'<h1>{e(card["title"])}</h1>' if card.get("title") else ""
    n = len(card.get("steps") or card.get("items") or card.get("rows") or card.get("sides") or [])
    few = " class=\"few\"" if 0 < n <= 3 else ""
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head><body{few}>'
            f'<img class="wm" src="{logo_uri.replace("logo_full", "logo_symbol")}"><div class="hdr"><img src="{logo_uri}"><div class="tag">{e(lecture)}</div></div><div class="bar"></div>'
            f'<div class="wrap">{title}{sub}<div class="body">{RENDER[card["type"]](card, shown)}</div></div>'
            '</body></html>')


def main():
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    assets = out / "_assets"
    assets.mkdir(exist_ok=True)
    logo = make_logo(assets).resolve().as_uri()
    index = []
    for c in spec["cards"]:
        stem = f'{c["no"]:02d}_{c.get("name", c["type"])}'
        # build: [항목1 시각, 항목2 시각, …] 이 있으면 항목이 하나씩 쌓이는 단계별 PNG 를 낸다
        builds = c.get("build") or [c.get("at")]
        for k, t in enumerate(builds, 1):
            shown = k if c.get("build") else None
            name = f"{stem}_{k}" if c.get("build") else stem
            h = assets / f"{name}.html"
            h.write_text(page(c, spec["lecture"], logo, shown), encoding="utf-8")
            png = out / f"{name}.png"
            subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                            "--force-device-scale-factor=1", "--window-size=1920,1080",
                            f"--screenshot={png.resolve()}", h.resolve().as_uri()],
                           check=True, capture_output=True)
            index.append({"file": png.name, "card": c["no"], "step": k, "at": t,
                          "cue": (c.get("cues") or [None] * len(builds))[k - 1], "end": c.get("end")})
            print(f"  {png.name}")
    (out / "_index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
