# SPDX-License-Identifier: MIT
"""Pack an eight-frame OLED GIF into a matching right-half UF2 template."""

from pathlib import Path
import struct
import subprocess
import sys

FRAME_BYTES = 72 * 32 // 8
FRAME_COUNT = 8
START = b'EYELASH-FRAMES-A'
END = b'EYELASH-FRAMES-Z'
MAGIC = (0x0A324655, 0x9E5D5157)


def read_art(gif):
    raw = subprocess.check_output([
        'ffmpeg', '-v', 'error', '-i', str(gif), '-f', 'rawvideo',
        '-pix_fmt', 'gray', '-',
    ])
    assert len(raw) == 32 * 128 * FRAME_COUNT, 'Unexpected frame count or dimensions'
    assert set(raw) == {0, 255}, 'Expected monochrome frames'
    blocks = []
    for index in range(FRAME_COUNT):
        frame = raw[index * 4096:(index + 1) * 4096]
        assert not any(frame[:19 * 32] + frame[91 * 32:]), 'Artwork outside reserved area'
        packed = bytes(
            sum((frame[(90 - x) * 32 + y] != 0) << (7 - x % 8)
                for x in range(offset * 8, offset * 8 + 8))
            for y in range(32)
            for offset in range(9)
        )
        blocks.append(packed)
    assert len(set(blocks)) >= 6, 'Expected both panels to move'
    return b''.join(blocks)


def payload_locations(image):
    assert image and len(image) % 512 == 0
    locations = {}
    for offset in range(0, len(image), 512):
        assert struct.unpack_from('<II', image, offset) == MAGIC
        assert struct.unpack_from('<I', image, offset + 508)[0] == 0x0AB16F30
        flags, address, size = struct.unpack_from('<III', image, offset + 8)
        assert flags in (0, 0x2000), f'Unexpected UF2 flags {flags:#x}'
        assert 0 < size <= 476
        for index in range(size):
            assert address + index not in locations
            locations[address + index] = offset + 32 + index
    return [locations[address] for address in sorted(locations)]


def patch(image, art):
    assert len(art) == FRAME_BYTES * FRAME_COUNT
    locations = payload_locations(image)
    payload = bytes(image[offset] for offset in locations)
    assert payload.count(START) == payload.count(END) == 1, 'Missing or ambiguous artwork slot'
    start = payload.index(START) + len(START)
    end = payload.index(END)
    assert end - start == len(art), 'Artwork slot size differs from the GIF'
    target_offsets = locations[start:end]
    assert len(set(target_offsets)) == len(art)
    updated = bytearray(image)
    for location, value in zip(target_offsets, art):
        updated[location] = value
    assert bytes(updated[location] for location in target_offsets) == art
    changed = {i for i, (a, b) in enumerate(zip(image, updated)) if a != b}
    assert changed and changed <= set(target_offsets)
    assert payload_locations(updated) == locations
    return updated


if __name__ == '__main__':
    gif, template, destination = map(Path, sys.argv[1:])
    artwork = read_art(gif)
    destination.write_bytes(patch(template.read_bytes(), artwork))
    print(f'{destination.name}: verified all {FRAME_COUNT} frames; only artwork bytes changed')
