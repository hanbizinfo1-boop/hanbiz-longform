# -*- coding: utf-8 -*-
"""성제관02 «종이 책상» 무대(R1 — Mustard 식: 종이 자료를 3D 책상에 놓고 카메라가 미끄러지며 훑음).
s07·s08·s32·s42 가 같은 무대를 spec 만 바꿔 쓴다. 글은 종이 텍스처(make_papers.py)에 이미 들어 있다 — 3D 글자 없음.

    blender -b -P desk.py -- <spec.json> [--still τ] [--frames a:b]

spec = {
  "out": "_tmp/sjk02/blender/s07",            # f0001.png … (프레임 1 = τ −pre)
  "pre": 0.18, "dur": 5.057, "post": 0.0,
  "desk": "소재/sjk02/codex/t_dark_desk.png", "desk_size": [3.2, 2.13],
  "sheets": [{"id": "a0", "tex": "menuA0", "tex2": "menuA0", "x": 0, "y": 0, "rz": 4, "s": 1,
              "drop": τ|null,                  # 그 시각에 위에서 내려앉음(없으면 처음부터 놓여 있음)
              "desat": [[τ, 0], [τ, 1]],       # 탈색 키(0 색 → 1 회색)
              "mix": [[τ, 0], [τ, 1]],          # tex → tex2 넘어감(전체)
              "wipe": [[τ, 0], [τ, 1]],         # tex → tex2 왼쪽에서 오른쪽으로 닦아 넘어감(형광펜 긋기)
              "lift": [[τ, 0], [τ, 0.02]],      # 들림(m)
              "z": 0}],                          # 쌓기 순서(겹칠 때 위)
  "cam": [{"t": τ, "pos": [x,y,z], "look": [x,y,z], "lens": 50, "focus": [x,y,z]|null, "fstop": 2.8}],
  "thread": {"pts": [[x,y,z], …], "keys": [[τ, 0], [τ, 1]], "width": 0.004},   # 주홍 실(선택)
  "light": "warm"
}
"""
import json
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[4]
argv = sys.argv[sys.argv.index("--") + 1:]
spec = json.load(open(argv[0], encoding="utf-8"))
STILL = float(argv[argv.index("--still") + 1]) if "--still" in argv else None
FR = argv[argv.index("--frames") + 1] if "--frames" in argv else None
P = lambda p: str(p if Path(p).is_absolute() else ROOT / p)
TEX = ROOT / "_tmp/sjk02/blender/tex"
FPS = 60000 / 1001
PRE, DUR, POST = spec.get("pre", 0), spec["dur"], spec.get("post", 0)
NF = int(round((PRE + DUR + POST) * FPS)) + 1
fr = lambda tau: (tau + PRE) * FPS + 1                 # τ → 프레임(실수)
SW, SH = 0.21, 0.297                                    # A4 (m)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    try:
        sc.render.engine = eng; break
    except TypeError:
        pass
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.render.fps, sc.render.fps_base = 60000, 1001
sc.frame_start, sc.frame_end = 1, NF
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_mode = "RGB"
sc.view_settings.view_transform = "AgX"
try:
    sc.view_settings.look = "AgX - Medium High Contrast"
except TypeError:
    pass
sc.render.use_motion_blur = True
sc.render.motion_blur_shutter = 0.5
ee = sc.eevee
for a, v in (("taa_render_samples", 48), ("use_shadows", True), ("use_raytracing", True), ("shadow_ray_count", 2), ("shadow_step_count", 8)):
    if hasattr(ee, a):
        setattr(ee, a, v)

wd = bpy.data.worlds.new("w"); sc.world = wd; wd.use_nodes = True
bg = wd.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.05, 0.055, 0.06, 1); bg.inputs[1].default_value = 0.6


def key_val(sock, keys, data_path="default_value"):
    for t, v in keys:
        sock.default_value = v; sock.keyframe_insert(data_path, frame=fr(t))


# ── 책상
def desk():
    w, h = spec.get("desk_size", [3.2, 2.13])
    w, h = w * 3, h * 3                          # 화면 끝에 책상 가장자리가 보이지 않게 3배(무늬는 같은 크기로 반복)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    o = bpy.context.object; o.scale = (w, h, 1); o.name = "desk"
    m = bpy.data.materials.new("desk"); m.use_nodes = True; nt = m.node_tree
    b = nt.nodes["Principled BSDF"]; b.inputs["Roughness"].default_value = 0.62
    im = nt.nodes.new("ShaderNodeTexImage"); im.image = bpy.data.images.load(P(spec.get("desk", "소재/sjk02/codex/t_dark_desk.png")))
    im.extension = "MIRROR"                     # 판을 넓혀도 이음매 없이 반복(거울 반복)
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (3, 3, 1); mp.inputs["Location"].default_value = (-1, -1, 0)
    nt.links.new(tc.outputs["UV"], mp.inputs[0]); nt.links.new(mp.outputs[0], im.inputs[0])
    nt.links.new(im.outputs[0], b.inputs["Base Color"])
    o.data.materials.append(m)


