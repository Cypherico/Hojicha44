"""Hojicha44 case parameters (design constants; sources annotated in-line).

Frame: KiCad board frame, mm. z = 0 is the PCB TOP surface.
"""
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---- stack (spec/case.md "Stack", all per half) ----
# SUPPORT STRATEGY (b), rev-2: the plate now carries the Choc v1 clip
# engagement (14.0mm cutout, 1.2mm plate) and sits at the Choc gap of
# 1.00mm above the PCB top, so the whole top of the case comes DOWN
# 1.30mm (plate top 3.50 -> 2.20).  The diodes stay on the PCB's top
# side and the plate relieves 0.55mm over them (measured SOD-123 top
# = 1.26mm, part tolerance up to 1.40; see plate/gen_plate.py).
PLATE_UNDER = 1.00  # PCB top -> plate underside (Choc v1 clip band:
                    # the plate must sit between the clip lip <=1.3 and the
                    # 14.8 ears at 2.2 -> 1.0 gap + 1.2 plate = 1.0..2.2)
PLATE_T = 1.2       # plate thickness (Choc v1 clip engagement)
FOAM_T = 3.0        # poron pads under each tab (bottom gaskets)
TOP_FOAM_T = 1.5    # poron pads above each tab (top gaskets).  Thin
                    # STOCK on purpose: the top gap is now 1.28mm at
                    # the same 15% preload, so the top case sits just
                    # above the plate instead of 2.5mm above it.  The
                    # user review called the old 2.5mm foil stack
                    # "massive spaces above the gaskets".
PRELOAD = 0.15      # bottom-gasket assembly compression (spec: 0.15-0.20)
TOP_PRELOAD = 0.333 # top-gasket compression: the review wanted the caps
                    # to stand proud, so the 1.5mm top foam runs at 1/3
                    # compression (inside the spec's <=50% ceiling) and
                    # the whole top case sits at 2.20+1.00
TAB_W = 10.0        # tab width (plate/gen_plate.py)
TAB_L = 5.0         # tab protrusion past outline

PLATE_TOP = PLATE_UNDER + PLATE_T          # +2.20 (was 3.50)
# Tab-support shelf: bottom foam compressed under the tab.
# SHELF_Z = PLATE_UNDER - FOAM_T*(1-PRELOAD) = 1.00 - 2.55 = -1.55
SHELF_Z = PLATE_UNDER - FOAM_T * (1 - PRELOAD)   # = -1.55
# Top gap = compressed top foam between plate top and lip underside:
TOP_GAP = TOP_FOAM_T * (1 - TOP_PRELOAD)         # = 1.00
# Depths below the nominal PCB top. The Choc socket model reaches
# -3.468 (1.18 mm clear of the floor), the JST -3.40 and the encoder
# -3.65. Stock Würth switch leads reach -4.70..-5.10. For this tub,
# trim them to z >= -3.25 after soldering. Check the finished joints
# and the clearance under an encoder press on the first article.
POWER_LEAD_MAX = 3.25  # finished lead and solder measured from carrier top
POWER_Z_TRAVEL = 0.40  # verified geometric reserve below nominal carrier height
FLOOR_CLEAR = 1.0  # minimum slide-switch clearance after the travel reserve
FLOOR_Z = -3.65 - FLOOR_CLEAR  # floor top surface = -4.65 (spec ruler above)
FLOOR_T   = 1.7   # floor slab (MJF PA12; flat, braced by tab pockets)
                  # first-article caliper re-measures the family bounds

# ---- outer skin (v3: uniform dilation, Sofle/Corne/Lily lesson) ----
# ONE constant offset of the PCB RIM (gen_case.py). Notches shallower
# than the offset (USB ~5.45 deep, TRRS channel) fill in and vanish
# from the silhouette — breaching them is the port slots' job.
# STRENGTH HISTORY: at 6.0 the wall over every tab tip measured 0.5
# (skin rim+6.0 vs cavity tab tip rim+5.5) — 1-2 FDM extrusion lines
# over an 11mm span at each of 8 stations; the whole case thickened
# (user-sanctioned) to close the pockets without creating local
# swells (v2 sin, rejected).
CASE_OUTSET = 8.2   # wall over tab tip = 8.2 - TAB_L - RIM_CLEAR = 2.7
                    # (6-review audit 2026-10-20: 7.1 gave 1.595 measured
                    # wall — under both the 1.6 design floor and the MJF
                    # 2.0 pass; 8.2 clears them with margin and grows the
                    # band to 7.7 so MAG_STATION_BAND 7.5 fits with 0.2
                    # slack and magnet webs reach 1.6)
