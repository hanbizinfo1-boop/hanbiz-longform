# -*- coding: utf-8 -*-
"""성제관02 블렌더 은유 기계(R3 — Economist 식) 공용: 계산대 위 미니어처 무대 · 카메라 키 · 화면 좌표 내보내기.
단색 배경 금지 → 계산대 바닥(나무 사진·스테인리스) + 뒤에 흐린 주방 사진 벽. 글은 굽지 않고 proj.js 로 html 이 얹는다.
장면 스크립트(coins.py·funnel.py·tower.py·tanks.py)가 import 한다:  sys.path 에 이 폴더를 넣고 `import bl_common as B`.
"""
import json
import math
import sys
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[4]
DATA = Path(__file__).resolve().parents[1] / "data"
FPS = 60000 / 1001


def scene_data(n):
    t = (DATA / f"s{n:02d}.js").read_text(encoding="utf-8")
    return json.loads(t[t.index("{"):t.rindex("}") + 1])


def at(d, word, nth=0, end=False, exact=False):
    k = 0
    for l in d["lines"]:
        for w in l["words"]:
            ww = w["w"].strip(".,?!'\"")
            if (ww == word) if exact else (word in w["w"]):
                if k == nth:
                    return w["t1"] if end else w["t0"]
                k += 1
    raise KeyError(word)


