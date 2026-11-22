#!/usr/bin/env python3
"""Build the render asset pack for Hojicha44.

Runs in case/.venv (cadquery + ezdxf + trimesh + numpy). Read-only on all
manufacturing artifacts; every output lands under generated/renders/assets/
(a derived, regenerable tree — final renders and scripts are what get
committed).

Outputs:
  assets/board/Hojicha44-{L,R}.glb     PCB assembly, named nodes (kicad-cli
                                       STEP export -> OCCT CAF -> glTF)
  assets/plate/Hojicha44-{L,R}.glb     plate solid extruded from the
                                       tracked DXF (OUTLINE + CUTOUT through,
                                       RELIEF 0.55 pockets in the underside)
  assets/case/{L,R}-{tub,cover}.glb    converted from case/out/ STEPs
  assets/parts/{saddle,saddle_tilted,saddle_homing,normal_tilted,thumb}.glb
                                       KLP Lame keycaps (pinned download)
  assets/parts/knob.glb                procedural EC11 knob (13x13, knurl)
  assets/parts/screw.glb               procedural M2 pan-head
  assets/placements.json               every footprint (ref,x,y,rot) parsed
                                       from the COMMITTED boards and converted
                                       to the DESIGN frame (y-up; see below)
  assets/PROVENANCE.json               tool versions + source hashes
"""
import json
import math
import os
import re
import subprocess
import sys
import hashlib
from shutil import copy2, which as _which

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.environ.get("H44_RENDER_ASSETS",
                     os.path.join(REPO, "generated", "renders", "assets"))
KICAD_CLI = (os.environ.get("KICAD_CLI")
             or _which("kicad-cli")
             or "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli")
KEYCAP_DIR = os.environ.get("KEYCAP_DIR", "/tmp/kbd-renders/keycaps")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def r2(x):
    return round(float(x), 2)


# ------------------------------------------------------------- PCB -> glb

def export_pcb_step(half, dst):
    args = [KICAD_CLI, "pcb", "export", "step",
            "--include-tracks", "--include-pads", "--include-zones",
            "--include-soldermask", "--include-silkscreen",
            "-f", "-o", dst,
            os.path.join(REPO, "pcb", "kicad", f"Hojicha44-{half}.kicad_pcb")]
    r = subprocess.run(args, capture_output=True, text=True)
    # kicad-cli exits 2 when VRML component models cannot embed in STEP
    # ("Cannot use VRML models when exporting to non-mesh formats") while
    # still writing the file — the sockets/nano/slide-switch envelopes are
    # VRML, and they are hidden under the plate in renders anyway. The
    # artifact existing is the contract; the return code is not.
    if r.returncode != 0 and not (os.path.exists(dst)
                                  and os.path.getsize(dst) > 1_000_000):
        sys.exit(f"kicad-cli STEP export failed for {half}:\n{r.stderr[-800:]}")
    if r.returncode != 0:
        print("    (VRML component models skipped by kicad-cli — expected)")
    print(f"  pcb step: {dst} ({os.path.getsize(dst) // 1024} KiB)")


