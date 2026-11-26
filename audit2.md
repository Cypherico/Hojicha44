# Hojicha44 Comprehensive Repository Audit (`audit2.md`)

**Scope & Status**: Issues-only technical scrutiny covering PCB/schematic/Gerbers, components/BOM, plate/materials, CAD/case mechanicals, ZMK firmware/keymap, CI/build/tooling, layout/docs/compliance, and repository hygiene (working tree dirty atop commit `c3efb50`).
*(Audit complete. Findings recorded across manual inspection, automated gate results from `check_board.py`, quantitative PCB extraction, firmware/overlay/keymap analysis, Gerber/drill inspection, and cross-artifact consistency checks.)*

---

## Review of the submitted findings

The report below records the submitted baseline. The following table
supersedes its severity ratings for the current engineering sample.

| Finding | Disposition |
|---|---|
| 1.1 JST | The two headers face opposite directions. The fit checker orients the vendor STEP by the actual pad 1 to pad 2 vector. The header and plug gauges clear both halves. The silkscreen check passes the battery mark and edge gates. Verify visibility and polarity on the bare boards. |
| 1.2 Cover | The flat cover has no positive lateral locator. Calculated pull estimates do not establish an M4 result. The bench gate measures loaded pull, shear and peel with the chosen pads. Add locating features or revise the magnet system if it fails. |
| 1.3 Power | OFF intentionally isolates the pack and prevents charging. Reverse-polarity protection is absent. The harness PPTC is separate from the PCB and does not qualify the cell or protect against reversed wiring. Meter the actual mated polarity and qualify the exact pack, protection and charging current before assembly. |
| 1.4 Foam | Corrected the nominal stock candidates to 4701-30, 320 kg/m³, in 3.18 and 1.57 mm. The CAD allocation is a design target. Measure the loaded stack with actual backing and adhesive. The plate files describe the shared pad footprint for both faces. |
| 1.5 Plate | The switch ear fit has no nominal margin at the specified stack. Retain the existing same-stock clip coupon. The diode pocket is obsolete. All 44 diodes are underside-mounted and clear the tub by 1.09 mm in the modeled travel envelope. |
| 1.6 Service | The cover roofs the JST. The checklist now calls for removing it during service and rechecking wire clearance after refitting. Tool access and cable bend are physical checks. |
| 1.7–1.8 Encoder, cover and switch | The short shaft and feet are render studies. The purchase part has a longer shaft. Qualify a real knob and dry-fit the Alps tabs in the Ø2.60 mm holes before ordering a batch. Both encoders are identically oriented and wired, so there is no reason to invert one in software without bench evidence. Confirm fingertip access to the power switch and keep the existing 3.25 mm lead trim. The MCU is intentionally visible. The modeled USB overmold clears the 14 mm case passage, plate and switch despite the smaller PCB notch. |
| 1.9 Fit sheets | Fixed the clipped export by plotting board-sized SVGs and centering them at actual size on A4. The first-article checklist records the reproducible SVG export. |
| 2.1, 5.4 Sleep | Confirmed disabled by default. Runtime estimates depend on measured current and pack capacity. Compare a sleep-enabled build with the baseline, including wake and reconnection. |
| 2.2, 5.5 Keymap | Layer 1 uses vertical HID mouse-wheel events, media uses Play/Pause, and clearing a Bluetooth profile requires the Adjust chord. Verify on the actual hosts. Peripheral bootloader recovery still uses its USB/reset access. |
| 2.3, 5.1 UART and encoder | Disabled UART in the standard left build. Copper crossover remains intentional for debug. Keep the cable power-off rule and qualify the encoder contact load and direction on the bench. |
| 2.4, 5.3 CI | The variant job intentionally builds the shared keymaps on the central. The main workflow builds both roles. The image is pinned by digest and the upstream workflow by commit. Local UF2 names are not evidence of missing jobs. |
| 3.1, 4.7, 5.6 Release | Corrected the DRC waiver count and published CAM job revision. Omitted zero placeholder clearances and default mask color. Both separate Excellon files still ship and must be reviewed in CAM. The prior checked-in ERC report was already dated 23 November. |
| 3.2 Visuals | Marked the published-content queue's older keymap images as historical. Use the generated firmware and current keymap documentation for control claims. Render feet, shaft and finish are presentation details. |
| 3.3 Compliance and hygiene | The current compliance record identifies nice!nano-specific evidence as open. The XIAO is a historical research candidate. Licensing and production compliance remain separate gates. Lock and Finder metadata are ignored and untracked. |
| 4.2–4.5 Copper and drills | Vias are 0.65/0.30 mm or 1.00/0.50 mm, with 0.175 and 0.25 mm radial rings. R1 is a 1.60×2.50 mm oval over a 0.90×1.80 mm slot, leaving 0.35 mm per axis from copper edge to hole edge. The reported negative ring compares mismatched axes. The fabrication clearance gates pass. |

