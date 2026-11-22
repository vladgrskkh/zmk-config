// SPDX-License-Identifier: MIT

#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#include <lvgl.h>
#include <zephyr/kernel.h>
#include <zmk/display.h>
#include <zmk/event_manager.h>
#include <zmk/events/activity_state_changed.h>

#define ART_WIDTH 72
#define ART_HEIGHT 32
#define FRAME_BYTES (ART_WIDTH * ART_HEIGHT / 8)
#define FRAME_COUNT 8
#define FRAME_MS 500
#define PALETTE_BYTES 8

/* The build publishes the template. pack_oled_gif.py inserts personal art locally. */
static const struct {
    uint8_t start[16];
    uint8_t frames[FRAME_COUNT][FRAME_BYTES];
    uint8_t end[16];
} artwork __attribute__((used)) = {
    .start = "EYELASH-FRAMES-A",
    .frames = {{1}, {2}, {3}, {4}, {5}, {6}, {7}, {8}},
    .end = "EYELASH-FRAMES-Z",
};

#if IS_ENABLED(CONFIG_NICE_OLED_WIDGET_INVERTED)
#define BACKGROUND 0x00
#define FOREGROUND 0xff
#else
#define BACKGROUND 0xff
#define FOREGROUND 0x00
#endif

/* Two opaque BGRA palette entries followed by the bitmap. */
static uint8_t image_data[PALETTE_BYTES + FRAME_BYTES] LV_ATTRIBUTE_MEM_ALIGN = {
    BACKGROUND, BACKGROUND, BACKGROUND, 0xff,
    FOREGROUND, FOREGROUND, FOREGROUND, 0xff,
};
static const lv_img_dsc_t image = {
    .header.cf = LV_IMG_CF_INDEXED_1BIT,
    .header.w = ART_WIDTH,
    .header.h = ART_HEIGHT,
    .data_size = sizeof(image_data),
    .data = image_data,
};

static lv_obj_t *art;
static lv_timer_t *timer;
static unsigned int frame_index;
static bool active;

static void draw_frame(void) {
    memcpy(image_data + PALETTE_BYTES, artwork.frames[frame_index], FRAME_BYTES);
    lv_img_cache_invalidate_src(&image);
    lv_obj_invalidate(art);
}

static void next_frame(lv_timer_t *timer) {
    ARG_UNUSED(timer);
    frame_index = (frame_index + 1) % FRAME_COUNT;
    draw_frame();
}

static bool display_is_active(const zmk_event_t *event) {
    if (event == NULL) {
        return true;
    }
    const struct zmk_activity_state_changed *activity = as_zmk_activity_state_changed(event);
    return activity != NULL && activity->state == ZMK_ACTIVITY_ACTIVE;
}

static void update_art_activity(bool is_active) {
    if (art == NULL || is_active == active) {
        return;
    }
    active = is_active;
    if (!active) {
        lv_timer_pause(timer);
        return;
    }
    frame_index = 0;
    draw_frame();
    lv_timer_reset(timer);
    lv_timer_resume(timer);
}

ZMK_DISPLAY_WIDGET_LISTENER(eyelash_art_activity, bool, update_art_activity, display_is_active)
ZMK_SUBSCRIPTION(eyelash_art_activity, zmk_activity_state_changed);

struct zmk_widget_screen;

void __wrap_draw_animation(lv_obj_t *canvas, struct zmk_widget_screen *widget) {
    ARG_UNUSED(widget);
    /* The existing battery and link indicators occupy the remaining columns. */
    art = lv_img_create(canvas);
    lv_img_set_src(art, &image);
    lv_obj_align(art, LV_ALIGN_TOP_LEFT, 0, 0);

    timer = lv_timer_create(next_frame, FRAME_MS, NULL);
    lv_timer_pause(timer);
    eyelash_art_activity_init();
}
