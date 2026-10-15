# -*- coding: utf-8 -*-
r"""HTML 장면(seek(t) 시간 함수) → 헤드리스 Chrome 프레임 캡처(CDP 직접) → 서브프레임 모션블러 → ffmpeg.

[10-13 쇼츠광고 저장소에서 옮김 — AE 자리의 기본 엔진(references/ae-replacement.md). 강의 «Claude 가 HTML 한 장에 seek(t) 로 모든 스타일을 계산 → 브라우저 캡처 → ffmpeg» 를 우리 도구로 옮긴 시제품.
 Playwright·Remotion 없이 Chrome(config.CHROME) + aiohttp WebSocket 만 쓴다. 패키지 설치 없음.]

    python html_motion.py 장면.html [--alpha] [--sub 4] [--workers 2] [--out 폴더] [--name 이름] [--frames 0:30] [--no-sheet] [--box-step 0.1] [--무시]

장면 계약 (HTML 이 노출):
    window.W, H, FPS, DURATION       크기(1920x1080)·fps(59.94)·길이(초)
    async function seek(t)           t 초의 상태를 그린다. CSS transition·animation·setTimeout·requestAnimationFrame·Math.random·Date.now 금지.
                                      글자 크기 측정이 필요하면 seek 첫 호출 안에서(글꼴이 이미 로드된 뒤).
    window.EVENTS = [{t, role, id}]  (선택) 효과음 계기. role 이 «_in» 으로 끝나면 «새 요소 등장» — 앞 새 요소와 0.6초 미만이면 WARN(인지 텀, SKILL 3장 «인지할 텀 0.6초»)
    window.BOXES = [...]             (선택) 손으로 적는 박스 — 요소 {id, t0, t1, x, y, w, h[, group, bleed]} · 금지 구역 {kind:'keepout', id, x, y, w, h[, t0, t1]}
                                      t0/t1 을 안 적으면 장면 전체. 같은 group 끼리는 겹쳐도 되고(예: 판 위의 글), bleed:true 면 화면 가장자리 여유 검사를 뺀다(풀블리드 판).
    <요소 data-box="id" [data-box-group="g"] [data-box-bleed]>   (선택) BOXES 를 안 적어도 된다 — 렌더러가 장면을 0.1초 간격(+EVENTS 직후)으로
                                      seek 해 보이는 요소(자기·조상 불투명도 곱 >= 0.85, display/visibility 정상)의 getBoundingClientRect 를 모은다.
                                      («읽을 수 있게 자리 잡은 상태»만 센다 — 페이드 중간의 겹침은 연출이라 세지 않는다.) --box-step 으로 간격 변경.
    window.PALETTE = ['#ffffff', ...] (선택) 이 장면에 쓴 색 목록 — 4개 이상이면 WARN(3색, SKILL 3장 «비교 장면은 쪽마다 색 하나, 그 외 3색»). 안 적으면 «검사 못 함» WARN.

렌더 전 점검(CLAUDE.md «렌더 전 점검기»): 첫 프레임 전에 위 셋을 읽어 rule_check.report 형식으로 <out>/<name>_점검.txt 를 쓴다.
    ERROR(요소끼리 겹침 · 금지 구역 침범 · 화면 가장자리 15px 안쪽 — 기존 카드 스크립트의 check_layout 과 같은 규칙, 시간이 겹치는 것끼리만)가 있으면
    렌더하지 않고 멈춘다(종료 코드 1). --무시 로만 통과하고, 그때 위반 목록을 점검 파일에 «--무시 로 통과한 위반» 으로 적는다.
렌더 후: <name>_events.json. 효과음 붙일 때는 events_to_sfx_plan() 으로 «역할 → 시각 목록» 을 얻어 edit_plan 의 sfx 에 넣는다.

글꼴: 도구가 @font-face 를 주입한다(file:///, 장면은 이름만 쓴다).
    font-family: "HM Pretendard"  (weight 700 — config.FONTS['pretendard_bold'])
    font-family: "HM NotoSansKR"  (가변 weight 100~900 — config.FONTS['noto_sans_kr'])
    소재/fonts/ 사본(있을 때만 주입): "HM Pretendard" 는 weight 100~900 9종(Thin~Black) · "HM PretendardVar"(가변 45~930) ·
    "HM SUIT"(가변 100~900) · "HM BlackHanSans"(400) · "HM DoHyeon"(400) · "HM Paperlogy"(100~900 9종) ·
    "HM GmarketSans"(300·500·700) · "HM Archivo"(가변 100~900, font-stretch 62~125%) · "HM Mono"(JetBrains Mono 가변 100~800)
    페이지가 열린 뒤 document.fonts.load + document.fonts.ready 를 기다리고 나서 첫 seek.

프레임 시각: t = n·FPS_DEN/FPS_NUM (59.94fps 면 n·1001/60000). 모션블러: 한 프레임을 N 개 서브프레임(셔터 180°, 프레임 중심)으로 찍어
    premultiplied 알파로 평균(numpy) — 알파 가장자리가 번지지 않는다.

출력: <out>/<name>.mov (--alpha: ProRes 4444 yuva444p10le) 또는 <name>.mp4(H.264),
      <name>_preview.mp4 (검정 바탕 합성), <name>_sheet.jpg (0.25초 간격 접촉 시트).
"""
import argparse
import asyncio
import base64
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import aiohttp
import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import config as C  # noqa: E402
import rule_check as RC  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

