# -*- coding: utf-8 -*-
r"""자동 연출 합성기 — 원문 층(녹화·사람 PIP·자막)을 다시 쌓으며 모자이크·카메라·강조·연출 장면을 끼운다.

    python tools/auto/compose.py <plan.json> [--from 초] [--to 초] [--out 경로] [--preview]

plan.json
{
  "edit": "_tmp/pc/edit.json",               # read_lecture_edit 결과(V1·V2 트랙)
  "media_dirs": ["D:/…"],
  "audio": "원문.mp4",                        # 목소리·원래 소리는 원문 mp4 소리를 그대로 쓴다
  "sfx_wav": "_tmp/pc/sfx_bus.wav",          # (선택) 효과음 버스 — 원문 소리와 더한다
  "captions": "_tmp/pc/captions_v1.json",
  "caption_style": {"font":…, "size":48, "stroke":4, "padx":12, "pady":35, "radius":8, "cy":1011, "alpha":0.616},
  "pip": {"cx":154.76, "cy":929.85, "r":150.64},
  "mosaic": "_tmp/pc/mosaic_boxes.json",      # [{"t0","t1","box":[x0,y0,x1,y1]}] 시퀀스 시각 · 녹화 화면 좌표
  "cams": [{"t0","t1","box":[…],"q":[x,y],"zmax":1.8,"tin":0.45,"tout":0.45}],   # 녹화 화면 확대
  "fx": [{"t0","t1","kind":"brush_rect"|"underline"|"chip"|"overlay", "space":"screen"|"frame", …}],
  "pip_hide": [[t0,t1]],                      # 전체 화면 연출 동안 사람 PIP 숨김(사람은 V2 그대로 — 굽는 건 B 모드)
  "out": "납품/…/파일.mp4"
}
층 순서(아래→위): 녹화(모자이크 먼저) → 카메라 → screen 강조 → frame 연출(under) → 사람 PIP → 자막 → frame 연출(top).
"""
import json
import math
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.auto.layers import TrackReader, motion_of, SEQ_FPS  # noqa: E402

W, H = 1920, 1080
FPS = float(SEQ_FPS)


# ── 이징
def eo(x):                     # 감속(easeOutCubic)
    x = min(1.0, max(0.0, x)); return 1 - (1 - x) ** 3


def eio(x):                    # 가속·감속
    x = min(1.0, max(0.0, x)); return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


