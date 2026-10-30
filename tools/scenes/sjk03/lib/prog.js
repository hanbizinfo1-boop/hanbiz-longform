// 성제관03 진행표 카드 «가격 · 광고 · 단골»(연출표 1장 — 모냐구 위성 편 «4가지» 카드) — 장면 7·9·37·53·67 이 같은 모양을 쓴다.
// 가로 세 칸(칸 = 선 아이콘 + 단어 하나). 칸마다 show(0→1 나타남) · on(0→1 파랑으로 켜짐) 을 τ 로 계산해 넘긴다.
//   const pc = PROG.mount('#stage', {x:360, y:330, w:1200, h:360});   // 카드 바깥 상자(판 좌표)
//   PROG.draw(pc, [{show, on}, {show, on}, {show, on}], frameK)        // frameK: 카드 틀 나타남 0→1
// 칸 상자 좌표는 pc.cells[i] = {x, y, w, h}(판 좌표) — 칸으로 밀고 들어갈 때 카메라 목표로 쓴다.
(function () {
  const ICON = [
    // 가격 — 가격표(구멍 + 끈)
    '<path class="ln w4" d="M30 70 L70 30 L118 30 L118 78 L78 118 Z"/><circle class="ln w4" cx="100" cy="48" r="7"/><path class="ln w4" d="M100 41 C 96 20, 120 14, 132 22"/>',
    // 광고 — 확성기
    '<path class="ln w4" d="M28 62 L28 92 L52 92 L104 122 L104 32 L52 62 Z"/><path class="ln w4" d="M40 92 L50 124 L66 124 L60 96"/><path class="ln w4" d="M118 58 C 128 66, 128 88, 118 96"/><path class="ln w4" d="M128 46 C 146 62, 146 92, 128 108"/>',
    // 단골 — 가게 문 + 돌아오는 화살표
    '<path class="ln w4" d="M36 124 L36 52 L76 30 L116 52 L116 124 Z"/><path class="ln w4" d="M62 124 L62 84 L90 84 L90 124"/><path class="ln w4" d="M132 104 C 150 70, 140 36, 108 24"/><path class="ln w4" d="M112 14 L106 26 L120 32"/>'
  ];
  const WORD = ['가격', '광고', '단골'];
  window.PROG = {
    mount(parent, o) {
      const root = document.createElement('div');
      root.className = 'abs prog';
      root.style.cssText = `left:${o.x}px;top:${o.y}px;width:${o.w}px;height:${o.h}px`;
      const gap = 28, cw = (o.w - gap * 2) / 3;
      const cells = [];
      root.innerHTML = [0, 1, 2].map(i =>
        `<div class="card pcell" style="left:${i * (cw + gap)}px;top:0;width:${cw}px;height:${o.h}px;overflow:hidden">
           <div class="pfill abs" style="left:0;top:0;width:100%;height:100%;background:var(--bl);opacity:0"></div>
           <svg class="abs picon" viewBox="0 0 160 150" style="left:${(cw - 190) / 2}px;top:${o.h * 0.12}px;width:190px;height:178px">${ICON[i]}</svg>
           <div class="abs pword t" style="left:0;width:100%;top:${o.h * 0.64}px;text-align:center;font-size:76px;font-weight:900">${WORD[i]}</div>
           <div class="abs pnum t" style="left:22px;top:16px;font-size:30px;font-weight:800;color:var(--mute)">${i + 1}</div>
         </div>`).join('');
      (typeof parent === 'string' ? document.querySelector(parent) : parent).appendChild(root);
      for (let i = 0; i < 3; i++) cells.push({ x: o.x + i * (cw + gap), y: o.y, w: cw, h: o.h });
      return { root, cells, o };
    },
    // st[i] = {show:0..1, on:0..1} · frame = 카드 틀(빈 칸) 나타남 0..1
    draw(pc, st, frame = 1) {
      const cs = pc.root.querySelectorAll('.pcell');
      cs.forEach((c, i) => {
        const s = st[i] || { show: 0, on: 0 };
        c.style.opacity = (0.35 + 0.65 * frame) * (frame > 0 ? 1 : 0);
        c.style.transform = `translateY(${(16 * (1 - frame)).toFixed(2)}px)`;
        c.querySelector('.pfill').style.opacity = s.on.toFixed(3);
        const ic = c.querySelector('.picon'), wd = c.querySelector('.pword'), nm = c.querySelector('.pnum');
        ic.style.opacity = s.show; wd.style.opacity = s.show;
        ic.style.transform = wd.style.transform = `translateY(${(14 * (1 - s.show)).toFixed(2)}px)`;
        const col = s.on > 0.5 ? '#fff' : 'var(--ln)';
        wd.style.color = col; nm.style.color = s.on > 0.5 ? 'rgba(255,255,255,.8)' : 'var(--mute)';
        ic.querySelectorAll('.ln').forEach(p => { p.style.stroke = col; });
        c.style.borderColor = s.on > 0.5 ? 'var(--bl)' : 'var(--bd)';
      });
    }
  };
})();
