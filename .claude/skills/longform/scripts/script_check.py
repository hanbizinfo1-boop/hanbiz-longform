# -*- coding: utf-8 -*-
"""성제관 대본 AI 티 점검기 — 빡이사 30편 실측(references/study/bisa-script-1014.md 4장) 기준.

    python .claude/skills/longform/scripts/script_check.py <대본.md 또는 .txt> [--save]

- --save: 같은 폴더에 <대본>_검사.txt(통과/불통과 기록)를 남긴다 — 이 기록이 «통과» 가 아니면 연출표·녹음·제작으로 넘기지 않는다(CLAUDE.md 15번).
- 구조: 빡이사 대본결(이유 어미·질문·자문자답·확인 질문·첫머리 약속·끝 성장 마무리·판매 멘트 없음)을 잰다.

- WARN: 외래어(인사이트·솔루션·시너지) — 빡이사도 맥락상 가끔 씀, 남발만 고친다.
- ERROR: 빡이사가 30편에서 한 번도(또는 거의) 안 쓴 글말 — 0이 될 때까지 고친다.
- 수치: 문장 끝 어미·문장 첫 접속어·물음표 비율·문장 길이를 빡이사 실측과 나란히 보여 준다(맞추라는 값이 아니라 결이 벗어났는지 보는 거울).
- 대본의 «화면:» «[그림]» 같은 연출 메모 줄과 # 제목 줄은 세지 않는다.
종료 코드: ERROR 있으면 1.
"""

import re
import statistics
import sys

# (정규식, 이름, 대신 쓸 말)
BANNED = [
    (r"^\s*안녕하세요", "첫 인사로 시작", "첫 문장이 곧 훅"),
    (r"결론적으로", "결론적으로", "결론부터 말하면 / 정리하면"),
    (r"요약하(자면|면)", "요약하자면", "정리하면 ~(한 줄)"),
    (r"핵심은", "핵심은", "중요한 건 ~ / 이거 꼭 기억하셔야 해요"),
    (r"중요한 점은", "중요한 점은", "중요한 건 ~"),
    (r"라고 할 수 있습니다", "~라고 할 수 있습니다", "~라고 이해하시면 될 거 같아요"),
    (r"할 수 있습니다", "~할 수 있습니다", "~하실 수 있어요 / 돼요"),
    (r"것이 중요합니다", "~것이 중요합니다", "그게 제일 중요해요"),
    (r"것이 좋습니다", "~것이 좋습니다", "~하시는 게 좋아요"),
    (r"(함께 )?알아보(겠|도록 하겠)습니다", "알아보겠습니다", "바로 시작할게요 / 풀어 드릴게요"),
    (r"살펴보(겠|도록 하겠)습니다", "살펴보겠습니다", "한번 볼게요"),
    (r"소개해 ?드리겠습니다", "소개해 드리겠습니다", "보여 드릴게요"),
    (r"(^|[.?!]\s*)또한[ ,]", "문장 첫 «또한»", "그리고"),
    (r"한편", "한편", "근데"),
    (r"더불어", "더불어", "그리고 / 거기다"),
    (r"나아가", "나아가", "그리고 더 가면"),
    (r"이처럼", "이처럼", "이렇게"),
    (r"(^|[.?!]\s*)따라서", "문장 첫 «따라서»", "그래서"),
    # «즉,» 은 금지어에서 뺌 — 사장님 10-14 «실무자로 요약할 수 있는데 왜 굳이 길게써» (짧게 요약하는 접속어로 허용)
    (r"뿐만 아니라", "뿐만 아니라", "거기다 / 그것만이 아니라"),
    (r"(^|[.?!]\s*)다만", "다만", "대신 / 근데"),
    (r"다양한", "다양한", "여러 가지"),
    (r"효과적(으로|인)", "효과적으로", "효율이 좋다 / 잘"),
    (r"활용하여", "활용하여", "이걸 써서"),
    (r"를 통해|을 통해", "~를 통해", "~로 / ~해서"),
    (r"(^|\s)(첫째|둘째|셋째)[,\s]", "첫째·둘째·셋째", "첫 번째·두 번째·마지막 세 번째"),
    (r"도움이 되셨(길|기를) 바랍니다", "도움이 되셨길 바랍니다", "도움 되셨으면 좋아요 한 번만"),
    (r"응원합니다", "응원합니다", "돈 많이 버시길 바랍니다"),
    (r"…|\.\.\.", "말줄임표", "마침표로 끊기"),
    (r"~", "물결표", "빼기"),
    (r"[\U0001F300-\U0001FAFF]", "이모지", "빼기"),
    (r"(오늘|지금까지) (내용을|이야기를) 정리(하면|해 보면)", "마무리 요약 단락", "한 줄 다시 박기 + 집 가는 길 질문"),
]

