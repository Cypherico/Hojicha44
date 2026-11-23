"""Hojicha44 render scene — Blender 5.2 headless.

Run:
  blender --background --python renders/scene.py -- \
      --samples 96 --res 1600x1000 --setups bright --shots hero,exploded

FRAME — everything is assembled in the **design frame** (x right, y up),
the frame of the committed plate DXF, the case STLs and the board STEP
export. KiCad stores the .kicad_pcb y-down; kicad-cli's STEP export
negates y (measured: Edge.Cuts y -60.00..54.63 -> glb y -54.63..60.00),
so board GLBs and the plate/case already share the design frame.
placements.json is converted (y -> -y); cutouts.json is a raw
transcription of the plate DXF.

REGISTRATION MASTER — the plate CUTOUT holes. The scene matches every
switch footprint to a plate hole and ABORTS if any is off by > 0.05 mm.
The caps, switch bodies and thumb rotations all come from the matched
hole (center + polygon angle), never from a separately-computed origin.

STACK (z=0 is the PCB top; thin-top round):
  PCB substrate           -1.60..0        (STEP top 1.60 shifted down)
  bottom gaskets          -1.55..1.00     (3.0 poron compressed to 2.55)
  plate                    1.00..2.20
  switch housing           0.00..4.32, slider crown 5.07
  top gaskets              2.20..3.20     (1.5 poron compressed to 1.00)
  KLP Normal_Tilted top    11.14          (~5.9 mm proud of the cover;
                                           thumbs wear the same family)
  top cover plate          3.20..5.20     (flat, no-indent; 0.4 chamfer
                                           on the outer-rim top edges)
  encoder = short-shaft EC11-class (tip 13.5, two-tone) under a low
  fluted alu knob (OD 16.8, H 9.2, crown ~15.3, skirt rim+0.9 so the
  0.8mm max push travel can never hit the cover)

COLOURWAY (round 4: "make it less bland"): warm-bone satin PBT caps,
mid-grey matte PLA case, near-black waxy POM plate, machined-metal knob
and encoder, gold traces on the nice!nano.

POSE: each half is splayed 5°, tented 6°, and moved outward 5 mm.
The bright studio views support each half with a single molded foot.
"""
import bpy
import sys
import math
import json
import os
import re
import argparse

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ASSETS = os.environ.get("H44_RENDER_ASSETS",
                        os.path.join(REPO, "generated", "renders", "assets"))
OUTROOT = os.path.join(REPO, "generated", "renders", "v0.5.1")

SCALE = 0.001            # design-frame mm -> Blender meters
PCB_TOP_IN_STEP = 1.60   # substrate top inside the kicad-cli STEP
PLATE_Z = 1.00           # plate underside above the PCB top (GAP)
CAP_STEM_Z = 1.5         # cap stem tip above the PCB top (inside switch)

# Offsets along each half's assembly axis, in millimetres.
EXPLODE = {"knob": 117.0, "caps": 102.0, "cover": 77.0,
           "swbodies": 53.0, "gaskets": 42.0, "plate": 42.0,
           "encoder": 14.0, "jack": 12.0,
           "foam": -25.0, "gaskets_b": -25.0, "tub": -50.0}
# nice!nano courtyard in the FOOTPRINT's local (file) frame, from the
# embedded Socket_Strips_2x12_P2.54mm_NiceNano footprint (KiCad 10)
NANO_COURT = (-17.07, -29.94, 2.85, 2.60)   # x0, y0, x1, y1


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--samples", type=int, default=96)
    p.add_argument("--res", default="2400x1500")
    p.add_argument("--setups", default="dark,bright")
    p.add_argument("--shots", default="hero,exploded,orbit,top")
    p.add_argument("--out", default=OUTROOT)
    p.add_argument("--device", default="metal", choices=["metal", "cpu"])
    p.add_argument("--pp", action="store_true",
                   help="photoreal post pipeline (render_pp.py: Cycles "
                        "bounce/clamp tuning + subtle bloom/fringing/"
                        "grain compositor)")
    p.add_argument("--colourway", default="bright",
                   choices=["bright", "dark", "play", "artisan"],
                   help="product colourway (renders/SHOTLIST.md): dark = "
                        "charcoal set on honed stone; play = multicolour caps; "
                        "artisan = bright + one sculpted accent cap")
    p.add_argument("--framecheck", action="store_true",
                   help="report NDC extents per camera, render nothing")
    p.add_argument("--stack-colors", action="store_true",
                   help="apply the diagram palette to the exploded shot")
    p.add_argument("--palette", action="store_true",
                   help="garish debug colors to verify assignments")
    p.add_argument("--hide-cover", action="store_true")
    p.add_argument("--hide-case", action="store_true")
    p.add_argument("--hide-plate", action="store_true")
    p.add_argument("--no-floor", action="store_true",
                   help="omit the studio floor (debug/compare)")
    return p.parse_args(argv)


def import_glb(path, prefix):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    objs = [o for o in bpy.data.objects if o not in before]
    roots = [o for o in objs if o.parent is None or o.parent not in objs]
    grp = bpy.data.collections.new(prefix)
    bpy.context.scene.collection.children.link(grp)
    for o in objs:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        grp.objects.link(o)
        o.scale = (SCALE, SCALE, SCALE)
    # Blender's glTF importer converts Y-up -> Z-up by rotating +90 deg
    # about X (measured: our design (x, y, z) lands at (x, -z, y)).
    # Counter-rotate the roots by -90 deg about X so the world returns to
    # the design frame. NOTE: imported objects use rotation_mode
    # QUATERNION, where rotation_euler writes are silently ignored.
    for r in roots:
        r.rotation_mode = "XYZ"
        r.rotation_euler.x -= math.pi / 2
    # setting scale/rotation does not refresh matrix_world; every bbox
    # measurement below depends on an evaluated transform
    bpy.context.view_layer.update()
    return grp, roots, objs


def bbox_mm(objs):
    """World-frame bbox (metres) of a group. Evaluates the dependency
    graph FIRST: callers mutate object locations (pose, explode) and
    matrix_world is lazy — without this a bbox measured right after a
    move reads the PREVIOUS transform (found when the exploded shot's
    move-back left the macro's knob reading +52mm stale)."""
    bpy.context.view_layer.update()
    import mathutils
    pts = []
    for o in objs:
        if o.type != "MESH":
            continue
        for corner in o.bound_box:
            pts.append(o.matrix_world @ mathutils.Vector(corner))
    xs = [p.x for p in pts]; ys = [p.y for p in pts]; zs = [p.z for p in pts]
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


def pbr(name, color, rough=0.5, metal=0.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    return mat


def micro_texture(mat, scale, bump, dist, rough_lo=None, rough_hi=None,
                  detail=3.5):
    """Procedural surface texture in generated (per-object 0..1) space.

    One noise drives a bump normal plus an optional roughness range. The
    rendered board is ~3 px/mm, so the scale is chosen for features that
    read at that size (0.5-3 mm), not for powder-grain detail. Idempotent:
    materials are shared between halves, so repeated calls are no-ops.
    """
    if mat.get("micro_texture"):
        return mat
    mat["micro_texture"] = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = detail
    noise.inputs["Roughness"].default_value = 0.55
    nt.links.new(tc.outputs["Generated"], noise.inputs["Vector"])
    bmp = nt.nodes.new("ShaderNodeBump")
    bmp.inputs["Strength"].default_value = bump
    bmp.inputs["Distance"].default_value = dist
    nt.links.new(noise.outputs["Fac"], bmp.inputs["Height"])
    nt.links.new(bmp.outputs["Normal"], bsdf.inputs["Normal"])
    if rough_lo is not None and rough_hi is not None:
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = 0.0
        mr.inputs["From Max"].default_value = 1.0
        mr.inputs["To Min"].default_value = rough_lo
        mr.inputs["To Max"].default_value = rough_hi
        nt.links.new(noise.outputs["Fac"], mr.inputs["Value"])
        nt.links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])
    return mat


def assign(objs, mat):
    """Materials apply to MESHES *and* FONT/CURVE objects — the round-11
    label fiasco: the type guard silently skipped every label, so two
    rounds of text-colour changes never reached the render (the labels
    shipped with Blender's default grey-white material)."""
    for o in objs:
        if o.type not in ("MESH", "FONT", "CURVE", "SURFACE", "META"):
            continue
        o.data.materials.clear()
        o.data.materials.append(mat)


def mesh_area_span(o):
    """Surface area (mm^2) and world-z thickness (mm) of one board layer
    solid. The glTF stores design millimetres as raw vertex units (object
    scale 0.001 turns them into metres), so the area is directly
    comparable to the STEP. NOTE: the mesh data stays Y-up (the importer
    rotates the object), so design thickness = world z span, not local z."""
    import mathutils
    area = sum(p.area for p in o.data.polygons)
    zs = [(o.matrix_world @ mathutils.Vector(c)).z for c in o.bound_box]
    return area, (max(zs) - min(zs)) * 1000.0


