# -*- coding: utf-8 -*-
"""성제관01 장면 39 — 숫자의 방(짙은 남색) 3D 막대: 국밥 원가 블록 다섯이 쌓여 40%, 수육이 솟아 70%.
글자는 굽지 않는다 — 프레임마다 화면 좌표를 _tmp/sjk01/blender/b39/proj.json 으로 내보내 html 장면(s39.html)이 위에 얹는다.
    blender -b -P bars39.py -- <τ 시작> <τ 끝> <pre>
시각(τ) 은 tools/scenes/sjk01/data/s39.js 와 같은 기준(장면 시작 = 0).
"""
import json
import math
import sys
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[4]
argv = sys.argv[sys.argv.index("--") + 1:]
T0, T1 = float(argv[0]), float(argv[1])
OUT = ROOT / "_tmp/sjk01/blender/b39"
OUT.mkdir(parents=True, exist_ok=True)
FPS = 60000 / 1001

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
HMAX = 4.0                                   # 100% 높이


def mat(name, col, rough=0.35, emit=None, es=0.0, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = es
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
        m.surface_render_method = "BLENDED" if hasattr(m, "surface_render_method") else m.blend_method
    return m


def srgb(h):
    h = h.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def block(name, x, z0, h, m, w=0.9):
    bpy.ops.mesh.primitive_cube_add(location=(x, 0, z0 + h / 2))
    o = bpy.context.object; o.name = name; o.scale = (w / 2, w / 2, h / 2)
    bv = o.modifiers.new("bv", "BEVEL"); bv.width = 0.035; bv.segments = 3
    o.data.materials.append(m)
    return o


def key(o, attr, frames_vals):
    for f, v in frames_vals:
        setattr(o, attr, v); o.keyframe_insert(attr, frame=f)


fr = lambda tau: round((tau - T0) * FPS) + 1
EO = lambda p: 1 - (1 - p) ** 3

# 방
floor = mat("floor", srgb("#0F1B2E"), 0.22)
bpy.ops.mesh.primitive_plane_add(size=60); bpy.context.object.data.materials.append(floor)
wall = mat("wall", srgb("#0B1524"), 0.8)
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 14, 0), rotation=(math.radians(90), 0, 0)); bpy.context.object.data.materials.append(wall)

# 100% 유리 틀(빈 자리)
ghost = mat("ghost", srgb("#9FB4D8"), 0.5, emit=srgb("#9FB4D8"), es=0.6)
for x in (-1.3, 1.3):
    g = block("ghost", x, 0, HMAX, ghost, 0.96)
    g.modifiers.clear()
    w = g.modifiers.new("wf", "WIREFRAME"); w.thickness = 0.018

# 국밥 원가 블록(재현자료 10-1: 사골 육수 1,200 · 앞다리살 1,700 · 밥 400 · 부추·파·다대기 300 · 김치·깍두기 400 = 4,000 / 10,000)
SEG = [("사골 육수", 1200), ("돼지 앞다리살", 1700), ("밥", 400), ("부추·파·다대기", 300), ("김치·깍두기", 400)]
cols = ["#2E55D9", "#4A6FE8", "#2447B8", "#5C7FF0", "#1F3E9E"]
DROP = [0.55, 1.05, 1.55, 2.05, 2.55]          # τ — «재료랑 지금 사는 가격을 적어 줄게» 동안 차례로
z = 0.0
segs = []
for (nm, won), c, td in zip(SEG, cols, DROP):
    h = HMAX * won / 10000
    o = block(nm, -1.3, z, h, mat(nm, srgb(c), 0.3))
    zt = z + h / 2
    key(o, "location", [(fr(td - 0.01), Vector((-1.3, 0, zt + 3.0))), (fr(td), Vector((-1.3, 0, zt + 3.0))), (fr(td + 0.35), Vector((-1.3, 0, zt)))])
    key(o, "hide_render", [(fr(td) - 1, True), (fr(td), False)])
    segs.append((nm, won, o, z, h))
    z += h

