#!/usr/bin/env python3
"""Silk/symmetry audit for the Hojicha44 split pair.

The left and right halves mirror placement. The MCU socket and encoder
keep the same orientation, while the JST headers face the split from
opposite sides. Footprint art is compared in local coordinates.

What this audit DOES require per twin pair (L ref <-> R ref):
  1. placement rule: mirrored position for most parts. The MCU socket,
     encoder and JST use placement checks in check_board.py. Fiducial
     and tooling helpers use containment and DRC.
  2. rotation rule: negated mod 180 (body axis mirrors; polarity follows
     pad numbers, N/S preserved). The JST has a signed orientation per half.
  3. silk identity: same multiset of silk primitives (kind/layer/local
     geometry/normalized text) — both halves embed the same footprint
     files, so any difference is an embed/transform bug.
  4. texts readable: twin text angles equal (never mirrored).
  5. board-level silk texts mirror across the split. Each JST '+' is
     checked against its own pin-1 datum.

Usage: python3 pcb/generators/audit_silk.py  (exit 1 on findings)
"""
import math
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PCB_DIR = os.path.join(REPO, "pcb", "kicad")
AXIS = 145.75
TOL = 0.08


def split_top(s):
    items, depth, start, kw = [], 0, None, None
    in_str = esc = False
    for i, c in enumerate(s):
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == "(":
            if depth == 1:
                start = i
                m = re.match(r"\(([A-Za-z_][\w.-]*)", s[i:])
                kw = m.group(1) if m else None
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 1 and start is not None:
                items.append((kw, s[start:i + 1]))
                start = None
    return items


def footprints(board_file):
    s = open(board_file).read()
    out = []
    for kw, blk in split_top(s):
        if kw != "footprint":
            continue
        ref = re.search(r'\(property "Reference" "([^"]*)"', blk).group(1)
        at = re.search(r'\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', blk)
        out.append((ref, float(at.group(1)), float(at.group(2)),
                    float(at.group(3) or 0), blk))
    return out


def silk_sig(blk, lref, nref):
    """Multiset of (kind, layer, rounded-local-geometry, text-or-None).

    Purely local: independent of placement/rotation, so twins must match
    exactly regardless of mirror/translate rules.
    """
    sig = []
    for kw, sub in split_top(blk):
        if kw not in ("fp_line", "fp_rect", "fp_circle", "fp_arc", "fp_poly", "fp_curve",
                      "fp_text"):
            continue
        lay = re.search(r'\(layer "([^"]+)"', sub)
        if not lay or lay.group(1) not in ("F.SilkS", "B.SilkS"):
            continue
        sub = re.sub(r'\(uuid "[^"]*"\)', '(uuid "")', sub)  # fresh per build
        nums = tuple(round(float(v), 2) for v in
                     re.findall(r"(?<![\w.])-?\d+\.\d+|(?<![\w.])-?\d+(?![\w.])",
                                re.sub(r'"[^"]*"', '""', sub)))
        txt = None
        m = re.search(r'\(fp_text \S+ "([^"]*)"', sub)
        if m:
            txt = m.group(1).replace(lref, nref).replace("_L", "_R")
        sig.append((kw, lay.group(1), nums, txt))
    for m in re.finditer(r'\(property "(Reference|Value)" "([^"]*)"'
                         r' \(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)'
                         r'[\s\S]{0,200}?\(layer "(F\.SilkS|B\.SilkS)"', blk):
        sig.append(("prop", m.group(6),
                    (round(float(m.group(3)), 2), round(float(m.group(4)), 2),
                     round(float(m.group(5) or 0), 2)),
                    f"${m.group(1)}={m.group(2)}".replace(lref, nref).replace("_L", "_R")))
    return sorted(sig, key=repr)


def board_texts(board_file):
    s = open(board_file).read()
    out = []
    for m in re.finditer(r'\(gr_text "([^"]*)" \(at ([-\d.]+) ([-\d.]+)'
                         r'(?: ([-\d.]+))?\)\s*\(layer "([^"]+)"\)', s):
        if m.group(5) in ("F.SilkS", "B.SilkS"):
            out.append((m.group(1), (float(m.group(2)), float(m.group(3))),
                        float(m.group(4) or 0), m.group(5)))
    return out


