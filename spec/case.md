# Hojicha44 — case interface (plate + gasket contract, rev-1)

Source of truth for plate geometry: `plate/gen_plate.py`
(derives from the placed PCB; never hand-edit CAD).
Preview: `plate/Hojicha44-{Left,Right}-plate.svg`
Laser file: `plate/Hojicha44-{Left,Right}-plate.dxf` (R12, mm)
Tab map: `plate/Hojicha44-{Left,Right}-lands.json` (root centers for
jacket pockets)

## Mounting: tab-and-jacket suspension

The plate grows 8 discrete tongues per half (10mm wide, 5mm proud,
2mm root fillets, chamfered tips), each carrying a poron pad top and
bottom — no rim strips, no plate screws, no hard contact anywhere. Two
tabs are pinned (top edge above the outer key column, bottom-inner
corner under the MCU); the rest spread even. Support uniformity comes
from identical poron-padded tabs at even spacing, not from foam
proximity. The inner
(microcontroller) edge carries no tab: MCU/TRRS/encoder windows occupy
it fully and the remaining rim finger is narrower than a tab root, so
that zone floats between its flanking tabs by design — encoder push
stays soft there.
Encoder push over the window zone stays soft by design.

## Stack (top to bottom, per half)

| Layer | Spec |
|---|---|
| Top case | v0.5.4 magnetic cover. Underside z=3.20 at the pad stations, top z=6.40, thumb lip z=5.20. One merged key field, controller and encoder openings, and a dedicated power-switch actuator slot. Underside pockets roof the JST, TRRS body and switch housing. The lined USB-C channel is 14.0mm wide with a z=1.25 sill. Eight Ø4.3×0.7mm magnet pockets mirror the tub. |
| Top gaskets | Poron pads 7×4mm on each tab (PORON layer in the DXF), **1.5mm** thick (thin-top revision; compressed to 1.00 at 33% — TOP_FOAM_T/TOP_PRELOAD in `case/params.py`) |
| Plate | **1.2mm** (material below), outline = PCB outline + tabs (USB notch included). 1.2mm is the Choc v1 clip-engagement thickness (Keebio: a Choc plate must be 1.2mm for the clip to engage; at 1.5/1.6mm the "lower catch doesn't engage" and the switch is held by friction alone) |
| Plate↔PCB gap | **1.00mm** — the Choc v1 clip band. MEASURED from the Kailh Choc v1 outline drawing + a community STEP model (`spec/research-open-items-2026-10-21.md` §PG1350): above the PCB the switch is skirt 0–0.9, **flexible clip arms 0.9–1.3 (their lip grabs the plate underside)**, then the **14.8–15.0 "ears" at 2.2–3.0 that bear on the plate's top**. So the plate must sit between the lip (≤1.3) and the ears (2.2): a 1.2mm plate on a 1.00mm gap occupies **1.00–2.20** — the lip grabs the underside, the ears seat exactly on the top. A 1.05 gap lifts the ears 0.05 into the plate; a 1.3 gap drives the plate top through the ears (no grab at all). The diodes sit on the underside of the PCB, so the plate is through-cut. |
| PCB | 1.6mm, v0.5.4 carrier (hangs from the plate on the switches) |
| Bottom gaskets | Same 7×4 pads (3.0mm, compressed to 2.55 at 15%) under each tab (pairs at one XY); tub floor steps to −4.65 under the PCB zone (sockets + clearance) — foam sets tab height, floor depth is separate (see `case/params.py`) |
| Bottom case | v0.5.4 tub. Floor top z=−4.65, nominal slab 1.70mm, overall case height about 12.8mm. The rounded side bay clears the modeled Ø9.50mm TRRS boot. Keep optional acoustic foam clear of the diodes, sockets, switch leads and moving parts through the full gasket travel. |

