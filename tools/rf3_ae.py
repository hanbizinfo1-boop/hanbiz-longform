# -*- coding: utf-8 -*-
r"""[레거시 — 10-13 부터 AE 안 씀. 새 장면은 html_motion(references/ae-replacement.md)]
rf3 — PDF 장표 장면을 애프터이펙트로 만든다 (사장님 2026-09-28 «에펙으로 고급지게, 연속성으로 내용을 챙기게»).

장면 = 흐린 실사 배경 위에 PDF 장표가 3D 로 날아 들어오고, 카메라가 대본이 말하는 곳으로 밀고 들어가
       노란 테두리가 그려지며 나머지는 어두워진다. 다음 말로 넘어가면 같은 장표 안에서 이어서 옮겨 가거나
       옆 장표로 미끄러져 넘어간다(끊지 않고 잇는다). 레이더 = 위치, 노선 = 지하철이 실제로 달리듯 그려진다.

흐름: scenes(dict 목록) → build.jsx → AfterFX.exe -r (프로젝트 만들고 저장, 종료) → aerender (렌더 큐 전부) → ProRes .mov
AE 2026 한국어판 — 출력 모듈 템플릿 이름이 «고품질»(ProRes 422 HQ). JSX 안의 한글 경로는 \\u 이스케이프로 넣는다.
"""

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[0]))   # tools/ (config.py)
import config  # noqa: E402
import json
import subprocess
import time
from pathlib import Path

AE_DIR = config.AE_DIR
W, H, FPS = 1080, 1920, 30
TX, TY = 540, 640          # 관심 영역이 놓일 화면 중심 (자막 0.60H 위)
BW, BH = 1010, 860         # 관심 영역이 들어갈 상자
SMAX = 1.7
MOVE = 0.5                 # 장표 안에서 옮겨 가는 시간
SLIDE = 0.45               # 장표 바꾸는 시간
YEL = [1.0, 0.80, 0.05]
RED = [0.95, 0.18, 0.15]
PURPLE = [0.72, 0.38, 1.0]


def js(v):
    return json.dumps(v, ensure_ascii=True)


def probe_wh(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", str(p)],
                       capture_output=True, text=True)
    w, h = r.stdout.strip().split(",")[:2]
    return int(w), int(h)


def fit(roi, bw=BW, bh=BH, smax=SMAX):
    x0, y0, x1, y1 = roi
    return min(bw / (x1 - x0), bh / (y1 - y0), smax), ((x0 + x1) / 2, (y0 + y1) / 2)


HEAD = r"""
function ez(p){ if(!p||p.numKeys<1) return; for(var k=1;k<=p.numKeys;k++){ var e=new KeyframeEase(0,72);
  try{p.setTemporalEaseAtKey(k,[e],[e]);}catch(x){ try{p.setTemporalEaseAtKey(k,[e,e],[e,e]);}catch(y){ try{p.setTemporalEaseAtKey(k,[e,e,e],[e,e,e]);}catch(z){} } } } }
function lin(p){ if(!p) return; for(var k=1;k<=p.numKeys;k++){ p.setInterpolationTypeAtKey(k,KeyframeInterpolationType.LINEAR); } }
function flat(p){ if(!p) return; for(var k=1;k<=p.numKeys;k++){ try{p.setSpatialTangentsAtKey(k,[0,0,0],[0,0,0]);}catch(x){ try{p.setSpatialTangentsAtKey(k,[0,0],[0,0]);}catch(y){} } } }
function keys(p,arr){ for(var i=0;i<arr.length;i++){ p.setValueAtTime(arr[i][0],arr[i][1]); } }
function imp(path){ return app.project.importFile(new ImportOptions(new File(path))); }
function shapeLayer(comp,name,parent){ var L=comp.layers.addShape(); L.name=name; L.threeDLayer=true; L.setParentWithJump(parent);
  L.transform.position.setValue([0,0,0]); L.transform.anchorPoint.setValue([0,0,0]); return L; }
function grp(L){ return L.property("ADBE Root Vectors Group").addProperty("ADBE Vector Group").property("ADBE Vectors Group"); }
function stroke(c,col,w){ var s=c.addProperty("ADBE Vector Graphic - Stroke"); s.property("ADBE Vector Stroke Color").setValue(col);
  s.property("ADBE Vector Stroke Width").setValue(w); s.property("ADBE Vector Stroke Line Cap").setValue(2); s.property("ADBE Vector Stroke Line Join").setValue(2); return s; }
function fill(c,col){ var f=c.addProperty("ADBE Vector Graphic - Fill"); f.property("ADBE Vector Fill Color").setValue(col); return f; }
function glow(L,r,i){ try{ var g=L.Effects.addProperty("ADBE Glo2"); g.property("ADBE Glo2-0003").setValue(r); g.property("ADBE Glo2-0004").setValue(i);}catch(x){} }
function blur(L,v){ var b=L.Effects.addProperty("ADBE Gaussian Blur 2"); b.property("ADBE Gaussian Blur 2-0001").setValue(v); try{b.property("ADBE Gaussian Blur 2-0003").setValue(1);}catch(x){} }
var LOG=new File(%LOG%); LOG.open("w");
function log(s){ LOG.writeln(s); }
"""


