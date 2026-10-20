# -*- coding: utf-8 -*-
"""s33 «AI 는 평균적인 글» — 나무 계산대 위 유리 깔때기(R3). 여러 색 구슬(세상 글)이 깔때기로 쏟아져 돌며 내려가고
아래 주둥이로 회색 구슬 하나만 나온다. 끝에서 그 회색 구슬이 똑같은 회색 구슬 줄(다른 가게들) 사이로 굴러 들어가 묻힌다.
화면 글 없음(그림만).

    blender -b -P funnel.py -- [--still τ] [--frames a:b]
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bl_common as B  # noqa: E402
import bpy  # noqa: E402
import bmesh  # noqa: E402

st = B.Stage(33, "s33")
st.counter("wood", wall="p26_dawn_tile_wall", wall_dist=1.4, wall_bright=0.45)
st.lights(warm=True, key=200)

t_avg, t_world, t_pick, t_biz, t_mem = st.at("평균적인"), st.at("세상에"), st.at("제일"), st.at("장사에서"), st.at("기억에")
ZT, ZB, RT, RB = 0.52, 0.30, 0.17, 0.022            # 깔때기 위·아래 높이, 위·아래 반지름
SP = 0.10                                           # 주둥이 길이 → 끝 z = ZB - SP

glass = st.mat("glass", (0.93, 0.97, 0.98), rough=0.05, trans=1.0, ior=1.4)
steel = st.mat("steel", "#9EA5AA", rough=0.3, metal=1.0)
bpy.ops.mesh.primitive_cone_add(vertices=96, radius1=RB, radius2=RT, depth=ZT - ZB, end_fill_type="NOTHING", location=(0, 0, (ZT + ZB) / 2))
cone = bpy.context.object; cone.modifiers.new("s", "SOLIDIFY").thickness = 0.004; cone.data.materials.append(glass); bpy.ops.object.shade_smooth()
# 10-20 사장님 «공이 떨어지기전에 사라져» — 유리가 거의 안 보여 구슬이 허공에서 꺼지는 것처럼 보였다.
# → 깔때기 목(아래 띠)과 주둥이를 짙은 쇠로 막아 구슬이 «구멍으로 빠져 들어가» 보이게 + 입구에 쇠 테두리(깔때기 모양이 읽히게)
dark = st.mat("throat", "#3A3F44", rough=0.45, metal=1.0)
ZN = ZB + 0.06                                       # 쇠 목 윗선
RN = RB + (RT - RB) * (ZN - ZB) / (ZT - ZB)
bpy.ops.mesh.primitive_cone_add(vertices=96, radius1=RB + 0.003, radius2=RN + 0.003, depth=ZN - ZB, end_fill_type="NOTHING", location=(0, 0, (ZN + ZB) / 2))
nk = bpy.context.object; nk.modifiers.new("s", "SOLIDIFY").thickness = 0.004; nk.data.materials.append(dark); bpy.ops.object.shade_smooth()
bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=RB + 0.003, depth=SP, end_fill_type="NOTHING", location=(0, 0, ZB - SP / 2))
sp = bpy.context.object; sp.modifiers.new("s", "SOLIDIFY").thickness = 0.004; sp.data.materials.append(dark); bpy.ops.object.shade_smooth()
bpy.ops.mesh.primitive_torus_add(major_radius=RT, minor_radius=0.004, location=(0, 0, ZT))
bpy.context.object.data.materials.append(steel)
# 받침: 쇠 고리 + 다리 셋
bpy.ops.mesh.primitive_torus_add(major_radius=0.105, minor_radius=0.006, location=(0, 0, 0.40))
bpy.context.object.data.materials.append(steel)
for k in range(3):
    a = math.radians(90 + 120 * k)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.006, depth=0.41, location=(0.105 * math.cos(a), 0.105 * math.sin(a), 0.205))
    bpy.context.object.data.materials.append(steel)

COLS = ["#1FA39A", "#F05A28", "#E9B23A", "#3C6FB0", "#C8443B", "#6E9F4B", "#8D5BA6", "#E07B9A"]
mats = [st.mat(f"b{i}", c, rough=0.25, coat=0.8) for i, c in enumerate(COLS)]
grey = st.mat("grey", "#9AA0A6", rough=0.35, coat=0.5)
BR = 0.016
rnd = random.Random(33)


def ball(m):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=BR, segments=32, ring_count=16)
    o = bpy.context.object; bpy.ops.object.shade_smooth(); o.data.materials.append(m)
    return o


# 쏟아지는 구슬: 위에서 떨어져 테두리 → 돌며 내려가 주둥이로 사라짐
N = 46
for i in range(N):
    o = ball(mats[i % len(mats)])
    t0 = -0.1 + (t_pick + 0.3) * i / N + rnd.uniform(0, 0.08)     # 장면 시작부터 «제일» 무렵까지 고르게
    if i < 10:
        t0 = -0.15 + 0.06 * i                                         # 첫 화면에 이미 몇 개 돌고 있음
    a0 = rnd.uniform(0, 2 * math.pi); turns = rnd.uniform(1.4, 2.2); dur = rnd.uniform(1.3, 1.8)
    t_end = t0 + 0.4 + dur
    st.show(o, t0, t_end + 0.3)                                   # 목 구멍으로 빠져 들어간 뒤에 숨김
    o.location = (RT * 0.6 * math.cos(a0), RT * 0.6 * math.sin(a0), ZT + 0.35); o.keyframe_insert("location", frame=st.fr(t0))
    steps = 14
    for s_ in range(steps + 1):
        p = s_ / steps
        r = (RT - BR - 0.004) * (1 - p) + (RB - BR * 0.4) * p
        z = ZT - (ZT - ZB) * p + BR * 0.8
        a = a0 + turns * 2 * math.pi * (p ** 0.8)
        o.location = (r * math.cos(a), r * math.sin(a), z)
        o.keyframe_insert("location", frame=st.fr(t0 + 0.4 + dur * (p ** 1.3)))
    # 목 → 주둥이 안으로 빨려 들어감(작아지며 아래로) — 허공에서 꺼지지 않게
    o.scale = (1, 1, 1); o.keyframe_insert("scale", frame=st.fr(t_end))
    o.location = (0, 0, ZB - SP * 0.6); o.keyframe_insert("location", frame=st.fr(t_end + 0.28))
    o.scale = (0.55, 0.55, 0.55); o.keyframe_insert("scale", frame=st.fr(t_end + 0.28))

# 나오는 회색 구슬: «평균적인»에 한 번(작게), «제일 무난한»에 본 구슬 — 본 구슬은 앞으로 굴러 회색 줄 가운데로
Y_ROW = -0.30
row = []
for k, x in enumerate([-0.40, -0.30, -0.20, -0.10, 0.10, 0.20, 0.30, 0.40]):
    o = ball(grey); o.location = (x, Y_ROW, BR); row.append(o)
    st.show(o, -1)


def out_ball(t, roll_to):
    o = ball(grey)
    st.show(o, t)
    z_end = ZB - SP
    pts = [(t, (0, 0, z_end + 0.02)), (t + 0.18, (0, 0, z_end - 0.03)), (t + 0.40, (0, -0.02, BR))]
    for tt, p in pts:
        o.location = p; o.keyframe_insert("location", frame=st.fr(tt))
    for tt, p in roll_to:
        o.location = p; o.keyframe_insert("location", frame=st.fr(tt))
    # 굴러감 = x 축 회전(앞으로)
    last = roll_to[-1][1]
    dist = math.hypot(last[0], last[1] + 0.02)
    o.rotation_euler = (0, 0, 0); o.keyframe_insert("rotation_euler", frame=st.fr(t + 0.40))
    o.rotation_euler = (-dist / BR, 0, 0); o.keyframe_insert("rotation_euler", frame=st.fr(roll_to[-1][0]))
    return o


first = out_ball(t_avg + 0.1, [(t_avg + 1.0, (-0.06, -0.12, BR))])
main = out_ball(t_pick + 0.2, [(t_pick + 1.3, (0.02, -0.14, BR)), (t_biz + 0.2, (0.02, -0.15, BR)), (t_mem + 0.1, (0.0, Y_ROW, BR))])
# 첫 구슬도 줄 쪽으로 밀려 들어감(안 남음)
first.location = (-0.06, -0.12, BR); first.keyframe_insert("location", frame=st.fr(t_biz + 0.3))
first.location = (-0.50, Y_ROW, BR); first.keyframe_insert("location", frame=st.fr(t_mem + 0.3))
st.anchor("main", main)

st.camera([
    {"t": -st.pre, "pos": [0.10, -0.42, 0.62], "look": [0.0, 0.0, 0.46], "lens": 45, "fstop": 2.8, "focus": [0, 0, 0.46]},
    {"t": t_world - 0.1, "pos": [0.05, -0.46, 0.60], "look": [0.0, 0.0, 0.44], "lens": 45, "fstop": 2.8, "focus": [0, 0, 0.44]},
    {"t": t_world + 1.3, "pos": [0.22, -0.88, 0.46], "look": [0.0, 0.0, 0.31], "lens": 35, "fstop": 4.0, "focus": [0, 0, 0.32]},
    {"t": t_biz - 0.1, "pos": [0.22, -1.00, 0.50], "look": [0.0, -0.08, 0.22], "lens": 40, "fstop": 4.0, "focus": [0, -0.1, 0.15]},
    {"t": t_mem + 0.2, "pos": [0.05, -0.85, 0.16], "look": [0.0, Y_ROW, 0.03], "lens": 55, "fstop": 2.4, "focus": [0, Y_ROW, 0.02]},
    {"t": st.dur + st.post, "pos": [0.06, -0.80, 0.15], "look": [0.0, Y_ROW, 0.03], "lens": 55, "fstop": 2.4, "focus": [0.25, Y_ROW, 0.02]},
])
st.run()
