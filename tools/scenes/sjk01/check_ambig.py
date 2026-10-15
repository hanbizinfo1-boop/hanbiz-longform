# -*- coding: utf-8 -*-
"""성제관01 — 받아쓰기가 애매한 구간을 «귀 대신» 다시 확인한다.

구간마다 ① 그 조각만 잘라 whisper 로 다시 받아쓰고(앞 문맥·프롬프트 없이) ② 후보 글을 강제 정렬해 점수를 비교한다.
점수(MMS_FA 평균)가 높은 쪽이 녹음과 맞는 글. 결과는 _tmp/sjk01/audio/ambig.json.
    py -3.11 tools/scenes/sjk01/check_ambig.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
import torch  # noqa: F401
from faster_whisper import WhisperModel

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.auto.ko_align import Aligner  # noqa: E402

WAV = ROOT / "_tmp/sjk01/audio/voice16k.wav"
OUT = ROOT / "_tmp/sjk01/audio/ambig.json"

# (구간 시작, 끝, [후보 글 …])
CASES = [
    (160.2, 164.7, ["우리 가게는 ○○동 국밥집이야", "우리 가게는 ○○동 국밥집이야 우리 가게는 ○○동 국밥집이야"]),
    (215.5, 218.7, ["그냥 챗GPT 켜시고", "그냥 챗GPT 켜셔서 그냥 챗GPT 켜시고"]),
    (396.6, 402.4, ["번호 붙은 체크리스트로 정리해 줘 위험한 건 맨 위에 넣어주고",
                    "번호 붙은 체크리스트로 정리해 줘 위험한 건 맨 위에 넣어주고 위험한 건 맨 위에 넣어주고"]),
    (579.0, 585.2, ["글씨가 작고 말이 어렵잖아요 그냥 사인하시는 분들 진짜 많아요",
                    "글씨가 작고 말이 어렵잖아요 그냥 사인하시는 분들 진짜 많아요 그냥 사인하시는 분들 진짜 많아요"]),
    (646.3, 649.0, ["원가가 칠십 퍼센트라서 빼라고 했어요", "원가가 육십 퍼센트라서 빼라고 했어요"]),
    (41.7, 43.1, ["휴대폰으로도 다 됩니다", "휴대폰으로 다 됩니다"]),
    (44.3, 46.8, ["보시면 이건 내일 당장 써야겠다 하실 거예요", "보시면 이거 내일 당장 써야겠다 하실 거예요"]),
    (55.0, 56.6, ["그래서 세 덩어리로 나눌게요", "그래서 세 덩이로 나눌게요"]),
    (128.6, 133.1, ["별점 낮은 리뷰 답글은 사장님이 한 번은 꼭 읽고 올리셔야 돼요", "별점 낮은 리뷰 답글은 사장님이 한 번은 꼭 읽고 올리셔야 해요"]),
    (118.1, 119.9, ["싱겁게 따로 말아 드릴게요", "싱겁게 따로 말해 드릴게요"]),
    (211.3, 212.9, ["둘 중에 뭘 시키시겠어요", "둘 중에 뭘 시키겠어요"]),
    (241.0, 243.5, ["우리 가게에 진짜 있는 것만 남기셔야 됩니다", "우리 가게에 진짜 있는 것만 남기셔야 합니다"]),
    (306.0, 307.8, ["자 바로 다섯 번째 갈게요", "자 바로 다섯 번째 갈 거예요"]),
    (329.1, 331.1, ["주말은 하루 종일 세 명이 필요해", "주말엔 하루 종일 세 명이 필요해"]),
    (345.7, 347.8, ["AI는 계산은 정확하게 해 줘요", "AI는 계산을 정확하게 해 줘요"]),
    (375.1, 377.1, ["이게 몇 년째 반복이잖아요", "이거 몇 년째 반복이잖아요"]),
    (574.2, 576.5, ["마지막 열 번째 계약서예요", "마지막에 열 번째 계약서예요"]),
    (617.0, 618.9, ["자 열 가지 다 했고요", "자 여기까지 다 했고요"]),
    (622.1, 625.6, ["제가 아까 원가 표 뽑은 걸 그대로 넣고 이렇게 물어봤거든요", "제가 아까 원가 표 뽑은 걸 그대로 놓고 이렇게 물어봤거든요"]),
    (639.1, 641.0, ["보면 오 맞는 말이네 싶어요", "보면 오 많은 말이네 싶어요"]),
    (680.0, 683.0, ["그 시간 아껴서 사장님은 결정하는 일을 하시라는 거예요", "그 시간 앞에서 사장님은 결정하는 일을 하시라는 거예요"]),
    (21.0, 23.1, ["AI를 10%도 못 쓰고 계신 거예요", "AI를 십 퍼센트도 못 쓰고 계신 거예요"]),
]


def words(txt):
    t = txt.replace("○○", "오오").replace("GPT", "지피티").replace("AI", "에이아이").replace("%", " 퍼센트")
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
