#ifndef BOARD_H_
#define BOARD_H_

#ifdef __cplusplus
extern "C" {
#endif
// Unused spare pins satisfy TinyUSB's generic board API without touching any
// matrix, encoder, touch, joystick, RGB, or USB signal.
#define LED_PORT              GPIOB
#define LED_PIN               GPIO_PIN_14
#define LED_STATE_ON          1
#define BUTTON_PORT           GPIOB
#define BUTTON_PIN            GPIO_PIN_15
#define BUTTON_STATE_ACTIVE   0

static inline void board_stm32f0_clock_init(void)
{
  RCC_ClkInitTypeDef clk = {0};
  RCC_OscInitTypeDef osc = {0};

  osc.OscillatorType = RCC_OSCILLATORTYPE_HSI48;
  osc.HSI48State = RCC_HSI48_ON;
  osc.PLL.PLLState = RCC_PLL_ON;
  osc.PLL.PLLSource = RCC_PLLSOURCE_HSI48;
  osc.PLL.PREDIV = RCC_PREDIV_DIV2;
  osc.PLL.PLLMUL = RCC_PLL_MUL2;
  HAL_RCC_OscConfig(&osc);

  clk.ClockType = RCC_CLOCKTYPE_SYSCLK | RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_PCLK1;
  clk.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  clk.AHBCLKDivider = RCC_SYSCLK_DIV1;
  clk.APB1CLKDivider = RCC_HCLK_DIV1;
  HAL_RCC_ClockConfig(&clk, FLASH_LATENCY_1);

  // USB start-of-frame continually trims HSI48 on crystal-less STM32F072.
  __HAL_RCC_CRS_CLK_ENABLE();
  RCC_CRSInitTypeDef crs = {0};
  crs.Prescaler = RCC_CRS_SYNC_DIV1;
  crs.Source = RCC_CRS_SYNC_SOURCE_USB;
  crs.Polarity = RCC_CRS_SYNC_POLARITY_RISING;
  crs.ReloadValue = __HAL_RCC_CRS_RELOADVALUE_CALCULATE(48000000, 1000);
  crs.ErrorLimitValue = RCC_CRS_ERRORLIMIT_DEFAULT;
  crs.HSI48CalibrationValue = RCC_CRS_HSI48CALIBRATION_DEFAULT;
  HAL_RCCEx_CRSConfig(&crs);
}

static inline void board_vbus_sense_init(void) {}

#ifdef __cplusplus
}
#endif

#endif
