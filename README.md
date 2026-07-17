# CODEX KEYBORED — Work Loafer Edition, Rev A2

This folder contains a reproducible Fusion 360 model, CNC handoff, mechanically
compatible wired KiCad PCB, JLCPCB assembly outputs, and STM32F072/TinyUSB firmware for an
independent private prototype of OpenAI Supply Co × Work Louder
`kbd-1.0-codex-micro` (Codex Micro). The reconstruction is derived from official
product renders and Creator Micro 2 platform documentation; it is not an
official CAD/electronics release.

The parody production identity is printed on the board as **CODEX KEYBORED /
WORK LOAFER EDITION**. The final 90 × 90 mm, six-layer board has 0 DRC
violations and 0 unconnected nets; its Gerbers, drill files, IPC-D-356 netlist,
BOM/CPL, three-sheet principle schematic, and build-verified firmware are under
`electronics/production`, `output/pdf`, and `firmware/stm32/release`.

The signed-in JLC cart contains four CNC parts, the retained Y4 bottom-side
baseline, and a new Y5 turnkey job with five PCBs plus two both-side Standard
PCBA units. On 2026-07-17 JLC calculated the Y5 base at **$193.01** ($81.40 PCB
+ $111.61 PCBA). Function testing, programming/manual work, the PCBA remark,
and consigned-part procurement remain quote-after-review, so that figure is a
floor rather than the price of a finished device. This is a first-article
prototype: fabricated hardware has not yet completed electrical bring-up or
dimensional fit-check.

## Turnkey electronics route

The customer is not expected to solder switches or program the MCU. The intended
handoff is one complete PRIMARY unit and one electrically tested spare PCBA:

- JLC places all SMD parts on both sides, including the top-side USB-C port.
- Work Louder WRK-LP1 switches and the Alps planar joystick are shipped directly
  into JLC's consigned-parts inventory.
- JLC manually installs the twelve switches and encoder, mechanically fits the
  joystick/FFC, and installs caps on the PRIMARY unit after electrical test.
- JLC programs the STM32F072 from the release BIN/HEX and runs the supplied
  browser-based 20-control USB HID acceptance test plus RGB inspection.
- The customer only closes the CNC enclosure with the controlled screws after
  first-article fit approval.

The automatic JLC matcher uses `*_jlc_bom.csv` and `*_jlc_cpl.csv` for the 16
catalog groups. The expanded `*_turnkey_bom.csv`, `*_turnkey_cpl.csv`, consigned
parts CSV, and `CODEX_KEYBORED_RevA2_TURNKEY_SOP.md` are the engineering/manual
assembly handoff attached to the job. The Y4 bottom-only cart screenshots are
retained as historical quote evidence and should not be mistaken for Y5.

## Confidence legend

- `CONFIRMED` — explicitly published by OpenAI, Work Louder, or Framer.
- `MEASURED` — scaled from the official near-orthographic top render using the
  confirmed 19.05 mm key pitch.
- `INFERRED` — a manufacturing placeholder that must be checked against a
  physical unit or internal photographs before production.

## Mechanical datum set

| Parameter | Value | Confidence | Basis |
|---|---:|---|---|
| Key pitch | 19.05 mm | CONFIRMED | Work Louder MX keycap specification |
| Installed keyboard switches | 12 | CONFIRMED | Visible layout and Framer CM-2 specification |
| Total mechanical switch inputs | 13 | CONFIRMED | Work Louder counts the encoder push as a key |
| Outer envelope X/Y | 108 × 108 mm | MEASURED | Official top render, scaled from key centers |
| Top PCB/panel outline | 90 × 90 mm | MEASURED | Official top render |
| PCB screw pitch X/Y | 78 × 78 mm | MEASURED | Official top render; provisional ±0.5 mm |
| Outer corner radius | 14 mm | MEASURED | Official top render |
| 1U cap plan size | 17.6 × 17.6 mm | MEASURED | Official top render |
| 2U cap plan size | 36.55 × 17.6 mm | MEASURED | Pitch minus the measured inter-key gap |
| Top PCB thickness | 1.6 mm | INFERRED | Standard production PCB thickness |
| Upper housing thickness | 10.3 mm | MEASURED | Official front/side renders and JLC machinability pass |
| Circular aluminum bottom | Ø94 mm, 3.8→12.0 mm wedge, 5° | MEASURED/INFERRED | Side profile scaled from official render; CNC stock/angle production-ready |
| Battery envelope | 58 × 42 × 6 mm | INFERRED | Packaging volume for 1900–2100 mAh LiPo |
| Lower controller PCB | 68 × 25 × 1.0 mm | INFERRED | Packaging placeholder only |
| Planar joystick body | 19.6 × 18.1 × 4.9 mm | CANDIDATE | Alps RKJXY100000A published dimensions |