def _fps_ratio(fps):
    """config.FPS → (분자, 분모). 59.94 → 60000/1001 · 29.97 → 30000/1001 · 30 → 30/1."""
    n = round(fps * 1001)
    if abs(n / 1001 - fps) < 0.01 and abs(fps - round(fps)) > 1e-6:      # NTSC 계열(소수 fps)
        return round(fps) * 1000, 1001
    return round(fps), 1


FPS_NUM, FPS_DEN = _fps_ratio(C.FPS)
FRAME_DT = FPS_DEN / FPS_NUM
GAP_MIN = 0.6              # 새 요소 사이 인지 텀(초) — SKILL 3장
PALETTE_MAX = 3            # 한 장면 색 수 — SKILL 3장 (바탕·글·강조 하나)
EDGE = 15                  # 화면 가장자리 여유(px)
MIN_OPACITY = 0.85         # data-box 수집 때 «보이는 것»으로 치는 불투명도
FONT_FACES = [("HM Pretendard", "pretendard_bold", "700"), ("HM NotoSansKR", "noto_sans_kr", "100 900"),
              # 소재/fonts/ 사본 — 같은 family 에 weight 만 늘린다(700 은 위 항목 그대로라 기존 장면 렌더가 같다)
              ("HM Pretendard", "pretendard_thin", "100"), ("HM Pretendard", "pretendard_extralight", "200"),
              ("HM Pretendard", "pretendard_light", "300"), ("HM Pretendard", "pretendard_regular", "400"),
              ("HM Pretendard", "pretendard_medium", "500"), ("HM Pretendard", "pretendard_semibold", "600"),
              ("HM Pretendard", "pretendard_extrabold", "800"), ("HM Pretendard", "pretendard_black", "900"),
              ("HM PretendardVar", "pretendard_var", "45 930"), ("HM SUIT", "suit_var", "100 900"),
              ("HM BlackHanSans", "black_han_sans", "400"), ("HM DoHyeon", "do_hyeon", "400"),
              ("HM Paperlogy", "paperlogy_regular", "400"), ("HM Paperlogy", "paperlogy_bold", "700"),
              ("HM Paperlogy", "paperlogy_extrabold", "800"), ("HM Paperlogy", "paperlogy_black", "900"),
              ("HM GmarketSans", "gmarket_sans_light", "300"), ("HM GmarketSans", "gmarket_sans_medium", "500"),
              ("HM GmarketSans", "gmarket_sans_bold", "700"),
              ("HM Archivo", "archivo_var", "100 900"), ("HM Mono", "mono", "100 800")]


