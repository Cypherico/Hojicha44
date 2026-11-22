# Hojicha44 — first-article checklist (hands + parts required)

Use the v0.5.2 PCB, plate and case files together. Confirm connector
seating, cable fit and switch lead clearance on the first pair. The
[product audit](../audit.md) records the CAD checks and their limits.

Do these in order, both halves where marked ×2. Nothing here can be proven
in software — this is the release gate for the physical items. Prints:
`out/fit/Hojicha44-{Left,Right}-fit.pdf` (Edge.Cuts + silk + fab + F.Cu
pads, 1:1 — print at 100% / actual size, then calibrate: column-adjacent
key centres must measure **19.00mm**; if not, the print scaled and nothing
below counts). The fit sheet shows the PCB only; the 16.2 x 12.4mm encoder
window lives in the laser plate (`plate/Hojicha44-{Left,Right}-plate.dxf`),
which is the cutout source — not the PCB print. (`layout/generated/v2/outlines/plate.dxf`
is legacy ergogen output, superseded by `plate/`.)

Print notes (for the case tub/cover): **PETG at 100% infill is a
supported self-print material** (user decision 2026-10-24; strength
audit in `spec/case.md` — every thin feature >= 1.2mm and PETG is
STIFFER than the MJF PA12 reference, E ~2.1 vs ~1.65 GPa; the risks
are warp/dimensional, not strength: 4+ perimeters, brim on the 167mm
tub, calibrate XY against the 166.9mm outer width). ASA is the
better-warp alternative; MJF PA12 remains the production-order
reference. Print both parts AS ORIENTED — tub open-face-up,
cover underside-up (magnet pockets open) — every feature is then
self-supporting except the USB/TRRS mouth arc bridges (~7mm spans),
which typically bridge support-free on any decent bridge profile;
add supports only for a poor bridger.

## 0. Pilot batch

- [ ] **Build 5 half-pairs (10 halves)** for the pilot after the
  engineering sample passes. Allow spares for assembly and replacement:
  20 PCBs (10 halves + 10 spares), 20 plates, 12–15
  cases (3–4 printed spares per design). Ten assembled halves use
  220 switches, 220 hotswap sockets and 220 diodes before spares.
  The earlier 450–500 quantities would also populate most or all spare
  boards. Allow 12–14 cells, 80 tub magnets
  and 80 cover magnets plus spares, 12 modules, 20 polyfuses.
- [ ] **Measure the finished underside before ordering the case.** The
  floor is 4.65mm below the nominal PCB top. The Würth switch has
  4.70–5.10mm stock leads below its seating surface. For this floor,
  trim the three leads after soldering and inspect the joints. Measure
  from the PCB top to the lowest lead or solder point. The 3.25mm
  maximum leaves 1.40mm nominal clearance and 1.00mm with 0.40mm downward
  motion. Keep the area directly below the switch free of foam. Check the
  encoder, JST, sockets and actual gasket travel before adding foam.
- [ ] Indicative unit cost **~USD 35–70 per half** (PCB ~USD 2/5 pcs
  + ENIG adder, PCBA ~USD 8 setup + per-joint, PA12 ~USD 2–4 per
  half, PG1350 ~USD 1.1 ea, LiPo USD 1.5–6, N52 USD 0.01–0.08).

**Order policy (rev 3, review 2026-10-24):** *engineering-sample*
orders — the plate coupon below, the encoder coupon, one corrected PCB
pair, and one printed tub/cover set — are required before §0. The current
PCB and case files are [v0.5.2 first-article candidates](../pcb/MANUFACTURING.md). Sections
1–7 gate the **production batch** (the §0 quantities). The
cheap sequence is: coupon + 1 PCB pair + 1 tub (~USD 60–100), then the
10-half pilot. "Before ordering anything" in older revisions meant the
batch; it never forbade coupons.

## 1. Paper fit test (before ordering the batch)

- [ ] **Regenerate the fit PDFs first** — `out/fit` renders predate the
  16 Oct boards (and the case v3.3-v3.5 port changes); rebuild prints
  from the current tracked artifacts before any caliper check here.
