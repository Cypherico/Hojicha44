# Manufacturing order guide (v0.5.4)

> **v0.5.4 engineering sample.** Use the [matching PCB package](../generated/release/v0.5.4/)
> and [plate and case manifest](../generated/print/v0.5.4/MANIFEST.txt).
> The published v0.5.2 case fails the modeled USB-C envelope. Complete the
> physical first-article checks before ordering a batch.
> [First-article checklist](../spec/first-article.md) · [Audit](../audit.md)

[View the v0.5.4 PCB renders](../generated/renders/v0.5.4/README.md#pcb).
The underside views show the relocated matrix diodes. The routed relief
behind each TRRS face is part of Edge.Cuts. Check it in the CAM preview.

The exact answers for the JLCPCB Online PCB Quote, derived from the
committed design + vendor research (2026-10; sources at the bottom).
The live quote remains the only authority for anything price-shaped,
but every design-shaped field below has exactly one right answer.

## Frozen design facts (why several fields have one right answer)

| fact | where it's pinned |
|---|---|
| thickness **1.6mm** | `case/params.py` models the PCB bottom at -1.6 (case shelf/floor geometry) |
| outline **150.5 × 114.6mm** per half | Edge.Cuts extents — bigger than the 100×100 quote cell |
| smallest via **drill 0.30 / pad 0.65** | `gen_route.py` via rules (0.6/0.3 → 0.65/0.30); min drill scan = 0.30 both halves |
| smallest copper clearance **0.20 / 0.25** | signal / power pad classes |
| currents ≤ **0.5A** (charge jumper open; BLE-only) | `spec/electronics.yaml` charger block |
| finish **ENIG** | stamped into each `*.gbrjob` by `pcb/make_release.py` |
| no pours, no gold fingers, no castellations, no UL | v0.5.4 DRC records 47 documented footprint warnings per half and zero unconnected items |
| silk text **1.0mm / 0.15 stroke** | `gen_pcb.py` gr_text/fonts — at the vendor's guaranteed minimum, not below |

## The quote, field by field

| form field | value | why |
|---|---|---|
| Base Material | **FR-4** | Two-layer carrier for the nice!nano. Preserve the antenna copper clearance and validate the assembled RF performance. |
| Layers | **2** | as designed |
| Product Type | **Industrial/Consumer** | standard QC flow; Aerospace/Medical = fees for inspection we neither need nor asked for |
| PCB Qty | **5 per design** (10 total) | JLC minimum is 5 per design; qty 5 carries the fixed setup cost — hobby demand ≈ 5 |
| PCB Thickness | **1.6mm** | case constant (above); ±10% metal tolerance (1.44–1.76) is why the case keeps freeboard |
| PCB Color | **Black** (alt: purple) | aesthetic-only; current JLC policy = same fee for all standard colors **(verify in live quote)**; white-on-black hides solder flux best |
| Silkscreen | **White** | pairs with black mask; our art is already 1.0mm/0.15 = the guaranteed legibility floor |
| Material Type | **FR4-TG135** (first option) | TG class matters only for lead-free *reflow* (PCBA) or sub-5-mil pricing; 2-layer won't be there |
| Surface Finish | **ENIG** | flat pads (hotswap sockets sit flat), long shelf life, no HASL dome under sockets, and ENIG tolerates the sub-0.2mm exposed-clearance rules that HASL bridging restrictions would fight. Black-pad is a reflow/BGA failure mode — hand-solder doesn't hit it |
| Outer Copper Weight | **1 oz** | ≤0.5A and no pours: 2oz costs more, changes min-trace rules, buys nothing |
| Via Covering | **Tented** | sealed vias can't wick solder while hand-soldering near sockets; mask openings in the gerbers rule regardless of this toggle |
| Via Plating Method | **Not Specified** | the standard plating is implicit; the other two are filled-via/HDI-class options |
| Min via hole size/diameter | **0.3mm/(0.4/0.45mm)** tier | smallest finished hole = 0.30 with 0.65 pads — comfortably inside the free tier |
| Board Outline Tolerance | **±0.2mm (Regular)** | case clearances were designed ≥0.5mm; ±0.1 buys nothing (and thickness ±10% dominates any fit conversation) |
| Confirm Production file | **Yes** | Review both drill layers. Ask CAM to confirm plating and routing of the short slots in writing if the preview cannot show them. |
| Mark on PCB | **Remove Mark** | no fab barcodes on a finished keyboard half (~$1.50); the free 2D barcode is the cosmetic alternative |
| Electrical Test | **Flying Probe Fully Test** | trivial adder at qty 5; catches what the eye won't |
| Gold fingers / Castellated / Edge plating / Blind slots / UL / Humidity card | **No ×6** | none apply; edge plating would even trigger extra review |

## Ordering mechanics (two designs, one keyboard)

- **Left and Right are two separate designs.** Either one checkout with
  "Different Design: 2", or two orders — each design is billed its own
  5-pc minimum. Don't merge them into one panel/gerber: per-extra-design
  fees exist and a shared panel of this size gains nothing.
- The first-article artifacts are `generated/release/v0.5.4/{Left,Right}/`.
  For each PCB quote, zip that half's nine Gerbers, job file and both
  drill files. Keep the placement, bill of materials and ERC/DRC files
  with your build record. Cross-check the manifest stamp
  (`git commit:` / `board sha256:` lines in
  `generated/release/v0.5.4/MANIFEST.txt`) — the ERC/DRC reports in the
  release are re-run at cut time, and the manifest records the board's
  hash, so the release certifies those exact bytes.
- **Use an approved bundle from `generated/release/vX.Y.Z/`.** The pre-M3
  `pcb/- FINAL/` tree is removed; it had stale power-switch pads and
  pinned an uncommitted board (`3016153-dirty`). Historical audit
  reports may still mention it.
- Record the PCB and print manifests, selected parts list, firmware source
  revision and both UF2 hashes together in the first-article build record.
- Check the separate PTH and NPTH drill files in the manufacturer's CAM
  preview. The 24 controller slots per half are **0.90 × 1.30mm plated
  G85** and the four PJ-320A contact slots are **0.90 × 1.80mm plated
  G85**. Confirm both types are milled end to end. Check the Choc holes
  and PJ-320A locating holes are non-plated.
- **Concave outline — TAB-ROUTE ONLY, NO V-CUT / V-SCORE.** Review current copper-to-edge spacing with the fabricator. CNC
  routing tolerance ±0.1mm precision / ±0.2mm regular (capabilities
  page) — prefer the precision tier at quote if offered. Put this in
  the fab order verbatim:
  `CONCAVE OUTLINE — TAB-ROUTE ONLY, NO V-CUT / V-SCORE`
- The ENIG pick in the **gbrjob is informational only** — the form's
  Surface Finish choice is what the fab actually executes. Pick ENIG
  there or the stamp ships nothing.
- Budget reality: >100×100mm boards scale their fabric+finish cost with
  area; a 5-pc ENIG order of this size has been seen around
  **$35–70 before shipping** (unconfirmed — the live quote decides; both
  halves carry the surcharge).

## Assembly

- **Intent is hand-solder**: bottom-side diodes (D_L*/D_R*), the **44 Choc v1
  hotswap sockets** (soldered on B.Cu under each switch — they are
  footprint-only parts, so they carry no MPN and never appear in the
  released `bom.csv`; order them from `pcb/BOM_ORDER.md`), the 2
  **EC11E15244G1 encoders**, the Nice!Nano socket headers, TRRS THT,
  and the pwrsw/JST. The SWITCHES themselves are never soldered (they
  plug into the hotswap sockets). ENIG is the friendly finish for
  exactly this.
- For diode-only PCBA, use the bottom-side `pos-smt.csv` with a matching 22-diode
  parts list per half. Confirm diode orientation in the assembly preview
  and have the assembler omit the hand-soldered socket apertures from
  its paste stencil. The full `bom.csv` is schematic reference data.
  For a complete assembly quote, reconcile it with [BOM_ORDER.md](BOM_ORDER.md)
  and explicitly include 22 underside Choc sockets per half.

## Non-PCB orders (case, plate, magnets)

- The case material for quotes is MJF PA12 nylon. Each half uses a
  magnetically retained cover seated on the tub lip. The v0.5.4 STEP
  solids measure 57.2 cm³ per tub and 23.4 cm³ per cover.
- **Plate at 1.2mm: PC (default, per spec/case.md — the generator's
  MATERIAL constant) or POM (the firmer upgrade) or CNC aluminum.**
  **1.2mm is not a free choice: the Choc v1 clip only engages a 1.2mm
  plate** (at 1.5/1.6mm the switch has no retention). Through-cut the
  OUTLINE and CUTOUT layers. Use PORON as the pad template. Verify
  Choc clip retention on a supplier coupon. The **encoder
  window is 16.2 x 12.4** (rev 1's 12.7 square fouled the encoder's
  terminal blocks at the rev-2 plate height — measured off the
  vendored EC11E STEP).  The
  plate's W1 windows keep the MCU/battery/USB region clear, so even
  metal doesn't blanket the module; PC wins all-round for rev 1 (quiet,
  light and radio-transparent). Files:
  `plate/gen_plate.py`
  (DXF/SVG kept in `plate/`).
