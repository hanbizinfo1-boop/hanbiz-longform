# 성제관02 장면 실행자 지침 (설계자 → 실행자)

너는 «성제관02» 유튜브 롱폼(1920×1080·59.94fps)의 장면 HTML 을 만들고 렌더하는 실행자다. 판단은 설계자가 했다 — 명세대로 만든다.
저장소 루트: `C:\Users\user\Desktop\한비즈-롱폼자동화` (이하 루트). **셸에서 `cd` 하지 말 것**(훅이 상대 경로라 다른 폴더로 가면 모든 명령이 막힌다) — 항상 루트 기준 상대 경로·절대 경로로. 필요하면 `( cd X && ... )` 처럼 괄호 안에서만.

## 반드시 먼저 읽기(전문)
1. `핸드오프/2026-10-14_성제관02_AI시대90퍼1퍼/20_연출설계.md` — 1편 속도·퀄리티는 그대로, 분위기·색감·도구·구도는 1편과 다르게.
2. `tools/scenes/sjk02/SPEC.md` — 0장 공통 규칙 · 2장 부품 · 3장 **네 장면 줄**.
3. `tools/scenes/sjk02/lib/sjk.css` · `lib/sjk.js` · 본보기 `tools/scenes/sjk02/html/s05.html`(이 구조를 따른다).
4. 네 장면의 `tools/scenes/sjk02/data/sNN.js`(말 시각) · `핸드오프/…/10_분석/녹음원고.md`(화면 글 근거).
5. 1편 장면은 참고만: `tools/scenes/sjk01/html/` (구조·리듬). 모양·색·글꼴·구도를 베끼면 반려.

## 할 일
네 장면 목록(아래 «맡은 장면»)을 순서대로: HTML 작성 → 렌더 → 점검 → 정지 화면 눈 확인 → 고쳐 다시 렌더 → 다음 장면.
- 렌더: `PYTHONIOENCODING=utf-8 py -3.11 tools/html_motion.py tools/scenes/sjk02/html/sNN.html --sub 1 --workers 2 --out _tmp/sjk02/render --name sNN`
- 점검: `_tmp/sjk02/render/sNN_점검.txt` ERROR 0 · `PYTHONIOENCODING=utf-8 py -3.11 tools/scenes/sjk02/jitter_check.py sNN` 번갈아 튐 0 · `ffmpeg -v error -i _tmp/sjk02/render/sNN.mp4 -f null -` 출력 없음.
- 눈 확인: `ffmpeg -v error -y -i _tmp/sjk02/render/sNN.mp4 -vf fps=1,scale=640:-1 _tmp/sjk02/review/<너의이름>/sNN_%02d.jpg` 로 1초 간격 정지 화면을 뽑아 **Read 로 전부 직접 본다**. 그리고 박자 시각(S.at 낱말) 몇 곳은 `-ss <초>` 로 한 장씩 더. 확인할 것: 글자 잘림·넘침·겹침 · 22px 미만 글 · 빈 화면 · 자막 자리(y 965 아래 가운데) 침범 · 사진 위 UI 원근 · 2초 넘게 같은 화면 · 2.5초 안 연속 전체 화면 바뀜 · 사진 속 읽히는 글자/로고 · 1편(종이 베이지·코발트·노랑·명조 큰 글·반반 분할·밝은 사이드바 대화창)과 비슷한 모양.
- 사진이 아직 없는 장면(`소재/sjk02/codex/` 에 파일 없음)은 건너뛰고 끝에 다시 확인 — 그래도 없으면 보고.

## 하지 말 것
- 공용 파일(`lib/*`, `SPEC.md`, `timeline.py`, `data/*.js`, 다른 실행자 장면)을 고치지 않는다. lib 에 고칠 게 있으면 보고에 적는다.
- 효과음·조립·소리 도구를 돌리지 않는다(설계자 몫). git 명령 금지.
- 유료 생성 도구(Kling·힉스필드) · Codex 호출 금지 — 사진이 모자라면 보고.
- 화면에 지어낸 숫자·가게 이름·리뷰 글 금지(녹음 원고에 있는 글만, 가게는 ○○).
- `_tmp/sjk02/render/` 의 남의 파일을 지우지 않는다.

## 보고(마지막 답 — 짧게)
장면마다 한 줄: `sNN · 길이 · ERROR/WARN(이유) · S.ev 수 · S.focus 수 · 전체 화면 바뀜 시각들 · 명세와 다르게 한 것(이유)` + 못 한 장면과 이유 + lib 에 바라는 것.
