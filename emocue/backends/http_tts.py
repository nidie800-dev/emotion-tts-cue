"""HTTP backend for a local or remote TTS service.

Expected contract
-----------------
POST JSON::

    {"text": "...", "emotion": "happy", "intensity": 0.8,
     "language": "ja", "sample_rate": 24000}

Response: either ``audio/wav`` bytes, or JSON with one of:

* ``{"audio_base64": "..."}``
* ``{"audio": "..."}``
* ``{"audio_url": "https://..."}``

This keeps the project model-agnostic: CosyVoice, GPT-SoVITS, Fish Audio S2
Pro or your own service can sit behind the same contract.
"""

from __future__ import annotations

import base64
import json
import urllib.request
from pathlib import Path

from .base import TTSBackend


class HttpTTSBackend(TTSBackend):
    name = "http"

    def __init__(
        self,
        url: str,
        timeout: float = 120.0,
        api_key: str | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        self.url = url
        self.timeout = timeout
        self.api_key = api_key
        self.extra_headers = extra_headers or {}

    def synthesize(
        self,
        text: str,
        emotion: str,
        intensity: float,
        out_path: str | Path,
        sample_rate: int = 24000,
        language: str = "ja",
    ) -> None:
        payload = {
            "text": text,
            "emotion": emotion,
            "intensity": float(intensity),
            "language": language,
            "sample_rate": int(sample_rate),
        }
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        headers.update(self.extra_headers)

        request = urllib.request.Request(
            self.url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                content_type = response.headers.get("Content-Type", "")
                body = response.read()
        except Exception as exc:  # noqa: BLE001 - surface a readable backend error
            raise RuntimeError(f"TTS request failed: {exc}") from exc

        audio = self._extract_audio(body, content_type)
        if not audio.startswith(b"RIFF"):
            raise RuntimeError("backend did not return a RIFF/WAV payload")

        path = Path(out_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(audio)

    def _extract_audio(self, body: bytes, content_type: str) -> bytes:
        if "application/json" in content_type:
            data = json.loads(body.decode("utf-8"))
            if "audio_base64" in data:
                return self._decode_base64(data["audio_base64"])
            if "audio" in data:
                return self._decode_base64(data["audio"])
            if "audio_url" in data:
                with urllib.request.urlopen(data["audio_url"], timeout=self.timeout) as response:
                    return response.read()
            raise RuntimeError("JSON response has no audio_base64/audio/audio_url field")
        return body

    @staticmethod
    def _decode_base64(value: str) -> bytes:
        if value.startswith("data:") and "," in value:
            value = value.split(",", 1)[1]
        return base64.b64decode(value)
