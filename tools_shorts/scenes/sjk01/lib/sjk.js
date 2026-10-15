// 성제관01 장면 공용 — html_motion 계약(seek(t) · EVENTS · PALETTE · DURATION)을 장면 시각표(SC)와 이어 준다.
// 장면 파일은: <script src="../data/sNN.js"> (window.SC) → <script src="../lib/sjk.js"> → 자기 스크립트에서 S.scene(τ => {...}) 만 쓴다.
// τ = 장면 시작(첫 말 −0.25초) 기준 초. 앞뒤 전환 여유(pre/post) 동안 τ 는 음수·dur 초과가 된다 — 그때도 그림은 그대로 그린다.
(function () {
  const SC = window.SC || { pre: 0, dur: 5, post: 0, lines: [] };
  window.W = 1920; window.H = 1080; window.FPS = 59.94;
  window.DURATION = +(SC.pre + SC.dur + SC.post).toFixed(4);
  window.EVENTS = [];
  window.BOXES = [{ kind: 'keepout', id: 'subtitle', x: 300, y: 968, w: 1320, h: 100 }];

  // 베지어(ae-replacement.md 대응표): EO = 빠르게 들어와 감속(튕김 0), EZ = 카메라
  function bez(x1, y1, x2, y2) {
    const cx = 3 * x1, bx = 3 * (x2 - x1) - cx, ax = 1 - cx - bx, cy = 3 * y1, by = 3 * (y2 - y1) - cy, ay = 1 - cy - by;
    const sx = t => ((ax * t + bx) * t + cx) * t, sy = t => ((ay * t + by) * t + cy) * t, dx = t => (3 * ax * t + 2 * bx) * t + cx;
    return x => {
      if (x <= 0) return 0; if (x >= 1) return 1;
      let t = x;
      for (let i = 0; i < 8; i++) { const d = dx(t); if (Math.abs(d) < 1e-6) break; t -= (sx(t) - x) / d; }
      t = Math.min(1, Math.max(0, t));
      return sy(t);
    };
  }
  const S = window.S = {};
  S.SC = SC;
  S.EO = bez(0.001, 0, 0.15, 1);
  S.EZ = bez(0.72, 0, 0.28, 1);
  S.EIO = bez(0.45, 0, 0.25, 1);
  S.clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
  S.lerp = (a, b, k) => a + (b - a) * k;
  S.P = (t, a, b) => S.clamp((t - a) / (b - a));
  // 등장 진행률(기본 0.12초 ≈ 7프레임, 감속)
  S.ent = (t, a, d = 0.12) => S.EO(S.P(t, a, a + d));
  S.cam = (t, a, b) => S.EZ(S.P(t, a, b));
  S.$ = sel => document.querySelector(sel);
  S.css = (el, o) => { if (typeof el === 'string') el = S.$(el); for (const k in o) el.style[k] = o[k]; return el; };
  S.fmt = n => Math.round(n).toLocaleString('en-US');

  // 말 시각: 장면 안 줄들에서 글을 찾아 그 첫 글자가 나오는 τ(초). 글자 시각은 어절 안에서 고르게 나눔.
  const chars = [];
  (SC.lines || []).forEach((ln, li) => {
    (ln.words || []).forEach(w => {
      const cs = [...w.w.replace(/[^\p{L}\p{N}%○]/gu, '')];
      cs.forEach((c, k) => chars.push({ c, t: w.t0 + (w.t1 - w.t0) * k / Math.max(1, cs.length), li }));
    });
  });
  const flat = chars.map(x => x.c).join('');
  // at('15분') — 첫 번째, at('15분', 1) — 두 번째. end:true 면 그 글의 마지막 글자 끝 쪽(다음 글자 시각)
  S.at = (txt, nth = 0, end = false) => {
    const q = txt.replace(/[^\p{L}\p{N}%○]/gu, '');
    let p = -1;
    for (let k = 0; k <= nth; k++) { p = flat.indexOf(q, p + 1); if (p < 0) break; }
    if (p < 0) { console.warn('말 못 찾음: ' + txt); return 0; }
    if (end) { const e = p + [...q].length; return e < chars.length ? chars[e].t : SC.dur; }
    return chars[p].t;
  };
  S.line = i => SC.lines[i];              // {text, t0, t1, words}
  S.lineT = i => SC.lines[Math.min(i, SC.lines.length - 1)].t0;

  // 효과음 계기: τ 기준으로 적으면 html_motion 시각(pre 더함)으로 바꿔 넣는다
  S.ev = (tau, role, id) => window.EVENTS.push({ t: +(tau + SC.pre).toFixed(3), role, id });

  // 타자: 글을 n 글자까지
  S.type = (el, text, tau, t0, cps = 16, caret = true) => {
    if (typeof el === 'string') el = S.$(el);
    const arr = [...text];
    const n = Math.floor(S.clamp((tau - t0) * cps, 0, arr.length));
    const done = n >= arr.length;
    el.innerHTML = esc(arr.slice(0, n).join('')).replace(/\n/g, '<br>') + (caret && tau >= t0 && !done ? '<span class="caret"></span>' : '');
    return done;
  };
  // 글자를 시간에 맞춰 하나씩 보이게(말 시각 따라 쓰기 아님 — 화면 글은 적게)
  function esc(s) { return s.replace(/&/g, '&amp;').replace(/</g, '&lt;'); }
  S.esc = esc;

  // 숫자 올라가기
  S.count = (tau, t0, t1, from, to) => S.lerp(from, to, S.EO(S.P(tau, t0, t1)));

  // 사진 속 화면(초록 화면 네 모서리)에 요소를 원근으로 맞춤 — quad: [[x,y]×4] 왼위·오위·오아래·왼아래 (판 좌표)
  S.fitQuad = (el, w, h, q) => {
    const src = [[0, 0], [w, 0], [w, h], [0, h]];
    const A = [], B = [];
    for (let i = 0; i < 4; i++) {
      const [x, y] = src[i], [u, v] = q[i];
      A.push([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.push(u);
      A.push([0, 0, 0, x, y, 1, -v * x, -v * y]); B.push(v);
    }
    const s = solve(A, B);
    const m = [s[0], s[3], 0, s[6], s[1], s[4], 0, s[7], 0, 0, 1, 0, s[2], s[5], 0, 1];
    el.style.transformOrigin = '0 0';
    el.style.transform = 'matrix3d(' + m.map(v => v.toFixed(9)).join(',') + ')';
  };
  function solve(A, b) {
    const n = b.length, M = A.map((r, i) => [...r, b[i]]);
    for (let c = 0; c < n; c++) {
      let p = c; for (let r = c + 1; r < n; r++) if (Math.abs(M[r][c]) > Math.abs(M[p][c])) p = r;
      [M[c], M[p]] = [M[p], M[c]];
      for (let r = 0; r < n; r++) if (r !== c) { const f = M[r][c] / M[c][c]; for (let k = c; k <= n; k++) M[r][k] -= f * M[c][k]; }
    }
    return M.map((r, i) => r[n] / r[i]);
  }

  // ── 부각(10-15 사장님 «시간이 부각 이되게 가운데서 배경 살짝 불투명도처리하면서»)
  // S.focus([{t0, t1, big:'23:50', small:'밤 11시 50분'?, color:'#F2C230'?}]) — 장면 맨 위에서 한 번 적는다.
  // 그 동안 장면 전체가 흐려지고 어두워지며(backdrop-filter) 가운데에 큰 글(Serif 900)이 튀어 오른다. 효과음 big_in 자동.
  // 큰 글은 시간·숫자·개념어 몇 글자만(말 따라 쓰기 금지 그대로). 한 번 0.9~2.5초.
  let FOC = [];
  S.focus = list => {
    FOC = list;
    list.forEach((f, i) => S.ev(f.t0, 'big_in', 'focus' + i));
  };
  function focusEl() {
    let o = document.getElementById('__focus');
    if (o) return o;
    o = document.createElement('div'); o.id = '__focus';
    o.style.cssText = 'position:absolute;left:0;top:0;width:' + window.W + 'px;height:' + window.H + 'px;pointer-events:none;z-index:9000;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;opacity:0';
    o.innerHTML = '<div class="__fs mono" style="font-size:34px;color:#ECE8E0;letter-spacing:.08em;text-shadow:0 2px 12px rgba(0,0,0,.6)"></div>' +
      '<div class="__fb serif" style="font-size:210px;line-height:1;color:#ECE8E0;text-shadow:0 8px 40px rgba(0,0,0,.55)"></div>';
    document.body.appendChild(o);
    return o;
  }
  S.focusDraw = tau => {
    if (!FOC.length) return;
    const o = focusEl();
    const f = FOC.find(f => tau >= f.t0 - 0.2 && tau <= f.t1 + 0.25);
    if (!f) { o.style.opacity = 0; o.style.backdropFilter = 'none'; return; }
    const kin = S.EO(S.P(tau, f.t0 - 0.12, f.t0 + 0.06)), kout = 1 - S.P(tau, f.t1, f.t1 + 0.2);
    const k = Math.min(kin, kout);
    o.style.opacity = 1;
    o.style.background = `rgba(10,12,16,${0.42 * k})`;
    o.style.backdropFilter = `blur(${(9 * k).toFixed(2)}px)`;
    const fb = o.querySelector('.__fb'), fs = o.querySelector('.__fs');
    fb.textContent = f.big; fs.textContent = f.small || '';
    fb.style.color = f.color || '#ECE8E0';
    fb.style.fontSize = (f.size || 210) + 'px';
    const pop = S.EO(S.P(tau, f.t0, f.t0 + 0.14));
    fb.style.opacity = k; fs.style.opacity = k;
    fb.style.transform = `scale(${(1.35 - 0.35 * pop).toFixed(4)})`;
  };

  // 장면 등록
  S.scene = fn => {
    let first = true;
    window.seek = async t => {
      if (first) { first = false; if (S.init) await S.init(); }
      await fn(t - SC.pre);
      S.focusDraw(t - SC.pre);
    };
  };
})();
