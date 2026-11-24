"""Parse a small, human-friendly emotion script.

Syntax
------
    # comment
    [happy:0.8] 今天天气真好。
    [whisper:0.9] 靠近一点，别出声。
    [pause:0.6]
    [sad] 可是我还是有点难过。
    [laugh] 算了，不说了。

Rules
-----
* A line may start with one or more tags: ``[emotion]`` or ``[emotion:intensity]``.
* ``[pause:0.5]`` creates a silence segment. ``500ms`` and ``1s`` are accepted.
* An emotion tag with no text on the same line sets the "sticky" emotion for
  following lines. This keeps scripts short.
* Intensity is clamped to 0..1. Default is 0.5.
* Unknown tags are ignored with a warning; they never break the render.
"""

from __future__ import annotations

import re

from .models import EMOTIONS, TAG_ALIASES, Script, Segment

TAG_RE = re.compile(r"^\[([^\]]+)\]")
PAUSE_RE = re.compile(r"^pause(?::([0-9.]+)(ms|s)?)?$", re.IGNORECASE)


def _clamp_intensity(value: str) -> float | None:
    try:
        parsed = float(value)
    except ValueError:
        return None
    return max(0.0, min(1.0, parsed))


def _parse_pause(value: str | None, unit: str | None) -> float | None:
    if value is None:
        return 0.5
    try:
        amount = float(value)
    except ValueError:
        return None
    if (unit or "s").lower() == "ms":
        amount /= 1000.0
    return max(0.0, amount)


def parse_script(text: str, default_emotion: str = "neutral", default_intensity: float = 0.5) -> Script:
    """Parse ``text`` into a :class:`Script`."""

    script = Script()
    current_emotion = default_emotion
    current_intensity = max(0.0, min(1.0, default_intensity))
    index = 0

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue

        rest = line
        pause_total = 0.0
        saw_tag = False

        while True:
            match = TAG_RE.match(rest)
            if not match:
                break
            saw_tag = True
            tag = match.group(1).strip()
            rest = rest[match.end():].strip()

            pause_match = PAUSE_RE.match(tag)
            if pause_match:
                seconds = _parse_pause(pause_match.group(1), pause_match.group(2))
                if seconds is None:
                    script.warnings.append(f"line {line_number}: invalid pause tag [{tag}]")
                else:
                    pause_total += seconds
                continue

            name, separator, intensity_text = tag.partition(":")
            name = TAG_ALIASES.get(name.strip().lower(), name.strip().lower())
            if name not in EMOTIONS:
                script.warnings.append(f"line {line_number}: unknown tag [{tag}] ignored")
                continue

            current_emotion = name
            if separator and intensity_text.strip():
                parsed = _clamp_intensity(intensity_text.strip())
                if parsed is None:
                    script.warnings.append(f"line {line_number}: invalid intensity in [{tag}]")
                else:
                    current_intensity = parsed

        if pause_total > 0:
            index += 1
            script.segments.append(
                Segment(
                    index=index,
                    text="",
                    emotion="pause",
                    intensity=0.0,
                    pause=pause_total,
                    line=line_number,
                )
            )

        if rest:
            index += 1
            script.segments.append(
                Segment(
                    index=index,
                    text=rest,
                    emotion=current_emotion,
                    intensity=current_intensity,
                    line=line_number,
                )
            )
        elif not saw_tag:
            script.warnings.append(f"line {line_number}: empty line ignored")

    if not script.segments:
        script.warnings.append("script has no segments")

    return script
