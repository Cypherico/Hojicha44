# Hojicha44 — Project Synopsis

*A verbal reconstruction of the design, its reasoning, its machinery, and its evidence.*

Generated 2026-11-18 from the repository at `1afac6e` (the `v0.5.0` PCB release is
stamped at `8eef566`, 2026-10-23). This document is a **reading aid**, not a new
source of truth. Where this synopsis and a generator disagree, the generator and
its gates win for “what is built”; where it and a specification disagree, the
specification wins for “what is intended” and the discrepancy is a documentation
bug to fix.

Status vocabulary used here:

- **[built]** — implemented in the repository and covered by a passing gate.
- **[released]** — cut into a versioned manufacturing bundle.
- **[intended]** — stated as a design goal, not yet proven physically.
- **[historical]** — true of an earlier revision; retained to explain a decision.
- **[physical]** — can only be settled by building, measuring, or listening.
- **[drift]** — two repository documents state different things; the current
  generator value is given first.

---

## 1. The object in one page

**Hojicha44** is a custom split columnar mechanical keyboard. It has **44 keys**
and **two rotary encoders**, one per half. Each half is built around a
**nice!nano v2** (nRF52840) running **ZMK**, powered by a **301230 LiPo** and
connected to the host over **Bluetooth LE**. A **TRRS jack** exists on each half
as a wired bring-up/debug fallback, not as the normal link. Each half exposes its
own USB-C port through the controller module.

The key count decomposes as:

| Component | Per half | Both halves |
|---|---:|---:|
| Finger-matrix keys | 18 (6 columns × 3 rows) | 36 |
| Thumb keys | 4 | 8 |
| **Total keys** | **22** | **44** |
| Rotary encoders | 1 | 2 |

The electrical matrix is **4 rows × 6 columns**, but the fourth row is populated
only in columns 0–3 (the thumbs); R3C4 and R3C5 are deliberately unused. The
firmware transform is a **12-column × 4-row** map shared by both halves, with the
right half reporting at a column offset of 6. The keymap therefore has **46
positions** (48 matrix cells minus the two unused ones), of which 44 are
physical keys and two are unused.

The layout is columnar with **no splay**; the six columns are parallel. Vertical
stagger, relative to the home row, is:

| Column (outer → inner) | Stagger |
|---|---:|
| outer | −8 mm |
| pinky | +4 mm |
| ring | +5 mm |
| middle | +7 mm |
| index | −3 mm |
| inner | −6 mm |

The four thumb keys are not a rectangular cluster. They sit on a **true circle of
radius 91.2 mm** about the thumb joint, roughly **13.9° apart**, with each key
rotated to be tangent to that circle. The outer two positions are about 21° off
the arc’s neutral and are deliberately assigned the rare keys (Esc/Delete); the
middle two are about 6.66°/7.25° off neutral and carry the layer holds; the
innermost positions carry Space/Enter. This is an ergonomic decision, not a
drawing convenience.

The switch is **Kailh Choc v1 (PG1350)**, hot-swapped, at a measured column pitch
of **19.00 mm** (not the nominal MX 19.05 mm, and not the Choc-native 18 × 17 mm
cap pitch). Keycaps are Choc v1 only (MBK/MCC/CFX family); the renders use KLP
Lamé caps.

The case is a **two-part gasket enclosure with no screws**: a bottom tub and a
thin top plate, held together by **eight recessed magnet pairs per half**. The
switch plate floats on **poron-padded tabs** (“tab-and-jacket” suspension); the
PCB hangs from the switches, and the case never clamps the PCB. The current
assembly is **11.55 mm tall** from desk to cover top, and **13.93 mm** from desk
to the top of a flat Saddle cap.

Current state:

- **PCB release `v0.5.0` is cut, hashed, and fab-pointable** — Gerbers, drill,
  BOM, position files, ERC/DRC, and a manifest tying them to the board bytes.
- **Plate rev-8 is generated and gated** — 1.2 mm PC, 14.0 mm Choc cutouts,
  0.55 mm diode-relief pockets, 16.2 × 12.4 mm encoder window, eight gasket tabs.
- **Case tub v4.1 and thin-top cover v4.x are generated and gated** — floor
  −4.65 mm, slab 1.7 mm, tub bottom −6.35 mm, cover 3.20–5.20 mm.
- **ZMK firmware builds in CI**, including a workflow that compiles all four
  keymap variants.
- **Nothing has been physically built, ordered, or measured.** The first-article
  checklist is the gate between “software-clean” and “real”.

The project’s own name is used as an identity, not a technical descriptor. The
repository does not record a naming rationale; it pairs “Hojicha” with the key
count.

---

## 2. Design doctrine — the semantic core

The roadmap states the guiding principle directly:

> **The specification is the source of truth; CAD/EDA projects are engineering
> implementations; generated manufacturing files are release artefacts;
> prototypes and controlled tests determine whether a design actually works.**

Almost every unusual thing in this repository follows from that sentence.

### 2.1 Specification, implementation, artefact

The repository distinguishes three layers:

1. **Human-authored specification and decisions** — `spec/layout.yaml`,
   `spec/electronics.yaml`, `spec/case.md`, `spec/keymap.md`,
   `spec/first-article.md`, `spec/compliance.md`, and the roadmap.
2. **Generators and source geometry** — `layout/ergogen/config.yaml`,
   `pcb/generators/*.py`, `plate/gen_plate.py`, `case/params.py` and its
   generators, `config/gen_keymap.py`, `renders/*.py`.
3. **Derived artefacts** — KiCad schematics and boards, plate DXF/SVG/lands,
   case STEP/STL, keymap files, release bundles, print manifests, renders.

The rule is: **change the source, regenerate the output, never hand-edit the
output**. The repository enforces this with byte-comparison gates wherever it
can.

### 2.2 One authoritative source per fact

A fact should have one home and many consumers. Examples:

- Key geometry lives in `layout/ergogen/config.yaml`; the PCB, plate, case, and
  renders consume it rather than re-typing coordinates.
- Keymap content lives in `spec/layout.yaml`; `config/gen_keymap.py` emits every
  keymap file.
- Part numbers live in `spec/electronics.yaml`; the schematic, BOM, and order
  lists derive from it.
- Case stack constants live in `case/params.py`; the plate generator imports the
  same port anchors, and `tests/spec_checks.cjs` pins cross-generator ties.

The corollary is that duplicated numbers are treated as a bug risk. The
`stack-ties` check exists precisely because a plate gap and a case lip can drift
apart silently.

### 2.3 Gates, not assertions

A gate is only meaningful if it can fail. The project repeatedly adds **negative
controls**: a deliberately broken input that must be rejected. Examples:

- A 29th DRC `lib_footprint_mismatch` must fail the W1 gate.
- Changing `CUTOUT` to 14.015 must make `gen_plate.py --check` report stale
  files.
- Deleting one keymap binding must fail the 46-binding count.
- Truncating a home-row trigger list must fail the keymap gate.
- A Y-negated control board must fail the frame/notch self-test.
- A mirror check includes a 0.5 mm deliberate asymmetry that must be caught.

This is why the repository contains a lot of test code relative to its size. The
gates are the product’s memory.

### 2.4 Measure, do not inherit

Several important dimensions changed only after the project measured the actual
vendored model rather than trusting an inherited comment:

- The SOD-123 diode is **1.260 mm** tall in KiCad’s own STEP, not the inherited
  1.35 mm. The plate relief pocket was resized because of it.
- The EC11E encoder’s terminal blocks span **14.95 × 11.70 mm** in the plate band,
  not the 12.30 mm body width. The 12.7 mm plate window would not have passed the
  encoder at all.
- The TRRS mouth faces are **recessed** 0.99 mm behind the board edge, not
  protruding; the earlier clearance story was wrong in the safe direction.
- The Choc clip band is **0.9–1.3 mm** above the PCB; the plate must sit at
  **1.00 mm** so the 1.2 mm plate occupies 1.00–2.20 and the clip can catch.

The recurring lesson is stated in `notes.md`: **a component that moves relative
to a hole must have its clearance envelope re-measured in the new band.**

### 2.5 Release integrity

A manufacturing release must identify exactly what will be fabricated. The
project’s release manifest records:

- specification version,
- git commit and tag,
- router revision and KiCad CLI version,
- SHA-256 of each board file,
- ERC/DRC status and waiver policy,
- SHA-256 of every file in each half’s bundle.

`make_release.py --check` re-hashes the bundle, rejects extra top-level files,
checks the manifest commit against the board-affecting history, and fails on a
dirty board/spec tree. The print manifest does the same for plate and case
geometry. The phrase “fab-pointable” means exactly this: the bytes are identified
and verified, not merely present.

### 2.6 Human approval before irreversible actions

The roadmap requires human approval before fabrication, purchases, major
architecture changes, and public claims. Agents may propose, generate, check, and
explain; they may not quietly promote a candidate or weaken an acceptance
criterion. The repo’s `opencode/` directory is explicitly scratch space for agent
runs, logs, probes, and pre-regeneration board snapshots, not a second design.

### 2.7 The LLM/MCP experiment vision

The roadmap’s longer-term goal is a controlled experiment workflow: a structured
parameter patch, a candidate branch/worktree, generated artefacts, automated
checks, acoustic recordings, and a recorded decision. The intended MCP operations
include `spec.get`, `spec.validate`, `experiment.propose`, `candidate.generate`,
`candidate.check`, `acoustics.compare`, and `candidate.promote`. The repository
does not claim that all of these exist; it documents the intended interface and
the rules that keep agents honest. The actual implementation is the generator +
gate + manifest pipeline described here.

---

## 3. Requirements and invariants

These are the constraints that should remain true across revisions.

### 3.1 Layout

- **44 keys total, 22 per half**: 18 matrix keys + 4 thumbs.
- **No number row.** Digits and symbols live on layer 1.
- **QWERTY letters and the digit order 1234567890 do not move.**
- **Columnar, zero splay.** Parallel columns; vertical stagger only.
- **19.00 mm measured pitch**, not nominal 19.05.
- **Thumb arc**: R = 91.2 mm, ~13.9° spacing, tangent rotations, ≥1.0 mm cap
  clearance. All four thumb keys are 1u and standalone.
- **Left half is the central; right half is the peripheral**, by Kconfig
  convention and by CI.
- **Left-half key geometry is frozen** relative to the v7/v8 baseline; widening
  the split translates the right half only.
- **Mirror discipline**: right-half geometry is the exact mirror of the left
  about `x = 145.75` (`right = 291.5 − left`) unless a part is explicitly
  translated rather than mirrored (the encoder is one such part).

### 3.2 Electrical

- **nice!nano v2 ×2**, one per half, socketed in 2×12 machine-pin headers.
- **BLE primary**; TRRS is optional and debug-only.
- **Matrix is COL2ROW**: `COL → switch → diode → ROW`, with the diode cathode
  toward the row.
- **Power path**: cell → JST-PH → slide switch (pack+) → RAW; pack− → GND.
  B+/B− module holes stay open. Charging only works with the switch ON.
- **No on-board reverse-polarity protection** in rev 1; the procedural gate is
  meter-before-plug-in, JST pin-1 “+” silk, and a series polyfuse in the pack+
  lead.
- **TRRS ring 2 is unconnected** on both halves. Joining it would connect the two
  battery positives through the cable and into the charger MOSFETs.
- **Straight-cable crossover is in copper**: left `D1→TIP`, right `D1→RING1`;
  both halves therefore use the same UART pinctrl (`TX=P0.06`, `RX=P0.08`).
- **NFC pins P0.09/P0.10 are used as GPIO** (spare D10 and encoder push). This
  requires the UICR `nfct-pins-as-gpios` option and a first flash with a full
  chip erase.

### 3.3 Mechanical

- **Choc v1 PG1350 only.** 1.2 mm plate is mandatory for clip engagement.
- **Plate gap 1.00 mm**, plate 1.00–2.20 mm above PCB top.
- **14.0 mm switch cutouts** in the plate; 15.0 mm gives no retention.
- **0.55 mm diode-relief pockets**, never through-cuts.
- **Encoder window 16.2 × 12.4 mm**, sized to the terminal-block envelope.
- **Tab-and-jacket gasket mount**: eight tabs per half, poron top and bottom, no
  plate screws, no hard contact.
- **No visible fasteners** in the case; recessed magnets only.
- **PCB 1.6 mm**, 2-layer, ENIG, no pours in rev 1.
- **Antenna keepout**: r = 5 mm copper-free; no case material within 3 mm of the
  antenna circle; measured case clearance is much larger (≈14.15 mm in-plane,
  5.60 mm to the floor).
- **TRRS gap**: 20.42 mm board-edge to board-edge, 22.40 mm mouth-to-mouth;
  90° plugs required, straight plugs marginal/prohibited.

### 3.4 Firmware and keymap

- **ZMK, pinned to v0.3** by commit in both `west.yml` and the reusable CI
  workflow.
