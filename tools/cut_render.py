"""컷 계획대로 잘라 이어붙이고, 보이스를 일정한 레벨로 맞춘다.

컷 필터 조립은 subtitle-pipeline 의 검증된 `build_filter_script` 를 그대로 쓴다.
다른 것은 **인코더뿐**이다 — 저장소의 측정값(libx264 CRF 16)은 1080p 중간본 기준이라
4K60 소재에 그대로 걸면 몇 시간·수십 GB 가 된다. 같은 화질대를 NVENC 로 낸다.

오디오는 시간축을 건드리지 않는다. 측정한 LRA 가 6.4 LU 로 이미 고르므로
컴프레서 없이 **파일 전체 동일 게인**만 준다.
"""

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[0]))   # tools/ (config.py)
import config  # noqa: E402

import json
import subprocess
import sys
import time
from pathlib import Path

PIPE = config.SUBPIPE
sys.path.insert(0, str(PIPE))

from subpipe.cut.plan import CutPlan, Interval      # noqa: E402
from subpipe.cut.render import build_filter_script  # noqa: E402


def main():
    plan_path = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    gain_db = float(sys.argv[3])

    p = json.loads(plan_path.read_text(encoding="utf-8"))
    src = Path(p["source"])

    plan = CutPlan(
        keep=[Interval(s, e) for s, e in p["keep"]],
        removed=[],
        source_duration=p["source_duration"],
        fps=p["fps"],
        pad_seconds=p["pad_seconds"],
        speech=[Interval(s, e) for s, e in p["speech"]],
    )

    script = build_filter_script(plan, gain_db=gain_db)
    script_path = plan_path.parent / "filter_script.txt"
    script_path.write_text(script, encoding="utf-8")

    dst.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg", "-y", "-hide_banner",
        "-i", str(src),
        "-filter_complex_script", str(script_path),
        "-map", "[v]", "-map", "[a]",
        "-c:v", "hevc_nvenc", "-preset", "p5", "-rc", "vbr", "-cq", "19", "-b:v", "0",
        "-pix_fmt", "yuv420p",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-c:a", "pcm_s16le",
        str(dst),
    ]

    print("컷 구간:", len(plan.keep), "개 / 출력 길이 예상:", f"{plan.output_duration:.1f}초")
    print("오디오 게인:", f"{gain_db:+.2f}dB")
    print("인코딩 시작...")

    t0 = time.time()
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    elapsed = time.time() - t0

    if proc.returncode != 0:
        print("실패 — ffmpeg stderr 마지막 부분:")
        print((proc.stderr or "")[-3000:])
        return 1

    size = dst.stat().st_size
    print(f"완료: {dst}")
    print(f"  {size/1e9:.2f} GB / {elapsed/60:.1f}분 소요")
    return 0


if __name__ == "__main__":
    sys.exit(main())
