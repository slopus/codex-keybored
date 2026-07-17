#pragma once

#ifndef BOARD_TUD_RHPORT
#define BOARD_TUD_RHPORT 0
#endif
#ifndef BOARD_TUD_MAX_SPEED
#define BOARD_TUD_MAX_SPEED OPT_MODE_FULL_SPEED
#endif
#ifndef CFG_TUSB_MCU
#error CFG_TUSB_MCU must be defined by the TinyUSB STM32F0 family build
#endif
#ifndef CFG_TUSB_OS
#define CFG_TUSB_OS OPT_OS_NONE
#endif

#define CFG_TUD_ENABLED 1
#define CFG_TUD_MAX_SPEED BOARD_TUD_MAX_SPEED
#define CFG_TUSB_DEBUG 0
#define CFG_TUSB_MEM_ALIGN __attribute__((aligned(4)))
#define CFG_TUD_ENDPOINT0_SIZE 64
#define CFG_TUD_HID 1
#define CFG_TUD_CDC 0
#define CFG_TUD_MSC 0
#define CFG_TUD_MIDI 0
#define CFG_TUD_VENDOR 0
#define CFG_TUD_HID_EP_BUFSIZE 16
