# Hojicha44 — bill of materials (per half ×2, plus assembly notes)

Source of truth for part numbers: `spec/electronics.yaml`. Schematic symbols
carry `MPN` (all parts) and `Datasheet` (controller) properties from
`pcb/generators/gen_schematic.py`; verify with:

```sh
K=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
$K sch export bom --fields "Reference,Value,Footprint,MPN,Datasheet,QUANTITY" \
  -o /tmp/bom.csv pcb/kicad/Hojicha44-Left.kicad_sch
```

`Datasheet` holds a URL only where one is certain (controller docs); every
other part is identified by exact `MPN` text — no guessed vendor links.

## SMT (fab assembly)

| Qty | Part | Notes |
|---|---|---|
| 22 | 1N4148W, SOD-123 (example MPN: Diodes Incorporated 1N4148W-7-F, SOD-123 — listed at DigiKey `1N4148W-7-F` and Mouser `1N4148W-7-F`, manufacturer page `diodes.com/part/view/1N4148W`; or equivalent) | matrix diodes, front side |

## Hand assembly (through-hole / modules / mechanical)

| Qty | Part | Notes |
|---|---|---|
| 22 | Kailh PG1350 (Choc v1) switches | top side, seat into sockets — PG1350 names the family/series; builder chooses the exact feel/variant as a kit part (e.g. linear/tactile/clicky) — any PG1350 Choc v1 fits |
| 22 | MBK Choc v1 keycaps (PBT) | one per switch; 44–50 for the split incl. spares — order rows in `pcb/BOM_ORDER.md` §D |
| 22 | Kailh Choc v1 hotswap sockets | SMD bottom (pads part of footprint) |
| 1 | nice!nano v2 module | socketed, USB end to board notch |
| 2 | machine-pin 12-position SIP strips, 2.54mm pitch | rows 15.24mm apart. Measure **4.5–5.0mm** from carrier PCB top to the underside of the fully mated module. Qualify this spacing, contact engagement and the largest insulated pack. The Mill-Max 315-43-112-41-003000 socket housing is 1.80mm high. |
| 1 | **Alps EC11E15244G1** rotary encoder with push | Reference part for PCB, firmware and clearance checks. Qualify any alternate on the first article. |
| 1 | Knob matched to the qualified encoder shaft | Verify the bore, skirt clearance at full press, and sweep past the nearest cap. The low render knob was sized for a shorter shaft. |
| 1 if retained | XKB PJ-320A TRRS 3.5mm | Debug option. Leave unpopulated for a wireless-only build. |
| 1 per split if retained | Short, straight-through 4-pole TRRS cable, right-angle at both ends | Qualify the exposed shaft, required insertion depth, both boots and cable bend against the revised assembly. |
| 1 | Kapton (polyimide) tape, ≥10mm wide | cell sandwich: pouch face + nano underside before the cell goes in |
| 1 | JST S2B-PH-K-S + PHR-2 housing + 2× SPH-002T-P0.5S crimps | battery connector set, side-entry |
| 1 | Würth WS-SLTV 450301014042 | SPDT, pin 1 is common, 300mA switching rating. Trim the three soldered leads to a finished projection of at most 3.25mm below the PCB top. |
| 1 | 301230 LiPo cell (see below) | with protection PCM + JST-PH 2.0mm pigtail |

## Case (rev-1 plate + gaskets, per half ×2)

| Qty | Part | Notes |
|---|---|---|
| 1 | Switch plate, **1.2mm** | Through-cut OUTLINE and CUTOUT from the plate DXF. Machine RELIEF as 22 nominal **0.55mm** underside pockets. Use PORON as a punch template. Accept the coupon with **≥0.60mm** plate remaining and **≥0.15mm** seated clearance above a **1.40mm** diode. |
| 8 of each thickness | PORON 4701-30, 240kg/m³ candidate, 7×4mm pads | Target **3.0mm** bottom and **1.5mm** top. Confirm exact grade, density, thickness, tolerances and backing with the supplier. Qualify compression on the assembled coupon. |
| 8 | N52 disc magnet Ø4×2mm, axially magnetized | TUB pockets, Ø4.3×2.2mm, face up flush at the lip plane. |
| 8 | N52 disc magnet Ø4×0.5mm, axially magnetized | COVER pockets, Ø4.3×0.7mm, face down flush at the lip plane. Verify pull force on the assembled first article. |

## Cell selection and qualification

- The kriscables, KEEBD and Typeractive 301230 listings are candidates.
  The nice!nano's nominal 100mA is 0.91C for a 110mAh pack. Obtain the
  exact pack manufacturer, part number and revision, PCM details,
  allowed charging limits and maximum insulated dimensions, including
  the seam and wire exit, before connecting a cell. [nice!nano FAQ](https://nicekeyboards.com/docs/nice-nano/faq/)
- Hard requirements any cell must meet: 301230 size (302030 does NOT fit —
  20mm fouls the socket pins), 3.7V, ≥100mAh, protection PCM (reject any
  unprotected pouch on arrival), JST-PH 2.0mm pigtail with red=pack+.
- Pack+ (red) → PPTC fuse → switch common, pack− (black) → GND; charges
  only with the switch ON. Meter the pigtail polarity against JST pin 1
  BEFORE the first plug-in (reverse polarity kills board and cell).
- Select the exact series PPTC in the pack-positive lead and record its
  ratings, trip curve and installed placement. The earlier generic
  0.5–1A hold range was a placeholder. Qualify the pack PCM and charging
  limits independently of the harness fuse.
- First-article DMM checks (both halves): RAW↔B+ short, GND↔B− short,
  RAW↔VCC open; charge-ON orange LED.
- Charge-ON labeling: mark the case at each half "charge only when ON"
  (switch upstream of RAW — OFF does nothing); first-article verifies the
  orange LED lights with switch ON and stays dark with OFF.

## Fab limits — confirm with the chosen fab BEFORE ordering

- Confirm minima/cost for this 2-layer 1.6mm stackup: 0.25mm track /
  0.2mm clearance / 0.30-drill-in-0.65-pad signal vias + 0.50-in-1.00
  power vias, plus routed-slot rules for rev-2 flex
  cuts (typically >=1mm). Do not order until the fab accepts the
  Gerber/drill pack against these limits.

## Not parts (fab features)

3× fiducials + 2× 3.2mm NPTH tooling holes per half, placed by the
generator. Gasket mounting uses no PCB holes.

## Fab note

Each half is ~150×115mm — over the 100×100mm value tier at JLCPCB/PCBWay,
so price both tiers (and panel-by-2 quotes) before ordering. Design-vs-fab
limits, checked 2026-10-14 against JLCPCB's published 1–2 layer
capabilities (PCBWay comparable — recheck its page if you use them):
0.25mm tracks (min 0.10), 0.2mm clearance (min 0.10), 0.3/0.65mm signal
vias + 0.5/1.0mm power vias (min drill 0.3 this tier, annular ≥0.15;
ours = 0.30 drill in 0.65 pad → annular 0.175 — JLC-verified 2026-10; the
old "0.15/0.25" line quoted the KiCad template, not the boards),
150×115mm halves (2-layer max 670×600), 1.6mm/0.3 drill = 5.3:1 aspect
(max 8:1). Use tab routing for the concave profile. Review the
v0.5.3 copper-to-profile measurements and slot requirements with the
fabricator. [PCB order guide](../pcb/BOM_ORDER.md)

Use the measured maximum insulated pack thickness and the minimum clear
height under the fully seated module to establish the stack budget.
Allow room for the component bodies, solder, pouch seam and wire exit.