def materialize_pcb(objs):
    """Assign PCB materials by measured layer geometry, not by guesswork.

    kicad-cli emits the board as anonymous layer solids. Measured on the
    committed board: substrate 27.8k mm^2; top/bottom copper pours
    12.6k/12.4k on planes; silkscreen 206/63 mm^2 on planes; pad/via
    copper 1.5k/1.5k/211 mm^2 through the board thickness. The pours are
    rendered as black soldermask (their real appearance), the pad copper
    as ENIG gold, the sparse planes as white silk.
    """
    m_sub = pbr("pcb_substrate", (0.016, 0.026, 0.021), rough=0.45)
    m_mask = pbr("pcb_soldermask", (0.010, 0.010, 0.012), rough=0.32)
    m_cu = pbr("pcb_copper", (0.76, 0.60, 0.22), rough=0.26, metal=1.0)
    m_silk = pbr("pcb_silk", (0.86, 0.86, 0.83), rough=0.55)
    m_comp = pbr("pcb_component", (0.045, 0.045, 0.050), rough=0.35)
    m_diode = pbr("pcb_diode", (0.020, 0.020, 0.022), rough=0.25)
    # fine soldermask / substrate / silk grain; metal pads get only a
    # slight roughness break-up so the ENIG stays specular
    micro_texture(m_sub, 120, 0.25, 0.00006, 0.42, 0.50)
    micro_texture(m_mask, 180, 0.20, 0.00004, 0.28, 0.38)
    micro_texture(m_cu, 300, 0.10, 0.00002, 0.22, 0.30)
    micro_texture(m_silk, 300, 0.20, 0.00003, 0.50, 0.60)
    micro_texture(m_comp, 100, 0.15, 0.00004, 0.32, 0.40)
    micro_texture(m_diode, 200, 0.10, 0.00002, 0.22, 0.28)
    census = {}
    for o in objs:
        if o.type != "MESH":
            continue
        name = o.name
        if name.startswith("D_"):
            mat = m_diode
        elif name.startswith(("ENC_", "J_", "SW_")):
            mat = m_comp
        else:
            area, span = mesh_area_span(o)
            if area > 20000:
                mat = m_sub
            elif span < 0.2:
                # plane: the large pours are the soldermask, the sparse
                # ~50-200 mm^2 planes are silkscreen
                mat = m_mask if area > 5000 else m_silk
            else:
                mat = m_cu
            print(f"  [pcb] {name}: area {area:.1f} mm2, thickness "
                  f"{span:.3f} mm -> {mat.name}", flush=True)
        assign([o], mat)
        census[mat.name] = census.get(mat.name, 0) + 1
    print("  [pcb] material census:", census, flush=True)


def fp_to_design(ax, ay, rot_deg, lx, ly):
    """Footprint-local (KiCad file frame) -> design frame."""
    r = math.radians(rot_deg)
    c, s = math.cos(r), math.sin(r)
    return (ax + c * lx - s * ly, -(ay + s * lx + c * ly))


def smooth(objs, angle_deg=35.0):
    """Smooth shading for curved parts. Imported custom split normals are
    cleared first: the glTF exporter writes per-face normals from OCCT's
    split vertices, and those would override any smoothing we ask for."""
    meshes = [o for o in objs if o.type == "MESH"]
    if not meshes:
        return
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    for o in meshes:
        if o.data.has_custom_normals:
            bpy.context.view_layer.objects.active = o
            bpy.ops.mesh.customdata_custom_splitnormals_clear()
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.shade_smooth()
    try:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle_deg),
                                             keep_sharp_edges=True)
    except (AttributeError, TypeError):
        bpy.ops.object.shade_auto_smooth(angle=math.radians(angle_deg))


def move_exploded_layer(objs, dz):
    """Lift each root along its half's assembly axis."""
    for obj in objs:
        if obj.parent is None or obj.parent.name.startswith("pose_"):
            obj.location.z += dz
    bpy.context.view_layer.update()


def add_cube(name, loc, size, mat, rot_z=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = (size[0] * SCALE, size[1] * SCALE, size[2] * SCALE)
    o.rotation_euler.z = math.radians(rot_z)
    assign([o], mat)
    return o


def setup_world_and_lights(setup, cx, cy):
    world = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    lp = nt.nodes.new("ShaderNodeLightPath")
    mix = nt.nodes.new("ShaderNodeMixShader")
    bg_cam = nt.nodes.new("ShaderNodeBackground")
    bg_amb = nt.nodes.new("ShaderNodeBackground")
    if setup == "bright":
        bg_cam.inputs[0].default_value = (0.86, 0.88, 0.91, 1.0)
        bg_cam.inputs[1].default_value = 1.0
        # reflections/ambient: a bright studio wall the metal parts can see
        bg_amb.inputs[0].default_value = (0.80, 0.84, 0.90, 1.0)
        bg_amb.inputs[1].default_value = 0.40
    else:
        bg_cam.inputs[0].default_value = (0.004, 0.004, 0.005, 1.0)
        bg_cam.inputs[1].default_value = 1.0
        bg_amb.inputs[0].default_value = (0.22, 0.24, 0.27, 1.0)
        bg_amb.inputs[1].default_value = 0.22
    nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs["Fac"])
    nt.links.new(bg_amb.outputs[0], mix.inputs[1])
    nt.links.new(bg_cam.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])

    for o in list(bpy.data.objects):
        if o.type in {"LIGHT", "CAMERA"}:
            bpy.data.objects.remove(o, do_unlink=True)
    import mathutils

    def area(name, energy, size, loc, target, color=(1, 1, 1), shape="SQUARE"):
        li = bpy.data.lights.new(name, "AREA")
        li.energy = energy
        li.shape = shape
        li.size = size
        li.color = color
        o = bpy.data.objects.new(name, li)
        o.location = loc
        d = mathutils.Vector(target) - mathutils.Vector(loc)
        o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        bpy.context.collection.objects.link(o)

    if setup == "bright":
        area("key", 3, 1.0, (cx - 0.16, cy - 0.26, 0.40), (cx, cy, 0.0))
        area("fill", 0.8, 1.0, (cx + 0.34, cy - 0.16, 0.18),
             (cx, cy, 0.0), (0.82, 0.90, 1.0))
        area("rim", 2, 0.5, (cx + 0.02, cy + 0.34, 0.30), (cx, cy, 0.0))
        area("rim2", 0.6, 0.5, (cx - 0.36, cy + 0.18, 0.24), (cx, cy, 0.0))
    else:
        # Broad neutral key reveals the dishes; lower fill separates the case
        # from the stone, with a restrained warm reflection on the brass.
        area("dark_key", 2.85, 0.48, (cx - 0.28, cy - 0.20, 0.38),
             (cx, cy, 0.0), (1.0, 0.96, 0.91), shape="DISK")
        area("dark_fill", 1.35, 0.38, (cx + 0.35, cy - 0.10, 0.21),
             (cx, cy, 0.0), (0.81, 0.87, 1.0), shape="DISK")
        area("dark_rim", 1.9, 0.30, (cx + 0.08, cy + 0.30, 0.34),
             (cx, cy, 0.0), (1.0, 0.89, 0.73), shape="DISK")


def projected_bounds(cam, objects, res):
    """Return the screen-space bounds of the visible mesh vertices."""
    import numpy as np

    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    width, height = res
    projection = cam.evaluated_get(depsgraph).calc_matrix_camera(
        depsgraph, x=width, y=height)
    view = projection @ cam.matrix_world.inverted()
    lo, hi = np.full(2, np.inf), np.full(2, -np.inf)
    for source in objects:
        if source.type != "MESH" or source.hide_render:
            continue
        obj = source.evaluated_get(depsgraph)
        vertices = obj.data.vertices
        if not vertices:
            continue
        xyz = np.empty(len(vertices) * 3, dtype=np.float32)
        vertices.foreach_get("co", xyz)
        transform = np.asarray(view @ obj.matrix_world, dtype=np.float32)
        clip = xyz.reshape(-1, 3) @ transform.T[:3] + transform[:, 3]
        if (clip[:, 3] <= 0).any():
            raise ValueError(f"{cam.name}: {obj.name} crosses the camera plane")
        ndc = clip[:, :2] / clip[:, 3:4]
        lo = np.minimum(lo, ndc.min(axis=0))
        hi = np.maximum(hi, ndc.max(axis=0))
    return lo, hi


def frame_report(cam, objs, label, res, tol=1.0):
    try:
        lo, hi = projected_bounds(cam, objs, res)
    except ValueError as exc:
        print(f"[frame] {label}: {exc} - FAIL", flush=True)
        return False
    ok = bool((-tol <= lo).all() and (hi <= tol).all()
              and (lo <= hi).all())
    print(f"[frame] {label}: x [{lo[0]:+.3f},{hi[0]:+.3f}] "
          f"y [{lo[1]:+.3f},{hi[1]:+.3f}] "
          f"{'PASS' if ok else 'CLIPPED'}", flush=True)
    return ok


def center_subject(cam, objects, res):
    """Balance the projected silhouette while preserving the camera angle."""
    width, height = res
    lo, hi = projected_bounds(cam, objects, res)
    dx, dy = (lo + hi) / 2
    cam.data.shift_x += float(dx / 2)
    cam.data.shift_y += float(dy * height / (2 * width))
    lo, hi = projected_bounds(cam, objects, res)
    print(f"[center] {cam.name}: x {lo[0]:+.3f}..{hi[0]:+.3f}, "
          f"y {lo[1]:+.3f}..{hi[1]:+.3f}", flush=True)


def add_cam(name, loc, look_at, lens=50):
    cam = bpy.data.cameras.new(name)
    cam.lens = lens
    co = bpy.data.objects.new(name, cam)
    co.location = loc
    import mathutils
    direction = mathutils.Vector(look_at) - mathutils.Vector(loc)
    co.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.collection.objects.link(co)
    return co


def render_to(cam, path, res, samples, device="metal", pp=False):
    sc = bpy.context.scene
    sc.camera = cam
    sc.render.engine = "CYCLES"
    sc.render.use_persistent_data = True
    if pp:
        # render_pp: Cycles bounce/clamp realism + the photographic
        # compositor (5.2 quirks handled inside the module)
        try:
            import render_pp
            render_pp.tune_cycles(sc)
            render_pp.build_pp_chain(sc, res=res)
        except Exception as e:
            print(f"  (render_pp unavailable, base render: {e})",
                  flush=True)
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.render.film_transparent = False
    if device == "metal":
        try:
            prefs = bpy.context.preferences.addons["cycles"].preferences
            prefs.compute_device_type = "METAL"
            prefs.get_devices()
            for d in prefs.devices:
                d.use = True
            sc.cycles.device = "GPU"
        except Exception as e:
            print("  (GPU setup unavailable, CPU render):", e)
    else:
        sc.cycles.device = "CPU"
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.image_settings.file_format = "PNG"
    sc.render.filepath = path
    print(f"  rendering {os.path.basename(path)} ...", flush=True)
    bpy.ops.render.render(write_still=True)
    print("  wrote", path, flush=True)


