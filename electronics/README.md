# CODEX KEYBORED Wired Rev A2 — production notes

This directory contains a mechanically compatible **wired prototype**, not a
reverse-engineered copy of the unpublished Work Louder electronics.  The board
uses a clean-room STM32F072/USB-C design and keeps the 90 × 90 mm top-panel outline
so a later ESP32-S3/BLE controller can replace it without changing the housing.

## Electrical architecture

- Six copper layers: `F.Cu`, ground plane, two signal layers, `+5V` plane,
  `B.Cu`.
- STM32F072CBT6 with 128 KB internal flash, HSI48 + CRS crystal-less USB, and
  ME6211 3.3 V LDO. No external flash or crystal is required.
- USB-C device input with two 5.1 kΩ CC resistors and USBLC6 ESD protection.
  The reversible connector pairs cross on `SIGNAL_1` / `SIGNAL_2` before PA11/PA12.
- Twelve Gateron KS-33 / wrk. LP1-family matrix switches plus encoder push.
- Clickable encoder, TTP223-class touch input and two-channel analog joystick.
- 24 SK6812MINI-E pixels through a 5 V-compatible AHCT buffer: 12 per-key,
  nine perimeter underglow and three status LEDs.
- NRST, BOOT0 and SWD bring-up access.

The PCB is generated from `generate_wired_reva.py`; it deliberately does not
depend on a GUI schematic editor. Pad/net assignments in the generated KiCad
board are the electrical source of truth. `generate_jlc_outputs.py` derives the
assembly files from that same board and fails if an unmapped fitted reference is
encountered.

Final automated checks report **0 DRC violations and 0 unconnected nets**.
`docs/schematic.html` is a three-sheet engineering principle schematic derived
from that final connectivity; the IPC-D-356 file is the machine-readable netlist.

## Production files

- `production/codex_micro_wired_revA_gerbers.zip` — JLCPCB fabrication upload.
- `production/codex_micro_wired_revA_jlc_bom.csv` — JLCPCB BOM with LCSC IDs.
- `production/codex_micro_wired_revA_jlc_cpl.csv` — machine placement file.
- `production/codex_micro_wired_revA_turnkey_bom.csv` — both-side BOM including
  consigned/manual controls and factory-programming buttons.
- `production/codex_micro_wired_revA_turnkey_cpl.csv` — all 74 machine and
  manual placement centers.
- `production/codex_micro_wired_revA_consigned_parts.csv` — direct-to-JLC
  sourcing quantities for WRK-LP1, joystick, keycaps, and dial cap.
- `production/CODEX_KEYBORED_RevA2_TURNKEY_SOP.md` — assembly, programming,
  functional test, evidence, and delivery acceptance instructions.
- `production/codex_micro_wired_revA_hand_assembly.csv` — legacy list of parts
  omitted by the saved bottom-only baseline quote.
- `production/codex_micro_wired_revA_drc.json` — final clean DRC report.
- `production/netlist/CODEX_KEYBORED_RevA2.ipc` — IPC-D-356 connectivity.
- `production/schematic/CODEX_KEYBORED_RevA2_schematic.pdf` — principle schematic.

JLC cart job Y5 / `SMT026071763199-3086316A` is Standard PCBA on **both sides**:
five PCBs and two assembled boards. Its automatic matcher uses the catalog-only
`*_jlc_bom.csv` and `*_jlc_cpl.csv` and confirmed all 16 groups. The expanded
`turnkey` BOM/CPL and consigned-parts CSV are factory engineering references for
manual installation of `SW1–SW12`, the encoder, and the joystick/FFC. The
captured base is $193.01; programming, FCT, and manual engineering remain
quote-after-review. These are contract-assembly operations—not customer work.
Review every polarity/rotation and obtain JLC engineering approval before
confirming a paid order.

## Bring-up gate

This is a prototype design and has not been electrically tested on fabricated
hardware. Before attaching a computer, use a current-limited 5 V supply and
verify the 3.3 V rail, inspect for shorts, confirm SWD/NRST, and only then
enumerate USB. The supplied firmware limits
RGB channels to 4/255; still populate the chain last, or depopulate its bulk
capacitor/level shifter for the earliest rail-only bring-up.

The selected LCSC mappings and exact quantities are listed in the BOM. Part
stock and JLCPCB assembly classification can change; a successful web quote is
not an engineering substitute for the vendor's final DFM and placement review.