def step_to_named_glb(step_path, glb_path, tess_tol=0.12, weld=False):
    """Convert a STEP (possibly multi-solid, KiCad-named) to glTF with named
    nodes. Uses OCCT's CAF reader so footprint reference names survive.

    weld=True merges coincident vertices. OCCT triangulates face-by-face
    with duplicated vertices, which forces flat shading; welding is what
    lets Blender's smooth-by-angle show the keycaps' curved tops as
    curves instead of facets."""
    from OCP.STEPCAFControl import STEPCAFControl_Reader
    from OCP.TDocStd import TDocStd_Document
    from OCP.TCollection import TCollection_ExtendedString
    from OCP.XCAFDoc import XCAFDoc_DocumentTool
    from OCP.TDF import TDF_LabelSequence
    from OCP.TDataStd import TDataStd_Name
    from OCP.IFSelect import IFSelect_RetDone
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopAbs import TopAbs_FACE
    from OCP.TopoDS import TopoDS
    from OCP.BRep import BRep_Tool
    from OCP.TopLoc import TopLoc_Location
    import trimesh
    import numpy as np

    doc = TDocStd_Document(TCollection_ExtendedString("kbddoc"))
    reader = STEPCAFControl_Reader()
    reader.SetNameMode(True)
    reader.SetColorMode(False)
    if reader.ReadFile(step_path) != IFSelect_RetDone:
        sys.exit(f"cannot read {step_path}")
    reader.Transfer(doc)
    tool = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())

    labels = TDF_LabelSequence()
    tool.GetFreeShapes(labels)

    def label_name(lab, fallback):
        attr = TDataStd_Name()
        if lab.FindAttribute(TDataStd_Name.GetID_s(), attr):
            s = attr.Get().ToExtString()
            return s if s else fallback
        return fallback

    scene = trimesh.Scene()
    used = {}

    def add_shape(shape, name):
        # tessellate this shape in place, then harvest triangles per face
        BRepMesh_IncrementalMesh(shape, tess_tol, False, 0.35, True)
        verts, faces = [], []
        exp = TopExp_Explorer(shape, TopAbs_FACE)
        seen = 0
        while exp.More():
            face = TopoDS.Face_s(exp.Current())
            loc = TopLoc_Location()
            tris = BRep_Tool.Triangulation_s(face, loc)
            if tris is not None and tris.NbNodes() > 0:
                trsf = loc.Transformation()
                base = len(verts)
                for i in range(1, tris.NbNodes() + 1):
                    p = tris.Node(i).Transformed(trsf)
                    verts.append((p.X(), p.Y(), p.Z()))
                for i in range(1, tris.NbTriangles() + 1):
                    t = tris.Triangle(i)
                    a, b, c = t.Get()
                    faces.append((base + a - 1, base + b - 1, base + c - 1))
                seen += 1
            exp.Next()
        if not faces:
            return
        key = name
        n = used.get(key, 0)
        used[key] = n + 1
        if n:
            key = f"{name}#{n + 1}"
        import trimesh as _t
        mesh = _t.Trimesh(vertices=verts, faces=faces, process=False)
        if weld:
            n0 = len(mesh.vertices)
            mesh.merge_vertices()
            print(f"    weld {key}: {n0} -> {len(mesh.vertices)} verts")
        scene.add_geometry(mesh, node_name=key, geom_name=key)

    def walk(lab, depth=0):
        # assemblies: descend into component (instance) labels — each keeps
        # its own name + world location; leaves are tessellated as-is
        if tool.IsAssembly_s(lab):
            comps = TDF_LabelSequence()
            tool.GetComponents_s(lab, comps)
            if comps.Length() == 0:
                add_shape(tool.GetShape_s(lab), label_name(lab, f"asm{depth}"))
                return
            for i in range(1, comps.Length() + 1):
                walk(comps.Value(i), depth + 1)
        else:
            add_shape(tool.GetShape_s(lab), label_name(lab, f"leaf{depth}"))

    for i in range(1, labels.Length() + 1):
        walk(labels.Value(i))

    scene.export(glb_path)
    print(f"  glb: {glb_path} ({len(scene.geometry)} named geoms, "
          f"{os.path.getsize(glb_path) // 1024} KiB)")


# ------------------------------------------------------------- plate -> glb

def plate_glb(half, glb_path):
    """Extrude the tracked DXF: OUTLINE 1.2mm, CUTOUT through,
    RELIEF pockets 0.55 deep from the underside (z=0..0.55), PORON ignored
    (it is a punch template, not a cut)."""
    import ezdxf
    import cadquery as cq
    import trimesh

    doc = ezdxf.readfile(os.path.join(REPO, "plate",
                                      f"Hojicha44-{half}-plate.dxf"))
    msp = doc.modelspace()

    def poly_pts(e):
        if e.dxftype() == "LWPOLYLINE":
            return [(p[0], p[1]) for p in e.get_points()]
        if e.dxftype() == "POLYLINE":
            return [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices]
        return None

    outline, cutouts, reliefs = None, [], []
    for e in msp:
        pts = poly_pts(e)
        if pts is None:
            continue
        if e.dxf.layer == "OUTLINE":
            outline = pts
        elif e.dxf.layer == "CUTOUT":
            cutouts.append(pts)
        elif e.dxf.layer == "RELIEF":
            reliefs.append(pts)
    assert outline, "no OUTLINE polyline"
    plate = (cq.Workplane("XY")
             .polyline(outline).close()
             .extrude(1.2))
    for pts in cutouts:
        plate = plate.cut(cq.Workplane("XY").polyline(pts).close()
                          .extrude(1.3).translate((0, 0, -0.05)))
    for pts in reliefs:
        plate = plate.cut(cq.Workplane("XY").polyline(pts).close()
                          .extrude(0.55))
    # The DXF is authored in the design frame (y up) — the same frame the
    # board STEP export and the case STLs use — so export the plate exactly
    # as written, with no flip.
    shape = plate.val()
    verts, faces = [], []
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopAbs import TopAbs_FACE
    from OCP.TopoDS import TopoDS
    from OCP.BRep import BRep_Tool
    from OCP.TopLoc import TopLoc_Location
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    BRepMesh_IncrementalMesh(shape.wrapped, 0.1, False, 0.3, True)
    exp = TopExp_Explorer(shape.wrapped, TopAbs_FACE)
    while exp.More():
        face = TopoDS.Face_s(exp.Current())
        loc = TopLoc_Location()
        tris = BRep_Tool.Triangulation_s(face, loc)
        if tris is not None:
            trsf = loc.Transformation()
            base = len(verts)
            for i in range(1, tris.NbNodes() + 1):
                p = tris.Node(i).Transformed(trsf)
                verts.append((p.X(), p.Y(), p.Z()))
            for i in range(1, tris.NbTriangles() + 1):
                a, b, c = tris.Triangle(i).Get()
                faces.append((base + a - 1, base + b - 1, base + c - 1))
        exp.Next()
    mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
    scene = trimesh.Scene({f"plate_{half}": mesh})
    scene.export(glb_path)
    bb = mesh.bounds
    print(f"  plate glb: {glb_path}  bbox x {bb[0][0]:.1f}..{bb[1][0]:.1f} "
          f"y {bb[0][1]:.1f}..{bb[1][1]:.1f} z {bb[0][2]:.2f}..{bb[1][2]:.2f}")