The coordinate origin is the device center. `+Y` points toward the rear edge
(the arrow printed at the top of the official PCB), and `+Z` points upward.

## Layout

The controls occupy a 4 × 4 pitch grid with centers at ±28.575 mm and
±9.525 mm:

- Row 1: clickable encoder, 2 translucent agent keys, planar joystick.
- Row 2: 4 translucent agent keys.
- Row 3: 4 white command keys.
- Row 4: capacitive touch sensor, centered 2U push-to-talk key, 1U key.

This gives 12 conventional keyboard switches. Work Louder's published “13
mechanical switches” count is reconciled by the encoder's push switch, which is
also visible in the official CM2 firmware self-test.

## Confirmed internal architecture

Work Louder's own reset instructions describe a top PCB and a lower internal PCB
connected by a flat-flex cable. Inspection of Work Louder's published Creator
Micro 2 diagnostic firmware additionally confirms:

- ESP32-S3 target, 16 MB flash, ESP-IDF 5.3.2 bootloader;
- USB through TinyUSB and Bluetooth LE through NimBLE;
- MAX77972 battery-management/fuel-gauge family;
- separate GPIO functions for rear button, USB detect, layer LEDs, touch pad,
  encoder, top-board power, and charge enable;
- three BLE pairing slots;
- a keyboard matrix visually arranged 2 / 4 / 4 / 2, plus the encoder push as
  the thirteenth mechanical input. The diagnostic firmware's 2 / 4 / 4 / 3
  self-test row is therefore interpreted as including that encoder push.

No Work Louder / Creator Micro 2 grantee record was found in the official FCC
grantee registry, and no Work Louder / Creator Micro 2 record was found in the
Canadian ISED Company Name or Radio Equipment List searches. The production
device may therefore rely on modular radio certification, but the exact module
cannot be established from public exterior renders.

## Fusion model contents

`fusion/build_codex_micro_mechanical.py` creates one top-level assembly where
the active Fusion document supports occurrences. In a modern Fusion Part Design
document (which deliberately permits only one component), it creates the same
separate, well-named BRep bodies in the root component instead:

- translucent rounded PMMA/PC housing ring;
- circular 5° aluminum wedge and annular anti-slip pad;
- 90 mm top PCB/panel with four mounting holes;
- four standoffs and M3-class screw-head envelopes;
- 12 switch envelopes, 11 × 1U caps, 1 × 2U cap, and 2U stabilizers;
- encoder/knob, joystick, touch sensor, three layer LEDs;
- USB-C and rear-button envelopes;
- lower PCB, LiPo, and FFC keep-out placeholders.

The reproducible source script intentionally does **not** save an arbitrary
active document. The production bodies and verified layout migration have been
applied and saved to the user's Fusion document named `Codex`. In an Assembly
document the builder replaces only its own `Codex_Micro_Mechanical_v0_1`
occurrence; parameters prefixed `cm_` are updated in place.

`fusion/Codex_Micro_RevA.f3d` is the exported archive of that saved `Codex`
document and is the portable Fusion handoff. The Python scripts remain the
reproducible source for rebuilding and auditing the geometry.

## Manufacturing direction

For a one-off copy, the original clear housing geometry can be machined from
cast acrylic/PMMA or polycarbonate. A wood version should use the same external
geometry in stable hardwood or laminated birch, with a separate frosted acrylic
light pipe below the top PCB; wood alone will block the official underglow.
Leave at least 2.5–3.0 mm wall thickness around the internal pocket and add
0.15–0.25 mm radial clearance around the 90 mm top panel after measuring the
actual CNC process.

The vendor handoff is completed by `cnc/drawings/CM2_CNC_Drawing_Pack_RevA.pdf`
and four per-part drawing PDFs. They control material, finish, critical Rev A
dimensions, the 5° wedge requirement, and first-article inspection notes while
the STEP files remain authoritative for unlisted geometry.
