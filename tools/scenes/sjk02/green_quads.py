# -*- coding: utf-8 -*-
"""Codex 기기 사진의 초록 화면(#00FF00) 네 모서리 → quads.json · 초록을 지운 사본(_clean.png).

좌표 두 벌: photo(원본 1536×1024 픽셀) · stage(사진을 1920×1080 판에 cover 로 깔았을 때 — 가로 맞춤 1.25배, 위아래 100px 잘림).
장면에서는 사진을 `.bg` 로 깔고 `S.fitQuad(el, w, h, quads[이름][k].stage)` 로 UI 를 얹는다.
d42 는 왼쪽 흰 A4 종이 quad 도 «paper» 로 넣는다.
    py -3.11 tools/scenes/sjk02/green_quads.py
"""
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "소재/sjk02/codex"


def order(pts):
    pts = np.array(pts, np.float32)
    s = pts.sum(1); d = pts[:, 0] - pts[:, 1]
    return [pts[np.argmin(s)], pts[np.argmax(d)], pts[np.argmax(s)], pts[np.argmin(d)]]   # 왼위 오위 오아래 왼아래


def line_fit_quad(c):
    """둥근 모서리에도 맞게 — 최소 사각형 변마다 가운데 70% 점들로 직선을 맞추고 이웃 직선의 교점을 모서리로."""
    pts = c.reshape(-1, 2).astype(np.float32)
    box = np.array(order(cv2.boxPoints(cv2.minAreaRect(c))), np.float32)
    lines = []
    for k in range(4):
        a, b = box[k], box[(k + 1) % 4]
        ab = b - a; L = np.linalg.norm(ab); u = ab / L; nrm = np.array([-u[1], u[0]])
        rel = pts - a; t = rel @ u; dd = np.abs(rel @ nrm)
        sel = (t > 0.15 * L) & (t < 0.85 * L) & (dd < 0.08 * L + 12)
        q = pts[sel] if sel.sum() > 10 else np.array([a, b])
        vx, vy, x0, y0 = cv2.fitLine(q, cv2.DIST_HUBER, 0, 0.01, 0.01).ravel()
        lines.append((np.array([x0, y0]), np.array([vx, vy])))
    out = []
    for k in range(4):
        (p1, d1), (p2, d2) = lines[k - 1], lines[k]
        A = np.array([d1, -d2]).T
        s_ = np.linalg.solve(A, p2 - p1)
        out.append(p1 + s_[0] * d1)
    return order(out)


def quad_of(mask):
    cs, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    out = []
    for c in cs:
        if cv2.contourArea(c) < mask.size * 0.004:
            continue
        out.append(line_fit_quad(cv2.convexHull(c)))
    out.sort(key=lambda q: (q[0][0]))     # 왼쪽부터
    return out


def to_stage(q):
    return [[round(float(x) * 1.25, 1), round(float(y) * 1.25 - 100, 1)] for x, y in q]


def main():
    res = {}
    for p in sorted(list(SRC.glob("d*.png")) + list(SRC.glob("e44*.png"))):
        if p.stem.endswith("_clean"):
            continue
        a = np.array(Image.open(p).convert("RGB")).astype(np.int16)
        r, g, b = a[..., 0], a[..., 1], a[..., 2]
        m = ((g > 150) & (g - r > 70) & (g - b > 70)).astype(np.uint8) * 255
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
        qs = quad_of(m)
        res[p.stem] = [{"photo": [[round(float(x), 1), round(float(y), 1)] for x, y in q], "stage": to_stage(q)} for q in qs]
        if p.stem.startswith("d42"):
            wm = ((r > 195) & (g > 190) & (b > 185) & (np.abs(r - b) < 30)).astype(np.uint8) * 255
            wm[:, 900:] = 0; wm[:, :150] = 0
            wm = cv2.morphologyEx(wm, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
            pq = quad_of(wm)
            if pq:
                big = max(pq, key=lambda q: cv2.contourArea(np.array(q, np.float32)))
                res[p.stem + "_paper"] = [{"photo": [[round(float(x), 1), round(float(y), 1)] for x, y in big], "stage": to_stage(big)}]
        # 초록 지운 사본 — 화면 자리는 어두운 유리색, 가장자리 번짐도 같이
        mm = cv2.dilate(m, np.ones((5, 5), np.uint8)) > 0
        c = a.astype(np.uint8).copy()
        c[mm] = (18, 20, 24)
        sp = (g - np.maximum(r, b) > 30) & ~mm            # 초록 빛 번짐 줄이기
        c[sp, 1] = np.maximum(c[sp, 0], c[sp, 2]).astype(np.uint8)
        Image.fromarray(c).save(SRC / (p.stem + "_clean.png"))
        print(p.stem, [len(res[p.stem])], [q["stage"] for q in res[p.stem]])
    (SRC / "quads.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
