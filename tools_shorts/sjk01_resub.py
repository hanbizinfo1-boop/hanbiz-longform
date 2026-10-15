# -*- coding: utf-8 -*-
"""성제관01 쇼츠 다시 굽기(숏폼 세션 10-15) — 화면·소리는 그대로 읽고, 위 제목 띠(TITLES)와 «한 줄» 자막을 다시 굽는다.

    py -3.11 tools_shorts/sjk01_resub.py S1 [S2 …]

자막 규칙(사장님 10-15 «자막은 무조건 한줄로 나오게해줘»):
- 자막은 언제나 **한 줄**. 실제 글자 폭(56px)이 MAX_W 를 넘는 줄은 두 줄로 쌓지 않고 **시간으로 나눈다** —
  앞 조각이 먼저, 뒤 조각은 그 첫 낱말의 강제 정렬 시각(sh_SN.js `words`)에 바뀐다. 자막 시각은 롱폼 정렬값 그대로(다시 받아쓰지 않음).
- 나누는 자리는 말 덩어리 사이(기획 0장 ⑥) — `cut_penalty`. 너무 짧은 조각(MIN_DUR 미만)은 피한다.
- 처음 판(10-15 오전)은 롱폼 조립기가 «띄어쓰기 뺀 18자»로만 나눠 폭 넓은 줄이 화면 양끝까지 닿거나 잘렸다 → 폭으로 잰다.

읽기만: 롱폼 저장소(`핸드오프/역할.local.json` 의 롱폼경로)의 `_tmp/sjk01/render/sh_SN.mp4` · `_tmp/sjk01/shorts/SN_소리.wav` ·
`tools/scenes/sjk01/data/sh_SN.js`. 이 폴더 `_tmp/sjk01/render/sh_SN.mp4` 가 있으면(숏폼 세션이 장면을 고쳐 다시 렌더한 것) 그걸 먼저 쓴다.
쓰기: `납품/성제관01_쇼츠/<같은 이름>.mp4 · .srt`(같은 이름 덮어쓰기) · `_tmp/sjk01/resub_SN.json`(조각마다 시각·폭 기록).
점검: 글꼴에 없는 글자(`tools/glyph_check.py`) · 한 줄 폭이 MAX_W 넘음 · 조각 순서 뒤집힘이면 멈춘다.
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
SIZE, CY = 56, 1440                  # 롱폼 조립기와 같은 모양 — 글꼴·크기·띠 중심
PAD = 14                             # 글자 뒤 반투명 띠 좌우 여백
MAX_W = 900                          # 한 줄 글자 폭 상한(띠 포함 좌우 76px 이상 남김)
MIN_DUR = 0.45                       # 시간으로 나눈 조각이 이보다 짧으면 벌점(깜빡임)
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


def pieces(L):
    """한 자막 줄 → [(t0, t1, 글)] 한 줄짜리 조각들(넓으면 낱말 시각에서 시간으로 나눔)."""
    words = cap_text(L["text"]).split(" ")
    wt = [w["t0"] for w in L["words"]]
    if len(wt) != len(words):
        raise SystemExit(f"낱말 시각 수가 글과 다름 «{L['text']}»")

    def go(a, b, t0, t1):
        txt = " ".join(words[a:b])
        if tw(txt) <= MAX_W:
            return [(t0, t1, txt)]
        best = None
        for k in range(a + 1, b):
            tk = wt[k]
            s = max(tw(" ".join(words[a:k])), tw(" ".join(words[k:b]))) + cut_penalty(words[k - 1], words[k])
            s += 500 * ((tk - t0 < MIN_DUR) + (t1 - tk < MIN_DUR))
            if best is None or s < best[0]:
                best = (s, k, tk)
        if best is None:
            raise SystemExit(f"한 낱말이 한 줄보다 넓음 «{txt}»")
        _, k, tk = best
        return go(a, k, t0, tk) + go(k, b, tk, t1)

    return go(0, len(words), L["t0"], L["end"])


def cap_img(text):
    im = Image.new("RGBA", (W, 160), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    w = tw(text); y = 80
    d.rounded_rectangle((W / 2 - w / 2 - PAD, y - 40, W / 2 + w / 2 + PAD, y + 40), radius=8, fill=(0, 0, 0, 157))
    d.text((W / 2, y), text, font=F, anchor="mm", fill=(255, 255, 255, 255), stroke_width=4, stroke_fill=(0, 0, 0, 255))
    a = np.array(im).astype(np.float32)
    return a[..., [2, 1, 0]], a[..., 3:4] / 255, CY - 80


# 위 제목 — 사장님 10-15 레퍼런스(«하늘을 나는 / 70cm 잉어»): 위 검은 띠 + 굵은 고딕 큰 글씨 두 줄, 윗줄 흰색 · 아랫줄 노랑(핵심).
# «우리는 재미가 위주가 아니라 정보 전달이 중점이기 때문에 저 문구로 시청자들을 잡아야 해» → 짧은 명사구로 «무엇을 얻는지»가 바로 읽히게.
# 장면에 구워진 원래 제목은 띠가 통째로 덮는다(장면 그림은 y 455 아래라 가리지 않음).
TITLE_FONT = "C:/Users/user/AppData/Local/Microsoft/Windows/Fonts/GmarketSansBold.otf"
TITLE_BAND = 420                     # 띠 높이(레퍼런스 화면 높이의 약 21%)
TITLE_MAX, TITLE_W = 124, 960        # 글자 크기 상한 · 한 줄 폭 상한(두 줄 같은 크기)
TITLES = {
    "S1": ("AI 메뉴 설명에", "꼭 넣을 한 줄"),
    "S2": ("팔수록 손해 보는", "메뉴 찾는 법"),
    "S3": ("알바 교육 한 번에", "마감 매뉴얼 비법"),
    "S4": ("지원자 몰리는", "알바 공고 한 줄"),
    "S5": ("리뷰 답글 7시간 반", "30분으로 줄이는 법"),
    "S6": ("계약서 도장 찍기 전", "AI한테 물을 질문 5개"),
}


def title_img(name):
    a, b = TITLES[name]
    size = TITLE_MAX
    while size > 60:
        f = ImageFont.truetype(TITLE_FONT, size)
        if max(_D.textbbox((0, 0), s, font=f)[2] for s in (a, b)) <= TITLE_W:
            break
        size -= 2
    im = Image.new("RGB", (W, TITLE_BAND), (0, 0, 0)); d = ImageDraw.Draw(im)
    gap = int(size * 1.18)
    cy = TITLE_BAND / 2 + 6
    d.text((W / 2, cy - gap / 2), a, font=f, anchor="mm", fill=(255, 255, 255))
    d.text((W / 2, cy + gap / 2), b, font=f, anchor="mm", fill=(255, 214, 10))
    return np.array(im)[..., ::-1].copy(), size


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
        wav = HERE / f"_tmp/sjk01/shorts/{name}_소리.wav"  # 숏폼에서 다시 섞은 소리(sjk01_remix.py)가 있으면 먼저
        if not wav.exists():
            wav = LONG / f"_tmp/sjk01/shorts/{name}_소리.wav"
        rec, caps, n_split = [], [], 0
        for L in sc["lines"]:
            glyph_check(L["text"], FONT)
            ps = pieces(L)
            n_split += len(ps) > 1
            for t0, t1, txt in ps:
                if t1 <= t0 or tw(txt) > MAX_W:
                    raise SystemExit(f"{name} ERROR: 조각 «{txt}» {t0:.2f}~{t1:.2f} 폭 {tw(txt)}")
                rec.append({"t0": t0, "end": t1, "text": txt, "w": tw(txt), "line": L["i"]})
                caps.append((t0, t1, cap_img(txt)))
        json.dump({"src": str(src), "wav": str(wav), "pieces": rec}, open(HERE / f"_tmp/sjk01/resub_{name}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        tband, tsize = title_img(name)
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
            fr[:TITLE_BAND] = tband
            t = i * FD / FN
            for t0, t1, (rgb, al, y0) in caps:
                if t0 <= t < t1:
                    h = al.shape[0]; reg = fr[y0:y0 + h].astype(np.float32)
                    fr[y0:y0 + h] = (rgb * al + reg * (1 - al)).astype(np.uint8); break
            en.stdin.write(fr.tobytes())
        en.stdin.close(); en.wait(); rd.kill()
        with open(OUT / f"{NAMES[name]}.srt", "w", encoding="utf-8", newline="\n") as fo:
            for k, r in enumerate(rec):
                fo.write(f"{k + 1}\n{ts(r['t0'])} --> {ts(r['end'])}\n{r['text']}\n\n")
        print(name, "→", out, f"자막 {len(sc['lines'])}줄 → 한 줄 조각 {len(rec)}개(시간으로 나눈 줄 {n_split}) · 최대 폭 {max(r['w'] for r in rec)}px · 제목 «{' / '.join(TITLES[name])}» {tsize}px · 화면 {'숏폼 재렌더' if src == own else '롱폼 그대로'}")


if __name__ == "__main__":
    main()