- **Four variants**, differing only in home-row mod order and Space thumb:
  `mac_left` (default), `mac_right`, `win_left`, `win_right`.
- **Home-row mods on A S D F / ; L K J**, with G and H left plain.
- **L1 = digits/shifted/F-keys**, **L2 = nav/media/BT**, **L1+L2 = Adjust**.
- **Encoder push = Mute on both halves**, via a sideband, not the matrix.
- **Every keymap file is generated** from `spec/layout.yaml`; hand-editing is an
  anti-pattern.

### 3.5 Release and manufacturing

- **Only `generated/release/vX.Y.Z/` is fab-pointable.** Legacy `pcb/- FINAL/`
  was removed.
- **Only files hashed in `generated/print/vX.Y.Z/MANIFEST.txt` go to the plate
  and case shops.**
- **Tab-route only, no V-cut/V-score** on the concave PCB outline.
- **ENIG** surface finish for flat hotswap pads and hand soldering.
- **Coupon before batch**: the Choc cutout/relief coupon and the encoder window
  sample are required before production orders.
- **Personal builds only** for `v0.5.0`; no sale or supply is planned, which
  changes the compliance obligations.

---

## 4. Repository map

| Path | Role |
|---|---|
| `README.md` | Top-level orientation and current-phase summary. Some version labels are stale relative to the print manifest. |
| `KEYBOARD_PROJECT_ROADMAP.md` | Product goals, development phases, source-of-truth rules, experiment discipline, render/video ambitions. The philosophical charter. |
| `notes.md` | Chronological engineering review log: blockers, fixes, measurements, audits, rejected options, process lessons. Historical, explicitly not spec. |
| `AUDIT_REPORT_PCB_PLATE_CASE.md` | First external-style audit; largely superseded by v2 but still valid for PCB netlist/routing findings. |
| `AUDIT_REPORT_PCB_PLATE_CASE_v2.md` | The 2026-10-19/20 six-review audit that found the plate-retention blocker and forced the support-strategy rethink. Its numbers are pre-fix and marked historical. |
| `build.yaml` | ZMK CI build matrix: `nice_nano_v2` + `hojicha44_left` / `hojicha44_right`. |
| `zephyr/module.yml` | Declares the repo as a Zephyr module so `boards/` and `config/` are visible to west. |
| `boards/shields/hojicha44/` | ZMK shield: shared `hojicha44.dtsi`, left/right overlays, Kconfig, `.zmk.yml`. |
| `config/` | ZMK build inputs: active keymap, four variants, `.conf` files, `west.yml`, and `gen_keymap.py`. |
| `spec/` | Human-authored engineering source of truth and decision records. |
| `layout/ergogen/config.yaml` | Parametric key/outline source. Ergogen 4.2.1. |
| `layout/generators/` | KLE export and preview rendering. |
| `layout/generated/v2/` | Derived points, outlines, demo SVGs, keymap render. |
| `layout/- FINAL/` | Versioned KLE and Ergogen snapshots; v8 is the frozen layout. |
| `pcb/generators/` | `gen_schematic.py`, `gen_pcb.py`, `gen_route.py`, `check_board.py`, `audit_silk.py`, `frame.py`. |
| `pcb/kicad/` | Two KiCad projects (Left/Right), netlists, DRC/ERC reports, vendored symbols/footprints/3D models, `hand-copper.txt`. |
| `pcb/stock/` | Vendored stock inputs and attribution. |
| `pcb/make_release.py` | Release cutter/checker: gerbers, drill, BOM, positions, reports, manifest. |
| `pcb/render.py` | PCB 3D/render helper. |
| `pcb/BOM_ORDER.md` | Human shopping list with live-verified SKUs and vendor notes. |
| `pcb/MANUFACTURING.md` | JLCPCB order guide: every quote field, fab constraints, assembly intent. |
| `plate/gen_plate.py` | Derives plate DXF/SVG/lands from the placed PCB. |
| `plate/Hojicha44-*-plate.dxf` | Laser file, R12 mm, layers OUTLINE/CUTOUT/PORON/RELIEF. |
| `plate/Hojicha44-*-plate.svg` | Human preview. |
| `plate/Hojicha44-*-lands.json` | Tab root centers for case pockets. |
| `case/params.py` | Every case dimension with its source. |
| `case/gen_case.py` | Bottom tub generator + self-checks. |
| `case/gen_cover.py` | Thin top-plate generator + self-checks. |
| `case/mirror_gate.py` | STEP mirror check with negative control. |
| `case/probe_bores.py` | Offline bore-shape audit on finished solids. |
| `case/out/` | Tracked STEP solids and gitignored STL scratch. |
| `tests/spec_checks.cjs` | Static gate suite (`npm test`), no KiCad required. |
| `renders/` | Blender/Trimesh pipeline, keycap fetch, materials, environments, shot list. |
| `generated/release/vX.Y.Z/` | Versioned PCB manufacturing bundles. v0.3.1, v0.4.0, v0.5.0 exist. |
| `generated/print/v0.5.0/` | Hash record for plate + case order geometry. |
| `generated/renders/v0.5.0/` | Final PNGs and `MANIFEST.json`. |
| `out/` | Untracked local outputs: firmware build, fit prints. |
| `opencode/` | Untracked agent scratch: logs, probe scripts, pre-regeneration board archives. |

The repo deliberately keeps **specification and source separate from generated
outputs**. `generated/` is selectively tracked: release bundles, final renders,
layout points, and print manifests are worth versioning; mesh caches and build
outputs are not.

---

## 5. The generative pipeline

The design is one directed graph. In simplified form:

```
layout/ergogen/config.yaml
        │  ergogen + dump_points + export_kle
        ▼
layout/generated/v2/{points,outlines}
        │
        ├──────────────► pcb/generators/gen_pcb.py ──► .kicad_pcb (Left/Right)
        │                        ▲
spec/electronics.yaml ──► gen_schematic.py ──► .kicad_sch + .net
        │                        │
        │                        └── ERC + net audit
        ▼
placed PCB + plate outline
        │
        ├──► plate/gen_plate.py ──► DXF / SVG / lands.json
        │            │
        │            ▼
        └──► case/gen_case.py + gen_cover.py ──► STEP / STL
                                 │
                                 └── mirror_gate + probe_bores

spec/layout.yaml ──► config/gen_keymap.py ──► active keymap + 4 variants

boards + plate + case + keycaps
        └──► renders/build_assets.py ──► Blender scene ──► PNG + MANIFEST.json

boards ──► pcb/make_release.py ──► generated/release/vX.Y.Z/
plate + case ──► generated/print/vX.Y.Z/MANIFEST.txt
```

The important semantic point is that **the plate is derived from the placed PCB,
and the case is derived from the plate**. The PCB is not derived from the plate.
This ordering is what makes the interface contract enforceable:

- The PCB outline comes from the Ergogen `board` outline.
- The plate outline is the PCB Edge.Cuts loop plus tabs, with the encoder window
  and component windows added.
- The case cavity and skin are derived from the PCB rim and plate tab geometry.
- The plate and case share port anchors from `case/params.py`.

`gen_plate.py` deliberately reads the placed board, not the raw Ergogen output,
so the plate cannot silently diverge from the board that will be fabricated.

---

## 6. Layout

### 6.1 The Ergogen source

`layout/ergogen/config.yaml` is the geometric source of truth. It is written for
**Ergogen 4.2.1** and declares six matrix columns (`outer`, `pinky`, `ring`,
`middle`, `index`, `inner`), three rows (`top`, `home`, `bottom`), a thumb zone,
and a set of non-key anchors.

The matrix uses:

- `padding: 1ky`, `spread: 1kx` — a 19 mm pitch in the project’s units.
- `stagger` values per column as listed in §1.
- `splay: 0` — no column rotation.

The thumb zone is anchored to `matrix_middle_bottom` and shifts progressively:
`t_ctrl` at rotation 0.5°, `t_cmd` at −13.5°, `t_l1` at −27.5°, `t_space` at
−41.5°. The keys are named after their **rev-1** functions (Ctrl, Cmd, L1,
Space) because that is how the geometry was first laid out. In rev 3 those
functions moved to the home row and the thumb legends changed; the geometric
names remain as stable anchors.

### 6.2 From v1 to rev 3

The layout had a real ergonomic evolution:

- **v1** had 1.5u thumb keys and put Ctrl/Cmd/Shift on the thumbs.
- **Rev 3** moved all four modifiers to the home row as home-row mod-taps, freeing
  the thumbs for frequent keys: Esc, L1, Tab, Space on the left; Delete, L2,
  Backspace, Enter on the right.
- The inner-bottom keys became `-` (left) and `'` (right) on the base layer, since
  Tab and Esc had moved to the thumbs.
- The letters and digit order never moved.

This is a good example of the project’s semantic discipline: the physical key
positions are stable, but the *meaning* of a position can be revised when the
ergonomic argument changes. The keymap generator reads the legends from
`spec/layout.yaml`, so the physical and firmware stories stay aligned.

### 6.3 The thumb arc

The four thumb keys are placed on a circle of **R = 91.2 mm**. The keys are about
13.9° apart, with tangent rotations, so each key faces along the arc. The
comfort argument is:

| Position (outer → inner) | Angular offset | Role |
|---|---:|---|
| outermost | ~21° | rare + recoverable (Esc / Delete) |
| mid-outer | ~7.25° | layer hold (L1 / L2) — long holds want low strain |
| mid-inner | ~6.66° | Tab / Backspace |
| innermost | ~0° | Space / Enter — palm-side primary |

The left and right thumb lists are written in opposite physical directions in the
spec (left west→east, right west→east), and the generator reverses the right list
so the keymap reads outer→inner on both halves. This is a common source of
left/right legend bugs; the generator and its position gate exist to prevent it.

### 6.4 Encoder and MCU

The encoder anchor is **south of the inner column**, clear of the MCU zone at
top-inner. The EC11E body sits **on** the PCB; all seven pads need copper. There
is therefore **no encoder knock-through in the PCB outline**. The plate and case
carry the 16.2 × 12.4 mm window.

The MCU is placed **USB-up**: the USB end points at the north board edge, which
has an 11 mm-wide seat notch. The module’s USB shell does not overhang the board
edge (measured about 9 mm inboard); the notch provides plug seating. The antenna
end faces south, into the board, with an r = 5 mm copper-free keepout circle. The
antenna center is at least 13.65 mm from every board edge, so the circle itself
clears by at least 8.65 mm.

The module is **PCB-retained, not module-retained**. The module sits in its 2×12
socket; the PCB is held by the switches and plate. There is no clamp or press-fit
pocket. If a locating pocket is ever added, it must be a loose fit (0.2–0.3 mm
clearance), never a press fit. The USB plug’s lateral load is meant to be reacted
by the case’s 14.0 mm mouth, not by the module.

### 6.5 Non-key anchors

The Ergogen config defines mechanical anchors that are not keys:

| Anchor | Purpose |
|---|---|
| `usb` | Module USB-C center at the north edge; opens the seat notch. |
| `antenna` | Module south end; r = 5 mm copper keepout. |
| `batt` | 301230 cell under the socketed module; 12.5 × 31 mm outline. |
| `jst` | JST-PH socket south of the battery; 9 × 9 mm zone. |
| `pwrsw` | WS-SLTV slide switch on the north edge, west of USB; 13 × 5 mm outline. |
| `trrs` | PJ-320A at the inner/gap-facing edge; 17 × 7 mm outline. |

The board outline is a concave hull per half, built from key/anchor points,
expanded 4.5 mm with rounded joints and a 2 mm fillet. The USB notch is subtracted
as an 11 × 10.8 mm rectangle shifted 2.7 mm. The encoder circles are **not** cut
in the board outline.

### 6.6 Split width and TRRS

The mirror line is:

```
distance: 4.5kx + 16
```

`4.5kx` is the frozen baseline. Without the `+16`, the two board edges at the
encoder/TRRS height are only 2.5–4.4 mm apart, and a facing TRRS pair cannot
seat. The +16 mm widening gives an **18.50 mm worst-case inner gap** at the
encoder and **20.42 mm edge-to-edge** at the TRRS height. The left-half key
geometry is unchanged; only the right half translates. Reverting the widening is
a one-line deletion, but it reintroduces the TRRS seating problem.

Measured TRRS geometry on the placed boards:

- board edges: left 135.54, right 155.96 → **20.42 mm**;
- plastic mouth faces: left 134.55, right 156.95 → **22.40 mm**;
- each mouth is **0.99 mm recessed** behind its board edge;
- silk tops at **21.40 mm** (still 0.49 mm recessed).

A 90° plug protrudes only ~2–4 mm axially and needs ~8 mm of the 22.40 mm gap; it
fits easily. A molded straight plug protrudes ~12 mm and needs ~24 mm; it is
marginal at best. The design therefore **requires a right-angle TRRS cable**.

If the widened gap ever becomes undesirable, the documented alternatives are:
both jacks on the outer edge, one jack per half on the north edge above the MCU,
or dropping the wired split entirely. All of them change only the jack, never the
key geometry.

