from dataclasses import dataclass, field


@dataclass
class WordTimestamp:
    word: str
    start: float
    end: float
    confidence: float = 1.0


@dataclass
class TranscriptionSegment:
    speaker_id: str = ""
    speaker_label: str = ""
    text: str = ""
    start: float = 0.0
    end: float = 0.0
    words: list = field(default_factory=list)
    gender: str | None = None
    confidence: float = 0.0

    @property
    def duration(self) -> float:
        return self.end - self.start


@dataclass
class SpeakerSegment:
    speaker_id: str
    start: float
    end: float


@dataclass
class PipelineResult:
    segments: list = field(default_factory=list)
    audio_path: str = ""
    duration: float = 0.0
    errors: list = field(default_factory=list)