def _file_url(p):
    return Path(p).resolve().as_uri()


def font_css():
    out = []
    for fam, key, wt in FONT_FACES:
        p = C.FONTS.get(key)
        if p and Path(p).exists():
            st = ";font-stretch:62% 125%" if key == "archivo_var" else ""
            out.append(f'@font-face{{font-family:"{fam}";src:url("{_file_url(p)}");font-weight:{wt};font-style:normal{st}}}')
    return "\n".join(out)


INJECT_JS = """
(() => {
  const css = %s;
  const add = () => { const s = document.createElement('style'); s.id = '__hm_fonts'; s.textContent = css; (document.head || document.documentElement).appendChild(s); };
  if (document.head) add(); else document.addEventListener('DOMContentLoaded', add);
})();
"""


class Cdp:
    def __init__(self, ws):
        self.ws, self.n = ws, 0

    async def call(self, method, **params):
        self.n += 1
        mid = self.n
        await self.ws.send_json({"id": mid, "method": method, "params": params})
        while True:
            msg = await self.ws.receive()
            if msg.type != aiohttp.WSMsgType.TEXT:
                raise RuntimeError(f"CDP 연결 끊김: {msg.type}")
            d = json.loads(msg.data)
            if d.get("id") == mid:
                if "error" in d:
                    raise RuntimeError(f"CDP {method}: {d['error']}")
                return d.get("result", {})

    async def eval(self, expr, await_promise=True):
        r = await self.call("Runtime.evaluate", expression=expr, awaitPromise=await_promise, returnByValue=True)
        if "exceptionDetails" in r:
            ex = r["exceptionDetails"]
            raise RuntimeError("장면 JS 오류: " + str(ex.get("exception", {}).get("description") or ex.get("text")))
        return r.get("result", {}).get("value")


