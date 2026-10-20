r"""화면 글·연출 반복 검사기 — 10-19 사장님 «쓸데없이 화면채우기용 글자 따라쓰기 이런거 지양 … 차라리 시각적보조 이미지나 그림을 넣던지
… 지금 내가말한거 검수할때 잡아낼 수 있는 장치도 만들어줘 / B안같은 그런 연출 좋은데 이것도 너무 반복되면 안좋으니까».

html_motion 장면(HTML seek(t))을 헤드리스 Chrome 으로 열어 0.25초마다 «화면에 보이는 글»과 «그림»을 모으고, 장면의 말(window.SC 줄·어절 시각)과 맞대 본다.

  py -3.11 tools/screen_text_audit.py tools/scenes/sjk02/html/s*.html [--out 보고.md] [--step 0.25]

검사 (ERROR 가 하나라도 있으면 끝 코드 1)
  T1 말 따라 쓰기   얹은 글(재현 화면 밖)이 앞 20초~뒤 3초 말(앞 장면 말 포함)의 글자를 그대로 옮김 — 5글자 이상 & 80% 이상 같으면 ERROR, 4글자 이상 60% 이상 WARN.
                    숫자·단위(«12시간» «90%»)·3글자 이하 개념어·한 글자 기호(A·B)는 뺀다(부각 대상).
  T2 세 단 글 틀    위 작은 글 + 큰 제목 + 아래 설명처럼 얹은 글 3덩이 이상이 같은 왼쪽 줄에 위아래로 쌓임 — ERROR(«이거 너무 AI말투가» 10-19)
  T3 글자만         얹은 글이 보이는데 그림(사진·이미지·그림 SVG·재현 화면)이 화면의 15% 미만인 시간이 1.5초 이상 — ERROR
  T4 글 많음        한 순간 얹은 글이 40글자 넘음(재현 화면 안 글 제외) — WARN
  T6 같은 글 여러 번 한 화면에 같은 얹은 글이 3개 이상 — WARN(«아침 8시에 삶은 거라» 칩 4개 10-19)
  T5 같은 장치 반복  (여러 장면을 넘기면) 연속 두 장면이 같은 주 장치 — ERROR · 한 장치가 장면의 25% 넘게 — WARN
                    장치는 장면이 window.DEVICES = ['spotlight', …] 로 적거나, 없으면 DOM 으로 짐작(spotlight·chip·bigtype·callout·sticker).

  T7 회색 줄 자리표시 글 없는 납작한 회색 막대 3개 이상(그래프 막대는 data-chart 로 뺀다) — ERROR(절대금지 10-07)
  T8 같은 바탕 반복  연속 두 장면이 같은 바탕 그림 — ERROR · 한 바탕이 장면의 15% 넘게 — WARN(sjk-ref 7장 ① «같은 배경 반복 = AI 자동화 느낌»)

재현 화면(말이 실제로 일어나는 자리의 글 — 앱·대화창·시트·영수증·메모 등)은 «얹은 글»이 아니다:
  선택자 DIEGETIC(아래) 또는 요소에 data-diegetic 을 달면 빠진다. 장면마다 다르면 data-diegetic 으로.
말풍선(.speech, 10-20)도 빠진다 — 가게 주인↔손님이 실제로 말하는 대사(사장님 10-20 «진짜 사장이 손님한테 말하는행위 … 말풍선으로»).
  대사가 아닌 말(해설·요약)을 말풍선에 넣지 않는다. 장면마다 말풍선 수를 «말풍선» 줄로 따로 알린다(검수자가 대사인지 본다).
그림으로 치는 것: <img> · <video> · <canvas> · 배경 그림이 있는 요소(.tex-* 질감·.bg 바탕판은 뺀다) · 도형 4개 이상 든 SVG · 재현 화면 상자.
"""
import argparse
import asyncio
import json
import re
import socket
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import html_motion as HM  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

