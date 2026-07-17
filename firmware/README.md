# CODEX KEYBORED firmware

The production Rev A2 target is the STM32F072CBT6 project in [`stm32/`](stm32/).
It enumerates as a driverless USB HID keyboard and implements the complete PCB
pin map: 12-key matrix, clickable encoder, capacitive touch, two-axis joystick
ADC and a conservative 24-pixel SK6812 status/underglow chain.

The older root-level RP2040 proof-of-concept sources and `release/` binaries are
retained only as design history. They **must not** be flashed onto Rev A2.

See [`stm32/README.md`](stm32/README.md) for the reproducible build, SWD flash
command and first-power checklist.
