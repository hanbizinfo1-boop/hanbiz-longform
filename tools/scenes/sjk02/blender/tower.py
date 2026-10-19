# -*- coding: utf-8 -*-
"""s45 «매출 3천만 → 다 빠져요» — 스테인리스 계산대 위 나무 블록 탑(연출설계의 폭포 차트를 3D 로).
탑 = 매출 3,000만. 위에서부터 비용 블록이 하나씩 빠져 오른쪽에 회색 막대 줄로 선다(비용 막대 그래프가 됨).
마지막에 탑에 남은 맨 아래 블록(수익 300만)만 주홍. 숫자·이름표는 html(s45.html)이 proj.js 로 얹는다.

    blender -b -P tower.py -- [--still τ] [--frames a:b]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bl_common as B  # noqa: E402
import bpy  # noqa: E402

st = B.Stage(45, "s45")
U = 0.00018                     # 만 원당 높이(m) — 3,000만 = 0.54 m
W = 0.12
# 아래 → 위 (이름, 만 원, 빠지는 낱말)
STACK = [("수익", 300, None), ("가스비", 90, ("가스비", 0)), ("전기세", 90, ("전기세", 0)), ("광고비", 120, ("광고비", 0)),
         ("수수료", 300, ("수수료에", 0)), ("인건비", 750, ("인건비", 0)), ("월세", 300, ("월세", 0)), ("재료비", 1050, ("재료비", 0))]
# 빠진 블록이 서는 자리(x) — 광고·전기·가스는 같은 자리에 쌓임
SLOT = {"재료비": 0.24, "월세": 0.42, "인건비": 0.60, "수수료": 0.78, "광고비": 0.96, "전기세": 0.96, "가스비": 0.96}

st.counter("steel", wall="p59_shop_wall", wall_dist=1.6, wall_bright=0.45)
st.lights(warm=True)

t_build = 0.30
blocks, z = [], 0.0
for i, (nm, v, cue) in enumerate(STACK):
    h = v * U
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.object; o.name = nm; o.scale = (W, W, h - 0.0015)
    bv = o.modifiers.new("bv", "BEVEL"); bv.width = 0.004; bv.segments = 3
    m = st.wood_block_mat("m_" + nm); o.data.materials.append(m)
    blocks.append({"o": o, "nm": nm, "h": h, "z": z, "cue": cue, "m": m})
    # 쌓기: 위에서 떨어져 앉음(아래부터 0.09초 간격)
    t0 = t_build + 0.09 * i
    st.key(o, "location", [(t0, (0, 0, z + h / 2 + 0.35)), (t0 + 0.22, (0, 0, z + h / 2))])
    st.show(o, t0)
    z += h
TOP0 = z

stacked_on = {}       # 같은 자리에 쌓인 높이
pulls = []
for b in reversed(blocks):             # 위에서부터 빠짐
    if not b["cue"]:
        continue
    t = st.at(*b["cue"])
    o, h = b["o"], b["h"]
    x = SLOT[b["nm"]]; base = stacked_on.get(x, 0.0); stacked_on[x] = base + h
    zc = b["z"] + h / 2
    st.key(o, "location", [(t, (0, 0, zc)), (t + 0.22, (0.15, 0, zc + 0.01)), (t + 0.55, (x, 0, base + h / 2))])
    # 회색으로 빠짐
    mx = b["m"].node_tree.nodes["Mix"]
    sock = mx.inputs[6]
    sock.default_value = (*B.Stage.srgb("#D9B98C"), 1); sock.keyframe_insert("default_value", frame=st.fr(t + 0.2))
    sock.default_value = (*B.Stage.srgb("#8E959B"), 1); sock.keyframe_insert("default_value", frame=st.fr(t + 0.6))
    pulls.append((t, b))
    st.anchor("b_" + b["nm"], (lambda o=o, h=h: o.matrix_world.translation + B.Vector((0, 0, h / 2 + 0.01))))

# 남은 수익 블록 → 주홍
last_t = max(t for t, _ in pulls)
pm = blocks[0]["m"].node_tree.nodes["Mix"].inputs[6]
pm.default_value = (*B.Stage.srgb("#D9B98C"), 1); pm.keyframe_insert("default_value", frame=st.fr(last_t + 0.5))
pm.default_value = (*B.Stage.srgb("#F05A28"), 1); pm.keyframe_insert("default_value", frame=st.fr(last_t + 0.9))


def top():
    zz = 0.0
    for b in blocks:
        p = b["o"].matrix_world.translation
        if abs(p.x) < 0.02:
            zz = max(zz, p.z + b["h"] / 2)
    return B.Vector((0, 0, zz + 0.012))


st.anchor("top", top)
st.anchor("base", lambda: B.Vector((0, 0, 0)))

t_num, t_but, t_mat = st.at("숫자만"), st.at("근데"), st.at("재료비")
st.camera([   # 10-19: 탑 꼭대기·숫자가 화면 위로 잘려 위로 여유
    {"t": -st.pre, "pos": [0.70, -1.55, 0.58], "look": [0.30, 0.0, 0.32], "lens": 36, "fstop": 4.0, "focus": [0, 0, 0.3]},
    {"t": t_num - 0.1, "pos": [0.58, -1.45, 0.56], "look": [0.20, 0.0, 0.33], "lens": 36, "fstop": 4.0, "focus": [0, 0, 0.3]},
    {"t": t_num + 0.9, "pos": [0.18, -0.95, 0.06], "look": [0.0, 0.0, 0.36], "lens": 26, "fstop": 3.2, "focus": [0, 0, 0.3]},
    {"t": t_but - 0.05, "pos": [0.14, -0.92, 0.07], "look": [0.0, 0.0, 0.37], "lens": 26, "fstop": 3.2, "focus": [0, 0, 0.3]},
    {"t": t_mat - 0.15, "pos": [0.62, -1.55, 0.58], "look": [0.48, 0.0, 0.20], "lens": 38, "fstop": 4.0, "focus": [0.45, 0, 0.15]},
    {"t": st.dur + st.post, "pos": [0.56, -1.45, 0.52], "look": [0.48, 0.0, 0.18], "lens": 38, "fstop": 4.0, "focus": [0.45, 0, 0.15]},
])
st.run()
