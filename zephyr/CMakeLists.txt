# SPDX-License-Identifier: MIT

if(CONFIG_SHIELD_EYELASH_OLED AND CONFIG_NICE_OLED_WIDGET_STATUS)
  set(art_frames "${CMAKE_CURRENT_BINARY_DIR}/display_art_frames.h")
  set(art_generator "${CMAKE_CURRENT_SOURCE_DIR}/render_eyelash_art.py")
  add_custom_command(
    OUTPUT "${art_frames}"
    COMMAND "${PYTHON_EXECUTABLE}" "${art_generator}" "${art_frames}"
    DEPENDS "${art_generator}"
    VERBATIM
  )
  target_sources(app PRIVATE display_art.c "${art_frames}")
  target_include_directories(app PRIVATE "${CMAKE_CURRENT_BINARY_DIR}")

  # Keep the pinned nice!oled widgets and replace only their artwork entry points.
  if(CONFIG_ZMK_SPLIT_ROLE_CENTRAL)
    zephyr_link_options(-Wl,--wrap=zmk_widget_screen_init)
  else()
    zephyr_link_options(-Wl,--wrap=draw_animation)
  endif()
endif()