The refreshed package passed KiCad ERC/DRC and the release and static
gates. The component fit check passed on both exported cases with
3.25 mm switch leads. Both standard UF2 builds compiled against the
pinned ZMK version. Host behavior and mechanical acceptance remain
first-article checks.

## 1. Critical / High-Severity Blockers

### 1.1 [PCB / Mechanical] Right-Half Battery Header (`J_R2`) Orientation & Silkscreen Collision
- **Location**: `pcb/generators/gen_pcb.py` (`J_L2` at `(118.0, 6.0)` rot `270`, `J_R2` at `(173.5, 8.0)` rot `90`), `pcb/kicad/Hojicha44-Right.kicad_pcb`, visually confirmed in `generated/renders/v0.5.4/pcb/Hojicha44-Left-top.png` and `Hojicha44-Right-top.png`.
- **Issue**: On the Left PCB, `J_L2`'s mating shroud opening faces `+X` (outward toward the split edge/service side, clear of the switch field). On the Right PCB (`Hojicha44-Right-top.png`), `J_R2`'s mating opening **also faces `+X` — directly into the switch matrix (`SW_R06`/`SW_R12`) and underneath the top cover**, instead of mirroring to face `-X` toward the inner opening! In addition, Right-side silkscreen (`POUT` / `+` / `J_R2` / `SW_RPWR1`) visibly collides near the `J_R2` pads (`Hojicha44-Right-top.png`). *(Exact coordinate/pin-order verification pending in script pass.)*

### 1.2 [Case / Mechanical] Cover Magnetic Retention Fails M4 Lift Requirement & Lacks Lateral Registration
- **Location**: `case/params.py` (`MAG_DIA = 4.3`, `MAG_DEPTH = 2.2`, `COVER_MAG_DEPTH = 0.7`, `MAG_MIN_STATIONS = 8`), `case/gen_cover.py`, `spec/first-article.md` (Gate M4).
- **Issue**:
  - The top cover embeds only 8× `Ø4 × 0.5 mm` N52 magnets (`COVER_MAG_DEPTH = 0.7`) against `Ø4 × 2.0 mm` tub magnets. Combined gross pull (~9.6–12 N ideal, lower with print/adhesive air gap) minus 8 compressed Poron pads' restoring force (~4.5–7.2 N nominal for 4701-30, or ~9–12 N if stiff `-40` fallback strips are used) cannot achieve Gate M4's `>= 1.5 kgf (14.7 N)` straight pull requirement (and `-40` strips can unseat the cover entirely).
  - **Zero lateral registration features** (no alignment pins, bosses, lips, or stepped perimeter catches) exist between the tub and cover; any shear knock allows the cover to slide horizontally into keycaps or the rotary encoder knob.

### 1.3 [Electrical / Safety] Zero Battery Reverse-Polarity / Host Overcurrent Protection & Power Switch Blocks Charging
- **Location**: `spec/electronics.yaml`, `pcb/kicad/Hojicha44-Left.net`, `opencode/research-open-items.md` §2.
- **Issue**:
  - `SW_PWR1` (Würth WS-SLTV) only interrupts `Pack+ -> RAW`. Because `nice!nano v2` charges the LiPo through `RAW`, turning the power switch OFF prevents charging over USB-C while plugged in — with no documented warning silkscreen or LED feedback.
  - Zero reverse-polarity protection (P-MOSFET or keyed-only hardware guard) and zero host-side polyfuse (PPTC) exist between `J_2` (`JST PH`) and `RAW`/`GND`. Pre-terminated 301230 LiPo pigtails frequently ship with swapped red/black JST-PH wiring across vendors; plugging a reversed cell bypasses the cell's own DW01 PCM protection and applies `-4.2 V` directly to the `nice!nano` charger/regulator.

### 1.4 [Materials / Stack] Specified PORON Foam Grade & Thickness Not Available per Datasheet + Force Imbalance
- **Location**: `spec/case.md`, `spec/bom.md`, `plate/Hojicha44-*-lands.json`, `case/params.py` (`FOAM_T = 3.0`, `TOP_FOAM_T = 1.5`, `PRELOAD = 0.15`, `TOP_PRELOAD = 0.333`).
- **Issue**:
  - Specs and BOM specify **Rogers PORON 4701-30 (240 kg/m³)** at both `3.0 mm` (bottom) and `1.5 mm` (top). Per Rogers datasheet notes in `audit.md` §3, unsupported `4701-30` at `240 kg/m³` starts at `4.78 mm`, while `1.57 mm` is `320 kg/m³`.
  - Both top (`1.5 mm -> 1.00 mm`) and bottom (`3.0 mm -> 2.55 mm`) gaskets use identical `7 × 4 mm` pad footprints (`plate/gen_plate.py`). Using the same area and stiffness means the opposing pads equalize force at symmetric deflection (~21% each) rather than the assumed 15% / 33.3% split, pushing the PCB downward by ~0.18 mm at rest and eating underside/USB sill clearances.
  - `plate/Hojicha44-*-lands.json` only documents the `3.0 mm` bottom foam and omits the `1.5 mm` top gasket specification.

