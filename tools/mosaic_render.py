# -*- coding: utf-8 -*-
r"""업체명·고객명 모자이크 — 2단계: 가릴 글자 칸만 모자이크한 알파 영상 + 덮어씌울 XML.

    python mosaic_render.py <ocr.json> <가릴것.json> <녹화본.mp4> <edit.json> <출력폴더> [--미리보기]

가릴것.json: {"terms": ["업체명", …], "regex": ["…"], "pad": 10, "block": 18}
  - OCR 칸 글자(공백 제거)가 term 을 품거나 term 의 3글자 이상 조각이거나 비슷(0.8)하면 가린다.
흐름
  1) 표본(0.5초)마다 가릴 칸 → 원본 시각 구간(앞뒤 0.6초 여유)으로 묶는다
  2) 구간 안 프레임마다: 앞·뒤 표본의 칸을 템플릿 매칭으로 따라가 위치를 잡는다(스크롤 대응)
  3) 칸 밖은 투명, 칸 안은 블록 모자이크 → ProRes 4444 알파 mov (원본 30fps 그대로)
  4) 시퀀스의 녹화본 V1 조각마다 같은 in/out 으로 mov 를 배치한 XML (컷과 정확히 일치)
→ 프리미어: XML 시퀀스 V1 전체 복사 → «빡이사DB» 에서 V1 바로 위(사람 PIP 아래) 새 트랙에 0초 붙여넣기
"""

import difflib
import json
import re
import subprocess
import sys
from pathlib import Path
from xml.sax.saxutils import escape

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from overlay_xml import RATE, fr, url  # noqa: E402

W, H = 1920, 1080
BOTTOM = 1015                                   # 윈도 작업표시줄 위까지만


def norm(s):
    return re.sub(r"[\s·.,:;|'\"()\[\]]", "", s)


def is_hit(txt, terms, regs):
    t = norm(txt)
    if len(t) < 2:
        return False
    for term in terms:
        if term in t or (len(t) >= 3 and t in term and len(t) >= 0.75 * len(term)):
            return True
        if len(t) >= 3 and difflib.SequenceMatcher(None, t, term).ratio() >= 0.8:
            return True
    return any(r.search(txt) for r in regs)


def spans_of(samples, hits, step, gap=1.25, margin=0.6):
    ts = [s["s"] for s, h in zip(samples, hits) if h]
    out = []
    for t in ts:
        if out and t - out[-1][1] <= gap:
            out[-1][1] = t
        else:
            out.append([t, t])
    res = []
    for a, b in out:
        a, b = max(0.0, a - margin), b + margin
        while b - a > 15:                    # 길면 15초씩 (메모리)
            res.append([a, a + 15])
            a += 15
        res.append([a, b])
    return res


def track(prev_gray, cur_gray, box, rad=260):
    """prev 프레임의 box 조각을 cur 에서 찾아 옮긴 box. 못 찾으면 None."""
    x0, y0, x1, y1 = box
    tpl = prev_gray[y0:y1, x0:x1]
    if tpl.size == 0 or tpl.std() < 3:
        return box
    sx0, sy0 = max(0, x0 - 60), max(0, y0 - rad)
    sx1, sy1 = min(W, x1 + 60), min(H, y1 + rad)
    win = cur_gray[sy0:sy1, sx0:sx1]
    if win.shape[0] < tpl.shape[0] or win.shape[1] < tpl.shape[1]:
        return None
    r = cv2.matchTemplate(win, tpl, cv2.TM_CCOEFF_NORMED)
    _, mx, _, loc = cv2.minMaxLoc(r)
    if mx < 0.55:
        return None
    nx, ny = sx0 + loc[0], sy0 + loc[1]
    return (nx, ny, nx + (x1 - x0), ny + (y1 - y0))


