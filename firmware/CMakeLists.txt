cmake_minimum_required(VERSION 3.13)

include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)
project(codex_micro_wired_reva C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

pico_sdk_init()

add_executable(codex_micro_wired_reva
    main.c
    usb_descriptors.c
)

pico_generate_pio_header(codex_micro_wired_reva ${CMAKE_CURRENT_LIST_DIR}/ws2812.pio)

target_include_directories(codex_micro_wired_reva PRIVATE ${CMAKE_CURRENT_LIST_DIR})
target_link_libraries(codex_micro_wired_reva
    pico_stdlib
    hardware_adc
    hardware_pio
    tinyusb_device
    tinyusb_board
)

pico_enable_stdio_usb(codex_micro_wired_reva 0)
pico_enable_stdio_uart(codex_micro_wired_reva 0)
pico_add_extra_outputs(codex_micro_wired_reva)
