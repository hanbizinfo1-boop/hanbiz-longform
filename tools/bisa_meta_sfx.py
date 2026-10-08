# -*- coding: utf-8 -*-
r"""빡이사DB 01 메타 로고·업종 카드 — 효과음 (효과음 길라잡이 0장 문법대로).

    python bisa_meta_sfx.py
      → 빡이사DB\소재\효과음01\NN_*.wav (다듬은 낱개, 프리미어용)
      → 빡이사DB\납품\01_메타로고·업종카드_효과음.xml (V2 영상 + A2~ 효과음, 시퀀스 시각 그대로)
      → 빡이사DB\납품\01_메타로고·업종카드_효과음미리듣기.mp4 (장면 + 촬영본 목소리 + 효과음)

계기 → 소리 (길라잡이 0-2):
  로고 등장 = 브랜드 첫 소개 → 종소리 하나(띠링)
  로고가 퍼지며 화면 반분 = 큰 장면 전환 → 휙(정점을 퍼짐 한가운데에)
  카드 8장이 하나씩 = 항목이 하나씩 붙음 → 짧은 팝. 같은 소리 연속 금지(점검기 5-2)라 뿅·블록소리를 번갈아
  «여러가지 업종» 반짝 두 번 = 감탄·반짝 → 뾰로롱 → 치링
  사람 화면 복귀 = 전환 → 휙(다른 휙)
크기는 목소리(이 구간 말소리 50ms RMS 중앙) 대비 dB. 소재 다듬기는 길라잡이 6장(고역 셈 → 5kHz 셸빙 −6dB, 순간음 → 페이드인).
"""

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[0]))   # tools/ (config.py)
import config  # noqa: E402
import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(config.TOOLS))
sys.path.insert(0, str(Path(__file__).parent))
import rule_check  # noqa: E402
import lec_xml  # noqa: E402
from bisa_meta_cards import ITEMS, T0, T1, T_LOGO, T_SPREAD, T_OPEN, T_SHINE, T_BACK, SRC, OUT  # noqa: E402

SR = 48000
SFX_DIR = (config.WORK / "효과음01")
SCENE = OUT / "01_메타로고·업종카드_2.00~.mp4"

GRADE = config.GRADE_JSON      # yeneung_grade.py 결과 — A★ → A → B 순으로 고른다
ORDER = {"A★": 0, "A": 1, "B": 2, "C": 3}


def pick(cat, n, skip=(), new=None):
    """등급표에서 분류 cat 의 상위 n개(서로 다른 파일). skip = 뜻이 안 맞아 뺄 파일 이름 일부.
    new=True 면 새 라이브러리(소재\예능효과음)만, False 면 사장님 라이브러리만."""
    rs = [r for r in json.loads(GRADE.read_text(encoding="utf-8")) if r["분류"] == cat
          and not any(k in Path(r["파일"]).name for k in skip)
          and r.get("계열근거") != "소리추정(약함)"
          and (new is None or ("예능효과음" in r["파일"]) == new)]
    rs.sort(key=lambda r: (ORDER[r["등급"]], -r["점수"]))
    return rs[:n]


# 파일별 크기(목소리 «원음» 대비 dB, 구워 넣는 값) — 사장님이 프리미어에서 맞춘 최종값. 계기 기본값보다 우선한다.
# = 구운 값 + 사장님 클립 볼륨. 프리미어 저장값은 0dB = 0.17783(+15dB 여유) → dB = 20·log10(v / 0.17783).
# 사장님 타임라인 목소리(A1)는 +7dB 라서, 들리는 크기(목소리 대비) = 이 값 − 7.
# 같은 파일이 여러 장면에 나오면 가장 최근 장면 값. 04(10-07 15:14) · 05(15:31) · 06 2판(16:19 — 전부 +3, pep +6 더 올리심)
FILE_DB = {
    "휙２.mp3": 4, "휙1.mp3": 8,                                     # 06 (05 확대 휙２ 는 16:19 에 0dB 로 내리심 = 원음 −6)
    "채팅 효과음.mp3": 5, "ML_Cartoon bubbles popping.wav": 5,         # 06
    "KN_pepSound1.wav": 8, "KN_pepSound2.wav": 8,                    # 06
    "맑은소리.mp3": 7, "SEL_ゲージ回復1.mp3": 12, "KN_error_003.wav": 5,  # 06
    "SEL_キラッ1.mp3": -1,                                           # 05
    "SEL_キーボード2.mp3": 6, "키보드.mp3": 8,                          # 04
    "SEL_シャーペンで字を書く.mp3": 4,                                  # 04
}
FILE_DB_DEFAULT = 5                                                   # 표에 없는 파일(일반) — 06 에서 전부 +3 올리셔서 +2 → +5


