# -*- coding: utf-8 -*-
r"""완성본 전체 검수(10-13 규칙 3 «끝나고 전체 검수 1번») — 결과를 JSON 으로.

    python tools/auto/verify_final.py <plan.json> <완성본.mp4> <원문.mp4> <금지어.txt> <출력.json>

1) 원문 대조: 0.5초마다 완성본 ↔ 원문 SSIM(그레이 480p). 연출(카메라·강조·카드)·모자이크 구간은 «바뀌는 게 정상»이라 따로 집계.
   그 밖에서 0.93 미만 = 재구성 어긋남 후보.
2) 개인정보 재검사: 1초마다(원문 대조와 같은 순회) 완성본을 OCR(easyocr) → 금지어(실명·업체명 변형, 한 줄에 하나, git 제외 파일)·IP·실제 휴대폰 번호 패턴이 보이면 ERROR.
   체험병원 예시 번호(010-0000-·010-0010-)와 사장님 예외 번호는 금지어 파일의 «허용:» 줄로 뺀다.
3) 음량: ffmpeg ebur128 — 통합 LUFS·트루피크(−1.0 dBTP 넘으면 WARN).
"""
import json
import re
import subprocess
import sys

import cv2
import numpy as np


def frames(path, ts, size=(854, 480)):
    cap = cv2.VideoCapture(path)
    out = {}
    for t in ts:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, f = cap.read()
        if ok:
            out[t] = f
    return out


def ssim(a, b):
    a = cv2.cvtColor(cv2.resize(a, (854, 480)), cv2.COLOR_BGR2GRAY).astype(np.float64)
    b = cv2.cvtColor(cv2.resize(b, (854, 480)), cv2.COLOR_BGR2GRAY).astype(np.float64)
    C1, C2 = 6.5025, 58.5225
    mu1, mu2 = cv2.GaussianBlur(a, (11, 11), 1.5), cv2.GaussianBlur(b, (11, 11), 1.5)
    s1 = cv2.GaussianBlur(a * a, (11, 11), 1.5) - mu1 ** 2
    s2 = cv2.GaussianBlur(b * b, (11, 11), 1.5) - mu2 ** 2
    s12 = cv2.GaussianBlur(a * b, (11, 11), 1.5) - mu1 * mu2
    m = ((2 * mu1 * mu2 + C1) * (2 * s12 + C2)) / ((mu1 ** 2 + mu2 ** 2 + C1) * (s1 + s2 + C2))
    return float(m.mean())


def main():
    plan_p, final, orig, terms_p, out = sys.argv[1:6]
    plan = json.load(open(plan_p, encoding="utf-8"))
    mos = json.load(open(plan["mosaic"], encoding="utf-8")) if plan.get("mosaic") else []
    busy = [(c["t0"], c["t1"]) for c in plan.get("cams", [])] + [(f["t0"], f["t1"]) for f in plan.get("fx", [])] + \
           [(m["t0"], m["t1"]) for m in mos]
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", final],
                               capture_output=True, text=True).stdout)
    rep = {"duration": dur}
    # 1) 원문 대조
    # 순서대로 읽으며 30프레임(0.5초)마다 비교 — seek 는 느리다
    fa, fb = cv2.VideoCapture(final), cv2.VideoCapture(orig)
    fps = fa.get(cv2.CAP_PROP_FPS) or 59.94
    low, vals, k = [], [], 0
    ocr_frames = {}
    while True:
        oka = fa.grab(); okb = fb.grab()
        if not (oka and okb):
            break
        t = k / fps
        if k % 30 == 15:
            _, a = fa.retrieve(); _, b = fb.retrieve()
            if k % 60 == 15:
                ocr_frames[round(t, 2)] = cv2.imencode('.png', a)[1]      # 메모리 아끼려 압축해 둔다(무손실)
            if not any(x - 0.3 <= t <= y + 0.3 for x, y in busy):
                s_ = ssim(a, b); vals.append(s_)
                if s_ < 0.93:
                    low.append((round(t, 2), round(s_, 3)))
        k += 1
    rep["ssim_outside_fx"] = dict(n=len(vals), mean=round(float(np.mean(vals)), 4), min=round(float(np.min(vals)), 4), low=low)
    print("원문 대조:", rep["ssim_outside_fx"]["n"], "표본 평균", rep["ssim_outside_fx"]["mean"], "0.93 미만", len(low), flush=True)
    # 2) 개인정보 재검사
    if terms_p.endswith(".json"):                   # 제작 컴퓨터: 기획이 넘긴 금지어 지문(실명 없음)
        sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2]))
        from tools.auto import termhash
        tdata = termhash.load(terms_p); allow = tdata.get("allow", []); terms = []
    else:
        lines = [l.strip() for l in open(terms_p, encoding="utf-8") if l.strip() and not l.startswith("#")]
        allow = [l[3:].strip() for l in lines if l.startswith("허용:")]
        terms = [l for l in lines if not l.startswith("허용:")]
        tdata = None
    pat_ip = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")
    pat_ph = re.compile(r"01[0-9][-. ]?\d{3,4}[-. ]?\d{4}|\+82\s?10")
    import easyocr
    rd = easyocr.Reader(["ko", "en"], gpu=True, verbose=False)
    hits = []
    for t, enc in sorted(ocr_frames.items()):
        f = cv2.imdecode(enc, cv2.IMREAD_COLOR)
        for box, txt, conf in rd.readtext(f):
            s_ = txt.replace(" ", "")
            bad = [kk for kk in terms if kk.replace(" ", "") in s_]
            if tdata is not None and termhash.hit(txt, tdata):
                bad.append("금지어")
            if pat_ip.search(txt):
                bad.append("IP")
            ph = pat_ph.search(s_)
            if ph and not any(al.replace(" ", "") in s_ for al in allow):
                bad.append("휴대폰")
            if bad:
                x0 = int(min(p[0] for p in box)); y0 = int(min(p[1] for p in box))
                hits.append(dict(t=t, why=bad, at=[x0, y0], text=("(실명 생략)" if any(w not in ("IP", "휴대폰") for w in bad) else txt)))
    rep["privacy_hits"] = hits
    print("개인정보 재검사: 걸린 곳", len(hits), flush=True)
    # 3) 음량
    json.dump(rep, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)     # 음량 전에 한 번 저장(10-13 음량 단계에서 죽어 앞 결과를 잃었다)
    r = subprocess.run(["ffmpeg", "-nostats", "-i", final, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    m = re.findall(r"I:\s+(-?\d+\.\d) LUFS", r.stderr); p = re.findall(r"Peak:\s+(-?\d+\.\d) dBFS", r.stderr)
    rep["loudness"] = dict(integrated_lufs=float(m[-1]) if m else None, true_peak_dbtp=float(p[-1]) if p else None)
    print("음량:", rep["loudness"])
    json.dump(rep, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
