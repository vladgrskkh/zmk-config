"""Generate SSD1306 bitmaps from original upright OLED pixel art."""

from pathlib import Path
import struct
import sys
import zlib


class Scene:
    def __init__(self, height):
        self.height = height
        self.pixels = [bytearray(32) for _ in range(height)]

    def pixel(self, x, y, on=1):
        if 0 <= x < 32 and 0 <= y < self.height:
            self.pixels[y][x] = on

    def line(self, start, end, on=1):
        x, y = start
        end_x, end_y = end
        dx, dy = abs(end_x - x), -abs(end_y - y)
        sx, sy = (1 if x < end_x else -1), (1 if y < end_y else -1)
        error = dx + dy
        while True:
            self.pixel(x, y, on)
            if (x, y) == end:
                break
            doubled = 2 * error
            if doubled >= dy:
                error += dy
                x += sx
            if doubled <= dx:
                error += dx
                y += sy

    def path(self, *points):
        for start, end in zip(points, points[1:]):
            self.line(start, end)

    def fill(self, left, top, right, bottom, on=1):
        for y in range(top, bottom + 1):
            self.line((left, y), (right, y), on)

    def oled_bytes(self):
        # The two displays are mounted vertically on a 128-by-32 controller.
        return bytes(
            sum(self.pixels[self.height - 1 - x][y] << (7 - x % 8)
                for x in range(byte * 8, byte * 8 + 8))
            for y in range(32)
            for byte in range(self.height // 8)
        )


def swordsman(frame):
    scene = Scene(72)
    wind = (0, 2, 3, 1)[frame]

    # Crescent and distant ridge.
    scene.path((8, 8), (5, 9), (3, 12), (3, 16), (5, 19), (8, 20), (10, 19))
    scene.path((8, 8), (6, 12), (6, 15), (8, 18), (10, 19))
    scene.path((0, 34), (8, 29), (11, 31), (14, 30))
    scene.path((20, 30), (24, 28), (28, 30), (31, 30))

    # Topknot, face, robe and the scabbard behind the hip.
    scene.path((15, 27), (14, 24), (16, 21), (20, 21), (22, 23),
               (22, 26), (24, 27), (22, 28), (20, 30), (18, 30))
    scene.path((16, 21), (16, 19), (18, 18), (20, 19), (20, 21))
    scene.path((14, 24), (15, 28), (13, 31), (10, 36), (10, 42), (12, 46))
    scene.path((18, 30), (22, 33), (24, 39), (22, 42), (20, 40), (21, 37))
    scene.path((13, 32), (16, 35), (19, 36), (20, 40), (17, 43), (12, 44))
    scene.path((14, 45), (12, 50), (8 - wind, 55), (15, 53), (17, 50))
    scene.path((18, 44), (22, 47), (23, 54), (26 + wind, 58),
               (19, 58), (17, 55), (16, 61), (13, 63), (10, 63))
    scene.path((21, 54), (23, 60), (26, 62), (25, 64), (21, 64))
    scene.path((17, 42), (22, 43), (28, 39), (31, 37))
    scene.path((20, 45), (28, 40), (31, 37))
    scene.pixel(21, 25)

    # A few windblown foreground strokes move, while the figure stays fixed.
    for x, y, lean, rise in ((0, 65, 2, 16), (4, 68, 3, 13), (8, 71, -1, 11),
                             (12, 71, 4, 10), (19, 71, -4, 8), (24, 71, 2, 12),
                             (29, 70, -4, 18), (30, 66, -3, 9)):
        scene.path((x, y), (x + lean, y - rise // 2),
                   (x + lean + wind, y - rise))
    scene.path((0, 69), (5, 70), (12, 69), (19, 70), (25, 68), (31, 69))
    return scene


def rooftop(frame):
    scene = Scene(128)
    # Roof edge, bright windows, and the open shaft between buildings.
    scene.path((0, 32), (11, 32), (11, 36), (8, 36), (8, 127))
    scene.path((0, 36), (8, 36))
    scene.path((23, 69), (23, 63), (26, 63), (26, 54), (31, 54))
    scene.path((23, 69), (23, 127))
    scene.path((28, 59), (28, 127))
    for top in range(43, 124, 9):
        scene.line((2, top), (4, top))
        scene.line((2, top + 2), (3, top + 2))
    for top in range(74, 124, 8):
        scene.line((25, top), (26, top))
        scene.pixel(30, top + 3)
    scene.pixel(26, 22)
    scene.pixel(29, 14)

    # Each pose occupies only a small part of the open city shaft.
    if frame == 0:
        scene.path((12, 28), (14, 27), (16, 22), (16, 19), (18, 16),
                   (20, 16), (22, 19), (21, 22), (19, 24), (19, 27))
        scene.path((17, 24), (14, 31), (13, 36), (11, 38), (9, 38))
        scene.path((19, 27), (17, 32), (17, 35), (14, 38))
        scene.path((18, 26), (22, 29), (24, 27))
    else:
        dy = (0, 0, 19, 35)[frame]
        poses = (
            ((18, 42), (20, 43), (21, 46), (20, 49), (17, 49), (16, 46), (18, 42)),
            ((18, 42), (16, 38), (14, 35), (13, 30), (11, 27)),
            ((17, 42), (16, 35), (18, 33), (19, 28), (20, 24)),
            ((18, 41), (21, 39), (22, 37), (24, 38), (25, 41)),
            ((16, 39), (14, 42), (11, 41), (10, 38)),
        )
        for pose in poses:
            scene.path(*((x, y + dy) for x, y in pose))
        if frame >= 2:
            for y in range(27 + dy, 50 + dy, 4 if frame == 2 else 2):
                scene.line((10, y), (24, y), 0)
            scene.line((14, 43 + dy), (20, 43 + dy))
            scene.pixel(22, 36 + dy)
            scene.pixel(12, 31 + dy)
    return scene


def write_header(path, scenes):
    lines = ['/* Generated by render_eyelash_art.py. */', '#pragma once', '#include <stdint.h>']
    for name, frames in scenes:
        width = frames[0].height
        lines += ['', f'static const uint8_t {name}_frames[][{width} * 32 / 8] = {{']
        for frame in frames:
            data = frame.oled_bytes()
            lines.append('    {')
            for offset in range(0, len(data), 16):
                row = ', '.join(f'0x{byte:02x}' for byte in data[offset:offset + 16])
                lines.append(f'        {row},')
            lines.append('    },')
        lines.append('};')
    path.write_text('\n'.join(lines) + '\n')


def write_preview(path, scenes):
    scale, margin = 4, 3
    width, height = 8 * (32 + margin) + margin, 128 + 2 * margin
    pixels = [bytearray([24] * width) for _ in range(height)]
    for index, scene in enumerate(frame for _, frames in scenes for frame in frames):
        start = margin + index * (32 + margin)
        for row in range(128):
            pixels[margin + row][start:start + 32] = bytes(32)
        for row, line in enumerate(scene.pixels):
            pixels[margin + row][start:start + 32] = bytes(value * 255 for value in line)

    def chunk(name, data):
        return (struct.pack('>I', len(data)) + name + data
                + struct.pack('>I', zlib.crc32(name + data)))

    raw = b''.join((b'\0' + bytes(value for value in row for _ in range(scale))) * scale
                   for row in pixels)
    header = struct.pack('>2I5B', width * scale, height * scale, 8, 0, 0, 0, 0)
    path.write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', header)
                     + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))


if __name__ == '__main__':
    scenes = [('rooftop', [rooftop(i) for i in range(4)]),
              ('swordsman', [swordsman(i) for i in range(4)])]
    write_header(Path(sys.argv[1]), scenes)
    if len(sys.argv) > 2:
        write_preview(Path(sys.argv[2]), scenes)
