// 오프닝(장면 1·2) 공용 — 블렌더 2.5D 렌더 연번 두 개를 절대 시각으로 그린다.
// A = 거리(0~6.6초, _tmp/sjk01/blender/op_a) · B = 가게 안 계산대(6.0~14.3초, op_b). 6.0~6.6초: 유리문 통과(A 를 확대하며 B 로).
window.OP = (function () {
  const FPS = 60000 / 1001;
  const BASE = '../../../../_tmp/sjk01/blender/';
  const pad = n => String(n).padStart(4, '0');
  async function set(img, src) {
    if (img.dataset.src === src) return;
    img.dataset.src = src; img.src = src;
    try { await img.decode(); } catch (e) { }
  }
  let b = null;
  async function draw(t) {
    const a = document.getElementById('a');
    if (!b) {
      b = document.getElementById('b');
      if (!b) { b = document.createElement('img'); b.id = 'b'; b.className = 'seq'; a.after(b); }
    }
    const ia = Math.min(396, Math.max(1, Math.round(t * FPS) + 1));
    const ib = Math.min(497, Math.max(1, Math.round((t - 6.0) * FPS) + 1));
    const x0 = 6.0, x1 = 6.6;
    const p = Math.min(1, Math.max(0, (t - x0) / (x1 - x0)));
    const e = p * p * (3 - 2 * p);
    if (t < x1) await set(a, BASE + 'op_a/f_' + pad(ia) + '.png');
    if (t >= x0) await set(b, BASE + 'op_b/f_' + pad(ib) + '.png');
    a.style.opacity = t < x1 ? 1 : 0;
    a.style.transformOrigin = '1000px 470px';
    a.style.transform = `scale(${1 + 0.55 * e})`;
    a.style.filter = `brightness(${1 + 0.6 * e})`;
    b.style.opacity = t < x0 ? 0 : e;
    b.style.transform = `scale(${1.08 - 0.08 * e})`;
  }
  return { draw };
})();
