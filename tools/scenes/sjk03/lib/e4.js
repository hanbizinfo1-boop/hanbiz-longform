// 성제관03 장면 도우미(2편 e4.js 복사, 반짝 테두리 색만 파랑) — sjk.js 다음에 읽는다.
(function () {
  const E = window.E = {};
  const $ = el => (typeof el === 'string' ? document.querySelector(el) : el);
  // 등장: 투명 0→1 + 살짝 올라오며 커짐(감속). o: dy dx sc base d
  E.pop = (sel, tau, t0, o = {}) => {
    const el = $(sel), k = S.ent(tau, t0, o.d || 0.12);
    el.style.opacity = k;
    const dy = (o.dy === undefined ? 14 : o.dy) * (1 - k), dx = (o.dx || 0) * (1 - k);
    const sc = 1 - (o.sc === undefined ? 0.05 : o.sc) * (1 - k);
    el.style.transform = (o.base || '') + ` translate(${dx.toFixed(2)}px,${dy.toFixed(2)}px) scale(${sc.toFixed(4)})`;
    return k;
  };
  // 왼→오 닦아 보이기(글씨 써지는 마스크)
  E.wipe = (sel, tau, t0, d) => {
    const el = $(sel), k = S.EO(S.P(tau, t0, t0 + d));
    el.style.opacity = tau >= t0 ? 1 : 0;
    el.style.clipPath = `inset(-14px ${((1 - k) * 100).toFixed(2)}% -14px -6px)`;
    return k;
  };
  // 위→아래 닦아 보이기
  E.wipeY = (sel, tau, t0, d) => {
    const el = $(sel), k = S.EO(S.P(tau, t0, t0 + d));
    el.style.opacity = tau >= t0 ? 1 : 0;
    el.style.clipPath = `inset(0 0 ${((1 - k) * 100).toFixed(2)}% 0)`;
    return k;
  };
  // 글 + 토큰 {cls|글자} 를 n 글자까지만 그린다. 반환 true = 끝까지
  E.parse = s => { const out = []; let last = 0, m; const re = /\{(\w+)\|([^}]*)\}/g; while ((m = re.exec(s))) { if (m.index > last) out.push({ c: '', t: s.slice(last, m.index) }); out.push({ c: m[1], t: m[2] }); last = re.lastIndex; } if (last < s.length) out.push({ c: '', t: s.slice(last) }); return out; };
  E.typed = (el, str, n, caret = true) => {
    el = $(el); const segs = E.parse(str); let left = n, html = '', total = 0;
    segs.forEach(s => { total += [...s.t].length; });
    segs.forEach(s => {
      const a = [...s.t]; const take = Math.max(0, Math.min(a.length, left)); left -= take;
      if (take > 0) { const tx = S.esc(a.slice(0, take).join('')).replace(/\n/g, '<br>'); html += s.c ? `<span class="${s.c}">${tx}</span>` : tx; }
    });
    const done = n >= total;
    el.innerHTML = html + (caret && n > 0 && !done ? '<span class="caret"></span>' : '');
    return done;
  };
  E.total = str => E.parse(str).reduce((a, s) => a + [...s.t].length, 0);
  // 줄 타자: t0~t1 사이에 글 전체(균등)
  E.line = (el, str, tau, t0, t1, caret = true) => {
    const tot = E.total(str);
    const n = Math.floor(S.clamp((tau - t0) / Math.max(0.05, t1 - t0)) * tot + 1e-6);
    return E.typed(el, str, tau < t0 ? 0 : n, caret);
  };
  // SVG path 그리기(마스크 아님 — dash). path 의 길이는 기하라 글꼴과 무관
  E.stroke = (p, tau, t0, d) => {
    p = $(p); if (!p._len) { p._len = p.getTotalLength(); p.style.strokeDasharray = p._len; }
    const k = S.EO(S.P(tau, t0, t0 + d));
    p.style.strokeDashoffset = p._len * (1 - k); p.style.opacity = tau >= t0 ? 1 : 0; return k;
  };
  // 아주 느린 바탕 흐름(트래킹·1.00→1.04)
  E.drift = (tau, s0 = 1, s1 = 1.04) => S.lerp(s0, s1, S.P(tau, 0, S.SC.dur));
  // 색: 회색으로 빠짐
  E.gray = (sel, k) => { $(sel).style.filter = S.desat(k); };
  // 반짝 테두리(주홍) 0→1→0.4
  E.ring = (sel, tau, t0, color = '31,95,209') => {
    const k = S.EO(S.P(tau, t0, t0 + 0.2)); $(sel).style.boxShadow = `0 0 0 ${(k * 7).toFixed(1)}px rgba(${color},${(0.85 * k).toFixed(2)}),0 26px 54px rgba(20,25,30,.30)`;
    return k;
  };
})();
