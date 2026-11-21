"""Real KiCad PCB artwork generator for Hojicha44 renders.

Directly parses the committed KiCad boards (pcb/kicad/Hojicha44-Left.kicad_pcb
and Hojicha44-Right.kicad_pcb) and renders high-resolution photorealistic
textures:
  - pcb_albedo.png / pcbr_albedo.png: soldermask, real routed copper traces,
    ENIG gold pads, annular vias, silkscreen markings
  - pcb_metal.png / pcbr_metal.png: metallic mask + trace bump relief
"""

import math
import os
import re
import sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

PX_PER_MM = 24.0  # 24 px/mm -> ~3300x2400 per half, crisp sub-millimeter detail

FONT_CANDIDATES = (
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial.ttf",
)


def _font(px):
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, px)
            except Exception:
                pass
    return ImageFont.load_default()


def render_board(side, bbox, outdir):
    x0, y0, x1, y1 = bbox
    mm = PX_PER_MM
    W = int(math.ceil((x1 - x0) * mm))
    H = int(math.ceil((y1 - y0) * mm))

    def T(x, y):
        return ((x - x0) * mm, (y - y0) * mm)

    repo_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    pcb_name = f"Hojicha44-{side}.kicad_pcb"
    pcb_path = os.path.join(repo_dir, "pcb", "kicad", pcb_name)
    if not os.path.exists(pcb_path):
        raise FileNotFoundError(f"Missing PCB: {pcb_path}")

    txt = open(pcb_path).read()

    # 1. Base soldermask (classic dark rich emerald green)
    albedo = Image.new("RGB", (W, H), (14, 44, 25))
    metal = Image.new("L", (W, H), 0)
    da = ImageDraw.Draw(albedo)
    dm = ImageDraw.Draw(metal)

    # Subtle liquid soldermask resin variation
    hatch_step = int(1.2 * mm)
    for k in range(-H, W, hatch_step * 2):
        da.line([(k, 0), (k + H, H)], fill=(18, 56, 32), width=1)

    # 2. Parse Segments (copper traces)
    # KiCad stores board y-down; design frame negates y
    segs = re.findall(
        r'\(segment\s+\(start\s+([-\d.]+)\s+([-\d.]+)\)\s+\(end\s+([-\d.]+)\s+([-\d.]+)\)\s+\(width\s+([-\d.]+)\)\s+\(layer\s+\"([^\"]+)\"\)',
        txt
    )

    # Bottom copper (B.Cu) - subtle dark green trace through substrate
    for s in segs:
        if s[5] == "B.Cu":
            p1 = T(float(s[0]), -float(s[1]))
            p2 = T(float(s[2]), -float(s[3]))
            w = max(2, int(float(s[4]) * mm))
            da.line([p1, p2], fill=(22, 68, 38), width=w, joint="curve")

    # Top copper (F.Cu) - vibrant lighter green copper under mask, with bump relief
    for s in segs:
        if s[5] == "F.Cu":
            p1 = T(float(s[0]), -float(s[1]))
            p2 = T(float(s[2]), -float(s[3]))
            w = max(2, int(float(s[4]) * mm))
            da.line([p1, p2], fill=(82, 180, 112), width=w, joint="curve")
            dm.line([p1, p2], fill=128, width=w, joint="curve")

    # 3. Parse Vias
    vias = re.findall(
        r'\(via\s+\(at\s+([-\d.]+)\s+([-\d.]+)\)\s+\(size\s+([-\d.]+)\)\s+\(drill\s+([-\d.]+)\)',
        txt
    )
    for v in vias:
        cx, cy = T(float(v[0]), -float(v[1]))
        r = float(v[2]) * mm / 2.0
        rd = float(v[3]) * mm / 2.0
        da.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(215, 178, 96))
        da.ellipse([cx - rd, cy - rd, cx + rd, cy + rd], fill=(8, 18, 12))
        dm.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
        dm.ellipse([cx - rd, cy - rd, cx + rd, cy + rd], fill=0)

    # 4. Parse Footprints and Pads
    fp_blocks = re.split(r'\(footprint\s+', txt)[1:]
    for fp in fp_blocks:
        m_at = re.search(r'\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+([-\d.]+))?\)', fp)
        if not m_at:
            continue
        fx, fy = float(m_at.group(1)), float(m_at.group(2))
        f_rot = float(m_at.group(3) or 0.0)
        rad = math.radians(-f_rot)
        cos_r, sin_r = math.cos(rad), math.sin(rad)

        # Pads
        pads = re.findall(
            r'\(pad\s+\"([^\"]+)\"\s+([^\s]+)\s+([^\s]+)\s+\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+([-\d.]+))?\)\s+\(size\s+([-\d.]+)\s+([-\d.]+)\)',
            fp
        )
        for p in pads:
            num, ptype, shape, px_str, py_str, prot_str, pw_str, ph_str = p
            lx, ly = float(px_str), float(py_str)
            pw, ph = float(pw_str), float(ph_str)
            rx = fx + lx * cos_r - ly * sin_r
            ry = fy + lx * sin_r + ly * cos_r
            cx, cy = T(rx, -ry)
            hw, hh = pw * mm / 2.0, ph * mm / 2.0

            border = max(1, int(0.12 * mm))
            if shape in ("circle", "oval") and abs(pw - ph) < 0.05:
                da.ellipse([cx - hw - border, cy - hh - border, cx + hw + border, cy + hh + border],
                           fill=(10, 32, 18))
                da.ellipse([cx - hw, cy - hh, cx + hw, cy + hh],
                           fill=(218, 182, 102))
                dm.ellipse([cx - hw, cy - hh, cx + hw, cy + hh], fill=255)
            else:
                da.rounded_rectangle([cx - hw - border, cy - hh - border, cx + hw + border, cy + hh + border],
                                     radius=int(0.15 * mm), fill=(10, 32, 18))
                da.rounded_rectangle([cx - hw, cy - hh, cx + hw, cy + hh],
                                     radius=int(0.15 * mm), fill=(218, 182, 102))
                dm.rounded_rectangle([cx - hw, cy - hh, cx + hw, cy + hh],
                                     radius=int(0.15 * mm), fill=255)

        # Silkscreen inside footprint
        silk_lines = re.findall(
            r'\(fp_line\s+\(start\s+([-\d.]+)\s+([-\d.]+)\)\s+\(end\s+([-\d.]+)\s+([-\d.]+)\)\s+\(stroke[^)]*\)\s+\(layer\s+\"F\.Silkscreen\"\)',
            fp
        )
        if not silk_lines:
            silk_lines = re.findall(
                r'\(fp_line\s+\(start\s+([-\d.]+)\s+([-\d.]+)\)\s+\(end\s+([-\d.]+)\s+([-\d.]+)\)\s+\(layer\s+\"F\.Silkscreen\"\)',
                fp
            )
        for sl in silk_lines:
            sx, sy = float(sl[0]), float(sl[1])
            ex, ey = float(sl[2]), float(sl[3])
            rsx, rsy = fx + sx * cos_r - sy * sin_r, fy + sx * sin_r + sy * cos_r
            rex, rey = fx + ex * cos_r - ey * sin_r, fy + ex * sin_r + ey * cos_r
            da.line([T(rsx, -rsy), T(rex, -rey)], fill=(238, 238, 230), width=max(1, int(0.16 * mm)))

    # 5. General Silkscreen (Board level text & lines)
    gr_lines = re.findall(
        r'\(gr_line\s+\(start\s+([-\d.]+)\s+([-\d.]+)\)\s+\(end\s+([-\d.]+)\s+([-\d.]+)\)\s+\(stroke[^)]*\)\s+\(layer\s+\"F\.Silkscreen\"\)',
        txt
    )
    if not gr_lines:
        gr_lines = re.findall(
            r'\(gr_line\s+\(start\s+([-\d.]+)\s+([-\d.]+)\)\s+\(end\s+([-\d.]+)\s+([-\d.]+)\)\s+\(layer\s+\"F\.Silkscreen\"\)',
            txt
        )
    for gl in gr_lines:
        da.line([T(float(gl[0]), -float(gl[1])), T(float(gl[2]), -float(gl[3]))],
                fill=(238, 238, 230), width=max(1, int(0.18 * mm)))

    # Board logo text
    f_logo = _font(max(14, int(2.4 * mm)))
    f_small = _font(max(9, int(1.1 * mm)))
    tx, ty = T(x0 + (x1 - x0) * 0.28, y0 + 3.5)
    da.text((tx, ty), "HOJICHA44", font=f_logo, fill=(240, 240, 235))
    da.text((tx + 2, ty + 3.2 * mm), f"REV 0.5.1  [{side}]", font=f_small, fill=(210, 210, 205))

    os.makedirs(outdir, exist_ok=True)
    prefix = "pcb" if side == "Left" else "pcbr"
    a_path = os.path.join(outdir, f"{prefix}_albedo.png")
    m_path = os.path.join(outdir, f"{prefix}_metal.png")
    albedo.save(a_path)
    metal.save(m_path)
    print(f"  [pcb_tex] {side}: generated {a_path} ({W}x{H}) and {m_path}", flush=True)
    return a_path, m_path


def main(argv):
    import json
    bbox_path = argv[0]
    outdir = argv[1]
    boxes = json.load(open(bbox_path))
    for side in ("Left", "Right"):
        bb = boxes.get(side) or boxes.get("Left")
        flat = (bb[0][0], bb[0][1], bb[1][0], bb[1][1])
        render_board(side, flat, outdir)


if __name__ == "__main__":
    main(sys.argv[1:])
