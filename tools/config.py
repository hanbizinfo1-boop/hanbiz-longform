# -*- coding: utf-8 -*-
r"""한비즈 롱폼 자동화 — 경로·규격 설정 한 곳.

다른 PC 로 옮기면 여기(또는 같은 이름의 환경변수)만 고친다. 도구는 경로를 이 파일에서만 가져온다.
  예) set HANBIZ_SFX_LIB=E:\효과음\예능효과음
환경변수가 있으면 그것이 이긴다.

[원본 읽기 전용] ORIG_ROOT(D:\영상제작) · AGENT_ROOT(D:\★에이전트) 는 읽기만 한다. 이 폴더 도구는 산출물을 WORK/OUT(= 이 폴더 _tmp·납품)에만 쓴다.
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # 한비즈-롱폼자동화/
TOOLS = ROOT / "tools"


def _p(env, default):
    return Path(os.environ.get(env, default))


# ── 원본 폴더(읽기 전용 — 수정 금지)
ORIG_ROOT = _p("HANBIZ_ORIG_ROOT", r"D:\영상제작")                 # 길라잡이 문서·도구·빡이사DB 기록·강사님-강의편집
AGENT_ROOT = _p("HANBIZ_AGENT_ROOT", r"D:\★에이전트")
SUBPIPE = AGENT_ROOT / "tools" / "subtitle-pipeline"             # cut_plan_only·cut_render 가 import 하는 subpipe 패키지(읽기 전용)
RAW_ROOT = _p("HANBIZ_RAW_ROOT", r"D:\26년 10월\261001")           # 사장님 촬영 원본(후킹 건) — 건마다 바뀌면 여기만 고친다
LECTURE_SHOOT = _p("HANBIZ_LECTURE_SHOOT", r"C:\Users\user\Downloads\강의촬영본\강의촬영본\촬영본")   # 강의 촬영본(강사님 건)

# ── 애프터이펙트 (AE 2026 한국어판 — 출력 모듈 템플릿 이름이 «고품질» = ProRes 422 HQ)
AE_DIR = _p("HANBIZ_AE_DIR", r"C:\Program Files\Adobe\Adobe After Effects 2026\Support Files")
AE_RENDER_TEMPLATE = "고품질"                           # 알파 필요하면 «고품질(알파 포함)»

# ── 효과음 (음원 파일은 이 폴더에 복사하지 않았다 — 원본 경로만. 읽기 전용)
# SFX_LIB = Mixkit·Kenney·効果音ラボ 받은 것(앞말 ML_ KN_ SEL_). 등급표(GRADE_JSON)의 파일 경로가 이 폴더를 가리킨다.
SFX_LIB = _p("HANBIZ_SFX_LIB", ORIG_ROOT / "소재" / "예능효과음")
# 사장님 개인 라이브러리(앞말 없는 파일: 휙２.mp3 · 두꺼운 바람.mp3 · 맑은소리.mp3 …). 모음1~6(게임·방송 음원)은 쓰지 않는다.
SFX_LIB_OWNER = _p("HANBIZ_SFX_LIB_OWNER", r"C:\Users\user\Desktop\작업공간\효과음")
# 장면음(드론·지하철 같은 배경 소리)
SFX_LIB_SCENE = _p("HANBIZ_SFX_LIB_SCENE", r"C:\Users\user\Desktop\분양\효과음\오픈소스\16_장면음")
# 효과음 폴더 지도 — 찾는 순서(sfx_find.py · bisa_toc_cards.by_name 이 이 순서로 뒤진다). 설명은 references/sfx-workflow.md 1장
SFX_ROOTS = {
    "예능": SFX_LIB,                                   # 분류 01~16 폴더(약 680개) · 미리듣기 합본은 _청음\
    "사장님": SFX_LIB_OWNER / "효과음",                 # 사장님이 실제 편집에 쓰시는 소리 122개(휙２·맑은소리·도장·채팅 효과음·마우스 클릭…)
    "자주쓰는": SFX_LIB_OWNER / "자주쓰는 효과음",       # 사장님 단골 24개(뾰로롱·짜잔·카툰 팝·물방울·연필…)
    "말하는": SFX_LIB_OWNER / "말하는효과음",            # 목소리 효과음 46개(예능 리액션) — 강의 위엔 드물게
    "다운": SFX_LIB_OWNER / "다운효과음",               # 받아 둔 것 85개(검수 전 — 등급표 밖)
    "오픈소스": SFX_LIB_SCENE.parent,                  # 분양 때 모은 오픈소스 19분류(전환·임팩트·라이저·현장음·Kenney…)
}
SFX_PREVIEW = SFX_LIB / "_청음"                         # 분류별 미리듣기 합본 mp3 (01_쿵쾅_큰강조자막.mp3 …)
GRADE_JSON = TOOLS / "data" / "예능효과음-등급.json"      # A★ → A → B 등급표(파일 경로 문자열 + 점수)
USED_JSON = TOOLS / "data" / "예능효과음-실사용.json"      # 사장님이 실제 편집에서 통과·반려한 소리

# ── 글꼴
WIN_FONTS = Path(r"C:\Windows\Fonts")
USER_FONTS = _p("HANBIZ_USER_FONTS", r"C:\Users\user\AppData\Local\Microsoft\Windows\Fonts")
FONTS = {
    "pretendard_bold": _p("HANBIZ_FONT_PRETENDARD", USER_FONTS / "Pretendard-Bold.otf"),
    "noto_sans_kr": WIN_FONTS / "NotoSansKR-VF.ttf",     # 가변 폰트: 굵기 500 으로 쓴다(맑은 고딕 25px 은 받침이 뭉개짐)
    "noto_serif_kr": WIN_FONTS / "NotoSerifKR-VF.ttf",
    "malgun": WIN_FONTS / "malgun.ttf",
    "malgun_bold": WIN_FONTS / "malgunbd.ttf",
    "gaegu_bold": ROOT / "_tmp" / "fonts" / "Gaegu-Bold.ttf",   # 손글씨(OFL). 없으면 장면 도구가 받는다
}

# ── 작업 폴더
WORK = ROOT / "_tmp"            # 다시 만들 수 있는 것(중간 렌더·내려받은 원본). git 제외
OUT = ROOT / "납품"              # 사장님께 드리는 것. 같은 이름 제자리 덮어쓰기 — 폴더를 지우지 않는다
SRC = ROOT / "소재"              # 이 건 소재(이미지·로고). 출처는 소재/이미지-출처.md 에 한 줄씩

# ── 외부 도구
CODEX_RUN = Path(r"C:/Users/user/.claude/scripts/codex-run.ps1")
CHROME = _p("HANBIZ_CHROME", r"C:\Program Files\Google\Chrome\Application\chrome.exe")   # card_render·design 레이어 캡처
LOGO_SRC = _p("HANBIZ_LOGO_SRC", r"C:\Users\user\Downloads\한국중소기업비즈니스로고.png")    # 강의 카드 브랜드 로고(원본 경로만)

# ── 롱폼 규격 (가로). 강의 시퀀스는 59.94 fps. 건마다 시퀀스에서 재서 맞춘다.
W, H = 1920, 1080
FPS = 59.94