- [ ] **Choc cutout test coupon (PRE-ORDER, new in rev 2) — the support
  strategy hinges on this.**
  *What it is:* a **test piece** — one small offcut of the REAL plate
  material and thickness (1.2mm PC), cut by the same vendor with the
  same process, carrying every candidate feature. Not a full plate.
  *What to ask for:* a **100 x 100mm sheet of 1.2mm PC** with four
  **20 x 20mm squares**, one hole each of **13.8 / 14.0 / 14.2 /
  15.0mm**, all holes concentric in their square, PLUS one extra
  20x20mm square with a 14.0mm hole **and a 0.55mm-deep pocket in its
  underside** (the diode relief, **3.15 x 2.00mm** — the error bars of
  the SOD-123 outline max (2.85 x 1.70) + 0.15/side; the fabricator
  takes it from the RELIEF layer of the plate file). Cost: a few
  dollars; turnaround: a day.
  *What to do with it:* caliper the coupon's thickness first — it must
  be **≤1.25mm** (the capture margin for the plate's underside is the
  0.9–1.3mm lip band, and thickness spends it: 1.3 = lip tip).
  Then for each square (a) drop a PG1350 in — does
  the body pass the hole? (b) press the switch down onto the coupon
  and LIFT it — does the clip arm catch the plate's underside?
  Expected: at 14.0 the lip (0.9–1.3mm above the PCB) grabs the
  1.00mm underside and the 14.8mm ears seat on the 2.20mm top face;
  13.8 may be line-to-line (a switch that will not insert); 15.0
  reproduces the old rev-1 failure (the ears fall into the hole, no
  retention, the switch rocks out). Check the relieved square on the
  assembled switch-and-diode stack.
- [ ] **Plate relief pocket (PRE-ORDER).** Machine the RELIEF layer from
  the underside to 0.55mm nominal. The coupon must retain **at least
  0.60mm** of plate above each pocket and leave **at least 0.15mm**
  above a **1.40mm** diode with the plate seated. Measure stock thickness,
  pocket depth and the seated PCB-to-plate gap. At 1.20mm stock and
  1.00mm gap these criteria allow 0.55–0.60mm of relief. Confirm the
  switch ears seat flat and the clips capture the underside.
- [ ] **Encoder window (PRE-ORDER, new in rev 2)** — the plate's encoder
  window is now **16.2 x 12.4** (rev 1 had a 12.7 square, which fouled
  the encoder's terminal blocks once the plate moved down to the 1.00mm
  gap). On the coupon (or a scrap of the same 1.2mm PC): the encoder
  must pass the window freely, and the two terminal blocks must clear
  it with room to spare. **Caliper the real encoder**: the width
  across the A/B/C and S1/S2 terminal blocks at 1.0mm and 1.5mm above
  the PCB. If the blocks do NOT protrude above ~1.5mm (the vendored
  STEP may overstate them), the window can go back to 12.7 square and
  the plate batch saves material — but only with that measurement in
  hand, not with the STEP alone.
- [ ] Module footprint: place a real nice!nano on the print, pin-1/USB end
  to the notch edge. All 24 pads must sit on printed copper.
- [ ] Socket rows on print measure **15.24mm** apart, 2.54mm pitch.
- [ ] USB notch measures **11mm wide**; dry-fit the actual USB cable — with
  4.5mm sockets the plug sits above the PCB so 11mm is normally enough. If
  the housing hits the shoulders beside the notch, widen it to ~14mm. Plug
  axis rides high on 4.5mm sockets with a ~9mm-inboard shell, so verify the
  housing clears the plate top in the solid-board overlap zone (seating depth), not just the notch width.
- [ ] **Case port bores.** Seat the actual USB-C plug through a 14.0mm
  slot in a printed tub and cover slice. If the revised design retains
  TRRS, use its corrected board placement and case for the mating test.
  Measure shaft reach, boot clearance at both ends and cable bend at the
  planned half spacing.
