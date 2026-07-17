#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#include "bsp/board_api.h"
#include "stm32f0xx_hal.h"
#include "stm32f0xx_hal_adc.h"
#include "stm32f0xx_hal_adc_ex.h"
#include "tusb.h"

typedef struct { GPIO_TypeDef *port; uint16_t pin; } gpio_t;

static gpio_t const rows[4] = {
  {GPIOA, GPIO_PIN_2}, {GPIOA, GPIO_PIN_3},
  {GPIOA, GPIO_PIN_4}, {GPIOA, GPIO_PIN_5},
};
static gpio_t const cols[4] = {
  {GPIOA, GPIO_PIN_6}, {GPIOA, GPIO_PIN_7},
  {GPIOB, GPIO_PIN_0}, {GPIOB, GPIO_PIN_1},
};
static gpio_t const enc_a = {GPIOB, GPIO_PIN_2};
static gpio_t const enc_b = {GPIOB, GPIO_PIN_10};
static gpio_t const enc_sw = {GPIOB, GPIO_PIN_11};
static gpio_t const touch = {GPIOB, GPIO_PIN_12};
#define RGB_PORT GPIOB
#define RGB_PIN GPIO_PIN_13
#define RGB_COUNT 24

static uint8_t const keymap[4][4] = {
  {0, HID_KEY_F13, HID_KEY_F14, 0},
  {HID_KEY_F15, HID_KEY_F16, HID_KEY_F17, HID_KEY_F18},
  {HID_KEY_F19, HID_KEY_F20, HID_KEY_F21, HID_KEY_F22},
  {0, HID_KEY_F23, 0, HID_KEY_F24},
};
static uint8_t stable[4][4];
static uint8_t integrator[4][4];
static uint8_t encoder_last;
static int8_t encoder_delta;
static ADC_HandleTypeDef hadc;

static void configure_pin(gpio_t gpio, uint32_t mode, uint32_t pull) {
  GPIO_InitTypeDef init = {0};
  init.Pin = gpio.pin;
  init.Mode = mode;
  init.Pull = pull;
  init.Speed = GPIO_SPEED_FREQ_HIGH;
  HAL_GPIO_Init(gpio.port, &init);
}

static void keyboard_io_init(void) {
  for (unsigned i = 0; i < 4; i++) configure_pin(rows[i], GPIO_MODE_INPUT, GPIO_NOPULL);
  for (unsigned i = 0; i < 4; i++) configure_pin(cols[i], GPIO_MODE_INPUT, GPIO_PULLUP);
  configure_pin(enc_a, GPIO_MODE_INPUT, GPIO_PULLUP);
  configure_pin(enc_b, GPIO_MODE_INPUT, GPIO_PULLUP);
  configure_pin(enc_sw, GPIO_MODE_INPUT, GPIO_PULLUP);
  configure_pin(touch, GPIO_MODE_INPUT, GPIO_PULLDOWN);
  configure_pin((gpio_t){RGB_PORT, RGB_PIN}, GPIO_MODE_OUTPUT_PP, GPIO_NOPULL);
  HAL_GPIO_WritePin(RGB_PORT, RGB_PIN, GPIO_PIN_RESET);
  encoder_last = (HAL_GPIO_ReadPin(enc_a.port, enc_a.pin) << 1) |
                 HAL_GPIO_ReadPin(enc_b.port, enc_b.pin);
}

static void adc_init_local(void) {
  GPIO_InitTypeDef analog = {0};
  analog.Pin = GPIO_PIN_0 | GPIO_PIN_1;
  analog.Mode = GPIO_MODE_ANALOG;
  analog.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(GPIOA, &analog);
  __HAL_RCC_ADC1_CLK_ENABLE();
  hadc.Instance = ADC1;
  hadc.Init.ClockPrescaler = ADC_CLOCK_ASYNC_DIV1;
  hadc.Init.Resolution = ADC_RESOLUTION_12B;
  hadc.Init.DataAlign = ADC_DATAALIGN_RIGHT;
  hadc.Init.ScanConvMode = ADC_SCAN_DIRECTION_FORWARD;
  hadc.Init.EOCSelection = ADC_EOC_SINGLE_CONV;
  hadc.Init.LowPowerAutoWait = DISABLE;
  hadc.Init.LowPowerAutoPowerOff = DISABLE;
  hadc.Init.ContinuousConvMode = DISABLE;
  hadc.Init.DiscontinuousConvMode = DISABLE;
  hadc.Init.ExternalTrigConv = ADC_SOFTWARE_START;
  hadc.Init.ExternalTrigConvEdge = ADC_EXTERNALTRIGCONVEDGE_NONE;
  hadc.Init.DMAContinuousRequests = DISABLE;
  hadc.Init.Overrun = ADC_OVR_DATA_PRESERVED;
  HAL_ADC_Init(&hadc);
  HAL_ADCEx_Calibration_Start(&hadc);
}

static uint16_t adc_read_channel(uint32_t channel) {
  ADC_ChannelConfTypeDef config = {0};
  config.Channel = channel;
  config.Rank = ADC_RANK_CHANNEL_NUMBER;
  config.SamplingTime = ADC_SAMPLETIME_41CYCLES_5;
  HAL_ADC_ConfigChannel(&hadc, &config);
  HAL_ADC_Start(&hadc);
  HAL_ADC_PollForConversion(&hadc, 2);
  uint16_t result = (uint16_t)HAL_ADC_GetValue(&hadc);
  HAL_ADC_Stop(&hadc);
  return result;
}

