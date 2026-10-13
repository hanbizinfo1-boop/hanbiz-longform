# -*- coding: utf-8 -*-
"""맞춤법 의심 줄: 후보 글 둘을 같은 소리 구간에 강제 정렬해 점수로 비교(파트너센터 자동)."""
import json, sys
sys.path.insert(0, ".")
import soundfile as sf
from tools.auto.ko_align import Aligner
x, sr = sf.read("_tmp/pc/a16k.wav", dtype="float32")
al = Aligner()
CASES = [
    (83.53, "박서아님이 DB 수집됐다", "박서한님이 DB 수집됐다"),
    (165.95, "박서아님 전화 안 받으셨어요", "박서한님 전화 안 받으셨어요"),
    (284.78, "최화윤님 내가 하겠다", "최하윤님 내가 하겠다"),
    (512.53, "다음 날이 됐네?", "전날이 됐네?"),
    (559.43, "한서한 님 기준으로 봤을 때", "한서환 님 기준으로 봤을 때"),
    (988.10, "이건 무조건 끄고", "이건 무조건 그거"),
    (1013.51, "직접 설정해서도 보실 수가 있고요", "직접 설정에서도 보실 수가 있고요"),
    (1074.37, "성과를 분석을 해놓해보셨다 라는 분들은", "성과를 분석을 해보셨다 라는 분들은"),
    (1093.03, "무조건 봐야 하는 기능만 넣어놨고", "무조건 봐야 하는 기능들은 안 넣어놨고"),
    (1323.59, "또는 보는 사람에서", "또는 고른 사람에서"),
    (742.33, "페북 페이지도 저희가", "페이스북 페이지도 저희가"),
    (21.27, "전부 적응되실 거예요", "전부 적용되실 거예요"),
    (867.45, "저희가 제한을 해놨기 때문에", "저희가 제안을 해놨기 때문에"),
]
it = json.load(open("_tmp/pc/edit.json", encoding="utf-8"))["items"]
caps = sorted((i for i in it if i["track"] == "C1"), key=lambda i: i["t0"])
for t, a, b in CASES:
    c = min(caps, key=lambda c: abs(c["t0"] - t))
    s0, s1 = c["t0"] - 0.4, c["t1"] + 0.4
    seg = x[int(s0 * sr):int(s1 * sr)]
    def score(txt):
        r = al.align(seg, txt.split())
        rs = [q for q in r if q]
        return sum(q[2] for q in rs) / max(1, len(rs)), [round(q[2], 2) for q in r if q]
    sa, la = score(a); sb, lb = score(b)
    print(f"{t:8.2f} | 자막 «{c['text']}»\n   A {sa:.3f} {la} «{a}»\n   B {sb:.3f} {lb} «{b}»")