def cutouts_json(dst):
    """Plate CUTOUT polygons in the DESIGN frame — exactly the coordinates
    written in the tracked DXF. No origin offsets, no y flip: this file is
    a straight transcription so the plate holes can act as the render's
    registration master.

    Each item: center (x, y), bbox (w, h) and `angle` = longest-edge
    direction folded to (-45, 45]. For the 18 axis-aligned finger holes
    angle=0; the four thumb holes carry the real fan angle (0.5/13.5/
    27.5/41.5 deg) and the scene rotates those caps with the holes. The
    scene asserts that every switch footprint lands on one of these
    centers (<= 0.05 mm) before rendering."""
    import ezdxf
    import math
    out = {}
    for half in ("Left", "Right"):
        doc = ezdxf.readfile(os.path.join(REPO, "plate",
                                          f"Hojicha44-{half}-plate.dxf"))
        items = []
        for e in doc.modelspace():
            if e.dxf.layer != "CUTOUT":
                continue
            pts = ([(p[0], p[1]) for p in e.get_points()]
                   if e.dxftype() == "LWPOLYLINE"
                   else [(v.dxf.location.x, v.dxf.location.y)
                         for v in e.vertices])
            # bbox center — NOT the vertex mean: the closed POLYLINEs carry
            # a duplicated first vertex, which biases a mean by (w/10, h/10)
            cx = (max(p[0] for p in pts) + min(p[0] for p in pts)) / 2
            cy = (max(p[1] for p in pts) + min(p[1] for p in pts)) / 2
            # rotation from the longest polygon edge (squares are exact)
            best_len, ang = 0.0, 0.0
            for i in range(len(pts)):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % len(pts)]
                ln = math.hypot(x1 - x0, y1 - y0)
                if ln > best_len:
                    best_len = ln
                    ang = math.degrees(math.atan2(y1 - y0, x1 - x0)) % 90.0
            if ang > 45.0:
                ang -= 90.0
            items.append({"x": r2(cx), "y": r2(cy),
                          "w": r2(max(p[0] for p in pts)
                                  - min(p[0] for p in pts)),
                          "h": r2(max(p[1] for p in pts)
                                  - min(p[1] for p in pts)),
                          "angle": r2(ang)})
        out[half] = items
        print(f"  cutouts {half}: {len(items)} polygons (design frame, raw DXF)")
    with open(dst, "w") as f:
        json.dump(out, f, indent=1)


# ------------------------------------------------------------- knob + screw

def knob_glb(glb_path):
    """EC11 knob, low-profile edition (user review 2026-10-24: "after you
    find a shorter shafted encoder, add a knob to it — not too tall, not
    too thin, not too fat"; the previous 13x13 sat high on the 20mm
    shaft and read as visually too tall). Sized for the short-shaft
    EC11-class BOM primary on a 5.2mm case rim:
      - OD 16.8, height 9.2: skirt bottom lands rim+0.9 = 6.1 abs
        (EC11 push travel 0.5 +/- 0.3: the skirt must clear the 5.2mm
        cover even at full press), the crown reaches ~15.3 — a touch
        above the 11.14 cap tops
      - 18 vertical grip ridges (0.9 grooves on the OD, 0.45 deep)
      - 0.5 chamfer at the skirt base, 1.0 chamfer on the crown
      - z=0 is the skirt bottom, centred on the shaft axis
      - D-bore not modelled (hidden inside the skirt)
    """
    import math
    import cadquery as cq
    import trimesh
    knob = (cq.Workplane("XY").circle(8.4).extrude(9.2)
            .edges("<Z").chamfer(0.5)
            .edges(">Z").chamfer(1.0))
    for i in range(18):
        a = 2 * math.pi * i / 18
        knob = knob.cut(
            cq.Workplane("XY")
            .center(8.4 * math.cos(a), 8.4 * math.sin(a))
            .circle(0.45).extrude(9.2))
    verts, faces = [], []
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopAbs import TopAbs_FACE
    from OCP.TopoDS import TopoDS
    from OCP.BRep import BRep_Tool
    from OCP.TopLoc import TopLoc_Location
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    shape = knob.val().wrapped
    BRepMesh_IncrementalMesh(shape, 0.08, False, 0.3, True)
    exp = TopExp_Explorer(shape, TopAbs_FACE)
    while exp.More():
        face = TopoDS.Face_s(exp.Current())
        loc = TopLoc_Location()
        tris = BRep_Tool.Triangulation_s(face, loc)
        if tris is not None:
            trsf = loc.Transformation()
            base = len(verts)
            for i in range(1, tris.NbNodes() + 1):
                p = tris.Node(i).Transformed(trsf)
                verts.append((p.X(), p.Y(), p.Z()))
            for i in range(1, tris.NbTriangles() + 1):
                a, b, c = tris.Triangle(i).Get()
                faces.append((base + a - 1, base + b - 1, base + c - 1))
        exp.Next()
    mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
    mesh.merge_vertices()
    scene = trimesh.Scene({"knob": mesh})
    scene.export(glb_path)
    print(f"  knob glb: {glb_path} ({len(mesh.faces)} tris, "
          f"{len(mesh.vertices)} verts)")