class Worker:
    """Chrome 한 개 + 페이지 한 장."""

    def __init__(self, idx, scene, W, H, alpha, port):
        self.idx, self.scene, self.W, self.H, self.alpha, self.port = idx, scene, W, H, alpha, port
        self.proc = None
        self.session = None
        self.cdp = None
        self.profile = C.WORK / "chrome-hm" / f"p{port}"

    async def start(self):
        self.profile.mkdir(parents=True, exist_ok=True)
        args = [str(C.CHROME), "--headless=new", f"--remote-debugging-port={self.port}", f"--user-data-dir={self.profile}",
                f"--window-size={self.W},{self.H}", "--force-device-scale-factor=1", "--hide-scrollbars", "--allow-file-access-from-files",
                "--no-first-run", "--no-default-browser-check", "--disable-background-timer-throttling",
                "--disable-renderer-backgrounding", "--disable-backgrounding-occluded-windows", "--mute-audio", "about:blank"]
        self.proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        ws_url = None
        for _ in range(100):
            try:
                tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{self.port}/json", timeout=1).read())
                pages = [t for t in tabs if t.get("type") == "page"]
                if pages:
                    ws_url = pages[0]["webSocketDebuggerUrl"]
                    break
            except Exception:
                pass
            await asyncio.sleep(0.2)
        if not ws_url:
            raise RuntimeError("Chrome 디버깅 포트에 연결하지 못했다")
        self.session = aiohttp.ClientSession()
        ws = await self.session.ws_connect(ws_url, max_msg_size=0)
        self.cdp = Cdp(ws)
        c = self.cdp
        await c.call("Page.enable")
        await c.call("Emulation.setDeviceMetricsOverride", width=self.W, height=self.H, deviceScaleFactor=1, mobile=False)
        if self.alpha:
            await c.call("Emulation.setDefaultBackgroundColorOverride", color={"r": 0, "g": 0, "b": 0, "a": 0})
        await c.call("Page.addScriptToEvaluateOnNewDocument", source=INJECT_JS % json.dumps(font_css()))
        await c.call("Page.navigate", url=_file_url(self.scene))
        for _ in range(150):
            ok = await c.eval("typeof seek === 'function' && document.readyState === 'complete'", False)
            if ok:
                break
            await asyncio.sleep(0.1)
        else:
            raise RuntimeError("장면에 seek() 가 없거나 로드가 끝나지 않았다")
        loads = json.dumps([f"{wt.split()[0]} 40px \"{fam}\"" for fam, key, wt in FONT_FACES if C.FONTS.get(key) and Path(C.FONTS[key]).exists()] + ['900 40px "HM NotoSansKR"'], ensure_ascii=False)
        await c.eval("(async()=>{for(const f of " + loads + "){try{await document.fonts.load(f,'한비즈가나다')}catch(e){}} await document.fonts.ready; return true})()")

    async def meta(self):
        return await self.cdp.eval("({W:window.W,H:window.H,FPS:window.FPS,DURATION:window.DURATION,EVENTS:window.EVENTS||null,BOXES:window.BOXES||null,PALETTE:window.PALETTE||null,"
                                   "fonts:[...document.fonts].filter(f=>f.status==='loaded').map(f=>f.family)})")

    async def collect_boxes(self, times):
        """data-box 요소를 times 각 시각에 seek 해서 보이는 것의 getBoundingClientRect 를 모은다(화면은 안 찍는다)."""
        js = ("(async (times, minop) => { const out = [];"
              "for (const t of times) { await seek(t);"
              "for (const el of document.querySelectorAll('[data-box]')) {"
              "let op = 1, n = el, hidden = false;"
              "while (n && n.nodeType === 1) { const cs = getComputedStyle(n);"
              "if (cs.display === 'none' || cs.visibility === 'hidden') { hidden = true; break; }"
              "op *= parseFloat(cs.opacity); n = n.parentElement; }"
              "if (hidden || op < minop) continue;"
              "const r = el.getBoundingClientRect(); if (r.width < 1 || r.height < 1) continue;"
              "out.push({t, id: el.dataset.box, x: r.x, y: r.y, w: r.width, h: r.height,"
              "group: el.dataset.boxGroup || null, bleed: el.dataset.boxBleed !== undefined}); } }"
              f"return out; }})({json.dumps(times)}, {MIN_OPACITY})")
        return await self.cdp.eval(js)

    async def grab(self, t):
        await self.cdp.eval(f"seek({t!r})")
        r = await self.cdp.call("Page.captureScreenshot", format="png", fromSurface=True, captureBeyondViewport=False, optimizeForSpeed=True)
        buf = np.frombuffer(base64.b64decode(r["data"]), np.uint8)
        im = cv2.imdecode(buf, cv2.IMREAD_UNCHANGED)
        if im.ndim == 3 and im.shape[2] == 3:
            im = cv2.cvtColor(im, cv2.COLOR_BGR2BGRA)
            im[..., 3] = 255
        return cv2.cvtColor(im, cv2.COLOR_BGRA2RGBA)

    async def frame(self, n, sub, dur):
        """n 번째 프레임 = 서브프레임 sub 장의 premultiplied 평균 → RGBA uint8."""
        t0 = n * FRAME_DT
        if sub <= 1:
            return await self.grab(min(max(t0, 0), dur))
        ims = []
        for k in range(sub):
            t = t0 + ((k + 0.5) / sub - 0.5) * 0.5 * FRAME_DT        # 셔터 180°, 프레임 중심
            ims.append(await self.grab(min(max(t, 0), dur)))
        # 서브프레임 사이에 달라진 영역만 블렌드(나머지는 그대로) — 정지 구간은 거의 공짜
        diff = np.zeros(ims[0].shape[:2], bool)
        for im in ims[1:]:
            diff |= (cv2.absdiff(im, ims[0]).max(axis=2) > 0)
        if not diff.any():
            return ims[0]
        ys, xs = np.where(diff)
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        acc = None
        for im in ims:
            c = im[y0:y1, x0:x1].astype(np.float32)
            a = c[..., 3:4] / 255.0
            c[..., :3] *= a
            c[..., 3:4] = a
            acc = c if acc is None else acc + c
        acc /= sub
        a = acc[..., 3:4]
        rgb = np.where(a > 1e-4, acc[..., :3] / np.maximum(a, 1e-4), 0)
        blend = np.clip(np.concatenate([rgb, a * 255.0], axis=2) + 0.5, 0, 255).astype(np.uint8)
        out = ims[0].copy()
        out[y0:y1, x0:x1] = blend
        return out

    async def close(self):
        try:
            if self.session:
                await self.session.close()
        finally:
            if self.proc:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(self.proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                try:
                    self.proc.wait(timeout=10)
                except Exception:
                    pass
            shutil.rmtree(self.profile, ignore_errors=True)


# ───────────────────────── 렌더 전 점검 · 효과음 계기 ─────────────────────────

def _rect(b):
    return (b["x"], b["y"], b["x"] + b["w"], b["y"] + b["h"])


def _overlap(a, b):                      # 맞닿기만 한 것은 겹침 아님
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def _norm_color(c):
    c = str(c).strip().lower()
    if c.startswith("#") and len(c) == 4:
        c = "#" + "".join(ch * 2 for ch in c[1:])
    return c.replace(" ", "")


def sample_times(events, dur, step):
    ts = {round(i * step, 4) for i in range(int(dur / step) + 1) if i * step <= dur}
    for e in events or []:
        for d in (0.0, 0.25, 0.5):
            if 0 <= e["t"] + d <= dur:
                ts.add(round(e["t"] + d, 4))
    return sorted(ts)


def sampled_to_boxes(samples, times, dur):
    """시각별 수집 결과 → 박스(t0=그 시각, t1=다음 표본 시각). 표본 사이는 «같은 모양이 이어진다»고 본다."""
    nxt = {t: (times[i + 1] if i + 1 < len(times) else dur) for i, t in enumerate(times)}
    return [dict(b, t0=b["t"], t1=nxt[b["t"]]) for b in samples]


def check_scene(meta, sampled, dur):
    """장면 점검 → [(수준, 규칙, 메시지)] (rule_check.report 형식)."""
    out = []
    E = lambda r, m: out.append(("ERROR", r, m))   # noqa: E731
    Wn = lambda r, m: out.append(("WARN", r, m))   # noqa: E731
    W, H = int(meta["W"]), int(meta["H"])

    # (a) 인지 텀
    ev = meta.get("EVENTS")
    if not ev:
        Wn("인지 텀 점검 못 함", "window.EVENTS 가 없다 — 새 요소 등장 시각을 못 본다(효과음 계기도 없다)")
    else:
        news = sorted((e for e in ev if str(e.get("role", "")).endswith("_in")), key=lambda e: e["t"])
        for a, b in zip(news, news[1:]):
            gap = b["t"] - a["t"]
            if 1e-3 < gap < GAP_MIN - 1e-6:       # 0 = 동시 등장(묶음)
                Wn("인지 텀 0.6초", f"{a['t']:.2f}s {a.get('id')} → {b['t']:.2f}s {b.get('id')} 간격 {gap:.2f}초 — 새 요소는 혼자 0.6초 이상(SKILL 3장, 같은 종류는 묶음)")

    # (b) 겹침
    manual = list(meta.get("BOXES") or [])
    keeps = [b for b in manual if b.get("kind") == "keepout"]
    boxes = [dict(b, t0=b.get("t0", 0.0), t1=b.get("t1", dur)) for b in manual if b.get("kind") != "keepout"]
    boxes += sampled
    if not boxes:
        Wn("겹침 검사 못 함", "BOXES 도 data-box 요소도 없다")
    hit = {}

    def add(key, t, msg):
        if key in hit:
            hit[key][1] += 1
        else:
            hit[key] = [t, 1, msg]
    fmt = lambda b: "(%d,%d,%d,%d)" % tuple(round(v) for v in _rect(b))   # noqa: E731
    tov = lambda a, b: a["t0"] < b["t1"] and b["t0"] < a["t1"]               # noqa: E731
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            if a["id"] == b["id"] or (a.get("group") and a.get("group") == b.get("group")) or not tov(a, b):
                continue
            if _overlap(_rect(a), _rect(b)):
                add(("ov",) + tuple(sorted((a["id"], b["id"]))), max(a["t0"], b["t0"]), f"{a['id']} {fmt(a)} ↔ {b['id']} {fmt(b)}")
        for z in keeps:
            zt = dict(z, t0=z.get("t0", 0.0), t1=z.get("t1", dur))
            if tov(a, zt) and _overlap(_rect(a), _rect(z)):
                add(("ko", a["id"], z.get("id")), max(a["t0"], zt["t0"]), f"{a['id']} {fmt(a)} ↔ 금지 구역 {z.get('id')} {fmt(z)}")
        x0, y0, x1, y1 = _rect(a)
        if not a.get("bleed") and (x0 < EDGE or y0 < EDGE or x1 > W - EDGE or y1 > H - EDGE):
            add(("edge", a["id"]), a["t0"], f"{a['id']} {fmt(a)} 화면 밖(가장자리 여유 {EDGE}px)")
    for key, (t, n, msg) in hit.items():
        rule = {"ov": "레이아웃 겹침", "ko": "금지 구역 침범", "edge": "화면 가장자리"}[key[0]]
        E(rule, f"{msg} — {t:.2f}s 부터" + (f" (표본 {n}곳)" if n > 1 else ""))

    # (c) 색 수
    pal = meta.get("PALETTE")
    if not pal:
        Wn("색 수 점검 못 함", "window.PALETTE 가 없다 — 장면에 쓴 색을 밝힌다(3색: 바탕·글·강조 하나, 비교 장면은 쪽마다 색 하나)")
    else:
        cols = sorted({_norm_color(c) for c in pal})
        if len(cols) > PALETTE_MAX:
            Wn("3색", f"색 {len(cols)}개 {cols} — 장면 색은 3색(SKILL 3장; 비교 장면은 쪽마다 색 하나만 예외)")
    return out


def events_to_sfx_plan(src, t0=0.0, speed=1.0, roles=None):
    """EVENTS → {역할 이름: [시각, …]} (효과음 붙일 때 sfx/check_sfx 입력으로 쓰는 변환).
    src      <name>_events.json 경로 · 그 내용(dict) · EVENTS 목록
    t0       이 영상이 배치표(edit_plan)에서 시작하는 시각 · speed 배치표 speed — 시각 = t0 + t·speed
             (오버레이는 최종(배속 후) 초로 흐르므로 배치표 시각으로 바꾸려면 speed 를 곱한다. 장면 단독이면 기본값 그대로)
    roles    주면 그 역할만
    edit_plan 에 넣기:  [{"t": t, "role": r} for r, ts in plan.items() for t in ts]   (r 은 sfx_roles 에 있어야 한다)
    check_sfx 에 넣기:  (t, 파일, 길이) 3-튜플 — 파일·길이는 sfx_roles 가 정한 뒤 edit_render 가 만든다."""
    if isinstance(src, (str, Path)):
        src = json.loads(Path(src).read_text(encoding="utf-8"))
    if isinstance(src, dict):
        src = src.get("events") or []
    out = {}
    for e in src:
        r = e.get("role")
        if not r or (roles and r not in roles):
            continue
        out.setdefault(r, []).append(round(t0 + e["t"] * speed, 4))
    return {r: sorted(ts) for r, ts in out.items()}


def start_ffmpeg(W, H, out_main, out_prev, alpha):
    fr = f"{FPS_NUM}/{FPS_DEN}"
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-framerate", fr, "-i", "-",
           "-f", "lavfi", "-i", f"color=c=black:s={W}x{H}:r={fr}",
           "-filter_complex", "[1:v][0:v]overlay=shortest=1:format=auto,format=yuv420p[prev]"]
    if alpha:
        cmd += ["-map", "0:v", "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", "-vendor", "apl0", "-r", fr, str(out_main)]
    else:
        # 불투명 장면: 알파를 무시하고 그대로 H.264
        cmd += ["-map", "0:v", "-vf", "format=yuv420p", "-c:v", "libx264", "-crf", "14", "-r", fr, str(out_main)]
    cmd += ["-map", "[prev]", "-c:v", "libx264", "-crf", "16", "-r", fr, str(out_prev)]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)


