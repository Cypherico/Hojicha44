#!/usr/bin/env python3
"""Bore shape and mating clearance audit for the current case STEP files.

CASE_OUT selects the exported tub and cover STEP files (default: case/out).
Checks the wall shape, continuous floor, and plug envelopes throughout
the modeled PCB travel.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cadquery as cq
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.gp import gp_Pnt
from OCP.TopAbs import TopAbs_IN

import gen_case as G
import params

fails = []
VOLUME_TOL = 1e-6  # mm³, for numerical residue from CAD intersections


def probe(tag, name, solid, o, u, v, b, t, z, want):
    x, y = o[0] + u[0] * t + v[0] * b, o[1] + u[1] * t + v[1] * b
    clf = BRepClass3d_SolidClassifier(solid.wrapped, gp_Pnt(x, y, z), 1e-6)
    got = clf.State() == TopAbs_IN
    if got != want:
        fails.append(f"{tag} {name} t={t} b={b} z={z}: "
                     f"{'solid' if got else 'void'} != "
                     f"{'solid' if want else 'void'}")
    else:
        print(f"  ok {tag} {name} t={t} b={b:+.2f} z={z:+.2f} "
              f"{'solid' if want else 'void'}")


def check_plug_clearance(tag, ports, tub, cover):
    travel = params.POWER_Z_TRAVEL
    usb_x, usb_y = params.PORTS[tag]["usb"]
    usb_width = params.USB_HOUSING_W
    usb_bottom = params.USB_AXIS_MIN_Z - travel - params.USB_HOUSING_H / 2
    usb_height = params.USB_AXIS_MAX_Z + travel + params.USB_HOUSING_H / 2 - usb_bottom
    usb = cq.Solid.makeBox(usb_width, params.USB_HOUSING_REACH, usb_height,
                           (usb_x - usb_width / 2, usb_y, usb_bottom))

    jack = ports["trrs"]
    x, y = params.PORTS[tag]["trrs"]
    z = params.TRRS_JACK_AXIS_Z
    radius = params.TRRS_BOOT_D / 2
    reach = jack["out"] + 1.0
    direction = (*jack["u"], 0.0)
    lower = cq.Solid.makeCylinder(radius, reach, (x, y, z - travel), direction)
    upper = cq.Solid.makeCylinder(radius, reach, (x, y, z + travel), direction)
    # The span between the end circles completes the vertical sweep.
    x_min = min(x, x + reach * direction[0])
    span = cq.Solid.makeBox(reach, 2 * radius, 2 * travel,
                            (x_min, y - radius, z - travel))
    trrs = lower.fuse(upper, span)

    for plug, envelope in (("USB-C", usb), ("TRRS", trrs)):
        for part, shape in (("tub", tub), ("cover", cover)):
            overlap = envelope.intersect(shape).Volume()
            if overlap > VOLUME_TOL:
                fails.append(f"{tag} {plug} plug sweep hits {part}: {overlap:.3f} mm³")
            else:
                print(f"  ok {tag} {plug} plug sweep clears {part}")


for tag in ("Left", "Right"):
    print(f"{tag}:")
    rim = G.read_case_rim(tag)
    ring = G.resample_ring(rim, params.SKIN_STEP)
    skin = G.resample_ring(G.offset_pts(rim, params.CASE_OUTSET), params.SKIN_STEP)
    ports = G.compute_ports(tag, ring, G.outward_field(ring), skin, params)
    solid, cover = (
        cq.importers.importStep(os.path.join(G.OUT_DIR, f"Hojicha44-{tag}-{part}.step")).val()
        for part in ("tub", "cover")
    )
    check_plug_clearance(tag, ports, solid, cover)
    for name in ("usb", "trrs", "pwrsw"):
        pr = ports[name]
        o, u, v = pr["o"], pr["u"], pr["v"]
        if name == "usb":
            # Bracket the configured sill through the same part of the wall.
            z0 = pr["z0"]
            probe(tag, name + "/below", solid, o, u, v, 0.0, 3.5, z0 - 0.1, True)
            probe(tag, name + "/above", solid, o, u, v, 0.0, 3.5, z0 + 0.1, False)
            r, w = pr["r"], pr["w"]
            z = z0 + 0.4
            hw = (w / 2 - r) + math.sqrt(max(
                r ** 2 - (z0 + r - z) ** 2, 0.0))
            # The cavity extends past the notch floor near the flanks.
            # Probe at the wall so a missing cutter cannot pass as air.
            depth = 12.0
            near_lip = params.TOP_LIP_Z - 0.05
            for sign in (-1, 1):
                probe(tag, name + "/fillet-in", solid, o, u, v,
                      sign * (hw - 0.05), depth, z, False)
                probe(tag, name + "/fillet-out", solid, o, u, v,
                      sign * (hw + 0.05), depth, z, True)
                probe(tag, name + "/top", solid, o, u, v,
                      sign * (w / 2 - 0.10), depth, near_lip, False)
                probe(tag, name + "/flank", solid, o, u, v,
                      sign * (w / 2 + 0.30), depth, near_lip, True)
        elif name == "trrs":
            depth = 6.0
            for z in (-2.0, 0.0, params.TOP_LIP_Z - 0.1):
                for sign in (-1, 1):
                    probe(tag, name + "/bay", solid, o, u, v,
                          sign * (pr["w"] / 2 - 0.1), depth, z, False)
                    probe(tag, name + "/wall", solid, o, u, v,
                          sign * (pr["w"] / 2 + 0.3), depth, z, True)
            probe(tag, name + "/sill", solid, o, u, v,
                  0.0, depth, params.TRRS_BAY_Z0 - 0.1, True)
        elif name == "pwrsw":
            if pr.get("skipped") or pr.get("kind") == "none":
                # thin-cover lip: the pwrsw port lives entirely ABOVE
                # the tub (body top 5.0 > lip 3.20) — no tub bore; the
                # COVER carries PWRSW_WIN + the nail slot (gen_cover
                # gates probe that solid/void pattern).
                print(f"  skipped {tag} pwrsw (above-tub port; the cover "
                      f"carries PWRSW_WIN)")
            else:
                # v3.5 actuator window: the slot's sill below must be
                # solid, the fillet envelope must admit the nail, the wall
                # must resume past the 5.0-width (ring stays one piece),
                # and the lip plane stays open
                r_, w_ = pr["r"], pr["w"]
                z0_ = pr["z0"]
                probe(tag, name + "/below", solid, o, u, v, 0.0, 3.5,
                      z0_ - 0.6, True)
                probe(tag, name + "/flank", solid, o, u, v,
                      w_ / 2 - 0.15, 3.5, (z0_ + pr["z1"]) / 2, False)
                z = z0_ + 0.4
                hw = (w_ / 2 - r_) + math.sqrt(max(
                    r_ ** 2 - (z0_ + r_ - z) ** 2, 0.0))
                probe(tag, name + "/fillet-in", solid, o, u, v,
                      hw - 0.05, 3.5, z, False)
                probe(tag, name + "/wall-resumed", solid, o, u, v,
                      w_ / 2 + 0.55, 3.5, (z0_ + pr["z1"]) / 2, True)
                probe(tag, name + "/top", solid, o, u, v, 0.0, 3.5,
                      params.TOP_LIP_Z - 0.1, False)
        # slab under every bore stays solid at two depths
        probe(tag, name + "/slab1", solid, o, u, v, 0.0, 3.5,
              params.FLOOR_Z - 1.0, True)
        probe(tag, name + "/slab2", solid, o, u, v, 0.0, 3.5,
              params.FLOOR_Z - 0.2, True)
print()
if fails:
    print(f"FAIL ({len(fails)}):")
    for f in fails:
        print("  " + f)
    sys.exit(1)
print("all shape probes pass")
