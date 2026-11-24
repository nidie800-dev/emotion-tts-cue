"""Command backend: plug in any TTS CLI with a template.

Example::

    --backend command \
    --command "python my_tts.py --text {text} --emotion {emotion} \
               --intensity {intensity} --out {out} --language {language}"

Placeholders are ``{text}``, ``{emotion}``, ``{intensity}``, ``{out}``,
``{language}`` and ``{sample_rate}``. The command runs through the shell, so
only use templates you wrote yourself.
"""

from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

from .base import TTSBackend


class CommandBackend(TTSBackend):
    name = "command"

    def __init__(self, template: str) -> None:
        self.template = template

    def synthesize(
        self,
        text: str,
        emotion: str,
        intensity: float,
        out_path: str | Path,
        sample_rate: int = 24000,
        language: str = "ja",
    ) -> None:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        command = self.template.format(
            text=shlex.quote(text),
            emotion=shlex.quote(emotion),
            intensity=f"{float(intensity):.3f}",
            out=shlex.quote(str(out_path)),
            language=shlex.quote(language),
            sample_rate=int(sample_rate),
        )
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                f"TTS command failed ({result.returncode}): {result.stderr.strip() or result.stdout.strip()}"
            )
        if not out_path.exists() or out_path.stat().st_size == 0:
            raise RuntimeError(f"TTS command did not create {out_path}")
