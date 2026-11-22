# SPDX-License-Identifier: MIT

if(CONFIG_SHIELD_EYELASH_OLED AND CONFIG_NICE_OLED_WIDGET_STATUS)
  set(art_frames "${CMAKE_CURRENT_BINARY_DIR}/display_art_frames.h")
  set(art_generator "${CMAKE_CURRENT_SOURCE_DIR}/render_eyelash_art.py")
  add_custom_command(
    OUTPUT "${art_frames}"
    COMMAND "${Python3_EXECUTABLE}" "${art_generator}" "${art_frames}"
    DEPENDS "${art_generator}"
    VERBATIM
  )
  add_custom_target(eyelash_display_art_frames DEPENDS "${art_frames}")
  add_dependencies(app eyelash_display_art_frames)
  target_sources(app PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/display_art.c")
  target_include_directories(app PRIVATE "${CMAKE_CURRENT_BINARY_DIR}")

  # Keep the pinned nice!oled widgets and replace only their artwork entry points.
  if(CONFIG_ZMK_SPLIT_ROLE_CENTRAL)
    zephyr_link_libraries(-Wl,--wrap=zmk_widget_screen_init)
  else()
    zephyr_link_libraries(-Wl,--wrap=draw_animation)
  endif()
endif()
