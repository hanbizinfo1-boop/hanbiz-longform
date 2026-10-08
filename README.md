# 한비즈 롱폼 자동화

한비즈 **롱폼(강의형 가로 1920×1080 · 59.94fps) 영상 편집 자동화** 전용 작업 폴더. Claude Code 세션이 열자마자 일할 수 있게 스킬·도구·규칙을 담았다.
**이 저장소는 private 이어야 한다.** 영상·음원·프로젝트·이미지 바이너리와 고객 정보는 커밋하지 않는다(`.gitignore`).

## 폴더

```
한비즈-롱폼자동화/
├─ CLAUDE.md                 # 이 세션 규칙(하드 규칙) + 시작할 때 읽는 순서
├─ README.md                 # 이 파일
├─ .gitignore · .gitattributes
├─ .claude/
│  ├─ settings.json          # SessionStart(compact|resume) 훅 → python tools/resume_guide.py
│  └─ skills/longform/
│     ├─ SKILL.md            # 핵심 스킬: 단계 P0~P7 · 멈추는 곳 · 사장님 상시 규칙 · 범위 · 길 고르기 · 도구 · 점검표
│     └─ references/
│        ├─ motion-graphics.md   # 말하는 사람 위 애펙 장면: 한눈에 · 그림 길 A/B · 순서 · 납품 형태 · 통과/반려 · 영상미 · 함정
│        ├─ sfx.md               # 효과음 문법 · 파일별 크기 · 고르기 · 반복/빈 구간 · 검사 · 라이브러리 요약
│        ├─ silence-cut.md       # 무음편집 안전판 · 사장님 컷 실측 · 싱크 함정
│        ├─ lecture-graphics.md  # 강의 자료: 작업 방식 · 편집 문법 · 포토카드 통과 틀 · 보조 패널 · 자막 타이밍 자료
│        ├─ ai-video.md          # Codex 시작프레임 → 유료 영상화 · 사진풍 · 영상화 직전 점검
│        ├─ feedback-log.md      # 장면 기록 쓰는 법 · 장면별 사장님 피드백 원문
│        └─ checklist.md         # 납품 전 점검표 A~F
├─ tools/                    # 재사용 도구. 경로는 전부 config.py 한 곳
│  ├─ config.py · rule_check.py · glyph_check.py · resume_guide.py · sfx_find.py(효과음 찾기)
│  ├─ read_lecture_edit.py · lecture_edit_profile.py · lec_xml.py · overlay_xml.py   # 프리미어 읽기 · XML
│  ├─ transcribe_words.py · srt_from_words.py · cut_plan_only.py · cut_render.py · pause_compress.py · cut_diff_study.py
│  ├─ apply_removals.py · cut_to_fcpxml.py · cut_to_fcpxml_dual.py · sync_curve.py · rec_av_check.py · render_preview.py · final_preview.py
│  ├─ card_render.py · side_panel_render.py · side_panel_place.py · mosaic_scan.py · mosaic_render.py
│  ├─ bisa_web_vs_instant.py · bisa_meta_sfx.py · bisa_toc_cards.py · bisa_meta_cards.py · rf3_ae.py · design_layers.py   # 장면 프레임워크
│  ├─ data/                  # 예능효과음-등급.json · 예능효과음-실사용.json
│  └─ examples/              # 통과/최신 장면 도구 «본보기»(실행 보장 없음) — 어떤 장면의 본보기인지는 각 파일 docstring
├─ 기록/작업기록.md          # 지금 상태 · 다음 작업 예정 · 건 정보(사용 허락 범위) · 장면 틀
├─ 소재/                     # 이 건 소재(이미지·로고) + 소재/이미지-출처.md
├─ 납품/                     # 사장님께 드리는 것(같은 이름 제자리 덮어쓰기)
└─ _tmp/                     # 임시(중간 렌더·내려받은 원본). git 제외
```

원본(**읽기 전용 참조**): `D:\영상제작`(길라잡이 문서·도구·강의편집·빡이사DB 기록) · `D:\★에이전트`(`tools/subtitle-pipeline` 의 `subpipe` 패키지 — `cut_plan_only.py`·`cut_render.py` 가 import). 이 폴더에서 원본을 수정하지 않는다. 효과음 음원은 이 폴더에 복사하지 않았고 원본 경로만 `tools/config.py` 에 있다.

## 새 PC 세팅

