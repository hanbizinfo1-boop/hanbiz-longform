# -*- coding: utf-8 -*-
"""성제관03 — 받아쓰기가 애매한 구간을 «귀 대신» 다시 확인한다.

구간마다 ① 그 조각만 잘라 whisper 로 다시 받아쓰고(앞 문맥·프롬프트 없이) ② 후보 글을 강제 정렬해 점수를 비교한다.
점수(MMS_FA 평균)가 높은 쪽이 녹음과 맞는 글. 결과는 _tmp/sjk03/audio/ambig.json.
    py -3.11 tools/scenes/sjk03/check_ambig.py
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
import types
import torch  # noqa: F401
sys.modules.setdefault("av", types.ModuleType("av"))  # 10-30 앱 제어 정책이 PyAV DLL 을 막음 — 디코딩 안 쓰므로 빈 모듈
from faster_whisper import WhisperModel  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.auto.ko_align import Aligner  # noqa: E402

WAV = ROOT / "_tmp/sjk03/audio/voice16k.wav"
OUT = ROOT / "_tmp/sjk03/audio/ambig.json"

# (구간 시작, 끝, [후보 글 …]) — 3편은 _tmp/sjk03/audio/ambig_cases.json 에 [[t0, t1, [후보…]], …]
CASES = json.load(open(ROOT / "_tmp/sjk03/audio/ambig_cases.json", encoding="utf-8"))


def words(txt):
    t = txt.replace("○○", "오오").replace("GPT", "지피티").replace("AI", "에이아이").replace("%", " 퍼센트")
    t = re.sub(r"(\d)\.(\d)", lambda m: m.group(1) + "점" + m.group(2), t)
    return t.split()


def main():
    wav, sr = sf.read(str(WAV), dtype="float32")
    model = WhisperModel("large-v3", device="cuda", compute_type="int8_float16")
    al = Aligner()
    res = []
    for t0, t1, cands in CASES:
        clip = wav[int(t0 * sr):int(t1 * sr)]
        segs, _ = model.transcribe(clip, language="ko", beam_size=5, condition_on_previous_text=False, vad_filter=False)
        heard = " ".join(s.text.strip() for s in segs)
        sc = []
        for c in cands:
            sp = al.align(clip, words(c))
            v = [s[2] for s in sp if s]
            sc.append(round(float(np.mean(v)), 4) if v else None)
        rms = float(np.sqrt(np.mean(clip ** 2)))
        res.append(dict(t0=t0, t1=t1, heard=heard, cands=cands, scores=sc, best=cands[int(np.argmax(sc))], rms=round(rms, 4)))
        print(f"{t0:7.1f}-{t1:7.1f} | 다시 들음: {heard}\n          점수 {sc} → {res[-1]['best']}", flush=True)
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
