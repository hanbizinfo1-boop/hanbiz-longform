// 성제관02 실행자 e3 전용 도우미(공용 lib 를 고치지 않으려고 따로 둠) — 구간 타자·다크 대화창 조각·뼈대 막대
(function () {
  const E3 = window.E3 = {};
  const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
  const css = `
.sk{height:16px;border-radius:8px;background:#2E373E;margin:10px 0}
.sk.te{background:rgba(31,163,154,.38)}
.sk.gr{background:#38424A}
.dk .in.tall{height:auto;min-height:62px;border-radius:30px;padding:16px 28px;align-items:flex-end;line-height:1.5}
.dk .in .tx{flex:1;white-space:normal}
.dk .in .ph{color:#6E777E}
.dk .me .or,.dk .tx .or{color:#FF7A4D;font-weight:700}
.dk .tx .te{color:#43C9BF;font-weight:700}
.dk .or{color:#FF7A4D;font-weight:700}
`;
  const st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
  E3.esc = esc;
  E3.SEND = '<svg viewBox="0 0 24 24" fill="none" stroke="#14191E" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5M5 12l7-7 7 7"/></svg>';
  // 구간 타자: segs=[{t:'글', c:'or'|'te'|'', t0, t1}] — 각 조각을 t0~t1 사이에 고르게 쓴다. '\n' 은 줄바꿈. 반환 {html, done, started}
  E3.typed = (tau, segs, caret = true) => {
    let html = '', done = true, started = false, last = -1;
    segs.forEach((s, i) => {
      const arr = [...s.t];
      const n = tau >= s.t1 ? arr.length : Math.floor(S.clamp((tau - s.t0) / Math.max(0.01, s.t1 - s.t0)) * arr.length);
      if (tau >= s.t0) started = true;
      if (n < arr.length) done = false;
      if (n > 0) last = i;
      if (n <= 0) return;
      const h = esc(arr.slice(0, n).join('')).replace(/\n/g, '<br>');
      html += s.c ? `<span class="${s.c}">${h}</span>` : h;
    });
    if (caret && started && !done) html += '<span class="caret"></span>';
    return { html, done, started };
  };
  // 뼈대 막대(지어낸 글 대신) — widths: 퍼센트 배열
  E3.sk = (widths, cls = '') => widths.map(w => `<div class="sk ${cls}" style="width:${w}%"></div>`).join('');
})();
