# -*- coding: utf-8 -*-
r"""강의 «보조 패널» — 인물 전체화면 옆(오른쪽 모니터 자리)에 얹는 작은 정리 패널. 투명 1920×1080 PNG.

    python side_panel_render.py <보조패널.json> <출력폴더>

사장님 지시(2026-09-23):
  · 자체 자료를 전체화면으로 띄우면 화면이 계속 바뀌어 정신없다 → **인물 전체화면은 그대로, 말할 때 옆에 보조로**
  · 자료를 많이 넣지 말 것 — 정리해 주는 글자 · 짧은 표 · 지명이면 연상되는 그림(지도) 정도
  · **글자는 크게** (적더라도 크게) · 겹침 주의 · 정렬이 무질서하지 않게
규격:
  · 패널: 오른쪽 x 1192~1872 (폭 680) · 위 y 96 · 하단 자막(y 978~) 침범 금지 — 넘치면 오류로 멈춘다
  · 13~15강 카메라: 강사 x 350~1150, 오른쪽은 모니터(슬라이드가 안 읽힘) → 그 자리를 덮는다
  · 모든 패널이 같은 틀: 로고 머리 → 브랜드 띠 → 제목(50px) → 본문(항목 44px · 표 38px) · 왼쪽 정렬, 같은 여백
  · 패널 크기는 마지막 단계 기준으로 고정 — 항목이 쌓여도 패널이 튀지 않는다
종류: list(mark=num|check|icon) · table(head 선택, reveal=rows|cols) · lines · big · visual(img + list)
표기: «…» 주황 강조 · (O) 파랑 O · (X) 빨강 ✕
출력: NN_이름_K.png (K = 쌓인 단계) + _index.json (패널 실측 박스 포함)
"""

import html
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from card_render import CHROME, NAVY, BLUE, ORANGE, RED, font_url, make_logo  # noqa: E402

SUB_TOP = 970          # 자막 박스 윗선 — 패널은 이 위에서 끝나야 한다


def e(s):
    s = html.escape(str(s)).replace("\n", "<br>")
    s = s.replace("«", "<em>").replace("»", "</em>")
    return s.replace("(O)", '<b class="o">O</b>').replace("(X)", '<b class="x">✕</b>')


def h(i, shown):
    return " hid" if shown is not None and i >= shown else ""


def mark(c, i, it, base):
    m = c.get("mark", "num")
    if m == "num":
        return f'<span class="mk num">{i + 1}</span>'
    if m == "check" or it.get("icon") == "check":
        ok = it.get("ok", True)
        mk = f'<span class="mk {"ok" if ok else "no"}">{"✓" if ok else "✕"}</span>'
        return f'<span class="slot">{mk}</span>' if m == "icon" else mk     # 아이콘 줄과 글자 시작선을 맞춘다
    if m == "none":
        return ""
    if m == "icon":
        return f'<img class="ic" src="{(base / it["icon"]).resolve().as_uri()}">'
    return ""


def items_html(c, s, base):
    out = []
    for i, it in enumerate(c["items"]):
        d = f'<div class="ds">{e(it["d"])}</div>' if it.get("d") else ""
        out.append(f'<div class="it{h(i, s)}">{mark(c, i, it, base)}<div><div class="tx">{e(it["t"])}</div>{d}</div></div>')
    return "".join(out)


def p_list(c, s, base):
    note = f'<div class="nt{h(len(c["items"]), s)}">{e(c["note"])}</div>' if c.get("note") else ""
    return f'<div class="its">{items_html(c, s, base)}</div>{note}'