def init_scene():
    """Empty scene + a Standard view transform (AgX + strong lights
    lifts near-black albedos toward white — colors must render as
    authored)."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    print("[scene] empty scene ready", flush=True)
    sc = bpy.context.scene
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.view_settings.exposure = 0.0
    sc.view_settings.gamma = 1.0


def materialize_ports(encoder, jack, half, metal_body, shaft, plastic, terminals):
    from mathutils import Vector

    if REPO not in sys.path:
        sys.path.append(REPO)
    from case.params import PORTS, TRRS_JACK_AXIS_Z

    assign([encoder], metal_body)
    encoder.data.materials.append(shaft)
    encoder.data.materials.append(plastic)
    xform = encoder.matrix_world
    inverse = xform.inverted()
    for v in encoder.data.vertices:
        pos = xform @ v.co
        if pos.z > 13.5 * SCALE:
            pos.z = 13.5 * SCALE
            v.co = inverse @ pos
    encoder.data.update()
    for face in encoder.data.polygons:
        pos = xform @ face.center
        normal = xform.to_3x3() @ face.normal
        if pos.z >= 8.9 * SCALE or pos.z < 0:
            face.material_index = 1
        elif pos.z < 5.7 * SCALE and abs(normal.z) > 0.0004:
            face.material_index = 2

    # Register the STEP bore to the case datum, and use the PCB pads
    # for terminals because the STEP model's terminal spacing differs.
    mouth_sign = 1 if half == "Left" else -1
    x, y = PORTS[half]["trrs"]
    mouth = Vector((x, y, TRRS_JACK_AXIS_Z)) * SCALE
    outward = Vector((mouth_sign, 0, 0))
    xform = jack.matrix_world
    front = max((xform @ v.co).dot(outward) for v in jack.data.vertices)
    jack.location += outward * (mouth.dot(outward) - front)
    bpy.context.view_layer.update()
    xform = jack.matrix_world
    inverse = xform.inverted()
    for v in jack.data.vertices:
        pos = xform @ v.co
        if pos.z < 0:
            pos.z = 0
            v.co = inverse @ pos
    jack.data.update()

    # A ray down the real bore must travel into the housing before hitting
    # anything. This catches a closed back face facing the seam.
    ray_start = mouth + outward * (0.3 * SCALE)
    local_outward = (inverse.to_3x3() @ outward).normalized()
    hit, point, _, _ = jack.ray_cast(inverse @ ray_start, -local_outward)
    if not hit or (xform @ point - ray_start).length < 3 * SCALE:
        raise RuntimeError(f"{jack.name} bore does not face the case opening")
    jack["bore_center"] = tuple(inverse @ mouth)
    jack["bore_outward"] = tuple(local_outward)

    assign([jack], plastic)
    jack.data.materials.append(terminals)
    for face in jack.data.polygons:
        pos = xform @ face.center
        radius = math.hypot(pos.y - mouth.y, pos.z - mouth.z)
        if (pos - mouth).dot(outward) > -0.9 * SCALE and radius < 2.2 * SCALE:
            face.material_index = 1

    from pathlib import Path
    generators = str(Path(REPO) / "pcb" / "generators")
    if generators not in sys.path:
        sys.path.insert(0, generators)
    from check_board import committed_pads

    board = Path(REPO) / "pcb" / "kicad" / f"Hojicha44-{half}.kicad_pcb"
    pins = [add_cube(f"{ref}_{pin}_terminal", (x * SCALE, -y * SCALE, -1.2 * SCALE),
                     (0.72, 0.42, 2.65), terminals)
            for ref, pin, x, y, *_ in committed_pads(board)
            if ref == jack.name and pin in ("T", "R1", "R2", "S")]
    if len(pins) != 4:
        raise RuntimeError(f"{jack.name} expected four plated terminal pads")
    return pins


def build_keyboard(args):
    """Assemble both halves at their posed positions: boards, plates,
    cases, caps, gaskets, nano proxies, truncated encoders, knobs and
    the presentation-pose empties. Returns (parts, all_objs); every
    object is parented to pose_L/pose_R. Shared by the studio scene and
    the desk-environment scene (scene_env.py)."""
    if REPO not in sys.path:
        sys.path.append(REPO)
    from case.params import KNOB_COVER_GAP, PWRSW_ACTUATOR_REST

    # Share the four source meshes across all 44 switch positions.
    choc_glb_path = os.path.join(ASSETS, "parts", "choc.glb")
    if not os.path.exists(choc_glb_path):
        sys.exit("[scene] ABORT missing assets/parts/choc.glb — "
                 "run: case/.venv/bin/python renders/build_assets.py")
    _, choc_roots, _ = import_glb(choc_glb_path, "choc_src")
    choc_sources = [(r.name, r.data, r.rotation_euler.copy(),
                     r.scale.copy())
                    for r in choc_roots if r.type == "MESH"]
    for _r in choc_roots:
        _r.hide_render = True
        _r.hide_set(True)

    # round 23: ALL SCREWS REMOVED — the design has none (magnets
    # hold the cover); round-20's "corner hardware" was invented from
    # a misread of the review and floated/hovered in every shot.

    placements = json.load(open(os.path.join(ASSETS, "placements.json")))
    cutouts = json.load(open(os.path.join(ASSETS, "cutouts.json")))
    lands = {h: json.load(open(os.path.join(
        REPO, "plate", f"Hojicha44-{h}-lands.json")))
        for h in ("Left", "Right")}

    # round 21: DETAIL-pass materials (materials_detail.py — multi-
    # signal: brightness wash + roughness RANGE + two bump octaves +
    # micro-structure per material) with the original pbr set as the
    # fallback. Detail materials are MARKED so the generic
    # micro_texture pass below skips them (no double-processing).
    try:
        import materials_detail as MD
        m_cap = MD.cap_pbt_v2("cap_pbt")
        m_case = MD.case_sintered_v2("case_pla")
        m_plate = MD.plate_pom_v2("plate_pom")
        m_knob = MD.alu_anodized_v2("knob_alu")
        m_enc_body = MD.alu_anodized_v2("enc_gunmetal")
        m_enc_shaft = MD.steel_shaft_v2("enc_steel")
        m_poron = MD.poron_v2("poron_pad")
        for m in (m_cap, m_case, m_plate, m_knob, m_enc_body,
                  m_enc_shaft, m_poron):
            m["micro_texture"] = True
        print("[scene] materials: DETAIL pass active (materials_detail)",
              flush=True)
    except Exception as e:
        print(f"  (materials_detail unavailable, base set: {e})",
              flush=True)
        m_cap = pbr("cap_pbt", (0.55, 0.525, 0.475), rough=0.42)
        m_poron = pbr("poron_pad", (0.40, 0.38, 0.36), rough=0.93)
        micro_texture(m_poron, 90, 0.5, 0.001, 0.88, 0.97, detail=3.0)
        m_case = pbr("case_pla", (0.30, 0.30, 0.315), rough=0.62)
        m_plate = pbr("plate_pom", (0.035, 0.036, 0.042), rough=0.14)
        m_knob = pbr("knob_alu", (0.72, 0.73, 0.75), rough=0.26,
                     metal=1.0)
        m_enc_body = pbr("enc_gunmetal", (0.16, 0.16, 0.175),
                         rough=0.30, metal=0.9)
        m_enc_shaft = pbr("enc_steel", (0.66, 0.67, 0.70), rough=0.20,
                          metal=1.0)
    switch_materials = {
        "base": pbr("choc_base", (0.45, 0.43, 0.37), rough=0.43),
        "housing": pbr("choc_housing", (0.70, 0.66, 0.55), rough=0.36),
        "stem": pbr("choc_stem", (0.08, 0.11, 0.13), rough=0.34),
        "contacts": pbr("choc_contacts", (0.61, 0.41, 0.22), rough=0.27, metal=0.9),
    }
    nano_materials = {
        "mask": pbr("nano_mask", (0.012, 0.014, 0.016), rough=0.53),
        "gold": pbr("nano_enig", (0.63, 0.43, 0.14), rough=0.29, metal=0.92),
        "traces": pbr("nano_mask_over_copper", (0.115, 0.082, 0.047), rough=0.58),
        "vias": pbr("nano_via_plating", (0.36, 0.24, 0.10), rough=0.42, metal=0.67),
        "shell": pbr("nano_usb_shell", (0.49, 0.51, 0.53), rough=0.29, metal=0.93),
        "tongue": pbr("nano_usb_tongue", (0.062, 0.060, 0.056), rough=0.43),
        "packages": pbr("nano_ic", (0.035, 0.034, 0.035), rough=0.48),
        "crystal": pbr("nano_crystal", (0.45, 0.47, 0.48), rough=0.35, metal=0.78),
        "ceramic": pbr("nano_mlcc", (0.35, 0.29, 0.20), rough=0.51),
        "smd_ends": pbr("nano_solder", (0.47, 0.48, 0.50), rough=0.34, metal=0.82),
        "socket": pbr("nano_socket", (0.027, 0.028, 0.030), rough=0.49),
    }
    power_frame = pbr("power_switch_frame", (0.16, 0.16, 0.17), rough=0.53)
    power_lever = pbr("power_switch_lever", (0.40, 0.04, 0.025), rough=0.54)
    micro_texture(nano_materials["mask"], 160, 0.15, 0.00002, 0.48, 0.59)
    micro_texture(nano_materials["packages"], 140, 0.18, 0.00003, 0.42, 0.55)
    micro_texture(m_cap, 42, 0.28, 0.00022, 0.36, 0.48, detail=5.0)
    micro_texture(m_case, 85, 0.40, 0.00055, 0.52, 0.68, detail=5.0)
    micro_texture(m_plate, 240, 0.10, 0.00002, 0.11, 0.17)
    micro_texture(m_knob, 300, 0.06, 0.000015, 0.22, 0.30)
    micro_texture(m_enc_body, 140, 0.18, 0.00004, 0.24, 0.34)
    micro_texture(m_enc_shaft, 260, 0.08, 0.00002, 0.16, 0.24)

    parts = {}
    for half in ("Left", "Right"):
        h = half[0]
        parts[h] = {}
        _, roots, objs = import_glb(os.path.join(
            ASSETS, "board", f"Hojicha44-{half}.glb"), f"board_{h}")
        for o in roots:
            o.location.z -= PCB_TOP_IN_STEP * SCALE
        bpy.context.view_layer.update()
        parts[h]["board"] = objs
        print(f"[scene] {half}: board imported ({len(objs)} objs)", flush=True)
        _, roots, objs = import_glb(os.path.join(
            ASSETS, "plate", f"Hojicha44-{half}.glb"), f"plate_{h}")
        for o in roots:
            o.location.z += PLATE_Z * SCALE
        bpy.context.view_layer.update()
        parts[h]["plate"] = objs
        for part in ("tub", "cover"):
            _, roots, objs = import_glb(os.path.join(
                ASSETS, "case", f"Hojicha44-{half}-{part}.glb"),
                f"{part}_{h}")
            parts[h][part] = objs

        materialize_pcb(parts[h]["board"])
        if args.palette:
            assign(parts[h]["plate"], pbr(f"dbg_plate_{h}",
                                          (0.1, 0.7, 0.2), rough=0.4))
            assign(parts[h]["tub"], pbr(f"dbg_tub_{h}",
                                        (0.2, 0.3, 0.9), rough=0.5))
            assign(parts[h]["cover"], pbr(f"dbg_cover_{h}",
                                          (0.9, 0.7, 0.1), rough=0.5))
        else:
            assign(parts[h]["plate"], m_plate)
            assign(parts[h]["tub"], m_case)
            assign(parts[h]["cover"], m_case)

        # ---- registration: plate holes are the physical master
        pl = placements[half]
        power = next(p for p in pl if p["ref"] == f"SW_{h}PWR1")
        if not any(o.name == power["ref"] for o in parts[h]["board"]):
            # KiCad's STEP export omits the switch's VRML model.
            x, y = power["x"] * SCALE, power["y"] * SCALE
            parts[h]["board"].extend((
                add_cube(power["ref"], (x, y, 2.75 * SCALE), (10, 2.5, 4.5), power_frame),
                add_cube(f"{power['ref']}_lever", (x + PWRSW_ACTUATOR_REST * SCALE, y, 5.70 * SCALE),
                         (2.0, 1.4, 1.40), power_lever),
            ))
        cuts = cutouts[half]
        sw = [p for p in pl if re.fullmatch(r"SW_[LR]\d\d", p["ref"])]
        holes = {}
        worst = 0.0
        for p in sw:
            c = min(cuts, key=lambda c: (c["x"] - p["x"]) ** 2
                    + (c["y"] - p["y"]) ** 2)
            d = math.hypot(c["x"] - p["x"], c["y"] - p["y"])
            worst = max(worst, d)
            holes[p["ref"]] = c
        if len(sw) != 22 or worst > 0.05:
            sys.exit(f"[scene] ABORT {half}: registration {worst:.3f} mm "
                     f"over {len(sw)} switches")
        # every switch hole must also be hit exactly once (no shared holes)
        used = {(c["x"], c["y"]) for c in holes.values()}
        if len(used) != 22:
            sys.exit(f"[scene] ABORT {half}: {len(used)} distinct holes "
                     "for 22 switch footprints")
        print(f"[scene] {half}: REGISTRATION 22/22 switch footprints on "
              f"plate holes, worst {worst:.4f} mm", flush=True)

        # ---- cap variant map: thumbs by position, homing on the INNER
        # index home key (G/H), one column inboard of the F/J stagger peak.
        cols = {}
        for p in sw:
            if p["y"] < -10.0:
                continue
            cols.setdefault(round(p["x"], 1), []).append(p)
        if len(cols) != 6:
            sys.exit(f"[scene] ABORT {half}: {len(cols)} finger columns")
        peak_x = max(cols, key=lambda x: max(q["y"] for q in cols[x]))
        inboard = [x for x in cols
                   if (x > peak_x if half == "Left" else x < peak_x)]
        index_x = max(inboard, key=lambda x: max(q["y"] for q in cols[x]))
        home = sorted(cols[index_x], key=lambda q: q["y"])[1]
        print(f"[scene] {half}: inner index column x={index_x:.1f}, "
              f"homing key ({home['x']:.1f},{home['y']:.1f})", flush=True)

        # ---- caps (KLP Lamé; user review: the flat Saddle field read
        # as "basically inline with case" — switch to the TALL Tilted
        # family, cap tops ~11.1mm abs, ~5.9mm proud of the cover.
        # Round 4 review: the four THUMBS wore the low KLP "Thumb"
        # profile and read as sunken below the rim ("case seems taller
        # than the keys, hard to press inside the case holes") — the
        # KLP families share the foot, so thumbs now wear the same tall
        # Normal_Tilted as the fingers (Sofle/Lily/Corne thumb clusters
        # sit at full cap height too). The tilted family has no homing
        # variant; homing keys wear the same cap.
        for p in sw:
            c = holes[p["ref"]]
            variant = "normal_tilted"
            _, roots_c, objs = import_glb(os.path.join(
                ASSETS, "parts", f"klp_{variant}.glb"),
                f"cap_{h}_{p['ref']}")
            assign(objs, m_cap)
            parts[h].setdefault("caps", []).extend(objs)
            for o in roots_c:
                o.rotation_euler.z += math.radians(c["angle"])
            bpy.context.view_layer.update()
            # the KLP origin is not the cap's geometric centre — place by
            # bbox centre so every cap registers with its plate hole
            (cx0, cy0, z0), (cx1, cy1, _) = bbox_mm(objs)
            for o in roots_c:
                o.location.x += c["x"] * SCALE - (cx0 + cx1) / 2
                o.location.y += c["y"] * SCALE - (cy0 + cy1) / 2
                o.location.z += CAP_STEM_Z * SCALE - z0
            bpy.context.view_layer.update()

        # ---- switch housings visible between plate and cap skirt
        for p in sw:
            c = holes[p["ref"]]
            for src_name, src_data, rot, scl in choc_sources:
                tag = src_name.removeprefix("choc_")
                o = bpy.data.objects.new(
                    f"swbody_{h}_{p['ref']}_{tag}", src_data)
                o.rotation_euler = rot
                o.scale = scl
                o.location = (c["x"] * SCALE, c["y"] * SCALE, 0.0)
                o.rotation_euler.z += math.radians(p["rot"])
                bpy.context.collection.objects.link(o)
                assign([o], switch_materials[tag])
                parts[h].setdefault("swbodies", []).append(o)

        # ---- poron gaskets on every tab, compressed to the real
        # assembly heights (bottom 3.0 -> 2.55, top 1.5 -> 1.28). They
        # stick to the plate tabs, so the explode lifts them with the
        # plate; the pad centre is the tab root + 2.0mm outward (the
        # same rule plate/gen_plate.py uses for the PORON DXF layer).
        # rounds 11-13: the foam layers are one soft SLAB each, and
        # round 13 is decisive about the shape: "the keyboard is not
        # rectangular, your layers of foam peak out like giant floating
        # rectangles". A squashed DUPLICATE OF THE TUB MESH carries the
        # exact case outline (rounded corners and all) — the tub's
        # local-y axis maps to world -z under the -90deg X import
        # rotation, so scaling local-y squashes the world height from
        # the real 9.55 mm to the foam thickness, then the slab is
        # recentred at the true compressed z.
        def case_slab(name, thickness, z_center):
            # round 18: the foam follows the case's EXACT silhouette —
            # extracted from the tub's BOTTOM CAP (the one surface that
            # is pure footprint: no magnet pockets, no ridges; local y
            # = -design z, so the bottom is local ymax) and extruded
            # into a smooth sheet, then inset 5% so it sits clearly
            # inside the walls. Rounds 16-17 (bbox rectangle, then
            # rounded-rect) both poked past the case's real curves.
            import bmesh as _bm
            tub = next(o for o in parts[h]["tub"] if o.type == "MESH")
            bm = _bm.new()
            bm.from_mesh(tub.data)
            ymax = max(v.co.y for v in bm.verts)
            bot = [f for f in bm.faces
                   if all(v.co.y > ymax - 0.02 for v in f.verts)]
            others = [f for f in bm.faces if f not in bot]
            _bm.ops.delete(bm, geom=others, context="FACES")
            for e in list(bm.edges):
                if not e.link_faces:
                    bm.edges.remove(e)
            for v in list(bm.verts):
                if not v.link_faces:
                    bm.verts.remove(v)
            ret = _bm.ops.extrude_face_region(bm, geom=bm.faces[:])
            for g in ret["geom"]:
                if isinstance(g, _bm.types.BMVert):
                    g.co.y -= thickness   # local -y = design +z = up
            me = bpy.data.meshes.new(name)
            bm.to_mesh(me)
            bm.free()
            o = bpy.data.objects.new(name, me)
            o.location = tub.location.copy()
            o.rotation_euler = tub.rotation_euler.copy()
            o.scale = tub.scale.copy()
            bpy.context.collection.objects.link(o)
            bpy.context.view_layer.update()
            # inset 5% in plan (local x/z are the plan axes under the
            # -90deg X import rotation) about the slab's own centre
            (b0, b1) = bbox_mm([o])
            cxy = ((b0[0] + b1[0]) / 2, (b0[1] + b1[1]) / 2)
            o.scale = (o.scale[0] * 0.95, o.scale[1], o.scale[2] * 0.95)
            bpy.context.view_layer.update()
            (n0, n1) = bbox_mm([o])
            o.location.x += cxy[0] - (n0[0] + n1[0]) / 2
            o.location.y += cxy[1] - (n0[1] + n1[1]) / 2
            o.location.z += (z_center * SCALE
                             - (n0[2] + n1[2]) / 2)
            bpy.context.view_layer.update()
            assign([o], m_poron)
            return o

        parts[h].setdefault("foam", []).append(
            case_slab(f"foam_b_{h}", 2.55, -0.275))
        # ---- TOP GASKETS: real PORON pads, not a slab (round 24c
        # review: "where are gaskets? should be small poron pads on the
        # plate tabs"). plate/<half>-lands.json carries the eight tab
        # roots; the pad centre is the tab root + 2.0 mm outward and the
        # pad is 7 x 4 mm, exactly as plate/gen_plate.py defines the
        # DXF PORON layer.
        try:
            lands = json.load(open(os.path.join(
                REPO, "plate", f"Hojicha44-{half}-lands.json")))
        except Exception as e:
            lands = {"tabs": []}
            print(f"  [scene] lands.json unavailable ({e})", flush=True)
        for ti, t in enumerate(lands.get("tabs", [])):
            a = math.radians(t["angle"])
            ox = t["x"] + math.cos(a) * 2.0
            oy = t["y"] + math.sin(a) * 2.0
            for face, th, zc in (("t", 1.00, 2.70), ("b", 2.55, -0.275)):
                # The pad is 7 x 4 mm with the SHORT side along the
                # tab's outward axis (the lands' `pad: [7, 4]` is
                # width x protrusion) -- the first pass had it the
                # other way round, so every gasket sat 90 deg across
                # its tab. Local X is the outward direction here.
                o = add_cube(f"gsk_{face}_{h}_{ti}",
                             (ox * SCALE, oy * SCALE, zc * SCALE),
                             (4.0, 7.0, th), m_poron,
                             rot_z=math.degrees(a))
                # top pads sit ON the plate (so they explode with it);
                # bottom pads belong to the foam level
                grp = "gaskets" if face == "t" else "gaskets_b"
                parts[h].setdefault(grp, []).append(o)
        print(f"[scene] {h}: {len(lands.get('tabs', []))} tab pads per "
              f"face (poron)", flush=True)
        print(f"[scene] {half}: case-outline foam+gasket slabs at the "
              f"compressed heights", flush=True)

        # ---- nice!nano v2 stand-in (the VRML model kicad-cli skips),
        # dimensioned from the committed footprint courtyard
        nanos = [p for p in pl if p["ref"].startswith("U_")]
        big = [c for c in cuts if c["w"] > 27 and c["h"] > 55]
        for p in nanos:
            x0, y0, x1, y1 = NANO_COURT
            corners = [fp_to_design(p["x_file"], p["y_file"], p["rot"], lx, ly)
                       for lx in (x0, x1) for ly in (y0, y1)]
            nx0 = min(q[0] for q in corners)
            nx1 = max(q[0] for q in corners)
            ny0 = min(q[1] for q in corners)
            ny1 = max(q[1] for q in corners)
            # Position the GLB at the center of the 2x12 socket grid.
            # The courtyard is asymmetric around the actual pin rows.
            ncx, ncy = fp_to_design(p["x_file"], p["y_file"], p["rot"], -7.62, -13.97)
            if big:
                w = big[0]
                if not (w["x"] - w["w"] / 2 <= nx0 and nx1 <= w["x"] + w["w"] / 2
                        and w["y"] - w["h"] / 2 <= ny0
                        and ny1 <= w["y"] + w["h"] / 2):
                    sys.exit(f"[scene] ABORT {half}: nano courtyard "
                             f"({nx0:.2f}..{nx1:.2f},{ny0:.2f}..{ny1:.2f}) "
                             f"outside MCU window ({w['x']},{w['y']})")
                print(f"[scene] {half}: nano bbox x {nx0:.2f}..{nx1:.2f} "
                      f"y {ny0:.2f}..{ny1:.2f} inside MCU window", flush=True)
            _, nano_roots, nano_meshes = import_glb(
                os.path.join(ASSETS, "parts", "nano.glb"), f"nano_{h}")
            for obj in nano_roots:
                obj.location.x += ncx * SCALE
                obj.location.y += ncy * SCALE
            for obj in nano_meshes:
                part = obj.name.split(".")[0].removeprefix("nano_")
                assign([obj], nano_materials[part])
            parts[h]["nano"] = nano_meshes

        enc = next((o for o in parts[h]["board"] if o.name == f"ENC_{h}1"), None)
        jack = next((o for o in parts[h]["board"] if o.name == f"J_{h}1"), None)
        if enc is None or jack is None:
            raise RuntimeError(f"{half} asset needs both EC11E and PJ-320A STEP models")
        parts[h]["board"].remove(enc)
        parts[h]["board"].remove(jack)
        parts[h]["encoder"] = [enc]
        parts[h]["jack"] = [jack]
        parts[h]["jack"].extend(
            materialize_ports(enc, jack, half, m_enc_body, m_enc_shaft,
                              nano_materials["socket"], nano_materials["shell"]))

        # Locate the knob by the original shaft geometry, before shortening it.
        shaft = [enc.matrix_world @ v.co for v in enc.data.vertices
                 if (enc.matrix_world @ v.co).z > 0.0113]
        kx = (min(v.x for v in shaft) + max(v.x for v in shaft)) / 2
        ky = (min(v.y for v in shaft) + max(v.y for v in shaft)) / 2
        _, knob_roots, knob_objs = import_glb(
            os.path.join(ASSETS, "parts", "knob.glb"), f"knob_{h}")
        cover_top = bbox_mm(parts[h]["cover"])[1][2]
        for knob in knob_roots:
            knob.location = (kx, ky, cover_top + KNOB_COVER_GAP * SCALE)
        assign(knob_objs, m_knob)
        parts[h]["knob"] = knob_objs
        if "exploded" in args.shots.split(","):
            parts[h]["pcb_art"] = pcb_route_material(half, parts[h]["board"])

    # ---- smooth curved parts (welded glbs make this effective)
    for h in parts:
        smooth(parts[h].get("caps", []), 35.0)

    all_objs = [o for h in parts for lst in parts[h].values()
                for o in (lst if isinstance(lst, list) else [])]
    # ---- diagnostics: where every group actually landed
    bpy.context.view_layer.update()
    for h in parts:
        for grp in ("board", "plate", "tub", "cover", "caps",
                    "swbodies", "nano", "gaskets", "knob"):
            objs = parts[h].get(grp, [])
            if not objs:
                print(f"[diag] {h}/{grp}: EMPTY", flush=True)
                continue
            (x0, y0, z0), (x1, y1, z1) = bbox_mm(objs)
            hidden = sum(1 for o in objs if o.hide_render)
            print(f"[diag] {h}/{grp}: x {x0*1000:.1f}..{x1*1000:.1f} "
                  f"y {y0*1000:.1f}..{y1*1000:.1f} "
                  f"z {z0*1000:.2f}..{z1*1000:.2f} n={len(objs)} "
                  f"hidden={hidden}", flush=True)
    # the committed case places the halves in one layout: report the true
    # tub seam instead of inventing a split gap
    (_, _, _), (lx1, _, _) = bbox_mm(parts["L"]["tub"])
    (rx0, _, _), (_, _, _) = bbox_mm(parts["R"]["tub"])
    print(f"[diag] tub seam (design): {(rx0-lx1)*1000:.2f} mm", flush=True)
    if args.hide_cover:
        for h in parts:
            for o in parts[h]["cover"]:
                o.hide_render = True
    if args.hide_case:
        for h in parts:
            for o in parts[h]["tub"] + parts[h]["cover"]:
                o.hide_render = True
    if args.hide_plate:
        for h in parts:
            for o in parts[h]["plate"]:
                o.hide_render = True

    # ---- presentation pose (user review round 4: "two halves slightly
    # further apart, maybe even slightly angled away from each other"):
    # every object of a half is parented to an empty sitting on its
    # OUTER BOTTOM long edge, then the empty is splayed 4° in plan,
    # tented 5° about that edge (the hinge edge stays on the desk, so
    # nothing sinks below the floor) and pushed 7mm further out — the
    # classic Sofle/Corne product-shot wing. Pure render transform: the
    # committed case files still build the assembled 2.8mm-seam layout.
    # round-5 review: 7mm + 4 deg pushed the halves out of frame
    # ("can't see most of the left board") — halve the horizontal
    # spread, keep the tent (that is the "angled away" that reads)
    #
    # round 24: this block used to exist TWICE, back to back, so every
    # half was posed twice and the numbers below were silently doubled
    # in the render (5 deg splay / 10 deg tent / 5 mm split). The
    # duplicate is gone; the values are now stated once at their true
    # render strength so future tweaks behave predictably.
    SPLAY_DEG, TENT_DEG, SPLIT_MM = 5.0, 6.0, 5.0
    for h, sgn in (("L", -1.0), ("R", 1.0)):
        half_objs = [o for lst in parts[h].values()
                     for o in (lst if isinstance(lst, list) else [])]
        (hx0, hy0, hz0), (hx1, hy1, _) = bbox_mm(parts[h]["tub"])
        pe = bpy.data.objects.new(f"pose_{h}", None)
        pe.empty_display_size = 0.02
        bpy.context.collection.objects.link(pe)
        pe.location = ((hx0 if sgn < 0 else hx1), (hy0 + hy1) / 2, hz0)
        bpy.context.view_layer.update()
        # python parenting does NOT keep world transforms (no auto
        # parent-inverse like the UI operator) — without this every
        # child jumps by the pivot and the assembly lands ~2x out
        pe_inv = pe.matrix_world.inverted()
        for o in half_objs:
            o.parent = pe
            o.matrix_parent_inverse = pe_inv.copy()
        bpy.context.view_layer.update()
        # tent: +x edge lifts for the left half, -x edge for the right;
        # splay: far end swings outward (CCW left, CW right)
        pe.rotation_euler = (
            0.0,
            math.radians(TENT_DEG if sgn > 0 else -TENT_DEG),
            math.radians(SPLAY_DEG if sgn < 0 else -SPLAY_DEG))
        pe.location.x += sgn * SPLIT_MM * SCALE
        bpy.context.view_layer.update()
        print(f"[scene] pose {h}: splayed {SPLAY_DEG} deg, tented "
              f"{TENT_DEG} deg on the outer edge, split +{SPLIT_MM} mm",
              flush=True)

    return parts, all_objs


def studio_grain(mat, frequency, relief, roughness):
    """Use scene metres so grain has the same size on faces and sidewalls."""
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    coords = nt.nodes.new("ShaderNodeNewGeometry").outputs["Position"]
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = frequency
    noise.inputs["Detail"].default_value = 2
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.32
    bump.inputs["Distance"].default_value = relief
    rough = nt.nodes.new("ShaderNodeMapRange")
    rough.inputs["To Min"].default_value, rough.inputs["To Max"].default_value = roughness
    nt.links.new(coords, noise.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    nt.links.new(noise.outputs["Fac"], rough.inputs["Value"])
    nt.links.new(rough.outputs["Result"], bsdf.inputs["Roughness"])
    return noise.outputs["Fac"]


def honed_stone():
    """Quiet charcoal stone with diagonal mineral bands and a honed face."""
    mat = pbr("honed_charcoal", (0.025, 0.026, 0.028), rough=0.72)
    grain = studio_grain(mat, frequency=1150, relief=0.000045, roughness=(0.65, 0.80))
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Specular IOR Level"].default_value = 0.25
    coords = nt.nodes.new("ShaderNodeNewGeometry").outputs["Position"]
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Rotation"].default_value[2] = math.radians(22)
    mapping.inputs["Scale"].default_value = (4.2, 10.5, 8.0)
    bands = nt.nodes.new("ShaderNodeTexNoise")
    bands.inputs["Scale"].default_value = 1.0
    bands.inputs["Detail"].default_value = 3.4
    bands.inputs["Roughness"].default_value = 0.55
    tone = nt.nodes.new("ShaderNodeValToRGB")
    ramp = tone.color_ramp
    ramp.interpolation = "EASE"
    shades = ((0.24, (0.016, 0.018, 0.020)),
              (0.43, (0.025, 0.027, 0.028)),
              (0.57, (0.036, 0.037, 0.037)),
              (0.68, (0.058, 0.054, 0.050)),
              (0.79, (0.079, 0.074, 0.068)))
    for i, (position, color) in enumerate(shades):
        el = ramp.elements[i] if i < 2 else ramp.elements.new(position)
        el.position, el.color = position, (*color, 1.0)
    nt.links.new(coords, mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], bands.inputs["Vector"])
    nt.links.new(bands.outputs["Fac"], tone.inputs["Fac"])
    mineral = nt.nodes.new("ShaderNodeMapRange")
    mineral.inputs["From Min"].default_value = 0.25
    mineral.inputs["From Max"].default_value = 0.75
    mineral.inputs["To Min"].default_value = 0.72
    mineral.inputs["To Max"].default_value = 1.27
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MULTIPLY"
    mix.inputs[0].default_value = 1.0
    nt.links.new(grain, mineral.inputs["Value"])
    nt.links.new(tone.outputs["Color"], mix.inputs[1])
    nt.links.new(mineral.outputs["Result"], mix.inputs[2])
    nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def pcb_route_material(half, board):
    """Map the actual front copper segments onto the STEP soldermask."""
    from pathlib import Path
    import numpy as np

    pcb_dir = Path(REPO) / "pcb"
    generators = str(pcb_dir / "generators")
    if generators not in sys.path:
        sys.path.insert(0, generators)
    from check_board import committed_tracks
    from frame import read_design

    source = pcb_dir / "kicad" / f"Hojicha44-{half}.kicad_pcb"
    tracks = [t for t in committed_tracks(read_design(source)) if t[-1] == "F"]
    if not tracks:
        raise RuntimeError(f"No front copper segments in {source}")

    mask_layers = [o for o in board if o.type == "MESH" and
                   o.data.materials and o.data.materials[0].name.startswith("pcb_soldermask")]
    top_mask = max(mask_layers, key=lambda o: bbox_mm([o])[1][2])
    low, high = bbox_mm([top_mask])
    left, bottom = low[0] / SCALE, low[1] / SCALE
    width, height = (high[0] - low[0]) / SCALE, (high[1] - low[1]) / SCALE
    nx, ny = math.ceil(width * 16), math.ceil(height * 16)
    mask = np.zeros((ny, nx), dtype=np.float32)
    sx, sy = nx / width, ny / height
    aa = 1 / min(sx, sy)
    for x0, y0, x1, y1, trace_width, _ in tracks:
        radius = trace_width / 2
        margin = radius + aa
        xlo = max(0, math.floor((min(x0, x1) - margin - left) * sx))
        xhi = min(nx, math.ceil((max(x0, x1) + margin - left) * sx))
        ylo = max(0, math.floor((min(y0, y1) - margin - bottom) * sy))
        yhi = min(ny, math.ceil((max(y0, y1) + margin - bottom) * sy))
        x = left + (np.arange(xlo, xhi) + 0.5) / sx - x0
        y = bottom + (np.arange(ylo, yhi)[:, None] + 0.5) / sy - y0
        dx, dy = x1 - x0, y1 - y0
        length_sq = dx * dx + dy * dy
        t = np.clip((x * dx + y * dy) / length_sq, 0, 1) if length_sq else 0
        d = np.hypot(x - t * dx, y - t * dy)
        section = mask[ylo:yhi, xlo:xhi]
        np.maximum(section, np.clip((radius - d) / aa + 0.5, 0, 1), out=section)

    image = bpy.data.images.new(f"{half} F.Cu routes", width=nx, height=ny, alpha=False)
    image.colorspace_settings.name = "Non-Color"
    rgba = np.ones((ny, nx, 4), dtype=np.float32)
    rgba[:, :, :3] = mask[:, :, None]
    image.pixels.foreach_set(rgba.ravel())
    image.update()

    # UVs use pre-pose design coordinates, including the board's millimetre
    # scale and import rotation. They travel with the board during posing.
    mesh = top_mask.data
    uv = mesh.uv_layers.new(name="Routed copper")
    for loop in mesh.loops:
        pos = top_mask.matrix_world @ mesh.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = ((pos.x / SCALE - left) / width,
                                  (pos.y / SCALE - bottom) / height)

    mat = pbr(f"pcb_routed_mask_{half}", (0.018, 0.072, 0.034), rough=0.52)
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Specular IOR Level"].default_value = 0.25
    uv_node = nt.nodes.new("ShaderNodeUVMap")
    uv_node.uv_map = uv.name
    texture = nt.nodes.new("ShaderNodeTexImage")
    texture.image = image
    texture.extension = "CLIP"
    tint = nt.nodes.new("ShaderNodeMixRGB")
    tint.inputs[1].default_value = (0.017, 0.066, 0.031, 1)
    tint.inputs[2].default_value = (0.08, 0.32, 0.145, 1)
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.26
    bump.inputs["Distance"].default_value = 0.018 * SCALE
    nt.links.new(uv_node.outputs["UV"], texture.inputs["Vector"])
    nt.links.new(texture.outputs["Color"], tint.inputs[0])
    nt.links.new(texture.outputs["Color"], bump.inputs["Height"])
    nt.links.new(tint.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    print(f"[scene] {half}: mapped {len(tracks)} KiCad front copper segments", flush=True)
    return top_mask, mat


def porous_foam(name, colour):
    """Fine open-cell texture with softly shaded recesses."""
    mat = pbr(name, colour, rough=0.90)
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Specular IOR Level"].default_value = 0.20
    coords = nt.nodes.new("ShaderNodeNewGeometry")
    cell = nt.nodes.new("ShaderNodeTexVoronoi")
    cell.inputs["Scale"].default_value = 1560
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 4600
    noise.inputs["Detail"].default_value = 2.0
    distort = nt.nodes.new("ShaderNodeMath")
    distort.operation = "MULTIPLY_ADD"
    distort.inputs[1].default_value = 0.32
    cells = nt.nodes.new("ShaderNodeValToRGB")
    ramp = cells.color_ramp
    ramp.elements.remove(ramp.elements[1])
    ramp.elements[0].position = 0.30
    ramp.interpolation = "B_SPLINE"
    ramp.elements[0].color = (*[c * 0.46 for c in colour], 1)
    for position, value in ((0.43, 0.73), (0.61, 1.02), (0.82, 0.95)):
        ramp.elements.new(position).color = (*[c * value for c in colour], 1)
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.5
    bump.inputs["Distance"].default_value = 0.13 * SCALE
    cloud = nt.nodes.new("ShaderNodeTexNoise")
    cloud.inputs["Scale"].default_value = 148
    cloud.inputs["Detail"].default_value = 2.0
    mottling = nt.nodes.new("ShaderNodeValToRGB")
    mottling.color_ramp.elements[0].color = (0.76, 0.76, 0.76, 1)
    mottling.color_ramp.elements[1].color = (1.16, 1.16, 1.16, 1)
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MULTIPLY"
    mix.inputs[0].default_value = 1
    nt.links.new(coords.outputs["Position"], cloud.inputs["Vector"])
    nt.links.new(cloud.outputs["Fac"], mottling.inputs["Fac"])
    nt.links.new(cells.outputs["Color"], mix.inputs[1])
    nt.links.new(mottling.outputs["Color"], mix.inputs[2])
    for tex in (cell, noise):
        nt.links.new(coords.outputs["Position"], tex.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], distort.inputs[0])
    nt.links.new(cell.outputs["Distance"], distort.inputs[2])
    nt.links.new(distort.outputs[0], cells.inputs["Fac"])
    nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(cells.outputs["Color"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def add_tenting_feet(parts, desk_z, colourway="bright"):
    """Fit feet to the posed case undersides and a common studio floor."""
    from mathutils import Vector

    colour = (0.045, 0.047, 0.049) if colourway == "dark" else (0.43, 0.34, 0.27)
    material = pbr("tenting_molded", colour, rough=0.57)
    feet = []
    for half, groups in parts.items():
        tub = next(o for o in groups["tub"] if o.type == "MESH")
        transform = tub.parent.matrix_world @ tub.matrix_parent_inverse
        inverse = tub.matrix_world.inverted()
        normal = transform.to_3x3() @ Vector((0, 0, 1))
        x = 125.5 if half == "L" else 291.5 - 125.5
        origin = transform @ Vector((x * SCALE, -32 * SCALE, -0.02))
        hit, point, _, _ = tub.ray_cast(inverse @ origin, inverse.to_3x3() @ normal)
        if not hit:
            raise RuntimeError(f"Tenting mount {half} misses the case underside")
        contact = tub.matrix_world @ point

        # The rounded foot has one continuous profile, with a flat desk
        # contact and a wider top shaped to the sloping case underside.
        vertices = []
        rings = ((3.6, 0, 0), (4.35, 0.65, 0), (4.4, 1.6, 0),
                 (3.85, 5.0, 0), (4.5, -0.6, 1), (4.0, 0.25, 1))
        sides = 48
        for radius, rise, top in rings:
            for i in range(sides):
                angle = math.tau * i / sides
                dx, dy = radius * SCALE * math.cos(angle), radius * SCALE * math.sin(angle)
                roof = contact.z - (normal.x * dx + normal.y * dy) / normal.z
                vertices.append((contact.x + dx, contact.y + dy,
                                 (roof if top else desk_z) + rise * SCALE))
        faces = [tuple(reversed(range(sides)))]
        for j in range(len(rings) - 1):
            for i in range(sides):
                n = (i + 1) % sides
                faces.append((j*sides+i, j*sides+n, (j+1)*sides+n, (j+1)*sides+i))
        faces.append(tuple(range(len(vertices) - sides, len(vertices))))
        mesh = bpy.data.meshes.new(f"tenting_foot_{half}")
        mesh.from_pydata(vertices, [], faces)
        mesh.update()
        obj = bpy.data.objects.new(mesh.name, mesh)
        bpy.context.collection.objects.link(obj)
        assign([obj], material)
        for polygon in mesh.polygons:
            polygon.use_smooth = len(polygon.vertices) == 4
        feet.append(obj)
    return feet


def artisan_resin():
    """Deep teal cast resin with folded colour and suspended mica."""
    mat = pbr("artisan_cast_resin", (0.038, 0.23, 0.26), rough=0.30)
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Coat Weight"].default_value = 0.29
    bsdf.inputs["Coat Roughness"].default_value = 0.23
    bsdf.inputs["Subsurface Weight"].default_value = 0.07
    bsdf.inputs["Subsurface Scale"].default_value = 0.001
    coords = nt.nodes.new("ShaderNodeTexCoord").outputs["Generated"]
    folds = nt.nodes.new("ShaderNodeTexNoise")
    folds.inputs["Scale"].default_value = 3.3
    folds.inputs["Detail"].default_value = 2.3
    folds.inputs["Distortion"].default_value = 1.8
    tone = nt.nodes.new("ShaderNodeValToRGB")
    for i, (value, color) in enumerate(((0.24, (0.014, 0.062, 0.094)),
                                        (0.56, (0.047, 0.27, 0.27)),
                                        (0.83, (0.23, 0.56, 0.45)))):
        stop = tone.color_ramp.elements[i] if i < 2 else tone.color_ramp.elements.new(value)
        stop.position, stop.color = value, (*color, 1)
    mica = nt.nodes.new("ShaderNodeTexVoronoi")
    mica.inputs["Scale"].default_value = 52
    specks = nt.nodes.new("ShaderNodeMapRange")
    specks.inputs["From Min"].default_value = 0.065
    specks.inputs["From Max"].default_value = 0.14
    specks.inputs["To Min"].default_value = 0.76
    specks.inputs["To Max"].default_value = 0
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.inputs[2].default_value = (0.67, 0.43, 0.15, 1)
    for output, target in ((coords, folds.inputs["Vector"]),
                           (coords, mica.inputs["Vector"]),
                           (folds.outputs["Fac"], tone.inputs["Fac"]),
                           (mica.outputs["Distance"], specks.inputs["Value"]),
                           (specks.outputs["Result"], mix.inputs[0]),
                           (tone.outputs["Color"], mix.inputs[1]),
                           (mix.outputs["Color"], bsdf.inputs["Base Color"])):
        nt.links.new(output, target)
    return mat


def play_backdrop(center_x):
    mat = pbr("play_apricot_lilac", (0.52, 0.31, 0.40), rough=0.81)
    nt = mat.node_tree
    position = nt.nodes.new("ShaderNodeNewGeometry")
    axis = nt.nodes.new("ShaderNodeSeparateXYZ")
    span = nt.nodes.new("ShaderNodeMapRange")
    span.inputs["From Min"].default_value = center_x - 0.27
    span.inputs["From Max"].default_value = center_x + 0.27
    tone = nt.nodes.new("ShaderNodeValToRGB")
    tone.color_ramp.elements[0].color = (0.74, 0.38, 0.25, 1)
    tone.color_ramp.elements[1].color = (0.35, 0.31, 0.62, 1)
    nt.links.new(position.outputs["Position"], axis.inputs["Vector"])
    nt.links.new(axis.outputs["X"], span.inputs["Value"])
    nt.links.new(span.outputs["Result"], tone.inputs["Fac"])
    nt.links.new(tone.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    return mat


def apply_colourway(parts, colourway):
    """Round-9 colourway variants (renders/SHOTLIST.md). Overrides the
    product materials AFTER build_keyboard — called from main() and
    from scene_env.py so the desk environments can wear variants too."""
    if colourway == "bright":
        return
    if colourway == "dark":
        cap = pbr("dark_pbt", (0.066, 0.070, 0.075), rough=0.56)
        cap.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0.30
        studio_grain(cap, frequency=5200, relief=0.000017, roughness=(0.49, 0.65))
        case = pbr("dark_sintered_nylon", (0.029, 0.032, 0.035), rough=0.65)
        studio_grain(case, frequency=2100, relief=0.000055, roughness=(0.61, 0.77))
        plate = pbr("dark_pom", (0.022, 0.024, 0.026), rough=0.42)
        switch = pbr("dark_switch_plastic", (0.022, 0.024, 0.026), rough=0.49)
        knob = pbr("dark_satin_brass", (0.57, 0.39, 0.19), rough=0.36, metal=1.0)
        studio_grain(knob, frequency=6400, relief=0.000008, roughness=(0.30, 0.44))
        knob.node_tree.nodes["Principled BSDF"].inputs["Anisotropic"].default_value = 0.38
        for groups in parts.values():
            assign(groups.get("caps", []), cap)
            assign(groups.get("tub", []) + groups.get("cover", []), case)
            assign(groups.get("plate", []), plate)
            assign(groups.get("knob", []), knob)
            assign([obj for obj in groups.get("swbodies", [])
                    if not obj.name.endswith("_contacts")], switch)
        print("[scene] colourway: charcoal PBT, matte nylon and satin brass", flush=True)
        return
    if colourway == "play":
        # multicolour caps: curated 6-colour palette scattered on a
        # deterministic position hash (balanced, never clumped by row),
        # mid-grey case, silver plate
        palette = ((0.85, 0.35, 0.28),   # coral
                   (0.88, 0.66, 0.18),   # mustard
                   (0.16, 0.55, 0.52),  # teal
                   (0.14, 0.22, 0.48),  # navy
                   (0.88, 0.85, 0.80),  # cream
                   (0.45, 0.62, 0.48))  # sage
        m_case = pbr("cw_case", (0.28, 0.28, 0.295), rough=0.60)
        micro_texture(m_case, 85, 0.40, 0.00055, 0.52, 0.68, detail=5.0)
        m_plate = pbr("cw_plate", (0.58, 0.58, 0.60), rough=0.30,
                      metal=0.7)
        cap_materials = []
        for index, colour in enumerate(palette):
            cap = pbr(f"cw_play_{index}", colour, rough=0.50)
            studio_grain(cap, frequency=3900, relief=0.000030, roughness=(0.46, 0.57))
            cap_materials.append(cap)
        # round-11 review: "make the colour symmetrical (pink yellow
        # blue on the left, then blue yellow pink on the right)" — the
        # index is a function of |x - half centre| so each half mirrors
        # the other; no more left/right drift
        for h in parts:
            assign(parts[h].get("tub", []), m_case)
            assign(parts[h].get("cover", []), m_case)
            assign(parts[h].get("plate", []), m_plate)
            hcaps = parts[h].get("caps", [])
            if not hcaps:
                continue
            hx = (min(o.matrix_world[0][3] for o in hcaps)
                  + max(o.matrix_world[0][3] for o in hcaps)) / 2
            for o in hcaps:
                key = int(round(abs(o.matrix_world[0][3] - hx) * 60)
                          + round(o.matrix_world[1][3]) * 2) % len(palette)
                assign([o], cap_materials[key])
        print("[scene] colourway: play (mirror-symmetric caps)",
              flush=True)
        return
    if colourway == "artisan":
        # bright colourway + ONE sculpted accent cap: assets/parts/
        # artisan.glb (round-9 build_assets: oblate dome, three
        # concentric ridge rings, centre button, Saddle-family foot)
        # replaces the cap at the outer-top position, inheriting its
        # exact posed transform.
        caps = parts.get("L", {}).get("caps", [])
        art_path = os.path.join(ASSETS, "parts", "artisan.glb")
        if caps and os.path.exists(art_path):
            accent = sorted(
                caps, key=lambda o: (round(o.matrix_world[0][3], 3),
                                     -round(o.matrix_world[1][3], 3)))[0]
            _, art_roots, art_objs = import_glb(art_path, "artisan")
            bpy.context.view_layer.update()
            for ao in art_roots:
                ao.matrix_world = accent.matrix_world.copy()
            bpy.context.view_layer.update()
            m_art = artisan_resin()
            assign(art_objs, m_art)
            for ai, ao in enumerate(art_objs):
                ao.name = f"artisan_accent_{ai}"
            accent.hide_render = True
            accent.hide_set(True)
            # keep it in the caps group so poses/explodes treat it
            parts["L"]["caps"].extend(art_objs)
        print("[scene] colourway: artisan (sculpted accent cap)",
              flush=True)


def main():
    args = parse_args()
    res = tuple(int(v) for v in args.res.split("x"))
    os.makedirs(args.out, exist_ok=True)
    init_scene()
    parts, all_objs = build_keyboard(args)
    apply_colourway(parts, args.colourway)
    if args.colourway in ("play", "artisan"):
        view = bpy.context.scene.view_settings
        view.view_transform = "AgX"
        view.look = "AgX - Medium High Contrast"

    # ---- render queue
    shots = set(args.shots.split(","))
    orbits = [i for i in (2, 8) if "orbit" in shots or f"orbit_{i:02d}" in shots]
    (bx0, by0, bz0), (bx1, by1, bz1) = bbox_mm(all_objs)
    cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
    print(f"[scene] assembly centre ({cx*1000:.1f},{cy*1000:.1f}) mm",
          flush=True)

    # Set the studio floor at the feet's common contact height.
    feet = []
    desk_z = bz0 - 0.0002
    if (args.colourway in ("bright", "dark") and not args.hide_case and not args.no_floor
            and (orbits or {"hero", "top"} & shots)):
        desk_z = min(bbox_mm(g["tub"])[0][2] for g in parts.values())
        feet = add_tenting_feet(parts, desk_z, args.colourway)
    if not args.no_floor:
        bpy.ops.mesh.primitive_plane_add(size=20.0, location=(cx, cy, desk_z))
        floor = bpy.context.active_object
        floor.name = "studio_floor"
        if args.colourway == "dark":
            m_floor = honed_stone()
        elif args.colourway == "play":
            m_floor = play_backdrop(cx)
        else:
            m_floor = pbr("studio_floor", (0.40, 0.385, 0.365), rough=0.85)
            micro_texture(m_floor, 800, 0.60, 0.0008, 0.72, 0.90, detail=3.0)
        assign([floor], m_floor)
        print(f"[scene] floor at z {desk_z * 1000:.2f} mm", flush=True)

    PLAY = args.colourway == "play"
    if PLAY:
        from mathutils import Euler, Matrix, Vector

        for h, offset, angles in (
                ("L", (-0.005, -0.009, 0.045), (17, -19, 27)),
                ("R", (-0.014, 0.008, 0.087), (7, 16, -22))):
            lo, hi = bbox_mm(parts[h]["tub"] + parts[h]["cover"])
            pivot = (Vector(lo) + Vector(hi)) / 2
            turn = Euler(tuple(map(math.radians, angles)), "XYZ").to_matrix().to_4x4()
            pose = bpy.data.objects[f"pose_{h}"]
            pose.matrix_world = (Matrix.Translation(pivot + Vector(offset)) @ turn
                                 @ Matrix.Translation(-pivot) @ pose.matrix_world)
            bpy.context.view_layer.update()
        lo, hi = bbox_mm(all_objs)
        _pcx, _pcy, _pcz = ((a + b) / 2 for a, b in zip(lo, hi))

    setups = args.setups.split(",")
    for setup in setups:
        setup_world_and_lights(setup, cx, cy)
        sdir = os.path.join(args.out, setup)
        os.makedirs(sdir, exist_ok=True)
        if "exploded" in shots:
            stack_materials = {
                "foam": porous_foam("open_cell_foam", (0.41, 0.34, 0.26)),
                "gaskets": porous_foam("open_cell_gaskets", (0.31, 0.25, 0.18)),
                "tub": pbr("stack_tub", (0.12, 0.12, 0.12), rough=0.53),
                "cover": pbr("stack_cover", (0.15, 0.15, 0.15), rough=0.45),
                "plate": pbr("stack_plate", (0.24, 0.25, 0.27), rough=0.42, metal=0.66),
                "knob": pbr("stack_knob", (0.70, 0.52, 0.24), rough=0.30, metal=0.88),
            }
            stack_materials["gaskets_b"] = stack_materials["gaskets"]
            changes = []
            for groups in parts.values():
                for group, mat in stack_materials.items():
                    if not args.stack_colors and group not in ("foam", "gaskets", "gaskets_b"):
                        continue
                    for obj in groups.get(group, []):
                        changes.append((obj, list(obj.data.materials)))
                        assign([obj], mat)
                top_mask, mat = groups["pcb_art"]
                changes.append((top_mask, list(top_mask.data.materials)))
                assign([top_mask], mat)
            for obj in feet:
                obj.hide_render = True
            for group, dz in EXPLODE.items():
                for groups in parts.values():
                    move_exploded_layer(groups.get(group, []), dz * SCALE)
            camera_bg = next(n for n in bpy.context.scene.world.node_tree.nodes
                             if n.type == "BACKGROUND" and n.inputs[1].default_value == 1.0)
            saved_bg = tuple(camera_bg.inputs[0].default_value)
            camera_bg.inputs[0].default_value = (0.105, 0.119, 0.145, 1)
            floor_obj = bpy.data.objects.get("studio_floor")
            floor_hidden = floor_obj.hide_render if floor_obj else False
            if floor_obj:
                floor_obj.hide_render = True
            cam = add_cam("exploded", (cx - 0.23, cy - 0.89, 0.35),
                          (cx + 0.002, cy, 0.050), lens=76)
            if setup == args.colourway:
                center_subject(cam, all_objs, res)
            if args.framecheck:
                frame_report(cam, all_objs, "exploded", res)
            else:
                render_to(cam, os.path.join(sdir, "exploded.png"),
                          res, args.samples, args.device, pp=args.pp)
            camera_bg.inputs[0].default_value = saved_bg
            if floor_obj:
                floor_obj.hide_render = floor_hidden
            for obj, materials in changes:
                obj.data.materials.clear()
                for mat in materials:
                    obj.data.materials.append(mat)
            for obj in feet:
                obj.hide_render = False
            for group, dz in EXPLODE.items():
                for groups in parts.values():
                    move_exploded_layer(groups.get(group, []), -dz * SCALE)
        if "hero" in shots:
            if PLAY:
                # lower, closer, a touch of roll — playful, not catalogue;
                # framed on the airborne bbox, not the desk centre
                cam = add_cam("hero", (_pcx - 0.19, _pcy - 0.53,
                                       _pcz + 0.34),
                              (_pcx, _pcy, _pcz), lens=48)
                cam.rotation_euler.rotate_axis("Z", math.radians(9))
                center_subject(cam, all_objs, res)
            else:
                cam = add_cam("hero", (cx - 0.27, cy - 0.53, 0.24),
                              (cx, cy, 0.004), lens=51)
            if setup == args.colourway:
                center_subject(cam, all_objs + feet, res)
            if args.framecheck:
                frame_report(cam, all_objs + feet, "hero", res)
            else:
                render_to(cam, os.path.join(sdir, "hero.png"), res,
                          args.samples, args.device, pp=args.pp)
        if "artisan" in shots:
            # round-10 review: "the artisan keycaps can go to a niche fun
            # set, of singular expressive shots, not within the bright/
            # dark professional sets" — this is that shot: one low,
            # close, dramatic angle on the sculpted accent cap. Run as
            # its own invocation: --colourway artisan --shots artisan
            art_objs = [o for h in parts for o in parts[h].get("caps", [])
                        if o.name.startswith("artisan_accent")]
            if not art_objs:
                print("[scene] artisan shot: no accent cap present — run "
                      "with --colourway artisan", flush=True)
            else:
                (a0, a1) = bbox_mm(art_objs)
                a = ((a0[0] + a1[0]) / 2, (a0[1] + a1[1]) / 2,
                     (a0[2] + a1[2]) / 2)
                loc = (a[0] - 0.090, a[1] - 0.076, a[2] + 0.064)
                look = (a[0] + 0.004, a[1] + 0.005, a[2])
                import mathutils
                cam = add_cam("artisan", loc, look, lens=55)
                cam.data.dof.use_dof = True
                cam.data.dof.focus_distance = (
                    (mathutils.Vector(a) - cam.location).dot(
                        cam.rotation_euler.to_matrix() @ mathutils.Vector((0, 0, -1)))
                )
                cam.data.dof.aperture_fstop = 13.0
                near_art = art_objs + [
                    o for h in parts for o in parts[h].get("caps", [])
                    if (o.matrix_world[0][3] - a[0]) ** 2
                    + (o.matrix_world[1][3] - a[1]) ** 2 < 0.034 ** 2]
                if args.framecheck:
                    frame_report(cam, near_art, "artisan", res)
                else:
                    render_to(cam, os.path.join(sdir, "artisan.png"),
                              res, args.samples, args.device,
                              pp=args.pp)
        for i in orbits:
            angle = 2 * math.pi * i / 12
            label = f"orbit_{i:02d}"
            cam = add_cam(label, (cx + 0.55 * math.cos(angle),
                                  cy - 0.55 * math.sin(angle), 0.30),
                          (cx, cy, 0.006), lens=50)
            if setup == args.colourway:
                center_subject(cam, all_objs + feet, res)
            if args.framecheck:
                frame_report(cam, all_objs + feet, label, res)
            else:
                # From the rear, the fill panel's cutoff crosses the floor
                # in frame. The key and rim lights carry this angle.
                fill = bpy.data.objects.get("fill") if i == 8 and setup == "bright" else None
                if fill:
                    fill.hide_render = True
                render_to(cam, os.path.join(sdir, label + ".png"),
                          res, args.samples, args.device, pp=args.pp)
                if fill:
                    fill.hide_render = False
        if "top" in shots:
            cam = add_cam("top", (cx, cy - 0.0001, 0.50), (cx, cy, 0.0),
                          lens=60)
            cam.data.type = "ORTHO"
            # round 24: the nano USB shell removal shrank the assembly
            # bbox and moved cy, which pulled the north edge (jacks)
            # onto the frame line. 0.44 leaves 10 mm of air all round.
            cam.data.ortho_scale = 0.44
            if setup == args.colourway:
                center_subject(cam, all_objs + feet, res)
            if args.framecheck:
                frame_report(cam, all_objs + feet, "top", res)
            else:
                render_to(cam, os.path.join(sdir, "top.png"), res,
                          args.samples, args.device, pp=args.pp)
    print("SCENE-DONE")


if __name__ == "__main__":
    main()
