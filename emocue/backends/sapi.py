"""Windows SAPI backend: real Chinese speech with zero model downloads.

Uses the built-in ``System.Speech`` voice (Microsoft Huihui on zh-CN Windows).
It only has rate/volume control, so emotion is approximated. For real emotional
TTS, use the HTTP backend with CosyVoice / GPT-SoVITS.
"""

from __future__ import annotations

import base64
import os
import platform
import subprocess
from pathlib import Path

from .base import TTSBackend

RATE_BASE = {
    "neutral": 0,
    "happy": 2,
    "sad": -2,
    "angry": 1,
    "surprised": 3,
    "fearful": 1,
    "whisper": -1,
    "laugh": 3,
    "sigh": -2,
    "cry": -1,
}

RATE_DELTA = {
    "neutral": 0,
    "happy": 3,
    "sad": -2,
    "angry": 3,
    "surprised": 2,
    "fearful": 2,
    "whisper": -1,
    "laugh": 2,
    "sigh": -1,
    "cry": -1,
}

VOLUME = {
    "neutral": 100,
    "happy": 95,
    "sad": 72,
    "angry": 100,
    "surprised": 95,
    "fearful": 80,
    "whisper": 35,
    "laugh": 95,
    "sigh": 60,
    "cry": 65,
}


class SapiBackend(TTSBackend):
    name = "sapi"

    def __init__(self, voice: str | None = None) -> None:
        if platform.system() != "Windows":
            raise RuntimeError("sapi backend is Windows-only; use mock or http instead")
        self.voice = voice or os.environ.get("EMOCUE_SAPI_VOICE", "Microsoft Huihui Desktop")

    def synthesize(
        self,
        text: str,
        emotion: str,
        intensity: float,
        out_path: str | Path,
        sample_rate: int = 24000,
        language: str = "zh",
    ) -> None:
        path = Path(out_path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)

        intensity = max(0.0, min(1.0, float(intensity)))
        rate = RATE_BASE.get(emotion, 0) + int(round(RATE_DELTA.get(emotion, 0) * (intensity - 0.5) * 2))
        rate = max(-10, min(10, rate))
        volume = int(VOLUME.get(emotion, 100) * (0.8 + 0.2 * intensity))
        volume = max(0, min(100, volume))

        safe_text = text.replace("\r", " ").replace("\n", " ").replace("'", "''")
        safe_voice = self.voice.replace("'", "''")
        safe_path = str(path).replace("'", "''")

        script = (
            "Add-Type -AssemblyName System.Speech\n"
            "$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer\n"
            f"try {{ $synth.SelectVoice('{safe_voice}') }} catch {{ }}\n"
            f"$synth.Rate = {rate}\n"
            f"$synth.Volume = {volume}\n"
            f"$synth.SetOutputToWaveFile('{safe_path}')\n"
            f"$synth.Speak('{safe_text}')\n"
            "$synth.Dispose()\n"
        )
        encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-EncodedCommand",
                encoded,
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"SAPI failed ({result.returncode}): {result.stderr.strip() or result.stdout.strip()}"
            )
        if not path.exists() or path.stat().st_size == 0:
            raise RuntimeError(f"SAPI did not create {path}")
