# -*- coding: utf-8 -*-
r"""클로드 디자인(Design 캔버스) 아트보드 → 애펙 레이어 PNG (2026-10-06, 클라이언트 «클로드 디자인을 조합해서 영상미»).

    python design_layers.py <아트보드.dc.html | .html> <출력 폴더> [--자산 <blob→로컬 json>] [--크기 1920x1080]
      → <출력>/_all.png(완성 모습) · _base.png(레이어 밖 바탕) · <레이어>.png … · layers.json

흐름: 캔버스에서 디자인(사장님·클라이언트가 보고 댓글·직접 수정) → 아트보드 원본을 `Artifact read`로 받아 → 이 도구로
레이어마다 투명 PNG(화면 전체 크기, 제자리) → 애펙 JSX 는 `ae_lines()`로 레이어를 깔고 움직임만 건다.

아트보드 쓰는 규칙(이것만 지키면 된다)
  - 루트는 영상 크기 고정(1920×1080, `$preview` 같게). 움직일 덩어리마다 `data-layer="이름"`(영문·숫자·_).
    레이어 안의 레이어는 따로 떼어진다(부모 PNG 에서 빠짐) — 카드와 카드 안 글을 따로 움직일 때.
  - 레이어 순서 = 문서 순서(뒤 → 앞). 레이어 밖 요소는 `_base.png` 한 장(움직이지 않는 바탕).
  - `<sc-for>`·`<sc-if>`·`<dc-import>` 는 쓰지 않는다(이 변환기는 정적 마크업만 푼다). `{{값}}`은 data-props 기본값으로 채운다.
  - 이미지·글꼴은 캔버스에 올린 `/_blob/<id>` 그대로 두고, `--자산` json({"/_blob/<id>": "D:/…/파일.png"})으로 로컬 파일을 잇는다.
렌더: 크롬 헤드리스 `--default-background-color=00000000` → 투명 PNG.
"""

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[0]))   # tools/ (config.py)
import config  # noqa: E402
import html as H
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

CHROME = str(config.CHROME)


def to_plain(src, assets):
    """.dc.html → 크롬이 바로 그리는 평범한 html."""
    s = src
    s = re.sub(r'<script src="\./support\.js"></script>\s*', "", s)
    m = re.search(r"<script[^>]*data-dc-script[^>]*data-props='([^']*)'", s) or re.search(r"data-props='([^']*)'", s)
    props = {}
    if m:
        try:
            props = json.loads(H.unescape(m.group(1)))
        except json.JSONDecodeError:
            pass
    s = re.sub(r"<script[^>]*data-dc-script[\s\S]*?</script>", "", s)
    for bad in ("<sc-for", "<sc-if", "<dc-import"):
        if bad in s:
            print(f"경고: {bad}> 는 풀지 않는다 — 정적 마크업으로 바꿔 주세요")
    helmet = "\n".join(re.findall(r"<helmet>([\s\S]*?)</helmet>", s))
    s = re.sub(r"<helmet>[\s\S]*?</helmet>", "", s)
    s = s.replace("<x-dc>", "").replace("</x-dc>", "")
    defaults = {k: v.get("default") for k, v in props.items() if isinstance(v, dict) and "default" in v}
    s = re.sub(r"\{\{\s*([\w.]+)\s*\}\}", lambda mm: str(defaults.get(mm.group(1), "")), s)
    for blob, local in assets.items():
        s = s.replace(blob, Path(local).resolve().as_uri())
    base_css = "<style>html,body{margin:0;background:transparent !important;overflow:hidden}</style>"
    s = s.replace("</head>", helmet + base_css + "</head>", 1) if "</head>" in s else base_css + helmet + s
    pv = props.get("$preview") or {}
    return s, (int(pv.get("width", 0)) or None, int(pv.get("height", 0)) or None)


def layers_of(s):
    return list(dict.fromkeys(re.findall(r'data-layer="([A-Za-z0-9_]+)"', s)))


def shoot(page_html, out_png, w, h, tmp):
    tmp.write_text(page_html, encoding="utf-8")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--default-background-color=00000000",
                    f"--window-size={w},{h}", "--virtual-time-budget=4000", f"--screenshot={out_png}", tmp.resolve().as_uri()],
                   capture_output=True, timeout=120)
    if not Path(out_png).exists():
        raise SystemExit(f"렌더 실패: {out_png}")


def bbox(png):
    a = np.array(Image.open(png))[..., 3] > 8
    ys, xs = np.where(a)
    return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1] if len(xs) else None


def render(src_path, out_dir, assets=None, size=None):
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    plain, pv = to_plain(Path(src_path).read_text(encoding="utf-8"), assets or {})
    w, h = size or (pv[0] or 1920, pv[1] or 1080)
    names = layers_of(plain)
    tmp = out_dir / "_page.html"

    def with_css(css):
        return plain.replace("</head>", f"<style>{css}</style></head>", 1)
    shoot(plain, out_dir / "_all.png", w, h, tmp)
    shoot(with_css("[data-layer]{visibility:hidden !important}"), out_dir / "_base.png", w, h, tmp)
    info = []
    for n in names:
        css = (f"body *{{visibility:hidden !important}} [data-layer=\"{n}\"], [data-layer=\"{n}\"] *{{visibility:visible !important}}"
               f" [data-layer=\"{n}\"] [data-layer], [data-layer=\"{n}\"] [data-layer] *{{visibility:hidden !important}}")
        shoot(with_css(css), out_dir / f"{n}.png", w, h, tmp)
        info.append({"name": n, "png": f"{n}.png", "bbox": bbox(out_dir / f"{n}.png")})
    tmp.unlink()
    meta = {"size": [w, h], "base": "_base.png", "all": "_all.png", "layers": info}
    (out_dir / "layers.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"레이어 {len(info)}개 → {out_dir}")
    for x in info:
        print(f"  {x['name']:16s} {x['bbox']}")
    return meta


def ae_lines(layers_dir, js, prefix="L"):
    """애펙 JSX 줄 — 바탕 + 레이어를 문서 순서로 깔고, 기준점을 레이어 상자 가운데로(커지기·튕기기용).
    돌려주는 dict: 레이어 이름 → JSX 변수 이름. 움직임은 장면 도구가 이 변수에 keys()로 건다."""
    d = Path(layers_dir)
    meta = json.loads((d / "layers.json").read_text(encoding="utf-8"))
    L, var = [], {}
    L.append(f"var {prefix}_base=comp.layers.add(imp({js(str(d / meta['base']))}));")
    for i, x in enumerate(meta["layers"]):
        v = f"{prefix}{i}"
        var[x["name"]] = v
        L.append(f"var {v}=comp.layers.add(imp({js(str(d / x['png']))})); {v}.name={js(x['name'])};")
        if x["bbox"]:
            x0, y0, x1, y1 = x["bbox"]
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            L.append(f"{v}.transform.anchorPoint.setValue([{cx},{cy}]); {v}.transform.position.setValue([{cx},{cy}]);")
    return L, var, meta


if __name__ == "__main__":
    a = sys.argv
    assets = json.loads(Path(a[a.index("--자산") + 1]).read_text(encoding="utf-8")) if "--자산" in a else {}
    size = tuple(int(v) for v in a[a.index("--크기") + 1].split("x")) if "--크기" in a else None
    render(a[1], a[2], assets, size)