# 수육(소) 막대 — «만 사천 원이면» 에 솟아 70%
yel = mat("suyuk", srgb("#F2C230"), 0.3, emit=srgb("#F2C230"), es=0.25)
sb = block("수육", 1.3, 0, HMAX * 0.70, yel)
TS = float(argv[3]) if len(argv) > 3 else 16.0
sb.scale = (0.45, 0.45, 0.0001); sb.location = (1.3, 0, 0.0001)
key(sb, "hide_render", [(fr(TS) - 1, True), (fr(TS), False)])
for k in range(0, 31):
    p = k / 30; e = EO(p); h = HMAX * 0.70 * max(e, 0.0001)
    sb.scale = (0.45, 0.45, h / 2); sb.location = (1.3, 0, h / 2)
    sb.keyframe_insert("scale", frame=fr(TS) + k * 2); sb.keyframe_insert("location", frame=fr(TS) + k * 2)

# 40% 기준선(빛나는 얇은 판)
line = mat("line", srgb("#E8EDF5"), 0.5, emit=srgb("#E8EDF5"), es=6.0)
bpy.ops.mesh.primitive_cube_add(location=(0, -0.48, HMAX * 0.40)); ln = bpy.context.object
ln.scale = (2.4, 0.012, 0.012); ln.data.materials.append(line)

# 빛
for loc, en, col in (((-4, -5, 8), 900, (0.85, 0.9, 1.0)), ((6, 2, 6), 400, (1.0, 0.92, 0.8)), ((0, 6, 6), 700, (0.5, 0.6, 1.0))):
    L = bpy.data.lights.new("l", "AREA"); L.energy = en; L.size = 4; L.color = col
    o = bpy.data.objects.new("l", L); sc.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector((0, 0, 1.5)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
world = bpy.data.worlds.new("w"); sc.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (*srgb("#0A1220"), 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6

# 카메라 — 둘레를 돌다 멈춤(연출표 «둘레를 돌다 멈춤»)
cam = bpy.data.cameras.new("cam"); cam.lens = 34
co = bpy.data.objects.new("cam", cam); sc.collection.objects.link(co); sc.camera = co
tgt = bpy.data.objects.new("tgt", None); sc.collection.objects.link(tgt)
c = co.constraints.new("TRACK_TO"); c.target = tgt; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
nfr = round((T1 - T0) * FPS)
for f in range(1, nfr + 2, 6):
    tau = T0 + (f - 1) / FPS
    p = min(1.0, max(0.0, (tau - T0) / max(1e-6, (min(T1, 20.5) - T0))))
    e = p * p * (3 - 2 * p)
    ang = math.radians(-38 + 46 * e)
    r = 12.5 - 1.8 * e
    co.location = (r * math.sin(ang), -r * math.cos(ang), 2.6 + 0.4 * e)
    co.keyframe_insert("location", frame=f)
    tgt.location = (0.25 * e, 0, 1.55 + 0.25 * e); tgt.keyframe_insert("location", frame=f)

sc.frame_start, sc.frame_end = 1, nfr
sc.render.fps = 60; sc.render.fps_base = 1.001
for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
    try:
        sc.render.engine = eng; break
    except TypeError:
        pass
try:
    sc.eevee.taa_render_samples = 16
    sc.eevee.use_raytracing = False
except AttributeError:
    pass
sc.render.use_motion_blur = True
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.view_settings.view_transform = "AgX"
sc.render.image_settings.file_format = "PNG"
sc.render.filepath = str(OUT / "f_")

# 화면 좌표(html 글 얹기용)
proj = []
for f in range(1, nfr + 1):
    sc.frame_set(f)
    def P(v):
        q = world_to_camera_view(sc, co, Vector(v)); return [round(q.x * 1920, 1), round((1 - q.y) * 1080, 1)]
    d = {"A_top": P((-1.3, 0, HMAX * 0.40)), "B_top": P((1.3, 0, sb.scale.z * 2)), "line_l": P((-2.6, 0, HMAX * 0.4)), "line_r": P((2.6, 0, HMAX * 0.4)),
         "A_base": P((-1.3, 0, 0)), "B_base": P((1.3, 0, 0)), "ghost_A": P((-1.3, 0, HMAX)), "ghost_B": P((1.3, 0, HMAX))}
    d["segs"] = [P((-1.3 + 0.5, -0.5, z0 + h / 2)) for (_, _, _, z0, h) in segs]
    proj.append(d)
(OUT / "proj.json").write_text(json.dumps(proj), encoding="utf-8")
bpy.ops.render.render(animation=True)
print("완료", nfr)
