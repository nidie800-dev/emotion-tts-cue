from dataclasses import dataclass, field


EMOTIONS = {
    "neutral",
    "happy",
    "sad",
    "angry",
    "surprised",
    "fearful",
    "whisper",
    "laugh",
    "sigh",
    "cry",
}

# Common aliases so scripts can use either Chinese-friendly English names or
# short forms. Keep the canonical names stable: they are written to cue sheets.
TAG_ALIASES = {
    "joy": "happy",
    "anger": "angry",
    "fear": "fearful",
    "surprise": "surprised",
    "calm": "neutral",
    "soft": "whisper",
    "crying": "cry",
    "sighing": "sigh",
    "laughing": "laugh",
}


@dataclass
class Segment:
    """One unit of the script: either a speech line or a pause."""

    index: int
    text: str = ""
    emotion: str = "neutral"
    intensity: float = 0.5
    pause: float = 0.0
    line: int = 0

    @property
    def is_pause(self) -> bool:
        return self.pause > 0

    @property
    def kind(self) -> str:
        return "pause" if self.is_pause else "speech"


@dataclass
class Script:
    segments: list[Segment] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not self.segments
