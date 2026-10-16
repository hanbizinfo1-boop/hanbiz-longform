# -*- coding: utf-8 -*-
"""성제관02 — 받아쓰기가 애매한 구간을 «귀 대신» 다시 확인한다.

구간마다 ① 그 조각만 잘라 whisper 로 다시 받아쓰고(앞 문맥·프롬프트 없이) ② 후보 글을 강제 정렬해 점수를 비교한다.
점수(MMS_FA 평균)가 높은 쪽이 녹음과 맞는 글. 결과는 _tmp/sjk02/audio/ambig.json.
    py -3.11 tools/scenes/sjk02/check_ambig.py
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

WAV = ROOT / "_tmp/sjk02/audio/voice16k.wav"
OUT = ROOT / "_tmp/sjk02/audio/ambig.json"

# (구간 시작, 끝, [후보 글 …])
CASES = [
    (95.1, 99.5, ["손님이 눈에 띄게 늘어난 가게도 있었고요", "손님이 눈에 띄게 드러난 가게도 있었고요"]),
    (157.0, 160.4, ["우리는 새벽 다섯시에 불을 올려서 점심 전에 딱 한 솥만 끓여", "우리는 새벽 다섯시에 불을 흘려서 점심 전에 딱 한 손만 끓여", "우리는 새벽 다섯시에 불 올려서 점심 전에 딱 한 솥만 끓여"]),
    (163.6, 167.3, ["새벽 다섯시에 불을 올려서 점심 전에 딱 한 솥만 끓입니다", "새벽 다섯시에 불 올려서 점심 전에 딱 한 솥만 끓입니다"]),
    (465.2, 468.9, ["구십 퍼센트랑 일 퍼센트를 진짜로 가르는 게", "구십구 퍼센트랑 일 퍼센트를 진짜로 가르는 게"]),
    (553.7, 555.7, ["아까 그 새벽 다섯시 국밥집처럼요", "아까 그 새벽 세시 국밥집처럼요"]),
    (570.4, 572.5, ["이 첫 솥이에요 오늘 첫 솥이에요", "오늘 첫 솥이에요 오늘 첫 솥이에요", "오늘 첫 솥이에요"]),
    (309.8, 312.0, ["근데 여기서 이상한 생각 드실 수도 있어요", "근데 여기서 이상한 생각 드릴 수도 있어요", "근데 여기서 이런 생각 드실 수 있어요"]),
    (73.6, 76.8, ["그때 가서 갈리는 건 에이아이 말고 다른 거거든요", "그때 가서 갈리는 건 에이아이 말고 다른 거예요"]),
    (265.9, 268.5, ["아니에요 다 있어요 본인만 모르는 거예요", "아니에요 다 있어요 본인이 모르시는 거예요"]),
    (49.6, 51.8, ["배달앱 처음 나왔을 때 기억하시죠", "배달앱 처음 나왔을 때 기억나시죠"]),
    (248.5, 255.1, ["근데 시킬 때 이번 주는 배추가 너무 너무 좋아서 김치를 평소보다 두 통 더 담갔어요", "근데 시킬 때 이번 주는 배추가 너무 좋아서 김치를 평소보다 두 통 더 담갔어요"]),
    (529.9, 531.9, ["광고비는 오히려 줄었는데도요", "광고비는 오히려 줄였는데도요"]),
    (622.7, 626.4, ["만약 아직도 감이 안 잡혀서 도움 필요하시다면 댓글 남겨주세요", "만약 아직도 감이 안 잡히셔서 도움이 필요하시다면 댓글 남겨주세요"]),
    (186.6, 190.4, ["근데 장사에서 무난하다는 건 손님 기억에 안 남는다는 얘기거든요", "근데 장사에서 무난하다는 건 손님 기억이 안 남는다는 얘기거든요"]),
    (180.7, 183.1, ["에이아이가 잘 쓰는 건 평균적인 글이거든요", "에이아이가 잘 쓰는 건 평균적인 글이에요"]),
    (116.0, 120.7, ["똑같이 에이아이를 쓰는데 이 세 개를 어떻게 쓰느냐에 따라서 가게가 갈려요", "똑같이 에이아이를 쓰는데 이 세 개를 어떻게 쓰느냐에서 가게가 갈려요"]),
    (576.7, 579.0, ["이 세 개는 에이아이한테 시킬 수가 없어요", "이 세계는 에이아이한테 시킬 수가 없어요"]),
    (367.4, 369.3, ["세금 낼 때쯤 돼야 보이거든요", "세금 내 때쯤 돼야 보이거든요"]),
    (475.7, 479.1, ["근무표 짜는 데 한 시간 걸리던 게 오 분이면 끝나고요", "금문표 짜는 데 한 시간 걸리던 게 오 분이면 끝나고요"]),
    (561.0, 563.6, ["대표님들이 처음엔 다 쑥스러워하세요", "제가 이거 말씀드리면 대표님들이 처음엔 다 쑥스러워하세요"]),
    (19.0, 22.9, ["제일 먼저 사라질 수도 있어요 배달앱 한번 들어가 보세요", "제일 먼저 사라질 수도 있어요 왜 그러냐면요 배달앱 한번 들어가 보세요"]),
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