SKIN_MIN = 1.0      # min material between any pocket corner and the skin
SKIN_STEP = 1.0     # ring resample step for the outer skin (folds gone;
                    # verified crossing-free at 1.0/0.6/0.4)
MIRROR_AX = 145.75  # shared left/right mirror axis: RIGHT = 2 * MIRROR_AX
                    # - LEFT in frame coordinates (291.5 - x). Every
                    # per-half constant below is asserted or derived with
                    # this (6-review audit 2026-10-20: asymmetric
                    # derivations produced 6/7 magnet stations and +0.5mm
                    # plate keep-zone drift; symmetric sources replaced
                    # them).
TOP_LIP_Z = 3.20    # lip at plate top + TOP_GAP (2.20 + 1.00):
                    # the 1.5mm top foam runs at 33% compression and the
                    # top case sits right above the plate, so the caps
                    # stand 2.4mm proud of the 2.0mm top plate instead of
                    # barely 1.6mm. The tie TOP_LIP_Z == PLATE_UNDER +
                    # PLATE_T + TOP_GAP is enforced by
                    # tests/spec_checks.cjs (stack-ties).
#   NOTE: the USB-C module stack tops ~7.7 above the PCB, the EC11 body
#   tops ~5.2 and its shaft ~24.5 — the COVER carries windows for both
#   (gen_cover.py).

# ---- fastening (REVISED: no visible fasteners on the exterior) ----
# Rev-1 tub: friction fit (plate + poron preload holds the assembly).
# Future top cover: recessed magnets or internal clips — decided at
# cover-design time, NOT screws/bosses through the skin.
#   OPEN (cover): cover MUST carry the W1/W2 windows + USB notch + TRRS
#   channel openings (they exist in the plate outline today; do not lose
#   them in the cover) AND the plug passages above the slots — the USB
#   overmold tops ~3.2 and the socketed module ~7.7, both above the lip;
#   and it must keep ANT_R_MM + ANT_CASE_CLEAR clearance over the
#   antenna zones in case/params.py below.

# ---- tab pockets (lands.json roots; jackets swallow tab + both foams) ----
POCKET_CLEAR = 0.5        # side clearance in the pocket
POCKET_IN = 1.0           # pocket starts 1mm inside the rim line
POCKET_OUT = TAB_L + 0.5  # pocket nose past the tab tip
POCKET_BOT = SHELF_Z       # pocket floor IS the shelf (foam rests on it)
POCKET_TOP = TOP_LIP_Z     # open to the top (cover presses upper foam)

# ---- port mouths (v3.4: shaped bores, NOT full-height wall slots) ----
# The rim's USB notch (11 wide) fills in under CASE_OUTSET dilation, so
# ports still breach via explicit bores anchored on the RIM, SLOT_IN
# into the cavity through the skin and past it, and the outer extent
# stays MEASURED (gen_case.py marches the bore face outward until it
# clears the skin ring across the whole width + margin). v3.3 closed
# the same contract with full-wall 14x11.6 / 9.5x11.6 rectangles the
# user rightly called "gaping"; v3.4 shapes each mouth to the plug:
#   USB  = 14.0-wide port with 1.2 fillets UNDER it only (flat top,
#          z band 2.0..lip). Plug stack math: sockets ~4.5 (measured —
#          the old ~3.0 figure was wrong) -> module 4.5..7.7 ->
#          receptacle mid ~6.1 = the plug AXIS rides AT the lip plane;
#          overmold tops ~3.2 ABOVE
#          the lip (~9.2 abs), bottom ~2.8, so only 2.8..lip of the
#          plug crosses the wall band — its neck above the lip rides
#          through the open top plane, which the future COVER carries.
USB_MOUTH_W = 14.0
USB_MOUTH_Z0 = 2.0
USB_MOUTH_R = 1.2

# The plug boot enters an open bay. The case floor stays continuous.
TRRS_BAY_W = 10.5
TRRS_BAY_Z0 = -2.85
TRRS_BAY_R = 0.60
TRRS_JACK_AXIS_Z = 2.50
TRRS_BODY_WIN = (119.70, -25.60, 135.30, -18.40)

