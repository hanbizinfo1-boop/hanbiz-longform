# -*- coding: utf-8 -*-
"""성제관01 소리 — 목소리(정본 녹음) + 효과음(장면 EVENTS → sfx_bus) + BGM(장마다 한 곡, 목소리 아래) → −14 LUFS.

    py -3.11 tools/scenes/sjk01/audio_mix.py            → _tmp/sjk01/final/성제관01_소리.wav (+ 효과음 버스·보고)

효과음: 장면마다 _tmp/sjk01/render/sNN_events.json(html_motion) 의 {t, role} 를 «장면 시작 − pre + t» 로 옮긴다.
  역할 → 파일은 아래 VAR(뜻별 단골 sfx-workflow.md 3장). 같은 파일이 3초 안에 다시 나오면 다음 변형으로 돌리고, 변형이 다 막히면 뺀다(보고).
  전환(push·zoom·split·wipe)은 경계에 «휙»(sweep) 하나 — 컷마다 전환음 금지(09-22), dissolve·cut 은 소리 없음.
BGM: Mixkit Stock Music Free License(유튜브 허용·크레딧 불필요 — 한비즈-쇼츠광고/소재/BGM후보/라이선스.md). 장(세계)마다 한 곡, 장 경계 2초 교차.
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))
from tools.auto import sfx_bus as SB  # noqa: E402

SR = 48000
VOICE = r"D:\성제관 1편\성제관 1편.wav"
TL = json.load(open(ROOT / "_tmp/sjk01/timeline.json", encoding="utf-8"))
OUT = ROOT / "_tmp/sjk01/final"
BGM_DIR = Path(r"C:\Users\user\Desktop\한비즈-쇼츠광고\소재\BGM후보")
# 장(세계) → 곡. 1~4 손님(휴대폰 속) · 5~7 사람(주방) · 8~10 돈(숫자의 방) · 실험·마무리
CHAPTERS = [(0.0, "P1/Mixkit_Crying_Sea.mp3"), (66.6, "P1/Mixkit_Dreamy_Jazz.mp3"), (295.3, "P1/Mixkit_Lo-Fi_04.mp3"),
            (463.2, "P1/Mixkit_Coffee_or_Tea.mp3"), (617.3, "P1/Mixkit_Crying_Sea.mp3")]

# 역할 → [(파일, 원음 대비 구울 dB, 정렬)] 변형 순서
VAR = {
    # v2(10-15): 효과음이 2초에 하나꼴이라 «3초 사슬 같은 파일 3번» 을 지키려면 변형이 더 필요 — 휙·스윕·팝 변형 추가
    "in": [("휙２.mp3", 4, "peak"), ("휙1.mp3", 8, "peak"), ("ML_Fast whoosh transition", 5, "attack"),
           ("ML_Fast transitions swoosh", 5, "attack"), ("ML_Flying fast swoosh", 5, "attack"), ("ML_Speeding swoosh", 5, "attack")],
    "sweep": [("ML_Fast sweep transition", 5, "attack"), ("air sweep", 5, "attack"), ("small sweep", 5, "attack"),
              ("ML_Fast sweeping transition", 5, "attack"), ("ML_Swirling whoosh", 5, "attack"), ("ML_Vacuum swoosh transition", 5, "attack")],
    "card": [("ML_Cartoon bubbles popping", 5, "attack"), ("KN_pepSound1", 8, "attack"), ("KN_pepSound2", 8, "attack"), ("20. 카툰 팝", 5, "attack"),
             ("ML_Egg bubble pop", 5, "attack"), ("ML_Cartoon bubble pop", 5, "attack"), ("pop-up_02", 5, "attack")],
    "msg": [("채팅 효과음", 5, "attack"), ("7. 뿅", 5, "attack"), ("ML_Bell notification", 5, "attack"), ("ML_Bubble pop up alert", 5, "attack")],
    "big": [("SEL_文字表示の衝撃音1", 5, "attack"), ("SEL_文字表示の衝撃音2", 5, "attack"), ("SEL_文字表示の衝撃音3", 5, "attack"),
            ("ML_Movie whoosh impact", 5, "attack")],
    "ok": [("맑은소리", 7, "attack"), ("SEL_キラッ2", 0, "attack")],
    "no": [("KN_error_003", 5, "attack"), ("KN_lowDown", 5, "attack")],
    "miss": [("KN_lowDown", 5, "attack")],
    "type": [("SEL_キーボード2", 6, "attack"), ("SEL_キーボード1", 6, "attack")],
    "marker": [("SEL_油性マーカーで字を書く", 3, "attack"), ("SEL_シャーペンで字を書く", 4, "attack"), ("24. 연필", 4, "attack")],
    "pen": [("SEL_シャーペンで字を書く", 4, "attack"), ("SEL_油性マーカーで字を書く", 3, "attack")],
    "stamp": [("도장.mp3", 5, "attack")],
    "page": [("ML_Page turn chime", 5, "attack")],
    "gauge": [("SEL_ゲージ回復1", 12, "attack"), ("SEL_ゲージ回復2", 12, "attack"), ("SEL_ゲージ回復3", 12, "attack")],
    "shine": [("SEL_キラッ1", -1, "attack"), ("SEL_キラッ2", -1, "attack")],
    "click": [("마우스 클릭", 5, "attack"), ("15. 마우스클릭", 5, "attack")],
    "level": [("SEL_レベルアップ", 5, "attack")],
}
ALIAS = {"msg": "msg", "card": "card", "big": "big", "in": "in", "sweep": "sweep", "chip": "card", "pop": "card", "bell": "msg"}
DUR = {"marker": 0.35}


def role_key(r):
    r = r[:-3] if r.endswith("_in") else r
    return ALIAS.get(r, r)


def collect():
    cues, unknown = [], []
    for s in TL:
        p = ROOT / f"_tmp/sjk01/render/s{s['scene']:02d}_events.json"
        if not p.exists():
            continue
        base = s["t0"] - s["pre"]
        for e in json.load(open(p, encoding="utf-8")).get("events", []):
            k = role_key(e["role"])
            t = base + e["t"]
            if k not in VAR:
                unknown.append((round(t, 2), e["role"])); continue
            if t < s["t0"] - s["pre"] or t > s["t1"] + s["post"]:
                continue
            cues.append({"t": round(t, 3), "k": k, "scene": s["scene"]})
    # v2(10-15): 조립기가 쓴 전환 표(_tmp/sjk01/final/v2_plan.json)의 모든 전환에 «휙» — 휙(in)과 스윕(sweep)을 번갈아
    plan_p = ROOT / "_tmp/sjk01/final/v2_plan.json"
    trans = json.load(open(plan_p, encoding="utf-8"))["trans"] if plan_p.exists() else [s["trans_in"] for s in TL]
    alt = 0
    for k, s in enumerate(TL):
        if k and trans[k] not in ("cut", "cont"):
            alt += 1
            cues.append({"t": round(s["t0"] - 0.05, 3), "k": "sweep" if alt % 2 else "in", "scene": s["scene"], "trans": True})
    cues.sort(key=lambda c: c["t"])
    return cues, unknown


def assign(cues):
    """같은 파일 3초 안 반복 → 변형 돌리기 · 0.25초 안 겹친 큐는 뒤 것 뺌."""
    out, dropped, last, run = [], [], {}, {}
    for c in cues:
        if out and c["t"] - out[-1]["t"] < 0.25:
            dropped.append((c["t"], c["k"], "0.25초 안 앞 소리")); continue
        if out and c["t"] - out[-1]["t"] > 3.0:
            run = {}          # 3초 넘게 비면 사슬이 끊긴다(sfx_bus 점검과 같은 기준)
        # 변형이 여럿이면 가장 오래전에 쓴 것부터(같은 소리 단조 반복 줄이기), 3초 안 같은 파일 금지 · 한 사슬에서 같은 파일 3번까지
        cand = [v for v in VAR[c["k"]] if c["t"] - last.get(v[0], -99) >= 3.0 and run.get(v[0], 0) < 3]
        pick = min(cand, key=lambda v: last.get(v[0], -99)) if cand else None
        if not pick:
            dropped.append((c["t"], c["k"], "3초 안 같은 소리 — 변형 없음")); continue
        last[pick[0]] = c["t"]; run[pick[0]] = run.get(pick[0], 0) + 1
        out.append(dict(c, file=pick[0], db=pick[1], al=pick[2]))
    return out, dropped


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cues, unknown = collect()
    placed, dropped = assign(cues)
    # sfx_bus 에 넘길 큐(파일 직접 지정 — 역할표에 임시 등록)
    bus_cues = []
    for i, c in enumerate(placed):
        key = f"x{i}"
        SB.ROLES[key] = (c["file"], c["db"], "peak" if c["al"] == "peak" else "attack", 2)
        q = {"t": c["t"], "role": key}
        if c["k"] in DUR:
            q["dur"] = DUR[c["k"]]
        bus_cues.append(q)
    cue_p = OUT / "sfx_cues.json"
    json.dump(bus_cues, open(cue_p, "w", encoding="utf-8"), ensure_ascii=False)
    sys.argv = ["sfx_bus", str(cue_p), VOICE, str(OUT / "sfx_bus.wav"), "--report", str(OUT / "sfx_report.json")]
    rc = SB.main()
    rep = json.load(open(OUT / "sfx_report.json", encoding="utf-8"))
    rep["dropped_by_mix"] = dropped; rep["unknown_roles"] = unknown
    rep["placed_detail"] = [{k: c[k] for k in ("t", "k", "file", "scene")} for c in placed]
    json.dump(rep, open(OUT / "sfx_report.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("효과음 큐", len(cues), "→ 배치", len(placed), "· 뺌", len(dropped), "· 모르는 역할", len(unknown), "· sfx_bus 종료", rc)

    total = 711.93
    # BGM: 장마다 곡을 이어 붙이고(곡이 짧으면 반복) 2초 교차
    parts = []
    for i, (t0, f) in enumerate(CHAPTERS):
        t1 = CHAPTERS[i + 1][0] if i + 1 < len(CHAPTERS) else total
        parts.append((t0, t1, str(BGM_DIR / f)))
    bgm = np.zeros((int(total * SR) + SR, 2), np.float32)
    XF = 2.0
    for i, (t0, t1, f) in enumerate(parts):
        a = SB.load(f)
        need = int((t1 - t0 + XF) * SR)
        reps = int(np.ceil(need / len(a)))
        seg = np.concatenate([a] * reps)[:need]
        fi = int(XF * SR) if i else int(1.5 * SR)
        seg[:fi] *= np.linspace(0, 1, fi)[:, None]
        if i + 1 < len(parts):
            seg[-int(XF * SR):] *= np.linspace(1, 0, int(XF * SR))[:, None]
        else:
            fo = int(3.0 * SR); seg[-fo:] *= np.linspace(1, 0, fo)[:, None]
        s0 = int(max(0, t0 - (XF if i else 0)) * SR)
        e = min(len(bgm), s0 + len(seg))
        bgm[s0:e] += seg[: e - s0]
    import wave

    def wr(p, x):
        with wave.open(str(p), "wb") as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())
    wr(OUT / "bgm_raw.wav", bgm[: int(total * SR)])
    # 섞기: 목소리 +0 · BGM 은 목소리 아래(사이드체인 압축으로 말할 때 더 낮게) · 효과음 버스 → loudnorm −14 LUFS · 트루피크 −1.5
    fc = ("[0:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,asplit=2[v][vk];"
          "[1:a]volume=-21dB[b0];[b0][vk]sidechaincompress=threshold=0.03:ratio=4:attack=60:release=500[b];"
          "[2:a]volume=0dB[s];[v][b][s]amix=inputs=3:normalize=0:duration=first[m];"
          "[m]loudnorm=I=-14:TP=-1.7:LRA=11[o]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VOICE, "-i", str(OUT / "bgm_raw.wav"), "-i", str(OUT / "sfx_bus.wav"),
                    "-filter_complex", fc, "-map", "[o]", "-ar", "48000", "-c:a", "pcm_s16le", str(OUT / "성제관01_소리.wav")], check=True)
    r = subprocess.run(["ffmpeg", "-nostats", "-i", str(OUT / "성제관01_소리.wav"), "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    print("\n".join(r.stderr.strip().splitlines()[-12:]))


if __name__ == "__main__":
    main()
