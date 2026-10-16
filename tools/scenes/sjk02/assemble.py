# -*- coding: utf-8 -*-
"""성제관02 롱폼 조립 — 장면 클립 53개 → 전환 → 자막 굽기 → (자막본 · 자막없음본) 영상만. 소리는 audio_mix.py, 합치기는 mux.

    py -3.11 tools/scenes/sjk02/assemble.py [--from 초] [--to 초] [--out 이름] [--preview]

장면 클립: _tmp/sjk02/render/sNN.mp4 — 프레임 0 = 장면 시작(t0) − pre. (html_motion 장면은 그렇게 렌더되고, 블렌더·사진 장면도 같은 규칙으로 만든다.)
전환(timeline.json trans_in): cut·cont = 경계에서 바로 / dissolve · push(종이 밀어내기) · zoom(자료 속으로) · split(반으로 갈라짐) · wipe(지우개) = 경계 가운데 0.6초.
자막: 사장님 한비즈 강의 자막 실측 모양(compose.caption_style) — GmarketSansMedium 48 · 흰 글자+검정 테두리 4 · 검정 띠 61.6% · 띠 중심 y 1011.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.auto.compose import Captions  # noqa: E402
import re  # noqa: E402


# 화면 자막에서만 바꿔 보이는 말(녹음원고·강제 정렬은 말한 그대로) — 절대금지 10-16 «남는 돈 이라는 말은 수익이라는 단어로 항상 대체해서써줘».
# 편집본 녹음에 «남는 돈/남은 돈»이 6번 남아 있다(녹음이 규칙보다 먼저) → 자막은 «수익». 30_결과 «애매해서 정한 것».
SHOW = [("실제로 남은 돈", "실제 수익"), ("통장에 남는 돈은", "통장 수익은"), ("남는 돈", "수익"), ("남은 돈", "수익")]


def cap_text(t):
    """자막 글 — SHOW 바꿔 보이기 + 끝 마침표 하나만 뺀다(10-15 «자막에 마지막 마침표 다 제거해줘», 말줄임표·물음표는 그대로)."""
    for a, b in SHOW:
        t = t.replace(a, b)
    return re.sub(r"(?<!\.)\.\s*$", "", t.strip())


W, H = 1920, 1080
FN, FD = 60000, 1001
FPS = FN / FD
D = 0.36                                  # 2편 전환 0.3~0.4초(연출설계 2장)
# v2 전환 표 — 원테이크(cont)만 그대로, 나머지 경계는 모두 빠른 전환. 원래 정한 전환(dissolve·push·zoom·split·wipe)은 살리고
# «cut» 이던 경계에 아래 순서로 돌려 넣는다(같은 전환 연달아 금지).
def _plan():
    """2편: timeline.json 의 trans_in 을 그대로(연출설계 3-3 전환) — 같은 전환이 연달아 나오면 뒤 것은 cut."""
    out, prev = [], None
    for k, sc in enumerate(TL):
        tr = sc["trans_in"] if k else "cut"
        if tr == prev and tr not in ("cut", "cont"):
            tr = "cut"
        out.append(tr); prev = tr
    return out
TRANS = None
_TLP = ROOT / "_tmp/sjk02/timeline.json"
TL = json.load(open(_TLP, encoding="utf-8")) if _TLP.exists() else []
REND = ROOT / "_tmp/sjk02/render"
CAP_STYLE = {"font": "C:/Users/user/AppData/Local/Microsoft/Windows/Fonts/GmarketSansMedium.otf",
             "size": 48, "stroke": 4, "padx": 12, "pady": 35, "radius": 8, "cy": 1011, "alpha": 0.616}


class Clip:
    def __init__(self, sc):
        self.sc = sc
        self.path = REND / f"s{sc['scene']:02d}.mp4"
        self.start = sc["t0"] - sc["pre"]
        self.p = None; self.idx = -1; self.last = None
        if self.path.exists():
            self.n = int(subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v:0", "-show_entries",
                                         "stream=nb_read_packets", "-of", "csv=p=0", str(self.path)], capture_output=True, text=True).stdout.strip() or 0)
        else:
            self.n = 0

    def open(self, first):
        self.close()
        if not self.n:
            return
        ss = max(0.0, first / FPS)
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{ss:.4f}", "-i", str(self.path), "-f", "rawvideo", "-pix_fmt", "bgr24",
                                   "-s", f"{W}x{H}", "-"], stdout=subprocess.PIPE, bufsize=W * H * 3 * 4)
        self.idx = int(round(ss * FPS)) - 1

    def frame(self, t):
        if not self.n:
            return None
        li = min(self.n - 1, max(0, int(round((t - self.start) * FPS))))
        if self.p is None or li < self.idx:
            self.open(li)
        while self.idx < li:
            buf = self.p.stdout.read(W * H * 3)
            if len(buf) < W * H * 3:
                break
            self.last = np.frombuffer(buf, np.uint8).reshape(H, W, 3); self.idx += 1
        return self.last

    def close(self):
        if self.p:
            self.p.stdout.close(); self.p.kill(); self.p = None


_TEX = {}


def _tex(name):
    if name not in _TEX:
        from PIL import Image
        im = Image.open(ROOT / f"소재/sjk02/codex/{name}.png").convert("RGB")
        r = max(W / im.width, H / im.height)
        im = im.resize((int(im.width * r + 1), int(im.height * r + 1)))
        x0, y0 = (im.width - W) // 2, (im.height - H) // 2
        _TEX[name] = np.ascontiguousarray(np.asarray(im.crop((x0, y0, x0 + W, y0 + H)))[:, :, ::-1])
    return _TEX[name]


def shutter_tex():
    return _tex("p01b_shutter_closed_front")


def conc_tex():
    return _tex("t_concrete")


def ease(p):
    return p * p * (3 - 2 * p)


def scale_about(img, s, cx=W / 2, cy=H / 2):
    M = np.float32([[s, 0, cx - s * cx], [0, s, cy - s * cy]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def mblur(img, px, axis):
    px = int(abs(px))
    if px < 3:
        return img
    k = (1, px) if axis == 1 else (px, 1)
    return cv2.blur(img, k)


def transition(kind, a, b, p):
    e = ease(p)
    if a is not None and b is not None and kind in ("shut_dn", "shut_up"):
        # 셔터가 지나감 — 셔터 사진(p56 닫힌 셔터) 한 장 높이 판이 위→아래(내림) 또는 아래→위(올림)로 화면을 덮고 지나가며 A → B
        sh = shutter_tex()
        out = (a if p < 0.5 else b).copy()
        if kind == "shut_dn":
            y0 = int(round(e * 2 * H)) - H           # 셔터 판 위 끝: −H … +H
        else:
            y0 = H - int(round(e * 2 * H))           # 셔터 판 위 끝: +H … −H
        top, bot = max(0, y0), min(H, y0 + H)
        if bot > top:
            out[top:bot] = sh[top - y0:bot - y0]
            edge = bot if kind == "shut_dn" else top   # 움직이는 끝에 얕은 그림자
            if kind == "shut_dn" and bot < H:
                out[bot:min(H, bot + 18)] = (out[bot:min(H, bot + 18)] * 0.6).astype(np.uint8)
            if kind == "shut_up" and top > 0:
                out[max(0, top - 18):top] = (out[max(0, top - 18):top] * 0.6).astype(np.uint8)
        return out
    if a is not None and b is not None and kind == "desat":
        # 탈색 넘김 — 앞 장면 색이 빠져 회색이 되고, 회색인 채로 다음 장면이 겹쳐 들어와 색이 돌아옴
        g = lambda im: cv2.cvtColor(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
        if p < 0.5:
            k = ease(p * 2)
            return cv2.addWeighted(a, 1 - k, g(a), k, 0)
        k = ease((p - 0.5) * 2)
        mid = cv2.addWeighted(g(a), 1 - k, g(b), k, 0)
        return cv2.addWeighted(mid, 1 - k, b, k, 0)
    if a is not None and b is not None and kind == "slide":
        # 옆 흐름 이어짐 — 카메라가 옆 칸으로(흐림 약하게, 두 장면이 붙어서 흐름)
        sh = int(round(e * W))
        out = np.empty_like(a)
        out[:, : W - sh] = a[:, sh:]
        out[:, W - sh:] = b[:, : sh]
        return mblur(out, 48 * np.sin(np.pi * p), 1)
    if a is not None and b is not None and kind == "flip":
        # 카드 뒤집기 — 가로로 접히며(A) 뒤에서 B 가 펼쳐짐, 뒤 바탕은 콘크리트
        base = conc_tex().copy()
        im, sx = (a, np.cos(np.pi * e)) if e < 0.5 else (b, -np.cos(np.pi * e))
        wi = max(2, int(W * sx))
        sm = cv2.resize(im, (wi, int(H * (1 - 0.06 * (1 - sx)))))
        y0 = (H - sm.shape[0]) // 2; x0 = (W - wi) // 2
        base[y0:y0 + sm.shape[0], x0:x0 + wi] = (sm * (0.75 + 0.25 * sx)).astype(np.uint8)
        return base
    if a is not None and b is not None and kind == "into":
        # 모양 안으로 — A 가운데로 빨려 들어가며(확대) 둥근 창 안에 B 가 커짐
        A = scale_about(a, 1 + 0.9 * e)
        r = (0.08 + 0.92 * e) * 1.15
        w2, h2 = int(W * r / 2), int(H * r / 2)
        m = np.zeros((H, W), np.float32)
        cv2.rectangle(m, (W // 2 - w2, H // 2 - h2), (W // 2 + w2, H // 2 + h2), 1.0, -1)
        m = cv2.GaussianBlur(m, (0, 0), 6)[..., None]
        B = scale_about(b, 0.85 + 0.15 * e)
        return (B * m + A * (1 - m)).astype(np.uint8)
    if a is not None and b is not None and kind == "match":
        # 모양 이어 붙이기 — 둥근 창(원)이 가운데에서 열리며 B
        yy, xx = np.ogrid[:H, :W]
        rr = np.sqrt((xx - W / 2) ** 2 + (yy - H / 2) ** 2)
        R = e * np.hypot(W / 2, H / 2) * 1.05
        m = np.clip((R - rr) / 24, 0, 1).astype(np.float32)[..., None]
        return (b * m + a * (1 - m)).astype(np.uint8)
    if a is not None and b is not None and kind in ("whip", "whipup"):
        ax = 1 if kind == "whip" else 0
        L = W if ax == 1 else H
        sh = int(round(e * L))
        A = np.roll(a, -sh, axis=ax); B = np.roll(b, L - sh, axis=ax)
        out = A.copy()
        if ax == 1:
            out[:, L - sh:] = B[:, L - sh:]
        else:
            out[L - sh:] = B[L - sh:]
        return mblur(out, 140 * np.sin(np.pi * p), ax)
    if a is not None and b is not None and kind == "zoomout":
        A = scale_about(a, 1 - 0.3 * e)
        B = scale_about(b, 1.25 - 0.25 * e)
        return cv2.addWeighted(A, 1 - e, B, e, 0)
    if a is None:
        return b
    if b is None:
        return a
    if kind == "dissolve":
        return cv2.addWeighted(a, 1 - e, b, e, 0)
    if kind == "push":                       # 다음 판이 오른쪽에서 종이처럼 덮어 옴(앞 판은 조금 밀리고 어두워짐)
        x = int(round((1 - e) * W))
        out = scale_about(a, 1.0)
        sh = int(-0.18 * W * e)
        out = np.roll(out, sh, axis=1) if sh else out
        out = (out.astype(np.float32) * (1 - 0.25 * e)).astype(np.uint8)
        if x < W:
            out[:, x:] = b[:, : W - x]
            g = np.linspace(0.55, 1, min(40, x) or 1)[None, :, None]
            if x >= 40:
                out[:, x - 40:x] = (out[:, x - 40:x] * g).astype(np.uint8)
        return out
    if kind == "zoom":                       # 앞 판 속으로 들어가며 다음 판이 나타남
        A = scale_about(a, 1 + 0.6 * e)
        B = scale_about(b, 1.15 - 0.15 * e)
        return cv2.addWeighted(A, 1 - e, B, e, 0)
    if kind == "split":                      # 앞 판이 위아래로 갈라짐
        out = scale_about(b, 1.05 - 0.05 * e)
        off = int(e * H / 2)
        top, bot = a[: H // 2], a[H // 2:]
        if H // 2 - off > 0:
            out[: H // 2 - off] = top[off:]
            out[H // 2 + off:] = bot[: H - H // 2 - off]
        return out
    if kind == "wipe":                       # 지우개 — 부드러운 가장자리 왼→오
        xs = np.arange(W, dtype=np.float32)
        edge = -150 + e * (W + 300)
        m = np.clip((edge - xs) / 150, 0, 1)[None, :, None]
        return (b * m + a * (1 - m)).astype(np.uint8)
    return b


PUNCH = []


PUNCH_ON = False   # 10-15 2차 «한 이미지 여러 번 키프레임 별로 — 최대 두 번»: 같은 그림 반복 당김 없앰(SPEC_V2 8장)


def build_punch(lines):
    if not PUNCH_ON:
        return []
    out, last, lvl = [], -9, 0
    for sc in TL:
        lvl = 0
        for ln in sc["lines"]:
            t = sc["t0"] + ln["t0"]
            if t < sc["t0"] + 1.0 or t > sc["t1"] - 0.8 or t - last < 3.0:
                continue
            lvl = 1 - lvl; last = t
            out.append((t, 1.05 if lvl else 1.0, sc["t1"]))
    return out


def punch_scale(t):
    import bisect
    i = bisect.bisect_right([q[0] for q in PUNCH], t) - 1
    if i < 0:
        return 1.0
    t0, z, end = PUNCH[i]
    if t >= end:                      # 장면이 끝나면 원래 크기
        return 1.0
    prev = PUNCH[i - 1][1] if i > 0 and PUNCH[i - 1][2] == end else 1.0
    k = ease(min(1.0, (t - t0) / 0.14))
    return prev + (z - prev) * k


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="t_from", type=float, default=0.0)
    ap.add_argument("--to", dest="t_to", type=float, default=TL[-1]["t1"])
    ap.add_argument("--out", default="성제관02")
    ap.add_argument("--preview", action="store_true", help="960x540 확인본만")
    a = ap.parse_args()
    lines = json.load(open(ROOT / "_tmp/sjk02/audio/lines.json", encoding="utf-8"))
    capf = ROOT / "_tmp/sjk02/sub/captions.json"
    json.dump([{"t0": r["sub_t0"], "t1": r["sub_t1"], "text": cap_text(r["text"])} for r in lines], open(capf, "w", encoding="utf-8"), ensure_ascii=False)
    caps = Captions(str(capf), CAP_STYLE)
    t0s = [c["t0"] for c in caps.caps]
    global TRANS, PUNCH
    TRANS = _plan()
    PUNCH = build_punch(lines)
    json.dump({"trans": TRANS, "punch": PUNCH}, open(ROOT / "_tmp/sjk02/final/v2_plan.json", "w", encoding="utf-8"), ensure_ascii=False)
    print("전환:", " ".join(TRANS), "· 컷 줌", len(PUNCH), flush=True)
    clips = [Clip(s) for s in TL]
    miss = [s["scene"] for s, c in zip(TL, clips) if not c.n]
    print("빠진 장면 클립:", miss or "없음", flush=True)
    # 1편 10-16 교훈: 깨진 장면 클립을 조립기가 마지막 정상 프레임으로 19초 메움(5:18~5:38 멈춤) → 끝까지 디코드되는지 먼저 보고, 깨졌으면 멈춘다
    bad = []
    for c in clips:
        if c.n:
            r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(c.path), "-f", "null", "-"], capture_output=True, text=True)
            if r.stderr.strip():
                bad.append((c.sc["scene"], r.stderr.strip().splitlines()[0][:120]))
    if bad:
        print("★ 디코드 오류 장면 — 다시 렌더하고 조립:", bad, flush=True)
        raise SystemExit(2)
    if miss and not a.preview:
        print("★ 빠진 장면이 있어 완성본을 만들지 않는다(--preview 로만 확인)", flush=True)
        raise SystemExit(3)
    outdir = ROOT / "_tmp/sjk02/final"; outdir.mkdir(parents=True, exist_ok=True)
    enc = lambda path: subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", f"{FN}/{FD}", "-i", "-"]
        + (["-vf", "scale=960:540"] if a.preview else [])
        + ["-c:v", "h264_nvenc", "-preset", "p6", "-rc", "vbr", "-cq", "17", "-b:v", "0", "-pix_fmt", "yuv420p", str(path)],
        stdin=subprocess.PIPE)
    e_sub = enc(outdir / f"{a.out}_영상_자막.mp4")
    e_raw = None if a.preview else enc(outdir / f"{a.out}_영상_자막없음.mp4")
    n0, n1 = int(round(a.t_from * FPS)), int(round(a.t_to * FPS))
    import bisect
    k = 0
    last = np.zeros((H, W, 3), np.uint8)
    for n in range(n0, n1):
        t = n * FD / FN
        while k + 1 < len(TL) and t >= TL[k + 1]["t0"]:
            clips[k].close() if k > 0 else None
            k += 1
        cur = clips[k].frame(t)
        fr = cur
        # 다음 장면으로 넘어가는 전환(경계 앞쪽 절반)
        if k + 1 < len(TL) and TRANS[k + 1] not in ("cut", "cont") and t >= TL[k + 1]["t0"] - D / 2:
            b = TL[k + 1]["t0"]; p = (t - (b - D / 2)) / D
            fr = transition(TRANS[k + 1], cur, clips[k + 1].frame(t), p)
        # 이 장면으로 들어온 전환(경계 뒤쪽 절반)
        elif k > 0 and TRANS[k] not in ("cut", "cont") and t < TL[k]["t0"] + D / 2:
            b = TL[k]["t0"]; p = (t - (b - D / 2)) / D
            fr = transition(TRANS[k], clips[k - 1].frame(t), cur, p)
        if fr is not None and PUNCH:
            z = punch_scale(t)
            if z != 1.0:
                fr = scale_about(fr, z)
        if fr is None:
            fr = last                      # 클립이 없으면 앞 그림 유지(보고에 «빠진 장면»)
        last = fr
        base = np.ascontiguousarray(fr)
        if e_raw:
            e_raw.stdin.write(base.tobytes())
        i = bisect.bisect_right(t0s, t) - 1
        if i >= 0 and t < caps.caps[i]["t1"]:
            rgb, al, y0 = caps.rgba(i)
            out = base.copy()
            h = al.shape[0]
            reg = out[y0:y0 + h].astype(np.float32)
            out[y0:y0 + h] = (rgb * al + reg * (1 - al)).astype(np.uint8)
        else:
            out = base
        e_sub.stdin.write(out.tobytes())
        if n % 600 == 0:
            print(f"  {t:7.1f}s / {a.t_to:.1f}s  장면 {TL[k]['scene']}", flush=True)
    for e in (e_sub, e_raw):
        if e:
            e.stdin.close(); e.wait()
    for c in clips:
        c.close()
    print("완료", outdir)


if __name__ == "__main__":
    main()
