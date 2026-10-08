"""컷 계획대로 «확인용» 미리보기 영상을 뽑는다 — 납품본이 아니다.

    python render_preview.py <plan.json> <출력.mp4> <좌상단 이름표>

  · 카메라 원본(4K)을 720p 로 줄여 빠르게 낸다 (H.264 NVENC)
  · 좌상단에 이름표(«무음 컷만» / «버벅임 제거»)를 계속 띄운다
  · plan 에 `markers` 가 있으면 뺀 자리마다 «제거 04 · 중복» 을 2초 띄운다 (✂ 는 맑은 고딕에 없어 네모로 나온다)
소리는 손대지 않는다 (게인 0).
"""

import json
import subprocess
import sys
import time
from pathlib import Path

FONT = "C\\:/Windows/Fonts/malgun.ttf"


def esc(s):
    return s.replace("\\", "\\\\").replace("'", "’").replace(":", "\\:").replace("%", "\\%")


def main():
    plan_p, dst, tag = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    p = json.loads(plan_p.read_text(encoding="utf-8"))
    src = Path(p["source"])
    keep = p["keep"]

    sel = "+".join(f"between(t,{s:.4f},{e:.4f})" for s, e in keep)
    draw = [f"drawtext=fontfile='{FONT}':text='{esc(tag)}':x=24:y=20:fontsize=34:"
            "fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=10"]
    for m in p.get("markers", []):
        t = m["t"]
        label = esc("제거 %02d · %s" % (m["no"], m["label"]))
        draw.append(f"drawtext=fontfile='{FONT}':text='{label}':x=(w-text_w)/2:y=60:"
                    f"fontsize=40:fontcolor=yellow:box=1:boxcolor=black@0.7:boxborderw=12:"
                    f"enable='between(t,{t:.3f},{t + 2:.3f})'")
    graph = (f"[0:v]select='{sel}',setpts=N/FRAME_RATE/TB,scale=1280:720,format=yuv420p,"
             + ",".join(draw) + "[v];"
             f"[0:a]aselect='{sel}',asetpts=N/SR/TB[a]")
    script = dst.with_suffix(".filter.txt")
    dst.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(graph, encoding="utf-8")

    cmd = ["ffmpeg", "-y", "-hide_banner", "-v", "error", "-i", str(src),
           "-filter_complex_script", str(script), "-map", "[v]", "-map", "[a]",
           "-c:v", "h264_nvenc", "-preset", "p4", "-cq", "26", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", str(dst)]
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    script.unlink(missing_ok=True)
    if r.returncode != 0:
        print(r.stderr[-2000:])
        return 1
    print(f"저장: {dst}  ({dst.stat().st_size / 1e6:.1f}MB, {time.time() - t0:.0f}초 걸림)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
