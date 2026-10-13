# -*- coding: utf-8 -*-
r"""한국어 강제 정렬 — torchaudio MMS_FA(로마자) 로 «글 ↔ 소리» 단어 시각을 잰다.

whisper 단어 시각은 ±0.1~0.3초 흔들려 자막 타이밍 검수(99.99%)의 기준으로 못 쓴다.
그래서 자막 글(정답 글)을 소리에 강제 정렬한다. 한글은 자모를 개정 로마자로 바꿔 MMS 사전(a-z)에 맞춘다.

    from tools.auto.ko_align import Aligner
    al = Aligner()                     # GPU 있으면 GPU
    spans = al.align(wav16k_np, ["저는", "한비즈", ...])   # [(t0, t1, score), ...] (초, 입력 구간 기준)
"""
import re

import numpy as np
import torch
import torchaudio

CHO = ["g", "kk", "n", "d", "tt", "r", "m", "b", "pp", "s", "ss", "", "j", "jj", "ch", "k", "t", "p", "h"]
JUNG = ["a", "ae", "ya", "yae", "eo", "e", "yeo", "ye", "o", "wa", "wae", "oe", "yo", "u", "wo", "we", "wi", "yu", "eu", "ui", "i"]
JONG = ["", "k", "k", "k", "n", "n", "n", "t", "l", "k", "m", "l", "l", "l", "p", "l", "m", "p", "p", "t", "t", "ng", "t", "t", "k", "t", "p", "t"]
DIG = {"0": "yeong", "1": "il", "2": "i", "3": "sam", "4": "sa", "5": "o", "6": "yuk", "7": "chil", "8": "pal", "9": "gu"}


def romanize(word):
    out = []
    for ch in word:
        o = ord(ch)
        if 0xAC00 <= o <= 0xD7A3:
            s = o - 0xAC00
            out.append(CHO[s // 588] + JUNG[(s % 588) // 28] + JONG[s % 28])
        elif ch.isdigit():
            out.append(DIG[ch])
        elif "a" <= ch.lower() <= "z":
            out.append(ch.lower())
    return "".join(out)


class Aligner:
    def __init__(self, device=None):
        self.dev = device or ("cuda" if torch.cuda.is_available() else "cpu")
        b = torchaudio.pipelines.MMS_FA
        self.sr = b.sample_rate
        self.model = b.get_model(with_star=False).to(self.dev).eval()
        self.dic = b.get_dict(star=None)
        self.aligner = b.get_aligner()
        self.tok = b.get_tokenizer()

    def align(self, wav, words):
        rom = [romanize(w) for w in words]
        keep = [i for i, r in enumerate(rom) if r]
        rom = [rom[i] for i in keep]
        with torch.inference_mode():
            x = torch.from_numpy(np.asarray(wav, dtype=np.float32))[None].to(self.dev)
            em, _ = self.model(x)
            spans = self.aligner(em[0], self.tok(rom))
        ratio = x.shape[1] / em.shape[1] / self.sr
        res = [None] * len(words)
        for i, sp in zip(keep, spans):
            t0 = sp[0].start * ratio; t1 = sp[-1].end * ratio
            sc = float(np.mean([s.score for s in sp]))
            res[i] = (t0, t1, sc)
        return res
