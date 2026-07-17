# CODEX KEYBORED Rev A2 — turnkey assembly and test SOP

**Build intent:** deliver one complete, programmed, electrically tested control pad and one programmed spare PCBA. The customer performs no soldering. Home assembly is limited to the controlled enclosure screws after first-article fit approval.

## Order configuration

- Service: JLCPCB **Standard PCBA**, both sides.
- Fabrication: 6-layer FR-4, 90 × 90 × 1.6 mm, white mask, black silk, ENIG.
- PCB quantity: 5. PCBA quantity: 2.
- Submit `codex_micro_wired_revA_jlc_bom.csv` and `codex_micro_wired_revA_jlc_cpl.csv` to JLC's automatic catalog matcher. Use the expanded `turnkey` BOM/CPL and consigned-parts CSV as the manual-assembly engineering reference.
- Depanel and remove JLC edge rails before delivery.
- Enable component photo confirmation, programming/function test, and a PCBA remark referencing this SOP.
- Customer-consigned parts must be received and booked into the JLC parts library before production.

## Assembly sequence

1. Assemble all bottom-side SMD parts, including reverse-mount RGB LEDs, J2, RESET, and BOOT0.
2. Assemble the top-side USB-C connector J1.
3. Manually insert and solder twelve WRK-LP1 switches at SW1–SW12. Seat every switch body flush and square to the PCB before soldering.
4. Manually insert and solder EC11E09444A8 at ENC1. Keep the shaft normal to the PCB.
5. Mechanically install RKJXY1000006 at JOY1 and lock its four-wire flex tail into J2. Do not crease the tail.
6. Clean and visually inspect all manual joints. Verify no switch body is lifted by more than 0.15 mm and the 2U key remains centered over SW11.
7. Program both PCBAs, run the functional test below, and identify the passing units as PRIMARY and SPARE.
8. On PRIMARY only, fit the twelve final keycaps, the 2U stabilizer/cap, the dial cap, and the joystick cap after electrical test. Do not glue caps.
9. Bag PRIMARY and SPARE separately in ESD-safe packaging. Include unused switches and unused PCB blanks.

## Firmware programming

- Target: STM32F072CBT6.
- Image: `../../firmware/stm32/release/codeks_keybored_revA.bin` at address `0x08000000`, or the corresponding HEX file.
- Preferred production route: SWD pogo contact at TP1/TP2/TP3/TP4 (SWCLK/SWDIO/3V3/GND).
- Alternate route: hold BOOT0 (SW14), pulse RESET (SW13), release BOOT0 after USB DFU enumerates, then program with STM32CubeProgrammer.
- After programming, power-cycle and confirm USB HID enumeration as `CODEX KEYBORED`.

## Functional acceptance test

Open `../../firmware/factory_key_test.html` in a Chromium browser on the test host, focus the page, then exercise every control.

- SW1–SW12: all F13–F24 indicators must pass exactly once.
- Encoder push: Keypad Enter indicator must pass.
- Encoder clockwise/counter-clockwise: Page Up and Page Down must both pass.
- Joystick: Left, Right, Up, and Down must all pass and return to neutral.
- Touch pad: F12 indicator must pass.
- RGB: all 24 emitters must illuminate; installed-key LEDs change state when their key is pressed.
- USB: reconnect three times; the device must enumerate each time without a warning.
- No switch may chatter visibly in the browser tester during ten presses.

Save one photo of the completed PRIMARY top side, one bottom-side photo, and one screenshot of the all-green factory tester. Do not ship a failed unit as PRIMARY.

## Customer-side work

After dimensional first-article approval, the customer only installs the completed PRIMARY PCBA/light pipe into the CNC parts using the four specified enclosure screws. No soldering, firmware flashing, switch insertion, or key testing is assigned to the customer.

## Quote status

JLC cart job Y5 / `SMT026071763199-3086316A` is configured for five PCBs and two both-side Standard PCBA units. Its captured base is `$193.01` (`$81.40` PCB + `$111.61` PCBA). Function testing, the PCBA remark/manual work, and consigned WRK-LP1/RKJXY operations remain quote-after-review; the base is not the final turnkey price.
