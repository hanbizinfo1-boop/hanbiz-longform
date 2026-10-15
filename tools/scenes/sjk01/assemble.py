# -*- coding: utf-8 -*-
"""성제관01 롱폼 조립 — 장면 클립 53개 → 전환 → 자막 굽기 → (자막본 · 자막없음본) 영상만. 소리는 audio_mix.py, 합치기는 mux.

    py -3.11 tools/scenes/sjk01/assemble.py [--from 초] [--to 초] [--out 이름] [--preview]

장면 클립: _tmp/sjk01/render/sNN.mp4 — 프레임 0 = 장면 시작(t0) − pre. (html_motion 장면은 그렇게 렌더되고, 블렌더·사진 장면도 같은 규칙으로 만든다.)
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

W, H = 1920, 1080
FN, FD = 60000, 1001
FPS = FN / FD
D = 0.6
TL = json.load(open(ROOT / "_tmp/sjk01/timeline.json", encoding="utf-8"))
REND = ROOT / "_tmp/sjk01/render"
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


def ease(p):
    return p * p * (3 - 2 * p)


def scale_about(img, s, cx=W / 2, cy=H / 2):
    M = np.float32([[s, 0, cx - s * cx], [0, s, cy - s * cy]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def transition(kind, a, b, p):
    e = ease(p)
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="t_from", type=float, default=0.0)
    ap.add_argument("--to", dest="t_to", type=float, default=TL[-1]["t1"])
    ap.add_argument("--out", default="성제관01")
    ap.add_argument("--preview", action="store_true", help="960x540 확인본만")
    a = ap.parse_args()
    lines = json.load(open(ROOT / "_tmp/sjk01/audio/lines.json", encoding="utf-8"))
    capf = ROOT / "_tmp/sjk01/sub/captions.json"
    json.dump([{"t0": r["sub_t0"], "t1": r["sub_t1"], "text": r["text"]} for r in lines], open(capf, "w", encoding="utf-8"), ensure_ascii=False)
    caps = Captions(str(capf), CAP_STYLE)
    t0s = [c["t0"] for c in caps.caps]
    clips = [Clip(s) for s in TL]
    miss = [s["scene"] for s, c in zip(TL, clips) if not c.n]
    print("빠진 장면 클립:", miss or "없음", flush=True)
    outdir = ROOT / "_tmp/sjk01/final"; outdir.mkdir(parents=True, exist_ok=True)
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
        if k + 1 < len(TL) and TL[k + 1]["trans_in"] not in ("cut", "cont") and t >= TL[k + 1]["t0"] - D / 2:
            b = TL[k + 1]["t0"]; p = (t - (b - D / 2)) / D
            fr = transition(TL[k + 1]["trans_in"], cur, clips[k + 1].frame(t), p)
        # 이 장면으로 들어온 전환(경계 뒤쪽 절반)
        elif TL[k]["trans_in"] not in ("cut", "cont") and k > 0 and t < TL[k]["t0"] + D / 2:
            b = TL[k]["t0"]; p = (t - (b - D / 2)) / D
            fr = transition(TL[k]["trans_in"], clips[k - 1].frame(t), cur, p)
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
