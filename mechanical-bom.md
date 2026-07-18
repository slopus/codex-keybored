# Mechanical BOM and one-off manufacturing plan

Quantities are for one Codex Micro–class device. `Exact` means the part is sold
by Work Louder for Creator Micro 2. `Candidate` means it fits the published
description and measured envelope but still needs confirmation from a PCB photo
or physical sample.

## Buy rather than reproduce

| Item | Qty | Recommended source / specification | Status | Notes |
|---|---:|---|---|---|
| Low-profile switches | 12 + 2 spare | [Work Louder wrk. LP1](https://worklouder.cc/wrk-lp1-switches): MX stem, POM/POK, Gateron low-profile footprint | Exact family | Current pack is 106 pieces for **$59.00**. Choose Clicky or Silent. The encoder push makes the published 13th mechanical input; it is not a keyboard switch. |
| Translucent caps | 1 set | [wrk. MX Pure](https://worklouder.cc/wrk-mx-pure): 12×1U + 1×2U, frosted PC, 19.05 mm pitch | Exact geometry family | Current set is **$19.00**. Provides the correct pass-through-light cap shape. Use six translucent 1U caps; the rest are prototypes/spares. |
| White/icon caps | 5×1U + 1×2U | [wrk. MX Legend](https://worklouder.cc/wrk-mx-legend), or custom-made caps below | Exact interface | The current 58×1U + 1×2U icon set is **$54.00**, but does not reproduce the Codex-specific legends exactly. |
| Dial cap | 1 | [Work Louder wrk. Dial 2](https://worklouder.cc/wrk-dial-2) | Exact accessory | Current price is **$5.98**. Officially compatible with Creator Micro v2. Confirm encoder shaft length before choosing the encoder. |
| Encoder | 1 | Clickable incremental vertical encoder, 6 mm shaft; Bourns PEC11/Alps EC11 class | Candidate | Pinout, detent count, shaft height, and mounting tabs must be measured from an opened CM2. Firmware confirms A, B, and push-switch inputs. |
| Planar joystick | 1 | [Alps Alpine RKJXY100000A](https://tech.alpsalpine.com/e/products/detail/RKJXY100000A/), 19.6×18.1×4.9 mm, 2 kΩ X/Y | High-confidence candidate | The name, dimensions, continuous X/Y action, resin shaft, no center push, and official render geometry all match. The part is discontinued; source surplus or qualify a footprint-compatible OEM clone. |
| Joystick cap | 1 | CM2-004 machined black POM, target Ø14.5 × 7 mm | Quoted prototype | The current rigid cap is a geometry/fit first article. Retention geometry follows the selected joystick and may later be transferred to molded silicone. |
| Top fasteners | 4 | Black ISO 4762 M3 socket-head, provisional M3×10 or M3×12 | Candidate | Render head size matches M3. Final length depends on real standoff/thread depth. |
| Standoffs/inserts | 4 | Ø7 × 8.3 mm envelope, M3 internal thread | Custom/COTS | Turn aluminum/brass standoffs or use commercial M3 female spacers after the lower stack is fixed. |
| Continuous anti-slip ring | 1 | [JLCMC AMFG-P5-A65-65](https://jlcmc.com/product/s/A05/AMFG/o-ring-g-series), JIS B 2401 G-65, black NBR 65 Shore A | Exact purchased part | ID 64.4 ±0.57 mm, section 3.1 ±0.10 mm, nominal OD 70.6 mm. Captured in the machined base groove without adhesive. Live price **$0.1522**; in cart. |
| USB-C receptacle | 1 | HRO TYPE-C-31-M-12, LCSC C165948 | Selected | Exact KiCad footprint and JLCPCB-available part used on wired Rev A. |
| LiPo | 1 | Protected 1S pouch, 1900–2100 mAh, target envelope ≤58×42×6 mm | Candidate | Work Louder publishes 2100 mAh; Framer publishes 1900 mAh. Treat capacity and connector as variant-dependent. |

## Custom keycaps for the Codex look

The least risky path is to buy Work Louder caps for the shape and stem, then add
the artwork. Producing real single-shot PBT at one-off quantity is not economic.

1. **White caps:** start with low-profile MX PBT blanks. Dye-sublimate black
   artwork if the cap material and temperature window are known; otherwise use
   UV print or a thin UV-DTF transfer. Do not laser PBT without test coupons.
2. **Backlit agent caps:** use frosted PC `wrk. MX Pure` caps. Apply an opaque
   top coating, then laser-etch the icon, or leave them translucent and print a
   dark center icon. Test heat and solvent compatibility first.
3. **Fully custom one-off:** SLA-print a tough/clear resin cap master with an MX
   cross, wet-sand and clear-coat it, then cast polyurethane. Print the MX stem
   0.05–0.10 mm undersize only after a calibration coupon; consumer resin
   printers vary too much to assume a nominal press fit.
4. **2U cap:** use two stabilizers at provisional ±11.9 mm from the switch
   center. Do not freeze the stabilizer cutouts until the chosen low-profile
   stabilizer datasheet is selected.

For a private prototype, reproduce only the icons needed for testing. Do not
sell OpenAI/Work Louder branded caps or imply an authorized product.

## CNC housing — original material

### Upper body / captured light diffuser

- Current quoted stock: black POM, minimum 115×115×13 mm.
- Finished envelope: 108×108×10.3 mm, outer R14.
- Inner opening in v0.1: 92×92 mm, R7, leaving an 8 mm nominal wall.
- Finish: no bead blast; polish cosmetic A-surfaces to target Ra ≤0.8 µm.
- Capture the separate 1.5 mm clear cast PMMA light pipe in the 106.4 mm pocket;
  transparent-polish its edges and apply a uniform fine frost to the top face.
- Leave 0.20–0.30 mm total clearance around the 90 mm top PCB/panel until the
  machining process is characterized.

The production threads are in POM: four M3×0.5 PCB bosses and four M2.5×0.45
base bosses. Confirm thread gauges and screw engagement on the first article.

### Bottom wedge

- Stock: 6061-T6 aluminum round/plate, minimum Ø100×14 mm.
- Finished envelope: Ø94 mm, planar top, underside rising from 3.8 mm at the
  front datum to 12.0 mm at the rear datum; nominal tilt 5°.
- Finish quoted at JLC CNC: bead blast + matte black anodize, ISO 2768 medium.
- Four Ø2.8 mm M2.5 clearance holes with Ø5.0 × 1.9 mm counterbores.
- Continuous ring groove: Ø67.5 mm centerline, 3.6 mm wide × 2.2 mm deep.
  The G-65 ring stands 0.9 mm proud nominally; groove-to-counterbore land is
  2.95 mm and the minimum aluminum floor is 1.6 mm.
- Current one-off quote: **$68.31** before shipping; six quoted production days.

### Current JLC CNC one-off estimate

| Machined part | Material / finish | Quote |
|---|---|---:|
| Upper housing | Black POM, polished A-surfaces | $88.97 |
| Angled bottom wedge | 6061, G-65 groove, bead blast + matte black anodize | $68.31 |
| Captured light pipe | Clear cast PMMA, polished edges + frosted top face | $45.70 |
| Joystick cap prototype | Black POM | $19.42 |
| **JLCCNC subtotal** |  | **$222.40** |
| Purchased G-65 ring | JLCMC AMFG-P5-A65-65 | $0.16 |
| **Mechanical merchandise subtotal** | before shipping/tax/duty | **$222.56** |

These are live quote results captured on 2026-07-17, not guaranteed invoice
prices. The groove-base and the other three current parts are saved in the
signed-in cart together with the exact G-65 ring. Superseded flat/no-groove
parts and individual rubber feet were removed; the cart contains exactly four
CNC items and one JLCMC ring for this mechanical revision.

## CNC housing — recommended wood version

Use quarter-sawn hard maple, walnut, or laminated birch rather than unstable
flat-sawn stock. Keep the same 108 mm outline and 92 mm opening, but make the
upper ring 11–12 mm thick and finish-machine both faces after acclimation.

- Add a separate 1.5–2.0 mm frosted acrylic light-pipe/liner below the top PCB;
  wood cannot reproduce the official underglow by itself.
- Seal all faces, especially the inner pocket, with hardwax oil or a thin matte
  polyurethane finish.
- Use brass M3 inserts or separate metal standoffs. Pilot and insert tests belong
  on offcuts from the same stock.
- Allow at least 0.30–0.40 mm total PCB clearance across the grain and keep the
  90 mm panel mechanically located by the four standoffs, not by a tight wood
  pocket.
- A weighted Ø94 aluminum/brass bottom still gives the most faithful desk feel;
  a wood bottom is possible but will be much lighter.

## Dimensions to measure on the first physical sample

1. Exact external width/depth at top and bottom, all corner radii, and total
   height without caps.
2. Top PCB outline/thickness, four screw centers, hole diameter, and screw size.
3. Housing cross-section: inner ledge, standoff heights, bottom-disc step, and
   USB-C/rear-button openings.
4. Dial diameter/height, encoder shaft type and length.
5. Joystick manufacturer marking, pad footprint, cap retention geometry.
6. 2U stabilizer type and spacing.
7. Lower PCB and FFC dimensions; LiPo label, connector, and adhesive locations.