- [ ] **Power-switch aperture.** With the real switch installed, check that the
  cover seats against the tub without contacting the switch body and
  that the actuator is reachable across its full travel on both halves.
- [ ] **Magnets.** Use 16 axially magnetized N52 Ø4×2mm magnets in the tub
  pockets (Ø4.3×2.2mm) and 16 Ø4×0.5mm in the cover pockets
  (Ø4.3×0.7mm). Seat tub magnets face up and cover magnets face down,
  both flush, allowing 0.2mm nominal adhesive depth. Check polarity:
  face-up/face-down fixes the GEOMETRY, not the pole — a flipped disc
  still seats. Pick the orientation on ONE tub/cover pair (must
  attract), then dry-stack ALL 16 in their pockets and confirm every
  station attracts before any glue is applied; glue one station,
  re-test the stack, then continue. All-stations-same orientation
  keeps the covers polarity-interchangeable between halves. Station coordinates print in
  the gen_case/gen_cover census lines each run (PCB frame; LEFT tub at
  writing time: (130.17,57.76), (136.55,12.92), (133.44,-55.70),
  (67.30,-43.06), (19.46,-28.91), (-18.35,8.02), (6.74,52.44),
  (68.42,64.16) — the LEFT set is the SOURCE and Right is its exact
  mirror x->291.5-x). Cross-check one per half in
  the slicer against the STEP. Tests: dry-fit the cover with NO
  magnets and plate. The empty cover should sit level at the 3.20mm lip.
  Install the padded plate and PCB, reseat the cover and look for contact
  marks on the top and bottom pad at every tab. Measure rest height and
  movement under a keypress. With the magnets fitted, check for rocking,
  sideways slip and corner peel. The foam should release from both case
  surfaces when opened. **Pull test (M4 gate): with the plate
  installed, a straight lift must hold ≥1.5 kg before the cover lifts**
  with the specified 0.5mm cover magnets and the actual adhesive.
- [ ] **Cover dry-fit.** Close the cover flush with the tub without
  rocking. Check that all top pads make contact and the keycaps travel
  freely. With the cover closed, confirm both plugs seat and both power
  switches can be operated.
- [ ] Encoder shaft hole over the anchor — **FIRST pre-order bench check,
  order (1) hole sample, (2) Choc clip fit + kerf on the 0.71mm pad
  margin (needs a laser-cut sample), (3) the plug slices below**. The
  plate window is **16.2 x 12.4mm** (rev 2), sized to the encoder's
  measured **14.95 x 11.70mm** terminal-block envelope at the 1.00mm
  plate gap — ~0.34mm/side in y (gen_plate.py asserts >=0.2/side).
  Drop the real (or spec-identical) encoder through a laser-cut window
  sample before ordering the plate batch: ±0.2 fab tolerance can still
  rub. Fit a knob to the qualified encoder shaft. Check shaft
  engagement, clearance above the cover at full push, and clearance
  from the nearest keycap through a full turn. The low render knob
  assumes a shorter shaft than the reference part. If the calipered terminal blocks
  do not protrude above ~1.5mm, the window may return to 12.7 square —
  but only with that measurement in hand (see the coupon bullet above).
- [ ] 301230 cell outline (12×30mm) fits between the socket rows on print.
- [ ] If TRRS is retained, compare the revised drilling at 1:1 with the
  actual jack and verify each contact with an inserted plug. At the nominal
  22.40mm face-to-face spacing, check both mating depths, boot fit in the
  10.5mm open bays, and cable routing.
- [ ] Plug and unplug the battery harness through the JST access window.
  Check the wire exit and bend with the cover installed. Test continuity
  and confirm pin 1 is pack positive on each half before connecting power.
  During a firm keypress, the connector and wires must clear the walls.
- [ ] Fab limits confirmed with the chosen fab BEFORE ordering: 2-layer
  1.6mm, 0.25mm track / 0.2mm clearance / 0.30mm-drill-in-0.65mm-pad
  signal vias (0.50-in-1.00 power) accepted — the old "0.8-0.4mm" line
  quoted the KiCad template, not the boards; rev-2
  flex slots (typically >=1mm) quoted separately.
