# STM32F072 wired Rev A2

This build targets the directly assembled STM32F072CBT6 on the single 90 x 90
mm PCB. USB Full Speed uses the internal HSI48 oscillator disciplined by CRS;
there is no crystal and no removable controller module.

## Behavior

- 12 keys send F13–F24 in physical order.
- Encoder rotation sends Page Up/Page Down; push sends keypad Enter.
- Capacitive touch sends F12.
- Joystick thresholds send the four arrow keys.
- 24 SK6812MINI-E pixels are limited to channel values 0–4/255 during bring-up.
- USB identity: development VID/PID `CAFE:4B44`, product `CODEX KEYBORED Rev A2`.

## Reproducible build

TinyUSB is pinned at commit `aa410008e8e74b0727f8c30a1ec109ff2c37efc6`.
The large upstream checkout is intentionally not stored in this repository;
the tracked bootstrap script fetches only the required STM32F0 dependencies and
installs the local `codeks_keybored` board definition. Use an Arm GNU embedded
toolchain that includes newlib (verified with official Arm GNU Toolchain
15.2.Rel1):

```sh
sh firmware/stm32/fetch_dependencies.sh
cmake -S firmware/stm32 -B firmware/stm32/build-arm15 -G Ninja \
  -DFAMILY=stm32f0 -DBOARD=codeks_keybored -DTOOLCHAIN=gcc
cmake --build firmware/stm32/build-arm15 -j
```

The verified build uses 16,548 bytes of 128 KiB flash and 2,448 bytes of 16 KiB
RAM. Flash `release/codeks_keybored_revA.hex` through SWD (TP1 SWCLK, TP2 SWD,
TP3 3V3, TP4 GND), for example:

```sh
openocd -f interface/stlink.cfg -f target/stm32f0x.cfg \
  -c "program release/codeks_keybored_revA.hex verify reset exit"
```

## Verification boundary

The artifacts are compiler/linker verified, not hardware verified. Power the
first assembly from a current-limited 5 V supply before attaching a computer.
Confirm 3.3 V, SWD access, USB enumeration, every switch/encoder direction,
joystick center/endpoints, touch polarity and all RGB orientations. The
bit-banged SK6812 timing is deliberately isolated in `main.c`; verify it on an
oscilloscope and tune the delay constants for the assembled board before
raising brightness. Replace the development USB VID/PID before distribution.
