# -*- coding: utf-8 -*-
r"""완성본에서 «왼쪽 위 광고주 이름»이 보이는 시간대 찾기 — 모자이크 빠진 곳 점검 (10-12).

사장님 10-12 외부 피드백: «광고관리자 나올 때 왼쪽 상단 (자사) 상호명 모자이크가 안 됐고 … 광고관리자(메인) 탭
나올 때는 왼쪽 상단 광고주 이름도 가려 줘야 함». 이식본: 찾는 낱말은 건마다 --keys 로 준다(기본은 자사 상호 조각).

완성본(내보낸 mp4)을 STEP 초마다 뽑아 왼쪽 위 영역만 easyocr(ko+en, GPU)로 읽고,
찾는 낱말(KEYS)이 읽히면 그 시각을 모은다. 이어지는 시각은 한 구간으로 묶는다.

    python tools/corner_name_scan.py <완성본.mp4> <출력.json> [STEP=1.0] [x0,y0,x1,y1=0,0,960,400] [--keys 낱말,낱말]

원본 실측: 영역 0,0,680,320 · 1초 간격 · 실시간 속도(40분 영상에 약 40분). 걸린 구간은 앞뒤 1초 여유를 두고 프레임으로 확인.
대상 아닌 것도 걸린다(카메라 뒤 벽 간판·브라우저 탭 제목·시연 검색어) → 목록만 만들고 가릴지는 사장님이 정한다.

출력: {"hits":[[초, "읽은 글자", 신뢰도], …], "ranges":[[시작초, 끝초], …], "all":[[초, [글자…]], …]}
"""

import json
import sys

import cv2

KEYS = ("중소기업", "비즈니스", "비지니스", "한국중소", "한비즈", "센터")


def main():
    global KEYS
    if "--keys" in sys.argv:
        i = sys.argv.index("--keys")
        KEYS = tuple(k for k in sys.argv[i + 1].split(",") if k)
        del sys.argv[i:i + 2]
    video, out = sys.argv[1:3]
    step = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
    x0, y0, x1, y1 = map(int, (sys.argv[4] if len(sys.argv) > 4 else "0,0,960,400").split(","))
    import easyocr
    reader = easyocr.Reader(["ko", "en"], gpu=True)
    cap = cv2.VideoCapture(video)
    dur = cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS)
    hits, all_ = [], []
    t = 0.0
    while t < dur:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, fr = cap.read()
        if not ok:
            break
        crop = fr[y0:y1, x0:x1]
        txt = [(b[1], float(b[2])) for b in reader.readtext(crop)]
        all_.append([round(t, 2), [s for s, _ in txt]])
        for s, c in txt:
            if any(k in s.replace(" ", "") for k in KEYS):
                hits.append([round(t, 2), s, round(c, 2)])
        if int(t) % 60 == 0 and t == int(t):
            print(f"{t:.0f}/{dur:.0f}초 · 찾음 {len(hits)}", flush=True)
        t += step
    ranges = []
    for h in sorted({h[0] for h in hits}):
        if ranges and h - ranges[-1][1] <= step * 3 + 0.01:
            ranges[-1][1] = h
        else:
            ranges.append([h, h])
    json.dump({"step": step, "hits": hits, "ranges": ranges, "all": all_},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for a, b in ranges:
        print(f"{int(a // 60)}:{a % 60:04.1f} ~ {int(b // 60)}:{b % 60:04.1f}")


if __name__ == "__main__":
    main()