DIEGETIC = ".app,.dk,.sheet,.thermal,.memo,.rv,.speech,[data-diegetic]"
NOT_PICTURE = ".tex-conc,.tex-wall,.tex-dark,.tex-tile,.bg,[data-texture]"
TEXTURE_RE = r"/t_[^/]*\.(png|jpg)|thermal\.png"          # 질감 파일 이름(바탕판) — 그림으로 치지 않는다

COLLECT_JS = r"""
(async (times, DIE, NOTPIC, TEXSRC) => {
  const TEXRE = new RegExp(TEXSRC);
  const stage = document.getElementById('stage') || document.body;
  const vis = el => { let op = 1, n = el;
    while (n && n.nodeType === 1) { const cs = getComputedStyle(n);
      if (cs.display === 'none' || cs.visibility === 'hidden') return 0;
      op *= parseFloat(cs.opacity); n = n.parentElement; }
    return op; };
  const onScreen = r => r.width > 2 && r.height > 2 && r.right > 0 && r.bottom > 0 && r.left < 1920 && r.top < 1080;
  const clipArea = r => Math.max(0, Math.min(1920, r.right) - Math.max(0, r.left)) * Math.max(0, Math.min(1080, r.bottom) - Math.max(0, r.top));
  const out = [];
  for (const t of times) {
    await seek(t);
    const texts = [], pics = [];
    // 10-19: 부각 큰 글(S.focus → body 의 #__focus)도 얹은 글로 본다 — #stage 밖이라 놓쳤다(s68 «알아보는 집»)
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    const seen = new Set();
    while (walker.nextNode()) {
      const tn = walker.currentNode; const s = tn.textContent.replace(/\s+/g, ' ').trim(); if (!s) continue;
      const el = tn.parentElement; if (!el || seen.has(el)) continue;
      if (el.closest('script,style,title')) continue;
      const op = vis(el); if (op < 0.3) continue;
      const r = el.getBoundingClientRect(); if (!onScreen(r)) continue;
      seen.add(el);
      // 같은 요소의 바로 아래 글 전부(줄바꿈 태그로 나뉜 글을 한 덩이로)
      const own = [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join('').replace(/\s+/g, ' ').trim();
      const cs = getComputedStyle(el);
      texts.push({ s: own || s, x: r.left, y: r.top, w: r.width, h: r.height, fs: parseFloat(cs.fontSize),
                   die: !!el.closest(DIE), op });
    }
    for (const el of stage.querySelectorAll('*')) {
      const tag = el.tagName.toLowerCase();
      let pic = false;
      if (tag === 'img' || tag === 'video' || tag === 'canvas') pic = true;
      else if (tag === 'svg') pic = el.querySelectorAll('path,circle,rect,ellipse,polygon,polyline,line,image').length >= 4 && !el.closest('.chip');
      else { const bi = getComputedStyle(el).backgroundImage; pic = bi && bi.includes('url(') && !el.matches(NOTPIC) && !TEXRE.test(bi); }
      if (!pic && el.matches(DIE)) pic = true;
      if (!pic) continue;
      if (vis(el) < 0.3) continue;
      const r = el.getBoundingClientRect(); if (!onScreen(r)) continue;
      pics.push([Math.max(0, r.left), Math.max(0, r.top), Math.min(1920, r.right), Math.min(1080, r.bottom)]);
    }
    // 회색 줄 자리표시: 글 없는 납작한 회색 막대(높이 6~26px, 폭 40px 이상, 채도 낮음)
    let bars = 0;
    for (const el of stage.querySelectorAll('div,span,i')) {
      if (el.children.length || el.textContent.trim()) continue;
      const r = el.getBoundingClientRect(); if (r.height < 6 || r.height > 26 || r.width < 40 || !onScreen(r)) continue;
      const bg = getComputedStyle(el).backgroundColor.match(/[\d.]+/g); if (!bg) continue;
      const [R, G, B, A = 1] = bg.map(Number); if (A < .5) continue;
      if (Math.max(R, G, B) - Math.min(R, G, B) > 22) continue;          // 색 있는 막대(그래프)는 뺀다
      if (el.closest('[data-chart]')) continue;
      if (vis(el) < 0.3) continue;
      bars++;
    }
    // 화면을 가장 넓게 덮는 바탕 그림
    let bgUrl = null, bgArea = 0;
    for (const el of stage.querySelectorAll('*')) {
      const bi = getComputedStyle(el).backgroundImage; if (!bi || !bi.includes('url(') || vis(el) < 0.3) continue;
      const r = el.getBoundingClientRect(); const a = clipArea(r);
      if (a > bgArea) { bgArea = a; bgUrl = bi.match(/url\("?([^")]+)/)[1].split('/').pop(); }
    }
    // 장치 짐작
    const dev = new Set(window.DEVICES || []);
    if (!window.DEVICES) {
      for (const m of stage.querySelectorAll('svg mask')) { if (vis(m.closest('svg')) > 0.3 && m.closest('svg').querySelector('rect[mask]')) dev.add('spotlight'); }
      if ([...stage.querySelectorAll('.chip')].some(e => vis(e) > 0.3)) dev.add('chip');
      if (texts.some(x => !x.die && x.fs >= 90)) dev.add('bigtype');
      if ([...stage.querySelectorAll('.co,.lead')].some(e => vis(e) > 0.3)) dev.add('callout');
      if ([...stage.querySelectorAll('.stk,.badge')].some(e => vis(e) > 0.3)) dev.add('sticker');
    }
    out.push({ t, texts, pics, dev: [...dev], bars, bg: bgArea > 0.5 * 1920 * 1080 ? bgUrl : null });
  }
  return out;
})
"""