### 6.7 Layout status

`spec/layout.yaml` is marked `provisional`: geometry is agreed and the PCB
envelope is added, but the layout has not been print-tested at 1:1. The open
point is exactly that: print the fit sheet, calibrate the 19.00 mm pitch, then tag
the layout baseline.

---

## 7. Electrical architecture

### 7.1 Power

The power tree is deliberately simple:

```
301230 LiPo (3.7 V, ~110 mAh, PCM)
   │
   ├── pack+ (red) ── JST-PH pin 1 ── PPTC polyfuse ── slide switch common
   │                                                   │
   │                                                   └── switched rail ── nice!nano RAW
   │
   └── pack− (black) ── JST-PH pin 2 ── GND
```

- The cell must have a **protection PCM** (overcharge 4.28 V, over-discharge
  2.40 V, over-current, short). The board does **not** add a DW01A/8205A because
  that would duplicate the cell’s protection.
- The slide switch is a **Würth WS-SLTV 450301014042** (10 × 2.5 × 6.4 mm,
  P2.54). Pin 1 (middle) is common; pins 2/3 are throws; the design uses common →
  throw 2 and leaves throw 3 unconnected.
- The charger is the nice!nano’s onboard 100 mA charger. The 500 mA charge-boost
  jumper stays open. Because the switch is between pack+ and RAW, **the cell
  charges only when the switch is ON**. This must be labeled on the case:
  “CHARGE ONLY WHEN ON”.
- A **series PPTC polyfuse** (0.5–1 A hold, ≥16 V) lives in the pack+ lead, not on
  the PCB. One per half.
- There is **no reverse-polarity protection** in rev 1. A reversed pack can kill
  the board and cell. The procedural gates are: JST pin-1 “+” silk, meter the
  pigtail before first plug-in, and a documented DMM sequence. A P-MOSFET ideal
  diode is a rev-2 candidate only if field reversal is a real risk.

The 301230 cell is 3 × 12 × 30 mm. It sits **under the socketed module**, between
the socket rows. The 302030 (3 × 20 × 30) does **not** fit: 20 mm is wider than
the 18 mm module and fouls the socket pins. The socket stack must measure
**4.5–5.0 mm** assembled; the 2.11 mm Mill-Max 315 variant is banned by height
because it cannot clear the 3 mm cell. The JST is a side-entry S2B-PH-K-S and
sits **beside** the cell, not under the stack.

### 7.2 Matrix

The matrix is 4 rows × 6 columns:

- Rows R0–R2 are the finger rows; R3 is the thumb row.
- Columns C0–C5 are the six finger columns; thumbs use C0–C3.
- Only 22 of 24 cells are populated; R3C4 and R3C5 are NC.
- Diode direction is **COL2ROW**: column → switch → diode anode → cathode → row.
- Diodes are **1N4148W, SOD-123**, on the **top** side (F.Cu).

Why diodes stay on top: the Choc hotswap socket is a bottom-side part with
asymmetric tabs and a body whose orientation is fixed by the switch. The two
halves’ bottom copper therefore cannot be mirror-symmetric if a back-side diode
is added. Keeping diodes on top preserves the project’s left/right mirror
discipline. The cost is the plate relief pocket, which is a solved problem.

### 7.3 MCU pin map

The nice!nano v2 uses the Pro Micro/nice!nano numbering, not the stock KiCad
`PinSocket_2x12` row-major convention. The socket rows are **15.24 mm apart**,
pitch 2.54 mm; pads 1–12 run down the TX/D1 edge and pads 13–24 down the RAW edge
in the opposite direction. Pads 1 (D1) and 24 (RAW) share the USB end; pads
12/13 are at the antenna end.

| Function | Arduino | nRF |
|---|---|---|
| ROW0 | D4 | P0.22 |
| ROW1 | D5 | P0.24 |
| ROW2 | D6 | P1.00 |
| ROW3 | D7 | P0.11 |
| COL0 | D8 | P1.04 |
| COL1 | D9 | P1.06 |
| COL2 | D2 | P0.17 |
| COL3 | D3 | P0.20 |
| COL4 | D14 | P1.11 |
| COL5 | D15 | P1.13 |
| ENC_A | A0 | P1.15 |
| ENC_B | A1 | P0.02 |
| ENC_SW | D16 | P0.10 |
| Split left TX | D1 | P0.06 |
| Split left RX | D0 | P0.08 |
| Split right TX | D1 | P0.06 |
| Split right RX | D0 | P0.08 |
| Spare | A2 | P0.29 |
| Spare | A3 | P0.31 |
| Spare | D10 | P0.09 |

GPIO accounting: 15 used + 3 spare = 18 footprint GPIOs; no shortfall.

D10 and D16 are NFC pins P0.09/P0.10. The devicetree sets
`&uicr { nfct-pins-as-gpios; }`, which writes a sticky UICR option register. A
first flash **must use a full chip erase** (`--erase`); otherwise the board boots
but the encoder push and spare pin stay dead with no error.

### 7.4 Encoder

- Part: **Alps EC11E15244G1**, vertical, 30 detents / 15 pulses, 0.5 mm push
  travel, 20 mm shaft (tip ~24.5 mm above PCB).
- The committed build prefers a **short-shaft EC11-class** part (tip ≤14 mm above
  the PCB) with push, so the low knob sits correctly. The 20 mm Alps part is the
  fallback with a tall knob or a trimmed shaft.
- Quadrature on A0/A1, push on D16.
- Pull-ups are the nRF52840 internal ones via ZMK; no external resistors or caps
  in rev 1.
- ZMK v0.3’s `alps,ec11` driver reports `val = deltas × 360 / steps`. `steps`
  counts quadrature deltas per revolution, not Alps “pulse periods”. The part has
  15 pulse periods × 4 deltas = **60**, so the dtsi uses `steps = <60>` and
  `triggers-per-rotation = <30>`. One detent click = 12° = exactly one trigger.

### 7.5 TRRS and split link

- Part: **PJ-320A**, 3.5 mm 4-pole THT.
- Pad map: Tip = `SPLIT_TX`; Ring1 = `SPLIT_RX`; Ring2 = **unconnected**;
  Sleeve = GND.
- Left half: `D1 → TIP`, `D0 → RING1`.
- Right half: `D1 → RING1`, `D0 → TIP`.
- A straight cable therefore crosses TX/RX. The crossover is in copper, so both
  halves use identical UART pinctrl; there is no firmware swap.
- Ring2 is deliberately unconnected: wiring it would join both battery positives
  through the cable and into the charger MOSFETs. Splitkb documents MCU damage
  from this. ZMK’s wired split needs only TX/RX/GND; the 4-pole jack is kept for
  cable compatibility.
- Hot-plug procedure: **USB out of both halves, both switches OFF, then plug the
  TRRS cable, then power on.** Switch OFF alone is insufficient because USB still
  powers the controller. Sleeve-GND mates at an angle; live mating can glitch
  TX/RX and brown out the charger MOSFETs.
- Splitkb’s own nice!nano FAQ advises against cabling two battery-powered halves
  at all. This design mitigates the charging risk with ring2-NC and the shorting
  risk with the power-off ordering, but TRRS remains a **bring-up/debug fallback,
  not a daily-use link**. If a wired link is wanted in normal use, move to a
  4-pin JST or another proper inline connector.

### 7.6 Schematic generation

`pcb/generators/gen_schematic.py` reads `spec/electronics.yaml` and produces two
separate KiCad projects:

- `pcb/kicad/Hojicha44-Left.kicad_sch` (+ `.kicad_pro`, ERC report)
- `pcb/kicad/Hojicha44-Right.kicad_sch` (+ `.kicad_pro`, ERC report)

Why two projects: a single flat sheet produces one netlist, so “Update PCB from
schematic” would pull both halves into one board file and mix the outlines. One
project per half keeps each outline, netlist, and DRC separate. The half-to-half
link lives in the spec and in the copper crossover, not in a shared netlist.

The generator asserts things ERC and DRC cannot catch:

- **Socket rows are 15.24 mm apart at 2.54 mm pitch**, matching the nice!nano
  numbering. The stock `PinSocket_2x12` is row-major with 2.54 mm row spacing and
  would land every MCU net on the wrong pad while still passing checks.
- **Reference designators must end in a digit**, or KiCad treats them as
  unannotated and every export warns.
- **22 diodes must be `D_SOD-123`**, not the stock DO-41.
- **Exactly one `PWR_FLAG`**, no `VBAT_SHARED` net, no foreign-half references.
- **Title-block revision derives from the spec version** so the sheet cannot
  drift.

ERC result: **0 errors**, with exactly **five documented single-pin spare
warnings per half** (RST, VCC3V3, A3, A2, D10). The spares stay labeled for
future use/UICR; no-connect markers are deliberately not applied. The generator’s
union-find audit checks 22 named nets / 82 named pins per sheet, plus the
anonymous switch-diode and battery series segments.

---

## 8. PCB physical design and release

### 8.1 Placement and routing

`pcb/generators/gen_pcb.py` owns the outline, footprints, nets, placement, and
generator copper. It reads:

- `layout/generated/v2/points/points.yaml` for key positions;
- `layout/generated/v2/outlines/board.dxf` for the outline;
- the per-half netlist exported from the schematic.

The deterministic router is `pcb/generators/gen_route.py`: a dual-layer A* router.
Generator copper is **revision-tagged** so stale generator tracks are dropped
when the router revision changes. GUI copper is the opposite: `(segment …)`,
`(via …)`, and `(zone …)` are preserved verbatim, with net codes remapped by
name (codes are not stable across netlist exports).

`pcb/kicad/hand-copper.txt` is the authoritative preserve set, scoped per half
(`[Left]`/`[Right]`). A regeneration keeps only items matching manifest
signatures. A manifest line that the committed board lacks is a hard error. This
is provenance, not reproduction: it prevents a regeneration from silently
deleting hand-routed copper.

The placement generator also performs containment checks (every numbered pad
inside the outline, plus vias), which DRC does not check. It would have caught the
TRRS mouth-end pads going off-board. If DRC rejects a board, the generator reverts
it so it cannot leak into the next build.

### 8.2 Board facts

| Property | Value |
|---|---|
| Footprints per half | 54 |
| Nets per half | 47–48 depending on counting convention; the release audit reports 48 |
| Outline per half | ~150.5 × 114.6 mm |
| Layers | 2 |
| Thickness | 1.6 mm |
| Finish | ENIG |
| Track width | 0.25 mm signal, 0.5 mm `VBAT_SW` |
| Clearance | 0.20 mm signal / 0.25 mm power class |
| Signal vias | 0.30 mm drill in 0.65 mm pad |
| Power vias | 0.50 mm drill in 1.00 mm pad |
| Minimum copper-to-edge | 0.406 mm Left / 0.575 mm Right (after the M3.6 nudge) |
| Copper pour | None in rev 1; 0.25 mm GND chains |
| Fiducials | 3 per half, non-collinear |
| Tooling holes | 2 × 3.2 mm NPTH per half |

The 54 footprints are: 22 switches, 22 diodes, the MCU socket, the encoder, the
TRRS jack, the JST, the power switch, three fiducials, and two tooling holes.

### 8.3 DRC waivers

The release is **DRC-clean modulo two documented waivers**:

- **W1**: `lib_footprint_mismatch` on rotated parts, exactly **28 per half**. The
  set is asserted by count and by reference; each waived ref’s pad content is
  checked against the vendored stock. The mismatch is a KiCad library quirk, not
  a copper error.
- **W2**: a predicate for a Choc `B.SilkS`-vs-own-pad2 vendor marginality. It is
  **armed but zero on the routed boards**.

Unconnected items are not waived. PTH/NPTH-in-courtyard is an error.

### 8.4 Frame, Gerbers, and the release bundle

KiCad stores the board y-down; `kicad-cli`’s STEP export negates y. The committed
plate DXF and case STLs are y-up. To keep one design frame:

- The `.kicad_pcb` is stored **y-negated**; the title block records
  `(comment 3 "frame: storage-yneg")`.
- `pcb/generators/frame.py` converts between storage and design frames.
- Gerber/drill/pos exports land in the design frame.
- DRC is run on the **design-frame reflection** of the exported board, which is
  geometrically identical but lets KiCad compare footprint-local geometry to the
  libraries.

The release bundle `generated/release/v0.5.0/{Left,Right}/` contains **16 files
per half**:

- 9 Gerbers (F/B copper, mask, paste, silk, Edge.Cuts),
- `.gbrjob`,
- drill file,
- `bom.csv`,
- `pos.csv` and `pos-smt.csv`,
- ERC and DRC reports.

The manifest records the git commit `8eef566`, tag
`pcb-baseline-r10-114-g8eef566`, router `gen_route.py r13`, KiCad CLI `10.0.6`,
the SHA-256 of each board, and the SHA-256 of every bundle file.

### 8.5 Manufacturing rules

- **Two separate designs.** Left and Right are ordered as two 5-piece line items
  (or one checkout with “Different Design: 2”). Do not merge them into one panel.