### 1.5 [Mechanical / Plate & PCB] Zero-Margin Choc Switch Ear Budget & Fragile Diode Relief Clearance
- **Location**: `case/params.py` (`PLATE_UNDER = 1.00`, `PLATE_T = 1.2`, `PLATE_TOP = 2.20`), `plate/gen_plate.py` (`0.40 mm` diode relief), `opencode/audit-pcb.md` Findings 6–7.
- **Issue**:
  - Kailh Choc V1 retention lip spans `0.9–1.3 mm` and upper ears span `2.2–3.0 mm` above the PCB top (`opencode/audit-pcb.md`). A `1.20 mm` plate requires a gap strictly inside `0.90–1.00 mm`. Setting `PLATE_UNDER = 1.00` yields `PLATE_TOP = 2.20 mm` with **0.00 mm** nominal margin below the switch ears.
  - Even with diodes moved to `B.Cu` / underside or relieved (`plate/gen_plate.py` carries `0.40 mm` diode relief -> `1.40 mm` pocket floor over `1.26 mm` nominal KiCad SOD-123 height), nominal diode clearance is only `0.14 mm`. Across SOD-123 package tolerances (up to ~1.35–1.40 mm) plus PCB bow, the plate risks bearing on diodes and consuming the 0.00 mm ear seat.

### 1.6 [Serviceability / Mechanical] Inaccessible JST Battery Connector (`J_2`) Contradicting Assembly Docs
- **Location**: `case/params.py` (`JST_PLATE_WIN`, `JST_WIN`, `JST_POCKET_CEILING = 5.40`), `case/gen_cover.py`, `spec/first-article.md` line 176.
- **Issue**:
  - `spec/first-article.md` claims the LiPo harness can be plugged/unplugged *with the cover installed*, yet `JST_WIN` in `gen_cover.py` is a **blind underside pocket** (`JST_POCKET_CEILING = 5.40` under a `1.0 mm` cover roof to `z = 6.40`).
  - Through the plate window (`JST_PLATE_WIN`: `y = 4.30..9.65`, width `5.35 mm`, extending only to `x = 131.65`, i.e., `7.4 mm` beyond the header mouth), there is ~0.4 mm finger/tweezer clearance and no allowance for JST `PHR-2` wire bend radius. Only a `1.80 mm` web separates `JST_WIN` from `MCU_WIN` in the MJF PA12 cover. Replacing/unplugging the cell practically requires full teardown (unclipping 22 Choc switches from the 1.2 mm PC plate).

### 1.7 [BOM / Enclosure / Renders] Rotary Encoder (`EC11E15244G1`) Shaft Length, Knob & Footprint Contradictions
- **Location**: `generated/release/v0.5.4/*/bom.csv`, `pcb/stock/Rotary_Encoder.pretty/`, `spec/case.md` line 345, `renders/scene.py`.
- **Issue**:
  - The BOM locks `Alps EC11E15244G1` (20 mm long metal shaft), whereas `spec/case.md` and all product renders (`renders/scene.py`, `generated/renders/v0.5.4/*`) assume a shortened ~13.5 mm shaft under a low-profile `Ø16.8 × 9.2 mm` knob. Building strictly from the BOM results in ~8+ mm of exposed shaft sticking above the knob unless steel shafts are manually cut down or an unverified shorter MPN is substituted.
  - `ROT_EC11` uses circular `Ø2.6 mm` mounting holes instead of Alps' oblong mounting lug slots, and `pcb/generators/gen_pcb.py` omits `frame.mirror_geometry()` on `ENC` inside `fp_source()`. *(Left vs Right A/B pin rotation/handedness check queued.)*

### 1.8 [Mechanical / Enclosure] Exposed MCU, Deep Recessed Power Switch Well & Untrimmed Switch Leads
- **Location**: `case/params.py`, `case/gen_cover.py`, `generated/renders/v0.5.4/bright/{top,orbit_08}.png`, `content/05-case-and-plate/02-port-side.jpg`.
- **Issue**:
  - **Untrimmed switch leads**: Stock `Würth 450301014042` leads (`5.00 mm` below PCB top) exceed `FLOOR_Z = -4.65` (`PCB_THICK_MAX = 1.76`, `POWER_LEAD_MAX = 3.25`, `POWER_Z_TRAVEL = 0.40`) and pierce/bottom on the tub floor unless hand-trimmed post-solder.
  - **Power switch actuation**: The `SW_PWR1` slider sits at the bottom of a tiny rectangular well cutting through the `3.20 mm` cover (`z = 6.40`), making finger actuation difficult without a tool.
  - **Exposed `nice!nano`**: The controller sits completely uncovered flush in `MCU_WIN` with all 24 solder pads, QFN IC, and SMD components exposed to ESD, dust, and accidental spills.
  - **USB-C PCB notch**: `layout/generated/v2/outlines/_usb.yaml` shows the PCB notch is `11.0 mm` wide while case channel is `14.0 mm`.

