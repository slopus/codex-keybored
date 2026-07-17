#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
firmware_dir=$(CDPATH= cd -- "$script_dir/.." && pwd)
tinyusb_dir="$firmware_dir/third_party/tinyusb"
tinyusb_commit=aa410008e8e74b0727f8c30a1ec109ff2c37efc6

if [ ! -d "$tinyusb_dir/.git" ]; then
  mkdir -p "$firmware_dir/third_party"
  git clone https://github.com/hathach/tinyusb.git "$tinyusb_dir"
fi

git -C "$tinyusb_dir" fetch --depth 1 origin "$tinyusb_commit"
git -C "$tinyusb_dir" checkout --detach "$tinyusb_commit"
git -C "$tinyusb_dir" submodule update --init --depth 1 \
  hw/mcu/st/stm32f0xx_hal_driver \
  hw/mcu/st/cmsis_device_f0

board_target="$tinyusb_dir/hw/bsp/stm32f0/boards/codeks_keybored"
mkdir -p "$board_target"
cp "$script_dir/board/codeks_keybored/board.cmake" "$board_target/board.cmake"
cp "$script_dir/board/codeks_keybored/board.h" "$board_target/board.h"

echo "TinyUSB dependency prepared at $tinyusb_commit"
