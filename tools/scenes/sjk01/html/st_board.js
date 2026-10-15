// 장면 45·46 공용 — 블렌더 무대 연번(st45 사람 있음 · st46 빈 테이블)과 track.js 로 메뉴판 면·테이블 자리를 잡는다.
// 연번 프레임 k 의 절대 시각 = 641.13 + (k-1)/59.94 (spec t0). 장면 절대 시각 = S.SC.t0 + τ.
window.ST = (function () {
  const FPSV = 60000 / 1001, T0 = 641.13, BASE = '../../../../_tmp/sjk01/blender/';
  const pad = n => String(n).padStart(4, '0');
  const kOf = tau => Math.max(1, Math.round((S.SC.t0 + tau - T0) * FPSV) + 1);
  async function set(img, src) {
    if (img.dataset.src === src) return;
    img.dataset.src = src; img.src = src;
    try { await img.decode(); } catch (e) { }
  }
  // 프레임 번호는 연번 길이를 넘지 않게(끝 프레임 유지)
  const nOf = k => Math.min(window.TRACK.length, k);
  function geo(tau) {
    const k = nOf(kOf(tau)), t = window.TRACK[k - 1], t0 = window.TRACK[0];
    const d = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);
    const g = d(t[1], t[2]) / d(t0[1], t0[2]);          // 카메라가 다가간 정도(두 테이블 사이 거리 비)
    return { k, t, g, cx: t[0][0] + g * ST.BOARD_DX, cy: t[0][1] + g * ST.BOARD_DY };
  }
  return { FPSV, T0, BASE, pad, kOf, nOf, set, geo, BOARD_DX: -7, BOARD_DY: -99 };
})();
