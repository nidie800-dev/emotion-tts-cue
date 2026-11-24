"""Render a parsed script into audio + cue sheets."""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from pathlib import Path

from . import __version__
from .audio import concat_wavs, wav_info, write_silence
from .backends.base import TTSBackend
from .cues import Cue, write_cues_csv, write_project_json
from .midi import write_marker_midi
from .models import Script


@dataclass
class RenderResult:
    out_dir: Path
    full_wav: Path
    cues_csv: Path
    cues_mid: Path
    project_json: Path
    cues: list[Cue]
    sample_rate: int
    total_duration: float
    warnings: list[str]


def render_script(
    script: Script,
    backend: TTSBackend,
    out_dir: str | Path,
    gap: float = 0.25,
    sample_rate: int = 24000,
    language: str = "ja",
) -> RenderResult:
    if script.is_empty():
        raise ValueError("script has no segments")

    out_dir = Path(out_dir)
    segments_dir = out_dir / "segments"
    segments_dir.mkdir(parents=True, exist_ok=True)

    speech_files: dict[int, Path] = {}
    speech_rates: list[int] = []

    for segment in script.segments:
        if segment.is_pause:
            continue
        path = segments_dir / f"{segment.index:04d}_{segment.emotion}_{segment.intensity:.2f}.wav"
        backend.synthesize(
            text=segment.text,
            emotion=segment.emotion,
            intensity=segment.intensity,
            out_path=path,
            sample_rate=sample_rate,
            language=language,
        )
        actual_rate, _, _ = wav_info(path)
        speech_rates.append(actual_rate)
        speech_files[segment.index] = path

    if speech_rates:
        mix_rate = speech_rates[0]
        for rate in speech_rates[1:]:
            if rate != mix_rate:
                raise ValueError(
                    f"backend returned mixed sample rates ({mix_rate} and {rate}). "
                    "Make every segment use the same sample rate."
                )
    else:
        mix_rate = sample_rate

    segment_files: list[Path] = []
    cues: list[Cue] = []
    cursor = 0.0
    total = 0.0

    for position, segment in enumerate(script.segments):
        if segment.is_pause:
            path = segments_dir / f"{segment.index:04d}_pause_{segment.pause:.2f}.wav"
            write_silence(path, segment.pause, mix_rate)
        else:
            path = speech_files[segment.index]

        actual_rate, _, duration = wav_info(path)
        if actual_rate != mix_rate:
            raise ValueError(f"{path} has sample rate {actual_rate}, expected {mix_rate}")

        cue = Cue(
            index=segment.index,
            start=cursor,
            end=cursor + duration,
            duration=duration,
            emotion=segment.emotion,
            intensity=segment.intensity,
            text=segment.text,
            file=path.relative_to(out_dir).as_posix(),
            kind=segment.kind,
        )
        cues.append(cue)
        segment_files.append(path)
        total = cue.end + (gap if position < len(script.segments) - 1 else 0.0)
        cursor = total

    full_wav = out_dir / "full.wav"
    total_duration = concat_wavs(segment_files, full_wav, gap_seconds=gap)

    cues_csv = out_dir / "cues.csv"
    write_cues_csv(cues_csv, cues)

    cues_mid = out_dir / "cues.mid"
    write_marker_midi(
        cues_mid,
        [(cue.start, cue.marker_label) for cue in cues],
        total_duration=total_duration,
    )

    project_json = out_dir / "project.json"
    write_project_json(
        project_json,
        {
            "tool": "emocue",
            "version": __version__,
            "created_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            "backend": backend.name,
            "language": language,
            "gap": gap,
            "sample_rate": mix_rate,
            "total_duration": round(total_duration, 3),
            "segment_count": len(cues),
            "warnings": script.warnings,
            "cues": [
                {
                    "index": cue.index,
                    "start": round(cue.start, 3),
                    "end": round(cue.end, 3),
                    "duration": round(cue.duration, 3),
                    "emotion": cue.emotion,
                    "intensity": cue.intensity,
                    "kind": cue.kind,
                    "file": cue.file,
                    "text": cue.text,
                }
                for cue in cues
            ],
        },
    )

    return RenderResult(
        out_dir=out_dir,
        full_wav=full_wav,
        cues_csv=cues_csv,
        cues_mid=cues_mid,
        project_json=project_json,
        cues=cues,
        sample_rate=mix_rate,
        total_duration=total_duration,
        warnings=script.warnings,
    )