def p_table(c, s, base):
    cols = c.get("reveal") == "cols"
    head = c.get("head")
    n = len(c["rows"][0])
    widths = ["34%"] + [f"{66 / (n - 1):.2f}%"] * (n - 1) if n > 2 else ["38%", "62%"]
    cg = "".join(f'<col style="width:{w}">' for w in widths)
    hh = ""
    if head:
        hh = "<tr class='hr'>" + "".join(f'<th class="{h(j - 1, s).strip() if cols and j else ""}">{e(x)}</th>'
                                         for j, x in enumerate(head)) + "</tr>"
    body = ""
    for i, r in enumerate(c["rows"]):
        rc = "" if cols else h(i, s).strip()
        body += f'<tr class="{rc}">' + "".join(
            f'<td class="{"k" if j == 0 else "v"}{h(j - 1, s) if cols and j else ""}">{e(x)}</td>' for j, x in enumerate(r)) + "</tr>"
    note = f'<div class="nt{h(len(c["rows"]) - 1, s) if not cols else ""}">{e(c["note"])}</div>' if c.get("note") else ""
    return f'<table class="tb{" c3" if n > 2 else ""}"><colgroup>{cg}</colgroup>{hh}{body}</table>{note}'


def p_lines(c, s, base):
    return "".join(f'<div class="ln l{i}{h(i, s)}">{e(t)}</div>' for i, t in enumerate(c["lines"]))


def p_big(c, s, base):
    return (f'<div class="bg"><div class="bk">{e(c["kicker"])}</div>'
            f'<div class="bv{h(1, s)}">{e(c["value"])}</div><div class="bc{h(1, s)}">{e(c["caption"])}</div></div>')


def p_visual(c, s, base):
    return (f'<div class="vis"><img class="map" src="{(base / c["img"]).resolve().as_uri()}">'
            f'<div class="its">{items_html(c, s, base)}</div></div>')


PANEL = {"list": p_list, "table": p_table, "lines": p_lines, "big": p_big, "visual": p_visual}

CSS = """
@font-face{font-family:G;src:url('%(gb)s');font-weight:700}
@font-face{font-family:G;src:url('%(gm)s');font-weight:500}
@font-face{font-family:N;src:url('%(noto)s');font-weight:100 900}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1920px;height:1080px;overflow:hidden;background:transparent}
body{font-family:N,sans-serif;color:#1B2340;word-break:keep-all}
.hid{visibility:hidden}
em{font-style:normal;color:%(orange)s}
b.o{color:%(blue)s;font-family:G;font-weight:700}
b.x{color:%(red)s;font-weight:900}
.pn{position:absolute;left:1192px;top:96px;width:680px;
 background:rgba(255,255,255,.96);border-radius:28px;padding:30px 40px 40px;
 box-shadow:0 18px 50px rgba(0,0,0,.32),0 0 0 1px rgba(11,42,122,.06)}
.hd{display:flex;align-items:center;justify-content:space-between;height:40px}
.hd img{height:34px}
.tag{font-family:G;font-weight:500;font-size:20px;color:#fff;background:%(navy)s;padding:8px 16px;border-radius:20px}
.bar{height:5px;border-radius:3px;margin:18px 0 26px;
 background:linear-gradient(90deg,%(navy)s 0,%(blue)s 45%%,%(orange)s 80%%,%(red)s 100%%)}
h1{font-family:G;font-weight:700;font-size:50px;line-height:1.2;color:%(navy)s;letter-spacing:-1px}
.bd{margin-top:26px}
.bd.notitle{margin-top:4px}
.its{display:flex;flex-direction:column;gap:16px}
.it{display:flex;align-items:center;gap:22px;background:#F2F5FB;border-radius:18px;padding:20px 24px;min-height:100px}
.mk{flex:none;width:60px;height:60px;border-radius:16px;color:#fff;font-family:G;font-weight:700;font-size:32px;
 display:flex;align-items:center;justify-content:center}
.mk.num{background:linear-gradient(135deg,%(navy)s,%(blue)s)}
.it:nth-child(even) .mk.num{background:linear-gradient(135deg,%(orange)s,%(red)s)}
.mk.ok{background:%(blue)s;border-radius:50%%;font-size:36px}
.mk.no{background:%(red)s;border-radius:50%%;font-size:34px}
.slot{flex:none;width:96px;display:flex;justify-content:center}
.ic{flex:none;width:96px;height:96px;object-fit:contain;border-radius:14px;background:#fff}
.tx{font-family:G;font-weight:700;font-size:44px;line-height:1.2;color:%(navy)s;letter-spacing:-.5px}
.ds{font-size:28px;font-weight:600;color:#56607E;margin-top:6px}
.nt{margin-top:22px;font-family:G;font-weight:700;font-size:38px;color:%(navy)s;text-align:center;
 background:#FFF3E6;border-radius:18px;padding:18px 20px}
table.tb{width:100%%;border-collapse:separate;border-spacing:0 12px;margin-top:-12px;table-layout:fixed}
.tb th{font-family:G;font-weight:700;font-size:34px;color:#fff;background:%(navy)s;padding:14px 10px;text-align:center}
.tb th:first-child{background:transparent}
.tb th:nth-child(2){border-radius:14px 0 0 14px}.tb th:last-child{border-radius:0 14px 14px 0}
.tb td{font-family:G;font-weight:700;font-size:38px;padding:22px 20px;background:#F2F5FB;line-height:1.2}
.tb td.k{color:#56607E;font-size:32px;border-radius:16px 0 0 16px;background:#E6EBF6}
.tb td.v{color:%(navy)s}
.tb td:last-child{border-radius:0 16px 16px 0}
.tb.c3 td.v{text-align:center;font-size:36px}
.ln{font-family:G;font-weight:700;line-height:1.25;letter-spacing:-1px}
.ln.l0{font-size:56px;color:%(navy)s}
.ln.l1{font-size:56px;color:%(navy)s;margin-top:22px;padding-top:22px;border-top:4px solid #EEF1F8}
.bg{text-align:center;padding:6px 0 4px}
.bk{font-family:G;font-weight:500;font-size:40px;color:#56607E}
.bv{font-family:G;font-weight:700;font-size:130px;color:%(orange)s;letter-spacing:-4px;line-height:1.1;margin:10px 0}
.bc{font-family:G;font-weight:700;font-size:56px;color:%(navy)s}
.vis{display:flex;gap:24px;align-items:center}
.vis .map{flex:none;width:200px}
.vis .its{flex:1}
.vis .it{min-height:0;padding:18px 20px}
.vis .tx{font-size:38px}
"""


