r"""강조 표시 시안 정지 프레임 → 장면별 비교판(현재 · A · B · C).

  py -3.11 tools/scenes/sjk02/sian/render_sian.py s37 s27 s28 s29 --cur <현재 캡처 폴더> --out 납품/성제관02_시안
현재 캡처는 <폴더>/<장면>.png 가 있으면 비교판 왼쪽 위에 넣는다.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "tools"))
import config as C  # noqa: E402

TMP = ROOT / "_tmp" / "sjk02" / "sian"
VARS = {"a": "A 콜아웃 — 지시선 + 아이콘 카드", "b": "B 스포트라이트 — 주변 누르고 큰 글", "c": "C 스티커 — 칼선 스티커 + 손그림"}
# 2차 시안(장면 이름 끝 n): B 방향 안에서 다시 세 가지 — 파일 이름은 D·E·F
VARS_N = {"a": ("D", "D 분할 — 두 가게를 두 판으로"), "b": ("E", "E 헤드라인 — 앞 솥만 밝히고 큰 제목"), "c": ("F", "F 글자 뒤로 — 큰 글이 솥 뒤에 걸침")}


def shot(url: str, out: Path, w=1920, h=1080):
    out.parent.mkdir(parents=True, exist_ok=True)
    prof = TMP / "chrome-prof"
    subprocess.run([str(C.CHROME), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                    f"--user-data-dir={prof}", f"--window-size={w},{h}", "--virtual-time-budget=4000",
                    f"--screenshot={out}", url], check=True, capture_output=True)
    if not out.exists():
        raise SystemExit(f"캡처 실패: {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scenes", nargs="+")
    ap.add_argument("--cur")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = (ROOT / a.out) if not Path(a.out).is_absolute() else Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for s in a.scenes:
        page = (HERE / f"{s}.html").as_uri()
        nv = s.endswith("n")
        lab = {v: (VARS_N[v][1] if nv else VARS[v]) for v in VARS}
        tag = {v: (VARS_N[v][0] if nv else v.upper()) for v in VARS}
        base, suffix = (s[:-1], "2") if nv else (s, "")
        # 장면 파일이 <meta name="sian-labels" content="a=…|b=…|c=…"> 를 가지면 그 이름표(스토리보드 판) — 파일 끝 글자 s
        m = re.search(r'<meta name="sian-labels" content="([^"]+)"', (HERE / f"{s}.html").read_text(encoding="utf-8"))
        if m:
            lab = dict(kv.split("=", 1) for kv in m.group(1).split("|"))
            tag = {v: f"보드{i + 1}" for i, v in enumerate(VARS)}
            base, suffix = s.rstrip("s"), "3"
        for v in VARS:
            shot(f"{page}?v={v}", TMP / f"{s}_{v}.png")
            print("ok", s, v, flush=True)
        cur = Path(a.cur) / f"{s}.png" if a.cur else None
        cells = [("현재", cur.as_uri() if cur and cur.exists() else "")] + [(lab[v], (TMP / f"{s}_{v}.png").as_uri()) for v in VARS]
        html = ['<!doctype html><html><head><meta charset="utf-8"><style>',
                '@font-face{font-family:P;src:url("' + (ROOT / "소재/fonts/Pretendard-Bold.otf").as_uri() + '")}',
                'body{margin:0;background:#15191D;font-family:P;color:#fff}.g{display:grid;grid-template-columns:960px 960px;gap:24px;padding:24px}',
                '.c{position:relative;width:960px;height:540px;background:#000;border-radius:10px;overflow:hidden}',
                '.c img{width:100%;height:100%;object-fit:contain}.c b{position:absolute;left:14px;top:12px;right:14px;padding:6px 14px;border-radius:8px;background:rgba(0,0,0,.72);font-size:22px;line-height:1.35}',
                '</style></head><body><div class="g">']
        for name, src in cells:
            html.append(f'<div class="c">{f"<img src={chr(34)}{src}{chr(34)}>" if src else ""}<b>{name}</b></div>')
        html.append("</div></body></html>")
        sp = TMP / f"{s}_sheet.html"
        sp.write_text("".join(html), encoding="utf-8")
        shot(sp.as_uri(), out / f"{base}_시안비교{suffix}.png", 1992, 1152)
        for v in VARS:
            (out / f"{base}_{tag[v]}.png").write_bytes((TMP / f"{s}_{v}.png").read_bytes())
        print("sheet", s, flush=True)


if __name__ == "__main__":
    main()