- [ ] ORDER GATE — do not place the fab order until every box in §1 passes
  on paper AND the fab has accepted the limits above. §2–§5 need physical
  boards; nothing below can substitute for a failed box here.

## 2. Bare-board DMM (before soldering modules)

- [ ] ×2 JST pigtail red → JST pin 1 (`+` mark), black → pin 2. Meter on
  continuity beep AND record the readings — this board has NO
  reverse-polarity protection. Any doubt: STOP, do not plug the cell in.
  Reverse polarity kills board and cell.
- [ ] ×2Pack+ to RAW with switch ON (<1Ω); switch OFF open. Record which
  slider end is ON (either is fine, just label it).
- [ ] Solder the slide switch FIRST, before any other part, and re-verify:
  JST-1 → RAW <1Ω with switch ON, open with OFF. The switch is the only
  charge/safety disconnect — a dry joint here defeats it silently.
- [ ] On a real nice!nano (not yet soldered), meter on continuity beep:
  RAW↔B+ short (<1Ω), GND↔B− short (<1Ω), RAW↔VCC open (OL, no beep).
  Power must enter via RAW; B+/B− holes stay open.

## 3. Assembly order (both halves)

- [ ] Match each diode to its same-numbered switch. From the top, the
  diode centre is 9.50mm along the switch's local +X on Left and −X on
  Right. This offset rotates with the thumb switches. Match the diode
  band to the cathode tick and confirm the cathode connects to its row.
- [ ] Measure the installed socket stack before inserting the cell.
  Caliper from carrier PCB top to module PCB underside with all pins
  fully engaged. Accept a 4.5–5.0mm gap and check the usable space under
  the module after accounting for solder, components and insulation.
  Verify clearance for the actual cell and the USB plug, then record
  the installed gap and the measured maximum pack thickness.
- [ ] **Solder order (one list, no ambiguity — "sockets" means two
  different parts, so they are named):**
  1. slide switch (done in §2, FIRST — it is the charge disconnect)
  2. diodes (D_Lxx/D_Rxx, cathode tick to the row)
  3. **Choc hotswap sockets** (B.Cu, under each switch)
  4. **nice!nano machine-pin sockets** (the 2×12 headers — NOT the Choc
     sockets in step 3)
  5. Solder the corrected JST and EC11, plus the corrected jack if fitted.
     Trim the power-switch leads, inspect the joints and remove clippings.
  6. Dry-fit the nice!nano and qualified pack with power disconnected.
     Measure the socket gap and check the pouch, PCM and wire exit.
  7. With USB disconnected and the switch OFF, insulate the pouch and
     controller underside, secure the pack without compression and route
     its leads beside the socket. Seat the module fully.
  8. Attach the bottom and top PORON pads to each tab. Clip each Choc
     switch into the plate with its pins aligned to the matching socket.
  9. Mate the PCB to the switches while supporting the underside of
     each hotswap socket. Verify all switches seat fully.
  10. Lower the plate and PCB onto the eight gasket shelves.
  11. Fit the polarity-tested magnets with faces flush and adhesive cured.
  12. Seat the cover. Check all pad pairs contact, the cover stays flush
      and the PCB clears the floor throughout a firm keypress.
- [ ] If a corrected debug jack is fitted, switch both halves OFF and
  disconnect both USB cables before inserting or removing a TRRS plug.
  The battery switches leave USB power available.
- [ ] Antenna end: 5mm copper-free respected, no case material within 3mm.
  Case shell near the antenna end must be plastic/wood — no metal, no
  carbon fibre (both detune/kill 2.4GHz).
- [ ] Plate clearance (rev 2): the 22 top-side diodes stand **1.26mm**
  (measured; up to 1.40mm on a real part) in the inter-key gaps, and
  the plate now sits **1.00mm** above the PCB top with a **0.55mm
  RELIEF POCKET** over each diode (RELIEF layer in the DXF — machine
  it, do not cut through). The pocket floor is at 1.55mm, so there is
  **0.15–0.29mm** of clearance over the diode, not the solid plate.
  Depth-gauge the pockets and measure the actual stock thickness and
  seated gap. Accept at least 0.60mm remaining material and at least
  0.15mm clearance over the assembled diode as in §1. Inspect both
  pocket ends for contact or scrape marks.