def page(card, lecture, logo_uri, shown, base):
    css = CSS % dict(gb=font_url("GmarketSansBold.otf"), gm=font_url("GmarketSansMedium.otf"),
                     noto=font_url("NotoSansKR-VF.ttf"), navy=NAVY, blue=BLUE, orange=ORANGE, red=RED)
    title = f'<h1>{e(card["title"])}</h1>' if card.get("title") else ""
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head><body>'
            f'<div class="pn"><div class="hd"><img src="{logo_uri}"><span class="tag">{e(lecture)}</span></div>'
            f'<div class="bar"></div>{title}<div class="bd{"" if title else " notitle"}">'
            f'{PANEL[card["type"]](card, shown, base)}</div></div></body></html>')


def main():
    src = Path(sys.argv[1])
    spec = json.loads(src.read_text(encoding="utf-8"))
    out = Path(sys.argv[2])
    assets = out / "_assets"
    assets.mkdir(parents=True, exist_ok=True)
    logo = make_logo(assets).resolve().as_uri()
    index, bad = [], []
    for c in spec["cards"]:
        stem = f'{c["no"]:02d}_{c["name"]}'
        for k, t in enumerate(c["build"], 1):
            name = f"{stem}_{k}"
            hp = assets / f"{name}.html"
            hp.write_text(page(c, spec["lecture"], logo, k, src.parent), encoding="utf-8")
            png = out / f"{name}.png"
            subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                            "--force-device-scale-factor=1", "--window-size=1920,1080",
                            "--default-background-color=00000000", "--allow-file-access-from-files",
                            f"--screenshot={png.resolve()}", hp.resolve().as_uri()],
                           check=True, capture_output=True)
            a = np.array(Image.open(png))[..., 3]
            ys, xs = np.nonzero(a > 200)
            box = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
            if box[3] >= SUB_TOP:
                bad.append(f"{name}: 패널 아래끝 y={box[3]} (자막 {SUB_TOP} 침범)")
            index.append({"file": png.name, "card": c["no"], "step": k, "at": t,
                          "from": c["from"], "until": c["until"], "box": box})
            print(f"  {png.name}  {box}")
    (out / "_index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    if bad:
        print("\n".join(["자막 자리 침범:"] + bad))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
