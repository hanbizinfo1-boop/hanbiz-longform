# -*- coding: utf-8 -*-
"""s55 «배달 줄이고 포장 할인 → 매출 조금 ↓ · 수익 ↑» — 나무 계산대 위 유리 통 둘(R3 Economist 식 «차오르고 빠지는 통»).
왼쪽 통 = 매출(회청 물), 오른쪽 통 = 수익(주홍 물). 장면 앞 4초(배달 메뉴 줄이기·포장 할인)는 html 재현 화면 — 블렌더는 «그랬더니»부터.
이름표(매출·수익)는 html 이 proj.js 로 얹는다.

    blender -b -P tanks.py -- [--still τ] [--frames a:b]
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bl_common as B  # noqa: E402
import bpy  # noqa: E402

st = B.Stage(55, "s55")
st.counter("wood", wall="p54_delivery_bag", wall_dist=1.5, wall_bright=0.40)
st.lights(warm=True, key=200)

R, H = 0.11, 0.42
glass = st.mat("glass", (0.92, 0.96, 0.97), rough=0.04, trans=1.0, ior=1.45)
steel = st.mat("steel", "#A9AFB4", rough=0.25, metal=1.0)
t_then, t_sales, t_bank, t_more, t_only, t_never, t_count = (st.at("그랬더니"), st.at("매출은"), st.at("통장에"), st.at("오히려"),
                                                              st.at("매출만"), st.at("절대"), st.at("따져"))


def tank(name, x, col, lv_keys):
    bpy.ops.mesh.primitive_cylinder_add(radius=R, depth=H, vertices=96, location=(x, 0, H / 2 + 0.03))
    g = bpy.context.object; g.name = name + "_glass"
    sol = g.modifiers.new("sol", "SOLIDIFY"); sol.thickness = 0.005
    g.data.materials.append(glass); bpy.ops.object.shade_smooth()
    # 뚜껑 없이 위가 열린 통: 위 면 지우기
    import bmesh
    bm = bmesh.new(); bm.from_mesh(g.data)
    top = [f for f in bm.faces if f.normal.z > 0.9]
    bmesh.ops.delete(bm, geom=top, context="FACES"); bm.to_mesh(g.data); bm.free()
    for zz, hh in ((0.015, 0.03), (H + 0.03 + 0.008, 0.016)):     # 아래 받침 · 위 테두리(쇠)
        bpy.ops.mesh.primitive_cylinder_add(radius=R + 0.012, depth=hh, vertices=96, location=(x, 0, zz))
        r = bpy.context.object; r.data.materials.append(steel); bpy.ops.object.shade_smooth()
        if zz > 0.1:
            r.modifiers.new("sol", "SOLIDIFY").thickness = 0.01
            bm = bmesh.new(); bm.from_mesh(r.data)
            bmesh.ops.delete(bm, geom=[f for f in bm.faces if abs(f.normal.z) > 0.9], context="FACES"); bm.to_mesh(r.data); bm.free()
    # 물: 바닥 기준 높이 비율 키
    bpy.ops.mesh.primitive_cylinder_add(radius=R - 0.007, depth=1, vertices=96, location=(x, 0, 0))
    w = bpy.context.object; w.name = name + "_liq"; bpy.ops.object.shade_smooth()
    w.data.materials.append(st.mat(name + "_liq", col, rough=0.15, coat=0.6))
    for v in w.data.vertices:
        v.co.z += 0.5                                       # 원점을 바닥으로
    for t, lv in lv_keys:
        w.scale = (1, 1, max(0.001, lv * (H - 0.01))); w.location = (x, 0, 0.033)
        w.keyframe_insert("scale", index=2, frame=st.fr(t))
    w.keyframe_insert("location", frame=1)
    st.anchor(name + "_top", lambda w=w, x=x: B.Vector((x, 0, H + 0.08)))
    st.anchor(name + "_lv", lambda w=w, x=x: B.Vector((x + R + 0.01, 0, 0.033 + w.scale.z)))
    return w


XS, XP = -0.17, 0.17
sales = tank("sales", XS, "#7F93A3", [(-1, 0.86), (t_sales, 0.86), (t_sales + 0.9, 0.74)])
prof = tank("prof", XP, "#F05A28", [(-1, 0.20), (t_bank + 0.45, 0.20), (t_more + 0.2, 0.20), (t_more + 1.2, 0.52)])
# «매출만 봤으면» — 매출 통이 잠깐 회색으로 빠짐(못 할 결정) → «따져 보니까» 수익 통 빛
lm = bpy.data.materials["sales_liq"].node_tree.nodes["Principled BSDF"].inputs["Base Color"]
for t, c in ((t_only, "#7F93A3"), (t_only + 0.4, "#9AA0A6")):
    lm.default_value = (*B.Stage.srgb(c), 1); lm.keyframe_insert("default_value", frame=st.fr(t))
pe = bpy.data.materials["prof_liq"].node_tree.nodes["Principled BSDF"]
pe.inputs["Emission Color"].default_value = (*B.Stage.srgb("#F05A28"), 1)
for t, v in ((t_count, 0.0), (t_count + 0.5, 1.6)):
    pe.inputs["Emission Strength"].default_value = v; pe.inputs["Emission Strength"].keyframe_insert("default_value", frame=st.fr(t))

st.camera([
    {"t": -st.pre, "pos": [0.08, -1.30, 0.46], "look": [0.0, 0.0, 0.22], "lens": 35, "fstop": 4.0, "focus": [0, 0, 0.22]},
    {"t": t_then - 0.2, "pos": [0.08, -1.30, 0.46], "look": [0.0, 0.0, 0.22], "lens": 35, "fstop": 4.0, "focus": [0, 0, 0.22]},
    {"t": t_bank - 0.1, "pos": [-0.02, -1.22, 0.42], "look": [0.0, 0.0, 0.22], "lens": 35, "fstop": 4.0, "focus": [0, 0, 0.22]},
    {"t": t_only - 0.1, "pos": [-0.08, -1.20, 0.40], "look": [0.0, 0.0, 0.22], "lens": 35, "fstop": 4.0, "focus": [0, 0, 0.22]},
    {"t": t_only + 0.6, "pos": [-0.30, -0.95, 0.36], "look": [XS + 0.04, 0.0, 0.22], "lens": 38, "fstop": 2.8, "focus": [XS, 0, 0.22]},
    {"t": t_count - 0.2, "pos": [-0.28, -0.93, 0.36], "look": [XS + 0.05, 0.0, 0.22], "lens": 38, "fstop": 2.8, "focus": [XS, 0, 0.22]},
    {"t": t_count + 0.7, "pos": [0.30, -0.95, 0.36], "look": [XP - 0.04, 0.0, 0.22], "lens": 38, "fstop": 2.8, "focus": [XP, 0, 0.22]},
    {"t": st.dur + st.post, "pos": [0.27, -0.92, 0.35], "look": [XP - 0.04, 0.0, 0.22], "lens": 38, "fstop": 2.8, "focus": [XP, 0, 0.22]},
])
st.run()