- **Concave outline → tab-route only, no V-cut/V-score.** Put this in the order
  verbatim:
  `CONCAVE OUTLINE — TAB-ROUTE ONLY, NO V-CUT / V-SCORE`.
- **ENIG** in the quote form, not just in the `.gbrjob` (the job file is
  informational; the form is what the fab executes).
- 1 oz copper, tented vias, flying-probe test, no gold fingers, no castellations,
  no edge plating, no UL, no humidity card.
- Board outline tolerance ±0.2 mm is sufficient; thickness ±10% is why the case
  keeps freeboard.

---

## 9. Plate and gasket subsystem

### 9.1 The support problem

The first plate used **15.0 mm cutouts** because the Choc clip-wing envelope is
15.0 mm. That was a subtle but fatal error: a 15.0 mm hole gives the clip wings
**zero bearing area**. The plate could not hold the switch; the PCB could not
hang from the plate; the assembly would sag onto the case floor. The v2 audit
called this a blocker.

The fix is **support strategy (b): a true Choc hang**.

- Cutout: **14.0 mm**.
- Plate thickness: **1.2 mm**.
- Plate gap: **1.00 mm** above PCB top.
- Plate occupies **1.00–2.20 mm**.

The Choc geometry explains the numbers:

| Feature | Height above PCB |
|---|---:|
| Skirt | 0–0.9 mm |
| Flexible clip arms / lip | 0.9–1.3 mm |
| Plate underside (design) | 1.00 mm |
| Plate top (design) | 2.20 mm |
| 14.8–15.0 mm ears | 2.2–3.0 mm |

The clip lip grabs the plate underside; the ears seat on the plate top. A 14.0 mm
hole leaves 0.10 mm/side clearance on the 13.8 mm lower body, while the 15.0 mm
clip wing still overlaps the plate by 0.50 mm/side. That overlap is what the clip
arm hooks under.

The tolerance stack is tight: the capture window is z 0.9–1.3; the settled gap is
`2.2 − plate thickness`. For a 1.2 mm plate that is 1.00 mm, with 0.10 mm margin
below and 0.30 mm above. A plate thicker than 1.25 mm is rejected by the coupon
gate because a 1.3 mm plate puts the lip at its marginal tip. A 1.05 mm gap lifts
the ears into the plate; a 1.3 mm gap drives the plate top through the ears.

### 9.2 Diode relief

The 22 SOD-123 diodes are on the top side in the inter-key gaps. The measured
height is **1.260 mm** (KiCad’s `D_SOD-123.step`), with a part tolerance up to
**1.40 mm**. The plate therefore carries a **0.55 mm partial-depth pocket** in its
underside under every diode.

- Pocket XY: **3.15 × 2.00 mm** — the SOD-123 outline max (2.85 × 1.70) plus
  0.15 mm/side.
- Pocket floor: **1.55 mm** above PCB top.
- Remaining plate under the pocket: **0.65 mm**.
- Clearance over a worst-case 1.40 mm diode: **0.15 mm**.
- Clearance over a measured 1.26 mm diode: **0.29 mm**.

The pocket is **machined, not cut through**. A through-cut would leave the switch
without plate support. The DXF carries a `RELIEF` layer and a text entity
repeating the depth. The first-article check must measure the pocket depth
directly, not with a feeler slid under the plate: the intentional 1.00 mm gap lets
a 0.5 mm feeler pass anywhere beside the diodes, so that test cannot distinguish a
pocket from a through-cut.

### 9.3 Encoder window

The rev-1 plate had a **12.7 mm square** encoder hole, sized for the rev-1 plate
band (z 2.0–3.5), where the EC11E body is 12.30 mm wide. The rev-2 plate band is
z 1.00–2.20, which intersects the encoder’s **terminal blocks**:

- 14.95 × 11.70 mm for z 0.0–1.5 (A/B/C and S1/S2 blocks),
- 12.30 × 11.70 mm for z 1.6–2.3 (the waist).

A 12.7 mm hole would have fouled the encoder by up to **1.41 mm/side**; the
encoder would not have passed through the plate. The window is now
**16.2 × 12.4 mm**:

- 0.625 mm/side in x, 0.375 mm on the tight side (the shaft is 0.25 mm off the
  envelope center),
- 0.35 mm/side in y,
- symmetric about the shaft so the two halves’ windows remain exact mirrors (the
  encoder is translated, not mirrored).

`gen_plate.py` asserts the window can never shrink below envelope + 0.2 mm/side.
The first article should caliper the real encoder’s terminals; if they do not
protrude above ~1.5 mm, the window could return to 12.7 mm square, but only with
that measurement in hand.

### 9.4 Tabs and poron

The plate grows **eight discrete tongues per half**:

- 10 mm wide,
- 5 mm proud of the PCB outline,
- 2 mm root fillets,
- chamfered tips.

Each tab carries a **7 × 4 mm poron pad** on top and bottom. The 7 mm axis runs
laterally across the 10 mm tongue; the 4 mm axis runs along the 5 mm tongue. The
pad spans rim-line to +4.0 mm, leaving 1.0 mm tip spare, with no tip overhang. The
tightest pad corner-to-edge is **0.71 mm**, which is no longer kerf-fragile (the
old 8 mm pad left 0.35 mm).

The no-screw load path is:

- The PCB hangs from the switches, which are clipped into the plate.
- The plate’s tabs sit in case pockets, with poron above and below.
- The top cover presses the top pads; the case shelf supports the bottom pads.
- The case never clamps the PCB directly.

Two tabs are pinned (top edge above the outer key column, bottom-inner corner
under the MCU); the rest spread evenly. The inner (microcontroller) edge carries
no tab because the MCU/TRRS/encoder windows occupy it fully; the remaining rim
finger is narrower than a tab root, so that zone floats between its flanking tabs
by design. Encoder push stays soft there.

### 9.5 Plate materials

| Material | Fabrication | Notes |
|---|---|---|
| **PC 1.2 mm** (default) | laser | Softest feel, virtually unbreakable, cheapest prototype. 1.2 mm is mandatory for Choc clip engagement. |
| POM 1.2 mm | mill/laser | Machines beautifully, slightly firmer. |
| FR4 1.6 mm | route | Stiff, cheap; glass dust when routing. |
| ALU 1.2 mm | laser/waterjet/CNC | Balanced feel, best sound; isolate from copper. |
| CARBON 1.2 mm | mill only | Stiffest; **conductive**; never laser (toxic dust + delamination). |

`MATERIAL` in the generator re-gates every web minimum: PC/POM 1.0 mm,
FR4/ALU 1.5 mm, CARBON 2.0 mm. Tab roots carry 2 mm fillets against crack
initiation in every material.

The plate stays shop-cut PC for rev 1. **Do not print it in PETG**: flex and
creep defeat the Choc clip.

### 9.6 Plate output and gates

`plate/gen_plate.py` writes:

- `Hojicha44-{Left,Right}-plate.dxf` — R12, mm, layers:
  - `OUTLINE` and `CUTOUT`: cut through;
  - `RELIEF`: 22 × 0.55 mm partial-depth pockets, machine only;
  - `PORON`: pad placement/punch template, **do not cut**.
- `Hojicha44-{Left,Right}-plate.svg` — preview.
- `Hojicha44-{Left,Right}-lands.json` — tab root centers for the case.

Gates include: 14.0 mm cutout assertion, encoder envelope + 0.2 mm/side, tab/pad
containment, z-stack clearance for every top-side part crossing the plate band,
mirror of the right tabs from the left roots, and a byte comparison of the
generated DXF/SVG/lands against the tracked files. The `--check` mode regenerates
into a tempdir and fails on any drift.

---

## 10. Case and cover

### 10.1 The stack

All z values are in the PCB-top frame (z = 0 at the PCB top surface).

| Layer | z | Notes |
|---|---:|---|
| Bottom case floor | −4.65 | 1.0 mm clearance under the deepest untrimmed part (encoder legs −3.65) |
| Floor slab | 1.7 mm thick | Tub bottom −6.35 |
| Bottom poron shelf | −1.55 | Compressed 3.0 mm bottom foam at 15% |
| PCB | −1.6…0 | 1.6 mm |
| Plate gap | 0…1.00 | Choc clip band |
| Plate | 1.00…2.20 | 1.2 mm |
| Top poron | 2.20…3.20 | 1.5 mm foam compressed to 1.00 at 33% |
| Cover | 3.20…5.20 | 2.0 mm thin top plate |
| Assembled height | 11.55 mm | Desk → cover top |
| Desk → cap top | 13.93 mm | Flat Saddle cap |

The floor is provisioned by the **below-PCB protrusions**, not by the hotswap
sockets:

- encoder legs: **−3.65 mm** (deepest; vendored EC11E STEP),
- TRRS THT pin tips: **−3.0 mm**,
- Choc socket bump: **−1.25 mm**,
- slide-switch legs: **≤ −3.5 mm** (family bound; caliper on first article),
- JST PH: **~ −2.5 mm** (family bound).

The deepest known is −3.65, so `FLOOR_Z = −4.65` keeps 1.0 mm. The floor slab is
1.7 mm; the tub bottom is −6.35. A future option is to clip the THT leads after
soldering, raising the floor by ~0.8 mm, but the user prefers no trimming and the
design does not depend on it.

### 10.2 The tub

`case/gen_case.py` generates the bottom tub. Its key behaviors:

- The exterior dilates the **PCB rim**, not the plate outline, so the eight tabs
  do not create bulges.
- `CASE_OUTSET = 8.2 mm` gives a wall over the tab tip of ~2.7 mm and a local band
  of ~7.7 mm, enough for the magnet stations.
- The cavity pockets swallow the tabs; the shelf under each tab is the poron
  support.
- The floor steps down under the PCB zone; a flat floor at sandwich depth would
  collide with the encoder/TRRS/JST parts.
- Ports are **shaped bores**, not full-wall rectangles.

Measured current values (per half, 2026-10-24 generation):

- tub volume ~57.5 cm³,
- wall minimum ~2.62 L / 2.70 R,
- pocket-corner webs ~2.45 / 2.35,
- magnet band min ~7.68, web min ~1.69,
- antenna margin ~14.15 mm in-plane, ~5.60 mm to the floor.

### 10.3 The thin top cover

The original v3.5 design had a **ring cover** z 4.70–7.70. User review called it
“extraordinarily thick” and noted the caps barely poked out. The v4.0 redesign
made the top a **2.0 mm plate at z 3.20–5.20**:

- The plate cannot move upward: it must stay at the Choc clip band 1.00–2.20.
- The top therefore comes down: `TOP_LIP_Z` moved 4.70 → 3.20 by using 1.5 mm top
  foam at 33% compression (`TOP_PRELOAD`).
- The cover spans the key field with **one merged opening** around the 22 KLP cap
  footprints (17.48 × 16.48 mm + `CAP_CLEAR`).
- The current `CAP_CLEAR` is **1.5 mm/side**, so the 19 mm-pitch caps merge across
  rows and columns into one clean field, with zero row-webs/enclosed scraps. At
  1.0 mm, the 0.52 mm webs read as “ridges and dots”.
- The cover has windows for the MCU, the EC11 body (12.0 × 11.7 mm at the cover
  band +0.5 mm/side), the power-switch body/nail, the shared USB slot, and a
  **Ø6.0 mm round TRRS side hole** at zc 1.5 with a 0.7 mm roof.
- The cover is **flat (no-indent)**; the 0.8 mm ledge was removed after review.
  The only embellishment is a 0.4 mm chamfer on the outer-rim top edges.
- The cover presses the top poron pads at the designed 33% preload.
- Eight Ø4.3 × 0.7 mm magnet pockets mirror the tub stations; the pocket floor is
  1.3 mm (gated ≥ 1.2).

Cover volume is ~15.2 cm³ per half. The older ring-cover numbers (10.7 cm³,
z 4.70–7.70) are historical.

### 10.4 Ports

The port contract is structural, not a fixed depth:

- **USB**: 14.0 mm-wide slot with 1.2 mm bottom fillets, spanning z 2.0 to the top.
  The plug axis rides at the lip plane; the overmold bottom is ~2.8, so only the
  lower part crosses the wall. The neck above the lip exits through the open top,
  which is the cover’s duty. The measured outer extent is printed each build
  (`usb out=20.20` at `OUTSET 8.2`).
- **TRRS**: current cover uses a **Ø6.0 mm round side hole** at zc 1.5 with a
  0.7 mm closed roof. It clears a straight 3.5 mm barrel 1.25 mm/side. The old
  Ø9.5 boot bore was the “gaping” opening the review rejected. The tub’s port is
  still a shaped bore; the cover’s is the small side hole.
- **Power switch**: 5.0 mm-wide actuator slot spanning z 4.3 to the top, with
  0.8 mm bottom fillets. The WS-SLTV body sits wholly inside the cavity; the red
  actuator shows through and is flicked with a fingernail from above. The slot is
  centered on the switch origin (Left 106.3, Right 185.2), clearing the tab-4
  pocket by ≥3.2 mm and the USB mouth by ~1.8 mm.

