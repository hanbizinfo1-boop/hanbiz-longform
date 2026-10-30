# 성제관03 장면 명세 (html 장면) — 설계자가 정한 것. 실행자는 이대로 만든다.

> 기준(이 순서로 우선): `핸드오프/2026-10-23_성제관03_배달앱수수료/20_연출표.md`(1장 두 층 규격 · 2장 장면 표 — **장면 행이 곧 명세**) → 이 SPEC → 2편 `tools/scenes/sjk02/SPEC.md` 0장 1~14번(속도·퀄리티 규칙, 아래에 줄여 옮김).
> 시각: `data/sNN.js`(녹음 강제 정렬, `S.at('말')`). 공용: `lib/sjk.css` · `lib/sjk.js` · `lib/e4.js`(E.pop·E.wipe·E.stroke·E.drift) · `lib/prog.js`(진행표 카드). 본보기: `html/s02.html`(설명 층).
> 화면 글은 `10_분석/녹음원고.md` 에 나온 말·숫자만. 지어낸 금액·통계·가게 이름 금지(가게 ○○, 전화 010-0000-0000).

## 0. 모든 장면 공통 (어기면 반려)
1. 화면이 **2초 넘게 같은 상태로 있지 않는다** — 선이 그려짐·블록이 붙음·숫자 카운트·형광펜·체크·칸이 켜짐 중 하나가 2초 안에(말에 있는 것으로만). 설명 층은 **그림을 한 단계씩 더한다**(갈아 치우지 않음 — 모냐구).
2. 전체 화면 바뀜은 서로 **2.5초 이상** 떨어진다(장면 시작 포함). 짧은 변화는 화면 일부에.
3. 같은 요소 키프레임 강조 2번까지. 느린 바탕 흐름(`E.drift` 1.00→1.04)은 세지 않음.
4. 등장 0.10~0.12초 감속(`S.ent`·`E.pop`), 튕김 0. 선은 `E.stroke`(0.3~0.6초). 카메라 이동 0.3~0.5초 `S.cam`/`S.camState`.
5. 금지: 흔들기·떨림·깜빡임·바운스·폭죽·이모티콘·까만 화면·말풍선·«» 따옴표 대사·«재현» 라벨·**화면 구석 이름표 칩**(장 표시는 진행표 카드가 맡음)·말 따라 쓰기 글·흰 종이 소품.
6. 도형으로 물건 흉내 금지 — 실물 층의 휴대폰·노트북·봉투·그릇 같은 물건은 **사진**(Codex). 설명 층의 선 그림(그릇·통장·가게·저울 **선화**)은 «도면 그림»이라 허용 — 깔끔한 2.5~4px 선, 색 채움은 파랑/빨강 옅게만.
7. 모든 움직임은 그 말 시각(`S.at`) — 못 찾으면 콘솔 경고가 나니 다른 낱말로. 새 요소는 혼자 0.6초(같은 종류 묶음은 0.25초 간격 허용).
8. 자막 자리: y 965 아래 가운데(300~1620)에 중요한 글·요소 금지. 화면 가장자리 15px 안 data-box 금지. 판·카드는 위아래 90px·좌우 120px 안(카메라 끝 프레임까지).
9. 겹쳐야 하는 것(판 위 글, 그림 안 칸)은 같은 `data-box-group`.
10. 부각 `S.focus([{t0,t1,big,small?,color:'bl'|'rd'|'gn'}])` — 장면당 2번까지, 이번 편은 **아껴 쓴다**(큰 숫자가 이미 화면 주인공이면 쓰지 않음).
11. 효과음 계기 `S.ev(τ, 역할, id)` — 그림이 실제로 바뀌는 프레임에만, **1.5초에 1개 안팎**, 같은 역할 바로 연달아 금지. 역할: `in` `card_in` `msg_in` `ok` `no` `type` `marker`(선 그리기·밑줄·형광펜) `page`(종이·주문서 출력) `paper` `gauge`(막대·차트 차오름) `shine`(핵심 숫자) `click`(누름·켜짐) `sweep`(카메라 큰 이동) `coin`(동전·돈 빠짐).
12. 동작은 보이게 — 누른다 = 손가락 위치에 눌림 고리 + 화면 바뀜 / 타자 = 입력창 타자 → 보내기 → 답.
13. 페이지 뜰 때 재서 카메라를 정하지 않는다(τ 함수 안에서, 필요하면 `S.init`/첫 seek 에서 `document.fonts.ready` 뒤 한 번).
14. 글자 최소 28px(출처 줄만 24px). 큰 숫자 `.big` 110~200px.
15. `window.PALETTE` 3색 안(설명 층 기본 `['#F4F5F2','#20262D','#1F5FD1']` + 빨강이 뜻이면 4번째로 적고 WARN 이유 보고).

## 1. 설명 층 (`.grid` 모눈 바탕)
- `<div id="cam" class="abs"><div class="grid"></div> … </div>` — 바탕과 그림이 같이 움직인다(본보기 s02). 빈 모눈 1초 이상 금지 — 장면 첫 0.1초 안에 첫 선이 그려지기 시작.
- 선 그림은 SVG `class="ln"`(+`bl`/`rd`/`gn`/`w4`/`w6`). 칸·카드 `.card`. 큰 숫자 `.big`(빨강은 `.big.rd`). 글 `.t`.
- 화면의 **60~80%** 를 쓰는 크고 시원한 그림(작은 그림이 가운데 몰리면 반려). 글은 그림에 붙은 이름 몇 단어·숫자만.
- 앞 그림 다시 쓰기(장면 36·52·62·66·67·70): 그 장면의 html 에서 그림 SVG 를 **복사**해 같은 모양으로(다른 모양으로 다시 그리지 않음).
- 진행표 카드(장면 7·9·37·53·67): `lib/prog.js` `PROG.mount('#cam', {x:360,y:330,w:1200,h:380})` → `PROG.draw(pc, [{show,on}×3], frame)`. «칸으로 밀고 들어감»(9·37)은 `S.camState` 로 그 칸(`pc.cells[i]`)을 화면 가득 키운 뒤, 칸 안 파랑 바탕 위에 장 그림을 그린다(전환 «into» 는 조립기가 0.36초 디졸브로 받침).
- 출처 줄 `.src` 는 카드 바로 아래 12~20px.

