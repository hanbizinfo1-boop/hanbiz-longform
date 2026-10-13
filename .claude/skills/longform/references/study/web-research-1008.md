# 웹 조사 — 유튜브 강의·인기 쇼츠 편집 기법 (2026-10-08, 템플릿 서랍 근거)

> WebSearch·WebFetch 결과(영상 직접 해부 아님). 값 표시: **[출처값]** 글에 숫자 있음 · **[벤더추정]** 도구 회사가 쇼츠를 보고 추정 · **[일반론]** 출처 없음.
> **국내 강의 채널 편집 분석 글은 하나도 없었다** — 국내 문법은 프레임 해부(아래 D)로만 얻는다.
> 확인 안 된 통계(«85% 무음 시청», «질문 훅 유지율 25~35%↑»)는 쓰지 않는다.

## 1. 쓸 만한 출처값 (템플릿 수치 근거로 써도 되는 것)

| 기법 | 값 | 출처 |
|---|---|---|
| 마커 스윕 하이라이트 | 0.3~0.6초, 단어를 말하는 순간 끝나야 함(10프레임 늦어도 어색), 문장당 1개, 처음 빠르고 끝 부드럽게 | https://autoae.online/blog/how-to-make-highlight-text-animation-video |
| 펀치인 | 스케일 키를 1~2프레임 간격으로 찍으면 탁 튐, 앵커는 얼굴. **새 문장 시작에서만**(몇 초마다 바꾸지 않음) | https://www.autocut.com/en/blogs/tutoriel-zoom-premiere-pro/ · https://agent.vizard.ai/how-to/stop-the-punch-ins-cycling-too-fast-in-a-talking-head-edit.html |
| 3D 카메라 풀백 전환(Vox식) | 두 시퀀스를 3D 레이어로, 편집점 몇 프레임 전부터 카메라를 뒤로, EasyEase·그래프 정점이 편집점, 블러는 이동보다 짧게 | https://www.premiumbeat.com/blog/replicating-vox-motion-graphic/ |
| 12fps 스터터 그래픽(Vox식) | 그래픽을 12fps 로 렌더해 24fps 타임라인에 | 같은 글 |
| 거친 로워서드 마스크 리빌 | 거친 텍스처 PNG + 프레임 건너뛰며 불균일 확장, 글자는 몇 프레임 늦게 | 같은 글 |
| 텍스처 모션 배경 | 텍스처 5~6장을 초당 2~3장, 2~3번 복제해 약 10초 | 같은 글 |
| 텍스트 매치컷(JH식) | 같은 문구가 보이는 캡처 12장+를 문구 중앙 정렬로, 첫 클립 약 8프레임 → 점점 짧게, 컷마다 셔터음 | https://blog.motionarray.com/learn/premiere-pro/edit-documentary-in-premiere-pro/ |
| 사진 슬라이드인 + 블러(JH식) | 8프레임 지점 위치 키, 위에서 슬라이드인, 블러 약 50에서 사라짐, 프로젝터·셔터음 | 같은 글 |
| 지도 리빌(JH) | 지도 복제 → 아래층 패턴 → 트랙매트로 서서히 · AE + GEOlayers + Mapbox 스타일 | https://community.adobe.com/t5/after-effects-discussions/how-does-johnny-harris-do-this-mask-reveal-animation-in-after-effects/td-p/15191636 |
| 키네틱 타이포 | 한 장면 3~7단어, 한 서체 계열의 굵기 위계만, 문장은 음성에 맞춰 도착 | https://pexo.ai/tutorial/how-to-make-a-kinetic-typography-explainer-video |
| 전환 길이 계산 | A 40f + B 60f + 전환 30f = 70f (두 장면이 겹쳐 총 길이 줄어듦) | https://www.remotion.dev/docs/transitioning |
| 캡션(Hormozi식) | 2~4단어, 말하는 단어만 노랑[벤더추정] · 두 줄, 한 줄 15자 이하, 최소 2초[출처값] | https://www.submagic.co/blog/how-to-make-alex-hormozi-captions |
| Kurzgesagt 작업 | Illustrator → AE 60fps, 패스 애니·표현식 루프·타임 리매핑·멀티스테이트 화면·RubberHose 리깅 | https://www.skillshare.com/en/classes/Motion-Graphics-with-Kurzgesagt-%E2%80%93-Part-1/631970755 |
| 예능 자막(국내 PD) | 말 자막과 강조 자막 분리, 강조 자막에만 모션·CG, 짤·댓글 자막화(과하면 흐름 해침) | https://www.dailian.co.kr/news/view/1119954/ |