The generator **marches each bore’s outer face outward until it actually exits the
skin**, rather than pinning a depth. This was a hard-won fix: the rim dilation
bridges the USB notch, so a fixed-depth slot shipped sealed in v3.2. The current
gate re-proves on the finished solid that the mouth is void, air just beyond is
air, and the slab under the bore stays solid (no hole in the case bottom).

### 10.5 Retention magnets

- **Eight stations per half**, symmetric by construction: the left set is computed
  once; the right is its exact mirror `x → 291.5 − x` and is re-validated against
  right boundaries, ports, tab pockets, and antenna. Any asymmetric rejection
  aborts the build instead of producing unequal counts.
- Station filters: local band ≥7.5 mm, web ≥1.6 mm to both boundaries, ≥5.15 mm
  from every port/tab rect, ≥10.1 mm from the antenna center, ≥14 mm from other
  stations, snapped at perimeter/8 spacing.
- Tub pockets: Ø4.3 × 2.2 mm, face flush at the lip plane (`TOP_LIP_Z`), for a
  Ø4 × 2 mm N52 magnet glued face-up.
- Cover pockets: Ø4.3 × 0.7 mm, floor 1.3 mm, for a Ø4 × 0.5 mm N52 magnet glued
  face-down. The asymmetric pair is deliberate: the faces meet at the lip plane,
  and the rigid face contact is the zero-gap stop, not the foam.
- Pull test: with the plate installed, a straight lift must hold **≥1.5 kg**
  before the cover lifts. Eight mixed pairs are predicted to give ~2–2.8 kg; the
  glue lap is the weak link, not the 1.3 mm pocket floor.
- Polarity is a physical procedure: pick the orientation on one tub/cover pair
  (must attract), dry-stack all 16 in their pockets, confirm every station
  attracts, glue one, re-test, then continue. All stations same orientation keeps
  covers interchangeable between halves.

**Documentation drift:** `spec/case.md`’s retention section still describes the
old ring cover (z 4.70–7.70) and 4 × 2 magnets on both sides;
`spec/first-article.md` and `spec/bom.md` still list Ø4 × 1.5 cover magnets and a
1.7 mm pocket. The current thin-top generator (`case/params.py`,
`gen_cover.py`) uses the 0.7 mm pocket and Ø4 × 0.5 cover magnet described above.
This is a live documentation inconsistency, not a geometric ambiguity: a 2.0 mm
cover cannot take a 1.7 mm pocket and keep a 1.3 mm floor. The first-article
magnet text should be corrected before ordering the thin-top cover.

### 10.6 Materials and strength

- **MJF PA12** is the production-order reference for the tub and cover: best
  press-fit realism for the magnet pockets, gasket compression, and the magnet
  zero-gap stop.
- **PETG at 100% infill is a supported self-print material** (user decision
  2026-10-24). The strength audit says every thin feature is ≥1.2 mm except one
  non-spanning rim; PETG (E ≈ 2.1 GPa, tensile ≈ 50 MPa) is stiffer and as strong
  as MJF PA12 (E ≈ 1.65 GPa, ≈ 48 MPa) on every load path.
- The PETG risks are **warp and dimensional**, not strength: 4+ perimeters, brim
  on the 167 mm tub, calibrate XY against the 166.9 mm outer width, print as
  oriented (tub open-face-up, cover underside-up).
- The only through-layer tension is the eight magnet-pocket floors (~0.7 MPa
  under a 1 kgf magnet, trivial vs PETG’s ~20 MPa through-layer strength).
- Acrylic is an anti-recommendation for the plate: brittle at the gasket tabs.
- The case shell near the antenna must be plastic/wood — no metal, no carbon
  fiber. The 3 mm rule is met with large margin, but the real validation is the
  BLE range bench.

### 10.7 Service story

There are no fasteners. Reaching the JST cell connector or swapping a nice!nano
means:

1. Lift the cover (magnets).
2. Unseat the plate (22 Choc clips through 14.0 mm holes against the socket
   contacts).
3. Pull switches straight out of their sockets with a switch puller; never pry
   against the 1.2 mm PC plate.

Do this on a soft mat. Practise the sequence during the first article and time it.
If a cell swap takes more than ~10 minutes or cracks a plate, the next case
revision should add a hidden screw or a JST extension at the USB end.

### 10.8 Mirror discipline

The two halves must be exact mirrors where the design says they are. The mirror
axis is `x = 145.75`; right = `291.5 − left`.

Gates:

- `pcb/generators/check_board.py --self-test` — board 0.0000 mm, plate 0.0100 mm,
  with a 0.5 mm negative control.
- `case/mirror_gate.py` — tub 0.0094 mm, cover 0.0000 mm, floor 0.05 mm, with
  negative controls.
- The right plate’s tab roots are derived from the left roots and re-projected
  onto the right rim, not re-walked independently.
- Magnet stations are mirrored by construction.

The encoder is a deliberate exception: it is a **translated, not mirrored**, part,
so its window is symmetric about the shaft rather than mirrored about the split.

---

## 11. Firmware and keymap

### 11.1 Shield structure

The ZMK shield `hojicha44` requires `nice_nano_v2`. It has two siblings:

- `hojicha44_left` — the split **central**; USB HID enabled; UART enabled.
- `hojicha44_right` — the split **peripheral**; BLE only; UART left disabled.

The shared `hojicha44.dtsi` contains:

- the 4 × 6 `kscan0` matrix, `diode-direction = "col2row"`;
- row/column GPIOs (identical Arduino pins on both halves);
- a 12-column × 4-row `default_transform`, with the right overlay setting
  `col-offset = <6>`;
- the EC11 encoder node (`alps,ec11`, A0/A1, `steps = <60>`,
  `triggers-per-rotation = <30>`);
- the encoder push as a `gpio-keys` button on D16, plus a
  `zmk,kscan-gpio-direct` node (`enc_push_kscan`) that emits row 0/column 0;
- the UICR `nfct-pins-as-gpios` option.

The half overlays differ only in UART and split role. The left overlay enables
`uart0` and the shared encoder node; the right overlay sets the column offset and
enables the shared encoder node. Both halves define the same encoder node; the
name `left_encoder` is a shared node name, not a left-half leak.

### 11.2 Kconfig and split roles

`Kconfig.defconfig`:

- `SHIELD_HOJICHA44_LEFT` sets `ZMK_KEYBOARD_NAME="Hojicha44"` and
  `ZMK_SPLIT_ROLE_CENTRAL=y`.
- Both shields set `ZMK_SPLIT=y`.

`config/hojicha44.conf` (shared):

- `CONFIG_EC11=y`
- `CONFIG_EC11_TRIGGER_OWN_THREAD=y`
- `CONFIG_ZMK_BLE=y`
- `CONFIG_ZMK_BATTERY_REPORTING=y`
- NFC-pin comment.

`config/hojicha44_left.conf` adds:

- `CONFIG_ZMK_USB=y` (central only)
- `CONFIG_ZMK_SPLIT_BLE_CENTRAL_BATTERY_LEVEL_FETCHING=y`
- `CONFIG_ZMK_SPLIT_BLE_CENTRAL_BATTERY_LEVEL_PROXY=y`

There is deliberately **no** `hojicha44_right.conf`; the peripheral needs
nothing beyond the shared conf and Kconfig, and `ZMK_USB=y` there would warn
because the peripheral has no USB device role.

### 11.3 Keymap variants

Four variants, differing **only** in home-row mod order and which thumb carries
Space:

| Variant | Mod order (pinky→index) | Space thumb | Audience |
|---|---|---|---|
| `mac_left` | CAGS (Ctrl Alt GUI Shift) | left | macOS-heavy; default |
| `mac_right` | CAGS | right | macOS |
| `win_left` | GACS (GUI Alt Ctrl Shift) | left | Windows/Linux |
| `win_right` | GACS | right | Windows/Linux |

Rationale:

- Windows/Linux modifier frequency: GUI < Alt < Ctrl < Shift → GACS, with Shift
  on the index finger (strongest) and Ctrl on D/K.
- macOS adds Cmd (=GUI, second-most-used) and demotes Ctrl → CAGS, with Ctrl on
  A/;, Cmd on D/K, Alt on S/L.
- Mods are side-specific: `L*` on the left hand, `R*` on the right.
- Shift stays on F/J in both orders.

The active variant is `config/hojicha44.keymap` (what CI builds). The default is
`mac_left`. Switching is:

```sh
python3 config/gen_keymap.py --use win_right
```

which rewrites the active keymap, to be committed. All four variants are always
regenerated into `config/variants/` for diffing and local flashing.

### 11.4 Layers

The base layer is:

```
Q W E R T  ~`    |  P O I U Y  |\
hml A S D F  G [ |  ; L K J  H  ]}
Z X C V B  -     |  / . , M N  '
Esc  L1  Tab  Space    |    Del  L2  Bksp  Enter
```

where `hml`/`hmr` are per-hand home-row mod-taps and `?` is GUI/Ctrl depending on
the variant. Bars and brackets are shifted symbols; `|` is shift-backslash.

**L1 (lower)**:

- row 0: digits `1 2 3 4 5 6 | 7 8 9 0 - =`
- row 1: shifted symbols `! @ # $ % ^ | & * ( ) _ +`
- row 2: `F1…F6 | F7…F12`
- thumbs transparent; encoder = scroll (`C_AC_SCROLL_UP/DOWN`).

**L2 (raise)**:

- left half: BT clear/select 0–4, media (mute/prev/play/next/vol ±), clipboard
  (undo/cut/copy/paste);
- right half: inverted-T arrows, PgUp/PgDn, Home/End/Ins/PrtSc, Caps, Del/Bksp;
- thumbs transparent; encoder = prev/next track.

**Adjust (layer 3)**:

- `conditional_layers`: if layers 1 and 2, then layer 3.
- `&bootloader` at the W position; `&sys_reset` at the E position.
- Every other key `&none` — there is nothing safe to type mid-chord.
- Encoder = volume.

The bootloader/reset positions are on the left top row, above the ring/middle
home mods; both thumbs are busy holding the chord, so the placement is deliberate.
The first-article bench requires a recovery UF2 and a proven re-entry before
pressing the bootloader key.

### 11.5 Home-row mods

The recipe is ZMK’s documented “timeless home row mods”:

```
flavor = "balanced"
require-prior-idle-ms = <150>
tapping-term-ms = <280>
quick-tap-ms = <175>
bindings = <&kp>, <&kp>
hold-trigger-key-positions = <the OTHER hand's 22 positions>
hold-trigger-on-release
```

One behavior per hand so the trigger lists can differ. The lists are computed from
the layout, not hand-typed: left hand lists the right hand’s positions and vice
versa, row-major interleaved. The keymap gate asserts them against the layout.

How it resolves:

- Fast roll “ao”: O is same-hand as A, so A resolves on O’s press+release before
  the term → tap → “ao”.
- Hold A, press K: K is other-hand → hold fires on K’s release → instant
  cross-hand shortcut.
- Hold A, press G (same hand): G is not in the trigger list → A still resolves to
  the modifier if held past the term or when a listed key resolves. This is the
  accidental-mod insurance.
- `require-prior-idle` keeps fast rolls as taps even past 150 ms.
- `quick-tap-ms` on a double-tap-hold repeats the **letter**, not the modifier.

### 11.6 Encoder push sideband

The EC11 push is **not** in the 46-cell matrix. It is a dedicated GPIO (D16) with a
`gpio-keys` node and a `zmk,kscan-gpio-direct` node that emits a single row-0 /
column-0 event. A `zmk,kscan-sideband-behaviors` node maps that event to
`&kp C_MUTE` on both halves. This keeps the matrix transform and keymap cell count
untouched. The first article checks push on each half.

### 11.7 Keymap generation and gates

`config/gen_keymap.py` reads `spec/layout.yaml` and emits:

- `config/hojicha44.keymap` (active),
- `config/variants/hojicha44_<variant>.keymap` (all four).

`--check` does two things:

1. Re-derives every binding and **byte-compares** the tracked files. A legend
   edit without regeneration, or a generated file edited by hand, fails.
2. Structurally validates each emitted keymap:
   - exactly 4 layers × 46 bindings;
   - exactly one real `sensor-bindings` per layer (`&trans`/`&none` there is
     rejected by pinned v0.3);
   - mods exactly on the 8 home positions with the right variant codes;
   - Space/Enter on the variant’s thumb pair;
   - `&mo 1` / `&mo 2` fixed;
   - hold-trigger lists exactly the other hand’s 22 positions;
   - `hold-trigger-on-release` present;
   - the L1+L2→3 chord present;
   - exactly one sideband Mute;
   - no interior semicolons in binding arrays (dtc 1.8.1 treats them as syntax
     errors; the generator uses newline-separated rows).

