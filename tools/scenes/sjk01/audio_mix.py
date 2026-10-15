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
VOICE = str(ROOT / "_tmp/sjk01/audio/voice_cut.wav")   # 10-15 같은 말 다시 한 곳 3군데 뺀 목소리(cut_repeats.py) — 원본 D:\성제관 1편\성제관 1편.wav
TL = json.load(open(ROOT / "_tmp/sjk01/timeline.json", encoding="utf-8"))
OUT = ROOT / "_tmp/sjk01/final"
BGM_DIR = Path(r"C:\Users\user\Desktop\한비즈-쇼츠광고\소재\BGM후보")
# 장(세계) → 곡. 1~4 손님(휴대폰 속) · 5~7 사람(주방) · 8~10 돈(숫자의 방) · 실험·마무리
# 장(이야기 국면) → 곡(소재/bgm, Mixkit 무료 — 목록.md). 10-15 BGM 규칙 «분위기 5종»: 도입·문제 / 설명 / 따뜻함·사람 / 숫자 / 마무리
BGM_NEW = ROOT / "소재/bgm"
BGM_GAP = 24          # 목소리 말 중앙 − BGM 중앙(dB). 레퍼런스 9채널 실측 중앙값 24.8(범위 18~29), 이전 판 17.6 은 BGM 이 큰 쪽
CHAPTERS = [(0.0, BGM_NEW / "1_Piano_Reflections.mp3"), (66.6, BGM_NEW / "2_Lo-Fi_05.mp3"), (295.3, BGM_NEW / "3_My_Little_Prince.mp3"),
            (463.2, BGM_NEW / "4_Relaxation_2.mp3"), (617.3, BGM_NEW / "5_PlaceIt_World_02.mp3")]
CUT = json.load(open(ROOT / "_tmp/sjk01/audio/cut_report.json", encoding="utf-8"))
CHAPTERS = [(round(t - sum(c["dur"] for c in CUT["cuts"] if t >= c["b"]), 3), f) for t, f in CHAPTERS]   # 컷 전 시각 → 컷 뒤

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

    total = CUT["total_out"]
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
                    "[v][1:a][2:a]amix=inputs=3:normalize=0:duration=first[m]", "-map", "[m]", "-c:a", "pcm_f32le", str(pre)], check=True)
    r = subprocess.run(["ffmpeg", "-nostats", "-i", str(pre), "-af", "loudnorm=I=-14:TP=-1.5:LRA=20:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    js = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
    ln = ("loudnorm=I=-14:TP=-1.5:LRA=20:linear=true:measured_I={input_i}:measured_TP={input_tp}:measured_LRA={input_lra}:"
          "measured_thresh={input_thresh}:offset={target_offset}").format(**js)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(pre), "-af", ln, "-ar", "48000", "-c:a", "pcm_s16le",
                    str(OUT / "성제관01_소리.wav")], check=True)
    r = subprocess.run(["ffmpeg", "-nostats", "-i", str(OUT / "성제관01_소리.wav"), "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    print("\n".join(r.stderr.strip().splitlines()[-12:]))

if __name__ == "__main__":
    main()