def screw_glb(glb_path):
    """M2x6 pan-head + 0.8mm hex socket suggestion (procedural)."""
    import cadquery as cq
    import trimesh
    head = (cq.Workplane("XY").circle(1.9).extrude(0.9)
            .edges(">Z").fillet(0.25))
    socket = (cq.Workplane("XY").workplane(offset=0.4)
              .circle(0.6).extrude(0.5))
    head = head.cut(socket)
    # round 20: the shank extruded UPWARD through the head (a pin, not
    # a screw) — build it downward: z -6..0
    shank = (cq.Workplane("XY").circle(1.0).extrude(6.0)
             .translate((0, 0, -6.0)))
    screw = head.union(shank)
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopAbs import TopAbs_FACE
    from OCP.TopoDS import TopoDS
    from OCP.BRep import BRep_Tool
    from OCP.TopLoc import TopLoc_Location
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    verts, faces = [], []
    shape = screw.val().wrapped
    BRepMesh_IncrementalMesh(shape, 0.05, False, 0.25, True)
    exp = TopExp_Explorer(shape, TopAbs_FACE)
    while exp.More():
        face = TopoDS.Face_s(exp.Current())
        loc = TopLoc_Location()
        tris = BRep_Tool.Triangulation_s(face, loc)
        if tris is not None:
            trsf = loc.Transformation()
            base = len(verts)
            for i in range(1, tris.NbNodes() + 1):
                p = tris.Node(i).Transformed(trsf)
                verts.append((p.X(), p.Y(), p.Z()))
            for i in range(1, tris.NbTriangles() + 1):
                a, b, c = tris.Triangle(i).Get()
                faces.append((base + a - 1, base + b - 1, base + c - 1))
        exp.Next()
    mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
    mesh.merge_vertices()
    scene = trimesh.Scene({"screw": mesh})
    scene.export(glb_path)
    print(f"  screw glb: {glb_path}")


# ------------------------------------------------------ choc + artisan

def add_cad_mesh(scene, name, part):
    """Add a named CadQuery workplane result to a millimetre-scale scene."""
    import cadquery as cq
    import trimesh

    solids = part.vals()
    shape = solids[0] if len(solids) == 1 else cq.Compound.makeCompound(solids)
    vertices, faces = shape.tessellate(0.035, 0.18)
    mesh = trimesh.Trimesh(vertices=[v.toTuple() for v in vertices], faces=faces)
    scene.add_geometry(mesh, node_name=name, geom_name=name)


def choc_glb(glb_path):
    """PG1350 render model. Origin is the switch centre at the PCB top."""
    import cadquery as cq
    import trimesh

    def box(width, depth, height, x=0, y=0, z=0):
        return cq.Workplane("XY").box(width, depth, height).translate((x, y, z))

    def round_box(width, depth, height, radius, z):
        return box(width, depth, height, z=z).edges("|Z").fillet(radius)

    def post(x, y, radius, depth):
        return cq.Workplane("XY").center(x, y).circle(radius).extrude(-depth)

    # Two mouldings form a stepped shell with a visible parting line.
    base = round_box(13.8, 13.8, 2.20, 0.42, 1.10)
    base = base.edges("<Z").chamfer(0.18)
    base = base.union(post(0, 0, 1.7, 2.5))
    for x in (-5.5, 5.5):
        base = base.union(post(x, 0, 0.91, 1.8))
        side = math.copysign(1, x)
        clip = box(1.02, 4.0, 1.15, x=side * 6.78, z=1.25)
        base = base.union(clip.edges("|Y").chamfer(0.16))

    # The 14.8 mm flange seats on the plate. The cap legs engage a broad
    # twin-slot slider inside a recessed opening in the upper moulding.
    flange = round_box(14.8, 14.8, 0.68, 0.65, 2.54)
    lid = round_box(13.70, 13.70, 1.52, 0.72, 3.56)
    lid = lid.edges(">Z").chamfer(0.43)
    lid = flange.union(lid)
    lid = lid.cut(round_box(9.2, 5.3, 3.5, 0.62, 3.4))
    lid = lid.cut(box(3.9, 3.0, 1.50, y=6.1, z=3.76))  # LED opening
    for x in (-6.5, 6.5):
        lid = lid.cut(box(0.96, 2.4, 1.1, x=x, z=3.2))  # moulded latch recess

    stem = round_box(8.68, 4.85, 3.05, 0.50, 3.54)
    stem = stem.edges(">Z").chamfer(0.18)
    for x in (-2.85, 2.85):
        stem = stem.cut(box(1.31, 3.09, 4.2, x=x, z=3.72))
    pins = box(0.80, 0.46, 3.22, y=5.9, z=-1.53).edges("<Z").chamfer(0.12)
    pins = pins.add(
        box(0.80, 0.46, 3.22, x=5.0, y=3.8, z=-1.53)
        .edges("<Z").chamfer(0.12))

    scene = trimesh.Scene()
    for name, part in (("base", base), ("housing", lid),
                       ("stem", stem), ("contacts", pins)):
        add_cad_mesh(scene, f"choc_{name}", part)
    scene.export(glb_path)