Negative controls have been demonstrated: wrong tap keycode, deleted binding,
legend drift, truncated trigger list, and thumb canonical-order edit all fail
loudly and revert clean.

### 11.8 CI

- `.github/workflows/build.yml` calls the pinned ZMK reusable workflow at
  `edf5c0814fd3ea202e43aad2d68fd32e882a518c` (tag v0.3), building
  `nice_nano_v2` + `hojicha44_left` and `hojicha44_right` with the active keymap.
- `.github/workflows/build-variants.yml` compiles each of the four variants the
  same way a user would: `gen_keymap.py --use <variant>`, then a west build.
  One shield per variant is sufficient because the keymap file is shared by both
  shields.
- `.github/workflows/checks.yml` runs the static spec/gate suite, the plate gates,
  the case gates, and the release `--check` without requiring KiCad in CI.
- `config/west.yml` pins ZMK to the same v0.3 commit as the workflow. The pairing
  is deliberate; the `@main` workflow carries a compatibility diagnostic this tree
  predates.

### 11.9 Flashing and bring-up

- First flash per half must use **full chip erase** (`--erase`) so the UICR NFC
  option is written.
- After flashing both halves: BLE-pair, confirm keys from each side, confirm
  encoder push.
- If the encoder push is dead, re-flash with `--erase` before suspecting
  hardware.
- The spare input D10 has no keymap binding and no test pad. It cannot be
  “verified by toggling”; check continuity/level with a DMM if needed.
- The firmware bench covers: per-half type-through, thumbs, encoder direction per
  layer, encoder push, all 8 home-row holds/taps, fast rolls, same-hand chords,
  L1/L2 content, the Adjust chord, and the bootloader recovery.

---

## 12. Gates, manifests, and provenance

### 12.1 The gate family

| Gate | What it proves |
|---|---|
| `npm test` / `tests/spec_checks.cjs` | Spec parses; ERC stanza is correct; TRRS comment matches measured geometry; no duplicate schematic NEED entries; W1 exact set passes and a 29th fails; ZMK transform matches keymap; BLE-only, COL2ROW; encoder steps/TPR; stack ties; print manifest hashes; title-block rev tracks spec. |
| `gen_keymap.py --check` | All 5 keymap files are byte-identical to a fresh derivation and structurally valid. |
| `gen_plate.py --check` | Plate geometry gates plus byte comparison of DXF/SVG/lands. |
| `gen_case.py` / `gen_cover.py` | Solid topology, volumes, wall/web minima, magnet stations, port breach, bore probes, antenna clearance, mirror. |
| `check_board.py` | Pad/via containment, TRRS crossover, antenna keepout, W1 pad equality, silk-to-edge, mirror self-test. |
| `make_release.py --check` | Bundle hashes, manifest commit vs board history, no extra files, ERC/DRC reports. |
| `case/mirror_gate.py` | Tub/cover STEPs are exact mirrors within 0.05 mm, with a 0.5 mm negative control. |
| CI workflows | Static checks, plate gates, case gates, active firmware build, all four variants. |

### 12.2 Release versus print manifest

These are deliberately separate:

- **PCB release** (`generated/release/vX.Y.Z/`) contains Gerbers, drill, BOM,
  position files, ERC/DRC, and a manifest with board hashes and tool versions.
- **Print manifest** (`generated/print/vX.Y.Z/MANIFEST.txt`) contains SHA-256 for
  the six tracked plate files and the eight case solids. The shops are sent
  exactly those files.

The print manifest exists because the plate and case are not part of the PCB
Gerber bundle. If any generator constant changes, the plate and case must be
regenerated and the manifest re-recorded **in the same commit**. The `npm test`
print-manifest gate re-verifies the tracked plate files and any local case solids.

### 12.3 Negative controls

The project treats a gate without a negative control as suspect. Concrete
examples:

- W1: appending a 29th `lib_footprint_mismatch` must fail.
- Plate: CUTOUT=14.015 (inside the assertion window) must still produce a
  `STALE` result because the byte comparison catches it.
- Print manifest: tampering with one byte of `lands.json` must fail.
- Keymap: wrong tap keycode, deleted binding, legend drift, truncated trigger
  list, thumb order edit — all must fail.
- Mirror: a deliberate 0.5 mm asymmetry must be caught.
- Frame: a Y-negated control board must fail the notch/outline self-test.

This is the difference between “the check ran” and “the check would have caught
the bug”.

### 12.4 The authority order, restated

For a question about the current design:

1. **Generators + gates + manifests** define what is built and what will be
   fabricated.
2. **Specs** define intent and the reasons; if they disagree with a generator,
   one of them is wrong and must be fixed.
3. **READMEs** are orientation; they can lag.
4. **Notes/audits** are historical evidence, not current truth.
5. **Roadmap/renders** are intent and presentation.

The synopsis follows that order. Where it quotes a number that is not current, it
says so.

---

## 13. Manufacturing and BOM

### 13.1 What is ordered

Per half:

- 22 × 1N4148W SOD-123 diodes (SMT, top side).
- 22 × Kailh PG1350 Choc v1 switches (not soldered; seat into sockets).
- 22 × Choc v1 hotswap sockets (SMD, bottom side; footprint-only, no MPN, **not
  in the released BOM**).
- 1 × nice!nano v2 (socketed).
- 2 × 2×12 machine-pin SIP strips (assembled 4.5–5.0 mm; the 2.11 mm Mill-Max 315
  variant is banned by height).
- 1 × short-shaft EC11-class encoder with push (or EC11E15244G1 fallback + tall
  knob/trim).
- 1 × low round EC11 knob, Ø6 D bore, OD 15–17 mm, height ≤12 mm.
- 1 × XKB PJ-320A TRRS jack.
- 1 × right-angle 4-pole CTIA TRRS cable.
- 1 × JST S2B-PH-K-S + PHR-2 housing + 2 × SPH-002T-P0.5S crimps.
- 1 × Würth WS-SLTV 450301014042 slide switch.
- 1 × 301230 110 mAh LiPo with PCM + JST-PH pigtail.
- 1 × PPTC polyfuse, 0.5–1 A hold, ≥16 V, in the pack+ lead.
- 1 × 1.2 mm plate (PC default).
- 16 × 7 × 4 mm poron pads (8 tabs × top/bottom).
- 8 × Ø4 × 2 mm N52 tub magnets.
- 8 × Ø4 × 0.5 mm N52 cover magnets (current thin-top generator; older docs say
  1.5 mm — see §10.5).
- Kapton tape, solder, flux.

For the pilot: 5 half-pairs (10 halves), 20 PCBs, 20 plates, 12–15 cases, 490
switches, 450–500 hotswap sockets, 500 diodes, 12–14 cells, 150 magnets, 12
modules, 20 polyfuses. Indicative unit cost ~USD 35–70 per half.

### 13.2 JLCPCB quote fields

The manufacturing guide fixes every design-shaped field:

| Field | Value |
|---|---|
| Base material | FR-4 |
| Layers | 2 |
| Product type | Industrial/Consumer |
| Quantity | 5 per design (10 total) |
| Thickness | 1.6 mm |
| Color | Black (alt purple) |
| Silkscreen | White |
| Material type | FR4-TG135 |
| Surface finish | **ENIG** |
| Outer copper | 1 oz |
| Via covering | Tented |
| Via plating | Not specified |
| Min via | 0.3 mm hole / 0.4–0.45 mm tier |
| Outline tolerance | ±0.2 mm regular |
| Confirm production file | No |
| Mark on PCB | Remove |
| Electrical test | Flying probe fully test |
| Gold fingers / castellations / edge plating / blind slots / UL / humidity card | No |

The board is **over the 100 × 100 mm value tier** at ~150.5 × 114.6 mm, so the
live quote decides price. A 5-piece ENIG order of this size has been seen around
USD 35–70 before shipping, but that is research, not a quote.

### 13.3 Assembly intent

The design is **hand-solder**. The released `bom.csv` is not sufficient for a
contract assembler because the 44 Choc hotswap sockets are footprint-only and
have no MPN. Ordering PCBA from `bom.csv` would ship boards with zero sockets.
The BOM order list is the authoritative shopping list.

Solder order:

1. Slide switch first (the charge disconnect), then re-verify JST-1 → RAW with
   switch ON and open with OFF.
2. Diodes (D_Lxx / D_Rxx; cathode tick to the row).
3. Choc hotswap sockets (B.Cu).
4. nice!nano machine-pin sockets (2×12 headers).
5. TRRS jack, JST, switch wiring, encoder.
6. Modules last.
7. Cell sandwich: Kapton over the pouch face and nano underside; cell between
   the socket rows; JST leads beside the cell, never under the stack.
8. Plate onto the switches.
9. PCB into the tub.
10. Poron pads (bottom, then top).
11. Magnets (tub face-up, cover face-down, polarity stack-tested).
12. Cover on.

### 13.4 Plate and case ordering

- Plate: 1.2 mm PC (default), laser cut, four DXF layers:
  - OUTLINE + CUTOUT cut through;
  - RELIEF = 22 × 0.55 mm pockets, machine only;
  - PORON = punch template, do not cut.
- Ask the plate shop **first** whether they can do the 0.55 mm partial depth.
  A plain laser cut cannot; controlled-depth laser engraving or CNC depth milling
  can. PCBWay’s Z-axis milling is documented with ±0.15 mm depth tolerance, so
  order **0.70 mm nominal** and caliper the delivered 0.55–0.85 mm. JLCPCB
  publishes no controlled-depth service. If every pocket route fails, one
  `gen_plate.py` constant can flip the pockets to through-cut relief holes at the
  cost of 22 open holes.
- Case: MJF PA12 from `gen_case.py` / `gen_cover.py`; volumes ~57.5 cm³ tub +
  ~15.2 cm³ cover per half. PETG 100% infill is the cheap self-print alternative.

---

## 14. First article — the physical gate

The first-article checklist is the release gate for physical items. Nothing in it
can be proven in software. The order policy distinguishes:

- **engineering-sample orders** — coupon, encoder coupon, one PCB pair, one
  printed tub/cover set — which are permitted and required before the batch;
- **production/batch order** — the 10-half pilot — which is blocked until the
  checklist passes.

### 14.1 The coupon

A 100 × 100 mm sheet of the **real plate material and thickness** (1.2 mm PC),
cut by the same vendor with the same process, carrying:

- four 20 × 20 mm squares with **13.8 / 14.0 / 14.2 / 15.0 mm** holes, concentric;
- a fifth square with a 14.0 mm hole and the **0.55 mm diode-relief pocket**
  (3.15 × 2.00 mm) in its underside.

Tests:

1. Caliper the coupon thickness: must be **≤1.25 mm**.
2. Drop a PG1350 into each hole: does the 13.8 body pass? Does the 14.0 clip lip
   grab the 1.00 mm underside? Do the 14.8 ears seat on the 2.20 mm top?
3. On the relief square: pocket is 0.55 mm deep, **not through** (0.65 mm
   remaining), and the plate still sits flat on the switch housings.
4. If 14.0 does not catch, drop to **13.9** and re-cut the coupon.

The coupon costs a few dollars and a day. A wrong 0.1–0.2 mm hole size costs two
plates, 44 switches, and a re-cut of the case stack.

### 14.2 Paper fit

- Print the fit PDFs at 100% / actual size.
- Calibrate: adjacent key centers must measure **19.00 mm**.
- Check the module footprint, socket rows (15.24 mm apart, 2.54 mm pitch), USB
  notch width (11 mm), battery outline, TRRS gap, and case port bores.
- The fit sheet shows the PCB only; the encoder window is in the plate DXF.

### 14.3 Bare-board DMM

Before soldering modules:

- JST pigtail red → pin 1 (`+`), black → pin 2; continuity beep and record.
- Pack+ → RAW with switch ON (<1 Ω); switch OFF open.
- Solder the slide switch **first**, then re-verify.
- On a real nice!nano: RAW↔B+ short, GND↔B− short, RAW↔VCC open. Power enters via
  RAW; B+/B− stay open.

There is no reverse-polarity protection. Any doubt: stop.

### 14.4 Assembly and power-on

- Socket stack height: 4.5–5.0 mm assembled; reject <3.5 or >5.0.
- Diode map: D_Lxx / D_Rxx sits +x of its switch, 9.5 mm in local +x (thumb arc
  exceptions follow the switch rotation).
- Cell sandwich: Kapton both faces, JST beside the cell.
- Charge with switch ON: orange LED lights; OFF does nothing.
- TRRS continuity: tip-to-tip, ring1-to-ring1, sleeve-to-sleeve; ring2 open both
  ends.
- USB notch solder inspection: pads 0.78 mm from the edge; loupe-check mask and
  bridging.
- Encoder: both directions, push click, knob clears cover and caps through full
  rotation and push.
- BLE range with cells and case: note the measured range; fallback cell 301228.

### 14.5 Firmware bench

Record the flashed variant. Then:

- Two per-half type-throughs on the base layer; every QWERTY letter and
  ``` `~ | \ - ' [ { ] } , . : ; / ``` appears correctly.
