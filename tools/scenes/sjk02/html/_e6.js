// e6 실행자 전용 도우미(공용 lib 를 고치지 않으려고 따로 둠) — sjk.js 다음에 불러 쓴다.
(function () {
  const E = window.E = {};
  const $ = s => (typeof s === 'string' ? S.$(s) : s);
  // DOM 만들기(결정적: 한 번만, 장면 시작 때)
  E.mk = (parent, cls, html, css) => {
    const d = document.createElement('div');
    if (cls) d.className = cls;
    d.innerHTML = html || '';
    if (css) d.style.cssText = css;
    $(parent).appendChild(d);
    return d;
  };
  // 등장: opacity 0→1 + 아래서 dy 만큼 올라옴(+ 선택: dx, 시작 크기 s0, 기본 transform base)
  E.in = (el, tau, t0, o = {}) => {
    el = $(el);
    const k = S.ent(tau, t0, o.d || 0.12);
    const dy = o.dy === undefined ? 14 : o.dy, dx = o.dx || 0, s0 = o.s0 === undefined ? 1 : o.s0;
    el.style.opacity = (k * (o.max === undefined ? 1 : o.max)).toFixed(3);
    el.style.transform = `${o.base || ''} translate(${(dx * (1 - k)).toFixed(2)}px,${(dy * (1 - k)).toFixed(2)}px) scale(${(s0 + (1 - s0) * k).toFixed(4)})`;
    return k;
  };
  // 사라짐: t0 에서 d 초 동안 1→0 (이미 보이던 것)
  E.out = (el, tau, t0, d = 0.25) => {
    el = $(el);
    const k = S.EO(S.P(tau, t0, t0 + d));
    return k;
  };
  // 왼→오 그려지는 가림(손글씨·밑줄)
  E.wipe = (el, tau, t0, d = 0.4) => {
    el = $(el);
    const k = S.EO(S.P(tau, t0, t0 + d));
    el.style.clipPath = `inset(-20px ${((1 - k) * 100).toFixed(2)}% -20px -20px)`;
    el.style.opacity = k > 0 ? 1 : 0;
    return k;
  };
  // SVG 선 그리기
  E.stroke = (pathEl, tau, t0, d = 0.4) => {
    pathEl = $(pathEl);
    const len = pathEl.getTotalLength ? pathEl.getTotalLength() : 1000;
    const k = S.EO(S.P(tau, t0, t0 + d));
    pathEl.style.strokeDasharray = len;
    pathEl.style.strokeDashoffset = (len * (1 - k)).toFixed(2);
    pathEl.style.opacity = k > 0 ? 1 : 0;
    return k;
  };
  // 천천히 옆으로(고르게): a→b
  E.pan = (tau, t0, t1, a, b) => S.lerp(a, b, S.EIO(S.P(tau, t0, t1)));
  E.lin = (tau, t0, t1, a, b) => S.lerp(a, b, S.P(tau, t0, t1));
  // 위치
  E.at = (el, x, y, w, h) => { el = $(el); el.style.left = x + 'px'; el.style.top = y + 'px'; if (w) el.style.width = w + 'px'; if (h) el.style.height = h + 'px'; return el; };
  // SVG 만들기
  E.svg = (parent, w, h, inner, css) => {
    const s = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    s.setAttribute('viewBox', `0 0 ${w} ${h}`); s.setAttribute('width', w); s.setAttribute('height', h);
    s.style.cssText = 'position:absolute;left:0;top:0;overflow:visible;' + (css || '');
    s.innerHTML = inner;
    $(parent).appendChild(s);
    return s;
  };
})();
