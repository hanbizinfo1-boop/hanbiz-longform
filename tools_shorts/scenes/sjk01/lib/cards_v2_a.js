// 성제관01 v2 — 플랫폼 화면 모양 카드 10종 + AI 대화창(사이드바형) — 장면 5·6·4·15 공용(실행자 A).
// 글·숫자는 20_재현자료.md 그대로. 회사 로고·실제 앱 이름 없음. 카드 한 장 = 300×340 (px).
(function () {
  const css = `
.v2c{position:relative;width:300px;height:340px;background:#fff;border-radius:16px;overflow:hidden;font-family:"UI";color:#1A1A1A;box-shadow:0 16px 36px rgba(0,0,0,.30),0 2px 6px rgba(0,0,0,.2)}
.v2c *{box-sizing:border-box}
.v2c .hd{height:46px;display:flex;align-items:center;padding:0 16px;gap:8px;font-size:22px;font-weight:700;border-bottom:1px solid #E6E8EC;background:#fff}
.v2c .bd{padding:12px 16px}
.v2c .t22{font-size:22px;line-height:1.4}
.v2c .gr{color:#6B7280}
.v2c .row{display:flex;align-items:center;gap:10px}
.v2c .av{flex:none;width:42px;height:42px;border-radius:50%;background:#D5D8DE;display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:700;color:#4B5563}
.v2c .reply{margin-top:10px;background:#F1F2F4;border-radius:10px;padding:8px 12px;font-size:22px;line-height:1.35;color:#333}
.v2c .reply b{display:block;font-size:22px;color:#111;margin-bottom:2px}
.v2c .thumb{width:100%;height:110px;background-size:cover;background-position:center}
.v2c .badge{display:inline-block;font-size:22px;padding:0 8px;border-radius:6px;background:#FFE9D6;color:#D9480F;font-weight:700}
.v2c .pill{display:inline-block;font-size:22px;padding:0 10px;border-radius:999px;font-weight:700}
.v2c table{border-collapse:collapse;width:100%;font-size:22px;table-layout:fixed}
.v2c td,.v2c th{border:1px solid #D9DCE1;padding:4px 6px;text-align:center;white-space:nowrap;overflow:hidden;font-weight:500}
.v2c th{background:#F1F2F4;color:#6B7280;font-weight:500}
.v2c td.rn{background:#F1F2F4;color:#6B7280;width:30px;padding:4px 0}
.v2c td.l{text-align:left}
.v2c .bub{max-width:244px;border-radius:20px;padding:10px 14px;font-size:22px;line-height:1.4}
.v2c .bub.me{background:#2F7BF5;color:#fff;border-bottom-right-radius:6px;margin-left:auto}
.v2c .ck{flex:none;width:24px;height:24px;border:2.5px solid #9AA1AC;border-radius:6px}
.v2c .heat td{width:64px;font-weight:700;color:#1A1A1A}
.v2c .doc{padding:14px 20px;font-family:"Serif";font-weight:700}
.v2c .btn{display:block;text-align:center;background:#2F7BF5;color:#fff;font-weight:700;border-radius:10px;padding:6px 0;font-size:22px}
/* AI 대화창(사이드바형) */
.aic{position:absolute;display:flex;background:#fff;border-radius:18px;overflow:hidden;box-shadow:0 40px 90px rgba(0,0,0,.45);font-family:"UI";color:#1A1A1A}
.aic .sb{flex:none;width:300px;background:#F4F5F7;border-right:1px solid #E3E5E8;padding:20px 16px;display:flex;flex-direction:column;gap:10px}
.aic .sb .nw{display:flex;align-items:center;gap:10px;border:1.5px solid #D2D6DC;border-radius:12px;padding:10px 14px;font-size:24px;font-weight:700;background:#fff}
.aic .sb .it{font-size:22px;padding:8px 12px;border-radius:8px;color:#374151;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.aic .sb .it.on{background:#E3E7EE;font-weight:700}
.aic .sb .cap{font-size:22px;color:#8A8F98;padding:4px 12px}
.aic .mn{flex:1;display:flex;flex-direction:column;min-width:0}
.aic .tp{height:60px;display:flex;align-items:center;justify-content:center;border-bottom:1px solid #EDEEF1;font-size:24px;font-weight:700;gap:8px}
.aic .tp i{display:inline-block;width:12px;height:12px;border-right:2.5px solid #333;border-bottom:2.5px solid #333;transform:rotate(45deg) translate(-3px,-3px)}
.aic .ms{flex:1;padding:26px 44px;display:flex;flex-direction:column;gap:24px;overflow:hidden}
.aic .me{align-self:flex-end;max-width:78%;background:#EEF1F6;border-radius:20px;padding:14px 22px;font-size:28px;line-height:1.55}
.aic .ai{display:flex;gap:16px;align-items:flex-start;font-size:28px;line-height:1.6;color:#222}
.aic .ai .a{flex:none;width:42px;height:42px;border-radius:50%;background:#2E55D9;margin-top:4px}
.aic .inp{margin:0 36px 28px;min-height:72px;border:2px solid #D7DBE2;border-radius:36px;display:flex;align-items:center;gap:14px;padding:0 18px 0 22px;font-size:27px;color:#9AA1AC}
.aic .inp .tx{flex:1;white-space:nowrap;overflow:hidden}
.aic .inp .snd{flex:none;width:46px;height:46px;border-radius:50%;background:#1A1A1A;display:flex;align-items:center;justify-content:center}
`;
  const st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);

  const star = (sz, on) => `<svg width="${sz}" height="${sz}" viewBox="0 0 24 24" style="flex:none"><path d="M12 2l3.1 6.6 7.2.9-5.3 5 1.4 7.1L12 18l-6.4 3.6L7 14.5 1.7 9.5l7.2-.9z" fill="${on ? '#F5A800' : '#D5D8DE'}"/></svg>`;
  const stars = (n, sz) => '<span style="display:flex;gap:2px">' + [1, 2, 3, 4, 5].map(i => star(sz, i <= n)).join('') + '</span>';
  const ic = {
    heart: '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#374151" stroke-width="2"><path d="M12 21s-8-5.2-8-11a4.5 4.5 0 018-2.8A4.5 4.5 0 0120 10c0 5.8-8 11-8 11z"/></svg>',
    chat: '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#374151" stroke-width="2"><path d="M4 5h16v11H9l-5 4z"/></svg>',
    send: '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#374151" stroke-width="2"><path d="M21 3L3 11l7 3 3 7z"/></svg>',
    clip: '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#6B7280" stroke-width="2" stroke-linecap="round"><path d="M20 11l-8.5 8.5a5 5 0 01-7-7L13 4a3.5 3.5 0 015 5l-8.5 8.5a2 2 0 01-3-3L14 7"/></svg>',
    up: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5M5 12l7-7 7 7"/></svg>',
    plus: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#1A1A1A" stroke-width="2.6" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg>',
  };
  const PHOTO = "url('file:///C:/Users/user/Desktop/한비즈-롱폼자동화/소재/sjk01/codex/c18_gukbap_bowl.png')";
  const CARDS = [
    // 01 리뷰 + 사장님 답글
    { id: '리뷰 답글', html: () => `<div class="v2c"><div class="hd">리뷰</div><div class="bd"><div class="row"><div class="av">맛</div><div><b style="font-size:22px">맛집탐**</b><div class="row" style="gap:6px">${stars(1, 18)}<span class="gr" style="font-size:22px">오늘</span></div></div></div><div class="t22" style="margin-top:8px">국물이 너무 짜요. 다시는 안 갑니다.</div><div class="reply"><b>사장님 답글</b>짜게 느끼셨다니 죄송합니다. 다음에 오시면 말씀해 주세요.</div></div></div>` },
    // 02 소식 글
    { id: '소식 글', html: () => `<div class="v2c"><div class="hd"><span style="border-bottom:3px solid #1A1A1A;padding:8px 2px">소식</span><span class="gr" style="font-weight:400">사진</span></div><div class="thumb" style="background-image:${PHOTO}"></div><div class="bd" style="padding-top:8px"><div class="t22" style="font-weight:700">[신메뉴] 얼큰 순대국이 나왔습니다.</div><div class="t22 gr">진한 순대국에 청양고추 다대기를 올려…</div><div class="row" style="margin-top:4px;gap:14px">${ic.heart}${ic.chat}</div></div></div>` },
    // 03 배달앱 메뉴
    { id: '메뉴 설명', html: () => `<div class="v2c"><div class="hd">메뉴</div><div class="bd"><div class="row" style="align-items:flex-start"><div style="flex:none;width:100px;height:100px;border-radius:10px;background:${PHOTO} center/cover"></div><div><b style="font-size:24px">돼지국밥</b> <span class="badge">대표</span><div style="font-size:24px;font-weight:700;margin-top:4px">10,000원</div></div></div><div class="t22" style="margin-top:10px;color:#333">사골을 12시간 고아서 국물이 뽀얗고, 앞다리살이 한 숟갈마다 올라와요.</div></div></div>` },
    // 04 문자
    { id: '단골 문자', html: () => `<div class="v2c" style="background:#F7F8FA"><div class="hd" style="justify-content:center;font-size:22px">010-0000-0000</div><div class="bd"><div class="bub me">사장입니다. 날이 쌀쌀해졌네요. 국밥 생각나실 때 다음 주 평일 점심에 들러 주세요.</div></div></div>` },
    // 05 근무표 시트
    { id: '근무표', html: () => `<div class="v2c"><div class="hd">근무표</div><div class="bd" style="padding:10px 8px"><table><tr><th style="width:30px"></th><th style="width:78px">A</th><th>B</th><th style="width:76px">C</th></tr><tr><td class="rn">1</td><td class="l" style="background:#F1F2F4">이름</td><td style="background:#F1F2F4">월</td><td style="background:#F1F2F4">주 시간</td></tr><tr><td class="rn">2</td><td class="l">민지</td><td>저녁</td><td><b>32.5</b></td></tr><tr><td class="rn">3</td><td class="l">준호</td><td>—</td><td><b>20</b></td></tr><tr><td class="rn">4</td><td class="l">서연</td><td>점심·저녁</td><td><b>34.5</b></td></tr><tr><td class="rn">5</td><td class="l">현우</td><td>저녁</td><td><b>32.5</b></td></tr></table></div></div>` },
    // 06 체크리스트
    { id: '알바 매뉴얼', html: () => `<div class="v2c"><div class="hd">마감 체크리스트</div><div class="bd"><span class="pill" style="background:#FDE3E0;color:#C92A1F">위험한 것 먼저</span><div class="row" style="margin-top:10px;align-items:flex-start"><div class="ck" style="margin-top:3px"></div><div class="t22"><b>가스 잠그기</b> — 주방 뒤쪽 노란 밸브를 옆으로</div></div><div class="row" style="margin-top:8px;align-items:flex-start"><div class="ck" style="margin-top:3px"></div><div class="t22"><b>바닥은 물 뿌리지 않기</b></div></div></div></div>` },
    // 07 채용 공고
    { id: '채용 공고', html: () => `<div class="v2c"><div class="hd">알바 공고</div><div class="bd"><div style="font-size:26px;font-weight:800;line-height:1.3">저녁 알바 구해요 (평일 주 3일)</div><div class="t22 gr" style="margin-top:6px">17:30 ~ 21:00 · 시급 10,500원</div><div class="t22" style="margin-top:8px"><b>밥 줘요.</b> 출근하면 국밥 한 그릇 먹고 시작해요.</div></div><div style="position:absolute;left:16px;right:16px;bottom:14px" class="btn">문자 지원</div></div>` },
    // 08 매출 히트맵
    { id: '매출 분석', html: () => { const rows = [['월', 8, 5, 4], ['화', 7, 2, 5], ['수', 8, 3, 6]]; const col = v => `rgba(46,85,217,${(0.08 + v * 0.07).toFixed(2)})`; return `<div class="v2c"><div class="hd">요일 × 시간</div><div class="bd" style="padding:10px 8px"><table class="heat"><tr><th style="width:44px"></th><th>14시</th><th>15시</th><th>16시</th></tr>${rows.map(r => `<tr><th>${r[0]}</th>${[1, 2, 3].map(i => `<td style="background:${col(r[i])};${r[0] === '화' && i === 2 ? 'outline:3px solid #F2C230;outline-offset:-3px' : ''}">${r[i]}</td>`).join('')}</tr>`).join('')}</table><div class="t22 gr" style="margin-top:10px">평균 손님 수(명)</div></div></div>`; } },
    // 09 원가표 시트
    { id: '메뉴 원가', html: () => `<div class="v2c"><div class="hd">원가율</div><div class="bd" style="padding:10px 8px"><table><tr><th style="width:30px"></th><th style="width:120px">A</th><th>B</th></tr><tr><td class="rn">1</td><td class="l" style="background:#F1F2F4">메뉴</td><td style="background:#F1F2F4">원가율</td></tr><tr><td class="rn">2</td><td class="l">수육(소)</td><td><b>70.0%</b></td></tr><tr><td class="rn">3</td><td class="l">수육(대)</td><td><b>65.0%</b></td></tr><tr><td class="rn">4</td><td class="l">모둠순대</td><td><b>46.0%</b></td></tr><tr><td class="rn">5</td><td class="l">돼지국밥</td><td><b>40.0%</b></td></tr></table></div></div>` },
    // 10 계약서 + 질문
    { id: '계약서', html: () => `<div class="v2c" style="background:#FBFAF6"><div class="doc"><div style="text-align:center;font-size:22px;border-bottom:2px solid #1A1A1A;padding-bottom:6px">식자재 납품 계약서</div><div style="font-family:'UI';font-weight:400;font-size:22px;line-height:1.45;margin-top:8px"><b>제11조</b> 계약 기간은 1년으로 한다. 서면 통지가 없으면 같은 조건으로 1년씩 <b style="background:linear-gradient(transparent 55%,rgba(242,194,48,.85) 55%)">자동 연장</b>된다.</div></div><div style="position:absolute;right:16px;bottom:12px;font-family:'UI';font-size:22px;color:#6B7280">갑 (인)</div></div>` },
  ];
  // AI 대화창 뼈대 — 사이드바(새 채팅 + 이 영상에 나온 질문 제목만) · 위 모델 표시 · 입력창(첨부·보내기)
  function chat(o) {
    o = o || {};
    const titles = o.titles || [];
    const side = o.sidebar === false ? '' : `<div class="sb"><div class="nw">${ic.plus}새 채팅</div><div class="cap">최근</div>${titles.map((t, i) => `<div class="it${i === (o.on || 0) ? ' on' : ''}">${t}</div>`).join('')}</div>`;
    return `${side}<div class="mn"><div class="tp">AI <i></i></div><div class="ms" id="${o.id || 'ms'}"></div><div class="inp"><span>${ic.clip}</span><span class="tx" id="${o.id || 'ms'}_tx">무엇이든 물어보세요</span><span class="snd">${ic.up}</span></div></div>`;
  }
  window.V2 = { cards: CARDS, chat, ic, star, stars, PHOTO };
})();