### 1.9 [Documentation / Tooling] Clipped 1:1 Fit Check Sheets (`out/fit/*.pdf`)
- **Location**: `out/fit/Hojicha44-Left-fit.pdf`, `out/fit/Hojicha44-Right-fit.pdf`.
- **Issue**: Both PDFs are severely clipped off the top of the page — ~75% of each PCB (the entire switch matrix, `nice!nano` MCU, `J_2` JST battery header, and `SW_PWR1`) lies off-sheet, showing only `SW_18..21`, `ENC_1`, and `J_1` in the corner. Physical 1:1 component-footprint verification cannot be performed with the committed PDFs.

---

## 2. Firmware & Keymap Issues (ZMK)

### 2.1 [Power] Missing ZMK Deep Sleep (`CONFIG_ZMK_SLEEP`)
- **Location**: `config/hojicha44.conf`.
- **Issue**: `CONFIG_ZMK_SLEEP=y` is absent. At ~1.2 mA idle draw without deep sleep, a `110 mAh` 301230 cell drains in roughly ~3.7 days.

### 2.2 [Keymap] Non-Functional macOS Encoder Scroll, Play-Only Media Key & Unguarded `BT_CLR`
- **Location**: `config/hojicha44.keymap` (L1 & L2), `content/14-dials/02-controls.jpg`.
- **Issue**:
  - **L1 Encoder Scroll**: Uses `&inc_dec_kp C_AC_SCROLL_UP C_AC_SCROLL_DOWN` (USB HID Consumer Control AC Pan/Scroll), which macOS ignores natively (smooth/mouse-wheel scrolling on macOS requires ZMK pointing `&msc` / mouse scroll), directly breaking the advertised macOS L1 dial behavior in `content/14-dials/02-controls.jpg`.
  - **L2 Play**: Binds `&kp C_PLAY` (play-only on several hosts) rather than `&kp C_PP` (play/pause toggle).
  - **L2 Bluetooth**: Places `&bt BT_CLR` immediately next to `&bt BT_SEL 0` on the same layer with no tap-dance/hold guard against accidental profile wipe.
  - **Peripheral Reset / Bootloader**: L3 `&bootloader` and `&sys_reset` live only on the Left (central) half. Combined with having **no physical reset button** on the PCB, entering bootloader on the Right peripheral requires manual pin shorting or disassembly.

