# -*- coding: utf-8 -*-
r"""자동 연출 효과음 버스 — 큐 목록 → 한 편 길이 효과음 wav + 점검 보고 (study/fusion-1013.md 2장).

    python tools/auto/sfx_bus.py <cues.json> <원문(목소리) 오디오/영상> <출력.wav> [--report 보고.json]

cues.json: [{"t": 초, "role": "zoom_in"|…, "file": "이름(선택 — 없으면 역할표)", "dur": 초(펜처럼 길이 고정, 선택)}]

규칙
- 크기: 사장님 최종값(FILE_DB, 목소리 «원음» 대비) − 7 = 완성본 목소리 대비 «들리는 크기». 기준은 그 큐 앞뒤 3초 목소리(50ms RMS 상위 25dB 중앙).
- 들리는 시각: 어택(20ms RMS 가 피크 −20dB 에 처음 닿는 곳)을 큐 시각에(앞당김 최대 80ms) · 휙(peak)은 정점을 큐 시각에.
- 겹침: 앞 소리 꼬리가 다음 소리 어택에 걸치면 어택 10ms 전에서 끊고 60ms 페이드. 큐 간격 0.12초 미만이면 뒤 것을 뺀다(우선순위 낮은 쪽).
- 금지: 마림바·실로폰·합성 벨(SYN_) · 모음1~6 → ERROR.
- 자연 길이 최대 2.5초, 끝 min(길이/3, 0.25초) 페이드. 피크 −6dBFS 상한(짧은 클릭 과증폭 방지).
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402

SR = 48000
TAIL_MAX = 2.5
# 역할 → (파일, 원음 대비 구울 값, 정렬, 우선순위). 쇼츠 4-J 고정표 + 빡이사 사장님 최종값
ROLES = {
    "zoom_in":   ("휙２.mp3", -6, "peak", 2),          # 녹화 화면 확대엔 휙을 작게(05 16:19 사장님 0dB = 원음 −6)
    "zoom_out":  ("휙1.mp3", -6, "peak", 1),
    "brush":     ("SEL_油性マーカー", 3, "attack", 2),  # 밑줄·테두리 긋기
    "brush2":    ("SEL_シャーペンで字を書く", 4, "attack", 2),
    "chip":      ("KN_pepSound1.wav", 8, "attack", 2),
    "chip2":     ("KN_pepSound2.wav", 8, "attack", 2),
    "pop":       ("ML_Cartoon bubbles popping.wav", 5, "attack", 2),
    "chat":      ("채팅 효과음.mp3", 5, "attack", 3),
    "bell":      ("ML_Bell notification", 5, "attack", 3),
    "clear":     ("맑은소리.mp3", 7, "attack", 3),
    "swoosh":    ("SEL_高速移動", 5, "peak", 2),
    "fill":      ("SEL_ゲージ回復1.mp3", 12, "attack", 2),
    "shine":     ("SEL_キラッ1.mp3", -1, "attack", 1),
    "click":     ("마우스 클릭", 5, "attack", 2),
    "levelup":   ("SEL_レベルアップ", 5, "attack", 3),
}
BANNED = re.compile(r"SYN_|marimba|xylo|실로폰|마림바|모음[1-6]", re.I)
_index = None


def find(name):
    global _index
    if Path(name).exists():
        return Path(name)
    if _index is None:
        _index = []
        for root in config.SFX_ROOTS.values():
            if Path(root).exists():
                _index += [p for p in Path(root).rglob("*") if p.suffix.lower() in (".wav", ".mp3", ".ogg", ".m4a")]
    import unicodedata
    key = unicodedata.normalize("NFC", name).lower()
    hits = [p for p in _index if key in unicodedata.normalize("NFC", p.name).lower()]
    hits.sort(key=lambda p: (len(p.name), str(p)))
    if not hits:
        raise FileNotFoundError(name)
    return hits[0]


def load(path, a0=None, a1=None):
    cmd = ["ffmpeg", "-v", "error"]
    if a0 is not None:
        cmd += ["-ss", f"{a0}", "-t", f"{a1 - a0}"]
    cmd += ["-i", str(path), "-vn", "-af", "aresample=48000,aformat=sample_fmts=flt:channel_layouts=stereo", "-f", "f32le", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()


def rms_db(x, win):
    n = max(1, int(SR * win))
    m = x.mean(1)[: len(x) // n * n].reshape(-1, n)
    return 20 * np.log10(np.sqrt((m ** 2).mean(1)) + 1e-9)


def prep(path, rel_audible, voice_ref, dur=None):
    x = load(path)
    a = np.abs(x).max(1)
    x = x[int(np.argmax(a > a.max() * 10 ** (-40 / 20))):]
    e = np.abs(x).max(1); loud = np.where(e > e.max() * 10 ** (-45 / 20))[0]
    end = (loud[-1] + 1) if len(loud) else len(x)
    x = x[: int(dur * SR)] if dur else x[: min(end, int(TAIL_MAX * SR))]
    fo = min(len(x) // 3, int(0.25 * SR))
    if fo > 0:
        x[-fo:] *= (np.linspace(1, 0, fo) ** 2)[:, None]
    f50 = rms_db(x, 0.05)
    x *= 10 ** ((voice_ref + rel_audible - f50.max()) / 20)
    x *= min(1.0, 0.5 / (np.abs(x).max() + 1e-9))
    f20 = rms_db(x, 0.02)
    pk = int(np.argmax(f20))
    att = int(np.argmax(f20 >= f20[pk] - 20))
    return x, att * 0.02, (pk + 0.5) * 0.02


def main():
    args = sys.argv[1:]
    rep_p = args[args.index("--report") + 1] if "--report" in args else None
    cues_p, voice_p, out = args[:3]
    cues = sorted(json.load(open(cues_p, encoding="utf-8")), key=lambda c: c["t"])
    voice = load(voice_p)
    total = len(voice)
    vdb = rms_db(voice, 0.05)
    errs, warns, placed = [], [], []
    # 0.12초 안에 겹치는 큐 → 우선순위 낮은 쪽 뺌
    keep = []
    for c in cues:
        r = ROLES[c["role"]]
        c["_prio"] = r[3]
        if keep and c["t"] - keep[-1]["t"] < 0.12:
            if c["_prio"] > keep[-1]["_prio"]:
                warns.append(f"{keep[-1]['t']:.2f} {keep[-1]['role']} 뺌(0.12초 안 {c['role']})"); keep[-1] = c
            else:
                warns.append(f"{c['t']:.2f} {c['role']} 뺌(0.12초 안 {keep[-1]['role']})")
            continue
        keep.append(c)
    cache = {}
    for c in keep:
        fname, raw_db, align, _ = ROLES[c["role"]]
        fname = c.get("file", fname)
        if BANNED.search(fname):
            errs.append(f"{c['t']:.2f} 금지 음색 {fname}"); continue
        path = find(fname)
        if BANNED.search(str(path)):
            errs.append(f"{c['t']:.2f} 금지 음색/폴더 {path}"); continue
        rel = c.get("db", raw_db - 7)                    # 완성본 목소리 대비 들리는 크기
        i0, i1 = int(max(0, c["t"] - 3) / 0.05), int(min(total / SR, c["t"] + 3) / 0.05)
        seg = vdb[i0:i1]
        ref = float(np.median(seg[seg > seg.max() - 25])) if len(seg) else -20.0
        key = (str(path), round(rel, 1), round(ref), c.get("dur"))
        if key not in cache:
            cache[key] = prep(path, rel, ref, c.get("dur"))
        x, att, pk = cache[key]
        lead = pk if align == "peak" else min(att, 0.08)
        st = int((c["t"] - lead) * SR)
        placed.append(dict(t=c["t"], role=c["role"], file=path.name, st=st, x=x.copy(), att=st + int(att * SR), rel=rel))
    # 겹침: 다음 소리 어택 10ms 전에서 끊고 60ms 페이드
    for a, b in zip(placed, placed[1:]):
        cut = b["att"] - int(0.010 * SR)
        if a["st"] + len(a["x"]) > cut:
            keepn = max(0, cut - a["st"])
            if keepn < int(0.15 * SR):
                warns.append(f"{a['t']:.2f} {a['role']} 0.15초 안에서 잘림({keepn / SR:.2f}초) — 큐 배치 확인")
            a["x"] = a["x"][:keepn]
            fo = min(len(a["x"]), int(0.06 * SR))
            if fo:
                a["x"][-fo:] *= np.linspace(1, 0, fo)[:, None]
    # 같은 파일 연속 · 3초 사슬 3번
    for a, b in zip(placed, placed[1:]):
        if a["file"] == b["file"] and b["t"] - a["t"] < 3.0:      # 5-2 «바로 연달아»(3초 안)
            errs.append(f"{b['t']:.2f} 같은 소리 연속 {b['file']}")
    for i, p in enumerate(placed):
        chain = [p]
        for q in placed[i + 1:]:
            if q["t"] - chain[-1]["t"] > 3:
                break
            chain.append(q)
        n = sum(1 for q in chain if q["file"] == p["file"])
        if n > 3:
            errs.append(f"{p['t']:.2f} 3초 사슬에서 {p['file']} {n}번")
    bus = np.zeros((total, 2), np.float32)
    for p in placed:
        s = max(0, p["st"]); x = p["x"][s - p["st"]:]
        e = min(total, s + len(x))
        bus[s:e] += x[: e - s]
    pk = float(np.abs(bus).max()) if len(bus) else 0
    if pk > 0.89:
        bus *= 0.89 / pk; warns.append(f"버스 피크 {20 * np.log10(pk):.1f}dBFS → −1dB 로 내림")
    import wave
    with wave.open(out, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(bus, -1, 1) * 32767).astype("<i2").tobytes())
    rels = [p["rel"] for p in placed]
    rep = dict(cues=len(cues), placed=len(placed), errors=errs, warnings=warns,
               rel_spread_db=(max(rels) - min(rels)) if rels else 0,
               list=[dict(t=p["t"], role=p["role"], file=p["file"], rel=p["rel"], len=round(len(p["x"]) / SR, 2)) for p in placed])
    if rep_p:
        json.dump(rep, open(rep_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"큐 {len(cues)} → 배치 {len(placed)} · ERROR {len(errs)} · WARN {len(warns)} · 크기 폭 {rep['rel_spread_db']:.1f}dB")
    for e in errs:
        print("  ERROR", e)
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