# 경고만(빡이사도 맥락에 따라 씀 — 예: «백종원 솔루션») — 남발하면 고친다
WARN = [
    (r"인사이트|솔루션|시너지", "컨설턴트 외래어", "감 · 눈 · 방법"),
]

# 빡이사 30편 실측(자막 28.5만 자) — 비교용
REF = {
    "질문 비율(%)": 10.3,
    "문장 길이 중앙(자)": 28,
    "문장 길이 평균(자)": 37,
}
ENDINGS = ["잖아요", "거예요", "거든요", "거죠", "겁니다", "말이에요", "말이죠", "이거죠", "습니다", "니다"]
STARTS = ["그래서", "자,", "그리고", "근데", "그러면", "일단", "결국", "사실", "예를 들어"]

# 빡이사 결 구조 검사(10-14 사장님 «빡이사 학습한거 참고해서 짜는거 잊지마 … 검사장치하나해주고») — 빡이사 짧은 독백 실측으로 문턱을 낮게 잡음
REASON_END = ("잖아요", "거든요", "거예요", "거죠", "말이에요", "말이죠", "이거죠", "겁니다", "는 거야", "란 말이야")
SELF_QA = r"(뭐다\?|된다\?|한다\?|왜\?|뭘까요\?|뭐냐면|어떻게 해야 돼\?|뭐예요\?|그럴까요\?|말이냐\?|할까요\?|냐\?)"
CONFIRM = r"(그죠\?|그지\?|이해되시죠\?|보이시죠\?|아시죠\?|맞죠\?|그렇죠\?|있잖아요)"
PROMISE = r"(끝까지|적어 주세요|집중해|바로 시작|오늘 .{0,25}(얘기|이야기|알려|풀어|말씀|보여))"
GROWTH_END = r"(다음 영상|다음 편|댓글|좋아요|구독)"
# 다음 편 내용 약속 금지 — 사장님 10-14 «다음편 뭘 할지 정하지는 마 이게 예정대로 안될수도있는데 그냥 인사하는 마무리로»
NEXT_PROMISE = r"(다음 (영상|편)(에서|엔|은|에는)? .{0,30}(해 ?볼게|풀게|알려 ?드릴게|보여 ?드릴게|다룰게|가져올게)|다음 편 예고|2탄)"
SALES = r"(수강|강의 신청|배우러 오세요|무료 체험|상담 신청|문의 주세요|컨설팅 받으러)"


def structure(text, sents):
    """빡이사 대본결 구조 — (이름, 통과 여부, 값, 기준)"""
    n = len(sents) or 1
    L = max(len(text), 1)
    reason = sum(text.count(e) for e in REASON_END) / L * 1000
    q = sum(1 for s in sents if s.endswith("?")) / n * 100
    qa = len(re.findall(SELF_QA, text)) / L * 2000
    cf = len(re.findall(CONFIRM, text)) / L * 3000
    head, tail = text[:700], text[-700:]
    # 첫 항목까지 30초 안(10-28 — 1편 1:06 · 2편 2:01 에 첫 항목, 시청 지속 대책). 읽는 속도 8.9자/초 × 30초 ≈ 270자(공백 뺌)
    k = text.find("첫 번째")
    pre = len(re.sub(r"\s", "", text[:k])) if k >= 0 else 0
    return [
        ("첫 항목(«첫 번째»)까지 30초 안(10-28)", pre <= 270, f"{pre}자 ≈ {pre / 8.9:.0f}초" if k >= 0 else "«첫 번째» 없음", "≤270자(≈30초)"),
        ("이유·되묻기 어미(잖아요·거든요·거예요…)", reason >= 3.5, f"{reason:.1f}/천자", "≥3.5/천자 (빡이사 30편 대부분 3.5~13)"),
        ("질문 비율", q >= 5, f"{q:.1f}%", "≥5% (빡이사 10.3%)"),
        ("자문자답(«그게 뭐다? ~» «왜? ~»)", qa >= 0.5, f"{qa:.1f}/2000자", "≥0.5/2000자"),
        ("확인 질문(그죠?·이해되시죠?·있잖아요)", cf >= 0.7, f"{cf:.1f}/3000자", "≥0.7/3000자"),
        ("첫 700자 안에 약속·시청 지시(끝까지·바로 시작·오늘 ~ 알려 드릴게요)", bool(re.search(PROMISE, head)), "있음" if re.search(PROMISE, head) else "없음", "있어야"),
        ("끝 700자 안에 성장 마무리(다음 편·댓글·좋아요·구독)", bool(re.search(GROWTH_END, tail)), "있음" if re.search(GROWTH_END, tail) else "없음", "있어야"),
        ("판매 멘트 없음(성장 채널 — 수강·상담 권유 X)", not re.search(SALES, text), "없음" if not re.search(SALES, text) else "있음", "없어야"),
        ("호칭은 «대표님»만(«사장님» 없음 — 10-15 «우리는 무조건 대표님으로 호칭 통일»)", "사장님" not in text, "없음" if "사장님" not in text else f"사장님 {text.count('사장님')}번", "없어야"),
        ("«남는 돈» 대신 «수익»(10-16 «남는 돈 이라는 말은 수익이라는 단어로 항상 대체해서써줘»)", not re.search(r"남(는|은) ?돈", text), "없음" if not re.search(r"남(는|은) ?돈", text) else "있음: " + re.search(r"남(는|은) ?돈", text).group(0), "없어야"),
        ("다음 편 내용 약속 없음(끝은 인사로 — 10-14)", not re.search(NEXT_PROMISE, text), "없음" if not re.search(NEXT_PROMISE, text) else "있음: " + re.search(NEXT_PROMISE, text).group(0), "없어야"),
    ]