- [ ] Plate fit (rev-2 plate in `plate/`): 1:1 print over the real PCB —
  every 14×14 cutout frames its switch footprint, the 16.2×12.4 window frames
  the encoder body, W1/W2 windows clear switch/module/JST/TRRS bodies,
  outline matches edge-for-edge including the USB notch. Seat one real
  Choc switch per region (corner/edge/thumb): clips engage, no rock.
  (Laser kerf enlarges cutouts ~0.1–0.2mm, so expect a slip fit, not
  interference — rock is the reject criterion. If loose in every region,
  the cutout tightens 14.0 → 13.9.)
- [ ] **Poron pads.** Use eight 7×4mm pads per side of the plate, per
  half: 3.0mm stock below and 1.5mm stock above. Keep the pads on the
  tabs and away from adjacent cutouts.
- [ ] **Gasket preload.** The 4.75mm shelf-to-cover distance allows
  3.55mm for the two pads beside the 1.20mm plate. For nominal 4.50mm
  free foam this gives 0.95mm total compression. Measure the PCB's
  actual rest height, clearance under load and contact at every tab.

### 3b. Service story (review 2026-10-24)

- [ ] **Module / cell swap is a FULL teardown — know it before you
  build.** There are no fasteners: the PCB hangs off the switches in
  the plate, the plate on the gaskets/magnets. Reaching the JST cell
  connector or swapping a nice!nano means lifting the cover, then
  unseating the plate (22 Choc clips through 14.0mm holes against the
  socket contacts) — do it on a soft mat, pull switches straight out
  of their sockets with a switch puller, never pry against the 1.2mm
  PC plate. Practise the sequence once during the first article and
  time it; if a cell swap takes more than ~10 minutes or cracks a
  plate, a hidden screw or a JST extension at the USB end goes into
  the next case revision.

## 4. Power-on

- [ ] On both halves, measure charge current into a qualified, partially
  discharged pack with USB connected and switch ON. Verify it falls to
  zero with the switch OFF. Record current, pack voltage, termination
  behavior and LED indication with the switch in each position.
- [ ] ×2 TRRS continuity jack-to-jack over a straight cable: left
  TIP→right TIP, left RING1→right RING1, sleeve→sleeve (<1Ω each);
  RING2 open both ends (must never join batteries).
- [ ] Inspect solder and mask registration at the USB notch shoulders.
  On v0.5.1 the nearest socket-pad copper is 1.844mm from the notch
  profile on both halves. The nearest trace is 0.582mm on Left and
  0.405mm on Right. Recheck on the revised boards.
- [ ] ×2 Encoder: spin both directions + push click register; knob
  clears the cover rim and the nearest cap through full rotation +
  full push (skirt ≥0.9mm off the cover at max travel).
- [ ] Stack height: 4.5–5.0mm rows swallow the 3mm cell + PCM with
  clearance; JST sits beside the cell, not under the stack.
- [ ] BLE range with battery and case: with cells fitted and halves in
  the gasket case, each half links and types at the intended desk distance
  (no dropouts); note the measured range. If range disappoints, try the
  301228 fallback before re-spinning.

- [ ] CPL: `pos.csv`/`pos-smt.csv` use KiCad convention (negated Y, board
  origin) — JLCPCB/PCBWay ingest KiCad CPL natively, do not flip axes.

## 5. Firmware bring-up (first flash)

- [ ] Flash each stock nice!nano with the matching left/right UF2 via
  its USB bootloader. Verify both halves pair and report their matrix
  keys. Document a verified programmer and bootloader recovery procedure
  before using a full chip erase.
- [ ] Verify D16 is usable as GPIO on each half and check both encoder
  pushes send Mute to the host over BLE.
- [ ] D10/P0.09 is spare and the keyboard assigns it no pull or behavior.
  If needed, check continuity at its unpowered header contact. Exercise
  the populated D16 inputs with both encoder pushes after the stock UF2 flash.