- Thumbs: Space/Enter, Tab/Backspace, Esc/Delete.
- Encoder per layer: base volume, L1 scroll, L2 track, Adjust volume; direction
  correct on both halves.
- Encoder push on each half = Mute.
- All 8 home-row positions: deliberate hold, fast roll, same-hand chord,
  double-tap-hold.
- L1 digits/shifted/F-keys; L2 nav/media/BT; L1+L2 Adjust.
- Bootloader key with a recovery UF2 ready; prove re-entry.
- While Adjust is active, normal keys are dead.

### 14.6 Case labels

Apply before daily use:

- At the switch: `CHARGE ONLY WHEN ON`.
- At the TRRS jack: `TRRS: POWER OFF + USB OUT BOTH SIDES`.
- Inside the battery bay: `+ RED PIN1 — METER BEFORE PLUG-IN`.

---

## 15. Compliance and distribution

The keyboard is a battery-powered BLE (2.4 GHz) device: one nice!nano / Seeed XIAO
nRF52840 per half, USB-C, a 301230 LiPo per half. That makes it a short-range
(SRD) intentional radiator in every market.

**Current decision: personal builds only.** No sale or supply of units is planned
for `v0.5.0`. The product-level obligations become live only if that changes. The
module-grant nuance matters: installing the nice!nano yourself is fine, but
**instructing an end-user to install it is a compliance act** — another reason
this stays a self-build.

### 15.1 Australia / New Zealand

Two independent regimes, one mark:

- **ACMA (EMC/radio)**: register as an **“ACMA-only” Responsible Supplier** on the
  EESS database — free. Complete ACMA form **C02** Supplier’s Declaration of
  Conformity. Apply the **RCM** mark per AS/NZS 4417.1. Keep evidence producible
  within 10 business days; retain 5 years.
- **EESS (electrical safety)**: **not applicable**. The keyboard is extra-low
  voltage (<50 V AC / <120 V ripple-free DC), so it is out of scope; no EESS
  registration, no CoS, no compliance folder.
- **New Zealand**: same RCM mark; get a Supplier Code Number if importing.
- **Testing is not required** for a compliance level 1 (low-risk) BLE device. The
  supplier prepares a device description and signs the C02; a lab report is
  optional. A paid lab test is not a prerequisite.
- Penalties for supplying unlabeled or prematurely labeled product can reach 500
  penalty units.

### 15.2 Bluetooth SIG

- Adopter membership is **$0**.
- Product Qualification Fee is **$12,000** + **$1,250** Company Identifier, only
  if a unit is sold or branded.
- The keyboard is an **Unmodified Design** (Nordic’s qualified nRF52840 + ZMK), so
  it lists with no new RF testing.
- A self-built, never-sold pilot owes nothing. SIG membership is company-only, so
  an individual would need an entity.
- The owner dropped the SIG gate for the hobby build (2026-10-23); it reappears
  only if units are sold.

### 15.3 United States and EU (future)

- **US**: FCC Part 15 Subpart C (§15.247). The XIAO module has a Single Modular
  Approval (FCC ID Z4T-XIAONRF52840). The host must still carry the module’s FCC
  ID plus its own Class B statement and §15.21 manual text. It does not get its
  own FCC ID. SDoC testing ~USD 1,500–3,000; certification ~USD 4,000–8,000.
- **EU**: RED 2014/53/EU, EN 300 328, EN 301 489-1/-17, EN 62368-1, EN 50665.
  Cybersecurity Delegated Regulation (EU) 2022/30 applies from 1 Aug 2025, with
  EN 18031-1/-2/-3 cited with restrictions; (EU) 2026/339 repeals 2022/30 from
  11 Dec 2027, aligning with the Cyber Resilience Act. WEEE and RoHS apply.
  RED self-declaration with a lab report ~EUR 2,000–5,000; Notified Body adds
  EUR 5,000–15,000.
- The same board ships; only labels, manuals, and paperwork differ. **Do not print
  a market-specific label on the case** until the market is fixed; the RCM label
  is a sticker.

### 15.4 Transport

- The cell is 0.407 Wh, a small lithium-ion cell.
- UN 38.3 test summary is required for transport.
- IATA PI 967 Section II applies to batteries contained in equipment (≤2
  batteries or 4 cells per package; installed in the device for international
  mail).
- `notes.md` records a correction history for the transport memo: the earlier
  “UN 3480, PI 965 Section II, packed with equipment” line was wrong; UN 3481/PI
  967 is the correct pairing.

---

## 16. Renders and presentation

The render programme is Phase 10 of the roadmap. Its discipline: **build from
committed engineering artefacts only; no hand-modeled stand-ins for anything that
exists in the repo.** What you see is what the release contains.

### 16.1 Pipeline

```
renders/fetch_keycaps.sh        # download pinned keycap sources (network)
renders/build_assets.py         # case/.venv: kicad-cli STEP export, plate
                                # extrusion from DXF, knob/screw solids,
                                # named glTF conversion, placements.json
renders/scene.py                # Blender 5.2 headless: assembly, plate-hole
                                # registration gate, PBR materials,
                                # procedural textures, studio floor, shots
```

The standard deliverable is a bright hero + exploded view; the full shot set adds
top, macro, and orbit. `scene_env.py` adds desk and mat environments, reusing
`build_keyboard()` so there is no duplicated assembly.

### 16.2 Frame and registration

- The board is stored y-down; `kicad-cli` STEP export negates y; plate DXF and
  case STLs are y-up.
- Everything is assembled in one design frame: `placements.json` converts the
  board `(x, −y)`; `cutouts.json` transcribes the plate DXF as-is.
- The plate cutout holes are the registration master. Every switch footprint is
  matched to a hole; the scene aborts if any is more than 0.05 mm away. At
  `v0.5.0`: 22/22 switches per half, worst 0.0000 mm.
- There is no 1.4 mm “socket offset”; the plate polylines have a duplicated first
  vertex, so bbox centers are used, not vertex means.

### 16.3 Keycaps and stack

- KLP Lamé by braindefender, **CC-BY-SA 4.0**, pinned commit
  `8e4b89b484cafe3bcaced6b459a4e29660991a40`.
- Variants: flat Saddle on finger rows, Saddle Homing on G/H, Thumb on the four
  thumb keys. The renders use tall Normal_Tilted caps for the final look; the
  case geometry is cap-agnostic at the shared Saddle foot.
- Render stack (z = PCB top): substrate −1.60…0; bottom gaskets −1.55…1.00;
  plate 1.00…2.20; switch body 0.30…3.30; cap stem tip 1.50; top gaskets
  2.20…3.20; KLP cap top ~11.14, ~5.9 mm proud of the 5.20 cover.
- Encoder: short-shaft EC11 truncated at 13.5 mm, under a Ø16.8 × 9.2 fluted
  knob; skirt bottom 6.1 (0.9 mm above the cover for push travel); crown 15.3;
  nearest cap clearance 3.6 mm at every angle.
- Colourway hierarchy: warm-bone satin PBT caps > mid-grey matte PLA case >
  near-black waxy POM plate; silver knob, gunmetal encoder, gold PCB traces.
- Pose: halves parented to an empty on each outer bottom edge, 2.5 mm further
  apart, 2.5° splayed in plan, 5° tented. This is a pure render transform; the
  case files build the assembled 2.11 mm seam layout.

### 16.4 Shot programme

