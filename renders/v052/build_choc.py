#!/usr/bin/env python3
"""v0.5.2 Choc v1 (PG1350) switch model — rebuilt from the Kailh
dimensions, replacing the v0.5.x box-with-internal-voids model that read
as a fake painted block.

Sources (see PROVENANCE):
  - ink.parts parametric record for CPG135001D01:
      waist 13.8x13.8, flange 15x15, cover-height 2.65, cover-taper 0.3,
      stem-base-z 2.35 / stem-top-z 5.0, stem-span 8.7,
      stem-arm-x 3 / stem-arm-y 1.2, plate-cutout 14x14,
      clip-width 4, peg-length 3, pin-length 3.3
  - KLP Lámen cap meshes actually used by the scene: the cap underside
    carries TWO LEGS at x=+-2.85, each ~1.07 (X) x ~2.87 (Y) x ~2.0 (Z),
    protruding ~1.8-2.1 below the cap skirt. The switch stem therefore
    has to be the WIDE slider (span 8.7) with two through-slots milled
    from the top at x=+-2.85 — "two narrow prongs" in the literature.

Frame: millimetres, z=0 at the PCB top, shaft axis at the origin — the
same convention as the v0.5.x choc.glb so scene.py placement is
unchanged. Exports two named geometries, `choc_housing` and
`choc_stem`, which the scene materials split into ivory housing and
charcoal stem.
"""
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(REPO, "generated", "renders", "assets-v052", "parts",
                   "choc.glb")


def _loft(z0, w0, d0, z1, w1, d1):
    """Drafted box: rect w0 x d0 at z0 tapering to w1 x d1 at z1."""
    import cadquery as cq
    return (cq.Workplane("XY").workplane(offset=z0).rect(w0, d0)
            .workplane(offset=z1 - z0).rect(w1, d1).loft())


def _box(x0, x1, y0, y1, z0, z1):
    import cadquery as cq
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0,
                                  centered=(True, True, False)
                                  ).translate(((x0 + x1) / 2,
                                               (y0 + y1) / 2, z0))


def build_housing():
    import cadquery as cq
    parts = []

    # lower shell: 13.8 square below the rim (xemstudio: "housing below
    # the top rim is 13.80"), slight draft, z -0.4..1.95
    parts.append(_loft(-0.4, 13.2, 13.2, 1.95, 13.9, 13.9))

    # locator post Ø3.4 into the PCB centre hole + two Ø1.9 guide
    # posts 11.00 apart on the centre line (Kailh v1 pattern)
    parts.append(cq.Workplane("XY").circle(1.7).extrude(2.85)
                 .translate((0, 0, -2.65)))
    for sy in (1, -1):
        parts.append(cq.Workplane("XY").center(0, 5.5 * sy)
                     .circle(0.95).extrude(2.2)
                     .translate((0, 0, -2.05)))

    # plate-retention clips: two 4mm tabs per side at plate level
    for sy in (1, -1):
        y_out = 7.35 * sy
        y_in = 6.50 * sy
        parts.append(_box(-2.0, 2.0, min(y_in, y_out), max(y_in, y_out),
                          0.7, 1.9))

    # upper housing: 15x15 flange resting on the plate top (z 2.20),
    # 13.8 waist rising with a slight inward draft to z 4.60
    parts.append(_loft(2.20, 15.0, 15.0, 2.72, 14.7, 14.7))
    parts.append(_loft(2.72, 14.7, 14.7, 4.60, 13.6, 13.6))

    housing = parts[0]
    for p in parts[1:]:
        housing = housing.union(p)
    housing = housing.clean()

    # LED window on the -Y face: a through-opening the LED light pipe
    # sits in (the wall is ~6.8-7.0 out at that height)
    import cadquery as cq2
    led_cut = (cq2.Workplane("XY")
               .workplane(offset=3.30)
               .center(0, -6.15)
               .rect(3.2, 1.5)
               .extrude(1.6))
    housing = housing.cut(led_cut)
    # soften the top rim
    try:
        housing = housing.edges(">Z").chamfer(0.35)
    except Exception:
        pass
    return housing


def build_stem():
    import cadquery as cq
    # wide slider: span 8.7 in X (stem-span), ~4.4 in Y, drafted
    stem = _loft(1.15, 8.7, 4.4, 4.55, 8.1, 4.0)
    # domed/rounded tip: cap the loft top with a shallow pyramid loft
    tip = (cq.Workplane("XY").rect(7.4, 3.4).workplane(offset=0.5)
           .rect(5.6, 2.4).loft()
           .translate((0, 0, 4.55)))
    stem = stem.union(tip)

    # two keycap-leg slots milled from the top at x=+-2.85:
    # 1.30 (X) x 3.10 (Y), floor at z 1.40 (legs bottom out ~1.5)
    for sx in (1, -1):
        slot = (cq.Workplane("XY")
                .workplane(offset=1.40)
                .center(2.85 * sx, 0)
                .rect(1.30, 3.10)
                .extrude(4.2)
                .translate((0, 0, 0)))
        stem = stem.cut(slot)
    # soften top arrises
    try:
        stem = stem.edges(">Z").chamfer(0.18)
    except Exception:
        pass
    return stem


def tessellate(shape, deflection):
    import trimesh
    verts, faces = [], []
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopAbs import TopAbs_FACE
    from OCP.TopoDS import TopoDS
    from OCP.BRep import BRep_Tool
    from OCP.TopLoc import TopLoc_Location
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    sh = shape.val().wrapped if hasattr(shape, "val") else shape.wrapped
    BRepMesh_IncrementalMesh(sh, deflection, False, 0.3, True)
    exp = TopExp_Explorer(sh, TopAbs_FACE)
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
    m = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
    m.merge_vertices()
    return m


def main():
    import trimesh
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    housing = build_housing().val().clean()
    stem = build_stem().val().clean()
    scene = trimesh.Scene({
        "choc_housing": tessellate(housing, 0.03),
        "choc_stem": tessellate(stem, 0.02)})
    scene.export(OUT)
    for name, mesh in scene.geometry.items():
        bb = mesh.bounds
        print(f"  choc glb[{name}]: {OUT} ({len(mesh.faces)} tris, "
              f"{len(mesh.vertices)} verts, bbox "
              f"{bb[1][0]-bb[0][0]:.2f} x {bb[1][1]-bb[0][1]:.2f} x "
              f"{bb[1][2]-bb[0][2]:.2f} mm, "
              f"z {bb[0][2]:.2f}..{bb[1][2]:.2f})")


if __name__ == "__main__":
    main()