## 5b. Firmware bench — keymap (M3.3; spec/keymap.md is the reference)

Record which variant was flashed: ________ (files:
`config/variants/hojicha44_<v>.keymap`; active = `config/hojicha44.keymap`).

Matrix/base:
- [ ] Two per-half type-throughs on the base layer (finger-by-finger on
  each 6-column half while the sample text is visible): every QWERTY
  letter and `` `~ | \ - ' [ { ] } , . : ; /`` appears exactly as
  printed. A missing key = matrix/kscan, a WRONG key = keymap position
  bug (file which).
- [ ] Both thumbs: Space (or Enter on right-space variants) and
  Tab/Backspace fire from the correct thumbs; Esc/Delete reachable.
- [ ] Encoder per layer: base = volume ±, L1 = scroll ±, L2 =
  track prev/next, and rotating looks RIGHT compared to the printed
  detent direction on both halves (per-half).
- [ ] Encoder push on each half sends Mute to the host. Complete the
  firmware bench with the two halves paired.

Home-row mods (all 8 home positions A S D F / ; L K J):
- [ ] For a cross-hand copy shortcut, hold right K and tap left C.
  Expect Command+C on macOS variants and Control+C on Windows/Linux.
  Repeat with Shift held on one hand while tapping letters on the other.
- [ ] Fast roll (type "asa", "dfd", ";l", "jk j" quickly): letters only,
  no stray modifier bursts (require-prior-idle doing its job).
- [ ] Same-hand chord: hold a home-row mod past ~0.3 s, then tap a
  same-hand key — the mod applies (balanced + hold-trigger-on-release
  path).
- [ ] Double-tap-hold a letter (quick-tap-ms): it repeats the LETTER,
  not the modifier.
Layers and chord:
- [ ] Left mid-outer thumb hold = L1: digits 1–0 in QWERTY order; the
  shifted symbols row; F1–F12 sanity (F1/F10).
- [ ] Right mid-outer thumb hold = L2: arrows as an inverted-T
  (↑ above ↓), PgUp/PgDn/Home/End/Ins/PrtSc/Caps, media cluster, BT
  select 0 (pair ring must not leave the host — cancel with one press).
- [ ] L1+L2 chord → Adjust: `&bootloader` reachable at W — BEFORE pressing,
  stage a recovery: have the second .uf2 + flasher ready and confirm
  the half re-enters the bootloader (this is the deliberate-brick
  protection test, not an accident).
- [ ] While ADJUST is active, normal keys stay dead (&none) — type a
  few letters and confirm nothing appears.
- [ ] Tapping term / flavor belong to the generator (spec/keymap.md
  §3); if rolls or holds misfire on the bench, record which position,
  timing and intent — retune `config/gen_keymap.py` constants, never
  the generated files.

## 6. Case labels (apply before daily use)

- [ ] Each half, at the switch: `CHARGE ONLY WHEN ON`.
- [ ] Each half, at the TRRS jack: `TRRS: POWER OFF + USB OUT BOTH SIDES`.
- [ ] Inside the battery bay: `+ RED PIN1 — METER BEFORE PLUG-IN`.

## 7. Accepted prototype deviations + rev-2 backlog

These ship as-is in rev-1; recorded so nobody re-litigates them, and so
rev-2 has a list.

- The v0.5.1 left switched battery trace totals 174.02mm at 0.50mm wide
  and the pack-positive trace adds 112.70mm. Measure the voltage drop
  from pack to RAW under load and revisit this path in the PCB revision.
- Ground is a 0.25mm daisy-chain, no pour. OK for prototype; rev-2 gets a
  B.Cu pour for EMC/robustness.
- Recheck notch-to-copper clearance after routing the revised components.
- Diode height vs plate (§3) and antenna-enclosure rule (§3–§4 range test)
  validate on the first article; failures go to the case design, not a
  PCB re-spin, unless the range test indicts the layout.

Pass all → Gerbers. Fail anything → file an issue with the measured value.