def norm(s):
    return re.sub(r"[^0-9A-Za-z가-힣%○]", "", s)


EXEMPT = re.compile(r"^(?:[0-9][0-9,.]*(?:%|[가-힣]{0,3})|[A-Za-z]|[0-9]+[가-힣]{0,2}[0-9]*[가-힣]{0,2})$")


def lcs_sub(a, b):
    """a 의 글자 중 b 에 연속으로 그대로 들어 있는 가장 긴 조각 길이."""
    best = 0
    prev = [0] * (len(b) + 1)
    for i in range(1, len(a) + 1):
        cur = [0] * (len(b) + 1)
        for j in range(1, len(b) + 1):
            if a[i - 1] == b[j - 1]:
                cur[j] = prev[j - 1] + 1
                best = max(best, cur[j])
        prev = cur
    return best


def union_area(rects):
    """사각형 합집합 넓이(1920×1080 을 20px 격자로 근사)."""
    if not rects:
        return 0.0
    g = 20
    cells = set()
    for x0, y0, x1, y1 in rects:
        for gx in range(int(x0 // g), int((x1 - 1) // g) + 1):
            for gy in range(int(y0 // g), int((y1 - 1) // g) + 1):
                cells.add((gx, gy))
    return len(cells) * g * g / (1920 * 1080)


def _sc(p):
    txt = p.read_text(encoding="utf-8")
    return json.loads(txt[txt.index("{"): txt.rindex("}") + 1])


_ALL = {}


def scene_narration(scene):
    """data/sNN.js 의 window.SC → 이 장면 τ 기준 [(t0, t1, 글)] · pre.
    앞 장면에서 한 말을 다시 적는 것도 따라 쓰기라서, 같은 폴더 모든 장면의 줄을 편 전체 시각(SC.t0 + τ)으로 모아 이 장면 τ 로 옮긴다."""
    d = Path(scene).parent.parent / "data"
    p = d / (Path(scene).stem + ".js")
    if not p.exists():
        return [], 0.0
    sc = _sc(p)
    if d not in _ALL:
        allv = []
        for q in d.glob("*.js"):
            try:
                o = _sc(q)
            except Exception:
                continue
            base = float(o.get("t0", 0))
            allv += [(base + ln["t0"], base + ln["t1"], ln["text"]) for ln in o.get("lines", [])]
        _ALL[d] = sorted(set(allv))
    base = float(sc.get("t0", 0))
    if "t0" not in sc:
        return [(ln["t0"], ln["t1"], ln["text"]) for ln in sc.get("lines", [])], float(sc.get("pre", 0))
    return [(a - base, b - base, s) for a, b, s in _ALL[d]], float(sc.get("pre", 0))


def analyse(scene, samples, step):
    lines, pre = scene_narration(scene)
    found = []
    first = {}
    for smp in samples:
        for x in smp["texts"]:
            if x["die"]:
                continue
            k = norm(x["s"])
            if k and k not in first:
                first[k] = (smp["t"], x)
    # T1 말 따라 쓰기 — 타자로 늘어나는 글은 다 써진 글 하나로 본다(앞부분만 다른 짧은 글은 뺀다)
    keys = list(first)
    for k, (t, x) in first.items():
        if len(k) <= 3 or EXEMPT.match(k):
            continue
        if any(o != k and o.startswith(k) for o in keys):
            continue
        tau = t - pre
        near = norm("".join(s for a, b, s in lines if b >= tau - 20 and a <= tau + 3))
        if not near:
            continue
        m = lcs_sub(k, near)
        r = m / len(k)
        if len(k) >= 5 and r >= 0.8:
            found.append(("ERROR", "T1 말 따라 쓰기", f"{t:.2f}s «{x['s']}» — 말과 {m}/{len(k)}글자 같음"))
        elif len(k) >= 4 and r >= 0.6:
            found.append(("WARN", "T1 말 일부 옮김", f"{t:.2f}s «{x['s']}» — 말과 {m}/{len(k)}글자 같음"))
    # T6 같은 글 여러 번(한 화면에 같은 얹은 글 3개 이상)
    rep = {}
    for smp in samples:
        c = {}
        for x in smp["texts"]:
            if not x["die"] and len(norm(x["s"])) >= 2:
                c[norm(x["s"])] = c.get(norm(x["s"]), 0) + 1
        for k2, n in c.items():
            if n >= 3 and k2 not in rep:
                rep[k2] = (smp["t"], n)
    for k2, (t, n) in rep.items():
        found.append(("WARN", "T6 같은 글 여러 번", f"{t:.2f}s «{k2}» {n}개 동시"))
    # T2 세 단 글 틀
    seen2 = set()
    for smp in samples:
        ov = sorted([x for x in smp["texts"] if not x["die"] and len(norm(x["s"])) >= 1], key=lambda x: x["y"])
        for i in range(len(ov)):
            col = [ov[i]]
            for y in ov[i + 1:]:
                if abs(y["x"] - ov[i]["x"]) <= 40 and y["y"] - (col[-1]["y"] + col[-1]["h"]) <= 90 and y["y"] >= col[-1]["y"] + col[-1]["h"] - 5:
                    col.append(y)
            sizes = {round(c["fs"]) for c in col}
            if len(col) >= 3 and len(sizes) >= 2 and max(sizes) >= 1.8 * min(sizes):
                key = tuple(norm(c["s"]) for c in col)
                if key not in seen2:
                    seen2.add(key)
                    found.append(("ERROR", "T2 세 단 글 틀", f"{smp['t']:.2f}s " + " / ".join(f"«{c['s']}»({round(c['fs'])}px)" for c in col)))
    # T3 글자만 · T4 글 많음
    textonly = 0.0
    t3_at = None
    many = []
    for smp in samples:
        ov = [x for x in smp["texts"] if not x["die"]]
        if not ov:
            continue
        pic = union_area(smp["pics"])
        if pic < 0.15:
            textonly += step
            t3_at = t3_at if t3_at is not None else smp["t"]
        n = sum(len(norm(x["s"])) for x in ov)
        if n > 40:
            many.append(smp["t"])
    if textonly >= 1.5:
        found.append(("ERROR", "T3 글자만", f"{textonly:.1f}초 동안 그림 15% 미만에 얹은 글만(처음 {t3_at:.2f}s)"))
    if many:
        found.append(("WARN", "T4 글 많음", f"{len(many) * step:.1f}초 동안 얹은 글 40글자 넘음(처음 {many[0]:.2f}s)"))
    # T7 회색 줄 자리표시(절대금지 10-07 «이미지 속 화면 글을 회색 줄·블러로 때우지 않는다»)
    nb = max((smp.get("bars", 0) for smp in samples), default=0)
    if nb >= 3:
        t7 = next(smp["t"] for smp in samples if smp.get("bars", 0) == nb)
        found.append(("ERROR", "T7 회색 줄 자리표시", f"{t7:.2f}s 글 없는 회색 막대 {nb}개 — 읽히는 예시 글로"))
    devs = {}
    bgs = {}
    for smp in samples:
        if smp.get("bg"):
            bgs[smp["bg"]] = bgs.get(smp["bg"], 0) + step
    devs["_bg"] = max(bgs, key=bgs.get) if bgs else None
    for smp in samples:
        for d in smp["dev"]:
            devs[d] = devs.get(d, 0) + step
    return found, devs


async def collect(scene, step, port):
    w = HM.Worker(0, Path(scene), 1920, 1080, False, port)
    await w.start()
    try:
        meta = await w.meta()
        dur = float(meta.get("DURATION") or 5)
        times = [round(i * step, 3) for i in range(int(dur / step) + 1)]
        return await w.cdp.eval(COLLECT_JS + f"({json.dumps(times)}, {json.dumps(DIEGETIC)}, {json.dumps(NOT_PICTURE)}, {json.dumps(TEXTURE_RE)})")
    finally:
        await w.close()


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def continues(scene_path):
    """장면이 앞 장면을 설계상 이어 찍는지(window.CONTINUES = 'sNN') — 10-19 s07→s08 · s29→s30 같은 한 숏을 둘로 나눈 곳.
    선언한 쌍만 T5·T8 을 ERROR 대신 «이어 찍기» 메모로 내린다. 선언 없는 반복은 그대로 ERROR."""
    m = re.search(r"window\.CONTINUES\s*=\s*['\"](s\d+)['\"]", Path(scene_path).read_text(encoding="utf-8"))
    return m.group(1) if m else None


def main_dev(devs):
    """장면의 주 장치 = 가장 오래 보인 것(0.5초 이상만)."""
    c = [(v, k) for k, v in devs.items() if not k.startswith("_") and v >= 0.5]
    return max(c)[1] if c else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scenes", nargs="+")
    ap.add_argument("--out")
    ap.add_argument("--step", type=float, default=0.25)
    a = ap.parse_args()
    scenes = sorted({str(Path(s)) for s in a.scenes}, key=lambda p: (len(Path(p).stem), Path(p).stem))
    rows, allf = [], []
    for sc in scenes:
        samples = asyncio.run(collect(sc, a.step, free_port()))
        found, devs = analyse(sc, samples, a.step)
        rows.append((Path(sc).stem, found, devs))
        allf += [(Path(sc).stem, *f) for f in found]
        tag = "ERROR" if any(f[0] == "ERROR" for f in found) else ("WARN" if found else "ok")
        nsp = len(re.findall(r'class="speech', Path(sc).read_text(encoding="utf-8")))
        print(f"{Path(sc).stem}: {tag} · 바탕 {devs.get('_bg') or '-'} · 장치 {', '.join(f'{k} {v:.1f}s' for k, v in sorted(devs.items()) if not k.startswith('_')) or '-'}"
              + (f" · 말풍선 {nsp}(대사인지 눈으로 확인)" if nsp else ""), flush=True)
        for f in found:
            print(f"   {f[0]} {f[1]} — {f[2]}", flush=True)
    CONT = {Path(sc).stem: continues(sc) for sc in scenes}
    # T5 같은 장치 반복
    if len(rows) > 1:
        mains = [(r[0], main_dev(r[2])) for r in rows]
        for (s1, d1), (s2, d2) in zip(mains, mains[1:]):
            if d1 and d1 == d2 and CONT.get(s2) == s1:
                print(f"{s2}: 이어 찍기(설계 선언 CONTINUES={s1}) — 같은 장치 {d1} 허용")
            elif d1 and d1 == d2:
                allf.append((s2, "ERROR", "T5 같은 장치 연속", f"{s1}·{s2} 둘 다 주 장치 {d1}"))
                print(f"{s2}: ERROR T5 같은 장치 연속 — {s1}·{s2} 둘 다 {d1}")
        cnt = {}
        for s, d in mains:
            if d:
                cnt[d] = cnt.get(d, 0) + 1
        for d, n in cnt.items():
            if n > 0.25 * len(mains) and n >= 3:
                allf.append(("전체", "WARN", "T5 장치 쏠림", f"{d} 가 {n}/{len(mains)} 장면의 주 장치"))
                print(f"전체: WARN T5 장치 쏠림 — {d} {n}/{len(mains)}")
    # T8 같은 바탕 반복 — 연속 두 장면이 같은 바탕 그림 ERROR · 한 바탕이 장면의 15% 넘게 WARN(sjk-ref 7장 ①)
    if len(rows) > 1:
        bgl = [(r[0], r[2].get("_bg")) for r in rows]
        for (s1, b1), (s2, b2) in zip(bgl, bgl[1:]):
            if b1 and b1 == b2 and CONT.get(s2) == s1:
                print(f"{s2}: 이어 찍기(설계 선언 CONTINUES={s1}) — 같은 바탕 {b1} 허용")
            elif b1 and b1 == b2:
                allf.append((s2, "ERROR", "T8 같은 바탕 연속", f"{s1}·{s2} 둘 다 {b1}"))
                print(f"{s2}: ERROR T8 같은 바탕 연속 — {s1}·{s2} {b1}")
        cb = {}
        for s_, b in bgl:
            if b:
                cb[b] = cb.get(b, 0) + 1
        for b, n in cb.items():
            if n > 0.15 * len(bgl) and n >= 3:
                allf.append(("전체", "WARN", "T8 바탕 쏠림", f"{b} 가 {n}/{len(bgl)} 장면 바탕"))
                print(f"전체: WARN T8 바탕 쏠림 — {b} {n}/{len(bgl)}")
    ne = sum(1 for f in allf if f[1] == "ERROR")
    nw = sum(1 for f in allf if f[1] == "WARN")
    print(f"\n합계: ERROR {ne} · WARN {nw} · 장면 {len(rows)}")
    if a.out:
        md = ["# 화면 글·연출 반복 검사 (`tools/screen_text_audit.py`)", "", f"ERROR {ne} · WARN {nw} · 장면 {len(rows)}", "",
              "| 장면 | 등급 | 검사 | 내용 |", "|---|---|---|---|"]
        md += [f"| {s} | {lv} | {k} | {d} |" for s, lv, k, d in allf]
        md += ["", "## 장면별 장치(보인 초)", "", "| 장면 | 장치 |", "|---|---|"]
        md += [f"| {s} | {d.get('_bg') or '-'} · {', '.join(f'{k} {v:.1f}' for k, v in sorted(d.items()) if not k.startswith('_')) or '-'} |" for s, _, d in rows]
        Path(a.out).write_text("\n".join(md) + "\n", encoding="utf-8")
    sys.exit(1 if ne else 0)


if __name__ == "__main__":
    main()