# 예시 업종 — 앞 세 편과 겹치면 ERROR(10-16 사장님 «매번 설명에 국밥집이나오니까 뭔가 중복컨텐츠같아 매번 예시나 그런걸 들때 앞의 세편과는 다른업종으로해줘»)
# 업종 이름 → 그 업종을 드러내는 말(메뉴·재료 포함)
INDUSTRY = {
    "국밥집": r"국밥|수육|사골|순댓국|육수",
    "고깃집": r"고깃집|삼겹살|갈빗집",
    "파스타집": r"파스타|이탈리안",
    "쌀국수집": r"쌀국수",
    "디저트 가게": r"디저트|마카롱|케이크 ?가게",
    "반찬가게": r"반찬 ?가게",
    "카페": r"카페|커피 ?전문점",
    "빵집": r"빵집|베이커리",
    "치킨집": r"치킨",
    "분식집": r"분식|떡볶이|김밥",
    "중국집": r"중국집|짜장면|짬뽕",
    "횟집": r"횟집|초밥|스시",
    "술집": r"술집|호프|이자카야|포차",
    "족발·보쌈집": r"족발|보쌈",
    "피자집": r"피자",
    "미용실": r"미용실|헤어 ?숍",
    "네일숍": r"네일",
    "꽃집": r"꽃집",
    "세탁소": r"세탁소",
    "청소 업체": r"청소 ?업체|청소기",
    "학원": r"학원|공부방",
    "헬스·필라테스": r"헬스장|필라테스|피티 ?샵",
    "병원·의원": r"병원|치과|한의원|의원",
    "옷가게": r"옷가게|의류 ?매장",
    "편의점": r"편의점",
    "공방": r"공방",
    "숙박": r"펜션|모텔|게스트하우스",
}


def industries(text):
    return {name for name, pat in INDUSTRY.items() if re.search(pat, text)}


def prev_scripts(path, back=3):
    """같은 핸드오프 폴더 이름의 «성제관NN» 에서 앞 세 편 대본을 찾는다."""
    import glob, os
    m = re.search(r"성제관(\d+)", os.path.abspath(path))
    if not m:
        return []
    n = int(m.group(1))
    if n <= 2:  # 2편은 녹음 끝(10-16 «2편은 지금이미 녹음끝») — 3편부터 적용
        return []
    root = os.path.abspath(path)
    while os.path.basename(root) != "핸드오프" and os.path.dirname(root) != root:
        root = os.path.dirname(root)
    out = []
    for k in range(max(1, n - back), n):
        out += [(k, p) for p in glob.glob(os.path.join(root, f"*성제관{k:02d}_*", "20_대본.md"))]
    return out


MEMO = re.compile(r"^\s*(#|화면\s*[:：]|\[|\(연출|>|---|\|)")


def load(path):
    lines = open(path, encoding="utf-8").read().splitlines()
    return [l for l in lines if l.strip() and not MEMO.match(l)]


