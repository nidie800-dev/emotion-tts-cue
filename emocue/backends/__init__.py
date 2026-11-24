"""Backend factory."""

from __future__ import annotations

from .base import TTSBackend
from .command import CommandBackend
from .http_tts import HttpTTSBackend
from .mock import MockBackend
from .sapi import SapiBackend

__all__ = [
    "TTSBackend",
    "MockBackend",
    "HttpTTSBackend",
    "CommandBackend",
    "SapiBackend",
    "create_backend",
]


def create_backend(name: str, **kwargs) -> TTSBackend:
    if name == "mock":
        return MockBackend()
    if name == "sapi":
        return SapiBackend(voice=kwargs.get("voice"))
    if name == "http":
        url = kwargs.get("url")
        if not url:
            raise ValueError("http backend requires url")
        return HttpTTSBackend(
            url=url,
            timeout=float(kwargs.get("timeout", 120.0)),
            api_key=kwargs.get("api_key"),
        )
    if name == "command":
        template = kwargs.get("template")
        if not template:
            raise ValueError("command backend requires template")
        return CommandBackend(template=template)
    raise ValueError(f"unknown backend: {name}")