def role(r, mx, rel, align):
    st = r["소재상태"]
    rel = FILE_DB.get(Path(r["파일"]).name, rel)
    return (Path(r["파일"]), mx, ("셸빙" in st) or ("고역 조금" in st), 30 if "페이드" in st else 0, rel, align, r["등급"])


# 계기 → 분류(효과음 길라잡이 0-2). 사장님 A★ 와 새 라이브러리 A 를 섞는다(10-02 «가지고 있는 것에서만 하다 보니 아쉽다»).
# 카드 8장은 뿅 계열 4개를 돌려 같은 파일이 2번씩·약 2초 간격(번갈아 3번 이하, 점검기 5-2b).
# 12_종 분류는 초인종·계산대뿐이라 로고(브랜드 첫 등장)는 반짝 분류의 짧은 반짝(キラッ)으로.
_logo = pick("04_반짝_띠링", 1, new=True, skip=("回復", "ステータス", "Magic transition"))
_pops = pick("02_뿅_팝", 2, new=False, skip=("도장",)) + pick("02_뿅_팝", 2, new=True)
_shine = pick("04_반짝_띠링", 1, new=False) + pick("04_반짝_띠링", 1, new=True, skip=(Path(_logo[0]["파일"]).name, "回復", "Magic transition", "Page"))   # 로고와 같은 페이지 차임 결은 피한다
SND = {"logo": role(_logo[0], 0.8, -4, "onset"),
       "spread": role(pick("10_휙_전환", 1, new=False)[0], 0.7, -5, "peak"),
       "shine1": role(_shine[0], 0.7, -4, "onset"),
       "shine2": role(_shine[1], 0.9, -4, "onset"),
       "back": role(pick("10_휙_전환", 1, new=True)[0], 0.8, -5, "peak")}
for _k, _r in enumerate(_pops):
    SND[f"pop{_k}"] = role(_r, 0.45, -4, "onset")

# (시퀀스 초, 이름). 휙은 그 시각에 정점이 오게 맞춘다.
EVENTS = ([(T_LOGO, "logo"), ((T_SPREAD + T_OPEN) / 2 - 0.08, "spread")]
          + [(t, f"pop{(0, 2, 1, 3)[k % 4]}") for k, (t, _, _) in enumerate(ITEMS)]
          + [(T_SHINE[0], "shine1"), (T_SHINE[1], "shine2"), (T_BACK + 0.25, "back")])


def load(path, shelf=False):
    af = ["aresample=48000", "aformat=sample_fmts=flt:channel_layouts=stereo"]
    if shelf:
        af.insert(0, "treble=g=-6:f=5000")
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-af", ",".join(af), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()


