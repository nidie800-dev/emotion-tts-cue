"""Minimal Standard MIDI File writer with marker events.

Cubase imports MIDI markers, so ``cues.mid`` can be dropped next to
``full.wav`` and the segment starts line up on the timeline.
"""

from __future__ import annotations

import struct
from pathlib import Path


def _var_len(value: int) -> bytes:
    value = max(0, int(value))
    buffer = value & 0x7F
    while value >> 7:
        value >>= 7
        buffer <<= 8
        buffer |= (value & 0x7F) | 0x80

    out = bytearray()
    while True:
        out.append(buffer & 0xFF)
        if buffer & 0x80:
            buffer >>= 8
        else:
            break
    return bytes(out)


def _ascii(text: str) -> bytes:
    # MIDI meta text is historically Latin-1. Keep markers ASCII so every DAW
    # shows them correctly; the full Chinese text lives in cues.csv.
    return text.encode("ascii", "replace")


def write_marker_midi(
    path: str | Path,
    markers: list[tuple[float, str]],
    total_duration: float | None = None,
    bpm: float = 120.0,
    ppq: int = 480,
) -> None:
    """Write a type-0 MIDI file containing one marker per segment start."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    tempo = int(round(60_000_000 / bpm))
    ticks_per_second = ppq * bpm / 60.0

    clean_markers: list[tuple[float, str]] = []
    for seconds, text in sorted(markers, key=lambda item: item[0]):
        clean_markers.append((max(0.0, float(seconds)), text))

    if not clean_markers or clean_markers[0][0] > 0.0:
        clean_markers.insert(0, (0.0, "START"))
    if total_duration is not None:
        clean_markers.append((max(0.0, float(total_duration)), "END"))

    track = bytearray()
    track_name = _ascii("EmoCue")
    track += _var_len(0) + b"\xFF\x03" + _var_len(len(track_name)) + track_name
    track += _var_len(0) + b"\xFF\x51\x03" + tempo.to_bytes(3, "big")

    last_tick = 0
    for seconds, text in clean_markers:
        tick = int(round(seconds * ticks_per_second))
        delta = max(0, tick - last_tick)
        last_tick = tick
        data = _ascii(text)[:120]
        track += _var_len(delta) + b"\xFF\x06" + _var_len(len(data)) + data

    track += _var_len(0) + b"\xFF\x2F\x00"

    header = b"MThd" + struct.pack(">IHHH", 6, 0, 1, ppq)
    chunk = b"MTrk" + struct.pack(">I", len(track)) + bytes(track)
    path.write_bytes(header + chunk)
