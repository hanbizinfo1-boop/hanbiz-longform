# -*- coding: utf-8 -*-
"""성제관01 쇼츠 조립 — sh_SN.mp4(세로 화면, html_motion) + 자막(중심 y 1440) + 목소리 조각 + 효과음(sfx_bus) + BGM → 납품/성제관01_쇼츠/.

    py -3.11 tools/scenes/sjk01/shorts_assemble.py S1 [S2 …]

자막: 롱폼과 같은 글꼴(GmarketSansMedium)·모양, 세로판이라 56px, 띠 중심 y 1440, 한 줄(18자 넘으면 말 덩어리에서 두 줄).
효과음: sh_SN_events.json → sfx_bus(목소리 대비 크기·겹침 끊기·금지 음색) — 같은 파일 한 편 2번까지(넘으면 다음 변형, 없으면 뺌).
BGM: 그 편 소재가 나온 장의 곡(Mixkit), 목소리 아래.
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.auto import sfx_bus as SB  # noqa: E402
from tools.scenes.sjk01.audio_mix import VAR, role_key, BGM_DIR  # noqa: E402

W, H = 1080, 1920
SHORTS_DIR = ROOT / "_tmp/sjk01/shorts"
OUT = ROOT / "납품/성제관01_쇼츠"
FONT = "C:/Users/user/AppData/Local/Microsoft/Windows/Fonts/GmarketSansMedium.otf"
NAMES = {"S1": "S1_메뉴설명", "S2": "S2_메뉴원가", "S3": "S3_마감매뉴얼", "S4": "S4_채용공고", "S5": "S5_리뷰답글", "S6": "S6_계약서"}
BGM = {"S1": "P1/Mixkit_Dreamy_Jazz.mp3", "S5": "P1/Mixkit_Dreamy_Jazz.mp3", "S3": "P1/Mixkit_Lo-Fi_04.mp3", "S4": "P1/Mixkit_Lo-Fi_04.mp3",
       "S2": "P1/Mixkit_Coffee_or_Tea.mp3", "S6": "P1/Mixkit_Coffee_or_Tea.mp3"}


def sc_of(name):
    t = (ROOT / f"tools/scenes/sjk01/data/sh_{name}.js").read_text(encoding="utf-8")
    return json.loads(t.split("=", 1)[1].strip().rstrip(";"))


def split2(text, n=18):
    s = text.replace(" ", "")
    if len(s) <= n:
        return [text]
    words = text.split(" ")
    best, cut = 1e9, 1
    for k in range(1, len(words)):
        a = len("".join(words[:k])); b = len("".join(words[k:]))
        if abs(a - b) < best:
            best, cut = abs(a - b), k
    return [" ".join(words[:cut]), " ".join(words[cut:])]


def cap_img(text):
    f = ImageFont.truetype(FONT, 56)
    lines = split2(text)
    im = Image.new("RGBA", (W, 260), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    lh = 74; cy = 130
    y0 = cy - lh * (len(lines) - 1) / 2
    for i, ln in enumerate(lines):
        y = y0 + i * lh
        bb = d.textbbox((0, 0), ln, font=f, anchor="ls"); w = bb[2] - bb[0]
        d.rounded_rectangle((W / 2 - w / 2 - 14, y - 40, W / 2 + w / 2 + 14, y + 40), radius=8, fill=(0, 0, 0, 157))
    for i, ln in enumerate(lines):
        y = y0 + i * lh
        d.text((W / 2, y), ln, font=f, anchor="mm", fill=(255, 255, 255, 255), stroke_width=4, stroke_fill=(0, 0, 0, 255))
    a = np.array(im).astype(np.float32)
    return a[..., [2, 1, 0]], a[..., 3:4] / 255, 1440 - 130


def srt(sc, path):
    def ts(t):
        ms = int(round(t * 1000)); return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    with open(path, "w", encoding="utf-8", newline="\n") as fo:
        for k, L in enumerate(sc["lines"]):
            fo.write(f"{k + 1}\n{ts(L['t0'])} --> {ts(L['end'])}\n" + "\n".join(split2(L["text"])) + "\n\n")


def audio(name, sc, outwav):
    ev = ROOT / f"_tmp/sjk01/render/sh_{name}_events.json"
    cues = []
    if ev.exists():
        for e in json.load(open(ev, encoding="utf-8")).get("events", []):
            k = role_key(e["role"])
            if k in VAR:
                cues.append((e["t"], k))
    cues.sort()
    used, placed, dropped, last_t = {}, [], [], -9
    for t, k in cues:
        if t - last_t < 0.25:
            dropped.append((t, k, "0.25초 안")); continue
        pick = next(((f, db, al) for f, db, al in VAR[k] if used.get(f, 0) < 2 and all(not (p["file"] == f and t - p["t"] < 3) for p in placed)), None)
        if not pick:
            dropped.append((t, k, "같은 소리 2번 넘음")); continue
        used[pick[0]] = used.get(pick[0], 0) + 1; last_t = t
        placed.append({"t": t, "file": pick[0], "db": pick[1], "al": pick[2]})
    bus_cues = []
    for i, p in enumerate(placed):
        SB.ROLES[f"y{i}"] = (p["file"], p["db"], "peak" if p["al"] == "peak" else "attack", 2)
        bus_cues.append({"t": p["t"], "role": f"y{i}"})
    voice = SHORTS_DIR / f"{name}_목소리.wav"
    cp = SHORTS_DIR / f"{name}_sfx_cues.json"; json.dump(bus_cues, open(cp, "w", encoding="utf-8"))
    sys.argv = ["sfx_bus", str(cp), str(voice), str(SHORTS_DIR / f"{name}_sfx.wav"), "--report", str(SHORTS_DIR / f"{name}_sfx_report.json")]
    SB.main()
    fc = ("[0:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,asplit=2[v][vk];"
          "[1:a]volume=-21dB,afade=t=in:d=1,afade=t=out:st=" + f"{sc['dur'] - 1.2:.2f}" + ":d=1.2[b0];[b0][vk]sidechaincompress=threshold=0.03:ratio=4:attack=60:release=500[b];"
          "[2:a]volume=0dB[s];[v][b][s]amix=inputs=3:normalize=0:duration=first[m];[m]loudnorm=I=-14:TP=-1.7:LRA=11[o]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(voice), "-stream_loop", "-1", "-i", str(BGM_DIR / BGM[name]), "-i", str(SHORTS_DIR / f"{name}_sfx.wav"),
                    "-filter_complex", fc, "-map", "[o]", "-t", f"{sc['dur']:.3f}", "-ar", "48000", "-c:a", "pcm_s16le", str(outwav)], check=True)
    return placed, dropped


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name in sys.argv[1:]:
        sc = sc_of(name)
        src = ROOT / f"_tmp/sjk01/render/sh_{name}.mp4"
        if not src.exists():
            print("화면 없음", name); continue
        wav = SHORTS_DIR / f"{name}_소리.wav"
        placed, dropped = audio(name, sc, wav)
        caps = [(L["t0"], L["end"], cap_img(L["text"])) for L in sc["lines"]]
        FN, FD = 60000, 1001
        n = int(round(sc["dur"] * FN / FD))
        rd = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(src), "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-"], stdout=subprocess.PIPE)
        out = OUT / f"{NAMES[name]}.mp4"
        en = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", f"{FN}/{FD}", "-i", "-",
                               "-i", str(wav), "-map", "0:v", "-map", "1:a", "-c:v", "h264_nvenc", "-preset", "p6", "-rc", "vbr", "-cq", "18", "-b:v", "0",
                               "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-shortest", str(out)], stdin=subprocess.PIPE)
        last = None
        for i in range(n):
            buf = rd.stdout.read(W * H * 3)
            fr = np.frombuffer(buf, np.uint8).reshape(H, W, 3).copy() if len(buf) == W * H * 3 else last
            last = fr
            t = i * FD / FN
            for t0, t1, (rgb, al, y0) in caps:
                if t0 <= t < t1:
                    h = al.shape[0]; reg = fr[y0:y0 + h].astype(np.float32)
                    fr[y0:y0 + h] = (rgb * al + reg * (1 - al)).astype(np.uint8); break
            en.stdin.write(fr.tobytes())
        en.stdin.close(); en.wait(); rd.kill()
        srt(sc, OUT / f"{NAMES[name]}.srt")
        json.dump({"sfx": placed, "dropped": dropped}, open(SHORTS_DIR / f"{name}_조립보고.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(name, "→", out, f"효과음 {len(placed)} · 뺌 {len(dropped)}")


if __name__ == "__main__":
    main()
