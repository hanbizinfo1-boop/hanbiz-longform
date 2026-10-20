// 성제관02 장면 공용(1편 sjk.js 복사 → 부각 모양·도우미만 2편 것으로) — html_motion 계약(seek(t) · EVENTS · PALETTE · DURATION)을 장면 시각표(SC)와 이어 준다.
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
  // 말풍선(10-20) — 가게 주인↔손님 대사. on 에 감속 확대로 뜨고 off 에 0.15초 사라짐(튕김 없음). 꼬리 쪽이 기준점(.speech.bl 등)
  S.speech = (sel, tau, on, off) => {
    const k = S.ent(tau, on, 0.14), o = off == null ? 1 : 1 - S.P(tau, off, off + 0.15);
    S.css(sel, { opacity: (k * o).toFixed(3), transform: `scale(${(0.86 + 0.14 * k).toFixed(4)})` });
  };
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

  // ── 부각(2편 — 연출설계 3-3 «배경이 탈색(흑백) + 큰 굵은 고딕을 왼쪽 아래 3분의 1 자리에, 주홍 밑판 · 가운데 정렬 금지»)
  // S.focus([{t0, t1, big:'90%', small:'사라지는 쪽'?, color:'or'|'te'|'gr'?}]) — 장면 맨 위에서 한 번. 효과음 big_in 자동.
  // 그 동안 장면 전체가 흑백으로 빠지고 살짝 어두워지며(backdrop-filter grayscale) 왼쪽 아래에 큰 글(Pretendard Black)이
  // 주홍(또는 청록·회색) 밑판 위에 왼쪽에서 밀려 들어온다. 큰 글은 숫자·개념어 몇 글자만(말 따라 쓰기 금지). 한 번 0.9~2.0초 · 장면당 2번까지.
  let FOC = [];
  const FCOL = { or: '#F05A28', te: '#1FA39A', gr: '#E0353B' };   // 10-19 «다 같은 가게는 다른색으로 강조를 제대로» — 회색(#6E767D)이 흑백 바탕에 묻힘 → 선명한 빨강(다 똑같아 사라지는 쪽) + 흰 테두리
  S.focus = list => {
    FOC = list;
    list.forEach((f, i) => S.ev(f.t0, 'big_in', 'focus' + i));
  };
  function focusEl() {
    let o = document.getElementById('__focus');
    if (o) return o;
    o = document.createElement('div'); o.id = '__focus';
    o.style.cssText = 'position:absolute;left:0;top:0;width:' + window.W + 'px;height:' + window.H + 'px;pointer-events:none;z-index:9000;opacity:0';
    o.innerHTML = '<div class="__fw" style="position:absolute;left:120px;top:560px;display:flex;flex-direction:column;align-items:flex-start;gap:14px">' +
      '<div class="__fs" style="font-family:Pre;font-weight:700;font-size:30px;letter-spacing:.16em;color:#fff;text-shadow:0 2px 10px rgba(0,0,0,.55)"></div>' +
      '<div class="__fb" style="font-family:Pre;font-weight:900;letter-spacing:-.02em;line-height:1;color:#fff;padding:18px 34px 22px;border-radius:12px;white-space:nowrap"></div></div>';
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
    o.style.background = `rgba(20,25,30,${0.30 * k})`;
    o.style.backdropFilter = `grayscale(${k.toFixed(3)}) brightness(${(1 - 0.12 * k).toFixed(3)})`;
    const fb = o.querySelector('.__fb'), fs = o.querySelector('.__fs'), fw = o.querySelector('.__fw');
    fb.textContent = f.big; fs.textContent = f.small || '';
    fb.style.background = FCOL[f.color || 'or'] || f.color;
    fb.style.boxShadow = '0 0 0 5px #fff, 0 18px 40px rgba(0,0,0,.45)';
    fb.style.fontSize = (f.size || 190) + 'px';
    const pop = S.EO(S.P(tau, f.t0, f.t0 + 0.14));
    fw.style.opacity = k;
    fw.style.transform = `translateX(${(-60 * (1 - pop)).toFixed(2)}px)`;
    if (f.top) fw.style.top = f.top + 'px'; else fw.style.top = (f.size && f.size < 160 ? 600 : 520) + 'px';
  };

  // 카메라 키(같은 그림 키프레임 강조는 2번까지 — SPEC_V2 8장): keys=[{t,s,x,y}] → 0.32초 EZ 로 다음 키
  S.camState = (tau, keys, d = 0.32) => {
    let prev = keys[0], cur = prev;
    for (let i = 1; i < keys.length; i++) {
      const k = keys[i]; if (tau < k.t) break;
      const p = S.cam(tau, k.t, k.t + (k.d || d));
      cur = { s: S.lerp(prev.s, k.s, p), x: S.lerp(prev.x, k.x, p), y: S.lerp(prev.y, k.y, p) };
      if (p < 1) break; prev = k; cur = k;
    }
    return cur;
  };
  S.camCss = c => `translate(960px,540px) scale(${c.s}) translate(${-c.x}px,${-c.y}px)`;
  // 탈색(«다 똑같은 것» → 회색으로 빠짐): k 0→1
  S.desat = k => `grayscale(${S.clamp(k).toFixed(3)}) brightness(${(1 + 0.06 * S.clamp(k)).toFixed(3)}) contrast(${(1 - 0.12 * S.clamp(k)).toFixed(3)})`;
  // 옆 흐름(트래킹): 사진을 1.25배로 깔고 x 를 from→to 로 고르게(EIO) — 사진 래퍼 transform 문자열
  S.track = (tau, t0, t1, from, to, sc = 1.25) => `scale(${sc}) translateX(${S.lerp(from, to, S.EIO(S.P(tau, t0, t1))).toFixed(2)}px)`;
  // 사진 경로
  S.ph = name => `url("../../../../소재/sjk02/codex/${name}.png")`;

  // 블렌더 프레임(10-19 R1·R3 무대): <img id> 에 _tmp/sjk02/blender/<dir>/f####.png 를 τ 에 맞춰 띄우고 디코드를 기다린다.
  // 프레임 1 = τ −pre (blender/desk.py · bl_common.py 와 같은 시계). 장면 함수는 async 로: S.scene(async τ => { await S.bl('#bl', 's45', τ); … })
  // o = {t0: 프레임 1 의 τ(기본 −pre), nf: 프레임 수, pfx: 파일 앞글자(기본 'f' — parallax.py 는 'f_')}
  S.bl = async (sel, dir, tau, o = {}) => {
    const img = typeof sel === 'string' ? S.$(sel) : sel;
    const t0 = o.t0 === undefined ? -SC.pre : o.t0;
    const nf = o.nf || Math.round((SC.pre + SC.dur + SC.post - (t0 + SC.pre)) * 60000 / 1001) + 1;
    const n = Math.min(nf, Math.max(1, Math.round((tau - t0) * 60000 / 1001) + 1));
    const src = `../../../../_tmp/sjk02/blender/${dir}/${o.pfx || 'f'}${String(n).padStart(4, '0')}.png`;
    if (img.dataset.src !== src) { img.dataset.src = src; img.src = src; try { await img.decode(); } catch (e) { } }
    return n;
  };
  // 블렌더 화면 좌표(proj.js — window.PROJ[프레임][이름] = [x, y, 깊이])
  S.proj = (name, tau) => {
    const P = window.PROJ; if (!P) return null;
    const n = Math.max(1, Math.round((tau + SC.pre) * 60000 / 1001) + 1);
    const row = P[n] || P[Object.keys(P).length];
    return row ? row[name] : null;
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
