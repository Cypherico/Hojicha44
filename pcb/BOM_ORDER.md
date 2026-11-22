# Part order list (v0.5.2) — with live-verified SKUs

> Use v0.5.2 for the first article and qualify the assembly before a batch. [Order guide](MANUFACTURING.md)

Prices/stock verified 2026-10-19 against vendor pages — they WILL drift;
re-check at cart time. PCB fab choices are NOT here: see
`MANUFACTURING.md`. Quantity basis: the full split (2 halves).

## A. SMD pass (DigiKey)

| Buy | Qty | Part | ~Price | Note |
|---|---|---|---|---|
| ☐ | 50 | Diodes Inc **1N4148W-7-F** (DigiKey `1N4148W-7-F`) | $3.84 | SOD-123 matrix diodes, 44 needed + spares; same MPN as footprint/schematic |

## B. Modules (splitkb.com)

| Buy | Qty | Part | ~Price | Note |
|---|---|---|---|---|
| ☐ | 2 | **nice!nano v2** | €21.44 ea | Typeractive $25 is sold out (restock notify); KEEBD $25 stock spotty |
| ☐ | 2 | **Machine-pin socket and pin sets**, two 12-position rows per module | per supplier | Qualify one fully mated set at **4.5–5.0mm carrier top to module underside**, with the pack and USB plug in place. The Mill-Max 315-43-112-41-003000 strip has 1.80mm insulation height. Compare the Samtec BBL-112-T-E option and verify the resulting stack before buying a batch. |

## C. Distribution pass (DigiKey / TME / LCSC)

| Buy | Qty | Part | ~Price | Note |
|---|---|---|---|---|
| ☐ | 2 | **Alps EC11E15244G1** rotary encoder with push | — | Reference part for PCB, firmware and clearance checks. A shorter part needs a verified pinout, mounting pattern, body clearance, detent count and push travel before substitution. |
| ☐ | 2 | Würth **450301014042** (DigiKey) | $2.15 | WS-SLTV slide SPDT; no drop-in alternate (clones need footprint check) |
| ☐ | 2 | JST **S2B-PH-K-S** (DigiKey) | $0.12 | side-entry battery header |
| ☐ | 2 | JST **PHR-2** housing | $0.10 | |
| ☐ | 1 | JST **SPH-002T-P0.5S** contacts, strip of 100 | $4.09 | 4 needed; strip = cheapest entry + spares |
| ☐ | 2 | XKB **PJ-320A** (LCSC **C2884926**, MOQ 5) | $0.75 | footprint is PJ-320A-specific — don't substitute PJ-3xx variants |
| ☐ | 2 | Knob matched to the qualified encoder shaft | — | Dry-fit the knob through full rotation and push travel. The low render knob was sized for a shorter shaft and does not fit the unmodified EC11E15244G1 at the shown height. |

## D. Keyboard-specialty pass