def sentences(text):
    parts = re.split(r"(?<=[.?!])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    path = sys.argv[1]
    lines = load(path)
    text = " ".join(lines)
    errs = []
    for i, line in enumerate(lines, 1):
        for pat, name, alt in BANNED:
            if pat.startswith(r"^\s*안녕") and i > 3:
                continue
            for m in re.finditer(pat, line):
                errs.append((i, name, alt, line.strip()[:60]))
    warns = [(i, name, alt, line.strip()[:60]) for i, line in enumerate(lines, 1)
             for pat, name, alt in WARN for _ in re.finditer(pat, line)]
    sents = sentences(text)
    n = len(sents) or 1
    q = sum(1 for s in sents if s.endswith("?"))
    lens = [len(s) for s in sents] or [0]
    print(f"# 대본 점검 — {path}")
    print(f"문장 {len(sents)}개 · 글자 {len(text)}자 · 읽는 시간 약 {len(text)/8.9/60:.1f}분(빡이사 8.9자/초)")
    print()
    print("| 지표 | 이 대본 | 빡이사 |")
    print("|---|---|---|")
    print(f"| 질문 비율(%) | {q/n*100:.1f} | {REF['질문 비율(%)']} |")
    print(f"| 문장 길이 중앙(자) | {statistics.median(lens):.0f} | {REF['문장 길이 중앙(자)']} |")
    print(f"| 문장 길이 평균(자) | {statistics.mean(lens):.0f} | {REF['문장 길이 평균(자)']} |")
    print()
    print("문장 끝 어미:", " · ".join(f"{e} {sum(1 for s in sents if s.rstrip('.?!').endswith(e))}" for e in ENDINGS))
    print("문장 첫 접속:", " · ".join(f"{w} {sum(1 for s in sents if s.startswith(w))}" for w in STARTS))
    print()
    st = structure(text, sents)
    print("## 빡이사 대본결 구조 (study/bisa-script-1014.md)")
    for name, ok, val, ref in st:
        print(f"- {'OK ' if ok else 'ERR'} {name}: {val} (기준 {ref})")
    print()
    # 확인 질문은 경고만(빡이사 책 요약 독백 tOon 은 0회) — 나머지 구조는 ERROR
    errs += [(0, f"구조: {name}", ref, val) for name, ok, val, ref in st if not ok and not name.startswith("확인 질문")]
    mine = industries(text)
    prevs = prev_scripts(path)
    print(f"## 예시 업종 — 이 대본: {', '.join(sorted(mine)) or '없음'}")
    for k, p in prevs:
        dup = mine & industries(" ".join(load(p)))
        print(f"- {k}편: {'겹침 ' + ', '.join(sorted(dup)) if dup else '안 겹침'}")
        for name in sorted(dup):
            hit = next((l.strip()[:60] for l in lines if re.search(INDUSTRY[name], l)), "")
            errs.append((0, f"예시 업종 «{name}» — {k}편과 겹침", "앞 세 편에 안 나온 업종으로(10-16)", hit))
    print()
    if "--save" in sys.argv:
        import datetime
        rec = path.rsplit(".", 1)[0] + "_검사.txt"
        NL = chr(10)
        with open(rec, "w", encoding="utf-8", newline=NL) as f:
            f.write(f"대본 검사 기록 — {datetime.datetime.now():%Y-%m-%d %H:%M}{NL}파일: {path}{NL}글자 {len(text)} · 약 {len(text)/8.9/60:.1f}분{NL}")
            f.write(f"결과: {'통과' if not errs else '불통과'} (ERROR {len(errs)}){NL}")
            for name, ok, val, ref in st:
                f.write(f"- {'OK ' if ok else 'ERR'} {name}: {val}{NL}")
            for i, name, alt, ctx in errs:
                f.write(f"- ERROR {i}줄 {name} → {alt} | {ctx}{NL}")
        print(f"검사 기록 저장: {rec}")
    if warns:
        print(f"## WARN {len(warns)}건 — 맥락 확인")
        for i, name, alt, ctx in warns:
            print(f"- {i}줄 «{name}» → {alt} | {ctx}")
        print()
    if errs:
        print(f"## ERROR {len(errs)}건 — 빡이사가 안 쓰는 글말 · 구조 미달")
        for i, name, alt, ctx in errs:
            print(f"- {i}줄 «{name}» → {alt} | {ctx}")
        sys.exit(1)
    print("ERROR 0 — 금지어 없음 · 빡이사 구조 통과")


if __name__ == "__main__":
    main()
