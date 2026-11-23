#!/usr/bin/env python3
"""Check USB-C and PJ-320A plug paths, top-side JST and Würth switch fit.

Pass the KiCad JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal.step as the first
argument. CASE_OUT selects the tub and cover STEP directory. The stock
switch has 5.00 mm nominal leads. Use --switch-lead-mm to check a finished
lead length measured from the PCB top. Dimensions are in millimetres.
"""
import argparse
import math
import sys
from pathlib import Path

import cadquery as cq

import gen_case
import params

REPO = Path(gen_case.REPO)
sys.path.insert(0, str(REPO / "pcb" / "generators"))
from check_board import committed_pads, dxf_polylines


def plate_overlap(header, half):
    base = REPO / "plate" / f"Hojicha44-{half}"
    layers = dxf_polylines(f"{base}-plate.dxf")
    outline, = [points for layer, points in layers if layer == "OUTLINE"]
    underside = params.PLATE_UNDER
    overlap = header.intersect(gen_case.prism(outline, underside, params.PLATE_TOP))
    bounds = header.BoundingBox()
    for layer, points in layers:
        if overlap.Volume() == 0.0:
            break
        if layer != "CUTOUT":
            continue
        xs, ys = zip(*points)
        if (max(xs) < bounds.xmin or min(xs) > bounds.xmax or
                max(ys) < bounds.ymin or min(ys) > bounds.ymax):
            continue
        overlap = overlap.cut(gen_case.prism(points, underside, params.PLATE_TOP))
    return overlap.Volume()


def check_jack(half, pins):
    jack = f"J_{half[0]}1"
    if not any(ref == jack for ref, _ in pins):
        print(f"{half} has no {jack} jack footprint")
        return True
    # When the inline contacts progress to the right in the manufacturer's
    # top view, the lone contact lies below the row. The sign is invariant
    # under an in-plane rotation.
    front, rear, sleeve = (pins[jack, name] for name in ("R2", "T", "S"))
    dx, dy = rear[0] - front[0], rear[1] - front[1]
    length = math.hypot(dx, dy)
    if length == 0:
        raise ValueError(f"{jack} has coincident T and R2 contacts")
    offset = (dx * (sleeve[1] - front[1]) - dy * (sleeve[0] - front[0])) / length
    print(f"{half} jack signed contact offset: {offset:+.3f} mm (top-side part expects negative)")
    return offset < 0


def diode_floor_clearance(tub, pins, side):
    """Bound the bottom-side SOD-123 package at the gasket travel limit."""
    height = 1.40  # 1.35 mm package height plus 0.05 mm solder allowance
    travel = params.POWER_Z_TRAVEL
    # DS30086 maximum terminal span and width, plus a 0.05 mm
    # allowance on each side and the full in-plane travel.
    radius = math.hypot(3.95 / 2, 1.80 / 2) + math.sqrt(2) * travel
    bottom = -params.PCB_THICK_MAX - height - travel
    gaps = []
    for idx in range(22):
        x, y = pins[f"D_{side}{idx:02d}", "1"]
        x2, y2 = pins[f"D_{side}{idx:02d}", "2"]
        gauge = cq.Solid.makeCylinder(radius, height + 2 * travel,
                                      ((x + x2) / 2, (y + y2) / 2, bottom))
        gaps.append(gauge.distance(tub))
    return min(gaps)