벤더추정(참고만): Hormozi 샷 1~3초·펀치인 10~20% · Ali Abdaal 샷 2~5초·흑백+노랑·구절 단위 손글씨 자막(https://www.choppity.com/tools/recreate-video-editing-style/ali-abdaal/). 화면녹화 줌 150~200%, 은은 2~3초 / 강하게 1~2초(https://www.screen.studio/guide/adding-editing-zooms, 미검증).
주의: 2.5D 패럴랙스는 다큐에서 «클리셰» 지적(https://blog.motionarray.com/learn/after-effects/animate-flat-2d-images-after-effects/).

## 2. 시장 템플릿 카테고리 → 우리 서랍

| 우리 | 시장 카테고리 |
|---|---|
| GU 구성 | 없음 — 직접 설계 |
| CA 카메라 | 거의 없음(Remotion Layouts 의 PIP·Slide to Split 정도) — 직접 설계 |
| EM 강조 | Text · Captions · Callouts(방향 5분류) · Quote card · Metric label · Highlighter · Circle/Strike marker · Speed lines · Article/Comment highlight |
| SC 장면 | Data(차트 5종·카운터) · Maps · Backgrounds(종이·노트·텍스처) · Infographics · Storytelling · Polaroid |
| TR 전환·표지 | Transitions(cut/overlap/overlay) · Title sequences · Chapter marker · Lower thirds(이름·장소) · Rotating cards |
| OE 오프닝·엔딩 | Openers · Logo stings · End card · Subscribe nudge · CTA overlay |
| SD 소리 | Whoosh(전환 길이에 맞춤) · Riser(피크를 리빌에) · Impact(타이틀에만) · Pop/Click · 셔터·프로젝터 |

출처: https://convert.remotion.dev/elements · https://elements.envato.com/video-templates · https://hera.video/templates/overlay-motion-graphics-pack · https://pixflow.net/youtubers-bundle/ · https://motionbro.com/

## 3. 쇼츠 훅 (롱폼 오프닝에 옮길 것)

훅 = 첫 프레임 · 첫 문장 · 화면 글자 · 약속의 네 겹. 유형 7: 결과 먼저 / 정확한 질문 / 문제-해결 / 스토리 티저 / 놀라운 주장 / 시각 공개 / 직접 약속(https://www.bytecap.io/research/best-hooks-for-youtube-shorts). 첫 프레임은 소리 없이도 읽혀야 함. 긴 인트로·채널 범퍼 생략(https://subscribr.ai/p/scripting-youtube-shorts-engagement).

## 4. 프레임 해부할 영상 (D 목록 — yt-dlp 로 받아 `ref_study` 로 해부, 내용은 아직 안 봄)

우선 1순위(한비즈 강의와 가장 가까움): 
- Thomas Frank «The ULTIMATE Second Brain Setup in Notion» https://www.youtube.com/watch?v=vs8WQh2k-Ow — 화면녹화 위주 강의의 줌·멀티앵글·투명 처리
- 슈카월드 «[경제T슈카쌤] OT» https://www.youtube.com/watch?v=oBDnEPnnOz0
- 단희TV «내가 만든 유튜브 영상 한개의 놀라운 힘 7가지» https://www.youtube.com/watch?v=vlhYKW9jImg — N가지 번호 연출
- 체인지그라운드 «말투 하나로 상대방의 마음을 바꾸는 4가지 방법» https://www.youtube.com/watch?v=ePlqNoiws9c
- 신사임당 «쇼핑몰 창업 준비 집에서 혼자 하는 방법» https://m.youtube.com/watch?v=J1fFX1lTJEs — 업로더 공식 여부 확인 필요
- 부읽남 «자본주의에서는 '이런 사람이' 부자가 됩니다» https://www.youtube.com/watch?v=hrfr9isodQM

지도·그래프 원형: Johnny Harris MLK https://www.youtube.com/watch?v=TfIQNTZIktw · Wendover «How Budget Airlines Work» https://www.youtube.com/watch?v=069y1MpOkQY · Polymatter «Demographic Collapse» https://www.youtube.com/watch?v=vTbILK0fxDY
2D·벡터·도식 원형: Kurzgesagt «The Egg» https://www.youtube.com/watch?v=h6fcK_fRYaI · 3Blue1Brown «But what is a neural network?» https://youtube.com/watch?v=aircAruvnKk
그 밖: Veritasium https://www.youtube.com/watch?v=DxL2HoqLbyA · Fireship «Redis in 100 Seconds» https://www.youtube.com/watch?v=G1rOthIU-uo · Ali Abdaal «How to study for exams» https://www.youtube.com/watch?v=ukLnPbIffxE · 조코딩 https://www.youtube.com/watch?v=yGhAT4bwB1s · 노마드코더 https://www.youtube.com/watch?v=3CuUmy7jX6k · 김작가TV 쇼츠 https://www.youtube.com/shorts/yIPCoGXmVe0 · 드로우앤드류 https://www.youtube.com/watch?v=snAcqJmDwss