| Buy | Qty | Part | ~Price | Note |
|---|---|---|---|---|
| ☐ | 2 | kriscables **301230 110mAh LiPo**, PCM + JST-PH pigtail | €8.90–18.90 ea (two listings seen; re-check at checkout) | Qualify actual maximum pack dimensions and charge rating. Meter pigtail polarity against the carrier before first plug-in. |
| ☐ | 2 | **Polyfuse (PPTC), 0.5–1A hold, ≥16V** (axial/radial) | ~$1–2 | series with pack+ (1/half; the 10-half pilot buys 20) — wired, NOT on the PCB; research §2b/2d |
| ☐ | 5 | Kailh **PG1350 Choc v1** switches (Typeractive, $5.50/10) | $27.50 | 44 needed; pick feel family; any PG1350 fits the hotswap socket |
| ☐ | 44 | **Kailh Choc v1 hotswap SOCKETS** (socketed, bottom side) | ~$1–2 ea | **not in the released bom.csv** — the release BOM only lists parts with an MPN, and a footprint-only socket has none, so this line is the ONLY place the 44 sockets get ordered. Sockets solder on B.Cu under each switch; the diode sits beside its switch, not under it. Verify the variant matches the vendored `SW_Hotswap_Kailh_Choc_V1_1.00u` footprint (the spec fixes the footprint, not the SKU) |
| ☐ | 1 | 4-pole TRRS cable, if retained for debug | — | Qualify the shaft reach and boot on each end against the revised jack and bore before ordering. |
| ☐ | 44–50 | **MBK Choc keycaps** (PBT, Typeractive ~$1/cap) | ~$44 | Choc v1 stems only (MX won't fit); MBK legend sets spotted sold out at splitkb — CFX (~$25/set) is the budget fallback |
| ☐ | 16 + spares | Axially magnetized **N52 Ø4×2mm** discs for the tubs | per quote | The previously listed supermagnete S-04-02-N is N45. Qualify it with the actual 0.5mm cover magnet if using it as an alternate. [Manufacturer data](https://www.supermagnete.ch/eng/data_sheet_S-04-02-N.pdf) |
| ☐ | 16 + spares | N52 disc magnets, Ø4×0.5mm, axially magnetized | — | COVER magnets, face-down flush in Ø4.3×0.7mm pockets. Confirm supply and pull force before the batch. |
| ☐ | — | glue for the magnets: **B-7000** | $5 | flexible, nylon-safe (PA12); JB-Weld rigid alt; no hot glue |

## E. Case-shop pass

> **Send exactly the files hashed in `generated/print/v0.5.2/MANIFEST.txt`**
> (sha256, both shops: plate DXF/SVG for the laser, case STEP/STL for MJF).
> If any generator constant changed, regenerate everything and re-record
> the manifest in the same commit — never order from a stale hash.

| Buy | Qty | Part | ~Price | Note |
|---|---|---|---|---|
| ☐ | — | Very soft PORON, nominal design targets 3.0mm bottom and 1.5mm top | per quote | Confirm series, available density, sheet thickness tolerance and adhesive backing. Check compression on an assembled coupon. Cut eight 7×4mm pads per thickness per half. |
| ☐ | 2 | **1.2mm** plate from the Left and Right DXFs | — | Through-cut OUTLINE and CUTOUT. Machine 22 nominal 0.55mm underside pockets from RELIEF. PORON is a punch template. Approve the fabrication process on a coupon that leaves ≥0.60mm of plate and ≥0.15mm seated clearance above a 1.40mm diode. At nominal thickness and gap the allowable relief is 0.55–0.60mm. |
| ☐ | — | Tub and cover in **MJF PA12** | per quote | The v0.5.2 STEP volumes are approximately 57.2 cm³ per tub and 15.2 cm³ per cover. Quote the matching STEP files. PETG is an option for a first fit print. |
| ☐ | 1 roll | Kapton/polyimide tape ≥10mm | $2–5 | cell sandwich + nano underside |
| ☐ | 1 | SAC305 no-clean 0.5mm solder (e.g. SRA) + **NC-559-class flux pen** | ~$25 + ~$10 | ENIG pads, hand work |

## PCB order note (must be pasted into the fab order)

Use tab routing for the concave outline. KiCad measured minimum
copper-to-profile distances of **0.5821mm Left and 0.3301mm Right** on
v0.5.1. The closest right trace belongs to the TRRS tip. Confirm the
chosen profile tolerance and remeasure both revised boards before ordering.

```
CONCAVE OUTLINE — TAB-ROUTE ONLY, NO V-CUT / V-SCORE
```

(also stated in `spec/bom.md`; the fab rejects or breaks the panel
otherwise).

## Cart mechanics

- Order-split reality: DigiKey/TME/LCSC (A+C), splitkb (B),
  kriscables (knob, battery), Typeractive (switches/caps/sockets,
  in-stock check first), KEEBD (cable), supermagnete, then the
  case/plate services. They don't consolidate — expect 5–7 carts.
- **Pending stock at check time**: Typeractive nice!nano +
  sockets, MBK legend sets. splitkb fills those roles now; set
  restock notifications as backup.
- **PCBs are a separate order** — see `MANUFACTURING.md` (the two
  designs are ordered as two 5-pc line items, ENIG chosen in the form).
- Rough part total **~$310–350** firm picks (ex-PCBs, ex-shipping);
  ~$230–250 with budget alternates.
- Message-order across carts (polarity-critical first): everything
  above can be bought simultaneously EXCEPT nothing — no part here
  depends on another's arrival. Only *assembly* has gates
  (`spec/first-article.md`).

## Verify-at-cart flags (things research flagged or spec demands)

1. **Encoder**: use the specified Alps EC11E15244G1 and qualify the matching knob on the first article.
2. **Socket kit.** Check the installed board-to-board gap and contact
   engagement with a fully seated module. Use the measured gap and the
   largest insulated pack dimension to qualify the pair.
3. **Battery.** Check the pack's maximum envelope, charge rating,
   protection and polarity against the actual build.
4. **TRRS.** Qualify the jack and cable together if retained for debug.
5. Source axially magnetized N52 discs in both sizes. Verify the assembled pair force with the actual pads and cured adhesive before ordering the batch.
6. KiCad 10.0.6 measurements hold steady in this doc; if the layout
   ever re-cuts, re-read `spec/bom.md` first — this list derives from it.

## Sources

Prices from live vendor listings 2026-10-19 via research pass:
DigiKey (1N4148W-7-F, 450301014042, JST PH items), TME (EC11E15244G1),
LCSC C2884926, splitkb (nano, Mill-Max sets), Typeractive (switches,
caps), kriscables (knob, 301230), KEEBD (TRRS cable),
supermagnete S-04 data sheets, SRA (SAC305), 42keebs (laser plate).
Key repo sources of truth: `spec/bom.md`, `spec/electronics.yaml`,
`spec/first-article.md`, `spec/case.md`.
