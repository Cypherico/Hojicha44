# Hojicha44

A low-profile wireless split keyboard with 44 keys, two knobs, and a gasket-mounted plate.

![Concept render of the two Hojicha44 halves with cream keycaps and a rotary knob on each side](generated/renders/v0.5.1/bright/hero.png)

Set each half where your hands naturally land. The staggered columns follow your fingers, and four keys along each thumb’s arc put everyday controls within reach. Turn either knob for volume, scrolling, or track control, depending on the active layer. Push either one to mute.

[Find the v0.5.3 build files](pcb/MANUFACTURING.md) · [See the keymap](spec/keymap.md) · [Explore the assembly](generated/renders/v0.5.1/bright/exploded.png)

## What’s inside

- **Low-profile Choc v1 switches.** Hotswap sockets let you change the switches without soldering.
- **A floating polycarbonate plate.** PORON pads cradle the switch plate, and magnets hold each removable cover in place.
- **A wireless split.** Two nice!nano v2 controllers run ZMK and link the halves over Bluetooth. Connect to your computer over Bluetooth or plug into the left half for USB.
- **Familiar QWERTY with thumb layers.** Tap home-row keys for letters and hold them for modifiers. The thumb layers bring numbers, symbols, function keys, and navigation into reach. Choose a macOS or Windows/Linux keymap and put Space under either thumb.

## Build one

**v0.5.3 is the engineering sample.** Use the matching PCB, plate and case files from this tree. The published v0.5.2 case can obstruct larger USB-C plugs at the low end of the socket stack. Build one pair and work through the first-article checks before ordering a batch. The images show an earlier CAD revision.

[Parts list](spec/bom.md) · [Fabrication guide](pcb/MANUFACTURING.md) · [First-article checklist](spec/first-article.md)

The design files are available for anyone who wants to inspect or adapt the board. [KiCad projects](pcb/kicad/) · [Ergogen layout](layout/ergogen/config.yaml) · [Case design](case/) · [Hardware audit](audit.md)
