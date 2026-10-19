r"""성제관02 블렌더 장면 차례로 렌더(이미 다 된 장면은 건너뜀).

    py -3.11 tools/scenes/sjk02/blender/render_all.py [s32 s42 …] [--force]
desk 장면(s07·s08·s32·s42)은 desk_specs.py 로 spec 을 먼저 만든다.
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "tools"))
import config as C  # noqa: E402

OUT = ROOT / "_tmp" / "sjk02" / "blender"
FPS = 60000 / 1001
JOBS = {"s07": "desk", "s08": "desk", "s32": "desk", "s42": "desk", "s17": "coins.py", "s33": "funnel.py", "s45": "tower.py", "s55": "tanks.py"}


def nframes(s):
    t = (HERE.parent / "data" / f"{s}.js").read_text(encoding="utf-8")
    d = json.loads(t[t.index("{"):t.rindex("}") + 1])
    return int(round((d["pre"] + d["dur"] + d["post"]) * FPS)) + 1


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    force = "--force" in sys.argv
    names = args or list(JOBS)
    if any(JOBS[n] == "desk" for n in names):
        subprocess.run([sys.executable, str(HERE / "desk_specs.py")], check=True)
    for s in names:
        out = OUT / s
        nf = nframes(s)
        have = len(list(out.glob("f*.png"))) if out.exists() else 0
        if have >= nf and not force:
            print("skip", s, have, flush=True); continue
        if force and out.exists():
            for f in out.glob("f*.png"):
                f.unlink()
        cmd = [str(C.BLENDER), "-b", "-P"]
        cmd += [str(HERE / "desk.py"), "--", str(OUT / f"spec_{s}.json")] if JOBS[s] == "desk" else [str(HERE / JOBS[s]), "--"]
        log = OUT / f"{s}.log"
        with open(log, "w", encoding="utf-8", errors="replace") as fh:
            r = subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT)
        have = len(list(out.glob("f*.png")))
        print(("ok" if have >= nf else "FAIL"), s, have, "/", nf, flush=True)


if __name__ == "__main__":
    main()
