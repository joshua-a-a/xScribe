from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class TranscriptionSegment:
    start: float
    end: float
    text: str
    confidence: Optional[float] = None
    speaker: Optional[str] = None

    def __post_init__(self):
        if self.start < 0:
            raise ValueError("Start time cannot be negative")
        if self.end < self.start:
            raise ValueError("End time must be greater than start time")
        if self.confidence is not None and not (0.0 <= self.confidence <= 1.0):
            raise ValueError("Confidence must be between 0.0 and 1.0")

    @property
    def duration(self) -> float:
        return self.end - self.start

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start": self.start,
            "end": self.end,
            "text": self.text,
            "confidence": self.confidence,
            "speaker": self.speaker,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TranscriptionSegment":
        return cls(
            start=data["start"],
            end=data["end"],
            text=data["text"],
            confidence=data.get("confidence"),
            speaker=data.get("speaker"),
        )


@dataclass
class TranscriptionResult:
    segments: List[TranscriptionSegment]
    language: str
    language_probability: float
    duration: float
    processing_time: float
    model_used: str
    word_timestamps: Optional[List[Dict[str, Any]]] = None
    file_path: Optional[Path] = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.segments:
            raise ValueError("Transcription result must contain at least one segment")
        if not (0.0 <= self.language_probability <= 1.0):
            raise ValueError("Language probability must be between 0.0 and 1.0")
        if self.duration <= 0:
            raise ValueError("Duration must be positive")
        if self.processing_time < 0:
            raise ValueError("Processing time cannot be negative")

    @property
    def full_text(self) -> str:
        return " ".join(segment.text.strip() for segment in self.segments)

    @property
    def word_count(self) -> int:
        return len(self.full_text.split())

    @property
    def average_confidence(self) -> Optional[float]:
        confidences = [
            seg.confidence for seg in self.segments if seg.confidence is not None
        ]
        return sum(confidences) / len(confidences) if confidences else None

    def get_segments_by_speaker(self, speaker: str) -> List[TranscriptionSegment]:
        return [seg for seg in self.segments if seg.speaker == speaker]

    def get_unique_speakers(self) -> List[str]:
        speakers = {seg.speaker for seg in self.segments if seg.speaker}
        return sorted(list(speakers))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "segments": [segment.to_dict() for segment in self.segments],
            "language": self.language,
            "language_probability": self.language_probability,
            "duration": self.duration,
            "processing_time": self.processing_time,
            "model_used": self.model_used,
            "file_path": str(self.file_path) if self.file_path else None,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
            "text": self.full_text,
            "full_text": self.full_text,
            "word_count": self.word_count,
            "average_confidence": self.average_confidence,
            "unique_speakers": self.get_unique_speakers(),
        }

    def to_json(self) -> str:
        import json

        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TranscriptionResult":
        segments = [
            TranscriptionSegment.from_dict(seg_data)
            for seg_data in data.get("segments", [])
        ]

        created_at = (
            datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else datetime.now()
        )

        file_path = Path(data["file_path"]) if data.get("file_path") else None

        duration = data.get("duration")
        if duration is None and segments:
            duration = max(seg.end for seg in segments) - min(
                seg.start for seg in segments
            )

        return cls(
            segments=segments,
            language=data.get("language", "unknown"),
            language_probability=data.get("language_probability", 1.0),
            duration=duration if duration is not None else 0.0,
            processing_time=data.get("processing_time", 0.0),
            model_used=data.get("model_used", "unknown"),
            word_timestamps=data.get("word_timestamps"),
            file_path=file_path,
            created_at=created_at,
            metadata=data.get("metadata", {}),
        )


@dataclass
class ProcessingStatus:
    file_path: Path
    status: str  # 'pending', 'processing', 'completed', 'failed'
    progress: float = 0.0  # 0.0 to 100.0
    current_step: str = ""
    error_message: str = ""
    result: Optional[TranscriptionResult] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        valid_statuses = {"pending", "processing", "completed", "failed"}
        if self.status not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        if not (0.0 <= self.progress <= 100.0):
            raise ValueError("Progress must be between 0.0 and 100.0")

    @property
    def is_completed(self) -> bool:
        return self.status == "completed" and self.result is not None

    @property
    def is_failed(self) -> bool:
        return self.status == "failed"

    @property
    def processing_duration(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": str(self.file_path),
            "status": self.status,
            "progress": self.progress,
            "current_step": self.current_step,
            "error_message": self.error_message,
            "result": self.result.to_dict() if self.result else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "processing_duration": self.processing_duration,
        }