# ---- power-switch actuator window (v3.5, north rim) ----
# WS-SLTV (450301014042, Wuerth datasheet + KiCad footprint name
# 10x2.5x6.4): body 10 x 2.5, body top z 5.0 above the PCB, red
# actuator 1.4 tall on top (z 5.0..6.4), slide travel 0.8/side along
# the 10mm axis, flick = fingernail entering the aperture from above.
# Placement: footprint at (106.3,51) Left / (185.2,51) Right (M3:
# origin centred on this window; the M2 "2mm WEST" shift ran the wrong
# way and left the blade band wholly behind the wall); the north rim
# runs a STRAIGHT plateau y=58 across x 97.5..110.5 (frozen in the
# ergogen outline — does not follow the switch), so the whole switch
# (its most outboard point y=52.25) sits >=6.25mm INSIDE the cavity — no bodyor
# pin ever crosses the wall band. The mouth is therefore only the
# actuator aperture, and it must NOT span the 7.0 wall band fully: a
# full-width cut breaks the ring into two disconnected arcs (2 solids).
PWRSW_MOUTH_W = 5.0    # lever (~3 swept with throw) + nail entry; ALSO
#   the ring-safety cap: (7.0 band - w)/2 >= 1.0 web.
PWRSW_MOUTH_Z0 = 4.3   # 0.7 below the body top for nail entry angle.
#   With the thin-cover lip at 3.48 this is ABOVE the tub, so the tub
#   has no pwrsw bore at all (compute_ports marks it skipped); the
#   COVER carries the body window + nail slot (PWRSW_WIN/PWRSW_NAIL_W).
PWRSW_COVER_IN = 1.6   # cover slot starts this far outboard of the port
                       # anchor, leaving the 1.1mm inner web next to the
                       # cavity edge (W1 must stay the ring's ONLY full
                       # radial severance — single-solid gate)
PWRSW_MOUTH_R = 0.8    # bottom fillets (molded look, matches USB)

# ---- plug envelopes the census prints against (gen_case.py table) ----
# Same sources as the port comments above: USB housing from the plug
# stack math, boot/face from the vendored PJ-320A STEP, lever from the
# Wuerth WS-SLTV datasheet (blade ~2.0 + travel 1.6; verify first art.)
USB_HOUSING_W = 12.35       # overmold body widest around the axis
PWRSW_LEVER_SWEEP = 3.6     # actuator blade ~2.0 + travel 1.6 (verify)

# ---- retention magnets (v3.5 tub + ring cover, recessed both sides) ----
# Zero-gap stack: tub magnet faces flush at TOP_LIP_Z, ring magnet faces
# flush at the cover underside — adjacent faces MEET at the lip plane, a
# rigid stop, so the ring bottom cannot pass the lip plane and the
# poron top-pad preload stays purely geometric (uncompressed 6.5 vs ring
# bottom 6.0 = the designed 16.7%); the ~3-4 kg magnet pull is reacted
# by the band-face contact, NOT by crushing the foam. 4x2 N52 pairs:
# ~0.4-0.6 kg/pair x 8 >= 3 kg vs a ~200 g half; nothing pokes outside.
MAG_DIA = 4.3          # pocket bore for a Ø4.0 magnet: 0.15/side glue film
                       # (post-audit P1 full adoption; Ø4.2 was starved after
                       # FDM shrink — see spec/case.md retention)
MAG_DEPTH = 2.2        # TUB pocket depth (2.0 magnet + glue line)
COVER_MAG_DEPTH = 0.7  # COVER pocket depth (thin-cover round): cover-
#   side magnets are Ø4x0.5 -> pocket floor 2.0-0.7 = 1.3mm, the same
#   floor the T4 review demanded, on a 2.0mm cover. Faces still meet
#   exactly at the lip plane; Ø4x2 (tub) vs Ø4x0.5 (cover) is
#   asymmetric-tolerant (force drops, 8 pairs must still cover the
#   ~200 g half; the rigid zero-gap stop is the face plane, not the
#   pull; first-article pull test re-gates the thinner cover magnet).
MAG_STATION_BAND = 7.5 # local band needed: pocket + >=1.6 web both faces
                       # (6-review audit 2026-10-20: the web >= 1.6 reviewer
                       # floor is NOW met in-band — webs (7.5-4.3)/2 = 1.6,
                       # straight-rim band is 7.7 = OUTSET 8.2 - RIM 0.5)
