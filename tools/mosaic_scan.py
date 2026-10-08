# -*- coding: utf-8 -*-
r"""화면녹화에서 글자를 전부 읽어 둔다 — 업체명·고객명 모자이크의 1단계.

시퀀스에 실제로 쓰인 녹화본 구간(read_lecture_edit.py 결과의 V1 조각)만 원본 시각으로
STEP 초마다 뽑아 easyocr(ko+en, GPU)로 읽는다. 앞 표본과 거의 같은 화면이면 다시 읽지 않고 재사용.

    python mosaic_scan.py <edit.json> <녹화본.mp4> <출력.json> [STEP=0.5]

출력: {"step":…, "samples":[{"s":원본초, "boxes":[[x0,y0,x1,y1,"글자",신뢰도],…]}]}
다음 단계: 글자 목록에서 가릴 것(업체·고객명)을 골라 mosaic_render.py 로.
"""

import json
import sys

import cv2
import numpy as np


def used_ranges(edit_json, media):
    it = json.load(open(edit_json, encoding="utf-8"))["items"]
    rs = sorted((x["s0"], x["s1"]) for x in it
                if x["track"] == "V1" and x["name"] == media)
    out = []
    for a, b in rs:
        if out and a <= out[-1][1] + 0.5:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def main():
    edit_json, video, out = sys.argv[1:4]
    step = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
    import easyocr
    reader = easyocr.Reader(["ko", "en"], gpu=True)
    media = video.replace("\\", "/").split("/")[-1]
    rngs = used_ranges(edit_json, media)
    want = []
    for a, b in rngs:
        t = a
        while t < b:
            want.append(round(t, 3))
            t += step
    print(f"구간 {len(rngs)}개 · 표본 {len(want)}개", flush=True)

    cap = cv2.VideoCapture(video)
    fps = cap.get(cv2.CAP_PROP_FPS)
    samples, prev_small, prev_boxes, wi, fi, ocr_n = [], None, None, 0, 0, 0
    while wi < len(want):
        ok = cap.grab()
        if not ok:
            break
        t = fi / fps
        fi += 1
        if t + 0.5 / fps < want[wi]:
            continue
        _, frame = cap.retrieve()
        while wi < len(want) and want[wi] <= t + 0.5 / fps:
            wi += 1
        small = cv2.cvtColor(cv2.resize(frame, (480, 270)), cv2.COLOR_BGR2GRAY).astype(np.int16)
        # 재사용은 «사실상 같은 화면»만: 바뀐 픽셀이 0.2% 미만(커서·시계 정도). 평균 차이로 보면
        # 흰 화면이 살짝 스크롤된 것도 같은 화면으로 쳐서 칸이 30~70px 어긋났다(10-06 실측).
        # 비교 기준은 마지막으로 OCR 한 화면 — 조금씩 바뀌는 게 쌓여도 놓치지 않게
        if prev_small is not None and (np.abs(small - prev_small) > 12).mean() < 0.002:
            boxes, fresh = prev_boxes, False
        else:
            fresh = True
            boxes = []
            for pts, txt, conf in reader.readtext(frame):
                xs = [p[0] for p in pts]
                ys = [p[1] for p in pts]
                boxes.append([int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys)), txt, round(float(conf), 3)])
            ocr_n += 1
            prev_small, prev_boxes = small, boxes
        samples.append({"s": round(t, 3), "boxes": boxes, "fresh": fresh})
        if len(samples) % 200 == 0:
            print(f"  {len(samples)}/{len(want)} (새로 읽음 {ocr_n})", flush=True)
    json.dump({"step": step, "fps": fps, "ranges": rngs, "samples": samples},
              open(out, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"저장: {out} · 표본 {len(samples)} · OCR {ocr_n}")


if __name__ == "__main__":
    main()
