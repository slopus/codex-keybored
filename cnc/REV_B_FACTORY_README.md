# CODEX KEYBORED — Mechanical Rev B factory handoff

This package is the controlled mechanical first-article set for one device.
Submit four custom parts to JLC CNC and purchase one standard continuous grip
ring from JLCMC. Do not substitute individual rubber feet.

## Order exactly these items

| ID | File / part number | Qty | Material and finish | Live price 2026-07-17 |
|---|---|---:|---|---:|
| CM2-001 | `STEP/CM2-001_upper_housing.step` | 1 | POM (Black); no bead blast; polish cosmetic A-surfaces | $88.97 |
| CM2-002 | `STEP/CM2-002_bottom_weight.step` | 1 | 6061-T6; fine bead blast + matte black anodize; strict appearance | $68.31 |
| CM2-003 | `STEP/CM2-003_lightpipe.step` | 1 | Clear cast PMMA; transparent-polished edges; fine-frost top optical face | $45.70 |
| CM2-004 | `STEP/CM2-004_joystick_cap.step` | 1 | POM (Black); no surface finish | $19.42 |
| CM2-005 | JLCMC `AMFG-P5-A65-65` | 1 | JIS B 2401 G-65; black NBR; 65 Shore A | $0.1522 |

Mechanical merchandise subtotal at the captured prices: **$222.56** before
shipping, tax, duty, and engineering review. Prices are dynamic.

## Drawing association

Attach the matching PDF to each CNC line item:

- CM2-001 → `drawings/CM2-001_Drawing_RevB.pdf`
- CM2-002 → `drawings/CM2-002_Drawing_RevB.pdf`
- CM2-003 → `drawings/CM2-003_Drawing_RevB.pdf`
- CM2-004 → `drawings/CM2-004_Drawing_RevB.pdf`

The consolidated pack is `drawings/CM2_CNC_Drawing_Pack_RevB.pdf`. Its fifth
sheet defines the purchased ring and groove interface; CM2-005 is not a custom
machined or printed part.

## Critical Rev B interface

- Aluminum base envelope: Ø94 mm, 3.8 mm front to 12.0 mm rear, nominal 5°.
- G-65 groove: Ø67.5 mm centerline, 3.6 mm width, 2.2 mm depth.
- Purchased ring: 64.4 ±0.57 mm ID, 3.1 ±0.10 mm section, 70.6 mm nominal OD.
- Ring protrusion: 0.9 mm nominal. No adhesive.
- Minimum aluminum floor below groove: 1.6 mm.
- Groove-to-counterbore radial land: 2.95 mm.
- Base fasteners: one M2.5×8 front, two M2.5×12 sides, one M2.5×16 rear.

## First-article acceptance

1. Inspect all four custom parts against their controlled drawing PDFs.
2. Dry-fit the G-65 ring; it must remain continuously captured while standing
   approximately 0.9 mm proud without adhesive.
3. Verify the base sits on the ring rather than on anodized aluminum or screw
   heads and does not rock on a flat reference surface.
4. Verify the PMMA light pipe seats in the POM pocket without force and its rear
   USB gap aligns with the housing notch.
5. Gauge M3 and M2.5 threads, then assemble with the four specified screw
   lengths at low torque.
6. Approve one physical first article before ordering multiples.

The authoritative machine-readable values are in `rev_b_spec.json`; the
independent geometry audit is in `rev_b_fit_report.json` and must report
`"status": "PASS"`.