def check_half(half, header_model, lead_length):
    side = half[0]
    board = REPO / "pcb" / "kicad" / f"Hojicha44-{half}.kicad_pcb"
    # The physical, top-view artwork uses x and -y from the KiCad board.
    pins = {(ref, pin): (x, -y) for ref, pin, x, y, *_ in committed_pads(board)}
    jack_handedness_ok = check_jack(half, pins)
    x, y = pins[f"J_{side}2", "1"]
    x2, y2 = pins[f"J_{side}2", "2"]
    if not math.isclose(math.hypot(x2 - x, y2 - y), 2.0, abs_tol=0.01):
        raise ValueError(f"{half} JST pitch differs from the 2.00 mm model")
    # In the physical STEP pin 1 is the origin and pin 2 lies along +X.
    angle = math.degrees(math.atan2(y2 - y, x2 - x))
    header = header_model.rotate((0, 0, 0), (0, 0, 1), angle).translate((x, y, 0))
    tub, cover = (
        cq.importers.importStep(str(Path(gen_case.OUT_DIR) / f"Hojicha44-{half}-{kind}.step")).val()
        for kind in ("tub", "cover")
    )
    diode_gap = diode_floor_clearance(tub, pins, side)
    print(f"{half} bottom-side diode sweep to tub: {diode_gap:.3f} mm clearance")
    volumes = (plate_overlap(header, half), header.intersect(cover).Volume(),
               header.intersect(tub).Volume())
    print(f"{half} JST overlap with plate, cover, tub (mm³): "
          + ", ".join(f"{volume:.3f}" for volume in volumes))

    facing = 1 if half == "Left" else -1
    mouth_x, mouth_y = params.PORTS[half]["trrs"]
    jack_path = REPO / "pcb/kicad/Hojicha44.3dshapes/PJ-320A.step"
    jack_body = (cq.importers.importStep(str(jack_path)).val()
                 .rotate((0, 0, 0), (1, 1, 1), 120)
                 .rotate((0, 0, 0), (0, 0, 1), 0 if facing > 0 else 180)
                 .translate((mouth_x - 2 * facing, mouth_y, 0)))
    interfaces = []
    usb_x, usb_y = params.PORTS[half]["usb"]
    # A rectangular swept gauge includes the plastic overmold over the
    # full insertion path and the range of installed receptacle heights.
    usb_bottom = params.USB_AXIS_MIN_Z - params.POWER_Z_TRAVEL - params.USB_HOUSING_H / 2
    usb_top = params.USB_AXIS_MAX_Z + params.POWER_Z_TRAVEL + params.USB_HOUSING_H / 2
    usb = cq.Solid.makeBox(params.USB_HOUSING_W, params.USB_HOUSING_REACH,
                           usb_top - usb_bottom,
                           (usb_x - params.USB_HOUSING_W / 2, usb_y, usb_bottom))
    interfaces.append(("USB-C 12.35 x 6.50 overmold insertion sweep", usb, True))
    switch_x, switch_y = pins[f"SW_{side}PWR1", "1"]
    travel_z = params.POWER_Z_TRAVEL
    # Würth 450301014042 drawing, with body and mounting allowance.
    # The actuator gauge includes its full lateral slide.
    switch_body = cq.Solid.makeBox(10.4, 2.9, 4.6 + 2 * travel_z,
                                   (switch_x - 5.2, switch_y - 1.45, 0.5 - travel_z))
    switch_lever = cq.Solid.makeBox(4.1, 1.8, 1.7 + 2 * travel_z,
                                    (switch_x - 2.05, switch_y - 0.9, 4.8 - travel_z))
    interfaces.extend((("power switch body", switch_body, True),
                       ("power switch actuator sweep", switch_lever, True)))
    switch_gap = min(switch_body.distance(usb), switch_lever.distance(usb))
    print(f"{half} power switch to USB-C overmold sweep: {switch_gap:.3f} mm clearance")
    liner_zone = cq.Solid.makeBox(2 * params.USB_LINER_HALF_W,
                                 params.USB_HOUSING_REACH + params.USB_LINER_INSET,
                                 params.TOP_LIP_Z - params.USB_LINER_BOTTOM_Z,
                                 (usb_x - params.USB_LINER_HALF_W, usb_y - params.USB_LINER_INSET,
                                  params.USB_LINER_BOTTOM_Z))
    liner = tub.intersect(liner_zone)
    # The rim is fixed and the PCB/plate assembly floats. Move the liner
    # in the opposite direction to check both vertical travel limits.
    liner_plate = max(plate_overlap(liner.translate((dx, 0, dz)), half)
                      for dx in (-travel_z, 0.0, travel_z)
                      for dz in (-travel_z, 0.0, travel_z))
    print(f"{half} USB liner to suspended plate: {liner_plate:.3f} mm³ max interference")
    # Gauge the entire boot path from its seating face out of the case.
    for dz in (-params.POWER_Z_TRAVEL, 0, params.POWER_Z_TRAVEL):
        boot = cq.Solid.makeCylinder(params.TRRS_BOOT_D / 2, 16,
                                     (mouth_x, mouth_y, params.TRRS_JACK_AXIS_Z + dz),
                                     (facing, 0, 0))
        interfaces.append((f"TRRS Ø9.50 boot gauge at dz={dz:+.2f}",
                           boot, dz == 0))
        interfaces.append((f"PJ-320A body at dz={dz:+.2f}",
                           jack_body.translate((0, 0, dz)), dz == 0))
    # 4.5 mm wide plug, wire tail and removal envelope beyond the housing.
    # A bounding gauge leaves the specific plug and tool to physical fitting.
    end_x = x + facing * 6.25
    travel = params.JST_SERVICE_L
    width = params.JST_SERVICE_W
    plug = cq.Solid.makeBox(travel, width, 4.35,
                            (min(end_x, end_x + facing * travel), (y + y2 - width) / 2, 0.5))
    for dz in (-params.POWER_Z_TRAVEL, 0, params.POWER_Z_TRAVEL):
        interfaces.append((f"JST service envelope at dz={dz:+.2f}",
                           plug.translate((0, 0, dz)), dz == 0))
        interfaces.append((f"JST header at dz={dz:+.2f}",
                           header.translate((0, 0, dz)), False))
    fits = switch_gap > 0.0 and liner_plate < 1e-6
    for name, envelope, check_plate in interfaces:
        overlaps = (plate_overlap(envelope, half) if check_plate else 0.0,
                    envelope.intersect(cover).Volume(), envelope.intersect(tub).Volume())
        print(f"{half} {name}: max interference {max(overlaps):.3f} mm³")
        fits &= max(overlaps) < 1e-6

    clearances = []
    for pin in ("2", "1", "3"):
        x, y = pins[f"SW_{side}PWR1", pin]
        lead = cq.Solid.makeCylinder(0.30, lead_length, (x, y, -lead_length), (0, 0, 1))
        volume = lead.intersect(tub).Volume()
        clearance = lead.distance(tub)
        clearances.append(clearance)
        print(f"{half} switch pin {pin}: {volume:.3f} mm³ tub overlap, "
              f"{clearance:.3f} mm clearance")
    return (jack_handedness_ok and max(volumes) < 1e-6 and fits
            and diode_gap >= params.FLOOR_CLEAR - 1e-5
            and min(clearances) >= params.FLOOR_CLEAR + params.POWER_Z_TRAVEL - 1e-5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jst_step", type=Path)
    parser.add_argument("--switch-lead-mm", type=float, default=5.00)
    args = parser.parse_args()
    if not args.jst_step.is_file():
        parser.error(f"JST STEP file missing: {args.jst_step}")
    if not math.isfinite(args.switch_lead_mm) or args.switch_lead_mm <= 0:
        parser.error("--switch-lead-mm must be a positive finite length")
    model = cq.importers.importStep(str(args.jst_step)).val()
    results = [check_half(half, model, args.switch_lead_mm) for half in ("Left", "Right")]
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
