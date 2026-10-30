r"""장면 렌더 검수용 시트 — 장면마다 고르게 n 프레임(기본 8)을 뽑아 4×2 한 장으로.
    py -3.11 tools/scenes/sjk03/review_sheet.py s01 s05 … [--n 8]  → _tmp/sjk03/review/<장면>_rv.jpg
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REN, OUT = ROOT / "_tmp/sjk03/render", ROOT / "_tmp/sjk03/review"


def dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)], capture_output=True, text=True)
    return float(r.stdout.strip())


def main():
    av = sys.argv[1:]
    args = [a for i, a in enumerate(av) if not a.startswith("--") and not (i and av[i - 1] == "--n")]
    n = int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else 8
    OUT.mkdir(parents=True, exist_ok=True)
    for s in args:
        mp = REN / f"{s}.mp4"
        d = dur(mp)
        fps = n / d
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mp), "-vf",
                        f"fps={fps:.4f},scale=640:-1,tile=4x{(n + 3) // 4}",
                        "-frames:v", "1", str(OUT / f"{s}_rv.jpg")], check=True)
        print("ok", s, round(d, 2))


if __name__ == "__main__":
    main()
