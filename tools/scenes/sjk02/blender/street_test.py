# -*- coding: utf-8 -*-
"""성제관02 ★1 오프닝 — 블렌더 절차 모델 밤 상가 거리 «실사 느낌» 시험(한 장).
    blender -b -P street_test.py -- <출력.png>
지시서: 실사 느낌이 안 나오면 그 장면만 Codex 사진 + 카메라 움직임으로 대체.
"""
import math
import random
import sys

import bpy

out = sys.argv[sys.argv.index("--") + 1]
random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene


def mat(name, color, rough=0.6, metal=0.0, emit=None, es=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = es
    return m


def box(name, loc, size, m):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object; o.name = name; o.scale = (size[0] / 2, size[1] / 2, size[2] / 2); o.data.materials.append(m)
    return o


# 젖은 아스팔트 — 노이즈로 물웅덩이(거칠기 낮음)
road = bpy.data.materials.new("road"); road.use_nodes = True
nt = road.node_tree; b = nt.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.025, 0.025, 0.028, 1)
nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.35
cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].position = 0.45; cr.color_ramp.elements[1].position = 0.6
cr.color_ramp.elements[0].color = (0.04, 0.04, 0.04, 1); cr.color_ramp.elements[1].color = (0.55, 0.55, 0.55, 1)
nt.links.new(nz.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], b.inputs["Roughness"])
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0)); g = bpy.context.object; g.scale = (40, 120, 1); g.data.materials.append(road)

conc = mat("conc", (0.18, 0.17, 0.16), 0.85)
shut = mat("shutter", (0.32, 0.33, 0.34), 0.35, 0.8)
sign = mat("sign", (0.05, 0.05, 0.06), 0.4)
win_d = mat("wind", (0.01, 0.012, 0.015), 0.1)
win_l = mat("winl", (0.0, 0.0, 0.0), 0.5, emit=(1.0, 0.75, 0.45), es=3.0)
glass = bpy.data.materials.new("glass"); glass.use_nodes = True
gb = glass.node_tree.nodes["Principled BSDF"]; gb.inputs["Transmission Weight"].default_value = 1.0; gb.inputs["Roughness"].default_value = 0.02
warm = mat("warm", (0.6, 0.45, 0.3), 0.7)

for side in (-1, 1):
    y = -60.0
    while y < 40:
        w = random.uniform(6, 9); h = random.uniform(7, 12)
        x0 = side * 7
        box("bld", (side * 11, y + w / 2, h / 2), (8, w - 0.2, h), conc)
        lit = side == 1 and abs(y + w / 2) < 4
        if lit:
            box("glass", (x0 - side * 0.05, y + w / 2, 1.6), (0.05, w - 1.2, 3.0), glass)
            box("room", (side * 9.5, y + w / 2, 1.6), (4.8, w - 1.4, 3.1), warm)
            L = bpy.data.lights.new("shop", "AREA"); L.energy = 2500; L.color = (1.0, 0.72, 0.45); L.size = 3
            lo = bpy.data.objects.new("shop", L); sc.collection.objects.link(lo); lo.location = (side * 9, y + w / 2, 2.9)
            lo.rotation_euler = (0, math.radians(-60 * side), 0)
        else:
            box("shutter", (x0 - side * 0.1, y + w / 2, 1.5), (0.06, w - 0.8, 3.0), shut)
        box("sign", (x0 - side * 0.25, y + w / 2, 3.8), (0.5, w - 0.6, 0.9), sign)
        for fz in range(1, int(h // 3)):
            for k in range(int(w // 2.2)):
                box("win", (x0 - side * 0.04, y + 1.2 + k * 2.2, 3 * fz + 2), (0.04, 1.4, 1.4), win_l if random.random() < 0.12 else win_d)
        y += w
    for py in range(-55, 40, 18):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=9, location=(side * 6.2, py, 4.5))
        bpy.context.object.data.materials.append(conc)

for py in (-40, -15, 15):
    L = bpy.data.lights.new("lamp", "POINT"); L.energy = 400; L.color = (0.75, 0.85, 1.0)
    o = bpy.data.objects.new("lamp", L); sc.collection.objects.link(o); o.location = (-5.5, py, 6.5)

world = bpy.data.worlds.new("w"); sc.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.006, 0.009, 0.02, 1)

cam = bpy.data.cameras.new("cam"); cam.lens = 32
co = bpy.data.objects.new("cam", cam); sc.collection.objects.link(co); sc.camera = co
co.location = (1.8, -30, 1.65)
d = (5 - 1.8, 0 + 30, 1.8 - 1.65)
co.rotation_euler = (math.radians(90) + math.atan2(d[2], math.hypot(d[0], d[1])), 0, -math.atan2(d[0], d[1]))
cam.dof.use_dof = True; cam.dof.focus_distance = 30; cam.dof.aperture_fstop = 2.8

sc.render.engine = "CYCLES"
pr = bpy.context.preferences.addons["cycles"].preferences; pr.compute_device_type = "OPTIX"; pr.get_devices()
for dv in pr.devices: dv.use = True
sc.cycles.device = "GPU"; sc.cycles.samples = 96; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