# ── 종이: 살짝 휜 격자 + 텍스처 두 장(섞기·닦기) + 채도
def sheet(d, idx):
    rnd = random.Random(idx * 7 + 3)
    s = d.get("s", 1.0)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=14, y_subdivisions=20, size=1)
    o = bpy.context.object; o.name = "sh_" + d["id"]
    curl = d.get("curl", rnd.uniform(0.004, 0.010))
    cx, cy = rnd.choice([-1, 1]), rnd.choice([-1, 1])
    for v in o.data.vertices:
        x, y = v.co.x * SW * s, v.co.y * SH * s
        u, w = v.co.x + 0.5, v.co.y + 0.5
        cu = max(0.0, (u - 0.6) / 0.4) if cx > 0 else max(0.0, (0.4 - u) / 0.4)
        cw = max(0.0, (w - 0.7) / 0.3) if cy > 0 else max(0.0, (0.3 - w) / 0.3)
        v.co = Vector((x, y, curl * (cu * cu + 0.6 * cw * cw) + 0.0015 * math.sin(u * 3.1)))
    bpy.ops.object.shade_smooth()
    m = bpy.data.materials.new("m_" + d["id"]); m.use_nodes = True; nt = m.node_tree
    b = nt.nodes["Principled BSDF"]; b.inputs["Roughness"].default_value = 0.78
    if "Subsurface Weight" in b.inputs:
        b.inputs["Subsurface Weight"].default_value = 0.02
    uv = nt.nodes.new("ShaderNodeTexCoord")
    t1 = nt.nodes.new("ShaderNodeTexImage"); t1.image = bpy.data.images.load(str(TEX / f"{d['tex']}.png"))
    t2 = nt.nodes.new("ShaderNodeTexImage"); t2.image = bpy.data.images.load(str(TEX / f"{d.get('tex2', d['tex'])}.png"))
    for t in (t1, t2):
        t.interpolation = "Cubic"; nt.links.new(uv.outputs["UV"], t.inputs[0])
    # 닦기: u < p 면 tex2
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(uv.outputs["UV"], sep.inputs[0])
    lt = nt.nodes.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; nt.links.new(sep.outputs[0], lt.inputs[0])
    lt.inputs[1].default_value = -0.01
    mx = nt.nodes.new("ShaderNodeMath"); mx.operation = "MAXIMUM"; nt.links.new(lt.outputs[0], mx.inputs[0]); mx.inputs[1].default_value = 0.0
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
    nt.links.new(mx.outputs[0], mix.inputs["Factor"]); nt.links.new(t1.outputs[0], mix.inputs[6]); nt.links.new(t2.outputs[0], mix.inputs[7])
    hsv = nt.nodes.new("ShaderNodeHueSaturation"); nt.links.new(mix.outputs[2], hsv.inputs["Color"])
    nt.links.new(hsv.outputs[0], b.inputs["Base Color"])
    if d.get("wipe"):
        key_val(lt.inputs[1], [(t, -0.01 + v * 1.02) for t, v in d["wipe"]])
    if d.get("mix"):
        key_val(mx.inputs[1], d["mix"])
    if d.get("desat"):
        key_val(hsv.inputs["Saturation"], [(t, 1 - 0.95 * v) for t, v in d["desat"]])
        key_val(hsv.inputs["Value"], [(t, 1 - 0.18 * v) for t, v in d["desat"]])
    o.data.materials.append(m)
    zbase = 0.0006 + 0.0011 * d.get("z", idx % 3)
    o.rotation_euler = (0, 0, math.radians(d.get("rz", 0)))
    o.location = (d["x"], d["y"], zbase)
    if d.get("drop") is not None:        # 위에서 내려앉음: 0.38초, 마지막에 미끄러짐
        t0 = d["drop"]
        o.location = (d["x"] - 0.05, d["y"] + 0.03, zbase + 0.22); o.rotation_euler[2] = math.radians(d.get("rz", 0) + 9)
        o.keyframe_insert("location", frame=fr(t0)); o.keyframe_insert("rotation_euler", frame=fr(t0))
        o.location = (d["x"], d["y"], zbase); o.rotation_euler[2] = math.radians(d.get("rz", 0))
        o.keyframe_insert("location", frame=fr(t0 + 0.38)); o.keyframe_insert("rotation_euler", frame=fr(t0 + 0.38))
        o.hide_render = True; o.keyframe_insert("hide_render", frame=fr(t0) - 1)
        o.hide_render = False; o.keyframe_insert("hide_render", frame=fr(t0))
    if d.get("lift"):
        for t, v in d["lift"]:
            o.location[2] = zbase + v; o.keyframe_insert("location", index=2, frame=fr(t))
    return o