- **Bottom-case floor.** The floor top is z=−4.65 and the 1.70mm slab
  ends at −6.35, measured from the nominal carrier PCB top. The bare
  PCB has 3.05mm below it, the modeled Choc sockets 1.18mm, the modeled JST
  tips 1.25mm and the encoder leads 1.00mm. A stock Würth 450301014042
  projects 4.70–5.10mm and intersects the floor at all three pins.
  For this tub, trim the soldered switch terminals and inspect the joints.
  The finished lead and solder may project at most 3.25mm from the PCB
  top. This leaves 1.40mm nominally and 1.00mm with 0.40mm downward travel. A full-length lead design
  requires a deeper floor or local clearance preserving the floor web.
  Test the seated PCB through its gasket travel before placing acoustic
  foam in the open regions. [Würth drawing](https://www.we-online.com/components/products/datasheet/450301014042.pdf)

- **Historical strength estimate (October 2026 cover; user: "strong enough
  in PETG, 100% infill okay, no exotic materials"):** measured minimum
  features on the gated solids, all >= 1.2mm except one non-spanning
  rim: tub wall 2.62, tab-pocket web 2.45, floor slab 1.70, cover web
  1.69, ledge web 1.20 (cover 2.0 − ledge 0.8, by construction — the
  ledge cutter spans past the cover top), magnet-pocket floor 1.30,
  TRRS hole roof 0.70 (plate material around a Ø6.0 hole, not a
  spanning beam). Load paths: the cover's center press deflects
  ~0.3–0.9mm for a firm 5N press (strip model) against the 1.0mm foam
  gap — the foam/plate bounds it, magnets only retain; the tub walls
  take desk/grip loads in compression or in-plane; the only through-
  layer tension is the 8 magnet-pocket floors (~0.7MPa under a 1kgf
  magnet — trivial vs PETG's ~20MPa through-layer strength). PETG at
  100% infill (E ≈ 2.1 GPa, tensile ≈ 50 MPa) is STIFFER and as strong
  as the MJF PA12 reference (E ≈ 1.65 GPa, ≈ 48 MPa) on every path;
  the PETG risks are warp/dimensional, not strength: brim the 167mm
  tub, 4+ perimeters, calibrate XY (measure the 166.9 outer width),
  print as oriented (tub open-face-up, cover underside-up). Gate:
  `tests/spec_checks.cjs` pins FLOOR_T >= 1.5 and the ledge web
  >= 1.0; `plate/gen_plate.py --check` carries the new z-stack gate.
  The plate stays shop-cut 1.2mm PC (do NOT print it in PETG: flex +
  creep defeat the Choc clip).

- **Silhouette vs sandwich cases (research round 2026-10-24; user: "the
  classics don't have beefy top cases"):** Sofle / Corne / Lily58 class
  builds use an acrylic/FR4 **sandwich** — bottom plate + PCB + a TOP
  PLATE that IS the switch plate, joined by standoffs (commonly 7mm choc
  / 10mm+ MX; Aurora Corne plates 1.5–1.6mm). There is no enclosure over
  the keycaps: the plate is the top, caps tower above it, and the
  underside is open foam. Hojicha44 keeps the same plate stack (plate at
  the Choc clip band) and adds a thin magnetic cosmetic cover over
  everything, enclosing the acoustic volume without visible fasteners.
  The v0.5.4 thumb lip lowers the wrist-facing cover beside the thumb
  caps. Check thumb access and cap travel on the assembled first article.

## Gasket stock and preload

- Use eight 7×4 mm pads of each thickness per half. Target 3.00 mm
  below the plate and 1.50 mm above it, including adhesive and backing.
- Rogers lists unsupported 4701-30 at 320 kg/m³ in 3.18 and 1.57 mm
  nominal thicknesses. These are sample candidates. The 240 kg/m³
  grade starts at 4.78 mm. Obtain the exact material and thickness
  tolerances from the supplier before ordering assembled parts.
  [Rogers 4701-30 data sheet](https://rogerscorp.com/-/media/project/rogerscorp/documents/elastomeric-material-solutions/poron/english/data-sheets/17-316-poron-4701-30-very-soft-global-standards-data-sheet.pdf)
- The 4.75 mm shelf-to-lip stack leaves 3.55 mm total for compressed
  foam once the 1.20 mm plate is in place. The CAD allocates 2.55 mm
  below the plate and 1.00 mm above it. Actual PCB height depends on
  pad force, backing, adhesive and assembly load. Check seating,
  loaded travel, cable fit and cover retention with the chosen pads.
- Plate note: foam spec is plate-agnostic; recommended **PC 1.2 mm**
  (softest, most flex, deepest sound) or **POM 1.2 mm** (balanced,
  good feel, stable). Bounce comes from plate span between tabs; foam
  sets mount resonance and damping. (FR4/ALU/CARBON change downstream
  only via `MATERIAL` — web minimums re-gate.)
- Cut 7×4 mm pads from 90×4 mm stock (≈12 pads per 90 mm strip; 16 pads/half
  ⇒ 2 strips/half). Single-supported (PET adhesive) preferred; unsupported
  stock needs spray/transfer adhesive and holds less well.
- Pads stick to the TABs (plate), top and bottom — never to the case,
  so the assembly keeps its gaskets on disassembly. Pad centers = tab
  root centers + 2.0mm outward (`lands.json`); placement map on the PORON DXF layer.
- USB/TRRS port openings in the case walls per the notch/mouth positions
  in `spec/electronics.yaml`; antenna end keeps the 3mm plastic-only rule
  (rationale: it is a dielectric-loss/shadowing guard around the module's
  own keepout practice, not a λ/10 detune rule — at 2.4GHz λ/4 ≈ 31mm, so
  full shadowing avoidance is impossible in any closed case; the real
  validation is the BLE range bench in first-article §5)

## Port-bore contract (v3.3 breach + v3.4 shaping + v3.5 pwrsw, gate-enforced)

The rim dilation (CASE_OUTSET 8.2 today; 7.0 when this note was written v3.4) BRIDGES the USB notch (the notch floor sits
6.3–10.3mm below the local rim line depending on which shoulder you
measure against — "~5.45 deep" was a one-point figure; the skin
envelope rides ~17mm north of the rim there
— arc around the notch-mouth corners), so a fixed-DEPTH slot shipped
sealed shut in v3.2. Contract is
now structural, not numeric:

- Every port bore's OUTER FACE must actually exit the skin: `gen_case.py`
  measures the needed extent per port (marches the face outward until the
  whole face clears the skin ring, +1.0mm travel; prints
  `usb out=20.20 / trrs out=10.70 / pwrsw out=10.70` at OUTSET 8.2) —
  do not hand-pin a depth (the
  v3.1-v3.2 fixed `SLOT_OUT = 8.5` was the failure). The march is
  z-independent — breach proof and bore shape are separate decisions.
- Bore z bands are sized to the PLUGS, not to the wall (v3.2 introduced
  the full-wall z band and v3.3 kept it while fixing the depth: 14×11.6
  / 9.5×11.6 rectangles the user called "big gaping"; v3.4 shapes the
  z band):
  - USB = **14.0-wide slot with 1.2mm bottom fillets spanning z 2.0..top**
    (`SLOT_PAST_TOP` pushes the cut past the case top plane so the
    mouth's top face is the solid's own face). Plug stack: sockets
    ~4.5 → module 4.5..7.7 → receptacle mid ~6.1, i.e. the plug AXIS
    rides at the lip plane; its overmold tops ~3.2 above the lip
    (~9.2 abs) and bottoms ~2.8, so only ~2.8..lip of the plug
    crosses the wall band — the neck above the lip exits through the
    OPEN TOP and is the future cover's duty (see Stack/open-IF cover).
  - TRRS = **round Ø9.5 bore centered on the jack axis z 2.5**
    (measured off the vendored PJ-320A STEP: body 6.1 wide, top face
    flat at z 5.0). The required right-angle plug's ball boot (≤8.5)
    swings freely about that axis; ball-vs-bore margins hold for
    ±0.5mm axis drift. The bore is clipped flat by the lip only where
    it would pass above the open top — the jack itself tops at z 5.0
    below the lip. Drop-in is measured-clear with margin to spare: the
    jack's 0.99mm-RECESSED mouth face never enters the wall band at
    all (review-measured); the worst-corner bound — face corner r
    3.94 vs bore r 4.75, ~0.8mm clear — is conservative
    (case/probe_bores.py gates this against the finished solid).
  - PWR = **5.0-wide actuator slot spanning z 4.3..top with 0.8mm
    bottom fillets**, opening through the north rim plateau — the raw
    Edge.Cuts line y=58.0 across x 97.5..110.5 (mirror 181..194), so
    the slot frame is EXACT axis-aligned (no resample phase: a wobbling
    anchor x had the slot 0.87 from tab-4's pocket at x=100.59, which
    the SAT gate rejected; mouth centre 106.3/185.2 clears the pocket
    by ≥3.2 and the USB mouth by ~1.8). The WS-SLTV body (10×2.5×6.4)
    sits wholly inside the cavity — nothing internal ever crosses the
    wall; the red actuator (1.4 tall, top z 6.4) shows through the slot
    and flicks with a fingernail entering from above (~0.7 slot margin
    over the ~3.6 assumed lever sweep; blade exacts at first article).
- `check_half` re-proves it on the finished solid: mouth probes across
  the bore cross-section at two z planes (0.9 of the bore half-width;
  z planes inside each bore) must be void, air just beyond the face
  must stay air at those planes, the slab under each bore stays solid
  (no bottom holes), skin-band probing is bore-aware at z=0 (USB's
  band stays solid below its z0=2.0 bore), wall census minimum is
  printed (2.62 L / 2.70 R measured at OUTSET 8.2) with pocket-corner webs (2.45 / 2.35),
  and SAT keeps every bore ≥3mm from tab pockets (bounding-rect proof
  is conservative: fillet/circle regions are subsets of the rect).
- **Antenna window: none.** The antenna circle keeps ≥13mm of air
  (measured **14.15mm** in-plane, to the nearest case WALL on both
  halves; the nearest 3D material is the floor slab below at
  **5.60mm** — both printed per build by the new `census antenna`
  line) —
  the 3mm rule (electronics.yaml) is met with margin; plastic beyond
  3mm is not a radio problem. A window would only become required if
  the future COVER had to pass closer than 3mm over the zone, which
  the cover contract already forbids.
- Widths/axes are first-article-verified against the real plugs
  (`spec/first-article.md`): USB 14 covers the 12.35 housing, the TRRS
  bore covers the boot swing inside it, and the boot/jack z bands get
  measured at the slice dry-fit.

## Retention: recessed magnets and cover

User-approved scheme: ring-cover retention with recessed magnets — no
snap lips, no heat-set inserts, nothing internal pokes through the
exterior.

- **Stations** (`gen_case.magnet_stations()`, symmetric build v3.6):
  the LEFT half is computed once per build; the RIGHT half is its exact
  mirror (`x -> 291.5 - x`, the `MIRROR_AX` axis) re-validated against
  the right boundaries/obstructions/antenna — any asymmetric rejection
  aborts the build instead of yielding unequal counts (the 2026-10-20
  six-review audit caught the old per-half walk resolving to 6/7
  stations and putting Left's retention ON the pull-test gate). A
  station centres a Ø4.3×2.2 pocket where the local band is ≥7.5mm
  (web ≥1.6 to BOTH boundaries — the reviewer floor, at OUTSET 8.2 /
  RIM_CLEAR 0.5 the straight-rim band is 7.7 so the premise holds with
  slack), ≥5.15mm from every port rect and tab pocket rect (rect-aware
  distance: a point INSIDE a rect is distance 0 — edge-distance alone
  once read a deep-inside point as "far" and placed a phantom station
  over the USB-notch void; the pocket web probes caught it), ≥10.1mm
  from the antenna centre, and ≥14mm from every other station, snapped
  at perimeter/8 spacing (8 per half — measured 8/8 exact mirrors at
  band min 7.68 / web min 1.69; the gate floor is ≥8).
- **Pockets**: the tub uses Ø4.3×2.2mm pockets for Ø4×2mm magnets.
  The cover uses Ø4.3×0.7mm pockets for Ø4×0.5mm magnets. Seat the
  opposite faces flush at the 3.20mm lip plane, allowing 0.2mm nominal
  adhesive depth. The cover pocket leaves 1.30mm of material.
- **Preload**: the tab shelf sits at z −1.55mm and the seated cover
  underside at z 3.20mm. The 4.75mm stack comprises 2.55mm compressed
  bottom foam, 1.20mm plate, and 1.00mm compressed top foam. Verify
  contact at each pad and magnet pull force on the first article.
- **Ports**: check the actual USB and TRRS plugs through the closed
  case. The Ø6.0mm TRRS bore has a roof. Check cover seating and full
  actuator travel with the power switch installed.

## Poron pad-to-tab margin (rev-1 verified 2026-10-16; fix adopted 2026-10-20)

Pad orientation from the generator (`hl` scales the transverse vector,
`hw` the outward one): the **7 mm axis runs LATERAL** across the 10 mm
tongue, the **4 mm axis runs ALONG** the 5 mm tongue (pad spans rim-line
to +4.0 → 1 mm tip spare, no tip overhang). All pad corners test
on-plate (point-in-poly within 0.1 mm). The August-rev 8 mm pad left the
**tightest corner-edge ≈ 0.35 mm** — a laser kerf of ≈0.1–0.2 mm plus
≈0.1 mm part tolerance could nibble it. The six-review audit (2026-10-20)
adopted the rev-2 carve: **7 mm pads, corner-edge 0.71 mm measured on
both halves** — no longer kerf-fragile; strip stock still cuts 12 pads on
90 mm.
- No tip overhang — projection proof over all 8 tabs × both halves: every
  pad spans +0.0→+4.0 along the tongue against the +5.0 tip (1.0 mm spare),
  lateral half-width 4.0 against 5.0 nominal. Support is structural, not
  marginal: tongues splice outward of solid rim, tab eligibility bars any
  opening within web minimum of the tab frame, so solid material sits
  under every pad — the 0.71 mm is purely a manufacturing-tolerance
  margin, not a support question.
## Plate materials (pick one, re-run the generator to re-gate)

| Material | Fab | Notes |
|---|---|---|
| PC 1.2mm (default) | laser | softest feel, virtually unbreakable, cheapest prototype. **1.2mm is mandatory for Choc v1 clip engagement** — a thicker plate does not clip |
| POM 1.2mm | mill/laser | machines beautifully, slightly firmer than PC |
| FR4 1.6mm | route | stiff, cheap; glass dust when routing |
| ALU 1.2mm | laser/waterjet/CNC | balanced feel, best sound; isolate from copper |
| CARBON 1.2mm | mill ONLY (never laser: toxic dust + delamination) | stiffest; **conductive** — plate touches switch plastic + jackets only by construction, verify at assembly |

`MATERIAL` in the generator re-gates every web minimum
(PC/POM 1.0, FR4/ALU 1.5, CARBON 2.0); tab roots carry 2mm fillets
against crack initiation in every material.

## Plate openings (both halves)

- 22× 14×14mm Choc cutouts at switch centers/rotations (rev 2) — **body
  clearance, not a clip fit**: the PG1350 lower body passes at 13.8
  square (Kailh's plate-footprint datum; the 15.0 outline is the CLIP
  WING span).  Rev-2 (support strategy b, ADOPTED) uses a **14.0mm
  cutout in a 1.2mm plate**: 0.10mm/side on the 13.8 body (a 13.8
  hole is line-to-line and risks a switch that will not insert) while
  the 15.0 clip wing still overlaps the plate by 0.50mm/side — the
  overlap the clip arm hooks under.  The old 15.0 hole + 1.5mm plate
  had NO retention: the switch rocked, lifted out and was held by
  friction and the hotswap sockets alone.  First-article coupon
  (spec/first-article.md): cut 13.8 / 14.0 / 14.2 / 15.0 squares in
  1.2mm PC and measure insertion + retention before the plate order.
  **Tolerance stack (the clip band is only 1.3mm tall):** the capture
  window for the plate's underside is the clip-lip band z **0.9–1.3**
  (below 0.9 the plate falls out of the band = friction-only, which is
  the documented 1.5/1.6 failure; above 1.3 the lip never reaches the
  underside). In the assembled state the ears seat the plate from
  above, so the settled gap = **2.2 − plate_thickness**: for a 1.2mm
  plate that is **1.00**, between the capture limits with **0.10 of
  margin below and 0.30 above**. The ±0.1 laser slice tolerance spends
  the entire bottom margin at 1.3mm (lip tip, marginal capture), which
  is why the coupon gate rejects any plate thicker than 1.25 and the
  first article calipers the real plate. The +0.1 plate does NOT push
  the switch off the stack: the ears seat the plate 0.1 lower and the
  switch stays put (the failure mode of a too-thick plate is "no
  scan-row retention", not "the switch sits high") — verify both on
  the first article (caliper the plate and the gap, confirm every
  switch is flush with its neighbours and the clip catches).
- **16.2 × 12.4mm encoder window** (instance rot 0, body axis-aligned).
  **CHANGED IN REV 2, and it was a blocker.** The rev-1 hole was a
  12.7mm square sized off the vendored ROT_EC11E STEP for the rev-1
  plate band (z 2.0..3.5), where the encoder's body is 12.30 wide.
  The rev-2 plate band is **z 1.00..2.20** (1.00 gap + 1.20 plate),
  and measuring the SAME vendored STEP gives the encoder's
  cross-section as **14.95 wide × 11.70 deep for z 0.0..1.5** (the
  A/B/C and S1/S2 terminal blocks stand proud of the 12.30 body) and
  12.30 × 11.70 for z 1.6..2.3 (the waist). The rev-2 band therefore
  sits **inside the terminal blocks**: the 12.7 hole fouled the
  encoder by up to **1.41mm/side** and the encoder would not pass
  through the plate at all. The window is now sized to the measured
  ENVELOPE, not the waist: 16.2 × 12.4 gives **0.625/side in x (0.375
  on the tight side — the shaft is 0.25 off the envelope's centre) and
  0.35/side in y** over 14.95 × 11.70, and stays symmetric about the
  shaft so the two halves' windows remain exact mirrors (the encoder is a translated,
  NOT mirrored, part — an offset window would break the mirror gate).
  Nothing is lost: the encoder is located by its PCB pins, and the
  rev-1 hole had 0.20/side, i.e. clearance only. `gen_plate.py` asserts
  the window can never shrink below envelope + 0.2/side.
  **First article:** caliper the real encoder's terminals at
  z 1.0..1.5; if they do not protrude above ~1.5mm (the STEP may
  overstate them) the window may be reduced to 12.7 square, but the
  shipped plate must clear the model as it stands.
  Corner relief maths (audit 2026-10-20): body extreme over the
  diagonal = (12.30/2)·√2 − 0.17·(√2−1) ≈ 8.63 vs the hole's 0.5
  fillet-relief reach ≈ 8.77 → 0.145mm nominal corner clearance;
  tangency would need a 0.85 fillet or the 13.0-hole fallback, both
  rejected as needless (hand insert).
  The knob sits ABOVE the cover, not through it: short-shaft
  encoder (tip ~13.5 abs) under a low round fluted knob — OD 16.8,
  skirt bottom 6.1 (cover 5.2 + 0.9: the EC11 push travel is 0.5±0.3,
  so a full press can never land the skirt on the cover), crown
  ~15.3. A round knob sweeps a constant Ø16.8 about the shaft centre;
  the nearest cap corner sits 12.04mm away (SW_L17 centre 24.04mm −
  12.0 cap half-diagonal), a 3.6mm clearance at every angle — no
  45° corner-sweep check needed (that was the old square 13×13 knob's
  caveat). The knob fully covers the cover's 12.0×11.7 encoder
  window (diagonal 16.75 < 16.8). A 17mm round hole was rejected: the encoder SHAFT center
  sits 24.04mm from the nearest switch center (SW_L17; the old "18.18"
  was the raw EC11 footprint origin, not the shaft center — the "18.2
  pitch" cited by earlier revs is the same off-center figure), so a
  17mm hole plus that neighbour's 15mm key cutout leaves next to no
  web once the rows' splay is accounted. The generator now prints the
  definitive webs each run (`gen_plate.py`): **enc↔cutouts 7.90,
  enc↔windows 3.80, enc↔port rects 4.38 (both halves — the audit-round
  mirroring removed the old L/R asymmetry)**
  — the old "~3.55" figure was approximately the window web, not the
  cutout web.
- W1 windows: slide-switch strip + MCU/cell/USB core (tall top-side parts).
- W2 window + channel to the split-gap edge: TRRS mouth must exit; the
  plug overlaps plate-top height, so no solid edge allowed there.
