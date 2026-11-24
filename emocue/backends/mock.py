"""Mock backend: no model, no GPU, no network. Useful for testing the pipeline."""

from __future__ import annotations

from pathlib import Path

from ..audio import generate_tone
from .base import TTSBackend

FREQUENCIES = {
    "neutral": 220.0,
    "happy": 330.0,
    "sad": 196.0,
    "angry": 160.0,
    "surprised": 392.0,
    "fearful": 180.0,
    "whisper": 260.0,
    "laugh": 440.0,
    "sigh": 180.0,
    "cry": 300.0,
}

VIBRATO = {
    "happy": 0.012,
    "sad": 0.006,
    "angry": 0.004,
    "surprised": 0.015,
    "fearful": 0.02,
    "whisper": 0.003,
    "laugh": 0.03,
    "sigh": 0.005,
    "cry": 0.035,
}


class MockBackend(TTSBackend):
    name = "mock"

    def synthesize(
        self,
        text: str,
        emotion: str,
        intensity: float,
        out_path: str | Path,
        sample_rate: int = 24000,
        language: str = "ja",
    ) -> None:
        if emotion in {"laugh", "sigh", "cry"}:
            duration = {"laugh": 0.7, "sigh": 0.9, "cry": 1.1}[emotion]
        else:
            duration = max(0.5, min(8.0, 0.35 + len(text) * 0.09))
            if emotion == "whisper":
                duration *= 1.1

        amplitude = 0.12 + 0.12 * max(0.0, min(1.0, intensity))
        if emotion == "whisper":
            amplitude *= 0.7

        generate_tone(
            out_path,
            seconds=duration,
            frequency=FREQUENCIES.get(emotion, 220.0),
            sample_rate=sample_rate,
            amplitude=amplitude,
            vibrato=VIBRATO.get(emotion, 0.0),
        )