1. **Python 3.11** + 패키지: `pip install numpy pillow opencv-python faster-whisper fonttools`(단어 시각 `faster-whisper` 는 이 PC 에서 `device="cpu", compute_type="int8", medium`; GPU 쓰는 `transcribe_words.py` 는 torch 의 cublas 때문에 `import torch` 를 먼저 한다). 모자이크(보관용)는 `easyocr` 도 필요.
2. **ffmpeg / ffprobe** 를 PATH 에 — 컷 렌더·미리보기·효과음 다듬기·XML 길이 계산.
3. **After Effects 2026(한국어판)** — 기본 경로 `C:\Program Files\Adobe\Adobe After Effects 2026\Support Files\`(`AfterFX.exe`, `aerender.exe`). 출력 모듈 템플릿 이름 «고품질». 앞 실행이 비정상 종료되면 «충돌 복구 옵션» 창이 스크립트를 막는다 → `bisa_web_vs_instant.run_ae_guarded` 가 지켜본다.
4. **Google Chrome** — 클로드 디자인 아트보드 레이어 PNG(`design_layers.py`) · 자료 카드 캡처(`card_render.py`).
5. **글꼴** — Pretendard Bold(`C:\Users\<사용자>\AppData\Local\Microsoft\Windows\Fonts\Pretendard-Bold.otf`) · Noto Sans KR VF · Noto Serif KR VF(`C:\Windows\Fonts\`) · 손글씨 개구 굵게(Gaegu Bold, OFL; `_tmp/fonts/Gaegu-Bold.ttf`, 없으면 장면 도구가 받는다) · G마켓 산스(강의 카드). 경로는 `tools/config.py` `FONTS`.
6. **효과음 라이브러리(읽기 전용 원본)** — `SFX_LIB` = `D:\영상제작\소재\예능효과음`(Mixkit `ML_` · Kenney `KN_` · 効果音ラボ `SEL_`) · `SFX_LIB_OWNER` = `C:\Users\user\Desktop\작업공간\효과음`(앞말 없는 사장님 파일, 한글 파일명이 NFD 일 수 있어 NFC 로 정규화해 찾는다) · `SFX_LIB_SCENE`(장면음). 새 PC 에서는 `HANBIZ_SFX_LIB` 등 환경변수로 옮긴 위치를 가리킨다. 재배포 금지 라이선스 소재(効果音ラボ 등)는 저장소에 올리지 않는다. `모음1~6`(게임·방송 음원)은 쓰지 않는다.
7. **Codex CLI** — 이미지는 Codex 내장 `image_gen` 으로(추가 과금 없음). 호출 스크립트 `C:\Users\user\.claude\scripts\codex-run.ps1` 은 이 폴더 밖(사용자 홈)에 있다. 인증이 풀리면(401) 터미널에서 `codex login`.
8. **유료 생성 MCP** — Kling · 힉스필드(claude.ai 커넥터). 호출마다 과금. Kling 은 세션에서 `who_am_i` 를 먼저 부른다.
9. **Premiere Pro** — 사장님 편집본(`.prproj`)은 gzip XML 이라 `read_lecture_edit.py` 로 읽는다(Premiere 설치 불필요). 열려 있는 프로젝트는 **사본을 떠서** 읽는다. 자동저장본(`Adobe Premiere Pro Auto-Save\`)이 가장 최신.

### 경로를 바꾸려면

`tools/config.py` 를 고치거나 환경변수로 덮어쓴다:

| 환경변수 | 뜻 |
|---|---|
| `HANBIZ_ORIG_ROOT` | 원본 `D:\영상제작` (읽기 전용) |
| `HANBIZ_AGENT_ROOT` | 원본 `D:\★에이전트` (읽기 전용, subpipe) |
| `HANBIZ_RAW_ROOT` | 사장님 촬영 원본 폴더(건마다) |
| `HANBIZ_LECTURE_SHOOT` | 강의 촬영본 폴더 |
| `HANBIZ_AE_DIR` | After Effects `Support Files` 폴더 |
| `HANBIZ_SFX_LIB` · `HANBIZ_SFX_LIB_OWNER` · `HANBIZ_SFX_LIB_SCENE` | 효과음 라이브러리 3곳 |
| `HANBIZ_FONT_PRETENDARD` · `HANBIZ_USER_FONTS` | 글꼴 |
| `HANBIZ_CHROME` · `HANBIZ_LOGO_SRC` | chrome.exe · 강의 카드 로고 |

### 설치 확인

```powershell
cd tools
python -c "import config, rule_check, glyph_check, lec_xml, read_lecture_edit, design_layers, rf3_ae, bisa_meta_sfx, bisa_toc_cards, bisa_web_vs_instant, resume_guide; print('ok')"
```
`examples/` 는 본보기라 import 확인 대상이 아니다. `cut_plan_only`·`cut_render` 는 `D:\★에이전트` 가 있어야 import 된다.

## 쓰는 법 한눈에

- 세션을 열면 `CLAUDE.md` → `.claude/skills/longform/SKILL.md` 순으로 읽는다(자동 압축·재개 때는 훅이 상시 규칙을 다시 넣는다).
- 한 편 흐름: P0 접수 → P1 무음편집(안전판) → P2 **사장님 컷·자막 확정** → P3 최신 자동저장 prproj 읽기 → P4 장면 연출 → P5 효과음 → P6 납품 3종 → P7 피드백 기록.
- 장면 하나: 앞뒤 맥락 → 단어 시각 → 구도 → 그림 → 정지 스토리보드 → 겹침 검사·애펙 → 효과음 → 점검(`checklist.md`) → 납품 3종 → 폴더 열기.
- 새 장면 도구는 `tools/scenes/` 에 `examples/` 의 가장 가까운 본보기를 복사해 시작한다(입력 소재 경로를 자기 건 것으로 바꾼다).
- 강의 자료 카드는 `tools/examples/lec12_card01.py` 복사로 시작(`lecture-graphics.md` 5장).

## 커밋

자동으로 하지 않는다. 사용자가 요청할 때만 커밋·푸시한다. 비공개 저장소 이름은 사용자가 정한다.
