# -*- coding: utf-8 -*-
"""s17 «남은 건 뭐다? 수수료랑 광고비 경쟁» — 스테인리스 계산대 위 유리 동전 통(R3). 바닥 양쪽 관 둘로 동전이 빠져나가 통이 빈다.
«수수료랑»에 왼쪽 관, «광고비»에 오른쪽 관. 이름표(수수료·광고비)는 html 이 proj.js 로 관 끝에 얹는다.

    blender -b -P coins.py -- [--still τ] [--frames a:b]
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bl_common as B  # noqa: E402
import bpy  # noqa: E402
import bmesh  # noqa: E402

st = B.Stage(17, "s17")
st.counter("steel", wall="p14_old_counter_film", wall_dist=1.4, wall_bright=0.45)
st.lights(warm=True, key=200)
t_fee, t_ad = st.at("수수료랑"), st.at("광고비")

glass = st.mat("glass", (0.93, 0.97, 0.98), rough=0.05, trans=1.0, ior=1.45)
steel = st.mat("steel", "#A3AAAF", rough=0.28, metal=1.0)
gold = st.mat("coin", "#C9A15A", rough=0.3, metal=1.0)
R, H, Z0 = 0.12, 0.30, 0.12                       # 통 반지름·높이·바닥 높이(다리 위)

bpy.ops.mesh.primitive_cylinder_add(radius=R, depth=H, vertices=96, location=(0, 0, Z0 + H / 2))
g = bpy.context.object; g.modifiers.new("s", "SOLIDIFY").thickness = 0.005; g.data.materials.append(glass); bpy.ops.object.shade_smooth()
bm = bmesh.new(); bm.from_mesh(g.data); bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z > 0.9], context="FACES"); bm.to_mesh(g.data); bm.free()
bpy.ops.mesh.primitive_cylinder_add(radius=R + 0.01, depth=0.02, vertices=96, location=(0, 0, Z0 - 0.01))
bpy.context.object.data.materials.append(steel)
for k in range(4):
    a = math.radians(45 + 90 * k)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.008, depth=Z0, location=(0.09 * math.cos(a), 0.09 * math.sin(a), Z0 / 2))
    bpy.context.object.data.materials.append(steel)

# 관 둘: 통 바닥 옆에서 나와 아래로 휘어 계산대 바깥(화면 아래)으로
def pipe(sign):
    cu = bpy.data.curves.new("pipe", "CURVE"); cu.dimensions = "3D"
    sp = cu.splines.new("BEZIER"); pts = [(sign * (R - 0.01), 0, Z0 + 0.015), (sign * 0.22, 0, Z0 + 0.01), (sign * 0.32, -0.05, 0.05), (sign * 0.40, -0.18, 0.02)]
    sp.bezier_points.add(len(pts) - 1)
    for bp, p in zip(sp.bezier_points, pts):
        bp.co = p; bp.handle_left_type = bp.handle_right_type = "AUTO"
    cu.bevel_depth = 0.022; cu.bevel_resolution = 6; cu.resolution_u = 32
    o = bpy.data.objects.new("pipe", cu); st.sc.collection.objects.link(o)
    cu.materials.append(glass)
    return pts


PL, PR = pipe(-1), pipe(1)
rnd = random.Random(17)


def coin():
    bpy.ops.mesh.primitive_cylinder_add(radius=0.016, depth=0.0035, vertices=32)
    o = bpy.context.object; o.data.materials.append(gold)
    bv = o.modifiers.new("bv", "BEVEL"); bv.width = 0.001; bv.segments = 2
    return o


# 통 안 동전 더미: 층층이(아래부터). 위 동전부터 사라지며 관으로 흘러 나감
pile = []
for i in range(260):
    o = coin()
    r = R - 0.02; a = rnd.uniform(0, 2 * math.pi); rr = r * math.sqrt(rnd.random())
    z = Z0 + 0.006 + 0.19 * (i / 260) + rnd.uniform(0, 0.006)
    o.location = (rr * math.cos(a), rr * math.sin(a), z)
    o.rotation_euler = (rnd.uniform(-0.22, 0.22), rnd.uniform(-0.22, 0.22), rnd.uniform(0, 6.28))
    pile.append(o)
pile.sort(key=lambda o: -o.location.z)
end = st.dur + st.post
drain = [o for o in pile[:200]]            # 200개가 빠짐(통 거의 빔)
for j, o in enumerate(drain):
    t = t_fee + 0.15 + (end - t_fee - 0.2) * (j / len(drain)) ** 0.9
    if j % 2 == 1 and t < t_ad:              # 오른쪽 관은 «광고비»부터
        t = t_ad + (t - t_fee) * 0.5
    o.hide_render = False; o.keyframe_insert("hide_render", frame=1)
    o.hide_render = True; o.keyframe_insert("hide_render", frame=int(st.fr(t)))

# 관 안을 흐르는 동전(흐름 표현): 관 길을 따라 미끄러짐
def flow(pts, t_start, n):
    for k in range(n):
        o = coin(); t0 = t_start + k * (end - t_start) / n
        st.show(o, t0, t0 + 0.5)
        for s_, p in enumerate(pts):
            o.location = (p[0] + rnd.uniform(-0.004, 0.004), p[1], p[2]); o.keyframe_insert("location", frame=st.fr(t0 + 0.5 * s_ / (len(pts) - 1)))
        o.rotation_euler = (rnd.uniform(0, 6), rnd.uniform(0, 6), 0); o.keyframe_insert("rotation_euler", frame=st.fr(t0))
        o.rotation_euler = (rnd.uniform(6, 12), rnd.uniform(6, 12), 0); o.keyframe_insert("rotation_euler", frame=st.fr(t0 + 0.5))


flow(PL, t_fee + 0.1, 26)
flow(PR, t_ad + 0.05, 18)
st.anchor("fee", lambda: B.Vector(PL[-1]))
st.anchor("ad", lambda: B.Vector(PR[-1]))

st.camera([
    {"t": -st.pre, "pos": [0.05, -0.95, 0.50], "look": [0.0, 0.0, 0.20], "lens": 40, "fstop": 3.5, "focus": [0, 0, 0.2]},
    {"t": t_fee - 0.1, "pos": [0.03, -0.82, 0.44], "look": [0.0, 0.0, 0.20], "lens": 40, "fstop": 3.5, "focus": [0, 0, 0.2]},
    {"t": end, "pos": [0.00, -0.98, 0.40], "look": [0.0, -0.03, 0.14], "lens": 36, "fstop": 4.0, "focus": [0, 0, 0.18]},
])
st.run()