def pixelate(frame, box, block):
    x0, y0, x1, y1 = box
    roi = frame[y0:y1, x0:x1]
    if roi.size == 0:
        return roi
    h, w = roi.shape[:2]
    sm = cv2.resize(roi, (max(1, w // block), max(1, h // block)), interpolation=cv2.INTER_AREA)
    return cv2.resize(sm, (w, h), interpolation=cv2.INTER_NEAREST)


def clamp(b, pad):
    x0, y0, x1, y1 = b
    return (max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad), min(H, y1 + pad))


def corr(a, b):
    if a.shape != b.shape or a.size == 0:
        return -1.0
    a = a.astype(np.float32) - a.mean()
    b = b.astype(np.float32) - b.mean()
    d = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / d) if d > 1e-6 else (1.0 if np.abs(a - b).mean() < 4 else -1.0)


def iou(p, q):
    ix = max(0, min(p[2], q[2]) - max(p[0], q[0]))
    iy = max(0, min(p[3], q[3]) - max(p[1], q[1]))
    inter = ix * iy
    return inter / ((p[2] - p[0]) * (p[3] - p[1]) + (q[2] - q[0]) * (q[3] - q[1]) - inter + 1e-9)


def follow(gray, k, box, n, hold, boxes, allow_move=True):
    """k 프레임에서 찾은 box 를 앞뒤로 hold 프레임까지: 같은 자리에 같은 그림이면 유지, 움직였으면(스크롤) 찾아 옮김.
    원래 조각과 비교하니 오차가 쌓이지 않는다. 그 프레임에 이미 같은 칸이 있으면 거기서 멈춘다(다른 표본 몫)."""
    x0, y0, x1, y1 = box
    tpl = gray[k][y0:y1, x0:x1]
    boxes[k].add(box)
    for direc in (1, -1):
        cur, j = box, k
        for _ in range(hold):
            j += direc
            if j < 0 or j >= n:
                break
            if any(iou(cur, b) > 0.85 for b in boxes[j]):
                break
            a0, b0, a1, b1 = cur
            if corr(gray[j][b0:b1, a0:a1], tpl) > 0.85:
                boxes[j].add(cur)
                continue
            if not allow_move:                  # 위치로 정한 고정 칸은 그 자리에서만 (옮기면 상단 아이콘 줄로 튀었다)
                break
            sx0, sy0 = max(0, a0 - 60), max(0, b0 - 260)
            sx1, sy1 = min(W, a1 + 60), min(H, b1 + 260)
            win = gray[j][sy0:sy1, sx0:sx1]
            if tpl.std() < 3 or win.shape[0] < tpl.shape[0] or win.shape[1] < tpl.shape[1]:
                break
            r = cv2.matchTemplate(win, tpl, cv2.TM_CCOEFF_NORMED)
            _, mx, _, loc = cv2.minMaxLoc(r)
            if mx < 0.85:                   # 글자 조각은 맞으면 0.95+ — 0.6 이면 옆 줄로 튀었다(10-06)
                break
            cur = (sx0 + loc[0], sy0 + loc[1], sx0 + loc[0] + (x1 - x0), sy0 + loc[1] + (y1 - y0))
            boxes[j].add(cur)


def render_span(video, fps, a, b, sample_boxes, out_mov, block, preview=None, hold_s=3.0):
    """sample_boxes: [(t, [box…])]. 표본마다 찾은 칸을 앞뒤 hold_s 초까지 follow() 로 이어 붙여 깜빡임·빠짐을 막는다."""
    hold = int(fps * hold_s)
    f0, f1 = int(round(a * fps)), int(round(b * fps))
    e0 = max(0, f0 - hold)                      # 따라가기용으로 앞뒤 hold 만큼 더 읽는다(회색만 — 메모리)
    cap = cv2.VideoCapture(video)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    e1 = min(total, f1 + hold)
    cap.set(cv2.CAP_PROP_POS_FRAMES, e0)
    gray = []
    for _ in range(e1 - e0):
        ok, fr_ = cap.read()
        if not ok:
            break
        gray.append(cv2.cvtColor(fr_, cv2.COLOR_BGR2GRAY))
    n = len(gray)
    boxes = [set() for _ in range(n)]
    for t, bxs in sample_boxes:
        k = int(round(t * fps)) - e0
        if not bxs or k < 0 or k >= n:
            continue
        for bx in bxs:
            fixed = len(bx) == 5
            bx = tuple(bx[:4])
            if any(iou(bx, q) > 0.85 for q in boxes[k]):
                continue
            follow(gray, k, bx, n, hold, boxes, allow_move=not fixed)
    del gray
    cap.set(cv2.CAP_PROP_POS_FRAMES, f0)
    frames = []
    for _ in range(f1 - f0):
        ok, fr_ = cap.read()
        if not ok:
            break
        frames.append(fr_)
    boxes = boxes[f0 - e0:f0 - e0 + len(frames)]
    n = len(frames)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
           "-r", f"{fps}", "-i", "-", "-c:v", "prores_ks", "-profile:v", "4", "-pix_fmt", "yuva444p10le",
           "-vendor", "apl0", str(out_mov)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i, f in enumerate(frames):
        canvas = np.zeros((H, W, 4), np.uint8)
        for bx in boxes[i]:
            x0, y0, x1, y1 = bx
            canvas[y0:y1, x0:x1, :3] = pixelate(f, bx, block)
            canvas[y0:y1, x0:x1, 3] = 255
        p.stdin.write(canvas.tobytes())
        if preview is not None and i == n // 2:
            show = f.copy()
            m = canvas[:, :, 3] > 0
            show[m] = canvas[:, :, :3][m]
            cv2.imencode(".jpg", show)[1].tofile(str(preview))   # 한글 경로는 imwrite 가 조용히 실패
    p.stdin.close()
    p.wait()
    return n / fps


def main():
    ocr_p, rule_p, video, edit_p, out_dir = sys.argv[1:6]
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ocr = json.load(open(ocr_p, encoding="utf-8"))
    rule = json.load(open(rule_p, encoding="utf-8"))
    terms = [norm(t) for t in rule["terms"]]
    regs = [re.compile(r) for r in rule.get("regex", [])]
    pad, block = rule.get("pad", 10), rule.get("block", 18)
    fps, step = ocr["fps"], ocr["step"]
    samples = ocr["samples"]
    hitboxes = [[clamp(tuple(b[:4]), pad) for b in s["boxes"] if is_hit(b[4], terms, regs)] for s in samples]
    for hb in hitboxes:                         # 이름 왼쪽 로고까지 넓히기 (페이지 목록 등)
        for ex in rule.get("extend_left", []):
            for i, (x0, y0, x1, y1) in enumerate(hb):
                if ex["x0"][0] <= x0 + pad <= ex["x0"][1]:
                    hb[i] = (max(0, x0 - ex["dx"]), max(0, y0 - 15), x1, min(H, y1 + 55))
    # 기준 글자 옆 고정 칸: OCR 이 자주 놓치는 것(북마크 폴더명·스토리 이름 줄·바로가기)을 위치로 가린다
    for s, hb in zip(samples, hitboxes):
        for an in rule.get("anchors", []):
            for b in s["boxes"]:
                if an["text"] in norm(b[4]) and abs(b[0] - an["at"][0]) < 40 and abs(b[1] - an["at"][1]) < 40:
                    for dx0, dy0, dx1, dy1 in an["boxes"]:
                        x0, y0, x1, y1 = clamp((b[0] + dx0, b[1] + dy0, min(W, b[0] + dx1), min(BOTTOM, b[1] + dy1)), 0)
                        hb.append((x0, y0, x1, y1, "F"))
                    break
    spans = spans_of(samples, [bool(h) for h in hitboxes], step, gap=6.0, margin=3.0)
    print(f"가릴 칸 있는 표본 {sum(1 for h in hitboxes if h)} · 구간 {len(spans)}개")

    import os
    part = tuple(int(x) for x in os.environ["MOSAIC_PART"].split("/")) if os.environ.get("MOSAIC_PART") else None
    pv = out_dir / "확인"
    pv.mkdir(exist_ok=True)
    made = []
    for i, (a, b) in enumerate(spans, 1):
        sb = [(s["s"], h) for s, h in zip(samples, hitboxes) if a - 4 <= s["s"] <= b + 4]
        mov = out_dir / f"모자이크_{i:03d}_{a:07.2f}.mov"
        # 나눠 돌리기: MOSAIC_PART=k/n 이면 i%n==k 인 구간만 렌더하고 XML 은 안 쓴다.
        # 다 끝난 뒤 MOSAIC_PART 없이 한 번 더 돌리면 있는 mov 는 건너뛰고 XML 만 쓴다.
        if part and (i % part[1]) != part[0]:
            continue
        if mov.exists() and mov.stat().st_size > 0 and (out_dir / f".done_{i:03d}").exists():
            dur = (int(round(b * fps)) - int(round(a * fps))) / fps
        else:
            dur = render_span(video, fps, a, b, sb, mov, block, pv / f"{i:03d}_{a:07.2f}.jpg")
            (out_dir / f".done_{i:03d}").write_text("ok")
        made.append({"file": str(mov), "s0": a, "s1": a + dur})
        print(f"  {i}/{len(spans)} 원본 {a:.1f}~{a + dur:.1f}", flush=True)

    if part:
        print("부분 렌더 끝 — XML 은 MOSAIC_PART 없이 다시 돌려 만든다")
        return
    # 시퀀스 배치: 녹화본 V1 조각과 겹치는 부분만, 같은 원본 시각으로
    media = Path(video).name
    it = json.load(open(edit_p, encoding="utf-8"))["items"]
    clips = sorted((x for x in it if x["track"] == "V1" and x["name"] == media), key=lambda x: x["t0"])
    items, n = [], 0
    for c in clips:
        for k, m in enumerate(made):
            lo, hi = max(c["s0"], m["s0"]), min(c["s1"], m["s1"])
            if hi - lo < 1 / fps:
                continue
            n += 1
            t0 = c["t0"] + (lo - c["s0"])
            t1 = t0 + (hi - lo)
            a, b = fr(t0), fr(t1)
            src_in = fr(lo - m["s0"])
            first = not any(x[0] == k for x in items)
            fid = f"mz{k}"
            fe = (f'<file id="{fid}"><name>{escape(Path(m["file"]).name)}</name><pathurl>{escape(url(m["file"]))}</pathurl>'
                  f'<rate><timebase>30</timebase><ntsc>FALSE</ntsc></rate><duration>{int(round((m["s1"] - m["s0"]) * 30))}</duration>'
                  f'<media><video><samplecharacteristics><rate><timebase>30</timebase><ntsc>FALSE</ntsc></rate>'
                  f'<width>{W}</width><height>{H}</height><pixelaspectratio>square</pixelaspectratio>'
                  f'</samplecharacteristics></video></media></file>') if first else f'<file id="{fid}"/>'
            items.append((k, f'<clipitem id="mzc{n}"><name>{escape(Path(m["file"]).name)}</name>{RATE}'
                             f'<start>{a}</start><end>{b}</end><in>{src_in}</in><out>{src_in + (b - a)}</out>'
                             f'<alphatype>straight</alphatype>{fe}</clipitem>'))
    end = max((fr(c["t1"]) for c in clips), default=0)
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n<xmeml version="4"><sequence>'
           f'<name>빡이사DB_모자이크</name>{RATE}<duration>{end}</duration>'
           f'<media><video><format><samplecharacteristics>{RATE}<width>{W}</width><height>{H}</height>'
           '<pixelaspectratio>square</pixelaspectratio></samplecharacteristics></format>'
           '<track>' + "".join(x[1] for x in items) + '</track></video></media></sequence></xmeml>\n')
    xp = out_dir / "빡이사DB_모자이크.xml"
    xp.write_text(xml, encoding="utf-8")
    json.dump(made, open(out_dir / "구간.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"저장: {xp} · 클립 {n}개 · mov {len(made)}개")


if __name__ == "__main__":
    main()
