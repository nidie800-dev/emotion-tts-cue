"""Cue sheet and project manifest writers."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Cue:
    index: int
    start: float
    end: float
    duration: float
    emotion: str
    intensity: float
    text: str
    file: str
    kind: str

    @property
    def marker_label(self) -> str:
        return f"{self.index:02d} {self.emotion} {self.intensity:.1f}"


def write_cues_csv(path: str | Path, cues: list[Cue]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["index", "start", "end", "duration", "emotion", "intensity", "kind", "file", "text"]
        )
        for cue in cues:
            writer.writerow(
                [
                    cue.index,
                    f"{cue.start:.3f}",
                    f"{cue.end:.3f}",
                    f"{cue.duration:.3f}",
                    cue.emotion,
                    f"{cue.intensity:.2f}",
                    cue.kind,
                    cue.file,
                    cue.text,
                ]
            )


def write_project_json(path: str | Path, payload: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