def nano_glb(glb_path):
    """Photograph-based nice!nano v2 render model, centred over its sockets.

    Reference: https://nicekeyboards.com/docs/nice-nano/
    """
    import cadquery as cq
    import numpy as np
    import trimesh

    def block(w, d, h, x=0, y=0, z=0):
        return cq.Workplane("XY").box(w, d, h).translate((x, y, z))

    pins = [(sign * 7.62, (i - 5.5) * 2.54)
            for sign in (-1, 1) for i in range(12)]
    pins += [(-6.55, 15.10), (6.55, 15.10)]
    body = block(17.8, 33.0, 1.6, z=3.2).edges("|Z").fillet(0.55)
    body = body.faces(">Z").workplane(centerOption="CenterOfBoundBox").pushPoints(pins).hole(1.16)
    body = body.cut(block(8.9, 4.7, 2.1, y=15.1, z=3.2))
    plated_holes = (cq.Workplane("XY").workplane(offset=2.38).pushPoints(pins)
                    .circle(0.91).circle(0.54).extrude(1.64, combine=False))

    # Round-ended mid-mount USB-C shell and a recessed contact tongue.
    shell = block(8.85, 5.30, 3.15, y=14.4, z=3.2).edges("|Y").fillet(0.71)
    cavity = block(7.95, 4.3, 2.34, y=15.3, z=3.2).edges("|Y").fillet(0.61)
    shell = shell.cut(cavity)
    tongue = block(6.5, 3.5, 0.67, y=14.9, z=3.2).edges("|Y").fillet(0.19)
    shell_contacts = cq.Workplane("XY")
    for i in range(12):
        shell_contacts = shell_contacts.add(
            block(0.29, 1.65, 0.035, x=(i - 5.5) * 0.50, y=15.35, z=3.55).val())
    pads = plated_holes.add(shell_contacts.vals())

    # Photo-matched component types and proportions. Keep the mask clean.
    packages = block(6.9, 6.9, 0.75, y=-1.8, z=4.40).edges(">Z").chamfer(0.11)
    packages = packages.add(block(3.05, 3.05, 0.64, x=-2.45, y=8.05, z=4.34).val())
    packages = packages.add(block(2.1, 2.35, 0.56, x=3.7, y=7.25, z=4.30).val())
    crystal = block(3.20, 2.48, 0.55, x=3.85, y=3.13, z=4.30).edges("|Z").fillet(0.25)
    crystal = crystal.add(block(1.60, 1.18, 0.42, x=-3.7, y=-8.25, z=4.23).val())
    ceramic = block(4.4, 1.55, 0.80, x=0.85, y=-14.15, z=4.42)
    smd_ends = cq.Workplane("XY")
    for x, y in ((-5.0, 9.3), (3.7, 10.5), (5.3, 5.5), (4.8, -2.2),
                 (5.3, -5.8), (3.0, -8.6), (-2.35, -9.9), (-0.3, -7.4),
                 (-4.9, -4.7), (-5.1, 2.9), (-1.7, 4.2), (0.95, 6.35),
                 (-5.25, 11.65), (5.25, 11.65), (3.9, -11.0)):
        ceramic = ceramic.add(block(0.85, 0.49, 0.31, x=x, y=y, z=4.17).val())
        for dx in (-0.485, 0.485):
            smd_ends = smd_ends.add(block(0.24, 0.53, 0.33, x=x+dx, y=y, z=4.17).val())
    # Pin-one dimple and the little programming pad row at the antenna end.
    packages = packages.cut(block(0.48, 0.48, 0.11, x=-2.75, y=0.98, z=4.77))
    for x in (-4.85, -2.84, -0.83):
        pads = pads.add(block(1.02, 1.12, 0.028, x=x, y=-11.9, z=4.015).val())
    socket = block(2.45, 29.7, 2.40, x=-7.62, z=1.20).edges("|Z").fillet(0.18)
    socket = socket.add(block(2.45, 29.7, 2.40, x=7.62, z=1.20).edges("|Z").fillet(0.18).val())

    # Render layout following the component-side reference. Top-layer
    # routes run from lands to parts or disappear at vias; the antenna
    # end beyond the test pads has no signal fan-out.
    gpio = (
        ((-7.62, 3.81), (-6.10, 3.81), (-5.47, 3.18), (-5.47, 1.79), (-4.63, 0.95), (-3.20, 0.95)),
        ((-7.62, 1.27), (-6.28, 1.27), (-5.55, 0.54), (-4.81, 0.54), (-4.35, 0.08), (-3.20, 0.08)),
        ((-7.62, -1.27), (-5.92, -1.27), (-5.42, -0.77), (-3.20, -0.77)),
        ((-7.62, -3.81), (-6.77, -3.81), (-6.29, -3.33), (-5.41, -3.33), (-4.25, -2.17), (-3.20, -2.17)),
        ((-7.62, -6.35), (-6.56, -6.35), (-5.97, -5.76), (-5.97, -5.26), (-5.41, -4.70)),
        ((-4.41, -4.70), (-4.10, -4.70), (-3.85, -4.45), (-3.85, -3.43), (-3.20, -2.78)),
        ((-7.62, -8.89), (-6.36, -8.89), (-5.80, -8.33), (-5.80, -7.47), (-5.10, -6.77)),
        ((-7.62, -11.43), (-6.49, -11.43), (-6.02, -11.90), (-4.85, -11.90)),
        ((7.62, -1.27), (6.10, -1.27), (5.30, -0.47), (3.20, -0.47)),
        ((7.62, -3.81), (6.28, -3.81), (5.61, -3.14), (4.93, -3.14), (4.57, -2.78), (3.20, -2.78)),
        ((7.62, -6.35), (6.28, -6.35), (5.78, -5.85)),
        ((4.82, -5.80), (4.24, -5.80), (3.82, -5.38), (3.82, -4.14), (3.20, -3.52)),
        ((7.62, -8.89), (5.10, -8.89), (4.59, -9.40), (4.59, -9.94)),
        ((7.62, -11.43), (6.62, -11.43), (6.26, -11.07), (4.38, -11.00)),
        ((3.42, -11.00), (2.00, -11.00), (1.10, -11.90), (-0.83, -11.90)),
    )
    for dx in (-0.21, 0.21):
        gpio += (tuple((x + dx, y) for x, y in (
            (0.70, 12.25), (0.70, 10.51), (1.58, 9.63), (1.58, 5.28),
            (0.46, 4.16), (0.46, 1.14))),)
    power = (
        ((6.55, 15.10), (6.55, 11.12), (5.93, 10.50), (4.18, 10.50)),
        ((3.22, 10.50), (2.61, 10.50), (2.21, 10.10)),
        ((-6.55, 15.10), (-6.55, 12.86), (-5.97, 12.28), (-5.97, 11.88), (-5.73, 11.65)),
        ((7.62, 8.89), (5.62, 8.89), (4.62, 7.89), (4.62, 7.25)),
        ((2.75, 7.25), (2.51, 7.25), (2.27, 7.01)),
        ((-5.48, 9.30), (-5.93, 8.85), (-5.93, 8.54), (-5.32, 7.93), (-3.72, 7.93)),
        ((-3.95, -8.30), (-3.95, -6.88), (-2.37, -5.30), (-2.37, -4.96)),
        ((-0.30, -5.05), (-0.30, -5.69), (-0.79, -6.18), (-0.79, -7.40)),
    )
    trace_meshes = []
    for routes, width in ((gpio, 0.24), (power, 0.32)):
        for route in routes:
            points = np.asarray(route)
            segments = np.diff(points, axis=0)
            normals = segments[:, [1, 0]] * (-1, 1)
            normals /= np.linalg.norm(normals, axis=1)[:, None]
            # A shared miter at each bend keeps the strip continuous.
            miters = (normals[:-1] + normals[1:]) / (
                1 + (normals[:-1] * normals[1:]).sum(axis=1)[:, None])
            offsets = np.vstack((normals[0], miters, normals[-1])) * (width / 2)
            vertices = np.column_stack((np.stack((points + offsets, points - offsets), axis=1)
                                        .reshape(-1, 2), np.full(2 * len(points), 4.009)))
            faces = [(i, i + 1, i + 2) for i in range(0, len(vertices) - 2, 2)]
            faces += [(i + 1, i + 3, i + 2) for i in range(0, len(vertices) - 2, 2)]
            trace_meshes.append(trimesh.Trimesh(vertices=vertices, faces=faces, process=False))
    via_centres = ((-5.10, -6.77), (4.59, -9.94), (2.21, 10.10), (2.27, 7.01),
                   (-0.31, 7.44), (5.90, 1.61), (-4.37, 5.23))
    vias = (cq.Workplane("XY").workplane(offset=4.009).pushPoints(via_centres)
            .circle(0.245).circle(0.102).extrude(0.019, combine=False))

    scene = trimesh.Scene()
    for name, part in (("mask", body), ("gold", pads), ("shell", shell),
                       ("tongue", tongue), ("packages", packages),
                       ("crystal", crystal), ("ceramic", ceramic),
                       ("smd_ends", smd_ends), ("socket", socket), ("vias", vias)):
        add_cad_mesh(scene, "nano_" + name, part)
    scene.add_geometry(trimesh.util.concatenate(trace_meshes),
                       node_name="nano_traces", geom_name="nano_traces")
    scene.export(glb_path)


