"""ComfyUI node for EmoCue.

Install:
1. Copy this folder into ``ComfyUI/custom_nodes/comfyui_emotion_tts_cue``.
2. ``pip install -e /path/to/emotion-tts-cue`` (or add the repo root to PYTHONPATH).
3. Restart ComfyUI. The node appears under ``audio/EmoCue``.
"""

from __future__ import annotations

import os
import sys
import wave
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from emocue.backends import create_backend  # noqa: E402
from emocue.parser import parse_script  # noqa: E402
from emocue.render import render_script  # noqa: E402


class EmoCueRender:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "script": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "[whisper:0.9] 靠近一点，别出声。\n[pause:0.6]\n[happy:0.8] 今天的花，开得很好。\n",
                    },
                ),
                "backend": (["sapi", "mock", "http", "command"], {"default": "sapi"}),
                "output_dir": ("STRING", {"default": "emocue"}),
                "gap": ("FLOAT", {"default": 0.25, "min": 0.0, "max": 5.0, "step": 0.05}),
                "sample_rate": ("INT", {"default": 24000, "min": 8000, "max": 48000, "step": 1000}),
                "language": ("STRING", {"default": "zh"}),
                "api_url": ("STRING", {"default": "http://127.0.0.1:8000/tts"}),
                "command_template": ("STRING", {"default": ""}),
            }
        }

    RETURN_TYPES = ("AUDIO", "STRING", "STRING")
    RETURN_NAMES = ("audio", "cues_csv", "cues_mid")
    FUNCTION = "run"
    CATEGORY = "audio/EmoCue"

    def run(
        self,
        script: str,
        backend: str,
        output_dir: str,
        gap: float,
        sample_rate: int,
        language: str,
        api_url: str,
        command_template: str,
    ):
        parsed = parse_script(script)
        if parsed.is_empty():
            raise ValueError("EmoCue: script has no segments")

        output_dir = self._resolve_output_dir(output_dir)
        backend_instance = create_backend(
            backend,
            url=api_url,
            template=command_template or None,
        )
        result = render_script(
            parsed,
            backend_instance,
            out_dir=output_dir,
            gap=float(gap),
            sample_rate=int(sample_rate),
            language=language,
        )

        try:
            import numpy as np
            import torch
        except ImportError as exc:  # pragma: no cover - ComfyUI always has these
            raise RuntimeError("EmoCue: ComfyUI environment needs numpy and torch") from exc

        with wave.open(str(result.full_wav), "rb") as handle:
            channels = handle.getnchannels()
            rate = handle.getframerate()
            raw = handle.readframes(handle.getnframes())

        data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        if channels > 1:
            data = data.reshape(-1, channels).T
            tensor = torch.from_numpy(data).unsqueeze(0)
        else:
            tensor = torch.from_numpy(data).unsqueeze(0).unsqueeze(0)

        audio = {"waveform": tensor, "sample_rate": rate}
        return (audio, str(result.cues_csv), str(result.cues_mid))

    @staticmethod
    def _resolve_output_dir(output_dir: str) -> str:
        """Keep relative paths inside ComfyUI's output folder."""
        if os.path.isabs(output_dir):
            return output_dir
        try:
            import folder_paths

            relative = output_dir.replace("\\", "/").lstrip("/")
            if relative.startswith("output/"):
                relative = relative[len("output/"):]
            return os.path.join(folder_paths.get_output_directory(), relative)
        except Exception:
            return output_dir


NODE_CLASS_MAPPINGS = {"EmoCueRender": EmoCueRender}
NODE_DISPLAY_NAME_MAPPINGS = {"EmoCueRender": "EmoCue Render (Emotion TTS + Cues)"}
