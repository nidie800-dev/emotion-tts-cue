"""TTS backend interface."""

from __future__ import annotations

from pathlib import Path


class TTSBackend:
    """A backend writes one WAV file per segment."""

    name = "base"

    def synthesize(
        self,
        text: str,
        emotion: str,
        intensity: float,
        out_path: str | Path,
        sample_rate: int = 24000,
        language: str = "ja",
    ) -> None:
        raise NotImplementedError
