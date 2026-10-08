"""컷 계획만 먼저 뽑는다 — 인코딩은 하지 않는다.

4K60 소재는 인코딩이 몇 시간짜리라, 컷이 몇 개이고 얼마나 줄어드는지부터 보고
출력 스펙을 정한다. 컷 판정 로직은 subtitle-pipeline 의 검증된 모듈을 그대로 쓴다.
"""

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[0]))   # tools/ (config.py)
import config  # noqa: E402

import json
import subprocess
import sys
from pathlib import Path

PIPE = config.SUBPIPE
sys.path.insert(0, str(PIPE))

from subpipe import audio as audio_module          # noqa: E402
from subpipe.cut import loudness, vad              # noqa: E402
from subpipe.cut.plan import build_plan            # noqa: E402
from subpipe.cut.report import render_cut_report   # noqa: E402


def probe(video: Path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=r_frame_rate",
         "-show_entries", "format=duration",
         "-of", "json", str(video)],
        capture_output=True, text=True, check=True,
    ).stdout
    j = json.loads(out)
    num, den = j["streams"][0]["r_frame_rate"].split("/")
    return float(num) / float(den), float(j["format"]["duration"])


def main():
    video = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)

    fps, duration = probe(video)
    print(f"소재: {video.name}")
    print(f"  {fps:.3f}fps / {duration:.1f}초 ({duration/60:.1f}분)")

    wav = out_dir / "audio_16k.wav"
    if not wav.exists():
        print("오디오 추출 중...")
        audio_module.extract(video, wav)
    print(f"  오디오: {wav.stat().st_size/1e6:.1f}MB")

    # VAD 판정 기준을 일정하게 — 이 사본은 판정용이고 출력에는 쓰지 않는다
    gain = loudness.peak_normalize_gain(wav, target_dbfs=-3.0)
    wav_vad = out_dir / "audio_16k_vad.wav"
    if not wav_vad.exists():
        loudness.apply_gain(wav, wav_vad, gain)
    print(f"  VAD용 게인: {gain:+.2f}dB")

    print("발화 구간 검출 중...")
    speech = vad.detect_speech(wav_vad)
    print(f"  발화 구간 {len(speech)}개")

    # 발화 앞뒤 여유. 사장님 지정 2026-09-23: 0.2초는 길다 → 0.12초, 2026-09-30: «여전히 너무 길어» → 0.06초 (세 번째 인자로 바꿀 수 있다)
    pad = float(sys.argv[3]) if len(sys.argv) > 3 else 0.06
    plan = build_plan(speech, source_duration=duration, fps=fps, pad_seconds=pad)
    print(f"  앞뒤 여유: {pad}초")

    report = render_cut_report(plan)
    (out_dir / "cut_report.txt").write_text(report, encoding="utf-8")
    print()
    print(report)

    # 계획을 JSON 으로도 남긴다 — 렌더링 단계에서 다시 계산하지 않기 위해
    (out_dir / "cut_plan.json").write_text(json.dumps({
        "source": str(video),
        "fps": fps,
        "source_duration": duration,
        "pad_seconds": plan.pad_seconds,
        "keep": [[i.start, i.end] for i in plan.keep],
        "speech": [[i.start, i.end] for i in plan.speech],
    }, ensure_ascii=False), encoding="utf-8")
    print(f"\n계획 저장: {out_dir / 'cut_plan.json'}")


if __name__ == "__main__":
    main()
