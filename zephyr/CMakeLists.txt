# SPDX-License-Identifier: MIT
if(CONFIG_SHIELD_EYELASH_OLED AND CONFIG_NICE_OLED_WIDGET_STATUS AND CONFIG_ZMK_SPLIT_ROLE_CENTRAL)
  target_sources(app PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/gopher.c")
  zephyr_link_libraries(-Wl,--wrap=draw_background)
endif()

# SPDX-License-Identifier: MIT

if(CONFIG_SHIELD_EYELASH_OLED AND CONFIG_NICE_OLED_WIDGET_STATUS AND NOT CONFIG_ZMK_SPLIT_ROLE_CENTRAL)
  target_sources(app PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/display_art.c")
  zephyr_link_libraries(-Wl,--wrap=draw_animation)
endif()