MAG_WEB_MIN = 1.6      # ABSOLUTE magnet-pocket web floor (reviewer floor).
                       # The derived gate ((MAG_STATION_BAND - MAG_DIA)/2)
                       # shrinks with the band it polices, so it can never
                       # catch a thinner pocket — this constant can
                       # (3-review audit 2026-10-21: all three reviewers
                       # found the derived floor unenforceable).
WALL_MIN_ABS = 2.0     # ABSOLUTE tub wall floor (the MJF 2.0 print pass).
                       # The derived gate (OUTSET - TAB_L - RIM_CLEAR - 0.3)
                       # moves with OUTSET and therefore cannot detect an
                       # absolute thinning (same audit).
MAG_MIN_SEP = 14.0     # arc separation between stations
MAG_MAX_STATIONS = 8
MAG_MIN_STATIONS = 8   # retention gate on station count (audit: the doc
                       # chain promises 8/half — BOM 16+16, first-article
                       # pull math; the old per-half generation yielded
                       # 6/7 and Left sat ON the 1.5 kg pull gate)

# ---- port anchors (slot frame anchors, KiCad frame) ----
# SOURCE OF TRUTH for both the case bores and the plate's port
# keep-rects (plate/gen_plate.py asserts every anchor sits inside
# its keep-rect — the two files cannot drift apart silently).
# usb   = points.yaml helper usb / mirror_usb (mcu + [0,17.95])
# trrs  = jack MOUTH centres derived from the layout trrs anchor
#         (130.5/-22) via the PCB placement chain: anchor ± 2.05
#         (gen_pcb.py TRRS rot-90 dX) + physical mouth at native y=-2.0
#         -> 134.55 (L) / 156.95 (R), rounded.
# pwrsw = the ACTUATOR MOUTH centre on the north rim plateau, NOT the
#         switch footprint (SW_LPWR1/SW_RPWR1 sit at 106.3/185.2, 51 after
#         M3 — origins centred on this fixed window, band = origin +/-1.8
#         vs the 5.0-wide mouth = 0.70/side; M2's "2mm WEST" shift had run
#         the WRONG way and left the band wholly behind the west/east
#         wall). The mouth itself cannot move: SAT-constrained,
#         pocket >=3.2 / USB ~1.8 margins. The plateau is the raw
#         Edge.Cuts line y=58.0 across x 97.5..110.5 (mirror 181..194,
#         frozen in the ergogen outline), so the frame is axis-aligned
#         EXACT (no resample-phase wobble): a wobbly +/-.5 anchor x
#         swings the slot into tab-4's pocket (east edge x=100.59; SAT
#         floor 3 wants west edge >= 103.6) or onto the notch shoulder
#         (110.5). The mouth centre 106.3 clears both; blade/throw stays
#         exposed (body spans x 101.3..111.3 / 180.2..190.2).
# Slots are explicit rects whose outer extent is measured to actually
# breach the skin.
# The trrs pair is mirror-exact to 0.01 (the 2026-10-21 audit found the
# 1-decimal rounding had broken the mirror by 0.1mm: 134.6 <-> 156.9,
# not 157.0 — the derived pair is 134.55 / 156.95).
PORTS = {"Left": {"usb": (118.0, 49.95), "trrs": (134.55, -22.0),
                  "pwrsw": (106.3, 58.0)},
         "Right": {"usb": (173.5, 49.95), "trrs": (156.95, -22.0),
                   "pwrsw": (185.2, 58.0)}}

# ---- ring cover (v3.5: flush bezel ring on the lip) ----
# Underside = TOP_LIP_Z (presses the top poron), top = +COVER_T (stays
# below the keycap field ~9.5-10.5). Openings: W1 = USB plug
# neck/housing band to its top ~9.2 (full-depth pass), W2 = TRRS boot
# swing past the lip (top ~6.75: the Ø9.5 cylinder cut reaches 7.25 and
# its chord in the 6..9 slice stays <=6.42 at the lip plane so the ring is
# NOT split),
# the pwrsw flick slot, and the magnet pockets. Outer face = the skin
# face FLUSH (an intentional lid seam).
COVER_T = 2.0          # 3.20..5.20 (TOP_LIP_Z + 2.0): a thin top
                    # plate that also covers the MCU/encoder strip and
                    # the key field between caps (key-field opening +
                    # component windows), instead of a bare rim ring.
                    # 1.3 floor over the 0.7 magnet pockets
