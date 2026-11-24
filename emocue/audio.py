"""Small WAV utilities built on the standard library (no ffmpeg needed)."""

from __future__ import annotations

import math
import wave
from array import array
from pathlib import Path


def wav_info(path: str | Path) -> tuple[int, int, float]:
    """Return ``(sample_rate, channels, duration_seconds)`` for a PCM WAV."""

    with wave.open(str(path), "rb") as handle:
        sample_rate = handle.getframerate()
        channels = handle.getnchannels()
        frames = handle.getnframes()
    return sample_rate, channels, frames / float(sample_rate)


def read_wav(path: str | Path) -> tuple[bytes, int, int, int]:
    """Return ``(frames_bytes, sample_rate, channels, sample_width)``."""

    with wave.open(str(path), "rb") as handle:
        sample_rate = handle.getframerate()
        channels = handle.getnchannels()
        sample_width = handle.getsampwidth()
        frames = handle.readframes(handle.getnframes())
    return frames, sample_rate, channels, sample_width


def write_wav(
    path: str | Path,
    frames: bytes,
    sample_rate: int,
    channels: int = 1,
    sample_width: int = 2,
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(channels)
        handle.setsampwidth(sample_width)
        handle.setframerate(sample_rate)
        handle.writeframes(frames)


def write_silence(
    path: str | Path,
    seconds: float,
    sample_rate: int = 24000,
    channels: int = 1,
    sample_width: int = 2,
) -> None:
    frames = max(0, int(round(seconds * sample_rate)))
    silence = b"\x00" * frames * channels * sample_width
    write_wav(path, silence, sample_rate, channels, sample_width)


def concat_wavs(
    paths: list[str | Path],
    out_path: str | Path,
    gap_seconds: float = 0.25,
) -> float:
    """Concatenate WAV files with silence between them.

    Returns the total duration in seconds. All inputs must share the same
    sample rate, channel count and sample width; this is deliberate so the cue
    times stay sample-accurate.
    """

    if not paths:
        raise ValueError("no input WAV files")

    first_frames, sample_rate, channels, sample_width = read_wav(paths[0])
    all_frames = [first_frames]

    silence_frames = max(0, int(round(gap_seconds * sample_rate)))
    silence = b"\x00" * silence_frames * channels * sample_width

    for path in paths[1:]:
        frames, sr, ch, sw = read_wav(path)
        if (sr, ch, sw) != (sample_rate, channels, sample_width):
            raise ValueError(
                f"{path} has {(sr, ch, sw)}, expected {(sample_rate, channels, sample_width)}. "
                "Make every backend return the same sample rate/channels/bit depth."
            )
        all_frames.append(silence)
        all_frames.append(frames)

    joined = b"".join(all_frames)
    write_wav(out_path, joined, sample_rate, channels, sample_width)
    return len(joined) / float(sample_rate * channels * sample_width)


def generate_tone(
    path: str | Path,
    seconds: float,
    frequency: float,
    sample_rate: int = 24000,
    amplitude: float = 0.2,
    vibrato: float = 0.0,
) -> None:
    """Generate a short, faded sine tone for the mock backend."""

    frames = max(1, int(round(seconds * sample_rate)))
    fade = max(1, int(0.012 * sample_rate))
    samples = array("h")

    for i in range(frames):
        t = i / float(sample_rate)
        mod_frequency = frequency * (1.0 + vibrato * math.sin(2.0 * math.pi * 5.0 * t))
        envelope = 1.0
        if i < fade:
            envelope = i / float(fade)
        elif i > frames - fade:
            envelope = (frames - i) / float(fade)
        value = amplitude * envelope * math.sin(2.0 * math.pi * mod_frequency * t)
        samples.append(int(max(-1.0, min(1.0, value)) * 32767))

    write_wav(path, samples.tobytes(), sample_rate, 1, 2)