def rms_frames(x, win=0.05):
    n = int(SR * win)
    m = x.mean(1)[: len(x) // n * n].reshape(-1, n)
    return 20 * np.log10(np.sqrt((m ** 2).mean(1)) + 1e-9)


def voice_ref():
    v = load(SRC)[int(T0 * SR): int(T1 * SR)]
    f = rms_frames(v)
    return float(np.median(f[f > f.max() - 25])), v


TAIL_MAX = 2.5                                                    # 효과음 최대 길이(초)


def prep(name, ref):
    fn, mx, shelf, fin, rel, _, _ = SND[name]
    x = load(fn, shelf)
    a = np.abs(x).max(1)
    st = int(np.argmax(a > a.max() * 10 ** (-40 / 20)))          # 앞 무음 제거
    x = x[st:]
    # 길이: 소리가 자연히 잦아드는 곳(최고점 −45dB)까지, 최대 TAIL_MAX초 · 최소 mx초.
    # 10-07 사장님 «효과음 또 짧게 끊기고» — 예전엔 mx(0.4~0.6초)에서 자르고 0.08초에 꺼서 뚝 끊겼다.
    e = np.abs(x).max(1)
    loud = np.where(e > e.max() * 10 ** (-45 / 20))[0]
    end = (loud[-1] + 1) if len(loud) else len(x)
    if mx < 0:                                                     # 음수 = 그 길이로 딱(펜처럼 동작 길이에 맞춰야 하는 소리)
        x = x[: int(-mx * SR)]
    else:
        x = x[: max(int(mx * SR), min(end, int(TAIL_MAX * SR)))]
    fo = min(len(x) // 3, int(0.25 * SR))                          # 꼬리 페이드아웃(부드럽게)
    x[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 2
    if fin:
        n = int(fin / 1000 * SR)
        x[:n] *= np.linspace(0, 1, n)[:, None]
    f = rms_frames(x)
    x *= 10 ** ((ref + rel - f.max()) / 20)
    x *= min(1.0, 0.5 / (np.abs(x).max() + 1e-9))   # 짧은 클릭은 50ms RMS 가 작게 잡혀 과증폭 → 피크 −6dBFS 상한(10-02 03 마우스클릭 0dB 잘림)
    peak_at = (int(np.argmax(f)) + 0.5) * 0.05
    return x, peak_at


def write_wav(path, x):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())


def main():
    ref, voice = voice_ref()
    print(f"목소리 기준(50ms RMS 중앙) {ref:.1f} dBFS")
    SFX_DIR.mkdir(parents=True, exist_ok=True)
    cache, placed, mix = {}, [], np.zeros_like(voice)
    for k, (t, name) in enumerate(EVENTS):
        if name not in cache:
            cache[name] = prep(name, ref)
        x, peak_at = cache[name]
        start = t - (peak_at if SND[name][5] == "peak" else 0.0)
        f = SFX_DIR / f"{k + 1:02d}_{name}.wav"
        write_wav(f, x)
        placed.append((round(start, 3), f, name))
        i = int((start - T0) * SR)
        seg = x[: len(mix) - i]
        mix[i: i + len(seg)] += seg
        print(f"  {start:5.2f}s  {name:7s} [{SND[name][6]}] {SND[name][0].name}")
    for lv, msg, where in rule_check.check_sfx([(t - T0, SND[n][0]) for t, _, n in placed], T1 - T0):
        print(lv, msg, where)
        if lv == "ERROR":
            sys.exit(1)

    write_wav(SFX_DIR / "00_효과음만_합본_2.00~.wav", mix)
    pre = OUT / "01_메타로고·업종카드_효과음미리듣기.mp4"
    both = voice + mix
    tmp = SFX_DIR / "_미리듣기소리.wav"
    write_wav(tmp, both)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(SCENE), "-i", str(tmp), "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-af", "alimiter=limit=0.84:level=false", "-c:a", "aac", "-b:a", "256k", "-shortest", str(pre)], check=True)
    tmp.unlink()
    pk = 20 * np.log10(np.abs(both).max() + 1e-9)
    print(f"미리듣기 합 피크 {pk:.1f} dBFS (리미터 −1.5dB) → {pre}")
    lec_xml.V_TRACK, lec_xml.A_TRACK = 2, 2
    print(lec_xml.write(OUT / "01_메타로고·업종카드_효과음.xml", "빡이사DB_01_메타카드_효과음", SCENE, T1 - T0, T0,
                        [(t, f) for t, f, _ in placed], 59.94, tag="bs01s"))


if __name__ == "__main__":
    main()
