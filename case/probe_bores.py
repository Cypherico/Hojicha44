#!/usr/bin/env python3
"""Bore shape audit for the current generated tub STEP files.

Probe the exported tub STEP files in CASE_OUT (default: case/out).
Checks the bore shape and slab sills against the current parameters.
Component and plug mating need separate fit checks.
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


for tag in ("Left", "Right"):
    print(f"{tag}:")
    board = os.path.join(G.REPO, "pcb", "kicad", f"Hojicha44-{tag}.kicad_pcb")
    rim = G.read_pcb_outline(board)
    ring = G.resample_ring(rim, params.SKIN_STEP)
    skin = G.resample_ring(G.offset_pts(rim, params.CASE_OUTSET), params.SKIN_STEP)
    ports = G.compute_ports(tag, ring, G.outward_field(ring), skin, params)
    step = os.path.join(G.OUT_DIR, f"Hojicha44-{tag}-tub.step")
    solid = cq.importers.importStep(step).val()
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