static void scan_matrix(void) {
  for (unsigned row = 0; row < 4; row++) {
    configure_pin(rows[row], GPIO_MODE_OUTPUT_PP, GPIO_NOPULL);
    HAL_GPIO_WritePin(rows[row].port, rows[row].pin, GPIO_PIN_RESET);
    for (volatile unsigned delay = 0; delay < 40; delay++) __NOP();
    for (unsigned col = 0; col < 4; col++) {
      bool pressed = HAL_GPIO_ReadPin(cols[col].port, cols[col].pin) == GPIO_PIN_RESET;
      uint8_t *acc = &integrator[row][col];
      if (pressed && *acc < 5) (*acc)++;
      if (!pressed && *acc > 0) (*acc)--;
      if (*acc == 5) stable[row][col] = 1;
      if (*acc == 0) stable[row][col] = 0;
    }
    configure_pin(rows[row], GPIO_MODE_INPUT, GPIO_NOPULL);
  }
}

static void encoder_update(void) {
  uint8_t now = (HAL_GPIO_ReadPin(enc_a.port, enc_a.pin) << 1) |
                HAL_GPIO_ReadPin(enc_b.port, enc_b.pin);
  static int8_t const table[16] = {
    0, -1, 1, 0, 1, 0, 0, -1, -1, 0, 0, 1, 0, 1, -1, 0
  };
  encoder_delta += table[(encoder_last << 2) | now];
  encoder_last = now;
}

static inline void rgb_delay(unsigned count) {
  while (count--) __NOP();
}

static void rgb_bit(bool one) {
  RGB_PORT->BSRR = RGB_PIN;
  rgb_delay(one ? 17 : 6);
  RGB_PORT->BRR = RGB_PIN;
  rgb_delay(one ? 7 : 18);
}

static void rgb_word(uint32_t grb) {
  for (int bit = 23; bit >= 0; bit--) rgb_bit((grb >> bit) & 1u);
}

static uint32_t grb(uint8_t red, uint8_t green, uint8_t blue) {
  return ((uint32_t)green << 16) | ((uint32_t)red << 8) | blue;
}

static bool key_led_pressed(uint8_t index) {
  static uint8_t const positions[12][2] = {
    {0,1}, {0,2}, {1,0}, {1,1}, {1,2}, {1,3},
    {2,0}, {2,1}, {2,2}, {2,3}, {3,1}, {3,3},
  };
  return stable[positions[index][0]][positions[index][1]];
}

static void send_rgb_frame(void) {
  __disable_irq();
  for (uint8_t i = 0; i < RGB_COUNT; i++) {
    uint32_t color;
    if (i < 12) color = key_led_pressed(i) ? grb(4,1,0) : (i < 6 ? grb(1,4,0) : grb(2,2,2));
    else if (i < 21) color = grb(1,3,0);
    else color = grb(0,1,4);
    rgb_word(color);
  }
  __enable_irq();
  HAL_Delay(1);
}

static void add_key(uint8_t key, uint8_t keys[6], uint8_t *count) {
  if (key && *count < 6) keys[(*count)++] = key;
}

static void send_report(void) {
  if (!tud_hid_ready()) return;
  uint8_t keys[6] = {0};
  uint8_t count = 0;
  for (unsigned row = 0; row < 4; row++)
    for (unsigned col = 0; col < 4; col++)
      if (stable[row][col]) add_key(keymap[row][col], keys, &count);
  if (HAL_GPIO_ReadPin(enc_sw.port, enc_sw.pin) == GPIO_PIN_RESET)
    add_key(HID_KEY_KEYPAD_ENTER, keys, &count);
  if (HAL_GPIO_ReadPin(touch.port, touch.pin) == GPIO_PIN_SET)
    add_key(HID_KEY_F12, keys, &count);

  uint16_t x = adc_read_channel(ADC_CHANNEL_0);
  uint16_t y = adc_read_channel(ADC_CHANNEL_1);
  if (x < 900) add_key(HID_KEY_ARROW_LEFT, keys, &count);
  if (x > 3200) add_key(HID_KEY_ARROW_RIGHT, keys, &count);
  if (y < 900) add_key(HID_KEY_ARROW_DOWN, keys, &count);
  if (y > 3200) add_key(HID_KEY_ARROW_UP, keys, &count);
  if (encoder_delta >= 4) { add_key(HID_KEY_PAGE_UP, keys, &count); encoder_delta = 0; }
  if (encoder_delta <= -4) { add_key(HID_KEY_PAGE_DOWN, keys, &count); encoder_delta = 0; }
  tud_hid_keyboard_report(0, 0, keys);
}

int main(void) {
  board_init();
  keyboard_io_init();
  adc_init_local();
  tusb_rhport_init_t dev = {.role = TUSB_ROLE_DEVICE, .speed = TUSB_SPEED_FULL};
  tusb_init(BOARD_TUD_RHPORT, &dev);
  board_init_after_tusb();

  uint32_t next_scan = 0;
  uint32_t next_rgb = 0;
  while (1) {
    tud_task();
    uint32_t now = HAL_GetTick();
    if ((int32_t)(now - next_scan) >= 0) {
      next_scan = now + 1;
      scan_matrix();
      encoder_update();
      send_report();
    }
    if ((int32_t)(now - next_rgb) >= 0) {
      next_rgb = now + 20;
      send_rgb_frame();
    }
  }
}
