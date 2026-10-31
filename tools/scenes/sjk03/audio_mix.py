# -*- coding: utf-8 -*-
"""성제관03 소리(2편 audio_mix.py 복사 — 경로·BGM 장만 3편) — 목소리(정본 녹음) + 효과음(장면 EVENTS → sfx_bus) + BGM(장마다 한 곡, 목소리 아래) → −14 LUFS.

    py -3.11 tools/scenes/sjk03/audio_mix.py            → _tmp/sjk03/final/성제관03_소리.wav (+ 효과음 버스·보고)

효과음: 장면마다 _tmp/sjk03/render/sNN_events.json(html_motion) 의 {t, role} 를 «장면 시작 − pre + t» 로 옮긴다.
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
VOICE = str(ROOT / "_tmp/sjk03/audio/voice.wav")   # 녹음 정본 D:\성제관 3편\사장의파트너 3편.wav 사본(컷 바꾸지 않음)
TL = json.load(open(ROOT / "_tmp/sjk03/timeline.json", encoding="utf-8"))
OUT = ROOT / "_tmp/sjk03/final"
BGM_DIR = Path(r"C:\Users\user\Desktop\한비즈-쇼츠광고\소재\BGM후보")
# 장(세계) → 곡. 1~4 손님(휴대폰 속) · 5~7 사람(주방) · 8~10 돈(숫자의 방) · 실험·마무리
# 장(이야기 국면) → 곡(소재/bgm, Mixkit 무료 — 목록.md). 10-15 BGM 규칙 «분위기 5종»: 도입·문제 / 설명 / 따뜻함·사람 / 숫자 / 마무리
BGM_NEW = ROOT / "소재/bgm"
BGM_GAP = 19          # 목소리 말 중앙 − BGM 중앙(dB). 10-16 사장님 «다음에는 19db정도로 줄여줘»(24 → 19, BGM 5dB 크게). 레퍼런스 9채널 실측 18~29 안
# 2편(연출설계 8장): 1편 5곡(Piano Reflections · Lo-Fi 05 · My Little Prince · Relaxation 2 · PlaceIt World 02) 빼고 나머지에서 —
# 흐린 낮의 긴장 → 새벽에 풀림. 장 경계 = 대본 장([00]~[02] 훅·문제 / [03]~[04] 상담·약속 / [05] 글 / [06] 숫자 / [07] 시간 / [08] 정리·끝)
# 3편: 1편 5곡 · 2편 6곡을 빼고 남은 4곡(앞 편과 같은 분위기·도구 금지 — 절대금지 10-16). 장 = 연출표 진행표 카드 장 시작
#   훅·가격(설명 — 로파이 가볍게) / 광고(숫자·분석) / 단골(따뜻함) / 정리·끝(마무리·희망)
# 10-31 사장님 «BGM이 너무 장난스러워서» → 로파이(Lo-Fi 02)·신스웨이브(Better Times) 빼고 잔잔한 곡만:
#   훅·가격 Pilates and Yoga(피아노+신스 앰비언트) / 광고·단골 Don't Leave Me Tonight(조용한 기타) / 정리·끝 Jump into Hope(신스 앰비언트 — 2편 끝 곡, 잔잔한 미사용 곡이 더 없어 다시 씀)
CHAPTERS = [(0.0, BGM_NEW / "4_Pilates_and_Yoga.mp3"), (254.4, BGM_NEW / "3_Dont_Leave_Me_Tonight.mp3"),
            (515.64, BGM_NEW / "5_Jump_into_Hope.mp3")]
TOTAL = TL[-1]["t1"] if TL else 547.213

# 역할 → [(파일, 원음 대비 구울 dB, 정렬)] 변형 순서
# 10-31 사장님 «효과음 대비 목소리가 작아서 목소리에 몰입이 안되는거» · «효과음이 톡톡 튀는 효과음이 많아서»
#   → 반짝(キラッ)·카툰 팝·게임 게이지·오답 삑·맑은 띵 같은 밝고 튀는 소리를 빼고, 낮고 부드러운 소리(바람 휙·천 펄럭·종이·연필)로.
#   반짝(shine)은 소리 없이(SKIP). 효과음 버스 전체도 SFX_GAIN 만큼 낮춘다.
VAR = {
    "in": [("휙２.mp3", 0, "peak"), ("air sweep", 0, "attack"), ("휙1.mp3", 3, "peak"), ("두꺼운 바람", 0, "attack")],
    "sweep": [("air sweep", 0, "attack"), ("두꺼운 바람", 0, "attack"), ("휙1.mp3", 3, "peak"), ("휙２.mp3", 0, "peak")],
    "card": [("SEL_マントを翻す", 0, "attack"), ("휙２.mp3", -3, "peak"), ("종이소리 화면전환", -2, "attack"), ("air sweep", -3, "attack")],
    "msg": [("채팅 효과음", 0, "attack"), ("SEL_マントを翻す", 0, "attack")],
    "big": [("두꺼운 바람", 2, "attack"), ("휙1.mp3", 4, "peak")],
    "ok": [("SEL_シャーペンで字を書く", 2, "attack"), ("24. 연필", 2, "attack"), ("볼펜소리", 2, "attack")],
    "no": [("KN_lowDown", 2, "attack"), ("종이소리", 0, "attack")],
    "miss": [("KN_lowDown", 2, "attack")],
    "type": [("SEL_キーボード2", 3, "attack"), ("SEL_キーボード1", 3, "attack"), ("Mechanical Keyboard Click 01", 2, "attack")],
    "marker": [("SEL_シャーペンで字を書く", 2, "attack"), ("24. 연필", 2, "attack"), ("볼펜소리", 2, "attack"), ("SEL_油性マーカーで字を書く", 0, "attack")],
    "pen": [("SEL_シャーペンで字を書く", 2, "attack"), ("24. 연필", 2, "attack")],
    "stamp": [("도장.mp3", 3, "attack")],
    "page": [("종이넘기는 소리", 0, "attack"), ("종이소리 화면전환", 0, "attack")],
    "gauge": [("ML_Air woosh", 0, "attack"), ("air sweep", -2, "attack"), ("두꺼운 바람", -2, "attack")],
    "click": [("15. 마우스클릭", -2, "attack"), ("마우스 클릭", -2, "attack")],
    "shutter": [("Lightweight sliding door close", 2, "attack")],
    "paper": [("종이넘기는 소리", 0, "attack"), ("종이소리 화면전환", 0, "attack"), ("종이소리", 0, "attack")],
    "coin": [("ML_Bag of coins touch", 2, "attack"), ("KN_glass_004", 0, "attack")],
    "marble": [("KN_drop_001", 3, "attack"), ("KN_drop_002", 3, "attack")],
    "water": [("21. 물방울1", 3, "attack"), ("23. 물방울2", 3, "attack")],
    "phone": [("전화벨소리", 0, "attack")],
    "shine": [("air sweep", -4, "attack")],
}
SKIP = {"shine"}            # 반짝 = 소리 없음(10-31 «톡톡 튀는 효과음»)
SFX_GAIN = -5.0             # 효과음 버스 전체(dB) — 10-31 «효과음 대비 목소리가 작아서»
ALIAS = {"msg": "msg", "card": "card", "big": "big", "in": "in", "sweep": "sweep", "chip": "card", "pop": "card", "bell": "msg", "print": "page", "tear": "paper"}
DUR = {"marker": 0.35, "phone": 2.4}


def role_key(r):
    r = r[:-3] if r.endswith("_in") else r
    return ALIAS.get(r, r)


def collect():
    cues, unknown = [], []
    for s in TL:
        p = ROOT / f"_tmp/sjk03/render/s{s['scene']:02d}_events.json"
        if not p.exists():
            continue
        base = s["t0"] - s["pre"]
        for e in json.load(open(p, encoding="utf-8")).get("events", []):
            k = role_key(e["role"])
            t = base + e["t"]
            if k in SKIP:
                continue
            if k not in VAR:
                unknown.append((round(t, 2), e["role"])); continue
            if t < s["t0"] - s["pre"] or t > s["t1"] + s["post"]:
                continue
            cues.append({"t": round(t, 3), "k": k, "scene": s["scene"]})
    # 2편 전환 소리(전환 종류마다 뜻에 맞게 — 컷·탈색·디졸브는 소리 없음, 09-22 «컷마다 전환음 금지»)
    plan_p = ROOT / "_tmp/sjk03/final/v2_plan.json"
    trans = json.load(open(plan_p, encoding="utf-8"))["trans"] if plan_p.exists() else [s["trans_in"] for s in TL]
    TSND = {"shut_dn": "shutter", "shut_up": "shutter", "slide": "sweep", "flip": "paper", "into": "in", "match": "in"}
    for k, s in enumerate(TL):
        if k and trans[k] in TSND:
            cues.append({"t": round(s["t0"] - 0.05, 3), "k": TSND[trans[k]], "scene": s["scene"], "trans": True})
    cues.sort(key=lambda c: c["t"])
    return cues, unknown


_ALEN = {}


def audible_len(v, k):
    """변형 v 를 큐 시각에 맞춰 놓았을 때 «큐 시각 → 들리는 끝»(20ms RMS 가 피크 −15dB 아래로 내려가는 곳) 초.
    그 뒤 꼬리는 sfx_bus 가 다음 소리 앞에서 0.2초에 걸쳐 줄인다(자연 감쇠처럼 — 뚝 끊김 아님)."""
    key = (v[0], v[2], DUR.get(k))
    if key not in _ALEN:
        x, att, pk = SB.prep(SB.find(v[0]), 0, -20.0, DUR.get(k))
        f20 = SB.rms_db(x, 0.02)
        ae = (int(np.where(f20 >= f20.max() - 15)[0][-1]) + 1) * 0.02
        lead = pk if v[2] == "peak" else min(att, 0.08)
        _ALEN[key] = ae - lead
    return _ALEN[key]


def assign(cues):
    """같은 파일 3초 안 반복 → 변형 돌리기 · 0.25초 안 겹친 큐는 뒤 것 뺌.
    10-15 «효과음이 나오는 도중에 짤리는 듯한 지점» → 다음 큐 전에 들리는 끝까지 나오는 변형만 고른다.
    맞는 변형이 없으면 가장 짧은 것 — 그래도 0.12초 넘게 잘리면 그 큐를 뺀다(잘라 넣지 않는다, 절대금지 10-07 «자연 길이»)."""
    out, dropped, last, run = [], [], {}, {}
    # 부각(big — S.focus)은 먼저 자리 잡는다: 변형을 미리 정하고, 그 소리가 들리는 동안 오는 다른 큐는 뺀다(부각음을 자르지 않는다)
    hold, bigpick, blast = [], {}, {}
    for c in cues:
        if c["k"] != "big":
            continue
        if hold and c["t"] < hold[-1][1]:
            continue                                   # 앞 부각음이 울리는 중 — 아래에서 뺀다
        if any(0 < c["t"] - d["t"] < 0.25 for d in cues if d is not c):
            continue                                   # 10-20: 0.25초 안 앞 소리로 어차피 빠질 부각음 — 자리를 잡으면 뒤 2초가 통째로 비었다(s23·s64)
        vs = [v for v in VAR["big"] if c["t"] - blast.get(v[0], -99) >= 3.0] or VAR["big"]
        v = min(vs, key=lambda v: blast.get(v[0], -99))
        blast[v[0]] = c["t"]; bigpick[id(c)] = v
        hold.append((c["t"], c["t"] + audible_len(v, "big") + 0.03))
    keep = []
    for c in cues:
        if id(c) not in bigpick and any(a < c["t"] < b for a, b in hold):
            dropped.append((c["t"], c["k"], "부각음이 울리는 중")); continue
        keep.append(c)
    cues = keep
    for i, c in enumerate(cues):
        if out and c["t"] - out[-1]["t"] < 0.25:
            dropped.append((c["t"], c["k"], "0.25초 안 앞 소리")); continue
        if out and c["t"] - out[-1]["t"] > 3.0:
            run = {}          # 3초 넘게 비면 사슬이 끊긴다(sfx_bus 점검과 같은 기준)
        nxt = next((d["t"] for d in cues[i + 1:] if d["t"] - c["t"] >= 0.25), None)
        gap = (nxt - c["t"] - 0.03) if nxt is not None else 99
        # 변형이 여럿이면 가장 오래전에 쓴 것부터(같은 소리 단조 반복 줄이기), 3초 안 같은 파일 금지 · 한 사슬에서 같은 파일 3번까지
        cand = [v for v in VAR[c["k"]] if c["t"] - last.get(v[0], -99) >= 3.0 and run.get(v[0], 0) < 3]
        if id(c) in bigpick:
            cand = [bigpick[id(c)]]; gap = 99      # 부각음은 미리 정한 변형 그대로(뒤 큐는 이미 비웠다)
        if not cand:
            dropped.append((c["t"], c["k"], "3초 안 같은 소리 — 변형 없음")); continue
        fit = [v for v in cand if audible_len(v, c["k"]) <= gap]
        if fit:
            pick = min(fit, key=lambda v: last.get(v[0], -99))
        else:
            pick = min(cand, key=lambda v: audible_len(v, c["k"]))
            if audible_len(pick, c["k"]) - gap > 0.12:
                dropped.append((c["t"], c["k"], f"다음 소리 전에 안 끝남({audible_len(pick, c['k']):.2f}>{gap:.2f}초)")); continue
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

    total = TOTAL
    # BGM(10-15 규칙 — tools/data/bgm-rules-1015.md, 레퍼런스 9채널 실측 _tmp/bgm_ref/측정.md):
    # 장(이야기 국면)마다 분위기 맞는 곡 하나 · 곡 안 반복과 곡 바뀜 모두 3초 같은 힘 교차 · 곡마다 크기 먼저 맞춤 ·
    # 목소리 말 중앙보다 BGM_GAP dB 아래로 «고르게»(말할 때 누르는 덕킹 없음 — 레퍼런스 쉼 레벨 평탄 ±2dB).
    import soundfile as sf

    def mdb(x, w=0.05):
        m = x.mean(1) if x.ndim > 1 else x
        n = int(w * SR); k = len(m) // n
        return 20 * np.log10(np.sqrt((m[:k * n].reshape(k, n) ** 2).mean(1)) + 1e-9)

    parts = []
    for i, (t0, f) in enumerate(CHAPTERS):
        t1 = CHAPTERS[i + 1][0] if i + 1 < len(CHAPTERS) else total
        parts.append((t0, t1, str(f)))
    XF = 3.0
    xs = int(XF * SR)
    eq = lambda n: (np.sqrt(np.linspace(0, 1, n))[:, None], np.sqrt(np.linspace(1, 0, n))[:, None])
    bgm = np.zeros((int(total * SR) + SR, 2), np.float32)
    for i, (t0, t1, f) in enumerate(parts):
        a = SB.load(f)
        d = mdb(a); live = np.where(d > d.max() - 40)[0]               # 앞뒤 무음 잘라 반복 이음매에 빈틈 없게
        a = a[live[0] * int(0.05 * SR):(live[-1] + 1) * int(0.05 * SR)]
        d = mdb(a); a = a * 10 ** ((-30 - np.median(d[d > d.max() - 30])) / 20)   # 곡마다 크기 맞춤(50ms RMS 중앙 −30)
        need = int((t1 - t0 + XF) * SR)
        seg = a.copy()
        while len(seg) < need:                                          # 곡 반복도 3초 교차(뚝 이어짐 없음)
            fin, fout = eq(xs)
            seg = np.concatenate([seg[:-xs], seg[-xs:] * fout + a[:xs] * fin, a[xs:]])
        seg = seg[:need].copy()
        fin, fout = eq(xs)
        if i:
            seg[:xs] *= fin
        else:
            f0 = int(1.5 * SR); seg[:f0] *= np.linspace(0, 1, f0)[:, None]
        if i + 1 < len(parts):
            seg[-xs:] *= fout
        else:
            fo = int(3.0 * SR); seg[-fo:] *= np.linspace(1, 0, fo)[:, None]
        s0 = int(max(0, t0 - (XF if i else 0)) * SR)
        e = min(len(bgm), s0 + len(seg))
        bgm[s0:e] += seg[: e - s0]
    bgm = bgm[: int(total * SR)]
    v, _ = sf.read(VOICE, dtype="float32")
    dv = mdb(v); sp = float(np.median(dv[dv > np.percentile(dv, 90) - 20]))
    db = mdb(bgm); bm = float(np.median(db[db > -80]))
    g = sp - BGM_GAP - bm
    bgm *= 10 ** (g / 20)
    print(f"BGM: 목소리 말 중앙 {sp:.1f}dB · BGM 중앙 {bm + g:.1f}dB(목소리 −{BGM_GAP}dB) · 곡 {[Path(p[2]).name for p in parts]}")
    sf.write(OUT / "bgm_raw.wav", bgm, SR, subtype="FLOAT")
    # 섞기: 목소리 + BGM(이미 크기 맞춤, 덕킹 없음) + 효과음 → 2번 재는 loudnorm(linear — 소리끼리 비율 그대로) −14 LUFS · 트루피크 −1.5
    pre = OUT / "mix_pre.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VOICE, "-i", str(OUT / "bgm_raw.wav"), "-i", str(OUT / "sfx_bus.wav"),
                    "-filter_complex", "[0:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo[v];"
                    f"[2:a]volume={SFX_GAIN}dB[s];[v][1:a][s]amix=inputs=3:normalize=0:duration=first[m]", "-map", "[m]", "-c:a", "pcm_f32le", str(pre)], check=True)
    r = subprocess.run(["ffmpeg", "-nostats", "-i", str(pre), "-af", "loudnorm=I=-14:TP=-2.3:LRA=20:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    js = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
    ln = ("loudnorm=I=-14:TP=-2.3:LRA=20:linear=true:measured_I={input_i}:measured_TP={input_tp}:measured_LRA={input_lra}:"
          "measured_thresh={input_thresh}:offset={target_offset}").format(**js)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(pre), "-af", ln, "-ar", "48000", "-c:a", "pcm_s16le",
                    str(OUT / "성제관03_소리.wav")], check=True)
    r = subprocess.run(["ffmpeg", "-nostats", "-i", str(OUT / "성제관03_소리.wav"), "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    print("\n".join(r.stderr.strip().splitlines()[-12:]))

if __name__ == "__main__":
    main()