# ── 자막
class Captions:
    def __init__(self, path, st):
        d = json.load(open(path, encoding="utf-8"))
        self.caps = d["captions"] if "captions" in d else d
        self.st = st
        self.font = ImageFont.truetype(st["font"], st["size"])
        self.cache = {}

    def at(self, t):
        for i, c in enumerate(self.caps):           # 798줄 — 선형이면 느리다 → bisect 대용 캐시
            pass
        return None

    def build_index(self):
        self.t0s = [c["t0"] for c in self.caps]

    def rgba(self, i):
        if i in self.cache:
            return self.cache[i]
        st, text = self.st, self.caps[i]["text"]
        im = Image.new("RGBA", (W, 160), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        cy = 80
        bb = d.textbbox((0, 0), text, font=self.font, anchor="ls")
        w = bb[2] - bb[0]
        d.rounded_rectangle((960 - w / 2 - st["padx"], cy - st["pady"], 960 + w / 2 + st["padx"], cy + st["pady"]),
                            radius=st["radius"], fill=(0, 0, 0, int(round(st["alpha"] * 255))))
        d.text((960, cy), text, font=self.font, anchor="mm", fill=(255, 255, 255, 255),
               stroke_width=st["stroke"], stroke_fill=(0, 0, 0, 255))
        a = np.array(im)
        ys = np.where(a[..., 3].max(1) > 0)[0]
        y0, y1 = int(ys.min()), int(ys.max()) + 1
        crop = a[y0:y1]
        rgb = crop[..., [2, 1, 0]].astype(np.float32); al = crop[..., 3:4].astype(np.float32) / 255
        res = (rgb, al, st["cy"] - cy + y0)
        self.cache[i] = res
        if len(self.cache) > 64:
            self.cache.pop(next(iter(self.cache)))
        return res


def blend(dst, rgb, al, x0, y0):
    h, w = al.shape[:2]
    X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if X0 >= X1 or Y0 >= Y1:
        return
    s = (slice(Y0 - y0, Y1 - y0), slice(X0 - x0, X1 - x0))
    a = al[s]; d = dst[Y0:Y1, X0:X1].astype(np.float32)
    dst[Y0:Y1, X0:X1] = (rgb[s] * a + d * (1 - a)).astype(np.uint8)


# ── 모자이크
def pixelate(img, box, block=16):
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(img.shape[1], x1), min(img.shape[0], y1)
    if x1 - x0 < 2 or y1 - y0 < 2:
        return
    roi = img[y0:y1, x0:x1]
    sw, sh = max(1, (x1 - x0) // block), max(1, (y1 - y0) // block)
    small = cv2.resize(roi, (sw, sh), interpolation=cv2.INTER_AREA)
    img[y0:y1, x0:x1] = cv2.resize(small, (x1 - x0, y1 - y0), interpolation=cv2.INTER_NEAREST)


# ── 카메라(녹화 층 확대)
def cam_state(cams, t):
    """(z, vx, vy): 출력 = (화면좌표 − v)·z."""
    for c in cams:
        if c["t0"] - 1e-6 <= t <= c["t1"]:
            x0, y0, x1, y1 = c["box"]
            bw, bh = x1 - x0, y1 - y0
            zt = min(c.get("zmax", 1.8), W * c.get("fill", 0.62) / bw, H * c.get("fill", 0.62) / bh)
            zt = max(1.0, zt)
            qx, qy = c.get("q", [1080, 470])
            vx_t = (x0 + x1) / 2 - qx / zt; vy_t = (y0 + y1) / 2 - qy / zt
            vx_t = min(max(0, vx_t), W - W / zt); vy_t = min(max(0, vy_t), H - H / zt)
            tin, tout = c.get("tin", 0.45), c.get("tout", 0.45)
            if t < c["t0"] + tin:
                k = eo((t - c["t0"]) / tin)
            elif t > c["t1"] - tout:
                k = 1 - eio((t - (c["t1"] - tout)) / tout)
            else:
                k = 1.0
            # 로그 공간에서 z 보간 → 일정한 체감 속도
            z = math.exp(math.log(zt) * k)
            # v 는 «화면 가운데가 어디를 보나»로 보간
            cx = (W / 2) + ((vx_t + W / zt / 2) - W / 2) * ((1 - 1 / z) / (1 - 1 / zt) if zt > 1 else 0)
            cy = (H / 2) + ((vy_t + H / zt / 2) - H / 2) * ((1 - 1 / z) / (1 - 1 / zt) if zt > 1 else 0)
            vx, vy = cx - W / z / 2, cy - H / z / 2
            vx = min(max(0, vx), W - W / z); vy = min(max(0, vy), H - H / z)
            return z, vx, vy
    return 1.0, 0.0, 0.0


def apply_cam(img, z, vx, vy):
    if z <= 1.0001:
        return img
    M = np.float32([[z, 0, -vx * z], [0, z, -vy * z]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


# ── 강조 그림(붓 획) — 2배 크기로 그려 줄여 매끈하게
SS = 2


def _taper_poly(pts, width):
    """폴리라인을 따라 끝이 가늘어지는 획 다각형(양 끝 20% 테이퍼)."""
    pts = np.asarray(pts, np.float32)
    seg = np.diff(pts, axis=0); L = np.linalg.norm(seg, axis=1); tot = L.sum()
    if tot < 1:
        return None
    cum = np.concatenate([[0], np.cumsum(L)])
    left, right = [], []
    for i, p in enumerate(pts):
        s = cum[i] / tot
        wv = width * min(1.0, s / 0.2, (1 - s) / 0.2 + 0.35)
        d = seg[min(i, len(seg) - 1)]; n = np.array([-d[1], d[0]]) / (np.linalg.norm(d) + 1e-6)
        left.append(p + n * wv / 2); right.append(p - n * wv / 2)
    return np.vstack([left, right[::-1]])


def brush_layer(kind, pts_screen, prog, color, width, xf):
    """xf: 화면좌표 → 출력좌표. prog 0~1 = 그려진 정도. 반환 (rgba 조각, x0, y0) — 획 주변만 2배로 그려 줄인다."""
    P = np.array([xf(p) for p in pts_screen], np.float32)
    if kind == "brush_rect":
        x0, y0 = P[0]; x1, y1 = P[1]
        pad = 10
        x0 -= pad; y0 -= pad; x1 += pad; y1 += pad
        path = [(x0 + 3, y0), (x1, y0 + 1.5), (x1 - 1.5, y1), (x0, y1 - 1), (x0 + 1.5, y0 + 7)]
    else:
        path = [tuple(P[0]), tuple(P[1])]
    m = width * 2 + 4
    bx0 = int(min(p[0] for p in path) - m); by0 = int(min(p[1] for p in path) - m)
    bx1 = int(max(p[0] for p in path) + m); by1 = int(max(p[1] for p in path) + m)
    bw, bh = bx1 - bx0, by1 - by0
    if bw <= 2 or bh <= 2:
        return None
    lp = [((x - bx0) * SS, (y - by0) * SS) for x, y in path]
    dense = []
    for a, b in zip(lp, lp[1:]):
        n = max(2, int(np.hypot(b[0] - a[0], b[1] - a[1]) / 6))
        for k in range(n):
            dense.append((a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n))
    dense.append(lp[-1])
    mm = max(2, int(len(dense) * prog))
    poly = _taper_poly(dense[:mm], width * SS)
    if poly is None:
        return None
    big = np.zeros((bh * SS, bw * SS, 4), np.uint8)
    cv2.fillPoly(big, [poly.astype(np.int32)], (int(color[2]), int(color[1]), int(color[0]), 255), lineType=cv2.LINE_AA)
    return cv2.resize(big, (bw, bh), interpolation=cv2.INTER_AREA), bx0, by0


def chip_rgba(text, size=40, fg=(255, 255, 255), bg=(20, 24, 33), accent=(255, 205, 40), font=None):
    f = ImageFont.truetype(font, size)
    tmp = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    bb = tmp.textbbox((0, 0), text, font=f)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    pw, ph = 26, 16
    im = Image.new("RGBA", (w + pw * 2 + 10, h + ph * 2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=13, fill=bg + (255,))
    d.rounded_rectangle((0, 0, 9, im.height - 1), radius=4, fill=accent + (255,))
    d.text((pw + 10 - bb[0], ph - bb[1]), text, font=f, fill=fg + (255,))
    a = np.array(im)
    return a[..., [2, 1, 0]].astype(np.float32), a[..., 3:4].astype(np.float32) / 255


def draw_image(frame, f, t):
    """이미지 연출: 들어옴 0.32초(아래서 24px 올라오며 감속, 92→100%), 나감 0.25초 페이드. move 가 있으면 끝 위치로 이동."""
    rgb, al = f["_rgba"]
    din = f.get("tin", 0.32); dout = f.get("tout", 0.25)
    p = eo((t - f["t0"]) / din)
    fade = 1.0 if t < f["t1"] - dout else max(0.0, (f["t1"] - t) / dout)
    s = f.get("s0", 0.92) + (1 - f.get("s0", 0.92)) * p
    x, y = f["xy"]
    if f.get("move"):                       # [[t0,t1],[x2,y2,scale2]] — 예: 로고가 표로 빨려 들어감
        (ma, mb), (x2, y2, s2) = f["move"]
        q = eio((t - ma) / max(1e-3, mb - ma)) if t >= ma else 0.0
        x, y = x + (x2 - x) * q, y + (y2 - y) * q; s = s * (1 + (s2 - 1) * q)
    h, w = al.shape[:2]
    nw, nh = max(1, int(w * s)), max(1, int(h * s))
    r2 = cv2.resize(rgb, (nw, nh), interpolation=cv2.INTER_AREA); a2 = cv2.resize(al, (nw, nh))[..., None] if nw > 1 else al
    if a2.ndim == 2:
        a2 = a2[..., None]
    a2 = a2 * min(1.0, p * 1.6) * fade
    oy = int(round((1 - p) * f.get("rise", 24)))
    blend(frame, r2, a2, int(round(x + (w - nw) / 2)), int(round(y + (h - nh) / 2)) + oy)


# ── 메인 루프
def main():
    args = sys.argv[1:]
    plan = json.load(open(args[0], encoding="utf-8"))

    def opt(k, d=None):
        return args[args.index(k) + 1] if k in args else d
    t_from = float(opt("--from", 0)); t_to = opt("--to")
    out = opt("--out", plan["out"])
    preview = "--preview" in args

    items = json.load(open(plan["edit"], encoding="utf-8"))["items"]
    V1 = TrackReader([i for i in items if i["track"] == "V1"], plan["media_dirs"])
    V2 = TrackReader([i for i in items if i["track"] == "V2"], plan["media_dirs"])
    caps = Captions(plan["captions"], plan["caption_style"])
    t0s = [c["t0"] for c in caps.caps]
    import bisect
    mos = json.load(open(plan["mosaic"], encoding="utf-8")) if plan.get("mosaic") and Path(plan["mosaic"]).exists() else []
    mos.sort(key=lambda m: m["t0"])
    cams = plan.get("cams", [])
    fx = plan.get("fx", [])
    for f in fx:
        if f["kind"] == "chip":
            f["_rgba"] = chip_rgba(f["text"], f.get("size", 40), font=plan["chip_font"])
        if f["kind"] == "image":
            im = Image.open(f["src"]).convert("RGBA")
            if f.get("w"):
                im = im.resize((int(f["w"]), int(round(im.height * f["w"] / im.width))), Image.LANCZOS)
            a = np.array(im)
            f["_rgba"] = (a[..., [2, 1, 0]].astype(np.float32), a[..., 3:4].astype(np.float32) / 255)
    pip = plan["pip"]
    yy, xx = np.mgrid[0:H, 0:W]
    dist = np.sqrt((xx - pip["cx"]) ** 2 + (yy - pip["cy"]) ** 2) - pip["r"]
    pip_a = np.clip(0.8 - dist, 0, 1).astype(np.float32)
    pip_box = (0, int(pip["cy"] - pip["r"] - 2), int(pip["cx"] + pip["r"] + 2), H)
    pip_a_crop = pip_a[pip_box[1]:pip_box[3], pip_box[0]:pip_box[2], None]
    pip_hide = plan.get("pip_hide", [])

    dur = max(i["t1"] for i in items)
    k0 = int(round(t_from * FPS)); k1 = int(round((float(t_to) if t_to else dur) * FPS))
    scale = "scale=960:540," if preview else ""
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", "60000/1001",
           "-i", "-", "-ss", f"{k0 / FPS:.6f}", "-t", f"{(k1 - k0) / FPS:.6f}", "-i", plan["audio"]]
    amap = ["-map", "0:v", "-map", "1:a"]
    if plan.get("sfx_wav") and Path(plan["sfx_wav"]).exists():
        cmd += ["-ss", f"{k0 / FPS:.6f}", "-t", f"{(k1 - k0) / FPS:.6f}", "-i", plan["sfx_wav"]]
        amap = ["-filter_complex", "[1:a][2:a]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.84[a]",
                "-map", "0:v", "-map", "[a]"]
    vcodec = ["-c:v", "h264_nvenc", "-preset", "p5", "-rc", "vbr", "-cq", "19", "-b:v", "20M", "-maxrate", "40M"] \
        if not preview else ["-c:v", "h264_nvenc", "-preset", "p3", "-cq", "28"]
    cmd += amap + (["-vf", scale.rstrip(",")] if preview else []) + vcodec + \
        ["-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    mi = 0
    for k in range(k0, k1):
        t = k / FPS
        rec, it1 = V1.frame(k)
        if rec is None:
            rec = np.zeros((H, W, 3), np.uint8)
        elif rec.shape[1] != W:
            pos, sc = motion_of(it1)
            rec = cv2.resize(rec, (int(rec.shape[1] * sc / 100), int(rec.shape[0] * sc / 100)), interpolation=cv2.INTER_AREA)
            if rec.shape[:2] != (H, W):
                c = np.zeros((H, W, 3), np.uint8); h, w = rec.shape[:2]
                c[(H - h) // 2:(H - h) // 2 + h, (W - w) // 2:(W - w) // 2 + w] = rec[:H, :W]; rec = c
        else:
            rec = rec.copy()
        # 모자이크(녹화 층)
        while mi < len(mos) and mos[mi]["t1"] < t - 5:
            mi += 1
        for m in mos[mi:]:
            if m["t0"] > t:
                break
            if m["t0"] <= t <= m["t1"]:
                pixelate(rec, m["box"], m.get("block", 16))
        # 카메라
        z, vx, vy = cam_state(cams, t)
        frame = apply_cam(rec, z, vx, vy)
        xf = lambda p: ((p[0] - vx) * z, (p[1] - vy) * z)  # noqa: E731
        # 강조(screen) · 연출(frame under)
        for f in fx:
            if not (f["t0"] <= t <= f["t1"]):
                continue
            if f["kind"] in ("brush_rect", "underline"):
                prog = eo((t - f["t0"]) / f.get("draw", 0.35))
                fade = 1.0 if t < f["t1"] - 0.2 else max(0.0, (f["t1"] - t) / 0.2)
                lay = brush_layer(f["kind"], f["pts"], prog, f.get("color", (255, 70, 70)), f.get("width", 7), xf if f.get("space", "screen") == "screen" else (lambda p: p))
                if lay is not None:
                    piece, bx0, by0 = lay
                    blend(frame, piece[..., :3].astype(np.float32), piece[..., 3:4].astype(np.float32) / 255 * fade, bx0, by0)
            elif f["kind"] == "chip" and f.get("layer", "under") == "under":
                rgb, al = f["_rgba"]
                p = eo((t - f["t0"]) / 0.22); fade = 1.0 if t < f["t1"] - 0.2 else max(0.0, (f["t1"] - t) / 0.2)
                s = 0.7 + 0.3 * p
                h, w = al.shape[:2]
                r2 = cv2.resize(rgb, (max(1, int(w * s)), max(1, int(h * s)))); a2 = cv2.resize(al, (r2.shape[1], r2.shape[0]))[..., None] * p * fade
                x, y = f["xy"]
                blend(frame, r2, a2, int(x + (w - r2.shape[1]) / 2), int(y + (h - r2.shape[0]) / 2))
            elif f["kind"] == "dim":
                p = eo((t - f["t0"]) / 0.3) * (1.0 if t < f["t1"] - 0.3 else max(0.0, (f["t1"] - t) / 0.3))
                if p > 0:
                    bl = cv2.GaussianBlur(frame, (0, 0), 9)
                    dark = (bl.astype(np.float32) * (1 - 0.42)).astype(np.uint8)
                    frame[:] = (dark.astype(np.float32) * p + frame.astype(np.float32) * (1 - p)).astype(np.uint8)
            elif f["kind"] == "image" and f.get("layer", "under") == "under":
                draw_image(frame, f, t)
        # 사람 PIP
        hide = any(a <= t <= b for a, b in pip_hide)
        if not hide:
            cam, it2 = V2.frame(k)
            if cam is not None and not any(f.get("name") == "모션" for f in it2.get("fx", [])):
                # 모션 이펙트가 없는 V2 = 사람 전체 화면 컷(10-13 실측 212.96~215.60 마우스 시연) → 원형 마스크 없이 화면 전체
                frame[:] = cv2.resize(cam, (W, H), interpolation=cv2.INTER_AREA) if cam.shape[:2] != (H, W) else cam
            elif cam is not None:
                pos, sc = motion_of(it2)
                s = sc / 100; nw, nh = int(round(cam.shape[1] * s)), int(round(cam.shape[0] * s))
                camr = cv2.resize(cam, (nw, nh), interpolation=cv2.INTER_AREA)
                x0, y0 = int(round(pos[0] * W - nw / 2)), int(round(pos[1] * H - nh / 2))
                bx0, by0, bx1, by1 = pip_box
                sub = np.zeros((by1 - by0, bx1 - bx0, 3), np.uint8)
                sx0, sy0 = bx0 - x0, by0 - y0
                sub[:] = camr[sy0:sy0 + (by1 - by0), sx0:sx0 + (bx1 - bx0)][: by1 - by0, : bx1 - bx0]
                dst = frame[by0:by1, bx0:bx1].astype(np.float32)
                frame[by0:by1, bx0:bx1] = (sub.astype(np.float32) * pip_a_crop + dst * (1 - pip_a_crop)).astype(np.uint8)
        # 자막
        j = bisect.bisect_right(t0s, t + 1e-6) - 1
        if j >= 0 and t < caps.caps[j]["t1"] - 1e-6:
            rgb, al, y0 = caps.rgba(j)
            blend(frame, rgb, al, 0, y0)
        # 연출(frame top)
        for f in fx:
            if f["kind"] == "image" and f.get("layer") == "top" and f["t0"] <= t <= f["t1"]:
                draw_image(frame, f, t)
            if f["kind"] == "chip" and f.get("layer") == "top" and f["t0"] <= t <= f["t1"]:
                rgb, al = f["_rgba"]; x, y = f["xy"]
                p = eo((t - f["t0"]) / 0.22)
                blend(frame, rgb, al * p, int(x), int(y))
        proc.stdin.write(frame.tobytes())
        if (k - k0) % 600 == 0:
            print(f"  {t:8.1f}s", flush=True)
    proc.stdin.close(); proc.wait()
    print("저장:", out)


if __name__ == "__main__":
    main()