- Acrylic is the anti-recommendation: brittle at the gasket tabs.
- **Magnets ordered separately** (axially magnetized N52, Ø4×2mm tub and
  Ø4×0.5mm cover) — see
  `spec/first-article.md` for the seat-force verify gates and the
  tub/cover polarity pairing note.
- **H-7 mirror gate (v0.4.0+):** the plate/case halves must be exact
  mirrors before ordering. Run `python3
  pcb/generators/check_board.py --self-test` (board 0.0000mm, plate
  0.0100mm) and `case/.venv/bin/python case/mirror_gate.py` (tub
  0.0094mm, cover 0.0010mm); the limit is 0.05mm and both gates include
  negative controls. The right plate's gasket tabs are now derived from
  the left roots (`plate/gen_plate.py`), not re-walked independently.

- **Public supply:** confirm the finished keyboard's requirements and
  collect evidence for the actual nice!nano v2 revision before release.
  See [the compliance record](../spec/compliance.md).
- **Pilot batch: 5 half-pairs (10 halves)** — see `spec/first-article.md`
  §0 for the order quantities and the indicative ~USD 35–70/half unit
  cost.

## Before you click buy

1. Live-quote the size surcharge (both halves, separately) and any
   current color fee — the numbers above are research, the quote is
   truth.
2. Confirm the coupon's T&Cs: ENIG/big-area orders are a common
   exclusion from promos.
3. The silk text ships at exactly the vendor's guaranteed minimum
   (1.0mm/0.15) — passing today, but don't shrink anything.
4. DIY assembly needs: 1N4148W + pin headers + modules + magnets;
   distributor SKUs are the open BOM homework (see the release BOM or
   spec/bom.md).

## Sources (research basis, 2026-10)

- https://jlcpcb.com/help/article/different-design-in-your-pcb-files
- https://jlcpcb.com/help/article/in-what-cases-will-there-be-charged-extra
- https://jlcpcb.com/blog/pcb-pricing-breakdown
- https://jlcpcb.com/help/article/pcb-via-covering
- https://jlcpcb.com/capabilities/pcb-capabilities
- https://blog.poly.nomial.co.uk/2025-07-05-tips-for-getting-pcbs-made-with-jlcpcb.html
- https://jlcpcb.com/help/article/how-to-confirm-the-production-file