# ---- top-cover openings (thin top plate, gen_cover.py) ----
# The cover is no longer a bare rim ring: it also spans the key field,
# so it hides the plate/switch bodies between caps and covers the
# MCU/encoder wiring strip. Openings are fixed here so the render and
# the CAD read the same numbers:
#   key field = union of the 22 cap footprints (KLP Lamé Saddle/Thumb
#               are all 17.48x16.48 in plan) dilated CAP_CLEAR/side —
#               1.0 makes the 19mm-pitch caps merge into ONE opening
#   MCU       = module courtyard + margin; the south edge is pulled to
#               y=12.0 so the cover is >=3mm (in 3D) from the antenna
#               centre at (118, 15.55) (ANT_CASE_CLEAR)
#   encoder   = EC11 body 16.2x12.4 + 0.2/side
#   USB/TRRS  = the SAME compute_ports passages as the tub (shared
#               anchors; TRRS is now an edge notch because the lip is
#               below the bore top)
#   pwrsw     = body window + nail slot to the north skin
CAP_FOOT_W = 17.48     # KLP Saddle / Thumb plan footprint (measured)
CAP_FOOT_H = 16.48
CAP_CLEAR = 1.5        # key-field opening clearance per side. gen_cover
                       # fills the union's enclosed holes, so the
                       # staggered caps become ONE opening. 1.0 merged
                       # COLUMNS only (17.48+2 = 19.48 > 19) and left
                       # 0.52mm ROW webs ("ridges and dots", user
                       # review); 1.5 merges rows too (16.48+3 = 19.48
                       # > 19) so the opening is one clean field. The
                       # cover is FLAT (no-indent, user review round 2):
                       # a 0.4mm top-edge chamfer is the only
                       # embellishment; caps stand full-height proud.
CAP_ROUND = 2.0        # cutter corner radius (molded look)
JST_SERVICE_W = 4.50
JST_SERVICE_L = 7.00  # plug, wires and straight withdrawal beyond header face
JST_PLATE_WIN = (115.85, 4.30, 131.65, 9.65)
JST_WIN = (115.85, 3.30, 134.50, 10.70)  # header, plug and tool access
MCU_WIN = (106.5, 12.0, 129.0, 48.6)      # x0, y0, x1, y1
ENC_WIN = (111.5, -14.35, 124.5, -1.65)   # x0, y0, x1, y1: EC11
                       # BODY at the cover band (measured 12.0x11.7 at
                       # z 3.2..5.2, centred (118,-8)) + 0.5/side. The
                       # old 17.2x13.2 window exposed the whole part;
                       # this one covers the rectangular terminal base
                       # and leaves only the body top + bushing/shaft.
PWRSW_WIN = (101.0, 49.2, 111.6, 70.0)    # clears the 10×2.5 body at (106.3, 51)
                       # extended through the north skin in ONE clean
                       # notch (a 5mm nail slot beside the USB slot left
                       # an enclosed 3x7mm cover island between them).

SLOT_PAST_TOP = 0.5    # bore cut extends past the case top plane so the
#   mouth's top face is the solid's own face, not a coincident-face seam
SLOT_IN = 2.0          # bore starts inside the cavity (anchored in material)
SLOT_OUT = CASE_OUTSET + 1.5   # scan start / minimum outer extent
SLOT_BREACH_MARGIN = 1.0   # extra travel past the skin along the face

# ---- antenna keepout (spec/electronics.yaml antenna_keepout block) ----
# NB: the keepout circle drawn on each board's Cmts.User has radius 5.0
# (pcb gen_pcb.py ANT_R_MM) at the antenna centre; this file must match.
# CONSUMED by the case gate (envelope rings + wall-distance floor).
# Antenna centres = layout helper points antenna/mirror_antenna
# (mcu + [0, -16.45]) in layout/generated/v2/points/points.yaml.
ANT_R_MM = 5.0
ANT_CASE_CLEAR = 3.0   # "no case material within 3mm" (electronics.yaml)
ANTENNA_L = (118.0, 15.55)
ANTENNA_R = (173.5, 15.55)

# ---- internals carried over ----
RIM_CLEAR = 0.5   # plate-to-wall clearance (spec/case.md stack table)