async def render(args):
    scene = Path(args.scene).resolve()
    name = args.name or scene.stem
    out = Path(args.out) if args.out else C.WORK / "html_motion"
    out.mkdir(parents=True, exist_ok=True)
    t_all = time.time()
    base_port = 9400 + (os.getpid() % 300)
    workers = [Worker(i, scene, C.W, C.H, args.alpha, base_port + i) for i in range(args.workers)]
    try:
        print(f"[html_motion] Chrome {args.workers}개 기동 …", flush=True)
        await asyncio.gather(*[w.start() for w in workers])
        meta = await workers[0].meta()
        W, H, dur = int(meta["W"]), int(meta["H"]), float(meta["DURATION"])
        if (W, H) != (C.W, C.H):
            for w in workers:
                w.W, w.H = W, H
                await w.cdp.call("Emulation.setDeviceMetricsOverride", width=W, height=H, deviceScaleFactor=1, mobile=False)
        total = int(round(dur / FRAME_DT))
        a, b = 0, total
        if args.frames:
            s, e = args.frames.split(":")
            a, b = int(s or 0), min(int(e or total), total)
        count = b - a
        print(f"[html_motion] 장면 {W}x{H} 길이 {dur}s → {total}프레임({FPS_NUM}/{FPS_DEN}) 중 {a}~{b-1} · 서브프레임 {args.sub} · 로드된 글꼴 {meta['fonts']}", flush=True)
        if meta["EVENTS"]:
            print(f"[html_motion] EVENTS {len(meta['EVENTS'])}개: " + ", ".join(f"{e['t']:.2f}s:{e.get('role')}" for e in meta["EVENTS"]), flush=True)
        (out / f"{name}_events.json").write_text(json.dumps({"events": meta["EVENTS"], "boxes": meta["BOXES"], "palette": meta["PALETTE"], "duration": dur}, ensure_ascii=False, indent=1), encoding="utf-8")

        # 렌더 전 점검 (CLAUDE.md) — 첫 프레임을 찍기 전에
        times = sample_times(meta["EVENTS"], dur, args.box_step)
        samples = sampled_to_boxes(await workers[0].collect_boxes(times), times, dur)
        n_data = len({b["id"] for b in samples})
        items = check_scene(meta, samples, dur)
        rpt = out / f"{name}_점검.txt"
        n_err = RC.report(items, rpt, f"{scene.name} (EVENTS {len(meta['EVENTS'] or [])} · 수동 박스 {len(meta['BOXES'] or [])} · data-box {n_data}종/{len(times)}시각 · PALETTE {len(meta['PALETTE'] or [])}색)")
        if n_err and not args.ignore:
            with open(rpt, "a", encoding="utf-8", newline="\n") as fh:
                fh.write(f"★ 렌더 전 규칙 점검에서 ERROR {n_err}건 — 멈춤 (--무시 로만 통과)\n")
            print(f"[html_motion] ERROR {n_err}건 — 렌더하지 않는다 ({rpt})", flush=True)
            return None, rpt, n_err
        if n_err:
            errs = [x for x in items if x[0] == "ERROR"]
            with open(rpt, "a", encoding="utf-8", newline="\n") as fh:
                fh.write(f"★ --무시 로 통과한 위반 {len(errs)}건:\n" + "".join(f"    [{lv}] {r}: {m}\n" for lv, r, m in errs))
            print(f"[html_motion] --무시: ERROR {n_err}건을 알고 통과 (위반 목록을 {rpt.name} 에 적었다)", flush=True)

        main = out / (f"{name}.mov" if args.alpha else f"{name}.mp4")
        prev = out / f"{name}_preview.mp4"
        ff = start_ffmpeg(W, H, main, prev, args.alpha)

        results, ready = {}, asyncio.Event()
        state = {"next": a}

        async def run(wi):
            w = workers[wi]
            for n in range(a + wi, b, args.workers):
                while n - state["next"] > 8 * args.workers:       # 메모리 상한
                    await asyncio.sleep(0.01)
                results[n] = await w.frame(n, args.sub, dur)
                ready.set()

        tasks = [asyncio.create_task(run(i)) for i in range(args.workers)]
        t_cap = time.time()
        done = 0
        while state["next"] < b:
            if state["next"] in results:
                ff.stdin.write(results.pop(state["next"]).tobytes())
                state["next"] += 1
                done += 1
                if done % 30 == 0 or done == count:
                    el = time.time() - t_cap
                    print(f"  프레임 {done}/{count}  {el:.1f}s  ({done/el:.2f} fps)", flush=True)
            else:
                for t in tasks:
                    if t.done() and t.exception():
                        raise t.exception()
                ready.clear()
                try:
                    await asyncio.wait_for(ready.wait(), 1.0)
                except asyncio.TimeoutError:
                    pass
        await asyncio.gather(*tasks)
        ff.stdin.close()
        ff.wait()
        el = time.time() - t_cap
        print(f"[html_motion] 캡처+인코딩 {el:.1f}s = 초당 {count/el:.2f}프레임 (서브프레임 {args.sub} → 캡처 {count*args.sub}장, {count*args.sub/el:.1f}장/s)", flush=True)
    finally:
        for w in workers:
            await w.close()

    if not args.no_sheet and not args.frames:
        sheet = out / f"{name}_sheet.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(prev), "-vf", "fps=4,scale=320:180,tile=6x4", "-frames:v", "1", "-q:v", "3", str(sheet)])
        print(f"[html_motion] 접촉 시트 {sheet}")
    print(f"[html_motion] 완료 {time.time()-t_all:.1f}s → {main}\n                         {prev}\n                         {rpt}")
    return main, rpt, n_err


def main():
    ap = argparse.ArgumentParser(description="HTML seek(t) 장면 → 영상")
    ap.add_argument("scene")
    ap.add_argument("--alpha", action="store_true", help="투명 배경 → ProRes 4444 알파 MOV")
    ap.add_argument("--sub", type=int, default=4, help="서브프레임 수(모션블러), 1 이면 끔")
    ap.add_argument("--workers", type=int, default=1, help="Chrome 병렬 개수")
    ap.add_argument("--out")
    ap.add_argument("--name")
    ap.add_argument("--frames", help="시작:끝 프레임(시험용)")
    ap.add_argument("--no-sheet", action="store_true")
    ap.add_argument("--box-step", type=float, default=0.1, help="data-box 수집 간격(초)")
    ap.add_argument("--무시", dest="ignore", action="store_true", help="rule_check ERROR 를 무시하고 통과(위반 목록은 점검 파일에)")
    args = ap.parse_args()
    main_path, _, _ = asyncio.run(render(args))
    sys.exit(1 if main_path is None else 0)


if __name__ == "__main__":
    main()