- **bright/**: hero, top, exploded, orbit_02, orbit_08.
- **dark/**: “stealth” colourway on dark swirly marble; hero, top, orbit_02,
  orbit_08.
- **play/**: multicolour keycaps, curated six-colour palette, mid-grey case,
  silver plate; hero (+top).
- **artisan/**: a single expressive accent cap closeup.
- **env/**: desk (wireless story, all keyboard cables hidden) and mat (cable
  dressed between the halves, focus on the sag).
- **scenes/** (planned): gaming and dev use cases.

The exploded shot has its own matte palette per layer so the stack reads as a
technical diagram; product shots keep real materials. Every camera passes a
`--framecheck` NDC pre-flight before sampling, and lighting is calibrated by pixel
statistics (mean luma 0.30–0.45, blown <1%, shadows p05 <0.10). Outputs are
2400 × 1500, hashed in `MANIFEST.json`.

---

## 17. History and decision ledger

This section is deliberately narrative: the *why* is part of the design.

### 17.1 Roadmap phases

The roadmap defines 13 phases:

0. Set up project and rules.
1. Define product and acoustic intent.
2. Design and validate layout.
3. First integrated geometry prototype.
4. Schematic and PCB.
5. Plate and enclosure as a coordinated assembly.
6. Firmware.
7. Automate manufacturing outputs.
8. Physical prototypes and acoustic tests.
9. LLM/MCP experiment workflow.
10. Realistic product renders.
11. Promotional video.
12. Final verification and manufacturing release.
13. Optional public launch.

The repository’s actual directory structure diverged from the roadmap’s sketch
(it uses `generated/`, `opencode/`, and a flatter spec layout), but the phase
logic and source-of-truth doctrine remain the charter.

### 17.2 The blockers that shaped the design

| Problem | Resolution | Evidence |
|---|---|---|
| nice!nano pin numbering was mapped to the stock `PinSocket_2x12` row-major convention | Custom `Socket_Strips_2x12_P2.54mm_NiceNano` footprint with 15.24 mm row separation and the correct 1–24 numbering | Schematic/pin audit; `check_mcu_footprint()` |
| Encoder knock-through was cut into the PCB, which would remove copper from its own pads | Moved the knock-through to plate/case; PCB keeps the EC11 body on top with all seven pads | `gen_pcb.py` guard; layout spec |
| One flat schematic produced one netlist and two halves would merge on PCB update | Two separate KiCad projects, one per half | README “Why two projects” |
| Switch common was wired wrong | Fixed and guarded; WS-SLTV pin 1 = common | `check_pwr_footprint()`; notes |
| Plate cutout 15.0 mm gave zero clip bearing area; PCB unsupported | Support strategy (b): 14.0 mm cutout, 1.2 mm plate, 1.00 mm gap, true Choc hang | v2 audit; `gen_plate.py`; `spec/case.md` |
| Diodes on B.Cu would break left/right mirror symmetry because the hotswap socket is asymmetric | Diodes stay on top; plate carries 0.55 mm relief pockets | notes; `spec/electronics.yaml` |
| Encoder window 12.7 mm fouled the terminal blocks at the new plate band | 16.2 × 12.4 mm window sized to the measured envelope | notes M3.3/E; `gen_plate.py` |
| TRRS jacks could not seat at the frozen 4.5kx split width | +16 mm widening; left key geometry unchanged | layout config; measured gap |
| Released gerbers were stale and the release gate reported false CLEAN on a dirty tree | Re-cut release; harden `make_release.py --check`; quarantine legacy `pcb/- FINAL/` | v2 audit B1; notes |
| Power-switch M2 relocation hid the blade behind the wall | M3 centered the origin on the window; case mouth cut for 106.3/185.2 | notes; layout config; case params |
| Ring cover was “extraordinarily thick” and caps barely protruded | Thin top plate v4.0: 2.0 mm at 3.20–5.20, cap field opening, 33% top preload | case README v4.0; spec/case |
| Case floor was 4 mm of air under the PCB | Floor −5.6 → −4.65, slab 2.0 → 1.7, assembled height 12.80 → 11.55 | case README v4.1 |
| USB port slot shipped sealed because fixed depth did not breach the dilated skin | Port generator marches each face outward until it exits the skin | case README v3.3; `gen_case.py` |
| Magnet stations resolved 6/7 asymmetrically | Symmetric-by-construction: left set computed, right mirrored and re-validated | case README v3.6 |
| Keymap was hand-maintained and legend/position bugs were possible | Generated from `spec/layout.yaml`, byte-compared, structurally validated | M3.3; `gen_keymap.py` |
| Dtc 1.8.1 rejects semicolons inside binding arrays | Generator emits newline-separated rows; validation rejects interior `;` | M3.4 round 1 |
| EC11 `steps` semantics were misunderstood | `steps = <60>` (15 pulse periods × 4 deltas), TPR 30 | M3.4; `spec_checks` |
| Copper-to-edge 0.292 mm was below a quoted 0.3 mm rule | Research showed 0.3 is the V-cut rule; tab-route requires 0.2. Then nudged to 0.406/0.575 anyway for fab-agnostic headroom | M3.5/M3.6 |

### 17.3 Rejected or deferred paths

- **Diodes to B.Cu** — implemented, then proven impossible under the mirror
  discipline; the fallback (top-side diodes + relief pockets) was used.
- **PCB supported by the case floor** (strategy c) — contradicts the acoustic
  floor and moves every port z; rejected.
- **Rim strips / plate screws** — rejected in favor of discrete tabs and poron.
- **Ring cover** — replaced by the thin top plate after user review.
- **Full-height port slots** — rejected as “gaping”; replaced by shaped bores.
- **Square knob** — the old 13 × 13 square knob sweeps ~Ø18.4 at the corners and
  was replaced by a round Ø16.8 knob with constant sweep.
- **ALPS EC12 encoder** — lower, but no push switch; not a drop-in.
- **302030 cell** — does not fit under the module.
- **2.11 mm Mill-Max 315 socket** — banned by height; cannot clear the 3 mm cell.
- **Bluetooth SIG qualification for the hobby pilot** — dropped; only relevant if
  sold/branded.
- **R3-03 / A-01 / A-03** — deferred to the next natural re-cut, then landed with
  the M3.6 copper nudge.
- **Flex cuts** — deferred to rev 2; the gasket build works without them.
- **Ground pour** — deferred to rev 2; rev 1 uses 0.25 mm GND chains.

### 17.4 Audit rounds

- **2026-10-19/20 six-review audit** — found the plate-retention blocker B2, the
  stale release B1, the socket-side documentation error H1, and the unachievable
  switch test H2. It forced the support-strategy rethink and the case v3.6
  symmetry/strength round.
- **2026-10-21 second review** — focused on gates that re-derived instead of
  reading, release-chain integrity, and thresholds that could not police
  themselves.
- **2026-10-22 rev-2 audit** — found the encoder-window blocker; fixed before any
  plate was ordered.
- **2026-10-23 three-round production-readiness audit** — firmware/keymap (F01–
  F07), mechanical (14 findings), electronics/process (3 P2). All resolved,
  refuted on primary sources, or explicitly deferred; CI green.
- **2026-10-24 review triage + strength round** — PETG support, z-stack gate,
  order policy split, magnet polarity stack test, service story, diode-relief
  test correction, print-manifest gate, variant CI.

The audit history is not noise. It is the record of which claims survived contact
with a fresh reviewer and which did not.

---

## 18. Current state, risks, and next actions

### 18.1 What exists

- **PCB `v0.5.0`**: released, hashed, fab-pointable. Boards at `8eef566`; release
  bundle verified. DRC 0 non-waived (28 W1/half), ERC 0 errors (5 spare
  warnings/half).
- **Plate rev-8**: DXF/SVG/lands generated and gated; 14.0 mm cutouts, 0.55 mm
  relief, 16.2 × 12.4 mm encoder window, 8 tabs.
- **Case**: tub v4.1 (57.5 cm³), thin top cover v4.x (15.2 cm³), floor −4.65,
  slab 1.7, tub bottom −6.35, assembled 11.55 mm. STEP solids committed;
  print manifest recorded.
- **Firmware**: ZMK shield and four keymap variants; CI builds active + all
  variants; keymap gate proven with negative controls.
- **Renders**: `v0.5.0` final PNGs and manifest; Blender pipeline reproducible.
- **Documentation**: specs, BOM, manufacturing guide, first-article checklist,
  compliance memo, roadmap, notes, audit reports.

### 18.2 What does not exist

- No physical PCB, plate, case, or switch has been built.
- No coupon has been cut; no vendor has confirmed the 0.55 mm partial depth.
- No magnet pull, poron compression, plate flatness, TRRS boot fit, cell
  polarity, or BLE range has been measured.
- No CI run on a pushed tip after the last local audit cycle? The notes record CI
  green at `ca48bd4`; the release re-cut is local. Confirm the current pushed
  state before treating CI as final evidence.
- No acoustic recordings or listening tests.

### 18.3 Open gates before a batch order

1. **Choc cutout/relief coupon** — 13.8/14.0/14.2/15.0 holes + 0.55 mm pocket;
   thickness ≤1.25 mm; if 14.0 does not catch, re-cut at 13.9.
2. **Fabricator partial-depth capability** — ask the plate shop first; plan A
   controlled-depth laser engraving, plan B PCBWay Z-milling at 0.70 mm nominal,
   fallback through-cut relief holes.
3. **Pre-MJF caliper** — measure the actual slide-switch legs, JST legs, and
   hotswap socket bump before the MJF order; if anything exceeds −3.65, move the
   floor constants first.
4. **First-article measurements** — plate flatness, pocket depth, magnet pull,
   poron compression, cell polarity, TRRS boot, USB cable fit, switch retention,
   BLE range.
5. **Order policy** — coupon + one PCB pair + one printed tub/cover set is the
   cheap engineering-sample sequence (~USD 60–100), then the 10-half pilot.
6. **Compliance** — personal builds only; if that changes, register ACMA-only
   supplier, prepare C02, sticker RCM, and revisit Bluetooth SIG.

### 18.4 Document drift to fix

- `README.md` says “case/cover v4.1” while the print manifest records a v4.3
  cover batch; `case/README.md` newest entry is v4.2. Use the generator values,
  not the label.
- `spec/case.md` retention section still describes the old ring cover
  (z 4.70–7.70); the current thin top is 3.20–5.20.
- `spec/first-article.md` and `spec/bom.md` list Ø4 × 1.5 cover magnets and a
  1.7 mm pocket; the current thin cover uses Ø4 × 0.5 and 0.7 mm.
- Net count is reported as 47 in `spec/electronics.yaml` and 48 in the audit /
  README.
- The README calls the plate “rev-8”; the generator docstring is “rev-1” with
  rev-2 decisions. The revision labels are informal; the constants and gates are
  the truth.
- `layout/- FINAL/keyboard_layout_v8.yaml` was modified in the working tree at
  inspection; do not assume it is the committed baseline without checking.

The synopsis deliberately names these instead of silently picking one. A future
cleanup should make each fact single-sourced.

### 18.5 Honest risk statement

The design is **software-clean**, not **hardware-proven**. The gates are strong
and the audit history is unusually thorough, but the remaining failures are
exactly the ones CAD cannot settle:

- Does a real PG1350 clip catch a real 1.2 mm PC plate at 14.0 mm?
- Does the plate vendor hold 0.55 mm depth without cutting through?
- Does the 1.00 mm gap survive laser kerf and plate thickness tolerance?
- Does the 301230 cell fit under the socketed module with the chosen pin stack?
- Does the TRRS boot clear the Ø6.0 side hole, and does the USB overmold clear
  the 14.0 mm slot?
- Do the magnets hold ≥1.5 kg and stay polarity-consistent?
- Does the case stay dimensionally stable in PETG or MJF?
- Does BLE range survive the cell under the antenna and the closed case?

The first article exists to answer those questions before the batch order.

---

## 19. Glossary, units, commands, and file index

### 19.1 Terms

- **Columnar**: columns of keys are vertically aligned and staggered, not row-
  staggered like a conventional keyboard.
- **Splay**: rotation of columns outward from vertical. This design uses 0°.
- **Stagger**: vertical offset of a column relative to the home row.
- **Thumb arc**: the four thumb keys lie on a circle about the thumb joint, not a
  grid.
- **Home-row mod**: a hold-tap key on the home row that is a letter when tapped
  and a modifier when held.
- **Hold-tap**: ZMK behavior with tap/hold resolution controlled by timing and
  position.
- **Gasket mount**: the plate/PCB assembly floats on compressible pads rather than
  being screwed to the case.
- **Tab-and-jacket**: the plate’s eight tongues sit in case pockets (“jackets”)
  with poron above and below.
- **Relief pocket**: a partial-depth cut in the plate underside that clears a
  top-side component (here, the SOD-123 diodes).
- **Sideband**: a separate input path outside the main matrix; here, the encoder
  push.
- **Central / peripheral**: the two roles in a ZMK split. The central talks to the
  host; the peripheral sends key events over the split link.
- **W1 / W2**: documented DRC waivers. W1 is the rotated-footprint library
  mismatch; W2 is an armed predicate with zero hits.
- **Design frame vs storage frame**: the design frame is y-up and matches the
  plate/case; the KiCad board is stored y-negated.
- **Thin top**: the v4 cover, a 2.0 mm plate at z 3.20–5.20, replacing the old
  ring cover.
- **Key-field ledge**: the relieved area around the key field that lets caps stand
  proud of the cover surface. The current flat cover removed the 0.8 mm ledge;
  the phrase survives in historical notes.
- **PC / POM / FR4 / ALU / CARBON**: plate materials with different stiffness,
  fabrication, and web minima.
- **PCM**: protection circuit module on the LiPo pouch.
- **PPTC**: resettable polyfuse.
- **UICR**: nRF52840 user information configuration registers; the NFC-pin option
  is sticky and needs a full erase.

### 19.2 Units and conventions

- All mechanical dimensions are **millimetres**; angles are degrees.
- **z = 0 is the PCB top surface** in the case/plate/renders frame.
- **KiCad board frame** is the common XY frame for plate DXF, `lands.json`, and
  case geometry.
- The board is stored y-negated in KiCad; `frame.py` converts.
- The left/right mirror axis is **x = 145.75**; right = `291.5 − left`.
- Key pitch is **19.00 mm** measured, not 19.05 nominal.
- The split gap is **20.42 mm** edge-to-edge, **22.40 mm** mouth-to-mouth at the
  TRRS.
- The case is **11.55 mm** tall assembled, **13.93 mm** desk-to-cap with flat
  Saddle caps.

### 19.3 Canonical commands

```sh
# Static gates (no KiCad)
npm test

# Release integrity
python3 pcb/make_release.py --check

# Layout regeneration
npx ergogen layout/ergogen -o layout/generated/v2 --svg --clean
node layout/generators/dump_points.cjs
python3 layout/generators/export_kle.py --check
node layout/generators/render_preview.mjs

# Schematic + PCB
python3 pcb/generators/gen_schematic.py
python3 pcb/generators/gen_pcb.py

# Plate
python3 plate/gen_plate.py
python3 plate/gen_plate.py --check

# Case
case/.venv/bin/python case/gen_case.py
case/.venv/bin/python case/gen_cover.py
case/.venv/bin/python case/mirror_gate.py
case/.venv/bin/python case/probe_bores.py

# Keymap
python3 config/gen_keymap.py
python3 config/gen_keymap.py --check
python3 config/gen_keymap.py --use win_right

# Renders
bash renders/fetch_keycaps.sh
CASE_OUT="$PWD/case/out-dev" ./case/.venv/bin/python case/gen_case.py
CASE_OUT="$PWD/case/out-dev" ./case/.venv/bin/python case/gen_cover.py
CASE_OUT="$PWD/case/out-dev" ./case/.venv/bin/python renders/build_assets.py
blender --background --python renders/scene.py -- --samples 96 --res 2400x1500 --setups bright --shots hero,exploded
```

### 19.4 File index (selected)

| File | What it answers |
|---|---|
| `spec/layout.yaml` | Keymap, legends, thumb roles, layout decisions, split geometry. |
| `spec/electronics.yaml` | Matrix, pin map, parts, power, split link, PCB rules. |
| `spec/case.md` | Plate/gasket/case interface, stack, ports, materials. |
| `spec/keymap.md` | Narrative for every keymap layer and behavior. |
| `spec/first-article.md` | The physical build/test gate, coupon, assembly order, bench. |
| `spec/bom.md` | Part numbers and assembly notes. |
| `spec/compliance.md` | AU/NZ, US, EU, Bluetooth SIG, transport. |
| `spec/research-open-items-2026-10-21.md` | Primary-source research behind compliance, LiPo protection, module retention, pilot quantities, Choc plate cutout. |
| `layout/ergogen/config.yaml` | Parametric layout and outlines. |
| `pcb/generators/gen_schematic.py` | Spec → schematic + ERC + net audit. |
| `pcb/generators/gen_pcb.py` | Placement, routing, containment, DRC gate. |
| `pcb/generators/gen_route.py` | Deterministic dual-layer A* router. |
| `pcb/generators/check_board.py` | Board/plate/mirror/frame self-tests. |
| `plate/gen_plate.py` | Plate geometry and z-stack gates. |
| `case/params.py` | Every case constant with source. |
| `case/gen_case.py` | Tub generator and solid checks. |
| `case/gen_cover.py` | Thin top cover generator and checks. |
| `config/gen_keymap.py` | Keymap generator and structural gate. |
| `tests/spec_checks.cjs` | Cross-cutting static gates. |
| `generated/release/v0.5.0/MANIFEST.txt` | Exact PCB release provenance. |
| `generated/print/v0.5.0/MANIFEST.txt` | Exact plate/case order provenance. |
| `zmk/gpio-map.md` | Machine-generated pin/net continuity map. |

---

## 20. Closing

Hojicha44 is a project that treats a keyboard as an engineered system: layout,
electronics, firmware, plate, case, manufacturing, documentation, and physical
evidence are one chain. Its most distinctive property is not any single number —
not the 44 keys, the 19 mm pitch, the 14.0 mm cutout, or the 1.2 mm plate. It is
the insistence that every number has a source, every generated artefact has a
gate, every release has a hash, and every physical claim waits for a measurement.

The design is at the point where the software can go no further. The remaining
work is the first article: cut the coupon, measure the switch, confirm the pocket,
meter the cell, fit the plugs, pull the magnets, and listen. If those pass, the
batch order is justified. If they fail, the repository has already recorded where
to look.
