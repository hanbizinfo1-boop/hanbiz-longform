"""카메라 소리를 어절 단위 시각과 함께 전사한다 — 버벅임·중복 찾기의 입력.

Whisper 는 말더듬·반복을 매끄럽게 지우는 경향이 있다. 그래서
  · 추임새를 적은 initial_prompt 로 «들리는 대로» 쪽으로 민다
  · 이전 문맥 이어받기를 끈다 (앞 문장을 따라 지어내는 것을 막는다)
그래도 지워진 것은 `disfluency_scan.py` 가 «소리는 있는데 글자가 없는 구간» 으로 따로 잡는다.

    python transcribe_words.py <16k.wav> <출력 words.json>

모델·설정은 ADR 0007 과 같다: large-v3 · int8_float16.
"""

import json
import sys
from pathlib import Path

import torch  # noqa: F401  cuBLAS DLL 이 torch 안에 있다 — 먼저 임포트해야 CTranslate2 가 찾는다
from faster_whisper import WhisperModel

PROMPT = "어, 음, 그, 저, 그니까, 자, 이제, 어… 그 그러니까 이게 이게 말이죠."


def main():
    wav, out = Path(sys.argv[1]), Path(sys.argv[2])
    model = WhisperModel("large-v3", device="cuda", compute_type="int8_float16")
    segs, info = model.transcribe(
        str(wav), language="ko", word_timestamps=True, vad_filter=True,
        condition_on_previous_text=False, initial_prompt=PROMPT, beam_size=5)
    rows = []
    for s in segs:
        rows.append({"t0": round(s.start, 3), "t1": round(s.end, 3), "text": s.text.strip(),
                     "words": [{"t0": round(w.start, 3), "t1": round(w.end, 3),
                                "w": w.word.strip(), "p": round(w.probability, 3)}
                               for w in (s.words or [])]})
        print(f"{s.start:7.2f}-{s.end:7.2f} {s.text.strip()}")
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"저장: {out}  ({len(rows)}문장)")


if __name__ == "__main__":
    main()
