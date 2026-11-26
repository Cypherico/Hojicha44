# Keymap — Hojicha44 (status: FINAL, rev 3 / M3.3)

Reviewed and finalised 2026-10-22. The keymap files are **generated** by
`config/gen_keymap.py` from `spec/layout.yaml` and gated by
`npm test` → `zmk-structure` (which runs the generator's `--check`).
Do not hand-edit `config/hojicha44.keymap`; change `spec/layout.yaml`
or the generator and regenerate.

Locked constraints (from the layout spec):
- QWERTY letters and the digit order 1234567890 are **not moved**.
- Every modifier, Space, Backspace, Tab, `` `~ `` and punctuation has a
  home on the board: nothing lives only inside a catch-22 chord.
- Inspiration: miryoku (home-row mods, thumb blocks, letters left
  plain), Corne/Sofle (digits + F-keys on L1, nav cluster on L2,
  `conditional_layers` adjust), precondition's home-row-mod guide
  (mod-frequency placement and hold/tap tuning).

## 1. Variants

Four firmware variants differ in home-row mod order, which thumb carries
Space, and the modifier used by the L2 clipboard shortcuts
(`spec/layout.yaml` `keymap.variants`).

| variant      | mod order (pinky→index) | Space thumb | for |
|--------------|-------------------------|-------------|-----|
| `mac_left`   | CAGS (Ctrl Alt Gui Shft)| left        | macOS-heavy (default) |
| `mac_right`  | CAGS                    | right       | macOS |
| `win_left`   | GACS (Gui Alt Ctrl Shft)| left        | Windows/Linux |
| `win_right`  | GACS                    | right       | Windows/Linux |

CI builds both halves from the active `config/hojicha44.keymap`. Select a
variant with `python3 config/gen_keymap.py --use win_right` and commit the
result. The static gate accepts an exact generated copy of any of the
four variants. Running the generator without arguments refreshes all
four files in `config/variants/` and restores the default in
`spec/layout.yaml` (`mac_left`). The PCB release manifest covers PCB
artifacts. Record the CI run, source revision, selected variant, and the
hashes of both UF2 files when preparing firmware for a pilot.

Mod-order rationale (precondition's frequency data; both orders keep
**Shift on F/J** — the index fingers, the strongest):
- Windows/Linux frequency: GUI < Alt < Ctrl < Shift → GACS (miryoku's
  order): Ctrl on D/K, Alt on S/L, GUI on A/;.
- macOS adds Cmd (=GUI, second-most-used) and demotes Ctrl → CAGS:
  Ctrl on A/;, Cmd on D/K, Alt on S/L.
Mods are side-specific codes: `L*` on the left hand (A S D F in position
order), `R*` on the right (; L K J).

## 2. Base layer (`default_layer`, layer 0)

```
Q W E R T  ~`    |  |\  Y U I O P
A S D F G  [{     |  ]}  H J K L ;
Z X C V B  -      |  '   N M , . /
Esc  L1  Tab  Space    |    Enter  Bksp  L2  Del
```
All rows use physical left-to-right order. A/S/D/F and J/K/L/;
tap for their letters or semicolon and hold for their variant's modifiers.

- G and H, the other letter rows and the outer punctuation keys send
  ordinary key presses. The semicolon is also a right-hand home-row modifier.
- `[ { ] }` on the inner home keys (unchanged from rev 2), `` ` ~ `` on
  the inner top (unchanged), **`-` on the left inner-bottom and `'` on
  the right inner-bottom are NEW (rev 3)** — Tab and Esc moved to the
  thumbs, so the "third symbol" of those columns is now useful on the
  base layer: `-` beside `, .` for ranges/negatives, `'` for quotes.
  The shifted forms (`_` `"` via the mods/Shift) need no dedicated keys.

### Thumbs — measured placement

Thumb-joint circle R = 91.2 mm; the four keys sit ~13.9° apart: the
innermost keys are the arc's ends (21° off neutral = strained to hold,
fine to tap), the middle two are 6.66°/7.25° off neutral (comfortable).
Therefore the rare keys take the extremes, the **holds** take the
comfortable mids, the frequent primaries take the inner palm-side:

| left (outer→inner) | right (outer→inner) | why |
|--------------------|---------------------|-----|
| Esc                | Delete              | rare + recoverable = outermost |
| **L1 hold**        | **L2 hold**         | long holds want low strain |
| Tab                | Backspace           | adjacent to the primary thumb keys |
| Space / Enter*     | Enter / Space*      | Space on the palm-side inner |

(*left/right per the space-hand variant: left-space is the spec's
canonical order; right-space swaps Space↔Enter between the two
innermost positions, everything else fixed.)

## 3. Home-row mods — ZMK's "timeless" recipe

One behavior per hand so the hold-trigger lists can differ:

```
hml/hmr: zmk,behavior-hold-tap
  flavor = "balanced"          hold also fires when another key resolves
  require-prior-idle-ms = 150  fast rolls (of letters) resolve to taps
  tapping-term-ms = 280        high: the POSITIONAL triggers decide, not the timer
  quick-tap-ms = 175           tap-then-hold auto-repeats the LETTER
  bindings = <&kp>, <&kp>
  hold-trigger-key-positions = <the OTHER hand's 22 positions>
  hold-trigger-on-release      lets same-hand mod+key combos still work
```

