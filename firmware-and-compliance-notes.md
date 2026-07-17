# Firmware, Bluetooth, FCC, and ISED evidence

## Public firmware inspected

Work Louder published a diagnostic CM2 image in its battery-charging support
thread:

`https://github.com/worklouder/input-releases-internal/releases/download/battery.charging.diagnostic/firmware_cmv2_v0.3.0-rc.2_merged.bin`

`esptool 5.2.0 image-info` identifies the 2,117,568-byte merged image as:

- target: **ESP32-S3** (chip ID 9);
- flash: **16 MB**, DIO, 80 MHz;
- bootloader: ESP-IDF **5.3.2.250210**;
- compile time: 2026-01-16 11:32:52;
- image checksum and SHA-256 validation hash both valid.

Selected plain-text symbols/strings in the image:

- `Work Louder`, `Creator Micro 2`;
- `NimBLE`, `TinyUSB`, `ESP32 Keyboard`;
- `max77972_regs`, `Initializing battery IC`;
- GPIO initialization for rear button, USB detect, layer LEDs, touch pad,
  encoder A/B/switch, top-board power, and charge enable;
- `Switching to BLE slot %d`;
- self-test for key matrix, encoder rotation/press, touch button, rear button,
  and battery voltage/current;
- default keymap rows of 2 / 4 / 4 / 3 keyboard inputs.

Analog Devices describes MAX77972 as a one-cell Li-ion/Li-poly charger and fuel
gauge with USB-C CC and BC1.2 detection:
`https://www.analog.com/en/products/MAX77972.html`.

The binary proves the MCU family and charger IC used by the firmware build. It
does **not** prove whether production uses a bare ESP32-S3, an Espressif module,
or a custom certified radio module.

## FCC result

The official FCC EAS grantee-registration dataset was searched for:

- `Work Louder`
- `Worklouder`
- `Louder`
- `Creator Micro`
- `3300 Av Troie`

All returned zero records. The official exterior bottom render carries an FCC
logo but no visible FCC ID. This is consistent with, but does not prove, use of
a pre-certified radio module or a compliance route that does not create a Work
Louder grantee entry.

Official FCC grantee dataset:
`https://opendata.fcc.gov/resource/3b3k-34jp.json`

## Canadian ISED result

The official ISED Company Name Search returned no result for `Work Louder`.
The official Radio Equipment List returned no result for either:

- Product Marketing Name: `Creator Micro 2`
- Company Name: `Work Louder`

Search entry point:
`https://www.ised-isde.canada.ca/site/spectrum-management-system/en/equipment-certification-and-registration-services`

## What will resolve the radio module exactly

The next definitive evidence is a straight-on macro photograph of both sides of
the lower PCB after lifting the four top screws and disconnecting the FFC. The
required details are the ESP/module shield marking, antenna layout, FCC/ISED
text, crystal marking, USB-C connector, and MAX77972 area. Until that image
exists, the PCB should reserve a certified ESP32-S3 module keep-out rather than
copy an unverified antenna implementation.
