cmake_minimum_required(VERSION 3.20)

set(TOP ${CMAKE_CURRENT_SOURCE_DIR}/../third_party/tinyusb)
include(${TOP}/hw/bsp/family_support.cmake)

project(codeks_keybored_revA C CXX ASM)
family_initialize_project(${PROJECT_NAME} ${CMAKE_CURRENT_LIST_DIR})

add_executable(${PROJECT_NAME})
target_sources(${PROJECT_NAME} PUBLIC
  ${CMAKE_CURRENT_SOURCE_DIR}/main.c
  ${CMAKE_CURRENT_SOURCE_DIR}/usb_descriptors.c
  ${TOP}/hw/mcu/st/stm32f0xx_hal_driver/Src/stm32f0xx_hal_adc.c
  ${TOP}/hw/mcu/st/stm32f0xx_hal_driver/Src/stm32f0xx_hal_adc_ex.c
)
target_include_directories(${PROJECT_NAME} PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_compile_definitions(${PROJECT_NAME} PRIVATE HAL_ADC_MODULE_ENABLED)
target_compile_options(${PROJECT_NAME} PRIVATE -Wall -Wextra -Werror)

family_configure_device_example(${PROJECT_NAME} noos)