Sourced from ZMK's own hold-tap documentation ("timeless home row
mods", balanced + require-prior-idle + positional triggers), which is
also what v0.3's binding schema supports (verified against the pinned
v0.3 `zmk,behavior-hold-tap` YAML: `tapping-term-ms`, `quick-tap-ms`,
`require-prior-idle-ms`, the flavor enum, all present).

How it resolves:
- An A pressed just after another letter resolves to a tap during the
  prior-idle interval. O is on the right hand, so an A started from idle
  followed by O can trigger a modifier hold if they overlap.
- hold A, press K: K is other-hand list → hold fires on K's release
  (hold-trigger-on-release) → instant cross-hand shortcuts ✓.
- For a same-hand shortcut, first hold the modifier past its tapping term
  and then press the other key. A holds Ctrl on macOS variants and GUI on
  Windows/Linux variants. A fast same-hand roll should emit the letters.
- typist rolls like "the quick": require-prior-idle keeps zoom-mid-roll
  taps as taps even past 150 ms.

The trigger position lists are COMPUTED (the other hand's 22 of 46
positions, row-major interleaved), not hand-typed — the gate asserts
them against the layout.

## 4. L1 (lower, layer 1) — editing numbers: digits, shifts, F-keys

```
 1  2  3  4  5  6   |  7  8  9  0  -  =
 !  @  #  $  %  ^   |  &  *  (  )  _  +
 F1 F2 F3 F4 F5 F6  |  F7 F8 F9 F10 F11 F12
 thumbs: transparent (the row keeps working), L1 encoder = scroll
```
Read each row from left to right across the deck. Minus/equal fill the
last two positions after 0, and shifted symbols sit directly below
their unshifted counterparts. The encoder sends vertical HID mouse-wheel events.

## 5. L2 (raise, layer 2) — navigation, media, BT

```
    ·    P0  P1  P2  P3  P4 |   ·   End  Home  Caps  Ins  PrtSc
 MUTE  PREV PLAY/PAUSE NEXT V+ V- |   ·    ·    ·     ↑     ·    PgUp
 UNDO  CUT   COPY PAST  ·  · |  Bksp Del   ←     ↓     →    PgDn
 thumbs: transparent; L2 encoder = prev/next track
```
Left half = media/BT (Sofle's raise pattern; BT profiles 0–4 for the
split's central+peripheral+hosts), right half = an inverted-T arrow
cluster on the strong columns with PgUp/PgDn on the outer rail and
Home/End/Ins/PrtSc/Caps on the top rail. Delete/Backspace repeat here so
the editing trio lives under one thumb-hand reach.

## 6. Adjust (layer 3, the L1+L2 chord)

```
conditional_layers: if-layers = <1 2>, then-layer = <3>
- Bootloader at W and system reset at E.
- Clear the active Bluetooth profile at R while holding both layers.
- All other key positions are unused.
- encoder = volume (harmless while reaching for boot)
```

## 7. Encoder

| layer | rotation | push |
|-------|----------|------|
| base  | volume ± | Mute (both halves) |
| L1    | scroll ± | Mute |
| L2    | prev/next track | Mute |
| adjust| volume ± | Mute |

The composite scan adds the two encoder pushes after the existing matrix
positions. The split sends the right push position to the central,
which resolves Mute for both encoders on every layer.

L2 uses Command+Z/X/C/V in the macOS variants and Control+Z/X/C/V in
the Windows/Linux variants.

## 8. Gates

`npm test` → `zmk-structure` shells `python3 config/gen_keymap.py
--check`, which:
1. re-derives every binding from `spec/layout.yaml` and byte-compares
   the tracked active keymap + all 4 variants (a legend edit without
   regeneration, or vice versa, fails);
2. structurally validates each emitted keymap: exactly 4 layers × 48
   bindings matching the dtsi `RC()` count, one real `sensor-bindings`
   per layer (`&trans`/`&none` there is rejected by pinned v0.3 and
   would kill CI), mods exactly on the 8 home positions with the right
   variant codes, Space/Enter on the variant's thumb pair, `&mo 1`/`&mo
   2` fixed, hold-trigger lists == the other hand's 22 positions,
   hold-trigger-on-release present, the L1+L2→3 chord present, and both encoder pushes bound to Mute on every layer.

Negative controls (proven non-vacuous 2026-10-22, each reverts to
CLEAN): wrong tap keycode → caught as position drift AND stale-file;
deleted binding → incorrect layer length; legend drift in the spec → both halves
stale; truncated hold-trigger list → caught; thumbs canonical-order edit
→ spec-parse assert.

## 9. First-article bench (firmware half)

See `spec/first-article.md` §firmware-bench; the items: per-half matrix
type-through, per-half encoder push = Mute, per-layer encoder direction
check, home-row hold/tap on all 8 positions × both flavors of muscle
memory (slow deliberate hold, fast roll), same-hand mod chord
(press-hold-past-term), the L1+L2 chord → Adjust, and the bootloader key
with a re-flash before anything else ("reply-btn" recovery proven).