def norm_ref(r):
    return r.replace("_L", "_R")


def main():
    L = {ref: (x, y, rot, blk) for ref, x, y, rot, blk in
         footprints(os.path.join(PCB_DIR, "Hojicha44-Left.kicad_pcb"))}
    R = {ref: (x, y, rot, blk) for ref, x, y, rot, blk in
         footprints(os.path.join(PCB_DIR, "Hojicha44-Right.kicad_pcb"))}
    lr = sorted(norm_ref(r) for r in L)
    rr = sorted(R)
    print(f"footprints L={len(L)} R={len(R)}")
    bad = []
    if lr != rr:
        bad.append(f"REF MISMATCH: only-L={sorted(set(lr) - set(rr))} "
                   f"only-R={sorted(set(rr) - set(lr))}")

    for nref in rr:
        lref = nref.replace("_R", "_L")
        if lref not in L:
            continue
        lx, ly, lrot, lblk = L[lref]
        rx, ry, rrot, rblk = R[nref]
        locked = nref.startswith(("U_", "ENC_"))
        helper = nref.startswith(("FID_", "MT_"))
        if nref == "J_R2":
            # The stored KiCad angles are signed opposites. Match modulo
            # 360 so an accidental half turn cannot pass this check.
            if abs(math.remainder(lrot - 90, 360)) > 0.01 or \
                    abs(math.remainder(rrot + 90, 360)) > 0.01:
                bad.append(f"{nref}: JST mouths must face the split (L={lrot} R={rrot})")
        elif locked:
            if abs(lrot - rrot) > 0.01:
                bad.append(f"{nref}: locked-part rotation differs (L={lrot} R={rrot})")
        elif not helper:
            if abs((2 * AXIS - lx) - rx) > TOL or abs(ly - ry) > TOL:
                bad.append(f"{nref}: placement not mirrored "
                           f"(L=({lx:.2f},{ly:.2f}) R=({rx:.2f},{ry:.2f}))")
            drot = abs(math.sin(math.radians(-lrot - rrot)))
            if drot > 0.01:
                bad.append(f"{nref}: rotation not mirrored (L={lrot} R={rrot})")
        lsig = silk_sig(lblk, lref, nref)
        rsig = silk_sig(rblk, nref, nref)
        if lsig != rsig:
            only_l = [a for a in lsig if a not in rsig]
            only_r = [b for b in rsig if b not in lsig]
            bad.append(f"{nref}: silk art differs "
                       f"(L-only={only_l[:3]}, R-only={only_r[:3]})")

    lt = board_texts(os.path.join(PCB_DIR, "Hojicha44-Left.kicad_pcb"))
    rt = board_texts(os.path.join(PCB_DIR, "Hojicha44-Right.kicad_pcb"))
    ml, mr, pl, pr = [], [], [], []
    for t, (x, y), ang, lay in lt:
        (pl if t == "+" else ml).append((t, (x, y), ang, lay))
    for t, (x, y), ang, lay in rt:
        (pr if t == "+" else mr).append((t, (x, y), ang, lay))
    ml = sorted((t, (round(2 * AXIS - x, 2), round(y, 2)), ang, lay)
                for t, (x, y), ang, lay in ml)
    mr = sorted((t, (round(x, 2), round(y, 2)), ang, lay)
                for t, (x, y), ang, lay in mr)
    if ml != mr:
        bad.append(f"board texts differ:\n  L-mirrored={ml}\n  R={mr}")
    for ref, footprints_by_ref, marks, dx in (
            ("J_L2", L, pl, -2.6), ("J_R2", R, pr, 2.6)):
        if ref not in footprints_by_ref:
            bad.append(f"{ref}: footprint missing")
            continue
        # Pad 1 of the JST footprint is its local origin.
        x, y, _, _ = footprints_by_ref[ref]
        expected = [("+", (round(x + dx, 2), round(y, 2)), 0.0, "F.SilkS")]
        if marks != expected:
            bad.append(f"{ref}: JST '+' mark at {marks}, expected {expected}")

    if bad:
        print(f"{len(bad)} asymmetries:")
        for b in bad[:40]:
            print("  -", b)
        return 1
    print("silk symmetric OK "
          "(mirrored placement, locked orientation, identical art)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