class Stage:
    def __init__(self, n, out):
        self.d = scene_data(n)
        self.pre, self.dur, self.post = self.d["pre"], self.d["dur"], self.d["post"]
        self.NF = int(round((self.pre + self.dur + self.post) * FPS)) + 1
        self.out = ROOT / "_tmp/sjk02/blender" / out
        self.out.mkdir(parents=True, exist_ok=True)
        argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
        self.still = float(argv[argv.index("--still") + 1]) if "--still" in argv else None
        self.frames = argv[argv.index("--frames") + 1] if "--frames" in argv else None
        self.anchors = {}
        bpy.ops.wm.read_factory_settings(use_empty=True)
        sc = self.sc = bpy.context.scene
        for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
            try:
                sc.render.engine = eng; break
            except TypeError:
                pass
        sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
        sc.render.fps, sc.render.fps_base = 60000, 1001
        sc.frame_start, sc.frame_end = 1, self.NF
        sc.render.image_settings.file_format = "PNG"; sc.render.image_settings.color_mode = "RGB"
        sc.view_settings.view_transform = "AgX"
        try:
            sc.view_settings.look = "AgX - Medium High Contrast"
        except TypeError:
            pass
        sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.5
        ee = sc.eevee
        for a, v in (("taa_render_samples", 48), ("use_shadows", True), ("use_raytracing", True), ("shadow_ray_count", 2), ("shadow_step_count", 8)):
            if hasattr(ee, a):
                setattr(ee, a, v)
        wd = bpy.data.worlds.new("w"); sc.world = wd; wd.use_nodes = True
        bg = wd.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.20, 0.21, 0.22, 1); bg.inputs[1].default_value = 0.5

    def at(self, word, nth=0, end=False, exact=False):
        return at(self.d, word, nth, end, exact)

    def fr(self, tau):
        return (tau + self.pre) * FPS + 1

    # ── 재질
    @staticmethod
    def srgb(h):
        h = h.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)

    def mat(self, name, col, rough=0.45, metal=0.0, emit=None, es=0.0, alpha=1.0, trans=0.0, ior=1.45, coat=0.0):
        m = bpy.data.materials.new(name); m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (*(self.srgb(col) if isinstance(col, str) else col), 1)
        b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
        if trans:          # EEVEE 굴절 유리는 거울처럼 깨짐 → 반투명 + 맑은 코트(얇은 유리 느낌)
            b.inputs["Alpha"].default_value = 0.08 if trans >= 1 else 1 - 0.5 * trans
            b.inputs["Coat Weight"].default_value = 1.0; b.inputs["Coat Roughness"].default_value = 0.03
            b.inputs["Specular IOR Level"].default_value = 0.8
            if hasattr(m, "surface_render_method"):
                m.surface_render_method = "BLENDED"
            m.use_backface_culling = False
        if coat:
            b.inputs["Coat Weight"].default_value = coat
        if emit:
            b.inputs["Emission Color"].default_value = (*(self.srgb(emit) if isinstance(emit, str) else emit), 1)
            b.inputs["Emission Strength"].default_value = es
        if alpha < 1:
            b.inputs["Alpha"].default_value = alpha
        return m

    def wood_block_mat(self, name, tint="#D9B98C"):
        """나무 블록: 사진 결 대신 노이즈 결(장면마다 같은 사진 반복을 피함)."""
        m = self.mat(name, tint, rough=0.55)
        nt = m.node_tree; b = nt.nodes["Principled BSDF"]
        tc = nt.nodes.new("ShaderNodeTexCoord"); wv = nt.nodes.new("ShaderNodeTexWave")
        wv.wave_type = "RINGS"; wv.inputs["Scale"].default_value = 6; wv.inputs["Distortion"].default_value = 6
        nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"
        mx.inputs["Factor"].default_value = 0.18
        mx.inputs[6].default_value = (*self.srgb(tint), 1)
        nt.links.new(wv.outputs["Color"], mx.inputs[7]); nt.links.new(mx.outputs[2], b.inputs["Base Color"])
        return m

    # ── 무대: 바닥 + 뒤 벽 사진
    def counter(self, kind="wood", wall="p26_dawn_tile_wall", size=(4.0, 3.0), wall_dist=2.2, wall_h=2.4, wall_bright=0.55):
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
        o = bpy.context.object; o.scale = (size[0], size[1], 1); o.name = "counter"
        if kind == "wood":
            m = bpy.data.materials.new("counter"); m.use_nodes = True; nt = m.node_tree
            b = nt.nodes["Principled BSDF"]; b.inputs["Roughness"].default_value = 0.5
            im = nt.nodes.new("ShaderNodeTexImage"); im.image = bpy.data.images.load(str(ROOT / "소재/sjk02/codex/n09_wood_counter.png"))
            nt.links.new(im.outputs[0], b.inputs["Base Color"])
        elif kind == "steel":
            m = self.mat("counter", "#B9BEC2", rough=0.28, metal=1.0)
            nt = m.node_tree; b = nt.nodes["Principled BSDF"]
            ns = nt.nodes.new("ShaderNodeTexNoise"); ns.inputs["Scale"].default_value = 180; ns.inputs["Detail"].default_value = 4
            tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1, 40, 1)
            nt.links.new(tc.outputs["Object"], mp.inputs[0]); nt.links.new(mp.outputs[0], ns.inputs["Vector"])
            rm = nt.nodes.new("ShaderNodeMapRange"); rm.inputs["To Min"].default_value = 0.38; rm.inputs["To Max"].default_value = 0.55   # 10-19 반사가 하얗게 날아가 거칠게
            nt.links.new(ns.outputs["Fac"], rm.inputs["Value"]); nt.links.new(rm.outputs["Result"], b.inputs["Roughness"])
        else:
            m = bpy.data.materials.new("counter"); m.use_nodes = True; nt = m.node_tree
            im = nt.nodes.new("ShaderNodeTexImage"); im.image = bpy.data.images.load(str(ROOT / "소재/sjk02/codex/t_dark_desk.png"))
            nt.links.new(im.outputs[0], nt.nodes["Principled BSDF"].inputs["Base Color"])
        o.data.materials.append(m)
        if wall:
            bpy.ops.mesh.primitive_plane_add(size=1, location=(0, wall_dist, wall_h / 2 - 0.2), rotation=(math.radians(90), 0, 0))
            w = bpy.context.object; w.scale = (wall_h * 1.5 * 1.6, wall_h * 1.6, 1); w.name = "wall"
            wm = bpy.data.materials.new("wall"); wm.use_nodes = True; nt = wm.node_tree
            for n in list(nt.nodes):
                if n.type == "BSDF_PRINCIPLED":
                    nt.nodes.remove(n)
            im = nt.nodes.new("ShaderNodeTexImage"); im.image = bpy.data.images.load(str(ROOT / f"소재/sjk02/codex/{wall}.png"))
            em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = wall_bright
            nt.links.new(im.outputs[0], em.inputs[0]); nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs[0])
            w.data.materials.append(wm)

    def lights(self, warm=True, key=180, fill=50):
        bpy.ops.object.light_add(type="AREA", location=(-1.2, -0.8, 2.0))
        a = bpy.context.object; a.data.energy = key; a.data.size = 1.8; a.data.color = (1.0, 0.9, 0.8) if warm else (0.92, 0.96, 1.0)
        a.rotation_euler = (math.radians(35), math.radians(-35), 0)
        bpy.ops.object.light_add(type="AREA", location=(1.6, -1.4, 1.2))
        f = bpy.context.object; f.data.energy = fill; f.data.size = 2.5; f.data.color = (0.82, 0.9, 1.0)
        f.rotation_euler = (math.radians(-55), math.radians(45), 0)
        bpy.ops.object.light_add(type="AREA", location=(0.3, 1.4, 1.6))
        r = bpy.context.object; r.data.energy = 90; r.data.size = 1.0
        r.rotation_euler = (math.radians(-40), 0, 0)

    def camera(self, keys):
        cd = bpy.data.cameras.new("cam"); cam = bpy.data.objects.new("cam", cd); self.sc.collection.objects.link(cam); self.sc.camera = cam
        tgt = bpy.data.objects.new("tgt", None); self.sc.collection.objects.link(tgt)
        foc = bpy.data.objects.new("foc", None); self.sc.collection.objects.link(foc)
        tr = cam.constraints.new("TRACK_TO"); tr.target = tgt; tr.track_axis = "TRACK_NEGATIVE_Z"; tr.up_axis = "UP_Y"
        cd.dof.use_dof = True; cd.dof.focus_object = foc; cd.sensor_width = 36; cd.clip_start = 0.01
        for k in keys:
            f = self.fr(k["t"])
            cam.location = k["pos"]; cam.keyframe_insert("location", frame=f)
            tgt.location = k["look"]; tgt.keyframe_insert("location", frame=f)
            foc.location = k.get("focus") or k["look"]; foc.keyframe_insert("location", frame=f)
            cd.lens = k.get("lens", 50); cd.keyframe_insert("lens", frame=f)
            cd.dof.aperture_fstop = k.get("fstop", 4.0); cd.dof.keyframe_insert("aperture_fstop", frame=f)
        self.cam = cam
        return cam

    # ── 키 도우미
    def key(self, o, path, keys, index=-1, interp=None):
        """keys=[(τ, 값)] — 값은 스칼라(index 지정) 또는 벡터."""
        for t, v in keys:
            if index >= 0:
                getattr(o, path)[index] = v
            else:
                setattr(o, path, v)
            o.keyframe_insert(path, index=index, frame=self.fr(t))

    def show(self, o, t_on, t_off=None):
        o.hide_render = True; o.keyframe_insert("hide_render", frame=1)
        o.hide_render = False; o.keyframe_insert("hide_render", frame=max(1, int(self.fr(t_on))))
        if t_off is not None:
            o.hide_render = True; o.keyframe_insert("hide_render", frame=int(self.fr(t_off)))

    def anchor(self, name, obj_or_fn):
        """화면 좌표를 내보낼 점: 물체(위치) 또는 함수(→ Vector)."""
        self.anchors[name] = obj_or_fn

    # ── 렌더 + proj.js
    def run(self):
        sc = self.sc
        proj = {}
        if self.anchors:
            for f in range(1, self.NF + 1):
                sc.frame_set(f)
                row = {}
                for n, a in self.anchors.items():
                    p = a() if callable(a) else a.matrix_world.translation
                    v = world_to_camera_view(sc, self.cam, Vector(p))
                    row[n] = [round(v.x * 1920, 1), round((1 - v.y) * 1080, 1), round(v.z, 3)]
                proj[f] = row
            (self.out / "proj.js").write_text("window.PROJ = " + json.dumps(proj, separators=(",", ":")) + ";\n", encoding="utf-8")
        if self.still is not None:
            sc.frame_set(int(round(self.fr(self.still))))
            sc.render.filepath = str(self.out / f"still_{self.still:.2f}.png")
            bpy.ops.render.render(write_still=True)
        else:
            a, b = (int(x) for x in self.frames.split(":")) if self.frames else (1, self.NF)
            sc.frame_start, sc.frame_end = a, b
            sc.render.filepath = str(self.out / "f####")
            bpy.ops.render.render(animation=True)
        print("STAGE_DONE", self.NF)
