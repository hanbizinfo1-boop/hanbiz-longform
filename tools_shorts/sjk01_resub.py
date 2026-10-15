# -*- coding: utf-8 -*-
"""성제관01 쇼츠 다시 굽기(숏폼 세션 10-15) — 롱폼 세션이 만든 화면·소리는 그대로 읽고, 자막만 폭 기준으로 다시 굽는다.

    py -3.11 tools_shorts/sjk01_resub.py S1 [S2 …]

왜: 롱폼 조립기(`tools/scenes/sjk01/shorts_assemble.py`)는 띄어쓰기 뺀 18자 넘을 때만 두 줄로 나눠서,
18자 이하인데 폭이 넓은 줄(«우리 가게에 진짜 있는 것만 남기셔야 합니다» 등)이 화면 양끝까지 닿거나 잘렸다.
→ 실제 글자 폭(56px)을 재서 MAX_W 를 넘으면 두 줄. 나누는 자리는 양쪽 폭이 비슷한 띄어쓰기(⑥ — 결과는 사람이 줄마다 본다).

읽기만: 롱폼 저장소(`핸드오프/역할.local.json` 의 롱폼경로)의 `_tmp/sjk01/render/sh_SN.mp4` · `_tmp/sjk01/shorts/SN_소리.wav` ·
`tools/scenes/sjk01/data/sh_SN.js`. 이 폴더 `_tmp/sjk01/render/sh_SN.mp4` 가 있으면(숏폼 세션이 장면을 고쳐 다시 렌더한 것) 그걸 먼저 쓴다.
쓰기: `납품/성제관01_쇼츠/<같은 이름>.mp4 · .srt`(같은 이름 덮어쓰기) · `_tmp/sjk01/resub_SN.json`(줄마다 폭·나눔 기록).
점검: 글꼴에 없는 글자(`tools/glyph_check.py`) · 자막 띠가 판 밖·가장자리 60px 안으로 들어가면 멈춘다.
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parents[1]
LONG = Path(json.loads((HERE / "핸드오프/역할.local.json").read_text(encoding="utf-8"))["롱폼경로"])
sys.path.insert(0, str(HERE))
from tools.glyph_check import check as glyph_check  # noqa: E402

W, H = 1080, 1920
FONT = "C:/Users/user/AppData/Local/Microsoft/Windows/Fonts/GmarketSansMedium.otf"
SIZE, LH, CY = 56, 74, 1440          # 롱폼 조립기와 같은 모양 — 글꼴·크기·줄 간격·띠 중심
PAD = 14                             # 글자 뒤 반투명 띠 좌우 여백
MAX_W = 900                          # 글자 폭이 이걸 넘으면 두 줄(띠 포함 좌우 76px 이상 남김)
EDGE = 60                            # 띠가 이보다 가장자리에 붙으면 ERROR
NAMES = {"S1": "S1_메뉴설명", "S2": "S2_메뉴원가", "S3": "S3_마감매뉴얼", "S4": "S4_채용공고", "S5": "S5_리뷰답글", "S6": "S6_계약서"}
OUT = HERE / "납품/성제관01_쇼츠"
F = ImageFont.truetype(FONT, SIZE)
_D = ImageDraw.Draw(Image.new("L", (8, 8)))


def tw(s):
    b = _D.textbbox((0, 0), s, font=F, anchor="ls")
    return b[2] - b[0]


def cap_text(s):
    """롱폼 assemble.cap_text 와 같은 규칙 — 끝 마침표 하나만 뺀다(물음표·말줄임표 그대로, 사장님 10-15)."""
    s = s.strip()
    return s[:-1] if s.endswith(".") and not s.endswith("..") else s


NOUN_PAIRS = {("리뷰", "답글")}       # 명사+명사 — 이 건에서 본 것(늘어나면 여기에)
BOUND = ("것", "개", "번", "분", "위", "수", "줄")  # 앞말에 붙어야 뜻이 되는 말(의존명사·단위·«맨 위»)


def cut_penalty(prev, nxt):
    """⑥ 명사+명사·꾸미는 말+받는 말·수+단위 사이에서 자르지 않는다(숏폼 세션 반려 «인스턴트 / 양식»)."""
    p = 0
    if len(prev) == 1 or nxt in ("할", "될"):  # 한·열·맨 — 한 글자 수·관형사는 뒷말과, «-야 할·-야 될»은 앞말과 붙는다
        p += 1000
    if nxt[:1] in BOUND and len(nxt) <= 3:
        p += 1000
    if any(prev.startswith(a) and nxt.startswith(b) for a, b in NOUN_PAIRS):
        p += 1000
    return p


def split2(text):
    if tw(text) <= MAX_W:
        return [text]
    words = text.split(" ")
    best, cut = 1e9, 1
    for k in range(1, len(words)):
        a, b = tw(" ".join(words[:k])), tw(" ".join(words[k:]))
        if max(a, b) > MAX_W:
            continue
        s = max(a, b) + cut_penalty(words[k - 1], words[k])
        if s < best:
            best, cut = s, k
    return [" ".join(words[:cut]), " ".join(words[cut:])]


def cap_img(lines):
    im = Image.new("RGBA", (W, 260), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cy = 130; y0 = cy - LH * (len(lines) - 1) / 2
    for i, ln in enumerate(lines):
        y = y0 + i * LH; w = tw(ln)
        d.rounded_rectangle((W / 2 - w / 2 - PAD, y - 40, W / 2 + w / 2 + PAD, y + 40), radius=8, fill=(0, 0, 0, 157))
    for i, ln in enumerate(lines):
        d.text((W / 2, y0 + i * LH), ln, font=F, anchor="mm", fill=(255, 255, 255, 255), stroke_width=4, stroke_fill=(0, 0, 0, 255))
    a = np.array(im).astype(np.float32)
    return a[..., [2, 1, 0]], a[..., 3:4] / 255, CY - 130


def sc_of(name):
    t = (LONG / f"tools/scenes/sjk01/data/sh_{name}.js").read_text(encoding="utf-8")
    return json.loads(t.split("=", 1)[1].strip().rstrip(";"))


def ts(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    (HERE / "_tmp/sjk01").mkdir(parents=True, exist_ok=True)
    for name in sys.argv[1:]:
        sc = sc_of(name)
        own = HERE / f"_tmp/sjk01/render/sh_{name}.mp4"
        src = own if own.exists() else LONG / f"_tmp/sjk01/render/sh_{name}.mp4"
        wav = LONG / f"_tmp/sjk01/shorts/{name}_소리.wav"
        rec, caps, err = [], [], []
        for L in sc["lines"]:
            txt = glyph_check(cap_text(L["text"]), FONT)
            lines = split2(txt)
            wmax = max(tw(x) for x in lines)
            if W / 2 - wmax / 2 - PAD < EDGE or len(lines) > 2:
                err.append(f"자막 폭 {wmax}px · {len(lines)}줄 «{txt}»")
            rec.append({"t0": L["t0"], "end": L["end"], "lines": lines, "w": wmax})
            caps.append((L["t0"], L["end"], cap_img(lines)))
        if err:
            raise SystemExit(f"{name} ERROR:\n  " + "\n  ".join(err))
        json.dump({"src": str(src), "wav": str(wav), "lines": rec}, open(HERE / f"_tmp/sjk01/resub_{name}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
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
            fr = np.frombuffer(buf, np.uint8).reshape(H, W, 3).copy() if len(buf) == W * H * 3 else last.copy()
            last = fr
            t = i * FD / FN
            for t0, t1, (rgb, al, y0) in caps:
                if t0 <= t < t1:
                    h = al.shape[0]; reg = fr[y0:y0 + h].astype(np.float32)
                    fr[y0:y0 + h] = (rgb * al + reg * (1 - al)).astype(np.uint8); break
            en.stdin.write(fr.tobytes())
        en.stdin.close(); en.wait(); rd.kill()
        with open(OUT / f"{NAMES[name]}.srt", "w", encoding="utf-8", newline="\n") as fo:
            for k, r in enumerate(rec):
                fo.write(f"{k + 1}\n{ts(r['t0'])} --> {ts(r['end'])}\n" + "\n".join(r["lines"]) + "\n\n")
        two = sum(len(r["lines"]) == 2 for r in rec)
        print(name, "→", out, f"자막 {len(rec)}줄 · 두 줄 {two} · 최대 폭 {max(r['w'] for r in rec)}px · 화면 {'숏폼 재렌더' if src == own else '롱폼 그대로'}")


if __name__ == "__main__":
    main()
