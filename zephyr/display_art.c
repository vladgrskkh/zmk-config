// SPDX-License-Identifier: MIT

#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#include <lvgl.h>
#include <zephyr/kernel.h>
#include <zmk/display.h>
#include <zmk/event_manager.h>
#include <zmk/events/activity_state_changed.h>

#include "display_art_frames.h"

#define OLED_HEIGHT 32
#define RIGHT_FRAME_MS 750
#define LEFT_FRAME_MS 240
#define PALETTE_BYTES 8
#define FRAME_COUNT 4

#if IS_ENABLED(CONFIG_ZMK_SPLIT_ROLE_CENTRAL)
#define SCENE_WIDTH 128
#define FRAME_MS LEFT_FRAME_MS
#define FRAMES rooftop_frames
#else
#define SCENE_WIDTH 72
#define FRAME_MS RIGHT_FRAME_MS
#define FRAMES swordsman_frames
#endif

/* Indexed LVGL images start with two BGRA palette entries, then the bitmap. */
#if IS_ENABLED(CONFIG_NICE_OLED_WIDGET_INVERTED)
#define BACKGROUND 0x00
#define FOREGROUND 0xff
#else
#define BACKGROUND 0xff
#define FOREGROUND 0x00
#endif

static uint8_t image_data[PALETTE_BYTES + SCENE_WIDTH * OLED_HEIGHT / 8] LV_ATTRIBUTE_MEM_ALIGN = {
    BACKGROUND, BACKGROUND, BACKGROUND, 0xff,
    FOREGROUND, FOREGROUND, FOREGROUND, 0xff,
};
static const lv_img_dsc_t scene_image = {
    .header.cf = LV_IMG_CF_INDEXED_1BIT,
    .header.w = SCENE_WIDTH,
    .header.h = OLED_HEIGHT,
    .data_size = sizeof(image_data),
    .data = image_data,
};

static lv_obj_t *scene;
static lv_timer_t *scene_timer;
static unsigned int frame_index;
static bool scene_active;

static void draw_frame(unsigned int frame) {
    memcpy(image_data + PALETTE_BYTES, FRAMES[frame], sizeof(FRAMES[frame]));
    lv_img_cache_invalidate_src(&scene_image);
    lv_obj_invalidate(scene);
}

static void advance_scene(lv_timer_t *timer) {
    frame_index++;
#if IS_ENABLED(CONFIG_ZMK_SPLIT_ROLE_CENTRAL)
    if (frame_index == FRAME_COUNT) {
        lv_obj_add_flag(scene, LV_OBJ_FLAG_HIDDEN);
        lv_timer_pause(timer);
        return;
    }
#else
    frame_index %= FRAME_COUNT;
#endif
    draw_frame(frame_index);
}

static bool display_is_active(const zmk_event_t *event) {
    const struct zmk_activity_state_changed *activity =
        event == NULL ? NULL : as_zmk_activity_state_changed(event);
    return activity == NULL || activity->state == ZMK_ACTIVITY_ACTIVE;
}

static void update_scene_activity(bool active) {
    if (scene == NULL || scene_active == active) {
        return;
    }
    scene_active = active;
    if (!active) {
        lv_timer_pause(scene_timer);
#if IS_ENABLED(CONFIG_ZMK_SPLIT_ROLE_CENTRAL)
        lv_obj_add_flag(scene, LV_OBJ_FLAG_HIDDEN);
#endif
        return;
    }

    frame_index = 0;
    draw_frame(frame_index);
#if IS_ENABLED(CONFIG_ZMK_SPLIT_ROLE_CENTRAL)
    lv_obj_clear_flag(scene, LV_OBJ_FLAG_HIDDEN);
#endif
    lv_timer_reset(scene_timer);
    lv_timer_resume(scene_timer);
}

ZMK_DISPLAY_WIDGET_LISTENER(eyelash_art_activity, bool, update_scene_activity, display_is_active)
ZMK_SUBSCRIPTION(eyelash_art_activity, zmk_activity_state_changed);

static void initialize_scene(lv_obj_t *parent) {
    scene = lv_img_create(parent);
    lv_img_set_src(scene, &scene_image);
    lv_obj_align(scene, LV_ALIGN_TOP_LEFT, 0, 0);

    scene_timer = lv_timer_create(advance_scene, FRAME_MS, NULL);
    lv_timer_pause(scene_timer);
    eyelash_art_activity_init();
}

struct zmk_widget_screen;

#if IS_ENABLED(CONFIG_ZMK_SPLIT_ROLE_CENTRAL)
int __real_zmk_widget_screen_init(struct zmk_widget_screen *widget, lv_obj_t *parent);

int __wrap_zmk_widget_screen_init(struct zmk_widget_screen *widget, lv_obj_t *parent) {
    int result = __real_zmk_widget_screen_init(widget, parent);
    if (result == 0) {
        initialize_scene(parent);
    }
    return result;
}
#else
void __wrap_draw_animation(lv_obj_t *canvas, struct zmk_widget_screen *widget) {
    ARG_UNUSED(widget);
    /* The battery and link indicators occupy the remaining columns. */
    initialize_scene(canvas);
}
#endif