def artisan_glb(glb_path):
    """Sculpted artisan accent cap on the Saddle-family foot — the same
    17.48 x 16.48 plan and base plane (z=0) as the KLP caps it replaces,
    total height ~9.5:
      - dome: sphere R=11 centred at z -3 and cut at the base plane ->
        an 8mm dome cap height, apex at z +8.0
      - the plan prism clips the sphere's bulge, so the walls stay at
        the plan up to the crease at ~z 3.7..4.3 (the clean skirt,
        blending into the dome); a 1.4mm foot slab of the same plan
        restores the full family foot where the sphere misses the
        corners
      - three concentric ridge rings (tori bedded 0.30 deep along the
        surface normal, tube radius 0.75 -> 0.45mm relief, above the
        0.4mm that must still read at ~0.2 mm/px) and a centre button
        dot topping out at z ~9.45
    """
    import math
    import cadquery as cq
    import numpy as np
    import trimesh
    from OCP.BRepPrimAPI import BRepPrimAPI_MakeSphere, BRepPrimAPI_MakeTorus
    from OCP.gp import gp_Ax2, gp_Dir, gp_Pnt

    R, CZ = 11.0, -3.0
    dome = cq.Shape.cast(BRepPrimAPI_MakeSphere(gp_Pnt(0, 0, CZ), R).Shape())
    prism = (cq.Workplane("XY")
             .box(17.48, 16.48, 10.0, centered=(True, True, False))
             .edges("|Z").fillet(2.5)).val()
    cap = dome.intersect(prism)
    # foot slab: the sphere never reaches the plan corners, so bed the
    # clip on 1.4mm of the full rounded-rect plan
    foot = (cq.Workplane("XY")
            .box(17.48, 16.48, 1.4, centered=(True, True, False))
            .edges("|Z").fillet(2.5)).val()
    cap = cap.fuse(foot)
    # three concentric ridge rings, bedded 0.30 deep along the surface
    # normal so 0.45mm of each tube stands proud of the dome
    bed = 0.30
    for z_ring in (5.2, 6.4, 7.35):
        r = math.sqrt(R * R - (z_ring - CZ) ** 2)
        major = r * (1.0 - bed / R)
        cz = z_ring - bed * (z_ring - CZ) / R
        cap = cap.fuse(cq.Shape.cast(BRepPrimAPI_MakeTorus(
            gp_Ax2(gp_Pnt(0, 0, cz), gp_Dir(0, 0, 1)), major, 0.75).Shape()))
    # centre button dot
    cap = cap.fuse(cq.Shape.cast(
        BRepPrimAPI_MakeSphere(gp_Pnt(0, 0, 7.45), 2.0).Shape()))
    cap = cap.clean()
    verts, faces = [], []
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopAbs import TopAbs_FACE
    from OCP.TopoDS import TopoDS
    from OCP.BRep import BRep_Tool
    from OCP.TopLoc import TopLoc_Location
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    shape = cap.wrapped
    BRepMesh_IncrementalMesh(shape, 0.02, False, 0.2, True)
    exp = TopExp_Explorer(shape, TopAbs_FACE)
    while exp.More():
        face = TopoDS.Face_s(exp.Current())
        loc = TopLoc_Location()
        tris = BRep_Tool.Triangulation_s(face, loc)
        if tris is not None:
            trsf = loc.Transformation()
            base = len(verts)
            for i in range(1, tris.NbNodes() + 1):
                p = tris.Node(i).Transformed(trsf)
                verts.append((p.X(), p.Y(), p.Z()))
            for i in range(1, tris.NbTriangles() + 1):
                a, b, c = tris.Triangle(i).Get()
                faces.append((base + a - 1, base + b - 1, base + c - 1))
        exp.Next()
    mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
    mesh.merge_vertices()
    # the button sphere's pole leaves one zero-area seam triangle after
    # the weld — drop degenerate faces so the cap exports watertight
    mesh.update_faces(trimesh.triangles.area(mesh.triangles) > 1e-8)
    mesh.remove_unreferenced_vertices()
    scene = trimesh.Scene({"artisan": mesh})
    scene.export(glb_path)
    bb = mesh.bounds
    print(f"  artisan glb: {glb_path} ({len(mesh.faces)} tris, "
          f"{len(mesh.vertices)} verts, bbox "
          f"{bb[1][0] - bb[0][0]:.2f} x {bb[1][1] - bb[0][1]:.2f} x "
          f"{bb[1][2] - bb[0][2]:.2f} mm)")