class Scene:
    """한 장면(애펙 컴프 하나) — 시각은 전부 장면 시작 기준 초."""

    def __init__(self, name, dur, bg, bg_start=0.0):
        self.name, self.dur, self.bg, self.bg_start = name, dur, bg, bg_start
        self.items = []          # dict(kind, path, t, shots)
        self.sfx = []            # (장면 기준 초, 소리 종류)

    def page(self, path, t, shots):
        self.items.append(dict(kind="page", path=str(path), t=t, shots=shots))
        return self

    def video(self, path, t, start=0.0):
        self.items.append(dict(kind="video", path=str(path), t=t, start=start, shots=[dict(t=t, roi=None)]))
        return self

    def full(self, path, t, start=0.0, punches=(), mode="punch"):
        self.items.append(dict(kind="full", path=str(path), t=t, start=start, punches=list(punches), mode=mode, shots=[]))
        return self


def scene_jsx(sc, out_mov):
    L = []
    a = L.append
    comp_dur = sc.dur + 0.5
    a(f"(function(){{ var comp=app.project.items.addComp({js(sc.name)},{W},{H},1,{comp_dur:.3f},{FPS}); comp.motionBlur=true;")
    a("comp.shutterAngle=180; comp.bgColor=[0.05,0.06,0.08];")
    # 배경 — 흐린 실사 + 어둡게
    bw, bh = probe_wh(sc.bg)
    k = max(W / bw, H / bh) * 112
    a(f"var bgi=imp({js(str(sc.bg))}); var bg=comp.layers.add(bgi); bg.startTime={-sc.bg_start:.3f}; bg.transform.scale.setValue([{k:.2f},{k:.2f}]);")
    a(f"keys(bg.transform.scale,[[0,[{k:.2f},{k:.2f}]],[{comp_dur:.2f},[{k * 1.08:.2f},{k * 1.08:.2f}]]]); blur(bg,70);")
    a(f"var dk=comp.layers.addSolid([0.02,0.03,0.06],'dark',{W},{H},1); dk.transform.opacity.setValue(42);")
    for ii, it in enumerate(sc.items):
        t_in = it["t"]
        t_out = sc.items[ii + 1]["t"] if ii + 1 < len(sc.items) else None
        t_end = t_out if t_out is not None else comp_dur
        first = ii == 0
        if it["kind"] == "full":
            # 화면 가득 — 밀려 들어오기(1.32→1.0) + 번쩍 + 흔들림 (초반 후킹, 클라이언트 2026-09-28)
            if it["path"].lower().endswith((".png", ".jpg")):
                from PIL import Image
                fw, fh = Image.open(it["path"]).size
            else:
                fw, fh = probe_wh(it["path"])
            k = max(W / fw, H / fh) * 104
            v = f"f{ii}"
            end = min(comp_dur, (t_out + SLIDE) if t_out is not None else comp_dur)
            a(f"var {v}i=imp({js(it['path'])}); var {v}=comp.layers.add({v}i); {v}.motionBlur=true;")
            if not it["path"].lower().endswith((".png", ".jpg")):
                a(f"{v}.startTime={t_in - it.get('start', 0.0):.3f};")
            a(f"{v}.inPoint={max(0, t_in - 0.01):.3f}; {v}.outPoint={end:.3f};")
            if it.get("mode") == "slide":
                # 모형·실사를 장표처럼 — 3D 로 미끄러져 들어오고 천천히 밀려 들어가다 옆으로 빠진다 (사장님 2026-09-28 «모션그래픽처럼 자연스럽게»)
                a(f"{v}.threeDLayer=true;")
                pos, ry, scl = [], [], []
                if first:
                    scl += [[t_in, [k * 1.22] * 3], [t_in + 0.6, [k] * 3]]
                else:
                    pos += [[t_in, [W / 2 + 1250, H / 2, 300]], [t_in + SLIDE, [W / 2, H / 2, 0]]]
                    ry += [[t_in, -34], [t_in + SLIDE, 0]]
                    scl += [[t_in, [k] * 3]]
                    sc.sfx.append((t_in, "slide"))
                hold = t_out if t_out is not None else comp_dur
                scl += [[hold, [k * 1.09] * 3]]
                if t_out is not None:
                    pos += [[t_out, [W / 2, H / 2, 0]], [t_out + SLIDE, [W / 2 - 1250, H / 2, 300]]]
                    ry += [[t_out, 0], [t_out + SLIDE, 34]]
                for nm, arr in (("position", pos), ("yRotation", ry), ("scale", scl)):
                    if arr:
                        arr = sorted(dict((round(t, 3), val) for t, val in arr).items())
                        a(f"keys({v}.transform.{nm},{js([[t, val] for t, val in arr])}); ez({v}.transform.{nm});")
                a(f"flat({v}.transform.position);")
                continue
            ps = sorted(set([t_in] + list(it.get("punches", []))))
            sk = []
            for q, p in enumerate(ps):
                nxt = ps[q + 1] if q + 1 < len(ps) else t_end
                sk += [[p, [k * 1.32, k * 1.32]], [p + 0.32, [k, k]], [max(p + 0.33, nxt - 0.001), [k * 1.07, k * 1.07]]]
                sc.sfx += [(p - 0.08, "cut"), (p, "big")]
            a(f"keys({v}.transform.scale,{js(sk)}); ez({v}.transform.scale);")
            a(f"{v}.transform.position.expression={js('var P=' + json.dumps(ps) + '; var a=0; for(var i=0;i<P.length;i++){ if(time>=P[i]) a=Math.max(0,1-(time-P[i])/0.45);} value+[Math.sin(time*83)*30*a, Math.cos(time*71)*24*a];')};")
            a(f"var {v}f=comp.layers.addSolid([1,1,1],'flash',{W},{H},1); {v}f.inPoint={max(0, t_in - 0.01):.3f}; {v}f.outPoint={end:.3f};")
            fk = []
            for p in ps:
                fk += [[max(0, p - 0.001), 0], [p, 75], [p + 0.2, 0]]
            a(f"keys({v}f.transform.opacity,{js(fk)}); lin({v}f.transform.opacity);")
            continue
        if it["kind"] == "page":
            from PIL import Image
            pw, ph = Image.open(it["path"]).size
        else:
            pw, ph = probe_wh(it["path"])
        v = f"p{ii}"
        # 그림자 → 장표
        a(f"var {v}i=imp({js(it['path'])});")
        a(f"var {v}s=comp.layers.addSolid([0,0,0],'shadow{ii}',{pw},{ph},1); {v}s.threeDLayer=true; blur({v}s,60); {v}s.transform.opacity.setValue(70);")
        a(f"var {v}=comp.layers.add({v}i); {v}.threeDLayer=true; {v}.motionBlur=true;")
        if it["kind"] == "video":
            a(f"{v}.startTime={t_in - it['start']:.3f};")
        a(f"{v}s.setParentWithJump({v}); {v}s.transform.anchorPoint.setValue([{pw / 2},{ph / 2},0]); {v}s.transform.position.setValue([{pw / 2 + 10},{ph / 2 + 40},60]);")
        a(f"{v}.inPoint={max(0, t_in - 0.02):.3f}; {v}.outPoint={min(comp_dur, t_end + SLIDE + 0.05):.3f};")
        a(f"{v}s.inPoint={v}.inPoint; {v}s.outPoint={v}.outPoint;")
        if it.get("clip"):
            # 그림 부분만 카드로 — 제목·표·기사 글은 오려 낸다 (클라이언트 «글자 강조가 너무 많다»)
            x0, y0, x1, y1 = it["clip"]
            for lay in (v, f"{v}s"):
                a(f"var cm={lay}.Masks.addProperty('ADBE Mask Atom'); cm.maskMode=MaskMode.ADD; var cs=new Shape();"
                  f"cs.vertices=[[{x0},{y0}],[{x1},{y0}],[{x1},{y1}],[{x0},{y1}]]; cs.closed=true; cm.property('ADBE Mask Shape').setValue(cs);")
        # 샷마다 값
        shots = it["shots"]
        vals = []
        for s in shots:
            if it["kind"] == "video":
                sc_ = W * 1.22 / pw
                cx, cy = pw / 2, ph / 2
            else:
                sc_, (cx, cy) = fit(s["roi"])
            vals.append((sc_, cx, cy))
        anc, pos, scl, op, rx, ry = [], [], [], [], [], []
        s0, cx0, cy0 = vals[0]
        if first:
            anc.append((t_in, [cx0, cy0, 0])); pos.append((t_in, [TX, TY + 60, 900])); scl.append((t_in, [s0 * 90] * 3))
            rx.append((t_in, 16)); ry.append((t_in, -24)); op.append((t_in, 0))
            land0 = t_in + 0.55
            op.append((t_in + 0.3, 100))
        else:
            anc.append((t_in, [cx0, cy0, 0])); pos.append((t_in, [TX + 1350, TY, 250])); scl.append((t_in, [s0 * 100] * 3))
            ry.append((t_in, -38)); rx.append((t_in, 0)); op.append((t_in, 100))
            land0 = t_in + SLIDE
        anc.append((land0, [cx0, cy0, 0])); pos.append((land0, [TX, TY, 0])); scl.append((land0, [s0 * 100] * 3))
        rx.append((land0, 0)); ry.append((land0, 0))
        lands = [land0]
        for j in range(1, len(shots)):
            T = shots[j]["t"]
            sp, cxp, cyp = vals[j - 1]
            sj, cxj, cyj = vals[j]
            anc.append((T, [cxp, cyp, 0])); scl.append((T, [sp * 103] * 3))
            anc.append((T + MOVE, [cxj, cyj, 0])); scl.append((T + MOVE, [sj * 100] * 3))
            lands.append(T + MOVE)
        sl, cxl, cyl = vals[-1]
        hold_end = t_out if t_out is not None else comp_dur
        scl.append((hold_end, [sl * 104] * 3))
        if t_out is not None:
            anc.append((t_out, [cxl, cyl, 0])); pos.append((t_out, [TX, TY, 0])); ry.append((t_out, 0))
            pos.append((t_out + SLIDE, [TX - 1350, TY, 250])); ry.append((t_out + SLIDE, 38))
        for nm, arr in (("anchorPoint", anc), ("position", pos), ("scale", scl), ("opacity", op), ("xRotation", rx), ("yRotation", ry)):
            if arr:
                arr = sorted(dict((round(t, 3), val) for t, val in arr).items())
                a(f"keys({v}.transform.{nm},{js([[t, val] for t, val in arr])}); ez({v}.transform.{nm});")
        a(f"flat({v}.transform.position); flat({v}.transform.anchorPoint);")
        # 장면 소리
        if not first:
            sc.sfx.append((t_in, "slide"))
        if it["kind"] == "video":
            sc.sfx.append((t_in, "train"))
        # 샷별 얹는 것 — 장표에 붙인다(같이 움직인다)
        for j, s in enumerate(shots):
            L0 = lands[j]
            E = shots[j + 1]["t"] if j + 1 < len(shots) else hold_end
            if E - L0 < 0.2:
                continue
            if j > 0:
                sc.sfx.append((s["t"], "move"))
            sj = vals[j][0]
            if s.get("hl"):
                x0, y0, x1, y1 = s["hl"]
                pad = 14 / sj
                x0, y0, x1, y1 = x0 - pad, y0 - pad, x1 + pad, y1 + pad
                a(f"var d{ii}{j}=comp.layers.addSolid([0,0,0],'dim',{pw},{ph},1); d{ii}{j}.threeDLayer=true; d{ii}{j}.setParentWithJump({v});")
                a(f"d{ii}{j}.transform.anchorPoint.setValue([{pw / 2},{ph / 2},0]); d{ii}{j}.transform.position.setValue([{pw / 2},{ph / 2},0]);")
                if it.get("clip"):
                    cx0, cy0, cx1, cy1 = it["clip"]
                    a(f"var cm=d{ii}{j}.Masks.addProperty('ADBE Mask Atom'); cm.maskMode=MaskMode.ADD; var cs=new Shape();"
                      f"cs.vertices=[[{cx0},{cy0}],[{cx1},{cy0}],[{cx1},{cy1}],[{cx0},{cy1}]]; cs.closed=true; cm.property('ADBE Mask Shape').setValue(cs);")
                a(f"var m=d{ii}{j}.Masks.addProperty('ADBE Mask Atom'); m.maskMode=MaskMode.SUBTRACT; var ms=new Shape();"
                  f"ms.vertices=[[{x0},{y0}],[{x1},{y0}],[{x1},{y1}],[{x0},{y1}]]; ms.closed=true; m.property('ADBE Mask Shape').setValue(ms);"
                  f"m.property('ADBE Mask Feather').setValue([{18 / sj:.1f},{18 / sj:.1f}]);")
                a(f"keys(d{ii}{j}.transform.opacity,[[{L0:.3f},0],[{L0 + 0.3:.3f},55],[{E - 0.12:.3f},55],[{E:.3f},0]]);")
                a(f"var h{ii}{j}=shapeLayer(comp,'hl',{v}); var c=grp(h{ii}{j}); var r=c.addProperty('ADBE Vector Shape - Rect');"
                  f"r.property('ADBE Vector Rect Size').setValue([{x1 - x0},{y1 - y0}]); r.property('ADBE Vector Rect Position').setValue([{(x0 + x1) / 2},{(y0 + y1) / 2}]);"
                  f"r.property('ADBE Vector Rect Roundness').setValue({10 / sj:.1f}); var tr=c.addProperty('ADBE Vector Filter - Trim');"
                  f"stroke(c,{js(YEL)},{7 / sj:.2f}); tr=c.property('ADBE Vector Filter - Trim'); keys(tr.property('ADBE Vector Trim End'),[[{L0 + 0.05:.3f},0],[{L0 + 0.4:.3f},100]]); ez(tr.property('ADBE Vector Trim End'));"
                  f"keys(h{ii}{j}.transform.opacity,[[{E - 0.12:.3f},100],[{E:.3f},0]]); glow(h{ii}{j},{12 / sj:.1f},0.8);")
                sc.sfx.append((L0 + 0.05, "mark"))
            if s.get("radar"):
                x, y = s["radar"]
                d0, d1 = 30 / sj, 520 / sj
                a(f"var rd{ii}{j}=shapeLayer(comp,'radar',{v}); var c=grp(rd{ii}{j}); var e=c.addProperty('ADBE Vector Shape - Ellipse');"
                  f"e.property('ADBE Vector Ellipse Position').setValue([{x},{y}]); e.property('ADBE Vector Ellipse Size').setValue([{24 / sj:.1f},{24 / sj:.1f}]); fill(c,{js(RED)});"
                  f"keys(rd{ii}{j}.transform.opacity,[[{L0:.3f},0],[{L0 + 0.15:.3f},100],[{E - 0.1:.3f},100],[{E:.3f},0]]); glow(rd{ii}{j},{10 / sj:.1f},1.0);")
                n = 0
                t = L0
                while t < E - 0.3 and n < 6:
                    a(f"var rr=shapeLayer(comp,'ring',{v}); var c=grp(rr); var e=c.addProperty('ADBE Vector Shape - Ellipse'); e.property('ADBE Vector Ellipse Position').setValue([{x},{y}]);"
                      f"keys(e.property('ADBE Vector Ellipse Size'),[[{t:.3f},[{d0:.1f},{d0:.1f}]],[{t + 1.2:.3f},[{d1:.1f},{d1:.1f}]]]);"
                      f"stroke(c,{js(RED)},{6 / sj:.2f}); keys(rr.transform.opacity,[[{t:.3f},100],[{t + 1.2:.3f},0]]);"
                      f"rr.inPoint={t:.3f}; rr.outPoint={min(E, t + 1.25):.3f};")
                    n += 1
                    t += 0.45
                sc.sfx.append((L0, "radar"))
            for route, col in s.get("routes", []):
                seg = [((route[i + 1][0] - route[i][0]) ** 2 + (route[i + 1][1] - route[i][1]) ** 2) ** 0.5 for i in range(len(route) - 1)]
                tot = sum(seg)
                dur = min(1.3, max(0.6, E - L0 - 0.3))
                a(f"var ro=shapeLayer(comp,'route',{v}); var c=grp(ro); var pth=c.addProperty('ADBE Vector Shape - Group'); var sh=new Shape();"
                  f"sh.vertices={js([list(p) for p in route])}; sh.closed=false; pth.property('ADBE Vector Shape').setValue(sh);"
                  f"var tr=c.addProperty('ADBE Vector Filter - Trim'); stroke(c,{js(col)},{11 / sj:.2f}); tr=c.property('ADBE Vector Filter - Trim');"
                  f"keys(tr.property('ADBE Vector Trim End'),[[{L0:.3f},0],[{L0 + dur:.3f},100]]); lin(tr.property('ADBE Vector Trim End')); glow(ro,{16 / sj:.1f},1.2);"
                  f"keys(ro.transform.opacity,[[{E - 0.12:.3f},100],[{E:.3f},0]]);")
                # 달리는 열차 머리 — 흰 빛덩이
                acc, kk = 0.0, []
                for i, p in enumerate(route):
                    kk.append([L0 + dur * (acc / tot), [p[0], p[1], 0]])
                    if i < len(seg):
                        acc += seg[i]
                a(f"var tn=shapeLayer(comp,'train',{v}); var c=grp(tn); var e=c.addProperty('ADBE Vector Shape - Ellipse');"
                  f"e.property('ADBE Vector Ellipse Size').setValue([{30 / sj:.1f},{30 / sj:.1f}]); fill(c,[1,1,1]); glow(tn,{22 / sj:.1f},2.0);"
                  f"keys(tn.transform.position,{js(kk)}); lin(tn.transform.position); flat(tn.transform.position);"
                  f"keys(tn.transform.opacity,[[{L0:.3f},0],[{L0 + 0.08:.3f},100],[{L0 + dur + 0.25:.3f},100],[{L0 + dur + 0.5:.3f},0]]);")
                sc.sfx.append((L0 - 0.05, "train"))
    a(f"var rq=app.project.renderQueue.items.add(comp); var om=rq.outputModule(1); om.applyTemplate('\\uACE0\\uD488\\uC9C8'); om.file=new File({js(str(out_mov))});")
    a(f"log('ok {sc.name}'); }})();")
    return "\n".join(L)


