# -*- coding: utf-8 -*-
"""성제관03 — 녹음 받아쓰기(large-v3, 어절 시각). tools/transcribe_words.py 와 같은 설정.

10-30 제작 PC 에서 Windows 앱 제어 정책이 PyAV(av) DLL 을 막아 faster_whisper 를 import 할 수 없게 됐다.
av 는 파일 디코딩에만 쓰이므로 빈 모듈로 막아 두고, 소리는 soundfile 로 읽어 numpy 배열로 넘긴다(16kHz 모노 wav 전용).
    py -3.11 tools/scenes/sjk03/transcribe.py <16k.wav> <출력 words.json> [--clip t0 t1]   (--clip: 그 조각만, 시각은 원래 시각)
"""
import json
import sys
import types
from pathlib import Path

import numpy as np
import soundfile as sf
import torch  # noqa: F401  cuBLAS DLL 이 torch 안에 있다 — 먼저 임포트해야 CTranslate2 가 찾는다

sys.modules.setdefault("av", types.ModuleType("av"))
from faster_whisper import WhisperModel  # noqa: E402

PROMPT = "어, 음, 그, 저, 그니까, 자, 이제, 어… 그 그러니까 이게 이게 말이죠."


def main():
    wav, out = Path(sys.argv[1]), Path(sys.argv[2])
    x, sr = sf.read(str(wav), dtype="float32")
    assert sr == 16000 and x.ndim == 1, "16kHz 모노 wav 만"
    off = 0.0
    if "--clip" in sys.argv:
        k = sys.argv.index("--clip")
        t0, t1 = float(sys.argv[k + 1]), float(sys.argv[k + 2])
        x, off = x[int(t0 * sr):int(t1 * sr)], t0
    model = WhisperModel("large-v3", device="cuda", compute_type="int8_float16")
    segs, info = model.transcribe(
        x, language="ko", word_timestamps=True, vad_filter=True,
        condition_on_previous_text=False, initial_prompt=PROMPT, beam_size=5)
    rows = []
    for s in segs:
        rows.append({"t0": round(s.start + off, 3), "t1": round(s.end + off, 3), "text": s.text.strip(),
                     "words": [{"t0": round(w.start + off, 3), "t1": round(w.end + off, 3),
                                "w": w.word.strip(), "p": round(w.probability, 3)}
                               for w in (s.words or [])]})
        print(f"{s.start + off:7.2f}-{s.end + off:7.2f} {s.text.strip()}")
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"저장: {out}  ({len(rows)}문장)")


if __name__ == "__main__":
    main()
