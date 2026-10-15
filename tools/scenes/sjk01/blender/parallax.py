# -*- coding: utf-8 -*-
"""사진 + 깊이 지도 → 변위 메시(2.5D) → 블렌더 카메라 이동 렌더. 사진 색은 그대로(발광 셰이더, Standard 색 변환).

    blender -b -P parallax.py -- <spec.json>

spec = {
  "image": "소재/…png", "depth": "_tmp/sjk01/depth/….npy",   (저장소 기준 상대 경로 가능)
  "hfov": 60, "near": 2.5, "far": 70, "grid": [480, 320],
  "fps_num": 60000, "fps_den": 1001, "t0": 0.0, "t1": 6.5,          # 렌더할 구간(초) — 키 시각과 같은 시계
  "keys": [{"t": 0, "pos": [px, py, k], "look": [px, py], "lens": 33, "dx": 0, "dz": 0}],
        # pos = 사진 픽셀(px,py) 쪽 3D 점까지 거리의 k 배만큼 다가간 자리(+dx·dz 미터), look = 바라볼 픽셀
  "out": "_tmp/sjk01/blender/op_a"                                     # PNG 연번(f_00001.png …)
}
"""
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[4]
spec = json.load(open(sys.argv[sys.argv.index("--") + 1], encoding="utf-8"))
P = lambda p: str(p if Path(p).is_absolute() else ROOT / p)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
img = bpy.data.images.load(P(spec["image"]))
W, H = img.size
D = np.load(P(spec["depth"]))
if spec.get("depth_blur"):                 # 깊이 경계 계단(톱니) 줄이기 — 상자 흐림 여러 번(≈가우스)
    r = int(spec["depth_blur"])
    for _ in range(3):
        c = np.cumsum(np.pad(D, ((r + 1, r), (0, 0)), mode="edge"), 0); D = (c[2 * r + 1:] - c[:-2 * r - 1]) / (2 * r + 1)
        c = np.cumsum(np.pad(D, ((0, 0), (r + 1, r)), mode="edge"), 1); D = (c[:, 2 * r + 1:] - c[:, :-2 * r - 1]) / (2 * r + 1)
near, far = spec.get("near", 2.5), spec.get("far", 70.0)
tanh = math.tan(math.radians(spec.get("hfov", 60)) / 2)
inv = D * (1 / near - 1 / far) + 1 / far          # 상대 깊이(가까울수록 큼) → 1/거리
dist = 1.0 / inv


def ray(px, py):
    return Vector((tanh * (2 * px / W - 1), 1.0, tanh * (H / W) * (1 - 2 * py / H)))


def pix3d(px, py):
    x = min(W - 1, max(0, int(px))); y = min(H - 1, max(0, int(py)))
    return ray(px, py) * float(dist[y, x])


# 메시
gx, gy = spec.get("grid", [480, 320])
verts, uvs, faces = [], [], []
for j in range(gy + 1):
    for i in range(gx + 1):
        px, py = i / gx * (W - 1), j / gy * (H - 1)
        verts.append(tuple(pix3d(px, py)))
        uvs.append((i / gx, 1 - j / gy))
for j in range(gy):
    for i in range(gx):
        a = j * (gx + 1) + i
        faces.append((a, a + 1, a + gx + 2, a + gx + 1))
me = bpy.data.meshes.new("photo"); me.from_pydata(verts, [], faces); me.update()
uvl = me.uv_layers.new(name="uv")
for poly in me.polygons:
    for li in poly.loop_indices:
        uvl.data[li].uv = uvs[me.loops[li].vertex_index]
ob = bpy.data.objects.new("photo", me); sc.collection.objects.link(ob)
m = bpy.data.materials.new("photo"); m.use_nodes = True
nt = m.node_tree; nt.nodes.clear()
tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img; tex.interpolation = "Cubic"
em = nt.nodes.new("ShaderNodeEmission"); outn = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(tex.outputs["Color"], em.inputs["Color"]); nt.links.new(em.outputs["Emission"], outn.inputs["Surface"])
me.materials.append(m)

# 카메라
cam = bpy.data.cameras.new("cam"); cam.sensor_width = 36; cam.clip_start = 0.05; cam.clip_end = 500
co = bpy.data.objects.new("cam", cam); sc.collection.objects.link(co); sc.camera = co
tgt = bpy.data.objects.new("tgt", None); sc.collection.objects.link(tgt)
c = co.constraints.new("TRACK_TO"); c.target = tgt; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"

fps = spec.get("fps_num", 60000) / spec.get("fps_den", 1001)
sc.render.fps = 60; sc.render.fps_base = 1.001
f0 = round(spec["t0"] * fps)
for k in spec["keys"]:
    fr = round(k["t"] * fps) - f0 + 1
    px, py, kk = k["pos"]
    p = pix3d(px, py) * kk + Vector((k.get("dx", 0), 0, k.get("dz", 0)))
    co.location = p; co.keyframe_insert("location", frame=fr)
    lp = pix3d(*k["look"])
    tgt.location = lp; tgt.keyframe_insert("location", frame=fr)
    cam.lens = k.get("lens", 33); cam.keyframe_insert("lens", frame=fr)
for o in (co, tgt, cam):
    ad = o.animation_data
    if ad and ad.action:
        try:
            curves = ad.action.fcurves
        except AttributeError:   # 5.x 레이어드 액션
            curves = [fc for l in ad.action.layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves]
        for fc in curves:
            for kp in fc.keyframe_points:
                kp.interpolation = "BEZIER"; kp.easing = "AUTO"
                kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"

n = round(spec["t1"] * fps) - f0
sc.frame_start, sc.frame_end = 1, n
for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
    try:
        sc.render.engine = eng; break
    except TypeError:
        pass
try:
    sc.eevee.taa_render_samples = 16
except AttributeError:
    pass
sc.render.use_motion_blur = True
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.view_settings.view_transform = "Standard"
sc.render.image_settings.file_format = "PNG"
out = Path(P(spec["out"])); out.mkdir(parents=True, exist_ok=True)
sc.render.filepath = str(out / "f_")
if spec.get("track"):                      # 사진 픽셀 → 프레임마다 화면 좌표(html 글 얹기용)
    from bpy_extras.object_utils import world_to_camera_view
    pts = [pix3d(px, py) for px, py in spec["track"]]
    tr = []
    for f in range(1, n + 1):
        sc.frame_set(f)
        row = []
        for v in pts:
            q = world_to_camera_view(sc, co, v); row.append([round(q.x * 1920, 1), round((1 - q.y) * 1080, 1)])
        tr.append(row)
    (out / "track.js").write_text("window.TRACK = " + json.dumps(tr) + ";\n", encoding="utf-8")
bpy.ops.render.render(animation=True)
print("완료", n, "프레임 →", out)
