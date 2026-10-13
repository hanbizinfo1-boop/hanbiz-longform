# -*- coding: utf-8 -*-
"""파트너센터 자동 — 자막 확정본 만들기(사장님 C1 → 글 고침 · 빈 줄 채움 · 타이밍 다듬기).

입력: _tmp/pc/edit.json(prproj C1) · _tmp/pc/subtiming.json(강제 정렬 검수 결과)
출력: _tmp/pc/captions_v1.json {"captions":[{t0,t1,text}], "changes":[…]}  ← 검수표에 «바꾼 곳»으로 그대로 옮긴다

판단 근거(10-13 설계자 판정): 화면 글(데모 페이지 이름·메뉴)·강제 정렬 점수(후보 A/B)·받아쓰기·문맥.
애매한 곳(«끄고/그거» 988초)은 바꾸지 않고 «확인 필요»로만 적는다.
"""
import json

FILL = {  # prproj 글 블롭을 못 읽은 10줄 — mp4 화면에서 읽음(10-13)
    62.746: "인스턴트 양식", 157.341: "라는 가정하에", 195.278: "라고 하시면", 564.981: "이거를 클릭을 하시면",
    572.439: "예를 들어서", 691.291: "어떻게 될까요?", 978.444: "그래서 얼마인지", 1303.385: "예를 들어서",
    1339.288: "라고 이해를 하시면 될 것 같아요", 1365.414: "그렇게 알고 계시면 될 것 같아요",
}
TEXT_FIX = [  # (자막 시작초, 전, 후, 근거)
    (275.7, "최화윤님", "최하윤님", "화면 DB 목록 이름 «최하윤» · 강제 정렬 B 우세 · 뒤 자막 4곳도 «최하윤»"),
    (284.8, "최화윤님", "최하윤님", "같음"),
    (344.5, "최화윤님이", "최하윤님이", "같음"),
    (172.7, "네' 를 누르면", "'네'를 누르면", "따옴표 짝·띄어쓰기"),
    (494.4, "알림 톡을", "알림톡을", "표기 통일(영상 전체 «알림톡»)"),
    (513.4, "알림 톡이", "알림톡이", "표기 통일"),
    (526.8, "알림 톡", "알림톡", "표기 통일"),
    (542.5, "알림 톡", "알림톡", "표기 통일"),
    (512.5, "다음 날이 됐네?", "전날이 됐네?", "문맥(예약 시간을 보고 하루 전 알림톡) · 강제 정렬 «전날» 0.82 vs «다음» 0.20 · 받아쓰기 «전날»"),
    (559.4, "한서한 님", "한서아 님", "화면 이름 «한서아» · 강제 정렬 «한서아» 0.98 > «한서한» 0.85"),
    (732.3, "페북, 페이지, 세트, 캠페인", "페북 페이지, 세트, 캠페인", "«페북 페이지»가 한 항목(742초 «페북 페이지도»)"),
    (240.1, "최적화 되어", "최적화되어", "띄어쓰기(최적화되다)"),
    (1013.5, "직접 설정해서도", "직접 설정에서도", "메뉴 «직접 설정»에서 · 강제 정렬 B 0.97 > A 0.85 · 받아쓰기 «설정에서도»"),
    (1044.9, "있는 거 라서", "있는 거라서", "띄어쓰기"),
    (1074.4, "분석을 해놓해보셨다", "분석을 해보셨다", "말 더듬은 조각이 글로 남음 · 강제 정렬 B 0.83 > A 0.44"),
    (1323.6, "보는 사람에서", "고른 사람에서", "화면 버튼 «고른 사람» · 강제 정렬 B 0.93 > A 0.64 · 받아쓰기 «고른»"),
]
HOLD = [(988.1, "이건 무조건 끄고", "«그거»로 들렸을 수 있음(강제 정렬 0.61 vs 0.42, 받아쓰기 «그거») — 뜻이 둘 다 통해 바꾸지 않음")]


def main():
    it = json.load(open("_tmp/pc/edit.json", encoding="utf-8"))["items"]
    caps = [dict(t0=i["t0"], t1=i["t1"], text=i.get("text", "")) for i in sorted(
        (i for i in it if i["track"] == "C1"), key=lambda i: i["t0"])]
    changes = []
    for c in caps:
        if not c["text"]:
            k = min(FILL, key=lambda t: abs(t - c["t0"]))
            assert abs(k - c["t0"]) < 0.01
            c["text"] = FILL[k]
    for t, a, b, why in TEXT_FIX:
        c = min(caps, key=lambda c: abs(c["t0"] - t))
        assert abs(c["t0"] - t) < 0.2 and a in c["text"], (t, a, c)
        old = c["text"]; c["text"] = old.replace(a, b)
        changes.append(dict(kind="글", t0=round(c["t0"], 3), before=old, after=c["text"], why=why))
    import sys
    if "--timing" not in sys.argv:
        json.dump(dict(captions=caps, changes=changes), open("_tmp/pc/captions_text.json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print("글 단계 끝 → sub_timing.py captions_text.json → --timing")
        return
    # 타이밍 — 글을 고친 자막을 다시 강제 정렬한 결과(subtiming_text.json) + 받아쓰기로 교차 확인
    tm = json.load(open("_tmp/pc/subtiming_text.json", encoding="utf-8"))
    ws = [w for s in json.load(open("_tmp/pc/words.json", encoding="utf-8")) for w in s["words"]]
    WBIAS = 0.215          # 받아쓰기 단어 시작이 실제보다 이른 정도(10-13 실측 중앙값)
    FR = 1001 / 60000
    for k, c in enumerate(caps):
        r = tm[k]
        if "onset" not in r or r["lag"] <= 0.15 or k == 0:
            continue
        prev, pr = caps[k - 1], tm[k - 1]
        # 받아쓰기로도 늦은지: 자막 시작 전 0.8초 안에 시작한 단어가 있고 그 단어가 이 줄 첫 낱말과 같은 글자로 시작
        first = c["text"].replace("'", "").split()[0][:1]
        cand = [w for w in ws if c["t0"] - 0.8 < w["t0"] + WBIAS < c["t0"] - 0.1 and w["w"].lstrip("'\"").startswith(first)]
        if not cand:
            continue
        tgt = r["onset"] - 0.03
        if "offset" in pr:
            tgt = max(tgt, pr["offset"] + 0.02)
        if tgt < c["t0"] - 2 * FR and abs(prev["t1"] - c["t0"]) < 2 * FR:
            old = c["t0"]
            prev["t1"] = round(tgt, 3); c["t0"] = round(tgt, 3)
            changes.append(dict(kind="시작", t0=round(old, 3), before=round(old, 3), after=c["t0"], text=c["text"],
                                why=f"말 시작(강제 정렬 {r['onset']}초 · 받아쓰기 «{cand[0]['w']}»)보다 {round(old - r['onset'], 3)}초 늦게 뜸"))
    json.dump(dict(captions=caps, changes=changes, hold=[dict(t0=t, text=x, why=w) for t, x, w in HOLD]),
              open("_tmp/pc/captions_v1.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    from collections import Counter
    print(Counter(c["kind"] for c in changes))


if __name__ == "__main__":
    main()
