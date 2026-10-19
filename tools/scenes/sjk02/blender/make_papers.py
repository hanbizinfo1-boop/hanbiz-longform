r"""책상 종이 텍스처 굽기 — papers.html 을 Chrome 으로 찍어 _tmp/sjk02/blender/tex/<이름>.png (1000×1414).

    py -3.11 tools/scenes/sjk02/blender/make_papers.py [이름 …]
이름을 안 주면 전부. 이름 = SHEETS 의 열쇠.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "tools"))
import config as C  # noqa: E402

OUT = ROOT / "_tmp" / "sjk02" / "blender" / "tex"
SHEETS = {f"menuA{i}": f"k=menu&i={i}" for i in range(10)}
SHEETS.update({
    "menuB": "k=menu&i=10&b=1",
    "menuB_mk": "k=menu&i=10&b=1&mk=1",
    "menuB_mk_nm0": "k=menu&i=10&b=1&mk=1&nm=0",
    "reviewA": "k=review&i=0",
    "reviewB": "k=review&i=0&b=1",
    "reviewB_nm0": "k=review&i=0&b=1&nm=0",
    "newsB": "k=news&i=0",
    "newsB_nm0": "k=news&i=0&nm=0",
    "boardB": "k=board",
    "boardB_nm0": "k=board&nm=0",
    "guest": "k=guest",
})
# 한 달 쌓이면 — 날짜만 다른 종이 더미
for j, d in enumerate(["9. 22.", "9. 25.", "9. 29.", "10. 2.", "10. 6.", "10. 9.", "10. 13.", "10. 16."]):
    kind = ["review", "news", "menu", "review"][j % 4]
    SHEETS[f"pile{j}"] = f"k={kind}&i={10 if kind == 'menu' else j % 4}&b=1&mk=1&d=2026. {d}"


def main():
    names = sys.argv[1:] or list(SHEETS)
    OUT.mkdir(parents=True, exist_ok=True)
    prof = OUT.parent / "chrome-prof"
    page = (HERE / "papers.html").as_uri()
    for n in names:
        out = OUT / f"{n}.png"
        subprocess.run([str(C.CHROME), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                        f"--user-data-dir={prof}", "--window-size=1000,1414", "--virtual-time-budget=15000",
                        f"--screenshot={out}", f"{page}?{SHEETS[n]}"], check=True, capture_output=True)
        print("ok", n, flush=True)


if __name__ == "__main__":
    main()