# ------------------------------------------------------------- placements

def placements_json(dst):
    """Every footprint of the COMMITTED boards, converted to the DESIGN
    frame (x right, y up) — the frame of the board STEP export, the plate
    DXF and the case STLs.

    KiCad stores boards y-down, and kicad-cli's STEP export negates y
    (verified: Edge.Cuts y -60.00..54.63 -> STEP/glb y -54.63..60.00).
    The plate/case generators author in the same design frame, so:
        x_design = x_file,  y_design = -y_file
    `x_file`/`y_file`/`rot` are kept for provenance and for the
    nice!nano courtyard transform (which must be applied in the file
    frame before the y flip)."""
    sys.path.insert(0, os.path.join(REPO, "pcb", "generators"))
    import audit_silk as A
    placements = {}
    for half in ("Left", "Right"):
        path = os.path.join(REPO, "pcb", "kicad", f"Hojicha44-{half}.kicad_pcb")
        out = []
        for ref, fx, fy, frot, blk in A.footprints(path):
            out.append({"ref": ref,
                        "x": r2(fx), "y": r2(-fy),      # design frame
                        "x_file": r2(fx), "y_file": r2(fy),
                        "rot": float(frot)})
        placements[half] = out
        print(f"  placements {half}: {len(out)} footprints (design frame)")
    with open(dst, "w") as f:
        json.dump(placements, f, indent=1)