## 2. 실물 층 (Codex 사진)
- 사진: `소재/sjk03/codex/<이름>.png`(1536×1024). `<div id="ph" class="photo"></div>` + `style.backgroundImage = S.ph('이름')`. 사진 이름은 3장 표. 카메라 «천천히 밀기/당기기/옆 흐름»은 `#ph` 의 transform(1.00↔1.08, 옆 흐름은 translateX ±40px 를 장면 길이에 걸쳐). 2.5D 표시 장면도 이 느린 움직임으로.
- 초록 화면 사진(`d..`): `<이름>_clean.png` 를 깔고(초록 지운 사본), 화면 UI 는 `소재/sjk03/codex/quads.json` 의 `stage` 네 점에 `S.fitQuad(el, w, h, quad)` (값은 장면 파일에 복사 — fetch 막힘). 사진과 UI 는 같은 래퍼 안에서 같이 움직인다.
- 재현 화면 UI 는 어두운 `.app`(상표·실제 앱 이름·로고 없음, 버튼·켜짐은 파랑). 화면 글은 녹음 원고 말만.
- 사진 위 숫자는 `.dpan` 하나에 숫자만(«≈ 4,000원» 등 연출표 그대로). 쪽지 글은 `.kraft`/`.memo` + `.hand`(연출표의 대본 글 그대로).
- «정면 화면 가득»(장면 24·42) = 사진 없이 `.app` 를 화면 가득 크게(약 1500×900, 살짝 기울인 판 `perspective(2200px) rotateX(6deg)`) — 바탕은 앞 장면 사진을 흐리게(`filter: blur(18px) brightness(.55)`).
- 표 칸(정산서·보고서·계산 노트)은 HTML 로 그린다: 실물 층에선 사진 위에 놓인 **종이 결 카드**(바탕 `#EFEAE0` + `p12_paper_macro` 질감 `background-blend-mode:multiply`, 얇은 그림자, 원근 살짝).

## 3. 사진 이름 (장면 → 사진)
1 p01_pack_counter · 3 p03_counter_top · 5 p05_order_printer · 6 p06_two_shops · 8 d08_phone_counter_thumb · 10 p10_menu_wall → p10b_calculator_hand(+앱 메뉴 화면은 `.app` 작은 판) · 12 p12_paper_macro · 14 p14_desk_top · 16 p16_kitchen_staff → p16b_hand_bills · 18 p18_rider_small_bag · 20 p20_tteokbokki_top · 22 p22_ticket_rail · 24 (사진 없음 — 정면 화면 가득, 바탕 d08 흐림) · 26 p26_empty_hall_noon · 28 p28_street_birdseye · 30 p30a_recipe_note p30b_bowl_handing p30c_stamp_card p30d_warm_hall · 32 p32_office_lunch · 33 p33_rice_bowl_top · 35 p35a_scooters_many → p35b_scooters_one · 38 d38_phone_counter_side · 40 d40_bus_phone · 42 (사진 없음 — 정면 화면 가득, 바탕 d38 흐림) · 44 d44_sofa_phone → 같은 사진 여러 장 격자(2×3, 칸마다 같은 배너) · 46 d46_tablet_table · 48 p48_shop_window_note · 49 d49_laptop_night · 51 p51_busy_door · 54 p54_door_inside · 56 d56_home_phone_top · 58 p58_bag_handle_macro · 60 p60_jokbal_pack · 61 p61_note_macro · 63 p63_fridge_magnet · 65 p65_memo_board · 68 p68_counter_hall · 69 p69_closing_counter · 71 p71_pack_handover
- 사진이 없거나 사진 속에 읽히는 글자·로고·사람 얼굴이 보이면 쓰지 말고 보고(설계자가 다시 만든다).

## 4. 만드는 법 · 확인
1. `html/s02.html` 구조를 따라 `html/sNN.html`. `<script src="../data/sNN.js">` → `../lib/sjk.js` → `../lib/e4.js`(→ 필요하면 `../lib/prog.js`).
2. 렌더: `PYTHONIOENCODING=utf-8 py -3.11 tools/html_motion.py tools/scenes/sjk03/html/sNN.html --sub 1 --workers 3 --out _tmp/sjk03/render --name sNN`
3. 확인(전부 해야 완료):
   - `_tmp/sjk03/render/sNN_점검.txt` ERROR 0.
   - 정지 화면: 파이썬 subprocess 로 ffmpeg 를 불러(셸 경로에 한글이 있어 bash 직접 호출은 깨짐) 1초 간격 + 박자 시각 몇 곳 → `_tmp/sjk03/review/<너의이름>/` → **Read 로 직접 본다**. 볼 것: 글 잘림·넘침·겹침 · 빈 화면 · 작게 몰린 그림 · 자막 자리 침범 · 2초 넘게 같은 화면 · 사진 위 UI 원근 · 선이 글을 지나감.
   - `py -3.11 tools/scenes/sjk02/jitter_check.py` 는 sjk02 경로 고정이라 쓰지 않는다. 대신 페이지 뜰 때 재는 값이 없게(0장 13번).
4. 셸에서 `cd` 금지(훅이 막힌다). 항상 절대 경로.