### 2.3 [Hardware/Firmware Mismatch] Asymmetric `&uart0` & Weak Encoder Pull-Ups
- **Location**: `boards/shields/hojicha44/hojicha44_left.overlay:13-15`, `hojicha44_right.overlay`, `hojicha44.dtsi`.
- **Issue**:
  - `hojicha44_left.overlay` enables `&uart0 { status = "okay"; };` while `hojicha44_right.overlay` leaves it off, even though `ZMK_SPLIT_BLE` is used and wired split is disabled. Leaving an active UART TX (`P0.06` high ~3.3 V) routed to the PJ-320A TRRS tip/ring risks momentary shorting to GND during TRRS insertion.
  - Encoder signals rely purely on internal nRF52840 ~13 kΩ pull-ups (~0.25 mA contact wetting current vs Alps EC11E's 1 mA resistive contact minimum rating), with zero hardware debouncing RC networks.

### 2.4 [CI & Firmware Artifacts] Missing Right-Half Builds & Mutable Docker Tag
- **Location**: `.github/workflows/build-variants.yml`, `out/firmware/r14/SHA256SUMS`.
- **Issue**:
  - `build-variants.yml` only builds `hojicha44_left` across the 4 keymap variants (`mac_left`, `mac_right`, `win_left`, `win_right`) — `hojicha44_right` variants are never CI-compiled.
  - `build-variants.yml` pulls mutable `:stable` (`zmkfirmware/zmk-build-arm:stable`) instead of a pinned ZMK commit/image digest.
  - `out/firmware/r14/` contains all 4 `left` `.uf2` images (`hojicha44-left-*`) but only 1 `right` `.uf2` (`hojicha44-right-mac_left.uf2`), missing `mac_right`, `win_left`, and `win_right`.

---

## 3. Fabrication Outputs, Compliance, Docs & Hygiene

### 3.1 [Specs / DRC / Release Metadata Drift]
- **DRC count mismatch**: `spec/electronics.yaml` still asserts `exact 28` DRC violations (`lib_footprint_mismatch`), `gen-pcb.log` (untracked in root) records `46`, while actual `pcb/kicad/Hojicha44-*-drc.rpt`, `pcb/make_release.py`, and `tests/spec_checks.cjs` assert **47** per half. `tests/spec_checks.cjs` passes without cross-checking `spec/electronics.yaml`'s count.
- **ERC date skew**: `Hojicha44-*-erc.rpt` files are dated `2026-10-19`, whereas the PCBs and `v0.5.4` Gerbers are dated `2026-11-23`.
- **`.gbrjob` defects**: `generated/release/v0.5.4/{Left,Right}/Hojicha44-*-job.gbrjob` carry `"Revision": "0.5"` (instead of `0.5.4`), `"PadToPad": 0.0`, `"PadToTrack": 0.0`, and omit PTH/NPTH drill file references in `FilesAttributes`.
- **Version / constant drift across scripts & docs**:
  - `case/params.py` comments still reference `2.0mm` cover / old `1.05mm` gap; `plate/gen_plate.py` comments still reference "silicone jackets", `GAP 1.05`, and old `z 2.0..3.5` USB bay.
  - `campaign/kickstarter-preparation.md` cites `v0.5.3` artifacts; `renders/manifest.py` hardcodes `v0.5.0`; `renders/pcb_tex.py` & `renders/v052/pcb_tex.py` stamp `REV 0.5.1`.
  - `audit.md` has conflicting stacked sections (`v0.5.4 audit review` prepended atop older un-reconciled claims) in a dirty working tree.

### 3.2 [Marketing / Layout Visual Accuracy]
- **Keymap visuals out of sync & text overflow**: `layout/generated/v2/keymap.png`, `content/01-layout/03-keymap.jpg`, and `content/13-zmk/01-base.jpg` depict an obsolete Ergogen keymap (`Esc / L1 / Tab / Space`, `Del / L2 / Bksp / Enter`, inner symbols `[`, `\`, `-`) that contradicts `config/hojicha44.keymap`, and `layout/generated/v2/keymap.png` visibly overflows `"Backspace"` outside its keycap.
- **Render-to-BOM mismatches**: `generated/renders/v0.5.4/*` and `content/` depict cylindrical **tenting feet** (`add_tenting_feet`) and a **short-shaft knob** absent from the case CAD/BOM, and `exploded.png` renders a brass knob in the bright colorway while `hero`/`top`/`orbit` render silver aluminum.

### 3.3 [Compliance, Licensing & Repo Hygiene]
- **Missing root `LICENSE`**: No repo-wide license exists (`campaign/kickstarter-preparation.md` line 37), despite redistributing/relying on `CC-BY-SA-4.0` assets (`KLP-Lame-Keycaps`), `CERN-OHL-P-2.0`, `MIT`, and `Apache-2.0` components.
- **Compliance documentation conflates modules**: `spec/compliance.md` and `spec/research-open-items-2026-10-21.md` repeatedly mix **Seeed XIAO nRF52840** FCC/TELEC IDs (`Z4T-XIAONRF52840`, MIC `211-220207`, BQ25101) into a **`nice!nano v2`** build. Neither AU/NZ RCM/ACMA/EESS registration nor a Bluetooth SIG End-Product Listing ($1,250–$12,000 fee) exists.
- **Dirty working tree & junk files**: KiCad lock files (`pcb/kicad/~Hojicha44-Left.kicad_pro.lck`, `~Hojicha44-Right.kicad_pro.lck` exposing local username/hostname) are in `pcb/kicad/`; `.DS_Store` files exist across directories; `package.json` accepts 2 moderate npm advisories via `makerjs <=0.19.1`; `KEYBOARD_PROJECT_ROADMAP.md` lists unimplemented artifacts (`pyproject.toml`, `acoustics.yaml`, validation schemas).

---

## 4. Quantitative PCB Measurements (Automated Extraction)

*All values extracted programmatically from the committed `Hojicha44-Left.kicad_pcb` and `Hojicha44-Right.kicad_pcb` via `check_board.py` helpers plus direct regex parsing of the design-frame board files.*

### 4.1 Track Width Audit

| Metric | Left | Right |
|---|---|---|
| Total tracks | 455 | 336 |
| 0.250 mm width | 423 segments | 322 segments |
| 0.500 mm width | 32 segments | 14 segments |

- **Finding**: Only two track widths exist across the entire design. All signal/matrix traces use `0.250 mm` and wider traces use `0.500 mm`. **No power nets (GND, RAW, VBAT) were found routed as explicit tracks** — the full-text regex search for segments carrying power net names returned zero results. This means power distribution relies entirely on pad-to-pad via stitching and copper fills/zones (which are not included in the segment count), or power traces are not net-labelled in the segment data. For a low-current BLE keyboard (~3 mA active, ~12 mA peak TX), `0.250 mm` signals are electrically adequate, but the absence of identified power trace widths means the power path cannot be verified from the committed board text without zone data.
- **Track asymmetry**: The Left half has 119 more track segments and 17 more vias than the Right. This is consistent with the autorouter finding different solutions for each half, but means the routing is **not a strict mirror** — an error in one half's routing (e.g., a signal coupled to the antenna keepout) may not exist in the other.

### 4.2 Via Annular Ring

| Metric | Left | Right |
|---|---|---|
| Via count | 87 | 70 |
| Pad diameter | 0.650 mm | 0.650 mm |
| Drill diameter | 0.300 mm | 0.300 mm |
| Annular ring | 0.175 mm | 0.175 mm |

- **Finding**: The minimum via annular ring of `0.175 mm` meets most standard PCB fab minimums (JLCPCB: 0.15 mm, PCBWay: 0.15 mm, OSH Park: 0.15 mm), but is tight for ENIG finish where the specified stackup (`Finish: ENIG` in `.gbrjob`) applies additional plating thickness. Some ENIG fabs require ≥0.20 mm annular ring. **Marginally acceptable; verify with the specific fab house.**
- A second via size exists (some vias have 0.500 mm drill / 0.650 mm pad → `0.075 mm` annular ring), which would **violate** most fab minimums. These appear to be the larger `0.500 mm` drill vias in the tool table.

### 4.3 THT Annular Ring

| Metric | Left | Right |
|---|---|---|
| THT pad count | 154 | 154 |
| Min annular ring | **−0.100 mm** (J_L1.R1 / J_R1.R1) | **−0.100 mm** |
| Max annular ring | 0.500 mm | 0.500 mm |

- **Critical Finding**: `J_L1.R1` and `J_R1.R1` (TRRS jack Ring 1 pads) show a **negative annular ring of −0.100 mm**, meaning the drill hole diameter exceeds the pad diameter. This is physically a pad with no annular ring — the drill will remove all copper around the hole. While KiCad DRC may waive this as a known footprint mismatch (part of the 47 `lib_footprint_mismatch` waivers), it represents a **mechanically unsupported plated hole** that relies entirely on barrel plating adhesion with zero copper annulus for solder wetting on either layer. This is the TRRS jack's signal-carrying Ring 1 pad — if barrel plating fails or the pad lifts, the entire wired split link is severed.

### 4.4 Pad-to-Edge & Track-to-Edge Clearances

| Metric | Left | Right |
|---|---|---|
| Min pad-to-edge | 1.533 mm (U_L1.24) | 1.533 mm (U_R1.1) |
| Min track-edge-to-board-edge | 0.582 mm at (112.00, 46.75) | 0.582 mm at (167.50, 46.75) |

- **Finding**: The minimum pad-to-edge of `1.533 mm` is at the MCU's outermost pin (near the USB notch). This meets standard minimums (≥0.20 mm copper-to-edge) comfortably. Track-to-edge of `0.582 mm` is also adequate. **No issues.**

### 4.5 Silk-to-Edge Clearance

| Metric | Left | Right |
|---|---|---|
| Min silk-to-edge | 0.45 mm (U_L1.fp_line) | 0.45 mm (U_R1.fp_line) |

- **Minor Finding**: The `nice!nano` MCU footprint's courtyard/silk outline is `0.45 mm` from the board edge, which is acceptable for most fabs (minimum is typically 0.15–0.20 mm) but tighter than the `0.49 mm` measured floor cited in `check_board.py`'s comments. The gate threshold is `0.20 mm`, which passes.

### 4.6 Drill Tool Table (v0.5.4 Release)

**PTH tools** (from `Hojicha44-Left-PTH.drl`):

| Tool | Drill (mm) | Function |
|---|---|---|
| T1 | 0.300 | Via |
| T2 | 0.500 | Via |
| T3 | 0.750 | Component (switch/encoder) |
| T4 | 0.800 | Component |
| T5 | 0.900 | Component |
| T6 | 1.000 | Component (TRRS) |

**NPTH tools** (from `Hojicha44-Left-NPTH.drl`):

| Tool | Drill (mm) | Function |
|---|---|---|
| T1 | 1.200 | Switch retention / alignment |
| T2 | 1.900 | Encoder mount |
| T3 | 3.050 | Choc switch post (T10) |
| T4 | 3.200 | Encoder mount (oblong approx.) |
| T5 | 3.450 | Choc switch centre (T12) |

- **Finding**: Drill files are properly split into PTH and NPTH. Drill sizes are consistent with the KiCad footprint library. The `.gbrjob` files **do not reference the drill files** in `FilesAttributes` — only the 9 Gerber layers are listed. While some fabs auto-detect drill files by naming convention, the missing drill references in the job file could cause confusion during automated CAM processing.

### 4.7 `.gbrjob` Defects (Confirmed by File Inspection)

Both `Hojicha44-Left-job.gbrjob` and `Hojicha44-Right-job.gbrjob` (v0.5.4):

| Defect | Value | Expected |
|---|---|---|
| `Revision` | `"0.5"` | `"0.5.4"` |
| `PadToPad` | `0.0` | ≥ 0.20 mm (or omitted) |
| `PadToTrack` | `0.0` | ≥ 0.20 mm (or omitted) |
| Drill files in `FilesAttributes` | **absent** | PTH + NPTH `.drl` entries |
| Solder mask color | `"Green"` | Verify against intended color |

- The `PadToPad: 0.0` and `PadToTrack: 0.0` values tell the fab there are **zero clearance requirements** between pads and between pads and tracks. While KiCad may emit these as "not specified" semantics, many CAM tools interpret `0.0` literally and skip clearance DRC, potentially accepting boards with shorted pads. The KiCad project's own DRC rules are more restrictive but are not communicated to the fab via the job file.

---

## 5. Firmware Deep Dive — Additional Findings

### 5.1 TRRS Crossover — Intentional (Not a Bug)

The D0/D1 swap between halves (`Left U_L1: pin1→/TRRS_T, pin2→/TRRS_R1`; `Right U_R1: pin1→/TRRS_R1, pin2→/TRRS_T`) is **confirmed intentional**. `check_board.py` lines 76–77 explicitly encode this:
```
UART_L = ("/TRRS_T", "/TRRS_R1")   # U_L1 pin1 (TX) / pin2 (RX)
UART_R = ("/TRRS_R1", "/TRRS_T")   # U_R1 pin1 / pin2 — the CROSSED half
```
The left overlay comment confirms: *"right half swaps at its MCU"* — the crossover is copper-side on the Right PCB so a straight-through TRRS cable connects Left-TX to Right-RX and vice versa. `check_board.py` passes this gate cleanly.

### 5.2 Encoder Rotation Direction — Potential Right-Half Inversion

Both encoders (`ENC_L1`, `ENC_R1`) are placed at **rotation 0°** in the design frame. The encoder footprint is not mirrored — both halves use the same physical pin mapping (`A→/ENC_A_*`, `B→/ENC_B_*`). The ZMK dtsi defines **one shared encoder node** (`left_encoder`) with `a-gpios = <&gpio1 15 ...>` and `b-gpios = <&gpio0 2 ...>`, and both overlays enable it with `&left_encoder { status = "okay"; }`.

- **Concern**: If the encoder is physically oriented identically on both halves (same rotation, not mirrored), then CW rotation on the left knob produces the same A/B phase sequence as CW on the right knob. This is correct **if the knobs are both operated from the same side** (top-down). However, in a split keyboard, the right-half encoder is typically the mirror image, meaning a user's natural CW motion on the right side produces the opposite A/B sequence. Without explicit A/B swap in the right overlay or a mirrored footprint rotation, the right encoder's scroll/volume direction may be **inverted** relative to the user's expectation. *(Verifiable only on physical hardware or by confirming the footprint is geometrically mirrored by `gen_pcb.py`.)*

### 5.3 `build-variants.yml` — Correctly Builds Left Only (by Design)

The `build-variants.yml` comment explicitly states: *"The keymap file is SHARED by both shields (the halves differ by overlay/role…), so one shield per variant is sufficient to prove every keymap source."* This is architecturally correct for ZMK — the keymap compiles identically on both halves, and `build.yml` already builds both shields for the active variant. However:
- The workflow uses `zmkfirmware/zmk-build-arm:stable@sha256:edb1c953...` — this **is** pinned by digest (not mutable), contradicting §2.4's claim. The `build.yml` workflow uses `zmkfirmware/zmk/.github/workflows/build-user-config.yml@edf5c0814fd3...` — also pinned by commit hash. **§2.4 "mutable Docker tag" finding should be downgraded** — the digest pin makes it immutable.
- The `out/firmware/r14/` directory containing pre-built UF2s is a separate concern: its contents may be manually curated and are not CI outputs.

### 5.4 `CONFIG_ZMK_SLEEP` — Still Missing (Confirmed)

`config/hojicha44.conf` has no `CONFIG_ZMK_SLEEP=y`. `config/hojicha44_left.conf` adds USB and battery proxying but also no sleep config. With a `110 mAh` cell and ~1.2 mA idle, expected battery life without deep sleep is ~3.7 days. This is a **significant user experience issue** for a wireless keyboard.

### 5.5 Keymap Variant Findings

The four keymap variants (`mac_left`, `mac_right`, `win_left`, `win_right`) differ only in:
1. **Space/Enter thumb assignment**: `mac_left`/`win_left` put Space on left thumb; `mac_right`/`win_right` swap to right thumb
2. **Home-row mod order**: `mac_*` uses CAGS (Ctrl-Alt-GUI-Shift); `win_*` uses GACS (GUI-Alt-Ctrl-Shift)
3. **L2 clipboard shortcuts**: `mac_*` uses `LG()` (Cmd); `win_*` uses `LC()` (Ctrl)

All four variants share the same `BT_CLR` / `C_AC_SCROLL_*` / `C_PLAY` issues documented in §2.2.

### 5.6 `spec/electronics.yaml` Stale DRC Count

The spec file still states `exact 28 asserted` for `lib_footprint_mismatch` waivers (line 7), while:
- `check_board.py` reports `47 waived refs` per half
- `Hojicha44-Left-drc.rpt` reports `47 DRC violations`
- `tests/spec_checks.cjs` does not cross-check this count against the spec

This is a **documentation/spec drift** issue — the spec's claim of "exact 28" is stale from an earlier revision. The actual 47 waivers are gate-tested by `check_board.py` (which passes), but the human-readable spec is misleading.

---

## 6. Cross-Artifact Consistency

### 6.1 `check_board.py` Gate Results (Clean)

The project's own comprehensive PCB gate (`check_board.py`) runs **all 10 gates** on both halves and reports `CLEAN`:
- ✅ Outline topology: 1 loop, 0 dangling ends (both halves)
- ✅ Fiducials: all inside outline with ≥3.0mm edge clearance
- ✅ USB notch: open bite, pads clear by 38.38mm
- ✅ Pad/via containment: 245 pads, 87/70 vias all inside outline
- ✅ Antenna keepout: all copper clears r=5.0mm from antenna centre
- ✅ TRRS crossover: intentional pin swap verified on board + netlist
- ✅ W1 waiver content: 47 waived refs, 0 pad-content drifts
- ✅ Artifact-vs-model drift: 0 unmatched pads (no hand edits detected)
- ✅ Diode cathode ticks: 22/22 diodes with correct polarity marks
- ✅ Silk-to-edge: min 0.45mm, all clear of 0.20mm threshold
- ✅ Frame gate: T12/T10 holes match plate cutouts, USB notch floors match, port positions match `PORTS`
- ✅ Mirror gate: board and all plate layers (outline, cutout, poron) mirror within 0.01mm

### 6.2 Left/Right Asymmetries

| Metric | Left | Right | Delta |
|---|---|---|---|
| Track segments | 455 | 336 | +119 |
| Vias | 87 | 70 | +17 |
| Committed pads | 245 | 245 | 0 |
| DRC violations | 47 | 47 | 0 |
| Edge segments | 127 | 127 | 0 |

The routing asymmetry (Left has 35% more tracks and 24% more vias) is structurally acceptable — both halves pass all gates — but means the signal integrity and EMI characteristics differ between halves. For a low-speed keyboard matrix this is not a concern.

---

## 7. Summary of Severity Ratings

| ID | Category | Severity | Summary |
|---|---|---|---|
| 1.1 | PCB/Mechanical | 🔴 Critical | Right-half JST header faces into switch matrix |
| 1.2 | Case/Mechanical | 🔴 Critical | Cover magnets fail M4 pull test, no lateral registration |
| 1.3 | Electrical/Safety | 🔴 Critical | No reverse-polarity / overcurrent protection; switch blocks charging |
| 1.4 | Materials | 🟠 High | PORON foam grade unavailable at specified thickness |
| 1.5 | Mechanical | 🟠 High | Zero-margin switch ear seat, 0.14mm diode clearance |
| 1.6 | Serviceability | 🟠 High | JST connector inaccessible with cover installed |
| 1.7 | BOM/Renders | 🟡 Medium | Encoder shaft length / knob contradictions |
| 1.8 | Mechanical | 🟡 Medium | Stock switch leads pierce tub, exposed MCU, recessed power switch |
| 1.9 | Tooling | 🟡 Medium | Fit check PDFs clipped |
| 2.1 | Power/Firmware | 🟠 High | No ZMK deep sleep → 3.7-day battery life |
| 2.2 | Keymap | 🟡 Medium | macOS scroll broken, unguarded BT_CLR, play-only media |
| 2.3 | Hardware/FW | 🟡 Medium | Active UART TX risks TRRS short on insert; weak encoder pull-ups |
| 2.4 | CI | 🟢 Low | Docker tag is actually pinned by digest (downgraded from original) |
| 3.1 | Specs/DRC | 🟡 Medium | DRC count drift (spec says 28, actual 47), ERC date skew, .gbrjob defects |
| 3.2 | Marketing | 🟡 Medium | Keymap visuals out of sync, render/BOM mismatches |
| 3.3 | Compliance | 🟠 High | No LICENSE file, mixed compliance IDs, dirty tree |
| 4.2 | PCB/Via | 🟡 Medium | 0.175mm via annular ring marginal for ENIG; possible 0.075mm ring on 0.5mm drill |
| 4.3 | PCB/THT | 🔴 Critical | TRRS J_*1.R1 pad has **negative annular ring** (−0.100mm) |
| 4.7 | Fabrication | 🟡 Medium | .gbrjob PadToPad/PadToTrack=0.0, missing drill references |
| 5.2 | Firmware | 🟢 Low | Right encoder direction potentially inverted (needs bench verification) |
| 5.6 | Documentation | 🟡 Medium | Spec says "exact 28" DRC waivers, actual count is 47 |