# ------------------------------------------------------------- main

def main():
    os.makedirs(OUT, exist_ok=True)
    for sub in ("board", "plate", "case", "parts"):
        os.makedirs(os.path.join(OUT, sub), exist_ok=True)

    print("== 1. PCB STEP exports (kicad-cli, read-only on the boards)")
    for half in ("Left", "Right"):
        step = os.path.join(OUT, "board", f"Hojicha44-{half}.step")
        export_pcb_step(half, step)

    print("== 2. PCB STEP -> named glTF")
    for half in ("Left", "Right"):
        step_to_named_glb(os.path.join(OUT, "board", f"Hojicha44-{half}.step"),
                          os.path.join(OUT, "board", f"Hojicha44-{half}.glb"))

    print("== 3. plates from the tracked DXF")
    for half in ("Left", "Right"):
        plate_glb(half, os.path.join(OUT, "plate", f"Hojicha44-{half}.glb"))

    case_dir = os.environ.get("CASE_OUT", os.path.join(REPO, "case", "out"))
    print(f"== 4. case solids (convert from {os.path.relpath(case_dir, REPO)})")
    import trimesh
    for half in ("Left", "Right"):
        for part in ("tub", "cover"):
            src = os.path.join(case_dir, f"Hojicha44-{half}-{part}.stl")
            mesh = trimesh.load(src, force="mesh")
            scene = trimesh.Scene({f"{part}_{half}": mesh})
            dst = os.path.join(OUT, "case", f"Hojicha44-{half}-{part}.glb")
            scene.export(dst)
            bb = mesh.bounds
            print(f"  {half}-{part}: bbox x {bb[0][0]:.1f}..{bb[1][0]:.1f} "
                  f"y {bb[0][1]:.1f}..{bb[1][1]:.1f} z {bb[0][2]:.1f}..{bb[1][2]:.1f}")

    print("== 5. keycaps (KLP Lame, pinned download) -> glb")
    cached_parts = os.environ.get("H44_KEYCAP_MESHES")
    if cached_parts:
        provenance_path = os.path.join(os.path.dirname(cached_parts), "PROVENANCE.json")
        with open(provenance_path) as f:
            pinned_commit = json.load(f)["keycaps"]["pinned_commit"]
    else:
        with open(os.path.join(KEYCAP_DIR, "PINNED_SOURCE.txt")) as f:
            pinned_commit = f.read().strip()
    for v in ("Saddle", "Saddle_Tilted", "Saddle_Homing", "Normal",
              "Normal_Homing", "Normal_Tilted",
              "Thumb"):
        dst = os.path.join(OUT, "parts", f"klp_{v.lower()}.glb")
        if cached_parts:
            copy2(os.path.join(cached_parts, os.path.basename(dst)), dst)
            continue
        src = os.path.join(KEYCAP_DIR, f"klp_{v}.step")
        if not os.path.exists(src):
            sys.exit(f"missing keycap source {src} — run the fetch step")
        step_to_named_glb(src, dst, tess_tol=0.012, weld=True)

    print("== 6. knob + screw (procedural)")
    knob_glb(os.path.join(OUT, "parts", "knob.glb"))
    screw_glb(os.path.join(OUT, "parts", "screw.glb"))

    print("== 6b. choc switch + artisan cap (procedural)")
    choc_glb(os.path.join(OUT, "parts", "choc.glb"))
    nano_glb(os.path.join(OUT, "parts", "nano.glb"))
    artisan_glb(os.path.join(OUT, "parts", "artisan.glb"))

    print("== 7. placements (design frame) + plate cutout centers (raw DXF)")
    placements_json(os.path.join(OUT, "placements.json"))
    cutouts_json(os.path.join(OUT, "cutouts.json"))

    print("== 8. provenance")
    prov = {
        "boards": {
            half: sha256(os.path.join(REPO, "pcb", "kicad", f"Hojicha44-{half}.kicad_pcb"))
            for half in ("Left", "Right")
        },
        "keycaps": {
            "project": "braindefender/KLP-Lame-Keycaps",
            "license": "CC-BY-SA-4.0 (attribution required)",
            "pinned_commit": pinned_commit,
            "files": [f"klp_{v}.step" for v in ("Saddle", "Saddle_Tilted",
                      "Saddle_Homing", "Normal", "Normal_Homing",
                      "Normal_Tilted", "Thumb")],
        },
        "tools": {
            "kicad_cli": subprocess.run([KICAD_CLI, "version"],
                                        capture_output=True,
                                        text=True).stdout.strip(),
            "cadquery": __import__("cadquery").__version__,
            "trimesh": trimesh.__version__,
            "python": sys.version.split()[0],
        },
    }
    with open(os.path.join(OUT, "PROVENANCE.json"), "w") as f:
        json.dump(prov, f, indent=1)
    print(json.dumps(prov["tools"], indent=1))


if __name__ == "__main__":
    main()
