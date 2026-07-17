#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#include "bsp/board.h"
#include "hardware/adc.h"
#include "hardware/pio.h"
#include "pico/stdlib.h"
#include "tusb.h"
#include "class/hid/hid_device.h"
#include "ws2812.pio.h"

static const uint8_t row_gpio[4] = {0, 1, 2, 3};
static const uint8_t col_gpio[4] = {4, 5, 6, 7};
static const uint8_t encoder_a_gpio = 8;
static const uint8_t encoder_b_gpio = 9;
static const uint8_t encoder_sw_gpio = 10;
static const uint8_t touch_gpio = 11;
static const uint8_t rgb_gpio = 12;
static const uint8_t rgb_count = 24;

static const uint8_t keymap[4][4] = {
    {0, HID_KEY_F13, HID_KEY_F14, 0},
    {HID_KEY_F15, HID_KEY_F16, HID_KEY_F17, HID_KEY_F18},
    {HID_KEY_F19, HID_KEY_F20, HID_KEY_F21, HID_KEY_F22},
    {0, HID_KEY_F23, 0, HID_KEY_F24},
};

static uint8_t stable[4][4];
static uint8_t integrator[4][4];
static uint8_t encoder_last;
static int8_t encoder_delta;
static PIO rgb_pio;
static uint rgb_sm;

static void matrix_init(void) {
    for (int row = 0; row < 4; row++) {
        gpio_init(row_gpio[row]);
        gpio_set_dir(row_gpio[row], GPIO_IN);
        gpio_disable_pulls(row_gpio[row]);
    }
    for (int col = 0; col < 4; col++) {
        gpio_init(col_gpio[col]);
        gpio_set_dir(col_gpio[col], GPIO_IN);
        gpio_pull_up(col_gpio[col]);
    }
}

static void scan_matrix(void) {
    for (int row = 0; row < 4; row++) {
        gpio_set_dir(row_gpio[row], GPIO_OUT);
        gpio_put(row_gpio[row], 0);
        sleep_us(8);
        for (int col = 0; col < 4; col++) {
            bool pressed = !gpio_get(col_gpio[col]);
            uint8_t *acc = &integrator[row][col];
            if (pressed && *acc < 5) (*acc)++;
            if (!pressed && *acc > 0) (*acc)--;
            if (*acc == 5) stable[row][col] = 1;
            if (*acc == 0) stable[row][col] = 0;
        }
        gpio_set_dir(row_gpio[row], GPIO_IN);
        gpio_disable_pulls(row_gpio[row]);
    }
}

static void encoder_update(void) {
    uint8_t now = (gpio_get(encoder_a_gpio) << 1) | gpio_get(encoder_b_gpio);
    static const int8_t table[16] = {
        0, -1, 1, 0, 1, 0, 0, -1, -1, 0, 0, 1, 0, 1, -1, 0
    };
    encoder_delta += table[(encoder_last << 2) | now];
    encoder_last = now;
}

static void add_key(uint8_t key, uint8_t keys[6], uint8_t *count) {
    if (key && *count < 6) keys[(*count)++] = key;
}

static uint32_t grb(uint8_t red, uint8_t green, uint8_t blue) {
    return ((uint32_t)green << 16) | ((uint32_t)red << 8) | blue;
}

static void rgb_put(uint32_t pixel_grb) {
    pio_sm_put_blocking(rgb_pio, rgb_sm, pixel_grb << 8u);
}

static bool key_led_pressed(uint8_t index) {
    static const uint8_t positions[12][2] = {
        {0, 1}, {0, 2}, {1, 0}, {1, 1}, {1, 2}, {1, 3},
        {2, 0}, {2, 1}, {2, 2}, {2, 3}, {3, 1}, {3, 3},
    };
    return stable[positions[index][0]][positions[index][1]];
}

static void send_rgb_frame(void) {
    // Maximum channel code is 4/255. Even an all-white fault pattern stays far
    // below the uncontrolled full-brightness current of 24 SK6812 pixels.
    for (uint8_t index = 0; index < rgb_count; index++) {
        uint32_t color;
        if (index < 12) {
            if (key_led_pressed(index)) {
                color = grb(4, 1, 0);              // pressed: warm amber
            } else if (index < 6) {
                color = grb(1, 4, 0);              // agent keys: acid green
            } else {
                color = grb(2, 2, 2);              // command keys: dim white
            }
        } else if (index < 21) {
            color = grb(1, 3, 0);                  // perimeter underglow
        } else {
            color = grb(0, 1, 4);                  // status pixels
        }
        rgb_put(color);
    }
}

static void send_report(void) {
    if (!tud_hid_ready()) return;
    uint8_t keys[6] = {0};
    uint8_t count = 0;

    for (int row = 0; row < 4; row++) {
        for (int col = 0; col < 4; col++) {
            if (stable[row][col]) add_key(keymap[row][col], keys, &count);
        }
    }
    if (!gpio_get(encoder_sw_gpio)) add_key(HID_KEY_KEYPAD_ENTER, keys, &count);
    if (gpio_get(touch_gpio)) add_key(HID_KEY_F12, keys, &count);

    adc_select_input(0);
    uint16_t joy_x = adc_read();
    adc_select_input(1);
    uint16_t joy_y = adc_read();
    if (joy_x < 900) add_key(HID_KEY_ARROW_LEFT, keys, &count);
    if (joy_x > 3200) add_key(HID_KEY_ARROW_RIGHT, keys, &count);
    if (joy_y < 900) add_key(HID_KEY_ARROW_DOWN, keys, &count);
    if (joy_y > 3200) add_key(HID_KEY_ARROW_UP, keys, &count);

    if (encoder_delta >= 4) {
        add_key(HID_KEY_PAGE_UP, keys, &count);
        encoder_delta = 0;
    } else if (encoder_delta <= -4) {
        add_key(HID_KEY_PAGE_DOWN, keys, &count);
        encoder_delta = 0;
    }
    tud_hid_keyboard_report(0, 0, keys);
}

int main(void) {
    board_init();
    tusb_init();
    matrix_init();

    for (uint8_t gpio = encoder_a_gpio; gpio <= encoder_sw_gpio; gpio++) {
        gpio_init(gpio);
        gpio_set_dir(gpio, GPIO_IN);
        gpio_pull_up(gpio);
    }
    gpio_init(touch_gpio);
    gpio_set_dir(touch_gpio, GPIO_IN);
    gpio_pull_down(touch_gpio);
    encoder_last = (gpio_get(encoder_a_gpio) << 1) | gpio_get(encoder_b_gpio);

    rgb_pio = pio0;
    rgb_sm = pio_claim_unused_sm(rgb_pio, true);
    uint rgb_offset = pio_add_program(rgb_pio, &ws2812_program);
    ws2812_program_init(rgb_pio, rgb_sm, rgb_offset, rgb_gpio, 800000, false);
    send_rgb_frame();

    adc_init();
    adc_gpio_init(26);
    adc_gpio_init(27);

    absolute_time_t next_scan = get_absolute_time();
    absolute_time_t next_rgb = get_absolute_time();
    while (true) {
        tud_task();
        if (absolute_time_diff_us(next_scan, get_absolute_time()) >= 0) {
            next_scan = delayed_by_ms(next_scan, 1);
            scan_matrix();
            encoder_update();
            send_report();
        }
        if (absolute_time_diff_us(next_rgb, get_absolute_time()) >= 0) {
            next_rgb = delayed_by_ms(next_rgb, 20);
            send_rgb_frame();
        }
    }
}