def build_and_render(scenes, work):
    """scenes → .aep → .mov 들. 이미 같은 설정으로 렌더된 것은 건너뛴다."""
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    aep, jsx, logf = work / "rf3.aep", work / "build.jsx", work / "build_log.txt"
    body = [HEAD.replace("%LOG%", js(str(logf)))]
    body.append("app.newProject();")
    outs = {}
    for sc in scenes:
        out = work / f"{sc.name}.mov"
        outs[sc.name] = out
        if out.exists():
            out.unlink()
        body.append("try{" + scene_jsx(sc, out) + "}catch(e){ log('ERR " + sc.name + " '+e.toString()+' line '+e.line); }")
    body.append(f"app.project.save(new File({js(str(aep))})); LOG.close(); app.quit();")
    jsx.write_text("\n".join(body), encoding="ascii")
    if logf.exists():
        logf.unlink()
    t0 = time.time()
    subprocess.run([str(AE_DIR / "AfterFX.exe"), "-r", str(jsx)], capture_output=True, timeout=900)
    # AfterFX.exe 가 먼저 돌아오는 경우가 있어 로그가 닫힐 때까지 기다린다
    while time.time() - t0 < 900:
        txt_ = logf.read_text(errors="ignore") if logf.exists() else ""
        if aep.exists() and ("ok" in txt_ or "ERR" in txt_) and not _ae_running():
            break
        time.sleep(3)
    log = logf.read_text(errors="ignore") if logf.exists() else "(로그 없음)"
    print("AE 빌드:", log.strip().replace("\n", " | "), f"({time.time() - t0:.0f}초)", flush=True)
    if "ERR" in log:
        raise RuntimeError(log)
    r = subprocess.run([str(AE_DIR / "aerender.exe"), "-project", str(aep)], capture_output=True, timeout=3600)
    miss = [n for n, p in outs.items() if not p.exists()]
    if miss:
        raise RuntimeError(f"렌더 안 된 장면: {miss}\n{r.stdout.decode('cp949', 'ignore')[-2000:]}")
    return outs


def _ae_running():
    r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq AfterFX.exe"], capture_output=True, text=True, errors="ignore")
    return "AfterFX.exe" in r.stdout