def thread(th):
    cu = bpy.data.curves.new("thread", "CURVE"); cu.dimensions = "3D"
    sp = cu.splines.new("BEZIER"); pts = th["pts"]; sp.bezier_points.add(len(pts) - 1)
    for bp, p in zip(sp.bezier_points, pts):
        bp.co = Vector(p); bp.handle_left_type = bp.handle_right_type = "AUTO"
    cu.bevel_depth = th.get("width", 0.004); cu.bevel_resolution = 4; cu.resolution_u = 24
    o = bpy.data.objects.new("thread", cu); sc.collection.objects.link(o)
    m = bpy.data.materials.new("thread"); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.86, 0.10, 0.025, 1)          # #F05A28 근처(선형)
    b.inputs["Emission Color"].default_value = (0.86, 0.10, 0.025, 1); b.inputs["Emission Strength"].default_value = 1.2
    if th.get("show") is not None:
        o.hide_render = True; o.keyframe_insert("hide_render", frame=1)
        o.hide_render = False; o.keyframe_insert("hide_render", frame=fr(th["show"]))
    cu.materials.append(m)
    cu.bevel_factor_mapping_end = "RESOLUTION"          # 구간마다 같은 몫 — spec 의 i/nseg 가 그 점
    for t, v in th["keys"]:
        cu.bevel_factor_end = v; cu.keyframe_insert("bevel_factor_end", frame=fr(t))
    for t, v in th.get("glow", []):
        es = b.inputs["Emission Strength"]; es.default_value = v; es.keyframe_insert("default_value", frame=fr(t))
    for fc in (cu.animation_data.action.fcurves if hasattr(cu.animation_data.action, "fcurves") else []):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"


def lights():
    kind = spec.get("light", "warm")
    bpy.ops.object.light_add(type="AREA", location=(-0.6, 0.9, 1.6))
    a = bpy.context.object; a.data.energy = 140; a.data.size = 1.6; a.data.color = (1.0, 0.92, 0.82) if kind == "warm" else (0.9, 0.95, 1.0)
    a.rotation_euler = (math.radians(35), math.radians(-20), 0)
    bpy.ops.object.light_add(type="AREA", location=(1.2, -1.0, 1.0))
    f = bpy.context.object; f.data.energy = 40; f.data.size = 2.5; f.data.color = (0.82, 0.9, 1.0)
    f.rotation_euler = (math.radians(-50), math.radians(40), 0)


def camera():
    cd = bpy.data.cameras.new("cam"); cam = bpy.data.objects.new("cam", cd); sc.collection.objects.link(cam); sc.camera = cam
    tgt = bpy.data.objects.new("tgt", None); sc.collection.objects.link(tgt)
    foc = bpy.data.objects.new("foc", None); sc.collection.objects.link(foc)
    tr = cam.constraints.new("TRACK_TO"); tr.target = tgt; tr.track_axis = "TRACK_NEGATIVE_Z"; tr.up_axis = "UP_Y"
    cd.dof.use_dof = True; cd.dof.focus_object = foc; cd.sensor_width = 36; cd.clip_start = 0.01
    for k in spec["cam"]:
        f = fr(k["t"])
        cam.location = k["pos"]; cam.keyframe_insert("location", frame=f)
        tgt.location = k["look"]; tgt.keyframe_insert("location", frame=f)
        foc.location = k.get("focus") or k["look"]; foc.keyframe_insert("location", frame=f)
        cd.lens = k.get("lens", 50); cd.keyframe_insert("lens", frame=f)
        cd.dof.aperture_fstop = k.get("fstop", 2.8); cd.dof.keyframe_insert("aperture_fstop", frame=f)
    # 키 사이 이음: 기본 베지어(EZ 비슷) — 'lin' 키는 직선
    return cam


desk()
for i, d in enumerate(spec["sheets"]):
    sheet(d, i)
if spec.get("thread"):
    thread(spec["thread"])
lights()
camera()

out = Path(P(spec["out"]))
out.mkdir(parents=True, exist_ok=True)
if STILL is not None:
    f = int(round(fr(STILL))); sc.frame_set(f)
    sc.render.filepath = str(out / f"still_{STILL:.2f}.png")
    bpy.ops.render.render(write_still=True)
else:
    a, b = (int(x) for x in FR.split(":")) if FR else (1, NF)
    sc.frame_start, sc.frame_end = a, b
    sc.render.filepath = str(out / "f####")
    bpy.ops.render.render(animation=True)
print("DESK_DONE", NF)
